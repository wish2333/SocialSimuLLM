"""Non-blocking coordination for structured agent conversation turns."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from typing import Any, Iterable, Protocol

from socialsimullm.agents.agent import AgentAction
from socialsimullm.agents.memory_entry import MemoryEntry


class _AgentLike(Protocol):
    name: str
    location: str


class _MemoryStore(Protocol):
    def store(self, entry: MemoryEntry) -> None: ...


@dataclass(frozen=True)
class InteractionResult:
    """One coordination result ready for core logging and normal action flow."""

    action: AgentAction
    accepted: bool
    reason: str = ""
    event_type: str | None = None
    event_data: dict[str, Any] = field(default_factory=dict)
    routed_memory: MemoryEntry | None = None


@dataclass
class _ParticipationState:
    last_step: int | None = None
    consecutive_steps: int = 0
    cooldown_start: int | None = None
    cooldown_end: int | None = None


@dataclass
class _ConversationSession:
    conversation_id: str
    last_step: int


class InteractionCoordinator:
    """Validate and route at most one conversation turn per main action.

    The coordinator never calls an LLM and never loops over reply turns. A
    target receives the utterance as memory and can respond during its own
    normal main action call in the current or next simulation step.
    """

    def __init__(
        self,
        max_consecutive_steps: int = 3,
        cooldown_steps: int = 2,
    ) -> None:
        if max_consecutive_steps < 1:
            raise ValueError("max_consecutive_steps must be at least 1")
        if cooldown_steps < 0:
            raise ValueError("cooldown_steps must be non-negative")
        self.max_consecutive_steps = max_consecutive_steps
        self.cooldown_steps = cooldown_steps
        self._participation: dict[str, _ParticipationState] = {}
        self._sessions: dict[tuple[str, str], _ConversationSession] = {}

    def coordinate(
        self,
        *,
        actor: _AgentLike,
        action: AgentAction,
        all_agents: Iterable[_AgentLike],
        step: int,
        global_time: str,
        memory: _MemoryStore,
        visible_agent_names: set[str] | None = None,
    ) -> InteractionResult:
        """Validate one structured action and route one accepted utterance."""

        if action.action_type != "talk":
            return InteractionResult(action=action, accepted=False, reason="not_talk")

        agents_by_name = {agent.name: agent for agent in all_agents}
        target = agents_by_name.get(action.target)
        if not action.target:
            return self._reject(actor, action, "target_missing")
        if target is None:
            return self._reject(actor, action, "target_not_found")
        if target.name == actor.name:
            return self._reject(actor, action, "self_target")
        if target.location != actor.location:
            return self._reject(actor, action, "target_not_co_located")
        if visible_agent_names is not None and target.name not in visible_agent_names:
            return self._reject(actor, action, "target_not_visible")
        if not action.utterance:
            return self._reject(actor, action, "utterance_missing")
        if self._in_cooldown(actor.name, step) or self._in_cooldown(target.name, step):
            return self._reject(actor, action, "conversation_cooldown")

        pair = tuple(sorted((actor.name, target.name)))
        session = self._sessions.get(pair)
        if session is None or step > session.last_step + 1:
            session = _ConversationSession(
                conversation_id=str(
                    uuid.uuid5(uuid.NAMESPACE_URL, f"socialsimullm:{pair[0]}:{pair[1]}:{step}")
                ),
                last_step=step,
            )
            self._sessions[pair] = session
        else:
            session.last_step = max(session.last_step, step)

        self._record_participation(actor.name, step)
        self._record_participation(target.name, step)

        event_data = {
            "speaker": actor.name,
            "target": target.name,
            "utterance": action.utterance,
            "conversation_id": session.conversation_id,
            "continues_task": action.continues_task,
            "action": action.action,
        }
        routed_memory = MemoryEntry.create(
            agent_name=target.name,
            timestamp=global_time,
            location_id=target.location,
            # AgentMemory already routes importance-4 thoughts to the target's
            # next impression context. The structured subtype stays explicit.
            event_type="thought",
            content=f'{actor.name} said: "{action.utterance}"',
            summary=f'{actor.name} said: "{action.utterance}"',
            entities=[actor.name, target.name],
            importance=4,
            metadata={
                "interaction_type": "conversation_turn",
                "conversation_id": session.conversation_id,
                "speaker": actor.name,
                "target": target.name,
                "continues_task": action.continues_task,
            },
        )
        memory.store(routed_memory)
        return InteractionResult(
            action=action,
            accepted=True,
            event_type="conversation_turn",
            event_data=event_data,
            routed_memory=routed_memory,
        )

    def prompt_guidance(self, agent_name: str, step: int) -> str:
        """Return concise policy text to append to the agent's main prompt."""

        state = self._participation.get(agent_name)
        if state is not None and self._in_cooldown(agent_name, step):
            return (
                f"Conversation cooldown is active through step {state.cooldown_end}; "
                "do not use talk. Prioritize task, move, or idle."
            )

        current_streak = 0
        if state is not None and state.last_step in {step, step - 1}:
            current_streak = state.consecutive_steps
        remaining = max(self.max_consecutive_steps - current_streak, 0)
        return (
            f"At most {remaining} consecutive conversation step(s) remain. "
            "Use continues_task=true when speaking while still progressing a task."
        )

    def _reject(
        self,
        actor: _AgentLike,
        action: AgentAction,
        reason: str,
    ) -> InteractionResult:
        downgraded = replace(
            action,
            action_type="task",
            target="",
            utterance="",
            continues_task=False,
        )
        return InteractionResult(
            action=downgraded,
            accepted=False,
            reason=reason,
            event_type="conversation_rejected",
            event_data={
                "speaker": actor.name,
                "target": action.target,
                "utterance": action.utterance,
                "action": action.action,
                "reason": reason,
            },
        )

    def _in_cooldown(self, agent_name: str, step: int) -> bool:
        state = self._participation.get(agent_name)
        return bool(
            state is not None
            and state.cooldown_start is not None
            and state.cooldown_end is not None
            and state.cooldown_start <= step <= state.cooldown_end
        )

    def _record_participation(self, agent_name: str, step: int) -> None:
        state = self._participation.setdefault(agent_name, _ParticipationState())
        if state.last_step == step:
            return
        if state.last_step == step - 1:
            state.consecutive_steps += 1
        else:
            state.consecutive_steps = 1
        state.last_step = step

        if state.consecutive_steps >= self.max_consecutive_steps and self.cooldown_steps:
            state.cooldown_start = step + 1
            state.cooldown_end = step + self.cooldown_steps
