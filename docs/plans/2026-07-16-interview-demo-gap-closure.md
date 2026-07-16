# SocialSimuLLM 面试演示与履历功能补齐实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在尽量不重构仿真核心的前提下，补齐履历表述与 `dev-3.1.0` 实现之间的关键差距，并交付一个 5–8 分钟可稳定讲解项目设计与仿真结果、无需现场调用模型 API 的 Streamlit 原型。

**Architecture:** 保留现有 `SimulatorCore -> JSONL/checkpoint -> experiment analysis -> Streamlit` 单体数据链路。`projects/` 中的过时项目只作为构造素材，通过离线转换脚本生成符合 v3.1 展示契约的只读 demo 快照，运行时不读取旧项目；项目讲解内容使用显式维护的展示清单。限时事件和嵌入式对话只作为核心循环中的薄协调层接入，检查点恢复复用现有运行目录文件，不重写存储系统。

**Tech Stack:** Python 3.10+、Pydantic 2、Streamlit、Plotly、Pyvis、NetworkX、JSONL/YAML、pytest（新增纯离线测试）。

---

## 1. 审查结论

### 1.1 简历功能核验矩阵

| 简历能力 | 当前状态 | 代码证据与边界 | 结论 |
|---|---|---|---|
| 配置化运行 | 已实现但配置未完全生效 | `experiment/config.py` 有 Pydantic 配置；`memory_config`、`budget_limit` 只定义未消费 | 可保留，但不要宣称所有配置均已闭环 |
| 批量实验 | 已实现 | `ExperimentRunner.run_batch()` 按 seed 串行执行 | 可保留 |
| 结构化日志 | 已实现 | `StructuredLogger` 输出 JSONL 与文本日志 | 可保留 |
| 检查点恢复 | 部分实现 | 能保存和读取展示快照，但没有从 checkpoint 重建完整仿真状态的恢复入口；保存的 memory 只是统计摘要 | 必须补齐或将简历改为“断点状态保存” |
| 实验可复现 | 部分实现 | 保存 YAML 和 seed；LLM 温度、服务端模型版本及调用结果并不确定，seed 主要约束 Python/图生成 | 建议表述为“配置可复现、过程可追溯”，避免“结果完全一致” |
| 规划、行动、结构化记忆、反思 | 已实现 | `Agent`、`AgentMemory`、`ReflectionEngine` 已接入主循环 | 可保留 |
| 邻近感知 | 已实现 | `FieldOfView` 可配置接入 | 可保留 |
| 结构化 JSON、兼容回退 | 已实现 | `GPT_request_json()`，DeepSeek V4 三段回退；非 DeepSeek 单次解析后回退 | 可保留 |
| 冷却节流 | 局部实现 | 仅反思有 `min_cooldown_steps=6`；没有全局模型调用节流或对话冷却 | 简历最好写成“反思冷却”，或按本计划补对话冷却 |
| 嵌入式对话 | 未形成机制 | 提示词允许“conversation”，但动作仍是自由文本；无目标、话轮、会话 ID、结束条件和独立日志 | 必须补齐或删去“嵌入式对话”措辞 |
| 限时事件 | 未实现 | `events: list[str]` 仅在初始化时拼接并永久进入 agent context；`EventBus` 未接入核心 | 必须补齐或改成“全局事件注入” |
| 实验配置界面 | 部分实现 | 页面只暴露基础字段，空间/FOV/路径/目标/反思高级配置未完整展示 | 面试原型应提供模板预设而非塞满所有字段 |
| 结果分析 | 已实现基础能力 | 事件计数、DataFrame、跨实验摘要存在；缺少论文核心“创新扩散”指标 | demo 有可靠采纳标签时再增加领域指标，否则展示通用行为指标 |
| 回放、热力图 | 代码存在但当前不可可靠演示 | checkpoint 保存 `agent_states` 为 list；replay/heatmap 按 dict 读取，导致异常或空图 | P0 修复 |
| 研究辅助分析界面 | 代码存在但入口被状态值 bug 阻断 | storage 返回 `completed`，assistant 过滤 `complete` | P0 修复 |
| 前端启动真实实验 | 很可能失败或长时间阻塞 | 使用 `python -m socialsimullm.__main__:main`，模块名写法错误；stdout/stderr PIPE 长运行可能填满 | P0 修复 |
| 上千轮、约 30 天、成本 10–20 元 | 属于实验履历而非代码功能 | 仓库只带 `projects/t7` 的 10 轮样例，未附实验档案或成本证据 | 面试准备中补截图/汇总表，不必改核心 |

