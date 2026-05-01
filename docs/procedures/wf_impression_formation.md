# Impression Formation Workflow

## Metadata

- **ID**: WF-005
- **Version**: 3.1.0
- **Owner**: agents/agent.py
- **Trigger**: System event - after action execution and hourly planning

## Overview

After executing actions, agents form impressions of their current state across five dimensions: emotional status, social/learning drive, confidence in task completion, information acquisition preference, and technology acceptance inclination.

## Pre-conditions

- [ ] Agent has executed an action or completed hourly planning
- [ ] `hourly_plan` is set
- [ ] `global_time` is available
- [ ] LLM API is accessible

## Flow

### Step 1: Gather Context

**Actor**: System
**Action**:
- Get recent impressions: `memory.get_impressions_str(agent.name, 3)`
- Get new things: `memory.get_newthings_str(agent.name, memory_limit)`
- Get daily plans: `agent.daily_plans`

**Validation**: Context data is available.

### Step 2: Generate Impression via LLM

**Actor**: System (LLM)
**Action**: Call `agent.form_impression(global_time, prompt_meta, nearby_situations)`
- Format system prompt using `agent_impressions_system` template
- Format user prompt using `agent_impressions_prompt` template
- LLM generates impression
- Max 80 tokens, temperature 0.8

**Validation**: Impression is non-empty, <= 30 words.

### Step 3: Create Impression Experience

**Actor**: System
**Action**: Call `agent.memory_impression(global_time, impression)`
- Create experience dict with:
  - `exp_type='thought'`
  - `priority=4`
  - `action` = impression text

**Validation**: Experience dict is complete.

### Step 4: Store to Memory

**Actor**: System
**Action**: Call `memory.add_experience(experience, 'thought')`
- Save to agent's JSON memory file

**Validation**: Experience saved to `{agent_name}_memory.json`.

### Step 5: Log Output (Optional)

**Actor**: System
**Action**:
- If `log_actions` is True: Append impression to `log_output`
- If `print_actions` is True: Print impression to console

**Validation**: Output contains agent name and impression.

## Post-conditions

- [ ] All agents have updated `impression` attribute
- [ ] Impressions are saved to each agent's memory file
- [ ] Impressions use the five-dimension format

## Error Handling

| Error | Handling |
|-------|----------|
| LLM API unavailable | Return error string, log error, continue |
| Empty impression | Use default, log warning |
| Memory write fails | Exception raised, simulation stops |

## Related

- Business Rules: BR-014, BR-024
- State Machine: IMPRESSION_FORMATION (S7), MEMORY_UPDATE (S9)
- API: `GPT_request()` in text_generation.py
- Prompt: `agent_impressions_system`, `agent_impressions_prompt` in template_agents.py
