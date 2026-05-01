# Development Guide

> Version: 3.1
> Last Updated: 2026-05-01
> Status: Active

---

## 1. Getting Started

### 1.1 Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11+ | Check with `python --version` |
| uv | Latest | [Installation guide](https://docs.astral.sh/uv/) |
| Git | Latest | For version control |

### 1.2 Initial Setup

```bash
# Clone the repository
git clone https://github.com/wish2333/SocialSimuLLM.git
cd SocialSimuLLM

# Install dependencies using uv
uv sync

# Verify installation
uv run python -c "import socialsimullm; print('OK')"
```

### 1.3 LLM API Configuration

Edit `src/socialsimullm/utils/config.py`:

```python
# Copy and paste your OpenAI API Key
openai_api_key = "sk-your-key-here"

# If using a custom endpoint (e.g., local LLM server)
openai_base_url = "http://192.168.1.110:3001/v1"

# Set default models
class DefaultModel:
    embedding = "BAAI/bge-m3"      # Embedding model
    completion = "gpt-4o-mini"      # Completion model
```

---

## 2. Project Structure

```
SocialSimuLLM/
├── pyproject.toml                # Project config & dependencies
├── src/socialsimullm/            # Source package
│   ├── __init__.py
│   ├── __main__.py               # Entry point
│   ├── agents/                   # Agent behavior
│   │   ├── __init__.py
│   │   ├── agent.py              # Agent class
│   │   ├── memory.py             # Agent memory methods
│   │   └── movement.py          # Location rating & movement
│   ├── locations/                # Location management
│   │   ├── __init__.py
│   │   └── locations.py         # Location & Locations classes
│   ├── retrieve/                 # Memory retrieval
│   │   ├── __init__.py
│   │   ├── memory.py             # Memory class (JSON + SQLite)
│   │   └── reflect.py           # Reflect class (placeholder)
│   ├── prompt_templates/         # LLM prompt templates
│   │   ├── __init__.py
│   │   └── template_agents.py   # All agent prompt templates
│   ├── utils/                    # Utilities
│   │   ├── __init__.py
│   │   ├── config.py             # API keys & model config
│   │   ├── global_methods.py     # Helper functions
│   │   └── text_generation.py   # GPT requests & embeddings
│   └── data/                     # Template data files
│       └── town_data_template.json
├── tests/                        # Test files
│   ├── __init__.py
│   ├── test.py
│   ├── test_GPT.py
│   ├── test_module.py
│   └── test_math.py
├── projects/                     # Simulation output (gitignored)
│   └── <project_name>/
│       ├── meta.json
│       ├── town_data.json
│       ├── simulation_log.txt
│       ├── simulation_summary.txt
│       └── agent_data/
│           ├── event.json
│           ├── <agent>_memory.json
│           └── <agent>_memory.db
├── docs/                         # Documentation
│   ├── PRD.md
│   ├── changelog.md
│   ├── dev_guide.md
│   ├── business_rules.md
│   ├── design/
│   │   ├── system_design.md
│   │   ├── state_machine.md
│   │   └── data_models/
│   └── procedures/
│       └── workflow_index.md
├── README.md
└── README_zh.md
```

---

## 3. Running the Simulation

### 3.1 Basic Run

```bash
# From project root
uv run python -m socialsimullm
```

Or use the console script entry point:

```bash
uv run socialsimullm
```

### 3.2 Input Prompts

1. **Project Name**: Enter an existing project name to resume, or a new name to create one
2. **New Event**: Enter a global event description, or press Enter for "No new event."
3. **Number of Repeats**: How many 10-minute loops to run (Enter for 1)

### 3.3 Output Files

| File | Location | Description |
|------|----------|-------------|
| meta.json | `projects/<name>/` | Simulation state (time, round) |
| town_data.json | `projects/<name>/` | Town people and areas |
| simulation_log.txt | `projects/<name>/` | Detailed log of all rounds |
| simulation_summary.txt | `projects/<name>/` | LLM-generated daily summaries |
| event.json | `projects/<name>/agent_data/` | Global events |
| `<agent>_memory.json` | `projects/<name>/agent_data/` | Agent's experience memory |
| `<agent>_memory.db` | `projects/<name>/agent_data/` | Agent's embedding database |

---

## 4. Customization

### 4.1 Modify Town Data

After creating a project, edit `projects/<project_name>/town_data.json`:

```json
{
  "general": {
    "memory_limit": 5
  },
  "town_people": {
    "Agent Name": {
      "description": "{\"name\": \"Agent Name\", \"age\": 30, ...}",
      "starting_location": "Location Name"
    }
  },
  "town_areas": {
    "Location Name": "Description of the location"
  }
}
```

Then restart the simulation.

### 4.2 Modify Prompt Templates

Edit `src/socialsimullm/prompt_templates/template_agents.py` to change how agents:
- Plan their day (`agent_plan_system`, `agent_plan_prompt`)
- Plan their hour (`hourly_planning_system`, `hourly_planning_prompt`)
- Execute actions (`agent_execute_action_system`, `agent_execute_action_prompt`)
- Rate locations (`rate_location_system`, `rate_location_prompt`)
- Rate experiences (`rate_experiences_system`, `rate_experiences_prompt`)
- Form impressions (`agent_impressions_system`, `agent_impressions_prompt`)
- Simplify actions (`action_simpilfy_system`, `action_simpilfy_system_prompt`)
- Reflect on the day (`agent_reflection_system`, `agent_reflection_prompt`)

### 4.3 Modify Agent Behavior

Edit files in `src/socialsimullm/agents/`:
- `agent.py`: Core agent logic (planning, action, reflection)
- `memory.py`: Memory-related methods
- `movement.py`: Location rating and movement

### 4.4 Modify Configuration

Edit `src/socialsimullm/utils/config.py`:
- Change API endpoint (`openai_base_url`)
- Change models (`DefaultModel.completion`, `DefaultModel.embedding`)
- Change API key (`openai_api_key`)

---

## 5. Coding Standards

### 5.1 Style Guide

- Follow **PEP 8** conventions
- Use **type annotations** on all function signatures
- Use **Google style docstrings** (bilingual: English first, Chinese second)
- **No emojis in code** (may not render correctly in terminals)

### 5.2 File Organization

- Prefer **200-400 lines** per file, max 800 lines
- **Function size**: Prefer < 50 lines per function
- **Nesting depth**: Max 4 levels
- **No hardcoded values**: Use constants or config

### 5.3 Error Handling

- Handle errors explicitly at every level
- Provide user-friendly error messages in UI-facing code
- Log detailed error context on the server side
- Never silently swallow errors

### 5.4 Immutability

- Create new objects, never mutate existing ones
- Use `dataclasses` or `NamedTuple` for data containers

### 5.5 Import Order

1. External packages
2. Internal modules
3. Relative imports
4. Styles (if applicable)

### 5.6 Tools

| Tool | Purpose |
|------|---------|
| **black** | Code formatting |
| **ruff** | Linting |
| **isort** | Import sorting |
| **mypy** | Type checking |

---

## 6. Testing

### 6.1 Testing Philosophy

This project uses **manual test plans** rather than automated tests. AI generates step-by-step test instructions, and humans execute them.

### 6.2 Test Plan Location

```
tests/
├── test_plans/              # Manual test plans (AI writes, human runs)
│   └── feature_<name>.md      # One test plan per feature
└── integration/             # Integration test checklists
    └── <module>_tests.md
```

### 6.3 Test Plan Template

See `docs/procedures/_template.md` for the test plan template.

### 6.4 Running Tests

Since tests are manual:
1. Read the test plan for the feature
2. Follow the step-by-step instructions
3. Record results (Pass/Fail)
4. Report issues

---

## 7. Common Workflows

### 7.1 Creating a New Feature

1. Read `docs/PRD.md` to understand requirements
2. Read relevant design documents in `docs/design/`
3. Check `docs/business_rules.md` for domain constraints
4. Implement the feature
5. Generate test plan in `tests/test_plans/`
6. Code review (via `ecc:code-review` skill)
7. Update documentation

### 7.2 Fixing a Bug

1. Reproduce the bug (follow test plan steps)
2. Read relevant source code
3. Fix the issue
4. Add regression test case to test plan
5. Verify fix
6. Update `docs/changelog.md`

### 7.3 Adding a New Agent Type

1. Edit `town_data.json` (or the template at `src/socialsimullm/data/town_data_template.json`)
2. Add agent to `town_people` with description JSON
3. Add starting location
4. Optionally add new location to `town_areas`
5. Run simulation

### 7.4 Changing LLM Provider

1. Update `src/socialsimullm/utils/config.py`
2. Change `openai_base_url` to new provider's endpoint
3. Update `openai_api_key` if needed
4. Adjust `DefaultModel` class for model names
5. Test with a simple simulation

---

## 8. Debugging

### 8.1 Logging Flags

In `__main__.py`, toggle these flags to control output:

| Flag | Default | Effect |
|------|---------|--------|
| `log_debug` | True | Log debug information |
| `log_locations` | True | Log location changes to file |
| `log_actions` | True | Log agent actions to file |
| `log_plans` | True | Log agent plans to file |
| `log_ratings` | True | Log location ratings to file |
| `log_memory` | True | Log memory operations to file |

### 8.2 Print Flags

| Flag | Default | Effect |
|------|---------|--------|
| `print_locations` | True | Print locations to console |
| `print_actions` | True | Print actions to console |
| `print_plans` | True | Print plans to console |
| `print_ratings` | False | Print ratings to console |
| `print_memory` | False | Print memory to console |

### 8.3 Summarization Flags

| Flag | Default | Effect |
|------|---------|--------|
| `summarize_locations` | False | Include locations in summary |
| `summarize_actions` | True | Include actions in summary |
| `summarize_plans` | False | Include plans in summary |
| `summarize_ratings` | False | Include ratings in summary |
| `summarize_memory` | True | Include memory in summary |

---

## 9. Git Workflow

### 9.1 Branch Strategy

| Branch Type | Naming | Purpose |
|-------------|--------|---------|
| main | `main` | Production-ready code |
| Development | `dev-X.Y.Z` | Feature development for version X.Y.Z |
| Feature | `feat/[ticket]-[description]` | Individual feature development |
| Hotfix | `fix/[ticket]-[description]` | Urgent production fix |

### 9.2 Commit Format

```
<type>(<scope>): <description>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`

Examples:
```
feat(agents): add daily planning capability
fix(memory): correct embedding storage bug
docs(readme): update installation instructions
```

### 9.3 Pull Request Guidelines

1. Title: Short summary under 70 characters
2. Body: Comprehensive summary of ALL commits
3. Include test plan checklist
4. Reference related docs changes
5. Push with `-u` flag if new branch

---

## 10. Troubleshooting

### 10.1 API Connection Errors

**Symptom**: `Error occurred: Connection refused`

**Solution**:
- Verify `openai_base_url` is correct
- Check network connection
- Verify API key is valid

### 10.2 Module Not Found

**Symptom**: `ModuleNotFoundError: No module named 'socialsimullm'`

**Solution**:
```bash
uv sync  # Reinstall the package
```

### 10.3 JSON Decode Error

**Symptom**: `json.decoder.JSONDecodeError`

**Solution**:
- Check `town_data.json` for syntax errors
- Verify `meta.json` is valid JSON
- Check agent memory files for corruption

### 10.4 SQLite Errors

**Symptom**: `sqlite3.OperationalError`

**Solution**:
- Verify `agent_data/` directory exists
- Check file permissions
- Delete and recreate the `.db` file if corrupted
