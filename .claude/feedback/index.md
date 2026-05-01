# Feedback Index

> Central index for all user feedback signals.
> AI reads this at session start to avoid repeating known mistakes.

---

## How This Works

1. **Record**: User corrections or patterns are captured in `raw/`
2. **Index**: Each signal is tracked here with occurrence count
3. **Graduate**: Signals appearing 3+ times are promoted to `.claude/rules/`
4. **Propagate**: New sessions automatically follow graduated rules

---

## Active Signals

<!-- Format: | ID | Signal | Source | Count | First Seen | Status | -->

| ID | Signal | Source | Count | First Seen | Status |
|----|--------|--------|-------|------------|--------|
| F001 | [Example: no emojis in code] | user-correction | 1 | YYYY-MM-DD | active |
| F002 | [Example: validate input at boundary] | bug-fix | 1 | YYYY-MM-DD | active |

---

## Graduated Rules

<!-- Signals that have been promoted to formal rules -->

| ID | Signal | Graduated To | Graduation Date | Rule Summary |
|----|--------|-------------|-----------------|-------------|
| [F000] | [Example signal] | rules/coding-style.md | YYYY-MM-DD | [One-line summary] |

---

## How to Add Feedback

### When User Corrects AI Behavior

1. Create file: `raw/YYYY-MM-DD_*.md`
2. Add entry to the Active Signals table above
3. If count >= 3, graduate to rules:

```
1. Create rule file in .claude/rules/
2. Move signal from Active to Graduated table
3. Announce graduation to user
```

### Raw Feedback File Template

```markdown
# Feedback: [Signal Description]

- **Date**: YYYY-MM-DD
- **Source**: user-correction / bug-fix / pattern-observation
- **Context**: [What was happening when this feedback occurred]
- **User's exact words**: "[Quote if available]"
- **Impact**: [What went wrong because this rule wasn't followed]
- **Proposed rule**: [One-line rule that would prevent this]
```
