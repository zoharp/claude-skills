---
name: orcanos-document-control-process
description: How a controlled document (DMS item) moves through Orcanos — Routing State is THE state (never Status), the seven routing states and what moves between them, revisions, ECO release (Pending Approved), the item's Training section, and where Doc Review fits.
revision: 1.0.0
---

# Document Control (DMS) — process

Source: product owner (2026-11-13, with screenshots of a DMS item's *Revisions* and *Overview → Training*),
plus live orca60 reads recorded in `orcanos-api/get-section-data/section-revisions.md` and
`orcanos-training-process.md` Trap 3.

## 1. Routing State is the state — Status is not used

A DMS item has an `Obj_status` field, but **document control does not use it**. Every question about
where a document stands — draft, signing, released, obsolete — is answered by its **Routing State**:

- on the item (filter column): `DMS_Routing_State` (title *Routing State*), the **current** revision's state;
- per revision: `Routing_State` in the item's *Revisions* section (`section-revisions.md`).

Never show, filter, count or colour DMS items by `Status`. A screen that says "Status" for a document
means Routing State.

## 2. The seven routing states

| Routing State (as shown) | Live value | Meaning | How it gets there |
|---|---|---|---|
| **Draft** | `Draft` | New revision, not yet sent for signature | File uploaded / new revision created |
| **In Work** | `In Work` | Under the e-signature process | Routing (e-sign) started |
| **Approved** | `Approved` | Signed **and released** — the effective revision | Last signer signs (no ECO), or its ECO is released |
| **Pending Approved** | `Pending Approve` (live orca60; the Revisions section may spell it `Pending Approved`) | Signed, but part of an **ECO** — approved, **not yet released** | Last signer signs while the revision belongs to an ECO. Turns **Approved automatically** when the ECO is released |
| **Obsolete** | `Obsolete` | No longer in use | An explicit *obsolete* action, **or automatically** when a newer revision becomes Approved (the previous one becomes Obsolete) |
| **Cancelled** | `Cancel` | E-sign was started and the process was cancelled midway | Routing cancelled |
| **Reject** | `Reject` | A signer rejected the signature | A signer rejects |

Rules that follow:

- **The effective document = the revision whose Routing State is `Approved`.** `Pending Approved` is
  signed but must not be presented as released.
- A superseded revision is told by `Routing_State === 'Obsolete'` — **never** `is_obsolete` (observed empty).
- `Cancel` / `Reject` revisions are dead ends — a new revision (or re-routing) follows.
- Orcanos colours each state (`color_code` per revision row: `#97E0AC` approved, `#C4C0C6` obsolete) — reuse it.
- The live spelling of *Cancelled* is `Cancel` (seen in 1031 TRN tasks, Trap 3). Match labels
  case-insensitively and map both spellings.

## 3. Revisions

The *Revisions* tab lists every file version: Name, Description (change reason), Created Date, Type,
**Revision** (letter) + **Change #** (minor change within it — `(Revision, Change_no)` identifies a row),
Routing State, Document #, **Approved Date**, File Size, and per row: View PDF, Download for edit,
details. The header shows **Current Revision** as `C-1` (= Revision C, Change 1).
Drag & drop a file = a new revision. Field list and traps: `orcanos-api/get-section-data/section-revisions.md`.

**Where a DMS item lives (live orca60, 2026-11-13):** project → **DMS Workspace** (`WrkSpc`) / **DMS Folder** (`FOLDER`) →
… → DMS item; folders also sit under **DHF** and **DMR** items. A filter row's `Parent_name` names the parent
(`FOLDER-26624: DMS_F-9865 02 Design Controls`). `Get_Children` on a project fails (see `orcanos-api/get-children.md` 4b).

## 4. ECO on a revision

A revision released through an **ECO** (Engineering Change Order) carries the ECO on its row — all empty
otherwise:

| Column | Title |
|---|---|
| `eco_no` | ECO Number (link to the ECO) |
| `eco_status` | Related ECO Status (e.g. *Released*) |
| `eco_routing_state` | Related ECO Routing State (e.g. *Approved*) |
| `eco_release_date` | ECO Release Date |
| `eco_action_type` | ECO Action Type (add / change / obsolete) |

A revision in `Pending Approved` is waiting for its ECO: show the ECO and its routing state beside it.
The ECO's own item list: `eco_items` by `eco_no` (traceability-matrix Note #60).

## 5. Training on a DMS item (Overview → Training)

| Field | Meaning | Show it? |
|---|---|---|
| **Training List** | Holds a **default TRN record for everyone** (e.g. `21075-Read and Understand`), used only by the automation that creates Read-and-Understand tasks when the document is released | **No** — plumbing, not information |
| **Roles** | Roles that must train on this document | Yes |
| **Trainees** | Named people who must train on it | Yes |

Audience = `Roles` ∪ `Trainees` (traceability-matrix Note #44). The tasks themselves and their signed
state: `orcanos-training-process.md` (signed ⟺ the TRN task's `DMS_Routing_State == "Approved"`).

## 6. Other tabs

*Attachments*, *History*, *Discussion*, *Traceability*, *ESign* (signers + signature details) — plus
Overview sections *E-sign Details* and *Signers Details*. Header actions: *Start Review* (Doc Review),
*Launch Training* (only with an approved revision).

## 7. Doc Review (our tool)

Doc Review (traceability-matrix module) reviews a **Draft** revision before routing; its rounds and
comments live in our DB (`review_events`, Note #84), not in Orcanos. A document view can list them
per revision; starting one needs the DMS `X` (Start Routing) letter (Note #82).

## 8. Where this is used

traceability-matrix **Document Control** (QMS, 2026-11-13; `design/docs/DOC_CONTROL.md`, Note #132): libraries of
projects / a solution + a main DMS filter + a Folders filter; folder tree from `Parent_name` (see
`orcanos-api/get-children.md` 4b); DMS item view = Revisions section (+ ECO columns) + `QW_Get_Object_View` (Roles, Trainees)
+ Doc Review rounds; revision file through `download-attachment.md`.

## See also

- `orcanos-api/get-section-data/section-revisions.md` — Revisions section fields
- `orcanos-api/filter-result-fields.md` — `DMS_Routing_State`, `DMS_Routing_End_Date` (Approved Date)
- `orcanos-processes/orcanos-training-process.md` — R&U automation, Trap 3
- `orcanos-api/get-section-data/download-attachment.md` / `view-attachment-url.md` — the file, per routing state
