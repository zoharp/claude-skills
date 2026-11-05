# Section: `History` — an item's change log

`QW_Get_Section_Data` with `Section_Name=History` returns the **audit trail of a work item**: one
row per change event, each carrying the per-field before/after values. It is what the *History* tab
shows, and it is the evidence a Part 11 / ISO 13485 auditor asks for — who changed what, when.

Unlike [Revisions](section-revisions.md), History is **not DMS-specific** — it is available for any
item type. It is also where **tags (snapshots)** surface: signing an item freezes a copy of it, and
the `Comment` is the only handle the API gives you on that copy — see
[Tags](#tags--the-snapshots-hiding-in-the-comment) and
[Opening a tag's snapshot](#opening-a-tags-snapshot-the-frozen-html-copy).

> **Verified against `orca60` 2026-09-01/02** — DMS `18070` (36 rows) and item `25871`. Every trap
> below was observed on live data.

---

## Call

```
GET <base>/api/v2/Json/QW_Get_Section_Data
      ?Item_ID=18070&Item_Type=DMS&Section_Name=History&Ver_Id=363[&RecordCount=50]
```

⚠️ **`Item_Type` and `Ver_Id` are required by the API but ignored by this section.** Verified: the
same `Item_ID` returns byte-identical rows for `Item_Type=DHF`, `T_CASE` and even the nonsense value
`ZZZ_NOT_A_TYPE`, and `Ver_Id=1` returns the same 36 rows as the correct `363`. **History is keyed on
`Item_ID` alone.** Send the real values anyway — but never expect a wrong one to warn you.

⚠️ **`Section_Name` is case-sensitive.** `History` works; `history` returns
`IsSuccess: false, Message: "Cannot find table 0."` — the one *loud* failure in this endpoint.

**`RecordCount` omitted returns everything** (all 36 rows here); a value caps the list from the
newest end (`5` → the 5 most recent). A value larger than the log is harmless.

⚠️ **Build the Basic header on the canonical `User_name`, not what the user typed** *(observed on
the Covaris tenant, 2026-09 — inferred, not yet confirmed against that account's login response)*.
A user signed in with an **e-mail address** passed `QW_Login` and `QW_Get_Filter_Results` with that
header, yet this endpoint answered in a 200 envelope:
`IsSuccess: false, "Orcanos User Authentication issue : User or password is not valid."`
Take `Data.User_details.User_name` from the `QW_Login` response and rebuild the header on it. Don't
treat that message as a 401 / sign-out — the same credential still works on other endpoints.
Reference implementation: `login()` and `_getJson()` in covaris-bom's `src/api/orcanosClient.js`.

---

## Row shape — two levels

History is the **only section so far with nested rows**. Each entry under
`Data.section.history[]` has **both** keys:

```json
{
  "field":   [ { "title": "Change #", "show": "Y", "column": "Revision", "Value": "95" }, … ],
  "details": [ { "field": [ {…FieldName…}, {…OriginalValue…}, {…NewValue…} ] }, … ]
}
```

- `field[]` — **the event**: when, who, which change number, the comment.
- `details[]` — **the diffs**: one entry per field touched, each itself a `field[]` of three.

The generic `flattenRow()` in [qw-get-section-data.md](qw-get-section-data.md) only reads `field`,
so History needs the two-level version below.

*(Observed: both `history` and `details` serialize as real JSON arrays even with a single element —
this section did not exhibit the XML→JSON single-object quirk. `ensureArray()` remains cheap
insurance.)*

---

## Event fields (`field[]`)

| `column` | `title` | `show` | Meaning |
|---|---|---|---|
| `Obj_id` | ID | N | The item id the log belongs to — the **internal item id**, not the displayed original id (`DMS-18070`). |
| `obj_Version` | Version | Y | The item's version string **at that moment** (`01.00.000.0000`). It changes down the log — don't assume one value per item. |
| `Revision` | Change # | Y | ⚠️ **The change-log sequence number, NOT the document revision letter.** Revision `B` lives in the [Revisions](section-revisions.md) section; this is `95`, `41`, `40`… **Gaps are normal** (15–19 were absent on item 18070) — never use it as a count or a dense index. |
| `TimeDone` | Time Of Change | Y | Observed as `YYYY-MM-DD HH:MM:SS`, **no timezone**. ⚠️ **Don't assume that format** — the sibling [Revisions](section-revisions.md#-the-date-format-is-not-stable--never-sort-these-as-text) section returned **day-first** dates (`02/09/2026`) from the same tenant and credentials minutes later, so parse defensively rather than sorting as text. |
| `UserChangedBy_name` | Changed By | Y | The **username** that made the change (`orca`), not a display name or an id. Automation writes rows under the triggering user. |
| `descriptionInd` | Change In Description | Y | `"Yes"` / `"No"` — whether the item's rich-text **Description** changed in this event. See the diff note below. |
| `Comment` | Comment | Y | Human-readable summary. Sometimes user-entered, often system-generated (`Add relation: Source DOC-8543 , Target DMS-18070 from automation trigger`, `orca has downloaded …`). **Can be empty.** ⚠️ It is also the **only** place **tags (snapshots)** are exposed — see [Tags](#tags--the-snapshots-hiding-in-the-comment) below. |

## Diff fields (`details[].field[]`)

| `column` | `title` | Meaning |
|---|---|---|
| `FieldName` | Field Changed | The field's **display label** (`Routing State`, `Status`, `Category`, `Training List`, `File name`) — not an internal column name, and it varies by item type. |
| `OriginalValue` | Old Value | Value before. |
| `NewValue` | New Value | Value after. |

---

## The four traps in the diffs

**1. `'Change Made' → 'Change Made'` is a sentinel, not a value.** Event-shaped rows — `Relations`,
`Revision Downloaded`, `Description` — record only *that* something happened. Both sides read
`Change Made`. Rendering them literally produces an audit table full of meaningless
"changed from Change Made to Change Made" lines. Detect and render the `Comment` instead.

**2. Old == New happens on real fields too.** Orcanos logs every field **touched** by a save, not
only the ones that differ — `[Status] 'Approved' → 'Approved'`, `[Name] 'x.docx' → 'x.docx'` are all
observed. For "what actually changed", filter `OriginalValue !== NewValue` **after** excluding the
sentinel.

**3. `descriptionInd: "Yes"` tells you the description changed — it does not give you the change.**
The payload carries no before/after text (the matching detail is the `Change Made` sentinel). To
show a real description diff you need the two texts, and the API only exposes the **current** one
(`QW_Get_Object`) — so a true diff requires you to have snapshotted earlier versions yourself.
Treat `descriptionInd` as a flag to surface ("the text was edited here"), not as a diff source.

**4. Unset values arrive as at least three different things** — `""`, `"Not Set"`, and
`"-- Not Set  --"` (with a **double space**). Normalize before comparing, or a
"was blank, now set" row reads as a change from one word to another. Multi-value fields come back
**pipe-delimited** — `|DEV||EXECUTIVE||PRODMGR|` — so split on `|` and drop empties rather than
showing the raw string.

---

## Reading it (JavaScript)

```js
const ensureArray = v => Array.isArray(v) ? v : v == null ? [] : [v];
const flat = fs => Object.fromEntries(ensureArray(fs).map(f => [f.column, f.Value]));

const SENTINEL = 'Change Made';
const UNSET = new Set(['', 'Not Set', '-- Not Set  --']);
const norm = v => UNSET.has(String(v ?? '').trim().replace(/\s+/g, ' ')) ? '' : String(v ?? '');

function historyEvents(resp) {
  const d = typeof resp?.Data === 'string' ? JSON.parse(resp.Data) : resp?.Data;
  return ensureArray(d?.section?.history).map(row => {
    const e = flat(row.field);
    const diffs = ensureArray(row.details).map(x => flat(x.field));
    return {
      changeNo: Number(e.Revision),          // log sequence, NOT the revision letter
      when: e.TimeDone,                      // server-local, sorts correctly as text
      who: e.UserChangedBy_name,
      comment: e.Comment || '',
      descriptionChanged: e.descriptionInd === 'Yes',
      // an "event" row: it logged an action, not a field diff
      isEvent: diffs.every(x => x.OriginalValue === SENTINEL && x.NewValue === SENTINEL),
      // only the fields whose value genuinely moved
      changes: diffs
        .filter(x => x.OriginalValue !== SENTINEL || x.NewValue !== SENTINEL)
        .filter(x => norm(x.OriginalValue) !== norm(x.NewValue))
        .map(x => ({ field: x.FieldName, from: norm(x.OriginalValue), to: norm(x.NewValue) })),
    };
  });
}

// Who approved this document, and when?
const approvals = historyEvents(resp).filter(ev =>
  ev.changes.some(c => c.field === 'Routing State' && c.to === 'Approved'));
```

Rows arrive **newest first** (change # descending) — observed, not documented. Sort on `TimeDone`
explicitly if the order matters to you.

---

## Tags — the snapshots hiding in the `Comment`

When an item is **signed**, Orcanos takes a **tag**: a frozen snapshot of the item at that moment
(description, cover page, approvals). A user can also create one **manually**. Tags are the points
you can diff between — "what changed between revision B and revision C" is answered by comparing two
tags — and the **only** place the API surfaces them is the history `Comment`:

```
#95  Tag C.1 Approved Created ( DHF-25871 )      ← the signed snapshot
#94  Tag C.1 Created ( DHF-25871 )               ← one second earlier, pre-signature
#70  Item changed : Tag C.1 Approved Created ( DMS-24566 )   ← NOT this item's tag
```

**The grammar:** `[Item changed : ]Tag <Revision>.<Change> [Approved ]Created ( <KEY> )`.

⚠️ **Three traps, all of which inflate a tag list with things that aren't your tags:**

1. **`Item changed : …` rows belong to a *linked* item.** The key in parentheses is a **different
   document** (`DMS-24566`, not `DHF-25871`) — the parent logs that a child it links to was tagged.
   On item 25871, **only 4 of 21 tag-shaped rows were its own.** Always match the parenthesised key
   against the item you queried.
2. **A tag usually produces TWO rows** — `Created` and, a second later, `Approved Created`. They are
   one event. Deduplicate on `(revision, change)`, and prefer the **`Approved Created`** row: its
   snapshot carries the approval (verified — the plain `Created` row's snapshot renders with an
   **empty Approved Date**).
3. **The `Approved` half is not guaranteed.** A tag on a document that went to *In Work* rather than
   *Approved* appears as `Created` alone (observed: `Tag B.1 Created ( DMS-25102 )`). Don't require
   the pair.

```js
// This item's own tags, newest first, one entry per tag event.
function tags(events, ownKey /* e.g. 'DHF-25871' */) {
  const re = /^(Item changed\s*:\s*)?Tag\s+(\S+?)\.(\d+)\s+(Approved\s+)?Created\s*\(\s*([^)]+?)\s*\)$/;
  const out = new Map();
  for (const ev of events) {                       // events from historyEvents()
    const m = re.exec((ev.comment || '').trim());
    if (!m || m[1]) continue;                      // m[1] = "Item changed :" -> a LINKED item's tag
    if (m[5] !== ownKey) continue;                 // belt and braces
    const key = `${m[2]}.${m[3]}`;                 // e.g. "C.1"
    const approved = Boolean(m[4]);
    const prev = out.get(key);
    // keep the Approved row when both exist — it is the signed snapshot
    if (!prev || (approved && !prev.approved)) {
      out.set(key, { tag: key, revision: m[2], change: Number(m[3]), approved,
                     changeNo: ev.changeNo, when: ev.when, who: ev.who });
    }
  }
  return [...out.values()].sort((a, b) => b.changeNo - a.changeNo);
}
```

Each entry's **`changeNo` is what opens the snapshot** ↓.

---

## Opening a tag's snapshot (the frozen HTML copy)

Every tag keeps a rendered copy of the item — **cover page, approvals, change history and the
description as it stood** — reachable at:

```
https://app.orcanos.com/orca60/web/363/items/generatehtmlpage?ItemId=25871&IsLatest=1&ChangeNumber=95
                            └ tenant base ┘ └Ver_Id┘                      └ item ┘            └ history Change # ┘
```

`ChangeNumber` is the history row's **`Revision` (Change #)** — the `changeNo` from `tags()` above.
Returns `text/html`, not JSON.

**Verified on `orca60` (2026-09-02), item 25871:**

| Request | What came back |
|---|---|
| `ChangeNumber=95` (`Approved Created`) | Rev **C-1**, Approved Date `2026-09-02`, 11 history rows |
| `ChangeNumber=94` (plain `Created`) | Rev **C-1**, **Approved Date empty** — the pre-signature copy |
| `ChangeNumber=25` (tag B.1, 2024) | Rev **B-1**, Approved `2024-07-28`, 5 history rows |
| `ChangeNumber=13` (tag A.1, 2024) | Rev **A-1**, 2 history rows |
| `ChangeNumber` omitted | The **current** item |
| Works on any Document-Control type | ✅ also verified on `DMS 18070` |

⚠️ **`IsLatest` is counter-intuitively named.** With `IsLatest=1&ChangeNumber=25` the **cover page
matched the tag** (Rev B-1, approved 2024-07-28). With `IsLatest=0` the same change number rendered
the tag's history but the **current** cover (Rev C-1, 2026). **Use `IsLatest=1` for a faithful
snapshot.**

⚠️ **Nothing here fails loudly** — every bad request still returns **200 text/html**:

| Bad input | Result |
|---|---|
| Not logged in | 302 → the login page |
| `ChangeNumber=99999` | 200, a ~4.7 KB near-empty page |
| Wrong version segment (`/web/1/`) | 200, a ~343 KB page that is not the document |
| A change number that **isn't a tag** (e.g. 93) | 200, a plausible-looking page — no error, no warning |

**Guard on the content, not the status code:** a real snapshot contains `Doc No :`. And only feed it
change numbers you got from `tags()` — a non-tag number renders something believable and wrong.

### Fetching one server-side

Same authentication as the file download — **web-form login, session cookie; `Authorization: Basic`
is ignored**. Reuse `orcanos_web_session()` from
**[download-attachment.md](download-attachment.md)** rather than reimplementing it:

```python
from download_attachment import orcanos_web_session   # the helper in download-attachment.md

def tag_snapshot_html(session, base, *, version_id, item_id, change_no):
    r = session.get(f"{base}/web/{version_id}/items/generatehtmlpage",
                    params={"ItemId": item_id, "IsLatest": 1, "ChangeNumber": change_no},
                    timeout=120)
    r.raise_for_status()
    if "Doc No :" not in r.text:      # ⚠️ bad CN / dead session / wrong version all return 200
        raise RuntimeError("not a snapshot page — check ChangeNumber, version and session")
    return r.text
```

### Reading the page

| Part | Where |
|---|---|
| Cover page | First `table.gridtable` — `Doc No`, `Revision` (`C-1`), `Approved Date`, `Record Name`, `Routing State` |
| Approvals | Table under `<b class="cls">Approvals :</b>` — Job Title, Approved by, Quality Role, **Date & Time (GMT)**, Signature status, Comment |
| Change history | Table under `Change Revision History :` — Rev, Chg #, date, `Draft -> Draft` status transition, change description |
| **The document body** | `<div class="ObjDescription">` — everything after it is the item's description as of the tag |

Two quirks in the HTML itself, both observed:

- **Embedded relation-table links are malformed** — `href='httpsapp.orcanos.com/orca60/web/363/…'`,
  missing `://`. They are broken in Orcanos' own output; repair them if you re-render the page.
- **Empty cells contain `Â&nbsp;`** — UTF-8 read as cp1252. Decode the page as **UTF-8** and treat
  `Â ` / `&nbsp;` cells as empty.

Approval times are labelled **GMT** here, while History's `TimeDone` carries no timezone at all —
don't put the two on one timeline without deciding what `TimeDone` actually is on your instance.

---

## ⚠️ Reading a document writes to its history

Downloading or viewing a revision through
[ViewAttachment](view-attachment-url.md) **appends a history row**:

```
Comment: "orca has downloaded DMS_18070_Software Requirements Specifications (2)_B1_APP.pdf  Rev  B.1"
details: [ { FieldName: "Revision Downloaded", OriginalValue: "Change Made", NewValue: "Change Made" } ]
```

That is by design — controlled-document access is auditable. But it means **fetching a file is not
a read-only operation**: a batch export or a polling job will bloat the item's change log and put
its own service account's name all over an audit trail. Fetch deliberately, cache what you fetch,
and never poll `ViewAttachment`.

---

## See also
- [qw-get-section-data.md](qw-get-section-data.md) — the endpoint, params and shared envelope
- [section-revisions.md](section-revisions.md) — the sibling section; its `Revision` is the document's letter, this one's is a counter
- [download-attachment.md](download-attachment.md) — the `orcanos_web_session()` helper the snapshot fetch reuses; same auth, same 200-is-not-success trap
- [view-attachment-url.md](view-attachment-url.md) — opening a revision's PDF; that access shows up in this log
- [qw-get-object.md](../qw-get-object.md) — the item's **current** field values (the only side of a description diff the API gives you)
