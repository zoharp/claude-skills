# Viewing a DMS revision's file — `/web/Download/ViewAttachment`

How to **open one specific revision's PDF** (or its source file) of a controlled document.

This is a **UI route under `/web/`**, not an API route under `/api/v2/` — it returns the file
itself, streamed through Orcanos' own permission check, rather than a JSON envelope. It is the
supported way to show a revision to a user, and it is built entirely from values that
[`QW_Get_Section_Data` → `Revisions`](section-revisions.md) already returned.

---

## The URL

```
https://app.orcanos.com/orca60/web/Download/ViewAttachment
  ?ItemId=18070
  &ItemType=DMS
  &VersionId=363
  &AttachmentId=2917
  &name=DMS_18070_Software%20Requirements%20Specifications%20%282%29_B1.pdf
```

| Part | Value | Where it comes from |
|---|---|---|
| Base | `https://app.orcanos.com/orca60/web/` | Tenant base URL + `/web/` — the same base as every other deep link (see [SKILL.md](../SKILL.md#build-web-urls-deep-links-into-the-orcanos-ui)). |
| Route | `Download/ViewAttachment` | Fixed. |
| `ItemId` | `18070` | The **DMS item** id — `Obj_id` (or `Doc_no`) from the revision row. |
| `ItemType` | `DMS` | The item type **code** — `Attach_type` from the row. |
| `VersionId` | `363` | The **numeric `Ver_Id`** — the same one passed to `QW_Get_Section_Data`. |
| `AttachmentId` | `2917` | ⚠️ The **attachment id** — the `ID` column (`show: "N"`) of *that revision row*. **Not** `Obj_id`, which is titled `ID` as well. **This is the only parameter that selects the revision.** |
| `name` | `DMS_18070_…_B1.pdf` | Cosmetic. ⚠️ **Verified ignored by the server** (2026-09-01) — any value, or none, returns the same file. Include it to match Orcanos' own links; never rely on it. |

> **Verified 2026-09-01** against `orca60`: signed in, this URL returns **`200 application/pdf`**,
> 448,915 bytes, `Content-Disposition: inline; filename="DMS_18070_…_B1_APP.pdf"`. The `_APP`
> suffix is the routing state (`APP` approved / `OBS` obsolete) and is chosen by the **server**.

**Everything but the base comes from one revision row**, so a "view this revision" link is a pure
function of the row — no extra call.

---

## Building it (JavaScript)

```js
// encodeURIComponent leaves ( ) ! ' * alone; Orcanos' own links percent-encode them (%28/%29).
const enc = s => encodeURIComponent(String(s))
  .replace(/[!'()*]/g, c => '%' + c.charCodeAt(0).toString(16).toUpperCase());

const base = u => String(u).replace(/\/+$/, '');   // never double the slash

// row = a flattened Revisions row (see qw-get-section-data.md); versionId = the Ver_Id you queried with
function viewAttachmentUrl(baseUrl, row, versionId) {
  if (!row.Obj_id || !row.ID) return null;   // ← render nothing rather than a broken link
  const name = row.pdf_path_name || row.Attach_name || '';   // cosmetic only — server ignores it
  return `${base(baseUrl)}/web/Download/ViewAttachment`
       + `?ItemId=${enc(row.Obj_id)}`
       + `&ItemType=${enc(row.Attach_type || 'DMS')}`
       + `&VersionId=${enc(versionId)}`
       + `&AttachmentId=${enc(row.ID)}`
       + (name ? `&name=${enc(name)}` : '');
}
```

---

## Traps

- **`AttachmentId` is the row's `ID`, not the document's.** The Revisions section has **two fields
  titled `ID`** — `ID` (the attachment) and `Obj_id` (the DMS item). It is the **only** parameter
  that picks the revision (`2917` → B.1, `2300` → A.1), so the wrong one silently serves the wrong
  file. Index on `column`.
- **Omitting `AttachmentId` silently serves the LATEST revision** — verified: no error, just a
  different document than the one the link claimed to be.
- **`name=` decides nothing** — verified ignored. It does not choose PDF-vs-source and does not
  choose the revision; the response is **always the stamped PDF**, whatever you put there.
- **`PDFPreviewFileExist: "N"` does not mean this link fails.** Item 18070 reports `N` and the
  viewer served a 448 KB PDF regardless — it renders on demand. **Don't hide the link on that flag.**
- **Encode the name properly.** These filenames routinely contain spaces and parentheses
  (`Specifications (2)`); bare `encodeURIComponent` leaves `(` and `)` un-encoded. Use the `enc`
  helper above.
- **`VersionId` must match the item's own version** — the same `Ver_Id` that returned the row. A
  mismatched version is not an error, just a page that doesn't show the file.
- **This is a browser-session route.** It is served to a user **logged into Orcanos in that
  browser** — open it in a new tab / `window.open`, don't `fetch` it. **`Authorization: Basic` is
  ignored** (verified: 302 to the login page), so a backend must log in through the web form —
  see **[download-attachment.md](download-attachment.md)**.
- **Prefer it over the raw `pdf_path` / `Attach_path` URLs** the section also returns. Those are
  direct paths into the FTP-style store and are **blocked** — verified: 302 to `/orca60Ftp/Error`,
  with or without credentials. `ViewAttachment` is the only route that serves the file, and it
  applies Orcanos' own item-permission check.
- **A wrong or missing part does not error** — same as every `/web/` deep link. Build the URL only
  when every part is present, and render nothing otherwise.

---

## See also
- [download-attachment.md](download-attachment.md) — fetching the same file from a **backend** (web-form login → session cookie), verified working
- [section-revisions.md](section-revisions.md) — the row this URL is built from, field by field
- [qw-get-section-data.md](qw-get-section-data.md) — the call that returns it
- [SKILL.md](../SKILL.md#build-web-urls-deep-links-into-the-orcanos-ui) — the other `/web/` deep links (item view, filter listing)
