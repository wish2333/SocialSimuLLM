# SocialSimuLLM

A multi-agent social simulation framework powered by Large Language Models, based on the Generative Agents architecture (Park et al. 2023).

## Features

- **Modular architecture**: Clean separation between simulation engine, agent cognition, memory, reflection, world modeling, and goal planning
- **Structured memory system**: Typed `MemoryEntry` dataclass with multi-dimensional retrieval (semantic, temporal, spatial, importance)
- **Multi-level reflection**: Daily summary, cross-day pattern recognition, and social relationship analysis
- **Spatial world modeling**: Diverse graph topologies (ring, small-world, grid, random, scale-free) via `WorldVariationGenerator`
- **Proximity perception**: Graph distance-based `FieldOfView` for realistic agent awareness
- **Intelligent path planning**: LLM-driven movement intent with A* shortest path and multi-hop traversal
- **Goal-driven planning**: Hierarchical goal management with recursive task decomposition (ROMA-inspired)
- **NL scenario construction**: Generate complete simulation setups from natural language descriptions
- **Reproducible experiments**: Pydantic-based config, JSONL structured logging, checkpoint save/restore, random seed management
- **Batch execution**: Run multiple experiments with different seeds for statistical analysis
- **Web UI**: Streamlit frontend with experiment configuration, replay visualization, heatmaps, and AI research assistant
- **Jupyter notebooks**: Ready-to-use analysis templates for behavioral, spatial, and comparative studies
- **OpenAI-compatible**: Works with any OpenAI-compatible API endpoint (customizable base URL and model)

## Project Structure

```
SocialSimuLLM/
├── pyproject.toml                     # Project config & dependencies
├── src/socialsimullm/
│   ├── __main__.py                    # CLI entry point
│   ├── agents/                        # Agent cognition layer
│   │   ├── agent.py                   # Agent class
│   │   ├── memory.py                  # AgentMemory: storage & retrieval
│   │   ├── memory_entry.py            # MemoryEntry dataclass
│   │   └── reflection.py              # ReflectionEngine
│   ├── simulator/                     # Simulation engine
│   │   ├── core.py                    # SimulatorCore
│   │   ├── state.py                   # SimulationState
│   │   └── events.py                  # EventBus
│   ├── world/                         # Spatial world modeling
│   │   ├── spatial.py                 # WorldVariationGenerator (topologies)
│   │   ├── field_of_view.py           # FieldOfView (proximity perception)
│   │   └── path_planner.py            # PathPlanner (LLM + A*)
│   ├── cognition/                     # Cognitive modules
│   │   └── goal.py                    # GoalManager + RecursiveTaskDecomposer
│   ├── experiment/                    # Experiment infrastructure
│   │   ├── config.py                  # ExperimentConfig (Pydantic)
│   │   ├── runner.py                  # ExperimentRunner
│   │   ├── storage.py                 # Run directory & checkpoints
│   │   ├── analysis.py                # Result loading & analysis
│   │   ├── scenario.py                # ScenarioGenerator (NL -> town_data)
│   │   └── assistant.py               # ResearchAssistant (AI analysis)
│   ├── frontend/                      # Streamlit web UI (optional)
│   │   ├── app.py                     # Main entry (3 tabs)
│   │   ├── pages/                     # Configure, Results, Assistant
│   │   └── components/                # Forms, viz, replay, heatmaps
│   ├── notebooks/                     # Jupyter analysis templates
│   │   └── data_loader.py             # Shared data loading utilities
│   ├── locations/                     # Spatial world
│   ├── prompt_templates/              # LLM prompts
│   ├── utils/                         # Config, logger, LLM API
│   └── data/                          # Template data
├── projects/                          # Legacy simulation output
├── runs/                              # Experiment output (gitignored)
└── docs/                              # Documentation
```

## Quick Start

### Install Dependencies

