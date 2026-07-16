"""Read-only console for the archived innovation-diffusion design."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import streamlit as st
import yaml

from socialsimullm.showcase.content import (
    DEFAULT_BRANCH_TIMELINE,
    INTERVENTION_BOUNDARIES,
    VARIABLE_TRANSLATION,
)
from socialsimullm.showcase.loader import ShowcaseDemo


def render_experiment_design(demo: ShowcaseDemo) -> None:
    """Connect theory, simulation entities, branch controls, and evidence."""
    case = getattr(demo, "research_case", None)

    st.markdown(
        '<p class="archive-kicker">RESEARCH CONTROL / READ ONLY</p>',
        unsafe_allow_html=True,
    )
    st.title("实验设计：把理论变量转成可观察、可介入的仿真结构")
    st.caption("研究控制台展示已归档设计；选择分支只切换记录，不启动模型或改写实验数据。")

    if case is None:
        st.info("当前档案未附论文研究案例；以下保留框架级变量映射与介入边界。")
    else:
        questions = _as_sequence(_lookup(case, "research_questions", default=[]))
        if questions:
            st.markdown("### 研究问题")
            for question in questions:
                data = _as_mapping(question)
                st.markdown(f'**{_pick(data, "title", "id", default="研究问题")}**')
                st.write(_pick(data, "question", default=""))
                lenses = _pick(data, "theoretical_lens", default=[])
                if lenses:
                    st.caption("理论视角 · " + _display_value(lenses))

    _render_variable_translation(case)
    _render_branch_console(case)
    _render_configuration(case)
    _render_intervention_boundaries()


def _render_variable_translation(case: Any) -> None:
    st.markdown("### 从理论到仿真实体")
    st.caption("变量不是提示词装饰，而是进入角色、网络、事件和输出编码的实验结构。")

    archived = _lookup(case, "variable_operationalizations", "variables", default=[])
    rows = _as_sequence(archived) or VARIABLE_TRANSLATION
    columns = st.columns(2, gap="medium")
    for index, item in enumerate(rows):
        data = _as_mapping(item)
        theory = _pick(data, "theory", "construct", "name", default=f"变量 {index + 1}")
        question = _pick(
            data,
            "question",
            "definition",
            "operational_definition",
            "theoretical_source",
            default="",
        )
        entity = _pick(
            data,
            "entity",
            "simulation_entity",
            "mapping",
            "operationalization",
            default="",
        )
        control = _pick(
            data,
            "control",
            "intervention",
            "observable",
            "measurement",
            default="",
        )
        with columns[index % 2]:
            st.markdown(
                '<div class="design-card">'
                f'<small>THEORY → ENTITY → CONTROL</small><h4>{_escape(theory)}</h4>'
                f'<p>{_escape(question)}</p>'
                f'<b>{_escape(entity)}</b><br><span>{_escape(control)}</span>'
                "</div>",
                unsafe_allow_html=True,
            )


def _render_branch_console(case: Any) -> None:
    st.markdown("### 五分支运行时间轴")
    branches = _case_branches(case)
    if not branches:
        st.info("研究案例分支记录尚未加载；显示共同的实验阶段模板。")
        _render_timeline(DEFAULT_BRANCH_TIMELINE)
        return

    labels = [_branch_label(branch, index) for index, branch in enumerate(branches)]
    selected_label = st.selectbox("查看归档分支", labels, key="research_branch")
    selected = branches[labels.index(selected_label)]
    data = _as_mapping(selected)
    intervention_data = _collect_interventions(branches, selected)

    inherited = _pick(data, "inherits", "baseline", "shared_baseline", default="共享基线检查点")
    event_time = _joined_intervention_value(intervention_data, "global_time", fallback="无额外事件")
    target = _joined_intervention_value(intervention_data, "recipients", fallback="共享基线")
    intensity = _joined_intervention_value(intervention_data, "intensity", fallback="none")
    direction = _joined_intervention_value(intervention_data, "direction", fallback="neutral")

    metrics = st.columns(5)
    for column, (label, value) in zip(
        metrics,
        [
            ("继承基线", inherited),
            ("事件时间", event_time),
            ("目标对象", _display_value(target)),
            ("接触强度", intensity),
            ("政策方向", direction),
        ],
    ):
        column.metric(label, str(value))

    scale = _as_mapping(_lookup(case, "scale", "run_scale", default={}))
    timeline = _branch_timeline(data, intervention_data, scale)
    _render_timeline(timeline)

    description = _pick(data, "description", "summary", "content")
    if description:
        st.caption(str(description))


def _render_timeline(items: list[tuple[str, str, str]]) -> None:
    for time, title, detail in items:
        st.markdown(
            '<div class="branch-track">'
            f'<b>{_escape(time)} · {_escape(title)}</b><br>'
            f'<span>{_escape(detail)}</span></div>',
            unsafe_allow_html=True,
        )


def _render_configuration(case: Any) -> None:
    st.markdown("### 只读配置预览")
    config = _lookup(case, "config", "formal_config", "experiment_config", "configuration")
    scale = _lookup(case, "scale", "run_scale")
    preview = _configuration_preview(config, scale)
    if not preview:
        st.info("研究档案没有提供可显示的正式运行配置。")
        return

    st.code(
        yaml.safe_dump(preview, allow_unicode=True, sort_keys=False),
        language="yaml",
    )
    st.caption("预览仅列出研究运行参数与输出产物，不包含密钥、完整提示词或原始日志。")


def _render_intervention_boundaries() -> None:
    st.markdown("### 人为介入边界")
    columns = st.columns(3, gap="medium")
    for column, (stage, detail) in zip(columns, INTERVENTION_BOUNDARIES):
        column.markdown(f"#### {stage}")
        column.write(detail)
    st.warning("研究者控制实验条件和观察口径，但不直接替 Agent 作出行动，也不回写已归档的过程证据。")


def _case_branches(case: Any) -> list[Any]:
    """Return archived branches without assuming a concrete schema container."""
    return _as_sequence(_lookup(case, "branches", "intervention_branches", "scenarios", default=[]))


def _configuration_preview(config: Any, scale: Any = None) -> dict[str, Any]:
    """Whitelist non-sensitive fields for the read-only configuration panel."""
    data = _as_mapping(config)
    scale_data = _as_mapping(scale)
    fields = [
        ("language", ("language",)),
        ("completion_model", ("completion_model", "model")),
        ("embedding_model", ("embedding_model", "vector_model")),
        ("memory_limit", ("memory_limit",)),
        ("global_time_limit", ("global_time_limit",)),
        ("max_attempts", ("max_attempts",)),
        ("agent_count", ("agent_count", "agents")),
        ("location_count", ("location_count", "locations")),
        ("output_artifacts", ("output_artifacts", "outputs")),
        ("missing_reproducibility_fields", ("missing_reproducibility_fields",)),
    ]
    preview: dict[str, Any] = {}
    for label, aliases in fields:
        value = _pick(data, *aliases)
        if value not in (None, "", [], {}):
            preview[label] = value
    scale_fields = [
        ("time_step_minutes", ("time_step_minutes", "time_granularity", "step_minutes")),
        ("rounds_per_branch", ("rounds_per_branch", "steps_per_branch", "simulation_steps")),
        ("agents_per_branch", ("agents_per_branch", "agent_count")),
        ("locations", ("locations", "location_count")),
    ]
    for label, aliases in scale_fields:
        value = _pick(scale_data, *aliases)
        if value not in (None, "", [], {}):
            preview[label] = value
    return preview


def _branch_timeline(
    branch: Mapping[str, Any],
    interventions: list[Mapping[str, Any]],
    scale: Mapping[str, Any],
) -> list[tuple[str, str, str]]:
    starts_at = str(_pick(scale, "starts_at", default="Day 1, 08:00"))
    ends_at = str(_pick(scale, "ends_at", default="Day 6, 08:00"))
    baseline = str(_pick(branch, "baseline", default="继承共同基线"))
    items: list[tuple[str, str, str]] = [(starts_at, "共享基线", baseline)]
    for value in interventions:
        time = _pick(
            value,
            "time",
            "day",
            "global_time",
            "start_time",
            "event_time",
            default="归档时间",
        )
        title = _pick(value, "title", "name", "intervention_type", "type", default="事件")
        detail = _pick(value, "detail", "content", "description", default="")
        items.append((str(time), _intervention_label(str(title)), _display_value(detail)))
    if not interventions:
        items.append(("Day 1—6", "自然发展", "不追加技术或政策事件，保留 Agent 自主行动轨迹"))
    items.append((ends_at, "运行归档", "冻结事件、状态与编码口径，进入跨情景描述性比较"))
    return items


def _branch_label(branch: Any, index: int) -> str:
    data = _as_mapping(branch)
    return str(_pick(data, "label", "name", "branch_id", "id", default=f"分支 {index + 1}"))


def _joined_intervention_value(
    interventions: list[Mapping[str, Any]],
    field: str,
    *,
    fallback: str,
) -> str:
    values = [_display_value(item[field]) for item in interventions if item.get(field) not in (None, "", [])]
    return " / ".join(dict.fromkeys(values)) or fallback


def _collect_interventions(branches: list[Any], selected: Any) -> list[Mapping[str, Any]]:
    """Collect inherited interventions from the baseline branch to selection."""
    by_id = {
        str(_pick(_as_mapping(branch), "id", "branch_id")): branch
        for branch in branches
        if _pick(_as_mapping(branch), "id", "branch_id")
    }
    lineage: list[Any] = []
    seen: set[str] = set()
    current = selected
    while current is not None:
        data = _as_mapping(current)
        current_id = str(_pick(data, "id", "branch_id", default=""))
        if current_id and current_id in seen:
            break
        if current_id:
            seen.add(current_id)
        lineage.append(current)
        parent_id = _pick(data, "parent_id", "parent")
        current = by_id.get(str(parent_id)) if parent_id else None

    collected: list[Mapping[str, Any]] = []
    for branch in reversed(lineage):
        data = _as_mapping(branch)
        collected.extend(
            _as_mapping(item)
            for item in _as_sequence(_pick(data, "interventions", default=[]))
        )
    return collected


def _intervention_label(value: str) -> str:
    return {
        "technology_exposure": "技术曝光",
        "policy_encouragement": "鼓励政策",
        "policy_restriction": "限制 / 混合政策",
    }.get(value, value)


def _lookup(obj: Any, *names: str, default: Any = None) -> Any:
    data = _as_mapping(obj)
    return _pick(data, *names, default=default)


def _pick(data: Mapping[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in data and data[name] is not None:
            return data[name]
    return default


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="json")
    if hasattr(value, "__dict__"):
        return vars(value)
    return {}


def _as_sequence(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _display_value(value: Any) -> str:
    if isinstance(value, (list, tuple, set)):
        return "、".join(str(item) for item in value)
    if isinstance(value, Mapping):
        return "、".join(f"{key}: {item}" for key, item in value.items())
    return str(value)


def _escape(value: Any) -> str:
    from html import escape

    return escape(str(value))
