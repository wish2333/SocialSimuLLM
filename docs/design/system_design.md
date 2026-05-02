# System Design

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      __main__.py                         │
│               CLI entry (96 lines)                        │
│                                                          │
│  Experiment mode:  run | batch | list                   │
│  Legacy mode:      load_config() -> SimulatorCore       │
└────────────────────────┬────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
┌─────────▼──────────┐    ┌─────────────▼─────────────────┐
│  ExperimentRunner   │    │      SimulatorCore (core.py)  │
│  (runner.py)        │    │                                │
│                    │    │  initialize()                  │
│  run_single()       │    │    ├── Load town_data.json     │
│  run_batch()        │    │    ├── Create Agents, ...     │
│                    │    │    └── Assemble SimulationState │
│  ExperimentConfig   │    │                                │
│    ↓ to_simulation  │    │  step() per 10-min interval   │
│      _config()      │    │    ├── _daily_planning()      │
│                    │    │    ├── _hourly_planning()     │
│  runs/{proj}/{id}/  │    │    ├── _execute_actions()     │
└────────┬───────────┘    │    ├── _movement()            │
         │                │    ├── _impressions()         │
         │                │    ├── _run_reflection()      │
         │                │    └── _load_events()         │
         │                │                                │
         │                │  run(max_steps)                │
         │                │    └── loop step() + ...      │
         │                └──────────┬────────────────────┘
         │                           │
    ┌────▼───────────────────────────▼───────────────────┐
    │  experiment/storage.py + analysis.py               │
    │                                                    │
    │  create_run_dir()  list_experiments()               │
    │  load_checkpoint() find_run_dir()                  │
    │  load_results()    get_experiment_summary()         │
    │  compare_experiments()                              │
    └────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│              Streamlit Frontend (frontend/)            │
│                                                        │
│  app.py ── tabs: Configure | Results                  │
│  configure.py ── form + launch_experiment subprocess   │
│  results.py ── checkpoint viewer + spatial graph + viz │
│  components/forms.py ── pydantic-to-streamlit mapping  │
│  components/viz.py ── pyvis + plotly rendering        │
└────────────────────────────────────────────────────────┘
```

## Module Dependency Graph

```
__main__.py
  ├── utils/config.py (load_config, load_experiment_config)
  ├── simulator/core.py
  │     ├── simulator/state.py
  │     ├── simulator/events.py
  │     ├── agents/agent.py
  │     │     └── agents/memory_entry.py
  │     ├── agents/memory.py
  │     │     └── agents/memory_entry.py
  │     ├── agents/reflection.py
  │     │     └── agents/memory_entry.py
  │     ├── locations/locations.py
  │     ├── utils/config.py
  │     ├── utils/logger.py
  │     ├── utils/text_generation.py
  │     └── utils/global_methods.py
  └── experiment/ (lazy import on subcommand)
        ├── experiment/config.py
        │     └── pydantic, yaml
        ├── experiment/runner.py
        │     ├── experiment/config.py
        │     ├── experiment/storage.py
        │     └── simulator/core.py (lazy)
        ├── experiment/storage.py
        │     └── yaml
        └── experiment/analysis.py
              └── experiment/storage.py

frontend/ (optional deps, runs as separate Streamlit process)
  ├── frontend/pages/configure.py
  │     ├── experiment/config.py
  │     └── frontend/utils.py
  ├── frontend/pages/results.py
  │     ├── experiment/storage.py
  │     ├── experiment/analysis.py
  │     └── frontend/components/viz.py
  ├── frontend/components/forms.py
  │     └── pydantic
  └── frontend/utils.py
        ├── experiment/config.py
        └── experiment/storage.py
```

No circular dependencies. `memory_entry.py` is the leaf dependency. `experiment/` and `frontend/` are isolated from each other (communication via files).

## Data Flow

### Experiment Run Flow

```
CLI: socialsimullm run --config exp.yaml --id test001
  └── ExperimentConfig.from_yaml("exp.yaml")
      └── ExperimentRunner.run_single(config)
            ├── random.seed(config.random_seed)
            ├── create_run_dir(project, experiment_id)
            ├── _prepare_project_data(config, run_dir)
            │     └── copy town_data.json -> runs/{proj}/{id}/
            ├── config.to_yaml(run_dir / "config.yaml")
            ├── config.to_simulation_config() -> SimulationConfig
            │     └── project_name = str(run_dir)  # absolute path
            ├── _apply_config_to_globals() + validate_config()
            └── SimulatorCore(sim_config, initial_event)
                  ├── .initialize()
                  └── .run(max_steps)
                        └── logger.finalize() -> done.flag
```

### Batch Run Flow

```
CLI: socialsimullm batch --config exp.yaml --seeds 42,43,44
  └── ExperimentRunner.run_batch(config, [42, 43, 44])
        ├── For each seed:
        │     ├── Check no existing experiment (FileExistsError guard)
        │     ├── batch_config = config.model_copy(update={experiment_id, random_seed})
        │     └── runner.run_single(batch_config)
        └── Return list[experiment_id]
```

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
AgentMemory.recall_filtered(...)          <-- combined filtering
  └── Returns list[MemoryEntry]
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
2. Environment variables (OPENAI_API_KEY, OPENAI_BASE_URL)
3. SimulationConfig defaults in config.py
4. Town data (town_data.json, per-project)

Experiment mode adds:
5. ExperimentConfig YAML file (experiment_id, random_seed, events, etc.)
   - Converts to SimulationConfig via to_simulation_config()
   - API keys always from env vars, never from YAML
```

## Storage Layout

### Legacy Mode (projects/)

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

### Experiment Mode (runs/)

```
runs/{project}/{experiment_id}/
├── config.yaml                # Full experiment config snapshot
├── town_data.json             # Copied town configuration
├── simulation_log.txt         # Human-readable text log
├── events.jsonl               # Structured JSONL event log
├── done.flag                  # Completion marker
├── checkpoints/
│   └── step_{N}/
│       ├── spatial_graph.json  # NetworkX graph snapshot
│       ├── agent_states.json   # All agent state snapshots
│       ├── memory_summary.json # Memory statistics
│       └── meta.json           # Run metadata
└── agent_data/
    ├── {name}_memory.json     # Memory records (MemoryEntry dicts)
    └── {name}_memory.db       # SQLite embedding DB
```
