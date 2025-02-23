## 版本 3.0

*   **日期：** 2025年2月23日
*   **贡献者：** 黄淼森

---

**2025-02-23 更新摘要**

-   **核心目标：** 优化行为判断机制，完善长期记忆存储，实现每日反思功能，为研究员介入提供支持。
-   **关键改动：**
    -   **行为判断优化：**
        -   综合近期发生事件、近期感受（V2）、相关事件（V3）进行行为判断。
    -   **长期记忆优化：**
        -   通过大模型将 agent_name, date, location, action_des 简化为 action_des 后存入数据库。
        -   在 hourly plan 后运行相关事件提取，通过加权公式获取近期性、重要性和与 hourly plan 相似性综合最重要的5件事情。
    -   **反思机制：**
        -   每天进行一次反思，通过重要性不低于7的记忆生成今日要事总结。
        -   将反思结果（reflection）以 thought 类型存入记忆，并保存至向量数据库。
        -   在 simulation\main.py 的 # Whether to summary 之前添加 thought 判断逻辑。
    -   **控制台输出：**
        -   在 main.py 启动时返回 round 和 global_time 到控制台。
    -   **V1模块接入：**
        -   评估并确定可接入V1版本的模块。
    -   **V2版本修正：**
        -   修复 repeat = repeats - 1 时 summary 未运行的错误。
        -   修复获取记忆过多异常的bug。
        -   统一记忆读取方式，删除每小时计划的记忆并添加执行主程序后第一轮生成一次每小时计划。
        -   修改 action 记录方式 format_experience 的 action 部分。
        -   添加修改 json 里 starting_location，记忆 location_change。
        -   优化 prompt 和 get_xxx 部分，修改 memory_actions。
        -   在 main 中删除其他 GPT_request 的 impression 传入需求，直接读 self。
        -   删除一些 if new_hour/day 后对 repeat 的要求。
-   **技术细节：** (无)
-   **展望：**
    -   完善研究员介入模拟环境功能。
    -   优化长期记忆的向量化数据库保存与重关联事件提取机制。
    -   增强反思机制的智能化程度，提高总结的准确性和实用性。