# Changelog

> Version history for the project. Updated with each release.

## Format

Each entry follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`

---

## [Unreleased]

### Added
- New `src` layout with `pyproject.toml` for uv-based dependency management
- Entry point `socialsimullm` console script
- Bilingual docstrings (English + Chinese) in all source files

### Changed
- Reorganized project from flat `simulation/` directory to `src/socialsimullm/` package
- Updated all imports to use absolute package paths
- Moved test files to `tests/` directory
- Removed deprecated batch scripts and old files

### Fixed
- Syntax error in numpy dot product calculation (inherited from generative-agents)
- Import paths updated for new package structure

### Removed
- `requirements.txt` (replaced by `pyproject.toml`)
- Windows batch scripts (`*.bat` files)
- Old `simulation/` directory structure
- `simulation/projects/` (moved to root `projects/`)

---

## [3.1.0] - 2026-05-01

### Added
- Modern Python project structure with `pyproject.toml`
- `uv` as package manager
- `src/socialsimullm/` as main package directory
- Console script entry point: `socialsimullm`
- Module `__init__.py` files for proper package structure
- Comprehensive documentation suite:
  - `docs/PRD.md`
  - `docs/design/system_design.md`
  - `docs/design/state_machine.md`
  - `docs/business_rules.md`
  - `docs/dev_guide.md`
  - `docs/changelog.md`
  - `docs/procedures/workflow_index.md`

### Changed
- All imports updated from `simulation.X` to `socialsimullm.X`
- `main.py` moved to `__main__.py` with `main()` function
- README.md and README_zh.md updated for new structure
- `.gitignore` updated with modern Python patterns

### Migration Notes
- Users must run `uv sync` after pulling this version
- Old `simulation/` directory is deprecated
- Projects now stored in root `projects/` directory

---

## [3.0.0] - 2025-02-23

### Added
- Agent reflection capability (`form_reflection()`)
- Important things filtering for daily reflection (priority > 6)
- Event system with global events affecting all agents
- `summarize_simulation()` for daily narrative summaries
- Memory embeddings stored in SQLite for similarity search

### Changed
- Enhanced memory retrieval with combined scoring:
  - 50% similarity (cosine similarity of embeddings)
  - 30% recency (based on action index)
  - 20% importance (normalized priority)
- Improved prompt templates for more coherent agent behavior
- `get_related_things()` now uses weighted scoring algorithm

### Fixed
- Memory initialization for continuing simulations
- Location rating edge cases (missing ratings handled gracefully)

---

## [2.0.0] - 2025-02-22

### Added
- Agent impression formation (`form_impression()`)
- Five-dimension impression system:
  1. Emotional Status (Positive/Stable/Negative)
  2. Social/Learning Drive (Active/Routine/Exhausted)
  3. Confidence in Task Completion (Ahead/Normal/Behind)
  4. Information Acquisition Preference (Proactive/Passive/Shielding)
  5. Technology Acceptance Inclination (Open/Neutral/Rejection)
- Action simplification to SVO format (`simplify_action()`)
- Enhanced memory management with experience types

### Changed
- Optimized memory retrieval algorithms
- Improved agent state evaluation
- Refined memory management for better performance
- Updated main program structure
- Enhanced prompt templates

### Fixed
- Memory file initialization for new agents
- Edge cases in location rating

---

## [1.0.0] - 2025-02-20

### Added
- Initial release
- Agent class with daily planning (`daily_planning()`)
- Hourly planning (`hourly_planning()`)
- Action execution (`execute_action()`)
- Location rating (`rate_locations()`)
- Movement between locations using NetworkX shortest path
- Experience rating (1-9 scale)
- Memory storage in JSON format
- LLM integration via OpenAI API
- Prompt templates for all agent interactions
- Basic simulation loop with 10-minute increments
- Project persistence (meta.json, town_data.json)
- World graph creation from town areas
- Console-based user input for project name, events, and repeats

### Features
- F-001: Agent Daily Planning
- F-002: Agent Hourly Planning
- F-003: Action Execution
- F-004: Experience Rating
- F-005: Location Rating and Movement
- F-006: Memory Management (JSON)
- F-007: Project Persistence
- F-008: Simulation Log Output
