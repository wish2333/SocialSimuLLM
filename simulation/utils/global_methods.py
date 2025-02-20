# simulation\utils\global_tools.py

# -*- coding: utf-8 -*-
"""
First version created on 2025-02-19 20:12.

@author: Huang Miaosen
"""

import os
import json
import shutil
from datetime import datetime, timedelta

def load_meta_data(project_folder, project_name, global_time):
    meta_file = os.path.join(project_folder, "meta.json")
    
    if not os.path.exists(project_folder):
        os.makedirs(project_folder)
        os.makedirs(os.path.join(project_folder, "agent_data"))
        print(f"The project folder {project_folder} is created.")
        meta_data = {
            "project_name": project_name,
            "global_time": global_time,
            "round": 0,
        }
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(meta_data, f, ensure_ascii=False, indent=4)
    else:
        with open(meta_file, 'r', encoding='utf-8') as f:
            meta_data = json.load(f)
    
    return meta_data

def save_meta_data(project_folder, meta_data):
    meta_file = os.path.join(project_folder, "meta.json")
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(meta_data, f, ensure_ascii=False, indent=4)

def load_town_data(project_folder):
    json_path = os.path.join(project_folder, 'town_data.json')
    
    if not os.path.exists(json_path):
        current_json_path = 'town_data_template.json'
        if os.path.exists(current_json_path):
            shutil.copy(current_json_path, json_path)
            print("The town_data.json file is copied to the project folder.")
            print("Please modify the town_data.json file as needed and restart the script.")
            exit(0)
        else:
            raise FileNotFoundError("There is no town_town_data.json file in the current directory.")
        with open(json_path, 'r') as file:
            town_data = json.load(file)
        return town_data
    else:
        with open(json_path, 'r') as file:
            town_data = json.load(file)
            return town_data
        
def load_agent_data(project_folder, agent_name):
    json_path = os.path.join(project_folder, 'agent_data', f'{agent_name}.json')
    
    if not os.path.exists(json_path):
        agent_data = {
            "associated_memory": {},
        }
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(agent_data, f, ensure_ascii=False, indent=4)
        return agent_data
    else:
        with open(json_path, 'r', encoding='utf-8') as f:
            agent_data = json.load(f)
        return agent_data
    
def save_agent_data(project_folder, agent_name, agent_data):
    json_path = os.path.join(project_folder, 'agent_data', f'{agent_name}.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(agent_data, f, ensure_ascii=False, indent=4)

def exist_memory_file(agent_name, project_folder):
    memory_name = agent_name + "_memory.json"
    memory_file = os.path.join(project_folder, 'agent_data', memory_name)
    if not os.path.exists(memory_file):
        memory_data = {"memory": []}
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(memory_data, f, ensure_ascii=False, indent=4)





def add_ten_minutes(global_time):
    date_part, time_part = global_time.split(", ")
    day_number = int(date_part.split(" ")[1])
    time_format = "%H:%M"
    time_obj = datetime.strptime(time_part, time_format)
    new_time_obj = time_obj + timedelta(minutes=10)
    if new_time_obj.time() >= datetime.strptime("20:00", time_format).time():
        new_date = f"Day {day_number + 1}"
        new_time = "08:00"
    else:
        new_date = date_part
        new_time = new_time_obj.strftime(time_format)
    return f"{new_date}, {new_time}"


def if_new_day(global_time):
    if global_time.split(", ")[1] == "08:00":
        return True
    else:
        return False
    
def if_new_hour(global_time):
    if global_time.split(", ")[1].split(":")[1] == "00":
        return True
    else:
        return False
