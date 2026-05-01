# Business Rules

> Version: 3.1
> Last Updated: 2026-05-01
> Status: Active

---

## 1. Simulation Rules

### 1.1 Time Management

| Rule ID | Rule | Description | Priority |
|---------|------|-------------|----------|
| BR-001 | Time increments by 10 minutes each loop | Global time advances by exactly 10 minutes per simulation loop | P0 |
| BR-002 | Day starts at 08:00 | Each day begins at 08:00 | P0 |
| BR-003 | Day ends at 20:00 | When time reaches or passes 20:00, roll over to next day at 08:00 | P0 |
| BR-004 | Daily planning occurs at 08:00 | Agents generate daily plans only when `if_new_day()` returns True | P0 |
| BR-005 | Hourly planning occurs at xx:00 | Agents generate hourly plans only when `if_new_hour()` returns True | P0 |
| BR-006 | Actions execute every 10 minutes | Agents execute actions in each loop regardless of time | P0 |

### 1.2 Agent Behavior Rules

| Rule ID | Rule | Description | Priority |
|---------|------|-------------|----------|
| BR-010 | Agents must have a daily plan before acting | Daily plans are generated at 08:00 and used throughout the day | P0 |
| BR-011 | Agents must have an hourly plan before executing action | Hourly plans are generated at xx:00 for the next hour | P0 |
| BR-012 | Agents rate all locations every hour | Location ratings are refreshed each hour (xx:00) | P1 |
| BR-013 | Agents move to highest-rated location | Agent moves to location with highest rating | P0 |
| BR-014 | Agents form impressions after action execution | Impressions are formed after hourly planning and actions | P1 |
| BR-015 | Agents reflect at end of day | Reflection occurs when rolling over to next day (after 20:00) | P1 |
| BR-016 | Agents share actions with co-located agents | When an agent acts, the action is added to all agents at the same location | P0 |

### 1.3 Memory Rules

| Rule ID | Rule | Description | Priority |
|---------|------|-------------|----------|
| BR-020 | Actions are stored with priority 1-9 | Priority indicates importance/poignancy | P0 |
| BR-021 | Daily plans have priority 3 | Daily plans are moderately important | P1 |
| BR-022 | Hourly plans have priority 2 | Hourly plans are less important than daily plans | P1 |
| BR-023 | Location changes have priority 2 | Movement records are moderately low priority | P1 |
| BR-024 | Impressions have priority 4 | Impressions are moderately important | P1 |
| BR-025 | Reflections have priority 9 | Reflections are extremely important | P0 |
| BR-026 | Events have priority 9 | Global events are extremely important | P0 |
| BR-027 | Important things = priority > 6 | Used for daily reflection filtering | P1 |
| BR-028 | Memory limit controls retrieval count | `memory_limit` in town_data.json controls `get_newthings()` | P1 |
| BR-029 | Embeddings stored for actions only | Only `exp_type='action'` get embeddings in SQLite | P1 |
| BR-030 | Related things scored by similarity + recency + importance | Score = 0.5*similarity + 0.3*recency + 0.2*importance | P1 |

### 1.4 Location Rules

| Rule ID | Rule | Description | Priority |
|---------|------|-------------|----------|
| BR-030 | Locations form a cyclic graph | Each location connects to itself and neighbors, with first-last connection | P0 |
| BR-031 | Movement uses shortest path | NetworkX shortest_path algorithm determines movement route | P0 |
| BR-032 | Location rating scale is 1-9 | 1=Not likely, 4=Somewhat likely, 7=Very likely, 9=Extremely likely | P1 |
| BR-033 | Same location rating still triggers re-evaluation | Agents rate all locations every hour even if staying | P2 |

### 1.5 Experience Rating Scale

| Rating | Meaning | Examples |
|--------|---------|----------|
| 1 | Purely mundane | Brushing teeth, making bed |
| 2-3 | Routine activities | Eating, walking, working |
| 4-6 | Noteworthy events | Interesting conversation, learning something new |
| 7-8 | Significant events | Major decision, conflict resolution |
| 9 | Extremely poignant | Breakup, college acceptance, major life event |

---

## 2. Data Rules

### 2.1 Project Data

| Rule ID | Rule | Description | Priority |
|---------|------|-------------|----------|
| BR-050 | Project name cannot be empty | User must input a non-empty project name | P0 |
| BR-051 | Project folder created if not exists | New projects get folder + agent_data/ subfolder | P0 |
| BR-052 | meta.json stores global_time and round | Persistence file for simulation state | P0 |
| BR-053 | town_data.json copied from template if missing | Template at `src/socialsimullm/data/town_data_template.json` | P1 |

### 2.2 Agent Data

