#!/usr/bin/env python3
"""Build a self-contained v3.1 showcase snapshot from a legacy project.

This is a development-time migration tool. The generated demo never reads the
legacy project at runtime and deliberately excludes raw logs, databases, and
configuration fields that are not part of the showcase contract.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

from socialsimullm.showcase.schema import (
    ShowcaseAgent,
    ShowcaseAgentState,
    ShowcaseEvent,
    ShowcaseEventData,
    ShowcaseLocation,
    ShowcaseManifest,
    ShowcaseSource,
    ShowcaseStep,
)


CONVERSION_RULE_VERSION = "legacy-t7-v1"
ROUND_PATTERN = re.compile(
    r"^=+\s*ROUND\s+(?P<step>\d+)\s+TIME\s+(?P<global_time>.+?)\s*=+\s*$",
    re.MULTILINE,
)
SENSITIVE_PATTERNS = (
    re.compile(r"(?i)api[_-]?key\s*[:=]"),
    re.compile(r"(?i)authorization\s*:\s*bearer"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
)


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def _rounds_from_log(path: Path) -> list[tuple[int, str]]:
    text = path.read_text(encoding="utf-8")
    rounds = [
        (int(match.group("step")), match.group("global_time").strip())
        for match in ROUND_PATTERN.finditer(text)
    ]
    if not rounds:
        raise ValueError(f"No round timestamps found in {path}")
    if len({step for step, _ in rounds}) != len(rounds):
        raise ValueError(f"Duplicate round numbers found in {path}")
    return rounds


def _event_type(entry: dict[str, Any]) -> str:
    legacy_type = str(entry.get("exp_type", "")).strip() or "unknown"
    content = str(entry.get("action", "")).lower()
    if legacy_type == "plan" and "daily plan" in content:
        return "daily_plan"
    if legacy_type == "plan" and "hourly plan" in content:
        return "hourly_plan"
    if legacy_type == "thought":
        return "impression"
    return legacy_type


def _event_specific_payload(event_type: str, content: str) -> dict[str, str | None]:
    values: dict[str, str | None] = {"action": None, "plan": None, "impression": None}
    if event_type == "action":
        values["action"] = content
    elif event_type in {"daily_plan", "hourly_plan", "plan"}:
        values["plan"] = content
    elif event_type == "impression":
        values["impression"] = content
    return values


def _legacy_entries(source_project: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for memory_path in sorted((source_project / "agent_data").glob("*_memory.json")):
        memory = _read_json(memory_path).get("memory", [])
        if not isinstance(memory, list):
            raise ValueError(f"Expected a memory list in {memory_path}")
        entries.extend(entry for entry in memory if isinstance(entry, dict))
    return entries


def _deduplicate_entries(entries: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove copies written into co-located agents' legacy memory files."""

    unique: dict[tuple[Any, ...], dict[str, Any]] = {}
    for entry in entries:
        key = (
            entry.get("global_time", ""),
            entry.get("agent_name", ""),
            entry.get("location", ""),
            entry.get("exp_type", ""),
            entry.get("action", ""),
            entry.get("action_des", ""),
        )
        unique.setdefault(key, entry)
    return list(unique.values())


def _normalize_events(
    entries: Iterable[dict[str, Any]],
    time_to_step: dict[str, int],
    known_agents: set[str],
) -> tuple[list[ShowcaseEvent], int, int]:
    normalized: list[ShowcaseEvent] = []
    skipped_missing_time = 0
    skipped_unknown_agent = 0

    for entry in entries:
        global_time = str(entry.get("global_time", "")).strip()
        agent_name = str(entry.get("agent_name", "")).strip()
        if global_time not in time_to_step:
            skipped_missing_time += 1
            continue
        if agent_name not in known_agents:
            skipped_unknown_agent += 1
            continue

        content = str(entry.get("action", ""))
        summary = str(entry.get("action_des", ""))
        location = str(entry.get("location", ""))
        legacy_entities = entry.get("other_agents", [])
        if isinstance(legacy_entities, str):
            entities = [legacy_entities]
        elif isinstance(legacy_entities, list):
            entities = [str(value) for value in legacy_entities]
        else:
            entities = []
        raw_importance = entry.get("priority")
        try:
            importance = int(raw_importance) if raw_importance is not None else None
        except (TypeError, ValueError):
            importance = None
        if importance is not None and not 1 <= importance <= 9:
            importance = None

        event_type = _event_type(entry)
        normalized.append(
            ShowcaseEvent(
                timestamp=global_time,
                step=time_to_step[global_time],
                agent_id=agent_name,
                event_type=event_type,
                data=ShowcaseEventData(
                    global_time=global_time,
                    location=location,
                    content=content,
                    summary=summary,
                    entities=entities,
                    importance=importance,
                    **_event_specific_payload(event_type, content),
                ),
            )
        )

    normalized.sort(key=lambda event: (event.step, event.agent_id, event.event_type, event.data.content))
    return normalized, skipped_missing_time, skipped_unknown_agent


