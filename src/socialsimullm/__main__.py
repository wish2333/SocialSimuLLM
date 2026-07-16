# socialsimullm/__main__.py

# -*- coding: utf-8 -*-

"""
CLI entry point for SocialSimuLLM.

Usage:
    # Legacy mode (Phase 1 behavior)
    uv run socialsimullm --project <name> [--steps N] [--model <model>]

    # Experiment mode (Phase 2)
    uv run socialsimullm run --config <config.yaml> [--id <experiment_id>]
    uv run socialsimullm resume --config <config.yaml> [--step latest]
    uv run socialsimullm batch --config <config.yaml> --seeds 42,43,44
    uv run socialsimullm list [--project <name>]

@author: Huang Miaosen
"""

from typing import Any

from socialsimullm.utils.config import load_config, load_experiment_config
from socialsimullm.simulator.core import SimulatorCore


def _handle_run_command(args: Any) -> None:
    """Handle the 'run' subcommand."""
    from socialsimullm.experiment.config import ExperimentConfig
    from socialsimullm.experiment.runner import ExperimentRunner

    config = ExperimentConfig.from_yaml(args.config)
    if args.id:
        config.experiment_id = args.id

    runner = ExperimentRunner()
    eid = runner.run_single(config)
    print(f"Experiment {eid} completed.")


def _handle_batch_command(args: Any) -> None:
    """Handle the 'batch' subcommand."""
    from socialsimullm.experiment.config import ExperimentConfig
    from socialsimullm.experiment.runner import ExperimentRunner

    config = ExperimentConfig.from_yaml(args.config)
    seeds = [int(s.strip()) for s in args.seeds.split(",")]

    runner = ExperimentRunner()
    eids = runner.run_batch(config, seeds)
    print(f"Batch completed: {eids}")


def _handle_resume_command(args: Any) -> None:
    """Handle the 'resume' subcommand."""
    from socialsimullm.experiment.config import ExperimentConfig
    from socialsimullm.experiment.runner import ExperimentRunner

    config = ExperimentConfig.from_yaml(args.config)
    raw_step = str(args.step).strip().lower()
    if raw_step == "latest":
        step = None
    else:
        try:
            step = int(raw_step)
        except ValueError as exc:
            raise ValueError("--step must be an integer or 'latest'") from exc
        if step < 0:
            raise ValueError("--step must be non-negative")

    runner = ExperimentRunner()
    eid = runner.resume_single(config, step=step)
    selected = "latest checkpoint" if step is None else f"step {step}"
    print(f"Experiment {eid} resumed from {selected} and completed.")


def _handle_list_command(args: Any) -> None:
    """Handle the 'list' subcommand."""
    from socialsimullm.experiment.storage import list_experiments

    project_filter = getattr(args, "project", None)
    experiments = list_experiments(project_filter)

    if not experiments:
        print("No experiments found.")
        return

    print(f"{'ID':<20} {'Project':<20} {'Status':<12} {'Steps':<8} {'Events':<8} {'Model'}")
    print("-" * 85)
    for exp in experiments:
        print(
            f"{exp['experiment_id']:<20} "
            f"{exp['project']:<20} "
            f"{exp['status']:<12} "
            f"{exp.get('latest_checkpoint_step', 0):<8} "
            f"{exp.get('event_count', 0):<8} "
            f"{exp.get('model', '')}"
        )


def _handle_doctor_command(args: Any) -> None:
    """Handle the 'doctor' subcommand - pre-flight API connectivity check."""
    import os
    from socialsimullm.utils.config import (
        SimulationConfig, _apply_config_to_globals,
    )

    cfg = SimulationConfig(
        project_name="doctor",
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        openai_base_url=os.environ.get("OPENAI_BASE_URL", ""),
        embedding_model=os.environ.get("OPENAI_EMBEDDING_MODEL", "BAAI/bge-m3"),
        embedding_base_url=os.environ.get("EMBEDDING_BASE_URL", ""),
        embedding_api_key=os.environ.get("EMBEDDING_API_KEY", ""),
        completion_model=os.environ.get("OPENAI_MODEL", "deepseek-v4-flash"),
    )
    _apply_config_to_globals(cfg)

    from socialsimullm.utils.text_generation import test_connections
    test_connections()


def main() -> None:
    """Parse CLI arguments and dispatch to the appropriate handler."""
    command, args = load_experiment_config()

    if command == "run":
        _handle_run_command(args)
    elif command == "resume":
        _handle_resume_command(args)
    elif command == "batch":
        _handle_batch_command(args)
    elif command == "list":
        _handle_list_command(args)
    elif command == "doctor":
        _handle_doctor_command(args)
    else:
        # Legacy mode (backward compatible with Phase 1)
        config = load_config()
        simulator = SimulatorCore(config)
        simulator.initialize()
        simulator.run(max_steps=config.max_steps)


if __name__ == "__main__":
    main()
