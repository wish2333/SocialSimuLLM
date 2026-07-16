# Development Guide

## Project Structure

```
SocialSimuLLM/
├── pyproject.toml                     # Project config & dependencies (v3.1.0)
├── src/socialsimullm/                 # Source package
│   ├── __main__.py                    # CLI entry point (96 lines)
│   ├── agents/                        # Agent behavior, memory, reflection
│   │   ├── agent.py                   # Agent class + dialogue + nearby awareness (310 lines)
│   │   ├── memory.py                  # AgentMemory unified store/recall + active events (402 lines)
│   │   ├── memory_entry.py            # MemoryEntry frozen dataclass (153 lines)
│   │   └── reflection.py              # ReflectionEngine + cooldown (395 lines)
│   ├── simulator/                     # Simulation engine
│   │   ├── core.py                    # SimulatorCore: dialogue, nearby, events (657 lines)
│   │   ├── state.py                   # SimulationState dataclass (46 lines)
│   │   └── events.py                  # EventBus pub/sub (51 lines)
│   ├── world/                         # Spatial world modeling (Phase 3)
│   │   ├── __init__.py               # Package init (13 lines)
│   │   ├── spatial.py                 # WorldVariationGenerator (278 lines)
│   │   ├── field_of_view.py           # FieldOfView proximity perception (234 lines)
│   │   └── path_planner.py            # PathPlanner A* + LLM intent (341 lines)
│   ├── cognition/                     # Cognitive modules (Phase 3)
│   │   ├── __init__.py               # Package init (13 lines)
│   │   └── goal.py                    # GoalManager + RecursiveTaskDecomposer (760 lines)
│   ├── experiment/                    # Experiment infrastructure
│   │   ├── __init__.py               # Public exports (43 lines)
│   │   ├── config.py                  # ExperimentConfig Pydantic model (289 lines)
│   │   ├── runner.py                  # ExperimentRunner (250 lines)
│   │   ├── storage.py                 # Run directory + checkpoint helpers (281 lines)
│   │   ├── analysis.py                # Result loading + DataFrame export (179 lines)
│   │   ├── scenario.py                # ScenarioGenerator NL->town_data (370 lines)
│   │   └── assistant.py               # ResearchAssistant AI analysis (298 lines)
│   ├── frontend/                      # Streamlit web UI (optional deps)
│   │   ├── __init__.py               # Package init (3 lines)
│   │   ├── app.py                     # Main entry, three-tab layout (38 lines)
│   │   ├── pages/
│   │   │   ├── configure.py           # Experiment config form (138 lines)
│   │   │   ├── results.py             # Result visualization + replay + heatmaps (266 lines)
│   │   │   └── assistant.py           # AI research assistant page (177 lines)
│   │   ├── components/
│   │   │   ├── forms.py               # Pydantic-to-Streamlit mapping (104 lines)
│   │   │   ├── viz.py                 # pyvis + plotly rendering (137 lines)
│   │   │   ├── replay.py              # Checkpoint timeline replay (141 lines)
│   │   │   └── heatmap.py             # Heatmap visualizations (199 lines)
│   │   └── utils.py                   # Subprocess launch, polling (89 lines)
│   ├── locations/                     # Location management
│   │   └── locations.py               # Location/Locations classes (71 lines)
│   ├── prompt_templates/              # LLM prompt templates
│   │   └── template_agents.py         # Prompts + dialogue + nearby agent suffixes (181 lines)
│   ├── utils/                         # Infrastructure utilities
│   │   ├── config.py                  # SimulationConfig + experiment config parser (343 lines)
│   │   ├── logger.py                  # StructuredLogger JSONL+text (312 lines)
│   │   ├── text_generation.py         # GPT_request + GPT_request_json (325 lines)
│   │   └── global_methods.py          # File I/O, time parse + compare (154 lines)
│   └── data/                          # Template data files
│       └── town_data_template.json    # Town configuration template
├── notebooks/                         # Jupyter analysis templates (Phase 3)
│   ├── data_loader.py                 # Shared data loading utilities (218 lines)
│   ├── 00_quick_start.ipynb           # Quick start notebook
│   ├── 01_behavioral_analysis.ipynb   # Behavioral analysis notebook
│   ├── 02_spatial_analysis.ipynb      # Spatial analysis notebook
│   └── 03_experiment_comparison.ipynb # Experiment comparison notebook
├── projects/                          # Legacy simulation output data
├── runs/                              # Experiment output data (gitignored)
├── docs/                              # Documentation
├── references/                        # Reference materials
└── tests/                             # Test files
```

