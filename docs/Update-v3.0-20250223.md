## Version 3.0

*   **Date:** February 23, 2025
*   **Contributor:** Huang Miaosen

---

**Update Summary on February 23, 2025**

-   **Core Objective:** Optimize behavior judgment mechanism, enhance long-term memory storage, implement daily reflection function, and provide support for researcher intervention.
-   **Key Changes:**
    -   **Behavior Judgment Optimization:**
        -   Integrate recent events, recent feelings (V2), and related events (V3) for behavior judgment.
    -   **Long-Term Memory Optimization:**
        -   Simplify agent_name, date, location, action_des to action_des for database storage with a large model.
        -   Execute related event extraction after the hourly plan, and retrieve the most important 5 events through a weighted formula considering their relevance, importance, and similarity to the hourly plan.
    -   **Reflection Mechanism:**
        -   Conduct a daily reflection, generating a summary of today's important events with a minimum importance of 7.
        -   Store reflection results (reflection) as thought type in memory and save them to the vector database.
        -   Add thought judgment logic before # Whether to summary in simulation\main.py.
    -   **Console Output:**
        -   Return round and global_time to the console when main.py starts.
    -   **V1 Module Integration:**
        -   Evaluate and determine which modules can be integrated with V1 version.
    -   **V2 Version Corrections:**
        -   Fix the error where summary is not executed when repeat = repeats - 1.
        -   Resolve the bug of abnormal memory retrieval when too many memories are obtained.
        -   Standardize the memory reading method, delete hourly plan memory, and add the generation of hourly plans once after executing the main program.
        -   Modify the action recording format in format_experience.
        -   Add modifications to json, including starting_location, and record location changes.
        -   Optimize prompt and get_xxx parts, update memory_actions.
        -   In main, remove the requirement for GPT_request's impression input, directly read self.
        -   Delete some if new_hour/day requests for repeat.
-   **Technical Details:** (None)
-   **Prospects:**
    -   Improve the simulation environment's capability for researcher intervention.
    -   Optimize the vector database storage and retrieval mechanism for associated event extraction in long-term memory.
    -   Enhance the intelligence of the reflection mechanism, improving the accuracy and practicality of summaries.