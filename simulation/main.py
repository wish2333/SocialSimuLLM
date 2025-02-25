# simulation\main.py

# -*- coding: utf-8 -*-

"""
First version created on Wed Sep 29 15:32:22 2021

@author: Huang Miaosen

Comment format:Comment format: Use standard Google style docstring format for comments, bilingual in English and Chinese (note to write English comments first), compatible with VSCode intelligent prompts.
"""

import os
import json
import networkx as nx
from agents.agent import Agent
from locations.locations import Locations
from retrieve.memory import Memory
from utils.text_generation import summarize_simulation
from utils.global_methods import *

# Initialize global variables
prompt_meta = '### Instruction:\n{}\n### Response:'
global_time = 'Day 1, 08:00'
while True:
    project_name = str(input("Please enter the project name: "))
    if project_name:
        break
    else:
        print("Project name cannot be empty. Please try again.")
project_folder = os.path.join(os.getcwd(), "projects", project_name)

log_debug = True
log_locations = True
log_actions = True
log_plans = True
log_ratings = True
log_memory = True

print_locations = True
print_actions = True
print_plans = True
print_ratings = False
print_memory = False

summarize_locations = False
summarize_actions = True
summarize_plans = False
summarize_ratings = False
summarize_memory = True

log_output = ""
summary_input = ""

# Initialize modules
agents = []
locations = Locations()

# Load project data
meta_data = load_meta_data(project_folder, project_name, global_time)
town_data = load_town_data(project_folder)

global_time = meta_data['global_time']
round = meta_data['round']
memory_limit = town_data['general']['memory_limit']
town_people = town_data['town_people']
town_areas = town_data['town_areas']

print(f"=== CONFIGURATIONS for {project_name} LOADED ===")
print(f"==Global time: {global_time} Round: {round}==")

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
for name, detail in town_people.items():
    starting_location = detail['starting_location']
    if starting_location not in world_graph.nodes():
        print(f"Warning: Starting location {starting_location} for agent {name} is not in world_graph.")
    description = json.dumps(detail['description']) #Convert the description to a string
    agents.append(Agent(name, description, starting_location, world_graph))

for agent in agents:
    exist_memory_file(agent.name, project_folder)
memory = Memory(project_folder, agents, memory_limit)

new_event = str(input("Please enter a new event: ")) or "No new event."
if new_event == "No new event.":
    events = [event_json['action'] for event_json in memory.load_event_file()['event']]
else:
    new_event_experience={
            "agent_name": "global_event",
            "global_time": global_time,
            "action": f"In {global_time}: \"{new_event}\".",
            "exp_type": 'event',
            "priority": 9
            }
    memory.add_experience(new_event_experience, 'event')
    events = [event_json['action'] for event_json in memory.save_and_load_event_file(new_event_experience)['event']]

for agent in agents:
    init_memory_list = memory.get_init_memory(agent.name)
    agent.init_memory(init_memory_list[0], init_memory_list[1], events)

for name, detail in town_areas.items():
    locations.add_location(name, description)

print(f"=== MODULES INITIALIZED ===")


