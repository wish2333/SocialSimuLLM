# Product Requirements Document (PRD) - v3.1.0 Upgrade

> Version: 3.1.0
> Last Updated: 2026-05-02
> Status: Phase 1 + Phase 2 + Phase 3 Complete
> Based on: `references/reference-3.1.0-3rdVersion.md`
> Supersedes: `docs/PRD.md` (v3.0 baseline)

---

## 1. Product Overview

### 1.1 Product Name

SocialSimuLLM - Large Language Model Based Social Simulation Framework

### 1.2 Upgrade Context

v3.1.0 is a research-platform upgrade aimed at transforming the current working prototype into a reproducible, analyzable, and publishable research tool. The core principle is: **minimum changes for maximum research output**, centered on a single researcher's workflow.

### 1.3 Problem Statement

The current system (v3.0) has several fundamental limitations:

- **Monolithic architecture**: `__main__.py` (279 lines) contains initialization, main loop, event handling, and output -- violates the 800-line limit
- **Incomplete cognition**: Reflection system exists partially through `agent.form_reflection()` but the `Reflect` class is an unused stub; no trigger conditions or multi-level reflection
- **Non-reproducible experiments**: No checkpoint/restore, no structured logging, no seed management, no experiment configuration model
- **Unanalyzable output**: Plain text logs only, not machine-readable
- **No experiment tooling**: Manual one-off runs, no batch execution, no A/B comparison support
- **Code quality debt**: MethodType binding pattern, missing type annotations, mutable state, hardcoded configurations

### 1.4 Target Audience

- **Primary**: The developer/researcher (single-person team) conducting LLM-based social simulation research
- **Secondary**: Social science researchers using the platform for published work
- **Tertiary**: AI researchers exploring LLM-based agent behavior patterns

---

## 2. Current State Baseline

> Audit-confirmed status of the existing codebase under `src/socialsimullm/`.

### 2.1 Module Inventory

| Module | File | Lines | Status | Notes |
|--------|------|-------|--------|-------|
| Entry | `__main__.py` | 279 | Functional | Monolithic, needs split |
| Agent | `agents/agent.py` | 151 | Functional | Uses MethodType binding |
| Agent Memory | `agents/memory.py` | 117 | Functional | Standalone functions, bound via MethodType |
| Movement | `agents/movement.py` | 67 | Functional | Standalone functions, bound via MethodType |
| Retrieval | `retrieve/memory.py` | 247 | Functional | JSON + SQLite + embedding search |
| Reflection | `retrieve/reflect.py` | 26 | Stub | Unused class, actual reflection in agent.py |
| Locations | `locations/locations.py` | 71 | Functional | Simple Location/Locations classes |
| Templates | `prompt_templates/template_agents.py` | 106 | Functional | All prompt strings |
| Config | `utils/config.py` | 20 | Functional | Hardcoded, no runtime override |
| LLM | `utils/text_generation.py` | 125 | Functional | OpenAI client + custom base_url |
| Helpers | `utils/global_methods.py` | 144 | Functional | File I/O, time manipulation |

### 2.2 Key Implementation Details

**Agent Method Binding Pattern** (to be refactored):
```python
# agents/agent.py lines 63-72
self.rate_locations = MethodType(rate_locations, self)
self.move = MethodType(move, self)
self.memory_actions = MethodType(memory_actions, self)
# ... etc
```
Functions from `agents/memory.py` and `agents/movement.py` are bound to Agent instances via `MethodType`. This pattern is unusual and should be refactored into proper class methods.

**Memory Architecture**:
- Per-agent JSON file (`{name}_memory.json`) stores structured experience records
- Per-agent SQLite DB (`{name}_memory.db`) stores action embeddings
- Retrieval scoring: `0.5*similarity + 0.3*recency + 0.2*importance`
- Experience types: `action`, `plan`, `thought`, `event`, `reflection`

**Reflection Status**:
- `retrieve/reflect.py`: Contains unused `Reflect` class (empty stub)
- `agent.form_reflection()` (agent.py:143-151): Working LLM-based daily reflection
- Prompt templates exist for reflection in `template_agents.py`
- **PRD decision**: Full rewrite -- replace current mechanism with standalone reflection module following Generative Agents paper

**Spatial Graph**:
- Simple ring graph: each node connected to its neighbor, first to last
- Uses `nx.shortest_path()` for movement
- Currently 4 locations in template (Phandalin setting)

**Known Bug**: `__main__.py` line 124 uses `description` variable that holds the last agent's JSON description, not the location description.

### 2.3 Experience Data Model (Current)

| Field | Type | Description |
|-------|------|-------------|
| agent_name | str | Agent who owns this memory |
| global_time | str | Format: "Day X, HH:MM" |
| location | str | Where the experience occurred |
| action | str | Narrative description |
| action_des | str | Simplified SVO sentence (action/thought types) |
| other_agents | list[str] | Agents present during experience |
| exp_type | str | One of: action, plan, thought, event, reflection |
| priority | int | Importance rating 1-9 |

---

## 3. Goals and Objectives

### 3.1 Primary Goals

