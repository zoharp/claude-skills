---
name: req-gap-check
description: Scan all source files and report which have no linked requirement.
revision: 1.0.0
---

# req-gap-check

## When to use
Before an audit, milestone review, or release — to get a full picture of traceability coverage.

## What to do

1. Read `compliance.json` for `source_paths`
2. Read `requirements/_index.json` — build a set of all files referenced in `source_refs`
3. List all files under `source_paths` in the repo
4. Compare — find files with no REQ reference at all
5. For each untraced file, assign risk level:
   - **HIGH**: auth, encryption, search pipeline, routing, account isolation
   - **MEDIUM**: API endpoints, UI components with data
   - **LOW**: config, static assets, utility helpers
6. Report:
   - Coverage % (files with ≥1 REQ / total files)
   - HIGH risk gaps first
   - Full table at the end

## Output format
Markdown report with summary stats at the top.
