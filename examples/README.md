# SocialSimuLLM v3.1.0 Examples & Testing Guide

Examples, configurations, and step-by-step instructions for testing and using SocialSimuLLM v3.1.0.

## Quick Start

```bash
# 1. Set API credentials
export OPENAI_API_KEY="your-key"
export OPENAI_BASE_URL="http://your-server/v1"

# 2. Run the minimal example (1-day simulation, 144 steps)
uv run socialsimullm run --config examples/minimal.yaml

# 3. View results
uv run streamlit run src/socialsimullm/frontend/app.py
```

---

## File Index

| File | Category | Description |
|------|----------|-------------|
| `minimal.yaml` | Basic | Minimal config, 1-day run, all defaults |
| `full_config.yaml` | Reference | All v3.1.0 parameters documented |
| `batch_example.yaml` | Methodology | Multi-seed comparison |
| `custom_town.yaml` | Basic | Custom world (Chinese setting) |
| `town_data_custom.json` | Data | Custom town data file |
| `with_events.yaml` | Methodology | Global event injection |
| `spatial_variants.yaml` | Phase 3 | Spatial topology comparison |
| `cognitive_enhanced.yaml` | Phase 3 | Goal-driven planning + reflection |
| `nl_scenario.yaml` | Phase 3 | NL scenario generation (Python only) |
| `python_runner.py` | API | Programmatic access to all features |
| `ab_test_reflection.yaml` | A/B Test | Reflection on/off comparison |
| `ab_test_fov.yaml` | A/B Test | Basic FOV on/off comparison |
| `ab_test_fov_extended.yaml` | A/B Test | FOV with weighted graph |
| `ab_test_path_planner.yaml` | A/B Test | A* vs legacy movement |
| `ab_test_goal.yaml` | A/B Test | Goal planning on/off |
| `ab_test_spatial.yaml` | A/B Test | Ring vs small_world |

---

## Feature Overview (v3.1.0)

### Phase 1: Core Simulation (always active)

The simulation engine runs a step-based loop (each step = 10 sim-minutes):

1. **Daily Planning** (once/day) - Agents generate their day plan
2. **Hourly Planning** (once/hour) - Agents refine immediate actions
3. **Action Execution** (every step) - Agents act on their plans
4. **Movement** (once/hour) - Agents move between locations
5. **Impression Formation** (once/hour) - Agents form observations
6. **Memory Store** - All events stored as MemoryEntry with embeddings

### Phase 2: Experiment Infrastructure

| Feature | Config Field | What It Does |
|---------|-------------|--------------|
| Reproducible runs | `experiment_id`, `random_seed` | Same seed = same behavior |
| YAML configs | `--config file.yaml` | Declarative experiment setup |
| Batch execution | `batch --seeds 42,43,44` | Multiple runs, different seeds |
| Checkpointing | `checkpoint_interval` | Periodic state snapshots |
| Result analysis | `load_results()`, Streamlit | Load/visualize experiment data |
| Memory weights | `memory_config` | Tune recency/similarity/importance |

### Phase 3: Extended Exploration

| Feature | Config Field | What It Does |
|---------|-------------|--------------|
| Spatial graph generation | `spatial_config` | Generate world topologies algorithmically |
| Field of View | `fov_enabled` | Agents perceive nearby agents |
| A* Pathfinding | `path_planner_enabled` | LLM intent + shortest path movement |
| Goal planning | `goal_enabled` | Hierarchical goal decomposition |
| NL scenario | `ScenarioGenerator` | Create worlds from text descriptions |
| Research assistant | Streamlit tab | LLM-powered experiment analysis |

---

## Testing Guide

### Test 1: Basic Run (no extra features)

**Purpose**: Verify the core simulation loop works.

```bash
uv run socialsimullm run --config examples/minimal.yaml
```

**Expected**: Creates `runs/minimal_demo/<id>/` with events.jsonl, checkpoints/, done.flag.

**Verify**:
```bash
uv run socialsimullm list
```

### Test 2: Full Configuration

**Purpose**: Verify all config fields are parsed correctly.

```bash
uv run socialsimullm run --config examples/full_config.yaml
```

**Expected**: Run completes with spatial_config, FOV, path planner, and goals enabled.

### Test 3: Batch Seed Comparison

**Purpose**: Verify reproducibility and batch infrastructure.

```bash
uv run socialsimullm batch --config examples/batch_example.yaml --seeds 42,43,44
```

**Expected**: 3 directories under `runs/batch_demo/`, each with done.flag.

**Analyze**: Open Streamlit -> View Results -> compare the runs.

### Test 4: Custom World

**Purpose**: Verify custom town_data.json loading.

```bash
uv run socialsimullm run --config examples/custom_town.yaml
```

**Expected**: Agents use Chinese-named locations and characters from `town_data_custom.json`.

### Test 5: Global Events

**Purpose**: Verify event injection affects agent behavior.

```bash
uv run socialsimullm run --config examples/with_events.yaml
```

**Expected**: Events appear in agent daily plans and reflections.

### Test 6: Spatial Topology Comparison (Phase 3)

**Purpose**: Compare how graph topology affects movement and interactions.