1. **Architectural cleanup**: Split `__main__.py` into focused modules, refactor MethodType bindings into proper class methods
2. **Cognitive core completion**: Full rewrite of reflection system with trigger conditions and multi-level reflection
3. **Experiment reproducibility**: Checkpoint/restore, structured JSONL logging, seed management, Pydantic-based config
4. **Research output**: Enable ablation experiments (memory/reflection variants) producing publishable results
5. **Experiment tooling**: ExperimentRunner for batch execution, CLI interface, result analysis
6. **Visualization**: Streamlit MVP frontend for experiment configuration and result viewing

### 3.2 Success Metrics

- `uv run socialsimullm` behavior is identical before and after refactoring (Phase 1)
- Agent reflections demonstrate self-consistent behavior across simulation days
- Ablation experiment (baseline vs. structured memory vs. +reflection) produces statistically distinct results
- A single experiment run can be fully reproduced from its config + seed
- JSONL logs are directly loadable into Pandas DataFrame for analysis
- Streamlit frontend supports configure-run-view workflow end-to-end

---

## 4. Feature Requirements

### 4.1 Phase 1: Technical Debt + Cognitive Core (4-6 weeks)

**Target**: All paths. System stability, analyzability, reproducibility; Agent self-awareness and behavioral coherence significantly improved.

#### F-101: Refactor `__main__.py` (P0, Week 1)

**Status**: Done

Split the 279-line monolith into focused modules:

| Target Module | Responsibility | Max Lines |
|---------------|---------------|-----------|
| `__main__.py` | CLI entry + argparse only | < 50 |
| `simulator/core.py` | `SimulatorCore` class: `initialize()`, `step()`, `run()` | < 200 |
| `simulator/state.py` | `SimulationState` dataclass (world graph, agent list, time) | < 100 |
| `simulator/events.py` | `EventBus` class (global event registration/dispatch) | < 150 |
| `utils/logger.py` | `StructuredLogger` class (JSONL output + checkpoint save) | < 200 |

**Acceptance Criteria**:
- `uv run socialsimullm` produces identical output to pre-refactoring baseline
- Each module < 200 lines
- No MethodType bindings remain in Agent class

**Target Directory Structure**:
```
src/socialsimullm/
  __main__.py              # CLI entry only
  simulator/
    __init__.py
    core.py                # SimulatorCore
    state.py               # SimulationState
    events.py              # EventBus
  agents/
    agent.py               # Agent class (merged methods)
    memory.py              # AgentMemory (unified API, merged from retrieve/memory.py)
    movement.py            # Movement + path planning
    reflection.py           # Reflection system (full rewrite)
    planning.py            # Daily/hourly planning + action
  cognition/               # Pluggable modules (Phase 2+)
    __init__.py
    memory_store.py        # Structured storage + multi-dim retrieval
    goal.py                # Goal-driven planning (balanced path)
  world/
    __init__.py
    spatial.py             # NetworkX spatial graph management
    field_of_view.py       # FOV perception (balanced path)
    path_planner.py        # LLM intent + A* (balanced path)
  experiment/              # Phase 2
    __init__.py
    runner.py              # ExperimentRunner
    config.py              # ExperimentConfig (Pydantic)
    checkpoint.py          # Checkpoint save/load + JSONL log
    analysis.py            # Result collection + DataFrame export
  utils/
    config.py              # Runtime config (CLI override support)
    text_generation.py     # LLM calls (keep OpenAI compat)
    logger.py              # Structured JSONL logger
    global_methods.py      # Utility functions
  frontend/                # Phase 2
    app.py
    pages/
    components/
    utils.py
  locations/
    locations.py
  prompt_templates/
    template_agents.py
  data/
    town_data_template.json
```

#### F-102: Refactor Agent Method Binding (P0, Week 1)

**Status**: Done

Merge MethodType-bound functions from `agents/memory.py` and `agents/movement.py` into the Agent class as proper methods.

**Current** (to be removed):
```python
# agents/agent.py
from socialsimullm.agents.memory import *
from socialsimullm.agents.movement import *
self.rate_locations = MethodType(rate_locations, self)
self.memory_actions = MethodType(memory_actions, self)
# ...
```

**Target**:
```python
# agents/agent.py
class Agent:
    def rate_locations(self, locations, global_time, ...): ...
    def move(self, new_location_name): ...
    def memory_actions(self, agents, global_time, priority): ...
    def rate_experience(self, prompt_meta, ...): ...
    # All methods are proper class methods
```

**Acceptance Criteria**:
- No `MethodType` imports in Agent class
- No wildcard imports (`from ... import *`) in agent.py
- All agent operations work identically

#### F-103: Merge/Unify Memory Module (P0, Week 1)

**Status**: Done

Consolidate `agents/memory.py` (agent-side operations) and `retrieve/memory.py` (storage/retrieval) into a unified `AgentMemory` class.

