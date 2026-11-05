# Orcanos Structured Documents — DOC → paragraphs → traceable items

How design-control / ALM documents (URS, SRS, PRS, test protocols, risk files …) are held **inside
the Orcanos database** as a hierarchy of work items, and how to read that hierarchy.

> Source: product owner (Zohar Peretz, mail *"DOC management in trace matrix"*, 2026-10-27) — 📌 given.
> **Used in:** traceability-matrix DHF module (`dhf_engine.py` / `dhf_build.py` / `dhf_api.py`, 2026-10-27) — not yet run live.
> The API shapes are ✅ where marked; everything else must be confirmed live before it ships.

---

## 1. What a structured document is — and what it is NOT

- Every requirement, risk and test case **can live inside a document** that is itself a work item.
  The document is an **outline of work items** in the Orcanos DB — the user works on the items, and
  when done **exports it to Word** and signs that Word file in **Document Control**.
- It is **NOT Document Control.** A structured document is not a `DMS_ITEM` and has no file
  revisions. The signed Word export ends up in a `DMS_ITEM`; the structured document is its source.
- Containment (this page) is **not** traceability. The outline says *where an item sits in a
  document*; traces say *what it satisfies / verifies*. See `orcanos-work-items.md` §3.4.

## 2. The shape

```
DOC                     the document                     (e.g. "Software Requirements Specification")
├─ PAR                  paragraph / section               (INTRODUCTION)
│  ├─ PAR               sub-paragraph (any depth)          (SCOPE, PURPOSE, DEFINITIONS …)
├─ PAR                                                     (Functional requirements)
│  └─ PAR                                                  (Items Manager – Instrument Log Book)
│     ├─ SRS / REQ / MR_REQ / T_CASE / RISK …   traceable items — the leaves that matter
│     └─ …
```

| Role | Work item | Notes | Conf. |
|---|---|---|---|
| **Document** | `DOC` | The root. Its **id** is what every descendant carries in `Root_Document`. | 📌 code to confirm from `QW_Login` |
| **Paragraph** | `PAR` **or** `REQ_HD` — *"whatever comes below the DOC"* | Headings. Nest to any depth. `PAR` is often the **custom code** of `REQ_HD` (Key `PAR-19831`, Type `REQ_HD` — `get-children.md` sample). Treat any non-traceable child type as a paragraph; never hard-code one. | ✅ `REQ_HD`/`PAR` seen live |
| **Traceable item** | `MR_REQ` (UR), `REQ` (PR), `SRS` (SR), `T_CASE` (TC), risk types … | Sit under paragraphs (normally the deepest ones). These are what a trace panel scores. | ✅ codes per `orcanos-work-items.md` §4 |

> ⚠️ **Older notes called `REQ_HD` the document root.** Per the product owner the root is the `DOC`
> item and `REQ_HD` is a paragraph. `orcanos-work-items.md` §4.4 was corrected 2026-10-27.

## 3. `Root_Document` — which document is an item in?

Every item, at **every level** of the outline, carries the id of its **DOC** in a filter column:

```json
{ "Type": "text", "Name": "Root_Document", "Title": "Root Document Id",
  "Visible": "Y", "Order": "4", "Section": "" }
```

- Read it from `QW_Get_Filter_Results` — **only if the filter SELECTS the column** (a filter returns
  only its own columns; a missing column is an empty value, not an error — Critical Note #62 in the
  traceability-matrix repo). So: check the column is in the filter's field list first, and if it
  isn't, **tell the user** ("add *Root Document Id* to filter X") — never read every item as
  "not in a document".
