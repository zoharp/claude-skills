# Section: `Revisions` — the file history of a controlled document

`QW_Get_Section_Data` with `Section_Name=Revisions` returns **one row per file version of a DMS
item** — a copy of the document as it stood each time a file was uploaded or signed off in
Document Control. It is the audit trail behind the *Revisions* tab: what the file was called, who
described the change, which revision letter and change number it carried, where it got to in the
approval routing, whether a PDF rendition was produced, and which ECO released it.

**`Revisions` exists only on `DMS` items.** Any other `Item_Type` returns an empty section with
`IsSuccess: true` — see the silent-failure warning in [qw-get-section-data.md](qw-get-section-data.md).

---

## Call

```
GET <base>/api/v2/Json/QW_Get_Section_Data
      ?Item_ID=12767&Item_Type=DMS&Section_Name=Revisions&Ver_Id=363&RecordCount=1
```

`Ver_Id` is **usually the Document Control project's version id — but not always**. Read it off the
DMS item itself; a wrong version yields an empty list, not an error.

Rows arrive under `Data.section.revision[]`, each as a `field[]` array — flatten it with
`sectionRows(data, 'revision')` from [qw-get-section-data.md](qw-get-section-data.md#flatten-a-row-javascript).

---

## Fields

Keyed on `column` (the stable key — `title` is **not** unique here: two fields are titled `ID`).

### Identity

| `column` | `title` | `show` | Meaning |
|---|---|---|---|
| `ID` | ID | N | ⚠️ **The ATTACHMENT id** (`"3335"`) — the id of *this file version*, not the document. This is the id used to build a file URL. |
| `Obj_id` | ID | N | **The DMS item id** (`"12767"`) — the document these revisions belong to. Same number as `Doc_no`. |
| `Doc_no` | Document # | Y | The DMS item id again, as displayed to the user. |
| `Attach_type` | Type | Y | The work-item type — `DMS`. |

> The two `ID` titles are the single biggest trap in this section. Index rows on `column`, and
> never take "the ID field" without saying which one.

### The file

| `column` | `title` | `show` | Meaning |
|---|---|---|---|
| `Attach_name` | Name | Y | The uploaded file's name, e.g. `Quality Record Procedure_A_P.docx`. |
| `Attach_description` | Description | Y | The **change description** the user typed on upload. ⚠️ **HTML** (`<p>comment</p>`) — sanitize before rendering, strip tags before searching or exporting to Excel. |
| `Attach_path` | Path | N (`file_exist: Y`) | Absolute URL of the stored file, e.g. `https://app.orcanos.com/orca60FTP/PROJECT_10045/OBJECT_12767_…_V_1.docx`. ⚠️ Contains **spaces and other unescaped characters** — encode before using it in an `href` or a fetch. |
| `Attach_size` | File Size | Y | Size in **bytes**, as a string (`"634091"`). Format it yourself. |
| `Created_date` | Created Date | Y | When this file version was uploaded. ⚠️ **The date FORMAT is not stable** — see below. **No timezone** either way. |

> ### ⚠️ The date format is not stable — never sort these as text
>
> `Created_date` and `Effective_Date` have been observed in **two different formats on the same
> tenant**:
>
> | Seen | Example |
> |---|---|
> | ISO-ish | `2026-01-13 18:39:54` |
> | **Day-first** | `02/09/2026 05:28:42`, `27/01/2022 09:55:47` (orca60, 2026-09-02) |
>
> It appears to follow the **calling user's date-format preference**, not a fixed API contract — and
> [History](section-history.md)'s `TimeDone` came back **ISO in the same tenant, with the same
> credentials, minutes apart**. So you cannot assume one format per instance, per response, or even
> across sections of the same item.
>
> Consequences: `localeCompare` / lexical sorting is **wrong** for the day-first form (`27/01/2022`
> sorts after `06/08/2018` by luck, not by date), and `new Date("02/09/2026")` parses it as **Feb 9**
> in a US locale. **Sniff the format and parse explicitly:**
>
> ```js
> function parseOrcanosDate(v) {
>   const s = String(v || '').trim();
>   let m = /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2}):(\d{2})$/.exec(s);   // 2026-01-13 18:39:54
>   if (m) return new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +m[6]);
>   m = /^(\d{2})\/(\d{2})\/(\d{4})[ T](\d{2}):(\d{2}):(\d{2})$/.exec(s);     // 02/09/2026 05:28:42
>   if (m) return new Date(+m[3], +m[2] - 1, +m[1], +m[4], +m[5], +m[6]);     // DAY first
>   return null;                                                              // don't guess
> }
> ```
>
> Safer still: **order by `(Revision, Change_no)`**, which is unambiguous, and use dates for display.

### Revision & workflow

| `column` | `title` | `show` | Meaning |
|---|---|---|---|
| `Revision` | Revision | Y | The document revision this file belongs to — `A`, `B`, `V`… |
| `Change_no` | Change # | Y | The **minor change within that revision**. `(Revision, Change_no)` together identify a row; `Revision` alone does not. |
| `Routing_State` | Routing State | Y | Where *this revision* got to: `Draft`, `In Work`, `Pending Approved`, `Approved`, `Reject`, `Cancel`, **`Obsolete`**. ⚠️ **This — not `is_obsolete` — is how you tell a superseded revision** (observed on orca60: rev A.1 reads `Obsolete`). |
| `Effective_Date` | Approved Date | Y | When the revision was approved. `null` until it is. |
| `color_code` | Color Code | N | The hex swatch Orcanos uses for that routing state (`#97E0AC` approved, `#C4C0C6` obsolete) — reuse it to stay consistent with their UI. |
| `is_obsolete` | is_obsolete | N | ⚠️ **Unreliable — observed EMPTY on an obsolete revision** (orca60, 2026-09-01: rev A.1 was `Routing_State: "Obsolete"` with `is_obsolete: ""`). Never branch on it. Use `Routing_State === 'Obsolete'`. |

### PDF rendition

| `column` | `title` | `show` | Meaning |
|---|---|---|---|
| `PDFPreviewFileExist` | PDFPreviewFileExist | N | `"Y"` if a PDF rendition is **stored**. ⚠️ **Does NOT mean a PDF is unavailable when `"N"`** — verified: item 18070 reports `N`, and [ViewAttachment](view-attachment-url.md) served a 448 KB PDF anyway (rendered on demand). Don't gate a viewer link or a download on this flag. |
| `pdf_path_name` | PDF Path Name | N | Filename of the rendition, e.g. `DMS_12767_…_V_1.pdf`. |
| `pdf_path` | PDF Path | N (`file_exist: Y`) | Absolute URL of the rendition. Same encoding caveat as `Attach_path`. |

### Office protection

| `column` | `title` | `show` | Meaning |
|---|---|---|---|
| `is_protected` | Protected | N | For Office files: `"0"` / `"1"` — whether the document is protected (edit-locked) in the stored copy. |
| `ProtectionReasons` | ProtectionReasons | N | Why, when protected; `null` otherwise. |

### ECO (Engineering Change Order)

All `null` unless this revision was released through an ECO.

| `column` | `title` | `show` | Meaning |
|---|---|---|---|
| `eco_no` | ECO Number | Y | The releasing ECO's number. |
| `eco_status` | Related ECO Status | Y | That ECO's status. |
| `eco_routing_state` | Related ECO Routing State | Y | That ECO's routing state. |
| `eco_version` | ECO Version | N | The ECO's version. |
| `eco_type` | ECO Type | N | The ECO's item type. |
| `eco_release_date` | ECO Release Date | Y | When the ECO released this revision. |
| `eco_action_type` | ECO Action Type | Y | What the ECO did to the document (add / change / obsolete…). |

### Internal

| `column` | `title` | `show` | Meaning |
|---|---|---|---|
| `HangfireJobID` | HangfireJobID | N | The background-job id that produced the rendition. Diagnostic only — never key on it. |

---

## Reading the rows

```js
const rows = sectionRows(resp, 'revision');   // see qw-get-section-data.md

// Newest first. Order from the API is NOT guaranteed — and dates must NOT be sorted as text
// (the format is user-dependent, see above), so order by revision letter + change number.
const byRecency = [...rows].sort((a, b) =>
  a.Revision === b.Revision ? Number(b.Change_no) - Number(a.Change_no)
                            : b.Revision.localeCompare(a.Revision)
);

// The current released file. `is_obsolete` is unreliable — read Routing_State.
const current = rows.find(r => r.Routing_State === 'Approved');
const superseded = r => r.Routing_State === 'Obsolete';

// To SHOW or DOWNLOAD the file, build a ViewAttachment URL from the row — the pdf_path /
// Attach_path URLs in the row are direct store paths and are blocked (302 -> /orca60Ftp/Error).
// see view-attachment-url.md (link) and download-attachment.md (backend fetch)

// Label a row the way the UI does.
const label = r => `${r.Revision}.${r.Change_no} — ${r.Routing_State}`;
```

⚠️ **Traps worth repeating:**

- **Order is not specified.** Rows come back in whatever order the query produced. Sort on
  `Created_date`, or on `(Revision, Change_no)` — never rely on `[0]` being the latest.
- **`RecordCount` truncates from the top of *that* order**, and there is no page parameter. If you
  need the full history, omit it; if you cap it, say "showing N of ?" rather than implying it's all.
- **"Approved" is per revision, not per document.** Several rows can read `Approved` — a superseded
  one flips to `Routing_State: "Obsolete"`, and **`is_obsolete` stays empty when it does**.
- **`Attach_path` / `pdf_path` are not fetchable.** Verified: both 302 to `/orca60Ftp/Error`, with
  and without credentials. They are informational; use
  [ViewAttachment](view-attachment-url.md) to open or [download](download-attachment.md) the file.
- **A DMS item with no uploaded file has no rows at all**, which looks identical to a wrong
  `Ver_Id`. Confirm the item and version first.

---

## Opening a revision's file

Don't link `pdf_path` / `Attach_path` directly — build a `/web/Download/ViewAttachment` URL from the
row instead, so Orcanos applies its own permission check:
**[view-attachment-url.md](view-attachment-url.md)**. It needs only `Obj_id`, `Attach_type`, the
`Ver_Id` you queried with, and the row's `ID` (the **attachment** id).

To fetch the bytes from a backend — including going straight from
**"item + version + revision letter" to a file** — see
**[download-attachment.md](download-attachment.md#starting-from-a-revision-letter-instead-of-an-attachment-id)**.
⚠️ What comes back depends on this row's `Routing_State`: **Approved / Obsolete give a stamped PDF,
a Draft gives the original Office file** — and the `Content-Type` header claims `application/pdf`
in every case.

---

## See also
- [qw-get-section-data.md](qw-get-section-data.md) — the endpoint, params and shared envelope
- [view-attachment-url.md](view-attachment-url.md) — open one revision's PDF in the Orcanos viewer
- [SKILL.md](../SKILL.md) — base URL, auth, XML→JSON quirks
- [qw-get-filter-results.md](../qw-get-filter-results.md) — find DMS items and their `Ver_Id`
