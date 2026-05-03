# Phase 1

## Sprint 1

```
  Sprint 1 完成: F-101, F-102, F-108

  已完成
  ┌─────────┬────────┬───────────────────────────────────────────────────────────────────────────────────────────────┐
  │ Feature │ Status │                                            Details                                            │
  ├─────────┼────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
  │ F-102   │ Done   │ 10 functions merged from memory.py+movement.py into Agent class. Both files deleted. No       │
  │         │        │ MethodType, no wildcard imports.                                                              │
  ├─────────┼────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
  │ F-108   │ Done   │ locations.add_location(name, detail) uses correct detail from town_areas instead of stale     │
  │         │        │ description.                                                                                  │
  ├─────────┼────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
  │ F-101   │ Done   │ __main__.py split: 32-line CLI entry + simulator/core.py (438) + state.py (46) + events.py    │
  │         │        │ (51).                                                                                         │
  └─────────┴────────┴───────────────────────────────────────────────────────────────────────────────────────────────┘

  Files Changed

  - Rewritten: agents/agent.py, __main__.py
  - Created: simulator/__init__.py, simulator/core.py, simulator/state.py, simulator/events.py
  - Deleted: agents/memory.py, agents/movement.py
  - Fixed: utils/text_generation.py (wildcard -> explicit import)

  Code Review Fixes Applied

  - summary_input now properly threaded through all helper methods (was lost in _daily_planning)
  - _reflection accumulates to summary_input for summaries
  - Summary logic moved into step() (no dead code stub)
  - Removed unused import re from agent.py

  Notes

  - core.py is 438 lines (above the 200-line aspiration but well under the 800-line hard limit). The logging/summary
    orchestration adds significant bulk. Will be addressed in F-106 (Week 2) when structured JSONL logging replaces the
      current string accumulation pattern.
  - EventBus is created but unused yet -- it's infrastructure for future event handling.
```

## Sprint 2

```
  Sprint 2 完成: F-103, F-106, F-107

  已完成

  ┌─────────┬────────┬───────────────────────────────────────────────────────────────────────────────────────────────┐
  │ Feature │ Status │                                            Details                                            │
  ├─────────┼────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
  │ F-107   │ Done   │ SimulationConfig dataclass with CLI args (--project, --model, --steps, --checkpoint-interval).│
  │         │        │ load_config() with env var overrides. validate_config(). Backward-compatible module globals.    │
  ├─────────┼────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
  │ F-103   │ Done   │ AgentMemory class (297 lines) replaces Memory from retrieve/memory.py. Unified API: store(),  │
  │         │        │ recall_recent(), recall_semantic(), recall_by_location(), recall_time_span(),                  │
  │         │        │ recall_by_importance(), recall_impressions(). Deleted retrieve/memory.py, reflect.py,          │
  │         │        │ __init__.py. 25+ call sites updated in core.py. Storage format unchanged (backward compat).   │
  ├─────────┼────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
  │ F-106   │ Done   │ StructuredLogger (312 lines) with JSONL events.jsonl + text simulation_log.txt + checkpoint  │
  │         │        │ save/restore. LogConfig dataclass. done.flag completion marker. core.py reduced from 438 to   │
  │         │        │ 376 lines (logging bloat removed).                                                         │
  └─────────┴────────┴───────────────────────────────────────────────────────────────────────────────────────────────┘

  Files Changed
  - Created: utils/config.py (rewrite), agents/memory.py, utils/logger.py
  - Modified: __main__.py, simulator/core.py, simulator/state.py
  - Deleted: retrieve/memory.py, retrieve/reflect.py, retrieve/__init__.py (whole directory)

  Code Review Fixes Applied
  - Division-by-zero guard in recall_semantic cosine similarity
  - step() captures log_output before flush (was returning empty string)
  - store() explicitly writes to acting agent before fan-out
  - _load_events accepts optional event parameter for non-interactive mode
  - log_round_end format consistent between file and console
```

## Sprint 3

