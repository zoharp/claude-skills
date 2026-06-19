---
name: release-management
description: Use after every code change that requires version bumping or release notes. Handles versioning rules, release_notes.json updates, CLAUDE.md version tracking, and SCHEMA.md sync. Invoke when committing, releasing, or asked about versioning.
revision: 1.0.0
---

# Release Management

## After every code change, always:
1. Bump the version in the changed component(s)
2. Update `CLAUDE.md` — the `### Current versions` section must always reflect the latest versions
3. Update `release_notes.json` in the project root — prepend new entry, most recent first
4. Update `SCHEMA.md` — if any DB schema changed (new tables, columns, indexes, RPC functions), sync the relevant section

## Bump rules
- **Patch** (0.0.X): bug fix / tweak
- **Minor** (0.X.0): new feature
- **Major** (X.0.0): breaking change / schema change
- If the project has multiple components (backend/frontend), bump only the changed component(s)

## release_notes.json format

Each change string must start with an icon + bold short label, then an em-dash, then the detail:

| Icon | Meaning |
|------|---------|
| ✨ | New feature / added |
| 🐛 | Bug fix |
| 🔄 | Update / improvement / change |
| ⚡ | Performance |
| 🗑️ | Removed / reverted |

```json
[
  {
    "version": "2.1.1",
    "date": "2026-04-06",
    "changes": [
      "✨ **Summary export** — new Summary view option groups children by part key and sums quantities, one line per unique part.",
      "🐛 **Export order** — nodes are now reordered to DFS after BFS fetch so each parent is immediately followed by its descendants.",
      "🔄 **Locate BFS** — Locate now does a true level-order BFS; stops on first match instead of walking the full subtree."
    ]
  }
]
```

Prepend — newest entry first. The bold label is the scannable headline; keep it 2–4 words. The detail after the em-dash is one sentence max.

## CLAUDE.md — version tracking
The `### Current versions` block in `CLAUDE.md` must be updated on every bump:
```markdown
### Current versions (update after every bump)
- **Backend:** `X.Y.Z`
- **Frontend:** `X.Y.Z`
```

## SCHEMA.md — schema sync
If the change involved any of the following, update the corresponding section in `SCHEMA.md`:
- New or modified tables / columns
- New or modified indexes
- New or modified RPC / stored functions
- New migrations

## Checklist before committing
- [ ] Version bumped in changed component(s)
- [ ] `CLAUDE.md` → `### Current versions` updated
- [ ] `release_notes.json` prepended with new entry (icon + **bold label** — detail)
- [ ] `SCHEMA.md` updated if schema changed
