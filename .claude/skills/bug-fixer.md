---
name: bug-fixer
description: Systematic 4-phase debugging workflow. Use when investigating or fixing bugs.
trigger: User reports bug, error message, unexpected behavior, /bug-fixer command
---

# Bug Fixer Skill

> Four-phase systematic debugging methodology.
> Core principle: "No evidence, no conclusion. One change at a time."

---

## Phase 1: Collect Evidence

### 1.1 Reproduce the Bug

- Ask user for exact reproduction steps
- Identify the trigger (user action / system event / timing)
- Determine scope (all users / specific scenario / edge case)

### 1.2 Gather Context

```
MUST CHECK:
1. Error messages (exact text, stack traces)
2. Console logs (browser console, backend logs)
3. Recent changes (git log, git diff)
4. Related business rules (docs/business_rules.md)
5. State machine (docs/design/state_machine.md)
6. Known pitfalls (.claude/feedback/index.md)
```

### 1.3 Classify the Bug

| Type | Symptoms | Approach |
|------|----------|----------|
| Logic error | Wrong result, no crash | Trace data flow |
| State error | Wrong UI state, stale data | Check state machine |
| Race condition | Intermittent, timing-dependent | Check async flows |
| Rendering error | Visual glitch | Check component lifecycle |
| Integration error | API/network failure | Check endpoint & contract |
| Data error | Wrong/missing data | Check persistence |

**STOP here until evidence is collected. Do NOT jump to conclusions.**

---

## Phase 2: Analyze Patterns

### 2.1 Trace the Execution Path

Map the full execution chain from trigger to symptom:

```
[Trigger] --> [Component A] --> [Component B] --> [Component C] --> [Symptom]
     |              |               |               |
     v              v               v               v
  [State]       [Data]          [API Call]      [Render]
```

### 2.2 Identify the Gap

Where does the execution diverge from expected behavior?

- [ ] Input: Is the input correct?
- [ ] Processing: Is the logic correct?
- [ ] Output: Is the result what was expected?
- [ ] State: Is the state machine transition valid?

### 2.3 Form Hypotheses

List ALL possible causes ranked by likelihood:

```
H1: [Most likely cause] - Evidence: [what supports this]
H2: [Second most likely] - Evidence: [what supports this]
H3: [Third possibility] - Evidence: [what supports this]
```

---

## Phase 3: Verify Hypothesis

### 3.1 Test Hypothesis in Order

For each hypothesis (H1 first):

1. **Add minimal diagnostic code** (log, breakpoint)
2. **Run the reproduction steps**
3. **Observe the result**

### 3.2 Decision Tree

```
Does evidence support this hypothesis?
  YES -> Proceed to Phase 4 (Fix)
  NO  -> Move to next hypothesis
  UNCERTAIN -> Collect more evidence, return to Phase 1
```

### 3.3 Rule: One Hypothesis at a Time

Do NOT test multiple hypotheses simultaneously.
Do NOT make changes to "see if it fixes it" without understanding why.

---

## Phase 4: Implement Fix

### 4.1 Minimal Fix

- Make the smallest possible change that addresses the root cause
- Do NOT refactor surrounding code
- Do NOT add "improvements" while fixing

### 4.2 Verify the Fix

1. Reproduce the original bug -> should NOT reproduce
2. Test related functionality -> should still work (regression check)
3. Check edge cases

### 4.3 Clean Up

- Remove any diagnostic code (logs, breakpoints)
- Remove any temporary comments
- Ensure code follows project conventions

### 4.4 Document

- Update business_rules.md if the fix reveals a new rule
- Add test case to test plan
- Record in changelog

### 4.5 Feedback Check

If this bug was caused by a pattern (e.g., forgetting to check a condition):
- Record in `.claude/feedback/raw/` as a prevention signal
- Update `.claude/feedback/index.md` if not already tracked

---

## Common Pitfalls

| Pitfall | Why It's Bad | Correct Approach |
|---------|-------------|-----------------|
| Guessing the fix | Wastes time, may introduce new bugs | Collect evidence first |
| Changing multiple things | Can't tell which change fixed it | One change at a time |
| Fixing the symptom | Bug will recur | Find and fix root cause |
| Not testing regression | Fix may break something else | Test related functionality |
| Not documenting | Same bug will be found again | Add test case + feedback |