**Unified API**:
```python
class AgentMemory:
    """Unified agent memory with structured storage and multi-dim retrieval."""

    def store(self, observation: MemoryEntry) -> None: ...
    def recall_recent(self, n: int = 10) -> list[MemoryEntry]: ...
    def recall_semantic(self, query: str, top_k: int = 5) -> list[MemoryEntry]: ...
    def recall_by_location(self, location_id: str) -> list[MemoryEntry]: ...
    def recall_time_span(self, start: str, end: str) -> list[MemoryEntry]: ...
    def recall_by_importance(self, min_importance: int = 7) -> list[MemoryEntry]: ...
    def recall_impressions(self, n: int = 3) -> list[MemoryEntry]: ...
    def get_related_things(self, query: str, top_k: int = 5) -> list[MemoryEntry]: ...
```

**Migration Strategy**: Fresh start (incompatible with old data). Old `projects/` directory retained as reference only.

**Acceptance Criteria**:
- Single `agents/memory.py` file exposes unified API
- `retrieve/memory.py` and `retrieve/reflect.py` are removed after migration
- All recall methods return typed `MemoryEntry` objects

#### F-104: Full Rewrite of Reflection System (P0, Weeks 3-4)

**Status**: Done

Replace the current `agent.form_reflection()` mechanism with a complete reflection module following Generative Agents (Park et al. 2023).

**New module**: `agents/reflection.py`

**Trigger Mechanisms**:
1. **Scheduled**: Automatically at end of each simulation day
2. **Threshold**: When un-reflected observations' cumulative importance exceeds configurable threshold

**Reflection Flow**:
1. Retrieve recent high-importance observations (`recall_by_importance`)
2. Retrieve existing reflections to avoid duplicate themes
3. LLM generates high-level reflection (e.g., "I seem to prefer quiet locations", "Interactions with X increase my community trust")
4. Store reflection as special memory entry (`exp_type="reflection"`, elevated priority)

**Reflection Types** (extensible):
- Daily summary reflection (current behavior, enhanced)
- Pattern reflection (identify behavioral patterns across days)
- Social reflection (relationship trends with other agents)

**Acceptance Criteria**:
- Agent can reference past reflections to guide subsequent behavior (verified via logs)
- Reflections demonstrate non-trivial self-awareness (not just restating events)
- Trigger threshold is configurable
- Unused `Reflect` class in `retrieve/reflect.py` is removed

#### F-105: Memory System Structured Upgrade (P0, Weeks 5-6)

**Status**: Done

Extend the existing JSON + SQLite storage with structured fields for multi-dimensional retrieval.

**New MemoryEntry fields**:

| Field | Type | Description | New/Existing |
|-------|------|-------------|-------------|
| id | str | Unique entry UUID | New |
| agent_name | str | Agent who owns this memory | Existing |
| timestamp | str | Simulation time "Day X, HH:MM" | Existing (as global_time) |
| location_id | str | Where the event occurred | Existing (as location) |
| event_type | str | action/plan/thought/reflection/event | Existing (as exp_type) |
| content | str | Full narrative description | Existing (as action) |
| summary | str | Simplified SVO sentence | Existing (as action_des) |
| entities | list[str] | Other agents involved | Existing (as other_agents) |
| importance | int | 1-9 rating | Existing (as priority) |
| embedding | list[float] | Vector embedding | Existing (in SQLite) |
| reflection_link | str or None | Linked reflection ID | New |
| metadata | dict | Extensible key-value pairs | New |

**Acceptance Criteria**:
- `MemoryEntry` is a typed dataclass with all fields
- All recall methods support combined filtering (time + location + type + importance)
- SQLite schema updated to include new indexable fields
- Backward-incompatible migration is documented

#### F-106: Checkpoint and Structured Logging (P0, Week 2)

**Status**: Done

**JSONL Event Log**: Write `{timestamp, step, agent_id, event_type, data}` per step.

**Checkpoint**: Save `SimulationState` snapshot every N steps (configurable) to:
```
runs/{experiment_id}/checkpoints/step_{N}/
  spatial_graph.json
  agent_states.json
  memory_summary.json
```

**Completion Marker**: `done.flag` file when simulation completes.

**Acceptance Criteria**:
- JSONL log is valid and loadable by `pd.read_json(path, lines=True)`
- Checkpoint can restore full simulation state
- Interrupted simulation can resume from latest checkpoint

#### F-107: Configuration Management Improvement (P0, Week 2)

**Status**: Done

Extend `utils/config.py` to support:
- CLI argument override: `--model deepseek-chat --steps 144`
- Runtime parameter validation
- Preparation for Pydantic `ExperimentConfig` (Phase 2)

**CLI Interface**:
```bash
uv run socialsimullm run --project my_experiment --steps 144 --model deepseek-chat
uv run socialsimullm run --project my_experiment  # resume from checkpoint
```

**Acceptance Criteria**:
- All hardcoded values in config.py are overridable via CLI
- Invalid parameters produce clear error messages
- Config is validated before simulation starts

#### F-108: Bug Fix -- Location Description (P0, Week 1)

**Status**: Done

Fix `__main__.py` line 124 where `description` variable holds the last agent's JSON description instead of the location description.

```python
# Current (buggy):
for name, detail in town_areas.items():
    locations.add_location(name, description)  # description is from last agent

# Fix:
for name, detail in town_areas.items():
    locations.add_location(name, detail)
```

**Acceptance Criteria**:
- Each location receives its correct description from `town_areas`

