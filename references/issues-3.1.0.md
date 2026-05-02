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

# Phase 2 Implementation Plan: Experiment Infrastructure + Frontend

## Context

Phase 1 is complete -- the monolithic `__main__.py` has been split into modular components, the Agent class has been refactored, memory is unified, reflection is implemented, and structured logging with checkpoints works. Phase 2 transforms SocialSimuLLM from a single-run interactive tool into a reproducible experiment platform with batch execution, result analysis, and a Streamlit web UI.

**User decisions**: Implement all Phase 2 features (F-201 through F-204), config-supplied events for batch mode, output path `runs/{project}/{experiment_id}/`.

---

## Architecture

```
src/socialsimullm/
  __main__.py                  # MODIFIED: subcommand dispatch (run/batch/list + legacy)
  experiment/                  # NEW PACKAGE
    __init__.py
    config.py                  # F-201: ExperimentConfig (Pydantic)
    runner.py                  # F-202: ExperimentRunner
    storage.py                 # F-203: run directory + checkpoint helpers
    analysis.py                # F-203: result loading + DataFrame export
  frontend/                    # NEW PACKAGE (Streamlit, optional deps)
    __init__.py
    app.py                     # F-204: main entry
    pages/
      configure.py             # F-204: experiment config form
      results.py               # F-204: result visualization
    components/
      forms.py                 # F-204: pydantic-to-streamlit mapping
      viz.py                   # F-204: pyvis + plotly rendering
    utils.py                   # F-204: subprocess launch, polling
  simulator/
    core.py                    # MODIFIED: +initial_event param, absolute path support
    state.py                   # UNCHANGED
    events.py                  # UNCHANGED
  utils/
    config.py                  # MODIFIED: +load_experiment_config() for subcommands
    logger.py                  # UNCHANGED (writes to self.output_dir, no changes needed)
    ...
```

**Key design**: ExperimentConfig (Pydantic) wraps SimulationConfig (dataclass). `ExperimentConfig.to_simulation_config()` produces a `SimulationConfig` for `SimulatorCore`. API keys come from env vars, not from ExperimentConfig. The two configs never overlap -- `SimulatorCore` only ever sees `SimulationConfig`.

---

## Sprint 1: ExperimentConfig + Storage Foundation

### Files to create

**`src/socialsimullm/experiment/__init__.py`** (~20 lines)
- Public exports: ExperimentConfig, MemoryConfig, ExperimentRunner, load_results, list_experiments

**`src/socialsimullm/experiment/config.py`** (~200 lines)
- `MemoryConfig(BaseModel)`: recency/similarity/importance weights (0-1 floats), importance_threshold (1-9)
- `ExperimentConfig(BaseModel)`: experiment_id (auto UUID), project, model, embedding_model, simulation_steps, memory_limit, random_seed, checkpoint_interval, spatial_graph_path, events (list[str]), budget_limit, memory_config, reflection settings, prompt_meta
- `to_simulation_config() -> SimulationConfig`: field mapping (model->completion_model, simulation_steps->max_steps, etc.)
- `to_yaml(path)` / `from_yaml(path)`: serialization via pydantic + pyyaml
- `get_event_string() -> str`: join events list, default "No new event."
- API keys NOT stored here -- resolved from env vars by `_apply_config_to_globals()`

**`src/socialsimullm/experiment/storage.py`** (~200 lines)
- `get_runs_root() -> Path`: `Path(os.getcwd()) / "runs"`
- `create_run_dir(project, experiment_id) -> Path`: `runs/{project}/{experiment_id}/` with agent_data/ subdir
- `is_complete(run_dir) -> bool`: checks done.flag
- `list_experiments(project=None) -> list[dict]`: scans runs/ tree, returns status/config info
- `load_checkpoint(experiment_id, step=None, project=None) -> dict`: loads spatial_graph.json, agent_states.json, memory_summary.json, meta.json
- `find_run_dir(experiment_id, project=None) -> Path`: locate run directory
- `get_latest_checkpoint_step(run_dir) -> int | None`

### Files to modify

**`pyproject.toml`** (+2 lines): add `pydantic>=2.0`, `pyyaml` to core dependencies

---

## Sprint 2: ExperimentRunner + SimulatorCore Tweaks

### Files to modify

**`src/socialsimullm/simulator/core.py`** (+10 lines net)
- `__init__()`: add `initial_event: str | None = None` parameter, store as `self._initial_event`
- `__init__()`: path resolution -- if `config.project_name` is absolute, use directly; otherwise prepend `os.path.join(os.getcwd(), "projects", ...)` (backward compat)
- `initialize()` line 112: pass `new_event=self._initial_event` to `_load_events()`
- No changes to `_load_events()` -- it already handles the `new_event` parameter

**`src/socialsimullm/utils/config.py`** (+60 lines)
- Add `load_experiment_config(argv=None) -> tuple[str | None, Any]`: subcommand parser for `run`, `batch`, `list`. Returns `(None, None)` for legacy mode (backward compat). Detection: check if first arg is a known subcommand.

### Files to create

**`src/socialsimullm/experiment/runner.py`** (~250 lines)
- `ExperimentRunner.run_single(config) -> experiment_id`:
  1. Set random seed if > 0
  2. Create run dir via `create_run_dir()`
  3. Copy town_data.json to run dir
  4. Save config.yaml snapshot
  5. Build SimulationConfig via `config.to_simulation_config()`, set project_name to full run dir path
  6. Call `_apply_config_to_globals()` and `validate_config()`
  7. Create `SimulatorCore(sim_config, initial_event=config.get_event_string())`, call `.initialize().run()`
  8. Return experiment_id
