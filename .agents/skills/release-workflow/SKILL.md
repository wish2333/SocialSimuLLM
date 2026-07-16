---
name: release-workflow
description: >
  Close out a milestone or implementation session by: (1) writing a Review.md doc matching the project's existing review style,
  (2) staging all changes, (3) committing with a structured message body, (4) creating a git tag, (5) creating a GitHub PR,
  (6) merging the PR with admin bypass. A generic replacement for project-specific session-closure skills.
  Use when the user says "close out", "wrap up", "finish a milestone", "create a review doc and commit", "release this version",
  or at the end of any significant implementation phase.
---

# Release Workflow

A six-step pipeline that turns completed work into a versioned, reviewed, PR-merged deliverable.

---

## Step 1: Set the version label

Decide the milestone or version label from context (e.g., `v2.1.0`, `sprint-14`, `M9`). This label drives the review document filename, commit title prefix, git tag name, and PR title.

Check existing conventions:

```bash
git tag --sort=-v:refname | head -5          # find tag naming pattern
ls docs/ | head -10                           # find review doc naming pattern
```

---

## Step 2: Write the Review document

Find the most recent review doc in the project to match style:

```bash
# typical locations
ls docs/ | head -10
ls docs/v1.0.0/ | head -10
```

Study one existing review doc — note its section structure, heading style, tone, and table format. Then create a new review doc:

- Path: `<docs-dir>/<label>-Review.md`
- Match existing review style (sections, tables, tone)
- Cover these topics (adapt to project):

  1. **Conclusion / 0** — one-paragraph summary of what was done and whether all gates passed
  2. **Deliverables** — checklist of tasks, new files, modified files
  3. **Architecture decisions** — why key choices were made (especially unexpected ones)
  4. **Verification results** — exact command outputs (typecheck, lint, test, build)
  5. **Known limitations** — what's deferred or known-broken
  6. **Migration / upgrade notes** — if this release changes configs, env vars, or data formats

---

## Step 3: Stage ALL changed files

```bash
git add -A
```

Always use `-A` to capture modified (M), deleted (D), and untracked (?) files. Do NOT stage manually — the user expects full coverage.

Check staged file count:

```bash
git diff --cached --stat | tail -1   # "X files changed, Y insertions(+), Z deletions(-)"
```

---

## Step 4: Commit with structured message

Structure: **one-line title** + **blank line** + **detailed body with grouped bullet points**.

```bash
git commit -m '<type>: <Label> delivery（<area1> + <area2> + ...）

<scope/context paragraph>.

<Area Header>:

  - <file/path>: <specific change>
  - <file/path>: <specific change>

<Another Area>:

  - <file/path>: <specific change>

Documentation:

  - <doc path>: <description>

Verification:

  - Static checks: <typecheck> zero errors / <linter> zero warnings
  - Tests: <test-command> <N>/<N> passed
  - Build: <build-command> succeeded

See <review-doc-path> for details; baseline tag = <tag-name>.'
```

Guidelines:

- Title type: `feat` / `fix` / `chore` / `refactor` (follow conventional commits)
- Area headers: brief, colon-terminated
- File paths: relative from repo root, no backticks
- Each bullet: one concrete change, no filler
- Verification section: exact numbers, not guesses
- Study the project's existing commit history for local style conventions:

```bash
git log --oneline -10
git log -1 --format="%B"    # last commit body
```

---

## Step 5: Create and push git tag

Tag the current HEAD. Check existing tag naming pattern first:

```bash
git tag --sort=-v:refname | head -10
```

Then:

```bash
git tag <label>
git push origin <label>
```

Use `--force` only if the tag already exists remotely and needs replacement.

---

## Step 6: Create and merge GitHub PR

Create a PR body file with a summary of what changed (can be a condensed version of the commit body):

```bash
gh pr create \
  --base main \
  --head <current-branch> \
  --title "<type>: <summary>" \
  --body-file <pr-body-path>
```

Check mergeability before merging:

```bash
gh pr view <pr-number> --json mergeable,mergeStateStatus,state
```

Merge with the appropriate strategy. Use `--admin` to bypass branch protection rules:

```bash
# merge (preserves all commits)
gh pr merge <pr-number> --merge --admin

# squash (compresses into one commit)
gh pr merge <pr-number> --squash --admin

# rebase (linear history without merge commit)
gh pr merge <pr-number> --rebase --admin
```

Choose based on project convention:
- Default: `--merge` (preserves atomic commits)
- `--squash` for project style that prefers one commit per PR
- `--rebase` for strictly linear main branch history

Verify merge result:

```bash
gh pr view <pr-number> --json state,mergedAt,mergeCommit
```

---

## What this skill replaces

This skill is a **generic** version of project-specific session-closure scripts. Compare to a project-specific version:

| Aspect | Generic (this skill) | Project-specific (example) |
|--------|---------------------|---------------------------|
| Package manager | `<package-manager>` | `bun` |
| Test command | `<test-command>` | `bun run test` |
| Typecheck command | `<typecheck>` | `bun run typecheck` |
| Lint command | `<linter>` | `bun run lint` |
| Build command | `<build-command>` | `bun run build` |
| Review doc format | Match existing project style | Predictable section# pattern |
| Commit message language | Any | Chinese |
| Tag naming | Match existing conventions | `m7.8-review`, `v1.0.0` |
| PR base branch | `main` by default | `main` |
| Merge method | Adaptable (`--merge`/`--squash`/`--rebase`) | `--merge --admin` |

When adapting this skill to a new project, identify these project-specific defaults in Step 1 before executing the pipeline.