- **Empty `Root_Document` on an item = the item is in the POOL** — it exists, but in no document.
  New items created through `QW_Add_Object` without a parent land there (today's default).
- ⚠️ The value is the DOC's **ORIGINAL id** (`Original_id`, stable across versions) — **not** the
  `ID` that `Get_Children` takes. Because of **item branching** a DOC can have a **different `ID` in
  every version**, while an item has one parent document — so `Root_Document` stores the original.
  Keep **both**: group items by the original id; read the outline with the DOC's `ID` **in the
  version** you read it in. Passing the original id to `Get_Children` answers 200 `"Item not found."`
  for a branched DOC.
- **Resolving original → ID (live, orca60, 2026-10-27):** read a saved **DOC filter** with
  `QW_Get_Filter_Results` (`Item_Type` `DOC`, `Version_id` = the version). Every row carries the system
  fields **`ID`** and **`Original_id`** (hidden, always returned), and `Key` reads `DOC-<ID> (<Original>)`.
  E.g. filter 713 *All Design Documents*, version 434: `Original_id` 8467 → `ID` 16278, and
  `Get_Children/16278?Ver_Id=434` returns the outline. Read it once per version → a map.
  - ✗ `QW_Get_Object_View(original, DOC, Ver_Id)` → "The Item could not be found." for a branched DOC
    (works only when ID = original). `QW_Get_Object` returns no ID/version. `Get_Children` on the
    PROJECT times out / hits SQL max recursion.
  - ✗ `GetItemURL(original)` points at the DOC's ORIGINAL version (e.g. 332) — reading the outline there
    gives the OLD document, without the panel's (branched) items.
  - The same applies to paragraphs/items: `Key` `PAR-19831 (8503)` = ID 19831, original 8503.
- Many items → few documents: group by `Root_Document` to get the document list of a trace level.

## 4. Reading a document — `Get_Children` recursively

`GET <base>/api/v2/Json/Get_Children/<ID>?Ver_Id=<version>` (`Ver_Id` required — 404 without it, live 2026-10-27) — direct children only, one call per node, already
enriched (Key, Type, Name, Status, Description HTML, ItemURL). Full contract and traps:
**`orcanos-api/get-children.md`**. The rules that matter here:

1. Start at the DOC's **`ID` in the version** (resolved from `Root_Document`'s original id, §3);
   recurse into **every** child (paragraphs and items — an item can have sub-items). The same
   applies to a `Parent_ID` write at the document's top level.
2. Recurse with the **child's own `Ver_Id`** (it can differ from the parent's), and use the
   server's `ItemURL` for the "open in Orcanos" link — never rebuild it.
3. Carry a `visited` set (cycles / shared nodes) and a depth cap.
4. Display the `Key`; branch logic on `Type` (Key prefix is the custom code — §3.2 of work-items).
5. **Sibling order** is the document order. Keep the order `Get_Children` returns; number
   paragraphs from it (1, 1.1, 1.2 …) the way the Word export does.
6. `Description` is HTML and may hold `<a name="FILTER_587" …>` embedded-filter anchors (a table
   Orcanos renders in place) — show a marker, don't flatten it to prose.
7. Cost: a 300-item document is ~300 calls. Cache per document per build; never walk on every view.

## 5. Status — "is this item done?"

An item's `Status` is a label. Whether it counts as done comes from its type's **status system
table** (`orcanos-api/get-item-statuses.md`): **done = `IsActive = 1` AND `IsComplete = 1`** on
that status's row (product-owner rule for document completion). Read the table once per type;
map on `Description` (the label), never on `Code`.

> ⚠️ get-item-statuses.md trap 3 shows a *final* CAPA status with `IsActive: 0, IsComplete: 1`.
> If a type's terminal status is inactive, the AND rule never counts its items as done — check each
> type's table when wiring this and report a type with no `IsActive ∧ IsComplete` row.

## 6. Writing — placing an item in a document

- **Create under a parent:** an item created with a parent paragraph becomes part of the document
  (and inherits its `Root_Document`). The exact `QW_Add_Object` parameter for the parent is
  **not yet confirmed** — find it before building.
- **Move from the pool / between paragraphs:** a re-parent call. **Endpoint not yet confirmed.**
- **Reorder within a paragraph:** sibling order write. **Endpoint not yet confirmed.**

Mark every one of these unverified in code until a live call has succeeded.

## 7. Checklist for a feature that uses documents

- [ ] Does each source filter **select `Root_Document`**? If not, say so to the user.
- [ ] Pool items (empty `Root_Document`) are shown as *pool*, not dropped.
- [ ] DOC root type and paragraph types read from the tenant, not hard-coded.
- [ ] Recursion uses child `Ver_Id`, a `visited` set, and a depth cap.
- [ ] Done = `IsActive ∧ IsComplete` from the status table, per type.
- [ ] Keys link to `ItemURL`.

## See also
- `orcanos-work-items.md` — the item catalogue and identifier traps
- `orcanos-api/get-children.md` — the call
- `orcanos-api/get-item-statuses.md` — the status flags
- `orcanos-api/qw-get-filter-results.md` — reading `Root_Document` from a filter
