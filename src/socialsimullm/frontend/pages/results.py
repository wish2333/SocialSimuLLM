# socialsimullm/frontend/pages/results.py

# -*- coding: utf-8 -*-

"""
Results visualization page for SocialSimuLLM.

Displays experiment list, checkpoint data, spatial graph,
and agent behavior charts from completed experiment runs.

@author: Huang Miaosen
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

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
    """Render the paper case as a social-science evidence workbench."""
    st.markdown('<p class="archive-kicker">SOCIAL SCIENCE EVIDENCE DESK</p>', unsafe_allow_html=True)
    st.title("结果分析：从运行记录到机制解释")
    st.caption(
        "论文案例以描述性对照、过程证据和理论解释为主；"
        "页面不提供 p 值、显著性或因果效应声称。"
    )

    case = getattr(demo, "research_case", None)
    if case is None:
        st.info("当前展示包未附论文研究案例；以下仅展示工程快照指标。")
        _render_engineering_snapshot_metrics(demo)
        return

    descriptive, heterogeneity, mechanisms, boundaries, next_tests, snapshot = st.tabs(
        ["描述性对照", "角色异质性", "三重耦合证据", "反例与边界", "下一步检验", "工程快照"]
    )
    with descriptive:
        _render_descriptive_comparison(case)
    with heterogeneity:
        _render_role_heterogeneity(case)
    with mechanisms:
        _render_mechanism_matrix(case)
    with boundaries:
        _render_boundaries(case)
    with next_tests:
        _render_next_tests(case)
    with snapshot:
        _render_engineering_snapshot_metrics(demo)


def _render_descriptive_comparison(case: Any) -> None:
    import pandas as pd

    st.markdown("### GE / NA 归档组的描述性编码")
    st.caption("分母为各归档组完整 simulation_log 主行动条数；event.json 只提供注入事件。规则命中占比不是个体采纳率。")
    rows = archive_metric_rows(case)
    if not rows:
        st.info("没有可对照的二次编码指标。")
        return
    frame = pd.DataFrame(rows)
    st.dataframe(
        frame[["归档组", "指标", "命中条数", "分母", "描述性占比", "口径"]],
        width="stretch",
        hide_index=True,
    )
    for archive in _items(case, "archives"):
        with st.expander(f'{_value(archive, "display_name", "归档组")} · 事件记录'):
            for event in _value(archive, "interventions_from_archive", ()) or ():
                st.write(f"— {event}")
            paths = _value(archive, "source_paths", ()) or ()
            if paths:
                st.caption("来源 · " + " · ".join(f"`{path}`" for path in paths))


def _render_role_heterogeneity(case: Any) -> None:
    import pandas as pd

    st.markdown("### 同一编码规则下的角色差异")
    st.caption("仅报告每个角色的指标命中次数；因缺少角色各自全部行动分母，不计算个体采纳率。")
    rows = role_count_rows(case)
    if not rows:
        st.info("没有按角色编码的归档记录。")
        return
    frame = pd.DataFrame(rows)
    metric_options = list(dict.fromkeys(frame["指标键"].tolist()))
    selected = st.selectbox("选择归档指标", metric_options, key="research_role_metric")
    selected_frame = frame[frame["指标键"] == selected].drop(columns=["指标键"])
    st.dataframe(selected_frame, width="stretch", hide_index=True)

    st.markdown("### 可追溯过程片段")
    excerpts = _items(case, "evidence_excerpts")
    if not excerpts:
        st.info("未附带紧凑证据片段。")
    for excerpt in excerpts:
        st.markdown(
            f'**{_value(excerpt, "agent", "Agent")}** · '
            f'`{_value(excerpt, "archive_id", "archive")}` · '
            f'{_value(excerpt, "global_time", "归档时间")}'
        )
        st.write(_value(excerpt, "excerpt", ""))
        st.caption(
            f'证据等级 · {_evidence_label(_value(excerpt, "evidence_level", "archive_descriptive"))} '
            f'· 来源 `{_value(excerpt, "source_path", "—")}`'
        )
        st.divider()


def _render_mechanism_matrix(case: Any) -> None:
    st.markdown("### 三重耦合：结论、机制与证据不合并")
    st.caption("“论文解释”是对过程记录的理论归纳，不等于统计因果识别。")
    findings = _items(case, "findings")
    if not findings:
        st.info("没有附带机制解释。")
        return
    for finding in findings:
        level = _value(finding, "evidence_level", "paper_interpretation")
        with st.expander(str(_value(finding, "title", "研究发现")), expanded=True):
            st.caption(
                f'证据等级 · {_evidence_label(level)} · '
                f'PDF pp.{_page_label(_value(finding, "pdf_pages", ()))}'
            )
            st.markdown("**记录支持的论文命题**")
            st.write(_value(finding, "claim", ""))
            st.markdown("**机制解释**")
            st.write(_value(finding, "mechanism", ""))
            metric_ids = _value(finding, "archive_metric_ids", ()) or ()
            if metric_ids:
                st.caption("关联二次编码 · " + " · ".join(f"`{item}`" for item in metric_ids))


def _render_boundaries(case: Any) -> None:
    st.markdown("### 反例与替代解释")
    alternatives = alternative_explanation_rows(case)
    if alternatives:
        for item in alternatives:
            st.markdown(f'**{item["finding"]}**')
            st.write(f'— {item["alternative"]}')
    else:
        st.info("档案未记录替代解释。")

    st.markdown("### 已知边界")
    for limitation in _items(case, "limitations"):
        st.markdown(f'**{_value(limitation, "description", "研究边界")}**')
        st.write(_value(limitation, "consequence", ""))
        pages = _value(limitation, "pdf_pages", ()) or ()
        if pages:
            st.caption(f'论文来源 · PDF pp.{_page_label(pages)}')

    notes = _value(case, "coding_notes")
    if notes is not None:
        for caution in _value(notes, "cautions", ()) or ():
            st.warning(str(caution))


def _render_next_tests(case: Any) -> None:
    st.markdown("### 将探索性发现推进到可检验研究")
    st.caption("这些是根据当前证据边界得出的后续研究设计，不是已完成结果。")
    tests = next_test_rows(case)
    for index, item in enumerate(tests, start=1):
        st.markdown(f'**{index:02d} · {item["title"]}**')
        st.write(item["design"])
        st.caption(f'对应边界 · {item["basis"]}')


def _render_engineering_snapshot_metrics(demo: ShowcaseDemo) -> None:
    st.markdown("### 论文小镇验证档案")
    st.caption("当前展示包不包含逐步工程快照；四人小镇的论文归纳结果请在“系统验证”页查看。")
    st.info("校园 GE / NA 正式归档的描述性指标已在本页前五个分析标签中展示。")


def archive_metric_rows(case: Any) -> list[dict[str, Any]]:
    """Return explicitly denominated secondary-coding rows for display/tests."""
    rows: list[dict[str, Any]] = []
    for archive in _items(case, "archives"):
        archive_name = str(_value(archive, "display_name", "归档组"))
        for metric in _value(archive, "metrics", ()) or ():
            numerator = int(_value(metric, "numerator", 0) or 0)
            denominator = int(_value(metric, "denominator", 1) or 1)
            rows.append(
                {
                    "归档组": archive_name,
                    "指标": str(_value(metric, "label", "编码指标")),
                    "命中条数": numerator,
                    "分母": denominator,
                    "描述性占比": f"{numerator / denominator * 100:.1f}%",
                    "口径": "主行动规则命中 / 归档组全部主行动",
                }
            )
    return rows


def role_count_rows(case: Any) -> list[dict[str, Any]]:
    """Return raw per-agent hit counts without inventing per-agent rates."""
    rows: list[dict[str, Any]] = []
    for archive in _items(case, "archives"):
        archive_name = str(_value(archive, "display_name", "归档组"))
        for metric in _value(archive, "metrics", ()) or ():
            metric_id = str(_value(metric, "id", "metric"))
            metric_label = str(_value(metric, "label", metric_id))
            for item in _value(metric, "by_agent", ()) or ():
                rows.append(
                    {
                        "指标键": f"{archive_name} · {metric_label}",
                        "归档组": archive_name,
                        "指标": metric_label,
                        "Agent": str(_value(item, "agent", "Unknown")),
                        "命中次数": int(_value(item, "count", 0) or 0),
                        "口径": "原始次数（非个体采纳率）",
                    }
                )
    return rows


def alternative_explanation_rows(case: Any) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for finding in _items(case, "findings"):
        title = str(_value(finding, "title", "研究发现"))
        for alternative in _value(finding, "alternative_explanations", ()) or ():
            rows.append({"finding": title, "alternative": str(alternative)})
    return rows


def next_test_rows(case: Any) -> list[dict[str, str]]:
    """Translate declared limitations into transparent follow-up designs."""
    templates = [
        ("重复与稳健性", "固定配置后进行多种子重复，报告分布和异常轮次，不仅展示单次轨迹。"),
        ("组织因素操作检查", "将访问权限、基础设施和师生规范转为显式约束，验证 Agent 是否真正感知并遵循。"),
        ("与现实资料对照", "将仿真中的采纳轨迹与问卷、访谈或校园行为数据对照，检查方向和机制是否外推。"),
        ("网络与时间指标", "预先定义暴露、讨论、评估和实践编码，比较网络渗透与转化所需时间。"),
    ]
    limitations = _items(case, "limitations")
    rows: list[dict[str, str]] = []
    for index, limitation in enumerate(limitations):
        title, design = templates[index % len(templates)]
        rows.append(
            {
                "title": title,
                "design": design,
                "basis": str(_value(limitation, "description", "当前证据边界")),
            }
        )
    return rows or [
        {
            "title": "预注册的重复实验",
            "design": "固定变量、编码规则和分析口径后进行多次重复。",
            "basis": "当前档案为探索性案例",
        }
    ]


def _items(value: Any, name: str) -> list[Any]:
    items = _value(value, name, ()) or ()
    return list(items) if isinstance(items, (list, tuple)) else []


def _value(value: Any, name: str, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _evidence_label(value: str) -> str:
    return {
        "archive_descriptive": "归档描述性证据",
        "paper_interpretation": "论文理论解释",
        "mechanism_evidence": "过程机制证据",
        "unverified_alternative": "待检验替代解释",
    }.get(str(value), str(value))


def _page_label(pages: Any) -> str:
    return ", ".join(str(item) for item in pages) if pages else "—"


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
    resumed_from = exp_info.get("resumed_from_step")
    if resumed_from is not None:
        st.info(f"This run was resumed from step {resumed_from}.")

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
        st.dataframe(pd.DataFrame(agent_states), width="stretch")


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
