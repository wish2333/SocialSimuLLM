# socialsimullm/simulator/state.py

# -*- coding: utf-8 -*-

"""
Simulation state dataclass.

Holds all mutable state for a running simulation as a single data object
passed between modules.

@author: Huang Miaosen
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SimulationState:
    """Mutable simulation state container.

    Attributes:
        global_time: Current simulation time string, e.g. "Day 1, 08:00".
        round: Current simulation round number.
        agents: List of Agent instances.
        locations: Locations collection instance.
        world_graph: NetworkX graph representing the spatial world.
        memory: AgentMemory (agents/memory.py) instance for all agents.
        project_folder: Absolute path to the project directory.
        meta_data: Dictionary of persistent metadata (project_name, global_time, round).
        town_areas: Dictionary of area_name -> area_description.
        events: List of active global event description strings.
    """

    global_time: str
    round: int
    agents: list[Any]
    locations: Any
    world_graph: Any
    memory: Any
    project_folder: str
    meta_data: dict[str, Any]
    town_areas: dict[str, Any]
    events: list[str] = field(default_factory=list)
