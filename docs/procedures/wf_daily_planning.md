# Daily Planning Workflow

## Metadata

- **ID**: WF-001
- **Version**: 3.1.0
- **Owner**: agents/agent.py
- **Trigger**: System event - global_time is "08:00" (new day)

## Overview

At the start of each day (08:00), every agent in the simulation generates a daily plan consisting of hourly actions from 08:00 to 20:00. The plan is generated using an LLM prompt that considers the agent's description, recent impressions, and recent events.

## Pre-conditions

- [ ] global_time is "08:00" (`if_new_day()` returns True)
- [ ] Agent has been initialized with `init_memory()`
- [ ] `prompt_meta` template is available
- [ ] LLM API is accessible

## Flow

### Step 1: Check New Day

**Actor**: System
**Action**: Call `if_new_day(global_time)` to check if time is 08:00
**Validation**: If True, proceed to Step 2; otherwise, skip daily planning

### Step 2: Prepare Prompt

**Actor**: System
**Action**:
- Get recent impressions: `memory.get_impressions_str(agent.name, 3)`
- Get new things: `memory.get_newthings_str(agent.name, memory_limit)`
- Format system prompt using `agent_plan_system` template
- Format user prompt using `agent_plan_prompt` template with current hour

**Validation**: Prompts are non-empty

### Step 3: Generate Daily Plan

**Actor**: System (LLM)
**Action**: Call `agent.daily_planning(global_time, prompt_meta, recent_impressions, newthings)`
- LLM generates hourly plan using `GPT_request()`
- Max 300 tokens, temperature 0.7

**Validation**: Plan covers 08:00-20:00 with one action per hour

### Step 4: Store Plan to Memory

**Actor**: System
**Action**:
- Create experience dict with `exp_type='plan'`, `priority=3`
- Call `memory.add_experience(experience, 'plan')`
- Store to agent's JSON memory file

**Validation**: Experience saved to `{agent_name}_memory.json`

### Step 5: Log Output (Optional)

**Actor**: System
**Action**:
- If `log_plans` is True: Append plan to `log_output`
- If `print_plans` is True: Print plan to console

**Validation**: Output contains agent name and plan

## Post-conditions

- [ ] All agents have updated `daily_plans` attribute
- [ ] Daily plans are saved to each agent's memory file
- [ ] Plans are formatted as hourly actions from 08:00-20:00

## Error Handling

| Error | Handling |
|-------|----------|
| LLM API unavailable | Return error string, log error, continue |
| Empty plan generated | Use empty string, log warning |
| Memory file write fails | Exception raised, simulation stops |

## Related

- Business Rules: BR-004, BR-010, BR-021
- State Machine: DAILY_PLANNING (S2), MEMORY_UPDATE (S9)
- API: `GPT_request()` in text_generation.py
- Prompt: `agent_plan_system`, `agent_plan_prompt` in template_agents.py
