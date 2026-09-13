# Orcanos Training Management — the process

**Part of:** `orcanos-processes` · **Objects:** `Orcanos-infra/orcanos-work-items.md` · **API:** `orcanos-api`

---

## 0. Sources and precedence

| Ref | Document | Role |
|---|---|---|
| **[RU]** | `04.3.3 QMS Onboarding — Training Management — Read and understand.pdf` (12 slides) | **GOVERNS.** On any conflict, this document wins. |
| **[TC]** | `04.3.2 Training Management — Training Coordinator Cookbook Rev 2.pptx.pdf` (27 slides) | Broader coverage — manual launches, use cases, dashboards. Used wherever [RU] is silent. |

| **[PO]** | Product owner (Zohar), 2026-08-25 | **OVERRIDES BOTH.** Decisions in §0.1. |
| **[LIVE]** | Measured against orca60, 2026-08-25 (filters 865/866/867/868) | **Beats every deck on facts** — field names, codes, status values. §2.3. |

Citations below are `[RU p6]`, `[TC p14]`, etc. **Conflicts and their resolutions are listed in §11** —
read that section before trusting any single bullet.

---

## 0.1 Product-owner decisions — these govern

Confirmed 2026-08-25. Where these touch anything below, **they win over both decks.**

| # | Decision | Effect |
|---|---|---|
| 1 | **A Training Record is a collection of training tasks across MULTIPLE users.** | Settles §11 conflict #1 — [RU] was right, [TC p6] is loose wording. Now authoritative, not inferred. |
| 2 | **`Roles` and `Job Title` are the SAME field / the same vocabulary.** | There is **one** role vocabulary, so the DMS-item side and the user side match **exactly**. No fuzzy matching. This removes the largest unknown in the estimate. |
| 3 | **Everything is created in the Pool.** | Confirmed. Filters must be pool-scoped or they return nothing. |
| 4 | **Approved vs pending-approved trigger — out of scope for now.** | Don't chase the preliminary setup; assume the automation fires on approval. |
| 5 | ~~Previous revisions — out of scope for now.~~ **SUPERSEDED 2026-08-26 [PO]: previous revisions are IN.** | The headline numbers still judge the **current / last approved** revision — and a cell now counts *only* that revision's tasks, where before every task for a (person, document) pair was pooled and an old signature read as trained. Earlier releases are kept **per document**, newest first, with a **joined-after-release exclusion** (see §2.3 Traps 6 and 7). Shipped v3.10.0. |
| 6 | **The traceability-matrix design and code stay as they are for now.** | Record findings here; do **not** edit `design/DESIGN_TRAINING_MANAGEMENT.md` or the code until discussed. |

### The Missing-task rule *(authoritative definition)*

```
MISSING(user, dms_item)  ⟺
      USRP.Roles  ∩  DMS_ITEM.Roles  ≠  ∅        (the user holds a role the document names)
  AND ∄ TRN_TSK  where  TRN_TSK.[Assigned To] = USRP.[Assigned To]   ← user id, NOT the USRP work-item id
                  and   the task covers this dms_item
                        (evaluated on the CURRENT / last approved revision)
```

Everything the tool reports as ❓ Missing is this predicate and nothing else.
The identity join is the one in §2.1 Trap 1 — get it wrong and **every** user reads as untrained.

**"The task covers this dms_item" is scoped by REVISION** (2026-08-26). A task counts toward the
current requirement only when its revision is **not older** than `last_approved_revision` — a
signature on a superseded release is untrained in audit terms. "Not older" rather than "equal" is
deliberate: a wave raised on a revision still in routing is legitimate (§2.3 Trap 6).

On a **previous** revision the predicate gains a date gate, because the audience is historical:

```
MISSING(user, dms_item, previous_revision)  ⟺
      the role intersection holds  (as above)
  AND ∄ TRN_TSK on that revision
  AND USRP.[Created / Joining date]  ≤  the revision's date      ← they were here
```

A user whose profile **postdates** the revision is *not yet joined* — reported, never counted as
missing. Where either date is unreadable the answer is **unknown**: guessing one way invents a
finding, the other hides one. The current revision is deliberately **not** date-gated — whoever
holds the role today owes today's revision, however recently they arrived.

> **Parked, not dropped:** the DMS item also carries a **`Trainees`** field naming individuals
> directly [RU p5]. A named trainee with no task is missing by the same logic, but is **outside the
> v1 rule above**.

> [RU p11] names two further decks in the same family that we do **not** have:
> **Training Management Basics (Preliminary)** and **Formal Training**, plus a **User Profile** deck.
> Anything below marked *(gap)* is likely answered in one of those.

---

## 1. What the module is for

ISO 13485 **§6.2** requires documented **qualification, awareness and training**. The module exists to
prove employees are trained to perform their roles in the QMS, and to be audit-ready on demand.
[TC p2]

Orcanos does this by turning training into ordinary work items, so training inherits traceability,
e-signature, routing, filters and dashboards from the rest of the platform.

---

## 2. The work items

[TC p5] — codes confirmed against the rendered keys in the screenshots.

| Code | Type | Role in the process | Evidence |
|---|---|---|---|
| `DMS_ITEM` | **DMS Item** | The controlled document. Carries the **Training Details** section that drives everything. | `DMS-6119` [RU p5], `ORCA-29757` [TC p14] |
| `USRP` | **User Profile** | The employee e-record. Also the **training file** view. | `USRP-29762` [TC p17, p19] |
| `JD` | **Job Description** | Connects a person to the list of job descriptions. **This is likely the real role vocabulary — see §12.** | [TC p5, p15 nav] |
| `TRN` | **Training Record** | Created for each training process. The QA-signed compliance record. | `TRN-29755`, `TRN-5966` [TC p11], [RU p3] |
| `TRN_TSK` | **Training Task** | One per trainee. Signed by the trainee. | `TRN_TSK-29761`, `TRN_TSK-29778` [TC p15, p19] |
| `TRN_P` | **Training Plan** | Scheduled **annual** training framework; links to training records. | [TC p5, p6] |

