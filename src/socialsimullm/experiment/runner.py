# socialsimullm/experiment/runner.py

# -*- coding: utf-8 -*-

"""
Experiment execution engine for SocialSimuLLM.

Orchestrates single and batch experiment runs by creating run directories,
translating ExperimentConfig to SimulationConfig, and delegating execution
to SimulatorCore. Never imports from frontend/.

@author: Huang Miaosen
"""

from __future__ import annotations

import os
import random
import shutil
from pathlib import Path
from typing import Any

from socialsimullm.experiment.config import ExperimentConfig
from socialsimullm.experiment.storage import create_run_dir


class ExperimentRunner:
    """Orchestrates single and batch experiment runs.

    Creates run directories under runs/{project}/{experiment_id}/,
    translates ExperimentConfig to SimulationConfig, and delegates
    execution to SimulatorCore.

    Usage::

        runner = ExperimentRunner()
        eid = runner.run_single(config)
        eids = runner.run_batch(config, seeds=[42, 43, 44])
    """

    def run_single(self, config: ExperimentConfig) -> str:
        """Execute a single experiment run.

        Args:
            config: Validated ExperimentConfig.

        Returns:
            The experiment_id of the completed run.

        Raises:
            ValueError: If config is invalid or spatial_graph_path not found.
            RuntimeError: If simulation fails during execution.
        """
        # 1. Set random seed
        if config.random_seed > 0:
            random.seed(config.random_seed)

        # 2. Create run directory (flat structure when no project specified)
        from socialsimullm.experiment.storage import get_runs_root

        project = config.project
        if project:
            run_dir = create_run_dir(project, config.experiment_id)
        else:
            run_dir = get_runs_root() / config.experiment_id
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "agent_data").mkdir(exist_ok=True)

        # 3. Copy town_data.json into run directory (or generate from spatial_config)
        self._prepare_project_data(config, run_dir)

        # 3b. If spatial_config is set, generate a custom town_data.json
        if config.spatial_config is not None:
            self._generate_spatial_town_data(config, run_dir)

        # 4. Save config snapshot
        config.to_yaml(str(run_dir / "config.yaml"))

        # 5. Build SimulationConfig from ExperimentConfig
        sim_config = config.to_simulation_config()
        sim_config.project_name = str(run_dir)
        sim_config.memory_config = config.memory_config

        # 6. Setup error logging to run directory
        from socialsimullm.utils.logger import setup_error_logging

        setup_error_logging(str(run_dir))

        # 7. Sync API keys from environment and validate
        from socialsimullm.utils.config import (
            _apply_config_to_globals,
            validate_config,
        )
        _apply_config_to_globals(sim_config)
        validate_config(sim_config)

        # 8. Run the simulation
        from socialsimullm.simulator.core import SimulatorCore

        spatial_cfg = self._to_world_spatial_config(config)

        core = SimulatorCore(
            sim_config,
            initial_event=config.get_event_string(),
            spatial_config=spatial_cfg,
        )
        observer = self._start_observability(run_dir, config)
        try:
            core.initialize()
            self._bind_checkpoint_runtime(core)
            core.run(max_steps=config.simulation_steps)

            # Ensure done.flag is written (logger.finalize flushes buffers + writes done.flag)
            if core.logger is not None:
                core.logger.finalize()
            observer.finish_run_metadata("completed")
        except Exception:
            observer.finish_run_metadata("failed")
            raise
        finally:
            self._stop_model_call_logging()

        return config.experiment_id

    def resume_single(
        self,
        config: ExperimentConfig,
        step: int | None = None,
    ) -> str:
        """Restore a full checkpoint and continue to the configured total steps."""
        from socialsimullm.experiment.storage import restore_checkpoint

        restored = restore_checkpoint(
            config.experiment_id,
            step=step,
            project=config.project or None,
        )
        restored_step = int(restored["step"])
        remaining_steps = config.simulation_steps - restored_step
        if remaining_steps < 0:
            raise ValueError(
                f"Checkpoint step {restored_step} exceeds configured total "
                f"simulation_steps {config.simulation_steps}"
            )

        if config.random_seed > 0:
            random.seed(config.random_seed)

        run_dir = Path(restored["run_dir"])
        sim_config = config.to_simulation_config()
        sim_config.project_name = str(run_dir)
        sim_config.memory_config = config.memory_config

        from socialsimullm.utils.logger import setup_error_logging
        from socialsimullm.utils.config import (
            _apply_config_to_globals,
            validate_config,
        )

        setup_error_logging(str(run_dir))
        _apply_config_to_globals(sim_config)
        validate_config(sim_config)

        from socialsimullm.simulator.core import SimulatorCore

        core = SimulatorCore(
            sim_config,
            initial_event="No new event.",
            spatial_config=self._to_world_spatial_config(config),
        )
        observer = self._start_observability(
            run_dir, config, resumed_from_step=restored_step
        )
        try:
            core.initialize()
            self._apply_runtime_state(core, restored["runtime_state"])
            self._bind_checkpoint_runtime(core)

            print(
                f"Resuming experiment {config.experiment_id} from step "
                f"{restored_step}; {remaining_steps} step(s) remaining."
            )
            if remaining_steps > 0:
                core.run(max_steps=remaining_steps)
            if core.logger is not None:
                core.logger.finalize()
            observer.finish_run_metadata("completed")
        except Exception:
            observer.finish_run_metadata("failed")
            raise
        finally:
            self._stop_model_call_logging()
        return config.experiment_id

    def run_batch(
        self, config: ExperimentConfig, seeds: list[int]
    ) -> list[str]:
        """Execute multiple runs with different random seeds.

        Each seed produces a separate experiment directory.

        Args:
            config: Base ExperimentConfig.
            seeds: List of random seeds, one per run.

        Returns:
            List of experiment_ids for each completed run.
        """
        results: list[str] = []
        for seed in seeds:
            batch_eid = f"{config.experiment_id}_seed{seed}"

            # Check for existing experiment to prevent data overwrite
            from socialsimullm.experiment.storage import find_run_dir
            try:
                find_run_dir(batch_eid, config.project)
                raise FileExistsError(
                    f"Experiment '{batch_eid}' already exists. "
                    f"Delete it or use a different experiment_id."
                )
            except FileNotFoundError:
                pass  # Safe to proceed

            batch_config = config.model_copy(
                update={
                    "experiment_id": batch_eid,
                    "random_seed": seed,
                }
            )
            eid = self.run_single(batch_config)
            results.append(eid)
        return results

    def _prepare_project_data(
        self, config: ExperimentConfig, run_dir: Path
    ) -> None:
        """Copy town_data.json to the run directory.

        If spatial_graph_path is set, copies from that path.
        Otherwise, copies from the default template location.

        Args:
            config: ExperimentConfig with spatial_graph_path.
            run_dir: Target run directory.

        Raises:
            FileNotFoundError: If the source town_data.json does not exist.
        """
        dst = run_dir / "town_data.json"
        if dst.exists():
            return

        src = config.spatial_graph_path
        if not src:
            # Use default template
            src = self._get_template_path()

        src_path = Path(src)
        if not src_path.exists():
            raise FileNotFoundError(
                f"town_data.json not found at '{src}'. "
                f"Set spatial_graph_path in ExperimentConfig or ensure "
                f"the template exists."
            )

        shutil.copy2(str(src_path), str(dst))

    @staticmethod
    def _get_template_path() -> str:
        """Get the default town_data_template.json path.

        Returns:
            Absolute path to the template file.
        """
        template_path = os.path.join(
            os.path.dirname(__file__),
            "..", "data", "town_data_template.json",
        )
        return os.path.normpath(template_path)

    def _generate_spatial_town_data(
        self, config: ExperimentConfig, run_dir: Path
    ) -> None:
        """Generate a town_data.json using the spatial config.

        Reads the base template and replaces the topology with
        the configured graph variant.

        Args:
            config: ExperimentConfig with spatial_config set.
            run_dir: Target run directory.
        """
        import json

        from socialsimullm.world.spatial import WorldVariationGenerator

        world_spatial_config = self._to_world_spatial_config(config)
        if world_spatial_config is None:
            return

        template_path = config.spatial_graph_path or self._get_template_path()
        with open(template_path, "r", encoding="utf-8") as f:
            base_template = json.load(f)

        generator = WorldVariationGenerator(world_spatial_config)
        town_data = generator.generate_town_data(base_template)

        dst = run_dir / "town_data.json"
        with open(dst, "w", encoding="utf-8") as f:
            json.dump(town_data, f, indent=2, ensure_ascii=False)

    def _to_world_spatial_config(
        self, config: ExperimentConfig
    ) -> SpatialConfig | None:
        """Convert ExperimentConfig.spatial_config to world.SpatialConfig.

        Args:
            config: ExperimentConfig with optional spatial_config.

        Returns:
            World SpatialConfig or None if spatial_config is not set.
        """
        if config.spatial_config is None:
            return None

        from socialsimullm.world.spatial import SpatialConfig as WorldSpatialConfig

        sc = config.spatial_config
        return WorldSpatialConfig(
            topology=sc.topology,
            num_locations=sc.num_locations,
            edge_weight_range=(sc.edge_weight_min, sc.edge_weight_max),
            seed=sc.seed,
            extra_params={
                "k": sc.small_world_k,
                "p": sc.small_world_p,
                "rows": sc.grid_rows,
                "cols": sc.grid_cols,
                "random_p": sc.random_p,
                "m": sc.scale_free_m,
            },
        )

    @staticmethod
    def _bind_checkpoint_runtime(core: Any) -> None:
        """Expose coordinator state to StructuredLogger checkpoint snapshots."""
        if core.logger is None:
            return
        bind = getattr(core.logger, "bind_runtime", None)
        if callable(bind):
            bind(
                reflection_engine=getattr(core, "reflection_engine", None),
                interaction_coordinator=getattr(core, "interaction_coordinator", None),
            )

    @staticmethod
    def _config_summary(config: ExperimentConfig) -> dict[str, Any]:
        """Return reproducibility inputs without prompts, paths, or credentials."""
        return {
            "experiment_id": config.experiment_id,
            "project": config.project,
            "model": config.model,
            "embedding_model": config.embedding_model,
            "simulation_steps": config.simulation_steps,
            "memory_limit": config.memory_limit,
            "random_seed": config.random_seed,
            "checkpoint_interval": config.checkpoint_interval,
            "events_count": len(config.events),
            "reflection_enabled": config.reflection_enabled,
            "fov_enabled": config.fov_enabled,
            "path_planner_enabled": config.path_planner_enabled,
            "goal_enabled": config.goal_enabled,
            "memory_config": config.memory_config.model_dump(),
        }

    @classmethod
    def _start_observability(
        cls,
        run_dir: Path,
        config: ExperimentConfig,
        *,
        resumed_from_step: int | None = None,
    ) -> Any:
        """Start safe metadata persistence before initialization model calls."""
        from socialsimullm.utils.logger import StructuredLogger
        from socialsimullm.utils.text_generation import (
            clear_model_call_metadata,
            set_model_call_metadata_sink,
        )

        observer = StructuredLogger(str(run_dir))
        observer.start_run_metadata(
            cls._config_summary(config),
            config.prompt_meta,
            resumed_from_step=resumed_from_step,
        )
        clear_model_call_metadata()
        set_model_call_metadata_sink(observer.log_model_call)
        return observer

    @staticmethod
    def _stop_model_call_logging() -> None:
        """Release the process-global sink and its bounded metadata buffer."""
        from socialsimullm.utils.text_generation import (
            drain_model_call_metadata,
            set_model_call_metadata_sink,
        )

        set_model_call_metadata_sink(None)
        drain_model_call_metadata()

    @classmethod
    def _apply_runtime_state(cls, core: Any, payload: dict[str, Any]) -> None:
        """Rehydrate in-memory agent, reflection, path, goal, and dialog state."""
        state = core.state
        if state is None:
            raise RuntimeError("SimulatorCore.initialize() did not create state")

        state.active_event_ids = list(payload.get("active_event_ids", []))
        state.events = list(payload.get("events", state.events))
        state.timed_events = list(payload.get("timed_events", state.timed_events))

        agents_by_name = {agent.name: agent for agent in state.agents}
        for name, saved in payload.get("agents", {}).items():
            agent = agents_by_name.get(name)
            if agent is None or not isinstance(saved, dict):
                continue
            for field in (
                "location",
                "daily_plans",
                "hourly_plan",
                "impression",
                "action",
                "recent_actions",
                "reflection",
                "related_things",
                "event",
                "place_ratings",
            ):
                if field in saved:
                    setattr(agent, field, saved[field])
            agent.action_detail = cls._restore_agent_action(saved.get("action_detail"))
            agent.goals = cls._restore_goals(saved.get("goals", []))
            agent.planned_path = cls._restore_planned_path(saved.get("planned_path"))

        reflection = getattr(core, "reflection_engine", None)
        saved_reflection = payload.get("reflection", {})
        if reflection is not None and isinstance(saved_reflection, dict):
            reflection._last_reflection_cache = dict(
                saved_reflection.get("last_reflection_cache", {})
            )
            reflection._last_reflection_step = {
                str(name): int(value)
                for name, value in saved_reflection.get("last_reflection_step", {}).items()
            }

        cls._restore_interactions(
            getattr(core, "interaction_coordinator", None),
            payload.get("interactions", {}),
        )
        saved_logger = payload.get("logger", {})
        if core.logger is not None and isinstance(saved_logger, dict):
            core.logger._summary_buffer = list(
                saved_logger.get("summary_buffer", [])
            )
        random_state = payload.get("random_state")
        if isinstance(random_state, list):
            random.setstate(cls._nested_tuple(random_state))

    @staticmethod
    def _restore_agent_action(value: Any) -> Any:
        from socialsimullm.agents.agent import AgentAction

        if not isinstance(value, dict):
            return AgentAction(action="")
        return AgentAction.from_response(value)

    @staticmethod
    def _restore_goals(value: Any) -> list[Any]:
        if not isinstance(value, list) or not value:
            return []
        from socialsimullm.cognition.goal import GoalConfig, GoalManager

        return GoalManager(GoalConfig()).deserialize_goals(value)

    @staticmethod
    def _restore_planned_path(value: Any) -> Any:
        if not isinstance(value, dict):
            return None
        from socialsimullm.world.path_planner import MovementIntent, PlannedPath

        intent_data = value.get("intent")
        intent = (
            MovementIntent(**intent_data)
            if isinstance(intent_data, dict)
            else None
        )
        return PlannedPath(
            agent_name=str(value.get("agent_name", "")),
            origin=str(value.get("origin", "")),
            destination=str(value.get("destination", "")),
            path=list(value.get("path", [])),
            total_distance=float(value.get("total_distance", 0.0)),
            steps_remaining=int(value.get("steps_remaining", 0)),
            intent=intent,
        )

    @staticmethod
    def _restore_interactions(coordinator: Any, value: Any) -> None:
        if coordinator is None or not isinstance(value, dict):
            return
        from socialsimullm.simulator.interactions import (
            _ConversationSession,
            _ParticipationState,
        )

        coordinator._participation = {
            str(name): _ParticipationState(**saved)
            for name, saved in value.get("participation", {}).items()
            if isinstance(saved, dict)
        }
        sessions = {}
        for saved in value.get("sessions", []):
            if not isinstance(saved, dict) or len(saved.get("pair", [])) != 2:
                continue
            pair = tuple(str(item) for item in saved["pair"])
            sessions[pair] = _ConversationSession(
                conversation_id=str(saved.get("conversation_id", "")),
                last_step=int(saved.get("last_step", 0)),
            )
        coordinator._sessions = sessions

    @classmethod
    def _nested_tuple(cls, value: Any) -> Any:
        if isinstance(value, list):
            return tuple(cls._nested_tuple(item) for item in value)
        return value
