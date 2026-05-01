# socialsimullm/agents/agent.py

# -*- coding: utf-8 -*-
"""
First version created on 2025-02-19 19:37.

@author: Huang Miaosen

Comment format: Use standard Google style docstring format for comments, bilingual in English and Chinese (note to write English comments first), compatible with VSCode intelligent prompts.
"""

from socialsimullm.utils.text_generation import GPT_request
from socialsimullm.prompt_templates.template_agents import *
from socialsimullm.agents.memory import *
from socialsimullm.agents.movement import *
from types import MethodType
import time
import re



class Agent:
    """A class to represent an individual agent in a simulation similar to The Sims.
    A class that simulates intelligent individuals like in The Sims.

    Attributes:
        name (str):
            The name of the agent.
        description (str):
            A brief description of the agent.
        location (str):
            The current location of the agent in the simulated environment.
        daily_plans (str):
            The agent's daily plans, generated at the beginning of each day.

    Methods:
        plan(global_time: int, town_people: list, prompt_meta: str) -> str:
            Generates the agent's daily plan.

        execute_action(agents: list, location: 'Location', global_time: int,
                        town_areas: dict, prompt_meta: str) -> str:
            Executes the agent's action based on their current situation and interactions with other agents.

        rate_locations(locations: list, town_areas: dict, global_time: int, prompt_meta: str) -> dict:
            Rates different locations in the simulated environment based on the agent's preferences and experiences.
    """
    def __init__(self, name, description, starting_location, world_graph):
        self.name = name
        self.description = description
        self.location = starting_location

        self.daily_plans = ""
        self.hourly_plan = ""
        self.impression = ""
        self.hourly_action_prompt = ""
        self.action = ""
        self.reflection = ""
        self.world_graph = world_graph

        self.related_things = ""
        self.event = []

        self.rate_locations = MethodType(rate_locations, self)
        self.move = MethodType(move, self)
        self.memory_location_change = MethodType(memory_location_change, self)
        self.rate_experience = MethodType(rate_experience, self)
        self.memory_actions = MethodType(memory_actions, self)
        self.simplify_action = MethodType(simplify_action, self)
        self.memory_daily_plans = MethodType(memory_daily_plans, self)
        self.memory_hourly_plan = MethodType(memory_hourly_plan, self)
        self.memory_impression = MethodType(memory_impression, self)
        self.memory_reflection = MethodType(memory_reflection, self)

    def __repr__(self):
        return f"Agent({self.name}, {self.description}, {self.location})"

    def init_memory(self, daily_plans, hourly_plan, event:list):
        self.daily_plans = daily_plans
        self.hourly_plan = hourly_plan
        self.event = ";".join(event)

    def daily_planning(self, global_time, prompt_meta, recent_impressions, newthings):
        """
        Generates the agent's daily plan.
        """
        system = agent_plan_system.format(self.name, self.description, self.event, recent_impressions, newthings)
        global_hour = global_time.split(':')[0]
        prompt = agent_plan_prompt.format(str(global_hour))
        self.daily_plans = GPT_request(system, prompt_meta.format(prompt), gpt_parameter={"max_tokens": 300})
        experience = self.memory_daily_plans(global_time)
        return experience


    def hourly_planning(self,
                    agents: list,
                    location,
                    global_time: int,
                    town_areas: dict,
                    prompt_meta: str,
                    recent_impressions: str,
                    newthings: str) -> dict:
        people = [agent.name for agent in agents if agent.location == location]
        system = hourly_planning_system.format(self.name, self.description, recent_impressions, newthings, self.daily_plans)
        prompt = hourly_planning_prompt.format(location.name, town_areas[location.name], str(global_time), ', '.join(people))
        people_description = [f"{agent.name}: {agent.description}" for agent in agents if agent.location == location.name]
        prompt += ' You know the following about people: ' + '. '.join(people_description)
        self.hourly_action_prompt = prompt.replace(str(global_time), '{}') # Replace the global time with {} to make it flexible for execute_action().
        prompt += "You can choose to interact with them or not. What do you do in the next hour? Use at most 20 words to explain."

        self.hourly_plan = GPT_request(system, prompt_meta.format(prompt), gpt_parameter={"max_tokens": 45})
        experience = self.memory_hourly_plan(global_time)
        return experience

    def execute_action(self, global_time, prompt_meta, recent_impressions, nearby_situations):
        """
        Executes an action for the agent based on the global time, prompt metadata, recent impressions, and nearby situations.

        Args:
            global_time (int): The current global time in the simulation.
            prompt_meta (str): The metadata template for the prompt.
            recent_impressions (list): A list of recent impressions on the agent.
            nearby_situations (list): A list of situations near the agent.

        Returns:
            None: This method updates the self.action attribute but does not return any value.
        """
        system = agent_execute_action_system.format(self.name, self.description, self.event, recent_impressions, self.daily_plans)
        hourly_prompt = self.hourly_action_prompt.format(str(global_time))
        prompt = agent_execute_action_prompt.format(hourly_prompt, self.hourly_plan, self.related_things, nearby_situations)
        self.action = GPT_request(system, prompt_meta.format(prompt), gpt_parameter={"max_tokens": 80})
        return self.action

    def form_impression(self, global_time, prompt_meta, nearby_situations):
        """
        Forms an impression for the agent based on the global time, prompt metadata, recent impressions, and nearby situations.
        """
        system = agent_impressions_system.format(self.name, self.description)
        prompt = agent_impressions_prompt.format(self.daily_plans, global_time, nearby_situations)
        self.impression = GPT_request(system, prompt_meta.format(prompt), gpt_parameter={"max_tokens": 80})
        experience = self.memory_impression(global_time, self.impression)
        return experience

    def form_reflection(self, global_time, prompt_meta, recent_reflection, important_things):
        """
        Forms a reflection for the agent based on the global time, prompt metadata, recent impressions, and nearby situations.
        """
        system = agent_reflection_system.format(self.name, self.description, recent_reflection, self.daily_plans)
        prompt = agent_reflection_prompt.format(important_things)
        self.reflection = GPT_request(system, prompt_meta.format(prompt), gpt_parameter={"max_tokens": 120})
        experience = self.memory_reflection(global_time, self.reflection)
        return experience
