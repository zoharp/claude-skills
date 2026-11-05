# Delete Traceability Link — QW_Delete_Relation vs QW_Delete_Relation_Custom_Code

The inverse of [qw-add-trace.md](qw-add-trace.md). Again **two** endpoints with the **same** request
body (`Delete_Relation_Parameter`), split by the key form they resolve:

| Endpoint | Key form it expects | `Data` on success |
|---|---|---|
| `QW_Delete_Relation` | the true **original** work-item code | object `{ "Status": "..." }` (`RelationDelete`) |
| `QW_Delete_Relation_Custom_Code` | the **custom / display** code | string |

> ⚠️ **From the orca60 swagger only (`/orca60/api/swagger/docs/v2`, read 2026-10-27) — never run
> against a live delete yet.** Unknown: (1) whether `QW_Delete_Relation` refuses display keys the way
> `QW_AddRelation` does (likely — same original-code rule); (2) whether deleting a link that does not
> exist answers `IsSuccess: true` (check `Data.Status`, and re-read with
> [QW_Get_Object_Relations](qw-get-object-relations.md) to be sure); (3) whether the direction must
> match the one the link was created with. Update this file after the first live call.

## Endpoint

```
POST <base>/api/v2/Json/QW_Delete_Relation                  ← original codes (e.g. SRS-123)
POST <base>/api/v2/Json/QW_Delete_Relation_Custom_Code      ← display / custom codes (e.g. SR-123)
Content-Type: application/json
Authorization: Bearer <api-key> OR Basic <base64(username:password)>
OrcanosAPIKey: <api-key>  (alternative header)
```

`<base>` includes the tenant, e.g. `https://app.orcanos.com/orca60`. No body without auth answers
`{"Message":"Authorization has been denied for this request."}` (endpoint exists — confirmed).

**Auth:** See [main skill](SKILL.md).

---

## Request Body

```json
{
  "Source_Key": "SR-19832",
  "Target_Key": "UR-4501"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `Source_Key` | string | **Yes** | Source item key, `{code}-{id}` (swagger example `DMS-20176`). Strip any ` (nnnn)` suffix from a displayed key |
| `Target_Key` | string | **Yes** | Target item key (swagger example `CR-30829`) |

Note the field names differ from the add call (`SourceIdKeys` / `TargetIdKeys`) — **underscore, singular**.
No `RelationType`: the call removes the link between the pair whatever its type.

---

## Which one to call

Keys taken from a grid or from `QW_Login` `Item_type[].Code` are **display codes** → the safe order is:

1. `QW_Delete_Relation` (original code) — what the traceability-matrix app calls first;
2. on `IsSuccess: false`, `QW_Delete_Relation_Custom_Code` with the same keys;
3. still refused → the same two with **source and target swapped** (a link made in the Orcanos UI may
   point either way; this app records links deeper → shallower).

Reference implementation: `traceability-matrix` → `OrcanoClient.delete_relation()` and
`POST /api/matrix/{id}/delete-relation` (`matrix_api.py`).

---

## Permissions (QW_Login)

Deleting a trace is a **Delete** action — letter **`D`** in `User_details.Permission` and in the
type's `Projects.Project[].Item_type[].Permission` (per type, per project; see [qw-login.md](qw-login.md)).
The matrix app requires `D` on the **authored (deeper) item's type**, and treats an empty letter
string as unknown = allowed (Orcanos still enforces on the call). A viewer (`V` only) is refused.

---

## Success Response (HTTP 200)

```json
{ "IsSuccess": true, "Data": { "Status": "..." }, "Message": "", "HttpCode": 200 }
```

(`_Custom_Code`: `Data` is a string.) The `Status` text is not yet observed live.

## Error Response (HTTP 500)

```json
{
  "IsSuccess": false,
  "Data": { "ErrorStatus": 0, "ErrorInfo": "string", "ErrorTrace": "string" },
  "Message": "string",
  "HttpCode": 500
}
```

Read the error as `Message` or `Data.ErrorInfo`.

---

## Full Example (Python, httpx)

```python
async def delete_relation(base, auth, source_key, target_key, custom_code=False):
    ep = "QW_Delete_Relation_Custom_Code" if custom_code else "QW_Delete_Relation"
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{base}/api/v2/Json/{ep}",
                         headers={"Authorization": auth, "Content-Type": "application/json"},
                         json={"Source_Key": source_key, "Target_Key": target_key})
    data = r.json()
    if not data.get("IsSuccess"):
        d = data.get("Data") if isinstance(data.get("Data"), dict) else {}
        raise RuntimeError(data.get("Message") or d.get("ErrorInfo") or "Delete relation failed")
    return data
```

---

## See also
- [qw-add-trace.md](qw-add-trace.md) — create a relation
- [qw-get-object-relations.md](qw-get-object-relations.md) — read an item's relations (verify a delete)
- [qw-login.md](qw-login.md) — permission letters
