---
name: req-trace
description: Trace a source file or function to its linked requirements, and identify gaps.
revision: 1.0.0
---

# req-trace — Requirement Traceability Analysis

**Business logic:** Traces source code to requirements, identifies gaps.  
**Technical sync:** See [orcanos-api QW_Add_Trace](../orcanos-api/qw-add-trace.md) for syncing traceability to Orcanos.

## When to use
- **Automatically** after every code change to `backend/` or `frontend/src/` — run on each modified file before the task is considered done.
- After adding or refactoring code, to check what requirements cover it and whether any traceability links are missing.
- When a REQ REMINDER is shown by the Stop hook.

## What to do

1. Read `requirements/_index.json`
2. Find all REQs where `source_refs` contains the given file or symbol
3. Read the source file and identify its key functions/classes
4. Compare: which symbols have a REQ link, which don't
5. Report in three sections:
   - **Existing traceability** — table of REQ ID | title | symbol traced
   - **Gaps** — untraced symbols with suggested action (extend existing REQ or create new)
   - **Recommended actions** — ordered list of what to do next
6. **Sync to Orcanos** (if configured): Use [QW_Add_Trace](../orcanos-api/qw-add-trace.md) to create traceability links in Orcanos

## Output format
Markdown report. Be specific about symbol names — not just "the file" but the actual function.

## See also
- [[req-create]] — Create IEC 62304 requirements (business logic)
- [QW_Add_Trace](../orcanos-api/qw-add-trace.md) — Technical API call to sync traceability to Orcanos
