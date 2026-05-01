# Simulation Summary Workflow

## Metadata

- **ID**: WF-010
- **Version**: 3.1.0
- **Owner**: __main__.py, utils/text_generation.py
- **Trigger**: System event - end of day (time rolls to next day) and end of repeats

## Overview

At the end of each day (when time rolls over) and at the end of the simulation, a summary of the day's activities is generated using an LLM and saved to the simulation summary file.

## Pre-conditions

- [ ] `if_new_day(new_global_time)` returns True, OR end of repeats reached
- [ ] `summary_input` has accumulated action data
- [ ] LLM API is accessible

## Flow

### Step 1: Check Summary Trigger

**Actor**: System
**Action**: Check if:
- `if_new_day(new_global_time)` is True AND `repeat != 0`, OR
- `repeat == repeats - 1` (last iteration)

**Validation**: Trigger condition met.

### Step 2: Accumulate Summary Input

**Actor**: System
**Action**: During simulation, append to `summary_input`:
- Location information (if `summarize_locations`)
- Agent actions (if `summarize_actions`)
- Agent plans (if `summarize_plans`)
- Agent ratings (if `summarize_ratings`)
- Agent memories (if `summarize_memory`)

**Validation**: `summary_input` contains relevant data.

### Step 3: Generate Summary via LLM

**Actor**: System (LLM)
**Action**: Call `summarize_simulation(summary_input)`
- System prompt: "You are a social science expert..."
- User prompt: `summary_input`
- LLM generates summary
- Max 500 tokens, temperature 0.8.

**Validation**: Summary is non-empty.

### Step 4: Output Summary

**Actor**: System
**Action**:
- Print to console: `print(summary_output)`
- Append to `log_output`
- Save to `simulation_summary.txt` (append mode, UTF-8)

**Validation**: Summary saved to file and printed.

### Step 5: Reset Summary Input

**Actor**: System
**Action**: Clear `summary_input = ""` for next day.

**Validation**: `summary_input` is empty.

## Post-conditions

- [ ] Daily summary generated and saved
- [ ] Summary file `simulation_summary.txt` updated
- [ ] `summary_input` cleared for next cycle

## Error Handling

| Error | Handling |
|-------|----------|
| LLM API unavailable | Log error, skip summary |
| Empty summary input | Skip summary generation |
| File write fails | Exception raised, simulation stops |

## Related

- Business Rules: BR-310 to BR-313
- State Machine: SUMMARIZING (L4)
- API: `summarize_simulation()` in text_generation.py
