"""Evidence-bound helpers for the four-person paper-town validation page."""

from socialsimullm.frontend.pages.system_validation import feature_validation_rows
from socialsimullm.showcase.content import PAPER_TOWN_VALIDATION


def test_paper_town_validation_is_four_person_and_four_location() -> None:
    assert PAPER_TOWN_VALIDATION["agents"] == 4
    assert PAPER_TOWN_VALIDATION["locations"] == 4
    assert PAPER_TOWN_VALIDATION["rounds"] == 78
    assert len(PAPER_TOWN_VALIDATION["roles"]) == 4


def test_reflection_row_explicitly_marks_paper_boundary() -> None:
    reflection = next(row for row in feature_validation_rows() if row["feature"] == "反思")
    assert "未单独报告" in reflection["paper_evidence"]
    assert "不冒充论文观测结果" in reflection["boundary"]


def test_extension_row_keeps_campus_scale_out_of_town_validation() -> None:
    extension = next(row for row in feature_validation_rows() if row["feature"] == "延展性")
    assert "10 Agent / 10 地点" in extension["boundary"]