- `ExperimentRunner.run_batch(config, seeds) -> list[str]`: loop over seeds, create per-seed config copies via `model_copy(update={...})`
- `_prepare_project_data(config, run_dir)`: copy town_data_template.json if no spatial_graph_path

**`src/socialsimullm/experiment/analysis.py`** (~150 lines)
- `load_results(experiment_id, project=None) -> list[dict]`: streaming JSONL reader
- `load_results_dataframe(experiment_id, ...) -> pd.DataFrame`: lazy import pandas
- `get_experiment_summary(experiment_id, ...) -> dict`: quick stats
- `compare_experiments(experiment_ids, ...) -> pd.DataFrame`: cross-run comparison

**`src/socialsimullm/__main__.py`** (~50 lines, from 27)
- Try `load_experiment_config()` first
- If command is `run`: load YAML config, call `ExperimentRunner.run_single()`
- If command is `batch`: load YAML config, parse seeds, call `ExperimentRunner.run_batch()`
- If command is `list`: call `list_experiments()`, print table
- If command is None: fall through to existing `load_config()` + `SimulatorCore` path (unchanged)

---

## Sprint 3: Analysis Polish + CLI Complete

### Files to modify

**`src/socialsimullm/experiment/storage.py`**: complete `load_checkpoint()` and `list_experiments()` with full metadata
**`src/socialsimullm/experiment/analysis.py`**: add `compare_experiments()` cross-run metrics
**`.gitignore`**: add `runs/`, `*.flag`

### Verification
- `socialsimullm run --config config.yaml --id test001` completes a run
- `socialsimullm batch --config config.yaml --seeds 42,43` produces 2 directories
- `socialsimullm list` shows all experiments with status
- `socialsimullm --project t7` (legacy mode) still works identically
- JSONL loadable by `pd.read_json(path, lines=True)`

---

## Sprint 4: Streamlit Frontend MVP

### Files to create

**`src/socialsimullm/frontend/app.py`** (~80 lines): tab-based layout (Configure / Results)
**`src/socialsimullm/frontend/pages/configure.py`** (~150 lines): form fields from ExperimentConfig, "Save & Run" button launches subprocess
**`src/socialsimullm/frontend/pages/results.py`** (~150 lines): experiment selector, checkpoint viewer, spatial graph + charts tabs
**`src/socialsimullm/frontend/components/forms.py`** (~100 lines): pydantic field -> streamlit widget mapping
**`src/socialsimullm/frontend/components/viz.py`** (~150 lines): pyvis spatial graph, plotly location/action charts
**`src/socialsimullm/frontend/utils.py`** (~80 lines): subprocess launch, done.flag polling

### Dependencies (optional group)
```toml
[project.optional-dependencies]
frontend = ["streamlit>=1.30", "pyvis>=0.3", "plotly>=5.0", "pandas>=2.0"]
analysis = ["pandas>=2.0", "plotly>=5.0"]
```

---

## Backward Compatibility

| Invocation                                          | Behavior                                              |
| --------------------------------------------------- | ----------------------------------------------------- |
| `socialsimullm --project t7`                        | Legacy mode, writes to `projects/t7/`                 |
| `socialsimullm --project t7 --steps 144`            | Legacy mode with steps, no `input()` for repeat count |
| `socialsimullm t7`                                  | Legacy mode (positional arg)                          |
| `socialsimullm run --config X.yaml`                 | Experiment mode, writes to `runs/{project}/{id}/`     |
| `socialsimullm batch --config X.yaml --seeds 42,43` | Batch experiment mode                                 |
| `socialsimullm list`                                | List all experiments                                  |

Detection: first CLI arg is `run`/`batch`/`list` -> experiment mode; otherwise -> legacy mode.

---

## Verification Plan

1. **Config validation**: Create minimal YAML with just `model` field, verify `ExperimentConfig.from_yaml()` works with defaults
2. **Single run**: `uv run socialsimullm run --config test.yaml --id test001`, verify `runs/{project}/test001/` contains config.yaml, events.jsonl, done.flag, checkpoints/
3. **Batch run**: `uv run socialsimullm batch --config test.yaml --seeds 42,43,44`, verify 3 experiment directories
4. **Legacy compat**: `uv run socialsimullm --project t7 --steps 10`, verify writes to `projects/t7/` as before
5. **List**: `uv run socialsimullm list`, verify shows experiments with status
6. **Analysis**: `load_results_dataframe("test001")` returns valid DataFrame
7. **Frontend**: `uv run streamlit run src/socialsimullm/frontend/app.py`, verify config form + run button + result display

---

## Critical Files Reference

| File                                                     | Role                                                   |
| -------------------------------------------------------- | ------------------------------------------------------ |
| [simulator/core.py](src/socialsimullm/simulator/core.py) | 2 touch points: initial_event param + abs path support |
| [utils/config.py](src/socialsimullm/utils/config.py)     | Add subcommand parser, keep existing `load_config()`   |
| [__main__.py](src/socialsimullm/__main__.py)             | Subcommand dispatch layer                              |
| [utils/logger.py](src/socialsimullm/utils/logger.py)     | No changes needed (reference for checkpoint format)    |
| [pyproject.toml](pyproject.toml)                         | Add pydantic, pyyaml, optional frontend deps           |
