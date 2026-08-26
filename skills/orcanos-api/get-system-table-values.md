# List a System Table's Values — GetSystemTableValues

Returns the **values (list items) of one Orcanos system table**, paged. A *system table* is the
tenant's repository of predefined values that back custom fields of type **combo box** and
**multi-select** — i.e. this is the endpoint you call to populate a picklist dropdown from the
source of truth rather than hard-coding options.

Use it to:
- build a real picklist/dropdown for a custom field (Category, Work Item Status, any custom list);
- validate a value before sending it to [QW_Add_Object](qw-add-item.md) / `QW_Update_Object`;
- resolve a stored internal code (`Text`) back to its human label (`Display_text`);
- render an admin-style "browse a list" screen.

> **Two different "codes" — don't conflate them.**
> `TableName` identifies **the table** (e.g. `SYS_GROUPS`). `Code` filters **one value inside**
> that table. `TableName` is the required one; `Code` is an optional narrowing filter.

**Note the method name:** `GetSystemTableValues` — **no `QW_` prefix**, like
[Get_Children](get-children.md) and [GetFilterList](get-filter-list.md).

**Note the verb:** this is a **`GET` with query-string parameters**, not the `POST`-with-JSON-body
shape that most endpoints in this skill use. There is no request body.

---

## Endpoint

```
GET  <base>/api/v2/Json/GetSystemTableValues?TableName=<code>&PageNo=<n>&PageSize=<n>
Authorization: Basic <base64(username:password)>     ← Basic auth
   — or —
OrcanosAPIKey: <api-key>                             ← API-key auth (this endpoint's own header)
Content-Type: application/json
```

`<base>` includes the tenant, e.g. `https://app.orcanos.com/orca60` or
`https://us.orcanos.com/covaris`. Auth options: see [SKILL.md](SKILL.md).

> ⚠️ **API-key header name differs here.** Swagger declares a dedicated `OrcanosAPIKey` header on
> this endpoint alongside `Authorization`. If you're using key auth and `Authorization: Bearer …`
> gets rejected, send `OrcanosAPIKey: <key>` instead. Basic auth via `Authorization` works either way.

---

## Request Parameters

All parameters are **query-string**. Only `TableName` is required.

| Parameter | Required | Type | Description |
|---|---|---|---|
| `TableName` | **Yes** | string | The **system table's code** — e.g. `SYS_GROUPS`. This is the list you want the values of. Swagger marks it required; omitting it is an error, not an "all tables" query. |
| `PageNo` | No | string (int) | 1-based page number. Start at **`1`**, not `0`. |
| `PageSize` | No | string (int) | Rows per page. **Keep it in 1–100.** |
| `OrderBy` | No | string | Sort expression. Column names are not documented — see the trap below. |
| `Code` | No | string | Filter to a **single value's** code within the table. Not the table code. |
| `Description` | No | string | Filter by the value's description text (likely a contains/LIKE match — unverified). |

> ⚠️ **Everything is typed `string` in swagger, including the paging numbers.** Send
> `PageNo=1&PageSize=50` as plain query text; don't try to force JSON numbers. This mirrors
> [QW_Get_Filter_Results](qw-get-filter-results.md), where numeric-vs-string paging flags
> materially change the response.

### Page size: use 1–100

Treat **100 as the working ceiling** and 1 as the floor; clamp before sending
(`Math.min(100, Math.max(1, n))`). Swagger does not declare a maximum, so an over-large value is
not guaranteed to error — the realistic failure mode is a **silently truncated or empty page**,
which reads as "the table only has N values." Page instead of asking for everything at once.

**Defaults are undeclared.** Omitting `PageNo`/`PageSize` does not reliably mean "all rows" — it
means whatever the server defaults to. **Always pass both explicitly** and page until you've seen
`Total_records` rows.

---

## Response

Swagger types this operation's 200 body as a bare `object` — the shape is **not declared**. Its
sibling `SystemTableValue_Get` *is* declared, as `ResultClass[Filter]`, and this endpoint's paging
parameters line up with that envelope's `Total_records` / `Current_page` / `Page_size` fields, so
expect the standard wrapper:

