# Add_Attachment — Attach a file or URL, or add a DMS revision

> Three jobs, one call:
> 1. ONE file (or a URL) on a work item's or defect's **Attachments** tab (`Object_Type` `OBJECT` / `DEFECT`).
> 2. A **new revision of a DMS item** — the controlled document's own file, A → B → C (`Object_Type=DMS`,
>    `Attachment_Type=FILE`). This is how a file BECOMES the document; an `OBJECT` upload on a DMS item only
>    lands on its Attachments tab.
> 3. A URL attachment (`Attachment_Type=URL` + `URL`).
>
> For an image that should show **inside** a rich-text field, use [Qw_Add_MiscAttachment](qw-add-misc-attachment.md) instead.

## Endpoint

```
POST <base>/api/v2/Json/Add_Attachment?Object_ID=<id>&Object_Type=<DEFECT|OBJECT>&Attachment_Type=FILE&Attachment_Description=<text>
Authorization: Basic <base64(username:password)> OR OrcanosAPIKey: <key>
Content-Type: multipart/form-data; boundary=…      (one file, form key "File")
```

No `QW_` prefix.

| Query parameter | Behaviour (Swagger) |
|---|---|
| `Object_ID` **required** | The item id (e.g. `1792`). |
| `Object_Type` **required** | **`OBJECT`** for a work item, **`DMS`** for a DMS item (→ a new **revision**), **`DEFECT`** for a defect — *not* the item type code. (Defects live in their own table, like `QW_Add_Defect`.) The help page writes `Object` / `DMS` / `Defect` in its bullets and `OBJECT/DMS/DEFECT` in its heading; upper case is what has been verified (`DEFECT`). Not `DMS_ITEM`. |
| `Attachment_Type` **required** | `FILE` (with the `File` form part) or `URL` (with `URL`). Swagger also lists `DMS` — that is the **attachment row type of a linked controlled document** (what `Attach_type` reads back as on another item's Attachments tab), *not* how to upload a revision: a revision is `Object_Type=DMS` + `Attachment_Type=FILE`. |
| `Attachment_Description` | Free text shown on the tab / the revision's change description. ⚠️ The help page and the Zapier step call it **`Attachment_Desc`**; Swagger calls it `Attachment_Description` — the Swagger name is the one verified live (DEFECT, 2026-10-18). Sending both is harmless (unknown params are ignored). |
| `URL` | Only for `Attachment_Type=URL`. |
| `KeepOldName` | `YES`/`NO`, **DMS only**: `YES` keeps the latest revision's current file name, `NO` uses the uploaded file's name. |
| `Over_Write` | Replace an existing attachment of the same name (help page: file attachments only; value not documented — `YES` presumably). |
| `File` (form part) | The file — for a file attachment **and** for a DMS revision. |

**Spec sources:** Swagger `…/api/swagger/docs/v1` (`POST /v2/Json/Add_Attachment`) · Orcanos help
[Add_Attachment](https://help.orcanos.com/knowledgebase/add_attachment/) (read 2026-11-04; its request/response
examples are screenshots only) · the Zapier step Orcanos ran in production to copy Jira attachments to a new defect
(Rami Azulay, 2026-10-18).

## Which variant to call

| You want | `Object_Type` | `Attachment_Type` | Other |
|---|---|---|---|
| A file on a work item's Attachments tab | `OBJECT` | `FILE` | `File`; `Over_Write` to replace |
| A file on a defect | `DEFECT` | `FILE` | `File` |
| A link on an item | `OBJECT` / `DEFECT` | `URL` | `URL` |
| **The document file of a DMS item (new revision)** | **`DMS`** | **`FILE`** | `File`; `KeepOldName`; `Object_ID` = the DMS item id |

A new DMS item has **no revision** until this call — create it with `QW_Add_Object` (type label of the tenant's
DMS type), then `Add_Attachment` `DMS`/`FILE` with the file. Read it back on
[`QW_Get_Section_Data` → **Revisions**](get-section-data/section-revisions.md) (`Item_Type: DMS`, `Ver_Id`
load-bearing): the newest row's `Attach_name` is the file. ⚠️ **Unverified live** (2026-11-04): whether the revision
letter is set by Orcanos (A for the first) and whether a revision added to an **approved** document is refused or
starts a new draft — test before relying on it. A DMS file download is AUDITED (Doc Review, Note #81).

> ✅ **Verified live** on orca60, 2026-10-18: `Object_Type=DEFECT` on DEFECT-2305 → `IsSuccess: true`, the file
> listed on the Attachments tab (ID 3490, `Attach_description` = the text sent). Still open: `OBJECT` for a non-defect
> type, and whether the answer carries the new attachment's id — the traceability-matrix integration dedupes by file
> NAME, so it does not rely on it.

## Response

`{"IsSuccess": true, "Data": "…", "Message": "Success"}`. Check `IsSuccess` — the Zapier step checked
for `"IsSuccess":true` in the body; a refusal is an HTTP 200 with `IsSuccess: false`.

## Python (httpx)

```python
r = await client.post(f"{base}/api/v2/Json/Add_Attachment",
                      params={"Object_ID": 1091, "Object_Type": "DEFECT", "Attachment_Type": "FILE",
                              "Attachment_Description": "Copied from Jira ZST-247"},
                      headers={"Authorization": auth},
                      files={"File": ("log.pdf", blob, "application/pdf")})
ok = r.json().get("IsSuccess")
```

## Which version it lands in

There is no version parameter. Observed 2026-10-18 (DEFECT 2305): the file was listed under the version the
calling integration works in (2.0, `Ver_Id` 341) and not under 1.0 — Orcanos attachments are per version, so a user
viewing another version sees an empty Attachments tab.

## Reading the file back

The tab is listed by [`QW_Get_Section_Data` → Attachments](get-section-data/section-attachments.md)
(`Ver_Id` load-bearing; verified it also answers for `DEFECT`, 2026-10-18) and downloaded through the
web-session route in [download-attachment.md](get-section-data/download-attachment.md) — Basic auth
is ignored there.

## See also
- [Qw_Add_MiscAttachment](qw-add-misc-attachment.md) — images inside rich text
- Used by: traceability-matrix `orcanos_client.add_attachment` (Integrations, v4.29.0); release validation (2026-11-04: the signed pack zip as the first **revision** of a NEW DMS item — `Object_Type: DMS`, `Attachment_Type: FILE`, read back on Revisions — **unverified live**); also the SBOM import (file on the release) and the BOM file import (2026-10-29: images on NEW Part (PRT) items + the BOM file on the product's part, `Object_Type: OBJECT`) — the PRT use is **unverified live**
