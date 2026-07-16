from __future__ import annotations

from types import SimpleNamespace

import networkx as nx
import pytest

from socialsimullm.agents.agent import Agent, AgentAction
from socialsimullm.experiment.config import ExperimentConfig
from socialsimullm.prompt_templates.template_agents import JSON_ACTION_SUFFIX
from socialsimullm.simulator.core import SimulatorCore
from socialsimullm.simulator.interactions import InteractionCoordinator
from socialsimullm.utils.config import SimulationConfig


class RecordingMemory:
    def __init__(self) -> None:
        self.entries = []

    def store(self, entry) -> None:
        self.entries.append(entry)


def _agent(name: str, location: str = "Square") -> SimpleNamespace:
    return SimpleNamespace(name=name, location=location)


def _talk(target: str = "Bob", utterance: str = "Hello") -> AgentAction:
    return AgentAction(
        action="Greet Bob while arranging the counter.",
        action_type="talk",
        target=target,
        utterance=utterance,
        continues_task=True,
    )


def test_agent_action_keeps_legacy_action_only_response_compatible() -> None:
    action = AgentAction.from_response({"action": "Arrange the counter."})

    assert action.action == "Arrange the counter."
    assert action.action_type == "task"
    assert action.target == ""
    assert action.utterance == ""
    assert action.continues_task is False


def test_agent_action_safely_normalizes_unknown_optional_values() -> None:
    action = AgentAction.from_response(
        {
            "action": 7,
            "action_type": "unsupported",
            "target": None,
            "utterance": ["not", "text"],
            "continues_task": "false",
        }
    )

    assert action == AgentAction(action="7")


def test_agent_execute_action_preserves_string_api_and_structured_fields(monkeypatch) -> None:
    graph = nx.Graph()
    graph.add_node("Square")
    agent = Agent("Alice", "Merchant", "Square", graph)
    agent.hourly_action_prompt = "At the square at {}."

    monkeypatch.setattr(
        "socialsimullm.agents.agent.GPT_request_json",
        lambda *args, **kwargs: {
            "action": "Talk to Bob while sorting goods.",
            "action_type": "talk",
            "target": "Bob",
            "utterance": "Good morning.",
            "continues_task": True,
        },
    )

    result = agent.execute_action("Day 1, 09:00", "", "", "")

    assert result == "Talk to Bob while sorting goods."
    assert agent.action_detail == AgentAction(
        action="Talk to Bob while sorting goods.",
        action_type="talk",
        target="Bob",
        utterance="Good morning.",
        continues_task=True,
    )
    assert agent.recent_actions[-1] == result
    assert all(field in JSON_ACTION_SUFFIX for field in ("action_type", "target", "utterance", "continues_task"))


def test_valid_talk_creates_turn_event_and_routes_one_target_memory() -> None:
    alice = _agent("Alice")
    bob = _agent("Bob")
    memory = RecordingMemory()
    coordinator = InteractionCoordinator(max_consecutive_steps=3, cooldown_steps=2)

    result = coordinator.coordinate(
        actor=alice,
        action=_talk(),
        all_agents=[alice, bob],
        step=1,
        global_time="Day 1, 09:00",
        memory=memory,
        visible_agent_names={"Bob"},
    )

    assert result.accepted is True
    assert result.event_type == "conversation_turn"
    assert result.event_data["speaker"] == "Alice"
    assert result.event_data["target"] == "Bob"
    assert result.event_data["utterance"] == "Hello"
    assert result.event_data["conversation_id"]
    assert result.event_data["continues_task"] is True
    assert len(memory.entries) == 1
    assert memory.entries[0].agent_name == "Bob"
    assert memory.entries[0].event_type == "thought"
    assert memory.entries[0].importance == 4
    assert memory.entries[0].metadata["interaction_type"] == "conversation_turn"
    assert memory.entries[0].metadata["conversation_id"] == result.event_data["conversation_id"]


def test_invalid_location_downgrades_to_task_and_records_reason() -> None:
    alice = _agent("Alice", "Square")
    bob = _agent("Bob", "Inn")
    memory = RecordingMemory()
    coordinator = InteractionCoordinator()

    result = coordinator.coordinate(
        actor=alice,
        action=_talk(),
        all_agents=[alice, bob],
        step=1,
        global_time="Day 1, 09:00",
        memory=memory,
    )

    assert result.accepted is False
    assert result.reason == "target_not_co_located"
    assert result.action.action_type == "task"
    assert result.event_type == "conversation_rejected"
    assert result.event_data["reason"] == "target_not_co_located"
    assert memory.entries == []


def test_visibility_is_enforced_when_visible_names_are_supplied() -> None:
    alice = _agent("Alice")
    bob = _agent("Bob")
    coordinator = InteractionCoordinator()

    result = coordinator.coordinate(
        actor=alice,
        action=_talk(),
        all_agents=[alice, bob],
        step=1,
        global_time="Day 1, 09:00",
        memory=RecordingMemory(),
        visible_agent_names=set(),
    )

    assert result.accepted is False
    assert result.reason == "target_not_visible"


@pytest.mark.parametrize(
    ("action", "agents", "reason"),
    [
        (_talk(target=""), [_agent("Alice"), _agent("Bob")], "target_missing"),
        (_talk(target="Carol"), [_agent("Alice"), _agent("Bob")], "target_not_found"),
        (_talk(target="Alice"), [_agent("Alice"), _agent("Bob")], "self_target"),
        (_talk(utterance=""), [_agent("Alice"), _agent("Bob")], "utterance_missing"),
    ],
)
def test_invalid_talk_fields_are_safely_downgraded(action, agents, reason) -> None:
    result = InteractionCoordinator().coordinate(
        actor=agents[0],
        action=action,
        all_agents=agents,
        step=1,
        global_time="Day 1, 09:00",
        memory=RecordingMemory(),
    )

    assert result.accepted is False
    assert result.reason == reason
    assert result.action.action_type == "task"


