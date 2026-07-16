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
import shutil
import tempfile
from datetime import datetime
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


def _is_experiment_dir(path: Path) -> bool:
    """Check if a directory looks like an experiment run (has town_data.json or events.jsonl)."""
    return (path / "town_data.json").exists() or (path / "events.jsonl").exists()


def list_experiments(project: str | None = None) -> list[dict[str, Any]]:
    """List all experiments, optionally filtered by project.

    Scans the runs/ directory tree and returns metadata for each
    experiment directory found. Supports both flat layout
    (runs/{experiment_id}/) and nested layout (runs/{project}/{experiment_id}/).

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
    seen: set[str] = set()

    # Scan nested layout: runs/{project}/{experiment_id}/
    if project:
        project_dir = runs_root / project
        if project_dir.exists():
            _scan_project_dir(project, project_dir, results, seen)
    else:
        for proj_dir in sorted(runs_root.iterdir()):
            if not proj_dir.is_dir():
                continue
            _scan_project_dir(proj_dir.name, proj_dir, results, seen)

    # Scan flat layout: runs/{experiment_id}/ (directories that look like experiments)
    for d in sorted(runs_root.iterdir()):
        if not d.is_dir() or d.name in seen:
            continue
        if _is_experiment_dir(d):
            _build_experiment_entry(d, d.name, "", results)

    return results


def _scan_project_dir(
    proj_name: str,
    proj_dir: Path,
    results: list[dict[str, Any]],
    seen: set[str],
) -> None:
    """Scan a project directory for nested experiment subdirectories."""
    for exp_dir in sorted(proj_dir.iterdir()):
        if not exp_dir.is_dir() or not _is_experiment_dir(exp_dir):
            continue
        experiment_id = exp_dir.name
        seen.add(experiment_id)
        _build_experiment_entry(exp_dir, experiment_id, proj_name, results)


def _build_experiment_entry(
    exp_dir: Path,
    experiment_id: str,
    proj_name: str,
    results: list[dict[str, Any]],
) -> None:
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

    # Read round/step count from meta.json (more reliable than checkpoints)
    total_steps = 0
    resumed_from_step: int | None = None
    meta_path = exp_dir / "meta.json"
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            total_steps = meta.get("round", 0)
            created_at = meta.get("global_time", "")
            resume_data = meta.get("resume", {})
            if isinstance(resume_data, dict) and "from_step" in resume_data:
                resumed_from_step = int(resume_data["from_step"])
        except Exception:
            created_at = ""
    else:
        created_at = ""

    # Count checkpoints (fallback for step count)
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

    # Use meta.json round as step count; fall back to latest checkpoint
    display_steps = total_steps if total_steps > 0 else latest_step

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
        "latest_checkpoint_step": display_steps,
        "model": config_data.get("model", ""),
        "seed": config_data.get("random_seed", 0),
        "created_at": created_at,
        "resumed_from_step": resumed_from_step,
    })


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


def restore_checkpoint(
    experiment_id: str,
    step: int | None = None,
    project: str | None = None,
) -> dict[str, Any]:
    """Atomically restore a runnable experiment state from a full checkpoint.

    Unlike :func:`load_checkpoint`, this function mutates the run directory.
    Current log tails are archived first, the saved file-backed state is
    restored, and any stale completion marker is removed.
    """
    run_dir = find_run_dir(experiment_id, project)
    if step is None:
        step = get_latest_checkpoint_step(run_dir)
    if step is None:
        raise FileNotFoundError(
            f"No checkpoints found for experiment '{experiment_id}'"
        )
    checkpoint_dir = run_dir / "checkpoints" / f"step_{step}"
    if not checkpoint_dir.is_dir():
        raise FileNotFoundError(
            f"Checkpoint step_{step} not found for experiment '{experiment_id}'"
        )

    required = ("town_data.json", "agent_data", "meta.json", "runtime_state.json")
    missing = [name for name in required if not (checkpoint_dir / name).exists()]
    if missing:
        raise ValueError(
            f"Checkpoint step_{step} is display-only and cannot be resumed; "
            f"missing: {', '.join(missing)}"
        )

    try:
        runtime_state = json.loads(
            (checkpoint_dir / "runtime_state.json").read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid runtime state in checkpoint step_{step}") from exc

    archive_dir = _archive_resume_tail(run_dir, step)
    stage = Path(tempfile.mkdtemp(prefix=".resume-stage-", dir=run_dir))
    try:
        for filename in ("town_data.json", "meta.json"):
            shutil.copy2(checkpoint_dir / filename, stage / filename)
        shutil.copytree(checkpoint_dir / "agent_data", stage / "agent_data")
        for filename in (
            "events.jsonl",
            "simulation_log.txt",
            "simulation_summary.txt",
            "model_calls.jsonl",
        ):
            source = checkpoint_dir / filename
            if source.is_file():
                shutil.copy2(source, stage / filename)

        _replace_path(stage / "town_data.json", run_dir / "town_data.json")
        _replace_directory(stage / "agent_data", run_dir / "agent_data")
        _replace_path(stage / "meta.json", run_dir / "meta.json")
        for filename in (
            "events.jsonl",
            "simulation_log.txt",
            "simulation_summary.txt",
            "model_calls.jsonl",
        ):
            staged_log = stage / filename
            current_log = run_dir / filename
            if staged_log.exists():
                _replace_path(staged_log, current_log)
            elif current_log.exists():
                current_log.unlink()
    finally:
        if stage.exists():
            shutil.rmtree(stage)

    done_flag = run_dir / "done.flag"
    if done_flag.exists():
        done_flag.unlink()
    error_log = run_dir / "error.log"
    if error_log.exists():
        error_log.unlink()

    meta_path = run_dir / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["resume"] = {
        "from_step": step,
        "restored_at": datetime.now().isoformat(),
        "archive": str(archive_dir.relative_to(run_dir)),
    }
    _atomic_write_json(meta_path, meta)

    return {
        "experiment_id": experiment_id,
        "project": run_dir.parent.name,
        "step": step,
        "run_dir": run_dir,
        "archive_dir": archive_dir,
        "runtime_state": runtime_state,
    }


def _archive_resume_tail(run_dir: Path, step: int) -> Path:
    """Archive mutable logs before replacing them with checkpoint prefixes."""
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    archive = run_dir / "resume_archive" / f"step_{step}_{stamp}"
    archive.mkdir(parents=True)
    for filename in (
        "events.jsonl",
        "simulation_log.txt",
        "simulation_summary.txt",
        "model_calls.jsonl",
        "run_metadata.json",
        "error.log",
        "done.flag",
    ):
        source = run_dir / filename
        if source.is_file():
            shutil.copy2(source, archive / filename)
    return archive


def _replace_path(source: Path, target: Path) -> None:
    """Publish one staged file atomically on the same filesystem."""
    os.replace(source, target)


def _replace_directory(source: Path, target: Path) -> None:
    """Swap a staged directory while retaining rollback on failure."""
    backup = target.with_name(f".{target.name}.resume-backup")
    if backup.exists():
        shutil.rmtree(backup)
    if target.exists():
        os.replace(target, backup)
    try:
        os.replace(source, target)
    except Exception:
        if backup.exists() and not target.exists():
            os.replace(backup, target)
        raise
    if backup.exists():
        shutil.rmtree(backup)


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    os.replace(temporary, path)
