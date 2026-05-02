# Development Guide

## Project Structure

```
SocialSimuLLM/
├── pyproject.toml                     # Project config & dependencies (v3.1.0)
├── src/socialsimullm/                 # Source package
│   ├── __main__.py                    # CLI entry point (27 lines)
│   ├── agents/                        # Agent behavior, memory, reflection
│   │   ├── agent.py                   # Agent class (276 lines)
│   │   ├── memory.py                  # AgentMemory unified store/recall (374 lines)
│   │   ├── memory_entry.py            # MemoryEntry frozen dataclass (153 lines)
│   │   └── reflection.py              # ReflectionEngine (392 lines)
│   ├── simulator/                     # Simulation engine
│   │   ├── core.py                    # SimulatorCore: step(), run() (423 lines)
│   │   ├── state.py                   # SimulationState dataclass (46 lines)
│   │   └── events.py                  # EventBus pub/sub (51 lines)
│   ├── locations/                     # Location management
│   │   └── locations.py               # Location/Locations classes (71 lines)
│   ├── prompt_templates/              # LLM prompt templates
│   │   └── template_agents.py         # All prompt strings (152 lines)
│   ├── utils/                         # Infrastructure utilities
│   │   ├── config.py                  # SimulationConfig + load_config (222 lines)
│   │   ├── logger.py                  # StructuredLogger JSONL+text (312 lines)
│   │   ├── text_generation.py         # OpenAI API integration (125 lines)
│   │   └── global_methods.py          # File I/O, time helpers (144 lines)
│   └── data/                          # Template data files
│       └── town_data_template.json    # Town configuration template
├── projects/                          # Simulation output data
│   └── {project_name}/
│       ├── town_data.json             # Town configuration
│       ├── simulation_log.txt         # Text log
│       ├── events.jsonl               # Structured JSONL event log
│       ├── agent_data/                # Per-agent memory files
│       │   ├── {name}_memory.json     # Memory records (MemoryEntry dicts)
│       │   └── {name}_memory.db       # SQLite embedding DB
│       └── checkpoints/               # State snapshots
├── docs/                              # Documentation
├── references/                        # Reference materials
└── tests/                             # Test files
```

## Environment Setup

1. **Install Dependencies:** `uv` is used for dependency management.

   ```bash
   uv sync
   ```

2. **Configure LLM API:**

   Set environment variables (preferred):
   ```bash
   export OPENAI_API_KEY="your-key"
   export OPENAI_BASE_URL="https://your-endpoint/v1"  # optional
   ```

   Or configure in `src/socialsimullm/utils/config.py` as defaults.

## Running the Simulation

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

### CLI Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--project` | (prompt) | Project name (directory under `projects/`) |
| `--steps` | 144 | Number of simulation steps (1 step = 10 min) |
| `--model` | Config default | LLM model name |
| `--checkpoint-interval` | 10 | Steps between checkpoint saves |
| `--no-reflection` | (disabled) | Disable the reflection system entirely |
| `--reflection-threshold` | 15 | Cumulative importance threshold for mid-day reflection |

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
8. **Global Events**: Random events may occur

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

### Configuration

`SimulationConfig` dataclass with:
- CLI argument parsing via `load_config()`
- Environment variable overrides (`OPENAI_API_KEY`, `OPENAI_BASE_URL`, `DEFAULT_MODEL`)
- Runtime validation via `validate_config()`

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

## Coding Conventions

- Type annotations on all public functions
- No wildcard imports
- No emojis in code (terminal compatibility)
- No hardcoded values (use config)
- Error handling at system boundaries
- Files under `src/socialsimullm/` (setuptools src layout)
