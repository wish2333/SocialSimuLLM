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
