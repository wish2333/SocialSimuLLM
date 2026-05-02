# socialsimullm/experiment/storage.py

# -*- coding: utf-8 -*-

"""
Run directory management and checkpoint helpers for SocialSimuLLM.

Standardizes the experiment output layout under runs/{project}/{experiment_id}/
and provides functions for creating run directories, loading checkpoints,
and listing experiments.

@author: Huang Miaosen
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def get_runs_root() -> Path:
    """Return the root runs directory at the current working directory."""
    return Path(os.getcwd()) / "runs"


def create_run_dir(project: str, experiment_id: str) -> Path:
    """Create the standardized run directory structure.

    Creates:
        runs/{project}/{experiment_id}/
        runs/{project}/{experiment_id}/agent_data/

    Args:
        project: Project name (top-level grouping under runs/).
        experiment_id: Unique experiment identifier.

    Returns:
        Path to the created run directory.
    """
    run_dir = get_runs_root() / project / experiment_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "agent_data").mkdir(exist_ok=True)
    return run_dir


def is_complete(run_dir: Path) -> bool:
    """Check if an experiment run has completed.

    Args:
        run_dir: Path to the experiment run directory.

    Returns:
        True if done.flag exists in the run directory.
    """
    return (run_dir / "done.flag").exists()


def list_experiments(project: str | None = None) -> list[dict[str, Any]]:
    """List all experiments, optionally filtered by project.

    Scans the runs/ directory tree and returns metadata for each
    experiment directory found.

    Args:
        project: If provided, only list experiments under this project.

    Returns:
        List of dicts with keys: experiment_id, project, status,
        steps, checkpoint_count, created_at.
    """
    runs_root = get_runs_root()
    if not runs_root.exists():
        return []

    results: list[dict[str, Any]] = []

    if project:
        project_dir = runs_root / project
        if not project_dir.exists():
            return []
        project_dirs = [(project, project_dir)]
    else:
        project_dirs = sorted(
            (p.name, p) for p in runs_root.iterdir() if p.is_dir()
        )

    for proj_name, proj_dir in project_dirs:
        if not proj_dir.is_dir():
            continue
        for exp_dir in sorted(proj_dir.iterdir()):
            if not exp_dir.is_dir():
                continue
            experiment_id = exp_dir.name
            complete = is_complete(exp_dir)

            # Load config snapshot if available
            config_data: dict[str, Any] = {}
            config_path = exp_dir / "config.yaml"
            if config_path.exists():
                try:
                    import yaml
                    with open(config_path, "r", encoding="utf-8") as f:
                        config_data = yaml.safe_load(f) or {}
                except Exception:
                    pass

            # Count checkpoints
            checkpoint_count = 0
            latest_step = 0
            checkpoints_dir = exp_dir / "checkpoints"
            if checkpoints_dir.exists():
                for cp_dir in checkpoints_dir.iterdir():
                    if cp_dir.is_dir() and cp_dir.name.startswith("step_"):
                        checkpoint_count += 1
                        try:
                            step_num = int(cp_dir.name.split("_")[1])
                            if step_num > latest_step:
                                latest_step = step_num
                        except (ValueError, IndexError):
                            pass

            # Determine creation time
            created_at = ""
            meta_path = exp_dir / "meta.json"
            if meta_path.exists():
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    created_at = meta.get("global_time", "")
                except Exception:
                    pass

            # Count events from JSONL
            event_count = 0
            events_path = exp_dir / "events.jsonl"
            if events_path.exists():
                try:
                    with open(events_path, "r", encoding="utf-8") as f:
                        event_count = sum(1 for _ in f)
                except Exception:
                    pass

            results.append({
                "experiment_id": experiment_id,
                "project": proj_name,
                "status": "completed" if complete else "running",
                "event_count": event_count,
                "checkpoint_count": checkpoint_count,
                "latest_checkpoint_step": latest_step,
                "model": config_data.get("model", ""),
                "seed": config_data.get("random_seed", 0),
                "created_at": created_at,
            })

    return results


def find_run_dir(
    experiment_id: str, project: str | None = None
) -> Path:
    """Locate the run directory for a given experiment_id.

    Args:
        experiment_id: The experiment identifier to find.
        project: If provided, look only under this project directory.

    Returns:
        Path to the run directory.

    Raises:
        FileNotFoundError: If no matching run directory is found.
    """
    runs_root = get_runs_root()

    if project:
        run_dir = runs_root / project / experiment_id
        if run_dir.is_dir():
            return run_dir
        raise FileNotFoundError(
            f"Experiment '{experiment_id}' not found under project '{project}'"
        )

    # Search all projects
    if not runs_root.exists():
        raise FileNotFoundError(
            f"No runs directory found at {runs_root}"
        )

    for proj_dir in runs_root.iterdir():
        if not proj_dir.is_dir():
            continue
        candidate = proj_dir / experiment_id
        if candidate.is_dir():
            return candidate

    raise FileNotFoundError(
        f"Experiment '{experiment_id}' not found in any project under {runs_root}"
    )


def get_latest_checkpoint_step(run_dir: Path) -> int | None:
    """Return the latest checkpoint step number.

    Args:
        run_dir: Path to the experiment run directory.

    Returns:
        The highest step number found, or None if no checkpoints exist.
    """
    checkpoints_dir = run_dir / "checkpoints"
    if not checkpoints_dir.exists():
        return None

    latest: int | None = None
    for cp_dir in checkpoints_dir.iterdir():
        if not cp_dir.is_dir() or not cp_dir.name.startswith("step_"):
            continue
        try:
            step_num = int(cp_dir.name.split("_")[1])
            if latest is None or step_num > latest:
                latest = step_num
        except (ValueError, IndexError):
            continue

    return latest


def load_checkpoint(
    experiment_id: str,
    step: int | None = None,
    project: str | None = None,
) -> dict[str, Any]:
    """Load a checkpoint from a completed experiment.

    Args:
        experiment_id: The experiment identifier.
        step: Checkpoint step number. If None, loads the latest checkpoint.
        project: Project name. If None, searches all projects.

    Returns:
        Dict with keys: spatial_graph, agent_states, memory_summary, meta,
        step, experiment_id.

    Raises:
        FileNotFoundError: If the experiment or checkpoint does not exist.
    """
    run_dir = find_run_dir(experiment_id, project)

    if step is None:
        step = get_latest_checkpoint_step(run_dir)
    if step is None:
        raise FileNotFoundError(
            f"No checkpoints found for experiment '{experiment_id}'"
        )

    checkpoint_dir = run_dir / "checkpoints" / f"step_{step}"
    if not checkpoint_dir.exists():
        raise FileNotFoundError(
            f"Checkpoint step_{step} not found for experiment '{experiment_id}'"
        )

    result: dict[str, Any] = {
        "experiment_id": experiment_id,
        "project": run_dir.parent.name,
        "step": step,
    }

    for filename in ("spatial_graph.json", "agent_states.json", "memory_summary.json", "meta.json"):
        filepath = checkpoint_dir / filename
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    result[filename.replace(".json", "")] = json.load(f)
            except (json.JSONDecodeError, OSError):
                result[filename.replace(".json", "")] = None
        else:
            result[filename.replace(".json", "")] = None

    return result
