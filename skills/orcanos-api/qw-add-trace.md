# QW_Add_Trace — Create Traceability Link

## Endpoint

```
POST <base>api/v2/Json/QW_Add_Trace
Authorization: Basic <base64(username:password)> OR Bearer <api-key>
Content-Type: application/json
```

**Auth:** See [main skill](SKILL.md) for Basic Auth and API Key options.

---

## Request Body

```json
{
  "Source_Item_Id": "9876",
  "Target_Item_Id": "5432",
  "Link_Type": "Implements",
  "Version_id": 438
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `Source_Item_Id` | string | **Yes** | Source work item ID (e.g. requirement) |
| `Target_Item_Id` | string | **Yes** | Target work item ID (e.g. implementation) |
| `Link_Type` | string | No | Traceability relationship (Implements, Tests, Verifies, etc.) Default: "Links" |
| `Version_id` | int | **Yes** | Project version from `QW_Login` |

---

## Link Types

Common traceability relationships:

| Link Type | Meaning | Use Case |
|---|---|---|
| `Implements` | Code implements requirement | REQ → source file/function |
| `Tests` | Test case validates requirement | REQ → test case |
| `Verifies` | Test verifies requirement compliance | TC → REQ |
| `Calls` | Function calls another function | Function A → Function B |
| `Links` | Generic bidirectional link | Default fallback |

Check your Orcanos instance for available link types.

---

## Success Response

```json
{
  "IsSuccess": true,
  "Data": {
    "Message": "Traceability link created successfully"
  }
}
```

---

## Failure Responses

| HTTP | Meaning | Fix |
|---|---|---|
| `401` | Session expired | Re-authenticate via `QW_Login` |
| `200` + `IsSuccess: false` | Link failed | Check source/target IDs exist, validate `Link_Type` |
| Invalid item ID | Source or target not found | Verify IDs from `QW_Get_Filter_Results` |
| Duplicate link | Link already exists | Check before creating (no error, just idempotent) |

---

## Full Example (JavaScript + Proxy)

```js
const BASE = '/api/orcanos/';

async function addTrace({
  sourceItemId,
  targetItemId,
  linkType = 'Implements',
  versionId
}) {
  const auth = sessionStorage.getItem('auth');
  const body = {
    Source_Item_Id: sourceItemId,
    Target_Item_Id: targetItemId,
    Link_Type: linkType,
    Version_id: versionId
  };

  const r = await fetch(BASE + 'add-trace', {
    method: 'POST',
    headers: {
      Authorization: auth,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(body)
  });

  if (r.status === 401) throw new Error('Session expired');
  const data = await r.json();
  if (!data.IsSuccess) throw new Error(data.Message || 'Add trace failed');

  return data.Data;
}
```

---

## Idempotency

Creating a duplicate link may fail or be ignored depending on Orcanos version. Best practice: check if the link exists before creating.

---

## See also
- [Main Skill](SKILL.md) — Base URL, auth, common patterns
- [QW_Get_Filter_Results](qw-get-filter-results.md) — Query items and extract IDs
- [QW_Add_Item](qw-add-item.md) — Create work items