```
F-104 Reflection System Rewrite -- Complete
Files Changed
File	Action	Lines
agents/reflection.py	Created	392
agents/memory.py	Modified	344 (+24)
agents/agent.py	Modified	278 (-19)
simulator/core.py	Modified	423 (+25/-15)
prompt_templates/template_agents.py	Modified	152 (+46)
utils/config.py	Modified	222 (+15)
What was built
ReflectionEngine standalone class with Protocol-based coupling to AgentMemory and Agent
3 reflection types: daily (end-of-day summary), pattern (cross-day behavioral patterns, requires >= 2 prior daily reflections), social (relationship trends with other agents)
2 trigger mechanisms: scheduled (end of each day) + threshold (mid-day, when cumulative importance of un-reflected observations exceeds configurable threshold, default 15)
Cached last-reflection times to avoid repeated JSON file reads for threshold checks
Reflection-aware daily planning: past reflections injected into planning prompts
New CLI flags: --no-reflection (disable entirely), --reflection-threshold N
6 new prompt templates replacing 2 old ones
Code review fixes applied
Fixed race condition (double reflection on day boundaries)
Fixed recall_reflections return order (now most-recent-first)
Removed broken _reflection_fallback no-op
Fixed "Day 999" sentinel to "Day 99999" for lexicographic safety

F-105 Memory System Structured Upgrade -- Complete
Files Changed
File	Action	Lines
agents/memory_entry.py	Created	153
agents/memory.py	Modified	374 (+54/-30)
agents/agent.py	Modified	276 (+6/-118)
agents/reflection.py	Modified	392 (+19/-17)
simulator/core.py	Modified	423 (+14/-8)
utils/logger.py	Modified	312 (+4/-2)
What was built
MemoryEntry frozen dataclass replacing loose dicts as the canonical memory record type
13 typed fields: id (UUID), agent_name, timestamp, location_id, event_type, content, summary, entities, importance, embedding, reflection_link, reflection_type, metadata
create() factory method with auto-generated UUID
to_dict() / from_dict() serialization with full v3.0 backward compatibility (old field names: global_time, action, action_des, exp_type, priority, other_agents, location)
All 5 agent memory_*() methods now return MemoryEntry instead of dict
AgentMemory.store() accepts MemoryEntry, all recall_*() methods return list[MemoryEntry]
reflection.py _build_observation_dict() returns MemoryEntry
core.py uses attribute access (entry.content, entry.event_type) instead of dict key access
logger.py snapshot_memory_stats() has backward-compat field name fallbacks
Code review fixes applied
Division-by-zero guard in recall_semantic cosine similarity
step() captures log_output before flush
store() explicitly writes to acting agent before fan-out
```

# Phase 2

## Sprint 1-4 Combined