def _latest_event(
    events: list[ShowcaseEvent],
    event_types: set[str],
    step: int,
) -> ShowcaseEvent | None:
    candidates = [event for event in events if event.event_type in event_types and event.step <= step]
    return max(
        candidates,
        key=lambda event: (event.step, event.event_type, event.data.content),
        default=None,
    )


def _checkpoint_states(
    agents: list[ShowcaseAgent],
    events: list[ShowcaseEvent],
    step: int,
) -> list[ShowcaseAgentState]:
    events_by_agent: dict[str, list[ShowcaseEvent]] = defaultdict(list)
    for event in events:
        events_by_agent[event.agent_id].append(event)

    states: list[ShowcaseAgentState] = []
    for agent in agents:
        agent_events = events_by_agent[agent.name]
        latest_any = _latest_event(agent_events, {event.event_type for event in agent_events}, step)
        latest_action = _latest_event(agent_events, {"action"}, step)
        daily_plan = _latest_event(agent_events, {"daily_plan"}, step)
        hourly_plan = _latest_event(agent_events, {"hourly_plan", "plan"}, step)
        impression = _latest_event(agent_events, {"impression", "thought"}, step)
        reflection = _latest_event(agent_events, {"reflection"}, step)

        location = latest_any.data.location if latest_any and latest_any.data.location else agent.starting_location
        related = latest_action.data.entities if latest_action else []
        states.append(
            ShowcaseAgentState(
                name=agent.name,
                description=agent.description,
                location=location,
                daily_plans=daily_plan.data.content if daily_plan else "",
                hourly_plan=hourly_plan.data.content if hourly_plan else "",
                impression=(impression.data.summary or impression.data.content) if impression else "",
                action=(latest_action.data.summary or latest_action.data.content) if latest_action else "",
                reflection=(reflection.data.summary or reflection.data.content) if reflection else "",
                related_things=[name for name in related if name != agent.name],
            )
        )
    return states


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_checkpoints(
    output_dir: Path,
    agents: list[ShowcaseAgent],
    locations: list[ShowcaseLocation],
    rounds: list[tuple[int, str]],
    events: list[ShowcaseEvent],
    project_name: str,
    memory_limit: int,
) -> list[ShowcaseStep]:
    steps: list[ShowcaseStep] = []
    for step, global_time in rounds:
        relative = Path("checkpoints") / f"step_{step}"
        checkpoint_dir = output_dir / relative
        states = _checkpoint_states(agents, events, step)
        _write_json(
            checkpoint_dir / "agent_states.json",
            [state.model_dump(mode="json") for state in states],
        )
        _write_json(
            checkpoint_dir / "meta.json",
            {"project_name": project_name, "global_time": global_time, "round": step},
        )
        _write_json(
            checkpoint_dir / "spatial_graph.json",
            {
                "directed": False,
                "multigraph": False,
                "graph": {},
                "nodes": [
                    {"id": location.name, "description": location.description}
                    for location in locations
                ],
                "links": [],
            },
        )

        counts: dict[str, Any] = {"memory_limit": memory_limit, "agents": {}}
        for agent in agents:
            current = [event for event in events if event.agent_id == agent.name and event.step <= step]
            by_type = Counter(event.event_type for event in current)
            counts["agents"][agent.name] = {
                "total_entries": len(current),
                "by_type": dict(sorted(by_type.items())),
                "latest_timestamp": current[-1].timestamp if current else "",
            }
        _write_json(checkpoint_dir / "memory_summary.json", counts)
        steps.append(
            ShowcaseStep(
                step=step,
                global_time=global_time,
                checkpoint=relative.as_posix(),
            )
        )
    return steps


def _assert_no_sensitive_output(output_dir: Path) -> None:
    for path in output_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
            raise ValueError(f"Database file must not be included in showcase output: {path}")
        text = path.read_text(encoding="utf-8")
        if any(pattern.search(text) for pattern in SENSITIVE_PATTERNS):
            raise ValueError(f"Potential sensitive value found in showcase output: {path}")


