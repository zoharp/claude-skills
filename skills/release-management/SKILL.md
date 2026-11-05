---
name: release-management
description: Use after every code change that requires version bumping or release notes. Handles versioning rules, release_notes.json updates, CLAUDE.md version tracking, and SCHEMA.md sync. Invoke when committing, releasing, or asked about versioning.
revision: 1.1.0
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

## Help links on every change (since 2026-10-15 — new entries only, never retro-fit old ones)

When the project has a published user manual (GitBook or similar) and the change touches a
documented screen, end the change string with a link to the **help page it affects**:

```json
"✨ **Risk baselines** — freeze a risk file and compare later edits against it. [Help: Risk Baselines](https://orcanos.gitbook.io/traceability-marix/risk-management/risk-baselines)"
```

- **Format:** `[Help: <Page Title>](<absolute https URL>)` as the **last** thing in the string, after the sentence. One link per change; if two pages are affected, link the main one.
- **Absolute URLs only.** The same string is shown in the app's release-notes window, on the
  published Release Notes page and anywhere else — a relative link or GitBook's `page:` form only
  works in one of those places. (A GitBook import silently drops site-relative links.)
- **Build the URL from the published site**, never guess it: `<publishedUrl>/<module-slug>/<page-slug>`
  is the usual GitBook shape, but GitBook appends `-1` on clashes and renames slugs. After the
  manual push, check each link returns 200 (`curl -sL -o /dev/null -w "%{http_code}" <url>`).
  A page that is new in this release must be **published first**, then linked.
- **Order when documenting:** edit the manual → push manual → verify the page URL → write the
  release note with the link → push release notes.
- No link when there is no user-facing page (internal fix, backend-only change). Never link to
  a page that does not exist yet just to have a link.
- The app's release-notes renderer must turn `[text](https://…)` into a link that opens in a new
  tab (and render only `http(s)` URLs). If a project's renderer only handles `**bold**`, extend it
  in the same change.

## CLAUDE.md — version tracking
The `### Current versions` block in `CLAUDE.md` must be updated on every bump:
```markdown
### Current versions (update after every bump)
- **Backend:** `X.Y.Z`
- **Frontend:** `X.Y.Z`
```

## The detailed changelog entry — NOT in CLAUDE.md

The long-form entry (Changes / Mechanism / Verified / Files Modified / Schema) goes in the
project's **changelog file**, never in `CLAUDE.md`.

`CLAUDE.md` is loaded into **every** session, and Claude Code caps that at **150,000 chars**.
Release history is reference read on demand, so it does not belong there — in the traceability-matrix
project it had grown to **313,180 chars, 76% of the file**, pushing it to 411 KB (2.8× the limit) and
burning ~100k tokens per session on history that was almost never relevant.

**Where the entry goes** — check the project's own convention first:
- **traceability-matrix:** `docs/changelog/CHANGELOG-v{major}.md`, prepended newest-first, **plus**
  its one-line row in `docs/changelog/README.md`
- otherwise: the repo's `CHANGELOG.md`, or create `docs/changelog/` following the above

**What stays in `CLAUDE.md`:** the `### Current versions` block, and — only when the release
uncovered a trap that fails *silently* — a new numbered **Critical Implementation Note**. That note
is the distilled, always-loaded form of what the changelog entry records at length. A release that
merely worked as intended adds no note.

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
- [ ] Each user-facing change ends with a verified `[Help: Page](https://…)` link to the manual page it affects
- [ ] Long-form entry prepended to the **changelog file** (`docs/changelog/CHANGELOG-vN.md`), **not** `CLAUDE.md`
- [ ] Its one-line row added to `docs/changelog/README.md`
- [ ] A new **Critical Note** in `CLAUDE.md` only if the release exposed a silent-failure trap
- [ ] `SCHEMA.md` updated if schema changed
