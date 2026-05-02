# SocialSimuLLM Python API usage examples
#
# Usage:
#   uv run python examples/python_runner.py
#
# Requires OPENAI_API_KEY environment variable to be set for actual runs.

from socialsimullm.experiment.config import ExperimentConfig
from socialsimullm.experiment.runner import ExperimentRunner
from socialsimullm.experiment.storage import list_experiments, find_run_dir, is_complete
from socialsimullm.experiment.analysis import (
    load_results,
    get_experiment_summary,
)


def example_single_run() -> None:
    """Run a single experiment from code (no YAML file needed)."""
    config = ExperimentConfig(
        experiment_id="api_test_001",
        project="api_demo",
        model="gpt-4o-mini",
        embedding_model="BAAI/bge-m3",
        simulation_steps=144,
        memory_limit=10,
        random_seed=42,
        checkpoint_interval=10,
        reflection_enabled=True,
    )

    runner = ExperimentRunner()
    eid = runner.run_single(config)
    print(f"Experiment completed: {eid}")


def example_batch_run() -> None:
    """Run batch experiments with different seeds."""
    config = ExperimentConfig(
        experiment_id="api_batch",
        project="api_batch_demo",
        model="gpt-4o-mini",
        simulation_steps=72,
        random_seed=0,
        checkpoint_interval=10,
    )

    seeds = [42, 43, 44]
    runner = ExperimentRunner()
    eids = runner.run_batch(config, seeds)
    print(f"Batch completed: {eids}")


def example_load_results() -> None:
    """Load and analyze results from a completed experiment."""
    eid = "api_test_001"

    try:
        summary = get_experiment_summary(eid)
        print(f"Experiment: {eid}")
        print(f"  Steps: {summary['total_steps']}")
        print(f"  Events: {summary['total_events']}")
        print(f"  Agents: {summary['agent_names']}")
        print(f"  Event types: {summary['event_type_counts']}")
    except FileNotFoundError:
        print(f"Experiment '{eid}' not found. Run it first.")


def example_list_all() -> None:
    """List all experiments and their status."""
    experiments = list_experiments()

    if not experiments:
        print("No experiments found in runs/ directory.")
        return

    print(f"{'ID':<20} {'Project':<20} {'Status':<12} {'Events':<8}")
    print("-" * 60)
    for exp in experiments:
        print(
            f"{exp['experiment_id']:<20} "
            f"{exp['project']:<20} "
            f"{exp['status']:<12} "
            f"{exp.get('event_count', 0):<8}"
        )


def example_save_and_load_yaml() -> None:
    """Demonstrate YAML round-trip: create -> save -> load -> run."""
    import os

    # Create config programmatically
    config = ExperimentConfig(
        project="yaml_demo",
        model="gpt-4o-mini",
        simulation_steps=144,
        random_seed=123,
    )

    # Save to YAML
    yaml_path = os.path.join("examples", "roundtrip_test.yaml")
    config.to_yaml(yaml_path)
    print(f"Config saved to {yaml_path}")

    # Load from YAML
    loaded = ExperimentConfig.from_yaml(yaml_path)
    print(f"Loaded: project={loaded.project}, seed={loaded.random_seed}")

    # Clean up demo file
    if os.path.exists(yaml_path):
        os.remove(yaml_path)


if __name__ == "__main__":
    print("SocialSimuLLM Python API Examples")
    print("=" * 40)

    example_save_and_load_yaml()
    example_list_all()

    # Uncomment to run actual simulations (requires OPENAI_API_KEY):
    # example_single_run()
    # example_batch_run()
    # example_load_results()
