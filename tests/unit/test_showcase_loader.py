import shutil

import pytest
import yaml
from pydantic import ValidationError

from socialsimullm.showcase.content import declared_metric_labels
from socialsimullm.showcase.loader import (
    ShowcaseLoadError,
    load_showcase_demo,
    select_default_step,
)
from socialsimullm.showcase.schema import ResearchCase


DEMO_DIR = (
    __import__("pathlib").Path(__file__).resolve().parents[2]
    / "showcase"
    / "demo"
    / "default"
)
RESEARCH_CASE = DEMO_DIR.parents[1] / "research" / "campus_ivmodel" / "case.yaml"


def test_loader_reads_self_contained_copy_without_legacy_project(
    tmp_path, monkeypatch
) -> None:
    copied_demo = tmp_path / "offline-demo"
    shutil.copytree(DEMO_DIR, copied_demo)
    isolated_cwd = tmp_path / "empty-cwd"
    isolated_cwd.mkdir()
    monkeypatch.chdir(isolated_cwd)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    demo = load_showcase_demo(copied_demo)

    assert demo.manifest.project_id == "t7"
    assert demo.events
    assert len(demo.checkpoints) == len(demo.manifest.steps)
    assert not (isolated_cwd / "projects").exists()
    assert not (isolated_cwd / ".git").exists()


def test_default_demo_loads_validated_research_case() -> None:
    demo = load_showcase_demo(DEMO_DIR)

    assert demo.research_case is not None
    assert demo.research_case.provenance.repository_commit == (
        "cfedfc5689fb8cc43f9e68046f28a0469bef968f"
    )
    assert demo.research_case.scale.branch_count == 5
    assert demo.research_case.scale.archived_branch_count == 2
    assert "共享前缀" in demo.research_case.scale.execution_note
    assert demo.research_case.config.model.startswith("Doubao-1.5-pro-32k")
    assert (
        "archive-level model identifier"
        in demo.research_case.config.missing_reproducibility_fields
    )
    assert len(demo.research_case.branches) == 5
    assert {archive.repository_label for archive in demo.research_case.archives} == {
        "GE",
        "NA",
    }
    assert all(archive.total_actions == 4200 for archive in demo.research_case.archives)


def test_research_case_is_immutable() -> None:
    research_case = load_showcase_demo(DEMO_DIR).research_case
    assert research_case is not None

    with pytest.raises(ValidationError, match="frozen"):
        research_case.title = "mutated"  # type: ignore[misc]


def test_copied_demo_can_load_without_optional_research_sibling(tmp_path) -> None:
    copied_demo = tmp_path / "showcase" / "demo" / "offline-demo"
    shutil.copytree(DEMO_DIR, copied_demo)

    demo = load_showcase_demo(copied_demo)

    assert demo.research_case is None


def test_loader_rejects_research_case_path_outside_research_directory(
    tmp_path,
) -> None:
    copied_demo = tmp_path / "showcase" / "demo" / "offline-demo"
    shutil.copytree(DEMO_DIR, copied_demo)
    manifest_path = copied_demo / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["research_case"] = "../../../outside.yaml"
    manifest_path.write_text(
        yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(ShowcaseLoadError, match="outside showcase research"):
        load_showcase_demo(copied_demo)


def test_research_metric_rejects_numerator_larger_than_denominator() -> None:
    raw_case = yaml.safe_load(RESEARCH_CASE.read_text(encoding="utf-8"))
    raw_case["archives"][0]["metrics"][0]["numerator"] = 4201

    with pytest.raises(ValidationError, match="numerator cannot exceed"):
        ResearchCase.model_validate(raw_case)


def test_default_step_prefers_checkpoint_with_most_information() -> None:
    demo = load_showcase_demo(DEMO_DIR)

    selected = select_default_step(demo)

    assert selected == 10
    assert demo.checkpoint(selected)["agent_states"]


def test_result_metrics_are_driven_by_manifest_declaration() -> None:
    demo = load_showcase_demo(DEMO_DIR)

    visible_metrics = dict(
        declared_metric_labels(demo.manifest.available_metrics)
    )

    assert tuple(visible_metrics) == tuple(demo.manifest.available_metrics)
    assert "innovation_adoption" not in visible_metrics


def test_loader_rejects_checkpoint_path_outside_demo(tmp_path) -> None:
    copied_demo = tmp_path / "offline-demo"
    shutil.copytree(DEMO_DIR, copied_demo)
    manifest = copied_demo / "manifest.yaml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            "checkpoint: checkpoints/step_1",
            "checkpoint: ../../outside",
            1,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ShowcaseLoadError, match="outside demo directory"):
        load_showcase_demo(copied_demo)
