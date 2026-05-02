# socialsimullm/frontend/components/viz.py

# -*- coding: utf-8 -*-

"""
Visualization components for SocialSimuLLM.

Provides pyvis spatial graph rendering and plotly agent behavior charts
for the Streamlit frontend.

@author: Huang Miaosen
"""

from __future__ import annotations

import tempfile
import os
from typing import Any

import streamlit as st
import streamlit.components.v1 as components


def render_spatial_graph(
    graph_data: dict[str, Any],
    agent_states: list[dict[str, Any]] | None = None,
) -> None:
    """Render spatial graph using pyvis.

    Args:
        graph_data: NetworkX node_link_data dict with 'nodes' and 'links'.
        agent_states: List of agent state dicts to overlay on the graph.
    """
    try:
        from pyvis.network import Network
    except ImportError:
        st.error(
            "pyvis is required for spatial graph visualization. "
            "Install with: uv pip install pyvis"
        )
        return

    net = Network(height="500px", width="100%", directed=False)

    # Build agent location map
    agent_locations: dict[str, str] = {}
    if agent_states:
        for agent in agent_states:
            agent_locations[agent.get("name", "")] = agent.get("location", "")

    # Add nodes from graph data
    nodes = graph_data.get("nodes", [])
    node_ids = set()
    for node in nodes:
        node_id = str(node.get("id", node.get("name", "")))
        node_ids.add(node_id)

        # Check if any agent is at this location
        agents_here = [
            name for name, loc in agent_locations.items() if loc == node_id
        ]
        title = node_id
        if agents_here:
            title += f"\\nAgents: {', '.join(agents_here)}"

        node_color = "#4CAF50" if agents_here else "#90CAF9"
        net.add_node(node_id, label=node_id, title=title, color=node_color, size=30)

    # Add edges from graph data
    links = graph_data.get("links", [])
    for link in links:
        source = str(link.get("source", ""))
        target = str(link.get("target", ""))
        if source in node_ids and target in node_ids:
            net.add_edge(source, target)

    # Save and render
    tmp_path = os.path.join(tempfile.gettempdir(), "socialsimullm_graph.html")
    net.save_graph(tmp_path)
    components.html(tmp_path, height=540)


def render_agent_charts(agent_states: list[dict[str, Any]]) -> None:
    """Render agent behavior charts using plotly.

    Args:
        agent_states: List of agent state dicts from checkpoint.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        st.error(
            "plotly is required for charts. Install with: uv pip install plotly"
        )
        return

    if not agent_states:
        st.info("No agent data to display.")
        return

    # Location distribution pie chart
    names = [a.get("name", "Unknown") for a in agent_states]
    locations = [a.get("location", "Unknown") for a in agent_states]

    loc_counts: dict[str, int] = {}
    for loc in locations:
        loc_counts[loc] = loc_counts.get(loc, 0) + 1

    fig_pie = go.Figure(
        data=[go.Pie(labels=list(loc_counts.keys()), values=list(loc_counts.values()))]
    )
    fig_pie.update_layout(title_text="Agent Location Distribution")
    st.plotly_chart(fig_pie, use_container_width=True)

    # Agent summary table
    fig_table = go.Figure(
        data=[
            go.Table(
                header=dict(
                    values=["Agent", "Location", "Daily Plan", "Hourly Plan"],
                    fill_color="paleturquoise",
                    align="left",
                ),
                cells=dict(
                    values=[
                        names,
                        locations,
                        [a.get("daily_plans", "")[:80] for a in agent_states],
                        [a.get("hourly_plan", "")[:80] for a in agent_states],
                    ],
                    align="left",
                ),
            )
        ]
    )
    fig_table.update_layout(title_text="Agent State Summary")
    st.plotly_chart(fig_table, use_container_width=True)
