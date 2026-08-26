---
name: Orcanos-infra
description: How Orcanos is built underneath — work items, item types, modules and processes. The conceptual model behind the API. Start here to understand WHAT an Orcanos object is; use orcanos-api for HOW to call it.
revision: 1.0.0
---

# Orcanos Infrastructure — Router

This skill family describes **what Orcanos is made of**. It is the conceptual layer beneath
`orcanos-api`, which describes *how to call* it.

| Question | Skill |
|---|---|
| *What is a work item? What types exist? What does code `TRN_TASK` mean?* | **`orcanos-work-items.md`** |
| *How do I call `QW_Login` / `QW_Add_Object` / filters?* | `orcanos-api` (separate skill) |
| *What fields does item type X have on this tenant?* | `orcanos-form-builder` (separate skill) |

## Files in this skill

| File | Covers |
|---|---|
| `orcanos-work-items.md` | The work-item model, the anatomy of an item, the identifier traps, and the catalogue of item types with their codes |

## Planned — one file per module / process

Each will hold the workflow, the states, the roles, and the item types involved:

`training.md` · `document-control.md` · `capa.md` · `complaints.md` · `risk.md` ·
`requirements.md` · `test.md` · `change-control.md` · `audit.md` · `supplier.md`

> When adding one, add a row above and link it from the relevant catalogue entries in
> `orcanos-work-items.md`.

---

## The one rule for this skill family

**Never write a code into these files from memory or inference alone.** Every item-type code must be
either (a) read from a live `QW_Login` response, (b) observed in shipped working code, or
(c) supplied by the product owner. Anything else is marked as unconfirmed and says so out loud.

A wrong code does not raise an error in Orcanos — it returns an empty result, which reads as
"no data" and ships as a silent bug. The catalogue's confidence column exists for exactly this reason.
