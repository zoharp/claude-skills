---
name: orcanos-api
description: Use when integrating with the Orcanos QMS REST API — authentication (QW_Login), fetching projects, retrieving work items, or querying filter results (QW_Get_Filter_Results). Covers auth flow, pagination, Filter_By syntax, field extraction, and common gotchas.
---

# Orcanos REST API

Reference docs: `https://help.orcanos.com/knowledgebase/`

All endpoints are under:
```
<baseUrl>api/v2/Json/<endpoint>
```
e.g. `https://us.orcanos.com/<tenant>/api/v2/Json/QW_Login`

All requests use `Basic` auth and `Content-Type: application/json`.

---

## CORS and backend proxy

Browser-direct calls to Orcanos will always fail with CORS errors — Orcanos does not send CORS headers. **The only fix is a server-side proxy.** The frontend must never call Orcanos directly.

In the Orcanos QMS project, all Orcanos API calls go through FastAPI backend proxy endpoints:

| Endpoint | Proxies to |
|---|---|
| `POST /orcanos/proxy/login` | `QW_Login` |
| `POST /orcanos/proxy/filter` | `QW_Get_Filter_Results` |
| `GET /orcanos/auth` | Returns saved credentials status (no Orcanos call) |
| `POST /orcanos/save-creds` | Saves credentials to DB (no Orcanos call) |

**Important**: a CORS error in the browser often means the **backend returned a 500** before CORS headers were injected. Fix the backend error first — don't chase CORS config.

### URL normalization
The backend `_normalize_orcanos_url(url)` helper:
1. Adds `https://` if the URL has no scheme
2. Appends `/api/v2/Json` if the URL doesn't already end with it

So `app.orcanos.com/orca60` becomes `https://app.orcanos.com/orca60/api/v2/Json` automatically.

---

## Authentication — `QW_Login`

```
POST <base>api/v2/Json/QW_Login
Authorization: Basic <base64(username:password)>
Content-Type: application/json
(empty body — no JSON needed)
```

### base64 encoding

`btoa()` alone breaks on non-ASCII characters (accented usernames/passwords). Always encode via UTF-8 bytes first:

```js
function utf8ToBase64(s) {
  const bytes = new TextEncoder().encode(s);
  let bin = '';
  const CHUNK = 0x8000;
  for (let i = 0; i < bytes.length; i += CHUNK)
    bin += String.fromCharCode.apply(null, bytes.subarray(i, i + CHUNK));
  return btoa(bin);
}

const authHeader = 'Basic ' + utf8ToBase64(`${username}:${password}`);
```

### Success response

**CRITICAL: `Data.Projects` is NOT a plain array.** It is an XML-to-JSON object `{"Project": [...]}`. The actual project array is at `Data.Projects.Project`:

```json
{
  "IsSuccess": true,
  "Data": {
    "User_details": { "User_name": "orca", "Display_name": "Zohar Peretz", "Virtual_dir": "orca60", ... },
    "Projects": {
      "Project": [
        {
          "Id": "14667",
          "Project_name": "Agile SCRUM",
          "Is_solution": "0",
          "Display": "Y",
          "Version": [
            { "Ver_id": "438", "Version_label": "1.0", "List_label": "Agile SCRUM (1.0.0)", "Is_lock": "N" }
          ],
          "Item_type": [
            { "Code": "REQ", "Label": "Product Requirement", "Permission": "DUOTAYXBF" },
            { "Code": "T_CASE", "Label": "Test Case", "Permission": "DUOTYXABF" }
          ],
          "Modules_permissions": { ... }
        }
      ]
    },
    "Configurations": { "Idle_time": "45" }
  }
}
```

A project can have **multiple versions** — `Version` is always an array (even for single-version projects).

### URL format (tenant-aware)

The base URL **must include the tenant path**:
```
https://app.orcanos.com/<tenant>/api/v2/Json
```
e.g. `https://app.orcanos.com/orca60/api/v2/Json`

The tenant name is returned in `User_details.Virtual_dir` after successful login.

### Failure responses

| HTTP | Meaning |
|---|---|
| `401` | Bad credentials |
| `200` + `IsSuccess: false` | Auth rejected at application level; check `data.Message` |

### Idle time

Session timeout is in `Data.Configurations.Idle_time` (minutes), **not** `Data.Idle_time`.

### What to store

