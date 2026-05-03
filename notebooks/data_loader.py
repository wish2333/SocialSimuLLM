# notebooks/data_loader.py
# -*- coding: utf-8 -*-

"""
Shared data loading utilities for analysis notebooks.

Provides helper functions to load experiment data (events, checkpoints,
memory files) into pandas DataFrames for analysis.

Usage (in notebooks)::

    from data_loader import load_experiment, build_agent_timeline
    df = load_experiment("exp_abc123")

@author: Huang Miaosen
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any


def _get_runs_root() -> Path:
    """Return the runs/ directory relative to the project root."""
    # data_loader.py lives under notebooks/, so project root is one level up.
    return Path(__file__).resolve().parent.parent / "runs"


def _find_run_dir(experiment_id: str, project: str | None = None) -> Path | None:
    """Locate an experiment run directory."""
    runs_root = _get_runs_root()
    candidates: list[Path] = []

    if project:
        candidates = [runs_root / project / experiment_id]
    else:
        if not runs_root.exists():
            return None
        # Check direct child (flat layout) and nested layouts
        direct = runs_root / experiment_id
        if direct.is_dir():
            candidates.append(direct)
        candidates.extend(runs_root.rglob(f"*/{experiment_id}"))

    for c in candidates:
        if (c / "done.flag").exists() or (c / "events.jsonl").exists():
            return c
    return candidates[0] if candidates else None


def load_events_jsonl(run_dir: Path) -> list[dict[str, Any]]:
    """Load events.jsonl from a run directory."""
    events_file = run_dir / "events.jsonl"
    if not events_file.exists():
        return []
    events = []
    with open(events_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events


def load_experiment(experiment_id: str, project: str | None = None) -> list[dict[str, Any]]:
    """Load all events from an experiment as a list of dicts.

    Args:
        experiment_id: The experiment ID.
        project: Optional project name.

    Returns:
        List of event dicts with timestamp, step, agent_id, event_type, data.
    """
    run_dir = _find_run_dir(experiment_id, project)
    if run_dir is None:
        raise FileNotFoundError(f"Experiment '{experiment_id}' not found.")
    return load_events_jsonl(run_dir)


def load_checkpoints(experiment_id: str, project: str | None = None) -> list[dict[str, Any]]:
    """Load all checkpoint data from an experiment.

    Args:
        experiment_id: The experiment ID.
        project: Optional project name.

    Returns:
        List of checkpoint dicts, each containing spatial_graph, agent_states,
        memory_summary.
    """
    run_dir = _find_run_dir(experiment_id, project)
    if run_dir is None:
        raise FileNotFoundError(f"Experiment '{experiment_id}' not found.")

    checkpoints_dir = run_dir / "checkpoints"
    if not checkpoints_dir.exists():
        return []

    checkpoints = []
    for cp_dir in sorted(checkpoints_dir.iterdir()):
        if not cp_dir.is_dir():
            continue
        agent_file = cp_dir / "agent_states.json"
        graph_file = cp_dir / "spatial_graph.json"
        if agent_file.exists():
            checkpoint: dict[str, Any] = {}
            with open(agent_file, "r", encoding="utf-8") as f:
                checkpoint["agent_states"] = json.load(f)
            if graph_file.exists():
                with open(graph_file, "r", encoding="utf-8") as f:
                    checkpoint["spatial_graph"] = json.load(f)
            checkpoint["step"] = cp_dir.name.replace("step_", "")
            checkpoints.append(checkpoint)
    return checkpoints


def extract_movement_events(events: list[dict]) -> list[dict[str, Any]]:
    """Extract only movement events from the event list.

    Args:
        events: Full event list.

    Returns:
        Filtered list of movement events.
    """
    return [e for e in events if e.get("event_type") == "movement"]


def extract_action_events(events: list[dict]) -> list[dict[str, Any]]:
    """Extract only action events from the event list.

    Args:
        events: Full event list.

    Returns:
        Filtered list of action events.
    """
    return [e for e in events if e.get("event_type") == "action"]


def extract_reflection_events(events: list[dict]) -> list[dict[str, Any]]:
    """Extract only reflection events from the event list.

    Args:
        events: Full event list.

    Returns:
        Filtered list of reflection events.
    """
    return [e for e in events if e.get("event_type") == "reflection"]


def build_agent_timeline(events: list[dict], agent_name: str) -> list[dict[str, Any]]:
    """Build a step-by-step timeline for a specific agent.

    Args:
        events: Full event list.
        agent_name: Agent name to filter for.

    Returns:
        List of events for that agent, ordered by step.
    """
    return [e for e in events if e.get("agent_id") == agent_name]


def compute_location_transition_matrix(events: list[dict]) -> dict[str, dict[str, int]]:
    """Compute a location transition count matrix from movement events.

    Args:
        events: Full event list.

    Returns:
        Dict mapping from_location -> {to_location -> count}.
    """
    matrix: dict[str, dict[str, int]] = {}
    for e in extract_movement_events(events):
        data = e.get("data", {})
        if isinstance(data, str):
            parts = data.split('"')
            if len(parts) >= 3:
                from_loc = parts[1].strip().strip('"')
                to_loc = parts[3].strip().strip('"')
            else:
                continue
        elif isinstance(data, dict):
            from_loc = data.get("from", "")
            to_loc = data.get("to", "")
        else:
            continue

        if from_loc and to_loc and from_loc != to_loc:
            if from_loc not in matrix:
                matrix[from_loc] = {}
            matrix[from_loc][to_loc] = matrix[from_loc].get(to_loc, 0) + 1
    return matrix


def compute_interaction_matrix(events: list[dict]) -> dict[str, dict[str, int]]:
    """Compute an agent interaction frequency matrix from events.

    Counts co-location events and action events mentioning other agents.

    Args:
        events: Full event list.

    Returns:
        Dict mapping agent_name -> {other_agent -> interaction count}.
    """
    matrix: dict[str, dict[str, int]] = {}
    for e in extract_action_events(events):
        agent_id = e.get("agent_id", "")
        data_str = e.get("data", "")
        if not agent_id or not isinstance(data_str, str):
            continue

        mentions = re.findall(r'(?:Communicate with|interact with)\s+(\w+)', data_str)
        for mentioned in mentions:
            if agent_id not in matrix:
                matrix[agent_id] = {}
            matrix[agent_id][mentioned] = matrix[agent_id].get(mentioned, 0) + 1
    return matrix
