# QW_Add_Object — Create Work Item

> ⚠️ The create method is **`QW_Add_Object`**. There is **no** `QW_Add_Item` endpoint
> (it 404s). This file was previously named for a method that does not exist on the API.

## Endpoint

```
POST <base>/api/v2/Json/QW_Add_Object
Authorization: Basic <base64(username:password)> OR Bearer <api-key>
Content-Type: application/json
```

`<base>` includes the tenant, e.g. `https://app.orcanos.com/orca60`.
Full URL: `https://app.orcanos.com/orca60/api/v2/Json/QW_Add_Object`.

**Auth:** See [main skill](SKILL.md) for Basic Auth and API Key options.
**Prerequisites:** Call [QW_Login](qw-login.md) first to get `Project.Id`, the version, and `Item_type[].Code`.
**Spec source:** your instance's Swagger — `https://app.orcanos.com/<tenant>/api/swagger/ui/index#/Json`
(machine model at `.../api/swagger/docs/v1`).

---

## Request Body

```json
{
  "Project_ID": 14667,
  "Major_Version": 1,
  "Minor_Version": 0,
  "Object_Name": "User authentication",
  "Object_Type": "REQ",
  "Description": "The system shall authenticate users via OAuth2",
  "Insert_to_Pool": "Y"
}
```

### Required fields

| Field | Type | Notes |
|---|---|---|
| `Project_ID` | integer | Project id (`Project.Id` from `QW_Login`) |
| `Major_Version` | integer | Major part of the version view (e.g. `1` from version label `1.0`) |
| `Minor_Version` | integer | Minor part of the version view (e.g. `0` from version label `1.0`) |
| `Object_Name` | string | Work item name/title |
| `Object_Type` | string | Work item type — the **`Item_type[].Code`** from `QW_Login` (e.g. `REQ`, `T_CASE`) |
| `Description` | string | Plain text or HTML |

### Common optional fields

| Field | Type | Notes |
|---|---|---|
| `Insert_to_Pool` | string | `"Y"` = add to the pool (no parent); `"N"` = add into the product tree (CR/requirements only) |
| `Parent_ID` | string | Parent item location; defaults to the project |
| `Status`, `Priority`, `Category` | string | Workflow defaults are used if omitted |
| `Release_Version`, `Build_Version` | string | Extra version components (default `0`) |
| `Assigned_to` | string | Username |
| `Created_date`, `Start_Date`, `Due_date` | string | Must match the server's local date format |
| `CS1_Name`…`CS60_Name` / `CS1_value`…`CS60_value` | string | Up to 60 custom fields |
| `SkipIfNameExists` | string | `"Y"` to avoid creating a duplicate by name |
| `External_ID`, `Migration_Reference`, `Customer_ID`, `Site_ID` | string | Integration references |

> **Version note:** `QW_Add_Object` identifies the version by `Major_Version` + `Minor_Version`,
> **not** by the `Ver_id` that `QW_Get_Filter_Results` uses. Derive major/minor from the
> version label (`QW_Login` → `Version.Version_label`, e.g. `"1.0"` → `1`, `0`).

---

## Success Response

`ResultClass[Int32]` — `Data` is the new item's numeric id:

```json
{
  "IsSuccess": true,
  "Data": 53834,
  "Message": "Object created successfully.",
  "HttpCode": 200
}
```

To link the new item, build its **Key** as `{Item_type.Code}-{Data}` (e.g. `T_CASE-53834`) and call
**`QW_Add_Relations_Custom_Code`** (not `QW_AddRelation`). See [qw-add-trace.md](qw-add-trace.md).

---

## Failure Responses

| HTTP | Meaning | Fix |
|---|---|---|
| `404` | Wrong method/path (e.g. calling `QW_Add_Item`) | Use `QW_Add_Object` under `/api/v2/Json/` |
| `401` | Session expired | Re-authenticate via `QW_Login` |
| `200` + `IsSuccess: false` | Validation error | Check `Message` — often a missing required field or bad `Object_Type` |

---

## Full Example (JavaScript)

```js
async function addObject({ baseUrl, authHeader, projectId, major, minor, name, description, objectType }) {
  const r = await fetch(`${baseUrl}/api/v2/Json/QW_Add_Object`, {
    method: 'POST',
    headers: { Authorization: authHeader, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      Project_ID: projectId,
      Major_Version: major,
      Minor_Version: minor,
      Object_Name: name,
      Object_Type: objectType,   // Item_type[].Code, e.g. "REQ"
      Description: description || '',
      Insert_to_Pool: 'Y',
    }),
  });
  if (r.status === 401) throw new Error('Session expired');
  const data = await r.json();
  if (!data.IsSuccess) throw new Error(data.Message || 'Add object failed');
  return data.Data; // new numeric item id
}
```

---

## See also
- [Main Skill](SKILL.md) — Base URL, auth, common patterns
- [QW_Login](qw-login.md) — Projects, versions, and `Item_type[].Code`
- [QW_AddRelation](qw-add-trace.md) — Link the new item to its parent
