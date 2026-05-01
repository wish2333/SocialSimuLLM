# Event Injection Workflow

## Metadata

- **ID**: WF-009
- **Version**: 3.1.0
- **Owner**: __main__.py, retrieve/memory.py
- **Trigger**: User action - input global event at startup

## Overview

Global events can be injected into the simulation at startup. These events are added to all agents' memories with priority 9 (extremely important) and influence agent behavior throughout the simulation.

## Pre-conditions

- [ ] User provides an event description (or chooses "No new event.")
- [ ] Memory system is initialized
- [ ] Event file exists (or is created)

## Flow

### Step 1: Get Event from User

**Actor**: User
**Action**: Input event description when prompted: "Please enter a new event:"
- If empty: Use "No new event." and load existing events
- If provided: Create new event experience

**Validation**: Event is a non-empty string (or "No new event.").

### Step 2: Create Event Experience

**Actor**: System
**Action**: If new event provided:
```python
new_event_experience = {
    "agent_name": "global_event",
    "global_time": global_time,
    "action": f'In {global_time}: "{new_event}".',
    "exp_type": 'event',
    "priority": 9
}
```

**Validation**: Experience dict is complete with priority=9.

### Step 3: Save to Event File

**Actor**: System
**Action**: Call `memory.save_and_load_event_file(new_event_experience)`
- Load existing `event.json`
- Append new event to `event` array
- Save updated file

**Validation**: Event saved to `event.json`.

### Step 4: Propagate to All Agents

**Actor**: System
**Action**: Call `memory.add_experience(new_event_experience, 'event')`
- For `exp_type='event'`: Add to ALL agents' memories
- Save to each agent's `{name}_memory.json`

**Validation**: Event added to all agents' memory files.

### Step 5: Load Events for Initialization

**Actor**: System
**Action**: If no new event:
- Load events from `event.json`
- Extract action texts: `[event_json['action'] for event_json in events]`
- Pass to `agent.init_memory(daily_plans, hourly_plan, events)`

**Validation**: All events loaded and passed to agents.

## Post-conditions

- [ ] Event saved to `event.json`
- [ ] Event added to all agents' memory files
- [ ] Events have priority=9 (extremely important)
- [ ] Agents initialized with event context

## Error Handling

| Error | Handling |
|-------|----------|
| Event file write fails | Exception raised, simulation stops |
| Memory write fails for agent | Exception raised, simulation stops |
| Invalid event format | Log error, use empty event list |

## Related

- Business Rules: BR-026
- State Machine: MEMORY_UPDATE (S9)
- Data File: `event.json`
