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

> ✅ **Confirmed live (orca60, 2026-10-27): `?Ver_Id=<version>` — REQUIRED.**
> - No version, `?VerId=`, `?VersionId=`, POST, or `/<id>/<ver>` → **HTTP 404** `"No HTTP resource was found that matches the request URI"`.
> - A version the item does not exist in → **200** with `IsSuccess:false`, `"Item not found."`; `Ver_Id=0` → 400.
> - Any version the item IS in works (an item inherited into a later version answers in both).
> - `Get_Object` does not return the item's version — take it from the filter level / project version that found the item.

> ⚠️ **Not on every Orcanos server (2026-10-29).** `us.orcanos.com` (tenant ipgmedical) answers
> **HTTP 404 "No HTTP resource was found"** even with `?Ver_Id=` — the route is missing from that
> server's build. Probe without login: `GET <base>/api/v2/Json/Get_Children/1?Ver_Id=1` → **401** =
> route exists (app.orcanos.com), **404** = not deployed there. Same for `GetSystemTable` /
> `GetSystemTableValues`. Report it as "not available on this server", never as a bad id.

> ⚠️ **Which id?** Pass the item's **`ID` in that version** (`ID` in the response / `extract_item_id`),
> not the internal link id (the parenthesised number), and **not its `Original_id`**. A branched
> item has a different `ID` per version; `Root_Document` (and `Parent_original_id`) hold the
> ORIGINAL id. Resolve it first from a filter of that type read in the version — every row has the
> system fields `ID` + `Original_id` (`QW_Get_Object_View` with the original id does NOT work for a
> branched item). The original id of a branched item answers 200 `"Item not found."`. Live orca60
> 2026-10-27: DOC original 8467 = ID 16278 in version 434. See `Orcanos-infra/orcanos-documents.md` §3.

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
- ~~Recurse with the child's own `Ver_Id`~~ — **WRONG (corrected 2026-11-05, live orca60):**
  recurse in the version you are viewing (the document's), and fall back to the child's own
  `Ver_Id` only when that call fails. An inherited node's own `Ver_Id` is an OLDER version, and read
  there it lacks every child added since: `Get_Children/8757` (PAR-8757, `Ver_Id 332`) lists 7
  children with `?Ver_Id=434` (incl. a paragraph and an item created in 434) but only 5 with
  `?Ver_Id=332`. Same for read-backs after placing / creating an item under a paragraph.
- Don't treat a differing `Ver_Id` as an error or filter those rows out — they are real children.
- **Exception — the `DOC` root:** its "open in Orcanos" link is the **product tree**,
  `{base}/web/{ver}/tree?ItemId={id}` (same ver + id as its `ItemURL`), not the item form
  (product owner, 2026-11-10; `Orcanos-infra/orcanos-documents.md` §4a). Paragraphs and items keep `ItemURL`.

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

**4b. Never pass a PROJECT id (verified live, orca60 2026-11-13).** `Get_Children/10045?Ver_Id=363` (project *Document
Control*) ran **30 s** and answered `IsSuccess:false` *"The statement terminated. The maximum recursion 100 has been
exhausted before statement completion."* For the DMS tree, read the containers from a filter instead: any *All*-type
filter that selects **Parent Name**, run with `Item_Type` = `WrkSpc` (DMS Workspace) / `FOLDER` (DMS Folder) / `DHF` /
`DMR`; each row's `Parent_name` is `PROJECT-10045: Document Control`, `WrkSpc-20439: Archive #2`, `FOLDER-12518: …`.
`Get_Children` of a **folder** works (0.4 s, its DMS items: `Type: DMS`). traceability-matrix `doc_control_api._tree_raw`,
Note #132. The filter may select **Parent Original Id** instead of Parent Name: a bare number = the project id or
another row's `Original_id`. Set the filter's sort to **Treeview order** and keep the row order to get Orcanos's sibling
order (`qw-get-filter-results.md` → *Building a tree from a filter*, 2026-11-13).

**5. Copy-as-link items (2026-11-06).** Orcanos *Copy as link*
(https://help.orcanos.com/knowledgebase/copy-as-link-feature/) places ONE item under several
parents of the product tree — same key, same history; edits show everywhere; underlined in the
tree, blue in the grid; Traceability tab gets a *Copy As Link* relation; only Delete / Go to Source
on the link; default for DMS + Test Cases, same project only, not under another link, not for an
item with children. A saved filter lists the link as its own row (`IsLink = "1"`, same key), but
**`Filter_By parent_original_id = <node>` does not return it under the node it was linked to**
(user report, BOM Viewer). `Get_Children` of that node is the reliable way to list it.
The traceability-matrix BOM Viewer (`bom_api.tree_only_children`) reads `Get_Children` on every
expand and fetches the children the filter missed by `ID IN (…)` from their type's filter; a
child no filter returns is drawn from the `Get_Children` answer. **Not verified live yet:** which
`ID` `Get_Children` gives a link (the link row's or the original's) and what a link row's
`parent_original_id` holds — record it here after the first live run.

**4. Direct children only.** There is no depth parameter — a full tree means one call per node.

---

## Fetch a subtree (recursive, cycle-safe)

One call per node adds up fast, so **expand lazily** (fetch a node's children when the user opens
it) and only pre-fetch a whole subtree when you actually need it. Always carry a `visited` set —
same cycle discipline as [QW_Get_Object_Relations](qw-get-object-relations.md).

```js
function ensureArray(v) { return Array.isArray(v) ? v : v == null ? [] : [v]; }

async function getChildren(base, auth, itemId, verId) {
  const res = await fetch(`${base}/api/v2/Json/Get_Children/${itemId}?Ver_Id=${verId}`, {
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
- `Orcanos-infra/orcanos-documents.md` — what the tree means: DOC → paragraphs → items, `Root_Document`, the pool
- `Orcanos-infra/orcanos-supplier.md` — a SCAR's Action Items are its children; an action counts only when this call returns it under the SCAR
- [SKILL.md](SKILL.md) — base URL, auth, XML→JSON quirks
- [qw-get-object.md](qw-get-object.md) — one item's **full field set** (`Field[]`); this endpoint returns a fixed, pre-resolved subset instead
- [qw-get-object-relations.md](qw-get-object-relations.md) — **trace** links (a different graph from this parent/child tree), plus the cycle-safe expansion pattern
- [qw-get-filter-results.md](qw-get-filter-results.md) — batch fetch by saved filter, incl. `Traced Items Info`

---
**See also:** `Orcanos-infra/orcanos-version-management.md` (Views, branching, item version labels) and `Orcanos-infra/orcanos-database.md` (why `ID` ≠ `Original_id`: `objects` / `objects_ver_view`).
