# Claude Skills Repository

A collection of reusable Claude Code skills. Each skill is a folder containing a `SKILL.md` file that Claude Code auto-invokes based on task context.

---

## Current versions (update after every bump)
- **Skills Library:** `1.0.0`
- **Individual Skills:** `1.0.0` each (see SKILL.md frontmatter for revision)

---

## Project Goal

Maintain and publish a library of Claude Code skills that other users can install into their own projects. Skills are self-contained — each folder holds everything Claude needs to understand when and how to apply that skill.

---

## Structure

```
claude-skills/
├── CLAUDE.md           ← this file
├── README.md           ← user-facing install and usage docs
├── install.bat         ← Windows installer
├── install.sh          ← Mac/Linux installer
├── templates/          ← project templates (CLAUDE.md, deploy scripts)
└── skills/
    ├── deploy/
    ├── fastapi-streaming/
    ├── gcp-deployment/
    ├── new-project/
    ├── orcanos-rag-architecture/
    ├── release-management/
    ├── req-create/
    ├── req-gap-check/
    ├── req-status/
    ├── req-trace/
    └── supabase-patterns/
```

Each skill folder contains exactly one file: `SKILL.md`.

---

## Skill File Format

```markdown
---
name: skill-name
description: When Claude should auto-invoke this skill
---

# Skill content here
```

The `description` field is the trigger — Claude reads it to decide when to auto-invoke the skill. Make it specific and action-oriented.

---

## Adding a New Skill

1. Create the folder: `skills/my-new-skill/`
2. Add `SKILL.md` with YAML frontmatter + instructions
3. Run `install.bat` (Windows) or `./install.sh` (Mac/Linux) to copy it to `~/.claude/skills/`
4. Run `/reload-plugins` in Claude Code to pick it up
5. Commit and push

---

## Installing Skills (for end users)

**Windows:**
```bat
install.bat              # install all skills
install.bat deploy       # install one skill
```

**Mac/Linux:**
```bash
./install.sh             # install all skills
./install.sh deploy      # install one skill
```

Skills are copied to `~/.claude/skills/` (Mac/Linux) or `%USERPROFILE%\.claude\skills\` (Windows).

---

## Current Skills

### Code & Deployment
| Skill | Description |
|---|---|
| `code-review` | Efficient PR review — correctness, regressions, security, edge cases |
| `deploy` | Git commit, push, Cloud Build deployment |
| `fastapi-streaming` | NDJSON streaming, React fetch consumer |
| `gcp-deployment` | Cloud Run, Cloud Build, Vercel, GCP secrets |
| `implementation-plan-review` | Review implementation plans — safety, dependency sequencing, readiness |
| `spec-review` | Technical spec review — API consistency, migrations, architecture gaps |

### Project & Requirement Management
| Skill | Description |
|---|---|
| `new-project` | Collect project details and generate CLAUDE.md |
| `req-create` | Create IEC 62304 software requirements |
| `req-gap-check` | Scan source files for missing requirement links |
| `req-status` | Compliance status dashboard |
| `req-trace` | Trace files/functions to requirements |
| `release-management` | Version bumping, release_notes.json updates |

### Architecture & Patterns
| Skill | Description |
|---|---|
| `orcanos-api` | Orcanos REST API — 100+ endpoint docs, auth, CORS/proxy patterns. See folder for individual API files (qw-login.md, qw-get-filter-results.md, etc.) |
| `orcanos-rag-architecture` | RAG pipeline, 2-stage router, chunking, ETL |
| `orcanos-test-automation` | Test automation patterns |
| `supabase-patterns` | Auth, pgvector, RLS, live settings |
