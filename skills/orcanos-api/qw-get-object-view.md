# Get Every Form Field of an Item — QW_Get_Object_View

Returns **one work item's full form**: every field with its `Name` (internal, e.g. `CS94`),
`Title` (what the form shows, e.g. `Hazard`), `Type`, `Text` and `Code`. Prefer it over
[QW_Get_Object](qw-get-object.md) when you need field **titles** or picklist **labels**.

Verified live against orca60, RISK-25833 / Ver_Id 434 (2026-10-09).

---

## Endpoint

```
POST <base>/api/v2/Json/QW_Get_Object_View
Authorization: Basic <base64(username:password)>
Content-Type: application/json

{ "Item_id": "25833", "Item_Type": "RISK", "Ver_Id": 434, "IsParseDynamicFilter": 0 }
```

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `Item_id` | string | **Yes** | The **display id** (`25833`), not `RISK-25833` |
| `Item_Type` | string | **Yes (in practice)** | The type **code** (`RISK`, `SRS`, `T_CASE`) |
| `Ver_Id` | int | **Yes (in practice)** | The project **version** id the item lives in |
| `IsParseDynamicFilter` | int | No | `0` |

> ⚠️ Swagger marks nothing required, but **`{"Item_id": "25833"}` alone answers HTTP 500**
> `"Index 0 is either negative or above rows count."` Send the type and the version.

---

## Response

```json
{ "IsSuccess": true, "Data": {
    "Id": "25833", "Type": "RISK", "Type_description": "Risk", "Project_id": "7509",
    "Original_id": "25833", "Dms_routing_state": "DRAFT", "Eco_no": "", ...,
    "Section": [
      { "Path": {...}, "Work_item_section": {...}, "Field": [
          { "Type": "text",       "Name": "Obj_name",   "Title": "Name",   "Text": "Risk Template # 1(1)", "Code": null },
          { "Type": "combobox",   "Name": "Obj_status", "Title": "Status", "Text": "Identify Hazard", "Code": "NEW" },
          { "Type": "numeric",    "Name": "CS4",        "Title": "S1",     "Text": "3-Serious", "Code": null },
          { "Type": "checkBox",   "Name": "CS129",      "Title": "Acceptable?", "Text": "0" },
          { "Type": "richEditor", "Name": "CS94",       "Title": "Hazard", "Text": "<p>Hazard desc</p>\n" },
          { "Type": "html",       "Name": "Description",         "Title": "Description", "Text": "![CDATA[]]" },
          { "Type": "html",       "Name": "dynamic_description", "Title": "Description", "Text": "![CDATA[]]" }
      ]},
      { "Name": "Relations",   "Type": "tab", "Field": [] },
      { "Name": "Attachments", "Type": "tab", "Field": [] },
      { "Name": "History",     "Type": "tab", "Field": [] },
      { "Name": "ESign",       "Type": "tab", "Field": [] },
      { "Name": "Record",      "Type": "tab", "Field": [] }
] } }
```

**Quirks:**
- Picklist `Text` is the **label** (`"3-Serious"`); QW_Get_Object gives the code (`"3"`).
- `Description` is wrapped `"![CDATA[...]]"`; a duplicate comes as `dynamic_description` — skip it.
- Checkbox `Text` is `"0"` / `"1"`. Rich-text fields carry HTML.
- Sections with `Type: "tab"` have no fields — skip them.
- Calculated fields (`RPN1`, `RPN2`) that QW_Get_Object returns may be **absent** here.
- `Data.Type` echoes the type — **check it**; do not trust a mismatch.
- `Field.Section` is a section **ID** (see the Item Add/Edit note on `work_item_section`).

Used by traceability-matrix `src/backend/source_item.py` (Critical Note #98).
