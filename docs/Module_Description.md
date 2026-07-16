## Module Description

### agents/agent.py (310 lines)

Core `Agent` class representing a simulation participant. Contains all agent methods as proper class methods (no MethodType binding). Supports dialogue generation and nearby agent awareness.

**Key methods:**
- `memory_actions()` -> `MemoryEntry`: Records current action
- `memory_daily_plans()` -> `MemoryEntry`: Records daily plan
- `memory_hourly_plan()` -> `MemoryEntry`: Records hourly plan
- `memory_location_change()` -> `MemoryEntry`: Records location change
- `memory_impression()` -> `MemoryEntry`: Records impression of another agent
- `memory_dialogue()` -> `MemoryEntry`: Records dialogue exchange
- `rate_locations()`: LLM-based location preference rating
- `move()`: Execute location change via world graph
- `simplify_action()`: Compress action into 1-2 SVO sentences
- `execute_action(...)`: Execute action with nearby agent context and dialogue output

**Attributes:** `dialogue_target`, `dialogue_content`, `recent_actions: list[str]` (last 5 actions)

### agents/memory.py (402 lines)

`AgentMemory` class providing unified memory storage and multi-dimensional retrieval. Manages per-agent JSON files and SQLite embedding databases. Supports time-bounded event filtering.

**Key methods:**
- `store(entry: MemoryEntry)`: Route and persist by event_type (action/plan/thought/event/reflection/dialogue)
- `recall_recent(n)`: Most recent N entries
- `recall_semantic(query, top_k)`: Embedding similarity search (0.5*sim + 0.3*rec + 0.2*imp)
- `recall_by_location(location_id)`: Filter by location
- `recall_time_span(start, end)`: Filter by time range
- `recall_by_importance(min_importance)`: Filter by importance threshold
- `recall_reflections(n)`: Recent reflection entries
- `recall_filtered(...)`: Combined filtering (type + location + importance + time)
- `load_active_events(global_time)`: Filter events by time range, permanently active if no range
- `format_*_for_agent()`: Format recall results as strings for LLM prompts

### agents/memory_entry.py (153 lines)

`MemoryEntry` frozen dataclass defining the canonical memory record structure.

**Fields:** id (UUID), agent_name, timestamp, location_id, event_type, content, summary, entities, importance, embedding, reflection_link, reflection_type, metadata

**Key methods:**
- `create(...)`: Factory with auto-generated UUID
- `to_dict()`: Serialize to plain dict for JSON storage
- `from_dict(data)`: Deserialize with v3.0 backward compatibility

### agents/reflection.py (395 lines)

`ReflectionEngine` class implementing multi-level agent reflection following Generative Agents (Park et al. 2023). Uses Protocol-based coupling to AgentMemory and Agent interfaces. Includes cooldown throttle to prevent flooding.

**Key methods:**
- `reflect_daily()`: End-of-day summary reflection
- `reflect_pattern()`: Cross-day behavioral pattern identification (requires >= 2 daily reflections)
- `reflect_social()`: Relationship trend analysis with other agents
- `reflect_all()`: Complete reflection cycle returning `list[MemoryEntry]`
- `should_reflect(current_step)`: Threshold-based trigger check with cooldown enforcement

**Configuration:** `ReflectionConfig` dataclass with threshold (default 15), importance priorities per type, `min_cooldown_steps=6` (max once per in-game hour).

### simulator/core.py (657 lines)

`SimulatorCore` class orchestrating the simulation loop. Manages nearby agent awareness, dialogue bidirectional storage, and time-bounded event refresh.

**Key methods:**
- `initialize()`: Load town data, create agents/locations/graph, assemble SimulationState
- `step()`: Execute one 10-minute step (event refresh, daily/hourly planning, actions with nearby context, dialogue storage, movement, impressions, reflection with cooldown)
- `run(max_steps)`: Main loop with checkpointing and summary generation
- `_format_nearby_agents(agent, state)`: Collect recent actions of co-located agents for context
- `_refresh_events(state)`: Filter events by time range each step

### simulator/state.py (46 lines)

`SimulationState` dataclass holding all mutable simulation state: global_time, round, agents, locations, world_graph, memory, project_folder, meta_data, town_areas, events.

### simulator/events.py (51 lines)

`EventBus` class providing publish-subscribe mechanism for global simulation events. Currently infrastructure for future use.

### utils/config.py (222 lines)

`SimulationConfig` dataclass with CLI argument parsing and environment variable overrides.

**CLI arguments:** `--project`, `--steps`, `--model`, `--checkpoint-interval`, `--no-reflection`, `--reflection-threshold`

**Functions:** `load_config()`, `validate_config()`

### utils/logger.py (312 lines)

`StructuredLogger` producing JSONL structured logs (`events.jsonl`) and human-readable text logs (`simulation_log.txt`). Supports checkpoint save/restore and `done.flag` completion marker.

**Key methods:** `log_event()`, `add_summary()`, `save_checkpoint()`, `restore_checkpoint()`, `snapshot_memory_stats()`

### utils/text_generation.py (325 lines)

OpenAI-compatible API integration. Provides `GPT_request()` for text generation, `GPT_request_json()` for structured JSON output with 3-attempt retry and preset fallbacks, and `get_embedding()` for vector embeddings. Supports custom base_url and DeepSeek V4 JSON mode.

### utils/global_methods.py (154 lines)

Utility functions for file I/O, time manipulation (`parse_sim_time`, `is_time_in_range`), JSON handling, and simulation data management.

### locations/locations.py (71 lines)

`Location` and `Locations` classes managing the spatial world. Simple ring graph with NetworkX pathfinding.

### prompt_templates/template_agents.py (181 lines)

All LLM prompt templates for agent planning, action, movement, impression, reflection, location rating, and dialogue. Includes JSON instruction suffixes and nearby agent context placeholders.
