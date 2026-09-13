# Section (Tab) Data — QW_Get_Section_Data

One endpoint that returns **the contents of a work item's tabs**. An Orcanos work item is shown in
the UI with a row of tabs — Attachments, History, Relations, Defects, Revisions… — and this call
returns the rows behind **one** of them, chosen by `Section_Name`.

Because each section returns a **completely different set of columns**, this folder is split:
this file is the *transport* (endpoint, params, envelope, shared quirks), and one file per section
documents what that section's rows actually mean.

| Section | Applies to | Doc |
|---|---|---|
| `Revisions` | **DMS only** | **[section-revisions.md](section-revisions.md)** — every file version of a controlled document: uploads, sign-offs, routing state, PDF renditions, ECO release |
| `Attachments` | most types | *(not documented yet)* |
| `History` | **any type** | **[section-history.md](section-history.md)** — the item's change log: one row per event, with per-field before/after diffs nested in `details[]` |
| `Relations` | most types | *(not documented yet)* — see also [qw-get-object-relations.md](../qw-get-object-relations.md) |
| `Defects` | most types | *(not documented yet)* |

**Companions** — getting at the file a `Revisions` row describes:

- [view-attachment-url.md](view-attachment-url.md) — the `/web/Download/ViewAttachment` **link** that
  opens one revision's PDF for a logged-in user, built entirely from one row.
- [download-attachment.md](download-attachment.md) — **fetching the bytes from a backend**. ⚠️ That
  route ignores `Authorization: Basic` and the row's `pdf_path` is blocked; a web-form login is
  required. Verified working 2026-09-01.

> ⚠️ **A section that doesn't apply to the item type does not error.** Asking for `Revisions` on a
> `T_CASE` returns `IsSuccess: true` with an empty/absent section. Never read "no rows" as "this
> document has no revisions" without confirming the item type is right.

**Swagger:** `https://<instance>/<tenant>/api/swagger/docs/v1` → `/v2/Json/QW_Get_Section_Data`
(verified against `orca60`, 2026-09-01).

---

## Endpoint

```
GET  <base>/api/v2/Json/QW_Get_Section_Data
       ?Item_ID=<id>&Item_Type=<code>&Section_Name=<section>&Ver_Id=<verId>[&RecordCount=<n>]
Authorization: Basic <base64(username:password)>   OR   Bearer <api-key>
```

`<base>` includes the tenant, e.g. `https://app.orcanos.com/orca60`.
Auth: same options as every endpoint — see [SKILL.md](../SKILL.md).

**GET with query-string params** — there is no POST/JSON-body form. The API key may alternatively
be sent in the `OrcanosAPIKey` header.

---

