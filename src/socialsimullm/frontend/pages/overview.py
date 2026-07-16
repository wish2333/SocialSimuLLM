"""Project overview page for the research archive."""

from __future__ import annotations

import streamlit as st

from socialsimullm.showcase.content import PROJECT_OVERVIEW
from socialsimullm.showcase.loader import ShowcaseDemo


def render_overview(demo: ShowcaseDemo) -> None:
    """Render the research question, role, evidence, and supported numbers."""
    manifest = demo.manifest
    st.markdown(f'<p class="archive-kicker">{PROJECT_OVERVIEW["eyebrow"]}</p>', unsafe_allow_html=True)
    st.markdown(f'# {PROJECT_OVERVIEW["title"]}')
    st.markdown(f'<p class="archive-lede">{PROJECT_OVERVIEW["question"]}</p>', unsafe_allow_html=True)

    st.markdown("### 研究命题")
    st.write(PROJECT_OVERVIEW["positioning"])

    facts, using_research_scale = _overview_facts(demo)
    columns = st.columns(4)
    for column, (value, label, source) in zip(columns, facts):
        with column:
            st.metric(label, value)
            st.caption(f"来源 · `{source}`")

    left, right = st.columns([1.15, 0.85], gap="large")
    with left:
        st.markdown("### 本人职责")
        for index, item in enumerate(PROJECT_OVERVIEW["responsibilities"], start=1):
            st.markdown(f"**0{index}**　{item}")
    with right:
        st.markdown("### 证据索引")
        for label, path in PROJECT_OVERVIEW["evidence"]:
            st.markdown(f"**{label}**  \n`{path}`")

    if using_research_scale:
        st.info(
            "主指标来自论文研究案例；系统验证页单独使用论文中的四人小镇环境，"
            "两层证据不混用规模或结论。"
        )
        provenance = _as_mapping(_value(getattr(demo, "research_case", None), "provenance", default={}))
        pages = provenance.get("paper_pages", [])
        page_label = "、".join(str(page) for page in pages) if pages else "档案所列页码"
        st.caption(
            f'来源 · {provenance.get("paper_title", "论文研究案例")} · '
            f'第 {page_label} 页 · commit {provenance.get("repository_commit", "未记录")}'
        )
    else:
        st.info(f"当前仅加载工程运行记录：{manifest.title}。{manifest.source.disclaimer}")


def _overview_facts(demo: ShowcaseDemo) -> tuple[list[tuple[object, str, str]], bool]:
    """Prefer formal research scale and safely fall back to snapshot facts."""
    case = getattr(demo, "research_case", None)
    scale = _as_mapping(_value(case, "scale", "run_scale", default={}))
    config = _as_mapping(_value(case, "config", "formal_config", "experiment_config", default={}))
    branches = _value(case, "branches", "intervention_branches", default=[])
    branch_count = len(branches) if isinstance(branches, (list, tuple)) else None

    research_facts = [
        (
            _first(scale, config, names=("agents_per_branch", "agent_count", "agents")),
            "异质 Agent",
            "research_case.scale",
        ),
        (_first(scale, config, names=("locations", "location_count")), "研究空间", "research_case.scale"),
        (
            _first(scale, config, names=("branch_count", "scenario_count"), fallback=branch_count),
            "动态分支",
            "research_case.branches",
        ),
        (
            _first(
                scale,
                config,
                names=("rounds_per_branch", "steps_per_branch", "simulation_steps", "steps"),
            ),
            "单分支轮次",
            "research_case.scale",
        ),
    ]
    if case is not None and all(value not in (None, "") for value, _, _ in research_facts):
        return research_facts, True

    event_steps = {event["step"] for event in demo.events}
    return [
        (len(demo.manifest.agents), "角色", "manifest.agents"),
        (len(demo.manifest.locations), "地点", "manifest.locations"),
        (len(demo.manifest.steps), "真实时间点", "manifest.steps"),
        (len(event_steps), "有事件轮次", "events.jsonl"),
    ], False


def _first(*mappings: dict, names: tuple[str, ...], fallback=None):
    for mapping in mappings:
        for name in names:
            value = mapping.get(name)
            if value not in (None, ""):
                return value
    return fallback


def _value(obj, *names: str, default=None):
    data = _as_mapping(obj)
    for name in names:
        if name in data and data[name] is not None:
            return data[name]
    return default


def _as_mapping(value) -> dict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="json")
    if hasattr(value, "__dict__"):
        return vars(value)
    return {}
