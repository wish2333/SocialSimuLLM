# socialsimullm/experiment/__init__.py

"""
Experiment infrastructure for SocialSimuLLM.

Provides ExperimentConfig, ExperimentRunner, and helpers for
reproducible batch experiment execution and result analysis.
"""

from socialsimullm.experiment.analysis import (
    compare_experiments,
    get_experiment_summary,
    load_results,
    load_results_dataframe,
)
from socialsimullm.experiment.config import ExperimentConfig, MemoryConfig
from socialsimullm.experiment.runner import ExperimentRunner
from socialsimullm.experiment.scenario import ScenarioGenerator
from socialsimullm.experiment.storage import (
    create_run_dir,
    find_run_dir,
    get_latest_checkpoint_step,
    get_runs_root,
    is_complete,
    list_experiments,
    load_checkpoint,
)

__all__ = [
    "ExperimentConfig",
    "ExperimentRunner",
    "MemoryConfig",
    "ScenarioGenerator",
    "compare_experiments",
    "create_run_dir",
    "find_run_dir",
    "get_experiment_summary",
    "get_latest_checkpoint_step",
    "get_runs_root",
    "is_complete",
    "list_experiments",
    "load_checkpoint",
    "load_results",
    "load_results_dataframe",
]
