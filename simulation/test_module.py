from agents.memory import *
from agents.movement import rate_locations

class Agent:
    def __init__(self, name, description, starting_location, world_graph):
        self.name = name
        self.description = description
        self.location = starting_location
        self.memory_ratings = []
        self.memories = []
        self.compressed_memories = []
        self.daily_plans = ""
        self.hourly_plans = ""
        self.hourly_action_prompt = ""
        self.world_graph = world_graph
        self.rate_locations = rate_locations