## Request Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `Item_ID` | string | **Yes** | The work item's id, e.g. `12767`. The **display id** — the plain number, not the parenthetical link id of `"12767 (9876)"`. |
| `Item_Type` | string | **Yes** | The item type **ORIGINAL CODE** — `DMS`, `T_CASE`, `MR_REQ` — not the label ("Document"). |
| `Section_Name` | string | **Yes** | Exactly one section name: `Revisions`, `Attachments`, `History`, `Relations`, `Defects`. **One only** — a comma-separated list is not supported. ⚠️ **Case-sensitive** — verified: `history` returns `IsSuccess: false, Message: "Cannot find table 0."` |
| `Ver_Id` | integer | **Yes** | The numeric **version id** (`Ver_Id` from `QW_Login`'s `Projects.Project[].Version[]`), e.g. `363` — not the version label `1.0`. |
| `RecordCount` | string | No | How many rows to return (`10`, `20`, `50`…). A **top-N cap, not pagination** — there is no page-number parameter, so you cannot walk past it. **Omitting it returns everything** (verified on History: no param → all 36 rows; `5` → 5; `500` → all 36). |

⚠️ **How much each parameter matters is per section — verified, and they disagree:**

| Section | `Item_Type` | `Ver_Id` | Wrong value does what |
|---|---|---|---|
| `Revisions` | selects | **required** | `Ver_Id` 0 / 1 / 99999 → **0 rows, `IsSuccess: true`** — identical to "this document has no revisions" |
| `History` | **ignored** | **ignored** | `ZZZ_NOT_A_TYPE` and `Ver_Id=1` return the same rows as the correct values — History is keyed on `Item_ID` alone |

Always send correct values; never rely on a wrong one being rejected. **`Ver_Id` cannot be recovered
from the item**: `QW_Get_Object` returns the version *label* (`"1.0"`), not the numeric id (`363`) —
take it from `QW_Login`'s `Projects.Project[].Version[].Ver_id` or from the filter result that
produced the item.

⚠️ **`Ver_Id` is the item's own version, not the caller's current one.** For `Revisions` it is
usually the **Document Control** project's version — but *not always*; a DMS item can live in any
project. Take the version from the item you are querying (`QW_Get_Filter_Results` / `QW_Get_Object`),
never from the panel or the logged-in user's last-used project. A wrong `Ver_Id` returns an **empty
section, not an error**.

---

## Response envelope

```json
{
  "IsSuccess": true,
  "Data": { "section": { "<rowName>": [ { "field": [ {…}, {…} ] } ] } },
  "Message": "",
  "HttpCode": 200
}
```

Three shared traps:

1. **`Data` is declared as `string` in Swagger** (`ResultClass[String]`) but arrives as a nested
   **object** on live instances. Handle both — if it comes back as a string, `JSON.parse` it once.
2. **The row array is named per section** — `Data.section.revision` for Revisions, and a different
   key for every other tab. Don't hard-code `section.revision` in shared code.
3. **XML→JSON quirk:** a section with **one** row arrives as a single object, not a 1-element
   array — and so does a row with a single `field`. Wrap both with `ensureArray()`
   (see [SKILL.md](../SKILL.md#xml-to-json-quirks)).

### A row can be **two levels deep**

Most sections give each row a single `field[]`. **`History` also carries a `details[]`** — an array
of sub-rows, each with its own `field[]` (the per-field before/after diffs). `flattenRow()` below
reads only `field`, so check for `details` before assuming a section is flat; see
[section-history.md](section-history.md#row-shape--two-levels).

### Every row is a `field[]` array, not an object

```json
{ "title": "Name", "show": "Y", "column": "Attach_name", "file_exist": null,
  "Value": "Quality Record Procedure_A_P.docx" }
```

| Key | Meaning |
|---|---|
| `title` | The UI **column header**. ⚠️ **Not unique** — Revisions has two fields titled `ID`. |
| `column` | The **internal column name** — this is the stable key. Always index on it. |
| `show` | `Y` = the Orcanos UI displays this column; `N` = hidden. **Hidden ≠ useless** — the attachment id and the file URL are both `show: "N"`. |
| `file_exist` | `Y` only on fields that hold a **file path** whose file is present on the server; `null` otherwise. |
| `Value` | Always a **string or `null`** — numbers, dates and booleans all arrive as text. |

### Flatten a row (JavaScript)

```js
const ensureArray = v => Array.isArray(v) ? v : v == null ? [] : [v];

// field[] -> { Attach_name: "…", ID: "3335", … }  — keyed on `column`, NOT `title`
function flattenRow(row) {
  return Object.fromEntries(
    ensureArray(row?.field).map(f => [f.column, f.Value])
  );
}

function sectionRows(data, rowName /* e.g. 'revision' */) {
  const d = typeof data?.Data === 'string' ? JSON.parse(data.Data) : data?.Data;
  return ensureArray(d?.section?.[rowName]).map(flattenRow);
}
```

---

## Error handling

| Result | Meaning |
|---|---|
| `401` | Session expired / bad auth — see [SKILL.md](../SKILL.md#session-management). |
| `500` + `ResultClass[XMLError]` | Malformed request (usually a bad `Ver_Id` type or a missing required param). |
| `200`, `IsSuccess: true`, empty section | **The silent failure.** Wrong `Ver_Id`, wrong `Item_Type`, section not applicable to the type, or genuinely no rows — indistinguishable. Validate the item's type and version *before* the call so an empty result can be trusted. |

---

## See also
- [SKILL.md](../SKILL.md) — base URL, auth, XML→JSON quirks
- [section-revisions.md](section-revisions.md) — the `Revisions` section, field by field
- [qw-get-object.md](../qw-get-object.md) — fetch the item itself (to confirm its type and version)
