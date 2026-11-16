# Orcanos Supplier work items — Supplier, SCAR, Action Item

**What** the supplier-related work items are, where they live and which fields matter.
**Part of:** `Orcanos-infra` · **Process:** `orcanos-processes/orcanos-supplier-process.md` · **API:** `orcanos-api`

> Sources: **[LIVE]** orca60 tenant, 2026-11-12 (forms read, project tree seen) · **[PO]** product owner
> decisions, 2026-11-12 · **[DESIGN]** traceability-matrix `design/DESIGN_SUPPLIER_PORTAL.md` (design only)
> · **[CODE]** traceability-matrix `src/backend/supplier_portal_map.py` (field roles + status matching).
> Anything not marked verified live is a design intent or unverified — say so when you use it.

---

## 1. Where they live — the QMS E-Forms project

| Fact | Conf. |
|---|---|
| Every account has a project named **"QMS E-Forms"** — the **same name everywhere**, so find it **by name** from `QW_Login`, never by id. | ✅ verified live (orca60) + 📌 PO |
| Its tree folders include **Complaints, Non Conformities, CAPA, Change Control, Audits, Suppliers, Archive, Deviations**. | ✅ verified live |
| Supplier items sit in the **Suppliers** folder. | ✅ verified live |
| SCARs are meant to get their own **SCARs** folder beside Suppliers / Non Conformities / CAPA. | ◐ design (D3) — not seen live |

Folders are themselves work items (`Folder`, see `orcanos-work-items.md` §4.7) — the tree is containment,
not traceability.

---

## 2. The three types

| Code | Type | Key prefix | What it represents | Conf. |
|---|---|---|---|---|
| — (prefix `SUPLR`) | **Supplier** | `SUPLR-` (e.g. `SUPLR-21950`) | One approved / candidate supplier: who they are, what they provide, how critical they are, their certificate and audit state, and the review date. The record quality reviews periodically. | ✅ prefix verified live; **original code not read** — take it from `QW_Login` (code matcher tries `SUPLR`, `SUPPLIER`, `SUP`, then label "Supplier"/"Vendor") |
| `SCAR` | **SCAR** — Supplier Corrective Action Request | `SCAR-` | A request to a supplier to contain, find the root cause of and fix a nonconformity in what they supplied. Usually raised from an NCR. | ✅ type added to QMS E-Forms by the user, 2026-11-12. Live fields: see §4a. |
| `ACTION_ITEM` | **Action Item** | — | A single action with a category, due date and status. Used as the **corrective / preventive actions of a SCAR**, created **under** the SCAR. | ✅ verified live (label "Action Item", QMS E-Forms version 1.0) |

> **Also in Orcanos:** separate **Corrective Action** and **Preventive Action** work item types exist
> (the CAPA family). For SCAR actions the product owner chose **Action Items under the SCAR** instead
> (D17). Don't mix the two when reading a SCAR's actions.

---

## 3. Supplier — the form [LIVE orca60, 2026-11-12]

Sections **Overview / General information / Quality Review**. Tabs: Overview, Record, Attachments,
History, Discussion, Traceability, Defects.

⚠️ The **Description** (Record tab) is a smart template — a print layout of the form fields + an annual-reviews filter, not text. Never show it raw: `orcanos-smart-description.md`.

| Area | Field titles |
|---|---|
| Identity | Manufacturer · Vendor Name · Product/Service provided · Created By · Assigned To |
| Contact | Contact Name · Address · Telephone · email address |
| Criticality | Quality impact rank of part/service on product · Final product risk severity · Critical Supplier (checkbox) |
| Approval | **Approval Status** — workflow field (e.g. "Under Review"), has **Start Routing** · **Last Reviewed Date** |
| Quality system | Supplier Quality System · Quality Certification type and number · **ISO cert validity** |
| Audit | Audit Approval · Audit approval date · Next Audit Date |
| Agreement | Quality agreement applicable? · quality agreement status · Quality agreement signed date |

