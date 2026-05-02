# socialsimullm/cognition/goal.py

# -*- coding: utf-8 -*-

"""
Goal-driven hierarchical planning system.

Provides GoalManager for creating, decomposing, tracking, and
completing agent goals. Goals decompose into sub-goals, enabling
multi-step coordination across simulation hours and days.

@author: Huang Miaosen
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import TYPE_CHECKING, Any

from socialsimullm.utils.text_generation import GPT_request

if TYPE_CHECKING:
    from socialsimullm.agents.agent import Agent
    from socialsimullm.agents.memory_entry import MemoryEntry


class GoalStatus(Enum):
    """Lifecycle status of a goal."""

    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    BLOCKED = "blocked"


@dataclass
class Goal:
    """A persistent agent goal with optional sub-goals.

    Attributes:
        id: Unique UUID.
        description: What the agent wants to achieve.
        status: Current lifecycle status.
        priority: Importance rating (1-9).
        created_at: When the goal was created ("Day X, HH:MM").
        deadline: Optional deadline for time-sensitive goals.
        parent_id: ID of parent goal (for sub-goals).
        sub_goals: Decomposed child goals.
        progress_notes: Agent's notes on progress.
        completion_conditions: What must happen for completion.
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    description: str = ""
    status: GoalStatus = GoalStatus.ACTIVE
    priority: int = 5
    created_at: str = ""
    deadline: str | None = None
    parent_id: str | None = None
    sub_goals: list[Goal] = field(default_factory=list)
    progress_notes: str = ""
    completion_conditions: str = ""


@dataclass(frozen=True)
class GoalConfig:
    """Configuration for goal-driven planning.

    Attributes:
        enabled: Whether goal system is active.
        max_active_goals: Maximum concurrent active goals.
        goal_retention_days: How long completed goals persist (in sim days).
        decomposition_depth: Max nesting level for sub-goals.
    """

    enabled: bool = False
    max_active_goals: int = 3
    goal_retention_days: int = 3
    decomposition_depth: int = 2


GOAL_CREATION_SYSTEM = """You are a goal-setting assistant for {name}.
Description: {description}
Current time: {current_time}
Recent events: {recent_events}

Based on the character's personality and recent experiences,
suggest 1-3 goals they might pursue. Each goal should be specific,
actionable, and reflect the character's motivations.
Format: one goal per line, starting with priority (1-9).
Example:
7: Build a relationship with the teacher by visiting the school
5: Explore the market to find rare herbs
3: Organize a community gathering at the town square"""

GOAL_CREATION_PROMPT = """Given your character and recent experiences, what are your top goals?
Format: [Priority 1-9]: [Goal description]
List at most {max_goals} goals."""

GOAL_REVIEW_SYSTEM = """You are {name}.
Description: {description}
Active goals:
{active_goals}

Recent memories:
{recent_memories}

Review your active goals. For each goal, decide if it should be:
- CONTINUE: Still relevant and in progress
- COMPLETED: The completion conditions are met
- ABANDONED: No longer relevant or impossible
Format: [Goal ID]: [CONTINUE|COMPLETED|ABANDONED]"""

GOAL_DECOMPOSITION_SYSTEM = """You are a task planning assistant.
Goal: {goal_description}
Context: {context}

Break this goal into 2-4 concrete sub-tasks that can be accomplished
within a single simulation day. Each sub-task should have clear
completion conditions.
Format: [Priority 1-9]: [Sub-task description] | Completion: [conditions]
Depth level: {depth}"""

GOAL_CONTEXT_SYSTEM = """You are {name}.
Description: {description}
Your active goals are:
{goals_context}

Consider your goals when planning your day."""

TASK_ORDERING_SYSTEM = """You are a task scheduling assistant.
Given these sub-tasks:
{tasks}

Determine the execution order based on dependencies.
Format: one task per line, in execution order.
Just list the task descriptions, nothing else."""

TASK_IMMEDIATE_SYSTEM = """You are {name}.
Description: {description}

Your goal hierarchy is:
{goal_tree}

Based on the current time ({current_time}), which tasks should you
focus on right now? List only immediate actionable tasks.
Format: one task per line."""


