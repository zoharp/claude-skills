# Qw_Add_MiscAttachment — Upload images for a rich-text field

> Uploads one or more files **into the project's store, not onto any item**, and answers with the
> URL of each. That URL is what goes into an `<img src>` inside a rich-text field (Description,
> a custom rich-text field). For a file on an item's **Attachments tab** use
> [Add_Attachment](add-attachment.md) instead.

## Endpoint

```
POST <base>/api/v2/Json/Qw_Add_MiscAttachment?ProjectID=<project id>
Authorization: Basic <base64(username:password)> OR OrcanosAPIKey: <key>
Content-Type: multipart/form-data; boundary=…
```

`<base>` includes the tenant, e.g. `https://app.orcanos.com/orca60`. Note the casing: **`Qw_`**, not `QW_`.

| Part | Value |
|---|---|
| `ProjectID` (query, **required**) | The numeric project **id** (`QW_Login` → `Projects.Project[].Id`) — not the name. |
| Form files | The first file's form key is **`File`**, then **`File2`**, **`File3`**, … — several images in ONE call. |

**Spec sources:** Swagger `…/api/swagger/docs/v1` (`POST /v2/Json/Qw_Add_MiscAttachment`: "uploads the
images/files to the Orcanos system and returns the Orcanos application URL for the file") · the
Zapier step Orcanos ran in production for Jira → Orcanos images (Rami Azulay, 2026-10-18).

> ⚠️ **Not yet verified live by us.** The shape below is the Swagger contract plus the working
> Zapier script; the first live sync from the traceability-matrix Integrations module is the check.
> Update this note with what it shows (especially: is the returned URL readable with Basic auth, or
> only with a signed-in browser session?).

## Response

```json
{ "IsSuccess": true,
  "Data": { "screenshot.png": "https://…/orca60FTP/…/screenshot.png",
            "diagram.png":    "https://…" } }
```

- `Data` is a **map from the uploaded filename to its URL**. The Zapier step also fell back to
  **position** (the n-th file → the n-th value) in case Orcanos renames a file — do the same.
- Two files with the **same name** in one call collide in that map: make the names unique first.
- Then replace each `<img src>` in the HTML with its URL and write the field with
  `QW_Update_Object` / `QW_Update_Defect` (or pass it in `QW_Add_Object` / `QW_Add_Defect`).

## Python (httpx)

```python
files = [("File" if i == 0 else f"File{i + 1}", (name, blob, mime)) for i, (name, blob, mime) in enumerate(images)]
r = await client.post(f"{base}/api/v2/Json/Qw_Add_MiscAttachment", params={"ProjectID": project_id},
                      headers={"Authorization": auth}, files=files)
urls = r.json().get("Data") or {}          # {filename: url}
```

## Traps

- **Nothing is attached to an item.** The files only become visible where an `<img src>` points at
  them; an upload that is never written into a field is an orphan in the store.
- Build the multipart body with your HTTP client (`files=`); never set `Content-Type` by hand.
- Used by: traceability-matrix `orcanos_client.add_misc_attachments` (Integrations, v4.29.0).

## See also
- [Add_Attachment](add-attachment.md) — a file on an item's Attachments tab
- [section-attachments.md](get-section-data/section-attachments.md) — reading an item's Attachments tab