**Traps**

1. **Every customer's Supplier form differs.** Match fields **by TITLE** (same name → similar name →
   ask), never by a hard-coded field id. Titles are not even consistently cased (`email address`).
   The role → title lists the portal uses are in `supplier_portal_map.py` `ROLES["supplier"]`.
2. **There is NO review-interval field** on the orca60 form. The next review is **computed**:
   `Next review = Last Reviewed Date + interval`. The Supplier Portal keeps the interval per category
   (e.g. Critical 365 d, Major 730 d, Minor 1095 d — design D13); an interval field on a customer's
   form, if one exists, wins.
3. **Next Audit Date ≠ next review.** The audit date is its own field; the periodic review is driven
   by Last Reviewed Date.
4. **Approval Status is a workflow field** with routing — setting it may need a status transition /
   e-signature, not a plain field write (see `orcanos-workflow-chart`, `orcanos-api/qw-update-item.md`).
5. **What the Supplier Portal's annual review writes on close** (traceability-matrix Phase 4, 2026-11-13,
   `supplier_portal_review.py`, fakes only): as the portal's service user, one `QW_Update_Object` on the
   Supplier item — **Last Reviewed Date** = today (`YYYY-MM-DD`), **Approval Status** = the review result
   through the Supplier value map (Approved / Approved with conditions / Not approved; an unmapped value is
   NOT written — the portal never adds list values), and an optional mapped **Review score** (0-100 %) — then
   reads the form back and lists what did not stick. The answers go on as a PDF via `Add_Attachment` OBJECT.
   Because of trap 4, the Approval Status write is the first thing to check live.

---

## 4. SCAR — intended fields and statuses [DESIGN §1]

⚠️ The user created the type on orca60 on 2026-11-12, but its **live field titles and status names
have not been recorded**. The table below is what the design asked for; read the real form
(`QW_Get_Item_Add_Edit`, item 0) before relying on any title.

| Step | Fields | Filled by |
|---|---|---|
| 1 · Problem | Supplier (link / picklist to the Supplier item) · Part · Lot / batch · Quantity affected · Defect description (rich text) · Severity (Critical / Major / Minor) · Containment due date · Root cause due date | Quality |
| 2 · Containment | Containment actions (rich text) · Stock at supplier · Stock in transit · Shipped parts disposition (Replace / Sort at customer / None shipped) · Containment date | Supplier |
| 3 · Root cause + action | Root cause · Why not detected · *Actions = Action Items under the SCAR (§5)* | Supplier |
| 4 · Effectiveness | Effectiveness check method · Effectiveness result (Effective / Not effective) · Closed date | Quality |

Required to switch the portal on: Supplier, Defect description, Severity, Root cause, Effectiveness result.

**Statuses (design):** Draft → Sent to supplier → Containment submitted → Root cause submitted →
Effectiveness check → Closed. *Return* moves back one. The customer's own status names are mapped to
these steps (two steps may share one status). Process detail: `orcanos-supplier-process.md`.

**Relations (design):** NCR → SCAR (trace) · SCAR → CAPA (trace, optional) · SCAR → Action Items
(**children**, containment tree — not traces) · evidence files on the SCAR's Attachments tab.
Whether these traces / this parent-child pair are **allowed** in the tenant's settings is not yet confirmed.

---


### 4a. SCAR form on orca60 — live (QW_Get_Item_Add_Edit item 0 + filter 877, 2026-11-13)

Fields (title — code): Name, Description, Status, Assigned To, Category, Part Catalog Master (CS386), Lot # (CS79),
**Supplier Name (CS315, combobox, write col `CS2_Name`)**, Root Cause Due Date (CS148), Quantity (CS115), Case Description
(CS73), Severity Level (CS307), Containment date (CS150), Stock In Transit (CS227), Shipped parts disposition (CS415),
Containment actions (CS416), Containment Due Date (CS149), Stock At Supplier (CS226), Root Cause Analysis (CS317),
Effectiveness Check Due Date (CS135), Effectiveness Evaluation Results (CS93), Effectiveness Evaluation Description (CS80).
Statuses seen: New, Containment submitted.

