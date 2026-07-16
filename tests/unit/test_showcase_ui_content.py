"""Content and safe-adapter tests for the research archive pages."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

from socialsimullm.frontend.pages.experiment_design import (
    _case_branches,
    _collect_interventions,
    _configuration_preview,
)
from socialsimullm.frontend.pages.overview import _overview_facts
from socialsimullm.showcase.content import VARIABLE_TRANSLATION


@dataclass
class _Manifest:
    agents: list
    locations: list
    steps: list


def test_configuration_preview_whitelists_research_fields() -> None:
    preview = _configuration_preview(
        {
            "model": "archived-model",
            "embedding_model": "archived-embedding",
            "memory_limit": 10,
            "outputs": ["events.jsonl", "checkpoints/"],
            "api_key": "must-not-appear",
            "prompt_meta": "must-not-appear",
        },
        {"time_step_minutes": 10, "rounds_per_branch": 420},
    )

    assert preview["completion_model"] == "archived-model"
    assert preview["rounds_per_branch"] == 420
    assert "api_key" not in preview
    assert "prompt_meta" not in preview


def test_case_branches_accepts_object_records() -> None:
    case = SimpleNamespace(branches=[SimpleNamespace(name="A"), SimpleNamespace(name="B")])
    assert len(_case_branches(case)) == 2


def test_branch_timeline_collects_parent_interventions() -> None:
    branches = [
        {"id": "base", "interventions": []},
        {
            "id": "exposure",
            "parent_id": "base",
            "interventions": [{"intervention_type": "technology_exposure"}],
        },
        {
            "id": "policy",
            "parent_id": "exposure",
            "interventions": [{"intervention_type": "policy_encouragement"}],
        },
    ]

    inherited = _collect_interventions(branches, branches[-1])
    assert [item["intervention_type"] for item in inherited] == [
        "technology_exposure",
        "policy_encouragement",
    ]


def test_overview_prefers_complete_research_scale() -> None:
    demo = SimpleNamespace(
        research_case=SimpleNamespace(
            scale={
                "agents_per_branch": 10,
                "locations": 10,
                "branch_count": 5,
                "rounds_per_branch": 420,
            },
            branches=[1, 2, 3, 4, 5],
        ),
        manifest=_Manifest(agents=[1], locations=[1], steps=[1]),
        events=({"step": 1},),
    )

    facts, using_research_scale = _overview_facts(demo)
    assert using_research_scale is True
    assert [fact[0] for fact in facts] == [10, 10, 5, 420]


def test_overview_falls_back_when_research_scale_is_incomplete() -> None:
    demo = SimpleNamespace(
        research_case=SimpleNamespace(scale={"agent_count": 10}),
        manifest=_Manifest(agents=[1, 2], locations=[1], steps=[1, 2]),
        events=({"step": 1}, {"step": 1}),
    )

    facts, using_research_scale = _overview_facts(demo)
    assert using_research_scale is False
    assert [fact[0] for fact in facts] == [2, 1, 2, 1]


def test_variable_translation_covers_theory_entity_and_control() -> None:
    assert len(VARIABLE_TRANSLATION) >= 3
    assert all({"theory", "entity", "control"} <= item.keys() for item in VARIABLE_TRANSLATION)