# Start simulation loop
repeats = int(input("Please enter the number of repeats: ")) or 1
for repeat in range(repeats):
    #log_output for one repeat
    round += 1
    new_day = if_new_day(global_time)
    new_hour = if_new_hour(global_time)
    log_output = ""
    print(f"====================== ROUND {round} TIME {global_time} ========================\n")
    log_output += f"====================== ROUND {round} TIME {global_time} ========================\n"
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
    if new_day:
        for agent in agents:
            experience =agent.daily_planning(global_time, prompt_meta, memory.get_impressions_str(agent.name, 3), memory.get_newthings_str(agent.name, memory_limit))
            memory.add_experience(experience, 'plan')
            if log_plans:
                log_output += f"=== DAILY PLAN FOR {agent.name} AT ROUND {round} ===\n"
                log_output += f"{agent.name} plans:\n{agent.daily_plans}\n\n"
                if print_plans:
                    print(f"{agent.name} plans:\n{agent.daily_plans}\n")
                if summarize_plans:
                    summary_input += f"{agent.name} plans:\n{agent.daily_plans}\n"
            # if log_debug:
            #     log_output += memory.get_newthings_str(agent.name, memory_limit)
    
    # Whether to proceed with hourly plan and get related things
    if new_hour:
        for agent in agents:
            experience =agent.hourly_planning(agents, locations.get_location(agent.location), global_time, town_areas, prompt_meta, memory.get_impressions_str(agent.name, 3), memory.get_newthings_str(agent.name, memory_limit))

            agent.related_things = memory.get_related_things_str(agent.name, agent.hourly_plan, 5)
            memory.add_experience(experience, 'thought')

            if log_actions:
                log_output += f"=== HOURLY PLAN FOR {agent.name} AT ROUND {round} ===\n"
                log_output += f"{agent.name}'s hourly action:\n{agent.hourly_plan}\n\n"
                if print_actions:
                    print(f"{agent.name}'s hourly action:\n{agent.hourly_plan}\n")
                if summarize_actions:
                    summary_input += f"{agent.name}'s hourly action:\n{agent.hourly_plan}\n"
            if log_debug:
                log_output += f"Related things:\n{agent.related_things}\n\n"
    elif not new_hour and repeat == 0:
        for agent in agents:
            agent.related_things = memory.get_related_things_str(agent.name, agent.hourly_plan, 5)
            if log_debug:
                log_output += f"Related things:\n{agent.related_things}\n\n"
    
    # Execute planned actions and update memory
    for agent in agents:
        # Execute the action
        gotten_impression = memory.get_impressions_str(agent.name, 3)
        action = agent.execute_action(global_time, prompt_meta, gotten_impression, memory.get_newthings_str(agent.name, memory_limit))
        priority = agent.rate_experience(prompt_meta, gotten_impression, memory.get_newthings_str(agent.name, memory_limit), action)
        experience = agent.memory_actions(agents, global_time, priority)
        memory.add_experience(experience, 'action')
        
        if log_actions:
            log_output += f"=== ACTION EXECUTION FOR {agent.name} AT ROUND {round} ===\n"
            log_output += f"{agent.name} executes action: {action}\n\n"
            if print_actions:
                print(f"{agent.name} executes action: {action}\n")
            if summarize_actions:
                summary_input += f"{agent.name} executes action: {action}\n"
            if log_debug:
                log_output += f"{agent.name} gotten: {gotten_impression}\n\n"

    # Rate locations and determine where agents will go next
    if new_hour:
        for agent in agents:
            place_ratings = agent.rate_locations(locations, global_time, prompt_meta, memory.get_impressions_str(agent.name, 3), memory.get_newthings_str(agent.name, memory_limit))
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
            if new_location_name != agent.location:
                agent.move(new_location_name)
                agent.memory_location_change(global_time, old_location, new_location_name)
                save_location_change(project_folder, agent.name, new_location_name)
                if log_locations:
                    log_output += f"{agent.name} moved from {old_location} to {new_location_name}\n\n"
                    if print_locations:
                        print(f"{agent.name} moved from {old_location} to {new_location_name}\n")
                    if summarize_locations:
                        summary_input += f"{agent.name} moved from {old_location} to {new_location_name}\n"

    # Form recent impressions
    if new_hour:
        for agent in agents:
            impression = agent.form_impression(global_time, prompt_meta, memory.get_newthings_str(agent.name, memory_limit))
            memory.add_experience(impression, 'thought')
            if log_actions:
                log_output += f"=== RECENT IMPRESSIONS FOR {agent.name} AT ROUND {round} ===\n"
                log_output += f"{agent.name}'s recent impression: {impression['action']}\n\n"
                if print_actions:
                    print(f"{agent.name}'s recent impression: {impression['action']}\n")
                if summarize_actions:
                    summary_input += f"{agent.name}'s recent impression: {impression['action']}\n"

    # Save simulation log
    log_output += f"---------- END OF ROUND {round} ----------\n---------- END OF ROUND {round} ----------\n\n"
    print(f"====================== END OF ROUND {round} ==========\n====================== END OF ROUND {round} ==========\n\n")
    with open(os.path.join(project_folder, "simulation_log.txt"), "a", encoding="utf-8") as f:
        f.write(log_output)

    new_global_time = add_ten_minutes(global_time)

    if if_new_day(new_global_time):
        for agent in agents:
            reflection = agent.form_reflection(global_time, prompt_meta, memory.get_importants_str(agent.name, global_time), memory.get_newthings_str(agent.name, memory_limit))
            memory.add_experience(reflection, 'reflection')
            log_output += f"=== REFLECTION FOR {agent.name} AT ROUND {round} ===\n"
            log_output += f"{reflection}\n\n"
            print(f"{reflection}\n")
            summary_input += f"\n{reflection}\n"

        # Whether to summary
    if (if_new_day(new_global_time) and repeat != 0) or (repeat == repeats-1):
        print(f"----------------------- SUMMARY FOR ROUND {round} -----------------------\n")
        log_output += f"----------------------- SUMMARY FOR ROUND {round} ----------\n"
        summary_output = summarize_simulation(summary_input)
        summary_input = ""
        print(summary_output)
        log_output += summary_output + "\n\n"
        # Save simulation summary
        with open(os.path.join(project_folder, "simulation_summary.txt"), "a", encoding="utf-8") as f:
            f.write(f"----------------------- SUMMARY FOR ROUND {round} ----------\n{summary_output}\n\n")

    global_time = new_global_time
    meta_data['global_time'] = global_time
    meta_data['round'] = round
    
    save_meta_data(project_folder, meta_data)