### 1.2 当前测试风险

- `tests/test_module.py` 仍导入已删除的 `agents.movement`，测试已过期。
- `tests/test_GPT.py` 直接调用真实 API，不适合作为默认测试，会产生网络依赖和费用风险。
- 项目未声明 pytest 开发依赖，也没有覆盖 runner、storage、前端数据适配与恢复路径。
- 全部源码通过 AST 解析，但这不等于运行链路通过。

## 2. 原型方案比较与决策

### 方案 A：修复并收敛现有 Streamlit（推荐）

复用全部现有页面和图表，增加“面试演示”首页、演示快照和统一的数据适配函数。真实运行保留，但默认演示走离线数据。预计 1–2 天可交付，改动集中且风险最低。

### 方案 B：新增独立 React/Vue 展示站

视觉自由度更高，但需要增加 API 层、前端工程、状态同步和部署链路。即使只做静态原型，也会形成两套 UI，预计至少 3–5 天，不符合“马上要用、最小改动”。

### 方案 C：把 Streamlit 改成实时仿真控制台

加入 WebSocket/后台任务、逐步状态推送、暂停恢复和实时图谱。演示效果最好，但会触及运行器、并发、任务生命周期和错误恢复，预计 5 天以上，现场稳定性反而下降。

**决策（ADR-001）：选择方案 A。** 面试演示默认使用本地快照；真实实验由用户显式点击启动。暂不引入独立后端、消息队列、数据库和新前端框架。

**决策（ADR-002）：旧项目仅用于构造 demo，不作为运行时数据源。** 构建阶段从 `projects/` 提取人物、地点、动作、时间和记忆，将其归一化为当前 JSONL/checkpoint 契约；生成结果提交到独立 demo 目录。转换完成后，删除或移动旧项目都不影响面试原型。

## 3. 面试原型信息架构

前端改为中文优先的六段式叙事：

1. **项目总览**：研究问题、项目定位、本人职责和三项核心数字；先回答“为什么做”。
2. **技术路线**：配置输入、仿真核心、认知模块、实验基础设施、分析展示的数据流；回答“系统怎样工作”。
3. **Agent 设计**：人物设定、感知、记忆检索、规划、行动、反思、事件和对话的单轮决策链；回答“智能体怎样思考与交互”。
4. **工程演进**：V1 原型、V2 重构、V3.1 研究平台的时间线，并展示各阶段解决的问题；回答“独立主导了什么”。
5. **仿真演示**：选择由旧项目数据构造的 demo，展示时间轴、空间图、智能体卡片和事件流；回答“项目是否真的跑起来”。
6. **结果分析**：活动分布、交互关系、位置热力图、回放和 A/B 对比；如 demo 数据确实包含创新扩散标签，再展示采纳率等论文指标，禁止凭关键词虚构结论。

演示脚本：45 秒讲研究问题与职责；60 秒讲技术路线；90 秒讲 Agent 决策闭环；60 秒讲 V1→V3.1 演进；120 秒操作仿真回放；60 秒看分析结果；30 秒说明检查点、JSONL 和批量实验如何保障研究流程。

## 4. 实施顺序

### Task 1（P0，约 1 小时）：建立离线测试护栏

**Files:**
- Create: `tests/unit/test_frontend_adapters.py`
- Create: `tests/unit/test_storage.py`
- Modify: `tests/test_GPT.py`
- Modify: `tests/test_module.py`
- Modify: `pyproject.toml`

**Steps:**

1. 将真实 API 测试标为 `integration`，默认测试不执行；删除已失效的 `agents.movement` 导入。
2. 在 `pyproject.toml` 增加 `dev` 可选依赖与 pytest marker 配置。
3. 写失败测试：list/dict 两种 `agent_states` 都归一化为 `list[dict]`；实验完成状态统一为 `completed`。
4. 运行 `uv run pytest -m "not integration" -q`，预期适配器测试先失败。
5. 完成 Task 2 后重新运行，预期通过。

