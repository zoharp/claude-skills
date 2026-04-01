---
name: release-management
description: Use after every code change that requires version bumping or release notes. Handles backend/frontend versioning rules, version file locations, and release_notes.json updates. Invoke when committing, releasing, or asked about versioning.
---

# Release Management

## After every code change, always:
1. Bump the version in the changed component(s)
2. Update `release_notes.json` — prepend new entry, most recent first

## Bump rules
- Backend-only change → bump backend patch only
- Frontend-only change → bump frontend patch only
- Both changed → bump both
- **Patch**: bug fix / tweak
- **Minor**: new feature
- **Major**: breaking change / schema change

## Version file locations

| Component | File | Field / Notes |
|---|---|---|
| Backend | `backend/api.py` | Version string appears 3x — use `replace_all=true` |
| Frontend | `frontend/package.json` | `"version"` field |
| Frontend | `frontend/src/App.jsx` | `const FE_VERSION = '...'` (~line 16) |

> `package.json` and `App.jsx` **must always match** — update both together.

## release_notes.json format
```json
[
  {
    "version": "1.7.0",
    "date": "2025-01-15",
    "changes": [
      "Added feature X",
      "Fixed bug Y"
    ]
  }
]
```
Prepend — newest entry first.

## Checklist before committing
- [ ] Version bumped in all relevant files
- [ ] `package.json` and `App.jsx` versions match (if frontend changed)
- [ ] `release_notes.json` updated with new entry
- [ ] Current versions noted in `CLAUDE.md` updated
