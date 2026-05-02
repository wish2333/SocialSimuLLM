# socialsimullm/frontend/app.py

# -*- coding: utf-8 -*-

"""
Streamlit main entry point for SocialSimuLLM.

Provides a two-tab interface: Configure Experiment and View Results.
Launch with: uv run streamlit run src/socialsimullm/frontend/app.py

@author: Huang Miaosen
"""

import streamlit as st

st.set_page_config(
    page_title="SocialSimuLLM",
    page_icon="",
    layout="wide",
)

st.title("SocialSimuLLM Experiment Manager")

tab_configure, tab_results, tab_assistant = st.tabs(
    ["Configure Experiment", "View Results", "Research Assistant"]
)

with tab_configure:
    from socialsimullm.frontend.pages.configure import render_configure
    render_configure()

with tab_results:
    from socialsimullm.frontend.pages.results import render_results
    render_results()

with tab_assistant:
    from socialsimullm.frontend.pages.assistant import render_assistant
    render_assistant()