```json
{
  "IsSuccess": true,
  "Data": {
    "Object": [
      {
        "Id": "1",
        "Type": "SYS_GROUPS",
        "Field": [
          { "Name": "Code",        "Text": "QA",              "Display_text": "QA" },
          { "Name": "Description", "Text": "Quality Assurance" },
          { "Name": "IsDefault",   "Text": "0" },
          { "Name": "IsActive",    "Text": "1" }
        ]
      }
    ],
    "Total_records": "37",
    "Current_page": "1",
    "Page_size": "50"
  },
  "Message": "Success",
  "HttpCode": 200
}
```

> ⚠️ **The sample rows above are illustrative, not captured from a live call.** The envelope
> (`IsSuccess` / `Data.Object[]` / `Total_records` / `Current_page` / `Page_size`) is inferred from
> the declared sibling schema; the per-value field names come from the
> `SystemTableValue_Save_Parameter` definition (below), which is the same data going the other way.
> **Log one real response before you code against exact field names** — and update this file with
> what comes back.

The value-level attributes Orcanos itself round-trips (from `SystemTableValue_Save_Parameter`) are:

| Attribute | Meaning |
|---|---|
| `Code` | The value's own code — the stored/internal identifier. |
| `Description` | The human-readable label. **This is what you show the user.** |
| `IsDefault` | `0`/`1` — preselect this option. |
| `IsActive` | `0`/`1` — used for statuses. **Filter inactive values out of a picker.** |
| `IsComplete` | `0`/`1`. |
| `IsFreeze` | `0`/`1` — used for statuses (frozen = locks the item). |
| `Color` | Hex, **without** the leading `#` — prepend it before using in CSS. |

Read field values with the standard `Display_text → Display → Text → Value` precedence
(`fieldValue()` in [SKILL.md](SKILL.md)) — the same reason picklists render labels instead of ids.

**XML→JSON quirk:** a table with exactly one value may arrive as a single object rather than a
1-element array. Wrap `Data.Object` with `ensureArray()` (see [SKILL.md](SKILL.md)).

---

## Traps

**1. `TableName` vs `Code`.** The single most likely mistake: passing the table's code as `Code`.
That filters *values* by that code inside a table you never named, and `TableName` is missing.
Table → `TableName`. Value → `Code`.

**2. An unknown `TableName` may come back empty rather than as an error.** Same failure mode as
[GetFilterList](get-filter-list.md)'s label-vs-code trap: an empty list is indistinguishable from
"this table has no values." Verify against a table you know is populated before concluding a code
is wrong, and surface "no values found" distinctly from "call failed."

**3. `OrderBy` column names are undocumented.** A wrong column will not necessarily error — you may
get server-default ordering back and mistake it for your sort. Verify the order actually changed
before relying on it; otherwise omit `OrderBy` and sort client-side.

**4. Don't cache across tenants or forever.** System tables are admin-editable (custom ones), and
automation-generated tables are refreshed by the system. Cache per session at most, and re-fetch
after any admin change.

**5. Some tables are read-only.** `Work Item Status`, `Category`, and the auto-generated
"Work Item List" tables cannot be edited or deleted. Reading them is fine; don't build UI that
offers to change them.

---

## Fetch all values (paged, clamped)

```js
function ensureArray(v) { return Array.isArray(v) ? v : v == null ? [] : [v]; }

async function getSystemTableValues(base, auth, tableName, { pageNo = 1, pageSize = 50, code, description, orderBy } = {}) {
  const qs = new URLSearchParams({
    TableName: tableName,
    PageNo: String(Math.max(1, pageNo)),
    PageSize: String(Math.min(100, Math.max(1, pageSize))),   // 1..100
  });
  if (code) qs.set('Code', code);
  if (description) qs.set('Description', description);
  if (orderBy) qs.set('OrderBy', orderBy);

  const res = await fetch(`${base}/api/v2/Json/GetSystemTableValues?${qs}`, {
    headers: { Authorization: auth, 'Content-Type': 'application/json' },
  });
  if (res.status === 401) throw new Error('Orcanos session expired');
  if (!res.ok) throw new Error(`GetSystemTableValues ${tableName}: HTTP ${res.status}`);

  const data = await res.json();
  if (data.IsSuccess === false) throw new Error(`GetSystemTableValues ${tableName}: ${data.Message}`);

  return {
    rows: ensureArray(data.Data?.Object),
    total: parseInt(data.Data?.Total_records, 10) || 0,
  };
}

// Walk every page. Bounded so a wrong Total_records can't spin forever.
async function getAllSystemTableValues(base, auth, tableName, pageSize = 100) {
  const out = [];
  for (let page = 1; page <= 200; page++) {
    const { rows, total } = await getSystemTableValues(base, auth, tableName, { pageNo: page, pageSize });
    out.push(...rows);
    if (!rows.length || out.length >= total) break;   // short page OR total reached
  }
  return out;
}
```