### 4.2 Phase 2: Experiment Infrastructure + Frontend (6-10 weeks)

**Target**: Conservative path (full) + Balanced path (partial). Reproducible experiment workflow with visual tooling.

#### F-201: ExperimentConfig Pydantic Model (P0, Week 1 of Phase 2)

**Status**: Done

```python
from pydantic import BaseModel

class MemoryConfig(BaseModel):
    recency_weight: float = 0.3
    similarity_weight: float = 0.5
    importance_weight: float = 0.2
    importance_threshold: int = 6

class ExperimentConfig(BaseModel):
    experiment_id: str  # auto-generated or manual
    model: str = "deepseek-chat"
    embedding_model: str = "BAAI/bge-m3"
    agent_count: int = 5
    simulation_steps: int = 144  # 1 day = 144 ten-minute steps
    random_seed: int = 42
    spatial_graph_path: str = "data/town_data_template.json"
    memory_config: MemoryConfig = MemoryConfig()
    checkpoint_interval: int = 10
    budget_limit: float = 1.0  # USD
```

**New dependency**: `pydantic` (minimal, well-maintained)

**Acceptance Criteria**:
- Config validates all parameters with sensible defaults
- YAML/JSON export/import for sharing experiment configurations
- Config snapshot saved alongside each experiment run

#### F-202: ExperimentRunner (P0, Weeks 2-3 of Phase 2)

**Status**: Done

```python
class ExperimentRunner:
    def run_single(self, config: ExperimentConfig) -> str:
        """Run single experiment, return experiment_id."""

    def run_batch(self, config: ExperimentConfig, seeds: list[int]) -> list[str]:
        """Multiple runs with different random seeds."""

    def load_results(self, experiment_id: str) -> pd.DataFrame:
        """Load results as DataFrame for analysis."""
```

**CLI Interface**:
```bash
uv run socialsimullm run --config experiments/config.yaml --id exp001
uv run socialsimullm batch --config experiments/config.yaml --seeds 42,43,44
uv run socialsimullm list   # list all experiments
```

**Acceptance Criteria**:
- Single run produces complete experiment directory with config, logs, checkpoints
- Batch run produces comparable results across seeds
- Results loadable as Pandas DataFrame

#### F-203: Frontend-Backend Interface Contract (P0, Week 3 of Phase 2)

**Status**: Done

**Checkpoint Directory Structure**:
```
runs/{experiment_id}/
  config.yaml              # Full experiment config for reproducibility
  done.flag                # Completion marker
  events.jsonl             # Full event log
  checkpoints/
    step_{N}/
      spatial_graph.json   # NetworkX serialized
      agent_states.json    # All agent state snapshots
      memory_summary.json  # Memory statistics summary
```

**Helper Functions**:
```python
def load_checkpoint(experiment_id: str, step: int | None = None) -> dict: ...
def list_experiments() -> list[dict]: ...
```

#### F-204: Streamlit Frontend MVP (P1, Weeks 4-7 of Phase 2)

**Status**: Done

**Strictly 3 core features only**:

1. **Experiment Configuration Form**: Generate Streamlit form from `ExperimentConfig` Pydantic model
2. **"Run Experiment" Button**: subprocess launch + file-polling completion check
3. **Result Visualization**: Load checkpoint -> pyvis spatial graph + Plotly basic charts

**Explicitly excluded (v1)**: Real-time monitoring, time-slider replay, multi-view linking, social network graph, report export, experiment template library, NL input.

**Subprocess Communication** (file polling):
```
Frontend click "Run"
  -> Generate experiment_id
  -> subprocess.Popen(["uv", "run", "socialsimullm", "run", "--config", path, "--id", eid])
  -> Simulation runs independently, writes checkpoints to runs/{eid}/
  -> Frontend st.session_state tracks eid + running status
  -> time.sleep(30) + st.rerun() polls done.flag
  -> On completion, load results and render
```

**Frontend Directory**:
```
src/socialsimullm/frontend/
  app.py                # Main entry
  pages/
    1_configure.py      # Experiment configuration
    2_results.py        # Result visualization
  components/
    forms.py            # Pydantic form mapping
    viz.py              # pyvis + plotly rendering
  utils.py              # Checkpoint loading, polling logic
```

**New dependencies**: `streamlit`, `pyvis`, `plotly`, `pandas`

**Acceptance Criteria**:
- User can configure experiment via web form and launch it
- Simulation runs in background (survives browser close)
- Results display spatial graph + basic agent behavior charts
- State management via `st.session_state` (no lost state on rerun)

### 4.3 Phase 3: Extended Exploration (Variable duration)

**Target**: Balanced path (full) + Aggressive path. Requires Phase 2 completion.