```bash
# Run each topology variant
uv run socialsimullm run --config examples/spatial_variants.yaml --id exp_ring
# Edit spatial_variants.yaml: change topology to "small_world", re-run with --id exp_sw
# Repeat for "grid", "random", "scale_free"
```

**Analyze**:
- Open Streamlit -> View Results -> Heatmaps tab
- Compare location transition heatmaps across topologies
- Use `02_spatial_analysis.ipynb` for detailed transition matrices

### Test 7: Goal-Driven Planning (Phase 3)

**Purpose**: Verify hierarchical goal decomposition and daily review.

```bash
uv run socialsimullm run --config examples/cognitive_enhanced.yaml
```

**Expected**:
- `goal_review` events appear in events.jsonl
- Daily plans reference active goals
- Reflections include goal progress

**Verify**: Check events.jsonl for `"event_type": "goal_review"` entries.

### Test 8: NL Scenario Generation (Phase 3)

**Purpose**: Create a world from natural language and run it.

```bash
uv run python examples/python_runner.py --demo scenario
```

**Expected**: Generates `examples/generated_town.json` with locations and characters.

### Test 9: Research Assistant (Phase 3)

**Purpose**: LLM-powered experiment analysis.

**Prerequisite**: Complete at least one experiment (Test 1-7).

1. Open Streamlit: `uv run streamlit run src/socialsimullm/frontend/app.py`
2. Go to **Research Assistant** tab
3. Select a completed experiment
4. Click "Generate Summary" / "Identify Patterns" / "Generate Report"

### Test 10: Jupyter Analysis Notebooks

**Prerequisite**: Complete at least one experiment.

```bash
cd notebooks
# Open in Jupyter: jupyter notebook
# Start with 00_quick_start.ipynb, then 01/02/03
```

### Test 11: Replay & Heatmaps (Phase 3)

**Prerequisite**: An experiment with checkpoint_interval > 0.

1. Open Streamlit -> View Results
2. Select an experiment
3. **Replay** tab: use the slider to step through checkpoints
4. **Heatmaps** tab: view location occupancy, agent activity, transitions

---

## Python API Reference

All examples are in `examples/python_runner.py`.

```python
from socialsimullm.experiment.config import ExperimentConfig
from socialsimullm.experiment.runner import ExperimentRunner
from socialsimullm.experiment.assistant import ResearchAssistant
from socialsimullm.experiment.scenario import ScenarioGenerator
from socialsimullm.cognition.goal import GoalManager, RecursiveTaskDecomposer
```

### Running Experiments Programmatically

```bash
# Single run
uv run python examples/python_runner.py --run single

# Batch (3 seeds)
uv run python examples/python_runner.py --run batch

# Spatial topology comparison (5 topologies)
uv run python examples/python_runner.py --run spatial

# Goal-driven planning
uv run python examples/python_runner.py --run cognitive
```

### Generating Worlds from Text

```bash
uv run python examples/python_runner.py --run scenario
```

```python
from socialsimullm.experiment.scenario import ScenarioGenerator

gen = ScenarioGenerator()
town_data = gen.generate(
    "A harbor town with a fish market, tavern, shipyard, and town hall. "
    "5 characters: fisherman, tavern keeper, shipbuilder, merchant, mayor."
)
gen.save(town_data, "my_world/town_data.json")
```

### Analyzing Results

```bash
uv run python examples/python_runner.py --run assistant
```

```python
from socialsimullm.experiment.assistant import ResearchAssistant

assistant = ResearchAssistant()
summary = assistant.summarize_experiment("exp_abc123")
patterns = assistant.identify_patterns("exp_abc123")
hypotheses = assistant.suggest_hypotheses("exp_abc123")
report = assistant.generate_report("exp_abc123")
```

---

## A/B Testing: Feature Validation

Each Phase 3 feature is independently toggleable. The `ab_test_*.yaml` configs provide ready-to-run A/B pairs where the **control** (A) uses the legacy implementation and the **treatment** (B) enables the new feature. Every pair shares the same `random_seed` and `simulation_steps` so the only variable is the feature under test.

### Feature Independence Matrix

| Feature | Toggle Field | Default | Independent? |
|---------|-------------|---------|-------------|
| Reflection | `reflection_enabled` | true | Yes - no dependency on other features |
| Spatial Generation | `spatial_config` | null (off) | Yes - fallback to legacy ring |
| Field of View | `fov_enabled` | false | Yes - no dependency |
| Path Planner | `path_planner_enabled` | false | Yes - no dependency |
| Goal Planning | `goal_enabled` | false | Yes - no dependency (but synergizes with reflection) |

### Available A/B Pairs

| Config | A (Control) | B (Treatment) | Key Metric |
|--------|-------------|---------------|------------|
| `ab_test_reflection.yaml` | reflection off | reflection on | Plan consistency, action diversity |
| `ab_test_fov.yaml` | fov off | fov on | Interaction count |
| `ab_test_fov_extended.yaml` | fov off | fov on + weighted graph | Cross-location interactions |
| `ab_test_path_planner.yaml` | rate_locations | A* pathfinding | Movement diversity |
| `ab_test_goal.yaml` | goals off | goals on | Plan consistency, goal review count |
| `ab_test_spatial.yaml` | ring topology | small_world | Transition entropy |

