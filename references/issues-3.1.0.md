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

# 扩展功能

让我查看一下项目文档和代码，来了解扩展功能。

以下是 SocialSimuLLM 的拓展功能总览：

## 核心拓展功能

| 功能                            | 作用                                     | 激活阶段          |
| ------------------------------- | ---------------------------------------- | ----------------- |
| **空间感知系统 (FOV)**          | 基于图距离感知附近智能体，支持跨地点社交 | 每小时规划/行动时 |
| **智能路径规划 (Path Planner)** | LLM推理移动意图 + A*最短路径，多跳移动   | 移动决策时        |
| **目标驱动规划 (Goal-Driven)**  | 分层目标管理，递归任务分解，长期行为指导 | 每日计划时        |
| **对话系统**                    | 嵌入行动的社交对话，双向记忆             | 行动执行时        |

## 仿真前拓展

| 功能                   | 作用                                       |
| ---------------------- | ------------------------------------------ |
| **空间世界生成器**     | 支持环形/小世界/网格/随机/无标度等拓扑结构 |
| **自然语言场景生成器** | 用自然语言描述生成城镇数据，简化实验配置   |

## 仿真后分析

| 功能                 | 作用                                   |
| -------------------- | -------------------------------------- |
| **回放系统**         | 时间轴位置回放，可视化移动和交互       |
| **热力图**           | 地点占用频率、活动模式、转换统计       |
| **研究助手**         | 自动实验总结、模式识别、假设生成       |
| **Jupyter 分析模板** | 行为分析/空间分析/实验比较的标准化流程 |

## 仿真阶段集成流程

```
初始化: 空间拓扑 + 路径规划器 + 目标管理器
    |
每日计划: 目标管理器更新目标 -> 反思系统参考历史目标
    |
每小时规划: FOV感知周围智能体 -> 路径规划器生成移动计划
    |
行动执行: 路径规划器执行移动 -> 对话系统处理社交
    |
反思阶段: 目标完成度评估 -> 行为模式分析
```

这些功能都通过配置文件按需启用（`fov_enabled`、`path_planner_enabled`、`goal_enabled` 等），不启用时保持传统行为，互不干扰。

# 测试

## 诊断报告与解决方案

### BUG-1: DeepSeek V4 思考token耗尽输出预算（严重）

**现象**: 测试运行 `runs/exp_a58c0b42` 中约 **80% 的 LLM 调用返回空值**，agent 行为完全瘫痪（全部 idle / fallback 行为）。

**根因**: DeepSeek V4 的思考链 token 计入 `max_tokens` 预算。短输出调用（如 `rate_locations` 仅 5 tokens、`hourly_planning` 仅 45 tokens）的预算被思考过程完全消耗，导致实际输出为空。

**影响范围**: 全部 15 个模拟 LLM 调用点。

**解决方案**: 使用 DeepSeek JSON Output 模式（`response_format={"type": "json_object"}`），强制模型返回可解析的 JSON，不受思考 token 消耗影响。

### BUG-2: `rate_locations()` 重试循环无效（中等）

**现象**: `agent.py` 中 `rate_locations()` 方法存在死循环重试——对同一个字符串反复调用 `get_rating(res)`，永远得到相同结果。

**根因**: 原代码在解析失败时用同一个 `res` 字符串重试，不会产生不同结果。

**解决方案**: 移除手动重试循环，统一由 `GPT_request_json()` 内部的 3 次重试策略处理。

---

### 实施方案: `GPT_request_json()` + 3 次重试

**重试策略**:
```
Attempt 1: JSON 模式 (response_format=json_object)
    |
    +-- 解析失败? --> Attempt 2: JSON 模式重试
    |                   |
    |                   +-- 解析失败? --> Attempt 3: 纯文本模式 (无 response_format)
    |                                       |
    |                                       +-- 返回空? --> 写入预设 fallback
    |                                       +-- 非空? --> 尝试 json.loads(), 失败则写 raw text
    +-- 成功 --> 返回解析后的 dict
```

**max_tokens 预算调整**（为思考 token 留出空间）:

| 调用 | 原值 | 新值 |
|------|------|------|
| daily_planning | 300 | 800 |
| hourly_planning | 45 | 300 |
| execute_action | 80 | 300 |
| form_impression | 80 | 300 |
| rate_locations/experience | 5 | 300 |
| simplify_action | 30 | 200 |
| reflect_daily | 150 | 400 |
| reflect_pattern/social | 60 | 300 |

**15 个预设 fallback 值**（所有重试失败时注入，保证模拟不中断）:

| 调用 | Key | 预设值 |
|------|-----|--------|
| daily_planning | plan | `[8:00 - Wake up...\n20:00 - Go to bed.]` |
| hourly_planning | plan | `Continue with current activity.` |
| execute_action | action | `Idle[action]: Observing surroundings.[details]` |
| form_impression | impression | `Neutral, observing.` |
| rate_locations | rating | `5` |
| rate_experience | rating | `5` |
| simplify_action | summary | `{agent_name} did something.` |
| reflect_daily | reflection | `Nothing notable happened.` |
| reflect_pattern | reflection | `No clear pattern identified.` |
| reflect_social | reflection | `No social observations yet.` |
| initialize_goals | text | `5: Explore the surroundings` |
| review_and_update_goals | text | `CONTINUE` |
| decompose_goal | text | `5: Take first step toward ...` |
| order_by_dependency | text | 每个目标的 `[id] description` |
| infer_movement_intent | destination | `STAY` |

