# [Workflow Name]

## Metadata

- **ID**: WF-XXX
- **Version**: 0.1.0
- **Owner**: [Module/Component]
- **Trigger**: [User action / System event / Scheduled]
- **Last Updated**: YYYY-MM-DD

---

## Overview

[One-paragraph description of what this workflow accomplishes]

---

## Pre-conditions

- [ ] [Condition 1]
- [ ] [Condition 2]

---

## Flow

### Step 1: [Step Name]

**Actor**: User / System / External Service
**Action**: [Detailed description of what happens]
**Validation**: [What is validated at this step]
**On Failure**: [What happens if validation fails]

### Step 2: [Step Name]

**Actor**: User / System / External Service
**Action**: [Detailed description]
**Validation**: [What is validated]
**On Failure**: [Recovery or abort]

### Step 3: [Step Name]

**Actor**: User / System / External Service
**Action**: [Detailed description]
**Validation**: [What is validated]
**On Failure**: [Recovery or abort]

---

## Post-conditions

- [ ] [State 1 after completion]
- [ ] [State 2 after completion]

---

## Error Handling

| Error Scenario | Detection | Recovery | User Feedback |
|---------------|-----------|----------|---------------|
| [Scenario 1] | [How detected] | [Auto/Manual fix] | [Message shown] |
| [Scenario 2] | [How detected] | [Auto/Manual fix] | [Message shown] |

---

## Related

- **Business Rules**: [references to business_rules.md sections]
- **API Endpoints**: [references to system_design.md endpoints]
- **State Machine**: [references to state_machine.md states]
- **Data Models**: [references to data_models/*.csv]
