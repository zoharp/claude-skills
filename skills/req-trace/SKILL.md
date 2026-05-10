---
name: req-trace
description: Trace a source file or function to its linked requirements, and identify gaps.
---

# req-trace

## When to use
After adding or refactoring code, to check what requirements cover it and whether any traceability links are missing.

## What to do

1. Read `requirements/_index.json`
2. Find all REQs where `source_refs` contains the given file or symbol
3. Read the source file and identify its key functions/classes
4. Compare: which symbols have a REQ link, which don't
5. Report in three sections:
   - **Existing traceability** — table of REQ ID | title | symbol traced
   - **Gaps** — untraced symbols with suggested action (extend existing REQ or create new)
   - **Recommended actions** — ordered list of what to do next

## Output format
Markdown report. Be specific about symbol names — not just "the file" but the actual function.
