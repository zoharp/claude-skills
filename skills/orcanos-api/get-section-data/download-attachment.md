# Downloading a DMS revision's PDF (server-side)

How to actually **fetch the bytes** of a controlled document's revision from a backend — as opposed
to [handing a user a link](view-attachment-url.md) to click.

> **Verified end-to-end against `orca60` on 2026-09-01** — DMS `18070`, `Ver_Id 363`,
> `AttachmentId 2917` → `200 application/pdf`, 448,915 bytes, `%PDF-1.4`, 18 pages, valid trailer.
> Every claim below was observed, not inferred.

---

## The one thing that decides everything: which auth works

`/web/Download/ViewAttachment` is a **UI route**. It authenticates with the **ASP.NET forms-auth
session cookie** — the one a browser gets by logging in — and with nothing else.

| Attempt | Result |
|---|---|
| No auth | **302** → `/orca60/web/account/login?q=…` |
| `Authorization: Basic <base64(user:pass)>` — the API credential | **302** → the same login page. **The header is ignored.** |
| Direct `pdf_path` / `Attach_path` from the Revisions row (`…/orca60FTP/PROJECT_10045/OBJECT_…`) | **302** → `/orca60Ftp/Error`. Blocked with or without Basic auth. |
| **Web form login → session cookie → `ViewAttachment`** | **200 `application/pdf`** ✅ |

So a backend that wants the file must **log in the way the browser does** and reuse that session.
The API credentials are the same ones — it is the *mechanism* that differs, not the account.

