# simulation\agents\memory.py

# -*- coding: utf-8 -*-
"""
First version created on 2025-02-20 15:27.

@author: Huang Miaosen

Comment format: Use standard Google style docstring format for comments, bilingual in English and Chinese (note to write English comments first), compatible with VSCode intelligent prompts.
"""

from utils.text_generation import GPT_request, get_rating, get_embedding
from prompt_templates.template_agents import *


    # def update_memory(self, agents, global_time, action_results):
    #     """
    #     Updates the agent's memory based on their interactions with other agents.
    #     根据与其他代理的互动更新代理的记忆。

    #     Args:
    #         global_time (int): The current time in the simulation.
    #                                     模拟中的当前时间。
    #         action_results (dict): A dictionary of the results of each agent's action.
    #                                     每个代理行动结果的字典。

    #     Returns:
    #         None: This method does not return any value.
    #             此方法不返回任何值。
    #     """
    #     self.memory.update_memory(self, agents, global_time, action_results)

def rate_experience(self, prompt_meta, recent_impressions, nearby_situations, experience):
    """
    Rates the agent's experience based on the agent's preferences and experiences.
    """
    system = rate_experiences_system
    prompt = rate_experiences_prompt.format(self.name, self.description, recent_impressions, nearby_situations, experience)
    res = GPT_request(system, prompt_meta.format(prompt), {"max_tokens": 5, "temperature": 0.7})
    rating = get_rating(res)
    return rating



def memory_actions(self, agents, global_time, priority):
    """
    Formats the agent's experience based on the agent's preferences and experiences.
    """
    other_agents = []
    for agent in agents:
        if agent.location == self.location:
            other_agents.append(agent.name)
    # experience = [self.name, global_time, self.location, self.action, other_agents, exp_type]
    experience={
        "agent_name": self.name,
        "global_time": global_time,
        "location": self.location,
        "action": f"In {global_time}, {self.name} ,at {self.location}, has done: \"{self.action}\"",
        "other_agents": other_agents,
        "exp_type": 'action',
        "priority": priority
    }
    return experience
    
def memory_daily_plans(self, global_time):
    experience={
        "agent_name": self.name,
        "global_time": global_time,
        "location": self.location,
        "action": f"{self.name}'s daily plan is:\n{self.daily_plans}",
        "other_agents": [self.name],
        "exp_type": 'plan',
        "priority": 3
    }
    return experience

def memory_hourly_plan(self, global_time):
    experience={
        "agent_name": self.name,
        "global_time": global_time,
        "location": self.location,
        "action": f"{self.name}'s hourly plan is:\n{self.hourly_plan}",
        "other_agents": [self.name],
        "exp_type": 'plan',
        "priority": 2
    }
    return experience

def memory_location_change(self, global_time, old_location, new_location):
    experience={
        "agent_name": self.name,
        "global_time": global_time,
        "location": old_location,
        "action": f"In {global_time}, {self.name} has moved from {old_location} to {new_location}.",
        "other_agents": [self.name],
        "exp_type": 'action',
        "priority": 2
    }
    return experience

def memory_impression(self, global_time, impression):
    experience={
        "agent_name": self.name,
        "global_time": global_time,
        "location": self.location,
        "action": f"In {global_time}, {self.name} ,at {self.location}, has impressed: \"{impression}\".",
        "other_agents": [self.name],
        "exp_type": 'thought',
        "priority": 4
    }
    return experience
