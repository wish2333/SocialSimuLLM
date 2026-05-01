# SocialSimuLLM 研究平台升级方案（综合修订版 V3）

> 本文档是 `reference-3.1.0.md`（V1）经两轮审计后的最终合并版本。
> 整合了后端架构升级方案（V2）与前端可视化方案，经多轮审计修正，
> 聚焦**最小改动最大化研究产出**，严格对齐时间线与接口契约。

---

## 一、核心理念与原则

### 1.1 核心理念

**以个人研究者为中心，以最小改动最大化认知精度与研究产出。**

不追求"融入最前沿技术"，而是优先修复技术债、补强认知内核、建立可复现的实验流程。每一阶段的产出都应直接服务于一篇可发表的研究工作。

### 1.2 现状基线（审计确认）

| 方面 | 现状 | 审计备注 |
|------|------|---------|
| 架构 | 单体，`__main__.py` 279 行承载全部逻辑 | 违反 800 行上限，需拆分 |
| LLM 调用 | `openai` 库 + 自定义 `base_url`，已支持 DeepSeek 等 | 比预期更成熟，无需急于引入 LiteLLM |
| 记忆系统 | SQLite 嵌入存储 + `cosine_distance` 相似度检索 + 优先级评分 | 比原文档"简单向量"描述更完善 |
| 反思系统 | `reflect.py` 仅 26 行 stub | **最紧迫的技术债** |
| 空间表示 | NetworkX 图 + `nx.shortest_path` | 已有基础，升级成本低 |
| 配置系统 | `config.py` 仅 20 行，JSON 文件配置 | 不支持运行时参数覆盖，消融实验受限 |
| memory 模块 | `agents/memory.py` 与 `retrieve/memory.py` 同名 | 职责边界不清，需合并/理清 |
| 检查点/恢复 | 无 | 长时间仿真中断后无法恢复 |
| 日志 | 纯文本输出 | 不便于 Pandas 分析 |
| 并发 | 单线程顺序执行 | 暂不优化，非核心瓶颈 |
| 类型注解 | 大部分缺失 | 违反项目规范 |

### 1.3 设计原则

1. **研究驱动 + 消融实验**：每个阶段定义基线（当前版本）与量化评估指标。
2. **渐进 + 可回滚**：每次只改一个模块，保持主循环可运行。新增检查点/结构化日志支持中断恢复。
3. **技术债优先**：先清理阻碍实验的基础设施问题，再增强认知能力。
4. **多选项路径**：提供保守/平衡/进取三条路径，按个人时间灵活选择。
5. **时间估算诚实**：个人开发者有效时间约为全职的 40-60%，所有估算已乘以 1.5 系数。

### 1.4 多选项路径概览

| 路径 | 总时长 | 目标 | 核心模块 |
|------|--------|------|---------|
| **保守**（推荐） | 3-5 个月 | 产出 1-2 篇工作论文 | 认知内核 + 实验工具 + 基础前端 |
| **平衡** | 5-8 个月 | 系统化研究平台 | 保守 + 空间升级 + 简化规划 |
| **进取** | 8+ 个月 | 探索性研究平台 | 平衡 + NL 场景 + 有限互联 |

---

## 二、整体架构演进

### 2.1 当前架构

```
__main__.py (279行，单体)
  |-- 初始化（配置加载、世界图创建、Agent 初始化）
  |-- 主循环（10分钟步进，顺序调度）
  |     |-- 日计划（08:00）
  |     |-- 小时计划
  |     |-- 行动执行
  |     |-- 地点评分 + 移动
  |     |-- 印象形成
  |     |-- 反思（日末，stub）
  |-- 全局事件处理
  |-- 输出（纯文本日志）
```

### 2.2 目标架构（保守路径终点）

