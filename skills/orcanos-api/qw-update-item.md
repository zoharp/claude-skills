# QW_Update_Object — Update Work Item

## Endpoint

```
POST <base>/api/v2/Json/QW_Update_Object
Authorization: Basic <base64(username:password)> OR OrcanosAPIKey: <key>
Content-Type: application/json
```

`<base>` includes the tenant, e.g. `https://app.orcanos.com/orca60`.
Full URL: `https://app.orcanos.com/orca60/api/v2/Json/QW_Update_Object`.

**Auth:** See [main skill](SKILL.md) for Basic Auth and API Key options.
**Spec sources:** knowledgebase — https://help.orcanos.com/knowledgebase/qw_update_object-rest-api/ ·
tenant Swagger `…/api/swagger/docs/v1` (model `ObjectsUpdate`).
**Reference implementation:** `_orcanos_update_field` in Orcanos QMS `backend/api.py`.

> ✅ **Every rule below was verified live** on orca60 (CAPA-26547 / CAPA-26542, 2026-09-16).
> The knowledgebase and Swagger are ambiguous or wrong on several of them — trust this page.

---

## ⚠️ The four rules that make it work

### 1. `View_Version` is the version **ID**, not the label

"The view version of the project which displays in the URL" means the number in
`/web/422/items/...` → `"422"`. The label from QW_Login (`"1.0"`) fails with:

```json
{"IsSuccess": false, "Message": "Input string was not in a correct format.", "HttpCode": 500}
```

That error names no field, so it looks like a bad picklist or number — it is not. It is
returned **even for a body with nothing but `Object_ID` + `Object_Name`**.

### 2. It IS a partial update — send only what changes

Omitted fields keep their current values (diffed the whole form before/after). Do **not**
re-send the full field set from `QW_Get_Item_Add_Edit`: its picklist values come back as
labels mixed with codes and re-sending them is where things break. Minimum body:

```json
{ "Object_ID": 26547, "View_Version": "422", "Object_Name": "<current name>", "<Field>": "<value>" }
```

`Object_Name` is required — send the **current** name (from `QW_Get_Item_Add_Edit`'s
`Object_Name.current_value`) when not renaming, or you rename the item.

### 3. Picklist values are **labels**, not codes

`"Assigned_to": "Not Assigned"` ✅ (the option's `label`). The option `code` (`"4"`) is not what
the KB describes ("the user names…"); send labels. Matches what `QW_Get_Item_Add_Edit` returns
as `Text` / current value.

### 4. Custom fields go through a **slot pair** keyed by the field's TITLE

A custom field's `ws_add_col_name` is `CSn_Name` (e.g. `CS1_Name` = "Owner", internal name
`CS337`). Writing to that key directly **returns `IsSuccess: true` and changes nothing**.
Use the numbered slot pair, where `CSk_Name` holds the field **title** and `CSk_value` the value
(`k` is just a slot, 1..60, unrelated to `n`):

```json
{ "CS1_Name": "Owner", "CS1_value": "orca" }
```

| `CS1_Name` sent | Result |
|---|---|
| `"Owner"` (title) | ✅ updated |
| `"CS337"` / `"CS224"` (internal name) | ❌ `Field name CS224 not found.` |
| `"CS1_Name": "orca"` (value on the ws key, no pair) | ⚠️ success, **no change** |

---

## ⚠️ Success does not mean the field changed

A calculated/read-only field ("Number of related tasks", numeric) accepted
`CS1_Name`/`CS1_value` with `IsSuccess: true` and kept its value. **Always read the item back**
(`QW_Get_Item_Add_Edit` with the `Item_id`) and compare before reporting success.

---

## Other errors seen

| Message | Cause |
|---|---|
| `Input string was not in a correct format.` | `View_Version` sent as a label — see rule 1 |
| `You can not able to add release version in 3 digit versioning.` | `Release_Version` sent on a project using 3-digit versioning — omit it |
| `Field name <X> not found.` | `CSk_Name` holds something other than the field title |

---

## Request fields (Swagger `ObjectsUpdate`)

| Field | Type | Notes |
|---|---|---|
| `Object_ID` | integer | **Required.** Numeric item id |
| `View_Version` | string | **Required.** Version **id** from the URL — rule 1 |
| `Object_Name` | string | **Required.** Current name unless renaming |
| `Make_Branch` | integer | `0`/`1` |
| `Description` | string | Plain text or HTML |
| `Assigned_to` | string | User name label (e.g. `"orca"`, `"Not Assigned"`); user must belong to the project |
| `Status`, `Priority`, `Category` | string | Labels. ⚠️ Status changes may be gated by the workflow's e-signature process — untested |
| `Release_Version`, `Build_Version` | string | Omit unless versioning needs them (see errors) |
| `Start_Date`, `Due_date` | string | Server-local date format — untested |
| `Effort_Estimation` | string | |
| `Customer_Id`, `Site_Id` | string | |
| `CS1_Name`…`CS60_Name` / `CS1_value`…`CS60_value` | string | Slot pairs — rule 4 |

---

## Success Response

```json
{ "IsSuccess": true, "Data": 26547, "Message": "Object updated successfully.", "HttpCode": 200 }
```

`Data` is the item id (an integer in practice, not a string). Errors also come back **HTTP 200**
with `IsSuccess: false` and `HttpCode: 500` in the body — never rely on the HTTP status.

---

## Full Example (Python)

```python
def update_field(api_url, auth, item_id, version_id, form_fields, field, value):
    """form_fields: QW_Get_Item_Add_Edit fields for this item (Edit mode)."""
    name = next(f["current_value"] for f in form_fields if f["ws_add_col_name"] == "Object_Name")
    body = {"Object_ID": int(item_id), "View_Version": str(version_id), "Object_Name": name}
    col = field["ws_add_col_name"]
    if re.fullmatch(r"CS\d+_Name", col):
        body["CS1_Name"], body["CS1_value"] = field["title"], value   # custom field: title + value
    else:
        body[col] = value                                              # system field: label value
    data = requests.post(f"{api_url}/QW_Update_Object", json=body,
                         headers={"Authorization": auth, "Content-Type": "application/json"}).json()
    if not data.get("IsSuccess"):
        raise RuntimeError(data.get("Message"))
    # then re-fetch the form and confirm field["ws_add_col_name"] now equals value
```

---

## Used by: BOM Product structures — unit cost (2026-11-02, NOT verified live)

Traceability Matrix `bom_struct_api.py` → `POST /api/bom/structures/cost` writes a PRT's unit cost with
`{"CS1_Name": <cost field title>, "CS1_value": "<number>"}` (+ the current `Object_Name`), the title being the one
the Part Catalog filter reads the cost from. It then re-reads the part through the filter; an unchanged value is
reported as an error (rule *Success does not mean the field changed* above). Whether a tenant's cost field is a
system field that needs its own request key instead of the CS pair is **unknown** — update this section after the
first live write.

## See also
- [Main Skill](SKILL.md) — Base URL, auth, common patterns
- [QW_Get_Item_Add_Edit](qw-get-item-add-edit.md) — current values, titles, picklist labels (read before and after)
- [QW_Add_Object](qw-add-item.md) — Create a work item (sibling create endpoint)
- [QW_Update_Defect](qw-update-defect.md) — Defects are a separate table: use this, not QW_Update_Object
- [QW_Login](qw-login.md) — Session/auth prerequisite
