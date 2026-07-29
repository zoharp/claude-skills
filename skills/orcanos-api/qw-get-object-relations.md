# Get Item Relations — QW_Get_Object_Relations

Returns a work item's **traceability relations** (the edges to/from other items), regardless
of any saved filter. Use it to discover items that a saved filter would exclude — e.g. a
requirement linked to a **Risk**, **Defect**, or **Change Request** that isn't in the matrix
scope.

> ⚠️ **Returns only the edge ids, not item details.** Each relation is a pair of ids
> (`Source`, `Target`). To render a related item (name, type, key, url) you must look it up
> separately (e.g. `QW_Get_Filter_Results` on a whole-panel filter, or a get-item endpoint).

**Reference:** https://help.orcanos.com/knowledgebase/qw_get_object_relations-rest-api/

---

## Endpoint

```
GET  <base>/api/v2/Json/QW_Get_Object_Relations?Id=<itemId>
Authorization: Basic <base64(username:password)>  OR  Bearer <api-key>
```

`<base>` includes the tenant, e.g. `https://app.orcanos.com/orca60`.
Auth: same options as every endpoint — see [SKILL.md](SKILL.md).

> The public docs show a **GET** with the `Id` as a query-string parameter. Other write
> endpoints in this API are POST-with-JSON; if the GET form 404s or is rejected on your
> instance, retry as `POST <base>/api/v2/Json/QW_Get_Object_Relations` with body `{"Id": <id>}`.
> **Verify against your live instance and record the working form here.**

---

## Request Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `Id` | integer | **Yes** | The id of the item whose relations you want (e.g. `30829`). |

> ⚠️ **Which id?** Orcanos item ids come in two forms — the **display id** and the internal
> **link id** (the parenthetical in `"12345 (9876)"`). The docs' example (`30829`) doesn't say
> which. **Verify which id `QW_Get_Object_Relations` accepts, and which id form it returns in
> `Source`/`Target`, then record it here.** (In this codebase: `extract_item_id` → display id
> `12345`; `extract_link_id` → internal id `9876`.)

---

## Response

```json
{
  "IsSuccess": true,
  "Data": {
    "Id": "30829",
    "RelationCount": "3",
    "Relation": [
      { "Source": "30829", "Target": "41022" },
      { "Source": "30829", "Target": "41055" },
      { "Source": "18734", "Target": "30829" }
    ]
  },
  "Message": "",
  "HttpCode": 200
}
```

| Field | Notes |
|---|---|
| `Data.Id` | The queried item id, echoed back. |
| `Data.RelationCount` | Count as a **string**. |
| `Data.Relation` | Array of `{Source, Target}` id pairs. **XML→JSON quirk:** a single relation arrives as an object, not a 1-element array — wrap with `ensureArray()`. |
| `Data.Relation[].Source` / `.Target` | Item ids. The queried item is on one side; the **other** side is the neighbour. Direction: `Source → Target` (source traces to / depends on target). |

An item with **no** relations may return `RelationCount: "0"` and no `Relation`, or `Data: null`.
Treat both as "no neighbours".

---

## Extracting neighbours (JavaScript)

```js
function ensureArray(v) { return Array.isArray(v) ? v : v == null ? [] : [v]; }

// All ids related to `itemId`, with direction, excluding the item itself.
function neighbours(data, itemId) {
  const rels = ensureArray(data?.Data?.Relation);
  const me = String(itemId);
  return rels
    .map(r => {
      const s = String(r.Source), t = String(r.Target);
      if (s === me) return { id: t, dir: 'out' }; // me → t
      if (t === me) return { id: s, dir: 'in'  }; // s → me
      return null;
    })
    .filter(Boolean);
}
```

---

## Recursive expansion (external relations, cycle-safe)

To "open all items and their relations" starting from one node, BFS/DFS while tracking
visited ids so a **circular relation stops instead of looping forever**:

```js
async function expandAll(rootId, getRelations /* async id -> Data */, maxDepth = 6, maxNodes = 500) {
  const visited = new Set([String(rootId)]);
  const edges = [];               // { from, to }
  const queue = [{ id: String(rootId), depth: 0 }];
  const cycles = [];              // edges skipped because they'd revisit an ancestor

  while (queue.length) {
    const { id, depth } = queue.shift();
    if (depth >= maxDepth || visited.size >= maxNodes) continue;
    const data = await getRelations(id);
    for (const nb of neighbours(data, id)) {
      const from = nb.dir === 'out' ? id : nb.id;
      const to   = nb.dir === 'out' ? nb.id : id;
      const eKey = `${from}->${to}`;
      if (edges.some(e => `${e.from}->${e.to}` === eKey)) continue; // dedupe
      if (visited.has(nb.id)) { cycles.push({ from, to }); continue; } // ← cycle: record & STOP descending
      visited.add(nb.id);
      edges.push({ from, to });
      queue.push({ id: nb.id, depth: depth + 1 });
    }
  }
  return { nodeIds: [...visited], edges, cycles };
}
```

Notes:
- **Cycle safety** rests entirely on `visited` — never enqueue an id already in it. Record the
  skipped edge (in `cycles`) if you want to draw it dashed, but do **not** recurse through it.
- Cap with `maxDepth` **and** `maxNodes` — a dense graph can otherwise fan out to the whole DB.
- One HTTP call per node. Memoize `getRelations(id)` so shared neighbours aren't re-fetched.

---

## Rendering related items

`QW_Get_Object_Relations` gives ids only. To show name/type/key/status you still need item
details. Best option for **out-of-scope** items (Risks/Defects/CRs that aren't in any panel
filter):
- **`QW_Get_Object?id=<id>`** — returns a single item's `Data.Field[]` (`{Name, Text}` pairs:
  Name, Type, Status, Version, Description…) plus `Data.Id`. Same field shape as
  `QW_Get_Filter_Results` items. ⚠️ Marked *deprecated* in the docs in favour of a newer
  `Get_Object`; try `QW_Get_Object` first and fall back to `Get_Object` if it 404s. One call
  per related id — memoize.
- Alternative for **in-scope** types only: batch-resolve ids against a filter via
  `QW_Get_Filter_Results` + `Filter_By [ID]` (see [qw-get-filter-results.md](qw-get-filter-results.md)).
  Won't reach types outside the filter, so prefer `QW_Get_Object` here.

Because these items are **outside the matrix filter scope**, render them in a distinct colour
so they read as "related but not in this panel".

---

## See also
- [SKILL.md](SKILL.md) — base URL, auth, XML→JSON quirks
- [qw-get-filter-results.md](qw-get-filter-results.md) — resolve ids → item details
- [qw-add-trace.md](qw-add-trace.md) — create a relation (the inverse operation)
