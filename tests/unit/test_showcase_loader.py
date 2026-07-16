import shutil

import pytest

from socialsimullm.showcase.content import declared_metric_labels
from socialsimullm.showcase.loader import (
    ShowcaseLoadError,
    load_showcase_demo,
    select_default_step,
)


DEMO_DIR = (
    __import__("pathlib").Path(__file__).resolve().parents[2]
    / "showcase"
    / "demo"
    / "default"
)


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