```
socialsimullm/
  __main__.py              # 仅 CLI 入口 + 参数解析
  simulator/
    core.py                # 仿真调度器（时间推进、Agent 生命周期）
    state.py               # SimulationState 持有所有运行时状态
    events.py              # 事件总线（全局事件处理）
  agents/
    agent.py               # Agent 类
    memory.py              # 统一记忆模块（合并 agents/ + retrieve/）
    movement.py            # 移动 + 路径规划
    reflection.py          # 反思系统（完整实现）
    planning.py            # 规划系统（日计划、小时计划、行动）
  cognition/               # 可插拔认知模块（平衡/进取路径）
    memory_store.py        # 结构化记忆存储 + 多维度检索
    goal.py                # 目标驱动规划（平衡路径）
  world/
    spatial.py             # NetworkX 空间图管理
    field_of_view.py       # 视野感知（平衡路径）
    path_planner.py        # LLM 意图 + A* 路径（平衡路径）
  experiment/
    runner.py              # ExperimentRunner（批量运行、种子管理）
    config.py              # ExperimentConfig Pydantic 模型
    checkpoint.py          # 检查点保存/加载 + JSONL 日志
    analysis.py            # 结果收集 + DataFrame 导出
  utils/
    config.py              # 运行时配置（支持参数覆盖）
    text_generation.py     # LLM 调用（保持现有 OpenAI 兼容模式）
    logger.py              # 结构化 JSONL 日志
    global_methods.py      # 通用工具函数
  frontend/                # Streamlit 前端（第二阶段后半）
    app.py
    pages/
    components/
    utils.py
```

### 2.3 架构演进原则

- `__main__.py` 只做 CLI 解析，所有逻辑下沉到 `simulator/`
- `SimulationState` 作为不可变数据对象（dataclass/Pydantic），在模块间传递
- 认知模块通过接口隔离，可独立替换（如不同记忆策略的消融对比）
- `experiment/` 层与仿真核心解耦，通过 `ExperimentConfig` 和检查点文件通信

---

## 三、分阶段实施计划

### 3.1 第一阶段：技术债清理 + 认知内核补强

**时间**：4-6 周（保守路径）
**目标**：系统稳定、可分析、可复现；Agent 形成自我认知，行为连贯性显著提升。

#### 3.1.1 必做（P0，所有路径）

##### A. 重构 `__main__.py`（1 周）

| 当前 | 目标 |
|------|------|
| 初始化 + 主循环 + 全局事件 + 输出，共 279 行 | 拆分为 4 个模块，每个 < 200 行 |

**具体拆分**：
- `simulator/core.py`：`SimulatorCore` 类，包含 `initialize()`、`step()`、`run()` 方法
- `simulator/state.py`：`SimulationState` dataclass，持有世界图、Agent 列表、当前时间
- `simulator/events.py`：`EventBus` 类，全局事件注册与分发（从 `__main__.py` 中提取）
- `utils/logger.py`：`StructuredLogger` 类，JSONL 格式输出 + 检查点保存
- `__main__.py`：仅保留 `argparse` + 调用 `SimulatorCore.run()`

**验收标准**：`uv run socialsimullm` 行为与重构前完全一致。

##### B. 合并/理清 memory 模块（3-4 天）

| 文件 | 当前职责 | 建议归属 |
|------|---------|---------|
| `agents/memory.py` | Agent 侧记忆操作（存储印象、检索近期事件） | 合并到统一 `agents/memory.py` |
| `retrieve/memory.py` | 底层嵌入存储（SQLite、相似度检索） | 降级为内部实现，`agents/memory.py` 对外暴露统一 API |

**统一 API 设计**：
```python
class AgentMemory:
    def store(observation: MemoryEntry) -> None: ...
    def recall_recent(n: int = 10) -> list[MemoryEntry]: ...
    def recall_semantic(query: str, top_k: int = 5) -> list[MemoryEntry]: ...
    def recall_by_location(location_id: str) -> list[MemoryEntry]: ...
    def recall_time_span(start: datetime, end: datetime) -> list[MemoryEntry]: ...
```

**迁移策略**：全新开始（不兼容旧数据），对研究项目更简单。旧 `projects/` 目录保留作为参考。

##### C. 补全反思系统（1.5-2 周，**最高优先级**）

