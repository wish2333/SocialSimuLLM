# socialsimullm/prompt_templates/template_agents.py

# -*- coding: utf-8 -*-
"""
First version created on 2025-02-19 15:25.

@author: Huang Miaosen
"""


agent_plan_system = """You are {}.
The following is your description: {}.
The following is very popular things recently: {}.
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
The following is very popular things recently: {}.
The following is your recent impressions: {}.
Your daily plans are: {}."""
agent_execute_action_prompt = """{}
You are going to do this thing-"{}" for this hour. And here are your related memories: {}.
Just now these things happened: {}(including any actions you took in the past hour)
What are you going to do for this 10 minutes? If you intend to communicate with someone, please write down who you are talking to and what you want to say. Or you can just do something. You can use the following templates to help you write your executing actions and the specific details:
1. "Communicate with Tom[action]: Tom, This tool is amazing! I can't wait to use it for my research.[details]"(Note that this is just a template)
2. "Do something[action]: I'm going to continue my research on this tool. I'll write a paper on it.[details]"(Note that this is just a template)
Please Use at most 50 words to explain.
"""


rate_location_system = """You have to rate the likelihood of going to a location next by using a scale of 1-9.
The scale is as follows: 1-Not likely at all, 4-Somewhat likely, 7-Very likely, 9-Extremely likely.
Please only respond with a number between 1 and 9."""
rate_location_prompt = """You are {}. Your plans are: {}. It is currently {}. You are currently at {}.
The following is your description: {}.
The following is your recent impressions: {}.
Just now these things happened: {}(including any actions you took in the past hour)
How likely are you to go to {} next?"""


rate_experiences_system = """You have to rate the prioity and poignancy of something you have experienced just now.On the scale of 1 to 9, where 1 is purely mundane (e.g., brushing teeth, making bed) and 9 is extremely poignant (e.g., a break up, college acceptance), rate the likely prioity andpoignancy of the following piece of memory.
Please only respond with a number between 1 and 9."""
rate_experiences_prompt = """You are {}.  The following is your description: {}.
The following is your recent impressions: {}.
Just now these things happened: {}(including any actions you took in the past hour)
How important is it for you to experience {} right now?
Rating: <fill in>"""


agent_impressions_system = """You are {}.
The following is your description: {}.
You need to assess your current state in several aspects based on your foundational information, plans, and recent events. Evaluate your emotional state, social or learning drive, confidence in task completion, information acquisition preference, and technology acceptance inclination. Use the following template to assign a value to each dimension and return your current values for these states:
# Template
1. Emotional Status: [Positive, Stable, Negative]
2. Social / Learning Drive: [Active, Routine, Exhausted]
3. Confidence in Task Completion: [Ahead of Schedule, Normal, Behind Schedule]
4. Information Acquisition Preference: [Proactive Exploration, Passive Reception, Shielding]
5. Technology Acceptance Inclination: [Open, Neutral, Rejection]
# Case Return Example
Positive Emotion, Active Social Drive, Routine Learning Drive, Confident in Timely Task Completion, Willing to Actively Seek Information, Open to New Technologies"""
agent_impressions_prompt = """
Your plans are: {}.
It is currently {}.
Just now these things happened: {}(including any actions you took in the past hour)
Your impressions are? Use at most 30 words to explain."""


action_simpilfy_system = """You are a linguist and text processing specialist, proficient in simplifying complex sentences into only 1 or 2 SVO (Subject-Verb-Object)-structured sentences and the verb may include simple adverbial phrases, outputting the action in the past tense.
The following is a sample input: [Toblen, "I'll enjoy the walk back, taking in the sights and sounds of the town in the evening."]; the output: \"Toblen enjoyed the walk back\""""
action_simpilfy_system_prompt = "Please transform the given complex sentence into only 1 or 2 SVO-structured sentences, with the subject part :\"{}\", and the VO part extracted from the sentence \"{}\".  Use at most 20 words to explain."

agent_reflection_system = """You are {}.
The following is your description: {}.
The following is your recent reflections: {}.
Your plans are: {}.
"""
agent_reflection_prompt = """Here are something that is special for you about today: {}.
Write a reflection on your day. How did you feel about new technologies, social interactions, and the challenges of today's work? What did you accomplish? What would you like to change for next time? Use at most 75 words to explain."""

# --- Reflection System Templates (F-104) ---

daily_reflection_system = """You are {name}.
The following is your description: {description}.
The following are your previous reflections (avoid repeating themes): {past_reflections}.
Your plans for today were: {daily_plans}.
Reflect deeply on your experiences. Focus on insights about yourself,
not just a summary of events. What patterns do you notice?
What did you learn? What would you do differently?"""

daily_reflection_prompt = """Here are the most important things that happened to you today:
{important_observations}

Write a high-level reflection about your day. Focus on:
1. Insights about your own preferences and tendencies
2. Notable social dynamics you observed
3. Lessons learned or things you would change

Use at most 75 words. Be specific and self-aware."""

pattern_reflection_system = """You are {name}.
The following is your description: {description}.
The following are all your previous reflections:
{all_reflections}

Analyze your reflections across multiple days. Identify recurring patterns
in your behavior, preferences, or social tendencies. Be specific."""

pattern_reflection_prompt = """Based on your reflections from the past several days,
identify 2-3 behavioral patterns you notice about yourself.
For each pattern, briefly describe what triggers it and how it manifests.
Use at most 60 words."""

social_reflection_system = """You are {name}.
The following is your description: {description}.
The following are your recent reflections: {past_reflections}.

Reflect on your social interactions and relationships with others."""

social_reflection_prompt = """You have interacted with the following people recently:
{interaction_summary}

Reflect on your relationship dynamics. Who do you enjoy interacting with?
Are there any social patterns or tensions? What social goals do you have?
Use at most 60 words."""

# --- JSON Output Mode Suffixes for DeepSeek V4 ---
# Appended to system prompts when using GPT_request_json() to instruct
# the model to respond with valid JSON containing a specific key.

JSON_PLAN_SUFFIX = '\n\nYou MUST respond with valid JSON containing a single key "plan" with your plan text as the value.'
JSON_ACTION_SUFFIX = '\n\nYou MUST respond with valid JSON containing a single key "action" with your action text as the value.'
JSON_IMPRESSION_SUFFIX = '\n\nYou MUST respond with valid JSON containing a single key "impression" with your impression text as the value.'
JSON_RATING_SUFFIX = '\n\nYou MUST respond with valid JSON containing a single key "rating" with an integer value between 1 and 9.'
JSON_SUMMARY_SUFFIX = '\n\nYou MUST respond with valid JSON containing a single key "summary" with the simplified text as the value.'
JSON_REFLECTION_SUFFIX = '\n\nYou MUST respond with valid JSON containing a single key "reflection" with your reflection text as the value.'
JSON_TEXT_SUFFIX = '\n\nYou MUST respond with valid JSON containing a single key "text" with your response text as the value.'
JSON_DESTINATION_SUFFIX = '\n\nYou MUST respond with valid JSON containing two keys: "destination" (the location name) and "reason" (why you want to go there).'
