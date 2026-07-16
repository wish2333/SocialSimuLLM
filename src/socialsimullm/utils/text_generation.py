# socialsimullm/utils/text_generation.py

# -*- coding: utf-8 -*-
"""
First version created on 2025-02-19 12:37.

@author: Huang Miaosen

Comment format: Use standard Google style docstring format for comments, bilingual in English and Chinese (note to write English comments first), compatible with VSCode intelligent prompts.
"""

from openai import OpenAI
import json
import re
import os
import time
import logging
from threading import Lock
from typing import Callable

from socialsimullm.utils import config as _cfg

_log = logging.getLogger("socialsimullm.text_generation")

_model_call_metadata: list[dict] = []
_model_call_metadata_lock = Lock()
_model_call_metadata_sink: Callable[[dict], None] | None = None


def set_model_call_metadata_sink(sink: Callable[[dict], None] | None) -> None:
    """Register an optional sink for prompt-free model call metadata."""
    global _model_call_metadata_sink
    with _model_call_metadata_lock:
        _model_call_metadata_sink = sink


def get_model_call_metadata() -> list[dict]:
    """Return a copy of metadata collected for model calls in this process."""
    with _model_call_metadata_lock:
        return [
            dict(item, token_usage=dict(item["token_usage"]))
            for item in _model_call_metadata
        ]


def clear_model_call_metadata() -> None:
    """Clear buffered model call metadata."""
    with _model_call_metadata_lock:
        _model_call_metadata.clear()


def drain_model_call_metadata() -> list[dict]:
    """Atomically return and clear buffered model call metadata."""
    with _model_call_metadata_lock:
        items = [
            dict(item, token_usage=dict(item["token_usage"]))
            for item in _model_call_metadata
        ]
        _model_call_metadata.clear()
    return items


def _token_usage(response: object) -> dict[str, int]:
    """Extract token counts without retaining request or response content."""
    usage = getattr(response, "usage", None)
    if usage is None:
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    def value(name: str) -> int:
        if isinstance(usage, dict):
            raw = usage.get(name, 0)
        else:
            raw = getattr(usage, name, 0)
        return int(raw or 0)

    prompt_tokens = value("prompt_tokens")
    completion_tokens = value("completion_tokens")
    total_tokens = value("total_tokens") or prompt_tokens + completion_tokens
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


def _add_token_usage(total: dict[str, int], response: object) -> None:
    usage = _token_usage(response)
    for key in total:
        total[key] += usage[key]


def _record_model_call(
    *,
    call_type: str,
    model: str,
    retry_count: int,
    fallback_used: bool,
    token_usage: dict[str, int],
) -> None:
    """Buffer and emit safe metadata that never includes prompts or keys."""
    record = {
        "call_type": call_type,
        "model": model,
        "retry_count": retry_count,
        "fallback_used": fallback_used,
        "token_usage": dict(token_usage),
    }
    with _model_call_metadata_lock:
        _model_call_metadata.append(record)
        sink = _model_call_metadata_sink
    if sink is not None:
        try:
            sink(
                dict(record, token_usage=dict(record["token_usage"]))
            )
        except Exception:
            _log.exception("model call metadata sink failed")


def _create_chat_completion(
    system: str,
    prompt: str,
    params: dict,
    *,
    response_format: dict | None = None,
) -> object:
    """Execute one chat API attempt without recording request content."""
    if not prompt.strip():
        raise ValueError("Prompt cannot be empty or whitespace only.")
    time_sleep()
    client = OpenAI(api_key=_cfg.openai_api_key, base_url=_cfg.openai_base_url)
    request = {
        "model": params["model"],
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": params["temperature"],
        "max_tokens": params["max_tokens"],
        "top_p": params["top_p"],
        "frequency_penalty": params["frequency_penalty"],
        "presence_penalty": params["presence_penalty"],
        "n": 1,
    }
    if "stop" in params:
        request["stop"] = params["stop"]
    if response_format is not None:
        request["response_format"] = response_format
    return client.chat.completions.create(**request)


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

    try:
        response = _create_chat_completion(system, prompt, merged_params)
        _record_model_call(
            call_type="completion",
            model=str(merged_params["model"]),
            retry_count=0,
            fallback_used=False,
            token_usage=_token_usage(response),
        )
        return response.choices[0].message.content
    except Exception as e:
        _record_model_call(
            call_type="completion",
            model=str(merged_params["model"]),
            retry_count=0,
            fallback_used=False,
            token_usage=_token_usage(object()),
        )
        _log.error("GPT_request failed", exc_info=e)
        return f"ERROR: {str(e)}"


