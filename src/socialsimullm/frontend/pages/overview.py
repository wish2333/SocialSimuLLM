"""Project overview page for the interview narrative."""

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

    event_steps = {event["step"] for event in demo.events}
    columns = st.columns(4)
    facts = [
        (len(manifest.agents), "角色", "manifest.agents"),
        (len(manifest.locations), "地点", "manifest.locations"),
        (len(manifest.steps), "真实时间点", "manifest.steps"),
        (len(event_steps), "有事件轮次", "events.jsonl"),
    ]
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

    st.info(f"离线演示：{manifest.title}。{manifest.source.disclaimer}")
