# socialsimullm/agents/reflection.py

# -*- coding: utf-8 -*-

"""
Standalone reflection engine for social simulation agents.

Generates multi-level reflections following the Generative Agents
paper (Park et al. 2023). Supports daily, pattern, and social
reflection types with configurable triggers.

@author: Huang Miaosen
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

# Late import to avoid circular dependency
def _memory_entry():
    from socialsimullm.agents.memory_entry import MemoryEntry
    return MemoryEntry


class ReflectionType(Enum):
    """Extensible reflection types."""
    DAILY = "daily"
    PATTERN = "pattern"
    SOCIAL = "social"


@dataclass(frozen=True)
class ReflectionConfig:
    """Configuration for reflection behavior.

    Immutable -- create a new instance to change settings.
    """
    threshold_importance: int = 15
    threshold_min_observations: int = 3
    reflection_token_limit: int = 500
    min_cooldown_steps: int = 6
    daily_priority: int = 9
    pattern_priority: int = 8
    social_priority: int = 9
    include_in_planning: bool = True


# --- Protocols for loose coupling ---

class MemoryProvider(Protocol):
    """Protocol that AgentMemory fulfills."""

    def recall_by_importance(self, agent_name: str, global_time: str, min_importance: int = 7) -> list[dict]: ...
    def recall_reflections(self, agent_name: str, n: int = 3) -> list[dict]: ...
    def recall_time_span(self, agent_name: str, start: str, end: str) -> list[dict]: ...
    def recall_recent(self, agent_name: str, n: int = 10) -> list[dict]: ...
    def format_recent(self, agent_name: str, n: int) -> str: ...
    def format_by_importance(self, agent_name: str, global_time: str) -> str: ...
    def format_reflections(self, agent_name: str, n: int = 3) -> str: ...


class AgentData(Protocol):
    """Protocol for agent data needed by reflection."""

    name: str
    description: str
    daily_plans: str
    reflection: str


class ReflectionEngine:
    """Standalone reflection engine.

    Generates reflections for agents based on their memory contents.
    Supports scheduled (end-of-day) and threshold-based (mid-day)
    triggering, with multiple reflection types.

    Usage::

        engine = ReflectionEngine(config, memory, prompt_meta)
        observations = engine.run_reflection_cycle(agent, global_time, all_agents)
    """

    def __init__(
        self,
        config: ReflectionConfig,
        memory: MemoryProvider,
        prompt_meta: str,
    ) -> None:
        self._config = config
        self._memory = memory
        self._prompt_meta = prompt_meta
        self._last_reflection_cache: dict[str, str | None] = {}
        self._last_reflection_step: dict[str, int] = {}

    # --- Public API ---

    def should_reflect(self, agent_name: str, global_time: str, current_step: int = 0) -> bool:
        """Check if cumulative importance of un-reflected observations exceeds threshold.

        Args:
            agent_name: Name of the agent to check.
            global_time: Current simulation time string.
            current_step: Current simulation round number (for cooldown check).

        Returns:
            True if a mid-day reflection should be triggered.
        """
        last_step = self._last_reflection_step.get(agent_name, 0)
        if current_step - last_step < self._config.min_cooldown_steps:
            return False
        last_time = self._get_last_reflection_time(agent_name)
        observations = self._get_unreflected_observations(agent_name, last_time)
        if len(observations) < self._config.threshold_min_observations:
            return False
        non_reflection_obs = [
            o for o in observations
            if getattr(o, "event_type", None) != "reflection"
        ]
        if len(non_reflection_obs) < self._config.threshold_min_observations:
            return False
        cumulative = self._calculate_cumulative_importance(non_reflection_obs)
        return cumulative >= self._config.threshold_importance

    def reflect_daily(self, agent: AgentData, global_time: str) -> MemoryEntry:
        """Generate a daily summary reflection for an agent.

        Retrieves high-importance observations and past reflections,
        then asks the LLM to synthesize a high-level reflection.

        Args:
            agent: Agent data object.
            global_time: Current simulation time string.

        Returns:
            An observation dict ready for memory.store().
        """
        from socialsimullm.prompt_templates.template_agents import (
            daily_reflection_prompt,
            daily_reflection_system,
        )

        important = self._memory.format_by_importance(agent.name, global_time)
        past_reflections = self._format_past_reflections(agent.name)

        system = daily_reflection_system.format(
            name=agent.name,
            description=agent.description,
            past_reflections=past_reflections or "No previous reflections.",
            daily_plans=agent.daily_plans,
        )
        prompt = daily_reflection_prompt.format(
            important_observations=important or "Nothing notable happened today.",
        )
        from socialsimullm.utils.text_generation import GPT_request, GPT_request_json, deepseek_v4_marker
        from socialsimullm.prompt_templates.template_agents import JSON_REFLECTION_SUFFIX
        result = GPT_request_json(
            system + JSON_REFLECTION_SUFFIX,
            prompt,
            gpt_parameter={"max_tokens": self._config.reflection_token_limit},
            required_keys=["reflection"],
            fallback={"reflection": "Nothing notable happened."},
            thinking_mode="role_immersion",
        )
        reflection_text = result.get("reflection", "")
        self._last_reflection_cache[agent.name] = global_time
        return self._build_observation_dict(
            agent.name, global_time, reflection_text, ReflectionType.DAILY,
        )

    def reflect_pattern(self, agent: AgentData, global_time: str) -> MemoryEntry | None:
        """Generate a pattern reflection across multiple days.

        Only triggered when >= 2 prior daily reflections exist.
        Identifies recurring behavioral themes.

        Args:
            agent: Agent data object.
            global_time: Current simulation time string.

        Returns:
            An observation dict, or None if insufficient history.
        """
        from socialsimullm.prompt_templates.template_agents import (
            pattern_reflection_prompt,
            pattern_reflection_system,
        )

        reflections = self._memory.recall_reflections(agent.name, n=10)
        daily_reflections = [
            r for r in reflections
            if r.reflection_type == "daily"
        ]
        if len(daily_reflections) < 2:
            return None

        all_ref_text = "\n".join(
            f"- [{r.timestamp}] {r.summary or r.content}"
            for r in daily_reflections
        )

        system = pattern_reflection_system.format(
            name=agent.name,
            description=agent.description,
            all_reflections=all_ref_text,
        )
        prompt = pattern_reflection_prompt.format()

        from socialsimullm.utils.text_generation import GPT_request, GPT_request_json, deepseek_v4_marker
        from socialsimullm.prompt_templates.template_agents import JSON_REFLECTION_SUFFIX
        result = GPT_request_json(
            system + JSON_REFLECTION_SUFFIX,
            prompt,
            gpt_parameter={"max_tokens": 300},
            required_keys=["reflection"],
            fallback={"reflection": "No clear pattern identified."},
            thinking_mode="role_immersion",
        )
        reflection_text = result.get("reflection", "")
        return self._build_observation_dict(
            agent.name, global_time, reflection_text, ReflectionType.PATTERN,
        )

    def reflect_social(
        self,
        agent: AgentData,
        global_time: str,
        all_agents: list[AgentData],
    ) -> MemoryEntry | None:
        """Generate a social reflection about relationships.

        Analyzes interaction patterns with other agents.

        Args:
            agent: Agent data object.
            global_time: Current simulation time string.
            all_agents: All agents in the simulation.

        Returns:
            An observation dict, or None if insufficient social data.
        """
        from socialsimullm.prompt_templates.template_agents import (
            social_reflection_prompt,
            social_reflection_system,
        )

        interactions = self._get_interacting_agents(agent.name, n_days=2)
        if not interactions:
            return None

        top_interactions = sorted(interactions.items(), key=lambda x: -x[1])[:5]
        interaction_lines = [
            f"- {name}: {count} interactions"
            for name, count in top_interactions
        ]
        interaction_summary = "\n".join(interaction_lines)

        past_reflections = self._format_past_reflections(agent.name)

        system = social_reflection_system.format(
            name=agent.name,
            description=agent.description,
            past_reflections=past_reflections or "No previous reflections.",
        )
        prompt = social_reflection_prompt.format(
            interaction_summary=interaction_summary,
        )

        from socialsimullm.utils.text_generation import GPT_request, GPT_request_json, deepseek_v4_marker
        from socialsimullm.prompt_templates.template_agents import JSON_REFLECTION_SUFFIX
        result = GPT_request_json(
            system + JSON_REFLECTION_SUFFIX,
            prompt,
            gpt_parameter={"max_tokens": 300},
            required_keys=["reflection"],
            fallback={"reflection": "No social observations yet."},
            thinking_mode="role_immersion",
        )
        reflection_text = result.get("reflection", "")
        return self._build_observation_dict(
            agent.name, global_time, reflection_text, ReflectionType.SOCIAL,
        )

    def run_reflection_cycle(
        self,
        agent: AgentData,
        global_time: str,
        all_agents: list[AgentData],
    ) -> list[MemoryEntry]:
        """Run the complete reflection cycle for one agent.

        Generates daily reflection always, and conditionally generates
        pattern and social reflections based on available history.

        Args:
            agent: Agent data object.
            global_time: Current simulation time string.
            all_agents: All agents in the simulation.

        Returns:
            List of MemoryEntry objects ready for memory.store().
        """
        results: list[dict] = []

        daily = self.reflect_daily(agent, global_time)
        results.append(daily)

        pattern = self.reflect_pattern(agent, global_time)
        if pattern is not None:
            results.append(pattern)

        social = self.reflect_social(agent, global_time, all_agents)
        if social is not None:
            results.append(social)

        return results

    # --- Private helpers ---

    def _get_last_reflection_time(self, agent_name: str) -> str | None:
        """Get the global_time of the agent's most recent reflection.

        Uses cache to avoid repeated file reads within a simulation run.
        """
        if agent_name in self._last_reflection_cache:
            return self._last_reflection_cache[agent_name]

        reflections = self._memory.recall_reflections(agent_name, n=1)
        last_time: str | None = None
        if reflections:
            last_time = reflections[-1].timestamp
        self._last_reflection_cache[agent_name] = last_time
        return last_time

    def _get_unreflected_observations(
        self,
        agent_name: str,
        since_time: str | None,
    ) -> list:
        """Get all observations since the last reflection."""
        if since_time is None:
            return self._memory.recall_recent(agent_name, n=50)

        return self._memory.recall_time_span(
            agent_name, since_time, "Day 99999, 23:59",
        )

    @staticmethod
    def _calculate_cumulative_importance(observations: list) -> int:
        """Sum the importance values of the given observations."""
        return sum(m.importance for m in observations)

    def _format_past_reflections(self, agent_name: str) -> str:
        """Format the agent's existing reflections as a string for prompts."""
        return self._memory.format_reflections(agent_name, n=3)

    def _get_interacting_agents(
        self,
        agent_name: str,
        n_days: int = 2,
    ) -> dict[str, int]:
        """Count interactions with other agents over recent days.

        Returns:
            Dict mapping agent_name -> interaction_count.
        """
        day_count = self._count_current_day(agent_name) or 1
        start_day = max(1, (day_count - n_days) + 1)
        start_time = f"Day {start_day}, 00:00"
        end_time = f"Day {day_count + 1}, 23:59"

        observations = self._memory.recall_time_span(
            agent_name, start_time, end_time,
        )

        interaction_counts: dict[str, int] = {}
        for entry in observations:
            for name in entry.entities:
                if name != agent_name and name:
                    interaction_counts[name] = interaction_counts.get(name, 0) + 1

        return interaction_counts

    def _count_current_day(self, agent_name: str) -> int | None:
        """Extract the current day number from the agent's most recent memory."""
        recent = self._memory.recall_recent(agent_name, n=1)
        if not recent:
            return None
        time_str = recent[-1].timestamp
        try:
            return int(time_str.split(",")[0].replace("Day ", "").strip())
        except (ValueError, IndexError):
            return None

    def _build_observation_dict(
        self,
        agent_name: str,
        global_time: str,
        reflection_text: str,
        reflection_type: ReflectionType,
    ) -> MemoryEntry:
        """Build a MemoryEntry from reflection output."""
        priority_map = {
            ReflectionType.DAILY: self._config.daily_priority,
            ReflectionType.PATTERN: self._config.pattern_priority,
            ReflectionType.SOCIAL: self._config.social_priority,
        }
        return _memory_entry().create(
            agent_name=agent_name,
            timestamp=global_time,
            location_id="",
            event_type="reflection",
            content=f'In {global_time}, {agent_name} reflected ({reflection_type.value}): "{reflection_text}".',
            summary=f"{agent_name} reflected: {reflection_text}",
            importance=priority_map[reflection_type],
            reflection_type=reflection_type.value,
        )
