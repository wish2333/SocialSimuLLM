# Location Rating Workflow

## Metadata

- **ID**: WF-004
- **Version**: 3.1.0
- **Owner**: agents/movement.py
- **Trigger**: System event - minutes are ":00" (new hour)

## Overview

Every hour (xx:00), each agent rates all locations in the town on a 1-9 likelihood scale. The agent then moves to the highest-rated location using NetworkX shortest path algorithm.

## Pre-conditions

- [ ] Minutes are ":00" (`if_new_hour()` returns True)
- [ ] Agent is at a valid location
- [ ] All locations exist in world graph
- [ ] LLM API is accessible

## Flow

### Step 1: Check New Hour

**Actor**: System
**Action**: Call `if_new_hour(global_time)` to check if minutes are ":00"
**Validation**: If True, proceed to Step 2; otherwise, skip location rating.

### Step 2: Rate Each Location

**Actor**: System (LLM)
**Action**: For each location in `locations.locations.values()`:
- Format prompt using `rate_location_prompt` template
- LLM returns 1-9 rating via `GPT_request()`
- Max 5 tokens, temperature 0.7

**Validation**: Rating is parseable as integer (1-9)

### Step 3: Sort Locations by Rating

**Actor**: System
**Action**: Sort `place_ratings` list by rating (descending)
- Format: `[(location_name, rating, response), ...]`

**Validation**: Highest-rated location is first in list.

### Step 4: Move to Highest-Rated Location

**Actor**: System
**Action**: Call `agent.move(new_location_name)` where `new_location_name = place_ratings[0][0]`
- Uses NetworkX `shortest_path()` to find route
- Update `agent.location`

**Validation**: Agent's location is updated.

### Step 5: Record Location Change

**Actor**: System
**Action**: If location changed:
- Call `agent.memory_location_change(global_time, old_location, new_location)`
- Save to `town_data.json` via `save_location_change()`

**Validation**: Location change saved to memory and town_data.json.

### Step 6: Log Output (Optional)

**Actor**: System
**Action**:
- If `log_ratings` is True: Append ratings to `log_output`
- If `print_ratings` is True: Print ratings to console
- If `log_locations` is True: Append movement to `log_output`

**Validation**: Output contains location ratings and movement info.

## Post-conditions

- [ ] All agents have updated `place_ratings` attribute
- [ ] Agents moved to highest-rated location
- [ ] Location changes saved to memory (`exp_type='action'`, `priority=2`)
- [ ] Town data updated with new agent locations

## Error Handling

| Error | Handling |
|-------|----------|
| LLM API unavailable | Use rating=0, log error, skip movement |
| Rating parse fails | Retry 2 times, then use rating=0 |
| No path to destination | Log error, agent stays at current location |
| Location not in graph | Log warning, skip that location |

## Related

- Business Rules: BR-012, BR-013, BR-032, BR-033
- State Machine: LOCATION_RATING (S5), MOVING (S6)
- API: `GPT_request()` in text_generation.py
- Prompt: `rate_location_system`, `rate_location_prompt` in template_agents.py
