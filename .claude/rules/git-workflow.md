# Git Workflow

> Git conventions for this project.
> Extends common git-workflow.md with project-specific rules.

## Branch Strategy

| Branch Type | Naming | Purpose |
|-------------|--------|---------|
| main | `main` | Production-ready code |
| Development | `dev-X.Y.Z` | Feature development for version X.Y.Z |
| Feature | `feat/[ticket]-[description]` | Individual feature development |
| Hotfix | `fix/[ticket]-[description]` | Urgent production fix |

## Commit Message Format

```
<type>(<scope>): <description>
```

**Types**: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`

**Examples**:
```
feat(auth): add JWT token refresh
fix(queue): prevent duplicate task submission
refactor(api): extract validation to middleware
docs(pipeline): update state machine diagram
```

## Pull Request Guidelines

1. Title: Short summary under 70 characters
2. Body: Comprehensive summary of ALL commits (not just latest)
3. Include test plan checklist
4. Reference related docs changes
5. Push with `-u` flag if new branch

## Commit Strategy

- **Prefer atomic commits**: One logical change per commit
- **Never force push to main**
- **Always create new commits** (never amend published commits)
- **Stage specific files** (never `git add .` or `git add -A`)
