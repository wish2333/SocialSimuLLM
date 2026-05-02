# Development Guide

## Project Structure

```
SocialSimuLLM/
├── pyproject.toml                     # Project config & dependencies (v3.1.0)
├── src/socialsimullm/                 # Source package
│   ├── __main__.py                    # CLI entry point (96 lines)
│   ├── agents/                        # Agent behavior, memory, reflection
│   │   ├── agent.py                   # Agent class (276 lines)
│   │   ├── memory.py                  # AgentMemory unified store/recall (374 lines)
│   │   ├── memory_entry.py            # MemoryEntry frozen dataclass (153 lines)
│   │   └── reflection.py              # ReflectionEngine (392 lines)
│   ├── simulator/                     # Simulation engine
│   │   ├── core.py                    # SimulatorCore: step(), run() (427 lines)
│   │   ├── state.py                   # SimulationState dataclass (46 lines)
│   │   └── events.py                  # EventBus pub/sub (51 lines)
│   ├── experiment/                    # Experiment infrastructure
│   │   ├── __init__.py               # Public exports (43 lines)
│   │   ├── config.py                  # ExperimentConfig Pydantic model (216 lines)
│   │   ├── runner.py                  # ExperimentRunner (179 lines)
│   │   ├── storage.py                 # Run directory + checkpoint helpers (281 lines)
│   │   └── analysis.py                # Result loading + DataFrame export (179 lines)
│   ├── frontend/                      # Streamlit web UI (optional deps)
│   │   ├── __init__.py               # Package init (3 lines)
│   │   ├── app.py                     # Main entry, two-tab layout (32 lines)
│   │   ├── pages/
│   │   │   ├── configure.py           # Experiment config form (138 lines)
│   │   │   └── results.py             # Result visualization (174 lines)
│   │   ├── components/
│   │   │   ├── forms.py               # Pydantic-to-Streamlit mapping (104 lines)
│   │   │   └── viz.py                 # pyvis + plotly rendering (137 lines)
│   │   └── utils.py                   # Subprocess launch, polling (89 lines)
│   ├── locations/                     # Location management
│   │   └── locations.py               # Location/Locations classes (71 lines)
│   ├── prompt_templates/              # LLM prompt templates
│   │   └── template_agents.py         # All prompt strings (152 lines)
│   ├── utils/                         # Infrastructure utilities
│   │   ├── config.py                  # SimulationConfig + experiment config parser (293 lines)
│   │   ├── logger.py                  # StructuredLogger JSONL+text (312 lines)
│   │   ├── text_generation.py         # OpenAI API integration (125 lines)
│   │   └── global_methods.py          # File I/O, time helpers (144 lines)
│   └── data/                          # Template data files
│       └── town_data_template.json    # Town configuration template
├── projects/                          # Legacy simulation output data
│   └── {project_name}/
│       ├── town_data.json
│       ├── simulation_log.txt
│       ├── events.jsonl
│       ├── agent_data/
│       │   ├── {name}_memory.json
│       │   └── {name}_memory.db
│       └── checkpoints/
├── runs/                              # Experiment output data (gitignored)
│   └── {project}/{experiment_id}/
│       ├── config.yaml
│       ├── town_data.json
│       ├── events.jsonl
│       ├── done.flag
│       ├── checkpoints/
│       └── agent_data/
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
reflection_enabled: true
```

## Architecture Overview

### Simulation Loop

Each step in `SimulatorCore.step()` executes:

1. **Time Advancement**: Increment 10-minute clock, check for day boundary
2. **Daily Planning** (08:00): All agents generate full-day plans via LLM
3. **Hourly Planning**: Agents generate next-hour plans
4. **Action Execution**: Each agent acts based on their plan and current context
5. **Location Rating + Movement**: Agents rate locations and may move
6. **Impression Formation**: Agents form impressions of co-located agents
7. **Reflection**: Daily (end of day) or threshold-based (mid-day) reflection
8. **Global Events**: Configured or random events may occur

### Memory System

- **MemoryEntry**: Immutable frozen dataclass with 13 fields (id, agent_name, timestamp, location_id, event_type, content, summary, entities, importance, embedding, reflection_link, reflection_type, metadata)
- **Storage**: Per-agent JSON files + per-agent SQLite embedding databases
- **Retrieval Scoring**: `0.5*similarity + 0.3*recency + 0.2*importance`
- **Event Types**: `action`, `plan`, `thought`, `event`, `reflection`

### Reflection System

- **ReflectionEngine**: Standalone class with Protocol-based coupling
- **Three types**: daily (end-of-day), pattern (cross-day), social (relationship)
- **Two triggers**: scheduled (day end) + threshold (cumulative importance)
- Reflections are stored as `MemoryEntry` with `event_type="reflection"`

### Experiment Infrastructure

- **ExperimentConfig (Pydantic)**: Validated config with YAML serialization, wraps SimulationConfig
- **ExperimentRunner**: Single and batch execution with seed management
- **Storage**: Standardized `runs/{project}/{id}/` directory layout
- **Analysis**: JSONL loading, DataFrame export, cross-run comparison

### Configuration

Two config layers:

1. **SimulationConfig** (dataclass): Legacy CLI args, env vars, runtime validation
2. **ExperimentConfig** (Pydantic): YAML-based experiment setup with `to_simulation_config()` bridge

CLI mode detection: first arg is `run`/`batch`/`list` -> experiment mode; otherwise -> legacy mode.

### Logging

`StructuredLogger` produces:
- `events.jsonl`: Machine-readable event log (loadable via `pd.read_json(path, lines=True)`)
- `simulation_log.txt`: Human-readable text log
- `checkpoints/`: State snapshots at configurable intervals
- `done.flag`: Completion marker

## Key Design Decisions

1. **Immutable data**: `MemoryEntry` is a frozen dataclass; `SimulationState` is passed between methods
2. **Protocol coupling**: `ReflectionEngine` uses `Protocol` for `AgentMemory` and `Agent` interfaces
3. **Backward compatibility**: `MemoryEntry.from_dict()` handles both v3.0 and v3.1.0 field names
4. **File-size limits**: Target 200-400 lines per file, max 800 lines
5. **Config isolation**: `ExperimentConfig` (Pydantic) never stores API keys; `SimulatorCore` only sees `SimulationConfig` (dataclass)
6. **Frontend decoupling**: Streamlit frontend communicates via files (subprocess + done.flag polling), never imports simulator core

## Coding Conventions

- Type annotations on all public functions
- No wildcard imports
- No emojis in code (terminal compatibility)
- No hardcoded values (use config)
- Error handling at system boundaries
- Files under `src/socialsimullm/` (setuptools src layout)
