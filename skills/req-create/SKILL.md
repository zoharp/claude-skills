---
name: req-create
description: Create an IEC 62304 software requirement from a feature description or code change.
---

# req-create

## When to use
When a developer has built something new and needs a formal IEC 62304 requirement created for it.

## What to do

1. Read `requirements/_index.json` to find the next available REQ ID
2. Read `compliance.json` for project context and safety class default
3. Generate the requirement in this format:
   - `id`: next REQ-NNN
   - `title`: short imperative (max 80 chars)
   - `description`: must start with "The system shall"
   - `rationale`: why this exists
   - `safety_class`: A | B (default) | C (only if risk control or direct patient data)
   - `source_refs`: file, symbol, role (implementation | caller | spec | test)
   - `verification_method`: specific — name the test type and what it asserts
4. Write the REQ-NNN.md file to `/requirements/` using the format in any existing REQ file as template
5. Add the entry to `_index.json`
6. Report: REQ ID created, Orcanos sync will happen on next deploy

## Do not
- Create a requirement for trivial changes (config tweaks, style fixes, logging)
- Use vague verification methods like "manual testing"
- Set safety class C unless the feature directly handles risk scoring or patient data
