---
name: orcanos-version-management
description: Orcanos project versions (Views), baselines, the Pool, inheritance, Branch vs Save, freeze / lock, Force Branch, Cancel Branch and Move to View — the user-facing rules and how they map to the database and the API (ID vs Original_id, Ver_Id, item version labels).
revision: 1.0.0
---

# Orcanos Version (Baseline) Management

> **Sources:** KB *Version (Baseline) Management* https://help.orcanos.com/knowledgebase/version-baseline-management
> (read 2026-11-15) 📖 · product owner DB example (2026-11-15) 📌 → `orcanos-database.md` · live API ✅ where marked.
> Step-by-step admin process + planning use cases: `orcanos-processes/orcanos-version-management-process.md`.

## 1. Concepts

| Term | Meaning | Conf. |
|---|---|---|
| **View** | project **+** version (e.g. *Cardiology Monitor 5.6*). Every login, filter and tree read is in one View. A row in `project_version`; its id is the API's `Ver_id` / `Version_id` / `Ver_Id`. | 📖 📌 |
| **Version number** | Major.Minor.Release.Build. A View uses 2 digits (5.6) or 3 (5.6.1). 2 → 3 digits is allowed, never back. The first digits of the login version identify the baseline and can't be edited. | 📖 |
| **Baseline** | the state of a version. Opening the next version starts from the previous baseline. | 📖 |
| **Inheritance ("smart pointers")** | a new version copies **no content** — every item is a pointer to the previous version's record (`DUPLICATE` row) until it changes. | 📖 📌 |
| **Item version label** | the version in which the item was created or last **branched**, shown next to it in the product tree (R2 *(1.0)* while inherited, *(2.0)* after a branch). The API shows it as a child's own `Ver_Id` (✅ `Get_Children`: a 332 child under a 434 parent). | 📖 📌 ✅ |
| **Pool (Backlog)** | items created in the *Work Items* view that are in **no** version: not in the product tree, no hierarchy. Items can move Pool ⇄ View. **A branched item can't go to the Pool.** (Not the same as the DHF "pool" = no `Root_Document`, `orcanos-documents.md`.) | 📖 |

## 2. What happens to items when a new version opens

Example: 1.0 has two requirements; admin opens 2.0.

| Action | Result | DB (`orcanos-database.md`) |
|---|---|---|
| Open 2.0, change nothing | 2.0 shows the same items, labels still *1.0* | `DUPLICATE` view rows, no new `objects` |
| Create an item in 2.0 | exists only in 2.0 (and later versions), label *2.0* | new `objects` row, view row only in 2.0+ |
| Edit a 1.0 item logged into 2.0 → **Branch** | item becomes *2.0*; 1.0 content unchanged | new `objects` row, 2.0 view row → `UPD` |
| Edit a 1.0 item logged into 2.0 → **Save** | item changes **in place** — also in 1.0, stays labelled *1.0* | same physical row updated ❓ |
| 3.0 opened while 2.0 is still open | changes in 2.0 **flow into 3.0** (3.0 still points at them); changes in 3.0 follow the same add / branch rules | 📖 |
| Edit in 3.0 and save to 2.0 instead of branching | updates the item in both 2.0 and 3.0; **if 2.0 is locked, a branch is forced** | 📖 |

## 3. Branch vs Save — who gets the choice

1. Project option **Allow Branch on Change** must be on — otherwise there is no branching at all. 📖
2. **Previous version locked** → only **Force Branch** (no Save). 📖
3. **Previous version unlocked but inactive** → user chooses Save or Branch. 📖
4. Group permission **Force Branch [Work Item]** (per work item type, *Admin → Project → Groups*) → always branch,
   so the previous version's data never changes. 📖

## 4. Version states and admin actions

*Admin → Project → Versions*: open a new version · edit the version number/label · **lock** a version for login ·
**freeze** a version (no further changes) · hide / disable (enable) a version · delete a version. 📖
Which users may work in which versions: *Admin → Project → Groups*. 📖

| State | Effect |
|---|---|
| **Frozen** | no changes at all in that version |
| **Locked** | locked for login; edits from a later version must branch |
| **Disabled / hidden** | not offered at login; used to pre-create future versions (process doc, use cases) |

## 5. Cancel Branch and Move to View

- **Cancel Branch** — tree view → right-click → *Cancel Branch*: the item goes back to its previous version's
  content; the branch's changes are removed **but stay in history**. Not available for **DEFECT**. A branch per
  version is cancelled one at a time: branched in 1.1 and in 1.3 → cancelling 1.3 leaves 1.1; cancel 1.1 too to
  get back to 1.0. 📖
- **Move to View** — moves items between Views (e.g. items labelled 1.1 from 1.1 to 2.0). 📖

## 6. Rules for code that talks to Orcanos

1. **Always pass the version.** Every read is per View: `Get_Children` needs `?Ver_Id=` (404 without), filters take
   `Version_id`. Read a document / tree in the **document's** version, not a node's own older `Ver_Id` — the older
   version lacks children added since. ✅ (`orcanos-api/get-children.md`)
2. **Store / match the ORIGINAL id**, act on the **ID in the version.** `Original_id` is stable; `ID` changes on a
   branch. Resolve original → ID once per version from a filter (every row has both). ✅
3. **The label is not the View.** A row whose `Ver_Id` is older than the View is inherited, not stale or wrong. ✅
4. **A write in a later version may branch** (forced or chosen in the UI). After an API update, re-read the item's
   `ID` in that version — it may be new. ❓ (API branching behaviour not yet observed live)
5. **Pool ≠ View.** A pool item has no tree position; `Get_Children` will not find it under anything. 📖
