# socialsimullm/frontend/pages/configure.py

# -*- coding: utf-8 -*-

"""
Experiment configuration page for SocialSimuLLM.

Renders a form from ExperimentConfig fields and provides a
Save & Run button that launches the simulation as a subprocess.

@author: Huang Miaosen
"""

from __future__ import annotations

import uuid

import streamlit as st

from socialsimullm.experiment.config import ExperimentConfig
from socialsimullm.frontend.utils import launch_experiment, poll_experiment_status


def render_configure() -> None:
    """Render the experiment configuration form."""
    st.header("Configure Experiment")

    with st.form("experiment_form"):
        col1, col2 = st.columns(2)

        with col1:
            exp_id = st.text_input(
                "Experiment ID",
                value=f"exp_{uuid.uuid4().hex[:8]}",
                help="Unique identifier for this experiment run",
            )
            project = st.text_input(
                "Project Name",
                value=exp_id,
                help="Project grouping under runs/",
            )
            model = st.text_input(
                "Completion Model",
                value="gpt-4o-mini",
                help="LLM model for text generation",
            )
            embedding_model = st.text_input(
                "Embedding Model",
                value="BAAI/bge-m3",
                help="Model for memory embedding retrieval",
            )
            steps = st.number_input(
                "Simulation Steps",
                value=144,
                min_value=1,
                max_value=10000,
                help="Number of 10-minute steps (144 = 1 day)",
            )
            memory_limit = st.number_input(
                "Memory Limit",
                value=10,
                min_value=1,
                max_value=100,
                help="Number of recent experiences to consider",
            )

        with col2:
            seed = st.number_input(
                "Random Seed",
                value=42,
                min_value=0,
                help="Random seed for reproducibility (0 = no seed)",
            )
            checkpoint_interval = st.number_input(
                "Checkpoint Interval",
                value=10,
                min_value=0,
                max_value=1000,
                help="Steps between checkpoint saves (0 = disabled)",
            )
            spatial_graph_path = st.text_input(
                "Spatial Graph Path",
                value="",
                help="Path to town_data.json (leave empty for default template)",
            )
            events_text = st.text_area(
                "Initial Events (one per line)",
                value="",
                height=100,
                help="Global events to inject at simulation start",
            )
            reflection_enabled = st.checkbox(
                "Enable Reflection System",
                value=True,
                help="Enable agent self-reflection",
            )

        submitted = st.form_submit_button("Save Config & Run", type="primary")

    if submitted:
        events = [e.strip() for e in events_text.split("\n") if e.strip()]

        config = ExperimentConfig(
            experiment_id=exp_id,
            project=project,
            model=model,
            embedding_model=embedding_model,
            simulation_steps=int(steps),
            memory_limit=int(memory_limit),
            random_seed=int(seed),
            checkpoint_interval=int(checkpoint_interval),
            spatial_graph_path=spatial_graph_path,
            events=events,
            reflection_enabled=reflection_enabled,
        )

        eid = launch_experiment(config)
        st.success(f"Experiment **{eid}** launched! Check the Results tab for status.")

        # Auto-poll status
        status_placeholder = st.empty()
        if st.toggle("Auto-poll status", value=True, key="auto_poll_configure"):
            import time
            for _ in range(60):
                time.sleep(5)
                status = poll_experiment_status(eid, project)
                if status == "completed":
                    status_placeholder.success(
                        f"Experiment **{eid}** completed! "
                        f"Go to View Results to see the output."
                    )
                    st.rerun()
                    return
                status_placeholder.info(f"Experiment {eid} is running... ({_ * 5}s elapsed)")
            status_placeholder.warning(
                f"Still running after 5 minutes. Check the Results tab or "
                f"the runs/{project}/{eid}/ directory."
            )
