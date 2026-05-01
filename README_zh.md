## 项目介绍

本项目旨在模拟社会互动和智能体行为，提供一个可定制的框架，用于研究和探索各种社会场景。通过模拟，您可以观察智能体之间的互动，分析行为模式，并深入了解社会动力学。

## 项目结构

```
SocialSimuLLM/
├── pyproject.toml                # 项目配置与依赖管理
├── src/socialsimullm/            # 源代码包
│   ├── __main__.py               # 程序入口
│   ├── agents/                   # 智能体行为与记忆动作
│   ├── locations/                # 位置管理
│   ├── prompt_templates/         # LLM 提示词模板
│   ├── retrieve/                 # 记忆检索与反思
│   ├── utils/                    # 配置、文本生成、辅助工具
│   └── data/                     # 模板数据文件
├── tests/                        # 测试文件
├── projects/                     # 模拟输出数据
└── docs/                         # 文档
```

## 设置环境

1.  **安装依赖项：** 本项目使用 [uv](https://docs.astral.sh/uv/) 进行依赖管理，安装依赖：

    ```bash
    uv sync
    ```

2.  **配置 OpenAI API 密钥：**
    *   准备一个包含 completions 模型的 API。
    *   将您的 OpenAI API 密钥添加到 `src/socialsimullm/utils/config.py` 文件中的 `openai_api_key` 变量。
    *   您还可以根据需要修改 `openai_base_url`、`key_owner` 和 `DefaultModel`。

## 运行模拟

1.  **运行主程序：** 在项目根目录下执行：

    ```bash
    uv run python -m socialsimullm
    ```

    或使用脚本入口：

    ```bash
    uv run socialsimullm
    ```

2.  **输入项目名称：** 程序将提示您输入项目名称。
    -   **注意：** 项目可以沿用继续，但是需要注意增量备份，以防止数据丢失。
3.  **输入重复次数：** 程序将提示您输入模拟的重复次数。

## 模拟存储位置

模拟数据存储在以下位置：

*   **项目目录：** `projects/{project_name}/`，其中 `{project_name}` 是您在运行模拟时输入的项目名称。
*   **模拟日志：** `projects/{project_name}/simulation_log.txt`
*   **模拟摘要：** `projects/{project_name}/simulation_summary.txt`
*   **智能体记忆：** `projects/{project_name}/agent_data/`

## 自定义

您可以按照以下步骤自定义模拟：

1.  **修改城镇数据：** 生成 project 后修改 `projects/<your project name>/town_data.json` 文件以更改城镇数据。
2.  **修改代码：** 修改 `src/socialsimullm/__main__.py` 文件中的代码以更改模拟行为。
3.  **修改配置文件：** 修改 `src/socialsimullm/utils/config.py` 文件中的配置，例如 OpenAI API 密钥和默认模型。
4.  **修改智能体行为：** 修改 `src/socialsimullm/agents/` 目录下的文件以更改智能体的行为管理。
5.  **修改位置：** 修改 `src/socialsimullm/locations/` 目录下的文件以更改模拟世界位置管理。
6.  **修改记忆：** 修改 `src/socialsimullm/retrieve/` 目录下的文件以更改记忆管理。
7.  **修改提示词模板：** 编辑 `src/socialsimullm/prompt_templates/template_agents.py` 以更改智能体与 LLM 的交互方式。

模块说明请参见 [Module_Description.md](/docs/Module_Description.md)

## 更新介绍

V3.1 版本中，项目重构为现代 Python `src` 布局，采用 `pyproject.toml` 配合 `uv` 进行依赖管理。移除了已弃用的文件，更新了所有导入路径为标准包导入，并将测试文件整合到 `tests/` 目录。

本项目在 V3.0 版本中进行了重大更新，主要聚焦于智能体记忆和反思能力的提升，以及模拟提示词的优化，增强智能体的学习能力、适应能力和决策质量。

更新日志请参见 [Update-v3.0-20250223.md](/docs/Update-v3.0-20250223.md)

本项目在 V2.0 版本中进行了重大更新，包括优化记忆检索、改进 Agent 状态评估、完善记忆管理、为数据库交互奠定基础，并优化主程序和 Prompt。

更新日志请参见 [Update-v2.0-20250222.md](/docs/Update-v2.0-20250222.md)

## 作者和引用

黄淼森 Huang Miaosen

## 致谢

*   [https://github.com/mkturkcan/generative-agents](https://github.com/mkturkcan/generative-agents)，部分代码来源，已在 License 文件夹中附上 License
*   [https://github.com/joonspk-research/generative_agents](https://github.com/joonspk-research/generative_agents)，仅根据论文做思路参考，并未 Copy 代码