class GoalManager:
    """Manages agent goal lifecycle.

    Creates goals from agent context, reviews and updates status,
    decomposes high-level goals into sub-goals, and formats goal
    context for LLM planning prompts.

    Usage::

        gm = GoalManager(GoalConfig(), prompt_meta)
        goals = gm.initialize_goals(agent.description, events)
        goals = gm.review_and_update_goals(agent, memories, time)
    """

    def __init__(
        self,
        config: GoalConfig,
        prompt_meta: str = "### Instruction:\n{}\n### Response:",
    ) -> None:
        self._config = config
        self._prompt_meta = prompt_meta

    def initialize_goals(
        self,
        agent_description: str,
        initial_events: list[str],
        current_time: str = "Day 1, 08:00",
    ) -> list[Goal]:
        """Generate initial goals for an agent.

        Args:
            agent_description: Agent's character description.
            initial_events: Initial global events.
            current_time: Current simulation time.

        Returns:
            List of initial Goal objects.
        """
        agent_name = self._extract_name(agent_description)

        system = GOAL_CREATION_SYSTEM.format(
            name=agent_name,
            description=agent_description[:200],
            current_time=current_time,
            recent_events="; ".join(initial_events[:5]),
        )
        prompt = GOAL_CREATION_PROMPT.format(
            max_goals=self._config.max_active_goals,
        )

        response = GPT_request(
            system,
            self._prompt_meta.format(prompt),
            gpt_parameter={"max_tokens": 120},
        )

        return self._parse_goal_creation(response, current_time)

    def review_and_update_goals(
        self,
        agent: Agent,
        recent_memories: list[MemoryEntry],
        current_time: str,
    ) -> list[Goal]:
        """Review existing goals, update status, create new ones.

        Args:
            agent: The agent to review goals for.
            recent_memories: Recent memory entries.
            current_time: Current simulation time.

        Returns:
            Updated list of goals.
        """
        if not hasattr(agent, "goals") or not agent.goals:
            agent.goals = []

        active = [g for g in agent.goals if g.status in (GoalStatus.ACTIVE, GoalStatus.IN_PROGRESS)]
        if not active:
            return agent.goals

        agent_name = self._extract_name(agent.description)
        goals_text = "\n".join(
            f"[{g.id}] P{g.priority}: {g.description} (since {g.created_at})"
            for g in active
        )
        memories_text = "\n".join(m.summary for m in recent_memories[:5])

        system = GOAL_REVIEW_SYSTEM.format(
            name=agent_name,
            description=agent.description[:200],
            active_goals=goals_text,
            recent_memories=memories_text,
        )

        response = GPT_request(
            system,
            self._prompt_meta.format(system),
            gpt_parameter={"max_tokens": 80},
        )

        return self._apply_goal_review(agent.goals, response, current_time)

    def decompose_goal(
        self, goal: Goal, context: str, depth: int = 0,
    ) -> list[Goal]:
        """Break a high-level goal into actionable sub-goals.

        Args:
            goal: The goal to decompose.
            context: Current situation context.
            depth: Current decomposition depth.

        Returns:
            List of sub-goal objects.
        """
        if depth >= self._config.decomposition_depth:
            return []

        system = GOAL_DECOMPOSITION_SYSTEM.format(
            goal_description=goal.description,
            context=context[:300],
            depth=depth,
        )

        response = GPT_request(
            system,
            self._prompt_meta.format(system),
            gpt_parameter={"max_tokens": 100},
        )

        return self._parse_decomposition(response, goal, current_time=goal.created_at)

    def get_active_goals(self, goals: list[Goal]) -> list[Goal]:
        """Return goals with ACTIVE or IN_PROGRESS status.

        Args:
            goals: All goals.

        Returns:
            Filtered list of active goals.
        """
        return [g for g in goals if g.status in (GoalStatus.ACTIVE, GoalStatus.IN_PROGRESS)]

    def format_goals_context(self, goals: list[Goal]) -> str:
        """Format active goals as context string for LLM planning prompts.

        Args:
            goals: All goals.

        Returns:
            Formatted string for LLM consumption, or empty string.
        """
        active = self.get_active_goals(goals)
        if not active:
            return ""

        lines = []
        for g in active:
            sub_info = ""
            if g.sub_goals:
                sub_info = " (has sub-tasks)"
            lines.append(
                f"- P{g.priority}: {g.description}{sub_info} "
                f"[status: {g.status.value}]"
            )
        return "\n".join(lines)

    def format_goals_for_planning(
        self, agent: Agent, goals: list[Goal]
    ) -> str:
        """Format goals as a full system prompt addition for daily planning.

        Args:
            agent: The agent.
            goals: All goals.

        Returns:
            System prompt addition string, or empty string.
        """
        active = self.get_active_goals(goals)
        if not active:
            return ""

        goals_text = "\n".join(
            f"  - P{g.priority}: {g.description}"
            for g in active
        )
        return GOAL_CONTEXT_SYSTEM.format(
            name=agent.name,
            description=agent.description[:200],
            goals_context=goals_text,
        )

    def check_completion(
        self, goal: Goal, recent_actions: list[str]
    ) -> GoalStatus:
        """Evaluate whether a goal has been completed.

        Uses simple keyword matching against completion conditions.
        For more accurate evaluation, this should be LLM-powered.

        Args:
            goal: The goal to check.
            recent_actions: List of recent action descriptions.

        Returns:
            Updated GoalStatus.
        """
        if not goal.completion_conditions:
            return goal.status

        conditions_lower = goal.completion_conditions.lower()
        actions_text = " ".join(recent_actions).lower()

        if conditions_lower and any(
            kw in actions_text for kw in conditions_lower.split() if len(kw) > 3
        ):
            return GoalStatus.COMPLETED

        return goal.status

    def serialize_goals(self, goals: list[Goal]) -> list[dict[str, Any]]:
        """Serialize goals to a list of dicts for checkpoint storage.

        Args:
            goals: List of Goal objects.

        Returns:
            List of serializable dicts.
        """
        result: list[dict[str, Any]] = []
        for g in goals:
            d: dict[str, Any] = {
                "id": g.id,
                "description": g.description,
                "status": g.status.value,
                "priority": g.priority,
                "created_at": g.created_at,
                "deadline": g.deadline,
                "parent_id": g.parent_id,
                "progress_notes": g.progress_notes,
                "completion_conditions": g.completion_conditions,
                "sub_goals": self.serialize_goals(g.sub_goals),
            }
            result.append(d)
        return result

    def deserialize_goals(self, data: list[dict[str, Any]]) -> list[Goal]:
        """Deserialize goals from checkpoint data.

        Args:
            data: List of goal dicts.

        Returns:
            List of Goal objects.
        """
        goals: list[Goal] = []
        for d in data:
            sub_data = d.get("sub_goals", [])
            sub_goals = self.deserialize_goals(sub_data) if isinstance(sub_data, list) else []

            goals.append(Goal(
                id=d.get("id", ""),
                description=d.get("description", ""),
                status=GoalStatus(d.get("status", "active")),
                priority=d.get("priority", 5),
                created_at=d.get("created_at", ""),
                deadline=d.get("deadline"),
                parent_id=d.get("parent_id"),
                sub_goals=sub_goals,
                progress_notes=d.get("progress_notes", ""),
                completion_conditions=d.get("completion_conditions", ""),
            ))
        return goals

    def _parse_goal_creation(
        self, response: str, current_time: str
    ) -> list[Goal]:
        """Parse LLM goal creation response into Goal objects."""
        goals: list[Goal] = []
        for line in response.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            priority = 5
            description = line

            if ":" in line:
                parts = line.split(":", 1)
                try:
                    p = int(parts[0].strip())
                    if 1 <= p <= 9:
                        priority = p
                except ValueError:
                    pass
                description = parts[1].strip()

            if description:
                goals.append(Goal(
                    description=description[:100],
                    priority=priority,
                    created_at=current_time,
                    status=GoalStatus.ACTIVE,
                ))

        goals.sort(key=lambda g: g.priority, reverse=True)
        return goals[:self._config.max_active_goals]

    def _apply_goal_review(
        self, goals: list[Goal], response: str, current_time: str,
    ) -> list[Goal]:
        """Apply LLM review response to update goal statuses."""
        for line in response.strip().split("\n"):
            line = line.strip()
            if not line or "|" not in line:
                continue

            parts = line.split("|", 1)
            goal_part = parts[0].strip()
            status_part = parts[1].strip() if len(parts) > 1 else "CONTINUE"

            goal_id = self._extract_goal_id(goal_part)
            if not goal_id:
                continue

            for i, g in enumerate(goals):
                if g.id == goal_id:
                    status_map = {
                        "completed": GoalStatus.COMPLETED,
                        "abandoned": GoalStatus.ABANDONED,
                        "blocked": GoalStatus.BLOCKED,
                        "continue": GoalStatus.IN_PROGRESS,
                        "in_progress": GoalStatus.IN_PROGRESS,
                    }
                    new_status = status_map.get(status_part.lower(), g.status)
                    new_notes = g.progress_notes
                    if new_status == GoalStatus.COMPLETED:
                        new_notes = f"Completed at {current_time}"
                    goals[i] = replace(g, status=new_status, progress_notes=new_notes)
                    break

        return goals

    def _parse_decomposition(
        self, response: str, parent: Goal, current_time: str,
    ) -> list[Goal]:
        """Parse LLM decomposition response into sub-goals."""
        sub_goals: list[Goal] = []
        for line in response.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            priority = parent.priority - 1
            description = line
            completion = ""

            if "|" in line:
                parts = line.split("|", 1)
                desc_part = parts[0].strip()
                comp_part = parts[1].strip() if len(parts) > 1 else ""

                if ":" in desc_part:
                    p_parts = desc_part.split(":", 1)
                    try:
                        p = int(p_parts[0].strip())
                        if 1 <= p <= 9:
                            priority = p
                    except ValueError:
                        pass
                    description = p_parts[1].strip()

                if "completion:" in comp_part.lower():
                    completion = comp_part.split(":", 1)[1].strip()
                else:
                    completion = comp_part

            if description:
                sub_goals.append(Goal(
                    description=description[:100],
                    priority=max(1, priority),
                    created_at=current_time,
                    parent_id=parent.id,
                    completion_conditions=completion,
                    status=GoalStatus.ACTIVE,
                ))

        parent.sub_goals = sub_goals
        return sub_goals

    @staticmethod
    def _extract_name(description: str) -> str:
        """Extract agent name from description JSON or raw string."""
        import json

        try:
            data = json.loads(description)
            return data.get("name", "Agent")
        except (json.JSONDecodeError, TypeError):
            return description.split(",")[0].strip('"').strip()[:30]

    @staticmethod
    def _extract_goal_id(text: str) -> str | None:
        """Extract goal ID from a line like '[abc123] ...'."""
        import re

        match = re.search(r"\[([a-f0-9]+)\]", text)
        return match.group(1) if match else None


