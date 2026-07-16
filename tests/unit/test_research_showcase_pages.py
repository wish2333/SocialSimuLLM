"""Pure presentation adapters for the archived paper case."""

from __future__ import annotations

from types import SimpleNamespace

from socialsimullm.frontend.pages.demo import intervention_timeline
from socialsimullm.frontend.pages.results import (
    alternative_explanation_rows,
    archive_metric_rows,
    next_test_rows,
    role_count_rows,
)


def _case() -> SimpleNamespace:
    metric = SimpleNamespace(
        id="practice",
        label="实践行动",
        numerator=84,
        denominator=4200,
        by_agent=(
            SimpleNamespace(agent="林灵钥", count=50),
            SimpleNamespace(agent="王明哲", count=34),
        ),
    )
    archive = SimpleNamespace(
        display_name="GE 归档组",
        metrics=(metric,),
    )
    event = SimpleNamespace(
        global_time="Day 2, 08:00",
        intervention_type="technology_exposure",
        recipients=("林灵钥",),
        intensity="partial",
        direction="neutral",
        content="技术信息",
    )
    branches = (
        SimpleNamespace(id="B2", interventions=(event,)),
        SimpleNamespace(id="B4", interventions=(event,)),
    )
    finding = SimpleNamespace(
        title="场景需求耦合",
        alternative_explanations=("角色原始技术偏好可能解释部分差异",),
    )
    limitation = SimpleNamespace(description="缺乏重复实验")
    return SimpleNamespace(
        archives=(archive,),
        branches=branches,
        findings=(finding,),
        limitations=(limitation,),
    )


def test_archive_metrics_keep_explicit_denominator_and_descriptive_label() -> None:
    rows = archive_metric_rows(_case())

    assert rows == [
        {
            "归档组": "GE 归档组",
            "指标": "实践行动",
            "命中条数": 84,
            "分母": 4200,
            "描述性占比": "2.0%",
            "口径": "主行动规则命中 / 归档组全部主行动",
        }
    ]


def test_role_rows_report_counts_without_inventing_agent_rates() -> None:
    rows = role_count_rows(_case())

    assert [row["命中次数"] for row in rows] == [50, 34]
    assert all("采纳率" in row["口径"] for row in rows)
    assert all("占比" not in row for row in rows)


def test_intervention_timeline_deduplicates_shared_event_and_keeps_branches() -> None:
    timeline = intervention_timeline(_case())

    assert len(timeline) == 1
    assert timeline[0]["label"] == "技术暴露"
    assert timeline[0]["branches"] == ["B2", "B4"]


def test_analysis_exposes_alternatives_and_follow_up_as_unfinished_work() -> None:
    alternatives = alternative_explanation_rows(_case())
    follow_ups = next_test_rows(_case())

    assert alternatives[0]["finding"] == "场景需求耦合"
    assert "偏好" in alternatives[0]["alternative"]
    assert follow_ups[0]["basis"] == "缺乏重复实验"
    assert "多种子重复" in follow_ups[0]["design"]
