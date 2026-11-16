---
name: orcanos-database
description: The Orcanos MVC database underneath the API — the objects / project_version / objects_ver_view tables, how one logical item (original_id) maps to physical object rows (ID) per version (view_version), and what DUPLICATE / UPD / parent_original_id mean. Read before reasoning about ID vs Original_id, Ver_Id, branching or tree parents.
revision: 1.0.0
---

# Orcanos Database — objects, versions and the version view

How the Orcanos server stores work items and project versions. The API (`orcanos-api`) exposes these
tables through `ID`, `Original_id`, `Ver_Id`, `Parent_original_id` — this page says where they come from.

> **Source:** product owner, document *"Orcanos Database - Objects and Versions Management"* (2026-11-15) —
> 📌 given, worked example below copied from it. Behaviour rules: KB article
> https://help.orcanos.com/knowledgebase/version-baseline-management (read 2026-11-15).
> **Not read from a live database.** Column lists are the ones the example shows, not the full schema.
> Concepts + user-facing rules: `orcanos-version-management.md`. Process: `orcanos-processes/orcanos-version-management-process.md`.

Confidence marks: 📌 given by the product owner · 📖 KB article · ✅ seen live through the API · ❓ inferred, unconfirmed.

---

## 1. The three tables

| Table | One row per | Key columns (as given) | Conf. |
|---|---|---|---|
| **`objects`** | **physical** item record — every project, item and every *branch* of an item | `ID` (identity, PK), `obj_name`, `obj_type` (`PROJECT`, `TASK`, …), `Project` (→ `objects.ID` of the PROJECT row) | 📌 |
| **`project_version`** | version (= "View") of a project | `version_id` (PK), `proejct_id` (→ `objects.ID` of the PROJECT; spelled so in the source — ❓ real column name), `ver_major`, `ver_minor` | 📌 |
| **`objects_ver_view`** | **(logical item × version)** — which physical row represents the item in that version, and where it sits in the tree | `Id` (→ `objects.ID`), `view_version` (→ `project_version.version_id`), `original_id`, `action_type`, `parent_original_id` | 📌 |

Other columns referenced elsewhere in the API (`obj_description` — see `orcanos-smart-description.md`) live on
`objects` too; the full column list is not documented here yet.

### The two identities

| Name | Meaning | Changes when… | API field |
|---|---|---|---|
| **`objects.ID`** (= `objects_ver_view.Id`) | the physical record | the item is **branched** (a new `objects` row is inserted) | `ID`; the number in `Key` `DOC-16278 (8467)` before the brackets |
| **`original_id`** | the logical item, stable across all versions | never | `Original_id`; the number in brackets in `Key` |

An item that was never branched has `ID = original_id` in every version. ✅ Matches the live API:
DOC original `8467` = `ID 16278` in version 434 (orca60, 2026-10-27, `orcanos-documents.md` §3).

### `action_type`

| Value | Meaning | Conf. |
|---|---|---|
| *(empty)* | the item was **created in this version** (new row in `objects`) | 📌 |
| `DUPLICATE` | **inherited** — a pointer to the same physical row as the previous version ("smart pointer" in the KB). No new `objects` row; content is shared. | 📌 |
| `UPD` | **branched in this version** — `Id` points at a NEW `objects` row; the previous version keeps the old row | 📌 |
| *(the PROJECT row in a new version)* | shown as `?` in the source — unknown | ❓ |
| delete / *Move to view* / *Cancel branch* | not in the example — values unknown | ❓ |

### `parent_original_id`

The tree parent, stored as the parent's **ORIGINAL id**, never its physical `ID`. That is why a child
stays under its parent after the parent branches (§2, step 5: R3 keeps `parent_original_id 3` while R2's
physical row becomes 5). Same reason `Root_Document` holds the DOC's original id. 📌 + ✅ (API side)

---

## 2. Worked example (verbatim from the source, annotated)

### Step 1 — new project P1
`objects`: `1 | P1 | PROJECT` · `project_version`: `10 | 1 | 1 | 0` (version 1.0) ·
`objects_ver_view`: `1 | 10 | 1 | | ` — the project itself has a view row.

