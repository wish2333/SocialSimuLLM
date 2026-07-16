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
import re
import subprocess
import sys
from typing import Any

from socialsimullm.experiment.config import ExperimentConfig
from socialsimullm.experiment.storage import create_run_dir, find_run_dir, is_complete


_SENSITIVE_ERROR_FIELD = re.compile(
    r"(?i)(authorization|x-api-key|api[-_ ]?key)"
    r"(\s*['\"]?\s*[:=]\s*['\"]?)([^,\r\n}]+)"
)
_SECRET_TOKEN = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b")


def _sanitize_launch_error(message: str) -> str:
    """Redact common credential fields before showing stderr in the UI."""
    message = _SENSITIVE_ERROR_FIELD.sub(r"\1\2[REDACTED]", message)
    return _SECRET_TOKEN.sub("[REDACTED]", message)


def launch_experiment(config: ExperimentConfig) -> str:
    """Launch an experiment as an independent subprocess.

    Saves the config YAML to the run directory, then spawns
    `python -m socialsimullm run --config <path>` as a background process.
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

    # Use the same Python environment that is running Streamlit.
    python_exe = sys.executable

    # Redirect long-running output to disk so OS pipe buffers cannot fill and
    # block the simulation. The files also preserve diagnostics for failed
    # launches without keeping parent-side file descriptors open.
    stdout_path = run_dir / "experiment.stdout.log"
    stderr_path = run_dir / "experiment.stderr.log"
    with (
        open(stdout_path, "ab") as stdout_log,
        open(stderr_path, "ab") as stderr_log,
    ):
        proc = subprocess.Popen(
            [python_exe, "-m", "socialsimullm", "run", "--config", config_path],
            stdout=stdout_log,
            stderr=stderr_log,
            cwd=os.getcwd(),
        )

    # Brief check: if process exits immediately, it likely failed
    import time
    time.sleep(2)
    if proc.poll() is not None:
        try:
            stderr_output = stderr_path.read_text(
                encoding="utf-8", errors="replace"
            )[-4000:]
            stderr_output = _sanitize_launch_error(stderr_output)
        except OSError:
            stderr_output = ""
        raise RuntimeError(
            f"Experiment failed to start (exit code {proc.returncode}). "
            f"stderr: {stderr_output or f'see {stderr_path}'}"
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