```
Phase 2 完成: F-201, F-202, F-203, F-204

已完成

┌─────────┬────────┬───────────────────────────────────────────────────────────────────────────────────────────────┐
│ Feature │ Status │                                            Details                                            │
├─────────┼────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
│ F-201   │ Done   │ ExperimentConfig (Pydantic, 216 lines) + MemoryConfig. YAML serialization,                   │
│         │        │ to_simulation_config() bridge, auto UUID experiment_id, event list support.                    │
│         │        │ API keys resolved from env vars, never stored in config.                                       │
├─────────┼────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
│ F-202   │ Done   │ ExperimentRunner (179 lines) with run_single() and run_batch().                               │
│         │        │ Batch uses model_copy() for per-seed config isolation. Duplicate experiment detection.          │
│         │        │ Calls SimulatorCore with initial_event from config.                                            │
├─────────┼────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
│ F-203   │ Done   │ storage.py (281 lines): create_run_dir(), list_experiments(), load_checkpoint(),              │
│         │        │ find_run_dir(), get_latest_checkpoint_step(), is_complete().                                   │
│         │        │ analysis.py (179 lines): load_results(), load_results_dataframe(),                             │
│         │        │ get_experiment_summary(), compare_experiments(). Lazy pandas import.                           │
├─────────┼────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
│ F-204   │ Done   │ Streamlit MVP frontend (891 lines total):                                                    │
│         │        │ app.py (32): two-tab layout (Configure / Results).                                             │
│         │        │ configure.py (138): experiment form + Save & Run + auto-poll.                                  │
│         │        │ results.py (174): experiment selector + checkpoint viewer + viz tabs.                           │
│         │        │ forms.py (104): pydantic-to-streamlit widget mapping.                                         │
│         │        │ viz.py (137): pyvis spatial graph + plotly agent charts.                                       │
│         │        │ utils.py (89): subprocess launch + done.flag polling.                                         │
└─────────┴────────┴───────────────────────────────────────────────────────────────────────────────────────────────┘

Files Changed

- Created: experiment/__init__.py (43), experiment/config.py (216), experiment/runner.py (179),
  experiment/storage.py (281), experiment/analysis.py (179)
- Created: frontend/__init__.py (3), frontend/app.py (32), frontend/pages/configure.py (138),
  frontend/pages/results.py (174), frontend/components/forms.py (104), frontend/components/viz.py (137),
  frontend/utils.py (89)
- Modified: __main__.py (27->96 lines, subcommand dispatch for run/batch/list + legacy fallback)
- Modified: simulator/core.py (+10 lines: initial_event param + absolute path support)
- Modified: utils/config.py (+71 lines: load_experiment_config() subcommand parser)
- Modified: pyproject.toml (+14 lines: pydantic, pyyaml core deps + frontend/analysis optional groups)
- Modified: .gitignore (runs/, *.flag)

Architecture

ExperimentConfig (Pydantic) wraps SimulationConfig (dataclass).
ExperimentConfig.to_simulation_config() bridges the two.
API keys come from env vars only -- never stored in ExperimentConfig.
SimulatorCore only ever sees SimulationConfig.

CLI Modes

| Invocation                                          | Behavior                                              |
| --------------------------------------------------- | ----------------------------------------------------- |
| socialsimullm --project t7                          | Legacy mode, writes to projects/t7/                   |
| socialsimullm --project t7 --steps 144              | Legacy mode with steps                                |
| socialsimullm t7                                    | Legacy mode (positional arg)                          |
| socialsimullm run --config X.yaml                   | Experiment mode, writes to runs/{project}/{id}/       |
| socialsimullm batch --config X.yaml --seeds 42,43   | Batch experiment mode                                 |
| socialsimullm list                                  | List all experiments                                  |

Frontend

Launch: uv run streamlit run src/socialsimullm/frontend/app.py
Optional dependencies: streamlit>=1.30, pyvis>=0.3, plotly>=5.0, pandas>=2.0
```
# Phase 3 Implementation Plan: SocialSimuLLM Extended Exploration

## Context

Phase 1 (refactoring + cognitive core) and Phase 2 (experiment infrastructure + Streamlit frontend) are complete. Phase 3 transforms the simulation from a basic ring-graph prototype into a research platform with spatial awareness, intentional movement, goal-driven planning, and AI-assisted analysis. This enables the PRD-defined Experiments 2 (Spatial Structure Impact) and 3 (Environment Robustness).

**Scope**: Balanced path (F-301~F-305) + selected Aggressive features (F-306, F-307, F-310, F-311).

---

## Sprint Breakdown

### Sprint 1: Spatial Foundation (F-305 + F-301)
~5 days | Establish `world/` module, weighted graphs, proximity perception

### Sprint 2: Intelligent Movement (F-302 + F-303)
~6 days | A* pathfinding, LLM movement intent, goal-driven planning

### Sprint 3: Research Productivity (F-304 + F-307 + F-306)
~6 days | Jupyter templates, ROMA decomposition, NL scenario generation

### Sprint 4: Advanced Analysis (F-310 + F-311)
~5 days | Replay visualization, heatmaps, AI research assistant

---

## Sprint 1: Spatial Foundation

### F-305: WorldVariationGenerator

**Create**:
- `src/socialsimullm/world/__init__.py`
- `src/socialsimullm/world/spatial.py` (~300 lines)

**Key interfaces**:
```python
@dataclass(frozen=True)
class SpatialConfig:
    topology: str = "ring"  # ring | small_world | grid | random | scale_free
    num_locations: int = 4
    edge_weight_range: tuple[float, float] = (1.0, 1.0)
    seed: int = 42
    extra_params: dict[str, Any] = field(default_factory=dict)

class WorldVariationGenerator:
    def generate_graph(self, area_names: list[str]) -> nx.Graph: ...
    def generate_town_data(self, base_template: dict) -> dict: ...
    @staticmethod
    def topology_presets() -> dict[str, dict[str, Any]]: ...
```

**Modify**:
- `experiment/config.py` -- add `SpatialConfig` Pydantic model
- `experiment/runner.py` -- call generator when `spatial_config` set
- `simulator/core.py` -- refactor `_create_world_graph()` to delegate to generator

