# socialsimullm/experiment/analysis.py

# -*- coding: utf-8 -*-

"""
Result loading and analysis helpers for SocialSimuLLM experiments.

Loads events.jsonl from completed experiment runs into Python data
structures. Provides DataFrame export (requires pandas) and cross-run
comparison utilities.

@author: Huang Miaosen
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from socialsimullm.experiment.storage import find_run_dir


def load_results(
    experiment_id: str, project: str | None = None
) -> list[dict[str, Any]]:
    """Load events.jsonl as a list of dicts.

    Uses streaming line-by-line reading for memory efficiency.

    Args:
        experiment_id: The experiment identifier.
        project: Project name. If None, searches all projects.

    Returns:
        List of event dicts with keys: timestamp, step, agent_id,
        event_type, data.

    Raises:
        FileNotFoundError: If the experiment or events file not found.
    """
    run_dir = find_run_dir(experiment_id, project)
    events_path = run_dir / "events.jsonl"

    if not events_path.exists():
        raise FileNotFoundError(
            f"events.jsonl not found for experiment '{experiment_id}'"
        )

    events: list[dict[str, Any]] = []
    with open(events_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events


def load_results_dataframe(
    experiment_id: str, project: str | None = None
) -> Any:
    """Load events.jsonl as a pandas DataFrame.

    Args:
        experiment_id: The experiment identifier.
        project: Project name. If None, searches all projects.

    Returns:
        A pandas DataFrame with columns: timestamp, step, agent_id,
        event_type, data.

    Raises:
        ImportError: If pandas is not installed.
        FileNotFoundError: If the events file not found.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "pandas is required for DataFrame export. "
            "Install with: uv pip install pandas"
        )

    run_dir = find_run_dir(experiment_id, project)
    events_path = run_dir / "events.jsonl"

    if not events_path.exists():
        raise FileNotFoundError(
            f"events.jsonl not found for experiment '{experiment_id}'"
        )

    return pd.read_json(str(events_path), lines=True)


def get_experiment_summary(
    experiment_id: str, project: str | None = None
) -> dict[str, Any]:
    """Get summary statistics for an experiment.

    Args:
        experiment_id: The experiment identifier.
        project: Project name. If None, searches all projects.

    Returns:
        Dict with: total_steps, total_events, event_type_counts,
        agent_names, first_timestamp, last_timestamp.
    """
    events = load_results(experiment_id, project)

    if not events:
        return {
            "experiment_id": experiment_id,
            "total_steps": 0,
            "total_events": 0,
            "event_type_counts": {},
            "agent_names": [],
            "first_timestamp": "",
            "last_timestamp": "",
        }

    event_type_counts: dict[str, int] = Counter(
        e.get("event_type", "unknown") for e in events
    )
    agent_names = sorted(
        set(e.get("agent_id", "") for e in events if e.get("agent_id"))
    )
    steps = [e.get("step", 0) for e in events]
    timestamps = [
        e.get("timestamp", "")
        for e in events
        if e.get("timestamp")
    ]

    return {
        "experiment_id": experiment_id,
        "total_steps": max(steps) if steps else 0,
        "total_events": len(events),
        "event_type_counts": dict(event_type_counts),
        "agent_names": agent_names,
        "first_timestamp": timestamps[0] if timestamps else "",
        "last_timestamp": timestamps[-1] if timestamps else "",
    }


def compare_experiments(
    experiment_ids: list[str],
    project: str | None = None,
) -> Any:
    """Compare metrics across multiple experiment runs.

    Args:
        experiment_ids: List of experiment identifiers to compare.
        project: Project name. If None, searches all projects.

    Returns:
        A pandas DataFrame with one row per experiment_id, containing
        summary metrics for comparison.

    Raises:
        ImportError: If pandas is not installed.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "pandas is required for experiment comparison. "
            "Install with: uv pip install pandas"
        )

    rows: list[dict[str, Any]] = []
    for eid in experiment_ids:
        summary = get_experiment_summary(eid, project)
        rows.append(summary)

    return pd.DataFrame(rows)
