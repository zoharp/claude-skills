# Get a Single Item — QW_Get_Object

Fetches **one work item's full details** by id — every field (Name, Status, Priority, Version,
Assigned To, Description, custom fields…) as a flat `Field` array. Use it to render an item
**information card** (hover preview, side panel) or to enrich a bare id returned by
[QW_Get_Object_Relations](qw-get-object-relations.md) into a nameable node.

> ⚠️ **Deprecated upstream** in favour of a newer `Get_Object`. It still works on current
> instances (verified against orca60, 2026-07-11). Try `QW_Get_Object` first and fall back to
> `Get_Object` on a 404.

**Reference:** https://help.orcanos.com/knowledgebase/qw_get_object-rest-api/

---

## Endpoint

The **id is a path segment** (verified against the live orca60 API):

```
GET  <base>/api/v2/Json/QW_Get_Object/<id>
Authorization: Basic <base64(username:password)>  OR  Bearer <api-key>
Content-Type: application/json
```

`<base>` includes the tenant, e.g. `https://app.orcanos.com/orca60`.
Auth: same options as every endpoint — see [SKILL.md](SKILL.md).

> The public knowledge-base article shows the id as a query parameter (`?id=<id>`). The live
> API accepts the **path form** `QW_Get_Object/<id>`. If an instance rejects the path form,
> fall back to `?id=<id>`, then to a POST with `{"id": <id>}`. This client tries all three.

---

## Request Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `id` | integer | **Yes** | The item's **display id** (e.g. `14230`) — the number before the parenthesis in `"14230 (9876)"`. |

> ⚠️ **Which id?** Pass the **display id** (`extract_item_id` → `14230`), not the internal link
> id. If a call returns nothing, retry with the internal id (`extract_link_id` → `9876`) — the
> accepted form varies by instance.

---

## Response

```json
{
  "IsSuccess": true,
  "Data": {
    "Field": [
      { "Name": "Name",        "Text": "The system shall record patient vitals" },
      { "Name": "Status",      "Text": "Approved" },
      { "Name": "Priority",    "Text": "High" },
      { "Name": "Version",     "Text": "2.0" },
      { "Name": "Assigned To", "Text": "Jane Doe" },
      { "Name": "Description", "Text": "<p>Full rich-text description…</p>" }
    ],
    "Id": "14230",
    "Action": "",
    "ALManalyticsBIurl": ""
  },
  "Message": "",
  "HttpCode": 200
}
```

| Field | Notes |
|---|---|
| `Data.Field` | Array of `{Name, Text}` pairs — the item's fields. **XML→JSON quirk:** a single field arrives as an object, not a 1-element array — wrap with `ensureArray()`. `Text` may be `null` or contain **HTML** (Description, rich-text) — strip tags for a plain card. |
| `Data.Id` | The item id, echoed back (may be `"14230"` or `"14230 (9876)"`). |
| `Data.Action` / `Data.ALManalyticsBIurl` | Usually empty; ignore for a card. |

Same `Field` shape as a `QW_Get_Filter_Results` item, so the same `fieldValue()` /
`_format_item` helpers work on `Data`.

`IsSuccess: false` → read `Message`. A missing/inaccessible id may return `IsSuccess: true`
with an empty `Field` — treat "no meaningful fields" as "not found".

---

## Extract fields (JavaScript)

```js
function ensureArray(v) { return Array.isArray(v) ? v : v == null ? [] : [v]; }

function fieldMap(getObjectData) {
  const out = {};
  for (const f of ensureArray(getObjectData?.Data?.Field)) {
    const name = f.Name || f.Title;
    const text = f.Text ?? f.Display_text ?? '';
    if (name) out[name] = String(text);
  }
  return out;                       // { Name, Status, Priority, Version, Description, … }
}

const stripHtml = s => String(s || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
```

---

## Rendering an item card

A hover/preview card typically shows:
- **Title** — `Name` / `Obj_name` / `Synopsis` (first non-empty), with the item **key** if known.
- **Type & Status** — as pills.
- **A few key fields** — Version, Priority, Assigned To (skip empty ones).
- **Description** — `stripHtml(Description)`, truncated.

Because one hover = one HTTP round-trip, **debounce** the hover (~250 ms) and **memoize** by id
so re-hovering the same item doesn't refetch.

---

## See also
- [SKILL.md](SKILL.md) — base URL, auth, XML→JSON quirks, `fieldValue()` helper
- [qw-get-object-relations.md](qw-get-object-relations.md) — the id-only relations this enriches
- [qw-get-filter-results.md](qw-get-filter-results.md) — batch item fetch via a saved filter
