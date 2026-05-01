# socialsimullm/simulator/core.py

# -*- coding: utf-8 -*-

"""
Simulation core engine.

Contains SimulatorCore which handles initialization and execution
of the social simulation loop. Uses StructuredLogger for JSONL + text logging.

@author: Huang Miaosen
"""

from __future__ import annotations

import os
import json

import networkx as nx

from socialsimullm.agents.agent import Agent
from socialsimullm.agents.memory import AgentMemory
from socialsimullm.agents.reflection import ReflectionConfig, ReflectionEngine
from socialsimullm.locations.locations import Locations
from socialsimullm.simulator.state import SimulationState
from socialsimullm.utils.config import SimulationConfig
from socialsimullm.utils.global_methods import (
    add_ten_minutes,
    exist_memory_file,
    if_new_day,
    if_new_hour,
    load_meta_data,
    load_town_data,
    save_location_change,
    save_meta_data,
)
from socialsimullm.utils.logger import LogConfig, StructuredLogger
from socialsimullm.utils.text_generation import summarize_simulation


class SimulatorCore:
    """Core simulation engine.

    Handles initialization of the simulation world and execution of
    the step-by-step simulation loop.

    Usage::

        core = SimulatorCore(config)
        core.initialize()
        core.run(max_steps=100)
    """

    def __init__(self, config: SimulationConfig) -> None:
        self.config = config
        self.project_name = config.project_name
        self.project_folder = os.path.join(os.getcwd(), "projects", config.project_name)
        self.state: SimulationState | None = None
        self.logger: StructuredLogger | None = None
        self.reflection_engine: ReflectionEngine | None = None

    def initialize(self) -> None:
        """Initialize the simulation world from project data.

        Loads metadata, creates world graph, agents, locations, and memory.
        Prompts for global events if needed.
        """
        global_time = "Day 1, 08:00"

        # Initialize logger
        self.logger = StructuredLogger(self.project_folder)

        # Load project data
        meta_data = load_meta_data(self.project_folder, self.project_name, global_time)
        town_data = load_town_data(self.project_folder)

        global_time = meta_data["global_time"]
        round_num = meta_data["round"]
        memory_limit = town_data["general"]["memory_limit"]
        town_people = town_data["town_people"]
        town_areas = town_data["town_areas"]

        print(f"=== CONFIGURATIONS for {self.project_name} LOADED ===")
        print(f"==Global time: {global_time} Round: {round_num}==")

        # Create world graph (ring topology)
        world_graph = self._create_world_graph(town_areas)
        print("Nodes in world_graph:", world_graph.nodes())

        # Create agents
        agents = self._create_agents(town_people, world_graph)

        # Initialize memory
        for agent in agents:
            exist_memory_file(agent.name, self.project_folder)
        memory = AgentMemory(self.project_folder, agents, memory_limit)

        # Initialize reflection engine
        reflection_config = ReflectionConfig(
            threshold_importance=self.config.reflection_importance_threshold,
            threshold_min_observations=self.config.reflection_min_observations,
            reflection_token_limit=self.config.reflection_token_limit,
            include_in_planning=self.config.reflection_include_in_planning,
        )
        self.reflection_engine = ReflectionEngine(
            config=reflection_config,
            memory=memory,
            prompt_meta=self.config.prompt_meta,
        )

        # Handle global events
        events = self._load_events(memory, global_time)

        # Initialize agent memories
        for agent in agents:
            init_memory_list = memory.get_init_memory(agent.name)
            agent.init_memory(init_memory_list[0], init_memory_list[1], events)

        # Create locations (F-108 fix: use detail, not the description variable)
        locations = Locations()
        for name, detail in town_areas.items():
            locations.add_location(name, detail)

        print("=== MODULES INITIALIZED ===")

        self.state = SimulationState(
            global_time=global_time,
            round=round_num,
            agents=agents,
            locations=locations,
            world_graph=world_graph,
            memory=memory,
            project_folder=self.project_folder,
            meta_data=meta_data,
            town_areas=town_areas,
            events=events,
        )

    def step(self) -> str:
        """Execute one simulation step (one 10-minute interval).

        Returns:
            The log output string for this step.
        """
        assert self.state is not None, "Call initialize() before step()"
        assert self.logger is not None
        s = self.state
        logger = self.logger
        prompt_meta = self.config.prompt_meta

        s.round += 1
        new_day = if_new_day(s.global_time)
        new_hour = if_new_hour(s.global_time)

        logger.log_round_start(s.round, s.global_time)

        # Daily planning
        if new_day:
            self._daily_planning(s, prompt_meta)

        # Hourly planning
        if new_hour:
            self._hourly_planning(s, prompt_meta)
        elif s.round == 1:
            for agent in s.agents:
                agent.related_things = s.memory.format_semantic(agent.name, agent.hourly_plan, 5)
                logger.log_debug(f"Related things:\n{agent.related_things}\n")

        # Action execution
        self._execute_actions(s, prompt_meta)

        # Threshold-based mid-day reflection (skip near day boundary to avoid double)
        approaching_day_boundary = if_new_day(add_ten_minutes(s.global_time))
        if (
            self.config.reflection_enabled
            and self.reflection_engine is not None
            and not approaching_day_boundary
        ):
            for agent in s.agents:
                if self.reflection_engine.should_reflect(agent.name, s.global_time):
                    self._run_reflection(s, agent, "threshold")

        # Location rating and movement
        if new_hour:
            self._movement(s, prompt_meta)

        # Impression formation
        if new_hour:
            self._impressions(s, prompt_meta)

        # End of round
        logger.log_round_end(s.round)
        log_output = "\n".join(logger._text_buffer)
        logger.flush_text_log()

        # Time advancement
        new_global_time = add_ten_minutes(s.global_time)

        # Daily reflection
        if if_new_day(new_global_time):
            if self.config.reflection_enabled and self.reflection_engine is not None:
                for agent in s.agents:
                    self._run_reflection(s, agent, "scheduled")

        # Summary at day boundaries
        if if_new_day(new_global_time) and s.round != 1:
            summary_text = logger.get_summary_text()
            summary_output = summarize_simulation(summary_text)
            logger.write_summary(summary_output, s.round)
            logger.clear_summary()

        # Checkpoint
        if self.config.checkpoint_interval > 0 and s.round % self.config.checkpoint_interval == 0:
            logger.save_checkpoint(s, s.round)

        s.global_time = new_global_time
        s.meta_data["global_time"] = s.global_time
        s.meta_data["round"] = s.round
        save_meta_data(s.project_folder, s.meta_data)

        return log_output

    def run(self, max_steps: int = 0) -> None:
        """Run the simulation loop.

        Args:
            max_steps: Maximum number of steps to run. 0 means interactive mode
                       (prompts user for repeat count, matching original behavior).
        """
        if max_steps > 0:
            for _ in range(max_steps):
                self.step()
        else:
            # Interactive mode (original behavior)
            repeats = int(input("Please enter the number of repeats: ") or 1)
            for repeat in range(repeats):
                self.step()
                # Final summary on last repeat
                if repeat == repeats - 1:
                    assert self.state is not None
                    assert self.logger is not None
                    summary_output = summarize_simulation("")
                    self.logger.write_summary(summary_output, self.state.round)

        # Write completion marker
        if self.logger is not None:
            self.logger.finalize()

    # --- Private helper methods ---

    def _create_world_graph(self, town_areas: dict) -> nx.Graph:
        """Create a ring graph from town areas."""
        world_graph = nx.Graph()
        area_names = list(town_areas.keys())

        for area_name in area_names:
            world_graph.add_node(area_name)

        for i, area_name in enumerate(area_names):
            world_graph.add_edge(area_name, area_name)  # Self-loop
            if i > 0:
                world_graph.add_edge(area_name, area_names[i - 1])

        # Complete the cycle
        if len(area_names) > 1:
            world_graph.add_edge(area_names[0], area_names[-1])

        return world_graph

    def _create_agents(self, town_people: dict, world_graph: nx.Graph) -> list[Agent]:
        """Create Agent instances from town people data."""
        agents: list[Agent] = []
        for name, detail in town_people.items():
            starting_location = detail["starting_location"]
            if starting_location not in world_graph.nodes():
                print(f"Warning: Starting location {starting_location} for agent {name} is not in world_graph.")
            description = json.dumps(detail["description"])
            agents.append(Agent(name, description, starting_location, world_graph))
        return agents

    def _load_events(self, memory: AgentMemory, global_time: str, new_event: str | None = None) -> list[str]:
        """Load or prompt for global events.

        Args:
            memory: AgentMemory instance for event storage.
            global_time: Current simulation time string.
            new_event: Optional event string. If None, prompts via input().
        """
        if new_event is None:
            new_event = str(input("Please enter a new event: ") or "No new event.")
        if new_event == "No new event.":
            return [event_json["action"] for event_json in memory.load_events()["event"]]

        new_event_experience = {
            "agent_name": "global_event",
            "global_time": global_time,
            "action": f'In {global_time}: "{new_event}".',
            "exp_type": "event",
            "priority": 9,
        }
        memory.store(new_event_experience)
        return [event_json["action"] for event_json in memory.save_event(new_event_experience)["event"]]

    def _daily_planning(self, s: SimulationState, prompt_meta: str) -> None:
        """Execute daily planning for all agents."""
        assert self.logger is not None
        for agent in s.agents:
            recent_reflections = ""
            if self.config.reflection_include_in_planning:
                recent_reflections = s.memory.format_reflections(agent.name, 3)
            experience = agent.daily_planning(
                s.global_time, prompt_meta,
                s.memory.format_impressions(agent.name, 3),
                s.memory.format_recent(agent.name, s.memory.memory_limit),
                recent_reflections=recent_reflections,
            )
            s.memory.store(experience)
            self.logger.log_event("daily_plan", step=s.round, agent_id=agent.name,
                                  data={"plan": agent.daily_plans})
            self.logger.add_summary(f"{agent.name} plans:\n{agent.daily_plans}\n")

    def _hourly_planning(self, s: SimulationState, prompt_meta: str) -> None:
        """Execute hourly planning for all agents."""
        assert self.logger is not None
        for agent in s.agents:
            experience = agent.hourly_planning(
                s.agents, s.locations.get_location(agent.location),
                s.global_time, s.town_areas, prompt_meta,
                s.memory.format_impressions(agent.name, 3),
                s.memory.format_recent(agent.name, s.memory.memory_limit),
            )
            agent.related_things = s.memory.format_semantic(agent.name, agent.hourly_plan, 5)
            s.memory.store(experience)

            self.logger.log_event("hourly_plan", step=s.round, agent_id=agent.name,
                                  data={"plan": agent.hourly_plan})
            self.logger.log_debug(f"Related things:\n{agent.related_things}\n")
            self.logger.add_summary(f"{agent.name}'s hourly action:\n{agent.hourly_plan}\n")

    def _execute_actions(self, s: SimulationState, prompt_meta: str) -> None:
        """Execute planned actions and update memory."""
        assert self.logger is not None
        for agent in s.agents:
            gotten_impression = s.memory.format_impressions(agent.name, 3)
            action = agent.execute_action(
                s.global_time, prompt_meta, gotten_impression,
                s.memory.format_recent(agent.name, s.memory.memory_limit),
            )
            priority = agent.rate_experience(
                prompt_meta, gotten_impression,
                s.memory.format_recent(agent.name, s.memory.memory_limit), action,
            )
            experience = agent.memory_actions(s.agents, s.global_time, priority)
            s.memory.store(experience)

            self.logger.log_event("action", step=s.round, agent_id=agent.name,
                                  data={"action": action})
            self.logger.log_debug(f"{agent.name} gotten: {gotten_impression}\n")
            self.logger.add_summary(f"{agent.name} executes action: {action}\n")

    def _movement(self, s: SimulationState, prompt_meta: str) -> None:
        """Rate locations and move agents."""
        assert self.logger is not None
        for agent in s.agents:
            place_ratings = agent.rate_locations(
                s.locations, s.global_time, prompt_meta,
                s.memory.format_impressions(agent.name, 3),
                s.memory.format_recent(agent.name, s.memory.memory_limit),
            )

            self.logger.log_event("location_ratings", step=s.round, agent_id=agent.name,
                                  data={"ratings": str(place_ratings)})

            old_location = agent.location
            new_location_name = place_ratings[0][0]
            if new_location_name != agent.location:
                agent.move(new_location_name)
                agent.memory_location_change(s.global_time, old_location, new_location_name)
                save_location_change(s.project_folder, agent.name, new_location_name)
                self.logger.log_event("movement", step=s.round, agent_id=agent.name,
                                      data={"from": old_location, "to": new_location_name})

    def _impressions(self, s: SimulationState, prompt_meta: str) -> None:
        """Form recent impressions for all agents."""
        assert self.logger is not None
        for agent in s.agents:
            impression = agent.form_impression(
                s.global_time, prompt_meta,
                s.memory.format_recent(agent.name, s.memory.memory_limit),
            )
            s.memory.store(impression)
            self.logger.log_event("impression", step=s.round, agent_id=agent.name,
                                  data={"impression": impression["action"]})
            self.logger.add_summary(f"{agent.name}'s recent impression: {impression['action']}\n")

    def _run_reflection(
        self, s: SimulationState, agent: Agent, trigger: str
    ) -> None:
        """Run the reflection cycle for a single agent via ReflectionEngine."""
        assert self.logger is not None
        assert self.reflection_engine is not None
        observations = self.reflection_engine.run_reflection_cycle(
            agent, s.global_time, s.agents,
        )
        for obs in observations:
            s.memory.store(obs)
            if obs.get("exp_type") == "reflection":
                agent.reflection = obs.get("action", "")
            self.logger.log_event(
                "reflection",
                step=s.round,
                agent_id=agent.name,
                data={
                    "reflection": obs.get("action", ""),
                    "type": obs.get("reflection_type", "daily"),
                    "trigger": trigger,
                },
            )
            self.logger.add_summary(f"\n{obs.get('action', '')}\n")
