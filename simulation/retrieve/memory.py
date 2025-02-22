# simulation\retrieve\memory.py

# -*- coding: utf-8 -*-

"""
First version created on 2025-02-20 13:46.

@author: Huang Miaosen

Comment format: Use standard Google style docstring format for comments, bilingual in English and Chinese (note to write English comments first), compatible with VSCode intelligent prompts.
"""

import os
import json
import sqlite3
from utils.text_generation import get_embedding

class Memory:
    """
    This class represents the memory of the agent. It stores the past experiences and can be used to generate new experiences.
    """

    def __init__(self, project_folder, agents, memory_limit):
        """
        Initialize the memory.
        """
        self.memory_limit = memory_limit
        self.project_folder = project_folder
        self.agents = agents

    def load_memory_file(self, agent_name):
        memory_name = agent_name + '_memory.json'
        memory_file = os.path.join(self.project_folder, 'agent_data',
                                    memory_name)
        with open(memory_file, 'r') as f:
            memory = json.load(f)
        return memory

    def save_memory_file(self, agent_name, memory):
        memory_name = agent_name + '_memory.json'
        memory_file = os.path.join(self.project_folder, 'agent_data',
                                    memory_name)
        with open(memory_file, 'w') as f:
            json.dump(memory, f, indent=4)

    def add_experience(self, experience, exp_type):
        if exp_type == 'action':
            other_agents = experience['other_agents']
            for agent in self.agents:
                if agent.name in other_agents:
                    agent_memory_full = self.load_memory_file(agent.name)
                    agent_memory = agent_memory_full['memory']
                    agent_memory.append(experience)
                    agent_memory_full['memory'] = agent_memory
                    self.save_memory_file(agent.name, agent_memory_full)
        if exp_type == 'plan' or exp_type == 'thought':
            agent_name = experience['agent_name']
            agent_memory_full = self.load_memory_file(agent_name)
            agent_memory = agent_memory_full['memory']
            agent_memory.append(experience)
            agent_memory_full['memory'] = agent_memory
            self.save_memory_file(agent_name, agent_memory_full)
        if exp_type == 'event':
            for agent in self.agents:
                agent_memory_full = self.load_memory_file(agent.name)
                agent_memory = agent_memory_full['memory']
                agent_memory.append(experience)
                agent_memory_full['memory'] = agent_memory
                self.save_memory_file(agent.name, agent_memory_full)
        # self.sort_memory(experience['agent_name'], experience['action'])

    def get_init_memory(self, agent_name):
        agent_memory_full = self.load_memory_file(agent_name)
        agent_memory = agent_memory_full['memory']
        daily_plans = [plan for plan in agent_memory if plan['exp_type'] == 'plan' and plan['priority'] == 3]
        last_daily_plan = daily_plans[-1] if daily_plans else {"action": ""}
        hourly_plans = [plan for plan in agent_memory if plan['exp_type'] == 'plan' and plan['priority'] == 2]
        last_hourly_plan = hourly_plans[-1] if hourly_plans else {"action": ""}
        # impressions = [impression for impression in agent_memory if impression['exp_type'] == 'thought' and impression['priority'] == 4]
        # last_impression_list = impressions[-3:]
        # last_impression_str = '\n'.join(item['action'] for item in last_impression_list)
        return [last_daily_plan['action'], last_hourly_plan['action']]

    def get_newthings(self, agent_name, num_experiences):
        agent_memory_full = self.load_memory_file(agent_name)
        agent_memory = agent_memory_full['memory']
        action_memory = [action for action in agent_memory if action['exp_type'] == 'action']
        return action_memory[-num_experiences:]

    def get_newthings_str(self, agent_name, num_experiences):
        newthings = self.get_newthings(agent_name, num_experiences)
        newthings_str = f"'\n'.join(item['action'] for item in {newthings}\n"
        return newthings_str
    
    def get_importants(self, agent_name, num_experiences):
        agent_memory_full = self.load_memory_file(agent_name)
        agent_memory = agent_memory_full['memory']
        action_memory = [action for action in agent_memory if action['exp_type'] == 'action']
        importants_memory = [action for action in action_memory if action['priority'] > 4]
        importants = importants_memory[-num_experiences:]
        return importants
    
    def get_impressions(self, agent_name, num_experiences):
        agent_memory_full = self.load_memory_file(agent_name)
        agent_memory = agent_memory_full['memory']
        impressions = [impression for impression in agent_memory if impression['exp_type'] == 'thought' and impression['priority'] == 4]
        return impressions[-num_experiences:]

    def get_impressions_str(self, agent_name, num_experiences):
        impressions = self.get_impressions(agent_name, num_experiences)
        impressions_str = f"'\n'.join(item['action'] for item in {impressions}\n"
        return impressions_str

    # def sort_memory(self, agent_name, action):
    #     """
    #     Sort the memory by embedding the action and storing it in the agent's SQLite database.
    #     """
    #     action_embedding = self.embed_action(action)
    #     self.store_embedding_in_database(agent_name, action, action_embedding)

    # def embed_action(self, action):
    #     """
    #     Embed the action using a pre-trained model or API.
    #     """
    #     embedding = get_embedding(action)
    #     return embedding

    # def store_embedding_in_database(self, agent_name, action, embedding):
    #     """
    #     Store the action embedding in the agent's SQLite database.
    #     """
    #     embedding = json.dumps(embedding)
    #     db_file = os.path.join(self.project_folder, 'agent_data', f"{agent_name}_memory.db")
    #     conn = sqlite3.connect(db_file)
    #     cursor = conn.cursor()
    #     cursor.execute('''
    #         CREATE TABLE IF NOT EXISTS action_embeddings (
    #             action_description TEXT,
    #             action_embedding TEXT
    #         )
    #     ''')
    #     cursor.execute('''
    #         INSERT INTO action_embeddings (action_description, action_embedding)
    #         VALUES (?, ?)
    #     ''', (action, embedding))
    #     conn.commit()
    #     conn.close()