**Supplier Name** is a *Work Item List Automation* list (`orcanos-work-item-list-automation.md`): options
`{code: "25937", label: "25937-Test supplier"}`, `{code: "0", label: "Not Set"}` — code = the Supplier item ID. A filter
returns the label only, and **only if it selects the column** (filter 877 did not → empty).

## 5. Action Item — the form [LIVE orca60, 2026-11-12]

Code `ACTION_ITEM`, label "Action Item". Fields: **Name**, **Description**, **Category** (picklist —
values include **"Corrective Actions"** and **"Preventive Action"**; note the plural / singular
mismatch, match values by similarity), **Due Date**, and a **completion date**.

| Rule | Conf. |
|---|---|
| A SCAR's corrective / preventive actions are Action Items created **under the SCAR** (child). Being under a SCAR is what makes it a supplier action. | 📌 PO 2026-11-12 |
| **Category** tells corrective vs preventive. If a tenant's form has no such field, the kind goes into the name (`[CA] …` / `[PA] …`). | ✅ field live · 📌 fallback is design |
| **Never write the completion date.** Orcanos fills it itself when the item moves to a status with `IsComplete = 1`. Mark an action done by setting its **status** (`orcanos-api/get-item-statuses.md` rule 9). | ✅ PO rule; the stamping itself is product behaviour as stated by the PO |
| No verification field on the action — whether the actions worked is checked on the SCAR (step 4). | 📌 design |

---

## 6. Open / unverified — do not build on these without a live probe

| Unknown | Why it matters | State |
|---|---|---|
| **Creating an item UNDER a parent** through the API | Action Items must be children of the SCAR | ❓ Setting `Parent_ID` with `QW_Update_Object` answered **success but did not move the item** (traceability-matrix Critical Note #118). An item counts as a child only when `Get_Children` of the SCAR returns it. |
| `Add_Attachment` with `Object_Type = OBJECT` | Evidence files, review PDF | ❓ unverified (Critical Note #111) |
| Setting a SCAR **status** through the API (transition vs field write) | "Sent to supplier", Accept, Return | ❓ unverified |
| SCAR live field titles / status names; Supplier original code | Mapping | ❓ not recorded |
| NCR → SCAR, SCAR → CAPA traces and Action Item as a SCAR child allowed in the tenant | Structure | ❓ not confirmed |
| Writing **Approval Status** (a workflow field) and **Last Reviewed Date** with a plain `QW_Update_Object` | The annual review's close (Phase 4) | ❓ not run live — the portal reads back and reports a value that did not stick |

---

## See also

- `orcanos-work-item-list-automation.md` — the SCAR's **Supplier** field is a list on a Work Item List Automation table: stored = the supplier's item ID, shown = e.g. `25937-Test supplier` (live orca60, 2026-11-12)

- `orcanos-smart-description.md` — the Supplier Description is a **print template** (embedded `FIELD_` / `FILTER_` anchors, e.g. the annual-reviews filter `FILTER_805` obj-type `SAR`); the portal hides it
- `orcanos-processes/orcanos-supplier-process.md` — approval, periodic review, SCAR lifecycle, actions, certificates
- `orcanos-work-items.md` — the catalogue and identifier traps
- `orcanos-api/get-item-statuses.md` — `IsComplete` and the completion date (rule 9)
- `orcanos-api/qw-get-item-add-edit.md` — reading a type's live form (match fields by title)
- `orcanos-api/get-children.md` — reading a SCAR's Action Items
- `orcanos-api/add-attachment.md` — evidence files (OBJECT unverified)
- traceability-matrix `design/DESIGN_SUPPLIER_PORTAL.md` + `src/backend/supplier_portal_map.py` — the Supplier Portal that uses these items
