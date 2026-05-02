# Project Constitution

> This file is the "supreme law" for AI assistants working on this project.
> It defines behavior rules, document hierarchy, and directory conventions.
> AI MUST read this file first at every session start.

---

## Project Metadata

- **Name**: SocialSimuLLM
- **Domain**: Multi-Agent Social Simulation / Computational Social Science
- **Type**: CLI Tool + Library (with optional Streamlit frontend)
- **Version**: 3.1.0
- **Repository**: `socialsimullm` (GitHub)

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | Streamlit | >=1.30 |
| Backend | Python | >=3.10 |
| Database | JSON file-based / SQLite | - |
| Visualization | Plotly + PyVis | >=5.0 / >=0.3 |
| Data Processing | Pandas + NumPy | >=2.0 |
| LLM Integration | OpenAI API | - |
| Validation | Pydantic | >=2.0 |
| Build | setuptools | >=61.0 |
| Package Manager (backend) | uv | - |

## Development Environment

- **OS**: Windows 11
- **Runtime**: Python 3.11+ / Node 20+
- **Package Manager (frontend)**: bun
- **Package Manager (backend)**: uv
- **Build Check (frontend)**: cd frontend && bun run build

## AI Behavior Rules

### Core Principles

1. **Document-first**: Always read relevant docs before coding. Docs > Code.
2. **No guessing**: When uncertain, ask the user. Never make assumptions.
3. **One change at a time**: Modify one thing, verify it works, then proceed.
4. **Evidence over intuition**: Gather evidence before forming conclusions.
5. **Sub-agent isolation**: Each sub-task gets a fresh instance, no inherited context.

### Document Priority

When conflicting information exists, follow this priority:

1. `docs/PRD.md` - Product requirements (highest)
2. `docs/design/*.md` - System design and architecture
3. `docs/procedures/*.md` - Business and system workflows
4. `docs/business_rules.md` - Domain-specific rules
5. `.claude/rules/*.md` - Coding standards
6. Source code (lowest)

### Mandatory Before Coding

Before writing any code, the AI MUST:

1. Read `docs/PRD.md` to understand the requirement
2. Read relevant design documents in `docs/design/`
3. Check `docs/business_rules.md` for domain constraints
4. Review `feedback/index.md` for known pitfalls and user preferences
5. Re-read all of the above at the start of each new phase (prevent requirement drift)

### Mandatory Before Stopping

Before ending a task, the AI MUST:

1. Run code review (via `ecc:code-review` skill)
2. Sync documentation (via `/doc-sync` skill if user provides commit/release info)
3. Record any new user feedback to `feedback/`

## Directory Convention

```
project-root/
  CLAUDE.md                    # This file (constitution)
  docs/                        # Documentation layer
    PRD-x.x.x.md               # Product Requirements Document
    design/                    # System design artifacts
      system_design.md         # Architecture and module design
      state_machine.md         # State machine definitions
      data_models/             # Data model field definitions (CSV)
        *.csv                  # One CSV per model
    procedures/                # Workflow definitions
      workflow_index.md        # Master index with version tracking
      *.md                     # Individual workflow files
    business_rules.md          # Domain business rules
    dev_guide.md               # Development guide and conventions
    changelog.md               # Version change log
  .claude/
    rules/                     # Coding rules (extends global rules)
      coding-style.md          # Code style conventions
      testing.md               # Testing requirements
      git-workflow.md          # Git conventions
      security.md              # Security requirements
      performance.md           # Performance guidelines
      patterns.md              # Design patterns to follow
    skills/                    # Project-specific task templates
      bug-fixer.md             # Systematic debugging (4-phase method)
      doc-sync.md              # Auto-sync docs from user commit/release feedback
    feedback/                  # Feedback evolution system
      index.md                 # Central feedback index
      raw/                     # Raw feedback records
        YYYY-MM-DD_*.md        # Date-prefixed feedback files
      graduated/               # Rules promoted from feedback
        *.md                   # Graduated rule files
```

## Skill Reference

### Project Skills (`.claude/skills/`)

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `/bug-fixer` | Bug report / investigation | 4-phase systematic debugging |
| `/doc-sync` | User provides commit/release info | Auto-sync docs from manual releases |

### ECC Skills (External)

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `ecc:feature-dev` | New feature request | End-to-end feature development with planning |
| `ecc:code-review` | After code changes | Quality, security, performance review |

### Release Flow

Releases are performed **manually by the user**. After the user commits or releases:
1. User provides commit message and/or release version info
2. AI invokes `/doc-sync` to update all documentation accordingly

## Prohibited Actions

- NEVER skip reading docs before coding
- NEVER modify code without understanding the corresponding business rule
- NEVER stop a task without code review and doc sync
- NEVER reuse context from a previous sub-agent task
- NEVER make more than one unverified change at a time
- NEVER ignore feedback from `feedback/index.md`
