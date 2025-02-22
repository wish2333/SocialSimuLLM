# simulation\agents\agent.py

# -*- coding: utf-8 -*-
"""
First version created on 2025-02-19 19:37.

@author: Huang Miaosen

Comment format: Use standard Google style docstring format for comments, bilingual in English and Chinese (note to write English comments first), compatible with VSCode intelligent prompts.
"""

from utils.text_generation import GPT_request
from prompt_templates.template_agents import *
# from agents.memory import * #Not needed, memory module maintains
from agents.memory import *
from agents.movement import *
from types import MethodType
import time
import re



class Agent:
    """A class to represent an individual agent in a simulation similar to The Sims.
    一个模拟The Sims中的智能个体的类。

    Attributes(待更新):
        name (str): 
            The name of the agent. 
            代理的名称。
        description (str): 
            A brief description of the agent. 
            代理的简要描述。
        location (str): 
            The current location of the agent in the simulated environment. 
            代理在模拟环境中的当前位置。
        memory (list): 
            A list of memory the agent has about their interactions. 
            代理关于其互动的记忆列表。
        compressed_memory (list): 
            A list of compressed memory that summarize the agent's experiences. 
            总结代理经历的压缩记忆列表。
        plans (str): 
            The agent's daily plans, generated at the beginning of each day. 
            代理的每日计划，在每天开始时生成。

    Methods(待更新):
        plan(global_time: int, town_people: list, prompt_meta: str) -> str:
            Generates the agent's daily plan.
            根据当前时间和城镇中的人物生成代理的每日计划。

        execute_action(agents: list, location: 'Location', global_time: int, 
                        town_areas: dict, prompt_meta: str) -> str:
            Executes the agent's action based on their current situation and interactions with other agents.
            根据当前情境和其他代理的互动执行代理的动作。

        update_memory(agents: list, global_time: int, action_results: dict) -> None:
            Updates the agent's memory based on their interactions with other agents.
            根据与其他代理的互动更新代理的记忆。

        compress_memory(memory_ratings: dict, global_time: int, MEMORY_LIMIT: int = 10) -> None:
            Compresses the agent's memory to a more manageable and relevant set.
            将代理的记忆压缩为更易于管理和相关的一组。

        rate_locations(locations: list, town_areas: dict, global_time: int, prompt_meta: str) -> dict:
            Rates different locations in the simulated environment based on the agent's preferences and experiences.
            根据代理的偏好和经历对模拟环境中的不同地点进行评分。
    """
    def __init__(self, name, description, starting_location, world_graph):
        self.name = name
        self.description = description
        self.location = starting_location

        # self.memory_ratings = []  #Not needed, memory module maintains
        # self.memory = []  #Not needed, memory module maintains
        # self.compressed_memory = []  #Not needed, memory module maintains
        self.daily_plans = ""
        self.hourly_plan = ""
        self.impression = ""
        self.hourly_action_prompt = ""
        self.action = ""
        self.world_graph = world_graph

        self.rate_locations = MethodType(rate_locations, self)
        self.move = MethodType(move, self)
        self.memory_location_change = MethodType(memory_location_change, self)
        self.rate_experience = MethodType(rate_experience, self)
        self.memory_actions = MethodType(memory_actions, self)
        self.memory_daily_plans = MethodType(memory_daily_plans, self)
        self.memory_hourly_plan = MethodType(memory_hourly_plan, self)
        self.memory_impression = MethodType(memory_impression, self)
        # self.update_memory = MethodType(update_memory, self) #Not needed, memory module maintains
        # self.compress_memory = MethodType(compress_recent_impressions, self) #Not needed, memory module maintains
        # self.memory = Memory(project_folder, self) #Not needed, memory module maintains

    def __repr__(self):
        return f"Agent({self.name}, {self.description}, {self.location})"
    
    def init_memory(self, daily_plans, hourly_plan):
        self.daily_plans = daily_plans
        self.hourly_plan = hourly_plan
        # self.impression = impression

    def daily_planning(self, global_time, prompt_meta, recent_impressions, newthings):
        """
        Generates the agent's daily plan.

        Args:
            recent_impressions (list): A list of recent impressions.
                                    近期的印象列表。
            global_time (int): The current time in the simulation.
                            当前模拟时间。
            prompt_meta (str): The prompt used to generate the plan.
                            用于生成计划的提示。

        Returns:
            None: This method updates the self.daily_plans attribute but does not return any value.
                该方法会更新self.daily_plans属性，但不返回任何值。
        """
        system = agent_plan_system.format(self.name, self.description, recent_impressions, newthings)
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
        """Executes the agent's action based on their current situation and interactions with other agents.
        根据代理当前的位置、时间、环境以及与其他代理的交互情况，
        生成并执行相应的动作。

        Args:
            agents (list): 
                A list of other Agent objects in the simulation.
                模拟中的其他代理对象列表。
            location (Location): 
                The current Location object where the agent is located.
                代理当前所在的位置对象。
            global_time (int): 
                The current time in the simulation.
                模拟中的当前时间。
            town_areas (dict): 
                A dictionary of Location objects representing different areas in the simulated environment.
                表示模拟环境中不同区域的Location对象字典。
            prompt_meta (str): 
                The prompt used to generate the action.
                用于生成动作的提示信息。

        Returns:
            str: 
                The action executed by the agent.
                由代理执行的动作描述字符串。

        Example:
            >>> agent.execute_action(agents=[agent1, agent2], 
                                    location=current_location,
                                    global_time=12345,
                                    town_areas=town_map,
                                    prompt_meta="Go to the store")
        """

        people = [agent.name for agent in agents if agent.location == location]

        system = hourly_planning_system.format(self.name, self.description, recent_impressions, newthings, self.daily_plans)

        prompt = hourly_planning_prompt.format(location.name, town_areas[location.name], str(global_time), ', '.join(people))
        people_description = [f"{agent.name}: {agent.description}" for agent in agents if agent.location == location.name]
        prompt += ' You know the following about people: ' + '. '.join(people_description)
        self.hourly_action_prompt = prompt.replace(str(global_time), '{}') # Replace the global time with {} to make it flexible for execute_action().
        prompt += "You can choose to interact with them or not. What do you do in the next hour? Use at most 20 words to explain."

        self.hourly_plan = GPT_request(system, prompt_meta.format(prompt), gpt_parameter={"max_tokens": 30})
        experience = self.memory_hourly_plan(global_time)
        return experience
    
    def execute_action(self, global_time, prompt_meta, recent_impressions, nearby_situations):
        """
        Executes an action for the agent based on the global time, prompt metadata, recent impressions, and nearby situations.

        根据全局时间、提示元数据、最近的印象和附近的情况，为代理执行一个动作。

        Args:
            global_time (int): The current global time in the simulation.
                模拟中的当前全局时间。
            prompt_meta (str): The metadata template for the prompt.
                提示的元数据模板。
            recent_impressions (list): A list of recent impressions on the agent.
                代理最近的印象列表。
            nearby_situations (list): A list of situations near the agent.
                代理附近的情况列表.

        Returns:
            None: This method updates the self.action attribute but does not return any value.
            仅更新self.action属性，但不返回任何值。
        """
        system = agent_execute_action_system.format(self.name, self.description, recent_impressions, self.daily_plans)
        hourly_prompt = self.hourly_action_prompt.format(str(global_time))
        prompt = agent_execute_action_prompt.format(hourly_prompt, self.hourly_plan, nearby_situations)
        self.action = GPT_request(system, prompt_meta.format(prompt), gpt_parameter={"max_tokens": 80})
        return self.action
    
    def form_impression(self, global_time, prompt_meta, nearby_situations):
        """
        Forms an impression for the agent based on the global time, prompt metadata, recent impressions, and nearby situations.
        """
        system = agent_impressions_system
        prompt = agent_impressions_prompt.format(self.name, self.description, self.daily_plans, global_time, nearby_situations)
        self.impression = GPT_request(system, prompt_meta.format(prompt), gpt_parameter={"max_tokens": 50})
        experience = self.memory_impression(global_time, self.impression)
        return experience

