# socialsimullm/frontend/components/heatmap.py

# -*- coding: utf-8 -*-

"""
Heatmap visualization component for SocialSimuLLM.

Provides location occupancy and agent activity heatmaps using plotly.

@author: Huang Miaosen
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

import streamlit as st

from socialsimullm.frontend.adapters import normalize_agent_states


def render_location_heatmap(checkpoints: list[dict[str, Any]]) -> None:
    """Render a heatmap showing agent occupancy per location over time.

    Args:
        checkpoints: List of checkpoint dicts.
    """
    if not checkpoints:
        st.info("No checkpoints for heatmap.")
        return

    steps, locations, agent_counts = _compute_occupancy_data(checkpoints)

    try:
        import plotly.graph_objects as go
    except ImportError:
        st.error("plotly is required. Install with: uv pip install plotly")
        return

    fig = go.Figure(
        data=go.Heatmap(
            z=agent_counts,
            x=locations,
            y=steps,
            colorscale="YlOrRd",
            hoverongaps=False,
        ),
        layout=go.Layout(
            title="Agent Occupancy Heatmap",
            xaxis_title="Location",
            yaxis_title="Checkpoint Step",
            height=400,
        ),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_agent_activity_heatmap(events: list[dict[str, Any]]) -> None:
    """Render a heatmap showing event types per agent.

    Args:
        events: List of event dicts.
    """
    if not events:
        st.info("No events for activity heatmap.")
        return

    agents = sorted(set(e.get("agent_id", "") for e in events if e.get("agent_id")))
    event_types = sorted(set(e.get("event_type", "") for e in events))

    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for e in events:
        agent = e.get("agent_id", "")
        etype = e.get("event_type", "")
        if agent and etype:
            counts[agent][etype] += 1

    matrix = [
        [counts[agent].get(etype, 0) for etype in event_types]
        for agent in agents
    ]

    try:
        import plotly.graph_objects as go
    except ImportError:
        st.error("plotly is required. Install with: uv pip install plotly")
        return

    fig = go.Figure(
        data=go.Heatmap(
            z=matrix,
            x=event_types,
            y=agents,
            colorscale="Blues",
            hoverongaps=False,
        ),
        layout=go.Layout(
            title="Agent Activity Heatmap",
            xaxis_title="Event Type",
            yaxis_title="Agent",
            height=max(300, len(agents) * 30),
        ),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_transition_heatmap(events: list[dict[str, Any]]) -> None:
    """Render a heatmap of location transition frequencies.

    Args:
        events: List of event dicts with movement data.
    """
    movements = [e for e in events if e.get("event_type") == "movement"]

    if not movements:
        st.info("No movement events for transition heatmap.")
        return

    transitions: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    all_locations: set[str] = set()

    for e in movements:
        data = e.get("data", {})
        if not isinstance(data, dict):
            continue
        src = data.get("from", "")
        dst = data.get("to", "")
        if src and dst:
            transitions[src][dst] += 1
            all_locations.add(src)
            all_locations.add(dst)

    locations = sorted(all_locations)
    if not locations:
        return

    matrix = [
        [transitions[src].get(dst, 0) for dst in locations]
        for src in locations
    ]

    try:
        import plotly.graph_objects as go
    except ImportError:
        st.error("plotly is required. Install with: uv pip install plotly")
        return

    fig = go.Figure(
        data=go.Heatmap(
            z=matrix,
            x=locations,
            y=locations,
            colorscale="Viridis",
            hoverongaps=False,
        ),
        layout=go.Layout(
            title="Location Transition Heatmap",
            xaxis_title="Destination",
            yaxis_title="Source",
            height=max(300, len(locations) * 50),
        ),
    )
    st.plotly_chart(fig, use_container_width=True)


def _compute_occupancy_data(
    checkpoints: list[dict[str, Any]],
) -> tuple[list[int], list[str], list[list[int]]]:
    """Compute occupancy matrix from checkpoints.

    Returns:
        Tuple of (steps, locations, agent_counts_matrix).
    """
    steps: list[int] = []
    locations_set: set[str] = set()

    for cp in checkpoints:
        steps.append(int(cp.get("step", 0)))
        states = normalize_agent_states(cp.get("agent_states"))
        for state in states:
            location = state.get("location", "")
            if location:
                locations_set.add(location)

    locations = sorted(locations_set)

    matrix: list[list[int]] = []
    for cp in checkpoints:
        states = normalize_agent_states(cp.get("agent_states"))
        loc_counts: dict[str, int] = Counter()
        for state in states:
            loc = state.get("location", "")
            if loc:
                loc_counts[loc] += 1
        row = [loc_counts.get(loc, 0) for loc in locations]
        matrix.append(row)

    return steps, locations, matrix
