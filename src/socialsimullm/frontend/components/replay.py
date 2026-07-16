# socialsimullm/frontend/components/replay.py

# -*- coding: utf-8 -*-

"""
Timeline replay component for SocialSimuLLM.

Provides a slider-based replay interface that navigates checkpoints
and displays agent positions at each step.

@author: Huang Miaosen
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from socialsimullm.frontend.adapters import normalize_agent_states


def render_replay(
    checkpoints: list[dict[str, Any]],
    events: list[dict[str, Any]] | None = None,
) -> None:
    """Render a checkpoint replay with step navigation.

    Args:
        checkpoints: List of checkpoint dicts from load_checkpoints().
        events: Optional full event list for context.
    """
    if not checkpoints:
        st.info("No checkpoints available for replay.")
        return

    steps = [int(cp.get("step", 0)) for cp in checkpoints]

    col_slider, col_info = st.columns([3, 1])

    with col_slider:
        selected_idx = st.slider(
            "Replay Step",
            min_value=0,
            max_value=len(checkpoints) - 1,
            value=len(checkpoints) - 1,
            step=1,
        )

    with col_info:
        st.metric("Step", steps[selected_idx])
        st.metric("Total Checkpoints", len(checkpoints))

    checkpoint = checkpoints[selected_idx]

    st.subheader(f"Checkpoint: Step {steps[selected_idx]}")

    _render_agent_positions(checkpoint)
    _render_spatial_graph_snapshot(checkpoint)

    if events:
        step_num = steps[selected_idx]
        _render_step_events(events, step_num)


def _render_agent_positions(checkpoint: dict[str, Any]) -> None:
    """Render agent position cards for the current checkpoint."""
    agent_states = normalize_agent_states(checkpoint.get("agent_states"))
    if not agent_states:
        st.info("No agent states in this checkpoint.")
        return

    cols = st.columns(min(len(agent_states), 4))

    for i, state in enumerate(agent_states):
        col = cols[i % len(cols)]
        with col:
            name = state.get("name", "Unknown")
            location = state.get("location", "Unknown")
            daily = state.get("daily_plans", "")
            hourly = state.get("hourly_plan", "")

            st.markdown(f"**{name}**")
            st.caption(f"Location: {location}")
            if hourly:
                st.caption(f"Plan: {hourly[:60]}")
            if daily:
                with st.expander("Daily Plan"):
                    st.text(daily[:200])


def _render_spatial_graph_snapshot(checkpoint: dict[str, Any]) -> None:
    """Render spatial graph for the current checkpoint."""
    graph_data = checkpoint.get("spatial_graph")
    agent_states = normalize_agent_states(checkpoint.get("agent_states"))

    if not graph_data:
        return

    try:
        from socialsimullm.frontend.components.viz import render_spatial_graph

        render_spatial_graph(graph_data, agent_states or None)
    except ImportError:
        st.code(str(graph_data)[:500])


def _render_step_events(events: list[dict[str, Any]], step: int) -> None:
    """Render events that occurred around the given step."""
    from collections import Counter

    nearby = [e for e in events if abs(e.get("step", 0) - step) <= 5]

    if not nearby:
        st.caption("No events near this step.")
        return

    with st.expander(f"Events near step {step} ({len(nearby)} events)"):
        type_counts = Counter(e.get("event_type", "unknown") for e in nearby)
        for etype, count in type_counts.most_common():
            st.write(f"**{etype}**: {count}")

        for e in nearby[:20]:
            agent = e.get("agent_id", "")
            etype = e.get("event_type", "")
            data = e.get("data", {})
            if isinstance(data, dict):
                snippet = str(data.get("action", data.get("plan", "")))[:80]
            elif isinstance(data, str):
                snippet = data[:80]
            else:
                snippet = ""
            if snippet:
                st.write(f"  Step {e.get('step')}: [{agent}] {etype} - {snippet}")