## Environment Setup

1. **Install Dependencies:** `uv` is used for dependency management.

   ```bash
   uv sync
   ```

2. **Install optional dependencies** (frontend / analysis):

   ```bash
   uv sync --extra frontend   # Streamlit + pyvis + plotly + pandas
   uv sync --extra analysis   # pandas + plotly only
   ```

3. **Configure LLM API:**

   Set environment variables (preferred):
   ```bash
   export OPENAI_API_KEY="your-key"
   export OPENAI_BASE_URL="https://your-endpoint/v1"  # optional
   ```

   Or configure in `src/socialsimullm/utils/config.py` as defaults.

## Running the Simulation

### Legacy Mode (single run, projects/ output)

```bash
# Interactive mode (prompts for project name and steps)
uv run socialsimullm

# With CLI arguments
uv run socialsimullm --project my_town --steps 288

# With model override
uv run socialsimullm --project my_town --model deepseek-chat

# Disable reflection
uv run socialsimullm --project my_town --no-reflection

# Custom reflection threshold
uv run socialsimullm --project my_town --reflection-threshold 20
```

### Experiment Mode (reproducible, runs/ output)

```bash
# Single experiment run
uv run socialsimullm run --config experiments/my_exp.yaml --id exp001

# Batch experiment with multiple seeds
uv run socialsimullm batch --config experiments/my_exp.yaml --seeds 42,43,44

# List all experiments
uv run socialsimullm list
uv run socialsimullm list --project my_project
```

### Frontend (Streamlit Web UI)

```bash
uv run streamlit run src/socialsimullm/frontend/app.py
```

### CLI Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--project` | (prompt) | Project name (legacy mode) |
| `--steps` | 144 | Simulation steps (1 step = 10 min) |
| `--model` | Config default | LLM model name |
| `--checkpoint-interval` | 10 | Steps between checkpoint saves |
| `--no-reflection` | (disabled) | Disable the reflection system |
| `--reflection-threshold` | 15 | Importance threshold for mid-day reflection |
| `--no-json-mode` | (enabled) | Disable JSON output mode for DeepSeek V4 |
| `--fov-enabled` | (disabled) | Enable proximity-based agent perception |
| `fov-distance` | 0 | Max graph distance for visibility (0 = same location only) |
| `--path-planner-enabled` | (disabled) | Enable LLM intent + A* path planning |
| `--multi-hop-movement` | (disabled) | Agents traverse one graph node per step |
| `--goal-enabled` | (disabled) | Enable goal-driven hierarchical planning |
| `--max-active-goals` | 5 | Max concurrent active goals per agent |

### Experiment Config YAML

```yaml
experiment_id: exp_test_001
project: my_project
model: gpt-4o-mini
embedding_model: BAAI/bge-m3
simulation_steps: 144
memory_limit: 10
random_seed: 42
checkpoint_interval: 10
spatial_graph_path: ""   # empty = default template
events:
  - "A strange fog rolls into town."
  - "The merchant announces a festival."
  - "A traveling circus arrives | Day 2, 10:00 - Day 4, 18:00"  # time-bounded event
reflection_enabled: true

# Phase 3: Spatial configuration
spatial_config:
  topology: ring            # ring | small_world | grid | random | scale_free
  num_locations: 4
  edge_weight_range: [1.0, 1.0]
  seed: 42

# Phase 3: Perception
fov_enabled: false
fov_distance: 0             # 0 = same location only (legacy)

# Phase 3: Movement
path_planner_enabled: false
multi_hop_movement: false

# Phase 3: Goals
goal_enabled: false
max_active_goals: 5

# Phase 3: Scenario generation
# scenario_description: "A medieval village with 6 traders and a mysterious artifact"

# Phase 3: Memory weights
memory_config:
  recency_weight: 0.3
  similarity_weight: 0.5
  importance_weight: 0.2
```

## Architecture Overview

### Simulation Loop

Each step in `SimulatorCore.step()` executes:

1. **Time Advancement**: Increment 10-minute clock, check for day boundary
2. **Event Refresh**: Filter global events by time range, update active events for all agents
3. **Daily Planning** (08:00): All agents generate full-day plans via LLM
   - Goal management: `GoalManager.review_and_update_goals()`
   - Goals context injected into planning prompt
4. **Hourly Planning**: Agents generate next-hour plans
   - FOV context: visible agents within graph distance
   - Path context: current planned path if multi-hop movement
   - Recent actions: last 5 actions to prevent repetitive behavior
