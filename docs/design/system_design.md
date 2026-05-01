# System Design

> Version: 3.1
> Last Updated: 2026-05-01
> Status: Active

---

## 1. Architecture Overview

SocialSimuLLM uses a modular, agent-based architecture powered by Large Language Models (LLMs). The system simulates social interactions in a town setting where autonomous agents make decisions, form memories, and move between locations.

```
+-------------------+
|                   |
|   __main__.py    |  <-- Entry Point
|                   |
+--------+----------+
         |
         v
+--------+----------+       +------------------+
|                   |       |                  |
|  Agent System     |<----->|  Locations       |
|  (agents/)       |       |  (locations/)    |
|                   |       |                  |
+--------+----------+       +------------------+
         |
         v
+--------+----------+       +------------------+
|                   |       |                  |
|  Memory System   |<----->|  LLM API        |
|  (retrieve/)     |       |  (text_gen)      |
|                   |       |                  |
+-------------------+       +------------------+
         |
         v
+--------+----------+
|                   |
|  Data Persistence |
|  (JSON + SQLite) |
|                   |
+-------------------+
```

---

## 2. Module Specifications

### 2.1 Main Module (`socialsimullm/__main__.py`)

**Responsibility**: Orchestrate the entire simulation lifecycle.

**Key Functions**:
- `main()`: Main entry point function
- Global configuration: logging flags, summarization flags
- Project initialization: load meta.json, town_data.json
- World graph creation using NetworkX
- Agent creation and initialization
- Main simulation loop

**Simulation Loop Flow**:
1. Check if new day (08:00) -> Run daily planning
2. Check if new hour (xx:00) -> Run hourly planning, location rating, impression formation
3. Every 10 minutes -> Execute action, rate experience, update memory
4. At end of day -> Run reflection, generate summary

**Configuration Flags**:
| Flag | Default | Description |
|------|---------|-------------|
| log_debug | True | Log debug information |
| log_locations | True | Log location changes |
| log_actions | True | Log agent actions |
| log_plans | True | Log agent plans |
| log_ratings | True | Log location ratings |
| log_memory | True | Log memory operations |
| print_locations | True | Print locations to console |
| print_actions | True | Print actions to console |
| print_plans | True | Print plans to console |
| print_ratings | False | Print ratings to console |
| print_memory | False | Print memory to console |
| summarize_locations | False | Include locations in summary |
| summarize_actions | True | Include actions in summary |
| summarize_plans | False | Include plans in summary |
| summarize_ratings | False | Include ratings in summary |
| summarize_memory | True | Include memory in summary |

---

### 2.2 Agent Module (`socialsimullm/agents/`)

#### 2.2.1 Agent Class (`agent.py`)

**Responsibility**: Represent an intelligent agent that can plan, act, and reflect.

**Attributes**:
| Attribute | Type | Description |
|-----------|------|-------------|
| name | str | Agent identifier |
| description | str | JSON string of agent traits |
| location | str | Current location |
| daily_plans | str | Today's plans |
| hourly_plan | str | Current hour plan |
| impression | str | Current impression |
| action | str | Most recent action |
| reflection | str | Most recent reflection |
| world_graph | nx.Graph | NetworkX graph of town |
| related_things | str | Retrieved related memories |
| event | list | Global events |

**Methods**:
| Method | Description |
|--------|-------------|
| `init_memory(daily_plans, hourly_plan, event)` | Initialize agent's memory from saved data |
| `daily_planning(global_time, prompt_meta, impressions, newthings)` | Generate daily plan |
| `hourly_planning(agents, location, global_time, town_areas, prompt_meta, impressions, newthings)` | Generate hourly plan |
| `execute_action(global_time, prompt_meta, impressions, nearby_situations)` | Execute planned action |
| `form_impression(global_time, prompt_meta, nearby_situations)` | Form impression of current state |
| `form_reflection(global_time, prompt_meta, recent_reflection, important_things)` | Reflect on the day |

**Note**: Methods `rate_locations`, `move`, `rate_experience`, `memory_actions`, `simplify_action`, `memory_daily_plans`, `memory_hourly_plan`, `memory_location_change`, `memory_impression`, `memory_reflection` are attached dynamically via `MethodType` from `memory.py` and `movement.py`.

#### 2.2.2 Memory Helpers (`memory.py`)

**Responsibility**: Provide memory-related methods attached to Agent instances.

