# 更新日志

## 版本 1.0

*   **日期：** 2025年2月20日
*   **贡献者：** 黄淼森

---

**2025-02-19 更新摘要**

-   **核心目标：** 优化 Agent 逻辑，改进代码结构，增强可维护性，并为记忆功能奠定基础。
-   **关键改动：**
    -   **模板优化：** 将 Agent Prompt 模板集中存储于 `template_agents.py` 模块，提高代码可维护性。
    -   **OpenAI 调用：** 升级了 OpenAI API 调用方式。
    -   Agent 核心逻辑重构：
        -   新增了 `daily_plans`、`hourly_plans`、`hourly_action_prompt`等属性，用于存储计划信息。
        -   使用 `MethodType` 动态绑定 `rate_locations`, `move` 方法，增强 Agent 行为的灵活性。
        -   `world_graph` 用于模拟地图，支持路径规划。
        -   `daily_planning`, `hourly_planning`, `execute_action` 方法得到优化。
    -   **解决拆分后出现的错误：** 提供了针对 `AttributeError` 和 `TypeError` 的解决方案，确保代码的正确运行。
    -   Main 逻辑调整：
        -   **项目配置：** 允许通过输入项目名称加载不同的项目数据。
        -   **日志记录：** 增加了详细的日志记录，包括地点、行动、状态变化等信息，并提供摘要功能。
        -   **模拟总结：** 每次模拟结束，生成总结报告。
        -   **时间系统：** 引入更完善的时间系统。
-   **技术细节：**
    -   `GPT_request` 函数更新，使用新的 OpenAI API 调用方式。
    -   `movement.py` 模块的创建，负责移动相关功能。
    -   `world_graph` 构建，用于模拟环境。
-   **展望：**
    -   完善记忆功能，优化简化版逻辑。
    -   优化 `town_data` 和 Prompt，以适应实验环境。

**2025-02-20 更新摘要**

-   **核心目标：** 构建 Memory (记忆) 系统。
-   **实现计划和思路：**
    -   **Memory模块目标：** 为 Agent 提供记忆系统，存储行动、计划、事件等经验，并提供获取和使用记忆的能力。
    -   **设计思路 (Retrieve模块替代Memory模块)：**
        1.  **文件存储:** 每个 Agent 一个 JSON 文件。
        2.  **经验分类:** Action (动作), Plan (计划), Event (事件)。
        3.  **添加经验:** `add_experience` 函数。
        4.  **获取新记忆:** `get_newthings`方法。
        5.  **格式化新消息:** `format_newthings`方法。
    -   **Retrieve模块的文件结构：**
        -   `retrieve\memory.py`：存储和读取短期记忆。
        -   `retrieve\retrieve.py`：长期记忆的排序和检索。
-   **Main 模块修改：**
    -   整合了 Memory 模块。
    -   引入 `Memory` 模块。
    -   细化时间控制。
    -   经验优先级和格式化。
    -   日志记录和摘要改进。
    -   `Memory` 对象初始化.
    -   每日/每小时计划参数调整，每日/每小时计划经验加入Memory.
    -   行动、地点评级、日志更新。
-   **Agent的简单修改：** 与 Retrieve 模块交互的逻辑。

-   **详细说明：**
    -   **Memory 模块设计：** Memory 模块旨在为 Agent 提供一个记忆系统，使其能够存储、检索和使用过去的经验。该模块的核心思想是让 Agent 能够像人类一样，通过记忆来学习和适应环境。
    -   **JSON 文件存储：** 每个 Agent 对应一个 JSON 文件，用于存储其记忆。这种存储方式简单易用，方便数据的读取和修改。
    -   **经验分类：** 经验被分为三种类型：Action（动作）、Plan（计划）和 Event（事件）。这种分类方式有助于更好地组织和管理记忆。
        -   **Action (动作):** 记录 Agent 执行的动作，例如 "Agent 移动到商店"。
        -   **Plan (计划):** 记录 Agent 的计划，例如 "Agent 计划在明天早上 9 点去商店"。
        -   **Event (事件):** 记录 Agent 经历的事件，例如 "Agent 遇到了一个友好的 NPC"。
    -   **`add_experience` 函数：** 该函数用于将新的经验添加到 Agent 的记忆中。它接收经验的类型、内容和时间戳等信息，并将这些信息存储到 JSON 文件中。
    -   **`get_newthings` 方法：** 该方法用于获取 Agent 的新记忆。它根据时间、类型等条件，从 JSON 文件中检索相关的经验。
    -   **`format_newthings` 方法：** 该方法用于格式化新获取的记忆，以便 Agent 能够更好地理解和使用这些记忆。
    -   **Retrieve 模块：** Retrieve 模块用于长期记忆的排序和检索，它将对 Memory 模块进行补充，实现更高级的记忆功能。
-   **技术细节：**
    -   **JSON 文件格式：** JSON 文件采用以下格式存储记忆：

    ```json
    {
      "agent_id": "agent_1",
      "memory": [
        {
          "type": "Action",
          "content": "Agent 移动到商店",
          "timestamp": "2025-02-20 10:00:00"
        },
        {
          "type": "Plan",
          "content": "Agent 计划在明天早上 9 点去商店",
          "timestamp": "2025-02-21 00:00:00"
        },
        {
          "type": "Event",
          "content": "Agent 遇到了一个友好的 NPC",
          "timestamp": "2025-02-20 12:00:00"
        }
      ]
    }
    ```

    -   **`add_experience` 函数示例：**

    ```python
    import json

    def add_experience(agent_id, experience_type, content, timestamp):
        """
        将经验添加到 Agent 的记忆中。
        """
        file_path = f"simulation/projects/t4/agent_data/{agent_id}_memory.json"  # 假设记忆文件路径
        try:
            with open(file_path, "r") as f:
                memory = json.load(f)
        except FileNotFoundError:
            memory = {"agent_id": agent_id, "memory": []}

        new_experience = {
            "type": experience_type,
            "content": content,
            "timestamp": timestamp
        }
        memory["memory"].append(new_experience)

        with open(file_path, "w") as f:
            json.dump(memory, f, indent=2)
    ```

-   **总结：**

    这两天的主要工作集中在 Agent 核心逻辑的重构，为记忆功能的实现和完善打下了基础。通过模块化设计，代码的可读性和可维护性得到了显著提升。同时，对于 OpenAI API 的调用方式进行了更新，确保了代码的可用性。接下来，将重点完善和优化记忆模块，并调整 Agent 的行为逻辑，使其更加智能和符合预期。