# QW_Get_Filter_Results — Query Work Items

## Endpoint

```
POST <base>api/v2/Json/QW_Get_Filter_Results
Authorization: Basic <base64(username:password)> OR Bearer <api-key>
Content-Type: application/json
```

**Auth:** Use **Basic HTTP Auth** or **API Key** — see [main skill](SKILL.md) for details.

---

## Request Body

```json
{
  "Filter_id": 123,
  "Page_no": 1,
  "Page_Size": 50,
  "Item_Type": "REQ",
  "Version_id": 438,
  "Filter_By": "[Obj_name] LIKE '%widget%'",
  "IsNewPaging": 0,
  "IsReturnPageCount": "yes"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `Filter_id` | int | **Yes** | Saved filter ID from Orcanos UI |
| `Page_no` | int | No | 1-based page number (default: 1) |
| `Page_Size` | int | No | Items per page (default: 50) |
| `Item_Type` | string | No | See Item Types table below |
| `Version_id` | int | No | Project version ID from `QW_Login` |
| `Filter_By` | string | No | SQL WHERE fragment (appended to filter's WHERE) |
| `IsNewPaging` | int | No | Use `0` (default: 0, use 1 is broken) |
| `IsReturnPageCount` | string\|int | No | Use `"yes"` string for truthful total (NOT numeric 1) |

---

## Item Types

| Code | Meaning |
|---|---|
| `PRT` | Part / Product (top-level item) |
| `PI` | Part Instance (child of PRT — "usage" row) |
| `CR` | Change Request / ECO |
| `REQ` | Requirement |
| `TC` | Test Case |
| `TS` | Test Suite |
| `TSK` | Task |
| `DOC` | Document |
| `DEF` | Defect / Bug |

Must match the filter's configured type. Filter returns empty if types don't match.

---

## Field name quirks by item type

Not all item types use the same field names. When extracting name/title:

| Item Type | Name Field | Notes |
|---|---|---|
| REQ, TC, TSK, PRT, DOC | `Obj_name` | Standard |
| DEF (Defect) | `Synopsis` | Different field |

**Always try both when generic:**
```js
function getItemName(item) {
  return fieldValue(item, 'Obj_name') || fieldValue(item, 'Synopsis') || 'Unnamed';
}
```

---

## Success Response

```json
{
  "IsSuccess": true,
  "Data": {
    "Object": [
      {
        "Id": "12345 (9876)",
        "Type": "REQ",
        "Field": [
          { "Name": "Obj_name", "Title": "Name", "Text": "User Login", "Web_order": 1 },
          { "Name": "Status", "Title": "Status", "Text": "2", "Display_text": "Approved", "Web_order": 3 },
          { "Name": "Owner", "Title": "Owner", "Text": "zohar", "Web_order": 5 }
        ]
      }
    ],
    "Total_records": 127
  }
}
```

### Extract field values

Each item's `Field` is an array of field objects:

| Property | Meaning | Use |
|---|---|---|
| `Name` | Internal field name (e.g. `Obj_name`, `Status`) | Database lookups |
| `Title` | Human-readable label | Display to user |
| `Text` | Raw stored value (for picklists, this is internal id) | Database operations |
| `Display_text` | Picklist label (if applicable) | **Prefer this for display** |
| `Web_order` | Sort order (ascending) | Column ordering |

**Safe field extractor:**
```js
function fieldValue(item, nameOrTitle) {
  const f = item.Field?.find(f => 
    f.Name === nameOrTitle || f.Title === nameOrTitle
  );
  // Prefer Display_text for picklists; fall back to raw Text
  return f?.Display_text || f?.Display || f?.Text || f?.Value || '';
}

