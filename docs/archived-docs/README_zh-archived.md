# Generative Agents Simulation (生成式智能体模拟)

## Setting Up the Environment (设置环境)

1.  **安装Python:** 确保您已安装Python 3.x。
2.  **创建虚拟环境 (可选):** 建议使用虚拟环境来隔离项目依赖。
    ```bash
    python -m venv .venv
    .venv\\Scripts\\activate  # Windows
    source .venv/bin/activate  # Linux/macOS
    ```
3.  **安装依赖:** 使用 `requirements.txt` 文件安装项目依赖。
    ```bash
    pip install -r requirements.txt
    ```

## Running a Simulation (运行模拟)

1.  **运行主程序:**  使用以下命令运行模拟。
    ```bash
    python simulation/main.py
    ```
    或者，您可能需要根据您的具体配置运行其他脚本，例如：
    ```bash
    python 01 测试main.bat
    ```
    请根据您的实际情况调整命令。

## Simulation Storage Location (模拟存储位置)

模拟结果和数据存储在 `simulation/projects/` 目录下。具体来说：

*   `simulation/projects/t2/` 和 `simulation/projects/t3/` 等目录包含模拟的日志、摘要和城镇数据。
*   `simulation/projects/t4/agent_data/` 目录包含智能体的记忆数据。

## Customization (自定义)

*   **配置文件:**  您可以通过修改 `simulation/utils/config.py` 文件来配置模拟参数。
*   **城镇数据:**  `simulation/town_data_template.json` 文件提供了城镇数据的模板。您可以在 `simulation/projects/` 目录下创建新的城镇数据文件，并修改 `simulation/main.py` 以使用它们。
*   **智能体行为:**  `simulation/agents/` 目录包含智能体的行为逻辑。您可以修改 `simulation/agents/agent.py` 文件来定制智能体的行为。
*   **提示模板:**  `simulation/prompt_templates/` 目录包含用于生成文本的提示模板。您可以修改这些模板以影响智能体的对话和行为。

## Authors and Citation (作者和引用)

如果您使用了本项目的代码，请引用以下项目：

*   **原始项目:**
    *   [https://github.com/joonspk-research/generative\_agents](https://github.com/joonspk-research/generative_agents)
    *   [https://github.com/mkturkcan/generative-agents](https://github.com/mkturkcan/generative-agents)

## Acknowledgements (致谢)

感谢以下项目提供的灵感和代码：

*   [https://github.com/joonspk-research/generative\_agents](https://github.com/joonspk-research/generative_agents)
*   [https://github.com/mkturkcan/generative-agents](https://github.com/mkturkcan/generative-agents)