### How to Run an A/B Test

Each A/B config has a single toggle field. Run the control first, flip the toggle, then run the treatment:

```bash
# Step 1: Run control (A)
uv run socialsimullm run --config examples/ab_test_reflection.yaml --id ab_reflect_off

# Step 2: Edit ab_test_reflection.yaml: change reflection_enabled to true

# Step 3: Run treatment (B) with same seed
uv run socialsimullm run --config examples/ab_test_reflection.yaml --id ab_reflect_on
```

### Automated Analysis

After running both groups, use the A/B analysis notebook:

```bash
cd notebooks
# Open 04_ab_analysis.ipynb in Jupyter
# Update experiment IDs in the ab_pairs dict if needed
# Run all cells to get automated comparison
```

The notebook computes 7 metrics per pair and produces a verdict:

| Metric | What It Measures | Interpretation |
|--------|-----------------|----------------|
| Action Diversity | Unique actions / total actions | Higher = more varied behavior |
| Interaction Count | Agent-to-agent mentions | Higher = more social awareness |
| Movement Diversity | Unique destinations / total moves | Higher = more exploration |
| Reflection Count | Number of reflection events | Verifies reflection is active |
| Daily Plan Consistency | Jaccard similarity across days | Higher = more persistent focus |
| Transition Entropy | Shannon entropy of moves | Higher = more spread movement |
| Goal Review Count | Number of goal review events | Verifies goal system is active |

### Statistical Rigor

For publication-quality results, combine A/B tests with batch seeds:

```bash
# Run 3 seeds per condition
uv run socialsimullm batch --config examples/ab_test_goal.yaml --seeds 42,43,44
# Flip goal_enabled, rename project, run again
```

This controls for LLM variance and provides confidence intervals.

---

## Config Field Reference

### Core Parameters

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `experiment_id` | str | auto (UUID) | Unique run identifier |
| `project` | str | = experiment_id | Grouping name under runs/ |
| `model` | str | gpt-4o-mini | LLM completion model |
| `embedding_model` | str | BAAI/bge-m3 | Embedding model for memory |
| `simulation_steps` | int | 144 | Steps to run (144 = 1 day) |
| `memory_limit` | int | 10 | Recent memories to consider |
| `random_seed` | int | 42 | Reproducibility seed (0=random) |
| `checkpoint_interval` | int | 10 | Steps between snapshots (0=off) |

### Reflection (Phase 2)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `reflection_enabled` | bool | true | Enable reflection system |
| `reflection_importance_threshold` | int | 15 | Cumulative importance trigger |
| `reflection_include_in_planning` | bool | true | Inject reflections into daily plans |

### Memory Retrieval

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `memory_config.recency_weight` | float | 0.3 | Weight for time-based scoring |
| `memory_config.similarity_weight` | float | 0.5 | Weight for semantic similarity |
| `memory_config.importance_weight` | float | 0.2 | Weight for importance rating |

### Spatial Graph (Phase 3)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `spatial_config.topology` | str | ring | ring / small_world / grid / random / scale_free |
| `spatial_config.num_locations` | int | 4 | Number of location nodes |
| `spatial_config.edge_weight_min` | float | 1.0 | Min edge weight (distance) |
| `spatial_config.edge_weight_max` | float | 1.0 | Max edge weight (distance) |

### Perception & Movement (Phase 3)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `fov_enabled` | bool | false | Proximity-based agent perception |
| `fov_distance` | float | 0.0 | Visibility distance (0=co-located only) |
| `path_planner_enabled` | bool | false | A* pathfinding (replaces rate_locations) |
| `multi_hop_movement` | bool | true | One node per step (false=teleport) |

### Goal Planning (Phase 3)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `goal_enabled` | bool | false | Hierarchical goal decomposition |
| `max_active_goals` | int | 3 | Max concurrent goals per agent |

---

## Workflow Examples

### Workflow A: Compare spatial topologies

1. Run `spatial_variants.yaml` with topology=ring, small_world, grid
2. Open Streamlit -> Heatmaps -> compare transition patterns
3. Open `03_experiment_comparison.ipynb` for quantitative comparison
4. Use Research Assistant -> Compare mode

### Workflow B: Study goal impact on behavior

1. Run `minimal.yaml` (no goals) and `cognitive_enhanced.yaml` (with goals)
2. Open Streamlit -> Event Summary for each run
3. Compare daily plan consistency and action diversity
4. Generate research reports for both runs

### Workflow C: Custom world + scenario generation

1. Write a scenario description
2. `python_runner.py --run scenario` to generate town_data.json
3. `python_runner.py --run single` to run with generated world
4. Refine: use `ScenarioGenerator.refine()` to improve the world
5. Analyze results in notebooks

### Workflow D: Reproducible research

1. Set `random_seed` in config
2. Run batch with 3+ seeds
3. Analyze variance in `01_behavioral_analysis.ipynb`
4. Generate hypotheses with Research Assistant
5. Design follow-up experiments to test hypotheses
