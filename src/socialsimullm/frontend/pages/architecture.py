"""Technical route page for the interview narrative."""

from __future__ import annotations

import streamlit as st

from socialsimullm.showcase.content import ARCHITECTURE_STAGES


def render_architecture() -> None:
    """Render the end-to-end data route with inspectable module evidence."""
    st.markdown('<p class="archive-kicker">SYSTEM TRACE / 01—05</p>', unsafe_allow_html=True)
    st.title("技术路线：一条可回溯的数据链")
    st.caption("YAML → ExperimentRunner → SimulatorCore → Agent cognition → JSONL / checkpoint → analysis / Streamlit")

    for stage in ARCHITECTURE_STAGES:
        left, right = st.columns([0.13, 0.87])
        with left:
            st.markdown(f'<div class="stage-index">{stage["index"]}</div>', unsafe_allow_html=True)
        with right:
            st.markdown(f'#### {stage["title"]}')
            st.write(stage["summary"])
            st.caption(" · ".join(f"`{path}`" for path in stage["paths"]))
        st.divider()

    with st.expander("为什么选择单体数据链？"):
        st.write(
            "面试演示优先强调可解释与稳定：同一运行目录同时保存配置、过程事件和状态快照，"
            "分析层只读这些产物。这样无需实时服务或消息队列，也能逐步定位实验输入、执行过程与展示结果。"
        )