5. **Action Execution**: Each agent acts based on their plan and current context
   - **Nearby agents**: sees what other co-located agents are doing (including dialogues directed at them)
   - **Dialogue output**: agent may produce `dialogue_target` + `dialogue_content` alongside action
6. **Dialogue Storage**: Bidirectional -- both speaker and listener store the exchange in memory
7. **Location Rating + Movement**: Agents rate locations and may move
   - With PathPlanner: LLM infers movement intent, A* finds shortest path
   - Multi-hop: agent moves one graph node per step
8. **Impression Formation**: Agents form impressions of co-located agents
9. **Reflection**: Daily (end of day) or threshold-based (mid-day) reflection
   - Cooldown: `min_cooldown_steps=6` (max once per in-game hour) prevents flooding

### LLM Integration: JSON Output Mode

Two parallel LLM call functions in `utils/text_generation.py`:

| Function | Return Type | Used By | JSON Mode |
|----------|-----------|---------|-----------|
| `GPT_request()` | `str` | experiment/assistant.py, experiment/scenario.py | No |
| `GPT_request_json()` | `dict` | agents, reflection, goal, path_planner | DeepSeek V4 only |

**Retry strategy (DeepSeek V4 only):**

```
Attempt 1: JSON mode (response_format=json_object)
    |
    +-- parse failure? --> Attempt 2: JSON mode retry
    |                       |
    |                       +-- parse failure? --> Attempt 3: Plain text mode (no response_format)
    |                                               |
    |                                               +-- empty response? --> Return preset fallback dict
    |                                               |                       with "_error": True flag
    |                                               +-- non-empty? --> Return {"text": raw_content}
    +-- success --> Return parsed dict
```

Non-DeepSeek models: single plain text attempt, then fallback. No `response_format` is ever sent.

**Preset fallback values** (injected when all attempts fail):

| Call Site | Key | Fallback |
|-----------|-----|----------|
| daily_planning | `plan` | `[8:00 - Wake up and start the day.\n20:00 - Go to bed.]` |
| hourly_planning | `plan` | `Continue with current activity.` |
| execute_action | `action` | `Idle[action]: Observing surroundings.[details]` |
| form_impression | `impression` | `Neutral, observing.` |
| rate_locations | `rating` | `5` |
| rate_experience | `rating` | `5` |
| simplify_action | `summary` | `{agent_name} did something.` |
| reflect_daily | `reflection` | `Nothing notable happened.` |
| reflect_pattern | `reflection` | `No clear pattern identified.` |
| reflect_social | `reflection` | `No social observations yet.` |
| initialize_goals | `text` | `5: Explore the surroundings` |
| review_and_update_goals | `text` | `CONTINUE` |
| decompose_goal | `text` | `5: Take first step toward ...` |
| order_by_dependency | `text` | `[id] description` for each goal |
| infer_movement_intent | `destination` | `STAY` |

**Configuration:**
- `json_mode_enabled: bool = True` in `SimulationConfig` (default: enabled)
- `--no-json-mode` CLI flag to disable
- Falls back to `GPT_request()` path when disabled or model is not DeepSeek V4

### Memory System

- **MemoryEntry**: Immutable frozen dataclass with 13 fields (id, agent_name, timestamp, location_id, event_type, content, summary, entities, importance, embedding, reflection_link, reflection_type, metadata)
- **Storage**: Per-agent JSON files + per-agent SQLite embedding databases
- **Retrieval Scoring**: `0.5*similarity + 0.3*recency + 0.2*importance`
- **Event Types**: `action`, `plan`, `thought`, `event`, `reflection`, `dialogue`
- **Active events**: `load_active_events(global_time)` filters events by time range; events without ranges remain permanently active

### Reflection System

- **ReflectionEngine**: Standalone class with Protocol-based coupling
- **Three types**: daily (end-of-day), pattern (cross-day), social (relationship)
- **Two triggers**: scheduled (day end) + threshold (cumulative importance)
- **Cooldown**: `min_cooldown_steps=6` (max once per in-game hour); cumulative importance excludes `event_type="reflection"` to prevent positive feedback loop
- Reflections are stored as `MemoryEntry` with `event_type="reflection"`

### Agent Interaction System

- **Dialogue**: Agents produce `dialogue_target` + `dialogue_content` during action execution
  - Prompt requires JSON output with `action`, `dialogue_target`, `dialogue` fields
  - Bidirectional storage: both speaker and listener retain the exchange in memory
  - Dialogue is embedded within actions (no extra turns consumed)