Store the URL and username; do not store plaintext password in localStorage. In the Orcanos QMS project, credentials are saved to the `accounts` table (encrypted server-side) via `POST /orcanos/save-creds` after a successful login.

---

## Projects

`Data.Projects.Project` is the project array (XML-to-JSON nested object — see response above).

Each project has:
- `Id` — project ID (string)
- `Project_name` — project name
- `Version[]` — array of versions, each with `Ver_id` (the value to pass to `QW_Get_Filter_Results` as `Version_id`)
- `Item_type[]` — work item types available in this project, each with `Code` and `Label`

**The `Version_id` for `QW_Get_Filter_Results` is `Version[N].Ver_id`, NOT `Id`.**

For multi-version projects, each version is a separate target for filter queries.

### Extracting projects safely

```js
const raw = data.Data?.Projects;
// Handle XML-to-JSON dict wrapper {"Project": [...]} OR plain array
let projectList = [];
if (Array.isArray(raw)) {
  projectList = raw;
} else if (raw?.Project) {
  projectList = Array.isArray(raw.Project) ? raw.Project : [raw.Project];
}

// Normalize: expand multi-version projects, add Version_id field
const projects = [];
for (const p of projectList) {
  const versions = Array.isArray(p.Version) ? p.Version
    : p.Version ? [p.Version] : [];
  if (versions.length <= 1) {
    projects.push({ ...p, Version_id: versions[0]?.Ver_id ?? p.Id });
  } else {
    for (const v of versions) {
      const label = v.Version_label || '';
      projects.push({
        ...p,
        Version_id: v.Ver_id,
        Project_name: label ? `${p.Project_name} (${label})` : p.Project_name,
      });
    }
  }
}
```

---

## Fetching work items — `QW_Get_Filter_Results`

```
POST <base>api/v2/Json/QW_Get_Filter_Results
Authorization: Basic <auth>
Content-Type: application/json

{
  "Filter_id":         <int>,      // required — which saved filter to run
  "Page_no":           1,          // 1-based
  "Page_Size":         50,
  "Item_Type":         "PRT",      // see Item Types below
  "Version_id":        <int>,      // project id from login
  "Filter_By":         "...",      // optional SQL WHERE clause (see below)
  "IsNewPaging":       0,          // see Pagination gotchas
  "IsReturnPageCount": 0           // see Pagination gotchas
}
```

### Item Types

| Value | Meaning |
|---|---|
| `PRT` | Part / Product (top-level items) |
| `PI`  | Part Instance (child of a PRT — a "usage" row) |
| `CR`  | Change Request / ECO |
| `REQ` | Requirement |
| `TC`  | Test Case |
| `TS`  | Test Suite |
| `TSK` | Task |
| `DOC` | Document |
| `DEF` | Defect / Bug |

The valid types depend on what the filter was configured for in Orcanos. Use the type that matches the filter.

### Item type field differences

Not all item types share the same internal field names. Key differences:

| Item type | Name/title field | Notes |
|---|---|---|
| REQ, TC, TSK, PRT, DOC | `Obj_name` | Standard name field |
| DEF (Defect) | `Synopsis` | Defects use `Synopsis` instead of `Obj_name` |

When extracting the title/name of a work item, always try both:
```python
name_f = next((f for f in fields if f.get("Name") in ("Obj_name", "Synopsis")), None)
```

In the Orcanos QMS backend (`api.py` and `etl.py`), both field names are already tried in this order.

### Success response

```json
{
  "IsSuccess": true,
  "Data": {
    "Object": [
      {
        "Id":   "12345 (9876)",
        "Type": "PRT",
        "Field": [
          { "Name": "Obj_name",    "Title": "Name",   "Text": "Widget A",  "Web_order": 1 },
          { "Name": "User_Prefix", "Title": "Key",    "Text": "PRT-9876",  "Web_order": 2 },
          { "Name": "Status",      "Title": "Status", "Text": "12",        "Display_text": "Approved", "Web_order": 3 }
        ]
      }
    ],
    "Total_records": 124
  }
}
```

### Failure

`IsSuccess: false` — check `data.Data` (may be a string message) or `data.Message`. A 401 HTTP response means the session expired.

---

## Pagination gotchas

**`IsNewPaging` and `IsReturnPageCount` interact — this combination must be exact:**

