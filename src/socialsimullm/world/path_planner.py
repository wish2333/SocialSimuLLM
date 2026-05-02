# socialsimullm/world/path_planner.py

# -*- coding: utf-8 -*-

"""
LLM-driven path planning with A* shortest path.

Provides PathPlanner that infers agent movement intentions from
hourly plans using LLM, then finds the shortest weighted path
using NetworkX A* algorithm. Supports multi-hop traversal where
agents move one node per movement step instead of teleporting.

@author: Huang Miaosen
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import networkx as nx

from socialsimullm.utils.text_generation import GPT_request, get_rating, deepseek_v4_marker

if TYPE_CHECKING:
    from socialsimullm.agents.agent import Agent


@dataclass(frozen=True)
class PathPlannerConfig:
    """Configuration for the path planning system.

    Attributes:
        enabled: Whether path planner is active.
        multi_hop: If True, agent traverses one node per movement step.
                   If False, agent teleports to destination (legacy behavior).
        max_path_length: Maximum edges in a single path.
        prefer_shortest: Weight for shortest path preference (0=random, 1=always).
    """

    enabled: bool = False
    multi_hop: bool = True
    max_path_length: int = 10
    prefer_shortest: float = 0.8


@dataclass
class MovementIntent:
    """Agent's movement intention parsed from LLM response.

    Attributes:
        destination: Target location name.
        reason: Why the agent wants to go there.
        urgency: How urgently the agent wants to move (0.0-1.0).
    """

    destination: str
    reason: str
    urgency: float = 0.5


@dataclass
class PlannedPath:
    """A planned movement path through the world graph.

    Attributes:
        agent_name: Name of the agent.
        origin: Starting location.
        destination: Target location.
        path: Ordered list of location nodes to traverse.
        total_distance: Sum of edge weights along the path.
        steps_remaining: Number of steps left to reach destination.
        intent: The movement intention that triggered this path.
    """

    agent_name: str
    origin: str
    destination: str
    path: list[str] = field(default_factory=list)
    total_distance: float = 0.0
    steps_remaining: int = 0
    intent: MovementIntent | None = None


# Prompt templates for movement intent inference
MOVEMENT_INTENT_SYSTEM = """You are {name}.
The following is your description: {description}.
You are currently at {current_location}.
Your plan for this hour is: {hourly_plan}.
{visible_context}
Based on your plan and what you can see, where do you want to go?
Respond with the location name only, then a brief reason.
Format: [Location Name]|[reason]
Example: Stonehill Inn|I need to rest after a long day."""

MOVEMENT_INTENT_PROMPT = """Given your current location and plan, where do you want to move?
Respond in format: [Destination]|[Reason]
Available locations: {locations}
If you want to stay where you are, respond: STAY|I am content here."""


class PathPlanner:
    """LLM intent + A* pathfinding for agent movement.

    Replaces the rate_locations() approach with:
    1. LLM infers destination from agent's hourly plan
    2. A* finds shortest weighted path
    3. Agent traverses one hop per movement opportunity

    Usage::

        planner = PathPlanner(PathPlannerConfig(), graph, prompt_meta)
        path = planner.plan_movement(agent, hourly_plan, visible_context)
        if path:
            new_loc = planner.execute_step(path)
    """

    def __init__(
        self,
        config: PathPlannerConfig,
        world_graph: nx.Graph,
        prompt_meta: str = "### Instruction:\n{}\n### Response:",
    ) -> None:
        self._config = config
        self._graph = world_graph
        self._prompt_meta = prompt_meta

    def infer_movement_intent(
        self,
        agent: Agent,
        hourly_plan: str,
        visible_context: str = "",
    ) -> MovementIntent:
        """Use LLM to infer where the agent wants to go.

        Args:
            agent: The agent to plan movement for.
            hourly_plan: The agent's hourly plan string.
            visible_context: FOV context string of visible agents.

        Returns:
            MovementIntent with destination, reason, and urgency.
        """
        location_names = list(self._graph.nodes())

        system = MOVEMENT_INTENT_SYSTEM.format(
            name=agent.name,
            description=agent.description,
            current_location=agent.location,
            hourly_plan=hourly_plan,
            visible_context=f"You can see: {visible_context}" if visible_context else "",
        )
        prompt = MOVEMENT_INTENT_PROMPT.format(locations=", ".join(location_names))

        response = GPT_request(
            system,
            self._prompt_meta.format(prompt) + deepseek_v4_marker("role_immersion"),
            gpt_parameter={"max_tokens": 30},
        )

        return self._parse_intent_response(response, location_names)

    def find_path(self, origin: str, destination: str) -> list[str]:
        """Find shortest weighted path using A*.

        Args:
            origin: Starting location name.
            destination: Target location name.

        Returns:
            Ordered list of location names from origin to destination.

        Raises:
            ValueError: If no path exists.
        """
        if origin not in self._graph or destination not in self._graph:
            raise ValueError(
                f"Invalid location: '{origin}' or '{destination}'. "
                f"Valid: {list(self._graph.nodes())}"
            )

        try:
            path = nx.astar_path(
                self._graph, origin, destination, weight="weight"
            )
        except nx.NetworkXNoPath:
            raise ValueError(
                f"No path from '{origin}' to '{destination}' in the world graph."
            )

        if len(path) > self._config.max_path_length:
            raise ValueError(
                f"Path from '{origin}' to '{destination}' is too long "
                f"({len(path)} edges, max {self._config.max_path_length})."
            )

        return list(path)

    def plan_movement(
        self,
        agent: Agent,
        hourly_plan: str,
        visible_context: str = "",
    ) -> PlannedPath | None:
        """Full planning: infer intent + find path.

        Args:
            agent: The agent to plan movement for.
            hourly_plan: The agent's hourly plan string.
            visible_context: FOV context string.

        Returns:
            PlannedPath if the agent wants to move, None if staying.
        """
        intent = self.infer_movement_intent(agent, hourly_plan, visible_context)

        if intent.destination == "STAY" or intent.destination == agent.location:
            return None

        path = self.find_path(agent.location, intent.destination)
        total_distance = sum(
            self._graph.edges[path[i], path[i + 1]].get("weight", 1.0)
            for i in range(len(path) - 1)
            if path[i] != path[i + 1]
        )

        return PlannedPath(
            agent_name=agent.name,
            origin=agent.location,
            destination=intent.destination,
            path=path,
            total_distance=total_distance,
            steps_remaining=len(path) - 1,
            intent=intent,
        )

    def execute_step(self, planned_path: PlannedPath) -> str | None:
        """Execute one step of a multi-hop path.

        Moves the agent from path[0] to path[1], then shifts the
        path. If only one node remains (destination reached),
        returns None.

        Args:
            planned_path: The planned path to advance.

        Returns:
            The new location name, or None if already at destination.
        """
        if planned_path.steps_remaining <= 0:
            return None

        next_location = planned_path.path[1]
        planned_path.path = planned_path.path[1:]
        planned_path.steps_remaining -= 1
        planned_path.origin = next_location

        return next_location

    def format_path_context(self, agent: Agent) -> str:
        """Format current movement state for LLM prompts.

        Args:
            agent: The agent with a planned_path attribute.

        Returns:
            Context string about current movement, or empty if not moving.
        """
        if not hasattr(agent, "planned_path") or agent.planned_path is None:
            return ""

        pp = agent.planned_path
        if pp.steps_remaining <= 0:
            return ""

        remaining_path = " -> ".join(pp.path)
        return (
            f"You are currently traveling to {pp.destination}. "
            f"Route: {remaining_path}. "
            f"{pp.steps_remaining} steps remaining."
        )

    def _parse_intent_response(
        self, response: str, valid_locations: list[str]
    ) -> MovementIntent:
        """Parse LLM response into a MovementIntent.

        Expected format: "Location Name|Reason" or "STAY|Reason".
        Falls back to current location on parse failure.

        Args:
            response: Raw LLM response string.
            valid_locations: List of valid destination names.

        Returns:
            Parsed MovementIntent.
        """
        response = response.strip()

        if "|" in response:
            parts = response.split("|", 1)
            dest = parts[0].strip()
            reason = parts[1].strip() if len(parts) > 1 else ""
        else:
            dest = response.strip().strip('"').strip("'")
            reason = ""

        dest_normalized = self._match_location(dest, valid_locations)

        if dest_normalized is None or dest_normalized == "STAY":
            return MovementIntent(
                destination="STAY",
                reason=reason or "No movement intended.",
                urgency=0.0,
            )

        return MovementIntent(
            destination=dest_normalized,
            reason=reason or "Wants to visit this location.",
            urgency=0.5,
        )

    @staticmethod
    def _match_location(dest: str, valid_locations: list[str]) -> str | None:
        """Fuzzy-match a destination string against valid locations.

        Args:
            dest: Raw destination string from LLM.
            valid_locations: List of valid location names.

        Returns:
            Matched location name or None.
        """
        dest_lower = dest.lower()
        for loc in valid_locations:
            if loc.lower() == dest_lower:
                return loc
        for loc in valid_locations:
            if dest_lower in loc.lower() or loc.lower() in dest_lower:
                return loc
        return None
