# QW_Add_Object_Discussion — add a remark to a work item's Discussion

Writes one comment on an item's **Discussion**. It changes no field of the item. Used by the
Traceability tool (`ai_history.py`, 2026-11-12) to leave an AI-origin remark on every item added from
an AI suggestion: what made it, the data sources, the confidence, and a link back.

> **Status: read from Swagger v2 (orca60, 2026-11-12). NOT verified live.** A live probe was blocked
> on 2026-11-12. Update this file after the first real call. Things to learn: the `Is_Private` spelling,
> whether `VersionId` is needed, the response `Data`, and whether the comment **also shows on the
> History tab** (`QW_Get_Section_Data` `Section_Name=History`) or only on Discussion.

## Call

```
POST <base>/api/v2/Json/QW_Add_Object_Discussion
Authorization: Basic …          Content-Type: application/json
```

Body (Swagger definition `WorkItemDiscussion`, every property a string):

```json
{
  "Item_Key": "TC-27462",
  "Comment": "🤖 AI-generated item — added from Orcanos Traceability.\nConfidence: High — …",
  "Is_Private": "N",
  "VersionId": "434",
  "CommentedBy": ""
}
```

| Field | Notes |
|---|---|
| `Item_Key` | The item's **key** (`TC-27462`), not the bare id. Whether a custom code key (`SYSREQ-…`) or only the original-code key works is unverified. |
| `Comment` | Plain text. We send short lines joined with `\n`, ≤ 3,800 chars. Whether HTML renders is unknown — keep it plain. |
| `Is_Private` | We send `"N"` (Orcanos Y/N flags elsewhere, e.g. `Insert_to_Pool`). Unverified. |
| `VersionId` | The item's version **id** (`434`), not the label. We read it from the item's URL (`/web/<ver>/`) or the panel. |
| `CommentedBy` | Left out — we let the authenticated user be the author. Unverified whether it overrides. |

**Swagger docs:** `https://app.orcanos.com/<tenant>/api/swagger/docs/v2`. The `v1` path answers
`{"Message":"An error has occurred."}`; use `v2`.

## Response

Swagger says only `200 object`. As with every write here, treat `IsSuccess: false` with HTTP 200 as the
refusal and read `Message` (see `_post_write` in `orcanos_client.py`).

## Live result (orca60, 2026-11-15, validation VT-759.1)

Refused: `Not posted — Orcanos User Authentication issue : Commented by is not valid.` — the call reached Orcanos
but the commenter was not accepted (the add-on sends the session's own credential). Cause not found yet: try a
`Commented_by` / user field in the body, or the session's `User_name` instead of an e-mail. Until then a remark is
recorded as `failed: <reason>` and the add itself still succeeds.

## Permissions

Unknown which letter is needed. Assume the user needs at least **V** on the type; a refusal is
recorded and shown, never raised (the add itself already succeeded).

## In code

- `orcanos_client.OrcanoClient.add_discussion(auth, item_key, comment, version_id, private=False)`
- `ai_history.post_remarks(session, ids=…|setup_id=…|modules=…, root=…)` posts once per suggestion
  (claims `ai_suggestions.orcanos_note`), records `posted` / `failed: <reason>`.

## See also
- [qw-add-item.md](qw-add-item.md) — creating the item the remark goes on
- [get-section-data/section-history.md](get-section-data/section-history.md) — reading the History tab (to check where the remark lands)
