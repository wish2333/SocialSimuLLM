# socialsimullm/frontend/pages/assistant.py

# -*- coding: utf-8 -*-

"""
Research assistant page for SocialSimuLLM.

Provides an AI-powered analysis interface for experiment data,
including summarization, pattern identification, and report generation.

@author: Huang Miaosen
"""

from __future__ import annotations

import streamlit as st

from socialsimullm.experiment.storage import list_experiments


def render_assistant() -> None:
    """Render the research assistant page."""
    st.header("Research Assistant")

    experiments = list_experiments()

    if not experiments:
        st.info(
            "No experiments found in the runs/ directory. "
            "Run an experiment first, then come back for analysis."
        )
        return

    options = [
        e["experiment_id"]
        for e in experiments
        if e["status"] == "completed"
    ]

    if not options:
        st.info(
            "No completed experiments found. Wait for experiments to finish."
        )
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        selected_id = st.selectbox("Select Experiment", options=options)

    with col2:
        compare_mode = st.checkbox("Compare mode")

    if compare_mode:
        compare_ids = st.multiselect(
            "Select experiments to compare",
            options=options,
            default=[selected_id],
        )
        _render_compare_section(compare_ids)
    else:
        _render_single_analysis(selected_id)


def _render_single_analysis(experiment_id: str) -> None:
    """Render analysis tools for a single experiment."""
    tab_summary, tab_patterns, tab_hypotheses, tab_report = st.tabs(
        ["Summary", "Patterns", "Hypotheses", "Full Report"]
    )

    with tab_summary:
        _render_summary(experiment_id)

    with tab_patterns:
        _render_patterns(experiment_id)

    with tab_hypotheses:
        _render_hypotheses(experiment_id)

    with tab_report:
        _render_report(experiment_id)


def _render_summary(experiment_id: str) -> None:
    """Render experiment summary."""
    if st.button("Generate Summary", key=f"sum_{experiment_id}"):
        with st.spinner("Analyzing experiment..."):
            try:
                from socialsimullm.experiment.assistant import ResearchAssistant

                assistant = ResearchAssistant()
                summary = assistant.summarize_experiment(experiment_id)
                st.session_state[f"summary_{experiment_id}"] = summary

            except Exception as e:
                st.error(f"Analysis failed: {e}")

    cached = st.session_state.get(f"summary_{experiment_id}")
    if cached:
        st.markdown(cached)


def _render_patterns(experiment_id: str) -> None:
    """Render identified patterns."""
    if st.button("Identify Patterns", key=f"pat_{experiment_id}"):
        with st.spinner("Analyzing patterns..."):
            try:
                from socialsimullm.experiment.assistant import ResearchAssistant

                assistant = ResearchAssistant()
                patterns = assistant.identify_patterns(experiment_id)
                st.session_state[f"patterns_{experiment_id}"] = patterns

            except Exception as e:
                st.error(f"Analysis failed: {e}")

    cached = st.session_state.get(f"patterns_{experiment_id}")
    if cached:
        for p in cached:
            st.markdown(f"- {p}")


def _render_hypotheses(experiment_id: str) -> None:
    """Render suggested hypotheses."""
    if st.button("Suggest Hypotheses", key=f"hyp_{experiment_id}"):
        with st.spinner("Generating hypotheses..."):
            try:
                from socialsimullm.experiment.assistant import ResearchAssistant

                assistant = ResearchAssistant()
                hypotheses = assistant.suggest_hypotheses(experiment_id)
                st.session_state[f"hypotheses_{experiment_id}"] = hypotheses

            except Exception as e:
                st.error(f"Analysis failed: {e}")

    cached = st.session_state.get(f"hypotheses_{experiment_id}")
    if cached:
        for h in cached:
            st.markdown(f"- {h}")


def _render_report(experiment_id: str) -> None:
    """Render full research report."""
    if st.button("Generate Report", key=f"rep_{experiment_id}"):
        with st.spinner("Generating report..."):
            try:
                from socialsimullm.experiment.assistant import ResearchAssistant

                assistant = ResearchAssistant()
                report = assistant.generate_report(experiment_id)
                st.session_state[f"report_{experiment_id}"] = report

            except Exception as e:
                st.error(f"Report generation failed: {e}")

    cached = st.session_state.get(f"report_{experiment_id}")
    if cached:
        st.markdown(cached)


def _render_compare_section(experiment_ids: list[str]) -> None:
    """Render comparison analysis for multiple experiments."""
    if len(experiment_ids) < 2:
        st.info("Select at least 2 experiments for comparison.")
        return

    if st.button("Compare Experiments"):
        with st.spinner("Comparing experiments..."):
            try:
                from socialsimullm.experiment.assistant import ResearchAssistant

                assistant = ResearchAssistant()
                comparison = assistant.compare_runs(experiment_ids)
                st.markdown(comparison)
            except Exception as e:
                st.error(f"Comparison failed: {e}")