### Task 2（P0，约 1.5 小时）：修复现有前端断链

**Files:**
- Create: `src/socialsimullm/frontend/adapters.py`
- Modify: `src/socialsimullm/frontend/components/replay.py`
- Modify: `src/socialsimullm/frontend/components/heatmap.py`
- Modify: `src/socialsimullm/frontend/pages/results.py`
- Modify: `src/socialsimullm/frontend/pages/assistant.py`
- Modify: `src/socialsimullm/frontend/utils.py`

**Steps:**

1. 新增 `normalize_agent_states(value) -> list[dict]`，兼容 checkpoint 的 list 与旧版 dict。
2. replay、occupancy heatmap、空间图全部通过该适配器读取，禁止组件各自猜测结构。
3. 将助手页状态判断统一为 `completed`。
4. 将启动命令改为 `python -m socialsimullm run --config ...`。
5. stdout/stderr 写入运行目录日志或重定向到 `DEVNULL`，避免长进程因 PIPE 填满而挂起；保留启动后 2 秒失败检查。
6. 验收：已有 checkpoint 能显示智能体位置，回放不抛 `list has no attribute items`，助手能看到已完成实验。

### Task 3（P0，约 2–3 小时）：用过时项目构造标准化 demo 数据

**Files:**
- Create: `scripts/build_showcase_demo.py`
- Create: `src/socialsimullm/showcase/schema.py`
- Create: `showcase/research/t7_phandalin/manifest.yaml`
- Create: `tests/unit/test_showcase_builder.py`

**Steps:**

1. 定义只读 `ShowcaseManifest` 和 demo 数据契约：项目介绍、来源说明、agent、location、step、event、checkpoint、可用指标列表。
2. 写失败测试：输入 `projects/t7` 旧版 `meta.json`、`town_data.json`、memory JSON 和文本日志后，能生成当前统一的 list 型 `agent_states` 与 JSONL 事件。
3. 论文档案只保留四人小镇的归纳性验证记录；不再输出 `showcase/demo/default/` 十步快照，禁止运行时读取旧项目。
4. 从旧 memory 的 `global_time/location/action/exp_type` 映射为 `step/location/content/event_type`；无法可靠推导的字段设为空并记录 `migration_warnings`，禁止编造。
5. 根据每个时间点最近的 agent memory 构造回放 checkpoint；数据不足时降低 checkpoint 密度，不用插值制造不存在的行动。
6. manifest 记录 `source_project`、构建时间、转换规则版本和免责声明，确保面试时能说明“数据来自旧实验，但展示结构已迁移”。
7. 验收：构建完成后临时改名 `projects/`，demo 仍可独立加载；生成物不含 API key、SQLite DB 或冗余原始日志。

### Task 4（P0，约 3–4 小时）：补齐项目讲解型 Streamlit 原型

**Files:**
- Create: `src/socialsimullm/showcase/content.py`
- Create: `src/socialsimullm/showcase/loader.py`
- Create: `src/socialsimullm/frontend/pages/overview.py`
- Create: `src/socialsimullm/frontend/pages/architecture.py`
- Create: `src/socialsimullm/frontend/pages/agent_design.py`
- Create: `src/socialsimullm/frontend/pages/evolution.py`
- Create: `src/socialsimullm/frontend/pages/demo.py`
- Modify: `src/socialsimullm/frontend/app.py`
- Modify: `src/socialsimullm/frontend/pages/results.py`
- Create: `tests/unit/test_showcase_loader.py`

**Design:**

使用顶部导航或侧边栏组织“总览 / 技术路线 / Agent 设计 / 工程演进 / 仿真演示 / 结果分析”。讲解内容通过 `content.py` 的显式数据结构维护，不在运行时解析 Git 历史或扫描 AST，避免现场环境差异。架构和 Agent 流程优先使用 Streamlit 原生组件、Graphviz 或简单 HTML/CSS 卡片，不加入新的前端构建工具。

**Steps:**

