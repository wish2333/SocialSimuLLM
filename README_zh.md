## 项目介绍

SocialSimuLLM 是一个基于大语言模型的多智能体社会仿真框架，基于生成式智能体架构（Park et al. 2023）。本项目旨在模拟社会互动和智能体行为，提供一个可复现、可分析的研究平台，用于探索各种社会场景。

## 功能特性

- **模块化架构**: 仿真引擎、智能体认知、记忆系统和反思机制清晰分离
- **结构化记忆系统**: `MemoryEntry` 不可变数据类，支持多维度检索（语义、时间、空间、重要性）
- **多层次反思**: 每日总结、跨天模式识别、社交关系分析
- **可复现实验**: Pydantic 配置模型、JSONL 结构化日志、检查点保存/恢复、随机种子管理
- **批量实验**: 使用不同随机种子运行多次实验，支持统计分析
- **Web 界面**: Streamlit 前端，支持实验配置、启动和结果可视化
- **OpenAI 兼容**: 支持任何 OpenAI 兼容的 API 端点（可自定义 base URL 和模型）

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
│   ├── experiment/                    # 实验基础设施
│   │   ├── config.py                  # ExperimentConfig (Pydantic)
│   │   ├── runner.py                  # ExperimentRunner
│   │   ├── storage.py                 # 运行目录管理与检查点
│   │   └── analysis.py                # 结果加载与分析
│   ├── frontend/                      # Streamlit Web 界面（可选依赖）
│   │   ├── app.py                     # 主入口
│   │   ├── pages/                     # 配置页与结果页
│   │   └── components/                # 表单组件与可视化组件
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

### 实验模式（可复现）

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
```

## 输出结构

**传统模式：**
```
projects/{project_name}/
├── town_data.json              # 城镇配置
├── simulation_log.txt          # 文本日志
├── events.jsonl                # 结构化 JSONL 事件日志
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

- **v3.1.0**: 架构重构、结构化记忆、反思系统、可复现实验、Streamlit 前端
- **v3.0**: 增强智能体记忆和反思能力
- **v2.0**: 优化记忆检索、改进 Agent 状态评估、数据库交互基础

## 作者和引用

黄淼森 Huang Miaosen

## 致谢

- [mkturkcan/generative-agents](https://github.com/mkturkcan/generative-agents) - 部分代码来源，已在 License 文件夹中附上 License
- [joonspk-research/generative_agents](https://github.com/joonspk-research/generative_agents) - 仅根据论文做思路参考，并未 Copy 代码
