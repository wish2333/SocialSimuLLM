## 项目介绍

SocialSimuLLM 是一个基于大语言模型的多智能体社会仿真框架，基于生成式智能体架构（Park et al. 2023）。本项目旨在模拟社会互动和智能体行为，提供一个配置可复现、过程可追溯且可分析的研究平台，用于探索各种社会场景。

## 功能特性

- **模块化架构**: 仿真引擎、智能体认知、记忆系统、反思机制、世界建模和目标规划清晰分离
- **结构化记忆系统**: `MemoryEntry` 不可变数据类，支持多维度检索（语义、时间、空间、重要性）
- **多层次反思**: 每日总结、跨天模式识别、社交关系分析，带冷却节流机制
- **智能体交互**: 智能体可感知周围人的行动并产生自然对话（基于 `InteractionCoordinator` 协调，FOV 可见性过滤，双向记忆存储）
- **空间世界建模**: `WorldVariationGenerator` 支持多种图拓扑（环形、小世界、网格、随机、无标度）
- **近距感知**: 基于图距离的 `FieldOfView` 实现真实的智能体感知
- **智能路径规划**: LLM 驱动的移动意图推断 + A* 最短路径 + 多跳遍历
- **目标驱动规划**: 层次化目标管理与递归任务分解（ROMA 风格）
- **有时限事件**: 全局事件支持基于 step 的时间窗口（`start_step`/`end_step`）与生命周期日志（`global_event_started`/`global_event_ended`），按位置精确投放
- **自然语言场景构建**: 从自然语言描述生成完整的仿真配置
- **可追溯实验**: Pydantic 配置快照、JSONL 结构化日志、检查点和随机种子管理；不承诺随机 LLM 输出逐字一致
- **批量实验**: 使用不同随机种子运行多次实验，支持统计分析
- **Web 界面**: Streamlit 前端，支持实验配置、回放可视化、热力图和 AI 研究助手
- **Jupyter 笔记本**: 行为分析、空间分析和对比研究的即用型分析模板
- **OpenAI 兼容**: 支持任何 OpenAI 兼容的 API 端点（可自定义 base URL 和模型）；DeepSeek V4 JSON 输出模式与结构化重试

## 项目结构

```
SocialSimuLLM/
├── pyproject.toml                     # 项目配置与依赖管理
├── src/socialsimullm/                 # 源代码包
│   ├── __main__.py                    # CLI 入口（子命令分发）
│   ├── agents/                        # 智能体行为与记忆
│   │   ├── agent.py                   # Agent 类
│   │   ├── memory.py                  # AgentMemory: 统一存储与检索
│   │   ├── memory_entry.py            # MemoryEntry 数据类
│   │   └── reflection.py              # ReflectionEngine 反思引擎
│   ├── simulator/                     # 仿真引擎
│   │   ├── core.py                    # SimulatorCore
│   │   ├── state.py                   # SimulationState
│   │   └── events.py                  # EventBus
│   ├── world/                         # 空间世界建模
│   │   ├── spatial.py                 # WorldVariationGenerator（多拓扑）
│   │   ├── field_of_view.py           # FieldOfView（近距感知）
│   │   └── path_planner.py            # PathPlanner（LLM + A*）
│   ├── cognition/                     # 认知模块
│   │   └── goal.py                    # GoalManager + 递归任务分解
│   ├── experiment/                    # 实验基础设施
│   │   ├── config.py                  # ExperimentConfig (Pydantic)
│   │   ├── runner.py                  # ExperimentRunner
│   │   ├── storage.py                 # 运行目录管理与检查点
│   │   ├── analysis.py                # 结果加载与分析
│   │   ├── scenario.py                # ScenarioGenerator（自然语言 -> 城镇数据）
│   │   └── assistant.py               # ResearchAssistant（AI 分析）
│   ├── frontend/                      # Streamlit Web 界面（可选依赖）
│   │   ├── app.py                     # 主入口（三标签页）
│   │   ├── pages/                     # 配置页、结果页、助手页
│   │   └── components/                # 表单、可视化、回放、热力图
│   ├── notebooks/                     # Jupyter 分析模板
│   │   └── data_loader.py             # 共享数据加载工具
│   ├── locations/                     # 空间世界管理
│   ├── prompt_templates/              # LLM 提示词模板
│   ├── utils/                         # 配置、日志、LLM API
│   └── data/                          # 模板数据文件
├── projects/                          # 传统模式模拟输出
├── runs/                              # 实验模式输出（gitignored）
└── docs/                              # 文档
```

## 环境设置

