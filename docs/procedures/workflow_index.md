# Workflow Index

> Master index of all business and system workflows.
> Each workflow is versioned and linked to its detail file.

---

## Version Change Index

| Version | Workflow | Change Type | Description |
|---------|----------|-------------|-------------|
| v3.1.0 | WF-001 to WF-009 | New | Initial workflow definitions |
| v3.1.0 | WF-010 | New | Event Injection Workflow added |

---

## Workflows

| ID | Workflow | File | Status |
|----|----------|------|--------|
| WF-001 | [Daily Planning Workflow](#) | [wf_daily_planning.md](wf_daily_planning.md) | Active |
| WF-002 | [Hourly Planning Workflow](#) | [wf_hourly_planning.md](wf_hourly_planning.md) | Active |
| WF-003 | [Action Execution Workflow](#) | [wf_action_execution.md](wf_action_execution.md) | Active |
| WF-004 | [Location Rating Workflow](#) | [wf_location_rating.md](wf_location_rating.md) | Active |
| WF-005 | [Impression Formation Workflow](#) | [wf_impression_formation.md](wf_impression_formation.md) | Active |
| WF-006 | [Daily Reflection Workflow](#) | [wf_daily_reflection.md](wf_daily_reflection.md) | Active |
| WF-007 | [Memory Update Workflow](#) | [wf_memory_update.md](wf_memory_update.md) | Active |
| WF-008 | [Simulation Startup Workflow](#) | [wf_simulation_startup.md](wf_simulation_startup.md) | Active |
| WF-009 | [Event Injection Workflow](#) | [wf_event_injection.md](wf_event_injection.md) | Active |
| WF-010 | [Simulation Summary Workflow](#) | [wf_simulation_summary.md](wf_simulation_summary.md) | Active |

---

## Workflow Diagram

```
Start Simulation (WF-008)
        |
        v
+-------------------+
|                   |
|  Daily Planning  |<-- (every 08:00)
|  (WF-001)         |
+-------------------+
        |
        v
+-------------------+       +-------------------+
|                   |       |                   |
|  Hourly Planning  |----->|  Action Execution  |
|  (WF-002)         |       |  (WF-003)         |
+-------------------+       +--------+----------+
                                   |
                                   v
                +------------------+------------------+
                |                  |                  |
                v                  v                  v
        +--------+------+  +--------+------+  +--------+------+
        |               |  |               |  |               |
        |  Location     |  |  Impression   |  |  Memory        |
        |  Rating       |  |  Formation   |  |  Update        |
        |  (WF-004)     |  |  (WF-005)     |  |  (WF-007)     |
        +--------+------+  +--------+------+  +--------+------+
                |                  |                  |
                +--------+---------+---------+----------+
                         |
                         v
                +-------------------+
                |                   |
                |  End of Day?     |
                |  (next_day check) |
                +--------+----------+
                         |
                         | Yes
                         v
                +-------------------+       +-------------------+
                |                   |       |                   |
                |  Daily Reflection |------>|  Simulation     |
                |  (WF-006)         |       |  Summary         |
                +-------------------+       |  (WF-010)         |
                                        +-------------------+
```

---

## Workflow Template

Use this template when creating new workflow files:

```markdown
# [Workflow Name]

## Metadata

- **ID**: WF-XXX
- **Version**: X.X.X
- **Owner**: [Module/Component]
- **Trigger**: [User action / System event / Scheduled]

## Overview

[One-paragraph description of what this workflow accomplishes]

## Pre-conditions

- [ ] [Condition that must be true before workflow starts]

## Flow

### Step 1: [Step Name]

**Actor**: [User / System / External]
**Action**: [What happens]
**Validation**: [What is checked]

### Step 2: [Step Name]

**Actor**: [User / System / External]
**Action**: [What happens]
**Validation**: [What is checked]

## Post-conditions

- [ ] [State after workflow completes]

## Error Handling

| Error | Handling |
|-------|----------|
| [Error scenario] | [Recovery action] |

## Related

- Business Rules: [rule references]
- API Endpoints: [endpoint references]
- State Machine: [state references]
```
