# "My tasks" + e-signing a DMS / training task

How to tell which Orcanos rows belong to the signed-in user, and how to send them to sign. Learned from the
product owner (2026-11-12) while designing the traceability tool's Home page. **Not yet verified live** —
see the checklist at the end.

## Whose row is it?
- **A work item (Defect, CAPA, training task, …) belongs to the user named in its `Assigned to` field.**
  Compare that field with the signed-in user from `QW_Login` (user id or full name, depending on what
  the filter returns — normalise both).
- **A DMS item waiting for a signature belongs to the user named in its *next signee* field** — **verified live
  (orca60, DMS filter 581, 2026-11-13):** field `Name = Next_signee`, `Title = Next Assignee Details`, text like
  `Alex.Johnson (User) [Alternate:orca]` (the alternate may sign too; `(Group)` names a group). Empty when nobody is
  due. Some tenants also have a custom *Next Assignee List* (orca60 `CS355`, empty on every row). Parser:
  traceability-matrix `doc_control_engine.signers()` / `my_turn()`.
- **Both columns exist only if the filter SELECTS them.** A filter that does not include the column returns an
  empty value without an error ([filter-result-fields.md](filter-result-fields.md)). Any screen that relies on them must check the filter's
  columns when it is set up. If one is missing, it should name the missing column and offer
  `filterListingUrl(...)` ("Open the filter in Orcanos", see SKILL.md → *Build web URLs*) so an admin can add it.
  It should never treat a missing column as "nothing assigned".

## Two kinds of training task (product owner, 2026-11-12)
- **Read & understand** — the task points at a **DMS document revision** (`doc_key` = `DMS-…`, a revision letter).
  There is a file to read; a reader should gate Sign on reading it to the end.
- **Formal training** — the task points at a **training record `TRN`** (`doc_key` = `TRN-…`). It has **no document
  revision and no DMS item** — no file, no revision axis. Nothing to scroll: show the Training Material (if any) and
  let the person sign at once. The `TRN` id is `training_engine.record_id(doc_key)` (digits of `TRN-21803`).
- Telling them apart: the training report row's `src` (`"formal"` vs a document). Never look for a DMS revision /
  PDF for a formal task — there is none, and asking Orcanos for one is an empty answer, not an error.
- **Training Material** HTML may hold YouTube / Vimeo / slide-deck links. The traceability tool shows each link
  as-is plus a frame after it (`TaskReader.embedFor`): YouTube no-cookie, Vimeo player, Google Slides `/embed`,
  Drive `/preview`, SharePoint / OneDrive `action=embedview`, Canva `?embed`, Office files through
  `view.officeapps.live.com/op/embed.aspx?src=` (public URLs only), PDFs directly. A file attached in Orcanos is
  behind the Orcanos login and cannot be framed this way.

## Signing — the Orcanos e-sign page
```
{tenantBase}/web/async/signdocument?ItemId={itemId}&VersionId={verId}
e.g. https://app.orcanos.com/orca60/web/async/signdocument?ItemId=25869&VersionId=363
```
- **No Orcanos login is needed.** The page asks for user name + password itself (the e-signature).
- After **Approve**, the page goes to `{tenantBase}/web/Account/SignSuccess` (a "signed" confirmation).
- `VersionId` is the numeric `Ver_id` (as in every `/web/` link), not the version label.
- From another web app, open it in a **pop-up window**. The pop-up is on another origin, so its URL
  (SignSuccess) cannot be read. Watch for `popup.closed`, then **re-read the task from Orcanos** to learn whether it
  was signed. Never assume success because the window closed.
- After Approve the pop-up shows SignSuccess **or redirects to the Orcanos item** — not a page to leave the user on.
  Poll the task's status every few seconds while the pop-up is open and, once Orcanos says signed, call
  `popup.close()` from the opener (allowed cross-origin for a window you opened), then show your own message.

## Not yet verified live
- Whether `signdocument` opens in a pop-up with no Orcanos session cookie (expected: yes).
- Whether the same page signs a training task (`TRN_TSK`) or only a DMS item; which `ItemId` to pass for a task.
- Where the "Training Material" HTML field lives (TRN or TRN_TSK) and its field name. The tool reads the task first,
  then the TRN record (formal training) — `GET /api/home/material?task_id=&record_id=`.
- Which `ItemId` the e-sign page wants for a **formal** training task (we send the TRN_TSK id, same as read & understand).