**Key Functions** (attached to Agent instances):
- `rate_experience(prompt_meta, recent_impressions, nearby_situations, experience)` -> int
- `memory_actions(agents, global_time, priority)` -> dict
- `simplify_action()` -> str
- `memory_daily_plans(global_time)` -> dict
- `memory_hourly_plan(global_time)` -> dict
- `memory_location_change(global_time, old_location, new_location)` -> dict
- `memory_impression(global_time, impression)` -> dict
- `memory_reflection(global_time, reflection)` -> dict

#### 2.2.3 Movement (`movement.py`)

**Responsibility**: Handle location rating and physical movement.

**Key Functions** (attached to Agent instances):
- `rate_locations(locations, global_time, prompt_meta, recent_impressions, nearby_situations)` -> list of (location_name, rating, response)
- `move(new_location_name)` -> str (new location)

**Algorithm for Location Rating**:
1. For each location in the town, generate an LLM prompt
2. LLM returns a 1-9 rating
3. Parse the numeric rating from response
4. Sort locations by rating (descending)
5. Return sorted list

**Movement Algorithm**:
1. Use NetworkX shortest_path to find path to destination
2. Update agent.location to new_location_name
3. Return new location

---

### 2.3 Locations Module (`socialsimullm/locations/`)

#### 2.3.1 Location Class

**Attributes**:
- `name`: Location identifier
- `description`: Text description

**Methods**:
- `describe()`: Print the location description

#### 2.3.2 Locations Class

**Attributes**:
- `locations`: Dict mapping location names to Location objects

**Methods**:
- `add_location(name, description)`: Add a new location
- `get_location(name)`: Retrieve a Location by name
- `__str__()`: String representation of all locations

---

### 2.4 Retrieve Module (`socialsimullm/retrieve/`)

#### 2.4.1 Memory Class (`memory.py`)

**Responsibility**: Manage agent memories with JSON persistence and SQLite embedding storage.

**Attributes**:
| Attribute | Type | Description |
|-----------|------|-------------|
| project_folder | str | Path to project directory |
| agents | list | List of Agent objects |
| memory_limit | int | Max recent experiences to retrieve |

**Methods**:
| Method | Description |
|--------|-------------|
| `load_memory_file(agent_name)` -> dict | Load agent's memory JSON file |
| `save_memory_file(agent_name, memory)` | Save agent's memory JSON file |
| `load_event_file()` -> dict | Load global events JSON file |
| `save_and_load_event_file(new_event)` -> dict | Add event and return updated events |
| `add_experience(experience, exp_type)` | Add new experience to relevant agents' memories |
| `get_init_memory(agent_name)` -> [str, str] | Get last daily plan and hourly plan |
| `get_newthings(agent_name, num_experiences)` -> list | Get N most recent action experiences |
| `get_newthings_str(agent_name, num_experiences)` -> str | Get new things as formatted string |
| `get_importants(agent_name, global_time)` -> list | Get important experiences (priority>6) for current day |
| `get_importants_str(agent_name, global_time)` -> str | Get important things as string |
| `get_impressions(agent_name, num_experiences)` -> list | Get N most recent impression thoughts |
| `get_impressions_str(agent_name, num_experiences)` -> str | Get impressions as string |
| `sort_memory(agent_name, action)` | Embed action and store in SQLite |
| `embed_action(action)` -> list | Get embedding vector via LLM API |
| `store_embedding_in_database(agent_name, action, embedding)` | Store in SQLite |
| `get_related_things(agent_name, hourly_plan, num_related_things)` -> list | Get related experiences using similarity + recency + importance |
| `get_related_things_str(agent_name, hourly_plan, num_related_things)` -> str | Get related things as string |

**Memory Storage Format (JSON)**:
```json
{
  "memory": [
    {
      "agent_name": "Agent Name",
      "global_time": "Day 1, 08:00",
      "location": "Location Name",
      "action": "Narrative description",
      "action_des": "Simplified SVO sentence",
      "other_agents": ["Agent1", "Agent2"],
      "exp_type": "action|plan|thought|event|reflection",
      "priority": 1-9
    }
  ]
}
```

**SQLite Schema** (for embeddings):
```sql
CREATE TABLE action_embeddings (
    action_index INTEGER,
    action_description TEXT,
    action_embedding TEXT
)
```

**Related Things Scoring Algorithm**:
```
score = 0.5 * similarity + 0.3 * recency + 0.2 * normalized_importance
```
Where:
- `similarity`: Cosine similarity between hourly plan embedding and action embedding
- `recency`: 1 - (index / total_actions)
- `normalized_importance`: (min(max(priority, 1), 9) - 1) / 8

#### 2.4.2 Reflect Class (`reflect.py`)

**Status**: Placeholder - not yet implemented.