### F-301: FieldOfView

**Create**:
- `src/socialsimullm/world/field_of_view.py` (~250 lines)

**Key interfaces**:
```python
@dataclass(frozen=True)
class FOVConfig:
    enabled: bool = False
    distance_threshold: float = 0.0  # 0 = same location only (legacy)

@dataclass(frozen=True)
class PerceptibleAgent:
    name: str; description: str; location: str; distance: float; is_co_located: bool

class FieldOfView:
    def get_visible_agents(self, observer, all_agents) -> list[PerceptibleAgent]: ...
    def format_visible_agents(self, observer, all_agents) -> str: ...
    def format_nearby_context(self, observer, all_agents) -> str: ...
```

**Modify**:
- `simulator/core.py` -- inject FOV data into `_hourly_planning()` and `_execute_actions()`
- `experiment/config.py` -- add `fov_enabled`, `fov_distance` fields
- `utils/config.py` -- add FOV to `SimulationConfig`

**Verify**:
- Generate each topology, verify connectedness
- FOV `distance_threshold=0` matches legacy behavior
- Existing experiments without `spatial_config` still produce ring graphs

---

## Sprint 2: Intelligent Movement

### F-302: PathPlanner (LLM intent + A*)

**Create**:
- `src/socialsimullm/world/path_planner.py` (~350 lines)

**Key interfaces**:
```python
@dataclass
class MovementIntent:
    destination: str; reason: str; urgency: float

@dataclass
class PlannedPath:
    agent_name: str; origin: str; destination: str
    path: list[str]; total_distance: float; steps_remaining: int

class PathPlanner:
    def infer_movement_intent(self, agent, hourly_plan, visible_agents) -> MovementIntent: ...
    def find_path(self, origin, destination) -> list[str]: ...
    def plan_movement(self, agent, hourly_plan, visible_agents) -> PlannedPath | None: ...
    def execute_step(self, planned_path) -> str | None: ...
    def format_path_context(self, agent) -> str: ...
```

**Modify**:
- `agents/agent.py` -- add `planned_path` attribute
- `simulator/core.py` -- replace `_movement()` with PathPlanner integration
- `prompt_templates/template_agents.py` -- add movement intent prompt
- `experiment/config.py` -- add `path_planner_enabled`, `multi_hop_movement`

### F-303: Goal-Driven Planning

**Create**:
- `src/socialsimullm/cognition/__init__.py`
- `src/socialsimullm/cognition/goal.py` (~400 lines)

**Key interfaces**:
```python
class GoalStatus(Enum): ACTIVE | IN_PROGRESS | COMPLETED | ABANDONED | BLOCKED

@dataclass
class Goal:
    id: str; description: str; status: GoalStatus; priority: int
    created_at: str; deadline: str | None; parent_id: str | None
    sub_goals: list[Goal]; completion_conditions: str

class GoalManager:
    def initialize_goals(self, agent_description, initial_events) -> list[Goal]: ...
    def review_and_update_goals(self, agent, recent_memories, current_time) -> list[Goal]: ...
    def decompose_goal(self, goal, context) -> list[Goal]: ...
    def format_goals_context(self, goals) -> str: ...
    def check_completion(self, goal, recent_actions) -> GoalStatus: ...
    def serialize_goals(self, goals) -> list[dict]: ...
    def deserialize_goals(self, data) -> list[Goal]: ...
```

**Modify**:
- `agents/agent.py` -- add `goals` attribute
- `simulator/core.py` -- call goal management in daily planning
- `prompt_templates/template_agents.py` -- add goal planning prompts
- `utils/logger.py` -- add goal event types, checkpoint save/restore goals

**Verify**:
- A* returns correct paths on weighted graphs
- Multi-hop: agent traverses one node per step
- Goals persist across daily boundaries via checkpoints
- Legacy mode (all disabled) runs identically to Phase 2

---

## Sprint 3: Research Productivity

### F-304: Jupyter Analysis Templates

**Create**:
- `notebooks/data_loader.py` (~150 lines) -- shared import module
- `notebooks/00_quick_start.ipynb`
- `notebooks/01_behavioral_analysis.ipynb`
- `notebooks/02_spatial_analysis.ipynb`
- `notebooks/03_experiment_comparison.ipynb`