**回滚机制**: `--no-json-mode` CLI 参数关闭 JSON 模式，退回原有行为。

**未受影响的模块**: `experiment/assistant.py` 和 `experiment/scenario.py` 继续使用 `GPT_request()`（纯文本），完全不受影响。

## 本次会话完整问题诊断与修复记录

### 一、Smoke Test 自查发现的问题

| # | 问题 | 严重度 | 根因 |
|---|------|--------|------|
| 1 | `list` 命令输出 0 steps / 0 events / status=running | P0 | `list_experiments` 只扫描 `runs/{project}/{exp_id}/` 两级结构，`project=''` 时目录为扁平 `runs/{exp_id}/`，扫描器跳过；Steps 列依赖 checkpoint 而非 meta.json |
| 2 | error.log 记录 23 次 "all 3 attempts failed" | P0 | `reflection_token_limit=150`，DeepSeek V4 的思考 token 耗尽预算，JSON 输出空间为零 |
| 3 | Agent 输出 "Do something" 泛化回复 | P1 | prompt 模板中 `"Do something[action]: ..."` 被当作示例模板，模型学会了这种写法 |
| 4 | 反思每轮刷 2-3 条，内容高度重复 | P1 | 无冷却机制 + 反思产物计入 importance 形成正反馈循环 |
| 5 | 行为缺乏递进感，同一动作反复出现 | 提升 | agent 不知道自己上一步做了什么，每轮独立生成动作 |
| 6 | notebook 无法读取实验文件 | P0 | `data_loader.py` 用 `Path("runs")` 相对路径，notebook 工作目录为 `notebooks/`，解析到错误位置；`rglob` 模式无法匹配扁平目录结构 |

### 二、修复方案

**问题 1 -- storage.py**
- 新增 `_is_experiment_dir()` 判断目录是否为实验目录
- `list_experiments` 同时扫描扁平和嵌套两种布局，用 `seen` 集合去重
- Steps 优先从 `meta.json` 的 `round` 字段读取

**问题 2 -- 三处默认值**
- `ReflectionConfig`、`SimulationConfig`、`ExperimentConfig` 的 `reflection_token_limit` 从 150 提升到 500

**问题 3 + 5 -- template_agents.py + agent.py**
- 删除 `"Do something[action]: ..."` 模板示例
- Agent 新增 `recent_actions: list[str]`，每轮追加
- prompt 注入最近 5 条动作历史
- 初始指令："禁止重复" -> 经用户反馈后改为："允许跨 round 持续活动（走路、对话等），但每轮必须描述具体下一步新细节，禁止逐字复制"

**问题 4 -- reflection.py + core.py**
- `ReflectionConfig` 新增 `min_cooldown_steps=6`（1 小时最多触发一次）
- `should_reflect` 增加冷却时间检查
- 累计 importance 排除 `event_type=="reflection"` 的条目
- `_run_reflection` 执行后记录 step 到 `_last_reflection_step`

**问题 6 -- notebooks/data_loader.py**
- 用 `Path(__file__).resolve().parent.parent / "runs"` 推导项目根目录，不依赖工作目录
- 先检查 `runs_root / experiment_id`（扁平布局），再用 `rglob` 搜索嵌套布局

### 三、修改文件清单

| 文件 | 改动摘要 |
|------|----------|
| `src/socialsimullm/experiment/storage.py` | 扁平布局支持 + meta.json 读取 steps |
| `src/socialsimullm/agents/reflection.py` | 冷却机制 + reflection 排除 |
| `src/socialsimullm/prompt_templates/template_agents.py` | action prompt 重写 |
| `src/socialsimullm/agents/agent.py` | `recent_actions` 列表 + 传入 prompt |
| `src/socialsimullm/simulator/core.py` | 传递 step + 记录冷却 |
| `src/socialsimullm/utils/config.py` | token limit 150->500 |
| `src/socialsimullm/experiment/config.py` | token limit 150->500 |
| `notebooks/data_loader.py` | 路径解析修复 |

## Smoke Test 发现的问题与解决方案

### 问题：无 checkpoint 生成

**现象**：smoke test 运行完毕后，`runs/` 目录下没有 `checkpoints/` 文件夹。

