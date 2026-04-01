# claude-skills

Reusable Claude Code skills for Orcanos projects. Each skill is a folder with a `SKILL.md` file that Claude Code auto-invokes based on task context.

## Skills

| Skill | Description |
|---|---|
| `release-management` | Version bumping rules, release_notes.json format, checklist |
| `orcanos-rag-architecture` | RAG pipeline, 2-stage router, chunking, retrieval, ETL |
| `supabase-patterns` | Auth (allowlist + JWT), pgvector, live settings, multi-tenant |
| `gcp-deployment` | Cloud Run, Cloud Build, Vercel, secrets via substitution variables |
| `fastapi-streaming` | NDJSON streaming, React fetch consumer, module testing |

## Structure
```
claude-skills/
├── skills/
│   ├── release-management/
│   │   └── SKILL.md
│   ├── orcanos-rag-architecture/
│   │   └── SKILL.md
│   ├── supabase-patterns/
│   │   └── SKILL.md
│   ├── gcp-deployment/
│   │   └── SKILL.md
│   └── fastapi-streaming/
│       └── SKILL.md
├── README.md
├── install.sh
└── install.bat
```

## Install

**Mac / Linux:**
```bash
git clone https://github.com/zoharp/claude-skills
cd claude-skills
chmod +x install.sh
./install.sh              # install all skills
./install.sh release-management  # install one skill
```

**Windows:**
```bat
git clone https://github.com/zoharp/claude-skills
cd claude-skills
install.bat               # install all skills
install.bat release-management   # install one skill
```

Skills are copied to `~/.claude/skills/` (Mac/Linux) or `%USERPROFILE%\.claude\skills\` (Windows).

Then inside Claude Code run `/reload-plugins` to pick them up immediately.

## Update

```bash
git pull
./install.sh   # re-run to overwrite with latest versions
```

## Usage in CLAUDE.md

Reference skills in your project's `CLAUDE.md`:

```markdown
## Skills in use
- **`release-management`** — version bumping and release notes
- **`orcanos-rag-architecture`** — RAG pipeline and router
- **`supabase-patterns`** — auth and vector search
- **`gcp-deployment`** — Cloud Run and Cloud Build
- **`fastapi-streaming`** — NDJSON streaming endpoints
```

Claude will auto-invoke the relevant skill based on context, or you can reference them explicitly in conversation.

## Skill structure

```
skill-name/
└── SKILL.md       # YAML frontmatter + markdown instructions
```

`SKILL.md` frontmatter:
```markdown
---
name: skill-name
description: When Claude should auto-invoke this skill
---

# Skill content here
```

## Adding a new skill

1. Create a folder: `mkdir my-new-skill`
2. Add `my-new-skill/SKILL.md` with frontmatter + instructions
3. Run `./install.sh my-new-skill`
4. Test with `/reload-plugins` in Claude Code
5. Commit and push

## Versioning

Skills are versioned via git. Tag releases:
```bash
git tag v1.0.0
git push origin v1.0.0
```
