# Section `Attachments` — the files attached to a work item

`QW_Get_Section_Data?Section_Name=Attachments` lists what is on an item's **Attachments** tab: plain
uploaded files (a STEP model, a spreadsheet, a Word file) and linked controlled documents.

> **Measured against `orca60` on 2026-09-25** — `MR_REQ 18142`, `Ver_Id 434`. Transport, envelope
> and the `field[]` row shape are in [qw-get-section-data.md](qw-get-section-data.md).

---

## Request

```
GET <base>/api/v2/Json/QW_Get_Section_Data
      ?Item_ID=18142&Item_Type=MR_REQ&Section_Name=Attachments&Ver_Id=434
```

| Parameter | Behaviour (verified) |
|---|---|
| `Item_Type` | **Ignored** — `ZZZ` returns the same rows. Send the real code anyway. |
| `Ver_Id` | ⚠️ **Load-bearing.** `Ver_Id=1` → `attachment: null`, `IsSuccess: true` — identical to "no attachments". Use the item's own numeric version (the `Version` on its filter-result row). ⚠️ **A DEFECT's files are per version too** (verified orca60 2026-10-18, DEFECT 2305: two files under `Ver_Id` 341 = 2.0, none under 331 = 1.0, though the defect opens in both) — the Orcanos UI shows the tab empty in the other version. |

## Response

Rows live under **`Data.section.attachment`** (not `revision`). `null` when there are none; a
single object when there is one (XML→JSON quirk).

```json
{"field": [
  {"column": "Attach_name",        "title": "Name",         "Value": "Risk Management File (4).docx"},
  {"column": "Attach_description", "title": "Description",  "Value": null},
  {"column": "Created_date",       "title": "Created Date", "Value": "03/02/2022 13:12:47"},
  {"column": "ID",                 "title": "ID", "show": "N", "Value": "2918"},
  {"column": "Attach_path",        "title": "Path", "file_exist": "Y", "Value": "https://…/orca60FTP/PROJECT_7509/OBJECT_18142_Risk Management File (4).docx"},
  {"column": "Obj_id",             "title": "ID", "show": "N", "Value": "18142"},
  {"column": "Attach_type",        "title": "Type",         "Value": "FILE"},
  {"column": "Revision" / "Change_no" / "Routing_State" / "Doc_no", "Value": null},
  {"column": "updated_date",       "Value": null},
  {"column": "Attach_size",        "title": "File Size",    "Value": "73223"}
]}
```

| Column | Meaning |
|---|---|
| `ID` | The **attachment id** — what `ViewAttachment` selects by (`AttachmentId`). Titled `ID`, like `Obj_id`. |
| `Obj_id` | The owning item. |
| `Attach_type` | `FILE` = a plain upload. `DMS` = a linked controlled document (its file is a DMS revision — use [Revisions](section-revisions.md)). |
| `Attach_size` | Bytes — matched the downloaded size exactly. |
| `Attach_path` | Direct store path — **blocked**, like Revisions' `pdf_path`. Don't use it. |

## Downloading one

The same web-session route as a DMS revision ([download-attachment.md](download-attachment.md)),
with the item's own type and version:

```
/web/Download/ViewAttachment?ItemId=18142&ItemType=MR_REQ&VersionId=434&AttachmentId=2918
```

Verified: `200`, `Content-Disposition: inline; filename="Risk Management File (4).docx"`,
73,223 bytes, `PK…` — while **`Content-Type` said `application/pdf`**. A wrong `AttachmentId` lands
on `/web/Error/HttpError` (200, `text/html`, **no `Content-Disposition`**).

⚠️ A plain attachment can be any format (a STEP file is text), so the `%PDF` / `PK` magic-byte
guard used for DMS revisions does not apply. The evidence that you got a file is the
**`Content-Disposition` filename** plus a landing URL that is not `/account/login` or `/error/`.
