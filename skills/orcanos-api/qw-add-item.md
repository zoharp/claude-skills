# QW_Add_Object — Create Work Item

> ⚠️ The create method is **`QW_Add_Object`**. There is **no** `QW_Add_Item` endpoint
> (it 404s). This file was previously named for a method that does not exist on the API.

## Endpoint

```
POST <base>/api/v2/Json/QW_Add_Object
Authorization: Basic <base64(username:password)> OR Bearer <api-key>
Content-Type: application/json
```

`<base>` includes the tenant, e.g. `https://app.orcanos.com/orca60`.
Full URL: `https://app.orcanos.com/orca60/api/v2/Json/QW_Add_Object`.

**Auth:** See [main skill](SKILL.md) for Basic Auth and API Key options.
**Prerequisites:** Call [QW_Login](qw-login.md) first to get `Project.Id`, the version, and the
project's `Item_type[]` — you need the **`Label`** for `Object_Type` here (see the warning below).
**Spec source:** your instance's Swagger — `https://app.orcanos.com/<tenant>/api/swagger/ui/index#/Json`
(machine model at `.../api/swagger/docs/v1`).

---

> ✅ **ONE call creates the item WITH all its fields.** Besides name and description, the body
> takes the standard fields (`Status`, `Priority`, `Category`, `Assigned_to`, dates, `Parent_ID`, …)
> **and up to 60 custom fields** as `CS<n>_Name` / `CS<n>_value` pairs. You do **not** need a
> follow-up `QW_Update_Object` to fill fields on a new item — use that only to change an
> **existing** one. (A design once assumed create = name + description only; that was wrong —
> user correction 2026-10-07.)

## Full input schema (Swagger, as given by the user 2026-10-07)

Every property is a `string` except `Project_ID`, `Major_Version`, `Minor_Version` (integers).

```json
{
  "Project_ID": 0, "Major_Version": 0, "Minor_Version": 0,
  "Object_Name": "string", "Object_Type": "string",
  "Release_Version": "string", "Build_Version": "string",
  "Description": "string", "Parent_ID": "string",
  "Assigned_to": "string", "Created_date": "string", "Created_by": "string",
  "Category": "string", "Status": "string", "Priority": "string",
  "Start_Date": "string", "Effort_Estimation": "string", "Due_date": "string",
  "CS1_Name": "string", "CS1_value": "string",
  "...": "CS2_Name/CS2_value … CS60_Name/CS60_value — 60 pairs in all",
  "Insert_to_Pool": "string", "Migration_Reference": "string",
  "External_ID": "string", "Customer_ID": "string", "Site_ID": "string",
  "SkipIfNameExists": "string", "SpecialCustomFields": "string"
}
```

- The `CS<n>` slot number is just a **position in this request** (1…60), filled in any order; what
  identifies the field is the **title** in `CS<n>_Name` (see the custom-field warning below).
- More than 60 custom fields on one item → create with the first 60, then `QW_Update_Object` for
  the rest.
- `SpecialCustomFields` — purpose not yet verified.
- `Effort_Estimation` — standard field, string.

## Request Body (minimal example)

```json
{
  "Project_ID": 14667,
  "Major_Version": 1,
  "Minor_Version": 0,
  "Object_Name": "User authentication",
  "Object_Type": "REQ",
  "Description": "The system shall authenticate users via OAuth2",
  "Insert_to_Pool": "Y"
}
```

### Required fields

| Field | Type | Notes |
|---|---|---|
| `Project_ID` | integer | Project id (`Project.Id` from `QW_Login`) |
| `Major_Version` | integer | Major part of the version view (e.g. `1` from version label `1.0`) |
| `Minor_Version` | integer | Minor part of the version view (e.g. `0` from version label `1.0`) |
| `Object_Name` | string | Work item name/title |
| `Object_Type` | string | Work item type — the **`Item_type[].Label`** from `QW_Login` (e.g. `Complaint`, `Non Conformance`), **not** the `Code`. See the warning below |
| `Description` | string | Plain text or HTML — **but see the QMS item types warning below before writing to it** |

