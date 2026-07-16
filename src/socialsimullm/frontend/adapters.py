# -*- coding: utf-8 -*-

"""Data-shape adapters shared by frontend pages and components."""

from __future__ import annotations

from typing import Any


def normalize_agent_states(value: Any) -> list[dict[str, Any]]:
    """Return checkpoint agent states in the current list-based shape.

    Current checkpoints store a list of state dictionaries. Older checkpoints
    used a mapping keyed by agent name. The frontend accepts both formats so
    archived runs remain viewable.
    """
    if isinstance(value, list):
        return [dict(state) for state in value if isinstance(state, dict)]

    if not isinstance(value, dict):
        return []

    states: list[dict[str, Any]] = []
    for name, state in value.items():
        if isinstance(state, dict):
            normalized = dict(state)
            normalized.setdefault("name", str(name))
        else:
            normalized = {"name": str(name), "location": str(state)}
        states.append(normalized)
    return states
