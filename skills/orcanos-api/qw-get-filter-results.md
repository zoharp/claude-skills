# QW_Get_Filter_Results — Query Work Items

## Endpoint

```
POST <base>api/v2/Json/QW_Get_Filter_Results
Authorization: Basic <base64(username:password)> OR Bearer <api-key>
Content-Type: application/json
```

**Auth:** Use **Basic HTTP Auth** or **API Key** — see [main skill](SKILL.md) for details.

---

## ⚠️ Critical: Pagination Settings

**For pagination to work correctly with accurate total record counts, you MUST use:**

```json
{
  "IsNewPaging": "0",
  "IsReturnPageCount": "yes"
}
```

This is **the only combination** that returns both paginated rows AND accurate `Total_records`.

**What breaks pagination:**
- `IsNewPaging: "1"` → `Total_records` becomes unreliable
- `IsReturnPageCount: "0"` → No total count returned
- `IsReturnPageCount: "1"` (numeric) → API returns empty Data (error!)

See [Pagination & Return Types](#pagination--return-types) section below for full details.

---

## Request Body

```json
{
  "Filter_id": "839",
  "Page_no": "1",
  "Page_Size": "50",
  "Item_Type": "MR_REQ",
  "Version_id": "434",
  "Filter_By": "",
  "Order_By": "",
  "IsNewPaging": "0",
  "IsReturnPageCount": "yes",
  "DashboardItemId": "0",
  "IncludeProtectedCol": "true"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `Filter_id` | string | **Yes** | Saved filter ID from Orcanos UI |
| `Page_no` | string | No | 1-based page number (default: "1") |
| `Page_Size` | string | No | Items per page (default: "50") |
| `Item_Type` | string | No | REQ, TC, DEF, etc. See Item Types table below |
| `Version_id` | string | No | Project version ID from `QW_Login` |
| `Filter_By` | string | No | SQL WHERE fragment (appended to filter's WHERE) |
| `Order_By` | string | No | SQL ORDER BY clause |
| `IsNewPaging` | string | No | **MUST be `"0"`** (string) for correct pagination with Total_records |
| `IsReturnPageCount` | string | No | **MUST be `"yes"`** (string) to get both rows AND accurate total count. NOT "0" or "1" |
| `DashboardItemId` | string | No | Dashboard context (optional) |
| `IncludeProtectedCol` | string | No | Include protected columns in response |

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

## Pagination & Return Types

⚠️ **LOAD-BEARING SETTINGS:** This combination is the ONLY one that returns BOTH paginated rows AND accurate `Total_records`:

```json
{
  "IsNewPaging": "0",           // Must be "0" (string)
  "IsReturnPageCount": "yes"    // Must be "yes" (string) — NOT "0" or 1 (numeric)
}
```

### Why This Works

- `IsNewPaging: "0"` + `IsReturnPageCount: "yes"` returns full rows with pagination
- `IsNewPaging: "1"` makes `Total_records` echo `Page_Size` (wrong!)
- `IsReturnPageCount: "0"` returns no total count
- `IsReturnPageCount: "1"` (numeric) causes API to return empty Data (error!)

### What You Get

With the correct settings, the response includes:
```json
{
  "IsSuccess": true,
  "Data": {
    "Object": [...paginated rows...],
    "Total_records": 127          // Accurate total across all pages
  }
}
```

Use `Total_records` to calculate total pages:
```js
const totalPages = Math.ceil(Total_records / pageSize);
```

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
    Filter_id: String(filterId),
    Page_no: String(page),
    Page_Size: String(pageSize),
    Item_Type: itemType,
    Version_id: String(versionId),
    Filter_By: filterBy,
    IsNewPaging: '0',           // MUST be "0" — "1" breaks Total_records
    IsReturnPageCount: 'yes'    // MUST be "yes" — "0" or 1 (numeric) breaks it
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
  const totalRecords = parseInt(data.Data?.Total_records ?? items.length, 10);
  const totalPages = Math.ceil(totalRecords / pageSize);
  
  return {
    items,
    total: totalRecords,
    totalPages,
    hasMore: page < totalPages
  };
}
```

---

## See also
- [Main Skill](SKILL.md) — Base URL, auth, common patterns
- [QW_Login](qw-login.md) — Authenticate and fetch projects/versions