参考 Generative Agents（Park et al. 2023），将 `reflect.py` 从 26 行 stub 扩展为完整实现：

**触发机制**：
- 每日结束时自动触发
- 或当未反思的观察累积重要性分数超过阈值时触发

**反思流程**：

1. 检索近期高重要性观察（`recall_recent` + 重要性过滤）
2. 检索已有的 reflections（避免重复主题）
3. LLM 生成高层 reflection（例如"我似乎偏好安静地点"、"与 X 的互动让我更信任社区"）
4. 将 reflection 作为特殊记忆条目存储（`entry_type="reflection"`）

**验收标准**：Agent 在反思后能引用过去的反思内容指导行为（可通过日志验证）。

##### D. 记忆系统结构化升级（1-1.5 周）

在现有 SQLite 嵌入存储上扩展：

**新增字段**（ALTER TABLE 或重建表）：
- `timestamp`（datetime）：事件发生时间
- `location_id`（str）：事件发生地点
- `event_type`（str）：action / plan / thought / reflection / event
- `entities`（JSON）：涉及的其他 Agent 或实体
- `importance`（int 1-9）：重要性评分
- `reflection_link`（str, nullable）：关联的 reflection ID

**多维度 recall API**：在 B 的统一 API 基础上实现，支持组合过滤。

##### E. 检查点与结构化日志（3-4 天）

- JSONL 格式事件日志：每步写入 `{timestamp, step, agent_id, event_type, data}`
- 检查点：每 N 步（可配置）保存 `SimulationState` 快照到 `runs/{experiment_id}/checkpoints/step_{N}/`
- `done.flag` 文件标记仿真完成

##### F. 配置管理改进（2-3 天）

- 扩展 `config.py`，支持 CLI 参数覆盖（`--model deepseek-chat --steps 144`）
- 添加运行时参数校验
- 为后续 Pydantic `ExperimentConfig` 做铺垫

#### 3.1.2 可选（按路径选择）

| 功能 | 保守 | 平衡 | 进取 |
|------|------|------|------|
| 简单 WorldVariationGenerator | 可选 | 推荐 | 推荐 |
| sqlite-vec 向量扩展 | - | 可选 | 推荐 |
| LiteLLM 初步集成 | - | - | 可选 |

#### 3.1.3 第一阶段产出与评估

**系统产出**：
- 可运行的 vNext，带检查点 + 结构化 JSONL 日志
- 反思系统完整可用
- 记忆系统支持多维度检索

**研究产出**：
- 消融实验：基线（当前版本）vs 结构化记忆 vs +反思
- 评估指标：
  - 行为连贯性（人工评分或 LLM 评分）
  - 记忆利用率（检索命中率、回忆准确率）
  - 习惯形成强度（对特定地点的重复访问率）
  - 反思质量（人工评分：是否形成有意义的自我认知）
- 预期论文主题：**"结构化时空记忆与反思对 Agent 习惯形成与自我一致性的影响"**

---

### 3.2 第二阶段：实验基础设施 + 前端

**时间**：6-10 周（保守路径）
**前置条件**：第一阶段全部完成

#### 3.2.1 前半：ExperimentRunner + 接口契约（3-4 周）

##### A. ExperimentConfig Pydantic 模型

```python
class ExperimentConfig(BaseModel):
    experiment_id: str  # 自动生成或手动指定
    model: str = "deepseek-chat"
    embedding_model: str = "BAAI/bge-m3"
    agent_count: int = 5
    simulation_steps: int = 144  # 1天 = 144个10分钟步
    random_seed: int = 42
    spatial_graph_path: str = "data/town_data_template.json"
    memory_config: MemoryConfig = MemoryConfig()
    checkpoint_interval: int = 10  # 每10步保存
    budget_limit: float = 1.0  # USD
```

##### B. ExperimentRunner

