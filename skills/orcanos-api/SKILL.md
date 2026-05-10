---
name: orcanos-api
description: Use when integrating with the Orcanos REST API — authentication, reading items with QW_Get_Filter_Results, writing items with QW_Add_Object/QW_Update_Object, managing test steps, and creating traceability links. Covers both JavaScript (browser/Vercel) and Python (server-side) patterns with all known gotchas.
---

# Orcanos API Integration

All Orcanos REST API calls follow the same envelope: POST to `<baseUrl>api/v2/Json/<endpoint>` with the appropriate auth header. Every response is `{ "IsSuccess": true|false, "Data": {...}, "Message": "..." }`. Always check `IsSuccess` before using `Data`.

Full API reference: https://help.orcanos.com/knowledgebase/

---

## Auth — two patterns

### Pattern A: Basic auth (browser / JavaScript)
Used when the end-user logs in with their own Orcanos username and password.

```js
// Encode UTF-8 safely — btoa() alone breaks on accented characters
function utf8ToBase64(s) {
  const bytes = new TextEncoder().encode(s);
  let bin = '';
  const CHUNK = 0x8000;
  for (let i = 0; i < bytes.length; i += CHUNK)
    bin += String.fromCharCode.apply(null, bytes.subarray(i, i + CHUNK));
  return btoa(bin);
}

const authHeader = 'Basic ' + utf8ToBase64(`${username}:${password}`);

// Store only the encoded header — never the plaintext password
localStorage.setItem('orcanos_auth', authHeader);
```

Call `QW_Login` to validate and get project metadata:

```js
const resp = await fetch('/api/orcanos/QW_Login', {
  method: 'POST',
  headers: {
    Authorization: authHeader,
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});
const data = await resp.json();
if (!data.IsSuccess) throw new Error(data.Message || 'Login failed');
// data.Data.Projects — list of projects the user can access
// data.Data.User_details — user name etc.
// data.Data.Idle_time — session timeout in minutes
```

### Pattern B: API key (server-side / Python)
Used in backend scripts that access Orcanos without a user session.

```python
import os, requests

session = requests.Session()
session.headers.update({
    'OrcanosAPIKey': os.environ['ORCANOS_API_KEY'],
    'Content-Type': 'application/json',
})

def _post(endpoint: str, payload: dict) -> dict:
    url = f"{BASE_URL}/api/v2/Json/{endpoint}"
    resp = session.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data.get('IsSuccess'):
        raise RuntimeError(f"Orcanos API error [{endpoint}]: {data}")
    return data.get('Data', {})
```

`ORCANOS_API_KEY` goes in `.env` — never in source code.

---

## CORS (browser only)

Browser calls to Orcanos are blocked by CORS in most deployments. Use a proxy:

**Vercel — `vercel.json`:**
```json
{
  "rewrites": [
    {
      "source": "/api/orcanos/:path*",
      "destination": "https://us.orcanos.com/covaris/api/v2/Json/:path*"
    }
  ]
}
```

**Vite dev — `vite.config.js`:**
```js
server: {
  proxy: {
    '/api/orcanos': {
      target: 'https://us.orcanos.com/covaris/',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api\/orcanos/, 'api/v2/Json'),
    },
  },
}
```

Then always call `/api/orcanos/<endpoint>` — never the Orcanos URL directly from the browser.

---

## Reading items — QW_Get_Filter_Results

This is the only read endpoint. All data comes through saved filters.

### Request shape

```js
// JavaScript
const body = {
  Filter_id: <int>,           // filter ID from Orcanos (e.g. 609 for BOMs)
  Page_no: 1,
  Page_Size: 100,
  Item_Type: 'PRT',           // 'PRT', 'PI', 'REQ', 'T_CASE', 'CR', etc.
  Version_id: <int>,          // project/version ID
  Filter_By: '',              // optional SQL WHERE clause — see below
  IsNewPaging: 0,
  IsReturnPageCount: 0,       // see gotchas below
};

const resp = await fetch('/api/orcanos/QW_Get_Filter_Results', {
  method: 'POST',
  headers: { Authorization: getAuth(), 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
});
const data = await resp.json();
// data.Data.Object — array of items
// data.Data.Total_records — total count (only reliable with specific combo — see gotchas)
```

```python
# Python
payload = {
    'Filter_id': filter_id,
    'Page_no': page,
    'Page_Size': page_size,
    'Item_Type': item_type,
    'Version_id': project_id,
    'Filter_By': filter_by or '',
    'IsNewPaging': 0,
    'IsReturnPageCount': 0,
}
data = _post('QW_Get_Filter_Results', payload)
items = data.get('Object', []) if isinstance(data, dict) else []
```

### ⚠️ Paging gotchas — do not change without testing

