# QW_Add_Step — Add a Test Step to a Test Case

Appends one step (action + expected result) to a test case. Call once per step, in order.
Used after [QW_Add_Object](qw-add-item.md) creates a test case — e.g. when materialising the
steps an [Ask Paul](ai-get-response.md) draft generated.

## Endpoint

```
POST <base>/api/v2/Json/QW_Add_Step
Authorization: Basic <base64(username:password)> OR Bearer <api-key>
OrcanosAPIKey: <api-key>   (alternative header)
Content-Type: application/json
```

`<base>` includes the tenant, e.g. `https://app.orcanos.com/orca60`.
Full URL: `https://app.orcanos.com/orca60/api/v2/Json/QW_Add_Step`.

**Auth:** See [main skill](SKILL.md). **Prerequisite:** the test case must already exist —
create it with [QW_Add_Object](qw-add-item.md) (`Object_Type` = `Test Case`) and use the returned id.

---

## Request Body — `AddStep` model (verified against swagger, orca60)

The body is the step object directly (not wrapped):

```json
{
  "ItemId": "30811",
  "ItemType": "T_CASE",
  "ProjectId": "18427",
  "Description": "Power on the device and wait for boot.",
  "ExpectedValue": "The home screen appears within 10 seconds.",
  "ReferStepId": "",
  "ReferPosition": "",
  "LowerLimit": "",
  "UpperLimit": ""
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `ItemId` | string | **Yes** | The test case's numeric id (e.g. `30811`) — from `QW_Add_Object`'s returned `Data`, or the number in a displayed key `T_CASE-30811` |
| `ItemType` | string | **Yes** | The type **code**, e.g. `T_CASE` (`Item_type[].Code` from `QW_Login`) |
| `ProjectId` | string | **Yes** | Project id the test case lives in |
| `Description` | string | **Yes** | The step action / what the tester does. Plain text or basic HTML |
| `ExpectedValue` | string | No | Expected result for the step |
| `ReferStepId` | string | No | Insert relative to this existing step id (else appended) |
| `ReferPosition` | string | No | Position when referring to `ReferStepId` |
| `LowerLimit` / `UpperLimit` | string | No | Numeric pass/fail limits for the step (e.g. `1` / `10`) |

> **Ordering:** there is no explicit step-number field on `AddStep` — steps are appended in call
> order. Add them sequentially (step 1, then 2, …). To control placement use `ReferStepId` +
> `ReferPosition`. (The alternative `AddStep` endpoint uses model `AddStepNew` which *does* take a
> `StepNumber`; prefer `QW_Add_Step` unless you need explicit numbering.)

---

## Success Response (HTTP 200)

`ResultClass[String]` — `Data` is the new step id:

```json
{ "IsSuccess": true, "Data": "77021", "Message": "", "HttpCode": 200 }
```

## Error Response

| HTTP | Meaning | Fix |
|---|---|---|
| `401` | Session expired | Re-authenticate via `QW_Login` |
| `200` + `IsSuccess:false` | Validation error | Check `Message` — usually a bad `ItemId`/`ItemType`/`ProjectId` |
| `500` | `ResultClass[XMLError]` | Inspect `Data.ErrorInfo` |

---

## Full Example (JavaScript) — create a test case, then add its steps

```js
// steps: [{ description, expected }]
async function addTestCaseWithSteps({ baseUrl, authHeader, projectId, major, minor, name, steps }) {
  // 1) Create the test case
  const tcId = await addObject({                       // see qw-add-item.md
    baseUrl, authHeader, projectId, major, minor,
    name, description: '', objectType: 'Test Case',
  });

  // 2) Append steps in order
  for (const s of steps) {
    const r = await fetch(`${baseUrl}/api/v2/Json/QW_Add_Step`, {
      method: 'POST',
      headers: { Authorization: authHeader, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ItemId: String(tcId),
        ItemType: 'T_CASE',
        ProjectId: String(projectId),
        Description: s.description || '',
        ExpectedValue: s.expected || '',
      }),
    });
    const data = await r.json();
    if (!data.IsSuccess) throw new Error(data.Message || 'Add step failed');
  }
  return tcId;
}
```

---

## Related step endpoints (from swagger)
- `POST /api/v2/Json/AddStep` — body `AddStepNew` (has `StepNumber`, `ObjectType`)
- `POST /api/v2/Json/UpdateStep` — body `UpdateStepNew` (`CurrentStepNumber` → `NewStepNumber`)
- `POST /api/v2/Json/DeleteStep` — body `DeleteStep` (`ItemId`, `ObjectType`, `StepNumber`)

---

## See also
- [Main Skill](SKILL.md) — Base URL, auth
- [QW_Add_Object](qw-add-item.md) — Create the test case first
- [Get_AI_Response](ai-get-response.md) — Ask Paul generates the steps this endpoint materialises
