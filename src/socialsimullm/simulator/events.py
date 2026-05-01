# socialsimullm/simulator/events.py

# -*- coding: utf-8 -*-

"""
Simple event bus for global simulation events.

Provides a publish-subscribe mechanism for decoupling event producers
from event consumers within the simulation.

@author: Huang Miaosen
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable


class EventBus:
    """Simple publish-subscribe event bus.

    Allows modules to register handlers for event types and emit events
    without direct coupling between producer and consumer.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[dict[str, Any]], None]]] = defaultdict(list)

    def register(self, event_type: str, handler: Callable[[dict[str, Any]], None]) -> None:
        """Register a handler function for a given event type.

        Args:
            event_type: The event category to listen for.
            handler: A callable that receives event data as a dict.
        """
        self._handlers[event_type].append(handler)

    def emit(self, event_type: str, data: dict[str, Any]) -> None:
        """Emit an event, calling all registered handlers for its type.

        Args:
            event_type: The event category to emit.
            data: Event payload dictionary passed to each handler.
        """
        for handler in self._handlers.get(event_type, []):
            handler(data)

    def clear(self) -> None:
        """Remove all registered handlers."""
        self._handlers.clear()