| Use case | IsNewPaging | IsReturnPageCount | Result |
|---|---|---|---|
| Top-level fetch (need row count) | `0` | `"yes"` (string!) | Returns rows AND truthful `Total_records` |
| Children fetch (no count needed) | `0` | `0` | Returns rows only |
| Any other combination | — | — | Either empty `Data: ""` or `Total_records` echoes `Page_Size` |

`IsReturnPageCount` must be the **string** `"yes"` or `"true"` — not boolean `true` or integer `1`. Numeric/boolean values return an empty response.

### Filter_By — SQL WHERE clauses

```js
// Server-side name search (case-insensitive LIKE)
Filter_By: `[Obj_name] LIKE '%${q.replace(/'/g, "''")}%'`

// Children of a parent (use parent_original_id, not obj_name)
Filter_By: `parent_original_id = ${parentOriginalId}`  // no quotes — numeric

// Items by ID list (Where-Used / reverse lookup)
Filter_By: `ID IN (select * from dbo.fn_GetRootParentByCS21('${id}'))`

// AND two clauses
Filter_By: `(${clause1}) AND (${clause2})`
```

Always escape single quotes in user input: `.replace(/'/g, "''")`.

### Response structure

```js
// Raw Orcanos Object record:
{
  Id: "46584 (42195)",        // string — parenthetical is the canonical numeric ID
  Type: "PRT",
  Field: [
    { Name: "Obj_name", Title: "Name", Text: "...", Display_text: "...", Web_order: 1 },
    { Name: "Status",   Title: "Status", Text: "12", Display_text: "Active", Web_order: 2 },
    // ...
  ]
}
```

### Normalizing a row (JavaScript)

```js
function normalizeRow(obj) {
  const fields = (obj.Field || []).sort((a, b) =>
    parseInt(a.Web_order || 0) - parseInt(b.Web_order || 0)
  );

  // Prefer Display_text (human label) over Text (internal ID) for picklists
  const fieldText = (f) => (f && (f.Display_text || f.Display || f.Text || f.Value || '')) || '';
  const byName  = (n) => fieldText(fields.find(f => f.Name  === n));
  const byTitle = (t) => fieldText(fields.find(f => f.Title === t));

  // Extract numeric ID from parenthetical: "46584 (42195)" → "42195"
  const idStr = obj.Id ?? '';
  const m = String(idStr).match(/\((\d+)\)\s*$/);
  const itemId = m ? m[1] : String(idStr).replace(/[^\d]/g, '');

  return {
    id: idStr,
    itemId,
    type: obj.Type ?? '',
    fields,        // sorted Field array — iterate for column rendering
    byName,        // lookup by field Name
    byTitle,       // lookup by field Title
    objName:  byName('Obj_name') || byTitle('Obj_name'),
    userPrefix: byName('User_Prefix'),
    raw: obj,
  };
}
```

Key points:
- `fields` are sorted by `Web_order` — use this order for column rendering
- Picklist fields put the human label in `Display_text`, internal ID in `Text` — prefer `Display_text`
- Some filters use `Name`, others use `Title` for the same field — check both via `byName` and `byTitle`
- `Id` is a string that may contain a parenthetical numeric ID — extract it for URL building

---

## Creating items — QW_Add_Object

```python
# Python
payload = {
    'Project_ID': project_id,          # int
    'Major_Version': 1,
    'Minor_Version': 0,
    'Object_Name': 'REQ-001 My requirement title',
    'Object_Type': 'REQ',              # exact type string: 'REQ', 'T_CASE', 'PRT', etc.
    'Description': '<b>Description:</b><br>The system shall...',  # HTML allowed
    'External_ID': 'REQ-001',          # your own ID for dedup
    'Insert_to_Pool': 'Y',             # always 'Y' — required
}
data = _post('QW_Add_Object', payload)

# Response Data is either an int (the new Orcanos item ID) or a dict with Id/id key
if isinstance(data, int):
    orcanos_id = str(data)
else:
    orcanos_id = str(data.get('Id') or data.get('id') or '')
```

Always include `"Insert_to_Pool": "Y"`. Without it, items may be created in an inaccessible pool.

---

## Updating items — QW_Update_Object

```python
payload = {
    'Project_ID': project_id,
    'Object_ID': int(orcanos_id),      # must be int
    'Object_Name': 'REQ-001 Updated title',
    'Description': '<b>Updated description</b>',
}
_post('QW_Update_Object', payload)
```

---

## Test steps — QW_Add_Step / UpdateStep

```python
# Add a new step
def add_step(test_orcanos_id: str, step_number: int, description: str, expected_value: str):
    _post('QW_Add_Step', {
        'ItemId': str(test_orcanos_id),
        'ItemType': 'T_CASE',
        'ProjectId': str(project_id),
        'ReferStepId': '0',
        'ReferPosition': '0',
        'Description': description,
        'ExpectedValue': expected_value,
    })

# Update an existing step
def update_step(test_orcanos_id: str, step_number: int, description: str, expected_value: str):
    _post('UpdateStep', {
        'ItemId': int(test_orcanos_id),   # int here, not str
        'ObjectType': 'T_CASE',
        'CurrentStepNumber': str(step_number),
        'Description': description,
        'ExpectedValue': expected_value,
    })
```

Note the type difference: `QW_Add_Step` uses string `ItemId`, `UpdateStep` uses int `ItemId`.

---

## Traceability links — QW_AddRelation

Creates a directional link between two items. Convention: source=test, target=requirement.

```python
def add_relation(req_orcanos_id: str, test_orcanos_id: str):
    _post('QW_AddRelation', {
        'SourceIdKeys': f'T_CASE-{test_orcanos_id}',
        'TargetIdKeys': f'REQ-{req_orcanos_id}',
    })
```

Format: `"<TYPE>-<orcanos_id>"` — use the Orcanos item type prefix, then the numeric Orcanos ID (not your External_ID).

---

## Build the Orcanos web URL (for linking)

```js
// JavaScript
function orcanosItemUrl({ baseUrl, versionId, type, itemId }) {
  return `${baseUrl}web/${versionId}/items/view?Item=${encodeURIComponent(type)}&ItemId=${encodeURIComponent(itemId)}`;
}
// e.g. https://us.orcanos.com/covaris/web/5/items/view?Item=PRT&ItemId=42195
```

---

## Error handling

### JavaScript / browser
```js
async function orcanosRequest(endpoint, body) {
  const auth = localStorage.getItem('orcanos_auth');
  if (!auth) throw { code: 401, message: 'Not authenticated' };

  const resp = await fetch(`/api/orcanos/${endpoint}`, {
    method: 'POST',
    headers: { Authorization: auth, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (resp.status === 401) {
    localStorage.removeItem('orcanos_auth');
    throw { code: 401, message: 'Session expired — please sign in again.' };
  }
  if (!resp.ok) throw { code: resp.status, message: `Server error (HTTP ${resp.status})` };

  const data = await resp.json();
  if (!data.IsSuccess) {
    throw { code: data.HttpCode || 500, message: typeof data.Data === 'string' ? data.Data : data.Message || 'Request failed' };
  }
  return data.Data;
}
```

### Python / server
```python
def _post(endpoint: str, payload: dict) -> dict:
    url = f"{base_url}/api/v2/Json/{endpoint}"
    resp = session.post(url, json=payload, timeout=30)
    resp.raise_for_status()   # raises HTTPError on 4xx/5xx
    data = resp.json()
    if not data.get('IsSuccess'):
        raise RuntimeError(f"Orcanos [{endpoint}] failed: {data.get('Message')} | {data.get('Data')}")
    return data.get('Data', {})
```

---

## HTML in field values

Orcanos filter responses can contain HTML in field text (`<b>`, `<a>`, etc.). In browser code, always sanitize before rendering:

```js
import DOMPurify from 'dompurify';
// Allowlist: b, i, a, br, ul, li, p (extend as needed — edit this list, don't bypass)
element.innerHTML = DOMPurify.sanitize(rawHtml, { ALLOWED_TAGS: ['b','i','a','br','ul','li','p'] });
```

Never use `innerHTML = rawHtml` directly.

---

## Settings pattern (JavaScript apps)

Keep the Orcanos base URL, version ID, and filter IDs in a static config file — not hardcoded in JS:

```xml
<!-- public/settings.xml -->
<orcanosSettings>
  <baseUrl>https://us.orcanos.com/myproject/</baseUrl>
  <versionId>5</versionId>
  <bomFilterId>609</bomFilterId>
  <instanceFilterId>610</instanceFilterId>
  <pageSize>50</pageSize>
</orcanosSettings>
```

```js
// settings/settingsStore.js
let _settings = null;
export async function loadSettings() {
  const text = await fetch('/settings.xml').then(r => r.text());
  const xml = new DOMParser().parseFromString(text, 'application/xml');
  const get = (tag) => xml.querySelector(tag)?.textContent?.trim() ?? '';
  _settings = {
    baseUrl:          get('baseUrl'),
    versionId:        get('versionId'),
    bomFilterId:      parseInt(get('bomFilterId')),
    instanceFilterId: parseInt(get('instanceFilterId')),
    pageSize:         parseInt(get('pageSize')) || 50,
  };
}
export const getSettings = () => _settings;
```

Call `loadSettings()` once at app startup before rendering. Then use `getSettings()` synchronously everywhere else.

---

## .env / secrets reference

```bash
# Server-side Python scripts
ORCANOS_API_KEY=orc-...          # in Secret Manager on GCP, or .env locally

# Client-side config (NOT secret — these go in settings.xml, not .env)
# baseUrl, versionId, filterIds → settings.xml (served as a static file)
```

API keys never go in the frontend or in `settings.xml`. If a value is secret, it lives in `.env` and is used only from the backend.