> ⚠️ **On QMS item types (CAPA, NCR, Complaint, and similar), `Description` is usually the
> item's *print-layout template*** — HTML with embedded Orcanos merge-field placeholders,
> rendered as the print-friendly view of the item (the "print" button in the Orcanos UI). It is
> **not** a free-text description box, and writing plain text (or a different HTML blob) into it
> overwrites/corrupts that layout for the item.
>
> Before writing a description-like value on one of these item types:
> 1. Fetch the item type's form via `QW_Get_Item_Add_Edit` (see
>    [qw-get-item-add-edit.md](qw-get-item-add-edit.md)) and look for a **dedicated custom
>    field** whose *tenant-configured `title`* reads like "Description" (a `CS*` field, not the
>    literal `Description`/`ws_add_col_name`) — write there instead.
> 2. If no such custom field exists, fall back to a field titled like "Root Cause".
> 3. If neither exists, don't write a description at all rather than guessing — leave the print
>    template alone.
>
> This does not apply to item types where `Description` genuinely is the free-text body (e.g.
> `REQ`) — check the field's role on each item type/tenant rather than assuming either behavior.

### ⚠️ `Object_Type` takes the **Label**, not the Code

This is the single most common failure on this endpoint, and it is the opposite of every read
endpoint. Sending the code produces:

```json
{ "IsSuccess": false, "Message": "Object type could not be found: 'COMP'", "HttpCode": 200 }
```

Verified live on orca60, 2026-09-13 (project 12495): `Object_Type` of `COMP`, `NCR`, `CA`, `PA`
and `CHKLST` are **all rejected** with that message, while `Complaint` and `Non Conformance`
create the item. The error text is misleading — it names the code you sent and says it "could
not be found", even when that code is present in the project's `Item_type[]`.

| Where | Identify the type by |
|---|---|
| `QW_Add_Object` → `Object_Type` | **`Item_type[].Label`** (`Complaint`, `Non Conformance`) |
| `QW_Get_Item_Add_Edit` → `Item_type` | **`Item_type[].Code`** (`COMP`, `NCR`) |
| `QW_Get_Object`, item keys (`COMP-26765`), deep links | **`Code`** |

`CAPA` hides the bug: its `Code` and `Label` are the same string, so CAPA-shaped flows work
while Complaint and NCR fail. Passing the label to a *read* endpoint fails differently —
`QW_Get_Item_Add_Edit` returns `"Index 0 is either negative or above rows count."`

Resolve the label at runtime from `QW_Login`'s `Data.Projects.Project[].Item_type[]` — each
entry is `{Code, Label, Permission}`. Item types are configured **per project**, not just per
tenant, so look it up on the project you are writing to, and fall back to the code unchanged
when the lookup fails rather than erroring.

```js
function itemTypeLabel(project, code) {
  const types = ensureArray(project.Item_type);
  const hit = types.find(t => (t.Code || '').toUpperCase() === code.toUpperCase());
  return (hit?.Label || '').trim() || code;   // fall back, never throw
}
// itemTypeLabel(project, 'COMP') -> 'Complaint'
```

> Reference implementation: `_resolve_item_type_label()` in `backend/api.py` of the Orcanos QMS
> project, used for `Object_Type` only — the item key, deep link and form fetch stay on the code.

### ⚠️ Custom fields are a `CS<n>_Name` + `CS<n>_value` **pair**

`QW_Get_Item_Add_Edit` identifies a custom field by `ws_add_col_name`, e.g. `CS18_Name`. That is
the key for the field's **name**, not its value — writing the value there fails the whole create:

```json
{ "IsSuccess": false, "Message": "Custom field <your value here> not found.", "HttpCode": 200 }
```

Send both halves, with the field's tenant **title** in `CS<n>_Name` (the internal `name`, e.g.
`CS178`, is rejected — verified live on orca60, 2026-09-13):

```json
{ "CS18_Name": "Details:", "CS18_value": "The infusion pump stopped mid-infusion..." }
```

So a `{ws_add_col_name: value}` map from the eForm must be expanded before it is sent.
Reference implementation: `_expand_custom_fields()` in `backend/api.py`.

### Common optional fields

