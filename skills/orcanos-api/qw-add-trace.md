# Create Traceability Link — QW_AddRelation vs QW_Add_Relations_Custom_Code

There are **two** relation endpoints with the **same** request body (`Add_Relations_Parameter`):

| Endpoint | Key form it expects |
|---|---|
| `QW_AddRelation` | the true **original** work-item code |
| `QW_Add_Relations_Custom_Code` | the **custom / display** code (and it also accepts the `Item_type[].Code` from `QW_Login`) |

> ✅ **Verified against the live API (orca60, 2026-07-10):** keys built as `{Item_type.Code}-{id}`
> (e.g. `T_CASE-26470`, `SRS-26469`) **succeed with `QW_Add_Relations_Custom_Code`** and
> **fail with `QW_AddRelation`** — the latter returns a misleading `"Item is deleted and cannot
> be updated."`. So when your keys come from `QW_Login`'s `Item_type[].Code` (or from the matrix's
> displayed keys), use **`QW_Add_Relations_Custom_Code`**.

## Endpoint

```
POST <base>/api/v2/Json/QW_Add_Relations_Custom_Code     ← use this one for Item_type.Code / display keys
POST <base>/api/v2/Json/QW_AddRelation                    ← only for true original codes
Content-Type: application/json
Authorization: Bearer <api-key> OR Basic <base64(username:password)>
OrcanosAPIKey: <api-key>  (alternative header)
```

`<base>` includes the tenant, e.g. `https://app.orcanos.com/orca60`.

**Auth:** See [main skill](SKILL.md) for auth options. Requires either `Authorization` header or `OrcanosAPIKey` header.

**RelationType:** optional. Empty → Orcanos uses the default link type (observed: `"Dependent On"`).

---

## Which code to use

- **`QW_Add_Relations_Custom_Code`** (recommended when your keys come from `QW_Login`) resolves items
  by their **custom / display code**, and in practice also accepts the `Item_type[].Code` value
  (e.g. `T_CASE`, `SRS`). Build the key as `{Item_type.Code}-{id}` — where `id` is the item's numeric
  id (from `QW_Add_Object`'s returned `Data`, or the number in a displayed key like `SR-19832`).
- **`QW_AddRelation`** only accepts the true **original** code and rejects the `Item_type.Code` form.
  Prefer the custom-code endpoint unless you know the true original code.

**Key building (custom-code endpoint):**
- New item just created with `QW_Add_Object` → `{childType.Code}-{returnedId}` (e.g. `T_CASE-26470`).
- Existing item shown in a grid → use its **displayed key** as-is (e.g. `SR-19832`), stripping any
  ` (nnnn)` suffix.

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