**Modify**:
- `experiment/analysis.py` -- add helper functions for notebooks

### F-307: Simplified ROMA Planning

**Modify** (extends F-303 `cognition/goal.py`):
```python
class RecursiveTaskDecomposer:
    def decompose(self, goal, context, depth=0) -> list[Goal]: ...
    def order_by_dependency(self, goals) -> list[Goal]: ...
    def get_immediate_tasks(self, goals) -> list[Goal]: ...
    def format_task_plan(self, tasks) -> str: ...
```
- `prompt_templates/template_agents.py` -- add recursive decomposition prompts

### F-306: NL Scenario Construction

**Create**:
- `src/socialsimullm/experiment/scenario.py` (~250 lines)

**Key interfaces**:
```python
class ScenarioGenerator:
    def generate(self, scenario_description: str) -> dict: ...
    def validate_town_data(self, town_data: dict) -> list[str]: ...
    def refine(self, scenario_description, feedback, existing_town_data) -> dict: ...
```

**Modify**:
- `experiment/config.py` -- add `scenario_description` field
- `experiment/runner.py` -- call scenario generator before run
- `__main__.py` -- add `generate` subcommand
- `frontend/pages/configure.py` -- add NL scenario text area

**Verify**:
- All 4 notebooks run end-to-end against existing data
- `uv run socialsimullm generate --description "..."` produces valid JSON
- ROMA decomposition produces ordered task tree

---

## Sprint 4: Advanced Analysis

### F-310: Advanced Visualization (Replay + Heatmap)

**Create**:
- `src/socialsimullm/frontend/components/replay.py` (~200 lines)
- `src/socialsimullm/frontend/components/heatmap.py` (~150 lines)

**Modify**:
- `frontend/pages/results.py` -- add Replay and Heatmaps tabs
- `experiment/analysis.py` -- add timeline/interaction helpers

### F-311: Semi-Auto Research Assistant

**Create**:
- `src/socialsimullm/experiment/assistant.py` (~300 lines)
- `src/socialsimullm/frontend/pages/assistant.py` (~200 lines)

**Key interfaces**:
```python
class ResearchAssistant:
    def summarize_experiment(self, experiment_id, project) -> str: ...
    def identify_patterns(self, experiment_id, project) -> list[str]: ...
    def suggest_hypotheses(self, experiment_id, project) -> list[str]: ...
    def compare_runs(self, experiment_ids, project) -> str: ...
    def generate_report(self, experiment_id, project) -> str: ...
```

**Modify**:
- `frontend/app.py` -- add "Research Assistant" tab

**Verify**:
- Replay slider navigates checkpoints, agent positions update
- Heatmaps render with color scale
- Assistant generates non-empty summaries from experiment data

---

## Dependency Graph

```
F-305 (WorldVariation) --> F-301 (FOV) --> F-302 (PathPlanner) --> F-303 (Goals) --> F-307 (ROMA)
                                                                        |
F-304 (Jupyter) [independent]                                          |
F-306 (NL Scenario) [independent]                                     v
F-311 (Research Assistant) [independent]                          F-310 (Adv Viz)
```

# Phase 3 实现完成

## Sprint 1: Spatial Foundation (F-305 + F-301)

```
  Sprint 1 完成: F-305, F-301

  已完成

  ┌─────────┬────────┬───────────────────────────────────────────────────────────────────────────────────────────────┐
  │ Feature │ Status │                                            Details                                            │
  ├─────────┼────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
  │ F-305   │ Done   │ WorldVariationGenerator (278 lines): ring, small_world, grid, random, scale_free 拓扑生成。      │
  │         │        │ SpatialConfig dataclass (topology, num_locations, edge_weight_range, seed, extra_params)。      │
  │         │        │ generate_graph() + generate_town_data() + topology_presets()。                                 │
  ├─────────┼────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
  │ F-301   │ Done   │ FieldOfView (234 lines): 基于 graph distance 的 proximity perception。                        │
  │         │        │ FOVConfig (enabled, distance_threshold, include_location_info)。                               │
  │         │        │ PerceptibleAgent dataclass。get_visible_agents(), format_visible_agents(),                      │
  │         │        │ format_nearby_context()。distance_threshold=0 保持 legacy 行为。                                │
  └─────────┴────────┴───────────────────────────────────────────────────────────────────────────────────────────────┘

  Files Changed
  - Created: world/__init__.py (13), world/spatial.py (278), world/field_of_view.py (234)
  - Modified: simulator/core.py (427->571), experiment/config.py (216->289), utils/config.py (293->299)
```

