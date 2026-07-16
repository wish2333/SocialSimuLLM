import json

from socialsimullm.experiment.storage import list_experiments


def _create_experiment(tmp_path, experiment_id: str, *, completed: bool) -> None:
    run_dir = tmp_path / "runs" / "interview-demo" / experiment_id
    run_dir.mkdir(parents=True)
    (run_dir / "town_data.json").write_text("{}", encoding="utf-8")
    (run_dir / "meta.json").write_text(
        json.dumps({"round": 12, "global_time": "Day 1, 10:00"}),
        encoding="utf-8",
    )
    if completed:
        (run_dir / "done.flag").write_text("", encoding="utf-8")


def test_list_experiments_uses_completed_status_for_finished_runs(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    _create_experiment(tmp_path, "finished", completed=True)

    experiments = list_experiments(project="interview-demo")

    assert len(experiments) == 1
    assert experiments[0]["experiment_id"] == "finished"
    assert experiments[0]["status"] == "completed"


def test_list_experiments_keeps_unfinished_runs_running(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _create_experiment(tmp_path, "in-progress", completed=False)

    experiments = list_experiments(project="interview-demo")

    assert len(experiments) == 1
    assert experiments[0]["status"] == "running"
