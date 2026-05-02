# SocialSimuLLM Examples

Example configurations and scripts for running SocialSimuLLM in both legacy mode and experiment mode.

## Files

| File | Mode | Description |
|------|------|-------------|
| `minimal.yaml` | Experiment | Minimal config with defaults (1-day run) |
| `full_config.yaml` | Experiment | Full config with all parameters |
| `batch_example.yaml` | Experiment | Config for batch seed comparison |
| `custom_town.yaml` | Experiment | Config using a custom town_data.json |
| `with_events.yaml` | Experiment | Config with global events injection |
| `python_runner.py` | Both | Python API example for programmatic runs |
| `town_data_custom.json` | Experiment | Custom town data (3 agents, Chinese setting) |

## Usage

### Experiment mode (YAML config)

```bash
# Minimal: 1-day run with defaults
uv run socialsimullm run --config examples/minimal.yaml

# Full config with custom parameters
uv run socialsimullm run --config examples/full_config.yaml

# Batch: 3 runs with different seeds
uv run socialsimullm batch --config examples/batch_example.yaml --seeds 42,43,44

# Custom town data
uv run socialsimullm run --config examples/custom_town.yaml

# With global events
uv run socialsimullm run --config examples/with_events.yaml
```

### Legacy mode (CLI args)

```bash
# Quick single run (uses projects/t7 or creates new project)
uv run socialsimullm --project my_town --steps 144 --model gpt-4o-mini

# Short run for testing
uv run socialsimullm --project test --steps 10
```

### Python API

```bash
uv run python examples/python_runner.py
```

### View results

```bash
uv run socialsimullm list

# Or use the Streamlit frontend
uv run streamlit run src/socialsimullm/frontend/app.py
```
