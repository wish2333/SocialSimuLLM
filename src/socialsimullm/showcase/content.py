"""Curated, evidence-linked Chinese copy for the interview showcase."""

from __future__ import annotations

from typing import Final


PROJECT_OVERVIEW: Final = {
    "eyebrow": "SOCIAL SIMULATION / RESEARCH ARCHIVE",
    "title": "把生成式 Agent 变成可追溯的社会仿真实验",
    "question": "当多个拥有设定、记忆与目标的 Agent 共享一个空间时，个体决策如何累积成可观察的群体行为？",
    "positioning": (
        "SocialSimuLLM 是一个面向研究工作流的多智能体社会仿真框架。"
        "它把配置、认知循环、结构化日志、检查点与分析界面串成一条可审计的数据链路。"
    ),
    "responsibilities": [
        "设计并实现 Agent 感知、记忆检索、规划、行动与反思闭环",
        "搭建配置化实验、JSONL 过程日志、检查点和批量运行基础设施",
        "将历史实验迁移为无需模型 API 的只读演示快照",
    ],
    "evidence": [
        ("仿真主循环", "src/socialsimullm/simulator/core.py"),
        ("认知与记忆", "src/socialsimullm/agents/agent.py"),
        ("实验运行器", "src/socialsimullm/experiment/runner.py"),
        ("结构化日志", "src/socialsimullm/utils/logger.py"),
    ],
}


ARCHITECTURE_STAGES: Final = [
    {
        "index": "01",
        "title": "实验输入",
        "summary": "YAML / Pydantic 固化场景、模型、seed 与运行参数。",
        "paths": ["src/socialsimullm/experiment/config.py"],
    },
    {
        "index": "02",
        "title": "运行编排",
        "summary": "ExperimentRunner 创建隔离运行目录，并将配置交给仿真核心。",
        "paths": ["src/socialsimullm/experiment/runner.py"],
    },
    {
        "index": "03",
        "title": "Agent 认知",
        "summary": "每轮完成感知、记忆检索、计划、行动与写回。",
        "paths": ["src/socialsimullm/simulator/core.py", "src/socialsimullm/agents/agent.py"],
    },
    {
        "index": "04",
        "title": "研究证据",
        "summary": "JSONL 保留事件过程，checkpoint 保留可回放状态。",
        "paths": ["src/socialsimullm/utils/logger.py", "src/socialsimullm/experiment/storage.py"],
    },
    {
        "index": "05",
        "title": "分析展示",
        "summary": "分析模块与 Streamlit 只消费标准化输出，不反向修改实验。",
        "paths": ["src/socialsimullm/experiment/analysis.py", "src/socialsimullm/frontend/"],
    },
]


AGENT_LOOP: Final = [
    ("感知", "读取当前位置、邻居与当轮环境上下文。", "src/socialsimullm/world/field_of_view.py"),
    ("记忆检索", "按相关性、时间与重要度召回结构化经历。", "src/socialsimullm/agents/memory.py"),
    ("规划", "把角色设定和当前目标转成日计划与短时计划。", "src/socialsimullm/agents/agent.py"),
    ("行动", "输出结构化决策，并在空间与社会环境中执行。", "src/socialsimullm/agents/agent.py"),
    ("记忆写回", "把行动、观察和印象写回可检索记忆。", "src/socialsimullm/agents/memory_entry.py"),
    ("反思", "达到触发条件后提炼高阶认识，并受冷却机制约束。", "src/socialsimullm/agents/reflection.py"),
]


EVOLUTION: Final = [
    {
        "version": "V1",
        "label": "可运行原型",
        "problem": "先验证多角色、地点、时间推进与模型驱动行动可以闭环。",
        "decision": "采用单体 Python 主循环，快速打通 town data → Agent → 文本日志。",
        "result": "获得可观察的角色日常行为，但实验结构与分析能力有限。",
    },
    {
        "version": "V2",
        "label": "认知模块化",
        "problem": "自由文本状态难以支持稳定检索，也难以解释 Agent 为什么这样行动。",
        "decision": "拆分结构化记忆、目标、规划、感知与反思职责。",
        "result": "单轮决策链有了明确边界，可逐模块调试与复用。",
    },
    {
        "version": "V3.1",
        "label": "研究平台化",
        "problem": "单次运行不足以支撑批量实验、过程追踪和面试现场稳定演示。",
        "decision": "引入 Pydantic 配置、标准运行目录、JSONL、checkpoint 与离线展示契约。",
        "result": "配置输入、运行过程和展示输出形成同一条可核验链路。",
    },
]


METRIC_LABELS: Final = {
    "activity_distribution": "活动分布",
    "location_occupancy": "位置占用",
    "memory_distribution": "记忆分布",
    "interaction_network": "互动关系",
    "innovation_adoption": "创新采纳",
}


def declared_metric_labels(available_metrics: list[str]) -> tuple[tuple[str, str], ...]:
    """Map only manifest-declared metrics to their curated display labels."""
    return tuple(
        (metric, METRIC_LABELS[metric])
        for metric in available_metrics
        if metric in METRIC_LABELS
    )