[uv](https://docs.astral.sh/uv/) is used for dependency management:

```bash
uv sync
```

For the web UI or analysis features:

```bash
uv sync --extra frontend   # Streamlit + pyvis + plotly + pandas
uv sync --extra analysis   # pandas + plotly only
```

### Configure API Key

Set environment variables (recommended):

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://your-endpoint/v1"  # optional
```

### Run Simulation

```bash
# Legacy mode (single run)
uv run socialsimullm --project my_town --steps 288 --model deepseek-chat

# Experiment mode (reproducible)
uv run socialsimullm run --config config.yaml --id exp001

# Batch experiments
uv run socialsimullm batch --config config.yaml --seeds 42,43,44

# List experiments
uv run socialsimullm list

# Web UI
uv run streamlit run src/socialsimullm/frontend/app.py
```

### CLI Options

**Legacy Mode:**

| Argument | Default | Description |
|----------|---------|-------------|
| `--project` | (prompt) | Project name |
| `--steps` | 144 | Simulation steps (1 step = 10 min) |
| `--model` | Config default | LLM model name |
| `--checkpoint-interval` | 10 | Checkpoint interval |
| `--no-reflection` | (off) | Disable reflection |
| `--reflection-threshold` | 15 | Importance threshold for mid-day reflection |

**Experiment Mode:**

| Command | Description |
|---------|-------------|
| `run --config <yaml>` | Run single experiment |
| `run --config <yaml> --id <id>` | Run with custom experiment ID |
| `batch --config <yaml> --seeds 42,43` | Batch run with multiple seeds |
| `list` | List all experiments |
| `list --project <name>` | List experiments for a project |

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
events:
  - "A strange fog rolls into town."
reflection_enabled: true

# Phase 3: Spatial topology
spatial_config:
  topology: small_world
  num_locations: 6
  seed: 42

# Phase 3: Proximity perception
fov_enabled: true
fov_distance: 1

# Phase 3: Intelligent movement
path_planner_enabled: true
multi_hop_movement: true

# Phase 3: Goal-driven planning
goal_enabled: true
max_active_goals: 5
```

## Customization

1. **Town data**: Modify `projects/<name>/town_data.json` or set `spatial_graph_path` in experiment config
2. **Agent behavior**: Edit files in `src/socialsimullm/agents/`
3. **Prompt templates**: Edit `src/socialsimullm/prompt_templates/template_agents.py`
4. **LLM configuration**: Set environment variables or modify `src/socialsimullm/utils/config.py`
5. **Locations**: Edit `src/socialsimullm/locations/locations.py`

## Output Structure

**Legacy Mode:**
```
projects/{project_name}/
├── town_data.json              # Town configuration
├── simulation_log.txt          # Human-readable log
├── events.jsonl                # Structured JSONL event log
├── done.flag                   # Completion marker
├── checkpoints/                # State snapshots
└── agent_data/                 # Per-agent memory files
```

**Experiment Mode:**
```
runs/{project}/{experiment_id}/
├── config.yaml                # Full experiment config snapshot
├── town_data.json             # Copied town configuration
├── events.jsonl               # Structured JSONL event log
├── done.flag                  # Completion marker
├── checkpoints/               # State snapshots
└── agent_data/                # Per-agent memory files
```

## Documentation

- [PRD v3.1.0](docs/PRD-3.1.0.md) - Product requirements and upgrade roadmap
- [Development Guide](docs/dev_guide.md) - Architecture, conventions, and workflow
- [System Design](docs/design/system_design.md) - Architecture diagrams and data flow
- [Module Descriptions](docs/Module_Description.md) - Per-module API reference
- [Changelog](docs/changelog.md) - Version history

## Version History

- **v3.1.0**: Architecture refactoring, structured memory, reflection system, reproducible experiments, Streamlit frontend, spatial world modeling, goal-driven planning, AI research assistant
- **v3.0**: Enhanced agent memory and reflection capabilities
- **v2.0**: Memory retrieval optimization, agent state evaluation, database groundwork

## Authors and References

Huang Miaosen

## Acknowledgments

- [mkturkcan/generative-agents](https://github.com/mkturkcan/generative-agents) - Code source (license in License folder)
- [joonspk-research/generative_agents](https://github.com/joonspk-research/generative_agents) - Paper reference
