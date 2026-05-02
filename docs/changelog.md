# Changelog

All notable changes to SocialSimuLLM will be documented in this file.

## [3.1.0] - 2026-05-02

### Added (Phase 1)

- **F-101**: Split monolithic `__main__.py` into `simulator/core.py`, `simulator/state.py`, `simulator/events.py`
- **F-102**: Merged MethodType-bound functions from `agents/memory.py` and `agents/movement.py` into Agent class as proper methods
- **F-103**: Unified `AgentMemory` class replacing separate `agents/memory.py` and `retrieve/memory.py` modules
- **F-104**: Complete reflection system rewrite with `ReflectionEngine` class
  - Daily summary reflection (end-of-day trigger)
  - Pattern reflection (cross-day behavioral patterns)
  - Social reflection (relationship trends with other agents)
  - Scheduled + importance-threshold trigger mechanisms
  - Reflection-aware daily planning prompts
- **F-105**: `MemoryEntry` frozen dataclass as canonical memory record type
  - 13 typed fields with auto-generated UUID
  - Backward-compatible deserialization for v3.0 data
  - All recall methods return `list[MemoryEntry]`
  - Combined filtering via `recall_filtered()`
- **F-106**: `StructuredLogger` with JSONL structured logging + text logs + checkpoint save/restore
- **F-107**: `SimulationConfig` dataclass with CLI argument overrides and runtime validation
- **F-108**: Fixed location description bug using stale `description` variable

### Added (Phase 2)

- **F-201**: `ExperimentConfig` Pydantic model with YAML serialization and `to_simulation_config()` bridge
- **F-202**: `ExperimentRunner` with `run_single()` and `run_batch()` for reproducible experiments
- **F-203**: Experiment storage (`create_run_dir`, `list_experiments`, `load_checkpoint`, `find_run_dir`) and analysis (`load_results`, `load_results_dataframe`, `get_experiment_summary`, `compare_experiments`)
- **F-204**: Streamlit frontend MVP with experiment configuration form, subprocess-based experiment launch, and result visualization (spatial graph via pyvis, agent charts via plotly)
- CLI subcommands: `socialsimullm run`, `socialsimullm batch`, `socialsimullm list`
- `pydantic>=2.0` and `pyyaml` as core dependencies
- Optional dependency groups: `frontend` (streamlit, pyvis, plotly, pandas) and `analysis` (pandas, plotly)

### Changed

- `__main__.py` expanded from 27 to 96 lines (subcommand dispatch for run/batch/list + legacy fallback)
- `simulator/core.py` added `initial_event` parameter and absolute path support for experiment mode
- `utils/config.py` expanded from 222 to 293 lines (added `load_experiment_config()` subcommand parser)
- `pyproject.toml` added `pydantic`, `pyyaml` core deps and optional dependency groups
- Agent class now uses proper class methods (no MethodType binding)
- Memory storage uses `MemoryEntry` dataclass instead of loose dicts
- Field names renamed: `global_time` -> `timestamp`, `action` -> `content`, `action_des` -> `summary`, `exp_type` -> `event_type`, `priority` -> `importance`, `other_agents` -> `entities`, `location` -> `location_id`

### Removed

- `retrieve/memory.py`, `retrieve/reflect.py`, `retrieve/__init__.py` (merged into `agents/memory.py` and `agents/reflection.py`)
- `agents/movement.py` (merged into `agents/agent.py`)
- All `MethodType` imports and wildcard imports
- Deprecated `*_old` directories and `*.bat` files

### New Files (Phase 1)

- `agents/memory_entry.py` - MemoryEntry dataclass
- `agents/reflection.py` - ReflectionEngine standalone module
- `simulator/core.py` - SimulatorCore class
- `simulator/state.py` - SimulationState dataclass
- `simulator/events.py` - EventBus pub/sub infrastructure
- `utils/config.py` - SimulationConfig + load_config (rewrite)
- `utils/logger.py` - StructuredLogger (rewrite)

### New Files (Phase 2)

- `experiment/__init__.py` - Public exports
- `experiment/config.py` - ExperimentConfig Pydantic model
- `experiment/runner.py` - ExperimentRunner
- `experiment/storage.py` - Run directory management
- `experiment/analysis.py` - Result loading and analysis
- `frontend/__init__.py` - Package init
- `frontend/app.py` - Streamlit main entry
- `frontend/pages/configure.py` - Experiment configuration form
- `frontend/pages/results.py` - Result visualization
- `frontend/components/forms.py` - Pydantic-to-Streamlit mapping
- `frontend/components/viz.py` - pyvis + plotly rendering
- `frontend/utils.py` - Subprocess launch and polling

## [3.0.0] - 2025-02-23

- Enhanced agent memory and reflection capabilities
- Optimized simulation prompts
- Improved agent learning capacity and adaptability

## [2.0.0] - 2025-02-22

- Optimized memory retrieval
- Improved agent state evaluation
- Refined memory management
- Database interaction groundwork
- Optimized main program and prompts
