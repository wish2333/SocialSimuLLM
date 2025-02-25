# simulation\utils\text_generation.py

# -*- coding: utf-8 -*-
"""
First version created on 2025-02-19 12:37.

@author: Huang Miaosen

Comment format: Use standard Google style docstring format for comments, bilingual in English and Chinese (note to write English comments first), compatible with VSCode intelligent prompts.
"""

from openai import OpenAI
import re
import os
import time

from utils.config import *

def time_sleep(sec=0.1):
    time.sleep(sec)


def GPT_request(system, prompt, gpt_parameter: dict = {
        "model": DefaultModel.completion,
        "temperature": 0.8,
        "max_tokens": 50,
        "top_p": 1.0,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "stop": None
    }) -> str:
    """Generate text content via the OpenAI API.
    根据给定的提示词和GPT参数配置，调用OpenAI接口生成文本响应。

    Args:
        system (str): 
            The instruction or prompt used to generate text. 
            用于生成文本的提示词。
        prompt (str): 
            The instruction or prompt used to generate text. 
            用于生成文本的提示词。
        gpt_parameter (dict, optional): 
            A dictionary of GPT model parameters that can override the default values below:
            - model (str): Model to use. Default: DefaultModel.completion
                            使用的模型，默认值：DefaultModel.completion
            - temperature (float): Sampling temperature (0-2). Default: 0.8
                                    采样温度（0-2），默认0.8
            - max_tokens (int): Maximum number of tokens to generate. Default: 50
                                生成的最大token数，默认50
            - top_p (float): Nucleus sampling probability. Default: 1.0
                            核心采样概率，默认1.0
            - frequency_penalty (float): Frequency penalty coefficient (0-2). Default: 0
                                        频率惩罚系数（0-2），默认0
            - presence_penalty (float): Presence penalty coefficient (0-2). Default: 0
                                        存在惩罚系数（0-2），默认0
            - stop (list/str): Stop sequence(s). Default: None
                                停止序列，默认None

    Returns:
        str: 
            The text content string returned by the OpenAI API.
            OpenAI API返回的文本内容字符串。

    Example:
        >>> GPT_request("Hello world", {"temperature": 0.5})
    """

    # default parameters
    default_params = {
        "model": DefaultModel.completion,
        "temperature": 0.8,
        "max_tokens": 50,
        "top_p": 1.0,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "stop": None
    }
    # Merge user parameters and default parameters (user parameters have higher priority)
    # 合并用户参数和默认参数（用户参数优先级更高）
    merged_params = default_params.copy()
    if gpt_parameter is not None:
        merged_params.update(gpt_parameter)

    time_sleep()
    client = OpenAI(api_key=openai_api_key, base_url=openai_base_url)
    try:
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty or whitespace only.")
        response = client.chat.completions.create(
            model=merged_params["model"],
            messages=[
                {
                'role': 'system',
                'content': system
                },
                {
                'role': 'user',
                'content': prompt
                }
            ],
            temperature=merged_params["temperature"],
            max_tokens=merged_params["max_tokens"],
            top_p=merged_params["top_p"],
            frequency_penalty=merged_params["frequency_penalty"],
            presence_penalty=merged_params["presence_penalty"],
            stop=merged_params["stop"],
            n=1)
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return f"ERROR: {str(e)}"

def get_embedding(text, model=DefaultModel.embedding):
    client = OpenAI(api_key=openai_api_key, base_url=openai_base_url)
    text = text.replace("\n", " ")
    if not text:
        text = "this is blank"
    response = client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding

def get_rating(x):
    """
    Extract the rating from a string.
    """
    nums = [int(i) for i in re.findall(r'\d+', x)]
    if len(nums)>0:
        return min(nums)
    else:
        return None

def summarize_simulation_daily(prompt):
    prompt = f"Summarize the simulation loop:\n{prompt}"
    response = GPT_request(system="You are a social science expert observing a social experiment. You will receive a timeline of actions taken by participants over the course of a day. Please summarize what happened during that day.", prompt=prompt, gpt_parameter={"max_tokens": 500})
    return response

def summarize_simulation_session(prompt):
    prompt = f"Summarize the simulation loop:\n{prompt}"
    response = GPT_request(system="You are a social science expert observing a social experiment. You will receive a timeline of actions taken by participants over the course of a session. Please summarize what happened during that session.", prompt=prompt, gpt_parameter={"max_tokens": 500})
    return response

# def generate_prompt(curr_input, prompt_template):
#     """Generates prompt by formatting template with inputs
#     通过格式化模板和输入生成提示
#     Args:
#         curr_input (list/str): a str of the current input we want to feed in.
#                             要填充到模板中的参数，支持字符串或列表
#         prompt_template (str): a str of the prompt template that contains {} placeholders.
#                             包含{}占位符的提示模板字符串
#     Returns:
#         str: the generated prompt string.
#             生成的提示字符串
#     """
#     # convert to str and make a list
#     inputs = [curr_input] if isinstance(curr_input, str) else curr_input
#     inputs = [str(i) for i in inputs]

#     try:
#         formatted = prompt_template.format(*inputs)
#     except IndexError:
#         raise ValueError("Number of inputs does not match number of placeholders in prompt template.")
#     return formatted

if __name__ == "__main__":
    print(GPT_request("This is a test."))
