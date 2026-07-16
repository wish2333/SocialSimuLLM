from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PROJECT = PROJECT_ROOT / "projects" / "t7"
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.build_showcase_demo import build_showcase_demo  # noqa: E402
from socialsimullm.showcase.schema import ShowcaseManifest  # noqa: E402


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_builds_standard_demo_from_real_legacy_project(tmp_path: Path) -> None:
    source = tmp_path / "legacy" / "t7"
    output = tmp_path / "showcase" / "demo" / "default"
    shutil.copytree(SOURCE_PROJECT, source)

    manifest = build_showcase_demo(source, output)

    loaded_manifest = ShowcaseManifest.model_validate(
        yaml.safe_load((output / "manifest.yaml").read_text(encoding="utf-8"))
    )
    events = _load_jsonl(output / "events.jsonl")

    assert loaded_manifest == manifest
    assert loaded_manifest.source.source_project == "projects/t7"
    assert loaded_manifest.source.conversion_rule_version == "legacy-t7-v1"
    assert loaded_manifest.migration_warnings
    assert loaded_manifest.available_metrics == [
        "activity_distribution",
        "location_occupancy",
        "memory_distribution",
    ]
    assert {agent.name for agent in loaded_manifest.agents} == {
        "Daran Edermath",
        "Halia Thornton",
        "Linene Graywind",
        "Toblen Stonehill",
    }
    assert len(loaded_manifest.locations) == 4
    assert loaded_manifest.steps[-1].step == 10

    assert events
    assert all(
        set(event) == {"timestamp", "step", "agent_id", "event_type", "data"}
        for event in events
    )
    assert all(isinstance(event["data"].get("content"), str) for event in events)
    assert any(
        event["agent_id"] == "Daran Edermath"
        and event["step"] == 10
        and event["event_type"] == "action"
        and "remove any weeds" in event["data"]["content"]
        and "removed weeds" in event["data"]["summary"]
        for event in events
    )

    checkpoint = output / loaded_manifest.steps[-1].checkpoint
    agent_states = json.loads((checkpoint / "agent_states.json").read_text(encoding="utf-8"))
    assert isinstance(agent_states, list)
    assert len(agent_states) == 4
    assert all(isinstance(state, dict) for state in agent_states)
    assert {state["name"] for state in agent_states} == {
        "Daran Edermath",
        "Halia Thornton",
        "Linene Graywind",
        "Toblen Stonehill",
    }


def test_generated_demo_is_independent_and_contains_no_raw_or_sensitive_files(
    tmp_path: Path,
) -> None:
    source = tmp_path / "legacy" / "t7"
    output = tmp_path / "showcase" / "demo" / "default"
    shutil.copytree(SOURCE_PROJECT, source)
    build_showcase_demo(source, output)

    shutil.rmtree(tmp_path / "legacy")

    manifest = ShowcaseManifest.model_validate(
        yaml.safe_load((output / "manifest.yaml").read_text(encoding="utf-8"))
    )
    events = _load_jsonl(output / "events.jsonl")
    assert manifest.steps
    assert events

    generated_files = [path for path in output.rglob("*") if path.is_file()]
    assert not any(path.suffix in {".db", ".sqlite", ".sqlite3"} for path in generated_files)
    assert not any(path.name in {"simulation_log.txt", "simulation_summary.txt"} for path in generated_files)

    combined = "\n".join(path.read_text(encoding="utf-8") for path in generated_files)
    lowered = combined.lower()
    assert "api_key" not in lowered
    assert "authorization: bearer" not in lowered
    assert "sk-" not in lowered
