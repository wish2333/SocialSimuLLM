# Daily Reflection Workflow

## Metadata

- **ID**: WF-006
- **Version**: 3.1.0
- **Owner**: agents/agent.py
- **Trigger**: System event - end of day (time rolls over to next day 08:00)

## Overview

At the end of each day (when time rolls over from 20:00 to next day 08:00), agents reflect on their day's experiences, feelings about technology, social interactions, challenges, accomplishments, and what they would like to change.

## Pre-conditions

- [ ] Next global_time is a new day (`if_new_day(new_global_time)` returns True)
- [ ] Agent has important things from the day (priority > 6)
- [ ] `daily_plans` is set
- [ ] LLM API is accessible

## Flow

### Step 1: Check New Day

**Actor**: System
**Action**: Call `if_new_day(new_global_time)` to check if next time is 08:00
**Validation**: If True, proceed to Step 2; otherwise, skip reflection.

### Step 2: Gather Important Things

**Actor**: System
**Action**:
- Get important things: `memory.get_importants_str(agent.name, global_time)`
- Filters for `priority > 6` and same day as `global_time`
- Get recent reflections: `memory.get_impressions_str(agent.name, ...)` for context

**Validation**: Important things list is available.

### Step 3: Generate Reflection via LLM

**Actor**: System (LLM)
**Action**: Call `agent.form_reflection(global_time, prompt_meta, recent_reflection, important_things)`
- Format system prompt using `agent_reflection_system` template
- Format user prompt using `agent_reflection_prompt` template
- LLM generates reflection
- Max 120 tokens, temperature 0.8.

**Validation**: Reflection is non-empty, <= 75 words.

### Step 4: Create Reflection Experience

**Actor**: System
**Action**: Call `agent.memory_reflection(global_time, reflection)`
- Create experience dict with:
  - `exp_type='thought'`
  - `priority=9`
  - `action` = reflection text

**Validation**: Experience dict is complete.

### Step 5: Store to Memory

**Actor**: System
**Action**: Call `memory.add_experience(experience, 'reflection')`
- Save to agent's JSON memory file

**Validation**: Experience saved to `{agent_name}_memory.json`.

### Step 6: Log Output

**Actor**: System
**Action**:
- Append reflection to `log_output`
- Print reflection to console

**Validation**: Output contains agent name and reflection.

## Post-conditions

- [ ] All agents have updated `reflection` attribute
- [ ] Reflections are saved to each agent's memory file
- [ ] Reflections have priority=9 (extremely important)

## Error Handling

| Error | Handling |
|-------|----------|
| LLM API unavailable | Return error string, log error, continue |
| No important things | Use empty string, generate simple reflection |
| Memory write fails | Exception raised, simulation stops |

## Related

- Business Rules: BR-015, BR-025, BR-027
- State Machine: REFLECTION (S8), MEMORY_UPDATE (S9)
- API: `GPT_request()` in text_generation.py
- Prompt: `agent_reflection_system`, `agent_reflection_prompt` in template_agents.py
