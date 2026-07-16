import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from socialsimullm.experiment.config import ExperimentConfig
from socialsimullm.experiment.runner import ExperimentRunner
from socialsimullm.experiment.storage import list_experiments, restore_checkpoint
from socialsimullm.simulator.interactions import InteractionCoordinator
from socialsimullm.utils.config import load_experiment_config
from socialsimullm.utils.logger import LogConfig, StructuredLogger
from socialsimullm.world.path_planner import MovementIntent, PlannedPath


class _Agent:
    def __init__(self, name: str = "Alice") -> None:
        self.name = name
        self.description = "A deterministic test agent"
        self.location = "Lab"
        self.daily_plans = "Measure the system"
        self.hourly_plan = "Record the next value"
        self.impression = "Stable"
        self.action = "Observe"
        self.action_detail = SimpleNamespace(action="Observe", action_type="task")
        self.recent_actions = ["seed", "observe"]
        self.reflection = "Patterns remain stable"
        self.related_things = "prior observation"
        self.event = "Timed notice"
        self.place_ratings = [("Lab", 9, "reliable")]
        self.goals = []
        self.planned_path = PlannedPath(
            agent_name=name,
            origin="Lab",
            destination="Archive",
            path=["Lab", "Archive"],
            total_distance=1.0,
            steps_remaining=1,
            intent=MovementIntent("Archive", "Store results", 0.8),
        )


def _checkpoint_state(run_dir: Path, round_number: int = 2):
    return SimpleNamespace(
        global_time="Day 1, 08:10",
        round=round_number,
        agents=[_Agent()],
        world_graph=None,
        memory=None,
        project_folder=str(run_dir),
        meta_data={
            "project_name": "resume-test",
            "global_time": "Day 1, 08:10",
            "round": round_number - 1,
        },
        events=["Permanent notice"],
        timed_events=[{"id": "notice", "start_step": 1, "end_step": 3}],
        active_event_ids=["notice"],
    )


def _prepare_run(run_dir: Path) -> None:
    (run_dir / "agent_data").mkdir(parents=True)
    (run_dir / "town_data.json").write_text(
        json.dumps({"value": 7}), encoding="utf-8"
    )
    (run_dir / "agent_data" / "Alice_memory.json").write_text(
        json.dumps({"memory": [{"content": "checkpoint"}]}), encoding="utf-8"
    )
    (run_dir / "meta.json").write_text("{}", encoding="utf-8")
    (run_dir / "events.jsonl").write_text(
        json.dumps({"step": 1, "event_type": "action"}) + "\n",
        encoding="utf-8",
    )
    (run_dir / "simulation_log.txt").write_text("checkpoint log\n", encoding="utf-8")


def test_checkpoint_saves_full_files_and_runtime_state(tmp_path) -> None:
    _prepare_run(tmp_path)
    logger = StructuredLogger(
        str(tmp_path),
        LogConfig(log_to_file=False, log_to_jsonl=False, print_to_console=False),
    )
    reflection = SimpleNamespace(
        _last_reflection_cache={"Alice": "Day 1, 08:00"},
        _last_reflection_step={"Alice": 1},
    )
    interactions = InteractionCoordinator(max_consecutive_steps=3, cooldown_steps=2)
    interactions._record_participation("Alice", 2)
    logger.add_summary("prefix summary")
    logger.bind_runtime(
        reflection_engine=reflection,
        interaction_coordinator=interactions,
    )

    logger.save_checkpoint(_checkpoint_state(tmp_path), step=2)

    checkpoint = tmp_path / "checkpoints" / "step_2"
    runtime = json.loads((checkpoint / "runtime_state.json").read_text(encoding="utf-8"))
    meta = json.loads((checkpoint / "meta.json").read_text(encoding="utf-8"))
    assert (checkpoint / "town_data.json").is_file()
    assert (checkpoint / "agent_data" / "Alice_memory.json").is_file()
    assert runtime["active_event_ids"] == ["notice"]
    assert runtime["agents"]["Alice"]["recent_actions"] == ["seed", "observe"]
    assert runtime["agents"]["Alice"]["planned_path"]["destination"] == "Archive"
    assert runtime["reflection"]["last_reflection_step"] == {"Alice": 1}
    assert runtime["interactions"]["participation"]["Alice"]["last_step"] == 2
    assert runtime["logger"]["summary_buffer"] == ["prefix summary"]
    assert meta["round"] == 2
    assert meta["global_time"] == "Day 1, 08:20"


