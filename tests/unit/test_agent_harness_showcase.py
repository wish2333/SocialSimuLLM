"""Pure contract checks for the focused Agent / Harness showcase."""

from types import SimpleNamespace

from socialsimullm.frontend.pages.agent_harness import _items
from socialsimullm.showcase.content import (
    COLLABORATION_RULES,
    HARNESS_CONTRACTS,
    HARNESS_PIPELINE,
    PROMPT_LAYERS,
)


def test_harness_pipeline_has_ordered_input_output_stages() -> None:
    assert [item["stage"] for item in HARNESS_PIPELINE] == ["01", "02", "03", "04", "05", "06"]
    assert HARNESS_PIPELINE[0]["output"] == "bounded context"
    assert HARNESS_PIPELINE[-1]["output"] == "daily/pattern/social reflection"


def test_harness_contracts_point_to_implementation_evidence() -> None:
    assert {item["title"] for item in HARNESS_CONTRACTS} == {
        "输入边界",
        "动作边界",
        "记忆边界",
        "反思边界",
    }
    assert all(item["path"].startswith("src/socialsimullm/") for item in HARNESS_CONTRACTS)


def test_collaboration_and_prompt_layers_are_explicit() -> None:
    assert {item["title"] for item in COLLABORATION_RULES} == {"可见性", "对话", "移动", "记忆传播"}
    assert [item["layer"] for item in PROMPT_LAYERS] == ["人设", "环境", "记忆", "事件"]


def test_items_adapter_handles_pydantic_like_and_mapping_records() -> None:
    case = SimpleNamespace(branches=(SimpleNamespace(name="自然发展"), {"name": "技术暴露"}))
    assert [getattr(item, "name", item["name"] if isinstance(item, dict) else "") for item in _items(case, "branches")] == [
        "自然发展",
        "技术暴露",
    ]
