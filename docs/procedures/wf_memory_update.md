# Memory Update Workflow

## Metadata

- **ID**: WF-007
- **Version**: 3.1.0
- **Owner**: retrieve/memory.py
- **Trigger**: System event - after any experience is created

## Overview

Whenever an agent has a new experience (action, plan, thought, event, or reflection), the memory system stores it to the appropriate agent's JSON memory file and optionally creates embeddings in SQLite for similarity search.

## Pre-conditions

- [ ] Experience dict is complete with required fields
- [ ] `exp_type` is one of: action, plan, thought, event, reflection
- [ ] Agent memory files exist (or can be created)

## Flow

### Step 1: Determine Experience Type

**Actor**: System
**Action**: Check `exp_type` field:
- `action`: Propagate to all agents in `other_agents`
- `plan` or `thought`: Store to agent's own memory
- `event`: Propagate to ALL agents
- `reflection`: Store to agent's own memory

**Validation**: Valid `exp_type` identified.

### Step 2: Load Agent Memory

**Actor**: System
**Action**: For each target agent:
- Call `memory.load_memory_file(agent_name)`
- Parse JSON from `{agent_name}_memory.json`

**Validation**: Memory file loaded successfully.

### Step 3: Append Experience

**Actor**: System
**Action**:
- Get `memory` array from loaded data
- Append new experience dict
- Update `memory` array

**Validation**: Experience added to memory array.

### Step 4: Save Memory File

**Actor**: System
**Action**: Call `memory.save_memory_file(agent_name, agent_memory_full)`
- Write updated JSON to `{agent_name}_memory.json`
- Use `indent=4` for readability

**Validation**: File written successfully.

### Step 5: Sort Memory (For Actions Only)

**Actor**: System
**Action**: If `exp_type == 'action'`:
- Call `memory.sort_memory(agent_name, action_des)`
- Embed action using `get_embedding()`
- Store in SQLite `action_embeddings` table

**Validation**: Embedding stored in SQLite database.

## Post-conditions

- [ ] Experience saved to all relevant agents' JSON files
- [ ] Action embeddings stored in SQLite (for action type only)
- [ ] Memory files are valid JSON

## Error Handling

| Error | Handling |
|-------|----------|
| JSON decode error | Log error, create new empty memory structure |
| File write fails | Exception raised, simulation stops |
| Embedding API fails | Log error, continue without embedding |
| SQLite error | Log error, continue without embedding |

## Related

- Business Rules: BR-020 to BR-030, BR-029
- State Machine: MEMORY_UPDATE (S9)
- Storage: JSON files and SQLite databases
- Embedding: `get_embedding()` in text_generation.py