def test_restore_archives_tail_restores_snapshot_and_preserves_config(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "runs" / "project" / "resume-test"
    _prepare_run(run_dir)
    config_path = run_dir / "config.yaml"
    config_path.write_text("immutable: true\n", encoding="utf-8")
    logger = StructuredLogger(str(run_dir), LogConfig(print_to_console=False))
    logger.save_checkpoint(_checkpoint_state(run_dir), step=2)

    (run_dir / "town_data.json").write_text('{"value": 999}', encoding="utf-8")
    (run_dir / "agent_data" / "Alice_memory.json").write_text(
        '{"memory": [{"content": "tail"}]}', encoding="utf-8"
    )
    (run_dir / "events.jsonl").write_text('{"step": 99}\n', encoding="utf-8")
    (run_dir / "done.flag").write_text("wrong", encoding="utf-8")

    restored = restore_checkpoint("resume-test", step=2, project="project")

    assert restored["step"] == 2
    assert json.loads((run_dir / "town_data.json").read_text(encoding="utf-8"))["value"] == 7
    assert "checkpoint" in (run_dir / "agent_data" / "Alice_memory.json").read_text(encoding="utf-8")
    assert '"step": 1' in (run_dir / "events.jsonl").read_text(encoding="utf-8")
    assert not (run_dir / "done.flag").exists()
    assert config_path.read_text(encoding="utf-8") == "immutable: true\n"
    assert list_experiments(project="project")[0]["resumed_from_step"] == 2
    archives = list((run_dir / "resume_archive").iterdir())
    assert len(archives) == 1
    assert (archives[0] / "events.jsonl").read_text(encoding="utf-8") == '{"step": 99}\n'


def test_resume_cli_accepts_latest_or_explicit_step() -> None:
    command, latest = load_experiment_config(
        ["resume", "--config", "experiment.yaml"]
    )
    _, explicit = load_experiment_config(
        ["resume", "--config", "experiment.yaml", "--step", "12"]
    )

    assert command == "resume"
    assert latest.step == "latest"
    assert explicit.step == "12"


def test_runner_resume_matches_uninterrupted_deterministic_run(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "source-town.json"
    source.write_text(
        json.dumps(
            {
                "general": {"memory_limit": 1},
                "town_people": {},
                "town_areas": {"Lab": "A lab"},
                "value": 0,
            }
        ),
        encoding="utf-8",
    )

    import socialsimullm.simulator.core as core_module
    import socialsimullm.utils.config as config_module

    monkeypatch.setattr(core_module, "SimulatorCore", _DeterministicCore)
    monkeypatch.setattr(config_module, "validate_config", lambda _config: None)

    continuous = ExperimentConfig(
        experiment_id="continuous",
        project="project",
        simulation_steps=5,
        checkpoint_interval=2,
        spatial_graph_path=str(source),
    )
    partial = continuous.model_copy(
        update={"experiment_id": "resumed", "simulation_steps": 2}
    )
    target = partial.model_copy(update={"simulation_steps": 5})
    runner = ExperimentRunner()

    runner.run_single(continuous)
    runner.run_single(partial)
    config_snapshot = tmp_path / "runs" / "project" / "resumed" / "config.yaml"
    original_config = config_snapshot.read_bytes()
    # A checkpoint already at the requested total must finalize without
    # entering SimulatorCore.run(0), whose real implementation is interactive.
    runner.resume_single(partial)
    runner.resume_single(target)

    continuous_meta = json.loads(
        (tmp_path / "runs" / "project" / "continuous" / "meta.json").read_text(encoding="utf-8")
    )
    resumed_meta = json.loads(
        (tmp_path / "runs" / "project" / "resumed" / "meta.json").read_text(encoding="utf-8")
    )
    assert resumed_meta["round"] == continuous_meta["round"] == 5
    assert resumed_meta["value"] == continuous_meta["value"]
    assert config_snapshot.read_bytes() == original_config
    run_metadata = json.loads(
        (tmp_path / "runs" / "project" / "resumed" / "run_metadata.json").read_text(
            encoding="utf-8"
        )
    )
    assert run_metadata["status"] == "completed"
    assert run_metadata["finished_at"]
    assert run_metadata["prompt_template_version"]
    assert run_metadata["resume_history"][-1]["from_step"] == 2
    assert "prompt_meta" not in run_metadata["config_summary"]


class _DeterministicCore:
    """Pure offline core substitute used to verify runner resume semantics."""

    def __init__(self, config, initial_event=None, spatial_config=None) -> None:
        self.config = config
        self.project_folder = config.project_name
        self.logger = None
        self.state = None
        self.reflection_engine = SimpleNamespace(
            _last_reflection_cache={}, _last_reflection_step={}
        )
        self.interaction_coordinator = InteractionCoordinator()

    def initialize(self) -> None:
        run_dir = Path(self.project_folder)
        meta_path = run_dir / "meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        town = json.loads((run_dir / "town_data.json").read_text(encoding="utf-8"))
        current_round = int(meta.get("round", 0))
        self.state = SimpleNamespace(
            global_time=meta.get("global_time", "Day 1, 08:00"),
            round=current_round,
            agents=[_Agent()],
            world_graph=None,
            memory=None,
            project_folder=str(run_dir),
            meta_data={
                "project_name": run_dir.name,
                "global_time": meta.get("global_time", "Day 1, 08:00"),
                "round": current_round,
                "value": int(meta.get("value", town.get("value", 0))),
            },
            events=[],
            timed_events=[],
            active_event_ids=[],
        )
        self.logger = StructuredLogger(
            str(run_dir), LogConfig(print_to_console=False)
        )

    def run(self, max_steps: int = 0) -> None:
        assert self.state is not None and self.logger is not None
        assert max_steps > 0, "resume must not enter the interactive run(0) branch"
        for _ in range(max_steps):
            self.state.round += 1
            self.state.meta_data["value"] = (
                self.state.meta_data["value"] * 2 + self.state.round
            )
            self.state.meta_data["round"] = self.state.round
            self.state.meta_data["global_time"] = f"Step {self.state.round}"
            (Path(self.project_folder) / "meta.json").write_text(
                json.dumps(self.state.meta_data), encoding="utf-8"
            )
            if self.state.round % self.config.checkpoint_interval == 0:
                self.logger.save_checkpoint(self.state, self.state.round)
        self.logger.finalize()
