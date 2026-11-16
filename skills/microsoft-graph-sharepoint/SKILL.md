---
name: microsoft-graph-sharepoint
description: Microsoft Graph (v1.0) for SharePoint files, app-only — token, resolve a site's document library, upload (simple + upload session), org-wide edit link, download, delete — as used by the Orcanos "Edit in Office 365" feature. Use when writing or debugging code that puts a Word file in a customer's SharePoint for co-editing in Word for the web.
---

# Microsoft Graph — SharePoint files, app-only

Used by traceability-matrix `src/backend/o365_graph.py` (Edit in Office 365, design
`design/DESIGN_DOC_EDIT_O365.md`). **Everything here is from Microsoft's docs — NOT verified live yet**
(2026-11-13: built and tested on fakes only; no test M365 tenant). Record live results below when they exist.

## Setup the customer's IT admin does

App registration in Microsoft Entra ID → **API permissions → Microsoft Graph → Application permissions**:
- `Sites.ReadWrite.All` (simplest), or
- `Sites.Selected` + a site-level grant (`POST /sites/{site-id}/permissions` with role `write`, done by an admin
  with `Sites.FullControl.All`) — least privilege, one site only.

Then **Grant admin consent** and create a **client secret**. We store tenant id, client id, secret (encrypted).
Delegated sign-in is not used — the app acts on its own; users open the file with their own work account.

## Calls

| Purpose | Call | Notes |
|---|---|---|
| Token | `POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token` form: `client_id`, `client_secret`, `grant_type=client_credentials`, `scope=https://graph.microsoft.com/.default` | `expires_in` ≈ 3599 s; cache. Errors: `AADSTS7000215` bad secret, `AADSTS700016` unknown app, `AADSTS90002` unknown tenant. |
| Site | `GET /sites/{host}:/{server-relative-path}` e.g. `/sites/acme.sharepoint.com:/sites/Quality`; root site = `/sites/acme.sharepoint.com` | returns `id` = `host,siteGuid,webGuid` |
| Library | `GET /sites/{site-id}/drive` | the site's default document library ("Documents") |
| Upload ≤ 4 MB | `PUT /drives/{drive}/root:/{folder}/{name}:/content?@microsoft.graph.conflictBehavior=rename` body = bytes | creates missing folders in the path; returns the driveItem (`id`, `webUrl`) |
| Upload > 4 MB | `POST /drives/{drive}/root:/{path}:/createUploadSession` `{"item":{"@microsoft.graph.conflictBehavior":"rename"}}` → `uploadUrl`; `PUT` chunks with `Content-Range: bytes a-b/total` | chunk size a **multiple of 320 KiB**; the uploadUrl is pre-authorised — **no** Authorization header on it |
| Edit link | `POST /drives/{drive}/items/{id}/createLink` `{"type":"edit","scope":"organization"}` → `link.webUrl` | tenants may forbid org-wide links (403/400) → fall back to the item's `webUrl` (site members can open it) |
| Item | `GET /drives/{drive}/items/{id}?$select=id,name,webUrl,size,lastModifiedDateTime,lastModifiedBy` | |
| Download | `GET /drives/{drive}/items/{id}/content` | 302 to a pre-signed URL — follow redirects |
| Delete | `DELETE /drives/{drive}/items/{id}` | 204; goes to the site recycle bin; 404 = already gone |

Throttling: 429 / 503 with `Retry-After` (seconds) — retry after it.

## Traps (from the docs — confirm live)

- File names: `" * : < > ? / \ | # %` are refused; no trailing dot/space.
- Word for the web co-authoring saves to the same driveItem; the bytes read via `/content` are the latest
  **saved** state (autosave every few seconds) — an edit typed a second before Upload may be missing.
- Track Changes can't be switched on through Graph — set `<w:trackRevisions/>` in `word/settings.xml` of the
  .docx before uploading (`o365_docx.enable_track_changes`), and use lxml, not ElementTree (prefixes).
- There is no Graph API for "who is in the document now"; the app records who clicked Edit.

## See also
- `orcanos-api/add-attachment.md` — the redline + clean file are attached to the DMS item (`OBJECT`).
- `azure-devops-api` — the other Microsoft API in this codebase (PAT, not Graph).
