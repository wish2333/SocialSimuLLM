# Feedback: Agent / Harness-first showcase

- **Date**: 2026-07-16
- **Source**: user-correction / pattern-observation
- **Context**: 用户完成面试后复盘展示流程，指出概览与技术路线过长，Agent 设计、Agent 协作规范、Harness 逻辑和实验设计需要成为主线；当前版本必须保留，新增另一套展示。
- **User's exact words**: "所以，我觉得后续应该更多侧重放在 Agent 的设计以及实验设计上：1. Agent 设计：属于 harness 工程，以结构化和稳定校验为主。2. 实验设计：属于 prompt 工程，包含事件注入、人设、环境的设计。其中要以 harness 工程为优先，其他部分尽可能地缩减，只要能看懂一个大致的流程就行了。这一版的演示要保留啊，不要直接删掉，我们新建另一套展示。"
- **Impact**: 面试讲解容易被概览和技术路线打断，Agent 的结构化约束与实验输入层次不够突出。
- **Proposed rule**: 展示需要提供 Agent / Harness-first 独立入口，旧研究档案保留；新入口按 Harness → 协作 → Prompt → 结果组织。