1. 总览页展示研究问题、本人职责、版本范围和有证据支持的规模数据；数字旁标注数据来源。
2. 技术路线页展示 `YAML -> ExperimentRunner -> SimulatorCore -> Agent cognition -> JSONL/checkpoint -> analysis/Streamlit` 数据流，并可展开查看对应模块。
3. Agent 设计页展示“感知→记忆检索→规划→行动→记忆写回→反思”的闭环；每个节点附一段职责和真实文件路径。
4. 工程演进页用 V1/V2/V3.1 时间线说明从可运行原型到研究平台的重构动机、关键决策和结果，不展示无法证实的性能提升百分比。
5. 系统验证页只读取论文四人小镇档案，展示角色分工、社会协调和行为趋势边界。
6. 结果页根据 manifest 的 `available_metrics` 决定显示哪些图；普通旧项目 demo 默认展示活动、交互、位置和记忆分布，不强行展示创新扩散指标。
7. 增加“一键进入演示”入口，启动后默认定位到信息最完整的 step，而不是空的第一帧。
8. 验收：断网、无 API key、无 `.git`、无 `projects/` 时，讲解页与 demo 均能完整运行。

### Task 5（P1，约 3–4 小时）：实现真正的限时事件

**Files:**
- Modify: `src/socialsimullm/experiment/config.py`
- Modify: `src/socialsimullm/simulator/state.py`
- Modify: `src/socialsimullm/simulator/core.py`
- Modify: `src/socialsimullm/agents/memory_entry.py`
- Create: `tests/unit/test_timed_events.py`
- Modify: `examples/with_events.yaml`

**Design:**

新增 `TimedEventConfig`：`id`、`content`、`start_step`、`end_step`、`locations`、`importance`。`events` 同时接受旧字符串和新对象；每个 step 计算 active events，并刷新 `agent.event`。开始与结束各写一条 `global_event_started/global_event_ended` JSONL，避免每轮重复写入记忆。

**Acceptance:**

- 旧 YAML 不变即可运行。
- `start_step <= step <= end_step` 时事件进入 prompt，之后自动移除。
- checkpoint 中保存 active event IDs，恢复后行为一致。

### Task 6（P1，约 4–6 小时）：最小嵌入式对话，不引入阻塞子循环

**Files:**
- Modify: `src/socialsimullm/prompt_templates/template_agents.py`
- Modify: `src/socialsimullm/agents/agent.py`
- Create: `src/socialsimullm/simulator/interactions.py`
- Modify: `src/socialsimullm/simulator/core.py`
- Create: `tests/unit/test_interactions.py`

**Design:**

动作 JSON 从单一 `action` 扩展为兼容字段：`action`、`action_type`（`task|talk|move|idle`）、`target`、`utterance`、`continues_task`。旧模型只返回 `action` 时继续走原逻辑。`InteractionCoordinator` 只负责验证“目标存在且同地/可见”、生成 `conversation_turn` 事件并把发言路由到目标记忆；不启动 while 对话循环。目标在自己的当前轮（若尚未行动）或下一轮自然回复，因此聊天不会阻塞做事。

配置增加 `conversation_max_consecutive_steps=3` 和 `conversation_cooldown_steps=2`。超过连续话轮后提示词提高执行任务优先级；`continues_task=true` 允许“边做边聊”。

**Acceptance:**

- 两个同地智能体可产生带 speaker/target/utterance/conversation_id 的结构化话轮。
- 不同地目标会安全降级为普通动作并记录原因。
- 对话不增加额外嵌套循环，每个智能体每 step 最多仍只有一次主行动调用。
- 连续对话达到上限后至少冷却 2 step。

### Task 7（P1，约 4–5 小时）：让检查点具备恢复语义

**Files:**
- Modify: `src/socialsimullm/utils/logger.py`
- Modify: `src/socialsimullm/experiment/storage.py`
- Modify: `src/socialsimullm/experiment/runner.py`
- Modify: `src/socialsimullm/utils/config.py`
- Modify: `src/socialsimullm/__main__.py`
- Create: `tests/unit/test_checkpoint_resume.py`

**Design:**

