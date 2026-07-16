"""System validation console for the four-person Phandalin paper environment."""

from __future__ import annotations

from collections.abc import Mapping
from html import escape
from typing import Any

import streamlit as st

from socialsimullm.showcase.content import PAPER_TOWN_VALIDATION
from socialsimullm.showcase.loader import ShowcaseDemo


def render_system_validation(demo: ShowcaseDemo) -> None:
    """Present the paper's town validation before the formal campus design."""
    paper = PAPER_TOWN_VALIDATION
    manifest = demo.manifest

    st.markdown('<p class="archive-kicker">SYSTEM VALIDATION / PAPER TOWN</p>', unsafe_allow_html=True)
    st.title("系统验证：四人小镇行为基线")
    st.caption(
        "本页只使用论文中的 Phandalin 四人、四地点环境，验证 Generative Agents 的行为趋势；"
        "校园十 Agent / 十地点正式实验仍在后面的实验设计与结果分析中。"
    )

    metrics = st.columns(4)
    for column, (label, value) in zip(
        metrics,
        [
            ("角色", len(manifest.agents)),
            ("地点", len(manifest.locations)),
            ("论文运行轮次", paper["rounds"]),
            ("论文来源", "PDF"),
        ],
    ):
        column.metric(label, value)

    st.markdown("### 论文小镇的角色—地点—行为链")
    st.caption(
        f"论文记录约一日、{paper['rounds']} 轮运行；以下是论文对四名角色的行为分工归纳，不是当前模型重新运行的结果。"
    )
    columns = st.columns(2, gap="medium")
    for index, (agent, behavior, identity) in enumerate(paper["roles"]):
        location = next(
            (
                _field(item, "starting_location", default="未记录")
                for item in manifest.agents
                if _field(item, "name") == agent
            ),
            "未记录",
        )
        with columns[index % 2]:
            st.markdown(
                '<div class="design-card"><small>PAPER ROLE / '
                f'{escape(str(location))}</small><h4>{escape(agent)}</h4>'
                f'<p><b>{escape(behavior)}</b></p>'
                f'<span>{escape(identity)}</span></div>',
                unsafe_allow_html=True,
            )

    st.markdown("### 论文归纳出的稳定趋势")
    trend_columns = st.columns(3, gap="medium")
    trends = [
        ("角色专门化", "四名角色围绕自身身份、兴趣和地点形成差异化行动，而不是共享同一套行为脚本。"),
        ("社会协调", "交易站、果园与交易所之间出现供应、待客、信息与财务等互补性分工。"),
        ("制度化秩序", "重复的角色分工与互动逐步形成可识别的地方性社会秩序，为后续扩散研究提供基线。"),
    ]
    for column, (title, detail) in zip(trend_columns, trends):
        with column:
            st.markdown(f"#### {title}")
            st.write(detail)

    st.markdown("### 行为、记忆、反思：从论文基线到新增能力")
    for row in feature_validation_rows():
        st.markdown(
            '<div class="branch-track"><b>'
            f'{escape(row["feature"])} · {escape(row["status"])}</b><br>'
            f'<span>{escape(row["paper_evidence"])} → {escape(row["extension"])}</span><br>'
            f'<small>边界：{escape(row["boundary"])}</small></div>',
            unsafe_allow_html=True,
        )

    st.markdown("### 对研究问题的增量价值")
    values = [
        ("RQ1 · 哪些因素影响扩散？", "四人小镇先验证身份、兴趣与场景约束能够产生异质行为；校园实验再加入技术、组织与政策变量。"),
        ("RQ2 · 能否模拟扩散过程？", "计划、感知、行动、记忆与反思构成可解释的过程链，论文小镇提供最小行为基线。"),
        ("RQ3 · 能否识别关键因素？", "四人环境用于检查角色机制是否出现，正式分支和结构化日志再承担阶段比较与因素编码。"),
        ("RQ4 · 如何突破互动边界？", "小镇中的社会协调说明互动不止是单轮对话；记忆与反思扩展后可继续检验网络和政策耦合。"),
    ]
    value_columns = st.columns(2, gap="medium")
    for index, (title, detail) in enumerate(values):
        with value_columns[index % 2]:
            st.markdown(f"#### {title}")
            st.write(detail)

    with st.expander("来源与验证边界", expanded=True):
        st.warning(
            "本页不加载本地十步快照，也不把论文中的定性归纳写成新的统计结果。"
            "论文小镇验证是行为趋势与过程结构验证，不是人类效度检验或因果证明。"
        )
        st.write(f'{paper["source"]}；论文结论：{paper["finding"]}')
        st.caption("校园正式实验数据入口：实验设计 → 结果分析；本页只保留四人小镇验证。")
        st.code(
            "showcase/research/t7_phandalin/manifest.yaml\n"
            "showcase/research/campus_ivmodel/case.yaml\n"
            "src/socialsimullm/agents/memory.py\n"
            "src/socialsimullm/agents/reflection.py"
        )


def feature_validation_rows() -> list[dict[str, str]]:
    """Separate four-person paper evidence from current engineering claims."""
    return [
        {
            "feature": "行为",
            "status": "论文基线已验证",
            "paper_evidence": "四人角色围绕身份、兴趣和地点形成稳定分工",
            "extension": "结构化 AgentAction、互动协调、路径与定时事件可扩展到校园分支",
            "boundary": "论文归纳是定性基线，不等于大规模统计效度",
        },
        {
            "feature": "记忆",
            "status": "机制可解释",
            "paper_evidence": "论文小镇采用计划、感知、记忆写回与检索链路维持角色连续性",
            "extension": "当前 AgentMemory 增加相关性、时间性、重要度检索与 checkpoint 持久化",
            "boundary": "论文未提供统一的记忆质量标注或跨运行对照",
        },
        {
            "feature": "反思",
            "status": "当前能力探针",
            "paper_evidence": "论文小镇验证重点是行为趋势，未单独报告反思稳定性统计",
            "extension": "ReflectionEngine 提供日程、模式、社交触发与阈值 / 冷却控制",
            "boundary": "反思稳定性来自当前代码路径与离线测试，不冒充论文观测结果",
        },
        {
            "feature": "延展性",
            "status": "从最小环境扩展",
            "paper_evidence": "四人、四地点环境已呈现角色分工与社会协调",
            "extension": "配置化 Agent、场景、事件、分支与标准日志支持更大规模研究",
            "boundary": "校园正式实验的 10 Agent / 10 地点数据不在本页重复展示",
        },
    ]


def _field(value: Any, name: str, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)
