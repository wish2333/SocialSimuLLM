# Changelog

All notable changes to SocialSimuLLM will be documented in this file.

## [3.1.0] - 2026-05-02

### Added

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

### Changed

- `__main__.py` reduced from 279 to 27 lines (CLI entry only)
- Agent class now uses proper class methods (no MethodType binding)
- Memory storage uses `MemoryEntry` dataclass instead of loose dicts
- Field names renamed: `global_time` -> `timestamp`, `action` -> `content`, `action_des` -> `summary`, `exp_type` -> `event_type`, `priority` -> `importance`, `other_agents` -> `entities`, `location` -> `location_id`

### Removed

- `retrieve/memory.py`, `retrieve/reflect.py`, `retrieve/__init__.py` (merged into `agents/memory.py` and `agents/reflection.py`)
- `agents/movement.py` (merged into `agents/agent.py`)
- All `MethodType` imports and wildcard imports
- Deprecated `*_old` directories and `*.bat` files

### New Files

- `agents/memory_entry.py` - MemoryEntry dataclass
- `agents/reflection.py` - ReflectionEngine standalone module
- `simulator/core.py` - SimulatorCore class
- `simulator/state.py` - SimulationState dataclass
- `simulator/events.py` - EventBus pub/sub infrastructure
- `utils/config.py` - SimulationConfig + load_config (rewrite)
- `utils/logger.py` - StructuredLogger (rewrite)

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