| Field | Type | Notes |
|---|---|---|
| `Insert_to_Pool` | string | `"Y"` = add to the pool (no parent); `"N"` = add into the product tree (CR/requirements only) |
| `Parent_ID` | string | Parent item location; defaults to the project |
| `Status`, `Priority`, `Category` | string | Workflow defaults are used if omitted |
| `Release_Version`, `Build_Version` | string | Extra version components (default `0`) |
| `Assigned_to` | string | Username |
| `Created_date`, `Start_Date`, `Due_date` | string | Must match the server's local date format |
| `CS1_Name`…`CS60_Name` / `CS1_value`…`CS60_value` | string | Up to 60 custom fields |
| `SkipIfNameExists` | string | `"Y"` to avoid creating a duplicate by name |
| `External_ID`, `Migration_Reference`, `Customer_ID`, `Site_ID` | string | Integration references |

> **Version note:** `QW_Add_Object` identifies the version by `Major_Version` + `Minor_Version`,
> **not** by the `Ver_id` that `QW_Get_Filter_Results` uses. Derive major/minor from the
> version label (`QW_Login` → `Version.Version_label`, e.g. `"1.0"` → `1`, `0`).

---

## Success Response

`ResultClass[Int32]` — `Data` is the new item's numeric id:

```json
{
  "IsSuccess": true,
  "Data": 53834,
  "Message": "Object created successfully.",
  "HttpCode": 200
}
```

To link the new item, build its **Key** as `{Item_type.Code}-{Data}` (e.g. `T_CASE-53834`) and call
**`QW_Add_Relations_Custom_Code`** (not `QW_AddRelation`). See [qw-add-trace.md](qw-add-trace.md).

---

## Failure Responses

| HTTP | Meaning | Fix |
|---|---|---|
| `404` | Wrong method/path (e.g. calling `QW_Add_Item`) | Use `QW_Add_Object` under `/api/v2/Json/` |
| `401` | Session expired | Re-authenticate via `QW_Login` |
| `200` + `IsSuccess: false` | Validation error | Check `Message` — often a missing required field or bad `Object_Type` |
| `200` + `Message: "Object type could not be found: 'X'"` | You sent the item type's **Code**; `Object_Type` wants its **Label** | Resolve `Item_type[].Label` from `QW_Login` for that project. See the warning above |
| `200` + `Message: "Custom field ... not found"` | A value was sent under `CS<n>_Name` | Send the pair: `CS<n>_Name` = field title, `CS<n>_value` = value |

---

## Full Example (JavaScript)

```js
async function addObject({ baseUrl, authHeader, projectId, major, minor, name, description, objectType }) {
  const r = await fetch(`${baseUrl}/api/v2/Json/QW_Add_Object`, {
    method: 'POST',
    headers: { Authorization: authHeader, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      Project_ID: projectId,
      Major_Version: major,
      Minor_Version: minor,
      Object_Name: name,
      Object_Type: objectType,   // Item_type[].LABEL, e.g. "Complaint" — not the code
      Description: description || '',
      Insert_to_Pool: 'Y',
    }),
  });
  if (r.status === 401) throw new Error('Session expired');
  const data = await r.json();
  if (!data.IsSuccess) throw new Error(data.Message || 'Add object failed');
  return data.Data; // new numeric item id
}
```

---

## See also
- [Main Skill](SKILL.md) — Base URL, auth, common patterns
- [QW_Login](qw-login.md) — Projects, versions, and `Item_type[].Code`
- [QW_AddRelation](qw-add-trace.md) — Link the new item to its parent
- [QW_Add_Defect](qw-add-defect.md) — Defects are a separate table: use this, not QW_Add_Object

## Part (PRT) items from a BOM file import (traceability-matrix, 2026-10-29)
`bom_import_api._run` creates missing parts with `Object_Type` = the PRT **label** from QW_Login (e.g. "Part"),
`Insert_to_Pool: "Y"` (flat — no parent; the hierarchy is kept in the app), `Migration_Reference: bom-import:<id>`,
custom fields as `CS<n>_Name` (title) / `CS<n>_value`; ONE call at a time (parallel calls deadlocked SQL Server in the
SBOM import). **Unverified live for PRT:** whether the new part shows in the tenant's Part Catalog filter at once.

