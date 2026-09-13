# QW_Update_Object — Update Work Item

## Endpoint

```
POST <base>/api/v2/Json/QW_Update_Object
Authorization: Basic <base64(username:password)> OR Bearer <api-key>
Content-Type: application/json
```

`<base>` includes the tenant, e.g. `https://app.orcanos.com/orca60`.
Full URL: `https://app.orcanos.com/orca60/api/v2/Json/QW_Update_Object`.

**Auth:** See [main skill](SKILL.md) for Basic Auth and API Key options.
**Prerequisites:** Call [QW_Login](qw-login.md) first. Need the item's numeric id (from
[QW_Get_Filter_Results](qw-get-filter-results.md) / [QW_Get_Object](qw-get-object.md)) and the
project's `View_Version` (the version label shown in the item's URL, e.g. `1.0`).
**Spec source:** knowledgebase — https://help.orcanos.com/knowledgebase/qw_update_object-rest-api/
(the article doesn't state the path explicitly; it follows the standard `/api/v2/Json/<method>`
pattern documented in [SKILL.md](SKILL.md)). Cross-check against your instance's Swagger
(`.../api/swagger/docs/v1`) if fields don't behave as documented.

---

## Request Body

```json
{
  "Object_ID": 30769,
  "View_Version": "1.0",
  "Object_Name": "User authentication (revised)",
  "Description": "The system shall authenticate users via OAuth2 and SAML",
  "Status": "In Progress"
}
```

### Required fields

| Field | Type | Notes |
|---|---|---|
| `Object_ID` | integer | The item id to update (e.g. `6758`) |
| `View_Version` | string | The project's version **label** as shown in the item's URL (e.g. `"1.0"`) — **not** `Ver_id` |
| `Object_Name` | string | Item name — send the current name if not renaming; the API does not appear to support a partial/omit-to-keep update |

### Common optional fields

| Field | Type | Notes |
|---|---|---|
| `Description` | string | Plain text or HTML |
| `Status`, `Priority`, `Category` | string | System defaults apply if omitted |
| `Assigned_to` | string | Username; defaults to workflow-defined user if omitted |
| `Updated_Date` | string | Must match the server's local date format |
| `Updated_By` | string | Name of the user performing the update |
| `Make_Branch` | integer | `0`/`1` — branch the item instead of updating in place |
| `Release_Version`, `Build_Version` | string | Default `0` |
| `Start_date`, `Due_date` | string | Local machine date format |
| `Effort_estimation` | string | Default `0` |
| `Insert_to_Pool` | string | `Y`/`N` — CR/requirements only; default `N` |
| `CS1_Name`…`CS60_Name` / `CS1_value`…`CS60_value` | string | Up to 60 custom fields |
| `Customer_ID`, `Site_ID` | string | Integration references |
| `MigrationReference`, `External_ID` | string | Third-party/reporting references |

> ⚠️ **Untested field behavior:** the knowledgebase article doesn't document whether omitted
> optional fields are left unchanged or reset to blank/default. Verify against a real tenant
> before relying on partial updates — if fields get clobbered, always send the current value
> for anything you don't intend to change (fetch it first via [QW_Get_Object](qw-get-object.md)).

---

## Success Response

`ResultClass[String]` — `Data` is the updated item's id (as a string):

```json
{
  "IsSuccess": true,
  "Data": "30769",
  "Message": "Object updated successfully",
  "HttpCode": 200
}
```

---

## Failure Responses

| HTTP | Meaning | Fix |
|---|---|---|
| `404` | Wrong method/path | Confirm `/api/v2/Json/QW_Update_Object` |
| `401` | Session expired | Re-authenticate via `QW_Login` |
| `200` + `IsSuccess: false` | Validation error | Check `Message` — often a bad `Object_ID`, wrong `View_Version`, or missing `Object_Name` |

---

## Full Example (JavaScript)

```js
async function updateObject({ baseUrl, authHeader, objectId, viewVersion, name, description, status }) {
  const r = await fetch(`${baseUrl}/api/v2/Json/QW_Update_Object`, {
    method: 'POST',
    headers: { Authorization: authHeader, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      Object_ID: objectId,
      View_Version: viewVersion,   // version label, e.g. "1.0" — not Ver_id
      Object_Name: name,
      Description: description,
      Status: status,
    }),
  });
  if (r.status === 401) throw new Error('Session expired');
  const data = await r.json();
  if (!data.IsSuccess) throw new Error(data.Message || 'Update object failed');
  return data.Data; // updated item id (string)
}
```

---

## See also
- [Main Skill](SKILL.md) — Base URL, auth, common patterns
- [QW_Add_Object](qw-add-item.md) — Create a work item (sibling create endpoint)
- [QW_Get_Object](qw-get-object.md) — Fetch current field values before a partial update
- [QW_Login](qw-login.md) — Session/auth prerequisite
