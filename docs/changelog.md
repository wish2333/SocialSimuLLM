# Changelog

All notable changes to SocialSimuLLM will be documented in this file.

## [3.1.0] - 2026-05-03

### Added (Phase 3 - Sprint 1: Spatial Foundation)

- **F-305**: `WorldVariationGenerator` for diverse spatial graph topologies
  - Supports: ring, small_world, grid, random, scale_free
  - `SpatialConfig` dataclass with topology, num_locations, edge_weight_range, seed, extra_params
  - `generate_graph()` + `generate_town_data()` + `topology_presets()`
- **F-301**: `FieldOfView` proximity-based agent perception system
  - Graph distance-based visibility computation
  - `FOVConfig` with distance_threshold (0 = legacy same-location-only behavior)
  - `PerceptibleAgent` dataclass, `get_visible_agents()`, `format_visible_agents()`, `format_nearby_context()`

### Added (Phase 3 - Sprint 2: Intelligent Movement)

- **F-302**: `PathPlanner` with LLM movement intent inference + A* shortest path
  - `PathPlannerConfig`, `MovementIntent`, `PlannedPath` dataclasses
  - Multi-hop traversal: agent moves one graph node per step
  - `plan_movement()`, `execute_step()`, `format_path_context()`
- **F-303**: Goal-driven hierarchical planning system
  - `GoalManager` with `Goal` dataclass, `GoalStatus` enum
  - `initialize_goals()`, `review_and_update_goals()`, `decompose_goal()`
  - `serialize_goals()` / `deserialize_goals()` for checkpoint persistence
  - **F-307**: `RecursiveTaskDecomposer` in same module
    - `decompose()`, `order_by_dependency()`, `get_immediate_tasks()`, `format_task_plan()`

### Added (Phase 3 - Sprint 3: Research Productivity)

- **F-304**: Jupyter analysis templates (4 notebooks + shared data_loader)
  - `00_quick_start.ipynb`, `01_behavioral_analysis.ipynb`, `02_spatial_analysis.ipynb`, `03_experiment_comparison.ipynb`
  - `data_loader.py` (218 lines): `load_experiment()`, `load_checkpoints()`, `extract_*_events()`, `build_agent_timeline()`, `compute_*_matrix()`
- **F-306**: `ScenarioGenerator` for natural language scenario construction
  - `generate()`, `refine()`, `validate_town_data()` (static + LLM validation)
  - `save()`, `_parse_json_response()`, `_normalize_structure()`

### Added (Phase 3 - Sprint 4: Advanced Analysis)

- **F-310**: Advanced visualization components
  - `replay.py` (141 lines): checkpoint timeline slider, agent positions, spatial graph, step events
  - `heatmap.py` (199 lines): location occupancy, agent activity, location transition frequency
  - `results.py` expanded with replay + heatmap tabs
- **F-311**: Semi-auto research assistant
  - `ResearchAssistant` class: `summarize_experiment()`, `identify_patterns()`, `suggest_hypotheses()`, `compare_runs()`, `generate_report()`
  - `assistant.py` page: single/multi-experiment analysis UI
  - `app.py` expanded with "Research Assistant" tab

### Changed (Phase 3)

- `simulator/core.py` expanded from 427 to 571 lines (world, FOV, path planner, goal system integration)
- `agents/agent.py` expanded from 276 to 283 lines (added `planned_path` and `goals` attributes)
- `experiment/config.py` expanded from 216 to 289 lines (SpatialConfig, FOV, PathPlanner, Goal, MemoryConfig fields)
- `experiment/runner.py` expanded from 179 to 250 lines (spatial graph generation, FOV/path/goal support)
- `experiment/__init__.py` added `ScenarioGenerator` and `MemoryConfig` exports
- `utils/config.py` expanded from 293 to 299 lines (fov_enabled, fov_distance, path_planner_enabled, multi_hop_movement, goal_enabled, max_active_goals)
- `utils/logger.py` added goal_review event type and goal checkpoint support
- `prompt_templates/template_agents.py` added movement intent, goal creation, goal context, task decomposition prompts
- `frontend/pages/results.py` expanded from 174 to 266 lines (replay + heatmap tabs)
- `frontend/app.py` expanded from 32 to 38 lines (Research Assistant tab)

### New Files (Phase 3)

- `world/__init__.py` (13) - World modeling package
- `world/spatial.py` (278) - WorldVariationGenerator + SpatialConfig
- `world/field_of_view.py` (234) - FieldOfView + FOVConfig + PerceptibleAgent
- `world/path_planner.py` (341) - PathPlanner + PathPlannerConfig + MovementIntent + PlannedPath
- `cognition/__init__.py` (13) - Cognition package
- `cognition/goal.py` (760) - GoalManager + Goal + GoalStatus + RecursiveTaskDecomposer + GoalConfig
- `experiment/scenario.py` (370) - ScenarioGenerator
- `experiment/assistant.py` (298) - ResearchAssistant
- `frontend/components/replay.py` (141) - Checkpoint replay visualization
- `frontend/components/heatmap.py` (199) - Heatmap visualization (occupancy, activity, transitions)
- `frontend/pages/assistant.py` (177) - Research assistant UI page
- `notebooks/data_loader.py` (218) - Shared Jupyter data loading utilities
- `notebooks/00_quick_start.ipynb` - Quick start notebook
- `notebooks/01_behavioral_analysis.ipynb` - Behavioral analysis notebook
- `notebooks/02_spatial_analysis.ipynb` - Spatial analysis notebook
- `notebooks/03_experiment_comparison.ipynb` - Experiment comparison notebook

### Deferred (Phase 3 Aggressive)

- F-308: Lightweight cultural evolution
- F-309: LiteLLM full integration
- F-312: A2A/MCP prototype

---

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
