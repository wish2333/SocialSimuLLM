# Testing Rules

> Testing requirements and conventions for this project.
> Extends common testing.md with project-specific rules.

## Testing Philosophy

- **No automated tests**: Write test ITEMS (manual test checklists) in test files
- **AI writes test plans, human executes**: AI generates step-by-step test instructions
- **Test items track progress**: Each feature has a corresponding test checklist

## Test File Structure

```
tests/
  test_plans/              # Manual test plans (AI writes, human runs)
    feature_[name].md      # One test plan per feature
  integration/             # Integration test checklists
    [module]_tests.md
```

## Test Plan Template

```markdown
# Test Plan: [Feature Name]

## Setup
- [Prerequisites]

## Test Cases

### TC-001: [Test Case Name]
- **Steps**:
  1. [Step 1]
  2. [Step 2]
- **Expected**: [What should happen]
- **Priority**: P0 / P1 / P2

### TC-002: [Test Case Name]
- **Steps**:
  1. [Step 1]
  2. [Step 2]
- **Expected**: [What should happen]
- **Priority**: P0 / P1 / P2

## Regression Check
- [ ] Verify existing features still work
- [ ] Verify no performance regression
```

## When to Write Tests

1. **After every feature**: Generate test plan before marking feature complete
2. **After every bug fix**: Add regression test case
3. **Before release**: Run all test plans

## Coverage Guidelines

- All P0 (Must Have) requirements must have test cases
- All user-facing API endpoints must have test cases
- All state machine transitions must have test cases