// Sort fields by web order
const fields = [...item.Field].sort((a, b) =>
  (parseInt(a.Web_order) || 0) - (parseInt(b.Web_order) || 0)
);
```

---

## Parse Item ID

The `Id` field is a string like `"12345 (9876)"`. The parenthetical number is the canonical numeric id:

```js
function extractItemId(id) {
  const m = String(id ?? '').match(/\((\d+)\)\s*$/);
  return m ? m[1] : String(id).replace(/[^\d]/g, '');
}
```

---

## Build web links

```js
function itemUrl(baseUrl, versionId, type, itemId) {
  return `${baseUrl}web/${versionId}/items/view?Item=${encodeURIComponent(type)}&ItemId=${encodeURIComponent(itemId)}`;
}
// e.g. https://app.orcanos.com/orca60/web/438/items/view?Item=REQ&ItemId=9876
```

---

## Filter_By — SQL WHERE clauses

`Filter_By` is a SQL WHERE fragment appended to the filter's existing WHERE. Supports standard SQL operators.

### Examples

```sql
-- Exact match (string)
[Obj_name] = 'Widget A'

-- Partial text (case-insensitive)
[Obj_name] LIKE '%widget%'

-- Numeric field
parent_original_id = 39382

-- IN list
ID IN (1, 2, 3)

-- Subquery (Orcanos functions supported)
ID IN (select * from dbo.fn_GetRootParentByCS21('39382'))

-- AND combine
([Obj_name] LIKE '%foo%') AND (Status = 'Active')
```

### Rules

- Field names with spaces: use `[brackets]`
- System columns: bare names (e.g. `ID`, `parent_original_id`)
- Escape single quotes: double them (`'O''Brien'`)

---

## Pagination gotchas

**`IsNewPaging` and `IsReturnPageCount` are finicky. Use these exact values:**

```json
{
  "IsNewPaging": 0,
  "IsReturnPageCount": "yes"
}
```

| Config | Effect | Warning |
|---|---|---|
| `IsReturnPageCount: "yes"` | Truthful `Total_records` | Must be **string**, not numeric |
| `IsReturnPageCount: 1` (numeric) | Returns `Data: ""` (empty) | **BROKEN** — use `"yes"` |
| `IsNewPaging: 1` | `Total_records` echoes `Page_Size` | Don't use — always use 0 |
| `IsReturnPageCount: 0` | `Total_records` unreliable | Use `rows.length >= pageSize` as "has more" |

---

## Failure Responses

| HTTP | Meaning | Fix |
|---|---|---|
| `401` | Session expired | Re-authenticate via `QW_Login` |
| `200` + `IsSuccess: false` | API error | Check `data.Message` or `data.Data` |
| Empty `Data.Object` | Filter returned no results | Verify `Item_Type` matches filter config |

---

## Full Example (JavaScript + Proxy)

```js
const BASE = '/api/orcanos/';

async function fetchItems({
  filterId,
  versionId,
  itemType = 'REQ',
  page = 1,
  pageSize = 50,
  filterBy = ''
}) {
  const auth = sessionStorage.getItem('auth');
  const body = {
    Filter_id: filterId,
    Page_no: page,
    Page_Size: pageSize,
    Item_Type: itemType,
    Version_id: versionId,
    IsNewPaging: 0,
    IsReturnPageCount: 'yes'  // string!
  };
  if (filterBy) body.Filter_By = filterBy;

  const r = await fetch(BASE + 'filter', {
    method: 'POST',
    headers: {
      Authorization: auth,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(body)
  });

  if (r.status === 401) throw new Error('Session expired');
  const data = await r.json();
  if (!data.IsSuccess) throw new Error(data.Data || data.Message || 'Filter failed');

  const items = data.Data?.Object ?? [];
  return {
    items,
    total: parseInt(data.Data?.Total_records ?? 0, 10),
    hasMore: items.length >= pageSize
  };
}
```

---

## See also
- [Router & Auth Patterns](SKILL.md) — Base URL, CORS, common patterns
- [QW_Login](qw-login.md) — Authenticate and fetch projects/versions