> ⚠️ It is **`TRN_TSK`**, not `TRN_TASK`; and **`DMS_ITEM`**, not `DMS`. `DMS` and `ORCA` are the
> *custom display codes* two different tenants use for the same original type — the usual custom-vs-original
> code split (`Orcanos-infra` §3.2). **Do not derive the type code from a key prefix.**

**Hierarchy:** Training Plan → Training Records → Training Tasks → (a task may reference DMS items).

---

## 2.1 The join model ⭐

Product owner, 2026-08-25. **This is how the four item types actually connect.** Everything the
reporting layer does is built on these three edges.

```
   DMS_ITEM                              USRP  (User Profile)
   ├─ Roles / Job Titles ────────────►   ├─ Roles / Job Title      ◄──── same vocabulary
   └─ (revision)                         └─ Assigned To  = THE USER ID
                                                  ▲
   TRN  (Training Record)                         │  user id, NOT the work-item id
   ├─ Roles / Job Titles ─────────────────────────┤
   └─ id                                          │
        ▲                                         │
        │  Training Records List                  │
   TRN_TSK  (Training Task)                       │
   ├─ Training Records List ──► TRN.id            │
   └─ Assigned To ─────────────────────────────────┘
```

| # | Edge | Join |
|---|---|---|
| 1 | Document → people | `DMS_ITEM.Roles` = `USRP.Roles` |
| 2 | Training record → people | `TRN.Roles` = `USRP.Roles` |
| 3 | Task → its record | `TRN_TSK.[Training Records List]` = `TRN.id` |
| 4 | Task → person | `TRN_TSK.[Assigned To]` = `USRP.[Assigned To]` — **user id on both sides** |

### 🚨 Trap 1 — the user identity is `Assigned To`, **not** the work-item id

A User Profile has **two** identifiers and only one of them joins:

| | |
|---|---|
| `USRP` **work-item id** (e.g. `29762`) | identifies the *profile record*. **Never use this for training reports.** |
| `USRP.`**`Assigned To`** | the **system user id** — this is what a `TRN_TSK.Assigned To` holds, and the only thing that matches |

> Joining on the work-item id fails **silently**: every user resolves to zero tasks, and the report
> reads as *"nobody has been trained"* rather than as an error. Same shape as the code-vs-label traps
> in `Orcanos-infra` §3.1.

### 🚨 Trap 2 — the field names vary by customer

**`Roles` and `Job Titles` are the same concept** and either name may be in use; the exact label
drifts from tenant to tenant. The same is true of `Training Records List` on the task.

> These must be **configurable field mappings**, resolved per install — never hard-coded literals.
> Read them live per type with `QW_Get_Item_Add_Edit` (`orcanos-form-builder`).

---

## 2.2 Linking a task to its DMS item — the task **name** carries it

Product owner, 2026-08-25. A Read & Understand task is named to a fixed pattern, and that name
encodes the document key, the trainee and the **revision**:

```
Read and understand [Quincy.Angel , DMS-26533 : SOP Template (A.2) ]
                     └─ user id ─┘  └─ DMS key ┘ └─ doc name ─┘└rev┘
```

Matching [RU p8]: *"Task name contains the document ID + document name + Document revision."*

### Parse it by shape, never by the literal text

```python
KEY = r"[A-Za-z][A-Za-z0-9_]*-\d+"                  # DMS-26533; underscore prefixes too
inner    = name[name.rfind("[")+1 : name.rfind("]")]
dms_key  = re.search(KEY, inner)                    # DMS-26533
user_id  = inner.split(",")[0].strip()              # Quincy.Angel
revision = re.findall(r"\(([^()]*)\)", inner)[-1]   # A.2
```

| Rule | Why |
|---|---|
| **Anchor on the key pattern**, not on `"Read and understand"` | That prefix is **template text** — renameable and localisable per tenant. Matching it makes the link break on a customer who renamed their template |
| Take the **last** `[...]` pair and the **last** `(...)` group | A document name may itself contain `:`, `(` or `[` |
| **Never take the person from the name** — use `TRN_TSK.[Assigned To]` | ⚠️ **Measured, 2026-08-26**: they disagree on real data, and the **name is the wrong one**. See Trap 5 below |
| **Prefer the real field when populated** — `DMS Items List` / `Related DMS Item` | A field is structured data; a name is a rendering of it. Read both while prototyping and log the disagreement rate, so name-parsing can be dropped once the field proves reliable |

### 🚨 Trap 5 — the user id in the name is NOT the person the task belongs to

The bracket's first token looks exactly like a login and reads as authoritative. It is **template
text naming whoever the task was raised for**, and it can differ from the account the task is
actually assigned to.

Measured on orca60: `TRN_TSK-21810` / `21714` / `24906` / `21707` are named
`Read and understand [zohar , DMS-12677 : … ]` but carry **`Assigned_to: "orca"`** — and `orca` is
exactly Zohar Peretz's `USRP.Assigned_to`. Joining on the name matched **no profile**, so the report
said he had *no task* on every document he is in fact signed on. Nothing errors; the grid renders
cleanly and states the opposite of the truth.

> **`TRN_TSK.[Assigned To]` is the identity join. The name supplies only the DMS key + revision.**

**And a filter only returns the columns it SELECTS.** `Assigned_to` is a real, populated field on
`TRN_TSK`, but orca60's filter **867 does not return it** — which is how it was first (wrongly)
recorded as "empty on all 1031 tasks". Fetch it per item with `QW_Get_Item_Add_Edit` to check what
the field really holds before concluding a field is empty. If the column is missing from the filter,
**say so in the report and name the filter to fix** rather than falling back silently.

> ⚠️ **Only the R&U template names tasks this way.** A manually created or formal-training task
> (§8) has a free-text name and **will not parse** — for those, the DMS link must come from the field.