| Feature ID | Feature | Path | Research Value |
|------------|---------|------|---------------|
| F-301 | FieldOfView spatial perception | Balanced | Proximity-based interaction realism | Done |
| F-302 | PathPlanner (LLM intent + A*) | Balanced | Intentional movement vs. random walk | Done |
| F-303 | Goal-driven hierarchical planning | Balanced | Multi-step coordination emergence | Done |
| F-304 | Jupyter analysis templates | Balanced | Lower analysis barrier | Done |
| F-305 | WorldVariationGenerator | Balanced | Environment robustness experiments | Done |
| F-306 | NL scenario construction | Aggressive | Lower experiment setup cost | Done |
| F-307 | Simplified ROMA planning | Aggressive | Multi-step task emergence | Done |
| F-308 | Lightweight cultural evolution | Aggressive | Social norm emergence research | Deferred |
| F-309 | LiteLLM full integration | Aggressive | Multi-model + tool calling | Deferred |
| F-310 | Advanced visualization (replay, heatmap) | Aggressive | Intuitive emergence display | Done |
| F-311 | Semi-auto research assistant | Aggressive | Research efficiency multiplier | Done |
| F-312 | A2A/MCP prototype | Aggressive | Inter-framework interoperability | Deferred |

---

## 5. Architecture Evolution

### 5.1 Current Architecture (After Phase 3)

```
__main__.py (96 lines, CLI entry + subcommand dispatch)
  |-- load_experiment_config() -> "run" | "batch" | "list" | None (legacy)
  |-- Experiment mode: ExperimentRunner.run_single() / run_batch()
  |-- Legacy mode: load_config() -> SimulatorCore(config).initialize().run()

simulator/core.py (427 lines)
  |-- SimulatorCore: initialize(), step(), run()
  |     |-- _daily_planning()       (08:00 trigger)
  |     |-- _hourly_planning()      (top of hour trigger)
  |     |-- _execute_actions()      (agent actions)
  |     |-- _movement()             (location rating + move)
  |     |-- _impressions()          (agent impression formation)
  |     |-- _run_reflection()       (scheduled + threshold trigger)
  |     |-- _load_events()          (global event handling, supports initial_event)
  |-- initial_event param for non-interactive experiment mode
  |-- Absolute path support: experiment runs write to runs/{project}/{id}/

agents/agent.py (276 lines)
  |-- Agent class (all methods as proper class methods)
  |-- memory_actions(), memory_daily_plans(), memory_hourly_plan()
  |-- memory_location_change(), memory_impression()
  |-- rate_locations(), move(), simplify_action()

agents/memory.py (374 lines)
  |-- AgentMemory: unified store/recall API
  |     |-- store(MemoryEntry) -> routes by event_type
  |     |-- recall_recent(), recall_semantic(), recall_by_location()
  |     |-- recall_time_span(), recall_by_importance(), recall_impressions()
  |     |-- recall_reflections(), recall_filtered()
  |-- JSON file storage + SQLite embedding DB per agent

agents/memory_entry.py (153 lines)
  |-- MemoryEntry frozen dataclass (13 fields)
  |-- create() factory, to_dict()/from_dict() serialization
  |-- v3.0 backward-compatible deserialization

agents/reflection.py (392 lines)
  |-- ReflectionEngine: Protocol-based coupling
  |     |-- reflect_daily()      (end-of-day summary)
  |     |-- reflect_pattern()    (cross-day patterns, >= 2 daily refs)
  |     |-- reflect_social()     (relationship trends)
  |     |-- reflect_all()        (complete cycle, returns MemoryEntry list)

experiment/config.py (216 lines)
  |-- ExperimentConfig (Pydantic BaseModel)
  |     |-- experiment_id, project, model, embedding_model, simulation_steps
  |     |-- random_seed, checkpoint_interval, spatial_graph_path, events
  |     |-- memory_config (MemoryConfig), reflection settings, prompt_meta
  |-- to_simulation_config() -> SimulationConfig
  |-- to_yaml() / from_yaml() serialization

experiment/runner.py (179 lines)
  |-- ExperimentRunner: run_single(), run_batch()
  |-- Run dir creation, config snapshot, town_data preparation

experiment/storage.py (281 lines)
  |-- create_run_dir(), list_experiments(), find_run_dir()
  |-- load_checkpoint(), get_latest_checkpoint_step(), is_complete()

experiment/analysis.py (179 lines)
  |-- load_results() -> list[dict], load_results_dataframe() -> pd.DataFrame
  |-- get_experiment_summary(), compare_experiments()

frontend/app.py (32 lines)
  |-- Streamlit two-tab layout: Configure / Results

frontend/pages/configure.py (138 lines)
  |-- Experiment form + Save & Run + auto-poll status

frontend/pages/results.py (174 lines)
  |-- Experiment selector + checkpoint viewer + viz tabs

frontend/components/forms.py (104 lines)
  |-- pydantic_to_streamlit() + form_to_config()

frontend/components/viz.py (137 lines)
  |-- render_spatial_graph() (pyvis) + render_agent_charts() (plotly)

frontend/utils.py (89 lines)
  |-- launch_experiment() subprocess + poll_experiment_status()

utils/config.py (293 lines)
  |-- SimulationConfig dataclass
  |-- load_config() with CLI args + env var overrides
  |-- load_experiment_config() subcommand parser (run/batch/list)
  |-- validate_config()

utils/logger.py (312 lines)
  |-- StructuredLogger: JSONL events.jsonl + text simulation_log.txt
  |-- Checkpoint save/restore, done.flag completion marker
```

