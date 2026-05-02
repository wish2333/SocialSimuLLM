# socialsimullm/frontend/utils.py

# -*- coding: utf-8 -*-

"""
Frontend utility functions for SocialSimuLLM.

Provides subprocess-based experiment launching and file-polling
status checks for the Streamlit frontend.

@author: Huang Miaosen
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Any

from socialsimullm.experiment.config import ExperimentConfig
from socialsimullm.experiment.storage import create_run_dir, find_run_dir, is_complete


def launch_experiment(config: ExperimentConfig) -> str:
    """Launch an experiment as an independent subprocess.

    Saves the config YAML to the run directory, then spawns
    `uv run socialsimullm run --config <path>` as a background process.
    The simulation runs independently and survives browser close.

    Args:
        config: Validated ExperimentConfig to run.

    Returns:
        The experiment_id of the launched experiment.
    """
    project = config.project or config.experiment_id

    # Create run directory and save config
    run_dir = create_run_dir(project, config.experiment_id)
    config_path = str(run_dir / "config.yaml")
    config.to_yaml(config_path)

    # Determine the uv/socialsimullm executable path
    # On Windows, use the same Python that's running Streamlit
    python_exe = sys.executable
    module_path = "socialsimullm.__main__:main"

    # Launch as subprocess (non-blocking)
    proc = subprocess.Popen(
        [python_exe, "-m", module_path, "run", "--config", config_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.getcwd(),
    )

    # Brief check: if process exits immediately, it likely failed
    import time
    time.sleep(2)
    if proc.poll() is not None:
        stderr_output = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
        raise RuntimeError(
            f"Experiment failed to start (exit code {proc.returncode}). "
            f"stderr: {stderr_output}"
        )

    return config.experiment_id


def poll_experiment_status(
    experiment_id: str, project: str
) -> str:
    """Check if an experiment has completed.

    Args:
        experiment_id: The experiment identifier.
        project: Project name.

    Returns:
        One of: "running", "completed", "not_found".
    """
    try:
        run_dir = find_run_dir(experiment_id, project)
        if is_complete(run_dir):
            return "completed"
        return "running"
    except FileNotFoundError:
        return "not_found"
