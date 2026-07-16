"""System validation console for the archived Generative Agents baseline."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from html import escape
from typing import Any

import streamlit as st

from socialsimullm.showcase.content import T7_PAPER_VALIDATION
from socialsimullm.showcase.loader import ShowcaseDemo


def render_system_validation(demo: ShowcaseDemo) -> None:
    """Show baseline trend reproduction before the formal research design."""
    snapshot = validation_snapshot(demo)
    paper = T7_PAPER_VALIDATION

    st.markdown('<p class="archive-kicker">SYSTEM VALIDATION / BASELINE REPLAY</p>', unsafe_allow_html=True)
    st.title("系统验证：从 Generative Agents 基线到研究平台")
    st.caption(
        "先验证系统能否稳定复现角色—地点—计划—行动链路，再进入校园创新扩散的正式实验设计。"
        "这里展示的是只读证据，不会启动模型或改写归档。"
    )

    st.markdown("### 两层证据，避免把基线与扩展混在一起")
    left, right = st.columns(2, gap="medium")
    with left:
        st.markdown(
            '<div class="design-card"><small>LEGACY BASELINE / T7</small>'
            '<h4>Phandalin 十轮离线快照</h4>'
            f'<p>当前展示包来自 <b>{escape(str(snapshot["source"]))}</b>，包含 '
            f'{snapshot["agents"]} 名角色、{snapshot["locations"]} 个地点、'
            f'{snapshot["steps"]} 个观察点和 {snapshot["events"]} 条标准化事件。</p>'
            '<p>它回答：原有 Generative Agents 行为趋势能否被稳定回放？</p></div>',
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            '<div class="design-card"><small>PAPER VALIDATION / REPORTED RUN</small>'
            '<h4>论文中的小镇前测</h4>'
            f'<p>论文记录了 {paper["agents"]} 名角色、{paper["locations"]} 个地点、'
            f'{paper["rounds"]} 轮运行（{paper["source"]}）。</p>'
            f'<p>{escape(paper["finding"])}</p>'
            '<p>这组结果是论文叙事中的前测依据，不等同于左侧的迁移快照。</p></div>',
            unsafe_allow_html=True,
        )

    metrics = st.columns(5)
    for column, (label, value) in zip(
        metrics,
        [
            ("角色", snapshot["agents"]),
            ("地点", snapshot["locations"]),
            ("离线观察点", snapshot["steps"]),
            ("结构化事件", snapshot["events"]),
            ("动作事件", snapshot["action_events"]),
        ],
    ):
        column.metric(label, value)

    st.markdown("### 行为趋势：角色身份留下可观察的惯性")
    st.caption(
        "每名角色在十个观察点中均有 10 条 action；趋势来自当前快照的结构化记录，"
        "不是对所有可能运行的统计推断。"
    )
    role_columns = st.columns(2, gap="medium")
    for index, row in enumerate(role_trend_rows(demo)):
        with role_columns[index % 2]:
            st.markdown(
                '<div class="design-card"><small>ROLE TREND / '
                f'{escape(row["location"])}</small><h4>{escape(row["agent"])}</h4>'
                f'<p><b>{escape(row["trend"])}</b></p>'
                f'<p>{row["actions"]} 条动作 · 代表记录：{escape(row["example"])}</p></div>',
                unsafe_allow_html=True,
            )

    st.markdown("### 论文前测中的角色分工")
    st.caption("论文 78 轮小镇运行对同一组角色的定性归纳；与上方十轮快照的动作计数分开阅读。")
    paper_columns = st.columns(2, gap="medium")
    for index, (agent, behavior, identity) in enumerate(paper["roles"]):
        with paper_columns[index % 2]:
            st.markdown(
                '<div class="design-card"><small>PAPER ROLE OBSERVATION</small>'
                f'<h4>{escape(agent)}</h4><p><b>{escape(behavior)}</b></p>'
                f'<span>{escape(identity)}</span></div>',
                unsafe_allow_html=True,
            )

    st.markdown("### 事件链路的稳定性")
    chain_columns = st.columns(4)
    chain = [
        ("daily_plan", "日计划", "step 1 · 每名角色 1 条"),
        ("hourly_plan", "时计划", "step 1 / 7 · 每名角色 2 条"),
        ("action", "行动", "step 1—10 · 每名角色 10 条"),
        ("impression", "印象", "step 1 / 7 · 每名角色 2 条"),
    ]
    for column, (event_type, label, detail) in zip(chain_columns, chain):
        column.metric(label, snapshot["event_types"].get(event_type, 0))
        column.caption(detail)

    st.markdown("### 记忆条目随时间增长")
    st.caption("四名角色的 checkpoint 结构保持对称；这证明记录链可持续写回，但不等于记忆质量已被人类标注。")
    memory_columns = st.columns(3)
    memory_counts = memory_progression(demo)
    for column, (step, label) in zip(memory_columns, [(1, "STEP 1"), (7, "STEP 7"), (10, "STEP 10")]):
        value = memory_counts.get(step, "—")
        column.metric(label, value)
        column.caption("条 / 角色")

    st.markdown("### 新增能力：从基线可回放到研究可解释")
    st.caption(
        "下表把‘旧快照已经观测到的东西’与‘当前系统新增、可通过离线探针与单元测试验证的能力’分开。"
    )
    for row in feature_validation_rows(demo):
        status = row["status"]
        st.markdown(
            '<div class="branch-track"><b>'
            f'{escape(row["feature"])} · {escape(status)}</b><br>'
            f'<span>{escape(row["baseline"])} → {escape(row["extension"])}</span><br>'
            f'<small>证据：{escape(row["evidence"])}</small></div>',
            unsafe_allow_html=True,
        )

    st.markdown("### 对研究问题的增量价值")
    value_columns = st.columns(2, gap="medium")
    values = [
        ("RQ1 · 哪些因素影响扩散？", "基线先证明身份、兴趣和场景约束能产生异质行为；校园案例再加入技术属性、组织条件和政策事件。"),
        ("RQ2 · 能否模拟扩散过程？", "计划—行动—印象链路提供过程观测，结构化记忆与检查点让试用、讨论和持续行动可被追踪。"),
        ("RQ3 · 能否识别关键因素？", "事件、记忆和分支归档支持统一编码与描述性比较；它们是机制证据，不替代因果识别。"),
        ("RQ4 · 如何突破互动边界？", "小镇基线已呈现角色分工与社会协调；加入对话、反思和可控介入后，才能检验网络与政策耦合。"),
    ]
    for index, (title, detail) in enumerate(values):
        with value_columns[index % 2]:
            st.markdown(f"#### {title}")
            st.write(detail)

    with st.expander("验证边界与可复现说明", expanded=True):
        st.warning(
            "t7 是定性、过程导向的系统验证，不是人类行为效度检验，也不是统计因果证明。"
            "旧快照没有可靠 reflection、对话、跨地点移动或全局事件字段；页面不把这些缺失伪装成已观测结果。"
        )
        st.write(
            "论文报告的 78 轮小镇前测用于说明行为趋势；当前 bundle 的 10 个 checkpoint 用于可重复回放。"
            "新增记忆、反思、事件和检查点能力的稳定性来自当前代码路径与离线测试，后续正式实验再用校园档案检验其研究解释力。"
        )
        st.caption("旧快照的地点评分还存在 Toblen 全部为 1 的异常值，因此不将地点评分作为本页的验证指标。")
        st.code(
            "showcase/demo/default/manifest.yaml\n"
            "showcase/demo/default/events.jsonl\n"
            "showcase/demo/default/checkpoints/step_10/memory_summary.json\n"
            "src/socialsimullm/agents/memory.py\n"
            "src/socialsimullm/agents/reflection.py\n"
            "src/socialsimullm/experiment/runner.py"
        )


def validation_snapshot(demo: ShowcaseDemo) -> dict[str, Any]:
    """Return deterministic, testable facts for the bundled t7 snapshot."""
    event_types = Counter(str(event.get("event_type", "unknown")) for event in demo.events)
    latest = max(demo.checkpoints, key=lambda item: int(item.get("step", 0)))
    source = getattr(getattr(demo.manifest, "source", None), "source_project", "projects/t7")
    return {
        "source": source,
        "agents": len(demo.manifest.agents),
        "locations": len(demo.manifest.locations),
        "steps": len(demo.manifest.steps),
        "events": len(demo.events),
        "action_events": event_types.get("action", 0),
        "event_types": dict(event_types),
        "latest_step": int(latest.get("step", 0)),
    }


def role_trend_rows(demo: ShowcaseDemo) -> list[dict[str, Any]]:
    """Build role trend cards from the final checkpoint and action log."""
    latest = max(demo.checkpoints, key=lambda item: int(item.get("step", 0)))
    states = {str(item.get("name")): item for item in latest.get("agent_states", [])}
    action_counts = Counter(
        str(event.get("agent_id"))
        for event in demo.events
        if event.get("event_type") == "action" and event.get("agent_id")
    )
    curated_trends = {
        "Daran Edermath": "果园劳作与日常维护",
        "Halia Thornton": "交易账户与趋势整理",
        "Linene Graywind": "开店、陈列与货品整理",
        "Toblen Stonehill": "开店、补货与迎客",
    }
    rows = []
    for agent in ("Daran Edermath", "Halia Thornton", "Linene Graywind", "Toblen Stonehill"):
        state = states.get(agent, {})
        action = str(state.get("action") or state.get("hourly_plan") or "暂无动作记录")
        rows.append(
            {
                "agent": agent,
                "location": str(state.get("location") or "未记录地点"),
                "trend": curated_trends.get(agent, "角色专属行动"),
                "actions": action_counts.get(agent, 0),
                "example": _shorten(action, 108),
            }
        )
    return rows


def feature_validation_rows(demo: ShowcaseDemo) -> list[dict[str, str]]:
    """Describe baseline evidence and current extensions without overclaiming."""
    latest = max(demo.checkpoints, key=lambda item: int(item.get("step", 0)))
    memory = latest.get("memory_summary", {})
    agents = memory.get("agents", {}) if isinstance(memory, Mapping) else {}
    memory_entries = sorted(
        {int(item.get("total_entries", 0)) for item in agents.values() if isinstance(item, Mapping)}
    )
    entry_detail = f"step {latest.get('step')} 每名角色 {memory_entries[-1] if memory_entries else 0} 条记忆摘要"
    return [
        {
            "feature": "行为",
            "status": "稳定回放",
            "baseline": "t7 中身份—地点—日程与 action 趋势一致",
            "extension": "结构化 AgentAction、互动协调、路径与定时事件为后续分支提供可控接口",
            "evidence": "events.jsonl · 每名角色 10 条 action",
        },
        {
            "feature": "记忆",
            "status": "可追踪",
            "baseline": "旧快照保留 plan / action / impression 的记忆摘要",
            "extension": "AgentMemory 支持相关性、时间性、重要度检索，并可持久化到 checkpoint",
            "evidence": f"memory_summary.json · {entry_detail}",
        },
        {
            "feature": "反思",
            "status": "扩展能力探针",
            "baseline": "t7 十轮尚未到反思触发窗口，旧字段为空",
            "extension": "ReflectionEngine 提供日程、模式、社交触发与阈值 / 冷却控制",
            "evidence": "reflection.py · 离线单元测试；不是 t7 观测结果",
        },
        {
            "feature": "延展性",
            "status": "研究就绪",
            "baseline": "快照可按 step 回放，保留来源和迁移边界",
            "extension": "ExperimentConfig、ResearchCase、分支检查点和标准日志支持规模化实验",
            "evidence": "runner.py · case.yaml · checkpoints/",
        },
    ]


def memory_progression(demo: ShowcaseDemo) -> dict[int, str]:
    """Summarize per-agent memory entry counts at canonical checkpoints."""
    progression: dict[int, str] = {}
    for checkpoint in demo.checkpoints:
        step = int(checkpoint.get("step", 0))
        agents = checkpoint.get("memory_summary", {}).get("agents", {})
        values = [
            int(item.get("total_entries", 0))
            for item in agents.values()
            if isinstance(item, Mapping)
        ]
        if values and len(set(values)) == 1:
            progression[step] = f"{values[0]}"
    return progression


def _shorten(value: str, limit: int) -> str:
    compact = " ".join(value.split())
    return compact if len(compact) <= limit else compact[: limit - 1] + "…"