| Goal | `IsNewPaging` | `IsReturnPageCount` | Effect |
|---|---|---|---|
| Top-level rows + accurate total | `0` | `"yes"` (string) | Returns rows AND truthful `Total_records` |
| Children / filtered rows (no total needed) | `0` | `0` | Returns rows; `Total_records` may be unreliable |

**Critical:**
- `IsReturnPageCount` must be the **string** `"yes"` or `"true"` to get a truthful total. Passing the integer `1` or boolean `true` returns `Data: ""` (empty).
- `IsNewPaging: 1` causes `Total_records` to echo back `Page_Size` instead of the real count.
- When `IsReturnPageCount` is `0`, use `rows.length >= pageSize` as a "has more pages" fallback.

---

## Filter_By — SQL WHERE clause

`Filter_By` is a SQL WHERE fragment appended to the filter's own WHERE clause. It supports standard SQL operators and some Orcanos-specific extensions.

### Common patterns

```sql
-- exact match on a field by name
[Obj_name] = 'Widget A'

-- partial text search
[Obj_name] LIKE '%widget%'

-- numeric field (no quotes)
parent_original_id = 39382

-- IN list
ID IN (1, 2, 3)

-- subquery (Orcanos table-valued functions are supported)
ID IN (select * from dbo.fn_GetRootParentByCS21('39382'))

-- AND multiple clauses
([Obj_name] LIKE '%foo%') AND (Status = 'Active')
```

### Field references

- Use `[Field Name]` (bracket-quoted) for fields that contain spaces.
- Use bare names for system columns like `ID`, `parent_original_id`, `Status`.
- Escape single quotes by doubling them: `'O''Brien'`.

---

## Parsing the response — field extraction

Each item in `Data.Object` has a `Field` array. Fields have:

| Property | Meaning |
|---|---|
| `Name` | Internal programmatic name (e.g. `User_Prefix`, `PI_Status`) |
| `Title` | Human-readable label (e.g. `Key`, `Status`) |
| `Text` | Stored value — for picklist fields this is the internal id |
| `Display_text` | Human-readable picklist label — prefer this over `Text` |
| `Display` | Alternative display field (some versions) |
| `Value` | Alternative raw value (some versions) |
| `Web_order` | Integer — sort ascending for column order |

**Best-effort field extraction:**

```js
// Sort fields by Web_order for display
const fields = [...obj.Field].sort((a, b) =>
  (parseInt(a.Web_order) || 0) - (parseInt(b.Web_order) || 0)
);

// Get display-safe value: prefer Display_text so picklists show labels
const fieldText = (f) => f?.Display_text || f?.Display || f?.Text || f?.Value || '';

const byName  = (n) => fieldText(fields.find(f => f.Name  === n));
const byTitle = (t) => fieldText(fields.find(f => f.Title === t));
```

Use `byTitle` as a fallback when different item types use different `Name`s for the same logical field (e.g. `Status` vs `PI_Status`, both with `Title: "Status"`).


### `_field_titles` — persisting the Name→Title mapping for scoring

When indexing Orcanos items, store a `_field_titles` dict in each chunk's metadata so that display captions survive beyond the ETL run:

```python
# In ETL, after building the metadata dict keyed by Name:
_titles = {
    f["Name"]: f["Title"]
    for f in fields_sorted
    if f.get("Name") and f.get("Title") and f["Title"] != f["Name"]
}
if _titles:
    metadata["_field_titles"] = _titles
```

`_field_titles` is keyed by internal `Name` and maps to the human-readable `Title`. Only fields where `Title != Name` are included (avoids cluttering when there is no useful caption).

This is used by the scoring feature:

```python
from scoring import extract_field_titles, aggregate_metadata

rows = get_chunk_metadata_sample(repo_id)          # fetched chunks with metadata
field_titles = extract_field_titles(rows)           # merges _field_titles across rows
summary = aggregate_metadata(rows)                  # skips the _field_titles key itself
prompt = build_analyze_prompt(summary, field_titles=field_titles)
```

Formula rules carry both `field` (internal `Name`, used in DB matching) and `title` (display caption shown to users). Example rule:

```json
{ "field": "defect_severity", "title": "Severity", "value": "Critical", "weight": 40 }
```

Scoring UI shows `title` ("Severity"); internal scoring logic uses `field` ("defect_severity"). For newly-added rules without a title, the `field` value itself is displayed as a fallback.
---

## Parsing the Id field

The top-level `Id` arrives as a string like `"46584 (42195)"`. The parenthetical number is the canonical numeric item id (used for URL building and as `parent_original_id` for children):

