## 项目介绍

本项目旨在模拟社会互动和智能体行为，提供一个可定制的框架，用于研究和探索各种社会场景。通过模拟，您可以观察智能体之间的互动，分析行为模式，并深入了解社会动力学。

## 设置环境

请按照以下步骤设置环境：

1.  **创建 Conda 环境（可选）：** 如果您想使用 Conda 环境，请运行以下命令：

    ```bash
    00_condaCreate.bat
    ```

    这将创建一个名为 `env` 的 Conda 环境。
2.  **激活 Conda 环境（如果使用）：** 如果您创建了 Conda 环境，请激活它。
3.  **安装依赖项：** 使用以下命令安装项目依赖项：

    ```bash
    env\python.exe -m pip install -r requirements.txt
    ```
4.  **配置 OpenAI API 密钥：**
    *   将您的 OpenAI API 密钥添加到 `simulation/utils/config.py` 文件中的 `openai_api_key` 变量。
    *   您还可以根据需要修改 `openai_base_url`、`key_owner` 和 `DefaultModel`。

## 运行模拟

请按照以下步骤运行模拟：

1.  **运行主程序：** 运行 `simulation/main.py` 文件。
    *   或者，您可以使用 `01_testMain.bat` 文件运行 `test_main.py` 文件进行测试。
2.  **输入项目名称：** 程序将提示您输入项目名称。
3.  **输入重复次数：** 程序将提示您输入模拟的重复次数。

## 模拟存储位置

模拟数据存储在以下位置：

*   **项目目录：** `projects/{project_name}/`，其中 `{project_name}` 是您在运行模拟时输入的项目名称。
*   **模拟日志：** `projects/{project_name}/simulation_log.txt`
*   **模拟摘要：** `projects/{project_name}/simulation_summary.txt`

## 自定义

您可以按照以下步骤自定义模拟：

1.  **修改城镇数据：** 生成project后修改 `simulation/project/<your project name>/town_data.json` 文件以更改城镇数据。
2.  **修改代码：** 修改 `simulation/main.py` 文件中的代码以更改模拟行为。
3.  **修改配置文件：** 修改 `simulation/utils/config.py` 文件中的配置，例如 OpenAI API 密钥和默认模型。
4.  **修改智能体行为：** 修改 `simulation/agents/` 目录下的文件以更改智能体的行为管理。
5.  **修改位置：** 修改 `simulation/locations/` 目录下的文件以更改模拟世界位置管理。
6.  **修改记忆：** 修改 `simulation/retrieve/` 目录下的文件以更改记忆管理。

模块说明请参照

## 作者和引用

黄淼森 Huang Miaosen

## 致谢

*   [https://github.com/mkturkcan/generative-agents](https://github.com/mkturkcan/generative-agents)，部分代码来源，已在License文件夹中附上License
*   [https://github.com/joonspk-research/generative_agents](https://github.com/joonspk-research/generative_agents)，仅根据论文做思路参考，并为Copy代码