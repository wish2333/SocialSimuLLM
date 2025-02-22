## Version 2.0

*   **Date:** February 21, 2025
*   **Contributor:** Huang Miaosen

---

**Update Summary for February 21, 2025**

-   **Key Objectives:**
   -   **Core Focus:** Optimizing memory retrieval, improving Agent state evaluation, enhancing memory management, laying the groundwork for database interaction, and refining the main program and Prompt.
-   **Major Changes:**
   -   **Memory Retrieval Enhancements:**
      -   **get_newthings** function modified to only extract `action` type memories, enhancing retrieval accuracy.
      -   Added focus on significant recent events, extracting action type memories with importance ratings of 4 or higher.
   -   **Agent State Evaluation:**
      -   Introduced `thought` type memories to record Agent emotions, social/learning motivation, task completion confidence, information acquisition inclination, and technology acceptance tendency.
      -   Implemented hourly state evaluations, with assessment results saved as `thought` type memories.
   -   **Memory Management:**
      -   Consolidated memory reading methods, with `agent` module's `plans` and `gotten_impressions` accessed through `Memory` function.
      -   Updated action recording in `format_experience`, directing it to a specific person, thus ignoring `agent.name` when writing to the database.
      -   Implemented logic for real-time modification of `json`'s `starting_location` through Memory.location_change.
   -   **Database Interaction (Delayed until V3, some code commented out):**
      -   `exist_memory_file` function added SQLite database creation capabilities, creating individual database files for each Agent.
      -   `add_experience` function invoked `sort_memory`, storing action data in the database upon addition.
      -   Introduced functions for embedding and database storage.
   -   **Main Program Adjustments:**
      -   Adapting to changes in `town_data.json` format, allowing agent description as a dictionary, converting `description` field to string if it is a dictionary.
      -   In main, read current impressions before every hour starts.
      -   Removed requirements for `repeat` based on `new_hour/day`, as memories are recorded every time.
      -   Added steps for handling recent impressions.
   -   **Model Prompt and Parameter Optimization:**
      -   Modified related prompts to improve model output quality.
      -   Set `max_token` limits for daily_plan at 300, hourly_plan at 30, and execute_action at 80, adjusting `agent_execute_action_prompt`.
   -   **Project Structure:**
      -   Removed test projects, added example projects.
      -   Enhanced **README** with:
         -   Preparation of an API containing complements and embedding models.
         -   Projects can be continued with incremental backups considered.
         -   Execute `main.py` after adding `cd simulation` in main.
         -   Modified **Acknowledgments** section.
-   **Technical Details:** (No details mentioned)
-   **Prospect:**
   -   Long-term memory vectorized database storage and re-association event extraction.
   -   Related events extracted through a weighted formula, identifying the top 5 most significant, considering recentness, importance, and similarity.
   -   Daily reflection once a day, generating a summary of the day's key events based on important memories with ratings of 7 or higher.