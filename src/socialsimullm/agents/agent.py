# socialsimullm/agents/agent.py

# -*- coding: utf-8 -*-

"""
Agent class for social simulation entities.

All agent methods (planning, action, memory, movement) are defined as
proper class methods. No MethodType binding or wildcard imports.

@author: Huang Miaosen

Comment format: Use standard Google style docstring format for comments, bilingual in English and Chinese (note to write English comments first), compatible with VSCode intelligent prompts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import networkx as nx

from socialsimullm.prompt_templates.template_agents import (
    action_simpilfy_system,
    action_simpilfy_system_prompt,
    agent_execute_action_prompt,
    agent_execute_action_system,
    agent_impressions_prompt,
    agent_impressions_system,
    agent_plan_prompt,
    agent_plan_system,
    agent_reflection_prompt,
    agent_reflection_system,
    hourly_planning_prompt,
    hourly_planning_system,
    rate_experiences_prompt,
    rate_experiences_system,
    rate_location_prompt,
    rate_location_system,
)
from socialsimullm.utils.text_generation import GPT_request, get_rating

if TYPE_CHECKING:
    from socialsimullm.locations.locations import Locations


class Agent:
    """A class to represent an individual agent in a simulation similar to The Sims.

    Attributes:
        name: The name of the agent.
        description: A brief description of the agent.
        location: The current location of the agent.
        daily_plans: The agent's daily plans.
        hourly_plan: The agent's hourly plan.
        impression: The agent's recent impression.
        action: The agent's current action.
        reflection: The agent's latest reflection.
        world_graph: The NetworkX graph representing the world.
        related_things: Related memories retrieved for current context.
        event: Global events known to the agent.
    """

    def __init__(self, name: str, description: str, starting_location: str, world_graph: nx.Graph) -> None:
        self.name = name
        self.description = description
        self.location = starting_location

        self.daily_plans: str = ""
        self.hourly_plan: str = ""
        self.impression: str = ""
        self.hourly_action_prompt: str = ""
        self.action: str = ""
        self.reflection: str = ""
        self.world_graph: nx.Graph = world_graph

        self.related_things: str = ""
        self.event: str = ""

        self.place_ratings: list[tuple[str, int, str]] = []

    def __repr__(self) -> str:
        return f"Agent({self.name}, {self.description}, {self.location})"

    def init_memory(self, daily_plans: str, hourly_plan: str, event: list[str]) -> None:
        """Initialize agent memory with saved plans and events."""
        self.daily_plans = daily_plans
        self.hourly_plan = hourly_plan
        self.event = ";".join(event)

    # --- Planning methods ---

    def daily_planning(self, global_time: str, prompt_meta: str, recent_impressions: str, newthings: str) -> dict:
        """Generate the agent's daily plan."""
        system = agent_plan_system.format(self.name, self.description, self.event, recent_impressions, newthings)
        global_hour = global_time.split(":")[0]
        prompt = agent_plan_prompt.format(str(global_hour))
        self.daily_plans = GPT_request(system, prompt_meta.format(prompt), gpt_parameter={"max_tokens": 300})
        experience = self.memory_daily_plans(global_time)
        return experience

    def hourly_planning(
        self,
        agents: list[Agent],
        location: object,
        global_time: str,
        town_areas: dict,
        prompt_meta: str,
        recent_impressions: str,
        newthings: str,
    ) -> dict:
        """Generate the agent's hourly plan."""
        people = [agent.name for agent in agents if agent.location == location]
        system = hourly_planning_system.format(self.name, self.description, recent_impressions, newthings, self.daily_plans)
        prompt = hourly_planning_prompt.format(location.name, town_areas[location.name], str(global_time), ", ".join(people))
        people_description = [f"{agent.name}: {agent.description}" for agent in agents if agent.location == location.name]
        prompt += " You know the following about people: " + ". ".join(people_description)
        self.hourly_action_prompt = prompt.replace(str(global_time), "{}")
        prompt += "You can choose to interact with them or not. What do you do in the next hour? Use at most 20 words to explain."

        self.hourly_plan = GPT_request(system, prompt_meta.format(prompt), gpt_parameter={"max_tokens": 45})
        experience = self.memory_hourly_plan(global_time)
        return experience

    # --- Action execution ---

    def execute_action(self, global_time: str, prompt_meta: str, recent_impressions: str, nearby_situations: str) -> str:
        """Execute an action for the agent based on current context."""
        system = agent_execute_action_system.format(self.name, self.description, self.event, recent_impressions, self.daily_plans)
        hourly_prompt = self.hourly_action_prompt.format(str(global_time))
        prompt = agent_execute_action_prompt.format(hourly_prompt, self.hourly_plan, self.related_things, nearby_situations)
        self.action = GPT_request(system, prompt_meta.format(prompt), gpt_parameter={"max_tokens": 80})
        return self.action

    def form_impression(self, global_time: str, prompt_meta: str, nearby_situations: str) -> dict:
        """Form an impression based on recent events."""
        system = agent_impressions_system.format(self.name, self.description)
        prompt = agent_impressions_prompt.format(self.daily_plans, global_time, nearby_situations)
        self.impression = GPT_request(system, prompt_meta.format(prompt), gpt_parameter={"max_tokens": 80})
        experience = self.memory_impression(global_time, self.impression)
        return experience

    def form_reflection(self, global_time: str, prompt_meta: str, recent_reflection: str, important_things: str) -> dict:
        """Form a reflection on the day's events."""
        system = agent_reflection_system.format(self.name, self.description, recent_reflection, self.daily_plans)
        prompt = agent_reflection_prompt.format(important_things)
        self.reflection = GPT_request(system, prompt_meta.format(prompt), gpt_parameter={"max_tokens": 120})
        experience = self.memory_reflection(global_time, self.reflection)
        return experience

    # --- Movement methods (from agents/movement.py) ---

    def rate_locations(
        self,
        locations: Locations,
        global_time: str,
        prompt_meta: str,
        recent_impressions: str,
        nearby_situations: str,
    ) -> list[tuple[str, int, str]]:
        """Rate different locations based on the agent's preferences.

        Returns:
            A list of (location_name, rating, response) sorted by rating descending.
        """
        place_ratings: list[tuple[str, int, str]] = []
        for location in locations.locations.values():
            prompt = rate_location_prompt.format(
                self.name, self.hourly_plan, global_time,
                locations.get_location(self.location), self.description,
                recent_impressions, nearby_situations, location.name,
            )
            res = GPT_request(rate_location_system, prompt_meta.format(prompt), {"max_tokens": 5, "temperature": 0.7})
            rating = get_rating(res)
            max_attempts = 2
            current_attempt = 0
            while rating is None and current_attempt < max_attempts:
                rating = get_rating(res)
                current_attempt += 1
            if rating is None:
                rating = 0
            place_ratings.append((location.name, rating, res))
        self.place_ratings = place_ratings
        return sorted(place_ratings, key=lambda x: x[1], reverse=True)

    def move(self, new_location_name: str) -> str:
        """Move the agent to a new location via the world graph.

        Returns:
            The agent's current location after the move attempt.
        """
        if new_location_name == self.location:
            return self.location

        try:
            nx.shortest_path(self.world_graph, source=self.location, target=new_location_name)
            self.location = new_location_name
        except nx.NetworkXNoPath:
            print(f"No path found between {self.location} and {new_location_name}")
            return self.location
        except nx.NodeNotFound as e:
            print(f"Node not found: {e}")
            return self.location

        return self.location

    # --- Memory formatting methods (from agents/memory.py) ---

    def rate_experience(self, prompt_meta: str, recent_impressions: str, nearby_situations: str, experience: str) -> int | None:
        """Rate the poignancy/importance of a recent experience."""
        system = rate_experiences_system
        prompt = rate_experiences_prompt.format(self.name, self.description, recent_impressions, nearby_situations, experience)
        res = GPT_request(system, prompt_meta.format(prompt), {"max_tokens": 5, "temperature": 0.7})
        rating = get_rating(res)
        return rating

    def memory_actions(self, agents: list[Agent], global_time: str, priority: int | None) -> dict:
        """Format the agent's current action as a memory experience dict."""
        other_agents = [agent.name for agent in agents if agent.location == self.location]
        action_des = self.simplify_action()
        return {
            "agent_name": self.name,
            "global_time": global_time,
            "location": self.location,
            "action": f'In {global_time}, {self.name} ,at {self.location}, has done: "{self.action}"',
            "action_des": action_des,
            "other_agents": other_agents,
            "exp_type": "action",
            "priority": priority,
        }

    def simplify_action(self) -> str:
        """Simplify the current action into 1-2 SVO sentences."""
        system = action_simpilfy_system
        prompt = action_simpilfy_system_prompt.format(self.name, self.action)
        prompt_meta = "### Instruction:\n{}\n### Response:"
        prompt = prompt_meta.format(prompt)
        res = GPT_request(system, prompt, {"max_tokens": 30, "temperature": 0.7})
        return res

    def memory_daily_plans(self, global_time: str) -> dict:
        """Format daily plans as a memory experience dict."""
        return {
            "agent_name": self.name,
            "global_time": global_time,
            "location": self.location,
            "action": f"{self.name}'s daily plan is:\n{self.daily_plans}",
            "other_agents": [self.name],
            "exp_type": "plan",
            "priority": 3,
        }

    def memory_hourly_plan(self, global_time: str) -> dict:
        """Format hourly plan as a memory experience dict."""
        return {
            "agent_name": self.name,
            "global_time": global_time,
            "location": self.location,
            "action": f"{self.name}'s hourly plan is:\n{self.hourly_plan}",
            "other_agents": [self.name],
            "exp_type": "plan",
            "priority": 2,
        }

    def memory_location_change(self, global_time: str, old_location: str, new_location: str) -> dict:
        """Format a location change as a memory experience dict."""
        return {
            "agent_name": self.name,
            "global_time": global_time,
            "location": old_location,
            "action": f"In {global_time}, {self.name} has moved from {old_location} to {new_location}.",
            "action_des": f"{self.name} has moved from {old_location} to {new_location}.",
            "other_agents": [self.name],
            "exp_type": "action",
            "priority": 2,
        }

    def memory_impression(self, global_time: str, impression: str) -> dict:
        """Format an impression as a memory experience dict."""
        return {
            "agent_name": self.name,
            "global_time": global_time,
            "location": self.location,
            "action": f'In {global_time}, {self.name} ,at {self.location}, has impressed: "{impression}".',
            "action_des": f'{self.name} has impressed: "{impression}".',
            "exp_type": "thought",
            "priority": 4,
        }

    def memory_reflection(self, global_time: str, reflection: str) -> dict:
        """Format a reflection as a memory experience dict."""
        return {
            "agent_name": self.name,
            "global_time": global_time,
            "action": f'In {global_time}, {self.name} has reflected: "{reflection}".',
            "exp_type": "thought",
            "priority": 9,
        }