⚠️ **The failure mode is a 200, not a 401.** With redirects followed (every HTTP client's default),
an expired or missing session returns the **login page's HTML with status 200**. `raise_for_status()`
will not catch it. **Always check the magic bytes** — see the guard below.

---

## Recipe (Python — `requests`)

```python
import re, requests
from urllib.parse import unquote

def orcanos_web_session(base, username, password):
    """base = tenant base URL, e.g. https://app.orcanos.com/orca60"""
    s = requests.Session()
    # 1. GET the login page — this sets the anti-forgery cookie the token is bound to.
    html = s.get(f"{base}/web/account/login", timeout=60).text
    m = re.search(r'name="__RequestVerificationToken"[^>]*value="([^"]+)"', html)
    if not m:
        raise RuntimeError("login page has no __RequestVerificationToken")
    # 2. POST the form. Field names are exact; all five are sent by the real form.
    r = s.post(
        f"{base}/web/Account/Login/form-login",
        data={
            "Username": username,
            "Password": password,
            "__RequestVerificationToken": m.group(1),
            "IsShowSavePassword": "True",
            "failed_count": "0",
        },
        timeout=60,
    )
    r.raise_for_status()
    # Success lands on the Home page; a rejected login re-renders the login form.
    if "__RequestVerificationToken" in r.text and "/Account/Login/form-login" in r.text:
        raise RuntimeError("Orcanos web login failed (credentials or lockout)")
    return s


def download_revision(session, base, *, item_id, version_id, attachment_id, item_type="DMS"):
    """Returns (filename, pdf_bytes) for ONE revision of a DMS item."""
    r = session.get(
        f"{base}/web/Download/ViewAttachment",
        params={                      # requests encodes these correctly, spaces and parens included
            "ItemId": item_id,
            "ItemType": item_type,
            "VersionId": version_id,
            "AttachmentId": attachment_id,
        },
        timeout=120,
    )
    r.raise_for_status()
    cd = r.headers.get("Content-Disposition", "")
    m = re.search(r'filename="?([^"]+?)"?$', cd)
    # ⚠️ The guard that matters: a dead session returns 200 + the login HTML, and the
    #    Content-Type header says "application/pdf" no matter what the body really is.
    #    A PDF starts %PDF; a Draft revision hands back the source Office file (PK zip).
    if not (r.content.startswith(b"%PDF") or r.content.startswith(b"PK\x03\x04")):
        raise RuntimeError(
            f"neither PDF nor Office file (CD={cd!r}) — session expired, or this attachment "
            f"has no downloadable copy")
    name = unquote(m.group(1)) if m else f"DMS_{item_id}_{attachment_id}.bin"
    return name, r.content        # trust the EXTENSION in `name`, not the Content-Type
```

Usage — the ids all come from one [Revisions](section-revisions.md) row:

```python
s = orcanos_web_session(BASE, ORCANOS_USER, ORCANOS_PASS)      # log in ONCE, reuse the session
name, pdf = download_revision(s, BASE, item_id=row["Obj_id"], version_id=363,
                              attachment_id=row["ID"])          # row["ID"] = the ATTACHMENT id
open(name, "wb").write(pdf)
# -> DMS_18070_Software Requirements Specifications (2)_B1_APP.pdf   (448,915 bytes)
```

---

## What comes back

- ⚠️ **What you get depends on the revision's routing state — and the `Content-Type` lies.** The
  header is **always `application/pdf`**, even when the body is not a PDF:

  | Revision state | Body | `Content-Disposition` filename |
  |---|---|---|
  | Approved | stamped PDF (`%PDF`) | `…_C1_APP.pdf` |
  | Obsolete | stamped PDF (`%PDF`) | `…_B1_OBS.pdf` |
  | **Draft** | **the original Office file** (`PK\x03\x04`) | `…_D1_DRAFT.docx` |

  A draft has no controlled rendition yet, so Orcanos hands back the uploaded source — **mislabelled
  `application/pdf`**.

  ✅ **A draft's PDF IS available — add `&PreviewPDF=1`.** That is the flag the Orcanos item page's
  own *PDF preview* button sends (`PDFPreviewWithExistingFile(ItemId, ItemType, Version, AttachmentId)`
  in `/web/{ver}/items/view`). **Verified 2026-10-07** on orca60: DMS 18070 / ver 363 / attachment
  3355 (D.1 **Draft**, `PDFPreviewFileExist: "Y"`, `pdf_path` **empty**) → `200`, `%PDF-1.4`,
  454,307 bytes, `inline; filename="…_D_1.pdf"`. Orcanos builds the rendition asynchronously after an
  upload ("Generating PDF" on the item page), so a just-uploaded draft may still answer with its
  `PK` source — with the flag set, treat anything but `%PDF` as "not ready yet". Used by the
  traceability-matrix Doc Review compare (`orcanos_files.download_attachment(preview_pdf=True)`). Never trust the Content-Type; **read the extension off
  `Content-Disposition`** and confirm with the magic bytes.
- **The server names the file**, in `Content-Disposition`, and the suffix encodes the revision's
  standing:

  | Served filename | Revision | Routing state |
  |---|---|---|
  | `DMS_18070_…_B1_APP.pdf` | B.1 | **APP** = Approved |
  | `DMS_18070_…_A1_OBS.pdf` | A.1 | **OBS** = Obsolete |

  Take the filename from the header — don't reconstruct it. (Note `B1`, not the `B_1` that
  `pdf_path_name` uses.)
- ⚠️ **The same `AttachmentId` does not return stable bytes.** The rendition is stamped **at
  download time** with the revision's *current* standing. Verified: attachment `2917` returned
  `…_B1_APP.pdf` (448,915 bytes) and, after a later revision superseded it, `…_B1_OBS.pdf`
  (464,483 bytes) — same revision, same id, different file. So **never** treat a stored hash of a
  download as evidence the document changed, and re-fetch rather than assuming a cached copy still
  carries the right status stamp.
- **`PDFPreviewFileExist: "N"` does NOT mean there is no PDF here.** Item 18070's row says `N` and
  this route served a 448 KB PDF anyway. That flag describes a *stored* rendition; the viewer
  produces one on demand. **Do not gate a download on it.**

---

## Starting from a revision letter instead of an attachment id

The usual real-world input is **"DMS 18070, version 363, revision B"** — not an attachment id. One
[Revisions](section-revisions.md) call resolves it:

```python
def revision_rows(item_id, ver_id, user, pwd):
    r = requests.get(f"{BASE}/api/v2/Json/QW_Get_Section_Data", auth=(user, pwd), timeout=90,
        params={"Item_ID": item_id, "Item_Type": "DMS",
                "Section_Name": "Revisions", "Ver_Id": ver_id})     # ⚠️ Ver_Id IS required here
    rows = ((r.json().get("Data") or {}).get("section") or {}).get("revision") or []
    rows = rows if isinstance(rows, list) else [rows]
    return [{f["column"]: f["Value"] for f in row["field"]} for row in rows]

def get_dms_revision(session, item_id, ver_id, revision, change_no=None, *, user, pwd):
    """'DMS 18070, ver 363, revision B'  ->  (row, filename, bytes)"""
    rows = revision_rows(item_id, ver_id, user, pwd)
    if not rows:                        # empty is ambiguous — say so instead of returning nothing
        raise RuntimeError(f"no revisions for DMS {item_id} in version {ver_id} — check the Ver_Id")
    cands = [r for r in rows if r["Revision"].upper() == str(revision).upper()
             and (change_no is None or r["Change_no"] == str(change_no))]
    if not cands:
        have = ", ".join(f'{r["Revision"]}.{r["Change_no"]}' for r in rows)
        raise RuntimeError(f"revision {revision} not found on DMS {item_id}; available: {have}")
    row = max(cands, key=lambda r: int(r["Change_no"]))   # latest change within that letter
    name, blob = download_revision(session, BASE, item_id=item_id,
                                   version_id=ver_id, attachment_id=row["ID"])
    return row, name, blob
```

**Verified 2026-09-02** on DMS 18070 / ver 363, which holds `D.1 Draft`, `C.1 Approved`,
`B.1 Obsolete`, `A.1 Obsolete`:

- `revision="B"` → `DMS_18070_…_B1_OBS.pdf`, 464,483 bytes ✅
- `revision="D"` → `DMS_18070_…_D1_DRAFT.docx` (the draft's source file — the reason the guard above
  accepts `PK` as well as `%PDF`)
- `revision="Z"` → refused with `available: D.1, C.1, B.1, A.1`

Two things this function has to decide, because Orcanos won't:

- **A letter can carry several changes** (`B.1`, `B.2`, …). "Revision B" is ambiguous; this takes the
  **highest `Change_no`**. Pass `change_no` explicitly when the exact copy matters — an audit answer
  usually does.
- **`Ver_Id` is mandatory and cannot be derived.** Verified: `Ver_Id` 1 / 0 / 99999 each return
  **0 rows, `IsSuccess: true`** — the wrong version is indistinguishable from a document with no
  revisions, which is why the code raises rather than returning `[]`. And `QW_Get_Object` does
  **not** give it to you: its `Version` field is the label (`"1.0"`), not the numeric `Ver_Id`
  (`363`). Get it from `QW_Login`'s `Projects.Project[].Version[].Ver_id`, or from the filter result
  that produced the item. (Contrast [History](section-history.md), where `Ver_Id` is ignored.)

---

## Traps (all observed)

- **`AttachmentId` is the only selector that matters.** `2917` → B.1 (448,915 bytes); `2300` → A.1
  (340,311 bytes). It is the Revisions row's **`ID`** column — *not* `Obj_id`, which is confusingly
  titled `ID` as well.
- **Omitting `AttachmentId` silently serves the latest revision.** No error, no warning — the
  request for "the document" quietly becomes "whatever is current". If you meant a specific
  revision, always send it.
- **`name=` is ignored entirely.** The correct name, `pdf_path_name`, the `.docx` name, literal
  garbage (`zzz.pdf`), and omitting the parameter **all returned the identical file**. Keep it in
  user-facing links to match Orcanos' own URLs, but never rely on it to choose anything.
- **Log in once and cache the session.** This is a UI endpoint carrying a full page-login cost; do
  not re-authenticate per file. Refresh on the `%PDF` guard failing.
- **A failed login may count toward lockout** — the form posts a `failed_count`. Don't retry a
  rejected credential in a loop.
- **Never log the session cookie or the `q=` value on the login redirect** — both are bearer-grade.

---

## See also
- [section-revisions.md](section-revisions.md) — the row supplying `Obj_id`, `ID` and the revision's state
- [view-attachment-url.md](view-attachment-url.md) — the same route as a **link for a logged-in user** (no backend involved)
- [qw-get-section-data.md](qw-get-section-data.md) — the API call that lists the revisions
- [SKILL.md](../SKILL.md#authentication) — the API credentials (`QW_Login` / Basic), which this route does **not** accept
