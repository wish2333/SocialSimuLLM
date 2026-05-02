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
│                    │    │    ├── WorldVariationGenerator  │
│  ExperimentConfig   │    │    ├── FieldOfView             │
│    ↓ to_simulation  │    │    ├── PathPlanner            │
│      _config()      │    │    ├── GoalManager            │
│                    │    │    └── Assemble SimulationState │
│  runs/{proj}/{id}/  │    │                                │
└────────┬───────────┘    │  step() per 10-min interval   │
         │                │    ├── _daily_planning()      │
         │                │    │     └── GoalManager       │
         │                │    ├── _hourly_planning()     │
         │                │    │     └── FOV context       │
         │                │    ├── _execute_actions()     │
         │                │    │     └── FOV context       │
         │                │    ├── _movement()            │
         │                │    │     └── PathPlanner       │
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
    │  experiment/scenario.py (NL generation)            │
    │  experiment/assistant.py (AI analysis)             │
    └────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│              Streamlit Frontend (frontend/)            │
│                                                        │
│  app.py ── tabs: Configure | Results | Assistant      │
│  configure.py ── form + launch_experiment subprocess   │
│  results.py ── checkpoint viewer + replay + heatmaps   │
│  assistant.py ── AI research analysis interface       │
│  components/forms.py ── pydantic-to-streamlit mapping  │
│  components/viz.py ── pyvis + plotly rendering        │
│  components/replay.py ── checkpoint timeline replay    │
│  components/heatmap.py ── occupancy/activity/transit   │
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
  │     ├── world/spatial.py          # Phase 3: WorldVariationGenerator
  │     ├── world/field_of_view.py    # Phase 3: FieldOfView
  │     ├── world/path_planner.py     # Phase 3: PathPlanner
  │     ├── cognition/goal.py         # Phase 3: GoalManager + ROMA
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
        │     ├── world/spatial.py     # Phase 3: spatial graph generation
        │     └── simulator/core.py (lazy)
        ├── experiment/storage.py
        │     └── yaml
        ├── experiment/analysis.py
        │     └── experiment/storage.py
        ├── experiment/scenario.py     # Phase 3: NL scenario generation
        │     └── utils/text_generation.py
        └── experiment/assistant.py    # Phase 3: AI research assistant
              └── experiment/storage.py, experiment/analysis.py

frontend/ (optional deps, runs as separate Streamlit process)
  ├── frontend/pages/configure.py
  │     ├── experiment/config.py
  │     └── frontend/utils.py
  ├── frontend/pages/results.py
  │     ├── experiment/storage.py
  │     ├── experiment/analysis.py
  │     ├── frontend/components/viz.py
  │     ├── frontend/components/replay.py   # Phase 3
  │     └── frontend/components/heatmap.py  # Phase 3
  ├── frontend/pages/assistant.py           # Phase 3
  │     └── experiment/assistant.py
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
            │     ├── If spatial_config: WorldVariationGenerator.generate_town_data()
            │     ├── If scenario_description: ScenarioGenerator.generate()
            │     └── Else: copy town_data.json -> runs/{proj}/{id}/
            ├── config.to_yaml(run_dir / "config.yaml")
            ├── config.to_simulation_config() -> SimulationConfig
            │     └── project_name = str(run_dir)  # absolute path
            ├── _apply_config_to_globals() + validate_config()
            └── SimulatorCore(sim_config, initial_event)
                  ├── .initialize()
                  │     ├── _create_world_graph()      # delegate to WorldVariationGenerator
                  │     ├── FieldOfView(spatial_graph)  # if fov_enabled
                  │     ├── PathPlanner(spatial_graph)  # if path_planner_enabled
                  │     └── GoalManager()               # if goal_enabled
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

### Spatial Perception Flow (Phase 3)

```
SimulatorCore._hourly_planning() / _execute_actions()
  └── FieldOfView.get_visible_agents(observer, all_agents)
        ├── Compute graph distance from observer to each agent
        ├── Filter by distance_threshold
        └── Return list[PerceptibleAgent]

FieldOfView.format_nearby_context(observer, all_agents)
  └── Formatted string for LLM prompt (who is visible, where, distance)
```

### Movement Planning Flow (Phase 3)

```
SimulatorCore._movement(agent)
  └── PathPlanner.plan_movement(agent, hourly_plan, visible_agents)
        ├── infer_movement_intent()  ──► LLM: where does agent want to go?
        ├── find_path(origin, dest)   ──► A* shortest path on weighted graph
        └── PlannedPath | None

If multi_hop_movement:
  └── PathPlanner.execute_step(planned_path)  ──► next node on path
  └── Agent.planned_path updated with steps_remaining--
```

### Goal Management Flow (Phase 3)

```
SimulatorCore._daily_planning() (08:00)
  └── GoalManager.review_and_update_goals(agent, recent_memories, global_time)
        ├── Check existing goals for completion
        ├── Create new goals from agent description + events
        └── RecursiveTaskDecomposer.decompose() for active goals

GoalManager.format_goals_context(goals)
  └── Injected into daily planning LLM prompt
```

### Scenario Generation Flow (Phase 3)

```
ScenarioGenerator.generate(scenario_description)
  ├── LLM generates town_data.json from natural language
  ├── _normalize_structure() ensures schema compliance
  ├── _static_validation() checks structural correctness
  ├── _llm_validation() checks semantic coherence
  └── Return validated town_data dict
```

### Research Assistant Flow (Phase 3)

```
ResearchAssistant.summarize_experiment(experiment_id, project)
  ├── Load events from experiment storage
  ├── Build summary context from events.jsonl
  └── LLM generates natural language summary

ResearchAssistant.identify_patterns(experiment_id, project)
  ├── Load events + checkpoints
  ├── Compute behavioral statistics
  └── LLM identifies emergent patterns

ResearchAssistant.compare_runs(experiment_ids, project)
  ├── Load data from multiple experiments
  └── LLM generates comparative analysis
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

Phase 3 adds:
6. SpatialConfig (topology, num_locations, edge_weight_range, seed)
7. FOVConfig (enabled, distance_threshold)
8. PathPlannerConfig (enabled, multi_hop, max_path_length)
9. GoalConfig (enabled, max_active_goals, goal_retention_days)
10. scenario_description (NL input for town_data generation)
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
│       ├── memory_summary.json # Memory statistics
│       └── goals.json          # Phase 3: Goal state snapshot
└── agent_data/
    ├── {name}_memory.json      # Memory records (MemoryEntry dicts)
    └── {name}_memory.db        # SQLite embedding DB
```

### Experiment Mode (runs/)

```
runs/{project}/{experiment_id}/
├── config.yaml                # Full experiment config snapshot
├── town_data.json             # Copied or generated town configuration
├── simulation_log.txt         # Human-readable text log
├── events.jsonl               # Structured JSONL event log
├── done.flag                  # Completion marker
├── checkpoints/
│   └── step_{N}/
│       ├── spatial_graph.json  # NetworkX graph snapshot
│       ├── agent_states.json   # All agent state snapshots
│       ├── memory_summary.json # Memory statistics
│       ├── goals.json          # Phase 3: Goal state snapshot
│       └── meta.json           # Run metadata
└── agent_data/
    ├── {name}_memory.json     # Memory records (MemoryEntry dicts)
    └── {name}_memory.db       # SQLite embedding DB
```
