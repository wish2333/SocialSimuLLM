# Simulation Startup Workflow

## Metadata

- **ID**: WF-008
- **Version**: 3.1.0
- **Owner**: __main__.py
- **Trigger**: User action - run `uv run python -m socialsimullm`

## Overview

When the simulation starts, the system initializes global variables, loads project data, creates the world graph, creates agents, initializes memory, and enters the main simulation loop.

## Pre-conditions

- [ ] Project name is provided by user
- [ ] `pyproject.toml` dependencies are installed (`uv sync`)
- [ ] LLM API key is configured in `config.py`

## Flow

### Step 1: Get Project Name

**Actor**: User
**Action**: Input project name when prompted
**Validation**: Project name is non-empty.

### Step 2: Load or Create Project

**Actor**: System
**Action**: Call `load_meta_data(project_folder, project_name, global_time)`
- If project exists: Load `meta.json`
- If not: Create project folder, `agent_data/` subfolder, and default `meta.json`

**Validation**: `meta.json` loaded or created.

### Step 3: Load Town Data

**Actor**: System
**Action**: Call `load_town_data(project_folder)`
- Load `town_data.json`
- If not exists: Copy from template, prompt user to modify and exit

**Validation**: `town_data.json` loaded with `general`, `town_people`, `town_areas`.

### Step 4: Initialize Global Time and Round

**Actor**: System
**Action**: Read from `meta.json`:
- `global_time` (default: "Day 1, 08:00")
- `round` (default: 0)
- `memory_limit` from `town_data['general']`

**Validation**: Time format is "Day X, HH:MM".

### Step 5: Create World Graph

**Actor**: System
**Action**:
- Create NetworkX Graph: `world_graph = nx.Graph()`
- Add nodes for each town area
- Add edges: each node to itself, to neighbor, and first to last (cyclic)

**Validation**: Graph has all town areas as nodes and proper edges.

### Step 6: Create Agents

**Actor**: System
**Action**: For each person in `town_people`:
- Create `Agent(name, description, starting_location, world_graph)`
- Attach methods via `MethodType` from `memory.py` and `movement.py`

**Validation**: All agents created with correct attributes.

### Step 7: Initialize Memory

**Actor**: System
**Action**:
- Call `exist_memory_file(agent.name, project_folder)` for each agent
- Create `Memory(project_folder, agents, memory_limit)`
- Load event file: `memory.load_event_file()`
- Get initial memory for each agent: `memory.get_init_memory(agent.name)`
- Call `agent.init_memory(daily_plans, hourly_plan, events)`

**Validation**: All agents have initialized memory.

### Step 8: Get Global Event (Optional)

**Actor**: User
**Action**: Input global event when prompted (or press Enter for "No new event.")
**Validation**: Event is processed and added to all agents' memories with priority=9.

### Step 9: Enter Simulation Loop

**Actor**: System
**Action**: Get number of repeats from user, then enter main loop.
**Validation**: Loop starts with correct round number.

## Post-conditions

- [ ] Project folder exists with all required files
- [ ] World graph created with all locations
- [ ] All agents created and initialized
- [ ] Memory system initialized with existing or empty memories
- [ ] Global time and round loaded from persistence

## Error Handling

| Error | Handling |
|-------|----------|
| Project folder creation fails | Exception raised, simulation stops |
| `town_data.json` missing, no template | Exception raised with error message |
| Agent memory file creation fails | Exception raised, simulation stops |
| Starting location not in graph | Warning logged, agent still created |

## Related

- Business Rules: BR-050 to BR-064
- State Machine: INITIALIZING (L1) -> RUNNING (L2)
- Data Files: `meta.json`, `town_data.json`, `event.json`, `{agent}_memory.json`
