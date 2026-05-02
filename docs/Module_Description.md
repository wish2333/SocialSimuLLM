## Module Description

### agents/agent.py (276 lines)

Core `Agent` class representing a simulation participant. Contains all agent methods as proper class methods (no MethodType binding).

**Key methods:**
- `memory_actions()` -> `MemoryEntry`: Records current action
- `memory_daily_plans()` -> `MemoryEntry`: Records daily plan
- `memory_hourly_plan()` -> `MemoryEntry`: Records hourly plan
- `memory_location_change()` -> `MemoryEntry`: Records location change
- `memory_impression()` -> `MemoryEntry`: Records impression of another agent
- `rate_locations()`: LLM-based location preference rating
- `move()`: Execute location change via world graph
- `simplify_action()`: Compress action into 1-2 SVO sentences

### agents/memory.py (374 lines)

`AgentMemory` class providing unified memory storage and multi-dimensional retrieval. Manages per-agent JSON files and SQLite embedding databases.

**Key methods:**
- `store(entry: MemoryEntry)`: Route and persist by event_type (action/plan/thought/event/reflection)
- `recall_recent(n)`: Most recent N entries
- `recall_semantic(query, top_k)`: Embedding similarity search (0.5*sim + 0.3*rec + 0.2*imp)
- `recall_by_location(location_id)`: Filter by location
- `recall_time_span(start, end)`: Filter by time range
- `recall_by_importance(min_importance)`: Filter by importance threshold
- `recall_reflections(n)`: Recent reflection entries
- `recall_filtered(...)`: Combined filtering (type + location + importance + time)
- `format_*_for_agent()`: Format recall results as strings for LLM prompts

### agents/memory_entry.py (153 lines)

`MemoryEntry` frozen dataclass defining the canonical memory record structure.

**Fields:** id (UUID), agent_name, timestamp, location_id, event_type, content, summary, entities, importance, embedding, reflection_link, reflection_type, metadata

**Key methods:**
- `create(...)`: Factory with auto-generated UUID
- `to_dict()`: Serialize to plain dict for JSON storage
- `from_dict(data)`: Deserialize with v3.0 backward compatibility

### agents/reflection.py (392 lines)

`ReflectionEngine` class implementing multi-level agent reflection following Generative Agents (Park et al. 2023). Uses Protocol-based coupling to AgentMemory and Agent interfaces.

**Key methods:**
- `reflect_daily()`: End-of-day summary reflection
- `reflect_pattern()`: Cross-day behavioral pattern identification (requires >= 2 daily reflections)
- `reflect_social()`: Relationship trend analysis with other agents
- `reflect_all()`: Complete reflection cycle returning `list[MemoryEntry]`
- `should_reflect()`: Threshold-based trigger check

**Configuration:** `ReflectionConfig` dataclass with threshold (default 15), importance priorities per type.

### simulator/core.py (423 lines)

`SimulatorCore` class orchestrating the simulation loop.

**Key methods:**
- `initialize()`: Load town data, create agents/locations/graph, assemble SimulationState
- `step()`: Execute one 10-minute step (daily/hourly planning, actions, movement, impressions, reflection, events)
- `run(max_steps)`: Main loop with checkpointing and summary generation

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

### utils/text_generation.py (125 lines)

OpenAI-compatible API integration. Provides `GPT_request()` for text generation and `get_embedding()` for vector embeddings. Supports custom base_url.

### utils/global_methods.py (144 lines)

Utility functions for file I/O, time manipulation, JSON handling, and simulation data management.

### locations/locations.py (71 lines)

`Location` and `Locations` classes managing the spatial world. Simple ring graph with NetworkX pathfinding.

### prompt_templates/template_agents.py (152 lines)

All LLM prompt templates for agent planning, action, movement, impression, reflection, and location rating.