class RecursiveTaskDecomposer:
    """Recursive task decomposition with dependency ordering.

    Extends GoalManager.decompose_goal with:
    - Automatic recursive decomposition to configurable depth
    - Dependency-aware task ordering
    - Immediate task extraction for current planning cycle

    Usage::

        decomposer = RecursiveTaskDecomposer(goal_manager, max_depth=2)
        root_goal = Goal(description="Organize a festival")
        tree = decomposer.decompose(root_goal, context)
        ordered = decomposer.order_by_dependency(tree)
        immediate = decomposer.get_immediate_tasks(ordered)
        task_plan = decomposer.format_task_plan(immediate)
    """

    def __init__(
        self,
        goal_manager: GoalManager,
        max_depth: int = 2,
    ) -> None:
        self._gm = goal_manager
        self._max_depth = max_depth

    def decompose(
        self,
        goal: Goal,
        context: str,
        depth: int = 0,
    ) -> list[Goal]:
        """Recursively decompose a goal into sub-goals.

        Args:
            goal: The goal to decompose.
            context: Current situation context string.
            depth: Current recursion depth.

        Returns:
            All sub-goals (flattened, including nested).
        """
        if depth >= self._max_depth:
            return []

        sub_goals = self._gm.decompose_goal(goal, context, depth=depth)

        all_sub_goals: list[Goal] = []
        for sg in sub_goals:
            all_sub_goals.append(sg)
            if depth + 1 < self._max_depth:
                nested = self.decompose(sg, context, depth=depth + 1)
                all_sub_goals.extend(nested)

        return all_sub_goals

    def order_by_dependency(self, goals: list[Goal]) -> list[Goal]:
        """Order goals by dependency using LLM-based scheduling.

        Tasks with no prerequisites come first. Tasks that depend on
        other tasks come later.

        Args:
            goals: List of goals to order.

        Returns:
            Goals sorted in execution order.
        """
        if len(goals) <= 1:
            return goals

        tasks_text = "\n".join(
            f"[{g.id}] P{g.priority}: {g.description}"
            for g in goals
        )

        response = GPT_request(
            TASK_ORDERING_SYSTEM.format(tasks=tasks_text),
            self._gm._prompt_meta.format("List the tasks in execution order:"),
            gpt_parameter={"max_tokens": 100},
        )

        ordered_ids = self._extract_ordered_ids(response, goals)

        if not ordered_ids:
            return sorted(goals, key=lambda g: g.priority, reverse=True)

        ordered: list[Goal] = []
        seen_ids: set[str] = set()
        for gid in ordered_ids:
            if gid in seen_ids:
                continue
            seen_ids.add(gid)
            for g in goals:
                if g.id == gid and g not in ordered:
                    ordered.append(g)

        for g in goals:
            if g not in ordered:
                ordered.append(g)

        return ordered

    def get_immediate_tasks(self, goals: list[Goal]) -> list[Goal]:
        """Get leaf-level goals (no sub-goals) that are actionable now.

        Args:
            goals: Ordered list of goals.

        Returns:
            Leaf goals with ACTIVE or IN_PROGRESS status.
        """
        leaf_goals: list[Goal] = []
        for g in goals:
            is_leaf = not g.sub_goals
            is_active = g.status in (GoalStatus.ACTIVE, GoalStatus.IN_PROGRESS)
            if is_leaf and is_active:
                leaf_goals.append(g)

        return leaf_goals

    def format_task_plan(self, tasks: list[Goal]) -> str:
        """Format immediate tasks as a planning context string.

        Args:
            tasks: List of immediate tasks to format.

        Returns:
            Formatted task plan string for LLM prompts.
        """
        if not tasks:
            return ""

        lines: list[str] = []
        for i, t in enumerate(tasks, 1):
            conditions = ""
            if t.completion_conditions:
                conditions = f" (done when: {t.completion_conditions})"
            lines.append(f"{i}. {t.description}{conditions}")

        return "Immediate tasks:\n" + "\n".join(lines)

    def format_goal_tree(self, goal: Goal, indent: int = 0) -> str:
        """Format a goal and its sub-goals as an indented tree.

        Args:
            goal: The root goal.
            indent: Current indentation level.

        Returns:
            Tree-formatted string.
        """
        prefix = "  " * indent
        status_marker = {
            GoalStatus.ACTIVE: "[ ]",
            GoalStatus.IN_PROGRESS: "[>]",
            GoalStatus.COMPLETED: "[x]",
            GoalStatus.ABANDONED: "[-]",
            GoalStatus.BLOCKED: "[!]",
        }.get(goal.status, "[?]")

        line = f"{prefix}{status_marker} P{goal.priority}: {goal.description}"
        if goal.deadline:
            line += f" (due: {goal.deadline})"

        lines = [line]
        for sg in goal.sub_goals:
            lines.append(self.format_goal_tree(sg, indent + 1))

        return "\n".join(lines)

    def _extract_ordered_ids(
        self, response: str, goals: list[Goal]
    ) -> list[str]:
        """Extract goal IDs from LLM ordering response."""
        import re

        goal_descriptions = {g.description.lower(): g.id for g in goals}

        ordered_ids: list[str] = []
        seen_descriptions: set[str] = set()

        for line in response.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            line_clean = re.sub(r"^[\d.\-\*]+\s*", "", line).strip()

            for desc_lower, gid in goal_descriptions.items():
                if desc_lower in line_clean.lower() and desc_lower not in seen_descriptions:
                    ordered_ids.append(gid)
                    seen_descriptions.add(desc_lower)
                    break

        return ordered_ids
