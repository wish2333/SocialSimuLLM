# socialsimullm/utils/config.py

# -*- coding: utf-8 -*-

"""
Configuration management for SocialSimuLLM.

Provides SimulationConfig dataclass with CLI argument parsing,
environment variable overrides, and validation.

@author: Huang Miaosen

Comment format: Use standard Google style docstring format for comments, bilingual in English and Chinese (note to write English comments first), compatible with VSCode intelligent prompts.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass


@dataclass
class SimulationConfig:
    """Validated simulation configuration.

    Attributes:
        project_name: Project directory name under projects/.
        openai_api_key: OpenAI API key for LLM calls.
        openai_base_url: OpenAI-compatible API base URL.
        key_owner: Name of the API key owner.
        embedding_model: Model name for text embeddings.
        completion_model: Model name for text completion.
        max_steps: Maximum simulation steps. 0 = interactive mode.
        memory_limit: Number of recent experiences to consider.
        checkpoint_interval: Steps between checkpoints. 0 = disabled.
        prompt_meta: Prompt template wrapper for LLM instructions.
    """

    project_name: str
    openai_api_key: str = ""
    openai_base_url: str = ""
    key_owner: str = ""
    embedding_model: str = "BAAI/bge-m3"
    completion_model: str = "gpt-4o-mini"
    max_steps: int = 0
    memory_limit: int = 10
    checkpoint_interval: int = 0
    prompt_meta: str = "### Instruction:\n{}\n### Response:"


class DefaultModel:
    """Model name constants (backward-compatible with text_generation.py)."""

    embedding: str = "BAAI/bge-m3"
    completion: str = "gpt-4o-mini"


# Backward-compatible module-level variables
openai_api_key: str = ""
openai_base_url: str = ""
key_owner: str = ""


def _apply_config_to_globals(config: SimulationConfig) -> None:
    """Sync dataclass values to module-level variables for backward compat.

    Why: text_generation.py imports openai_api_key and openai_base_url
    as module-level names. This keeps them in sync with the config.
    """
    global openai_api_key, openai_base_url, key_owner
    openai_api_key = config.openai_api_key
    openai_base_url = config.openai_base_url
    key_owner = config.key_owner
    DefaultModel.embedding = config.embedding_model
    DefaultModel.completion = config.completion_model


def validate_config(config: SimulationConfig) -> None:
    """Validate configuration and raise ValueError on invalid values.

    Args:
        config: The configuration to validate.

    Raises:
        ValueError: If any configuration value is invalid.
    """
    if not config.project_name or not config.project_name.strip():
        raise ValueError("project_name must be a non-empty string.")

    if not config.openai_api_key or config.openai_api_key == "<your_api_key>":
        raise ValueError(
            "openai_api_key is not set. "
            "Set OPENAI_API_KEY environment variable or configure in config."
        )

    if not config.openai_base_url:
        raise ValueError("openai_base_url must be a non-empty URL.")

    if config.max_steps < 0:
        raise ValueError(f"max_steps must be >= 0, got {config.max_steps}.")

    if config.checkpoint_interval < 0:
        raise ValueError(
            f"checkpoint_interval must be >= 0, got {config.checkpoint_interval}."
        )

    if config.memory_limit < 1:
        raise ValueError(f"memory_limit must be >= 1, got {config.memory_limit}.")


def load_config(argv: list[str] | None = None) -> SimulationConfig:
    """Parse CLI arguments and environment variables into SimulationConfig.

    Priority (highest to lowest): CLI args > env vars > defaults.

    Args:
        argv: Command-line arguments. None means sys.argv is used.

    Returns:
        A validated SimulationConfig instance.
    """
    parser = argparse.ArgumentParser(
        description="SocialSimuLLM - LLM-based Social Simulation Framework"
    )
    parser.add_argument(
        "project_positional",
        nargs="?",
        default=None,
        help="Project name (positional, or use --project)",
    )
    parser.add_argument(
        "--project", "-p",
        default=None,
        help="Project name (creates/loads from projects/<name>/)",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=0,
        help="Number of simulation steps (0 = interactive mode)",
    )
    parser.add_argument(
        "--model", "-m",
        default=None,
        help="Override completion model (e.g., gpt-4o, deepseek-chat)",
    )
    parser.add_argument(
        "--embedding-model",
        default=None,
        help="Override embedding model (e.g., BAAI/bge-m3)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="OpenAI API key (or set OPENAI_API_KEY env var)",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="OpenAI-compatible base URL (or set OPENAI_BASE_URL env var)",
    )
    parser.add_argument(
        "--memory-limit",
        type=int,
        default=10,
        help="Number of recent experiences to consider (default: 10)",
    )
    parser.add_argument(
        "--checkpoint-interval",
        type=int,
        default=0,
        help="Steps between checkpoints (0 = disabled, default: 0)",
    )

    args = parser.parse_args(argv)

    # Resolve project name: --project flag > positional arg
    project_name = args.project or args.project_positional

    # Build config with priority: CLI > env vars > defaults
    config = SimulationConfig(
        project_name=project_name or "",
        openai_api_key=(
            args.api_key
            or os.environ.get("OPENAI_API_KEY", "")
        ),
        openai_base_url=(
            args.base_url
            or os.environ.get("OPENAI_BASE_URL", "http://192.168.1.110:3001/v1")
        ),
        key_owner=os.environ.get("SOCIALSIMU_KEY_OWNER", ""),
        embedding_model=args.embedding_model or DefaultModel.embedding,
        completion_model=args.model or DefaultModel.completion,
        max_steps=args.steps,
        memory_limit=args.memory_limit,
        checkpoint_interval=args.checkpoint_interval,
    )

    _apply_config_to_globals(config)
    validate_config(config)

    return config
