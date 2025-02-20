# simulation\main.py

# -*- coding: utf-8 -*-

"""
First version created on Wed Sep 29 15:32:22 2021

@author: Huang Miaosen
"""

import os
import json
import networkx as nx
from agents.agent import Agent
from locations.locations import Locations
from utils.text_generation import summarize_simulation
from simulation.utils.global_methods import *

# Initialize global variables
prompt_meta = '### Instruction:\n{}\n### Response:'
global_time = 'Day 1, 08:00'
project_name = str(input("Please enter the project name: "))

log_locations = True
log_actions = True
log_plans = True
log_ratings = True
log_memories = True

print_locations = True
print_actions = True
print_plans = True
print_ratings = True
print_memories = False

summarize_locations = False
summarize_actions = True
summarize_plans = False
summarize_ratings = False
summarize_memories = True

log_output = ""
summary_input = ""

# Initialize agents and locations
agents = []
locations = Locations()

# Initialize module's variables


# Load project data
project_folder = os.path.join(os.getcwd(), "projects", project_name)
meta_data = load_meta_data(project_folder, project_name, global_time)
town_data = load_town_data(project_folder)

global_time = meta_data['global_time']
round = meta_data['round']
town_people = town_data['town_people']
town_areas = town_data['town_areas']

print(f"=== CONFIGURATIONS for {project_name} LOADED ===")

# Create a graph of town areas
world_graph = nx.Graph()

# Add nodes and edges to world_graph
for town_area in town_areas.keys():
    world_graph.add_node(town_area)

# Add edges between nodes
for i, town_area in enumerate(town_areas.keys()):
    world_graph.add_edge(town_area, town_area)  # Add an edge to itself
    if i > 0:
        world_graph.add_edge(town_area, list(town_areas.keys())[i - 1])

# Add the edge between the first and the last town areas to complete the cycle
world_graph.add_edge(list(town_areas.keys())[0], list(town_areas.keys())[-1])

# Debug: Print nodes in world_graph
print("Nodes in world_graph:", world_graph.nodes())

# Create agents
for name, description in town_people.items():
    starting_location = description['starting_location']
    if starting_location not in world_graph.nodes():
        print(f"Warning: Starting location {starting_location} for agent {name} is not in world_graph.")
    agents.append(Agent(name, description['description'], starting_location, world_graph))

for name, description in town_areas.items():
    locations.add_location(name, description)

print(f"=== LOCATIONS AT START OF SIMULATION ===")


