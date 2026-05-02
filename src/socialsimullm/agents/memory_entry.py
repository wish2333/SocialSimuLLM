# socialsimullm/agents/memory_entry.py

# -*- coding: utf-8 -*-

"""
Typed memory entry dataclass for social simulation agents.

Defines the canonical memory record structure with serialization
support for JSON storage. Handles both v3.1.0 (new field names)
and v3.0 (old field names) for backward-compatible deserialization.

@author: Huang Miaosen
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MemoryEntry:
    """Immutable memory record for a single agent observation.

    Attributes:
        id: Unique entry UUID.
        agent_name: Agent who owns this memory.
        timestamp: Simulation time "Day X, HH:MM".
        location_id: Where the event occurred.
        event_type: action | plan | thought | reflection | event.
        content: Full narrative description.
        summary: Simplified SVO sentence.
        entities: Other agents involved.
        importance: 1-9 rating.
        embedding: Vector embedding (optional).
        reflection_link: Linked reflection ID (optional).
        reflection_type: daily | pattern | social (optional).
        metadata: Extensible key-value pairs.
    """

    id: str
    agent_name: str
    timestamp: str
    location_id: str
    event_type: str
    content: str
    summary: str = ""
    entities: tuple[str, ...] = ()
    importance: int = 1
    embedding: tuple[float, ...] | None = None
    reflection_link: str | None = None
    reflection_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        agent_name: str,
        timestamp: str,
        location_id: str,
        event_type: str,
        content: str,
        **kwargs: Any,
    ) -> MemoryEntry:
        """Factory that auto-generates UUID.

        Args:
            agent_name: Agent identifier.
            timestamp: Simulation time string.
            location_id: Location identifier.
            event_type: Type of experience.
            content: Full narrative description.
            **kwargs: Additional fields (summary, entities, importance, etc.).

        Returns:
            A new MemoryEntry with auto-generated id.
        """
        entities = kwargs.pop("entities", [])
        if isinstance(entities, str):
            entities = [entities]
        return cls(
            id=str(uuid.uuid4()),
            agent_name=agent_name,
            timestamp=timestamp,
            location_id=location_id,
            event_type=event_type,
            content=content,
            entities=tuple(entities),
            **kwargs,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to plain dict for JSON storage.

        Returns:
            A dictionary with all serializable fields.
        """
        d: dict[str, Any] = {
            "id": self.id,
            "agent_name": self.agent_name,
            "timestamp": self.timestamp,
            "location_id": self.location_id,
            "event_type": self.event_type,
            "content": self.content,
            "summary": self.summary,
            "entities": list(self.entities),
            "importance": self.importance,
        }
        if self.reflection_link:
            d["reflection_link"] = self.reflection_link
        if self.reflection_type:
            d["reflection_type"] = self.reflection_type
        if self.metadata:
            d["metadata"] = self.metadata
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MemoryEntry:
        """Deserialize from dict, supporting both v3.1.0 and v3.0 field names.

        Old field name mappings:
        - global_time -> timestamp
        - action -> content
        - action_des -> summary
        - exp_type -> event_type
        - priority -> importance
        - other_agents -> entities
        - location -> location_id

        Args:
            data: Dictionary with memory record fields.

        Returns:
            A MemoryEntry instance.
        """
        entities = data.get("entities", data.get("other_agents", []))
        if isinstance(entities, str):
            entities = [entities]
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            agent_name=data.get("agent_name", ""),
            timestamp=data.get("timestamp", data.get("global_time", "")),
            location_id=data.get("location_id", data.get("location", "")),
            event_type=data.get("event_type", data.get("exp_type", "")),
            content=data.get("content", data.get("action", "")),
            summary=data.get("summary", data.get("action_des", "")),
            entities=tuple(entities),
            importance=int(data.get("importance", data.get("priority", 1)) or 1),
            reflection_link=data.get("reflection_link"),
            reflection_type=data.get("reflection_type"),
            metadata=data.get("metadata", {}),
        )