The loop stops on a **short/empty page** as well as on `Total_records`, because `Total_records` is
undeclared for this operation and may echo the page size back (a known behavior on
[QW_Get_Filter_Results](qw-get-filter-results.md) with the wrong paging flags).

### Turn it into picklist options

```js
function fieldValue(row, name) {
  const f = row.Field?.find(f => f.Name === name || f.Title === name);
  return f?.Display_text || f?.Display || f?.Text || f?.Value || '';
}

const options = (await getAllSystemTableValues(base, auth, 'SYS_GROUPS'))
  .filter(r => fieldValue(r, 'IsActive') !== '0')          // hide inactive
  .map(r => ({
    value: fieldValue(r, 'Code'),                          // send this back to the API
    label: fieldValue(r, 'Description') || fieldValue(r, 'Code'),  // show this
    isDefault: fieldValue(r, 'IsDefault') === '1',
    color: fieldValue(r, 'Color') ? `#${fieldValue(r, 'Color')}` : undefined,  // no '#' in the API
  }));
```

---

## Sibling system-table endpoints

Same swagger tag, in case you need more than reading a list:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/v2/Json/GetSystemTable` | List **the tables themselves** (not their values). Same optional `PageNo` / `PageSize` / `OrderBy` / `Code` / `Description` params; **no `TableName`**. Call this first to discover valid `TableName` codes. |
| `POST` | `/v2/Json/SystemTableValue_Get` | **One** value's detail. Body `{ "TabelName": "...", "Code": "..." }` — ⚠️ the property really is misspelled **`TabelName`** in the API contract. Returns the declared `ResultClass[Filter]`. |

Write operations exist too (`SystemTableValue_Save_Parameter` / `SystemTableValue_Delete_Parameter`
definitions), with the same `TabelName` misspelling. Save uses `Operation: "add"` for a new entry
and an empty `Operation` for update. **Don't write to system tables from an integration unless
that's explicitly the task** — they back live picklists across the whole tenant.

---

## Reading the contract yourself

The swagger **UI** is a SPA (its `#!/Json/Json_GetSystemTableValues` fragment can't be fetched),
but the raw spec behind it is plain JSON and is worth pulling whenever an endpoint here is
under-documented:

```
https://<instance>/<tenant>/api/swagger/docs/v1
```

e.g. `https://app.orcanos.com/orca60/api/swagger/docs/v1` — no auth needed, ~140 KB, every path,
parameter and definition. (`docs/v2` 404s; the spec is `v1` even though the routes are `/v2/`.)
This file's parameter table was extracted from exactly that.

---

## See also
- [SKILL.md](SKILL.md) — base URL, auth, XML→JSON quirks, `fieldValue()`
- [qw-get-item-add-edit.md](qw-get-item-add-edit.md) — an item type's **form definition**, which already
  embeds each field's picklist values. Prefer it when rendering a whole form; use *this* endpoint when
  you need one list standalone, or the list's own metadata (`IsActive`, `IsDefault`, `Color`)
- [qw-get-filter-results.md](qw-get-filter-results.md) — the `Field[]` / `Display_text` extraction rules
  and the paging-flag gotchas referenced above
- [get-filter-list.md](get-filter-list.md) — the other no-`QW_`-prefix lookup endpoint, with the same
  "wrong identifier returns an empty list, not an error" trap
- Orcanos help: [System Tables](https://help.orcanos.com/knowledgebase/system-tables-2/)
