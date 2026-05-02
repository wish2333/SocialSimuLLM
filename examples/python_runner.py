# SocialSimuLLM Python API examples (v3.1.0)
#
# Usage:
#   uv run python examples/python_runner.py              # Safe demos (no API calls)
#   uv run python examples/python_runner.py --run        # Run a single experiment
#   uv run python examples/python_runner.py --run batch  # Run batch experiment
#
# Requires OPENAI_API_KEY and OPENAI_BASE_URL env vars (or .env file) for actual runs.

import argparse
import os
import sys

from socialsimullm.experiment.config import ExperimentConfig
from socialsimullm.experiment.runner import ExperimentRunner
from socialsimullm.experiment.storage import list_experiments, find_run_dir, is_complete
from socialsimullm.experiment.analysis import (
    load_results,
    get_experiment_summary,
)


def example_single_run() -> str:
    """Run a single experiment from code (no YAML file needed).

    Returns:
        The experiment_id of the completed run.
    """
    config = ExperimentConfig(
        experiment_id="api_test_001",
        project="api_demo",
        # model and embedding_model default to env vars (.env / OPENAI_MODEL)
        simulation_steps=144,
        memory_limit=10,
        random_seed=42,
        checkpoint_interval=10,
        reflection_enabled=True,
    )

    runner = ExperimentRunner()
    eid = runner.run_single(config)
    print(f"Experiment completed: {eid}")
    return eid


def example_batch_run() -> list[str]:
    """Run batch experiments with different seeds.

    Returns:
        List of experiment_ids for each completed run.
    """
    config = ExperimentConfig(
        experiment_id="api_batch",
        project="api_batch_demo",
        simulation_steps=72,
        random_seed=0,
        checkpoint_interval=10,
    )

    seeds = [42, 43, 44]
    runner = ExperimentRunner()
    eids = runner.run_batch(config, seeds)
    print(f"Batch completed: {eids}")
    return eids


def example_spatial_variants() -> None:
    """Run experiments with different spatial topologies.

    Demonstrates v3.1.0 spatial_config for comparing topologies.
    """
    topologies = ["ring", "small_world", "grid", "random", "scale_free"]

    for topo in topologies:
        config = ExperimentConfig(
            experiment_id=f"spatial_{topo}",
            project="spatial_comparison",
            simulation_steps=72,
            random_seed=42,
            checkpoint_interval=10,
            spatial_config={
                "topology": topo,
                "num_locations": 5,
                "seed": 42,
            },
            fov_enabled=True,
            path_planner_enabled=True,
        )

        runner = ExperimentRunner()
        eid = runner.run_single(config)
        print(f"  {topo}: {eid}")


def example_cognitive_run() -> None:
    """Run an experiment with goal-driven planning enabled.

    Demonstrates v3.1.0 goal and reflection integration.
    """
    config = ExperimentConfig(
        experiment_id="cognitive_test",
        project="cognitive_demo",
        simulation_steps=144,
        random_seed=42,
        checkpoint_interval=20,
        goal_enabled=True,
        max_active_goals=3,
        reflection_enabled=True,
        reflection_include_in_planning=True,
    )

    runner = ExperimentRunner()
    eid = runner.run_single(config)
    print(f"Cognitive experiment completed: {eid}")


def example_scenario_generation() -> None:
    """Generate a simulation world from natural language.

    Demonstrates v3.1.0 ScenarioGenerator.
    """
    from socialsimullm.experiment.scenario import ScenarioGenerator

    gen = ScenarioGenerator()

    description = (
        "A bustling harbor town with a fish market, tavern, shipyard, "
        "and town hall. 5 characters: a fisherman, a tavern keeper, "
        "a shipbuilder, a merchant, and a town mayor."
    )

    print(f"Generating scenario: {description}")
    town_data = gen.generate(description)

    # Validate
    issues = gen.validate_town_data(town_data)
    errors = [i for i in issues if i["severity"] == "error"]
    if errors:
        print(f"Validation errors: {errors}")
        return

    # Save
    output_path = os.path.join("examples", "generated_town.json")
    gen.save(town_data, output_path)
    print(f"Saved to {output_path}")
    print(f"  Locations: {list(town_data.get('town_areas', {}).keys())}")
    print(f"  Characters: {list(town_data.get('town_people', {}).keys())}")


def example_research_assistant() -> None:
    """Use the LLM research assistant to analyze an experiment.

    Demonstrates v3.1.0 ResearchAssistant.
    """
    from socialsimullm.experiment.assistant import ResearchAssistant

    eid = "api_test_001"
    assistant = ResearchAssistant()

    try:
        summary = assistant.summarize_experiment(eid)
        print(f"Summary for {eid}:")
        print(summary[:200] + "...")

        patterns = assistant.identify_patterns(eid)
        print(f"\nPatterns ({len(patterns)}):")
        for p in patterns[:3]:
            print(f"  {p}")

    except FileNotFoundError:
        print(f"Experiment '{eid}' not found. Run it first.")


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
    config = ExperimentConfig(
        project="yaml_demo",
        simulation_steps=144,
        random_seed=123,
    )

    yaml_path = os.path.join("examples", "roundtrip_test.yaml")
    config.to_yaml(yaml_path)
    print(f"Config saved to {yaml_path}")

    loaded = ExperimentConfig.from_yaml(yaml_path)
    print(f"Loaded: project={loaded.project}, seed={loaded.random_seed}")

    if os.path.exists(yaml_path):
        os.remove(yaml_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="SocialSimuLLM Python API Examples")
    parser.add_argument("--run", default=None, help="Run: 'single', 'batch', 'spatial', 'cognitive', or 'scenario'")
    parser.add_argument("--demo", default=None, help="Safe demo: 'list', 'scenario', 'yaml'")
    args = parser.parse_args()

    if args.run == "single":
        example_single_run()
    elif args.run == "batch":
        example_batch_run()
    elif args.run == "spatial":
        example_spatial_variants()
    elif args.run == "cognitive":
        example_cognitive_run()
    elif args.run == "scenario":
        example_scenario_generation()
    elif args.run == "assistant":
        example_research_assistant()
    elif args.demo == "list":
        example_list_all()
    elif args.demo == "scenario":
        example_scenario_generation()
    elif args.demo == "yaml":
        example_save_and_load_yaml()
    else:
        # Default: safe demos only (no API calls)
        print("SocialSimuLLM Python API Examples (v3.1.0)")
        print("=" * 45)
        print()
        print("Safe demos (no API key required):")
        example_list_all()
        example_save_and_load_yaml()
        print()
        print("To run simulations, use:")
        print("  uv run python examples/python_runner.py --run single")
        print("  uv run python examples/python_runner.py --run batch")
        print("  uv run python examples/python_runner.py --run spatial")
        print("  uv run python examples/python_runner.py --run cognitive")
        print("  uv run python examples/python_runner.py --run scenario")
        print("  uv run python examples/python_runner.py --run assistant")


if __name__ == "__main__":
    main()