def build_showcase_demo(source_project: Path, output_dir: Path) -> ShowcaseManifest:
    """Migrate a legacy project into an independent showcase directory."""

    source_project = Path(source_project)
    output_dir = Path(output_dir)
    required = [
        source_project / "meta.json",
        source_project / "town_data.json",
        source_project / "simulation_log.txt",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing legacy source files: {', '.join(missing)}")

    meta = _read_json(source_project / "meta.json")
    town_data = _read_json(source_project / "town_data.json")
    rounds = _rounds_from_log(source_project / "simulation_log.txt")
    time_to_step = {global_time: step for step, global_time in rounds}

    town_people = town_data.get("town_people", {})
    town_areas = town_data.get("town_areas", {})
    if not isinstance(town_people, dict) or not isinstance(town_areas, dict):
        raise ValueError("Legacy town_data.json must contain town_people and town_areas objects")

    agents = [
        ShowcaseAgent(
            name=str(name),
            description=str(value.get("description", "")) if isinstance(value, dict) else "",
            starting_location=str(value.get("starting_location", "")) if isinstance(value, dict) else "",
        )
        for name, value in town_people.items()
    ]
    locations = [
        ShowcaseLocation(name=str(name), description=str(description))
        for name, description in town_areas.items()
    ]

    raw_entries = _legacy_entries(source_project)
    unique_entries = _deduplicate_entries(raw_entries)
    events, skipped_missing_time, skipped_unknown_agent = _normalize_events(
        unique_entries,
        time_to_step,
        {agent.name for agent in agents},
    )
    if not events:
        raise ValueError("No legacy memory entries could be migrated")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    events_path = output_dir / "events.jsonl"
    with events_path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event.model_dump(mode="json"), ensure_ascii=False) + "\n")

    project_name = str(meta.get("project_name", source_project.name))
    general = town_data.get("general", {})
    raw_memory_limit = general.get("memory_limit", 0) if isinstance(general, dict) else 0
    try:
        memory_limit = int(raw_memory_limit)
    except (TypeError, ValueError):
        memory_limit = 0
    steps = _write_checkpoints(
        output_dir,
        agents,
        locations,
        rounds,
        events,
        project_name,
        memory_limit,
    )

    warnings = [
        "旧数据没有绝对日期；events.jsonl 的 timestamp 保留仿真时间，而非构建时钟时间。",
        "旧 town_data 没有地点拓扑；checkpoint 仅保留真实地点节点，不生成推测的连边。",
        "旧数据没有可靠的反思、地点评分和全局事件；对应 checkpoint 字段保持为空。",
        f"旧 memory 在同地点角色文件中有重复副本；已按原始字段去重 {len(raw_entries) - len(unique_entries)} 条。",
    ]
    if skipped_missing_time:
        warnings.append(f"有 {skipped_missing_time} 条 memory 无法映射到文本日志中的真实轮次，未迁移。")
    if skipped_unknown_agent:
        warnings.append(f"有 {skipped_unknown_agent} 条 memory 的角色不在 town_data 中，未迁移。")

    source_files = [
        "meta.json",
        "town_data.json",
        "simulation_log.txt",
        *[
            path.relative_to(source_project).as_posix()
            for path in sorted((source_project / "agent_data").glob("*_memory.json"))
        ],
    ]
    manifest = ShowcaseManifest(
        project_id=project_name,
        title="Phandalin 十轮离线社会仿真",
        summary="四名角色在四个地点中完成计划、行动与印象记录的十轮旧实验快照。",
        source=ShowcaseSource(
            source_project=f"projects/{source_project.name}",
            source_format="SocialSimuLLM legacy project (pre-v3.1)",
            source_files=source_files,
            built_at=datetime.now(timezone.utc),
            conversion_rule_version=CONVERSION_RULE_VERSION,
            disclaimer="展示数据来自旧实验的真实记录，仅迁移展示结构；缺失字段保持为空，不代表新的仿真结果。",
        ),
        agents=agents,
        locations=locations,
        steps=steps,
        available_metrics=[
            "activity_distribution",
            "location_occupancy",
            "memory_distribution",
        ],
        migration_warnings=warnings,
    )
    (output_dir / "manifest.yaml").write_text(
        yaml.safe_dump(
            manifest.model_dump(mode="json"),
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    _assert_no_sensitive_output(output_dir)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("projects/t7"))
    parser.add_argument("--output", type=Path, default=Path("showcase/demo/default"))
    args = parser.parse_args()
    manifest = build_showcase_demo(args.source, args.output)
    print(
        f"Built {len(manifest.steps)} checkpoints for {len(manifest.agents)} agents "
        f"at {args.output}"
    )


if __name__ == "__main__":
    main()