def GPT_request_json(
    system: str,
    prompt: str,
    gpt_parameter: dict | None = None,
    *,
    required_keys: list[str] | None = None,
    fallback: dict | None = None,
    thinking_mode: str = "role_immersion",
) -> dict:
    """Generate a JSON response via OpenAI-compatible API.

    For DeepSeek V4 models, uses response_format=json_object to ensure
    parseable output even when thinking tokens consume the token budget.
    For non-DeepSeek models, falls back to plain text and attempts
    JSON parsing of the response.

    Retry strategy (DeepSeek V4 only):
      1. Attempt 1: JSON mode (response_format=json_object)
      2. Attempt 2: JSON mode retry (same params)
      3. Attempt 3: Plain text mode (no response_format)
      4. Final: if plain text is also empty, return preset fallback dict.

    Non-DeepSeek models skip directly to plain text mode with a
    single attempt, then fallback if that fails.

    Args:
        system: System message content.
        prompt: User message content (NOT wrapped in prompt_meta by this function).
        gpt_parameter: Override parameters (max_tokens, temperature, etc.).
        required_keys: Keys that must be present in parsed JSON. Triggers retry if missing.
        fallback: Preset dict returned when all attempts fail (e.g. {"rating": 5}).
                  Must contain all required_keys. If None, returns {"_error": True, "text": ...}.
        thinking_mode: DeepSeek V4 thinking mode marker.

    Returns:
        Parsed JSON dict. On exhausted retries: fallback dict with "_error": True,
        or {"_error": True, "text": "<raw>"} if no fallback provided.
    """
    _make_fallback = lambda raw: dict(fallback) if fallback is not None else {"_error": True, "text": raw}

    def _is_valid(result: dict) -> bool:
        if result.get("_error"):
            return False
        if required_keys:
            return all(k in result for k in required_keys)
        return True

    # --- Non-DeepSeek / JSON mode disabled: single plain text attempt ---
    if not _is_deepseek_v4() or not _cfg.json_mode_enabled:
        plain_params = {
            "model": _cfg.DefaultModel.completion,
            "temperature": 0.8,
            "max_tokens": 50,
            "top_p": 1.0,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "stop": None,
        }
        if gpt_parameter is not None:
            plain_params.update(gpt_parameter)
        if plain_params["model"] == "PLACEHOLDER":
            plain_params["model"] = _cfg.DefaultModel.completion

        try:
            response = _create_chat_completion(system, prompt, plain_params)
            usage = _token_usage(response)
            raw = response.choices[0].message.content or ""
        except Exception as exc:
            _log.error("GPT_request_json: API error (non-DeepSeek)", exc_info=exc)
            _record_model_call(
                call_type="completion_json",
                model=str(plain_params["model"]),
                retry_count=0,
                fallback_used=True,
                token_usage=_token_usage(object()),
            )
            fb = _make_fallback("")
            fb["_error"] = True
            return fb

        def finish_non_deep(result: dict, fallback_used: bool) -> dict:
            _record_model_call(
                call_type="completion_json",
                model=str(plain_params["model"]),
                retry_count=0,
                fallback_used=fallback_used,
                token_usage=usage,
            )
            return result

        if not raw.strip():
            _log.warning("GPT_request_json: empty response from non-DeepSeek, using fallback")
            fb = _make_fallback("")
            fb["_error"] = True
            return finish_non_deep(fb, True)
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            _log.warning("GPT_request_json: non-DeepSeek response is not valid JSON, returning raw text")
            return finish_non_deep(_make_fallback(raw), True)
        if required_keys:
            missing = [k for k in required_keys if k not in parsed]
            if missing:
                _log.warning("GPT_request_json: non-DeepSeek response missing keys %s, returning raw text", missing)
                return finish_non_deep(_make_fallback(raw), True)
        return finish_non_deep(parsed, False)

    # --- DeepSeek V4 JSON mode: 3-attempt strategy ---
    default_params = {
        "model": _cfg.DefaultModel.completion,
        "temperature": 0.8,
        "max_tokens": 300,
        "top_p": 1.0,
        "frequency_penalty": 0,
        "presence_penalty": 0,
    }
    merged_params = default_params.copy()
    if gpt_parameter is not None:
        merged_params.update(gpt_parameter)
    if merged_params["model"] == "PLACEHOLDER":
        merged_params["model"] = _cfg.DefaultModel.completion

    user_content = prompt + deepseek_v4_marker(thinking_mode)
    accumulated_usage = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }

    def finish_deep(result: dict, retry_count: int, fallback_used: bool) -> dict:
        _record_model_call(
            call_type="completion_json",
            model=str(merged_params["model"]),
            retry_count=retry_count,
            fallback_used=fallback_used,
            token_usage=accumulated_usage,
        )
        return result

    # Attempt 1 & 2: JSON mode
    for attempt in range(2):
        try:
            response = _create_chat_completion(
                system,
                user_content,
                merged_params,
                response_format={"type": "json_object"},
            )
            _add_token_usage(accumulated_usage, response)
            content = response.choices[0].message.content or ""
            if not content.strip():
                _log.warning("GPT_request_json: attempt %d returned empty content", attempt + 1)
                continue
            result = json.loads(content)
            if _is_valid(result):
                return finish_deep(result, attempt, False)
            _log.warning("GPT_request_json: attempt %d missing keys or error in parsed result", attempt + 1)
        except json.JSONDecodeError:
            _log.warning("GPT_request_json: attempt %d JSON parse failed", attempt + 1)
        except Exception as e:
            _log.warning("GPT_request_json: attempt %d API error: %s", attempt + 1, e)

    # Attempt 3: plain text mode (no response_format)
    _log.info("GPT_request_json: JSON mode failed after 2 attempts, falling back to plain text mode")
    plain_params = dict(merged_params)
    plain_params.pop("response_format", None)
    try:
        response = _create_chat_completion(system, user_content, plain_params)
        _add_token_usage(accumulated_usage, response)
        raw_content = response.choices[0].message.content or ""
        if raw_content.strip():
            _log.info("GPT_request_json: plain text mode returned content successfully")
            try:
                parsed = json.loads(raw_content)
                if _is_valid(parsed):
                    return finish_deep(parsed, 2, True)
            except (json.JSONDecodeError, TypeError):
                pass
            return finish_deep(_make_fallback(raw_content), 2, True)
        _log.warning("GPT_request_json: plain text mode also returned empty, using preset fallback")
    except Exception as e:
        _log.warning("GPT_request_json: plain text mode API error: %s", e)

    # All attempts exhausted: return preset fallback
    _log.error("GPT_request_json: all 3 attempts failed, returning preset fallback")
    fb = _make_fallback("")
    fb["_error"] = True
    return finish_deep(fb, 2, True)


