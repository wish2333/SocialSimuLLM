# System Design

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   __main__.py                        │
│               CLI entry (27 lines)                   │
│         load_config() -> SimulatorCore              │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              SimulatorCore (core.py)                 │
│                                                      │
│  initialize()                                        │
│    ├── Load town_data.json                          │
│    ├── Create Agents, Locations, WorldGraph         │
│    ├── Create AgentMemory, StructuredLogger         │
│    └── Assemble SimulationState                     │
│                                                      │
│  step() ── per 10-minute interval                   │
│    ├── _daily_planning()     [08:00 trigger]        │
│    ├── _hourly_planning()    [top of hour]          │
│    ├── _execute_actions()    [all agents]            │
│    ├── _movement()           [rate + move]           │
│    ├── _impressions()        [co-located agents]     │
│    ├── _run_reflection()     [scheduled/threshold]   │
│    └── _load_events()        [global events]         │
│                                                      │
│  run(max_steps)                                      │
│    └── loop step() + checkpoint + summary            │
└──────────┬──────────┬──────────┬───────────────────┘
           │          │          │
    ┌──────▼──────┐ ┌▼────────┐ ┌▼──────────────┐
    │  agents/    │ │ utils/  │ │ simulator/     │
    │            │ │         │ │                 │
    │ Agent      │ │ Config  │ │ SimulationState │
    │ AgentMemory│ │ Logger  │ │ EventBus        │
    │ MemoryEntry│ │ TextGen │ │                 │
    │ Reflection │ │ Helpers │ │                 │
    └────────────┘ └─────────┘ └─────────────────┘
```

## Module Dependency Graph

```
__main__.py
  └── simulator/core.py
        ├── simulator/state.py
        ├── simulator/events.py
        ├── agents/agent.py
        │     └── agents/memory_entry.py
        ├── agents/memory.py
        │     └── agents/memory_entry.py
        ├── agents/reflection.py
        │     └── agents/memory_entry.py
        ├── locations/locations.py
        ├── utils/config.py
        ├── utils/logger.py
        ├── utils/text_generation.py
        └── utils/global_methods.py
```

No circular dependencies. `memory_entry.py` is the leaf dependency -- imported by agent.py, memory.py, and reflection.py.

## Data Flow

### Memory Storage Flow

```
Agent.memory_actions() ──► MemoryEntry.create() ──► AgentMemory.store()
Agent.memory_impression() ──► MemoryEntry.create() ──► AgentMemory.store()
ReflectionEngine ──► MemoryEntry.create() ──► AgentMemory.store()

AgentMemory.store(entry):
  ├── entry.event_type == "action"
  │     ├── Save to acting agent's JSON
  │     ├── Fan out to co-located agents' JSON
  │     └── Embed summary in SQLite
  ├── entry.event_type in ("plan", "thought")
  │     └── Save to agent's JSON only
  ├── entry.event_type == "event"
  │     └── Save to ALL agents' JSON
  └── entry.event_type == "reflection"
        └── Save to agent's JSON + embed in SQLite
```

### Recall Flow

```
AgentMemory.recall_recent(n)
AgentMemory.recall_semantic(query, top_k)
AgentMemory.recall_by_location(location_id)
AgentMemory.recall_time_span(start, end)
AgentMemory.recall_by_importance(min_importance)
AgentMemory.recall_filtered(...)          ← combined filtering
  └── Returns list[MemoryEntry]

format_recent_for_agent(agent_name)        ← string for LLM prompt
format_semantic_for_agent(agent_name)      ← string for LLM prompt
format_locations_for_agent(agent_name)     ← string for LLM prompt
format_impressions_for_agent(agent_name)   ← string for LLM prompt
```

### Reflection Flow

```
SimulatorCore._run_reflection(agent, trigger)
  └── ReflectionEngine.reflect_all(agent, global_time, all_agents)

reflect_all():
  1. Check daily trigger (end of day)
  2. Check threshold trigger (cumulative importance >= threshold)
  3. If triggered:
     a. reflect_daily()   ──► MemoryEntry (event_type="reflection")
     b. reflect_pattern() ──► MemoryEntry | None (needs >= 2 daily refs)
     c. reflect_social()  ──► MemoryEntry | None (needs interaction data)
  4. Return list[MemoryEntry]
```

## Configuration Layers

```
Priority (highest to lowest):

1. CLI arguments (--project, --model, --steps, etc.)
2. Environment variables (OPENAI_API_KEY, OPENAI_BASE_URL, DEFAULT_MODEL)
3. SimulationConfig defaults in config.py
4. Town data (town_data.json, per-project)
```

## Storage Layout

```
projects/{name}/
├── town_data.json              # Town configuration (areas, agents)
├── simulation_log.txt          # Human-readable text log
├── events.jsonl                # Structured JSONL event log
├── done.flag                   # Completion marker
├── checkpoints/
│   └── step_{N}/
│       ├── spatial_graph.json  # NetworkX graph snapshot
│       ├── agent_states.json   # All agent state snapshots
│       └── memory_summary.json # Memory statistics
└── agent_data/
    ├── {name}_memory.json      # Memory records (MemoryEntry dicts)
    └── {name}_memory.db        # SQLite embedding DB
```
