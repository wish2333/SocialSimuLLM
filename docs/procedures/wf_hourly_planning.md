# Hourly Planning Workflow

## Metadata

- **ID**: WF-002
- **Version**: 3.1.0
- **Owner**: agents/agent.py
- **Trigger**: System event - minutes are ":00" (new hour)

## Overview

At the start of each hour (xx:00), every agent generates a specific plan for the next hour based on their current location, nearby agents, and recent impressions. The plan is generated using an LLM prompt and limited to 20 words.

## Pre-conditions

- [ ] Minutes are ":00" (`if_new_hour()` returns True)
- [ ] Agent has a daily plan (`daily_plans` is set)
- [ ] Agent is at a valid location
- [ ] LLM API is accessible

## Flow

### Step 1: Check New Hour

**Actor**: System
**Action**: Call `if_new_hour(global_time)` to check if minutes are ":00"
**Validation**: If True, proceed to Step 2; otherwise, skip hourly planning

### Step 2: Gather Context

**Actor**: System
**Action**:
- Get people at current location: `[agent.name for agent in agents if agent.location == location]`
- Get location description from `town_areas[location.name]`
- Get recent impressions: `memory.get_impressions_str(agent.name, 3)`
- Get new things: `memory.get_newthings_str(agent.name, memory_limit)`
- Get related things: `memory.get_related_things_str(agent.name, agent.hourly_plan, 5)`

**Validation**: Context data is available

### Step 3: Generate Hourly Plan

**Actor**: System (LLM)
**Action**: Call `agent.hourly_planning(agents, location, global_time, town_areas, prompt_meta, recent_impressions, newthings)`
- LLM generates hourly plan using `GPT_request()`
- Max 45 tokens, temperature 0.7

**Validation**: Plan is non-empty, <= 20 words

### Step 4: Store Plan to Memory

**Actor**: System
**Action**:
- Create experience dict with `exp_type='plan'`, `priority=2`
- Call `memory.add_experience(experience, 'plan')`
- Store to agent's JSON memory file

**Validation**: Experience saved to `{agent_name}_memory.json`

### Step 5: Log Output (Optional)

**Actor**: System
**Action**:
- If `log_actions` is True: Append plan to `log_output`
- If `print_actions` is True: Print plan to console

**Validation**: Output contains agent name and hourly plan

## Post-conditions

- [ ] All agents have updated `hourly_plan` attribute
- [ ] Hourly plans are saved to each agent's memory file
- [ ] Related things are retrieved for the next action

## Error Handling

| Error | Handling |
|-------|----------|
| LLM API unavailable | Return error string, log error, continue |
| Empty plan generated | Use empty string, log warning |
| No agents at location | Use empty people list |

## Related

- Business Rules: BR-005, BR-011, BR-022
- State Machine: HOURLY_PLANNING (S3), MEMORY_UPDATE (S9)
- API: `GPT_request()` in text_generation.py
- Prompt: `hourly_planning_system`, `hourly_planning_prompt` in template_agents.py