**原因**：[smoke_test.yaml:10](examples/smoke_test.yaml#L10) 中设置了 `checkpoint_interval: 0`，即关闭 checkpoint 保存。

**触发逻辑**：[core.py:257](src/socialsimullm/simulator/core.py#L257) — 只有当 `checkpoint_interval > 0` 且当前步数是其整数倍时才保存：

```python
if self.config.checkpoint_interval > 0 and s.round % self.config.checkpoint_interval == 0:
    logger.save_checkpoint(s, s.round)
```

**解决方案**：按需修改 `checkpoint_interval` 值：

| 值 | 行为 | 适用场景 |
|----|------|---------|
| `0` | 不保存 | smoke test、快速验证 |
| `1` | 每步保存 | 调试、精细分析 |
| `5` | 每 5 步保存 | 一般实验 |
| `10` | 每 10 步保存（默认） | 标准实验 |

注意：smoke test 中设为 `0` 是**正确的设计**，它只需要验证代码管线能跑通，不需要保存中间状态。如果你需要 checkpoint 来测试 Replay/Heatmap 功能，用 `minimal.yaml` 或修改 smoke test 配置即可。

## 本次会话发现的问题与修复总结

---

### 问题 1：非 DeepSeek 模型计划为空（全员 fallback）

**现象**：非 DeepSeek 模型运行时，所有智能体的每日计划都是 `[8:00 - Wake up and start the day. 20:00 - Go to bed.]`，完全相同。

**根因**：`GPT_request_json` 中非 DeepSeek 路径的 fallback 逻辑有 bug。`_make_fallback` 在 `fallback` 参数不为 None 时直接返回硬编码的 fallback dict，**丢弃了模型实际返回的文本**。

**修复**（[text_generation.py](src/socialsimullm/utils/text_generation.py)）：
- JSON 解析失败时，将模型原始文本包装为 `{key: raw_text}` 而非丢弃
- 新增 markdown 代码围栏（` ```json...``` `）预处理，兼容部分模型返回带围栏的 JSON

---

### 问题 2：智能体无法感知周围人的行动

**现象**：智能体做行动决策时，完全不知道同地点其他人在做什么，无法产生自然互动。

**根因**：
- `execute_action` 的 `nearby_situations` 参数名有误导性，实际传入的是**自身记忆**而非周围情况
- 同一轮内顺序执行的智能体之间不可见
- prompt 模板没有展示其他智能体行为的字段

**修复**（3 个文件）：
- `core.py` — 新增 `_format_nearby_agents()` 收集同地点其他智能体的最近行动
- `agent.py` — `execute_action` 新增 `nearby_agents_info` 参数注入 prompt
- `template_agents.py` — prompt 新增占位符展示周围人动态

---

### 问题 3：智能体之间无法产生对话交互

**现象**：智能体只做自己的事，彼此之间无法聊天、回应或社交互动。

**根因**：整个提示词系统和数据流都没有设计对话机制——prompt 不鼓励对话，数据结构不存储对话，记忆系统不追踪对话。

**修复**（4 个文件）：
- `template_agents.py` — 新增 `JSON_ACTION_DIALOGUE_SUFFIX`，要求模型输出 `action` + `dialogue_target` + `dialogue` 三字段；prompt 鼓励自然社交
- `agent.py` — 新增 `dialogue_target`/`dialogue_content` 属性，`memory_dialogue()` 方法；`execute_action` 提取对话字段
- `core.py` — `_format_nearby_agents` 高亮显示对当前智能体说的对话；`_execute_actions` 将对话**双向存入记忆**（双方都能回忆）
- 设计原则：对话嵌入行动，不消耗额外轮次，边做事边聊天

---

### 问题 4：全局事件没有时效性

**现象**：事件一旦添加就永远生效，无法模拟"集市今天开放""商队经过 2 天后离开"等有时限的事件。且事件只在初始化时加载一次，运行期间不刷新。

**根因**：事件数据结构没有时间范围字段，`agent.event` 只在 `init_memory` 时设置一次。

**修复**（4 个文件）：
- `global_methods.py` — 新增 `parse_sim_time()` 和 `is_time_in_range()` 时间比较工具
- `memory.py` — 新增 `load_active_events(global_time)` 方法，按时间范围过滤活跃事件
- `core.py` — `_load_events` 支持解析时间范围格式 `"事件 | Day 1, 08:00 - Day 3, 20:00"`；新增 `_refresh_events()` 每步刷新；`step()` 中调用刷新
- `template_agents.py` — prompt 文案从 "very popular things recently" 改为 "current events happening around you"

向后兼容：不带时间范围的事件视为永久有效。

---

### 改动文件清单

| 文件 | 改动类型 |
|------|---------|
| `utils/text_generation.py` | Bug fix — fallback 逻辑修复 |
| `utils/global_methods.py` | Feature — 时间解析工具 |
| `agents/memory_entry.py` | 无变更（metadata 字段已存在） |
| `agents/memory.py` | Feature — 活跃事件过滤 |
| `agents/agent.py` | Feature — 对话属性 + 记忆方法 |
| `prompt_templates/template_agents.py` | Feature — 对话 prompt + 事件描述优化 |
| `simulator/core.py` | Feature — 周围人感知 + 对话存储 + 事件刷新 |

# 待定功能方向

- 记忆系统是否可以参考claude
- 更合理的时间配置
- 合理的多线程（不同空间内的异步运行？）
- 随机的行动顺序