- **Nearby agent awareness**: `_format_nearby_agents()` in `SimulatorCore`
  - Collects recent actions of agents at the same location
  - Highlights dialogues directed at the current agent
  - Injected into `execute_action` prompt as `nearby_agents_info`
- **Recent action history**: Agent tracks last 5 actions in `recent_actions: list[str]`
  - Injected into planning and action prompts
  - Allows cross-round sustained activities (walking, talking) but forbids verbatim copy

### Spatial World (Phase 3)

- **WorldVariationGenerator**: Creates diverse graph topologies (ring, small_world, grid, random, scale_free)
- **FieldOfView**: Graph distance-based proximity perception for agents
- **PathPlanner**: LLM movement intent inference + A* shortest path with multi-hop support
- **Backward compatibility**: All disabled by default; legacy ring graph behavior preserved

### Goal System (Phase 3)

- **GoalManager**: Manages agent goal lifecycle (create, review, update, complete, abandon)
- **Goal**: Persistent hierarchical dataclass with sub-goals and completion conditions
- **RecursiveTaskDecomposer**: Breaks high-level goals into ordered actionable sub-goals
- **Persistence**: Goals serialized to checkpoints for cross-day continuity

### Experiment Infrastructure

- **ExperimentConfig (Pydantic)**: Validated config with YAML serialization, wraps SimulationConfig
- **ExperimentRunner**: Single and batch execution with seed management
- **ScenarioGenerator**: Natural language -> town_data.json via LLM synthesis
- **Storage**: Standardized `runs/{project}/{id}/` directory layout; also supports flat `runs/{id}/` layout
- **Analysis**: JSONL loading, DataFrame export, cross-run comparison
- **ResearchAssistant**: AI-powered experiment analysis (summary, patterns, hypotheses, reports)

### Configuration

Three config layers:

1. **SimulationConfig** (dataclass): Legacy CLI args, env vars, runtime validation
2. **ExperimentConfig** (Pydantic): YAML-based experiment setup with `to_simulation_config()` bridge
3. **SpatialConfig / FOVConfig / PathPlannerConfig / GoalConfig** (dataclasses): Phase 3 feature flags and parameters

CLI mode detection: first arg is `run`/`batch`/`list` -> experiment mode; otherwise -> legacy mode.

### Logging

`StructuredLogger` produces:
- `events.jsonl`: Machine-readable event log (loadable via `pd.read_json(path, lines=True)`)
- `simulation_log.txt`: Human-readable text log
- `checkpoints/`: State snapshots at configurable intervals (including goal state)
- `done.flag`: Completion marker

### Frontend

Three-tab Streamlit application:

1. **Configure**: Experiment form with all Phase 3 config options
2. **Results**: Checkpoint viewer, spatial graph, agent charts, replay timeline, heatmaps
3. **Assistant**: AI-powered research analysis (summary, patterns, hypotheses, report, comparison)

## Key Design Decisions

1. **Immutable data**: `MemoryEntry` is a frozen dataclass; `SimulationState` is passed between methods
2. **Protocol coupling**: `ReflectionEngine` uses `Protocol` for `AgentMemory` and `Agent` interfaces
3. **Backward compatibility**: `MemoryEntry.from_dict()` handles both v3.0 and v3.1.0 field names; all Phase 3 features disabled by default
4. **File-size limits**: Target 200-400 lines per file, max 800 lines
5. **Config isolation**: `ExperimentConfig` (Pydantic) never stores API keys; `SimulatorCore` only sees `SimulationConfig` (dataclass)
6. **Frontend decoupling**: Streamlit frontend communicates via files (subprocess + done.flag polling), never imports simulator core
7. **Optional complexity**: Phase 3 features (world, FOV, path planner, goals) are all opt-in via config flags; legacy mode runs identically to Phase 2
8. **JSON Output Mode for DeepSeek V4**: All simulation calls use `GPT_request_json()` with structured retry; non-DeepSeek models and experiment tools are completely unaffected
9. **Embedded dialogue**: Conversations happen within action turns (no extra LLM calls), stored bidirectionally in both agents' memories
10. **Time-bounded events**: Events support optional time ranges (`"Event | Day 1, 08:00 - Day 3, 20:00"`); backward compatible with permanent events
11. **Reflection throttle**: Cooldown mechanism (`min_cooldown_steps=6`) prevents reflection flooding; importance scoring excludes reflection entries to avoid positive feedback

## Coding Conventions

- Type annotations on all public functions
- No wildcard imports
- No emojis in code (terminal compatibility)
- No hardcoded values (use config)
- Error handling at system boundaries
- Files under `src/socialsimullm/` (setuptools src layout)
