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
import numpy as np

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
                    self.sort_memory(experience['agent_name'], experience['action_des'])
        elif exp_type == 'plan' or exp_type == 'thought':
            agent_name = experience['agent_name']
            agent_memory_full = self.load_memory_file(agent_name)
            agent_memory = agent_memory_full['memory']
            agent_memory.append(experience)
            agent_memory_full['memory'] = agent_memory
            self.save_memory_file(agent_name, agent_memory_full)
        elif exp_type == 'event':
            for agent in self.agents:
                agent_memory_full = self.load_memory_file(agent.name)
                agent_memory = agent_memory_full['memory']
                agent_memory.append(experience)
                agent_memory_full['memory'] = agent_memory
                self.save_memory_file(agent.name, agent_memory_full)
        elif exp_type == 'reflection':
            agent_name = experience['agent_name']
            agent_memory_full = self.load_memory_file(agent_name)
            agent_memory = agent_memory_full['memory']
            agent_memory.append(experience)
            agent_memory_full['memory'] = agent_memory
            self.save_memory_file(agent_name, agent_memory_full)
            self.sort_memory(experience['agent_name'], experience['action'])

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
        things = [
            action.get('action_des', 'No new things recorded')
            for action in newthings
        ]
        return "\n".join(things)
    
    def get_importants(self, agent_name, global_time):
        day_str = global_time.split(',')[0]
        agent_memory_full = self.load_memory_file(agent_name)
        agent_memory = agent_memory_full['memory']
        daily_importants = [item for item in agent_memory if item['exp_type'] == 'action' and int(item.get('priority', 1) or 1) > 6 and item['global_time'].split(',')[0] == day_str]
        return daily_importants
    
    def get_importants_str(self, agent_name, global_time):
        daily_importants = self.get_importants(agent_name, global_time)
        actions = [
            item.get('action_des', 'No important things recorded')
            for item in daily_importants
        ]
        return '\n'.join(actions)
        
    
    def get_impressions(self, agent_name, num_experiences):
        agent_memory_full = self.load_memory_file(agent_name)
        agent_memory = agent_memory_full['memory']
        impressions = [impression for impression in agent_memory if impression['exp_type'] == 'thought' and impression['priority'] == 4]
        return impressions[-num_experiences:]

    def get_impressions_str(self, agent_name, num_experiences):
        impressions = self.get_impressions(agent_name, num_experiences)
        actions = [
            item.get('action', 'No impression recorded') 
            for item in impressions
        ]
        return '\n'.join(actions)

    def sort_memory(self, agent_name, action):
        """
        Sort the memory by embedding the action and storing it in the agent's SQLite database.
        """
        action_embedding = self.embed_action(action)
        self.store_embedding_in_database(agent_name, action, action_embedding)

    def embed_action(self, action):
        """
        Embed the action using a pre-trained model or API.
        """
        embedding = get_embedding(action)
        return embedding

    def store_embedding_in_database(self, agent_name, action, embedding):
        """
        Store the action embedding in the agent's SQLite database.
        """
        embedding = json.dumps(embedding)
        db_file = os.path.join(self.project_folder, 'agent_data', f"{agent_name}_memory.db")
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS action_embeddings (
                action_index INTEGER
                action_description TEXT,
                action_embedding TEXT
            )
        ''')
        cursor.execute('SELECT MAX(action_index) FROM action_embeddings')
        max_index = cursor.fetchone()[0] or 0
        cursor.execute('''
            INSERT INTO action_embeddings (action_index, action_description, action_embedding)
            VALUES (?, ?, ?)
        ''', (max_index+1, action, embedding))
        conn.commit()
        conn.close()

    def get_related_things(self, agent_name, hourly_plan, num_related_things):
        """
        Get related things to the hourly plan.
        """
        plan_embedding = self.embed_action(hourly_plan)

        db_file = os.path.join(self.project_folder, 'agent_data', f"{agent_name}_memory.db")
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT action_description, action_embedding
            FROM action_embeddings
            ORDER BY action_index DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        agent_memory_full = self.load_memory_file(agent_name)
        agent_memory = agent_memory_full['memory']
        action_memory = []
        for item1 in agent_memory:
            if item1['exp_type'] == 'action':
                action_memory.append(item1)
            if item1['exp_type'] == 'thought' and item1['priority'] == 7:
                action_memory.append(item1)
        action_map = {item['action_des']: item for item in action_memory}

        weights = {
            'similarity': 0.5,
            'recency': 0.3,
            'importance': 0.2
        }

        scored_actions = []
        for idx, (action_des, emb_json) in enumerate(rows):
            if action_des not in action_map:
                continue
            action = action_map[action_des]
            action_embedding = np.array(json.loads(emb_json))
            similarity = np.dot(plan_embedding, action_embedding)/(np.linalg.norm(plan_embedding)*np.linalg.norm(action_embedding))
            recency = 1 - (idx/len(rows))
            importance = int(action.get('priority') or 1)
            normalized_importance = (min(max(importance, 1), 9) - 1) / 8
            score = weights['similarity']*similarity + weights['recency']*recency + weights['importance']*normalized_importance + 0.0001
            scored_actions.append((score, action))
            scored_actions.sort(reverse=True, key=lambda x: x[0])
        
        return [item[1] for item in scored_actions[:num_related_things]]
    
    def get_related_things_str(self,agent_name, hourly_plan, num_related_things):
        related_things = self.get_related_things(agent_name, hourly_plan, num_related_things)
        actions = [
            item.get('action_des', 'No related things recorded')
            for item in related_things
        ]
        return '\n'.join(actions)

            

        
        