## Sprint 2: Intelligent Movement (F-302 + F-303)

```
  Sprint 2 完成: F-302, F-303

  已完成

  ┌─────────┬────────┬───────────────────────────────────────────────────────────────────────────────────────────────┐
  │ Feature │ Status │                                            Details                                            │
  ├─────────┼────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
  │ F-302   │ Done   │ PathPlanner (341 lines): LLM movement intent inference + A* shortest path。                    │
  │         │        │ PathPlannerConfig, MovementIntent, PlannedPath dataclasses。                                   │
  │         │        │ plan_movement(), execute_step() for multi-hop traversal。                                       │
  │         │        │ Agent.planned_path attribute for persistent path state。                                       │
  ├─────────┼────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
  │ F-303   │ Done   │ GoalManager + RecursiveTaskDecomposer (760 lines in cognition/goal.py)。                       │
  │         │        │ Goal dataclass with GoalStatus enum (ACTIVE/IN_PROGRESS/COMPLETED/ABANDONED/BLOCKED)。         │
  │         │        │ initialize_goals(), review_and_update_goals(), decompose_goal()。                              │
  │         │        │ serialize/deserialize for checkpoint persistence。                                             │
  │         │        │ Agent.goals attribute for persistent goal state。                                              │
  └─────────┴────────┴───────────────────────────────────────────────────────────────────────────────────────────────┘

  Files Changed
  - Created: world/path_planner.py (341), cognition/__init__.py (13), cognition/goal.py (760)
  - Modified: agents/agent.py (276->283), simulator/core.py (->571), experiment/config.py (->289),
    utils/config.py (->299), prompt_templates/template_agents.py (152, +new prompts)
```

## Sprint 3: Research Productivity (F-304 + F-307 + F-306)

```
  Sprint 3 完成: F-304, F-307, F-306

  已完成

  ┌─────────┬────────┬───────────────────────────────────────────────────────────────────────────────────────────────┐
  │ Feature │ Status │                                            Details                                            │
  ├─────────┼────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
  │ F-304   │ Done   │ Jupyter analysis templates (4 notebooks + shared data_loader.py 218 lines)。                   │
  │         │        │ 00_quick_start, 01_behavioral_analysis, 02_spatial_analysis, 03_experiment_comparison。       │
  │         │        │ data_loader: load_experiment(), load_checkpoints(), extract_*_events(),                        │
  │         │        │ build_agent_timeline(), compute_*_matrix()。                                                 │
  ├─────────┼────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
  │ F-307   │ Done   │ RecursiveTaskDecomposer in cognition/goal.py。                                              │
  │         │        │ decompose(), order_by_dependency(), get_immediate_tasks(), format_task_plan()。                 │
  │         │        │ Goal decomposition prompt templates added to template_agents.py。                              │
  ├─────────┼────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
  │ F-306   │ Done   │ ScenarioGenerator (370 lines): NL scenario -> town_data.json via LLM synthesis。              │
  │         │        │ generate(), refine(), validate_town_data() (static + LLM validation)。                        │
  │         │        │ save(), _parse_json_response(), _normalize_structure()。                                       │
  │         │        │ experiment/config.py: scenario_description field。                                            │
  │         │        │ experiment/__init__.py: ScenarioGenerator export。                                             │
  └─────────┴────────┴───────────────────────────────────────────────────────────────────────────────────────────────┘

  Files Changed
  - Created: experiment/scenario.py (370), notebooks/data_loader.py (218), 4 Jupyter notebooks
  - Modified: cognition/goal.py (+RecursiveTaskDecomposer), experiment/config.py, experiment/__init__.py,
    prompt_templates/template_agents.py
```

## Sprint 4: Advanced Analysis (F-310 + F-311)

