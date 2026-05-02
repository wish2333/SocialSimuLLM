# socialsimullm/frontend/pages/results.py

# -*- coding: utf-8 -*-

"""
Results visualization page for SocialSimuLLM.

Displays experiment list, checkpoint data, spatial graph,
and agent behavior charts from completed experiment runs.

@author: Huang Miaosen
"""

from __future__ import annotations

import streamlit as st

from socialsimullm.experiment.storage import (
    find_run_dir,
    get_latest_checkpoint_step,
    list_experiments,
    load_checkpoint,
)


def render_results() -> None:
    """Render the results visualization page."""
    st.header("View Results")

    experiments = list_experiments()

    if not experiments:
        st.info(
            "No experiments found in the runs/ directory. "
            "Go to Configure Experiment to create and run one."
        )
        return

    # Experiment selector
    options = [
        f"{e['experiment_id']} ({e['project']})"
        for e in experiments
    ]
    selected = st.selectbox("Select Experiment", options=options)

    if not selected:
        return

    eid = selected.split(" ")[0]
    proj = selected.split("(")[-1].rstrip(")")

    # Find experiment info
    exp_info = next(
        (e for e in experiments if e["experiment_id"] == eid), None
    )
    if not exp_info:
        st.error(f"Experiment {eid} not found.")
        return

    # Status and metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Status", exp_info["status"])
    with col2:
        st.metric("Events", exp_info.get("event_count", 0))
    with col3:
        st.metric("Latest Checkpoint", exp_info.get("latest_checkpoint_step", 0))

    # Load checkpoint
    try:
        run_dir = find_run_dir(eid, proj)
        latest_step = get_latest_checkpoint_step(run_dir)

        if latest_step is None:
            st.warning("No checkpoints available yet.")
            return

        step_selection = st.slider(
            "Checkpoint Step",
            min_value=latest_step,
            max_value=latest_step,
            value=latest_step,
            step=1,
        )

        checkpoint = load_checkpoint(eid, step=step_selection, project=proj)

    except FileNotFoundError:
        st.error(f"Could not load checkpoint for experiment {eid}.")
        return

    # Visualization tabs
    tab_graph, tab_agents, tab_events, tab_replay, tab_heatmaps = st.tabs(
        ["Spatial Graph", "Agent States", "Event Summary", "Replay", "Heatmaps"]
    )

    with tab_graph:
        _render_spatial_graph(checkpoint)

    with tab_agents:
        _render_agent_states(checkpoint)

    with tab_events:
        _render_event_summary(eid, proj)

    with tab_replay:
        _render_replay(eid, proj)

    with tab_heatmaps:
        _render_heatmaps(eid, proj)


def _render_spatial_graph(checkpoint: dict) -> None:
    """Render the spatial graph visualization."""
    graph_data = checkpoint.get("spatial_graph")
    agent_states = checkpoint.get("agent_states")

    if not graph_data:
        st.info("No spatial graph data in this checkpoint.")
        return

    try:
        from socialsimullm.frontend.components.viz import render_spatial_graph
        render_spatial_graph(graph_data, agent_states)
    except ImportError as e:
        st.warning(f"Visualization dependencies not installed: {e}")
        st.code(str(graph_data)[:500])


def _render_agent_states(checkpoint: dict) -> None:
    """Render agent state information."""
    agent_states = checkpoint.get("agent_states")

    if not agent_states:
        st.info("No agent state data in this checkpoint.")
        return

    try:
        from socialsimullm.frontend.components.viz import render_agent_charts
        render_agent_charts(agent_states)
    except ImportError as e:
        st.warning(f"Visualization dependencies not installed: {e}")

    # Raw data table
    with st.expander("Raw Agent States"):
        import pandas as pd
        st.dataframe(pd.DataFrame(agent_states), use_container_width=True)


def _render_event_summary(experiment_id: str, project: str) -> None:
    """Render event summary from JSONL."""
    try:
        from socialsimullm.experiment.analysis import get_experiment_summary
        summary = get_experiment_summary(experiment_id, project)
    except FileNotFoundError:
        st.info("No events data found.")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Steps", summary["total_steps"])
        st.metric("Total Events", summary["total_events"])
    with col2:
        st.write("**Agent Names:**")
        for name in summary.get("agent_names", []):
            st.write(f"  - {name}")

    st.write("**Event Type Distribution:**")
    event_counts = summary.get("event_type_counts", {})
    if event_counts:
        try:
            import pandas as pd
            st.bar_chart(pd.DataFrame(
                {"count": event_counts}
            ))
        except ImportError:
            for etype, count in event_counts.items():
                st.write(f"  {etype}: {count}")
    else:
        st.info("No events recorded yet.")


def _render_replay(experiment_id: str, project: str) -> None:
    """Render the checkpoint replay interface."""
    try:
        from socialsimullm.frontend.components.replay import render_replay
        from socialsimullm.experiment.analysis import load_results

        checkpoints = _load_all_checkpoints(experiment_id, project)
        events = load_results(experiment_id, project)
        render_replay(checkpoints, events)
    except FileNotFoundError:
        st.warning("No checkpoint or event data found for replay.")
    except ImportError as e:
        st.warning(f"Replay dependencies not available: {e}")


def _render_heatmaps(experiment_id: str, project: str) -> None:
    """Render heatmap analysis tabs."""
    try:
        from socialsimullm.frontend.components.heatmap import (
            render_agent_activity_heatmap,
            render_location_heatmap,
            render_transition_heatmap,
        )
        from socialsimullm.experiment.analysis import load_results
    except ImportError as e:
        st.warning(f"Heatmap dependencies not available: {e}")
        return

    try:
        checkpoints = _load_all_checkpoints(experiment_id, project)
        events = load_results(experiment_id, project)
    except FileNotFoundError:
        st.warning("No data found for heatmaps.")
        return

    sub_location, sub_activity, sub_transition = st.tabs(
        ["Location Occupancy", "Agent Activity", "Transitions"]
    )

    with sub_location:
        render_location_heatmap(checkpoints)

    with sub_activity:
        render_agent_activity_heatmap(events)

    with sub_transition:
        render_transition_heatmap(events)


def _load_all_checkpoints(
    experiment_id: str, project: str
) -> list[dict]:
    """Load all checkpoint dicts for an experiment."""
    import json

    run_dir = find_run_dir(experiment_id, project)
    checkpoints_dir = run_dir / "checkpoints"

    if not checkpoints_dir.exists():
        return []

    checkpoints: list[dict] = []
    for cp_dir in sorted(checkpoints_dir.iterdir()):
        if not cp_dir.is_dir():
            continue
        agent_file = cp_dir / "agent_states.json"
        graph_file = cp_dir / "spatial_graph.json"
        if agent_file.exists():
            checkpoint: dict = {}
            try:
                with open(agent_file, "r", encoding="utf-8") as f:
                    checkpoint["agent_states"] = json.load(f)
            except json.JSONDecodeError:
                continue
            if graph_file.exists():
                try:
                    with open(graph_file, "r", encoding="utf-8") as f:
                        checkpoint["spatial_graph"] = json.load(f)
                except json.JSONDecodeError:
                    pass
            checkpoint["step"] = cp_dir.name.replace("step_", "")
            checkpoints.append(checkpoint)

    return checkpoints