```python
class ExperimentRunner:
    def run_single(config: ExperimentConfig) -> str:
        """运行单次实验，返回 experiment_id"""

    def run_batch(config: ExperimentConfig, seeds: list[int]) -> list[str]:
        """多副本运行（不同随机种子）"""

    def load_results(experiment_id: str) -> pd.DataFrame:
        """加载实验结果为 DataFrame"""
```

##### C. 前后端接口契约

**检查点目录结构**：
```
runs/{experiment_id}/
  config.yaml              # 本次实验完整配置（复现用）
  done.flag                # 仿真完成标记
  events.jsonl             # 全量事件日志
  checkpoints/
    step_{N}/
      spatial_graph.json   # NetworkX 序列化
      agent_states.json    # 所有 Agent 状态快照
      memory_summary.json  # 记忆统计摘要
```

**辅助函数**：
```python
def load_checkpoint(experiment_id: str, step: int | None = None) -> dict: ...
def list_experiments() -> list[dict]: ...
```

##### D. CLI 接口

```bash
uv run socialsimullm run --config experiments/config.yaml --id exp001
uv run socialsimullm batch --config experiments/config.yaml --seeds 42,43,44
uv run socialsimullm list   # 列出所有实验
```

#### 3.2.2 后半：Streamlit 前端 MVP（3-4 周）

**严格 3 个核心功能**：

1. **实验参数配置表单**：从 `ExperimentConfig` Pydantic 模型生成 Streamlit 表单
2. **"运行实验"按钮**：subprocess 启动仿真，文件轮询检查完成状态
3. **结果可视化**：加载检查点 -> pyvis 空间图 + Plotly 基础图表

**不做（第一版）**：实时监控、时间滑块回放、多视图联动、社会交互网络图、报告导出、实验模板库、NL 输入框。

##### 工程实现细节

**subprocess 通信方案**（文件轮询，最简单可靠）：
```
前端点击"运行"
  -> 生成 experiment_id
  -> subprocess.Popen(["uv", "run", "socialsimullm", "run", "--config", path, "--id", eid])
  -> 仿真进程独立运行，写检查点到 runs/{eid}/
  -> 前端 st.session_state 记录 eid + running 状态
  -> time.sleep(30) + st.rerun() 轮询 done.flag
  -> 完成后加载结果渲染
```

**优点**：浏览器关闭后仿真继续；崩溃时可手动查看已有检查点。

**Pydantic -> Streamlit 表单**：
- 优先手写 `st.number_input` / `st.selectbox`（稳定可控）
- `streamlit-pydantic` 作为可选替代（注意：该库维护不稳定，需测试兼容性）

**可视化实现**：
- 空间图：`networkx` -> `pyvis.Network` -> `st.components.v1.html(html, height=600)`
- 图表：`st.plotly_chart()` 显示地点访问频率、Agent 轨迹

**Streamlit 状态管理**：
- `st.session_state` 存储：experiment_id、config、运行状态
- 所有关键逻辑封装在函数中，避免脚本重跑副作用

**前端目录结构**：
```
frontend/
  app.py                # 主入口
  pages/
    1_configure.py      # 实验配置
    2_results.py        # 结果可视化
  components/
    forms.py            # Pydantic 表单映射
    viz.py              # pyvis + plotly 渲染
  utils.py              # 检查点加载、轮询逻辑
```

#### 3.2.3 可选（按路径选择）

| 功能 | 保守 | 平衡 | 进取 |
|------|------|------|------|
| FieldOfView 视野感知 | - | 推荐 | 推荐 |
| PathPlanner（LLM + A*） | - | 推荐 | 推荐 |
| 目标驱动层级规划 | - | 推荐 | 可选 |
| Jupyter 分析模板 | 可选 | 推荐 | 推荐 |

#### 3.2.4 第二阶段产出与评估

**系统产出**：
- `ExperimentRunner` 支持批量运行 + 种子管理
- 结构化检查点 + CLI 接口
- Streamlit 前端 MVP（配置 -> 运行 -> 查看）