```
  Sprint 4 完成: F-310, F-311

  已完成

  ┌─────────┬────────┬───────────────────────────────────────────────────────────────────────────────────────────────┐
  │ Feature │ Status │                                            Details                                            │
  ├─────────┼────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
  │ F-310   │ Done   │ Replay component (141 lines): checkpoint timeline slider, agent positions, spatial graph,     │
  │         │        │ step events。Heatmap component (199 lines): location occupancy, agent activity,                │
  │         │        │ location transition frequency。results.py expanded to 266 lines with replay + heatmap tabs。   │
  ├─────────┼────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
  │ F-311   │ Done   │ ResearchAssistant (298 lines): summarize_experiment(), identify_patterns(),                  │
  │         │        │ suggest_hypotheses(), compare_runs(), generate_report()。                                      │
  │         │        │ assistant.py page (177 lines): single/multi-experiment analysis UI。                          │
  │         │        │ app.py expanded to 38 lines with Research Assistant tab。                                     │
  └─────────┴────────┴───────────────────────────────────────────────────────────────────────────────────────────────┘

  Files Changed
  - Created: frontend/components/replay.py (141), frontend/components/heatmap.py (199),
    experiment/assistant.py (298), frontend/pages/assistant.py (177)
  - Modified: frontend/pages/results.py (174->266), frontend/app.py (32->38)
```

### Phase 3 总计

```
新建文件 (12):
  world/__init__.py (13), world/spatial.py (278), world/field_of_view.py (234),
  world/path_planner.py (341), cognition/__init__.py (13), cognition/goal.py (760),
  experiment/scenario.py (370), experiment/assistant.py (298),
  frontend/components/replay.py (141), frontend/components/heatmap.py (199),
  frontend/pages/assistant.py (177), notebooks/data_loader.py (218)
  4 Jupyter notebooks (00-03)
  总计: ~3,040 行新代码 + ~1,000 行 notebook

修改文件 (9):
  simulator/core.py (427->571, +144), agents/agent.py (276->283, +7),
  experiment/config.py (216->289, +73), experiment/runner.py (+Spatial/FOV/Goal support),
  experiment/__init__.py (+ScenarioGenerator, MemoryConfig exports),
  utils/config.py (293->299, +6), utils/logger.py (+goal event types),
  prompt_templates/template_agents.py (+movement intent, goal, decomposition prompts),
  frontend/pages/results.py (174->266, +92), frontend/app.py (32->38, +6)

未实现 (Phase 3 Aggressive path, deferred):
  F-308: Lightweight cultural evolution
  F-309: LiteLLM full integration
  F-312: A2A/MCP prototype
```

**ExperimentConfig**: `spatial_config`, `fov_enabled`, `fov_distance`, `path_planner_enabled`, `multi_hop_movement`, `goal_enabled`, `max_active_goals`, `scenario_description`

**SimulationConfig**: `fov_enabled`, `fov_distance`, `path_planner_enabled`, `goal_enabled`

---

## File Creation Summary

| Sprint | File | Lines |
|--------|------|-------|
| 1 | `world/__init__.py` | 5 |
| 1 | `world/spatial.py` | 300 |
| 1 | `world/field_of_view.py` | 250 |
| 2 | `world/path_planner.py` | 350 |
| 2 | `cognition/__init__.py` | 5 |
| 2 | `cognition/goal.py` | 400 |
| 3 | `experiment/scenario.py` | 250 |
| 3 | `notebooks/data_loader.py` | 150 |
| 3 | `notebooks/*.ipynb` (4 files) | ~1000 |
| 4 | `frontend/components/replay.py` | 200 |
| 4 | `frontend/components/heatmap.py` | 150 |
| 4 | `experiment/assistant.py` | 300 |
| 4 | `frontend/pages/assistant.py` | 200 |
| **Total new** | | **~3,560** |

## Critical Files to Modify (all sprints)

- `simulator/core.py` -- step loop integration for all features
- `agents/agent.py` -- goals, planned_path attributes
- `experiment/config.py` -- all new config fields
- `prompt_templates/template_agents.py` -- new prompts
- `utils/config.py` -- SimulationConfig additions

# 测试

## Based on Test1 - smoke test

- max-token自查

- 完成后请自查

