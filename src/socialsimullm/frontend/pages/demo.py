"""Read-only simulation observatory for the bundled showcase demo."""

from __future__ import annotations

from collections import Counter
from html import escape

import streamlit as st

from socialsimullm.showcase.loader import ShowcaseDemo, select_default_step


def render_demo(demo: ShowcaseDemo) -> None:
    """Render timeline, spatial occupancy, agent cards, and current events."""
    manifest = demo.manifest
    st.markdown('<p class="archive-kicker">OFFLINE OBSERVATORY / READ ONLY</p>', unsafe_allow_html=True)
    st.title("仿真演示：沿真实记录观察角色状态")
    st.caption(f"{manifest.title} · 来源 {manifest.source.source_project} · 展示运行时不读取旧项目")

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