### 5.2 Target Architecture (Conservative Path End State)

```
src/socialsimullm/
  __main__.py              # CLI entry + argparse
  simulator/
    core.py                # SimulatorCore (time advancement, agent lifecycle)
    state.py               # SimulationState (immutable data object)
    events.py              # EventBus (global event handling)
  agents/
    agent.py               # Agent class (all methods as proper class methods)
    memory.py              # Unified AgentMemory (merged agents/ + retrieve/)
    movement.py            # Movement + path planning
    reflection.py          # Full reflection system (rewrite)
    planning.py            # Daily/hourly planning + action execution
  cognition/               # Pluggable modules (balanced/aggressive)
    memory_store.py        # Structured storage + multi-dim retrieval
    goal.py                # Goal-driven planning
  world/
    spatial.py             # NetworkX spatial graph management
    field_of_view.py       # FOV perception (balanced)
    path_planner.py        # LLM intent + A* (balanced)
  experiment/
    runner.py              # ExperimentRunner
    config.py              # ExperimentConfig (Pydantic)
    checkpoint.py          # Checkpoint save/load + JSONL
    analysis.py            # Result collection + DataFrame export
  utils/
    config.py              # Runtime config (CLI override)
    text_generation.py     # LLM calls (OpenAI compatible)
    logger.py              # Structured JSONL logger
    global_methods.py      # Utility functions
  frontend/
    app.py                 # Streamlit main entry
    pages/                 # Multi-page app
    components/            # Reusable UI components
    utils.py               # Frontend utilities
  locations/
    locations.py           # Location management (unchanged)
  prompt_templates/
    template_agents.py     # Prompt strings (unchanged)
  data/
    town_data_template.json
```

### 5.3 Architecture Principles

1. `__main__.py` only does CLI parsing; all logic sinks to `simulator/`
2. `SimulationState` is an immutable data object (dataclass/Pydantic), passed between modules
3. Cognitive modules are interface-isolated, independently replaceable (enables ablation experiments)
4. `experiment/` layer is decoupled from simulation core; communicates via `ExperimentConfig` and checkpoint files
5. All source files under `src/socialsimullm/` (setuptools src layout maintained)

---

## 6. Data Models

### 6.1 MemoryEntry (v3.1.0)

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class MemoryEntry:
    id: str                                    # UUID
    agent_name: str
    timestamp: str                             # "Day X, HH:MM"
    location_id: str
    event_type: str                            # action|plan|thought|reflection|event
    content: str                               # Full narrative
    summary: str                               # Simplified SVO sentence
    entities: tuple[str, ...]                   # Other agents involved
    importance: int                            # 1-9 rating
    embedding: tuple[float, ...] | None        # Vector embedding
    reflection_link: str | None                # Linked reflection ID
    metadata: dict[str, Any] = field(default_factory=dict)
```

### 6.2 SimulationState (v3.1.0)

```python
@dataclass(frozen=True)
class SimulationState:
    global_time: str                           # "Day X, HH:MM"
    round: int
    agents: tuple[AgentState, ...]
    world_graph_data: dict                     # NetworkX serializable
    events: tuple[str, ...]                    # Active global events
```

### 6.3 AgentState (v3.1.0)

```python
@dataclass(frozen=True)
class AgentState:
    name: str
    description: str
    location: str
    daily_plans: str
    hourly_plan: str
    last_action: str
    last_impression: str
    last_reflection: str
