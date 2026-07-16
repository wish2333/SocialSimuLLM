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

from socialsimullm.frontend.adapters import normalize_agent_states
from socialsimullm.showcase.content import declared_metric_labels
from socialsimullm.showcase.loader import ShowcaseDemo
from socialsimullm.experiment.storage import (
    find_run_dir,
    get_latest_checkpoint_step,
    list_experiments,
    load_checkpoint,
)


_SHOWCASE_METRIC_RENDERERS = {
    "activity_distribution": "_render_showcase_activity",
    "location_occupancy": "_render_showcase_occupancy",
    "memory_distribution": "_render_showcase_memory",
}


def enabled_showcase_metrics(demo: ShowcaseDemo) -> tuple[str, ...]:
    """Return only metrics both declared by the manifest and implemented here."""
    return tuple(
        metric
        for metric, _label in declared_metric_labels(demo.manifest.available_metrics)
        if metric in _SHOWCASE_METRIC_RENDERERS
    )


def render_showcase_results(demo: ShowcaseDemo) -> None:
    """Render metric panels allowed by the offline demo manifest."""
    st.markdown('<p class="archive-kicker">EVIDENCE DESK / DECLARED METRICS</p>', unsafe_allow_html=True)
    st.title("结果分析：只展示源数据能够支持的指标")
    st.caption("指标入口由 manifest.available_metrics 控制；未声明的研究结论不会出现在界面中。")

    metrics = enabled_showcase_metrics(demo)
    if not metrics:
        st.info("当前演示 manifest 没有声明可用指标。")
        return

    labels = dict(declared_metric_labels(demo.manifest.available_metrics))
    tabs = st.tabs([labels[metric] for metric in metrics])
    renderers = {
        "activity_distribution": _render_showcase_activity,
        "location_occupancy": _render_showcase_occupancy,
        "memory_distribution": _render_showcase_memory,
    }
    for tab, metric in zip(tabs, metrics):
        with tab:
            renderers[metric](demo)

    unsupported = [
        metric for metric in demo.manifest.available_metrics
        if metric not in _SHOWCASE_METRIC_RENDERERS
    ]
    if unsupported:
        st.caption("尚无展示组件：" + "、".join(unsupported))


def _render_showcase_activity(demo: ShowcaseDemo) -> None:
    from collections import Counter

    import pandas as pd

    counts = Counter(event.get("event_type", "unknown") for event in demo.events)
    if not counts:
        st.info("没有活动事件。")
        return
    frame = pd.DataFrame(
        [{"事件类型": key, "记录数": value} for key, value in counts.most_common()]
    ).set_index("事件类型")
    st.bar_chart(frame, color="#e5a85c")
    st.caption(f"来源 · {demo.manifest.event_log} · 共 {len(demo.events)} 条结构化事件")


def _render_showcase_occupancy(demo: ShowcaseDemo) -> None:
    from socialsimullm.frontend.components.heatmap import render_location_heatmap

    render_location_heatmap(list(demo.checkpoints))
    st.caption("来源 · checkpoints/*/agent_states.json；只统计有真实 checkpoint 的时间点。")


def _render_showcase_memory(demo: ShowcaseDemo) -> None:
    from collections import Counter

    import pandas as pd

    latest = max(demo.checkpoints, key=lambda checkpoint: int(checkpoint.get("step", 0)))
    agents = latest.get("memory_summary", {}).get("agents", {})
    totals: Counter[str] = Counter()
    for summary in agents.values():
        if isinstance(summary, dict):
            totals.update(summary.get("by_type", {}))
    if not totals:
        st.info("没有记忆摘要。")
        return
    frame = pd.DataFrame(
        [{"记忆类型": key, "记录数": value} for key, value in totals.most_common()]
    ).set_index("记忆类型")
    st.bar_chart(frame, color="#6fb3a8")
    st.caption(f'来源 · checkpoints/step_{latest["step"]}/memory_summary.json')


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
    agent_states = normalize_agent_states(checkpoint.get("agent_states"))

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
    agent_states = normalize_agent_states(checkpoint.get("agent_states"))

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
