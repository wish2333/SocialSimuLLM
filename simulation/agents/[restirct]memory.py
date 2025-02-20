# simulation\agents\memory.py

# -*- coding: utf-8 -*-
"""
First version created on 2025-02-19 19:37.
Restricted on 2025-02-20 13:12. The same logic is moved to the retrieve module.

@author: Huang Miaosen

Comment format: Use standard Google style docstring format for comments, bilingual in English and Chinese (note to write English comments first), compatible with VSCode intelligent prompts.
"""

from utils.text_generation import GPT_request, get_rating, get_embedding
import os
import json






def update_memories(self, agents, global_time, action_results):
    """
    Updates the agent's recent impressions based on their interactions with other agents.
    基于与其他代理的互动更新代理的记忆。

    Args:
        agents (list[Agent]): A list of other Agent objects in the simulation.
                                    模拟中的其他代理对象列表。
        global_time (int): The current time in the simulation.
                            模拟中的当前时间。
        action_results (dict): A dictionary of the results of each agent's action.
                            每个代理行动结果的字典。

    Returns:
        None: This method does not return any value.
            此方法不返回任何值。
    """

    memory_item = {'Time': str(global_time), 'Person': agent.name,'Memory': action_results[agent.name]}
    for agent in agents:
        if agent.location == self.location:
            self.memories.append(memory_item)
def compress_recent_impressions(self, global_time, MEMORY_LIMIT=10):
    """
    Compresses the agent's recent impressions to a more manageable and relevant set.
    压缩代理的短期记忆，使其更加简洁和相关。

    Args:
        global_time (int): The current time in the simulation.
                        模拟中的当前时间。
        MEMORY_LIMIT (int, optional): The maximum number of memories to compress. Default is 10.
                                    压缩的最大记忆数量。默认为10。

    Returns:
        memory_string (str): The compressed memory string.
                            压缩后短期记忆的字符串。
    """
    # Keep only the latest MEMORY_LIMIT memories
    if len(self.memories) > MEMORY_LIMIT:
        self.recent_impressions = self.memories[-MEMORY_LIMIT:]
    recent_impressions_string_compressed = '.'.join(self.recent_impressions)
    return '[Recollection at Time {}: {}]'.format(str(global_time), recent_impressions_string_compressed)

class Memory:
    """
    A class to load and store the agent's memories.
    """
    def __init__(self, project_folder, agent):
        self.project_folder = project_folder
        self.agent = agent
        self.memory_file = agent.name + '_memories.json'
        self.memory_path = os.path.join(self.project_folder, 'agent_data', self.memory_file)
        if not os.path.exists(self.memory_path):
            memory_data = {'memories': []}
            with open(self.memory_path, 'w') as f:
                json.dump(memory_data, f)

    def load_memories(self):
        try:
            with open(self.memory_path, 'r') as f:
                memory_content = json.load(f)['memories']
                return memory_content
        except FileNotFoundError as e:
            print(f"Error occurred: {str(e)}")
            return f"ERROR: {str(e)}"
    def update_memories(self, agents, global_time, action_results):
        memory_item = {'Time': str(global_time), 'Person': self.agent.name,'Memory': action_results[self.agent.name]}
        for agent in agents:
            if agent.location == self.agent.location:
                loaded_memories = self.load_memories()
                memory_content = loaded_memories + [memory_item]
                memory_data = {'memories': memory_content}
                with open(self.memory_path, 'w') as f:
                    json.dump(memory_data, f)










