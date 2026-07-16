"""Evidence-bound helpers for the t7 system validation page."""

from __future__ import annotations

from types import SimpleNamespace

from socialsimullm.frontend.pages.system_validation import (
    feature_validation_rows,
    memory_progression,
    role_trend_rows,
    validation_snapshot,
)


def _demo() -> SimpleNamespace:
    manifest = SimpleNamespace(
        agents=[SimpleNamespace(name=name) for name in ("Daran Edermath", "Halia Thornton", "Linene Graywind", "Toblen Stonehill")],
        locations=[1, 2, 3, 4],
        steps=list(range(1, 11)),
        source=SimpleNamespace(source_project="projects/t7"),
    )
    events = tuple(
        {"event_type": event_type, "agent_id": agent}
        for agent in ("Daran Edermath", "Halia Thornton", "Linene Graywind", "Toblen Stonehill")
        for event_type in (["action"] * 10 + ["daily_plan"] + ["hourly_plan"] * 2 + ["impression"] * 2)
    )
    states = [
        {"name": "Daran Edermath", "location": "Edermath Orchard", "action": "Tended the orchard."},
        {"name": "Halia Thornton", "location": "Phandalin Town Square", "action": "Checked accounts."},
        {"name": "Linene Graywind", "location": "Barthen's Provisions", "action": "Arranged goods."},
        {"name": "Toblen Stonehill", "location": "Phandalin Town Square", "action": "Greeted customers."},
    ]
    memory = {
        "agents": {
            name: {"total_entries": 15}
            for name in ("Daran Edermath", "Halia Thornton", "Linene Graywind", "Toblen Stonehill")
        }
    }
    return SimpleNamespace(
        manifest=manifest,
        events=events,
        checkpoints=({"step": 10, "agent_states": states, "memory_summary": memory},),
    )


def test_validation_snapshot_keeps_t7_bundle_counts_separate() -> None:
    facts = validation_snapshot(_demo())
    assert facts["source"] == "projects/t7"
    assert (facts["agents"], facts["locations"], facts["steps"]) == (4, 4, 10)
    assert facts["events"] == 60
    assert facts["action_events"] == 40


def test_role_trends_are_derived_from_latest_checkpoint() -> None:
    rows = role_trend_rows(_demo())
    assert {row["agent"] for row in rows} == {
        "Daran Edermath",
        "Halia Thornton",
        "Linene Graywind",
        "Toblen Stonehill",
    }
    assert next(row for row in rows if row["agent"] == "Daran Edermath")["location"] == "Edermath Orchard"


def test_reflection_row_explicitly_marks_legacy_boundary() -> None:
    rows = feature_validation_rows(_demo())
    reflection = next(row for row in rows if row["feature"] == "反思")
    assert "尚未" in reflection["baseline"]
    assert "不是 t7 观测结果" in reflection["evidence"]


def test_memory_progression_only_reports_symmetric_checkpoints() -> None:
    demo = _demo()
    demo.checkpoints = (
        {"step": 1, "memory_summary": {"agents": {"a": {"total_entries": 4}, "b": {"total_entries": 4}}}},
        {"step": 7, "memory_summary": {"agents": {"a": {"total_entries": 12}, "b": {"total_entries": 11}}}},
    )
    assert memory_progression(demo) == {1: "4"}