| Rule ID | Rule | Description | Priority |
|---------|------|-------------|----------|
| BR-060 | Agent memory file: `{name}_memory.json` | Each agent has separate memory file | P0 |
| BR-061 | Agent embedding DB: `{name}_memory.db` | SQLite database for action embeddings | P0 |
| BR-062 | Memory JSON structure: `{"memory": [...]}` | Array of experience objects | P0 |
| BR-063 | Event file shared: `event.json` | All agents share the same event file | P1 |
| BR-064 | Initial memory loads last daily and hourly plan | `get_init_memory()` returns most recent plans | P1 |

### 2.3 Experience Data

| Rule ID | Rule | Description | Priority |
|---------|------|-------------|----------|
| BR-070 | Experience requires agent_name | Identifies which agent owns the memory | P0 |
| BR-071 | Experience requires global_time | Format: "Day X, HH:MM" | P0 |
| BR-072 | Experience requires exp_type | One of: action, plan, thought, event, reflection | P0 |
| BR-073 | Action experiences require location | Where the action occurred | P0 |
| BR-074 | Action experiences require other_agents | List of agents present during action | P1 |
| BR-075 | Action descriptions simplified to SVO | `simplify_action()` converts to Subject-Verb-Object format | P2 |

---

## 3. LLM Interaction Rules

### 3.1 Prompt Rules

| Rule ID | Rule | Description | Priority |
|---------|------|-------------|----------|
| BR-100 | System prompt defines agent identity | `{name}`, `{description}` injected into system prompt | P0 |
| BR-101 | Prompt meta format: `### Instruction:\n{}\n### Response:` | Standardized prompt wrapper | P2 |
| BR-102 | Daily plans limited to 300 tokens max | `max_tokens=300` for daily planning | P1 |
| BR-103 | Hourly plans limited to 45 tokens max | `max_tokens=45` for hourly planning | P1 |
| BR-104 | Actions limited to 80 tokens max | `max_tokens=80` for action execution | P1 |
| BR-105 | Impressions limited to 80 tokens max | `max_tokens=80` for impression formation | P1 |
| BR-106 | Reflections limited to 120 tokens max | `max_tokens=120` for daily reflection | P1 |
| BR-107 | Summaries limited to 500 tokens max | `max_tokens=500` for simulation summary | P2 |
| BR-108 | Ratings limited to 5 tokens max | `max_tokens=5` for location/experience rating | P1 |

### 3.2 API Rules

| Rule ID | Rule | Description | Priority |
|---------|------|-------------|----------|
| BR-110 | API key stored in config.py | `openai_api_key` variable | P0 |
| BR-111 | Base URL configurable | `openai_base_url` for custom endpoints | P1 |
| BR-112 | Sleep 0.1s between API calls | `time_sleep()` prevents rate limiting | P2 |
| BR-113 | Temperature 0.7 for planning/rating | Lower temperature for more consistent outputs | P2 |
| BR-114 | Temperature 0.8 for general requests | Default GPT_request temperature | P2 |
| BR-115 | Handle API errors gracefully | Return `"ERROR: {str(e)}"` on failure | P0 |

---

## 4. Validation Rules

### 4.1 Input Validation

| Rule ID | Rule | Description | Priority |
|---------|------|-------------|----------|
| BR-200 | Project name must be non-empty string | Validated before project initialization | P0 |
| BR-201 | Repeats must be positive integer | Validated before simulation loop | P1 |
| BR-202 | Starting location must exist in world graph | Warning logged if not found | P1 |
| BR-203 | Prompt cannot be empty or whitespace | ValueError raised in GPT_request | P0 |

### 4.2 Data Validation

| Rule ID | Rule | Description | Priority |
|---------|------|-------------|----------|
| BR-210 | JSON files must be valid JSON | Handled by `json.load()` exceptions | P0 |
| BR-211 | SQLite tables created if not exist | `CREATE TABLE IF NOT EXISTS` used | P0 |
| BR-212 | Rating must be parseable as integer | `get_rating()` extracts digits via regex | P1 |
| BR-213 | Embedding cannot be empty | Default to "this is blank" if empty | P2 |

---

## 5. Output Rules

### 5.1 Logging Rules

| Rule ID | Rule | Description | Priority |
|---------|------|-------------|----------|
| BR-300 | Logs written to `simulation_log.txt` | Append mode, UTF-8 encoding | P0 |
| BR-301 | Logs include round number and global time | Format: `=== ROUND {N} TIME {T} ===` | P1 |
| BR-302 | Logs can be toggled per category | `log_locations`, `log_actions`, etc. | P2 |
| BR-303 | Logs can be printed to console | `print_locations`, `print_actions`, etc. | P2 |

### 5.2 Summary Rules

| Rule ID | Rule | Description | Priority |
|---------|------|-------------|----------|
| BR-310 | Summaries generated at end of day | Only when `if_new_day(next_time)` is True | P1 |
| BR-311 | Summaries written to `simulation_summary.txt` | Append mode, UTF-8 encoding | P0 |
| BR-312 | Summaries use LLM to generate narrative | `summarize_simulation()` function | P1 |
| BR-313 | Summaries can be toggled per category | `summarize_actions`, `summarize_locations`, etc. | P2 |