```

### 6.4 ExperimentConfig (v3.1.0)

See F-201 for full Pydantic model definition.

---

## 7. Multi-Path Strategy

### 7.1 Path Comparison

| Aspect | Conservative (Recommended) | Balanced | Aggressive |
|--------|---------------------------|----------|------------|
| Total Time | 3-5 months | 5-8 months | 8+ months |
| Target | 1-2 working papers | Systematic research platform | Exploratory platform |
| Phase 1 | All P0 features | All P0 + some optional | All P0 + all optional |
| Phase 2 | Full + Streamlit MVP | Full + spatial upgrades | Full + advanced viz |
| Phase 3 | None | Selected features | Full exploration |
| Reflection | Basic (daily + threshold) | + pattern/social reflection | + goal-driven reflection |
| Memory | Structured fields + unified API | + sqlite-vec extension | + Hindsight/A-MEM inspired |
| Spatial | Current ring graph | + FOV + PathPlanner | + dynamic graph updates |
| Experiment | CLI + Pydantic + Runner | + Jupyter templates | + NL parsing + auto-analysis |
| Frontend | Streamlit MVP (3 features) | Multi-page + basic replay | Full replay + AI assistant |
| LLM | Current OpenAI compat | + LiteLLM gradual | LiteLLM full + tool calling |

### 7.2 Path Selection Criteria

- **Choose Conservative** if: Limited time (< 5 months), primary goal is publishable results
- **Choose Balanced** if: Available 6+ months, want systematic platform for multiple studies
- **Choose Aggressive** if: Research-focused role, 8+ months available, exploring frontier capabilities

### 7.3 Path Transition

Paths are cumulative -- Balanced includes all Conservative features, Aggressive includes all Balanced features. You can start Conservative and upgrade to Balanced at any Phase 2 milestone.

---

## 8. Experiment Design

### 8.1 Experiment 1: Memory + Reflection Ablation

- **Variables**: Baseline (current) / Structured memory / +Reflection
- **Environment**: Same spatial graph, same agent group
- **Metrics**:
  - Behavioral coherence (LLM-scored or human-rated)
  - Memory utilization (retrieval hit rate, recall accuracy)
  - Habit formation strength (repeat visit rate to specific locations)
  - Reflection quality (human-rated: meaningful self-awareness)
- **Expected finding**: Reflection makes agent behavior more consistent; structured memory makes location preference more pronounced
- **Target paper**: "Effects of structured spatiotemporal memory and reflection on agent habit formation and self-consistency"

### 8.2 Experiment 2: Spatial Structure Impact

- **Variables**: Fully-connected / Small-world / Ring NetworkX topologies
- **Control**: Same agent configurations
- **Metrics**: Interaction frequency, movement path entropy, conflict event count
- **Expected finding**: Small-world networks may produce richest emergent behavior

### 8.3 Experiment 3: Environment Robustness

- **Method**: WorldVariationGenerator produces 5-10 spatial variants
- **Test hypothesis**: "High-density residential areas increase conflict frequency"
- **Analysis**: Does the hypothesis hold across variants? What environmental features break it?

### 8.4 Methodology Requirements

- Record per experiment: model + version, all prompt templates, random seed, environment config snapshot
- Baseline comparison + statistical significance tests (multiple replicas + different seeds)
- Automate analysis via structured JSONL logs (Pandas + Plotly)
- Archive results with checkpoints for reproducibility

---

## 9. Non-Functional Requirements

### 9.1 Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Simulation step | < 5s per step (excl. LLM latency) | Wall clock |
| Memory retrieval | < 1s for top-5 results | Function timing |
| Checkpoint save | < 2s per checkpoint | File I/O timing |
| JSONL log write | < 100ms per entry | I/O timing |

### 9.2 Scalability

| Metric | Current | Target |
|--------|---------|--------|
| Agents per simulation | 4 (template) | Up to 20 |
| Locations per simulation | 4 (template) | Up to 15 |
| Simulation steps per run | Manual | Up to 1000+ (with checkpoints) |
| Concurrent experiments | 1 | 1 (subprocess-managed) |

### 9.3 Reliability

- Simulation state must be persistable and resumable via checkpoints
- JSONL logs must be valid and append-only (crash-safe)
- Each checkpoint must be a complete, self-contained state snapshot
- `done.flag` must only be written after successful completion

### 9.4 Extensibility

- New prompt templates can be added without code changes
- LLM provider swappable via config.py (OpenAI-compatible base_url)
- Cognitive modules are pluggable (swap memory strategy for ablation)
- Town data is JSON-based for easy customization
- Pydantic config enables schema-validated extensions

### 9.5 Code Quality

- All public functions have type annotations
- Files < 800 lines (target 200-400)
- Functions < 50 lines
- No wildcard imports
- No MethodType binding pattern
- No hardcoded values (use config)
- No emojis in code (terminal compatibility)

---

## 10. Dependency Management

### 10.1 Current Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| openai | any | LLM API client |
| networkx | any | Graph operations |
| numpy | any | Embedding operations |

### 10.2 Planned New Dependencies

| Package | Phase | Purpose | Justification |
|---------|-------|---------|--------------|
| pydantic | Phase 2 | Config validation | Industry standard, minimal overhead |
| streamlit | Phase 2 | Frontend MVP | Python-native, minimal setup |
| pyvis | Phase 2 | Spatial graph visualization | NetworkX-native visual output |
| plotly | Phase 2 | Charts and graphs | Streamlit-compatible, interactive |
| pandas | Phase 2 | Data analysis | DataFrame for experiment results |

### 10.3 Optional Dependencies (Balanced/Aggressive)

| Package | Path | Purpose |
|---------|------|---------|
| sqlite-vec | Balanced | SQLite vector extension for faster similarity search |
| litellm | Aggressive | Multi-model switching |
| jupyter | Balanced | Analysis notebooks |

---

## 11. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| API cost overrun | Medium | High | Per-experiment budget cap; cache high-hit memory responses; prioritize cheap models |
| AI-generated environment logic errors | Medium | Medium | Validation rules + LLM self-fix + human spot-check (initially) |
| Time shortage, module backlog | High | Medium | Weekly review of research value density; low-yield modules immediately deferred |
| Non-reproducible results | Low | High | Checkpoints + full config + JSONL logs; seed management |
| Introducing new tech debt | Medium | Medium | Code review; file < 800 lines; type annotations gradual introduction |
| Subprocess management issues | Medium | Low | Record PID to file; provide "terminate" button; frontend exception handling |
| Streamlit state loss | Medium | Low | All state in session_state; critical logic in functions |
| Old data format incompatibility | Low | Low | Fresh start; old projects/ retained as reference; no backward compat needed |

---

## 12. Timeline

### 12.1 Phase 1: Technical Debt + Cognitive Core (4-6 weeks)

```
Week 1: Refactor __main__.py + Agent MethodType + bug fix
  |-- F-101: Split __main__.py into simulator/ modules
  |-- F-102: Merge MethodType-bound functions into Agent class
  |-- F-108: Fix location description bug
  |-- Verification: uv run socialsimullm identical output

