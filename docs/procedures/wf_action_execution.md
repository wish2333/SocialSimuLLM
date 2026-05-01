# Action Execution Workflow

## Metadata

- **ID**: WF-003
- **Version**: 3.1.0
- **Owner**: agents/agent.py
- **Trigger**: System event - every 10-minute loop

## Overview

Every 10 minutes in the simulation, each agent executes their planned hourly action using an LLM-generated response. The action can include communication with other agents at the same location or individual activities. The executed action is then rated for importance and stored to memory.

## Pre-conditions

- [ ] Agent has an hourly plan (`hourly_plan` is set)
- [ ] `hourly_action_prompt` is available (set during hourly planning)
- [ ] LLM API is accessible

## Flow

### Step 1: Prepare Action Prompt

**Actor**: System
**Action**:
- Format `hourly_action_prompt` with current `global_time`
- Get recent impressions: `memory.get_impressions_str(agent.name, 3)`
- Get new things: `memory.get_newthings_str(agent.name, memory_limit)`
- Get related things: `agent.related_things`

**Validation**: Prompt is non-empty

### Step 2: Execute Action via LLM

**Actor**: System (LLM)
**Action**: Call `agent.execute_action(global_time, prompt_meta, recent_impressions, nearby_situations)`
- LLM generates action using `GPT_request()`
- Max 80 tokens, temperature 0.8
- Action may include communication with other agents

**Validation**: Action is non-empty

### Step 3: Rate the Experience

**Actor**: System (LLM)
**Action**: Call `agent.rate_experience(prompt_meta, recent_impressions, nearby_situations, action)`
- LLM returns 1-9 rating using `rate_experiences_system` prompt
- Parse rating via `get_rating()`

**Validation**: Rating is between 1-9 (or 0 if parse fails)

### Step 4: Create Action Experience

**Actor**: System
**Action**: Call `agent.memory_actions(agents, global_time, priority)`
- Create experience dict with:
  - `exp_type='action'`
  - `priority` = rated value
  - `other_agents` = agents at same location
  - `action_des` = simplified SVO sentence

**Validation**: Experience dict is complete

### Step 5: Store to Memory

**Actor**: System
**Action**: Call `memory.add_experience(experience, 'action')`
- For action type: propagate to all `other_agents`
- Save to each agent's JSON memory file
- Embed action and store in SQLite

**Validation**: Experience saved to all relevant agents' memory files

### Step 6: Log Output (Optional)

**Actor**: System
**Action**:
- If `log_actions` is True: Append action to `log_output`
- If `print_actions` is True: Print action to console

**Validation**: Output contains agent name and executed action

## Post-conditions

- [ ] All agents have updated `action` attribute
- [ ] Actions are saved to relevant agents' memory files
- [ ] Action embeddings stored in SQLite for all agents at same location
- [ ] Experience has valid priority rating (1-9)

## Error Handling

| Error | Handling |
|-------|----------|
| LLM API unavailable | Return error string, log error, assign priority=0 |
| Rating parse fails | Retry 2 times, then use priority=0 |
| Memory write fails | Exception raised, simulation stops |

## Related

- Business Rules: BR-006, BR-016, BR-020, BR-029
- State Machine: ACTION_EXECUTION (S4), MEMORY_UPDATE (S9)
- API: `GPT_request()` in text_generation.py
- Prompt: `agent_execute_action_system`, `agent_execute_action_prompt` in template_agents.py
