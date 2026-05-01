## 版本 2.0

*   **日期：** 2025年2月21日
*   **贡献者：**  黄淼森

---

**2025-02-21 更新摘要**

-   **核心目标：** 优化记忆检索，改进 Agent 状态评估，完善记忆管理，为数据库交互奠定基础，并优化主程序和 Prompt。
-   **关键改动：**
    -   **记忆检索优化：**
        -   `get_newthings` 函数修改，仅提取 `action` 类型记忆，提高检索准确性。
        -   添加重要近期事件，提取 action 类型且重要性不小于 4。
    -   **Agent 状态评估：**
        -   新增 `thought` 类型记忆，用于记录 Agent 的情绪、社交/学习动力、任务完成信心、信息获取倾向、技术接受倾向等状态。
        -   实现每小时一次的状态评估，并将评估结果以 `thought` 类型存入记忆。
    -   **记忆管理：**
        -   统一记忆读取方式，`agent` 模块中的 `plans` 和 `gotten_impressions` 通过 `Memory` 函数读取文件生成。
        -   修改 action 记录方式 `format_experience` 的 action 部分，使其指向某个人，这样的话写入数据库的时候就可以忽略 agent.name 的记录。（并且修改了记忆管理参数experience的格式使其在记录中包含 agent.name、 global_time、 location、 action等信息）
        -   通过Memory.location_change添加实时修改 json 里的starting_location的逻辑。
    -   **数据库交互（推迟到 V3 版本实现，部分相关代码已注释）：**
        -   `exist_memory_file` 函数添加 SQLite 数据库创建功能，为每个 Agent 创建独立的数据库文件。
        -   `add_experience` 函数调用了 `sort_memory`，在添加 experience 时将 action 存入数据库。
        -   实现了嵌入（embedding）和数据库存储的相关函数
    -   **主程序调整：**
        -   适配 `town_data.json` 格式的变更，即 agent 的 descrption 可以输入字典，如果 `description` 字段为字典则将其转化为字符串。
        -   main 中在每小时开始前先读取当前状态 impressions
        -   main 删除一些 if new_hour/day 后对 repeat 的要求，因为现在每次都有记忆了。
        -   添加了近期印象的相关步骤
    -   **大模型提示词与参数优化：**
        -   修改相关 prompt，提升模型输出质量。
        -   agent 中 max_token 限制：daily_plan 为 300；hourly_plan 为 30；execute_action 的为 80，修改 agent_execute_action_prompt。
    -   **项目结构：**
        -   删除测试项目，添加示例项目。
        -   README 新增提示：
            -   要准备一个包含 complements 和 embedding 模型的 api
            -   project 可以沿用继续，但是需要注意增量备份。
            -   运行主程序添加 cd simulation 后才执行 main.py
            -   Acknowledgments 修改
-   **技术细节：** (无)
-   **展望：**
    -   长期记忆的向量化数据库保存与重关联事件提取。
    -   相关事件通过加权公式，获取近期性、重要性和相似性综合最重要的 5 件事情。
    -   反思每一天进行一次，通过所有重要性不低于 7 记忆生成今日要事总结。