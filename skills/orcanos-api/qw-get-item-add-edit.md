# QW_Get_Item_Add_Edit — Item Form Buildup (fields, sections, picklists, mandatory rules)

Returns the **form definition** for adding or editing a work item of a given type (CAPA, REQ,
T_CASE, …): every field on the Add/Edit screen, which **section** it lives in, its **display
order**, its **type** (text / combobox / date / html …), picklist **values** for comboboxes, and
**mandatory-field rules** — including *conditional* mandatory rules ("Status cannot be X if
Category is Y"). Use this to render a dynamic Add/Edit form, validate a payload client-side before
calling [QW_Add_Object](qw-add-item.md), or document an item type's field layout.

**Reference:** https://help.orcanos.com/knowledgebase/qw_get_item_add_edit-rest-api/
**Mandatory-field rule reference:** https://help.orcanos.com/knowledgebase/mandatory-field-rule/

---

## Endpoint

```
POST <base>/api/v2/Json/QW_Get_Item_Add_Edit
Authorization: Basic <base64(username:password)>  OR  Bearer <api-key>
Content-Type: application/json
```

`<base>` includes the tenant, e.g. `https://app.orcanos.com/orca60`.
Auth: same options as every endpoint — see [SKILL.md](SKILL.md).
**Prerequisites:** Call [QW_Login](qw-login.md) first for `Project.Id`, `VersionId`, and
`Item_type[].Code` (the `Item_Type` value below).

---

## Request Body

```json
{
  "Item_id": "0",
  "Item_Type": "CAPA",
  "Project_id": 7509,
  "VersionId": 434,
  "CustomerId": "",
  "EditFieldName": ""
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `Item_id` | string | Yes | `"0"` for the **Add** form. A real item id for the **Edit** form — returns current values/`OldValue` and re-evaluates dependent-mandatory rules against that item's data. |
| `Item_Type` | string | Yes | The item type **code** (`Item_type[].Code` from `QW_Login`), e.g. `"CAPA"`, `"REQ"`, `"T_CASE"`. |
| `Project_id` | integer | Yes | Project id (`Project.Id` from `QW_Login`). Form layout/mandatory rules can be project-specific. |
| `VersionId` | integer | Yes | Version id (`Ver_id`) — same id space as `QW_Get_Filter_Results`, **not** `Major_Version`/`Minor_Version`. |
| `CustomerId` | string | No | Leave `""` unless the instance uses customer-scoped forms. |
| `EditFieldName` | string | No | Name of a single field the user just changed in the UI (e.g. `"Category"`). When set, the response re-evaluates **dependent** fields' mandatory/value state against the new value — used to live-update a form as the user fills it in, rather than re-fetching the whole form definition. Leave `""` for the initial form load. |

---

## Response

```json
{
  "IsSuccess": true,
  "Data": {
    "field": [
      {
        "val": [],
        "Text": null,
        "OldValue": null,
        "MultiSelectText": null,
        "SelectedText": null,
        "tooltip": "",
        "name": "Obj_name",
        "default_title": "Name",
        "type": "text",
        "max_length": 255,
        "title": "Synopsis",
        "ws_add_col_name": "Object_Name",
        "ws_edit_col_name": "Object_Name",
        "is_mandatory": "0",
        "mandatory_value": "",
        "dependent_field_name": "",
        "dependent_mandatory_value": "",
        "edit_ind": null,
        "web_order": 3,
        "section": ""
      },
      {
        "val": [
          { "code": "NEW", "label": "New", "auto_assign": "Creator", "auto_assign_id": "5" }
        ],
        "Text": "New",
        "name": "Obj_status",
        "type": "combobox",
        "title": "Status",
        "web_order": 2,
        "section": ""
      }
    ]
  },
  "Message": "",
  "HttpCode": 200
}
```

`Data.field` is an array of field-definition objects (**XML→JSON quirk**: a form with only one
field returns a single object, not a 1-element array — wrap with `ensureArray()`, see
[SKILL.md](SKILL.md)).

### Field object shape

| Property | Notes |
|---|---|
| `name` | Internal field name to submit — usually maps to `QW_Add_Object`'s `ws_add_col_name` (see below), **not** always `name` itself. |
| `default_title` / `title` | `default_title` is the system label (e.g. `"Name"`); `title` is the **tenant-customized** label shown on screen (e.g. `"Synopsis"`). Render `title`, submit by `name`/`ws_*_col_name`. |
| `type` | Field widget: `text`, `combobox`, `date`, `html` (rich text), and others (`number`, `checkbox`, `multiselect` on other item types — not confirmed on this instance, verify per field). |
| `max_length` | Max chars for `text` fields; `0` = not applicable/unbounded. |
| `ws_add_col_name` / `ws_edit_col_name` | The **payload key** to use when calling `QW_Add_Object` (add) or the corresponding update endpoint (edit) for this field — usually the same value, occasionally differs. |
| `section` | Groups fields into form sections/tabs for rendering. Empty string = default/ungrouped section. Group fields by this value, then sort each group by `web_order`. |
| `web_order` | Integer sort key for field display order **within its section**. |
| `val` | For `combobox`/picklist types: array of `{code, label, auto_assign, auto_assign_id}` — the selectable options. `code` is the value to submit, `label` is the display text. `auto_assign`/`auto_assign_id` (seen on Status/Assigned_to) indicate the option auto-fills another field (e.g. selecting status `"New"` auto-assigns `Assigned_to` to `Creator`, id `5`). Empty `[]` for non-picklist types. |
| `Text` / `OldValue` | Current display value (Edit mode) / prior value before a pending change. `null` on Add mode for empty fields. |
| `SelectedText` / `MultiSelectText` | Populated for single/multi-select combobox current selections where applicable. |
| `edit_ind` | Non-null (e.g. `"1"`) marks a field as editable in Edit mode; check per-instance — not all field types set this. |
| `tooltip` | Help text to show near the field label, if any. |
| **`is_mandatory`** | `"1"` = field is always required to submit the form. `"0"` = not unconditionally mandatory (may still become mandatory conditionally — see below). |
| **`mandatory_value`** | When set, the field is only mandatory if its *own* current value matches/doesn't match this — used together with `is_mandatory` for self-referential mandatory rules on some item types. |
| **`dependent_field_name`** | Name of *another* field whose value controls this field's mandatory state. Empty = no dependency. |
| **`dependent_mandatory_value`** | The value `dependent_field_name` must have for **this** field to become mandatory. e.g. if a `Root_Cause` field has `dependent_field_name: "Obj_status"` and `dependent_mandatory_value: "Closed"`, `Root_Cause` becomes required once `Obj_status` is set to `"Closed"` — this is the "Status cannot be X if Category is Y" rule from the mandatory-field-rule doc, expressed the other way round (field Y becomes mandatory once field X = value). |

> ⚠️ None of the fields in the CAPA sample response had `is_mandatory: "1"` set — the exact
> shape of an active dependency (whether `dependent_mandatory_value` holds one value or a
> delimited list) hasn't been confirmed against a live example with real mandatory rules
> configured. Before relying on this for hard validation, fetch the form for an item type known
> to have mandatory-dependency rules configured (Admin → workflow rules) and inspect a field
> with non-empty `dependent_field_name`.

---

## Building a dynamic Add/Edit form

```js
function ensureArray(v) { return Array.isArray(v) ? v : v == null ? [] : [v]; }

function buildFormLayout(getItemAddEditData) {
  const fields = ensureArray(getItemAddEditData?.Data?.field);
  const bySection = {};
  for (const f of fields) {
    const section = f.section || 'General';
    (bySection[section] ??= []).push(f);
  }
  for (const section in bySection) {
    bySection[section].sort((a, b) => (a.web_order ?? 0) - (b.web_order ?? 0));
  }
  return bySection; // { "General": [field, field, ...], "Follow-up": [...] }
}

function fieldOptions(field) {
  return ensureArray(field.val).map(o => ({ value: o.code, label: o.label }));
}

// Is `field` currently mandatory, given the current value of the field it depends on?
function isFieldMandatory(field, currentValues) {
  if (field.is_mandatory === '1') return true;
  if (field.dependent_field_name) {
    const depValue = currentValues[field.dependent_field_name];
    return depValue === field.dependent_mandatory_value;
  }
  return false;
}
```

When the user changes a field in the UI, re-call `QW_Get_Item_Add_Edit` with `EditFieldName` set
to that field's `name` (and the rest of the currently-entered values, if the endpoint accepts them
— verify; the documented request body only shows the identity params) to get the updated mandatory
state for dependent fields, rather than re-implementing the dependency graph client-side.

---

## Failure Responses

| HTTP | Meaning | Fix |
|---|---|---|
| `404` | Wrong path, or `Item_Type` code doesn't exist on this project | Verify `Item_type[].Code` from `QW_Login` |
| `401` | Session expired | Re-authenticate via `QW_Login` |
| `200` + `IsSuccess: false` | Validation error (e.g. bad `Project_id`/`VersionId` combo) | Check `Message` |

---

## See also
- [SKILL.md](SKILL.md) — base URL, auth, XML→JSON quirks
- [QW_Login](qw-login.md) — `Item_type[].Code`, `Project.Id`, `Ver_id`
- [QW_Add_Object](qw-add-item.md) — submit the item using this form's field names/values
- [QW_Get_Object](qw-get-object.md) — read an existing item's current field values (Text-only, no form metadata)
- Mandatory field rule doc: https://help.orcanos.com/knowledgebase/mandatory-field-rule/