### Step 2 — add R1, R2 under P1 (in 1.0)

| objects.ID | obj_name | obj_type | Project |
|---|---|---|---|
| 1 | P1 | PROJECT | |
| 2 | R1 | TASK | 1 |
| 3 | R2 | TASK | 1 |

| Id | view_version | original_id | action_type | parent_original_id |
|---|---|---|---|---|
| 1 | 10 | 1 | | |
| 2 | 10 | 2 | | 1 |
| 3 | 10 | 3 | | 1 |

Tree: `P1 (1.0) › R1 (1.0), R2 (1.0)`

### Step 3 — admin opens version 2.0
`project_version` gets `20 | 1 | 2 | 0`. **No `objects` rows are copied** — only view rows:

| Id | view_version | original_id | action_type | parent_original_id |
|---|---|---|---|---|
| 1 | 20 | 1 | | |
| 2 | 20 | 2 | DUPLICATE | 1 |
| 3 | 20 | 3 | DUPLICATE | 1 |

Logged in to 2.0: `P1 (2.0) › R1 (1.0), R2 (1.0)` — the label is the version the **physical row** was
created in, so inherited items still read 1.0.

### Step 4 — add R3 under R2, in 2.0
`objects` row `4 | R3 | TASK | 1`; view row `4 | 20 | 4 | | 3` (no row in version 10 — R3 does not exist in 1.0).
Tree in 2.0: `P1 (2.0) › R1 (1.0), R2 (1.0) › R3 (2.0)`.

### Step 5 — edit R2 in 2.0 and choose **Branch**
- New `objects` row **5** (a copy of R2 with the change).
- In version 20 the view row `3 | 20 | 3 | DUPLICATE | 1` is **replaced** by `5 | 20 | 3 | UPD | 1`.
- Version 10 still points at row 3 — 1.0 content is unchanged.
- R3's `parent_original_id` stays **3** → still under R2.

Tree in 2.0: `P1 (2.0) › R1 (1.0), R2 (2.0) › R3 (2.0)`

> ⚠️ **Typo in the source:** the new `objects` row 5 is named `R3’`, but it is R2's branch — its view row
> carries `original_id 3` (R2) and the tree shows R2 at 2.0. Read it as `R2’`.

---

## 3. What this explains in the API (traps we already hit)

| API behaviour (✅ live) | Database reason |
|---|---|
| A branched item has a different `ID` per version; `Root_Document` / `Parent_original_id` hold the original | branch = new `objects` row; parents and documents point at `original_id` |
| `Get_Children/<ID>` needs the item's `ID` **in that version**, and `?Ver_Id=` (404 without it) | the tree is read from `objects_ver_view` rows of one `view_version` |
| `Get_Children` passed an **original** id of a branched item → 200 `"Item not found."` | no view row in that version has `Id = original` (it has `Id = 5`, not 3) |
| A child's own `Ver_Id` can be an OLDER version (332 under a 434 parent) | an inherited (`DUPLICATE`) row's physical record was created in the older version — the "version label" |
| Reading an inherited node in its own older `Ver_Id` misses children added later | children added in 2.0 have view rows only in version 20 (R3 has no row in 10) |
| The same `objects.ID` answers in several versions | `DUPLICATE` rows share the physical record |

## 4. Open questions — confirm before code relies on them

- ❓ `action_type` for a delete in a version, *Move to view*, *Cancel branch*, the PROJECT row of a new version.
- ❓ Pool items (no version): do they have any `objects_ver_view` row? (KB: they are in no View and have no hierarchy.)
- ❓ Where *frozen* / *locked* / *active* flags of a version live (likely `project_version`) and the real column names.
- ❓ How traces (`QW_Add_Trace`) reference items — physical `ID` or `original_id` — and whether a branch copies them.
- ❓ Whether a second branch in a later version (1.1 → 1.3, KB *Cancel Branch*) chains `UPD` rows per version.
