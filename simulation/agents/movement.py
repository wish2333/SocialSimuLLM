# simulation\agents\movement.py

# -*- coding: utf-8 -*-
"""
First version created on 2025-02-19 22:48.

@author: Huang Miaosen

Comment format: Use standard Google style docstring format for comments, bilingual in English and Chinese (note to write English comments first), compatible with VSCode intelligent prompts.
"""

from utils.text_generation import GPT_request, get_rating, get_embedding
import networkx as nx
from prompt_templates.template_agents import *

def rate_locations(self, locations, global_time, prompt_meta, recent_impressions, nearby_situations):

    """
    Rates different locations in the simulated environment based on the agent's preferences and experiences.
    
    Parameters:
    -----------
    locations : Locations
        The Locations object representing different areas in the simulated environment.
    global_time : int
        The current time in the simulation.
    prompt_meta : str
        The prompt used to rate the locations.

    Returns:
    --------
    place_ratings : list
        A list of tuples representing the location, its rating, and the generated response.

    """

    place_ratings = []
    for location in locations.locations.values():
        prompt = rate_location_prompt.format(self.name, self.hourly_plan, global_time, locations.get_location(self.location), self.description, recent_impressions, nearby_situations, location.name)
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

def move(self, new_location_name):
    if new_location_name == self.location:
        return self.location

    try:
        # Debug: Print source and target nodes
        # print(f"Source: {self.location}, Target: {new_location_name}")
        path = nx.shortest_path(self.world_graph, source=self.location, target=new_location_name)
        self.location = new_location_name
    except nx.NetworkXNoPath:
        print(f"No path found between {self.location} and {new_location_name}")
        return self.location
    except nx.NodeNotFound as e:
        print(f"Node not found: {e}")
        return self.location

    return self.location