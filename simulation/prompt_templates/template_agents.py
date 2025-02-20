# simulation\prompt_templates\template_agents.py

# -*- coding: utf-8 -*-
"""
First version created on 2025-02-19 15:25.

@author: Huang Miaosen
"""

agent_plan_system = """You are {}.
The following is your description: {}.
The following is your recent impressions: {}.
Just now these things happened: {}(including any actions you took in the past hour)

You just woke up."""

agent_plan_prompt = """What is your goal for today?Write it down in an hourly basis starting at {}:00 until 20:00. For every action, write only one short sentence that is brief and at most 10 words. You can use the following template to help you write your goal:
[8:00 - Wake up and get ready for the day.
9:00 - !Action1!
10:00 - !Action2!
11:00 - !Action3!
12:00 - Lunch break
13:00 - !Action4!
14:00 - !Action5!
15:00 - !Action6!
16:00 - !Action7!
17:00 - !Action8!
17:00 - !Action8!
18:00 - Dinner time
19:00 - !Action9!
20:00 - Enjoy the night and Go to bed.]"""

hourly_planning_system = """You are {}.
The following is your description: {}.
The following is your recent impressions: {}.
Just now these things happened: {}(including any actions you took in the past hour)
Your plans are: {}."""


hourly_planning_prompt = """You are currently in {} with the following description: {}.
It is currently {}.
The following people are in this area: {}."""

agent_execute_action_system = """You are {}.
The following is your description: {}.
The following is your recent impressions: {}.
Your plans are: {}."""


agent_execute_action_prompt = """{}
You are going to do this thing-"{}" for this hour.
Just now these things happened: {}(including any actions you took in the past hour)
What are you planning to do now? If you intend to communicate with someone, please write down who you are talking to and what you want to say. Or you can just do something. You can use the following templates to help you write your executing actions and the specific details:
1. "Communicate with Tom[action]: Tom, This tool is amazing! I can't wait to use it for my research.[details]"(Note that this is just a template)
2. "Do something[action]: I'm going to continue my research on this tool. I'll write a paper on it.[details]"(Note that this is just a template)
"""

rate_location_system = """You have to rate the likelihood of going to a location next by using a scale of 1-9.
The scale is as follows: 1-Not likely at all, 4-Somewhat likely, 7-Very likely, 9-Extremely likely.
Please only respond with a number between 1 and 9."""

rate_location_prompt = """You are {}. Your plans are: {}. It is currently {}. You are currently at {}.
The following is your description: {}.
The following is your recent impressions: {}.
Just now these things happened: {}(including any actions you took in the past hour)
How likely are you to go to {} next?"""

rate_experiences_system = """You have to rate the prioity of something you have experienced just now by using a scale of 1-9.
The scale is as follows: 1-Not important at all, 4-Somewhat important, 7-Very important, 9-Extremely important.
Please only respond with a number between 1 and 9."""

rate_experiences_prompt = """You are {}. Your plans are: {}. It is currently {}. You are currently at {}.
The following is your description: {}.
The following is your recent impressions: {}.
Just now these things happened: {}(including any actions you took in the past hour)
How important is it for you to experience {} right now?"""