# QW_AddRelation — Create Traceability Link

## Endpoint

```
POST <base>/v2/Json/QW_AddRelation
Content-Type: application/json
Authorization: Bearer <api-key> OR Basic <base64(username:password)>
OrcanosAPIKey: <api-key>  (alternative header)
```

**Auth:** See [main skill](SKILL.md) for auth options. Requires either `Authorization` header or `OrcanosAPIKey` header.

---

## ⚠️ CRITICAL: Original Code, Not Custom Code

**IMPORTANT:** Always use the **original work item code**, never the custom code.

**Example:**
- Item displays as: `ECO-30829`
  - `ECO` = custom code (do NOT use this)
  - `CR` = original code (use THIS)
  - Correct API call: `"SourceIdKeys": "CR-30829"`
  
- Another example: `DMS-23175`
  - `DMS` = custom code (do NOT use this)
  - Original code = use the actual original prefix (use THIS)
  - Correct API call: `"SourceIdKeys": "ORIG-23175"` (replace ORIG with actual original code)

---

## Request Body

```json
{
  "SourceIdKeys": "CR-12345",
  "TargetIdKeys": "CR-67890",
  "RelationType": "Implements",
  "Comments": "Implementation link"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `SourceIdKeys` | string | **Yes** | Source work item **original code key** — e.g. `CR-30829` (NOT custom code like `ECO-30829`, and NOT numeric ID) |
| `TargetIdKeys` | string | **Yes** | Target work item **original code key** — e.g. `DMS-23175` (NOT custom code like `ECO-30829`, and NOT numeric ID) |
| `RelationType` | string | No | Relation type designation (check your Orcanos config for valid values) |
| `Comments` | string | No | Additional comments for the relation |

---

## Success Response (HTTP 200)

```json
{
  "IsSuccess": true,
  "Data": "Relation added successfully.",
  "Message": "",
  "HttpCode": 200
}
```

---

## Error Response (HTTP 500)

```json
{
  "IsSuccess": false,
  "Data": {
    "ErrorStatus": 0,
    "ErrorInfo": "string",
    "ErrorTrace": "string"
  },
  "Message": "string",
  "HttpCode": 500
}
```

---

## Full Example (JavaScript + Proxy)

```js
const BASE = '/api/orcanos/';

async function addRelation({
  sourceIdKeys,
  targetIdKeys,
  relationType,
  comments
}) {
  const auth = sessionStorage.getItem('auth');
  const body = {
    SourceIdKeys: sourceIdKeys,
    TargetIdKeys: targetIdKeys,
    RelationType: relationType,
    Comments: comments
  };

  const r = await fetch(BASE + 'add-relation', {
    method: 'POST',
    headers: {
      Authorization: auth,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(body)
  });

  const data = await r.json();
  if (!data.IsSuccess) throw new Error(data.Message || 'Add relation failed');

  return data;
}
```

---

## See also
- [Main Skill](SKILL.md) — Base URL, auth, common patterns
- [QW_Login](qw-login.md) — Authenticate and get session/API key
