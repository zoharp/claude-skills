# Get an Item's Direct Children — Get_Children

Returns the **direct children** of one item — one hop, already enriched (name, type, status,
assignee, priority, description, and a ready-made web URL). Use it to walk a document /
requirement **hierarchy** (a REQ_HD outline: Introduction → User Requirements → …), lazily expand
a tree node, or build a breadcrumb-able outline view.

> **This is containment, not traceability.** `Get_Children` returns the parent→child *tree*
> (an item's sub-items). Trace links — what the matrix is built from — are a different graph:
> use [QW_Get_Object_Relations](qw-get-object-relations.md) (or the `Traced Items Info` field
> from [QW_Get_Filter_Results](qw-get-filter-results.md)) for those. Don't substitute one for
> the other.

**Note the method name:** it is `Get_Children` — **no `QW_` prefix**, unlike most endpoints here.

---

## Endpoint

The **item id is a path segment**:

```
GET  <base>/api/v2/Json/Get_Children/<ItemId>
Authorization: Basic <base64(username:password)>  OR  Bearer <api-key>
Content-Type: application/json
```

`<base>` includes the tenant, e.g. `https://app.orcanos.com/orca60`.
Auth: same options as every endpoint — see [SKILL.md](SKILL.md).

---

## Request Parameters

| Parameter | Where | Required | Description |
|---|---|---|---|
| `ID` | **path segment** | **Yes** | The item whose children you want — its **display id** (e.g. `19830`), the number *before* the parenthesis in `"PAR-19830 (8500)"`. |
| version id | query | **Yes** | The version to read the hierarchy in. Same `Ver_id` you get from `QW_Login` → `Projects.Project[].Version[].Ver_id`, or an item's `Ver_Id`. |

> ⚠️ **The version query-param spelling is not confirmed.** The call takes a version id, but the
> exact key wasn't captured from a live request. Try in order: `?VerId=` → `?Ver_Id=` →
> `?VersionId=`. **A wrong key does not necessarily error** — if a version is defaulted you get a
> plausible-but-wrong child set, so verify against a known item before trusting the result, and
> record the winning spelling here.

> ⚠️ **Which id?** Pass the **display id** (`ID` in the response / `extract_item_id`), not the
> internal link id (the parenthesised number). Same rule as
> [QW_Get_Object](qw-get-object.md).

---

## Response

Unlike [QW_Get_Object](qw-get-object.md), `Data` is a **flat array of already-resolved child
objects** — there is no `Field[]` array to walk and no `fieldValue()` helper needed.

```json
{
  "IsSuccess": true,
  "Data": [
    {
      "ID": 19831,
      "Ver_Id": 434,
      "Key": "PAR-19831 (8503)",
      "ItemURL": "http://app.orcanos.com/orca60/web/434/items/view?Item=REQ_HD&ItemId=19831",
      "Type": "REQ_HD",
      "Name": "Introduction",
      "Status": "Open",
      "AssignedTo": "Not Assigned",
      "Priority": "- Not Set -",
      "Description": "<p>this is the intro of the project</p>"
    },
    {
      "ID": 8502,
      "Ver_Id": 332,
      "Key": "PAR-8502",
      "ItemURL": "http://app.orcanos.com/orca60/web/332/items/view?Item=REQ_HD&ItemId=8502",
      "Type": "REQ_HD",
      "Name": "Interface",
      "Status": "Open",
      "AssignedTo": "Not Assigned",
      "Priority": "- Not Set -",
      "Description": "<P style=\"MARGIN-TOP: 0px\">&nbsp;</P>"
    }
  ],
  "Message": "Success",
  "HttpCode": 200
}
```

| Field | Notes |
|---|---|
| `ID` | Numeric **display id**. Feed this straight back into `Get_Children/<ID>` to recurse. |
| `Ver_Id` | The child's **own** version — **not necessarily the version you asked for** (see the trap below). |
| `Key` | `"PAR-19831 (8503)"` = `{custom-code prefix}-{display id} ({internal link id})`. The parenthesised part **can be absent** (`"PAR-8502"`) — never assume it's there. |
| `ItemURL` | Server-built web link — **use it as-is**, don't reconstruct (see below). |
| `Type` | The **original** type code (`REQ_HD`), *not* the custom-code prefix in `Key` (`PAR`). |
| `Name` | Plain text. `Status` / `AssignedTo` / `Priority` are display strings (`"Not Assigned"`, `"- Not Set -"`), not ids or nulls — treat those literals as "empty" when rendering. |
| `Description` | **HTML**, may be empty, whitespace-only (`<P>&nbsp;</P>`), or contain embedded-filter anchors (below). |

`Data: []` = a genuine leaf. `IsSuccess: false` → read `Message`.

**XML→JSON quirk:** as everywhere in this API, a single child may arrive as an object rather
than a 1-element array — wrap with `ensureArray()` (see [SKILL.md](SKILL.md)).

---

## Traps

**1. A child's `Ver_Id` can differ from the parent's.** In the sample, four children are in
version `434` and one (`8502`) is in `332` — an item inherited from an earlier version rather
than re-versioned. So:
- **Don't build the URL yourself** from the version you requested — `ItemURL` already carries the
  child's own version (`…/web/332/…` for that item). Rebuilding with the parent's version points
  at the wrong (or a non-existent) page.
- **Recurse with the child's own `Ver_Id`**, not the one you started from.
- Don't treat a differing `Ver_Id` as an error or filter those rows out — they are real children.

**2. `Key` prefix ≠ `Type`.** `Key` starts with the tenant's **custom code** (`PAR`), while
`Type` is the **original** code (`REQ_HD`). Display the key; key any API call or URL off `Type`.
(Same distinction that broke the graph's related-item links — see the app's V2.3.1 note.)

**3. `Description` may contain Orcanos embedded-filter anchors**, not ordinary links:
```html
<a name="FILTER_587" obj-type="MR_REQ" version_id="434">User requirements traceability to product</a>
```
These are placeholders Orcanos expands into a live filter result inside its own viewer. A plain
`stripHtml()` leaves just the caption text, which reads like prose but is really "a table renders
here" — if the description matters, detect `name="FILTER_\d+"` and render a marker rather than
silently flattening it.

**4. Direct children only.** There is no depth parameter — a full tree means one call per node.

---

## Fetch a subtree (recursive, cycle-safe)

One call per node adds up fast, so **expand lazily** (fetch a node's children when the user opens
it) and only pre-fetch a whole subtree when you actually need it. Always carry a `visited` set —
same cycle discipline as [QW_Get_Object_Relations](qw-get-object-relations.md).

```js
function ensureArray(v) { return Array.isArray(v) ? v : v == null ? [] : [v]; }

async function getChildren(base, auth, itemId, verId) {
  const res = await fetch(`${base}/api/v2/Json/Get_Children/${itemId}?VerId=${verId}`, {
    headers: { Authorization: auth, 'Content-Type': 'application/json' },
  });
  if (!res.ok) throw new Error(`Get_Children ${itemId}: HTTP ${res.status}`);
  const data = await res.json();
  if (!data.IsSuccess) throw new Error(`Get_Children ${itemId}: ${data.Message}`);
  return ensureArray(data.Data);
}

async function getSubtree(base, auth, itemId, verId, { maxDepth = 10, visited = new Set() } = {}) {
  if (maxDepth <= 0 || visited.has(itemId)) return [];   // depth cap AND cycle guard
  visited.add(itemId);

  const children = await getChildren(base, auth, itemId, verId);
  return Promise.all(children.map(async c => ({
    ...c,
    children: await getSubtree(base, auth, c.ID, c.Ver_Id, { maxDepth: maxDepth - 1, visited }),
    //                                          ^^^^^^^^ the CHILD's version, not verId
  })));
}
```

The `visited` set is shared across the whole walk, so an item reachable by two paths is expanded
once (its second appearance renders as a leaf) instead of looping forever.

---

## See also
- [SKILL.md](SKILL.md) — base URL, auth, XML→JSON quirks
- [qw-get-object.md](qw-get-object.md) — one item's **full field set** (`Field[]`); this endpoint returns a fixed, pre-resolved subset instead
- [qw-get-object-relations.md](qw-get-object-relations.md) — **trace** links (a different graph from this parent/child tree), plus the cycle-safe expansion pattern
- [qw-get-filter-results.md](qw-get-filter-results.md) — batch fetch by saved filter, incl. `Traced Items Info`
