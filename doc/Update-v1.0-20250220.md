## Version 1.0

*   **Date:** February 20, 2025
*   **Contributor:** Huang Miaosen

---

**Update Summary for February 19, 2025**

-   **Core Objective:** Optimizing Agent logic, enhancing code structure, improving maintainability, and laying the groundwork for the memory function.
-   **Key Changes:**
    -   **Template Optimization:** Centralized storage of Agent Prompt templates in the `template_agents.py` module to improve code maintainability.
    -   **OpenAI Calls:** Upgraded the OpenAI API calling method.
    -   **Agent Core Logic Refactoring:**
        -   Added `daily_plans`, `hourly_plans`, `hourly_action_prompt` properties for storing plan information.
        -   Dynamically bound `rate_locations`, `move` methods using `MethodType` to enhance Agent behavior flexibility.
        -   Utilized `world_graph` for simulating a map supporting path planning.
        -   Optimized `daily_planning`, `hourly_planning`, `execute_action` methods.
    -   **Error Resolution After Splitting:** Provided solutions for `AttributeError` and `TypeError` to ensure correct code execution.
    -   **Main Logic Adjustments:**
        -   **Project Configuration:** Allows loading different project data through input project name.
        -   **Logging:** Increased detailed logging, including locations, actions, state changes, and summary functionality.
        -   **Simulation Summary:** Generated summaries at the end of each simulation.
        -   **Time System:** Introduced a more comprehensive time system.
-   **Technical Details:**
    -   Updated `GPT_request` function with the new OpenAI API calling method.
    -   Created `movement.py` module for movement-related functionalities.
    -   Constructed `world_graph` for simulating the environment.
-   **Prospect:**
    -   Refine and optimize the simplified logic.
    -   Optimize `town_data` and Prompts to adapt to experimental environments.

**Update Summary for February 20, 2025**

- **Core Objective:** Building a Memory (memory) system for the Agent.

- **Implementation Plan and Thinking:**

  -   **Memory Module Purpose:** Provides a memory system for Agents to store actions, plans, events, and experiences, and enables the retrieval and utilization of memories.
  -   **Design Thinking (Replace Memory Module with Retrieve Module):**
      1.  **File Storage:** One JSON file per Agent.
      2.  **Experience Categorization:** Action (action), Plan (plan), Event (event).
      3.  **Adding Experience:** `add_experience` function.
      4.  **Getting New Memories:** `get_newthings` method.
      5.  **Formatting New Messages:** `format_newthings` method.
  -   **Retrieve Module File Structure:**
      -   `retrieve\memory.py`: Short-term memory storage and reading.
      -   `retrieve\retrieve.py`: Sorting and retrieval of long-term memory.

- **Main Module Modifications:**

  -   Integrated the Memory module.
  -   Introduced the `Memory` module.
  -   Refined time control.
  -   Prioritized and formatted experiences.
  -   Improved logging and summary.
  -   `Memory` object initialization.
  -   Adjusted daily/hourly plan parameters, added daily/hourly plan experiences to Memory.
  -   Action, location rating, and log updates.

- **Agent Simple Modifications:** Logic interacting with the Retrieve module.

- **Detailed Explanation:**

  -   **Memory Module Design:** The Memory module aims to provide an Agent with a memory system for storing, retrieving, and utilizing past experiences. Its core concept is to enable Agents to learn and adapt to the environment like humans by leveraging memory.
  -   **JSON File Storage:** Each Agent corresponds to a JSON file for storing its memory. This storage method is simple and convenient for reading and modifying data.
  -   **Experience Categorization:** Experiences are categorized into three types: Action (action), Plan (plan), and Event (event). This categorization helps in better organization and management of memories.
      -   **Action (action):** Records the actions taken by the Agent, such as "Agent moved to the store".
      -   **Plan (plan):** Records the plans made by the Agent, such as "Agent plans to go to the store at 9 am tomorrow morning".
      -   **Event (event):** Records events experienced by the Agent, such as "Agent encountered a friendly NPC".
  -   **`add_experience` Function:** This function adds new experiences to the Agent's memory. It receives the type, content, and timestamp of the experience and stores this information in the JSON file.
  -   **`get_newthings` Method:** This method retrieves the Agent's new memories based on time, type, and other conditions from the JSON file.
  -   **`format_newthings` Method:** This method formats the newly retrieved memories for better understanding and use by the Agent.
  -   **Retrieve Module:** The Retrieve module is used for sorting and retrieving long-term memory, supplementing the Memory module to implement more advanced memory functions.

- **Technical Details:**

  -   **JSON File Format:** The JSON file stores memory in the following format:

  ```json
  {
    "agent_id": "agent_1",
    "memory": [
      {
        "type": "Action",
        "content": "Agent moved to the store",
        "timestamp": "2025-02-20 10:00:00"
      },
      {
        "type": "Plan",
        "content": "Agent plans to go to the store at 9 am tomorrow morning",
        "timestamp": "2025-02-21 00:00:00"
      },
      {
        "type": "Event",
        "content": "Agent encountered a friendly NPC",
        "timestamp": "2025-02-20 12:00:00"
      }
    ]
  }
  ```

  -   **Example of `add_experience` Function:**

  ```python
  import json
  
  def add_experience(agent_id, experience_type, content, timestamp):
      """
      Adds experience to an Agent's memory.
      """
      file_path = "simulation


**Summary:**

The main tasks of the past two days have been focused on restructuring the core logic of the Agent, laying the groundwork for the implementation and improvement of its memory function. Through modular design, the readability and maintainability of the code have been significantly improved. At the same time, the calling method of the OpenAI API has been updated to ensure the availability of the code. In the next steps, the emphasis will be on refining and optimizing the memory module, and adjusting the Agent's behavior logic to make it more intelligent and in line with expectations.