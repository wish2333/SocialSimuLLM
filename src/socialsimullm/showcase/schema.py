"""Immutable data contracts for offline interview showcase snapshots."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class _ReadOnlyModel(BaseModel):
    """Base class for validated, immutable showcase records."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class ShowcaseSource(_ReadOnlyModel):
    """Provenance for a migrated showcase snapshot."""

    source_project: str
    source_format: str
    source_files: list[str]
    built_at: datetime
    conversion_rule_version: str
    disclaimer: str


class ShowcaseAgent(_ReadOnlyModel):
    """Agent identity copied from the source town configuration."""

    name: str
    description: str
    starting_location: str


class ShowcaseLocation(_ReadOnlyModel):
    """Location identity copied from the source town configuration."""

    name: str
    description: str


class ShowcaseStep(_ReadOnlyModel):
    """A real source time point for which a checkpoint was built."""

    step: int = Field(ge=1)
    global_time: str
    checkpoint: str


class ShowcaseEventData(_ReadOnlyModel):
    """Normalized payload migrated from one unique legacy memory entry."""

    global_time: str
    location: str
    content: str
    summary: str = ""
    entities: list[str] = Field(default_factory=list)
    importance: int | None = Field(default=None, ge=1, le=9)
    action: str | None = None
    plan: str | None = None
    impression: str | None = None


class ShowcaseEvent(_ReadOnlyModel):
    """Event compatible with the current structured JSONL envelope."""

    timestamp: str
    step: int = Field(ge=1)
    agent_id: str
    event_type: str
    data: ShowcaseEventData


class ShowcaseAgentState(_ReadOnlyModel):
    """List-form checkpoint state built only from known source fields."""

    name: str
    description: str
    location: str
    daily_plans: str = ""
    hourly_plan: str = ""
    impression: str = ""
    action: str = ""
    reflection: str = ""
    related_things: list[str] = Field(default_factory=list)
    event: list[str] = Field(default_factory=list)
    place_ratings: dict[str, Any] = Field(default_factory=dict)


class ShowcaseManifest(_ReadOnlyModel):
    """Top-level contract for a self-contained, read-only showcase demo."""

    schema_version: Literal["1.0"] = "1.0"
    project_id: str
    title: str
    summary: str
    source: ShowcaseSource
    agents: list[ShowcaseAgent]
    locations: list[ShowcaseLocation]
    steps: list[ShowcaseStep]
    event_log: str = "events.jsonl"
    available_metrics: list[str]
    migration_warnings: list[str]
