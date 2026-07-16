# socialsimullm/frontend/app.py

# -*- coding: utf-8 -*-

"""Streamlit entry point for the research archive and experiment workspace."""

import streamlit as st

st.set_page_config(
    page_title="SocialSimuLLM · 研究档案",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --archive-ink: #091523;
        --archive-panel: #102338;
        --archive-line: rgba(199, 214, 224, .18);
        --archive-paper: #dce5e9;
        --archive-muted: #91a5b2;
        --archive-amber: #e5a85c;
        --archive-mint: #6fb3a8;
    }
    .stApp {
        background:
            radial-gradient(circle at 82% 8%, rgba(111,179,168,.10), transparent 28rem),
            linear-gradient(115deg, rgba(229,168,92,.04) 1px, transparent 1px),
            var(--archive-ink);
        background-size: auto, 34px 34px, auto;
        color: var(--archive-paper);
    }
    header[data-testid="stHeader"] { background: rgba(7, 17, 29, .96); }
    [data-testid="stSidebarNav"] { display: none; }
    [data-testid="stSidebar"] { background: #07111d; border-right: 1px solid var(--archive-line); }
    [data-testid="stSidebar"]::before {
        content: "RESEARCH FILE  /  3.1"; display: block; color: var(--archive-amber);
        font: 600 .72rem Georgia, serif; letter-spacing: .18em; padding: 1.2rem 1.4rem .25rem;
    }
    h1, h2, h3, h4 { font-family: Georgia, "Songti SC", serif !important; letter-spacing: -.015em; }
    h1 { max-width: 980px; line-height: 1.08 !important; }
    .archive-kicker { color: var(--archive-amber); font: 700 .72rem Georgia, serif; letter-spacing: .18em; margin-bottom: .7rem; }
    .archive-lede { max-width: 960px; color: #b9c9d1; font: 1.25rem/1.75 Georgia, "Songti SC", serif; border-left: 3px solid var(--archive-amber); padding-left: 1.2rem; }
    .stage-index { color: var(--archive-amber); font: 2rem/1 Georgia, serif; border-top: 1px solid var(--archive-amber); padding-top: .5rem; }
    .version-stamp { display: inline-block; color: var(--archive-ink); background: var(--archive-amber); padding: .45rem .7rem; font: 700 1.2rem Georgia, serif; }
    .loop-strip { overflow-x: auto; white-space: nowrap; margin: 1.4rem 0 2rem; padding: 1rem 1.2rem; border: 1px solid var(--archive-line); color: var(--archive-mint); background: rgba(16,35,56,.68); font-family: Georgia, "Songti SC", serif; }
    .location-card { min-height: 190px; margin: .4rem 0 1rem; padding: 1.2rem 1.3rem; border: 1px solid var(--archive-line); border-top: 3px solid var(--archive-mint); background: linear-gradient(145deg, rgba(16,35,56,.95), rgba(10,25,41,.95)); }
    .location-card h4 { margin: -.6rem 0 .6rem; padding-right: 3rem; }
    .location-card p { color: var(--archive-muted); font-size: .9rem; min-height: 3.8rem; }
    .location-card small { color: var(--archive-amber); }
    .location-count { float: right; color: var(--archive-mint); font: 2rem/1 Georgia, serif; }
    .design-card { min-height: 180px; padding: 1.1rem 1.2rem; border: 1px solid var(--archive-line); border-top: 3px solid var(--archive-amber); background: rgba(16,35,56,.78); }
    .design-card small { color: var(--archive-mint); font: 700 .68rem Georgia, serif; letter-spacing: .12em; }
    .design-card p { color: var(--archive-muted); }
    .branch-track { padding: .9rem 1rem; border-left: 3px solid var(--archive-mint); background: rgba(16,35,56,.72); margin-bottom: .65rem; }
    [data-testid="stMetric"] { background: rgba(16,35,56,.72); border: 1px solid var(--archive-line); border-radius: 0; padding: 1rem; }
    [data-testid="stMetricValue"] { color: var(--archive-amber); font-family: Georgia, serif; }
    div[data-testid="stExpander"], div[data-testid="stAlert"] { border-radius: 0; border-color: var(--archive-line); }
    .stTabs [data-baseweb="tab-list"] { gap: 0; border-bottom: 1px solid var(--archive-line); }
    .stTabs [data-baseweb="tab"] { border-radius: 0; padding-left: 1.2rem; padding-right: 1.2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

from socialsimullm.showcase.loader import ShowcaseLoadError, load_showcase_demo

with st.sidebar:
    st.markdown("## SocialSimuLLM")
    mode = st.radio("视图", ["研究档案", "Agent / Harness", "实验工作台"], horizontal=True)

if mode == "研究档案":
    pages = [
        "项目总览",
        "技术路线",
        "Agent 设计",
        "系统验证",
        "实验设计",
        "运行与介入",
        "结果分析",
        "工程演进",
    ]
    with st.sidebar:
        page = st.radio("档案目录", pages)
        st.caption("只读研究记录 · 不调用模型 API")

    try:
        demo = load_showcase_demo()
    except ShowcaseLoadError as exc:
        st.error(f"研究档案加载失败：{exc}")
        st.stop()

    if page == "项目总览":
        from socialsimullm.frontend.pages.overview import render_overview
        render_overview(demo)
    elif page == "技术路线":
        from socialsimullm.frontend.pages.architecture import render_architecture
        render_architecture()
    elif page == "Agent 设计":
        from socialsimullm.frontend.pages.agent_design import render_agent_design
        render_agent_design()
    elif page == "系统验证":
        from socialsimullm.frontend.pages.system_validation import render_system_validation
        render_system_validation(demo)
    elif page == "实验设计":
        from socialsimullm.frontend.pages.experiment_design import render_experiment_design
        render_experiment_design(demo)
    elif page == "运行与介入":
        from socialsimullm.frontend.pages.demo import render_demo
        render_demo(demo)
    elif page == "结果分析":
        from socialsimullm.frontend.pages.results import render_showcase_results
        render_showcase_results(demo)
    else:
        from socialsimullm.frontend.pages.evolution import render_evolution
        render_evolution()
elif mode == "Agent / Harness":
    with st.sidebar:
        page = st.radio(
            "Agent / Harness",
            ["Agent 总览", "Harness 设计", "协作协议", "Prompt 实验", "结果证据"],
        )
        st.caption("技术讲解版 · 只读展示 · 不调用模型 API")

    try:
        demo = load_showcase_demo()
    except ShowcaseLoadError as exc:
        st.error(f"研究档案加载失败：{exc}")
        st.stop()

    if page == "Agent 总览":
        from socialsimullm.frontend.pages.agent_harness import render_agent_overview
        render_agent_overview()
    elif page == "Harness 设计":
        from socialsimullm.frontend.pages.agent_harness import render_harness_design
        render_harness_design()
    elif page == "协作协议":
        from socialsimullm.frontend.pages.agent_harness import render_collaboration_protocol
        render_collaboration_protocol()
    elif page == "Prompt 实验":
        from socialsimullm.frontend.pages.agent_harness import render_prompt_experiment
        render_prompt_experiment(demo)
    else:
        from socialsimullm.frontend.pages.agent_harness import render_evidence
        render_evidence(demo)
else:
    with st.sidebar:
        tool = st.radio("实验工作台", ["实验配置", "运行结果", "研究助手"])
    if tool == "实验配置":
        from socialsimullm.frontend.pages.configure import render_configure
        render_configure()
    elif tool == "运行结果":
        from socialsimullm.frontend.pages.results import render_results
        render_results()
    else:
        from socialsimullm.frontend.pages.assistant import render_assistant
        render_assistant()