# Start simulation loop
repeats = int(input("Please enter the number of repeats: "))
for repeat in range(repeats):
    #log_output for one repeat
    round += 1
    log_output = ""
    if global_time.split(":")[1] == "00":
        summary_input = ""
    print(f"====================== ROUND {round} ========================\n")
    log_output += f"====================== ROUND {round} ========================\n"
    if log_locations:
        log_output += f"=== LOCATIONS AT START OF ROUND {round} ===\n"
        log_output += str(locations) + "\n\n"
        if print_locations:
            print(f"=== LOCATIONS AT START OF ROUND {round} ===")
            print(str(locations) + "\n")
        if summarize_locations:
            summary_input += f"=== LOCATIONS AT START OF ROUND {round} ===\n"
            summary_input += str(locations) + "\n"


    
    # Whether to proceed with daily plan
    if global_time.split(", ")[1] == "08:00":
        for agent in agents:
            agent.daily_planning(global_time, prompt_meta, ['待修改'])
            if log_plans:
                log_output += f"=== DAILY PLAN FOR {agent.name} AT ROUND {round} ===\n"
                log_output += f"{agent.name} plans:\n{agent.daily_plans}\n\n"
                if print_plans:
                    print(f"{agent.name} plans:\n{agent.daily_plans}\n")
                if summarize_plans:
                    summary_input += f"{agent.name} plans:\n{agent.daily_plans}\n"
    
    # Whether to proceed with hourly plan
    if global_time.split(":")[1] == "00":
        for agent in agents:
            agent.hourly_planning(agents, locations.get_location(agent.location), global_time, town_areas, prompt_meta, ['待修改'])
            if log_actions:
                log_output += f"=== HOURLY PLAN FOR {agent.name} AT ROUND {round} ===\n"
                log_output += f"{agent.name}'s hourly action:\n{agent.hourly_plans}\n\n"
                if print_actions:
                    print(f"{agent.name}'s hourly action:\n{agent.hourly_plans}\n")
                if summarize_actions:
                    summary_input += f"{agent.name}'s hourly action:\n{agent.hourly_plans}\n"
    
    # Execute planned actions and update memories
    for agent in agents:
        # Execute the action
        action = agent.execute_action(global_time, prompt_meta, ['待修改'], ['待修改'])
        if log_actions:
            log_output += f"=== ACTION EXECUTION FOR {agent.name} AT ROUND {round} ===\n"
            log_output += f"{agent.name} executes action: {action}\n\n"
            if print_actions:
                print(f"{agent.name} executes action: {action}\n")
            if summarize_actions:
                summary_input += f"{agent.name} executes action: {action}\n"
        
        # Update memories
        # agent.update_memory(agents, )

    # Rate locations and determine where agents will go next
    if global_time.split(":")[1] == "50":
        for agent in agents:
            place_ratings = agent.rate_locations(locations, global_time, prompt_meta, ['待修改'], ['待修改'])
            if log_ratings:
                log_output += f"=== UPDATED LOCATION RATINGS {global_time} FOR {agent.name}===\n"
                log_output += f"{agent.name} location ratings: {place_ratings}\n"
                if print_ratings:
                    print(f"=== UPDATED LOCATION RATINGS {global_time} FOR {agent.name}===\n")
                    print(f"{agent.name} location ratings: {place_ratings}\n")
                if summarize_ratings:
                    summary_input += f"{agent.name} location ratings: {place_ratings}\n"
            
            old_location = agent.location

            new_location_name = place_ratings[0][0]
            agent.move(new_location_name)
            if log_locations:
                log_output += f"=== UPDATED LOCATIONS AT TIME {global_time} FOR {agent.name}===\n"
                log_output += f"{agent.name} moved from {old_location} to {new_location_name}\n\n"
                if print_locations:
                    print(f"=== UPDATED LOCATIONS AT TIME {global_time} FOR {agent.name}===\n")
                    print(f"{agent.name} moved from {old_location} to {new_location_name}\n")
                if summarize_locations:
                    summary_input += f"{agent.name} moved from {old_location} to {new_location_name}\n"

    
    print(f"----------------------- SUMMARY FOR ROUND {round} -----------------------\n")
    log_output += f"----------------------- SUMMARY FOR ROUND {round} ----------\n"

    summary_output = summarize_simulation(summary_input)
    print(summary_output)
    log_output += f"----------------------- SUMMARY FOR ROUND {round} ----------\n" + summary_output + "\n" + f"---------- END OF ROUND {round} ----------\n" + "\n" + f"---------- END OF ROUND {round} ----------\n\n"
    print(f"====================== END OF ROUND {round} ==========\n====================== END OF ROUND {round} ==========\n\n")

    # Save simulation summary
    with open(os.path.join(project_folder, "simulation_summary.txt"), "a", encoding="utf-8") as f:
        f.write(f"----------------------- SUMMARY FOR ROUND {round} ----------\n" + summary_output + "\n" + f"---------- END OF ROUND {round} ----------\n")

    # Save simulation log
    with open(os.path.join(project_folder, "simulation_log.txt"), "a", encoding="utf-8") as f:
        f.write(log_output)

    global_time = add_ten_minutes(global_time)

    meta_data['global_time'] = global_time
    meta_data['round'] = round
    
    save_meta_data(project_folder, meta_data)


        