**Planned Methods**:
- `get_reflect(newthings: list)`: Decide whether to reflect on actions and thoughts

---

### 2.5 Utils Module (`socialsimullm/utils/`)

#### 2.5.1 Config (`config.py`)

**Responsibility**: Store API configuration and model settings.

**Variables**:
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| openai_api_key | str | "<your_api_key>" | OpenAI-compatible API key |
| openai_base_url | str | "http://192.168.1.110:3001/v1" | API base URL |
| key_owner | str | "Huang Miaosen" | Key owner name |

**DefaultModel Class**:
| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| embedding | str | "BAAI/bge-m3" | Embedding model name |
| completion | str | "gpt-4o-mini" | Completion model name |

#### 2.5.2 Global Methods (`global_methods.py`)

**Responsibility**: Provide helper functions for file I/O, time management, and data persistence.

**Key Functions**:
| Function | Description |
|----------|-------------|
| `load_meta_data(project_folder, project_name, global_time)` -> dict | Load or create meta.json |
| `save_meta_data(project_folder, meta_data)` | Save meta.json |
| `load_town_data(project_folder)` -> dict | Load town_data.json (copy from template if not exists) |
| `save_location_change(project_folder, agent_name, location)` | Update agent's location in town_data.json |
| `load_agent_data(project_folder, agent_name)` -> dict | Load agent's data JSON |
| `save_agent_data(project_folder, agent_name, agent_data)` | Save agent's data JSON |
| `exist_memory_file(agent_name, project_folder)` | Create memory JSON and SQLite if not exist |
| `add_ten_minutes(global_time)` -> str | Add 10 minutes to global time |
| `if_new_day(global_time)` -> bool | Check if time is 08:00 |
| `if_new_hour(global_time)` -> bool | Check if minutes are ":00" |

**Time Format**: `"Day X, HH:MM"` (e.g., "Day 1, 08:00")

**Time Progression**:
- Increments by 10 minutes each loop
- At 20:00, rolls over to 08:00 next day

#### 2.5.3 Text Generation (`text_generation.py`)

**Responsibility**: Interface with LLM APIs for text generation and embeddings.

**Key Functions**:
| Function | Description |
|----------|-------------|
| `GPT_request(system, prompt, gpt_parameter)` -> str | Send chat request to LLM API |
| `get_embedding(text, model)` -> list | Get embedding vector for text |
| `get_rating(x)` -> int or None | Extract numeric rating (1-9) from string |
| `summarize_simulation(prompt)` -> str | Generate daily simulation summary |
| `time_sleep(sec)` | Sleep to avoid API rate limits |

**Default GPT Parameters**:
| Parameter | Default | Description |
|-----------|---------|-------------|
| model | DefaultModel.completion | Model to use |
| temperature | 0.8 | Sampling temperature (0-2) |
| max_tokens | 50 | Max tokens to generate |
| top_p | 1.0 | Nucleus sampling |
| frequency_penalty | 0 | Frequency penalty |
| presence_penalty | 0 | Presence penalty |
| stop | None | Stop sequences |

---

### 2.6 Prompt Templates (`socialsimullm/prompt_templates/`)

#### 2.6.1 Template Agents (`template_agents.py`)

**Responsibility**: Store all prompt templates for LLM interactions.

**Template Categories**:
| Template | Used By | Purpose |
|----------|---------|-------------|
| `agent_plan_system` / `agent_plan_prompt` | daily_planning() | Daily plan generation |
| `hourly_planning_system` / `hourly_planning_prompt` | hourly_planning() | Hourly plan generation |
| `agent_execute_action_system` / `agent_execute_action_prompt` | execute_action() | Action execution |
| `rate_location_system` / `rate_location_prompt` | rate_locations() | Location rating |
| `rate_experiences_system` / `rate_experiences_prompt` | rate_experience() | Experience rating |
| `agent_impressions_system` / `agent_impressions_prompt` | form_impression() | Impression formation |
| `action_simpilfy_system` / `action_simpilfy_system_prompt` | simplify_action() | Action simplification to SVO |
| `agent_reflection_system` / `agent_reflection_prompt` | form_reflection() | Daily reflection |

---

## 3. Data Flow

### 3.1 Simulation Startup Flow

```
User Input (project name)
    |
    v
Load meta.json --> Check if project exists
    |                              |
    v (exists)                     v (not exists)
Load existing data              Create project folder
Load town_data.json             Copy town_data_template.json
    |                              |
    v                              v
Create NetworkX Graph <-- town_areas
    |
    v
Create Agents <-- town_people
    |
    v
Initialize Memory for each agent
    |
    v
Load/Save event.json
    |
    v
Initialize agent memory (last daily plan, hourly plan, events)
    |
    v
Start Simulation Loop
```

