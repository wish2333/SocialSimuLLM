# socialsimullm/world/spatial.py

# -*- coding: utf-8 -*-

"""
Spatial graph generation and topology management.

Provides WorldVariationGenerator for creating diverse spatial graph
topologies (ring, small-world, grid, random, scale-free) for
experiment reproducibility and environment robustness testing.

@author: Huang Miaosen
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import networkx as nx


@dataclass(frozen=True)
class SpatialConfig:
    """Configuration for world graph generation.

    Attributes:
        topology: Graph topology type.
        num_locations: Number of location nodes in the graph.
        edge_weight_range: (min, max) range for random edge weights (distance).
        seed: Random seed for reproducible generation.
        extra_params: Topology-specific parameters (e.g., small_world k/p).
    """

    topology: str = "ring"
    num_locations: int = 4
    edge_weight_range: tuple[float, float] = (1.0, 1.0)
    seed: int = 42
    extra_params: dict[str, Any] = field(default_factory=dict)


class WorldVariationGenerator:
    """Generate spatial graph variants for experiments.

    Creates NetworkX graphs with various topologies from a list of
    area names. All graphs include self-loops and random edge weights
    representing travel distance between locations.

    Usage::

        gen = WorldVariationGenerator(SpatialConfig(topology="small_world"))
        graph = gen.generate_graph(["market", "school", "temple", "park"])
    """

    SUPPORTED_TOPOLOGIES = frozenset({
        "ring", "small_world", "grid", "random", "scale_free",
    })

    def __init__(self, config: SpatialConfig) -> None:
        self._config = config

    def generate_graph(self, area_names: list[str]) -> nx.Graph:
        """Generate a NetworkX graph with the configured topology.

        Args:
            area_names: Names for graph nodes (locations).

        Returns:
            A connected NetworkX Graph with named nodes, weighted edges,
            and self-loops on every node.

        Raises:
            ValueError: If topology is not supported or num_locations
                        doesn't match area_names length.
        """
        topology = self._config.topology
        if topology not in self.SUPPORTED_TOPOLOGIES:
            raise ValueError(
                f"Unsupported topology '{topology}'. "
                f"Supported: {sorted(self.SUPPORTED_TOPOLOGIES)}"
            )

        graph = self._build_topology(area_names)
        graph = self._add_edge_weights(graph)
        self._ensure_self_loops(graph)

        if graph.number_of_nodes() > 1 and not nx.is_connected(graph):
            raise RuntimeError(
                f"Generated {topology} graph is not connected. "
                f"This should not happen. Check topology parameters."
            )

        return graph

    def generate_town_data(
        self,
        base_template: dict,
        location_descriptions: dict[str, str] | None = None,
    ) -> dict:
        """Generate a complete town_data dict with a spatial variant.

        Takes a base template and generates a graph with the configured
        topology, producing a valid town_data.json structure.

        Args:
            base_template: Existing town_data dict (preserves general
                           settings and agent definitions).
            location_descriptions: Optional mapping of location names
                                  to descriptions. If None, generates
                                  placeholders.

        Returns:
            A valid town_data dict with new spatial topology.
        """
        town_areas = base_template.get("town_areas", {})
        area_names = list(town_areas.keys())
        if not area_names:
            area_names = [f"Location_{i}" for i in range(self._config.num_locations)]

        graph = self.generate_graph(area_names)

        new_town_data: dict[str, Any] = {
            "general": dict(base_template.get("general", {})),
            "town_areas": {},
            "town_people": dict(base_template.get("town_people", {})),
        }

        if location_descriptions:
            new_town_data["town_areas"] = dict(location_descriptions)
        else:
            for name in area_names:
                new_town_data["town_areas"][name] = (
                    town_areas.get(name, f"The {name} area.")
                )

        new_town_data["_graph_metadata"] = {
            "topology": self._config.topology,
            "num_nodes": graph.number_of_nodes(),
            "num_edges": graph.number_of_edges(),
            "edge_weight_range": list(self._config.edge_weight_range),
        }

        return new_town_data

    @staticmethod
    def topology_presets() -> dict[str, dict[str, Any]]:
        """Return available topology presets with default parameters.

        Returns:
            Dict mapping topology name to its default extra_params.
        """
        return {
            "ring": {},
            "small_world": {"k": 4, "p": 0.3},
            "grid": {"rows": 2, "cols": 2},
            "random": {"p": 0.4},
            "scale_free": {"m": 2},
        }

    def _build_topology(self, area_names: list[str]) -> nx.Graph:
        """Build the base graph topology without weights."""
        n = len(area_names)
        topology = self._config.topology

        if topology == "ring":
            return self._build_ring(area_names)
        if topology == "small_world":
            return self._build_small_world(area_names)
        if topology == "grid":
            return self._build_grid(area_names)
        if topology == "random":
            return self._build_random(area_names)
        if topology == "scale_free":
            return self._build_scale_free(area_names)

        raise ValueError(f"Unknown topology: {topology}")

    def _build_ring(self, area_names: list[str]) -> nx.Graph:
        """Build a ring (cycle) graph."""
        graph = nx.Graph()
        for name in area_names:
            graph.add_node(name)
        for i, name in enumerate(area_names):
            if i > 0:
                graph.add_edge(name, area_names[i - 1])
        if len(area_names) > 1:
            graph.add_edge(area_names[0], area_names[-1])
        return graph

    def _build_small_world(self, area_names: list[str]) -> nx.Graph:
        """Build a Watts-Strogatz small-world graph."""
        n = len(area_names)
        k = self._config.extra_params.get("k", 4)
        p = self._config.extra_params.get("p", 0.3)
        k = min(k, max(n - 1, 2))

        graph = nx.watts_strogatz_graph(n, k, p, seed=self._config.seed)
        mapping = {i: name for i, name in enumerate(area_names)}
        graph = nx.relabel_nodes(graph, mapping)
        return graph

    def _build_grid(self, area_names: list[str]) -> nx.Graph:
        """Build a 2D grid graph."""
        n = len(area_names)
        rows = self._config.extra_params.get("rows", 2)
        cols = self._config.extra_params.get("cols", 2)

        while rows * cols < n:
            cols += 1

        graph = nx.grid_2d_graph(rows, cols)
        mapping = {}
        for idx, (r, c) in enumerate(sorted(graph.nodes())):
            if idx < len(area_names):
                mapping[(r, c)] = area_names[idx]
            else:
                mapping[(r, c)] = f"empty_{idx}"

        graph = nx.relabel_nodes(graph, mapping)

        unused = [name for name in mapping.values() if name.startswith("empty_")]
        graph.remove_nodes_from(unused)
        return graph

    def _build_random(self, area_names: list[str]) -> nx.Graph:
        """Build an Erdos-Renyi random graph, ensuring connectivity."""
        n = len(area_names)
        p = self._config.extra_params.get("p", 0.4)

        if n <= 1:
            graph = nx.Graph()
            if area_names:
                graph.add_node(area_names[0])
            return graph

        graph = nx.erdos_renyi_graph(n, p, seed=self._config.seed)

        while not nx.is_connected(graph):
            components = list(nx.connected_components(graph))
            if len(components) >= 2:
                u = next(iter(components[0]))
                v = next(iter(components[1]))
                graph.add_edge(u, v)
            else:
                break

        mapping = {i: name for i, name in enumerate(area_names)}
        graph = nx.relabel_nodes(graph, mapping)
        return graph

    def _build_scale_free(self, area_names: list[str]) -> nx.Graph:
        """Build a Barabasi-Albert scale-free graph."""
        n = len(area_names)
        m = self._config.extra_params.get("m", 2)
        m = min(m, max(n - 1, 1))

        graph = nx.barabasi_albert_graph(n, m, seed=self._config.seed)
        mapping = {i: name for i, name in enumerate(area_names)}
        graph = nx.relabel_nodes(graph, mapping)
        return graph

    def _add_edge_weights(self, graph: nx.Graph) -> nx.Graph:
        """Add random distance weights to all non-self-loop edges."""
        import random

        rng = random.Random(self._config.seed)
        w_min, w_max = self._config.edge_weight_range

        for u, v in graph.edges():
            if u != v:
                graph.edges[u, v]["weight"] = rng.uniform(w_min, w_max)
        return graph

    def _ensure_self_loops(self, graph: nx.Graph) -> None:
        """Add self-loops to all nodes (agents can stay in place)."""
        for node in graph.nodes():
            if not graph.has_edge(node, node):
                graph.add_edge(node, node, weight=0.0)
