# Filter-Result Fields — the `Field[]` dictionary

What every column that comes back from [QW_Get_Filter_Results](qw-get-filter-results.md) actually
means. Load this when you are **interpreting or rendering** results — deciding which columns to
show, what a value means, whether a blank is really empty. The endpoint's own contract (request
body, paging flags, auth) stays in [qw-get-filter-results.md](qw-get-filter-results.md).

The same `Field[]` shape is returned by [QW_Get_Object](qw-get-object.md), so this dictionary
applies there too.

---

## The three levels of the response

```
Data.Object[]            ← one entry per work item
  ├─ Id / Type / Version / Allow_edit / Allow_branch / Freeze   ← item envelope
  └─ Field[]             ← the columns
       ├─ Name           ← table.field name — the stable machine key
       ├─ Title          ← the label the user sees (tenant-customisable)
       ├─ Text           ← the value
       └─ Type / Visible / Order / Section / Tooltip / Web_order
Data.Total_records / Current_page / Page_size / Info
```

### Item envelope

| Key | Meaning |
|---|---|
| `Id` | The item id. **Two shapes exist:** bare (`"26532"`) or `"<display> (<internal>)"` (`"12345 (9876)"`). Always run it through the parser in [qw-get-filter-results.md](qw-get-filter-results.md#parse-item-id). |
| `Type` | The **ORIGINAL work-item type code** — `SRS`, `MR_REQ`, `T_CASE`. ⚠️ Not the custom code in the `Key` field (`SR-26532`), and not the label in `Obj_type` (`Software Requirement`). All three coexist on one item; see [Three names for one type](#-three-names-for-one-type). |
| `Version` | The **project `Ver_Id`** (`"341"`) — the version the item was read in. ⚠️ Nothing to do with the `Obj_version` field (`00.00.000.0000`), which is the *item's* own version string. |
| `Allow_edit` | `0`/`1` — may the current user edit this item. Gate an edit affordance on it. |
| `Allow_branch` | `0`/`1` — may this item be branched into a newer project version. |
| `Freeze` | `0`/`1` — the item is frozen (locked by its status). A frozen item is read-only regardless of permission. |

`Data.Info` is an empty string in every capture so far — purpose unknown; don't code against it.

### Field object

| Key | Meaning |
|---|---|
| `Name` | **`table.field` name** — the stable machine key (`Obj_name`, `DMS_Revision`, `CS354`). Match on this. |
| `Title` | The label the user sees (`Name`, `Revision`, `Signers List`). **Tenant-customisable** — good for display, unsafe as a lookup key across tenants. |
| `Text` | The value. `null` when unset. What it holds varies by field — for some combo boxes it's the internal code (`IsHead: "1"`), for others already the label (`Obj_status: "New"`). The dictionary below says which. |
| `Type` | Widget type — `text`, `numeric`, `date`, `combobox`, `multiSelect`, `richEditor`. See [Type](#type-is-a-widget-hint-not-a-parse-guarantee). |
| `Visible` | `Y`/`N` — whether the field belongs in a user-facing field list. `N` fields (`ID`, `IsLink`) are plumbing. |
| `Order` | Position in the **field catalogue** (the "pick a column" list), *not* the grid. See below. |
| `Section` | Section id. Empty (`""`) here; in [QW_Get_Item_Add_Edit](qw-get-item-add-edit.md) it is a bare numeric id with no title. |
| `Tooltip` | Admin-authored help text. Empty in every capture so far. |
| `Web_order` | Grid column order — **and non-unique**. See below. |

---

## ⚠️ `Order` is alphabetical, not the column order

Verified across the full 46-field sample: `Order` **0–3 are pinned** — `0` Key, `1` Name,
`2` Status, `3` Traced Items Info — and **4–48 are strictly alphabetical by `Title`**
(Approval Duration, Approved Date, Assigned To, Category, Completion Date, …, Work Item Type).
`Visible: "N"` fields are pushed past the end (`60`, `999`).

Consequences:

- **Never use `Order` for grid columns.** It will render a filter's carefully-arranged columns in
  alphabetical order, which looks like a bug in the filter, not in your code.
- **`Order` is derived from `Title`, and `Title` is tenant-customisable** — so the same field can
  carry a different `Order` on two tenants. Don't persist it or compare it across accounts.
- **Gaps are normal.** Slots `19`, `22`, `24`, `44` are absent from this item type — the numbering
  is a global catalogue, and each type returns a subset.

## ⚠️ `Web_order` is the grid order — and it has duplicates

`Web_order` is non-`null` only on the fields the filter surfaces as columns; every other field
carries `null`. In the reference sample that's 10 of 46 fields.

**It is not a total order.** The same sample has `Web_order: "1"` on both *Name* and *Start Date*,
`"5"` on both *Priority* and *Category*, `"11"` on both *Efforts* and *Description*. So:

```js
// ⚠️ Array.prototype.sort is stable in modern JS, but only if you never compare unequal
//    values as equal by accident — parseInt(null) is NaN, and NaN comparisons put rows anywhere.
const columns = item.Field
  .map((f, i) => ({ f, i }))                       // keep the API's own order as tiebreak
  .filter(({ f }) => f.Web_order != null)          // only the filter's grid columns
  .sort((a, b) =>
    (parseInt(a.f.Web_order, 10) - parseInt(b.f.Web_order, 10)) || (a.i - b.i))
  .map(({ f }) => f);
```

The safest column order is simply **the order the API returned the fields in**, which within one
filter *is* the filter's own order — that is what this project relies on (see `CLAUDE.md`
Critical Note #5, "Keep filter column order").

## `Type` is a widget hint, not a parse guarantee

`Type: "text"` does **not** mean plain text. `traced_items_list` is typed `text` and routinely
contains an `<a>` hyperlink; a tenant's `Obj_description` typed `text` can hold full rich-text
markup. Conversely `richEditor` fields (`document_revision`) can arrive as plain text or `null`.

**Strip tags and decode entities on any field you render as text**, whatever its `Type` says —
and decode in a loop, because values can be double-encoded (`&lt;a href=…`). This is the same trap
documented for `Traced Items Info` and for `matrix_api._clean`.

## ⚠️ Three names for one type

One item carries the type in three different forms, and they are all different strings:

| Where | Example | Use it for |
|---|---|---|
| Envelope `Type` | `SRS` | API calls — `Item_Type`, view URLs, `QW_AddRelation` |
| `Obj_type` field `Text` | `Software Requirement` | Display; matching against Ask Paul prompt names; `QW_Add_Object`'s `Object_Type` |
| `User_Prefix` field `Text` | `SR-26532` | The key the **user** sees, and the key `Traced Items Info` references |

Picking the wrong one fails *silently* on several endpoints — [GetFilterList](get-filter-list.md)
returns an empty array for a code where it wanted the label, and `QW_AddRelation` rejects custom
codes with a misleading "Item is deleted". A `Test Case` and a `Test Run` even **share** the code
`T_CASE`, so the label is the only thing telling them apart.

## ⚠️ `CS<n>` fields are per-tenant custom slots

`CS354` / `CS355` are custom-field slots. **The number is tenant-specific** — `CS354` is
*Signers List* on this tenant and may be anything on the next. Match those on `Title`
(or resolve them from [QW_Get_Item_Add_Edit](qw-get-item-add-edit.md)), never on `Name`.

The inverse holds for every field in the dictionary below: those `Name`s are Orcanos system
columns and **are** stable across tenants — match those on `Name`, not on `Title`.

## Blank has several spellings

Unset does not consistently mean `null`. Observed sentinels: `null`, `""`, `"Not Assigned"`
(`Assigned_to`), `"Not Set"` (`Obj_category`), `"- Not Set -"` (`Obj_priority`), `"0"` on numerics
that were never filled (`Effort_estimation`, `approval_duration`), and `"00.00.000.0000"`
(`Obj_version`). Normalise before deciding a cell is empty, or a grid will show noise where the
user sees nothing.

---

## Field dictionary

Grouped by what the field is *for*. **Name** is the `table.field` key you match on; **Title** is
the default label (tenant-customisable).

### Identity & keys

| Name | Title | Type | What it is |
|---|---|---|---|
| `User_Prefix` | Key | text | **The displayed key, with the tenant's custom code** — `SR-26532`. This is the key `Traced Items Info` points at, and the one to show the user. Note the prefix (`SR`) is the *custom* code, not the original type code (`SRS`). |
| `ID` | ID | numeric | Internal row id. `Visible: "N"` — plumbing, not a user column. |
| `Original_id` | Original ID | numeric | The item's **original id**, stable across versions and branches. Equals `ID` for an item that was never branched. Use it to follow one logical item through project versions. |
| `Obj_type` | Work Item Type | text | The type's **Label** (`Software Requirement`), not its code. |
| `Obj_version` | Version | text | The **item's own** version string (`00.00.000.0000`). Not the project version — that's the envelope's `Version`. |

### Content

| Name | Title | Type | What it is |
|---|---|---|---|
| `Obj_name` | Name | text | The item's name / synopsis. ⚠️ **Defects use `Synopsis` instead** — try both (see [qw-get-filter-results.md](qw-get-filter-results.md#field-name-quirks-by-item-type)). |
| `Obj_description` | Description | text | The body text. Often rich text despite the `text` type — strip/decode before rendering. |

### Workflow & assignment

| Name | Title | Type | What it is |
|---|---|---|---|
| `Obj_status` | Status | combobox | The status **label** (`New`), already resolved — not a code. |
| `Active_Ind` | Status Active | combobox | `1`/`0` — the **Active flag of the item's current status**. Every status carries this indicator; `0` means the item's status is a non-active one (closed/cancelled/…). It is a property of the status, not a separate "is the item active" field. |
| `Completion_date` | Completion Date | date | Auto-filled by Orcanos when the item moves to a status whose `is_complete` flag is `1`. Not user-entered — a `null` here with a done-looking status means that status isn't marked complete. |
| `Assigned_to` | Assigned To | combobox | The assignee's **user id**. `"Not Assigned"` when unset. |
| `user_manager` | Employee Manager | combobox | The **user id** of the assignee's manager (every user has a manager). |
| `Obj_priority` | Priority | combobox | Priority label. Sentinel `"- Not Set -"`. |
| `Obj_category` | Category | combobox | Category label. Sentinel `"Not Set"`. |
| `Start_date` | Start Date | date | Planned start. |
| `Due_date` | Due Date | date | Planned due date. |
| `Effort_estimation` | Efforts | numeric | Effort estimate. `0` when unset. |

### Tree / containment (≠ traceability)

These describe the item's place in the **outline tree** (document → paragraph → requirement), which
is a *different graph* from the trace links. See [Get_Children](get-children.md).

| Name | Title | Type | What it is |
|---|---|---|---|
| `Parent_name` | Parent Name | text | The parent's `KEY: Name` (`PROJECT-7506: Cardiology - Software`). |
| `Parent_original_id` | Parent Original Id | text | The parent's `Original_id` — the id to recurse on. |
| `Root_Document_Name` | Document Name | text | When the item sits under paragraphs whose root is a **document**, this is that document's name. |
| `Root_Document` | Root Document Id | text | The same root document's **id**. |
| `IsHead` | In Pool | combobox | `1` = the item is **in the pool (backlog)**; `0` = it is placed in the tree. A pool item has no tree parent, which is why `Parent_name` can be populated on one item and empty on another of the same type. |
| `IsLink` | Copy As Link | combobox | `1` = this row is a **link copy** — a pointer to one item shown in more than one place in the tree. Two rows can therefore be the same underlying item. `Visible: "N"`. |
| `is_template` | Is Template Indicator | combobox | `1` = the item is marked as a **template**; users can "add from template", which copies it *and its children*. |
| `Project_name` | Project Name | text | The owning project's name. |

### Traceability

| Name | Title | Type | What it is |
|---|---|---|---|
| `traced_items_list` | Traced Items Info | text | The item's onward trace links — **the field the whole matrix is built on**. Arrives in three shapes (plain key, key + trailing text, or an `<a>` hyperlink) and one value can mix them. ⚠️ Never hand-parse it — see the full rules under *"`Traced Items Info` — THREE shapes"* in [qw-get-filter-results.md](qw-get-filter-results.md). |

### Revision & branching

| Name | Title | Type | What it is |
|---|---|---|---|
| `DMS_Revision` | Revision | text | The item's current revision (`A`, `B`, …). |
| `last_approved_revision` | Last Approved Revision | text | The last revision that completed approval. An item can be revision **B draft** while this reads **A** — the pair is how you tell "changed since approval". |
| `RevisionInd` | Revision Indicator | combobox | `0`/`1` revision flag. *(Exact semantics unconfirmed — log a populated example before relying on it.)* |
| `document_revision` | Document Revision | richEditor | Revision notes / text for the document. Rich text. |
| `IsBranch` | Is Branch | combobox | `1` = this item is a **branch**: it originated in an earlier project version (say 1.0) and was changed in a later one (2.0), so it now has its own row while sharing an `Original_id`. |

### Routing (electronic signature)

Orcanos' e-signature workflow. `DMS_Routing_State` is the live state; the dates bracket the run.

| Name | Title | Type | What it is |
|---|---|---|---|
| `DMS_Routing_State` | Routing State | combobox | Current routing state (`Draft`, …). This is the signature workflow's state — **distinct from `Obj_status`**. |
| `DMS_Routing_Start_Date` | Routing Start Date | date | When routing began. |
| `DMS_Routing_Due_Date` | Routing Due Date | date | When the signatures are due. |
| `DMS_Routing_End_Date` | **Approved Date** | date | ⚠️ Title says *Approved Date*, name says *routing end*: **the date the item was signed electronically**, i.e. routing finished. Same thing — the item is approved because the routing ended. |
| `approval_duration` | Approval Duration | numeric | How long approval took. `0` when never routed. *(Units unconfirmed — assume days, verify on a signed item.)* |
| `Next_signee` | Next Assignee Details | text | The **next users due to sign** in the routing process, as display text. |
| `CS355` | Next Assignee List | multiSelect | The same next-signee set as a selectable list. ⚠️ `CS355` is a **tenant-specific custom slot** — match on the Title. |
| `CS354` | Signers List | multiSelect | **All signers** in the associated routing (signature) process. Same custom-slot caveat. |

### ECO (Engineering Change Order)

Populated only when the item is linked to an ECO; all `null` otherwise.

| Name | Title | Type | What it is |
|---|---|---|---|
| `eco_no` | ECO Number | numeric | The linked ECO's number. |
| `eco_status` | Related ECO Status | combobox | That ECO's work-item status. |
| `eco_routing_state` | Related ECO Routing State | combobox | That ECO's routing (signature) state. |
| `eco_release_date` | ECO Release Date | date | When the ECO was signed — the moment it **released all its associated items/documents as a batch**. This is the release date for everything on that ECO, not just this item. |

### Audit

| Name | Title | Type | What it is |
|---|---|---|---|
| `Created_by` | Created By | combobox | **User id** (`orca`), not a display name. |
| `Created_date` | Created Date | date | `YYYY-MM-DD HH:mm:ss`. |
| `Updated_by` | Updated By | combobox | **User id**. |
| `Updated_date` | Updated Date | date | `YYYY-MM-DD HH:mm:ss`. |

---

## Confidence

Every row above is either taken from a **captured live response** (orca60, `SRS` item, 46 fields)
or from the product owner's own description of the field's meaning. Three entries are explicitly
hedged as unconfirmed: `RevisionInd`'s exact semantics, `approval_duration`'s units, and
`Data.Info`. The `Order`/`Web_order` orderings were derived by sorting the full sample, not assumed.

A tenant with custom fields will return **more** rows than this — anything not listed here is a
custom field. Resolve it via [QW_Get_Item_Add_Edit](qw-get-item-add-edit.md) (the form definition,
which carries labels, picklists and mandatory rules) or
[GetSystemTableValues](get-system-table-values.md) (one picklist's values standalone).

---

## See also
- [qw-get-filter-results.md](qw-get-filter-results.md) — the endpoint: paging flags, `Filter_By`, `Traced Items Info` parsing
- [qw-get-object.md](qw-get-object.md) — one item, same `Field[]` shape
- [qw-get-item-add-edit.md](qw-get-item-add-edit.md) — the type's form definition: which fields exist, their picklists and mandatory rules
- [get-system-table-values.md](get-system-table-values.md) — resolve a combo-box field's option list
- [get-children.md](get-children.md) — the containment tree the `Parent_*` / `Root_Document*` fields describe
- [qw-login.md](qw-login.md) — where type codes, labels and per-type permissions come from
- `Orcanos-infra` skill — the **conceptual model** behind these fields (what a work item, pool, branch, routing and ECO actually *are*). Read that for the "why"; this file is the "which field".
