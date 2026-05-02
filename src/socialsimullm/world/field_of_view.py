# socialsimullm/world/field_of_view.py

# -*- coding: utf-8 -*-

"""
Field-of-view (FOV) proximity-based agent perception.

Computes which agents are visible to a given observer based on
graph distance in the spatial world. Distance 0 = co-located,
distance > 0 = reachable via weighted graph edges.

When disabled (default), all agents at the same location are
visible (legacy behavior preserved).

@author: Huang Miaosen
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import networkx as nx

if TYPE_CHECKING:
    from socialsimullm.agents.agent import Agent


@dataclass(frozen=True)
class FOVConfig:
    """Field of view configuration.

    Attributes:
        enabled: Whether FOV perception is active.
        distance_threshold: Max graph distance for visibility.
            0.0 = same location only (legacy behavior).
        include_location_info: Include location description in
            the perception context string.
    """

    enabled: bool = False
    distance_threshold: float = 0.0
    include_location_info: bool = True


@dataclass(frozen=True)
class PerceptibleAgent:
    """An agent visible within the current agent's field of view.

    Attributes:
        name: Agent's name.
        description: Agent's character description.
        location: Agent's current location name.
        distance: Graph distance from observer (0 = co-located).
        is_co_located: Whether the agent is at the same location.
    """

    name: str
    description: str
    location: str
    distance: float
    is_co_located: bool


class FieldOfView:
    """Proximity-based agent perception system.

    Uses NetworkX shortest_path with edge weights to determine
    which agents fall within the observer's distance threshold.

    Usage::

        fov = FieldOfView(FOVConfig(enabled=True, distance_threshold=2.0), graph)
        visible = fov.get_visible_agents(agent, all_agents)
    """

    def __init__(self, config: FOVConfig, world_graph: nx.Graph) -> None:
        self._config = config
        self._graph = world_graph
        self._distances: dict[str, dict[str, float]] = dict(
            nx.all_pairs_dijkstra_path_length(world_graph)
        )

    @property
    def config(self) -> FOVConfig:
        return self._config

    def get_visible_agents(
        self, observer: Agent, all_agents: list[Agent]
    ) -> list[PerceptibleAgent]:
        """Return agents visible to the observer.

        When FOV is disabled, returns all agents at the same location
        (matching legacy behavior exactly).

        Args:
            observer: The observing agent.
            all_agents: All agents in the simulation.

        Returns:
            List of PerceptibleAgent, sorted by distance (nearest first).
        """
        if not self._config.enabled:
            return self._legacy_perception(observer, all_agents)

        threshold = self._config.distance_threshold
        result: list[PerceptibleAgent] = []

        for other in all_agents:
            if other.name == observer.name:
                continue

            distance = self._graph_distance(observer.location, other.location)
            if distance is not None and distance <= threshold:
                result.append(PerceptibleAgent(
                    name=other.name,
                    description=other.description,
                    location=other.location,
                    distance=distance,
                    is_co_located=(distance == 0.0),
                ))

        result.sort(key=lambda a: a.distance)
        return result

    def format_visible_agents(
        self, observer: Agent, all_agents: list[Agent]
    ) -> str:
        """Format visible agents as a string for LLM prompts.

        Produces output like:
        'At Stonehill Inn: Daran Edermath (retired adventurer).'

        Args:
            observer: The observing agent.
            all_agents: All agents in the simulation.

        Returns:
            Formatted string describing visible agents.
        """
        visible = self.get_visible_agents(observer, all_agents)
        if not visible:
            return "No one else is around."

        parts: list[str] = []

        co_located = [a for a in visible if a.is_co_located]
        if co_located:
            names = []
            for a in co_located:
                names.append(f"{a.name}: {a.description}")
            loc_name = observer.location
            parts.append(f"At {loc_name}: {'; '.join(names)}")

        nearby = [a for a in visible if not a.is_co_located]
        for a in nearby:
            desc = f"{a.name}: {a.description}"
            if self._config.include_location_info:
                desc += f" at {a.location}"
            desc += f" (distance: {a.distance:.1f})"
            parts.append(f"Nearby: {desc}")

        return ". ".join(parts) if parts else "No one else is around."

    def format_nearby_context(
        self, observer: Agent, all_agents: list[Agent]
    ) -> str:
        """Generate full perception context for LLM prompts.

        Includes a header, visible agents, and empty-state message.

        Args:
            observer: The observing agent.
            all_agents: All agents in the simulation.

        Returns:
            Multi-line context string.
        """
        visible = self.get_visible_agents(observer, all_agents)

        if not visible:
            return (
                f"{observer.name} looks around but sees no one nearby."
            )

        lines = [f"{observer.name} perceives the following people:"]

        if self._config.enabled and self._config.distance_threshold > 0:
            lines.append(
                f"(Perception range: {self._config.distance_threshold:.1f})"
            )

        for a in visible:
            if a.is_co_located:
                lines.append(
                    f"- {a.name}: {a.description} [same location]"
                )
            else:
                loc_info = f" at {a.location}" if self._config.include_location_info else ""
                lines.append(
                    f"- {a.name}: {a.description}{loc_info} "
                    f"[distance: {a.distance:.1f}]"
                )

        return "\n".join(lines)

    def _graph_distance(
        self, from_location: str, to_location: str
    ) -> float | None:
        """Lookup pre-computed shortest path distance between two locations.

        Returns None if no path exists.
        """
        if from_location not in self._distances:
            return None
        return self._distances[from_location].get(to_location)

    def _legacy_perception(
        self, observer: Agent, all_agents: list[Agent]
    ) -> list[PerceptibleAgent]:
        """Legacy behavior: all agents at the same location are visible."""
        result: list[PerceptibleAgent] = []
        for other in all_agents:
            if other.name == observer.name:
                continue
            if other.location == observer.location:
                result.append(PerceptibleAgent(
                    name=other.name,
                    description=other.description,
                    location=other.location,
                    distance=0.0,
                    is_co_located=True,
                ))
        return result
