import json

import pytest
from pydantic import ValidationError

from socialsimullm.experiment.config import ExperimentConfig, TimedEventConfig
from socialsimullm.simulator.core import SimulatorCore
from socialsimullm.simulator.state import SimulationState
from socialsimullm.utils.config import SimulationConfig
from socialsimullm.utils.logger import LogConfig, StructuredLogger


class _Agent:
    def __init__(self, name: str, location: str) -> None:
        self.name = name
        self.description = ""
        self.location = location
        self.daily_plans = ""
        self.hourly_plan = ""
        self.impression = ""
        self.action = ""
        self.reflection = ""
        self.related_things = ""
        self.event = ""
        self.place_ratings: list = []


class _Logger:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def log_event(
        self,
        event_type: str,
        step: int,
        agent_id: str = "",
        data: dict | None = None,
    ) -> None:
        self.events.append(
            {
                "event_type": event_type,
                "step": step,
                "agent_id": agent_id,
                "data": data or {},
            }
        )


class _EventMemory:
    def __init__(self) -> None:
        self.saved: list = []

    def load_events(self) -> dict:
        return {"event": [{"action": "A legacy stored event."}]}

    def store(self, entry) -> None:
        self.saved.append(entry)

    def save_event(self, entry: dict) -> dict:
        return {"event": [*self.load_events()["event"], entry]}


def _state(*events: TimedEventConfig) -> SimulationState:
    return SimulationState(
        global_time="Day 1, 08:00",
        round=0,
        agents=[_Agent("Alice", "Market"), _Agent("Bob", "Library")],
        locations=None,
        world_graph=None,
        memory=None,
        project_folder="",
        meta_data={},
        town_areas={},
        events=["A permanent town notice."],
        timed_events=list(events),
    )


def _core() -> tuple[SimulatorCore, _Logger]:
    core = SimulatorCore(SimulationConfig(project_name="test"))
    logger = _Logger()
    core.logger = logger  # type: ignore[assignment]
    return core, logger


def test_config_accepts_legacy_and_timed_events() -> None:
    config = ExperimentConfig(
        events=[
            "A permanent town notice.",
            {
                "id": "market-rain",
                "content": "Rain closes the market.",
                "start_step": 2,
                "end_step": 4,
                "locations": ["Market"],
                "importance": 8,
            },
        ]
    )

    assert config.events[0] == "A permanent town notice."
    assert isinstance(config.events[1], TimedEventConfig)
    assert config.get_event_string() == "A permanent town notice."
    assert config.to_simulation_config().timed_events == [config.events[1]]


def test_timed_event_rejects_an_end_before_its_start() -> None:
    with pytest.raises(ValidationError):
        TimedEventConfig(
            id="invalid",
            content="Invalid window.",
            start_step=5,
            end_step=4,
        )


def test_legacy_event_storage_reads_old_and_current_memory_fields() -> None:
    core, _ = _core()
    memory = _EventMemory()

    events = core._load_events(
        memory,  # type: ignore[arg-type]
        "Day 1, 08:00",
        new_event="A newly configured permanent event.",
    )

    assert events[0] == "A legacy stored event."
    assert "A newly configured permanent event." in events[1]
    assert len(memory.saved) == 1


def test_timed_event_lifecycle_refreshes_agents_and_logs_once() -> None:
    event = TimedEventConfig(
        id="market-rain",
        content="Rain closes the market.",
        start_step=2,
        end_step=3,
        locations=["Market"],
        importance=8,
    )
    state = _state(event)
    core, logger = _core()

    state.round = 1
    core._update_timed_events(state)
    assert state.active_event_ids == []
    assert state.agents[0].event == "A permanent town notice."

    state.round = 2
    core._update_timed_events(state)
    assert state.active_event_ids == ["market-rain"]
    assert "Rain closes the market." in state.agents[0].event
    assert "Rain closes the market." not in state.agents[1].event

    state.round = 3
    core._update_timed_events(state)
    assert state.active_event_ids == ["market-rain"]

    state.round = 4
    core._update_timed_events(state)
    assert state.active_event_ids == []
    assert "Rain closes the market." not in state.agents[0].event
    assert state.meta_data["active_event_ids"] == []

    assert [entry["event_type"] for entry in logger.events] == [
        "global_event_started",
        "global_event_ended",
    ]
    assert [entry["step"] for entry in logger.events] == [2, 4]
    assert logger.events[0]["data"]["event_id"] == "market-rain"


def test_checkpoint_meta_contains_active_event_ids(tmp_path) -> None:
    event = TimedEventConfig(
        id="festival",
        content="The festival is open.",
        start_step=1,
        end_step=2,
    )
    state = _state(event)
    core, _ = _core()
    state.round = 1
    core._update_timed_events(state)

    logger = StructuredLogger(
        str(tmp_path),
        LogConfig(log_to_file=False, log_to_jsonl=False, print_to_console=False),
    )
    logger.save_checkpoint(state, step=1)

    checkpoint_meta = json.loads(
        (tmp_path / "checkpoints" / "step_1" / "meta.json").read_text(
            encoding="utf-8"
        )
    )
    assert checkpoint_meta["active_event_ids"] == ["festival"]
