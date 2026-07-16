"""A focused Agent / harness showcase for technical walkthroughs."""

from __future__ import annotations

from collections.abc import Mapping
from html import escape
from typing import Any

import streamlit as st

from socialsimullm.showcase.content import (
    COLLABORATION_RULES,
    HARNESS_CONTRACTS,
    HARNESS_FAILURE_MODES,
    HARNESS_PIPELINE,
    PAPER_TOWN_VALIDATION,
    PROMPT_LAYERS,
)
from socialsimullm.showcase.loader import ShowcaseDemo


def render_agent_overview() -> None:
    """Render the shortest possible orientation for the new showcase."""
    st.markdown('<p class="archive-kicker">AGENT / HARNESS · 00</p>', unsafe_allow_html=True)
    st.title("Agent / Harness：让 Agent 可控、可验、可协作")
    st.caption("新展示的讲解顺序：先讲 Harness 如何约束 Agent，再讲 Prompt 如何改变实验条件，最后看证据。")

    labels = "　→　".join(item["title"] for item in HARNESS_PIPELINE)
    st.markdown(f'<div class="loop-strip">{labels}</div>', unsafe_allow_html=True)

    metrics = st.columns(4)
    for column, (label, value) in zip(
        metrics,
        [("Harness 阶段", 6), ("记忆类型", 5), ("反思类型", 3), ("仿真步长", "10 分钟")],
    ):
        column.metric(label, value)

    cards = [
        ("先讲结构", "输入契约、状态机、输出校验和失败策略，解释为什么 LLM 行为不会直接穿透系统。"),
        ("再讲实验", "人设、环境、事件和分支是 Prompt 工程；研究者改变条件，不替 Agent 做决定。"),
        ("最后给证据", "四人小镇验证行为基线，校园 GE / NA 归档验证实验变量与阶段差异。"),
    ]
    columns = st.columns(3, gap="medium")
    for column, (title, detail) in zip(columns, cards):
        with column:
            st.markdown(f"#### {title}")
            st.write(detail)

    st.info("建议现场主线：Harness 设计 → 协作协议 → Prompt 实验 → 结果证据。项目总览与技术路线保留在旧展示中，作为需要时的补充。")


def render_harness_design() -> None:
    """Render the implementation-first harness architecture."""
    st.markdown('<p class="archive-kicker">HARNESS ENGINEERING · 01</p>', unsafe_allow_html=True)
    st.title("Harness 设计：把不稳定输出压进稳定边界")
    st.caption("重点不是让模型永远正确，而是让每轮输入、输出、写回和失败都可检查。")

    for row in HARNESS_CONTRACTS:
        st.markdown(
            '<div class="branch-track"><b>'
            f'{escape(row["title"])} · {escape(row["evidence"])}</b><br>'
            f'<span>{escape(row["rule"])}</span><br>'
            f'<small>代码证据 · {escape(row["path"])}</small></div>',
            unsafe_allow_html=True,
        )

    st.markdown("### 核心输出契约")
    st.code(
        '{\n'
        '  "action": "整理货架并接待顾客",\n'
        '  "action_type": "task | talk | move | idle",\n'
        '  "target": "可选的 Agent / 地点",\n'
        '  "utterance": "可选的对话内容",\n'
        '  "continues_task": false\n'
        '}',
        language="json",
    )
    st.caption("LLM 先返回 JSON，再由 AgentAction.from_response() 归一化；后续 MemoryEntry 负责持久化语义。")

    st.markdown("### 主循环里的校验点")
    columns = st.columns(3, gap="medium")
    checks = [
        ("输入", "10 分钟步长、边界时间、可见范围和召回记忆已准备好。", "SimulatorCore.step()"),
        ("执行", "计划、行动、移动、印象和反思按状态机顺序运行。", "SimulatorCore.step()"),
        ("输出", "JSONL、MemoryEntry、checkpoint 和 done 标记可供复核。", "logger.py / storage.py"),
    ]
    for column, (title, detail, path) in zip(columns, checks):
        with column:
            st.markdown(f"#### {title}")
            st.write(detail)
            st.caption(path)

    with st.expander("失败策略：系统如何保持可运行"):
        for title, detail in HARNESS_FAILURE_MODES:
            st.markdown(f"**{title}**")
            st.write(detail)


