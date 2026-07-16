"""Read-only loader for self-contained showcase demo snapshots."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from socialsimullm.frontend.adapters import normalize_agent_states
from socialsimullm.showcase.schema import (
    ResearchCase,
    ShowcaseEvent,
    ShowcaseManifest,
)


class ShowcaseLoadError(RuntimeError):
    """Raised when an offline showcase snapshot cannot be safely loaded."""


@dataclass(frozen=True)
class ShowcaseDemo:
    """Validated manifest with immutable references to loaded demo records."""

    root: Path
    manifest: ShowcaseManifest
    events: tuple[dict[str, Any], ...]
    checkpoints: tuple[dict[str, Any], ...]
    research_case: ResearchCase | None = None

    def checkpoint(self, step: int) -> dict[str, Any]:
        """Return a checkpoint by exact step number."""
        for checkpoint in self.checkpoints:
            if checkpoint.get("step") == step:
                return checkpoint
        raise KeyError(f"No showcase checkpoint for step {step}")

    def events_at(self, step: int) -> list[dict[str, Any]]:
        """Return events emitted at one simulation step."""
        return [event for event in self.events if event.get("step") == step]


def get_default_demo_dir() -> Path:
    """Resolve the bundled demo independently from the process cwd."""
    return Path(__file__).resolve().parents[3] / "showcase" / "demo" / "default"


def load_showcase_demo(demo_dir: str | Path | None = None) -> ShowcaseDemo:
    """Load one offline demo without accessing legacy projects or APIs."""
    root = Path(demo_dir) if demo_dir is not None else get_default_demo_dir()
    root = root.expanduser().resolve()
    manifest_path = root / "manifest.yaml"
    if not manifest_path.is_file():
        raise ShowcaseLoadError(f"Showcase manifest not found: {manifest_path}")

    try:
        raw_manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        manifest = ShowcaseManifest.model_validate(raw_manifest)
    except (OSError, yaml.YAMLError, ValidationError) as exc:
        raise ShowcaseLoadError(f"Invalid showcase manifest: {exc}") from exc

    event_path = _safe_child(root, manifest.event_log)
    events = _load_events(event_path)
    checkpoints = tuple(
        _load_checkpoint(root, item.step, item.checkpoint)
        for item in manifest.steps
    )
    research_case = _load_research_case(root, manifest.research_case)
    return ShowcaseDemo(root, manifest, events, checkpoints, research_case)


def select_default_step(demo: ShowcaseDemo) -> int:
    """Choose the most information-rich checkpoint, preferring later ties."""
    if not demo.checkpoints:
        raise ShowcaseLoadError("Showcase contains no checkpoints")

    def score(checkpoint: dict[str, Any]) -> tuple[int, int]:
        states = normalize_agent_states(checkpoint.get("agent_states"))
        state_fields = sum(
            bool(state.get(field))
            for state in states
            for field in ("location", "daily_plans", "hourly_plan", "action", "impression", "reflection")
        )
        memory_total = sum(
            int(item.get("total_entries", 0))
            for item in checkpoint.get("memory_summary", {}).get("agents", {}).values()
            if isinstance(item, dict)
        )
        step = int(checkpoint.get("step", 0))
        return state_fields + memory_total + len(demo.events_at(step)), step

    return int(max(demo.checkpoints, key=score)["step"])


def _safe_child(root: Path, relative_path: str) -> Path:
    candidate = (root / relative_path).resolve()
    if candidate != root and root not in candidate.parents:
        raise ShowcaseLoadError(f"Path points outside demo directory: {relative_path}")
    return candidate


def _load_research_case(root: Path, relative_path: str | None) -> ResearchCase | None:
    """Load an optional case only from the showcase bundle's research folder."""
    if not relative_path:
        return None
    research_root = (root.parents[1] / "research").resolve()
    candidate = (root / relative_path).resolve()
    if candidate != research_root and research_root not in candidate.parents:
        raise ShowcaseLoadError(
            "Research case path points outside showcase research directory: "
            f"{relative_path}"
        )
    if not candidate.is_file():
        return None
    try:
        raw_case = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
        return ResearchCase.model_validate(raw_case)
    except (OSError, yaml.YAMLError, ValidationError) as exc:
        raise ShowcaseLoadError(f"Invalid research case: {exc}") from exc


def _load_events(path: Path) -> tuple[dict[str, Any], ...]:
    if not path.is_file():
        raise ShowcaseLoadError(f"Showcase event log not found: {path}")
    events: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                event = ShowcaseEvent.model_validate(json.loads(line))
                events.append(event.model_dump(mode="json"))
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise ShowcaseLoadError(f"Invalid event log {path.name}: {exc}") from exc
    return tuple(events)


def _load_checkpoint(root: Path, step: int, relative_path: str) -> dict[str, Any]:
    directory = _safe_child(root, relative_path)
    if not directory.is_dir():
        raise ShowcaseLoadError(f"Checkpoint directory not found: {relative_path}")
    checkpoint: dict[str, Any] = {"step": step}
    for key in ("agent_states", "spatial_graph", "memory_summary", "meta"):
        path = directory / f"{key}.json"
        if not path.is_file():
            raise ShowcaseLoadError(f"Checkpoint file not found: {path.name}")
        try:
            checkpoint[key] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ShowcaseLoadError(f"Invalid checkpoint file {path}: {exc}") from exc
    checkpoint["agent_states"] = normalize_agent_states(checkpoint["agent_states"])
    return checkpoint