### 3.2 Main Simulation Loop

```
FOR repeat in range(repeats):
    |
    +-- Check if_new_day(global_time)
    |       |
    |       +-- YES --> FOR each agent: daily_planning()
    |                        --> memory.add_experience(exp, 'plan')
    |
    +-- Check if_new_hour(global_time)
    |       |
    |       +-- YES --> FOR each agent: hourly_planning()
    |                        --> memory.add_experience(exp, 'thought')
    |                        --> get_related_things()
    |               FOR each agent: rate_locations()
    |                        --> agent.move(new_location)
    |                        --> memory.add_experience(exp, 'action')
    |               FOR each agent: form_impression()
    |                        --> memory.add_experience(exp, 'thought')
    |
    +-- FOR each agent: execute_action()
    |       --> rate_experience()
    |       --> memory.add_experience(exp, 'action')
    |
    +-- Add 10 minutes to global_time
    |
    +-- Check if_new_day(new_global_time)
    |       |
    |       +-- YES --> FOR each agent: form_reflection()
    |                        --> memory.add_experience(exp, 'reflection')
    |               Generate simulation summary
    |               Save summary to file
    |
    +-- Save meta_data (global_time, round)
```

### 3.3 Memory Storage Flow

```
Agent performs action
    |
    v
Construct experience dict (agent_name, global_time, location, action, etc.)
    |
    v
memory.add_experience(experience, exp_type)
    |
    +-- exp_type == 'action'
    |       |
    |       +-- FOR each agent in other_agents:
    |               load memory JSON
    |               append experience
    |               save memory JSON
    |               sort_memory() --> embed_action() --> store_embedding_in_database()
    |
    +-- exp_type == 'plan' or 'thought'
    |       |
    |       +-- load agent's memory JSON
    |           append experience
    |           save memory JSON
    |
    +-- exp_type == 'event'
            |
            +-- FOR each agent:
                    load memory JSON
                    append experience
                    save memory JSON
```

---

## 4. Technology Stack

| Layer | Technology | Version |
|-------|-------------|---------|
| Language | Python | 3.11+ |
| Package Manager | uv | Latest |
| Build System | hatchling | Latest |
| LLM API | OpenAI-compatible API | - |
| Graph Library | NetworkX | Latest |
| Embedding DB | SQLite3 | Built-in |
| Data Format | JSON | Built-in |
| Embedding Model | BAAI/bge-m3 | - |
| Completion Model | gpt-4o-mini (configurable) | - |

---

## 5. External Dependencies

| Package | Purpose | Used In |
|---------|---------|----------|
| openai | LLM API client | text_generation.py |
| networkx | Graph algorithms for world map | __main__.py, movement.py |
| numpy | Vector operations for similarity | retrieve/memory.py |
| sqlite3 | Embedding storage | retrieve/memory.py, global_methods.py |

---

## 6. Design Patterns Used

### 6.1 Dynamic Method Attachment (Monkey Patching)
Agent methods like `rate_locations`, `move`, `rate_experience`, etc. are defined as standalone functions in `memory.py` and `movement.py`, then attached to Agent instances using `types.MethodType`. This allows separating concerns while maintaining instance access.

### 6.2 Experience Types (Discriminated Union pattern)
Experiences use an `exp_type` field to distinguish between: action, plan, thought, event, reflection. The `add_experience()` method switches behavior based on this type.

### 6.3 Prompt Template Pattern
All LLM interactions use separated system and prompt templates stored in `template_agents.py`, allowing easy customization without code changes.

### 6.4 Dual Storage Pattern
Memory uses two storage mechanisms:
- **JSON**: Structured experience data (human-readable, easy to debug)
- **SQLite**: Embedding vectors (efficient similarity search)

---

## 7. Configuration

### 7.1 LLM Configuration (`config.py`)

```python
openai_api_key = "<your_api_key>"
openai_base_url = "http://192.168.1.110:3001/v1"

class DefaultModel:
    embedding = "BAAI/bge-m3"
    completion = "gpt-4o-mini"
```

### 7.2 Town Data (`town_data.json`)

```json
{
  "general": {
    "memory_limit": 5
  },
  "town_people": {
    "Agent Name": {
      "description": { ... },
      "starting_location": "Location Name"
    }
  },
  "town_areas": {
    "Location Name": "Description text"
  }
}
```

### 7.3 Meta Data (`meta.json`)

```json
{
  "project_name": "project_name",
  "global_time": "Day 1, 08:00",
  "round": 0
}
```
