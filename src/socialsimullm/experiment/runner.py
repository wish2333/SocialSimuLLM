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

        # 2. Create run directory
        project = config.project or config.experiment_id
        run_dir = create_run_dir(project, config.experiment_id)

        # 3. Copy town_data.json into run directory
        self._prepare_project_data(config, run_dir)

        # 4. Save config snapshot
        config.to_yaml(str(run_dir / "config.yaml"))

        # 5. Build SimulationConfig from ExperimentConfig
        sim_config = config.to_simulation_config()
        sim_config.project_name = str(run_dir)

        # 6. Sync API keys from environment and validate
        from socialsimullm.utils.config import (
            _apply_config_to_globals,
            validate_config,
        )
        _apply_config_to_globals(sim_config)
        validate_config(sim_config)

        # 7. Run the simulation
        from socialsimullm.simulator.core import SimulatorCore

        core = SimulatorCore(
            sim_config, initial_event=config.get_event_string()
        )
        core.initialize()
        core.run(max_steps=config.simulation_steps)

        # Ensure done.flag is written (logger.finalize flushes buffers + writes done.flag)
        if core.logger is not None:
            core.logger.finalize()

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
