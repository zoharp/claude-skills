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
| *Why does an item have a different `ID` per version? What is a View / branch?* | **`orcanos-version-management.md`**, **`orcanos-database.md`** |
| *What fields does item type X have on this tenant?* | `orcanos-form-builder` (separate skill) |

## Files in this skill

| File | Covers |
|---|---|
| `orcanos-work-items.md` | The work-item model, the anatomy of an item, the identifier traps, and the catalogue of item types with their codes |
| `orcanos-platform-facts.md` | Platform facts for RFIs / CRS answers / security questionnaires: ISO 27001, AWS US hosting, SSO (SAML 2.0 / Google / Microsoft / AD) with MFA through the IdP, GLP + equipment configured, eMDR phased plan — each with source + date |
| `orcanos-database.md` | **The database underneath**: `objects` (physical rows, `ID`), `project_version` (Views), `objects_ver_view` (item × version: `original_id`, `action_type` DUPLICATE / UPD, `parent_original_id`) — worked example; explains ID vs Original_id and `Ver_Id` |
| `orcanos-version-management.md` | **Versions / baselines**: View = project + version, inheritance (smart pointers), item version label, Pool, Branch vs Save, Force Branch, freeze / lock, Cancel Branch, Move to View; rules for API code. Process: `orcanos-processes/orcanos-version-management-process.md` |
| `orcanos-documents.md` | Structured (DHF / ALM) documents: DOC → PAR/REQ_HD → traceable items, `Root_Document`, the pool, walking with `Get_Children`, done = IsActive ∧ IsComplete |
| `orcanos-smart-description.md` | **Description (`obj_description`) is a smart template**: rich text with embedded form fields (`<a name="FIELD_<code>">`) and filters (`<a name="FILTER_<id>" obj-type version_id>`), rendered to values in review / print mode, names in edit mode — never show / parse / rewrite the raw template |
| *(DMS items)* | Controlled documents: **Routing State, never Status**; revisions, ECO per revision, Training section — see `orcanos-processes/orcanos-document-control-process.md` |
| `orcanos-work-item-list-automation.md` | **A list field based on work items** (Work Item List Automation → system table): the DB stores the item **ID** (code), the form shows First Field (+ Second Field), e.g. `25937-Test supplier`; filters return the shown text — map it to the ID through the form's `val[]` |
| `orcanos-supplier.md` | Supplier work items in QMS E-Forms: **Supplier** (`SUPLR-`, form fields live), **SCAR** (`SCAR`, intended fields/statuses), **Action Item** (`ACTION_ITEM`, Category = corrective / preventive, created under the SCAR); no review-interval field; open API unknowns. Process: `orcanos-processes/orcanos-supplier-process.md` |

## Planned — one file per module / process

Each will hold the workflow, the states, the roles, and the item types involved:

`training.md` · `document-control.md` · `capa.md` · `complaints.md` · `risk.md` ·
`requirements.md` · `test.md` · `change-control.md` · `audit.md` · ~~`supplier.md`~~ → written as `orcanos-supplier.md` (2026-11-12)

> When adding one, add a row above and link it from the relevant catalogue entries in
> `orcanos-work-items.md`.

---

## The one rule for this skill family

**Never write a code into these files from memory or inference alone.** Every item-type code must be
either (a) read from a live `QW_Login` response, (b) observed in shipped working code, or
(c) supplied by the product owner. Anything else is marked as unconfirmed and says so out loud.

A wrong code does not raise an error in Orcanos — it returns an empty result, which reads as
"no data" and ships as a silent bug. The catalogue's confidence column exists for exactly this reason.
