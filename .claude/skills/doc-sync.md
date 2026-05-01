---
name: doc-sync
description: Auto-sync documentation based on user-provided commit/release info. Use after user manually commits or releases.
trigger: User provides commit message or release info, /doc-sync command
---

# Doc Sync Skill

> Automatically update project documentation based on user feedback about commits and releases.
> The user performs commits/releases manually, then provides the information for doc sync.

---

## Trigger

User provides one of:

1. **Commit info**: "I just committed: `feat(auth): add JWT token refresh`"
2. **Release info**: "I just released v2.3.0 with these changes: ..."
3. **Direct command**: `/doc-sync`

---

## Sync Workflow

### Step 1: Parse User Input

Extract from user's message:
- **Type**: commit / release / PR merge
- **Version**: (if release) the version number
- **Changes**: list of what was done
- **Scope**: which modules/files were affected

### Step 2: Determine Which Docs to Update

| Change Type | Docs to Update |
|-------------|---------------|
| New feature | PRD.md (mark feature as done), changelog.md, dev_guide.md (if new patterns) |
| Bug fix | changelog.md, business_rules.md (if new rule discovered) |
| Refactor | changelog.md, Structure.md (if architecture changed) |
| New workflow | procedures/workflow_index.md + procedures/*.md |
| Data model change | design/data_models/*.csv, business_rules.md |
| State machine change | design/state_machine.md |
| New API endpoint | design/system_design.md |
| Release | changelog.md (set release date) |

### Step 3: Update Each Document

#### changelog.md

Add entry under current version section:

```markdown
### Added
- [Feature description]

### Changed
- [Change description]

### Fixed
- [Fix description]
```

If user reports a release, finalize the version section:

```markdown
## [X.Y.Z] - YYYY-MM-DD
```

#### procedures/workflow_index.md

If new workflow identified, add to index:

```markdown
| vX.Y.Z | [Workflow Name] | New | [Description] |
```

#### design/state_machine.md

If state transitions changed, update transition matrix and diagram.

#### business_rules.md

If new rules discovered during implementation, add rule section.

#### design/data_models/*.csv

If fields changed, update the CSV file.

### Step 4: Verify Consistency

- [ ] All changed files mentioned in docs
- [ ] Version numbers consistent across documents
- [ ] No stale references to removed features
- [ ] business_rules.md matches actual code behavior
- [ ] procedures/ match actual user flows

### Step 5: Report Changes

Output a summary of all documentation updates made:

```
## Doc Sync Summary

Updated files:
- docs/changelog.md: Added 3 entries under [Unreleased]
- docs/procedures/workflow_index.md: Added WF-007
- docs/design/state_machine.md: Updated transition matrix

Files verified consistent: 6/6
```

---

## Special Cases

### User Reports Breaking Change

- Update PRD.md to mark affected features
- Add migration notes to changelog.md
- Update business_rules.md with new constraints

### User Reports Rollback

- Revert documentation changes
- Add rollback entry to changelog.md
- Update procedures if workflow changed

### User Reports Hotfix Release

- Add to changelog under hotfix version
- Update business_rules.md if rule changed
- Do NOT touch PRD.md (features unchanged)