**研究产出**：
- 空间影响实验：固定 Agent 组，不同 NetworkX 拓扑变体（全连接/小世界/环形），观察交互频率、移动模式差异
- 环境鲁棒性实验：AI 生成多个空间变体，检验假设在不同环境下的普遍性
- 评估指标：共识形成速度、移动模式熵、路径重复率

---

### 3.3 第三阶段：扩展与探索（进取路径）

**时间**：按需，无固定期限
**前置条件**：第二阶段完成

#### 3.3.1 功能选项

| 功能 | 说明 | 研究价值 |
|------|------|---------|
| NL 场景构建 | `NLScenarioParser`：自然语言 -> 标准 JSON 场景 | 降低实验环境搭建成本 |
| 简化 ROMA 规划 | 目标驱动的简单子步骤分解（非完整递归树） | 多步协调任务中的涌现行为 |
| 轻量文化演化 | Agent 交互后可提议/修改"社会规则"，受群体反馈选择 | 社会规范涌现研究 |
| LiteLLM 全面集成 | 多模型切换 + tool calling | 降低 API 成本 + 外部工具访问 |
| 高级可视化 | 步数选择回放、社会交互网络图、热力图 | 直观展示涌现模式 |
| 半自动研究助手 | 输入研究问题 -> 建议实验设计 -> 运行 -> 初步分析 | 研究效率倍增 |
| A2A/MCP 原型 | 标准化 Agent 间通信或外部工具调用 | 与其他仿真框架互通 |

#### 3.3.2 风险控制

- 每个新模块独立评估研究价值/开发成本比，低收益立即推迟
- NL 生成稳定性通过 self-correction prompt + 校验规则保障
- 演化实验从小规模开始，完整记录种子/版本
- 不追求完美架构，保持每个阶段都可产出研究

---

## 四、技术选型

### 4.1 多选项技术矩阵

| 功能 | 保守（推荐初期） | 平衡 | 进取 |
|------|-----------------|------|------|
| 模型调用 | 当前 OpenAI 兼容 + base_url | + LiteLLM（渐进） | LiteLLM 全量 + tool calling |
| 记忆存储 | 现有 SQLite + 结构化字段 | + sqlite-vec 扩展 | Hindsight/A-MEM 灵感适配 |
| 反思/规划 | Generative Agents 式 reflections | + 目标驱动规划 | 简化 ROMA 探索 |
| 空间 | 现有 NetworkX | + FieldOfView + Planner | 同左 + 动态更新 |
| 实验管理 | CLI + 手动 JSON | Pydantic + YAML + ExperimentRunner | + NL 解析 + 自动分析 |
| 存储日志 | SQLite + JSONL 检查点 | 同左 + 结构化查询 | + MLflow 轻量追踪 |
| 前端 | 无 | Streamlit MVP | 多页面 + 回放 + AI 助手 |
| 可视化 | Matplotlib 静态图 | pyvis + Plotly | 回放 + 多视图联动 |

### 4.2 关键参考资源

| 资源 | 用途 | 备注 |
|------|------|------|
| Generative Agents (Park et al. 2023) | 反思系统设计 | 核心参考，反思是论文主要创新 |
| Hindsight | 结构化记忆组织 | 四网络结构：world facts, agent experiences, entity summaries, evolving beliefs |
| A-MEM | agentic/Zettelkasten 式动态记忆 | 轻量适配，不全盘引入 |
| ROMA (arXiv:2602.01848) | 递归任务分解 | 仅灵感参考，不完整实现 |
| YuLan-OneSim (arXiv:2505.07581) | NL 场景构建 | code-free 场景生成灵感 |
| AgentSociety | 大规模仿真 + 实验方法 | 干预/分析工具参考 |
| sqlite-vec | 轻量 SQLite 向量扩展 | 无额外进程，适合个人项目 |

---

## 五、实验设计

### 5.1 即时可做实验

#### 实验 1：记忆 + 反思消融

- **变量**：基线（当前） / 结构化记忆 / +反思
- **环境**：同一空间图，同一组 Agent
- **指标**：习惯路径重复率、记忆检索命中率、反思质量评分
- **预期发现**：反思使 Agent 行为更一致，结构化记忆使地点偏好更显著

