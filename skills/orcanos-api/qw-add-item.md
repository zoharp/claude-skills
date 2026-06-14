# QW_Add_Item — Create Work Item

## Endpoint

```
POST <base>api/v2/Json/QW_Add_Item
Authorization: Basic <base64(username:password)> OR Bearer <api-key>
Content-Type: application/json
```

**Auth:** See [main skill](SKILL.md) for Basic Auth and API Key options.  
**Prerequisites:** Call [QW_Login](qw-login.md) first to get `Version_id`.

---

## Request Body

```json
{
  "Item_Type": "REQ",
  "Version_id": 438,
  "Obj_name": "User authentication",
  "Obj_description": "The system shall authenticate users via OAuth2",
  "Fields": [
    { "Name": "Status", "Value": "Draft" },
    { "Name": "Priority", "Value": "High" },
    { "Name": "Owner", "Value": "zohar" }
  ]
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `Item_Type` | string | **Yes** | REQ, TC, TSK, PRT, DOC, DEF, CR, TS, PI |
| `Version_id` | int | **Yes** | Project version from `QW_Login` |
| `Obj_name` | string | **Yes** | Item name/title |
| `Obj_description` | string | No | Full description |
| `Fields` | array | No | Additional field values — `Name` (internal name) and `Value` |

---

## Success Response

```json
{
  "IsSuccess": true,
  "Data": {
    "Id": "12345 (9876)",
    "Message": "Item created successfully"
  }
}
```

Returns the newly created item ID.

---

## Failure Responses

| HTTP | Meaning | Fix |
|---|---|---|
| `401` | Session expired | Re-authenticate via `QW_Login` |
| `200` + `IsSuccess: false` | Validation error | Check `data.Message` for field errors |
| Missing required field | API rejects request | Verify `Item_Type`, `Version_id`, `Obj_name` |

---

## Full Example (JavaScript + Proxy)

```js
const BASE = '/api/orcanos/';

async function addItem({
  itemType = 'REQ',
  versionId,
  name,
  description,
  fields = []
}) {
  const auth = sessionStorage.getItem('auth');
  const body = {
    Item_Type: itemType,
    Version_id: versionId,
    Obj_name: name,
    Obj_description: description,
    Fields: fields
  };

  const r = await fetch(BASE + 'add-item', {
    method: 'POST',
    headers: {
      Authorization: auth,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(body)
  });

  if (r.status === 401) throw new Error('Session expired');
  const data = await r.json();
  if (!data.IsSuccess) throw new Error(data.Message || 'Add item failed');

  return data.Data;
}
```

---

## See also
- [Main Skill](SKILL.md) — Base URL, auth, common patterns
- [QW_Login](qw-login.md) — Authenticate and get project version IDs
