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
import logging

from socialsimullm.utils import config as _cfg

_log = logging.getLogger("socialsimullm.text_generation")


# --- DeepSeek V4 Role-Play Thinking Mode Markers ---
# Reference: https://github.com/victorchen96/deepseek_v4_rolepaly_instruct
# These markers are appended to user prompts to control the thinking chain style.
# Only effective for deepseek-v4-flash and deepseek-v4-pro models.

DEEPSEEK_V4_ROLE_IMMERSION_MARKER = (
    "\n\n"
    "In your thinking process, please follow these rules:\n"
    "1. Use first-person inner monologue in parentheses, "
    'e.g. "(thinking: ...)"\n'
    '2. Describe the character\'s inner feelings in first person, '
    'e.g. "I think", "I feel", "I secretly"\n'
    "3. Stay immersed in the character, analyzing the situation "
    "and planning responses through inner monologue"
)

DEEPSEEK_V4_PURE_ANALYSIS_MARKER = (
    "\n\n"
    "In your thinking process, please follow these rules:\n"
    "1. Do NOT use parentheses for inner monologue. "
    'e.g. no "(thinking: ...)"\n'
    "2. Do NOT use first-person inner activity descriptions, "
    'e.g. no "I think", "I feel". Use analytical language instead.\n'
    "3. Focus on logical analysis and response planning, "
    "not role-play style inner drama"
)


def _is_deepseek_v4(model: str | None = None) -> bool:
    """Check if the model is a DeepSeek V4 model that supports thinking mode markers."""
    effective = model or _cfg.DefaultModel.completion
    return effective.startswith("deepseek-v4-")


def deepseek_v4_marker(mode: str = "role_immersion") -> str:
    """Get the DeepSeek V4 thinking mode marker for the current model.

    Args:
        mode: 'role_immersion' for agent cognitive calls,
              'pure_analysis' for rating/scoring calls,
              'default' for no marker.

    Returns:
        The marker string, or empty string if model is not DeepSeek V4.
    """
    if not _is_deepseek_v4():
        return ""
    if mode == "role_immersion":
        return DEEPSEEK_V4_ROLE_IMMERSION_MARKER
    elif mode == "pure_analysis":
        return DEEPSEEK_V4_PURE_ANALYSIS_MARKER
    return ""

def time_sleep(sec=0.1):
    time.sleep(sec)


def GPT_request(system, prompt, gpt_parameter: dict = {
        "model": "PLACEHOLDER",
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
        "model": _cfg.DefaultModel.completion,
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
    if merged_params["model"] == "PLACEHOLDER":
        merged_params["model"] = _cfg.DefaultModel.completion

    time_sleep()
    client = OpenAI(api_key=_cfg.openai_api_key, base_url=_cfg.openai_base_url)
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
        _log.error("GPT_request failed", exc_info=e)
        return f"ERROR: {str(e)}"

def get_embedding(text, model=None):
    if model is None:
        model = _cfg.DefaultModel.embedding
    client = OpenAI(api_key=_cfg.embedding_api_key, base_url=_cfg.embedding_base_url)
    text = text.replace("\n", " ")
    if not text:
        text = "this is blank"
    try:
        response = client.embeddings.create(input=[text], model=model)
        return response.data[0].embedding
    except Exception as e:
        _log.error("get_embedding failed", exc_info=e)
        raise


def test_connections() -> None:
    """Pre-flight check for LLM and embedding API connectivity.

    Tests both endpoints with minimal requests. Prints results and
    exits with code 1 if the completion API is unreachable.
    """
    import sys

    print("Testing API connections...")
    print(f"  OPENAI_BASE_URL:       {_cfg.openai_base_url or '(empty)'}")
    print(f"  OPENAI_API_KEY:        {_cfg.openai_api_key[:8]}...{_cfg.openai_api_key[-4:]}")
    print(f"  OPENAI_MODEL:          {_cfg.DefaultModel.completion}")
    print(f"  EMBEDDING_BASE_URL:    {_cfg.embedding_base_url}")
    print(f"  EMBEDDING_API_KEY:     {_cfg.embedding_api_key[:8]}...{_cfg.embedding_api_key[-4:]}")
    print(f"  EMBEDDING_MODEL:       {_cfg.DefaultModel.embedding}")
    print()

    # Completion API
    try:
        client = OpenAI(api_key=_cfg.openai_api_key, base_url=_cfg.openai_base_url)
        resp = client.chat.completions.create(
            model=_cfg.DefaultModel.completion,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=5,
        )
        output = resp.choices[0].message.content or "(empty)"
        print(f"  Completion API: OK")
        print(f"    input:  [user] 'hi'")
        print(f"    output: {repr(output)}")
        print(f"    model:  {resp.model}")
        print(f"    usage:  prompt_tokens={resp.usage.prompt_tokens}, completion_tokens={resp.usage.completion_tokens}")
    except Exception as e:
        print(f"  Completion API: FAILED - {e}")
        print("\nFix OPENAI_API_KEY / OPENAI_BASE_URL in .env and retry.")
        sys.exit(1)

    print()

    # Embedding API
    try:
        client = OpenAI(api_key=_cfg.embedding_api_key, base_url=_cfg.embedding_base_url)
        resp = client.embeddings.create(input=["test"], model=_cfg.DefaultModel.embedding)
        vec = resp.data[0].embedding
        print(f"  Embedding API: OK")
        print(f"    input:  'test'")
        print(f"    output: dim={len(vec)}, first_5={vec[:5]}")
        print(f"    model:  {_cfg.DefaultModel.embedding}")
        print(f"    usage:  prompt_tokens={resp.usage.prompt_tokens}, total_tokens={resp.usage.total_tokens}")
    except Exception as e:
        print(f"  Embedding API: FAILED - {e}")
        print("\nWarning: embedding unavailable, memory retrieval will degrade.")

    print("\nDone.")


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