#### 实验 2：空间结构影响

- **变量**：全连接 / 小世界 / 环形 NetworkX 拓扑
- **控制**：同一组 Agent 配置
- **指标**：交互频率、移动路径熵、冲突事件数
- **预期发现**：小世界网络可能产生最丰富的涌现行为

#### 实验 3：环境鲁棒性

- **方法**：WorldVariationGenerator 生成 5-10 个空间变体
- **检验假设**："高密度居住区增加冲突频率"
- **分析**：该假设在多少变体中成立？破坏它的环境特征是什么？

### 5.2 方法论要求

- 每次实验记录：模型 + 版本、全部 prompt 模板、随机种子、环境配置快照
- 做基线对比 + 统计显著性检验（多副本 + 不同种子）
- 用结构化 JSONL 日志自动化分析（Pandas + Plotly）
- 实验结果与检查点一起归档，支持复现

---

## 六、风险与应对

| 风险 | 概率 | 影响 | 应对策略 |
|------|------|------|---------|
| API 调用成本失控 | 中 | 高 | 设单次实验预算上限；缓存高命中记忆回复；优先廉价模型 |
| AI 生成环境逻辑混乱 | 中 | 中 | 校验规则 + LLM self-fix + 人工抽查（初期） |
| 时间不足，模块积压 | 高 | 中 | 每周 review 研究价值密度；低收益模块立即降级或推迟 |
| 实验结果不可复现 | 低 | 高 | 检查点 + 完整 config + JSONL 日志；种子管理 |
| 引入新技术债 | 中 | 中 | 代码审查；文件 < 800 行；类型注解渐进引入 |
| subprocess 管理混乱 | 中 | 低 | 记录 PID 到文件；提供"终止"按钮；前端异常处理 |
| Streamlit 状态丢失 | 中 | 低 | 所有状态进 session_state；关键逻辑封装函数 |
| 旧数据格式不兼容 | 低 | 低 | 全新开始，旧 projects/ 保留参考；不追求向后兼容 |

---

## 七、时间线总览

```
第一阶段（4-6 周）：技术债 + 认知内核
  |-- W1: 重构 __main__.py + 合并 memory 模块
  |-- W2: 检查点 + JSONL 日志 + 配置改进
  |-- W3-4: 补全反思系统
  |-- W5-6: 记忆结构化升级 + recall API + 消融实验
  |-- 产出: vNext + 1 篇工作论文初稿

第二阶段前半（3-4 周）：实验基础设施
  |-- W1: ExperimentConfig Pydantic 模型
  |-- W2: ExperimentRunner + CLI 接口
  |-- W3: 检查点格式标准化 + 辅助函数
  |-- W4: 批量运行测试 + 空间变体实验
  |-- 产出: 可复现的实验流程

第二阶段后半（3-4 周）：Streamlit 前端 MVP
  |-- W1: Streamlit 骨架 + 配置表单
  |-- W2: subprocess 集成 + 文件轮询
  |-- W3: pyvis 空间图 + Plotly 图表
  |-- W4: 测试 + 修复 + 实验验证闭环
  |-- 产出: 研究者可用的操作面板

第三阶段（按需）：扩展与探索
  |-- NL 场景、高级规划、演化、互联...
```

**保守路径总计**：约 4-5 个月（含实验和写作）
**平衡路径总计**：约 6-7 个月
**进取路径总计**：8+ 个月

---

## 八、立即行动

1. **本周**：重构 `__main__.py` -- 拆分为 `simulator/core.py`、`simulator/state.py`、`simulator/events.py`、`utils/logger.py`
2. **下周**：合并 memory 模块 + 添加检查点机制
3. **第三周起**：补全反思系统 -- 这是第一阶段最有研究价值的改动
4. **第五周起**：记忆结构化升级，跑第一个消融实验
5. **验证闭环**：跑一个小实验（3-5 个 Agent，3 天仿真步数），确认新系统端到端可运行