def render_collaboration_protocol() -> None:
    """Render the multi-agent collaboration contract."""
    st.markdown('<p class="archive-kicker">COLLABORATION CONTRACT · 02</p>', unsafe_allow_html=True)
    st.title("协作协议：Agent 之间如何看到、说话、移动、记住")
    st.caption("协作不是把所有 Agent 状态拼进一个 Prompt，而是由空间、互动和记忆路由共同约束。")

    for row in COLLABORATION_RULES:
        st.markdown(
            '<div class="design-card"><small>PROTOCOL</small>'
            f'<h4>{escape(row["title"])}</h4><p>{escape(row["detail"])}</p>'
            f'<span>证据 · {escape(row["path"])}</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("### 一轮协作时序")
    timeline = [
        ("可见性裁剪", "FOV 生成当前 Agent 可见的邻居和环境上下文"),
        ("行动决定", "AgentAction 标记 task / talk / move / idle"),
        ("互动协调", "Coordinator 限制连续对话、参与者和冷却窗口"),
        ("记忆路由", "行动按 entities 传播，事件广播，计划与反思只写自身"),
    ]
    for index, (title, detail) in enumerate(timeline, start=1):
        st.markdown(
            '<div class="branch-track"><b>'
            f'0{index} · {escape(title)}</b><br><span>{escape(detail)}</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("### 记忆路由矩阵")
    st.dataframe(
        [
            {"事件": "action", "写入对象": "行动者 + entities", "embedding": "summary"},
            {"事件": "plan / thought", "写入对象": "Agent 自身", "embedding": "否"},
            {"事件": "event", "写入对象": "所有 Agent", "embedding": "否"},
            {"事件": "reflection", "写入对象": "Agent 自身", "embedding": "summary"},
        ],
        hide_index=True,
        width="stretch",
    )


def render_prompt_experiment(demo: ShowcaseDemo) -> None:
    """Render prompt-engineering inputs and a read-only branch selector."""
    st.markdown('<p class="archive-kicker">PROMPT ENGINEERING · 03</p>', unsafe_allow_html=True)
    st.title("Prompt 实验：人设、环境与事件如何改变条件")
    st.caption("实验设计改变输入条件和观察窗口，不直接代替 Agent 选择行动。")

    columns = st.columns(2, gap="medium")
    for index, row in enumerate(PROMPT_LAYERS):
        with columns[index % 2]:
            st.markdown(
                '<div class="design-card"><small>PROMPT LAYER</small>'
                f'<h4>{escape(row["layer"])} · {escape(row["question"])}</h4>'
                f'<p>{escape(row["fields"])}</p><span>证据 · {escape(row["path"])}</span></div>',
                unsafe_allow_html=True,
            )

    case = getattr(demo, "research_case", None)
    branches = _items(case, "branches")
    if not branches:
        st.info("当前档案未附可选择的研究分支。")
        return

    st.markdown("### 只读分支探针")
    labels = [str(_field(item, "name", default=f"分支 {index + 1}")) for index, item in enumerate(branches)]
    selected_label = st.selectbox("选择一个实验条件", labels, key="harness_prompt_branch")
    branch = branches[labels.index(selected_label)]
    parent = _field(branch, "parent_id", default="共享基线") or "共享基线"
    st.metric("继承基线", parent)
    interventions = _field(branch, "interventions", default=()) or ()
    if not interventions:
        st.success("自然发展：不追加技术或政策事件，观察 Agent 自主轨迹。")
    for intervention in interventions:
        st.markdown(
            '<div class="branch-track"><b>'
            f'{escape(str(_field(intervention, "global_time", default="归档时间")))} · '
            f'{escape(str(_field(intervention, "intervention_type", default="event")))}</b><br>'
            f'<span>{escape(str(_field(intervention, "content", default="")))}</span><br>'
            f'<small>对象 {_display(_field(intervention, "recipients", default=()))} · '
            f'强度 {_field(intervention, "intensity", default="未记录")} · '
            f'方向 {_field(intervention, "direction", default="neutral")}</small></div>',
            unsafe_allow_html=True,
        )

    with st.expander("Prompt 组装顺序"):
        st.code(
            "system: identity + current event + recent impressions + retrieved memory\n"
            "user: current time + location + visible agents + hourly plan\n"
            "output: JSON_ACTION_SUFFIX -> AgentAction -> MemoryEntry",
            language="text",
        )


def render_evidence(demo: ShowcaseDemo) -> None:
    """Render compact town and campus evidence for the technical story."""
    st.markdown('<p class="archive-kicker">EVIDENCE / HANDOFF · 04</p>', unsafe_allow_html=True)
    st.title("结果证据：Harness 稳定性如何服务实验")
    st.caption("只保留能支撑技术讲解的关键结果；完整社会科学分析仍在旧研究档案中。")

    st.markdown("### 四人小镇：最小行为基线")
    columns = st.columns(4)
    for column, (label, value) in zip(
        columns,
        [("角色", PAPER_TOWN_VALIDATION["agents"]), ("地点", PAPER_TOWN_VALIDATION["locations"]), ("运行", f'{PAPER_TOWN_VALIDATION["rounds"]} 轮'), ("证据", "论文归纳")],
    ):
        column.metric(label, value)
    for agent, behavior, identity in PAPER_TOWN_VALIDATION["roles"]:
        st.markdown(f"**{agent}** · {behavior} · {identity}")

    case = getattr(demo, "research_case", None)
    st.markdown("### 校园实验：结构化归档结果")
    for archive in _items(case, "archives"):
        label = _field(archive, "repository_label", default="归档组")
        metrics = _field(archive, "metrics", default=()) or ()
        summary = "；".join(
            f'{_field(metric, "label", default="指标")} {_field(metric, "numerator", default=0)}/{_field(metric, "denominator", default=0)}'
            for metric in metrics
        )
        st.markdown(
            '<div class="branch-track"><b>'
            f'{escape(str(label))} · {int(_field(archive, "total_actions", default=0)):,} 条主行动</b><br>'
            f'<span>{escape(summary)}</span></div>',
            unsafe_allow_html=True,
        )
    st.info("讲解落点：Harness 让每个行动、记忆、反思和事件都具备可定位的结构；Prompt 实验再改变它们的输入条件。")


def _items(value: Any, name: str) -> list[Any]:
    return list(_field(value, name, default=()) or ())


def _field(value: Any, name: str, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _display(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return "、".join(str(item) for item in value) or "无定向对象"
    return str(value)
