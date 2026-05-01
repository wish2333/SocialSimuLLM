# socialsimullm/utils/text_generation.py

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

from socialsimullm.utils.config import DefaultModel, openai_api_key, openai_base_url

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

    Args:
        system (str):
            The instruction or prompt used to generate text.
        prompt (str):
            The instruction or prompt used to generate text.
        gpt_parameter (dict, optional):
            A dictionary of GPT model parameters that can override the default values below:
            - model (str): Model to use. Default: DefaultModel.completion
            - temperature (float): Sampling temperature (0-2). Default: 0.8
            - max_tokens (int): Maximum number of tokens to generate. Default: 50
            - top_p (float): Nucleus sampling probability. Default: 1.0
            - frequency_penalty (float): Frequency penalty coefficient (0-2). Default: 0
            - presence_penalty (float): Presence penalty coefficient (0-2). Default: 0
            - stop (list/str): Stop sequence(s). Default: None

    Returns:
        str:
            The text content string returned by the OpenAI API.

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

def summarize_simulation(prompt):
    prompt = f"Summarize the simulation loop:\n{prompt}"
    response = GPT_request(system="You are a social science expert observing a social experiment. You will receive a timeline of actions taken by participants over the course of a day. Please summarize what happened during that day.", prompt=prompt, gpt_parameter={"max_tokens": 500})
    return response

if __name__ == "__main__":
    print(GPT_request("This is a test."))
