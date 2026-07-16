"""Agent cognition design page."""

from __future__ import annotations

import streamlit as st

from socialsimullm.showcase.content import AGENT_LOOP


def render_agent_design() -> None:
    """Render the single-turn cognition loop and its code evidence."""
    st.markdown('<p class="archive-kicker">COGNITION LOOP / ONE TURN</p>', unsafe_allow_html=True)
    st.title("Agent 设计：从看到什么，到为什么行动")
    st.caption("每个节点都有明确输入输出；结构化记忆让决策过程可检索，反思则在主循环外保持节制触发。")

    labels = "　→　".join(item[0] for item in AGENT_LOOP)
    st.markdown(f'<div class="loop-strip">{labels}</div>', unsafe_allow_html=True)

    for row_start in range(0, len(AGENT_LOOP), 3):
        columns = st.columns(3, gap="medium")
        for column, (title, summary, path) in zip(columns, AGENT_LOOP[row_start:row_start + 3]):
            with column:
                st.markdown(f"#### {title}")
                st.write(summary)
                st.caption(f"证据 · `{path}`")

    st.markdown("### 单轮约束")
    first, second, third = st.columns(3)
    first.info("**环境边界**\n\nAgent 只基于当轮可感知信息和被召回的记忆决策。")
    second.info("**状态写回**\n\n计划、行动与印象进入结构化记忆，供后续轮次检索。")
    third.info("**反思冷却**\n\n反思由阈值与 cooldown 控制，避免每轮重复调用。")