def get_embedding(text, model=None):
    if model is None:
        model = _cfg.DefaultModel.embedding
    client = OpenAI(api_key=_cfg.embedding_api_key, base_url=_cfg.embedding_base_url)
    text = text.replace("\n", " ")
    if not text:
        text = "this is blank"
    try:
        response = client.embeddings.create(input=[text], model=model)
        _record_model_call(
            call_type="embedding",
            model=str(model),
            retry_count=0,
            fallback_used=False,
            token_usage=_token_usage(response),
        )
        return response.data[0].embedding
    except Exception as e:
        _record_model_call(
            call_type="embedding",
            model=str(model),
            retry_count=0,
            fallback_used=False,
            token_usage=_token_usage(object()),
        )
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
        _record_model_call(
            call_type="connection_test_completion",
            model=str(_cfg.DefaultModel.completion),
            retry_count=0,
            fallback_used=False,
            token_usage=_token_usage(resp),
        )
        output = resp.choices[0].message.content or "(empty)"
        print(f"  Completion API: OK")
        print(f"    input:  [user] 'hi'")
        print(f"    output: {repr(output)}")
        print(f"    model:  {resp.model}")
        print(f"    usage:  prompt_tokens={resp.usage.prompt_tokens}, completion_tokens={resp.usage.completion_tokens}")
    except Exception as e:
        _record_model_call(
            call_type="connection_test_completion",
            model=str(_cfg.DefaultModel.completion),
            retry_count=0,
            fallback_used=False,
            token_usage=_token_usage(object()),
        )
        print(f"  Completion API: FAILED - {e}")
        print("\nFix OPENAI_API_KEY / OPENAI_BASE_URL in .env and retry.")
        sys.exit(1)

    print()

    # Embedding API
    try:
        client = OpenAI(api_key=_cfg.embedding_api_key, base_url=_cfg.embedding_base_url)
        resp = client.embeddings.create(input=["test"], model=_cfg.DefaultModel.embedding)
        _record_model_call(
            call_type="connection_test_embedding",
            model=str(_cfg.DefaultModel.embedding),
            retry_count=0,
            fallback_used=False,
            token_usage=_token_usage(resp),
        )
        vec = resp.data[0].embedding
        print(f"  Embedding API: OK")
        print(f"    input:  'test'")
        print(f"    output: dim={len(vec)}, first_5={vec[:5]}")
        print(f"    model:  {_cfg.DefaultModel.embedding}")
        print(f"    usage:  prompt_tokens={resp.usage.prompt_tokens}, total_tokens={resp.usage.total_tokens}")
    except Exception as e:
        _record_model_call(
            call_type="connection_test_embedding",
            model=str(_cfg.DefaultModel.embedding),
            retry_count=0,
            fallback_used=False,
            token_usage=_token_usage(object()),
        )
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
