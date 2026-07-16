"""Engineering evolution page."""

from __future__ import annotations

import streamlit as st

from socialsimullm.showcase.content import EVOLUTION


def render_evolution() -> None:
    """Render evidence-safe V1 to V3.1 engineering decisions."""
    st.markdown('<p class="archive-kicker">ENGINEERING LOG / V1—V3.1</p>', unsafe_allow_html=True)
    st.title("工程演进：不是堆功能，而是逐步消除研究摩擦")

    for item in EVOLUTION:
        version, body = st.columns([0.18, 0.82], gap="large")
        with version:
            st.markdown(f'<div class="version-stamp">{item["version"]}</div>', unsafe_allow_html=True)
            st.caption(item["label"])
        with body:
            st.markdown(f'#### {item["label"]}')
            st.markdown(f'**当时的问题**　{item["problem"]}')
            st.markdown(f'**关键决策**　{item["decision"]}')
            st.markdown(f'**得到的结果**　{item["result"]}')
        st.divider()

    st.warning("演进档案只描述代码中可核验的能力，不给出仓库无法证明的性能百分比或成本结论。")
