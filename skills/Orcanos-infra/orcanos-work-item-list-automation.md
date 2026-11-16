# Work Item List Automation — a list field whose values are Orcanos items

**What** a "list based on work items" is, what the database stores, and how to read it from the API.
**Part of:** `Orcanos-infra` · **API:** `orcanos-api/qw-get-item-add-edit.md`, `orcanos-api/qw-get-filter-results.md`
**Sources:** help.orcanos.com → *Work Item List Automation* (read 2026-11-12) + the user (2026-11-12) + live orca60 screen.

---

## 1. What it is

An admin rule that turns the items of one work item type into a **system table**, so another form can pick an item
from a list (combo box or multi-select) instead of typing its name.

Setup (Admin → *Alerts (Scheduled Emails), Notifications and Task automation* → **Work Items List Automation** → Add):

| Setting | Meaning |
|---|---|
| **Project** | The project whose items are listed (e.g. QMS E-Forms). |
| **Work Item** | The type listed (e.g. Supplier). |
| **First Field** | A unique value shown first — e.g. the item **ID**, **Key** or **Name**. |
| **Second Field** (optional) | Extra text added to the first — e.g. the Name. |
| **Active** (default on) | Items added later are added to the table. |
| **Get Existing Data** | Items that already exist are added too. |

Saving creates a reference table under **Admin → System Customization → System Tables**. A custom **combo box** or
**multi-select** field (Fields Management) is then based on that table.

## 2. What is stored vs what is shown — the trap

| | Value |
|---|---|
| **Stored (the table's CODE)** | The listed item's **ID** (user, 2026-11-12). |
| **Shown (the table's VALUE / label)** | First Field (+ Second Field), as the admin set it up: `Test supplier`, `25937`, `25937-Test supplier`, … |

Live orca60 (2026-11-12): SCAR-27498's **Supplier Name** shows **`25937-Test supplier`** (ID `25937` + `-` + Name) —
supplier `SUPLR-25937`.

- **`QW_Get_Filter_Results` returns the shown TEXT**, not the code. Matching that text to an item by name or by
  substring silently fails (`25937-Test supplier` ≠ `Test supplier`) or, worse, matches the wrong item.
- **`QW_Get_Item_Add_Edit` gives the list itself:** the field's `val[]` = `{code, label}` per entry — code = item ID,
  label = the shown text. Map text → code from it and compare **IDs**.
- **`QW_Get_Object_View`** gives a picklist field's `Text` (label) **and** `Code` for one item.
- Writing the field: send the value as the form expects for a combo (the label is what other picklist writes take —
  `qw-update-item.md`); **not yet verified live** for a list-automation field — read it back.

## 3. How to resolve a shown value to the item (pattern)

1. Read the form once (`QW_Get_Item_Add_Edit`, item 0 = the Add form) → the field's options → `{normalised label: code}`.
2. For each filter row, look the shown text up → the item ID. Compare IDs only.
3. Fallback when the form can't be read or the field is plain text: parse the text — the whole value is the ID / key /
   name, or an ID / key joined to a name (`25937-Test supplier`, `Name - 25937`, `Name (SUPLR-25937)`). The **ID / key part
   decides**; a name must match whole, never as a substring.

Used by traceability-matrix `supplier_portal_scar.py` (`supplier_codes`, `matches_supplier`, `_supplier_code_map`) to
tie a SCAR to its supplier (Critical Note #131).

## See also
- `orcanos-supplier.md` — the SCAR's Supplier field is such a list
- `orcanos-api/qw-get-item-add-edit.md` — `val[]` options with code + label
- `orcanos-api/qw-get-filter-results.md` — rows carry the shown Text only