def test_non_talk_action_passes_through_without_event_or_memory() -> None:
    action = AgentAction(action="Move crates.", action_type="task")
    memory = RecordingMemory()

    result = InteractionCoordinator().coordinate(
        actor=_agent("Alice"),
        action=action,
        all_agents=[_agent("Alice"), _agent("Bob")],
        step=1,
        global_time="Day 1, 09:00",
        memory=memory,
    )

    assert result.action is action
    assert result.reason == "not_talk"
    assert result.event_type is None
    assert memory.entries == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_consecutive_steps": 0},
        {"cooldown_steps": -1},
    ],
)
def test_invalid_coordinator_limits_are_rejected(kwargs) -> None:
    with pytest.raises(ValueError):
        InteractionCoordinator(**kwargs)


def test_pair_reuses_conversation_id_for_both_turns_in_same_step() -> None:
    alice = _agent("Alice")
    bob = _agent("Bob")
    coordinator = InteractionCoordinator(max_consecutive_steps=3, cooldown_steps=2)
    memory = RecordingMemory()

    first = coordinator.coordinate(
        actor=alice,
        action=_talk(),
        all_agents=[alice, bob],
        step=1,
        global_time="Day 1, 09:00",
        memory=memory,
    )
    reply = coordinator.coordinate(
        actor=bob,
        action=_talk(target="Alice", utterance="Morning."),
        all_agents=[alice, bob],
        step=1,
        global_time="Day 1, 09:00",
        memory=memory,
    )

    assert first.event_data["conversation_id"] == reply.event_data["conversation_id"]
    assert len(memory.entries) == 2


def test_consecutive_limit_enforces_two_full_cooldown_steps() -> None:
    alice = _agent("Alice")
    bob = _agent("Bob")
    coordinator = InteractionCoordinator(max_consecutive_steps=3, cooldown_steps=2)
    memory = RecordingMemory()

    accepted = [
        coordinator.coordinate(
            actor=alice,
            action=_talk(),
            all_agents=[alice, bob],
            step=step,
            global_time=f"Day 1, 09:{(step - 1) * 10:02d}",
            memory=memory,
        )
        for step in (1, 2, 3)
    ]
    blocked = [
        coordinator.coordinate(
            actor=alice,
            action=_talk(),
            all_agents=[alice, bob],
            step=step,
            global_time=f"Day 1, 09:{(step - 1) * 10:02d}",
            memory=memory,
        )
        for step in (4, 5)
    ]
    resumed = coordinator.coordinate(
        actor=alice,
        action=_talk(),
        all_agents=[alice, bob],
        step=6,
        global_time="Day 1, 09:50",
        memory=memory,
    )

    assert all(result.accepted for result in accepted)
    assert all(result.reason == "conversation_cooldown" for result in blocked)
    assert "do not use talk" in coordinator.prompt_guidance("Alice", step=4)
    assert resumed.accepted is True
    assert resumed.event_data["conversation_id"] != accepted[-1].event_data["conversation_id"]
    assert len(memory.entries) == 4


def test_conversation_config_is_passed_to_simulation_config() -> None:
    config = ExperimentConfig(
        conversation_max_consecutive_steps=5,
        conversation_cooldown_steps=4,
    )

    simulation = config.to_simulation_config()

    assert simulation.conversation_max_consecutive_steps == 5
    assert simulation.conversation_cooldown_steps == 4


def test_core_coordinates_talk_without_extra_main_action_calls() -> None:
    class Memory(RecordingMemory):
        memory_limit = 10

        def format_impressions(self, *_args) -> str:
            return ""

        def format_recent(self, *_args) -> str:
            return ""

    class Logger:
        def __init__(self) -> None:
            self.events = []

        def log_event(self, event_type, step, agent_id="", data=None) -> None:
            self.events.append((event_type, step, agent_id, data or {}))

        def log_debug(self, _message) -> None:
            pass

        def add_summary(self, _message) -> None:
            pass

    class CoreAgent:
        def __init__(self, name: str, detail: AgentAction) -> None:
            self.name = name
            self.location = "Square"
            self.action_detail = detail
            self.action = detail.action
            self.execute_calls = 0

        def execute_action(self, *_args, **_kwargs) -> str:
            self.execute_calls += 1
            self.action = self.action_detail.action
            return self.action

        def rate_experience(self, *_args) -> int:
            return 2

        def memory_actions(self, *_args):
            return SimpleNamespace(agent_name=self.name, event_type="action")

    alice = CoreAgent("Alice", _talk())
    bob = CoreAgent("Bob", AgentAction(action="Arrange shelves."))
    memory = Memory()
    logger = Logger()
    core = SimulatorCore(SimulationConfig(project_name="test"))
    core.logger = logger  # type: ignore[assignment]
    state = SimpleNamespace(
        agents=[alice, bob],
        memory=memory,
        round=1,
        global_time="Day 1, 09:00",
    )

    core._execute_actions(state, "")

    assert alice.execute_calls == 1
    assert bob.execute_calls == 1
    assert [event[0] for event in logger.events].count("conversation_turn") == 1
    assert [event[0] for event in logger.events].count("action") == 2
    assert any(
        getattr(entry, "agent_name", "") == "Bob"
        and getattr(entry, "metadata", {}).get("interaction_type")
        == "conversation_turn"
        for entry in memory.entries
    )
