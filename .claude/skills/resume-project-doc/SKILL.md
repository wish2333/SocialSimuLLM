---
name: resume-project-doc
description: >
  Generate a comprehensive Resume.md project document in the project's docs/ folder for job application purposes.
  Analyzes project docs, README, git history, and source code to produce a structured project experience document
  following the 8-element framework (overview, pain points, responsibilities, solution, dev process, results, highlights, retrospective).
  Use when: (1) user asks to generate resume/CV project documentation, (2) user wants to prepare project materials for job applications,
  (3) user asks to create a project experience document, (4) user mentions "resume project doc" or "project document for resume",
  (5) user wants to showcase a project for interview preparation.
  Triggers on keywords: resume, project document, job application, interview preparation, project experience, Resume.md.
---

# Resume Project Document Generator

Generate a `Resume.md` in the project's `docs/` folder that thoroughly documents a single project for resume/job application purposes.

## Workflow

1. **Gather project information** (read sources in parallel)
2. **Analyze and structure** (map findings to the 8-element framework)
3. **Fill gaps with reasonable fabrication** (within user's scope)
4. **Generate Resume.md** (write to `docs/Resume.md`)

## Step 1: Gather Project Information

Read these sources in parallel to build a complete picture:

| Source | What to Extract |
|--------|-----------------|
| `README.md` / `README_zh.md` | Project purpose, features, tech stack, user-facing description |
| `docs/` directory | Design docs, dev guide, changelog, procedures, architecture |
| `git log --oneline -100` | Development timeline, feature evolution, iteration phases |
| `git log --format="%H %s" --all` | Commit message patterns, major milestones |
| `package.json` / `pyproject.toml` / `Cargo.toml` etc. | Dependencies, scripts, project metadata |
| Source code structure | Architecture, modules, key components |
| `docs/changelog.md` | Version history, feature additions, bug fixes |
| `docs/design/` | System design decisions, architecture choices |
| `docs/dev_guide.md` | Development setup, contribution patterns |

If a source does not exist, skip it and rely on other sources.

## Step 2: Map to 8-Element Framework

Structure the document using these 8 sections (see `references/resume-template.md` for full template):

1. **Project Overview** -- name, type, role, duration, tech stack, target users, background
2. **Pain Points & Motivation** -- before/after framing with quantified improvements
3. **Key Responsibilities** -- full lifecycle coverage as independent developer
4. **Product Solution** -- overview, core feature design with rationale, system architecture
5. **Development Process** -- planning/research, MVP implementation, iteration phases
6. **Project Results** -- quantitative metrics, qualitative outcomes, capability demonstration
7. **Highlights & Challenges** -- technical challenges + solutions, design highlights, process highlights
8. **Project Retrospective** (optional) -- what went well, improvements, takeaways

## Step 3: Fill Gaps with Reasonable Fabrication

When project sources lack information for a section, fabricate details following these rules:

### Scope Constraints
- User is a **master's student** (sociology or similar social science)
- Has **education-related internship** experience
- **Self-taught developer** using AI-assisted VibeCoding approach
- Target users are **classmates, internship colleagues, fellow students** -- NOT commercial customers
- No large-scale deployment or marketing assumed unless explicitly stated

### Fabrication Guidelines
- **User persona**: Frame around campus/academic/internship scenarios (study groups, coursework, research workflows, internship tasks)
- **Pain points**: Draw from common student/intern frustrations (manual processes, tool fragmentation, information overload)
- **Metrics**: Use modest but realistic numbers (5-20 users among peers, 30-70% time savings)
- **Iterations**: Base on git commit history -- group commits into logical feature phases
- **Technical challenges**: Derive from actual code complexity and dependency choices
- **Never fabricate**: Enterprise clients, commercial revenue, large user bases, team management

### When Information is Ambiguous
- If git history is sparse: infer iteration phases from file structure changes and README version references
- If no docs exist: derive architecture and design decisions from source code analysis
- If tech stack is unusual: explain the choice as a learning opportunity (consistent with self-taught developer profile)

## Step 4: Generate Resume.md

Write the output to `docs/Resume.md` in the project directory.

### Writing Style
- Use **first person** ("I designed...", "I implemented...")
- Use **active voice** and **concrete verbs** (built, designed, optimized, integrated, deployed)
- **Quantify** wherever possible (time saved, users served, files processed, features delivered)
- **Link decisions to reasons** -- every design choice should reference a pain point or constraint
- Keep paragraphs concise: 2-4 sentences each
- Use tables for structured data (project overview, tech stack, metrics)
- Use bullet lists for features, responsibilities, results

### Section Length Guide
| Section | Target Length |
|---------|--------------|
| Project Overview | 150-250 words |
| Pain Points & Motivation | 100-200 words |
| Key Responsibilities | 80-150 words |
| Product Solution | 300-500 words |
| Development Process | 200-400 words |
| Project Results | 150-250 words |
| Highlights & Challenges | 200-350 words |
| Retrospective | 80-150 words |

Total target: 1500-2500 words.

### Language
- Generate in the **same language as the project's README** (check both README.md and README_zh.md)
- If both exist, default to **Chinese** (user's primary language based on CLAUDE.md)
- Technical terms may remain in English

## Template

Read `references/resume-template.md` for the complete output template with all sections and formatting examples.