```js
function extractItemId(id) {
  const m = String(id ?? '').match(/\((\d+)\)\s*$/);
  return m ? m[1] : String(id).replace(/[^\d]/g, '');
}
```

---

## Orcanos web item URL

```js
function itemUrl(baseUrl, versionId, type, itemId) {
  return `${baseUrl}web/${versionId}/items/view?Item=${encodeURIComponent(type)}&ItemId=${encodeURIComponent(itemId)}`;
}
// e.g. https://us.orcanos.com/acme/web/5/items/view?Item=PRT&ItemId=9876
```

---

## Session expiry / 401 handling

Any API call (not just login) can return HTTP 401 when the session has expired. Handle it uniformly:

```js
if (resp.status === 401) {
  // clear stored auth, redirect to login
}
```

`Data.Idle_time` from the login response is the inactivity timeout in minutes. Use it to warn the user or auto-logout before the server expires the session.

---

## Full minimal example (JavaScript, browser + proxy)

```js
const BASE = '/api/orcanos/';  // proxied to https://us.orcanos.com/<tenant>/api/v2/Json/

// 1. Login
async function login(username, password) {
  const auth = 'Basic ' + utf8ToBase64(`${username}:${password}`);
  const r = await fetch(BASE + 'QW_Login', {
    method: 'POST',
    headers: { Authorization: auth, 'Content-Type': 'application/json' },
  });
  if (r.status === 401) throw new Error('Bad credentials');
  const data = await r.json();
  if (!data.IsSuccess) throw new Error(data.Message || 'Login failed');
  sessionStorage.setItem('auth', auth);
  return data.Data;  // .Projects, .User_details, .Idle_time
}

// 2. Fetch items from a filter
async function fetchItems({ filterId, versionId, itemType, page = 1, pageSize = 50, filterBy = '' }) {
  const auth = sessionStorage.getItem('auth');
  const body = {
    Filter_id: filterId,
    Page_no: page,
    Page_Size: pageSize,
    Item_Type: itemType,
    Version_id: versionId,
    IsNewPaging: 0,
    IsReturnPageCount: 'yes',
  };
  if (filterBy) body.Filter_By = filterBy;
  const r = await fetch(BASE + 'QW_Get_Filter_Results', {
    method: 'POST',
    headers: { Authorization: auth, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (r.status === 401) throw new Error('Session expired');
  const data = await r.json();
  if (!data.IsSuccess) throw new Error(data.Data || data.Message || 'Filter failed');
  return { items: data.Data?.Object ?? [], total: data.Data?.Total_records ?? 0 };
}

// 3. Extract a field value from an item
function fieldValue(item, nameOrTitle) {
  const f = item.Field?.find(f => f.Name === nameOrTitle || f.Title === nameOrTitle);
  return f?.Display_text || f?.Display || f?.Text || f?.Value || '';
}
```

---

## Common issues

| Symptom | Cause | Fix |
|---|---|---|
| CORS error in browser | Direct call to Orcanos host OR backend 500 before CORS headers injected | Route through proxy; fix any backend 500 first |
| `500 Internal Server Error` on `/orcanos/proxy/login` | Backend expects `Projects` to be an array, but it's `{"Project": [...]}` | Extract inner `raw_node.get("Project")` list |
| `KeyError: 0` on `projects[0]` | `projects` was assigned the dict wrapper, not the inner list | See project extraction pattern above |
| `orcanosProjects.map is not a function` | Frontend received a non-array from the backend | Wrap with `Array.isArray(raw) ? raw : []` before setting state |
| Projects dropdown empty | `Data.Projects` extraction failed silently | Log the raw `Data.Projects` value — it's probably `{"Project": [...]}` |
| `Data: ""` (empty) | `IsReturnPageCount: 1` (numeric) | Use `"yes"` string |
| `Total_records` equals `Page_Size` | `IsNewPaging: 1` | Use `IsNewPaging: 0` |
| Picklist shows numeric id, not label | Reading `Text` directly | Use `Display_text` first |
| Filter returns no results | Wrong `Item_Type` for the filter | Match `Item_Type` to what the filter was built for |
| 404 on login | Missing tenant path in URL | URL must be `https://app.orcanos.com/<tenant>/api/v2/Json` |
| `btoa` throws `InvalidCharacterError` | Non-ASCII in credentials | Use UTF-8 → base64 helper above |