Week 2: Memory + logging infrastructure
  |-- F-103: Merge/merge memory modules into unified AgentMemory
  |-- F-106: Checkpoint + JSONL structured logging
  |-- F-107: Configuration management with CLI override
  |-- Verification: Checkpoint save/restore works

Week 3-4: Reflection system rewrite
  |-- F-104: Full rewrite of reflection module
  |-- Trigger conditions (scheduled + threshold)
  |-- Multi-level reflection (daily, pattern, social)
  |-- Verification: Agent references past reflections in behavior

Week 5-6: Memory structured upgrade + first ablation
  |-- F-105: MemoryEntry dataclass + multi-dim retrieval
  |-- Run first ablation experiment (baseline vs. structured vs. +reflection)
  |-- Verification: Experiment produces distinct metrics
  |-- Output: vNext + 1 working paper draft
```

### 12.2 Phase 2: Experiment Infrastructure + Frontend (6-10 weeks)

```
Phase 2a: Experiment Infrastructure (3-4 weeks)
  Week 1: F-201 ExperimentConfig Pydantic model
  Week 2: F-202 ExperimentRunner + CLI interface
  Week 3: F-203 Checkpoint format standardization + helpers
  Week 4: Batch run testing + spatial variant experiments
  Output: Reproducible experiment workflow

Phase 2b: Streamlit Frontend MVP (3-4 weeks)
  Week 1: Streamlit skeleton + configuration form
  Week 2: subprocess integration + file polling
  Week 3: pyvis spatial graph + Plotly charts
  Week 4: Testing + fixes + experiment verification loop
  Output: Researcher-usable operation panel
```

### 12.3 Phase 3: Extended Exploration (On demand)

No fixed timeline. Each feature independently evaluated for research value / development cost ratio. Low-return features immediately deferred.

---

## 13. User Stories

### US-101: Refactored Simulation

As a developer, I want the simulation to be modular so that I can modify one module without breaking others.

### US-102: Reproducible Experiment

As a researcher, I want to run an experiment with a config file and random seed so that anyone can reproduce my exact results.

### US-103: Interrupt-Resilient Simulation

As a researcher, I want long simulations to automatically save checkpoints so that I don't lose hours of API cost if the process crashes.

### US-104: Reflection-Enhanced Agents

As a researcher, I want agents to form self-aware reflections so that their behavior becomes more coherent and human-like across simulation days.

### US-105: Ablation Experiment

As a researcher, I want to compare baseline/structured-memory/reflection agents side-by-side so that I can write a publishable ablation study.

### US-106: Visual Experiment Monitoring

As a researcher, I want a web interface to configure and monitor experiments so that I don't have to manually edit JSON files and read text logs.

### US-107: Batch Experiment Execution

As a researcher, I want to run the same experiment with multiple random seeds so that I can perform statistical significance testing.

---

## 14. Acceptance Criteria Summary

### Phase 1 Exit Criteria

- [ ] `uv run socialsimullm` produces identical output to pre-refactoring baseline
- [ ] No MethodType bindings remain in codebase
- [ ] All modules < 200 lines, `__main__.py` < 50 lines
- [ ] AgentMemory provides unified API with multi-dim retrieval
- [ ] Reflection system produces non-trivial self-awareness (verified via logs)
- [ ] JSONL logs loadable by `pd.read_json(path, lines=True)`
- [ ] Checkpoint save/restore works for interrupted simulations
- [ ] CLI supports `--model`, `--steps`, `--project` overrides
- [ ] Location description bug fixed
- [ ] First ablation experiment produces distinct metrics across conditions

### Phase 2 Exit Criteria

- [ ] ExperimentConfig validates all parameters with Pydantic
- [ ] ExperimentRunner supports single + batch runs
- [ ] `uv run socialsimullm list` shows all experiments
- [ ] Streamlit: configure experiment via form -> run -> view results
- [ ] Simulation survives browser close (subprocess-based)
- [ ] Spatial graph renders via pyvis in Streamlit
- [ ] Agent behavior charts render via Plotly in Streamlit

---

## 15. Reference Resources

| Resource | Usage | Notes |
|----------|-------|-------|
| Generative Agents (Park et al. 2023) | Reflection system design | Core reference for reflection mechanism |
| Hindsight | Structured memory organization | 4-network: world facts, experiences, entity summaries, evolving beliefs |
| A-MEM | Agentic/Zettelkasten dynamic memory | Lightweight adaptation, not full adoption |
| ROMA (arXiv:2602.01848) | Recursive task decomposition | Inspiration only, no full implementation |
| YuLan-OneSim (arXiv:2505.07581) | NL scenario construction | Code-free scenario generation inspiration |
| AgentSociety | Large-scale simulation + experiment methods | Intervention/analysis tool reference |
| sqlite-vec | Lightweight SQLite vector extension | No extra process, suitable for solo dev |
