"""Read-only simulation observatory for the bundled showcase demo."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from html import escape
from typing import Any

import streamlit as st

from socialsimullm.showcase.loader import ShowcaseDemo, select_default_step


def render_demo(demo: ShowcaseDemo) -> None:
    """Render the paper run archive and the independent micro replay."""
    manifest = demo.manifest
    st.markdown('<p class="archive-kicker">RUN ARCHIVE / INTERVENTION LEDGER</p>', unsafe_allow_html=True)
    st.title("运行与介入：从统一基线到动态分支")
    st.caption("论文档案说明研究如何运行与介入；十轮工程快照独立提供逐 step 微观回放。")

    paper_tab, replay_tab = st.tabs(["论文运行档案", "十轮微观回放"])
    with paper_tab:
        case = getattr(demo, "research_case", None)
        if case is None:
            st.info("当前展示包未附论文研究档案，但不影响微观回放。")
        else:
            _render_research_archive(case)

    with replay_tab:
        st.markdown("### 工程快照·逐步状态")
        st.caption(f"{manifest.title} · 来源 {manifest.source.source_project} · 运行时不读取旧项目")
        _render_micro_replay(demo)


def _render_micro_replay(demo: ShowcaseDemo) -> None:
    """Render the original t7 step-level replay without mixing paper counts."""
    manifest = demo.manifest

    available_steps = [item.step for item in manifest.steps]
    default_step = select_default_step(demo)
    selected_step = st.select_slider(
        "观测时间轴",
        options=available_steps,
        value=default_step,
        format_func=lambda step: _step_label(demo, step),
    )
    checkpoint = demo.checkpoint(selected_step)
    events = demo.events_at(selected_step)
    states = checkpoint["agent_states"]

    a, b, c, d = st.columns(4)
    a.metric("STEP", selected_step)
    b.metric("当前角色", len(states))
    c.metric("当轮事件", len(events))
    d.metric("占用地点", len({state.get("location") for state in states if state.get("location")}))

    tab_scene, tab_agents, tab_events, tab_provenance = st.tabs(
        ["空间观测", "Agent 档案", "事件切片", "数据来源"]
    )
    with tab_scene:
        _render_scene(manifest.locations, states)
    with tab_agents:
        _render_agents(states)
    with tab_events:
        _render_events(events)
    with tab_provenance:
        st.write(manifest.source.disclaimer)
        st.code(
            f"source_project: {manifest.source.source_project}\n"
            f"conversion_rule_version: {manifest.source.conversion_rule_version}\n"
            f"checkpoint: checkpoints/step_{selected_step}\n"
            f"event_log: {manifest.event_log}"
        )
        with st.expander("迁移边界"):
            for warning in manifest.migration_warnings:
                st.write(f"— {warning}")


def _render_research_archive(case: Any) -> None:
    """Render declared scale, interventions, and two archived action groups."""
    scale = _as_mapping(_field(case, "scale"))
    columns = st.columns(4)
    facts = [
        (scale.get("agents_per_branch", "—"), "每分支 Agent"),
        (scale.get("locations", "—"), "研究空间"),
        (scale.get("branch_count", "—"), "动态分支"),
        (scale.get("rounds_per_branch", "—"), "单分支轮次"),
    ]
    for column, (value, label) in zip(columns, facts):
        column.metric(label, value)
    st.caption(
        f'论文宣称规模 · {scale.get("starts_at", "Day 1")} → '
        f'{scale.get("ends_at", "Day 6")} · '
        f'{scale.get("time_step_minutes", "—")} 分钟 / 轮；非统计样本量。'
    )

    st.markdown("### 研究者介入时间轴")
    st.caption("研究者可控制事件时间、对象、暴露强度与政策方向；不直接代替 Agent 作出行动。")
    st.markdown(
        '<div class="branch-track"><b>'
        f'{escape(str(scale.get("starts_at", "Day 1")))} · 共享基线</b><br>'
        '<span>无干预运行，记录统一初始状态，作为后续分支的共同起点。</span></div>',
        unsafe_allow_html=True,
    )
    for item in intervention_timeline(case):
        recipients = "、".join(item["recipients"]) if item["recipients"] else "无定向对象"
        st.markdown(
            '<div class="branch-track">'
            f'<b>{escape(item["time"])} · {escape(item["label"])}</b><br>'
            f'<span>{escape(recipients)} · {escape(item["intensity"])} · '
            f'{escape(item["direction"])} · 影响分支 {escape("、".join(item["branches"]))}</span>'
            "</div>",
            unsafe_allow_html=True,
        )
        if item["content"]:
            st.caption("介入内容 · " + item["content"])
    st.markdown(
        '<div class="branch-track"><b>'
        f'{escape(str(scale.get("ends_at", "Day 6")))} · 归档结束</b><br>'
        '<span>各分支独立保留运行记录，进入描述性对照和过程机制分析。</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown("### GE / NA 原始归档的主行动编码")
    st.caption("数字为完整 simulation_log 主行动的规则二次编码；event.json 仅存注入事件。每组分母独立，不是采纳率或因果效应。")
    archives = list(_field(case, "archives", default=()) or ())
    if not archives:
        st.info("研究档案没有附带可展示的归档编码。")
    else:
        tabs = st.tabs([str(_field(item, "display_name", default="归档组")) for item in archives])
        for tab, archive in zip(tabs, archives):
            with tab:
                _render_archive_group(archive)

    notes = _field(case, "coding_notes")
    if notes is not None:
        with st.expander("编码口径与排除项"):
            st.write(_field(notes, "unit", default="主行动记录"))
            for item in _field(notes, "exclusions", default=()) or ():
                st.write(f"— 排除：{item}")
            for item in _field(notes, "cautions", default=()) or ():
                st.write(f"— 边界：{item}")


def _render_archive_group(archive: Any) -> None:
    total = int(_field(archive, "total_actions", default=0) or 0)
    st.metric("完整主行动", f"{total:,}")
    st.caption(str(_field(archive, "coverage", default="归档覆盖范围未记录")))
    for metric in _field(archive, "metrics", default=()) or ():
        numerator = int(_field(metric, "numerator", default=0) or 0)
        denominator = int(_field(metric, "denominator", default=1) or 1)
        rate = numerator / denominator * 100
        st.markdown(f'**{_field(metric, "label", default="编码指标")}**')
        st.progress(min(max(numerator / denominator, 0.0), 1.0))
        st.caption(f"{numerator:,} / {denominator:,} 条主行动 · 描述性占比 {rate:.1f}%")
        st.write(_field(metric, "interpretation", default=""))
        temporal = _field(metric, "temporal", default=()) or ()
        if temporal:
            st.caption(
                "阶段变化 · "
                + " → ".join(
                    f'{_field(item, "label", "阶段")} {_field(item, "count", 0)}'
                    for item in temporal
                )
            )
        by_agent = sorted(
            _field(metric, "by_agent", default=()) or (),
            key=lambda item: int(_field(item, "count", default=0) or 0),
            reverse=True,
        )
        if by_agent:
            leaders = "、".join(
                f'{_field(item, "agent", "Agent")} {_field(item, "count", 0)}'
                for item in by_agent[:3]
            )
            st.caption(f"角色异质性 · 命中次数前三：{leaders}（非个体采纳率）")


def intervention_timeline(case: Any) -> list[dict[str, Any]]:
    """Build a de-duplicated intervention ledger from all formal branches."""
    grouped: dict[tuple[Any, ...], dict[str, Any]] = {}
    for branch in _field(case, "branches", default=()) or ():
        branch_id = str(_field(branch, "id", default="—"))
        for intervention in _field(branch, "interventions", default=()) or ():
            recipients = tuple(_field(intervention, "recipients", default=()) or ())
            key = (
                _field(intervention, "global_time", default="归档时间"),
                _field(intervention, "intervention_type", default="event"),
                recipients,
                _field(intervention, "intensity", default="未记录"),
                _field(intervention, "direction", default="neutral"),
                _field(intervention, "content", default=""),
            )
            item = grouped.setdefault(
                key,
                {
                    "time": str(key[0]),
                    "label": _intervention_label(str(key[1])),
                    "recipients": recipients,
                    "intensity": str(key[3]),
                    "direction": str(key[4]),
                    "content": str(key[5]),
                    "branches": [],
                },
            )
            item["branches"].append(branch_id)
    return list(grouped.values())


def _intervention_label(value: str) -> str:
    return {
        "technology_exposure": "技术暴露",
        "policy_encouragement": "激励性政策",
        "policy_restriction": "约束性政策",
    }.get(value, value)


def _field(value: Any, name: str, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="json")
    return {}


def _step_label(demo: ShowcaseDemo, step: int) -> str:
    item = next(value for value in demo.manifest.steps if value.step == step)
    return f"{item.global_time}  /  Step {step}"


def _render_scene(locations, states: list[dict]) -> None:
    occupancy = Counter(state.get("location", "") for state in states)
    columns = st.columns(2, gap="medium")
    for index, location in enumerate(locations):
        agents = [state["name"] for state in states if state.get("location") == location.name]
        agent_text = " · ".join(escape(name) for name in agents) or "暂无角色"
        with columns[index % 2]:
            st.markdown(
                '<div class="location-card">'
                f'<span class="location-count">{occupancy[location.name]:02d}</span>'
                f'<h4>{escape(location.name)}</h4>'
                f'<p>{escape(location.description)}</p>'
                f'<small>{agent_text}</small>'
                '</div>',
                unsafe_allow_html=True,
            )


def _render_agents(states: list[dict]) -> None:
    for state in states:
        with st.expander(f'{state.get("name", "Unknown")}　·　{state.get("location", "Unknown")}', expanded=True):
            action, plan = st.columns(2)
            action.markdown("**当前行动**")
            action.write(state.get("action") or "源数据未记录")
            plan.markdown("**短时计划**")
            plan.write(state.get("hourly_plan") or "源数据未记录")
            st.markdown("**当轮印象**")
            st.write(state.get("impression") or "源数据未记录")
            if state.get("reflection"):
                st.markdown("**反思**")
                st.write(state["reflection"])


def _render_events(events: list[dict]) -> None:
    if not events:
        st.info("该时间点没有可展示的事件。")
        return
    for event in events:
        data = event.get("data", {})
        summary = data.get("summary") or data.get("content") or "无摘要"
        st.markdown(f'**{event.get("agent_id", "Unknown")}**　`{event.get("event_type", "unknown")}`')
        st.write(summary)
        st.caption(f'{data.get("location", "Unknown")} · importance {data.get("importance", "—")}')
        st.divider()