> 💡 **The revision comes free.** `A.2` is in the name, so per-revision matching costs nothing —
> the deferred revision-history work ([PO] §0.1 #5) is cheaper than it looked.

---

## 2.3 Verified against live orca60 — the actual field names

Pulled 2026-08-25 from filters 865 / 866 / 867 / 868. **These are measured, not inferred.**

### Response shape

`QW_Get_Filter_Results` returns `Data[].Object[].Field[]`, and each field is:

```json
{ "Name":"usrp_job_title", "Title":"Job Title", "Text":"Developer",
  "Type":"text", "Visible":"Y", "Order":"3", "Section":"" }
```

| Trap | |
|---|---|
| The **value is `Text`** | not `Value` — reading `Value` yields `None` for every field and looks like empty data |
| The **human label is `Title`** | so a tenant's custom field names are **auto-discoverable** (`CS210` → `"Roles"`). §2.1 Trap 2's field mapping does **not** have to be hand-configured — match on `Title` |
| **Item type is `DMS`** | not `DMS_ITEM`. `DMS_ITEM` returns *"No results found"* — a silent empty, not an error |

### The fields that matter

| Source | Field `Name` | `Title` | Use |
|---|---|---|---|
| **DMS** (865, ver 363) | `CS210` | **Roles** | the role edge |
| | `CS194` | Trainees | named individuals (parked) |
| | `last_approved_revision` | Last Approved Revision | the released revision — a bare **letter** (`C`), while a task name says `C.1` ⚠️ **Trap 6** |
| | `DMS_Revision` · `DMS_Routing_State` | Revision · Routing State | `DMS_Revision` is the *working* revision and can be **ahead** of the approved one — Trap 6 |
| | `DMS_Routing_End_Date` | **Approved Date** | when the **current** revision was approved. No equivalent exists for earlier ones — Trap 7 |
| | *(varies)* | **Training List** | the `TRN` attached to this document ⇒ **training is configured for it**. Renders as the literal words **`Not set`** when empty — see Trap 8 |
| | `User_Prefix` | — | the key, `DMS-26533` |
| **USRP** (866, ver 448) | `usrp_job_title` | **Job Title** | the role edge |
| | `Assigned_to` | **Assigned To** | **the user id** (`Quincy.Angel`) — §2.1 Trap 1 |
| **TRN_TSK** (867, ver 448) | **`Assigned_to`** | **Assigned To** | **the user id — THE identity join** (§2.1 Trap 1, §2.2 Trap 5). ⚠️ **not returned by filter 867** — the field is populated, the filter just doesn't select it; add the column |
| | `Obj_name` | Name | carries the DMS key + revision (§2.2). **Its user id is NOT the assignee** — Trap 5 |
| | **`DMS_Routing_State`** | Routing State | **← signed/not-signed lives HERE** |
| | `Obj_status` | Status | **NOT a progress field** — see below |
| | `DMS_Routing_Due_Date` | Routing Due Date | overdue |
| | `CS218` | Training List | the parent `TRN` |
| **TRN** (868, ver 448) | `CS210` / `CS194` | Roles / Trainees | the formal-training edge |

### 🚨 Trap 6 — the two sides spell a revision differently *(verified orca60 2026-08-26)*

A revision is the identity of a release, and training is owed **per release** — but the two sides
that have to be joined do not agree on how to write one:

| Side | Field | Value |
|---|---|---|
| **DMS** | `last_approved_revision` | `C` — a bare **letter** |
| **TRN_TSK** | inside `Obj_name` | `C.1` — **letter + minor**, e.g. `… : SOP Template  (A.2) ]` |

`"C" == "C.1"` is false, so a direct string comparison matches **nothing** and every document
reads as untrained on its own current revision — with no error anywhere. **Join on the letter.**
`C.1` and `C.2` are both revision **C**.

Measured on orca60: 729 of 1031 tasks carry a revision (the other 302 are formal-training tasks
whose names don't parse at all, §2.2). 33 of 85 documents have tasks spanning more than one
revision; the longest run is 10 (`DMS-12768`, B→K).

Two further traps behind that:

1. **Validate the revision's SHAPE** (`^[A-Za-z]{1,3}(\.\d{1,3})?$`). The parse takes the *last*
   parenthesised group in the task name, so a document called `Cleaning SOP (EMEA region)` donates
   a release called "EMEA region" if you don't.
2. **A task's revision can be NEWER than `last_approved_revision`.** Four orca60 documents have
   their whole training wave on a revision still in routing — `DMS_Revision` = C while
   `last_approved_revision` = B, because the wave is raised before approval completes. Treating
   "current" as an exact match reports every trainee on those documents as untrained. Current
   means **not older**.
3. **Not every tenant selects BOTH revision columns**, and the two field roles then resolve to
   the **same** column. Comparing it with itself makes every document look mid-routing — so
   whenever you surface "current vs approved", drop the comparison when both roles resolve to
   one field name. Compare by **letter** (`rev_major`), or `B.2` reads as ahead of `B`.
4. **Surfacing the working revision is safe; scoring on it is not.** `DMS_Revision` is useful to
   *show* (a row reading *Rev B* is otherwise mistaken for a document untouched since B), but the
   audience owes the **approved** revision — an unapproved release has been read by nobody yet.

### 🚨 Trap 7 — there is no revision history, and no profile date, in a filter result

Nothing in Orcanos' filter output says when a *previous* revision was released. A DMS row carries
only the **current** revision's approval date (`DMS_Routing_End_Date`, Title *Approved Date*). The
only evidence a superseded revision ever existed is **its tasks**, so date it by them: earliest
task `Created Date`, else earliest `DMS_Routing_Due_Date` as a flagged proxy (due = created + N ⇒
late, not wrong).

Likewise a **User Profile has no date column** in filter 866 — but `Created Date` **is** on the
item (`QW_Get_Object` → field `Name: "Created Date"`, e.g. `11/7/2021 2:39:37 PM`). Reading them
per item is affordable precisely because the User Profile filter is the ceiling on the whole
report; on orca60 all 6 resolve in one concurrent pass.

⚠️ **The date format differs by endpoint.** A **filter result** is day-first (`23/09/2021` —
first component observed up to 31, second never above 12). **`QW_Get_Object` is month-first** with
a 12-hour clock (`4/26/2021 12:50:08 PM`). One build consumes both, so detect the order per source
from the corpus rather than assuming; where every value fits both readings, say so. Guessing wrong
shifts a date by up to eleven months.

⚠️ **Carry a date TWICE if you both show it and compare it.** `DMS_Routing_End_Date` is the only
date available to range documents over (there is no other approval date, and none at all for a
superseded revision). Anything user-facing must print it **exactly as the tenant rendered it** —
reformatting it means picking an order, and picking wrong moves the date. Keep the parsed ISO
form as a separate value and compare only that. A value that will not parse is **reported**, not
excluded silently: it simply cannot be placed in any range.

### 🚨 Trap 8 — a document that owes training but cannot be scored is invisible

The role intersection needs a document to name **at least one role** and to have an **approved
revision**. A document failing either is not "compliant" — it is **unmeasurable**, and the two
read identically unless you separate them:

| Fails | Meaning |
|---|---|
| no `Roles` | **nobody can ever be trained on it.** Orcanos has no tasks to report on, so it complains about nothing — the most complete failure of the lot |
| no `Last Approved Revision` | nothing released for anyone to train on (yet) |

⚠️ **Gate that list on the document's `Training List` field**, or it is a copy of the DMS filter
rather than a set of findings: most of a controlled library is forms and leaflets nobody trains
on (orca60: 55 of 333 documents are in scope at all).

⚠️ **`Not set` is a VALUE.** Orcanos renders an unset link field as those literal words, so
`if (value)` reads every un-configured document as *training is configured* — exactly backwards.

⚠️ **The field id is not portable.** `CS218` is the Training List on **`TRN_TSK`**; a `CS…` id is
per-tenant *and* per-type, so resolve this one by **`Title`** only. Binding it by id on `DMS`
silently reads whatever custom field happens to occupy that id.

⚠️ **If the filter has no Training List column, list nothing and name the column.** Guessing
turns most of the library into findings, and *"0 documents are missing their roles"* is a
different claim from *"this cannot be determined"*.

*(Recorded 2026-08-27 from the traceability-matrix v3.19.0 build. The behaviour of the
DMS-side field — that it is titled *Training List* and reads `Not set` when empty — follows the
product owner's description and the `TRN_TSK.CS218` precedent; it has **not** been measured
against a live orca60 DMS filter that selects the column.)*

### 🚨 Trap 3 — "signed" is `DMS_Routing_State`, **not** `Obj_status`

Measured over 1031 live tasks:

| `DMS_Routing_State` | n | | `Obj_status` | n |
|---|---|---|---|---|
| In Work | 913 | | In Process | 914 |
| **Approved** | **59** | | Read And Understand | 60 |
| Draft | 58 | | Draft | 57 |
| Cancel | 1 | | | |

They look interchangeable and are not. **`Obj_status` "Read And Understand" is the task *category*, not a completion state** — one task is `Draft` + `Read And Understand`, i.e. never launched but would count as signed.

```
signed      ⟺  DMS_Routing_State == "Approved"
open        ⟺  DMS_Routing_State == "In Work"
not launched⟺  DMS_Routing_State == "Draft"      (template — exclude)
dead        ⟺  DMS_Routing_State == "Cancel"     (not a live obligation)
```

### 🚨 Trap 4 — a signed task can be invisible to the report

Live reconciliation of all **59** signed tasks against the computed matrix:

| n | Where it went |
|---|---|
| **32** | **the user has no `USRP` record** |
| 11 | counted in the matrix ✅ |
| 10 | task name doesn't parse — formal training (§2.2) |
| 3 | the document isn't returned by the DMS filter |
| 3 | the user's role isn't on that document (trained as a named *Trainee*, not by role) |

> **The User Profile filter is the ceiling on everything.** orca60's filter 866 returns **6** profiles
> while at least **10** people hold tasks (`zohar` 130, `Testing` 102, `Orcanos.Support` 62,
> `marketing` 17 — ⚠️ **these counts are name-derived**, and the name is not the assignee (Trap 5);
> the `zohar`-named tasks are assigned to `orca`). A person with no `USRP` record cannot appear —
> not as trained, not as missing.
> **Always reconcile signed-task totals against the matrix and report the difference**; a matrix that
> quietly drops half the evidence is worse than no matrix.

### Scale of the real data (orca60)

| | |
|---|---|
| DMS items | **340** — of which 121 have an approved revision, **66 have Roles set**, 61 both |
| User profiles | **6** (3 distinct job titles; 1 profile has none) |
| Training tasks | **1031** — 729 parse by name, 302 don't |
| Roles named on documents | **14** — only **3** have any user profile behind them |

> **Page everything.** 1031 tasks needed 6 requests at 200/page. The task filter has **no `FILTER_BY`
> to narrow it**, so it must be read whole — the same unbounded-fetch shape that caused this repo's
> v3.6.2 bug, where a silent 500-item cap made one customer's data look empty. **A truncating page cap
> must log, never truncate quietly.**

### Why *both* `DMS_ITEM` and `TRN` carry roles *(inference — confirm)*

Two role-bearing edges into `USRP` looks redundant until you notice each mode needs its own:

- **Read & Understand** has a document, so the audience comes from **`DMS_ITEM.Roles`**
- **Formal training** has no document (§8.1, §8.2), so the audience must come from **`TRN.Roles`**

That would make edge 1 the R&U path and edge 2 the formal path, both landing on the same
`USRP.Roles` vocabulary. Marked as inference — the decks don't say it outright.

---

## 3. Two modes

[TC p7]

| | **Automated** | **Manual** |
|---|---|---|
| What | **Read & Understand.** A new DMS revision is released; the users who must read it are given a task to acknowledge it | **Formal training** — sessions or courses that multiple users, selected by role or by name, must complete |
| Fires | By itself, on document approval | By a person clicking **Launch** |
| Covered in | §4–§6 (governed by [RU]) | §7–§9 |

---

## 4. Read & Understand — the automated process ⭐

**This is the authoritative flow.** [RU p6]

> Triggered when a new DMS item is **approved *or* pending-approved** — which of the two is a
> preliminary setup choice, not a fixed product behaviour. *(gap: the setting itself is in the
> Preliminary deck.)*

1. **Start routing** the DMS item
2. **Last signer signs** → DMS item routing state = **Approved**
3. A **Training Record** is created, and **Training Tasks** are created for the relevant trainees and
   linked to that record — **in the Training Management project pool**
4. **Notify** — the trainee gets a **daily alert** of training tasks, or sees open tasks on their dashboard
5. **Self reading & signing** — the trainee reads the **released PDF** (hyperlinked from the training
   task) and signs to acknowledge read-and-understand
6. **QA verifies** every task on that training record is signed
7. **QA signs off** the training record for **effectiveness**

Condensed [RU p7]:

```
eSign DMS  →  Training Record created        →  Tasks eSigned   →  Record effectiveness
              + Training Tasks created           by trainees        signed by QA
```

**Two signatures, two meanings, and they are not interchangeable:**
the **trainee's** signature on the *task* attests they read and understood;
the **QA** signature on the *record* attests the training was **effective**. A record whose tasks are
all signed is still not closed until QA signs. [RU p6 steps 6–7], [TC p6]

---

## 5. Setting up Read & Understand

[RU p4] — the whole configuration is two fields on the DMS item's **Training Details** section:

1. **Training Records List** → choose the **Read & Understand** training record.
   It is the **default and does not need changing**. [RU p5]
2. **Trainees** and **Roles** → who receives an R&U task whenever a new revision is released. [RU p4]

> That's the entire setup. Once the DMS document is signed, tasks generate automatically. [RU p4]

Live example [RU p5] — DMS-6119 *Training Procedure*:

| Field | Value |
|---|---|
| Training Records List | `TRN-5966-Read and Understand` |
| Trainees | `Omri Geva (Customer Success Manager)`, `Orcanos. Tech (Administrator)` |
| Roles | `Professional Services Team Lead`, `Professional Services` |

**The audience is a union of two fields, not one.** `Trainees` names individuals; `Roles` names roles
whose holders are all pulled in — "the system will automatically associate all users linked to the
selected roles as trainees" [TC p14]. Any coverage calculation must union both. See §12.

---

## 6. The Read & Understand template — do not touch

[RU p3], [TC p20]

- Lives in the **product tree**: `Training Management / Training Record Templates / Read and Understand` (`TRN-5966`)
- It is **two records**: a **Training Record** (parent — the template) with a **Training Task** child
- On launch (from a DMS item *or* a User Profile) the system creates:
  - **one Training Record for the DMS revision**, and
  - **one Training Task per user**, based on the DMS item's **Roles and Trainees**
- The created records land **in the Pool, not the Tree view**

> 🔒 **There must be exactly ONE Read & Understand template**, used by both DMS items and User Profiles.
> **It must not be changed or removed.** [RU p3 — flagged in red], [TC p20]

A sibling template `Formal (Ad hoc) Training for` covers the manual path [RU p3].

---

## 7. Manual launch — three entry points

[TC p8]. All three **prevent duplicate tasks** — see §10.

| Launch from | What it does |
|---|---|
| **Training Program** | Assign tasks to users from a predefined template. Supports multiple tasks (including DMS-based) across multiple users |
| **DMS Item** | Assign tasks straight from a document to all relevant trainees. No task is created for a user who already has one **for the same revision** |
| **User Profile** | Generate a user's tasks from their assigned role. No duplicates (e.g. for the same DMS revision) |

### 7.1 From a Training Program

**Create the record** [TC p9]: Training module → the Training Management folder → right-click → **+ Add Item**
→ item type **Training Record** → pick a **Template** (or *Create a blank item*) → **Create** → fill in → **Save**.

> A Training Task is created automatically under the Training Record template. [TC p10]

Templates seen live [TC p10]: *Zoom motor assembly* · *Ad Hoc Training for DMS Item* ·
*Ad Hoc Training for evacuation protocol* · *Self Reading*.

**Add tasks** [TC p12]: open the record → **+ Add Item** → fill Name + Training Information → **Save / Save & New**.

- A task linked to a DMS item gets its **Document Revision** filled automatically
- **Assigned To** is filled per trainee **after** launch — it is empty by design beforehand

**Launch** [TC p13]: click **Launch** → a Run pop-up lists the participants → tasks go to everyone in
the **Trainees** field [TC p11]. Then change Status and sign via **Start Routing**.

Two conveniences worth knowing:
- A finished record can be saved as a **template** for reuse (right-click → More → *Set as a Template*) [TC p13]
- The record's **Description** shows all its training tasks through an **embedded filter** that is part
  of the description template [TC p13] — the list is a live query, not stored content

### 7.2 From a DMS item

[TC p14], [RU p8]

1. Select a DMS item — existing, or a new one that requires training
2. Assign **Roles and Trainees** (from the *Training Details* section); every user linked to a selected role becomes a trainee
3. Click **Launch**
4. When the Training Record is complete, **sign it**

Record and tasks are created in the **Training Management Project Pool** [RU p8]. Per task:

- **Assigned to** each user
- **Task name** = document ID + document name + document revision [RU p8]
  — [TC p14] gives the rendered form: `Read and Understand [Trainee Name, DMS-ID : DMS Name (Revision.Change #)]`
- **Document Revision** field holds the full document + revision name
- Each task is in **start routing mode — the assignee can only sign it**

> ⚠️ **Launch from a DMS item is only available when the document has an approved revision.** [RU p8]
> Training always attaches to the **latest approved revision**, never a draft.

### 7.3 From a User Profile

[TC p17], [RU p9]

1. Click **Launch** on the User Profile
2. A Training Record is created in the Training Management Project Pool
3. Tasks are generated in the pool, linked to that record:
   - **one task per relevant DMS item**, selected by the user's **role / name** [RU p9]
     — [TC p17] says the DMS items are those linked to the user's **Job Title**
   - Task name = document ID + name + revision; Document Revision = the **last approved** document + revision
   - Each task in **start routing mode**; the assignee can only sign

Then: tasks created → users sign → **the Training Coordinator reviews and signs the Training Record** [TC p17].

**Creating a User Profile** [TC p16]: **＋** → *Select User* → pick from existing system users → **Create** → fill metadata.
- **Job Title** is filled automatically from the **Admin User settings**
- User Profiles are managed **in the Pool**, through the Work Item view

---

## 8. Use-case catalogue

[TC p21] lists four beyond plain R&U. The distinction in §8.3 vs §8.4 is the one people get wrong.

### 8.1 Ad-hoc group training (trainer-approved only) [TC p22]

In-person (frontal) sessions run outside the digital process, documented afterwards for the audit trail.

- Approved and confirmed **by the trainer only**, who verifies attendance and completion
- Records the **attendees, topic, date, attachments and trainer signature**
- Each trainee's **User Profile shows the Training Record as evidence of participation**

`Add Training Record → select template → fill Trainer + Trainees → sign the record`
Template: *Training Record : Ad-Hoc group training approved by trainer only*

### 8.2 New Employee Training Program [TC p25]

A Training Record **template** holding many tasks, **tailored per role** so only relevant training is assigned.
Tasks mix general onboarding (policies, safety, compliance), DMS-based R&U for key documents, and
role-specific skills. Assign the new employee, launch, all tasks generate.

`Add Formal Training → add tasks → save as template → add trainees + Launch`

### 8.3 Formal Training Record **for** DMS items — one task **per document** [TC p23]

Each task makes a trainee read and understand **one specific** DMS item.

- Create the record from the **Formal** template
- Add several tasks, each linked to a single document via the **"Related DMS Item"** field
- On launch the system fills the **latest revision** into *Document Revision*
- **Each trainee receives a separate task for each DMS item**

### 8.4 Training Record **as evidence of** completed training [TC p24]

Documents training on several DMS items that already happened **outside the system**.

- One formal record consolidates it; trainees are assigned to the record
- The DMS items go on the **task**, in the **"DMS Items List"** field, and appear in the **Traceability** tab
- On launch, **a single task per trainee**, covering all the linked documents at once

> **§8.3 vs §8.4 is a field choice with a structural consequence.**
> **`Related DMS Item`** (one document per task) ⇒ *N documents × M trainees* = N×M tasks, each signed separately.
> **`DMS Items List`** (many documents per task) ⇒ *M* tasks; one signature covers every document on it.
> Same screen, same templates — very different evidence granularity, and very different task counts.

---

## 9. Field reference

Observed in screenshots; a tenant may customise. Verify per install with `QW_Get_Item_Add_Edit`.

### Training Record — `TRN` [TC p11]

| Section | Fields |
|---|---|
| Overview | Name · Category · **# Tasks** · Path · Status · Assigned To · **% Completion** |
| Scheduling | Training Start Date · Due Date · Completion Date |
| Training Information | **Trainees** · Certification Required · Training Material · **DMS Items List (Multi)** · Training Plan List · **Roles / Job Titles** ⟵ *the role edge, §2.1* · Source · Department · **Trainer** · ECO Number |
| Actions | **Launch Training** · Start Routing (sign) |

- **% Completion is auto-filled**, reflecting completion of the record [TC p11]
- Tasks are assigned according to the **Trainees** field [TC p11]

### Training Task — `TRN_TSK` [TC p12, p15, p19]

| Section | Fields |
|---|---|
| Overview | Name · Status · **Assigned To** = **the user id** (auto-filled on launch) ⟵ *the identity join, §2.1 Trap 1* · Category · Priority · Created Date · Parent Name |
| Training Information | **DMS Items List** · **Related DMS Item** · **Training Records List** = the parent `TRN` ⟵ *§2.1 edge 3* · Training Material · **Document Revision** (auto-filled from the linked DMS item) |
| Effectiveness | Effectiveness Evaluation Activities · Approver · Justification |
| Routing | Routing Start Date · Routing Due Date · **Approved Date** · **Approver** |

### DMS Item — `DMS_ITEM`, *Training Details* section [RU p5], [TC p14]

| Field | Meaning |
|---|---|
| **Training Records List** | Which training record fires — defaults to *Read and Understand* |
| **Trainees** | Named individuals who must be trained *(parked — outside the v1 rule)* |
| **Roles / Job Titles** | Roles whose holders must all be trained. ⟵ **the role edge, §2.1 edge 1.** Either name may be in use; it varies by tenant [RU p5] shows *Roles*, [TC p14] shows *Job Titles* |

Also present: Current Revision · **Routing State** (`Approved`) · ECO Details · Standard Compliance
(ISO 13485 §, 21 CFR Part 820 §) · Electronic Signature.

### User Profile — `USRP` [TC p16, p17, p19]

Overview · Personal Information · System User Information · Education and Experience (Degrees and
Diplomas; Previous Work Experience: Company / Job Role / Dates) · **Training Information → Training
Records List** · Description (Name · Employee Training File · Profile Image).

**The two fields that carry the joins** (§2.1):

| Field | Role |
|---|---|
| **`Assigned To`** | **the system user id** — the identity every `TRN_TSK` matches on. **Not** the `USRP` work-item id |
| **`Roles` / `Job Title`** | what the person is; matched against `DMS_ITEM.Roles` and `TRN.Roles`. Auto-filled from the **Admin User settings** [TC p16] |

**The User Profile is the training file.** [TC p19] It embeds two live tables:

| Table | Columns |
|---|---|
| **Employee Training Records** | Link · Key · Name · Assigned To · Training Records List · Status · DMS Items · Routing Start Date · Routing Due Date · Approved Date · Approver |
| **List Of Completed Trainings** | same |

---

## 10. Status, category and the duplicate rule

**Training Task / Record status** [TC p15, p26]:
`New` · `Draft [Template]` · `In Process` · `Completed` · `Approved Effectiveness`

> `Approved Effectiveness` is a **distinct terminal state after `Completed`** — it is the QA
> effectiveness sign-off of §4 step 7. Treating `Completed` as the end of the process **under-reports
> the compliance state**.

**Training Record category** [TC p26 — *Courses Topics* panel]:
`Not Set` · `Manufacturing…` · `New Employee` · `Informal` · `Formal` · `Read and understand` ·
`On the job training` · `Ad Hoc`

**Task category** [TC p15]: `Self Reading` · `Not Set`

### The duplicate rule

The system **will not create a second task for a user who already has one for the same DMS revision**
— stated for all three manual launch paths [TC p8], and again per path [TC p8 cards].

> This is load-bearing for any coverage report: **the absence of a task is not always a gap.** It may be
> suppression because the user already holds a task for that revision, elsewhere. Any "missing training"
> calculation must key on **(user, DMS item, revision)** — not on (user, document).

---

## 11. Conflicts between the two decks

Resolved by the precedence rule in §0 — **[RU] governs**.

| # | [TC] says | [RU] says | Resolution |
|---|---|---|---|
| 1 | "A Training Record is the summary of all training tasks assigned to **a specific user**" [TC p6] | "create **one training record for the DMS revision**, and one training task for each user" [RU p3] | **CLOSED by [PO] §0.1 #1** — a record is a collection of tasks across **multiple** users. [RU] was right; [TC p11]'s own screenshot agrees (plural *Trainees*, one `% Completion`). [TC p6] is loose wording. |
| 2 | "Training Record **and** Training Task will be created **to each trainee**" [TC p14] | one record, one task per user [RU p3, p8] | **[RU].** [TC p14] is describing the *task naming pattern*, which does embed the trainee name — not a per-trainee record. |
| 3 | Automation fires when "Document is signed" → Approved [TC p18] | fires when the DMS item is "**approved or pending approved** (see preliminary setup)" [RU p6] | **PARKED by [PO] §0.1 #4** — out of scope for now; assume it fires on approval. [RU] remains the more precise description when this is picked up. |
| 4 | Training Task code `TRN_TSK` [TC p5] | — | Confirmed by rendered keys `TRN_TSK-29761` [TC p15]. Supersedes the `TRN_TASK` spelling used in earlier notes. |
| 5 | DMS custom code renders `ORCA-29757` [TC p14] | renders `DMS-6119` [RU p5] | **Not a conflict** — two tenants, two custom codes, one original type `DMS_ITEM`. |

---

## 12. Implications for the Training Traceability tool

> **Now being built.** The consuming project is the **traceability-matrix** repo:
> `design/DESIGN_TRAINING_MANAGEMENT.md` **§0 START HERE** holds the build handoff (verified data
> model, config-screen spec, filter ids, scope), and `CLAUDE.md` **Critical Note #24** carries the
> traps. This section is the findings register behind those.

| # | Finding | Status |
|---|---|---|
| 0 | **The identity join is `Assigned To` (user id), not the `USRP` work-item id** — §2.1 Trap 1 | 🚨 **Highest-risk detail in the build.** Wrong ⇒ zero tasks match, every user reads untrained, no error raised |
| 0b | **Field names vary by tenant** (`Roles` / `Job Titles`, `Training Records List`) — §2.1 Trap 2 | ⚠️ Needs **configurable field mapping** per install. This is exactly what the design's per-slot field-mapping step is for |
| 0c | **Two role edges:** `DMS_ITEM.Roles` and `TRN.Roles`, both → `USRP.Roles` | ✅ **Confirmed and built** (traceability-matrix v3.22.0). The `TRN` edge **is** the formal-training audience, and it is `TRN.Roles` **∪ `TRN.Trainees`** — a formal training is routinely aimed at named people, so roles alone reports a correctly-run training as having nobody to train. Both populations are scored into one list, tagged by source. See §12.1 |
| 1 | **One role vocabulary.** `Roles` (DMS item) and `Job Title` (user) are the same field, so the join is an **exact match** | ✅ **Resolved** by [PO] §0.1 #2. The fuzzy-match contingency is off the table — this was the biggest unknown in the estimate |
| 2 | **Scope is the current / last approved revision only** | ✅ **Set** by [PO] §0.1 #5. Revision history deferred |
| 3 | **Records and tasks are created in the POOL, not the tree** [RU p3, p8, p9], confirmed [PO] §0.1 #3 | ⚠️ **Live trap.** A tree-scoped filter returns **zero** and reads as an empty tenant. The shipped dashboards scope tasks to *All Pool (Backlog) Items* and template records to *All View (w/o Pool) Items* [TC p26] |
| 4 | **Duplicate suppression per DMS revision** [TC p8] | ⚠️ **Open.** Orcanos won't create a second task for a user who already holds one for the same revision — so an absent task can be legitimate suppression. Contained for now because v1 evaluates only the current revision |
| 5 | **Two sign-offs, not one** — trainee signs the task, QA signs the record for **effectiveness**; `Approved Effectiveness` is a state beyond `Completed` [TC p26] | 📋 **For discussion.** Treating `Completed` as terminal under-reports the compliance state |
| 6 | **`% Completion` and `# Tasks` already exist on the record** [TC p11] | 📋 Cheaper roll-up than assumed — but it counts **created** tasks only, so it can never surface a missing one. The gap stays ours to compute |
| 7 | **Launch requires an approved revision** [RU p8] | 📋 A document with no approved revision is **not** a gap. Excluding it kills a whole class of false findings |
| 8 | **Existing dashboards already cover the easy views** [TC p26] | 📋 *Courses Topics*, *Trainers*, *Annual Training Plan*, *Employee Training Plan Execution Status*. Don't rebuild them — the differentiator stays the computed expected-set and ❓ Missing |
| 9 | **`Trainees` (named individuals) is a second audience** alongside `Roles` [RU p5] | ✅ **Built for FORMAL training** (v3.22.0, §12.1). Still parked on the **DMS** side, where the audience remains `Roles` alone |

---

## 12.1 Formal training — the three differences that fail silently

*(Built in traceability-matrix **v3.22.0**, 2026-08-27. Engine `training_engine._formal_rows`;
traps distilled in that repo's `CLAUDE.md` Critical Note **#26**; full reference
`docs/TRAINING_TRACEABILITY.md` §4.8. ⚠️ The field patterns follow the join documented here and
the `CS218` precedent of §2.3 — they have **not** been measured against a live `TRN` filter
response.)*

A `TRN` is scored exactly as a `DMS_ITEM` is — audience × people, one cell each. Three things
differ, and each one renders a clean, plausible, wrong report:

| # | Difference | What breaks if it is got wrong |
|---|---|---|
| 1 | **Audience is `Roles` ∪ `Trainees`** | Roles alone reports a correctly-run training as having nobody to train |
| 2 | **The task → record link is `TRN_TSK.[Training List]`** (§2.1 edge 3) | A formal task's **name is free text and parses to nothing** (§2.2) — the 302 of 1031 orca60 tasks. Without that column **every** record reads as though nobody was trained |
| 3 | **The record's completion is signed INDEPENDENTLY of its tasks** | Letting it mark people trained is a **fabricated pass** — the worst output a training report can produce |

### On difference 3 — the product owner's rule

> *"the TRN has 2 fields that show # of tasks, # of completed tasks. The completion I talk about
> here is the TRN completion (actually regardless of the tasks) since it is signed independently."*
> — [PO] 2026-08-27

So `completed` ⟺ **the completion date is set**, and nothing else. It is carried *beside* each
person's own task state, never folded into it, **precisely so the two can disagree** — a record
signed off complete while trainees still owe is a **finding**, and only carrying both values can
show it.

`# Tasks` / `# Completed Tasks` [TC p11] are shown beside the computed figures and never in place
of them: they count **created** tasks, so they can never surface a missing one (finding 6).

### On difference 1 — `Trainees` is rendered NAMES, not references

`Omri Geva (Customer Success Manager), Orcanos. Tech (Administrator)` [RU p5]. So:

- split on `,` `;` `|` **only outside parentheses** — a role suffix may itself read *"Manager, Quality"*
- strip the trailing parenthesised group; it is the rendered role, not part of the identity
- match **exactly, after normalising to letters and digits only**: `Orcanos. Tech` ≡ the user id
  `Orcanos.Tech` is a *formatting* difference; `Ada Lovelace` vs `Ada L` is **not** a match
- a trainee matching no `USRP` is **reported by name**, never joined — same rule as §2.1 Trap 1's
  near-miss discipline. The User Profile filter is the ceiling on everything (Trap 4)

Anyone in scope **only** by name belongs in their own reported column (`(named individually)`),
not folded under a role the record never named — that would misstate *why* they owe it.

### On difference 2 — resolving the link value

The field renders in several shapes. Resolve the id **anchored at the start**:

```
TRN-21803               -> 21803
21803-Setting up the lab -> 21803
21803                   -> 21803
Lab safety (TRN-21803)  -> 21803      (fallback: a KEY-shaped token anywhere)
Setting up the lab 2024 -> None       ⚠️ a leading NAME must not donate a stray number
Not set                 -> None       (§2.3 Trap 8 — "Not set" is a VALUE)
```

> A task silently attached to the **wrong** record is worse than one attached to none.

⚠️ **`Assigned To` is load-bearing here in a way it is not for R&U.** An R&U task can fall back to
the user id inside its name (§2.2 Trap 5 — badly, but it resolves *someone*); a formal task has no
name to fall back to, so without that column the task belongs to **nobody**.

### And one thing a record is not

A `TRN` is an **event, not a versioned document** — it has no revision axis, so none of §2.3
Trap 6 applies to it, and it must never be reported as *"not approved yet"*. A record naming
neither a role nor a trainee is its own finding (*nobody can ever be trained on it*), and unlike a
document it needs **no `Training List` gate** (Trap 8): a `TRN` in the training-records filter
**is** a training, whereas most of a controlled document library is not.

---

## 13. Dashboards that already ship

[TC p26] — dashboard **QMS - Training Management [Managers] (ISO 13485 Sec. 6.1)**; a **(Trainees)** variant also exists.

| Panel | Source |
|---|---|
| **Courses Topics** | Training Record, All View (w/o Pool) Items, group by **Category** |
| **Trainers** | Training Record, All View (w/o Pool) Items, group by **Trainer** |
| **Annual Training Plan** | Training Task, All Pool (Backlog) Items, group by **Training Records List, Status** |
| **Employee Training Plan Execution Status** | Training Task, All Pool (Backlog) Items, group by **Assigned To, Status** |

End-user side [RU p10]: a **My Open Tasks** dashboard with **Training Tasks Waiting for My Signature**
(Training Task + `{SysFilter} - My Tasks Waiting To be Sign`; columns Actions · Key · Name · Revision).

---

## 14. Open questions

Closed items are kept so they aren't re-asked.

### Still open

1. **Leavers** — are inactive User Profiles excluded from role expansion? (Directly affects the ❓ Missing count)
2. Whether a training task is creatable **via the API** (`QW_Add_Object` + relation) or only from the UI
   — decides whether "assign the missing tasks" is ever possible outside Orcanos
3. Whether a **role change** retro-assigns training the user missed
4. Whether **periodic retraining** is supported by `TRN_P`, or only annual planning
5. What happens to an **open task when a newer revision is released** — superseded, cancelled, or left open
   *(bundled with the deferred revision-history work)*

### Closed

| Was | Answer |
|---|---|
| How are **Roles** stored — free text, picklist, or `JD` references? | **One vocabulary; `Roles` ≡ `Job Title`; exact match.** [PO] §0.1 #2 |
| The **preliminary setup** for *approved* vs *pending-approved* [RU p6] | **Out of scope for now.** [PO] §0.1 #4 |
| Is a Training Record per user or per event? | **Per event — many users' tasks.** [PO] §0.1 #1 |
| Pool or tree? | **Pool.** [PO] §0.1 #3 |

> The two decks we don't have — **Training Management Basics (Preliminary)** and **Formal Training**
> [RU p11] — are the likeliest source for items 3–5 above.