1. **安装依赖项：** 使用 [uv](https://docs.astral.sh/uv/) 进行依赖管理：

   ```bash
   uv sync
   ```

   安装可选依赖（Web 界面 / 分析功能）：

   ```bash
   uv sync --extra frontend   # Streamlit + pyvis + plotly + pandas
   uv sync --extra analysis   # pandas + plotly
   ```

2. **配置 LLM API 密钥：**

   设置环境变量（推荐）：

   ```bash
   export OPENAI_API_KEY="your-api-key"
   export OPENAI_BASE_URL="https://your-endpoint/v1"  # 可选
   ```

## 运行模拟

### 传统模式（单次运行）

```bash
uv run socialsimullm --project my_town --steps 288 --model deepseek-chat
```

### 实验模式（配置可复现）

```bash
# 单次实验
uv run socialsimullm run --config config.yaml --id exp001

# 批量实验
uv run socialsimullm batch --config config.yaml --seeds 42,43,44

# 查看实验列表
uv run socialsimullm list
```

### Web 界面

```bash
uv run streamlit run src/socialsimullm/frontend/app.py
```

### CLI 参数

**传统模式：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--project` | （交互输入） | 项目名称 |
| `--steps` | 144 | 模拟步数（1 步 = 10 分钟） |
| `--model` | 配置默认值 | LLM 模型名称 |
| `--checkpoint-interval` | 10 | 检查点保存间隔 |
| `--no-reflection` | （关闭） | 禁用反思系统 |
| `--reflection-threshold` | 15 | 触发反思的重要性阈值 |

**实验模式：**

| 命令 | 说明 |
|------|------|
| `run --config <yaml>` | 运行单次实验 |
| `run --config <yaml> --id <id>` | 使用自定义实验 ID 运行 |
| `batch --config <yaml> --seeds 42,43` | 使用多个种子批量运行 |
| `list` | 列出所有实验 |

### 实验配置 YAML

```yaml
experiment_id: exp_test_001
project: my_project
model: gpt-4o-mini
embedding_model: BAAI/bge-m3
simulation_steps: 144
memory_limit: 10
random_seed: 42
checkpoint_interval: 10
events:
  - "一场奇怪的雾气笼罩了小镇。"
reflection_enabled: true

# 仅影响 recall_semantic 的候选阈值和三项评分权重
memory_config:
  similarity_weight: 0.5
  recency_weight: 0.3
  importance_weight: 0.2
  importance_threshold: 6

# Phase 3: 空间拓扑
spatial_config:
  topology: small_world
  num_locations: 6
  seed: 42

# Phase 3: 近距感知
fov_enabled: true
fov_distance: 1

# Phase 3: 智能移动
path_planner_enabled: true
multi_hop_movement: true

# Phase 3: 目标驱动规划
goal_enabled: true
max_active_goals: 5
```

### 实验可复现性与配置边界

- 相同 YAML、输入数据和随机种子可以复现实验配置与运行条件，并通过 JSONL、检查点和模型调用元数据追踪过程。
- LLM 服务端模型版本、采样和供应商实现可能变化，因此不保证两次运行的自然语言输出或最终状态逐字一致。
- `memory_config` 只影响 `AgentMemory.recall_semantic()`：三项权重用于语义相似度、时近性和重要性评分，`importance_threshold` 控制进入语义召回候选集的 thought 记忆。它不改变最近记忆、时间、位置、过滤检索或记忆容量。
- `budget_limit` 当前是保留字段，尚未执行费用估算、调用阻断或预算告警，不应将其视为有效的成本上限。

## 输出结构

**传统模式：**
```
projects/{project_name}/
├── town_data.json              # 城镇配置
├── simulation_log.txt          # 文本日志
├── events.jsonl                # 结构化 JSONL 事件日志
├── model_calls.jsonl           # 不含提示词与密钥的模型调用元数据
├── run_metadata.json           # 版本、配置摘要、模板指纹与起止时间
├── done.flag                   # 完成标记
├── checkpoints/                # 状态快照
└── agent_data/                 # 智能体记忆文件
```

**实验模式：**
```
runs/{project}/{experiment_id}/
├── config.yaml                # 完整实验配置快照
├── town_data.json             # 城镇配置副本
├── events.jsonl               # 结构化 JSONL 事件日志
├── model_calls.jsonl          # 不含提示词与密钥的模型调用元数据
├── run_metadata.json          # 版本、配置摘要、模板指纹与起止时间
├── done.flag                  # 完成标记
├── checkpoints/               # 状态快照
└── agent_data/                # 智能体记忆文件
```

## 自定义

1. **城镇数据**: 生成 project 后修改 `projects/<name>/town_data.json` 或在实验配置中设置 `spatial_graph_path`
2. **智能体行为**: 修改 `src/socialsimullm/agents/` 目录下的文件
3. **提示词模板**: 编辑 `src/socialsimullm/prompt_templates/template_agents.py`
4. **LLM 配置**: 设置环境变量或修改 `src/socialsimullm/utils/config.py`
5. **位置管理**: 修改 `src/socialsimullm/locations/locations.py`

## 文档

- [PRD v3.1.0](docs/PRD-3.1.0.md) - 产品需求与升级路线图
- [开发指南](docs/dev_guide.md) - 架构、规范与工作流
- [系统设计](docs/design/system_design.md) - 架构图与数据流
- [模块说明](docs/Module_Description.md) - 各模块 API 参考
- [更新日志](docs/changelog.md) - 版本历史

## 版本历史

- **v3.1.0**: 架构重构、结构化记忆、可追溯实验基础设施（含模型调用元数据）、反思系统（带冷却节流）、智能体交互与协调（`InteractionCoordinator` + FOV 可见性）、有时限事件系统（基于 step 窗口 + 生命周期日志）、Streamlit 前端、空间世界建模、目标驱动规划、AI 研究助手、DeepSeek V4 JSON 输出模式与结构化重试
- **v3.0**: 增强智能体记忆和反思能力
- **v2.0**: 优化记忆检索、改进 Agent 状态评估、数据库交互基础

## 作者和引用

黄淼森 Huang Miaosen

## 致谢

- [mkturkcan/generative-agents](https://github.com/mkturkcan/generative-agents) - 部分代码来源，已在 License 文件夹中附上 License
- [joonspk-research/generative_agents](https://github.com/joonspk-research/generative_agents) - 仅根据论文做思路参考，并未 Copy 代码
