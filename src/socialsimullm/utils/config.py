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

from dotenv import load_dotenv


def _load_dotenv() -> None:
    """Load .env file from CWD or project root into os.environ.

    Searches in order:
      1. ./.env  (current working directory)
      2. .env    (same directory as this source file, i.e. project root)

    .env values override existing environment variables (CLI > .env > system env).
    """
    load_dotenv(os.path.join(os.getcwd(), ".env"), override=True)
    src_dir = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(src_dir, "..", "..", "..", ".env"), override=True)


# Load .env as early as possible so all os.environ.get() calls pick it up
_load_dotenv()


@dataclass
class SimulationConfig:
    """Validated simulation configuration.

    Attributes:
        project_name: Project directory name under projects/.
        openai_api_key: OpenAI API key for LLM calls.
        openai_base_url: OpenAI-compatible API base URL.
        key_owner: Name of the API key owner.
        embedding_model: Model name for text embeddings.
        embedding_base_url: Separate base URL for embedding API. Empty = same as openai_base_url.
        embedding_api_key: Separate API key for embedding API. Empty = same as openai_api_key.
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
    embedding_base_url: str = ""
    embedding_api_key: str = ""
    completion_model: str = "deepseek-v4-flash"
    max_steps: int = 0
    memory_limit: int = 10
    checkpoint_interval: int = 0
    prompt_meta: str = "### Instruction:\n{}\n### Response:"
    reflection_enabled: bool = True
    reflection_importance_threshold: int = 15
    reflection_min_observations: int = 3
    reflection_token_limit: int = 500
    reflection_include_in_planning: bool = True
    fov_enabled: bool = False
    fov_distance: float = 0.0
    path_planner_enabled: bool = False
    multi_hop_movement: bool = True
    goal_enabled: bool = False
    max_active_goals: int = 3
    json_mode_enabled: bool = True


class DefaultModel:
    """Model name constants (backward-compatible with text_generation.py)."""

    embedding: str = "BAAI/bge-m3"
    completion: str = "deepseek-v4-flash"


# Backward-compatible module-level variables
openai_api_key: str = ""
openai_base_url: str = ""
key_owner: str = ""
embedding_api_key: str = ""
embedding_base_url: str = ""
json_mode_enabled: bool = True


def _apply_config_to_globals(config: SimulationConfig) -> None:
    """Sync dataclass values to module-level variables for backward compat.

    Why: text_generation.py imports openai_api_key and openai_base_url
    as module-level names. This keeps them in sync with the config.
    """
    global openai_api_key, openai_base_url, key_owner, embedding_api_key, embedding_base_url, json_mode_enabled
    openai_api_key = config.openai_api_key
    openai_base_url = config.openai_base_url
    key_owner = config.key_owner
    embedding_api_key = config.embedding_api_key or config.openai_api_key
    embedding_base_url = config.embedding_base_url or config.openai_base_url
    DefaultModel.embedding = config.embedding_model
    DefaultModel.completion = config.completion_model
    json_mode_enabled = config.json_mode_enabled


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
            "Set OPENAI_API_KEY in a .env file, environment variable, or CLI --api-key."
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

    Priority (highest to lowest): CLI args > .env > system env vars > defaults.

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
        help="OpenAI API key (or set OPENAI_API_KEY in .env / env var)",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="OpenAI-compatible base URL (or set OPENAI_BASE_URL in .env / env var)",
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
    parser.add_argument(
        "--no-reflection",
        action="store_true",
        default=False,
        help="Disable the reflection system",
    )
    parser.add_argument(
        "--reflection-threshold",
        type=int,
        default=15,
        help="Cumulative importance to trigger mid-day reflection (default: 15)",
    )
    parser.add_argument(
        "--no-json-mode",
        action="store_true",
        default=False,
        help="Disable JSON output mode for DeepSeek V4 models",
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
            or os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
        ),
        key_owner=os.environ.get("SOCIALSIMU_KEY_OWNER", ""),
        embedding_model=(
            args.embedding_model
            or os.environ.get("OPENAI_EMBEDDING_MODEL", DefaultModel.embedding)
        ),
        embedding_base_url=os.environ.get("EMBEDDING_BASE_URL", ""),
        embedding_api_key=os.environ.get("EMBEDDING_API_KEY", ""),
        completion_model=(
            args.model
            or os.environ.get("OPENAI_MODEL", DefaultModel.completion)
        ),
        max_steps=args.steps,
        memory_limit=args.memory_limit,
        checkpoint_interval=args.checkpoint_interval,
        reflection_enabled=not args.no_reflection,
        reflection_importance_threshold=args.reflection_threshold,
        json_mode_enabled=not args.no_json_mode,
    )

    _apply_config_to_globals(config)
    validate_config(config)

    return config


def load_experiment_config(
    argv: list[str] | None = None,
) -> tuple[str | None, Any]:
    """Parse experiment CLI subcommands.

    Detects whether the invocation uses a subcommand (run, batch, list)
    or falls through to legacy mode. The detection checks if the first
    non-script argument is a known subcommand name.

    Args:
        argv: Command-line arguments. None means sys.argv is used.

    Returns:
        Tuple of (command, args_namespace).
        command is one of: "run", "batch", "list", None (legacy mode).
        When command is None, the caller should use load_config() instead.
    """
    check_argv = argv if argv is not None else _get_argv()[1:]
    if not check_argv or check_argv[0] not in ("run", "batch", "list", "doctor"):
        return None, None

    parser = argparse.ArgumentParser(
        prog="socialsimullm",
        description="SocialSimuLLM experiment subcommands",
    )
    subparsers = parser.add_subparsers(dest="command")

    # "run" subcommand
    run_parser = subparsers.add_parser("run", help="Run a single experiment")
    run_parser.add_argument(
        "--config",
        required=True,
        help="Path to experiment config YAML file",
    )
    run_parser.add_argument(
        "--id",
        default=None,
        help="Override experiment ID",
    )

    # "batch" subcommand
    batch_parser = subparsers.add_parser("batch", help="Run batch experiments")
    batch_parser.add_argument(
        "--config",
        required=True,
        help="Path to experiment config YAML file",
    )
    batch_parser.add_argument(
        "--seeds",
        required=True,
        help="Comma-separated random seed list (e.g., 42,43,44)",
    )

    # "list" subcommand
    list_parser = subparsers.add_parser("list", help="List all experiments")
    list_parser.add_argument(
        "--project",
        default=None,
        help="Filter by project name",
    )

    # "doctor" subcommand
    subparsers.add_parser("doctor", help="Test LLM and embedding API connectivity")

    args = parser.parse_args(argv)
    return args.command, args


def _get_argv() -> list[str]:
    """Get sys.argv in a testable way."""
    import sys
    return sys.argv