checkpoint 除展示快照外，保存 `town_data.json`、完整 `agent_data/`、meta 和运行时状态（active events、recent actions、goals、planned paths、反思冷却 step）。新增显式 `resume --config ... [--step latest]`：先把现有尾部日志归档，再将 checkpoint 原子恢复到运行目录并继续剩余 steps。不要把 `load_checkpoint()` 的展示读取误当成恢复。

**Acceptance:**

- 离线替身模型下连续运行 N step 与运行 K step、恢复、再运行 N-K step 的最终状态一致。
- 恢复不会覆盖配置快照，不会留下错误的 `done.flag`。
- CLI 和前端明确显示“从 step K 恢复”。

### Task 8（P2，约 2 小时）：收紧“可复现”和成本表述

**Files:**
- Modify: `src/socialsimullm/utils/text_generation.py`
- Modify: `src/socialsimullm/utils/logger.py`
- Modify: `src/socialsimullm/experiment/config.py`
- Modify: `README_zh.md`

**Steps:**

1. 每次模型调用记录模型名、重试次数、是否 fallback、token usage（若 API 返回），不记录 prompt 原文或密钥。
2. 运行元数据记录 git commit、配置摘要、prompt 模板版本、开始/结束时间。
3. `budget_limit` 若本期不实现，先从面试配置页隐藏并在文档标记 reserved；不要显示一个无效控制项。
4. `memory_config` 要么接入 `AgentMemory` 权重，要么同样标记 reserved。本次优先接入，改动仅限构造参数与评分公式。
5. README 将“可复现实验”解释为配置和输入可复现，不承诺随机 LLM 输出逐字一致。

## 5. 推荐排期

| 时间 | 交付内容 | 是否可面试演示 |
|---|---|---|
| 第 0 天，6–9 小时 | Task 1–4：修复前端 + 旧数据迁移 + 项目讲解原型 | 是，已足够应急 |
| 第 1 天，7–10 小时 | Task 5–6：限时事件 + 最小对话协调 | 是，简历第二条可完整自证 |
| 第 2 天，4–5 小时 | Task 7：真正 checkpoint resume | 是，简历第一条闭环可信 |
| 第 3 天，2 小时 | Task 8 + 文档/演示彩排 | 是，表达更严谨 |

若只有半天，优先完成 Task 2、Task 3 和 Task 4 的最小子集：修复展示断链、迁移一个旧项目、完成总览/技术路线/Agent 设计/仿真演示四页；同时临时调整简历，将“检查点恢复”改为“检查点保存与回放”，将“嵌入式对话与限时事件机制”改为“交互提示与全局事件注入”。

## 6. 非功能要求与失败处理

- **安全：** 前端和日志不得展示 `.env`、API key、完整模型错误响应中的敏感 header。
- **成本：** 演示模式禁止发起任何模型调用；真实运行按钮需二次提示预计耗时和费用。
- **稳定性：** 所有图表对空事件、损坏 JSONL、缺失 checkpoint 做降级展示。
- **兼容性：** 旧字符串事件、旧版 memory 字段、list/dict checkpoint 均继续支持。
- **可运维性：** 后台进程 PID、启动时间、错误日志路径写入 run metadata；UI 不用固定 5 分钟轮询阻塞页面。
- **范围控制：** 不做登录、多用户、数据库迁移、实时 WebSocket、地图编辑器、云部署。

## 7. 最终验收清单

- `uv run pytest -m "not integration" -q` 全绿，默认不联网。
- 无 API key、断网、无 `.git`、无 `projects/` 环境下可加载已构造的 demo 并完成完整讲解。
- 配置、过程、回放、热力图和 manifest 声明可用的指标均有非空数据；不展示无法由源数据支持的指标。
- 总览、技术路线、Agent 设计、工程演进均能在界面中完成讲解，且引用真实模块与可核验数据。
- 真实实验能从前端成功启动，后台输出不会阻塞。
- 限时事件在到期后不再进入 agent prompt。
- 对话有结构化双方、话轮和结束/冷却语义，且不阻塞主行动。
- checkpoint 能被明确恢复，而不只是被读取展示。
- 简历中的每个技术名词都能在代码、日志或 UI 中指出一处直接证据。