- Smoke Test 自查报告

  ### 一、发现的问题

  | #    | 问题                        | 严重度 | 现象                                                         |
  | ---- | --------------------------- | ------ | ------------------------------------------------------------ |
  | 1    | `list` 命令目录扫描逻辑错误 | P0     | 实验已完成(done.flag 存在, events.jsonl 有 138 行)，但 `list` 输出 0 steps / 0 events / status=running |
  | 2    | reflection_token_limit 过小 | P0     | error.log 记录 23 次 "all 3 attempts failed"，DeepSeek V4 的思考 token 耗尽预算导致 JSON 输出空间为零 |
  | 3    | "Do something" 泛化回复     | P1     | prompt 模板中直接给出了 `"Do something[action]: ..."` 作为示例，模型学会了这种写法 |
  | 4    | 反思过度触发                | P1     | 无冷却机制 + 反思产物计入 importance 形成正反馈循环，导致每轮刷 2-3 条重复反思 |
  | 5    | 行为缺乏递进感              | 提升   | agent 每 round 只知道 hourly_plan，不知道自己上一步做了什么，导致重复编独立动作 |

  ### 二、修复方案

  **问题 1 -- storage.py**

  - `list_experiments` 只扫描 `runs/{project}/{exp_id}/` 两级结构，但 `project=''` 时目录是扁平的 `runs/{exp_id}/`
  - 新增 `_is_experiment_dir()` 辅助函数，支持扁平和嵌套两种布局
  - 用 `seen` 集合去重，防止同一实验被两种扫描路径重复计数
  - Steps 列改为优先从 `meta.json` 的 `round` 字段读取，而非依赖 checkpoint

  **问题 2 -- 三处默认值 150 -> 500**

  - `ReflectionConfig`、`SimulationConfig`、`ExperimentConfig` 的 `reflection_token_limit` 全部从 150 提升到 500
  - 为 DeepSeek V4 的思考过程留出足够空间

  **问题 3 -- prompt 模板重写**

  - 删除 `"Do something[action]: ..."` 模板示例
  - 指令中明确禁止泛化回复

  **问题 4 -- 反思冷却机制**

  - `ReflectionConfig` 新增 `min_cooldown_steps=6`（即 1 小时内最多触发一次）
  - `should_reflect` 新增冷却时间检查
  - 累计 importance 计算中排除 `event_type == "reflection"` 的条目，打破正反馈循环
  - `_run_reflection` 执行后记录 step 到 `_last_reflection_step`

  **问题 5 -- 行为递进感**（经一轮讨论后调整）

  - Agent 新增 `recent_actions: list[str]` 属性，每轮执行后追加
  - prompt 中注入最近 5 条动作历史
  - 初始方案：禁止重复动作
  - 用户反馈：有些活动（走路、对话）不可能 10 分钟完成
  - 最终方案：允许跨 round 持续活动，但要求每轮描述具体的下一步新细节，禁止逐字复制和泛化总结

  ### 三、调整过程

  用户指出只看上一步动作不够，在一个小时的计划下仍可能循环。改为展示最近 5 条动作。随后用户进一步指出有些事情不是 10 分钟能做完的，不能一刀切禁止重复。最终把约束从"禁止重复"改为"允许延续但要求递进"：

  > Some activities span multiple rounds (e.g. walking somewhere, having a conversation) -- that is fine, but each round must describe a concrete next step with new detail, not copy a previous action verbatim.

  ### 四、修改文件清单

  | 文件                                                         | 改动                                |
  | ------------------------------------------------------------ | ----------------------------------- |
  | [storage.py](app://localhost/epitaxy/src/socialsimullm/experiment/storage.py) | 扁平布局支持 + meta.json 读取 steps |
  | [reflection.py](app://localhost/epitaxy/src/socialsimullm/agents/reflection.py) | 冷却机制 + reflection 排除          |
  | [template_agents.py](app://localhost/epitaxy/src/socialsimullm/prompt_templates/template_agents.py) | action prompt 重写                  |
  | [agent.py](app://localhost/epitaxy/src/socialsimullm/agents/agent.py) | `recent_actions` 列表 + 传入 prompt |
  | [core.py](app://localhost/epitaxy/src/socialsimullm/simulator/core.py) | 传递 step + 记录冷却                |
  | [config.py](app://localhost/epitaxy/src/socialsimullm/utils/config.py) | token limit 150->500                |
  | [experiment/config.py](app://localhost/epitaxy/src/socialsimullm/experiment/config.py) | token limit 150->500                |