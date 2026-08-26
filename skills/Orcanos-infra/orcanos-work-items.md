# Orcanos Work Items — the model and the catalogue

**Part of:** `Orcanos-infra` · **Companion:** `orcanos-api` (how to call), `orcanos-form-builder` (fields per type)

---

## 1. What a work item is

**In Orcanos, almost everything is a work item.** A requirement, a test case, a defect, a CAPA, a
controlled document, a training task — and even a *user profile* — are all the same kind of object.
They are not separate tables with separate APIs. They are one generic object with a **type
discriminator**.

That single design decision explains most of how Orcanos behaves:

| Because everything is a work item… | …this follows |
|---|---|
| ids come from one space | an id is **globally unique across all types** — id `26521` is one object, whatever type it is |
| one relations graph | **any type can trace to any other type**. Requirement→Test, Complaint→CAPA, Training Task→Document all use the same mechanism |
| one field mechanism | every type's fields are **tenant-customisable**; two customers' "CAPA" have different fields |
| one permission mechanism | rights are granted **per type, per project** — not globally |
| one set of endpoints | `QW_Add_Object`, `QW_Get_Object`, `QW_Get_Filter_Results` serve every type; only the type parameter changes |
| filters are per type | a saved filter returns **one type**, which is why `Total_records` for (filter, type) is a true count |

**A work item represents a controlled record** — something the QMS must be able to show an auditor:
who created it, what it says, what it is linked to, what version it belongs to, and who may change it.
If a thing needs to be traceable, in Orcanos it is a work item.

---

## 2. Anatomy of a work item

| Part | What it is | Notes / traps |
|---|---|---|
| **id** | numeric, globally unique | Sometimes presented as `"12345 (9876)"` — **parse out the numeric part** |
| **Item Type** | the discriminator | Has **both** a Code and a Label — and they are not interchangeable (§3) |
| **Original code** | the system code (`MR_REQ`, `T_CASE`, `SRS`) | What most API calls take |
| **Custom code** | the tenant's display prefix (`UR`, `TC`, `SR`) | What the **user** sees. Configurable per tenant |
| **Key** | `{code}-{id}` — e.g. `UR-26514` | Displayed with the *custom* code. **A freshly created item's `Key` still carries the ORIGINAL code** (`MR_REQ-26514`) until re-read |
| **Name** | the title | `Obj_name` on most types — **`Synopsis` on defects**. Always try both |
| **Description** | rich HTML | Frequently **double-encoded** (`&amp;nbsp;`) — decode in a loop |
| **Project + Version** | items are scoped to `(project_id, version_id)` | A project's identity is `(project, version)`, not project alone |
| **Fields** | per type, per tenant | Read them live via `QW_Get_Item_Add_Edit`; never hard-code a field set |
| **Relations** | the traceability graph | `Traced Items Info` / `QW_Get_Object_Relations` |
| **Children** | the containment/outline tree | `Get_Children` — **a different graph** from relations (§3.4) |
| **Permission** | letter string, per type per project | `A`=Add, `U`=Edit, `D`=Delete, `O`=Ask Paul, `V`=Viewer (grants nothing) |

---

## 3. The identifier traps

These cost real debugging time. Each one fails **silently** — an empty result, not an error.

### 3.1 One type has THREE identifiers, and different endpoints want different ones

| Identifier | Example | Wanted by |
|---|---|---|
| **Original code** | `SRS` | most calls, `Item_Type` params, URL `Item=` |
| **Label / description** | `Software Requirement` | **`QW_Add_Object`** (`Object_Type`), **`GetFilterList`** (`ItemType`) |
| **Custom code** | `SR` | display only — and relation keys (`QW_Add_Relations_Custom_Code`) |

Pass the wrong one and you get `200 OK` with an empty array. `GetFilterList` called with `SRS`
instead of `Software Requirement` returns `[]`, which reads as "this tenant has no filters."

### 3.2 Custom code ≠ original code

The tenant renames the prefix. Confirmed mappings on orca60:

| Original | Custom | Type |
|---|---|---|
| `MR_REQ` | `UR` | User Requirement |
| `REQ` | `PR` | Product Requirement |
| `SRS` | `SR` | Software Requirement |
| `T_CASE` | `TC` | Test Case |

**Never derive the type code from a key prefix** — `UR-26514` is type `MR_REQ`, not `UR`.
Build a code→custom map from `QW_Login` and the items in scope.

### 3.3 Test Case and Test Run share the code `T_CASE`

A **Test Run is the execution of a Test Case** and is not independently creatable. Both carry
original code `T_CASE`; **only the Label distinguishes them.** A run also carries the **same Key**
as the case it executes. Any logic that keys on the code alone will merge the two.

### 3.4 Relations ≠ children

- **Relations** (`Traced Items Info`, `QW_Get_Object_Relations`) = the **traceability graph**. This is what a trace matrix is built from.
- **Children** (`Get_Children`) = the **containment/outline tree** — a document's sections. A child's `Ver_Id` can differ from its parent's.

They are different graphs. Never substitute one for the other.

### 3.5 A `USRP` has TWO identities — the work-item id is the wrong one

A **User Profile** is a work item, so it has an item id like everything else. But it also *represents
a person*, and the person's identity lives in its **`Assigned To`** field — the **system user id**.

| Identifier | Identifies | Use it for |
|---|---|---|
| `USRP` **work-item id** (`29762`) | the profile *record* | relations, links, opening the item |
| `USRP.`**`Assigned To`** | the **person** | **every join to work assigned to that person** |

A `TRN_TSK.Assigned To` (and any other assignment field) holds the **user id**. Joining on the
work-item id matches nothing and **raises no error** — the report simply reads as though nobody has
any assigned work.

> Generalise this: **"which item is it" and "who is it" are different keys.** Any work item that
> stands for a person or an assignment has both.

### 3.6 A Key can carry trailing text

`TC-8789 (7678)` — trailing internal id. `TC-44333 (Pass)` — trailing run result.
The key is `[A-Za-z][A-Za-z0-9_]*-\d+`; **the prefix may contain an underscore** (`MR_REQ-26514`).
Everything after the key is not part of it.

---

## 4. The catalogue

**Confidence column — read it before using a code.**

| | Meaning |
|---|---|
| ✅ | **Verified** — confirmed against the live API or in shipped working code |
| 📌 | **Given** — supplied by the product owner; authoritative |
| ◐ | **Observed** — the label is real on this tenant; the **original code is inferred and must be confirmed** |
| ○ | **Module known, code unknown** — Orcanos ships this; read the code from `QW_Login` |

### 4.1 System / People

| Code | Type | What it represents | Conf. |
|---|---|---|---|
| `USRP` | **User Profile** | The **employee e-record** — a system work item holding a person's details: name, id, role / **Job Title**, contact details, education and previous experience. Because it is a work item, a user can be traced to, filtered on and reported over like any other record. **It is also the training file**, embedding live tables of the person's training records and completed trainings. `Job Title` is filled automatically from the Admin User settings; profiles live **in the Pool**, managed through the Work Item view. | ✅ |

### 4.2 Document Control (DMS)

| Code | Type | Custom | What it represents | Conf. |
|---|---|---|---|---|
| `DMS_ITEM` | **DMS Item** | `DMS`, `ORCA` | The record that manages a **controlled document**. Holds the document's **metadata** and **all its file revisions (A, B, C…)** — the item is the container, the revisions live inside it. Carries a **Training Details** section (*Training Records List* · *Trainees* · *Roles*) that drives training. Approving a new revision is what fires it. | ✅ |

> **The custom code varies by tenant** — `DMS-6119` on one, `ORCA-29757` on another, both type
> `DMS_ITEM`. Classic §3.2 trap.

> **Consequence for any report:** the DMS item is one row, but training is owed **per revision**.
> A person trained on Rev B is not trained when Rev C ships. Never key training on the DMS item alone.

### 4.3 Training

| Code | Type | What it represents | Conf. |
|---|---|---|---|
| `TRN` | **Training Record** | Created **for each training process**. Holds the tasks for **all** its trainees (one record per training event / DMS revision — *not* one per user). The key compliance document: QA reviews and signs it for **effectiveness**. Carries `# Tasks` and an auto-computed `% Completion`. | ✅ |
| `TRN_TSK` | **Training Task** | **One per trainee**, linked to its Training Record and optionally to DMS items. Assigned on launch, then in **start-routing mode — the assignee can only sign it**. Either a general task or a DMS-based one. | ✅ |
| `TRN_P` | **Training Plan** | The scheduled **annual** training framework; links to the training records it plans. | ✅ |
| `JD` | **Job Description** | Connects a person to the list of job descriptions. Note **"role" and "job title" are one vocabulary** here (§5) — whether `JD` work items *are* that list, or sit alongside it, is unconfirmed. | ✅ |

> ⚠️ **`TRN_TSK`, not `TRN_TASK`. `DMS_ITEM`, not `DMS`.** Both confirmed from rendered keys
> (`TRN_TSK-29761`, `USRP-29762`) in the Orcanos training decks. Earlier notes used the wrong spellings.

> **Full process:** `orcanos-processes/orcanos-training-process.md` — the R&U automation, the three
> manual launch paths, the field reference, and the pool-vs-tree trap.
> **Project design doc:** `design/DESIGN_TRAINING_MANAGEMENT.md` in the traceability-matrix repo.

### 4.4 Requirements

| Code | Type | Custom | What it represents | Conf. |
|---|---|---|---|---|
| `MR_REQ` | User Requirement | `UR` | What the **user/market** needs. Usually the root of the trace chain. | ✅ |
| `REQ` | Product Requirement | `PR` | What the **product** must do to satisfy the user requirement. | ✅ |
| `SRS` | Software Requirement | `SR` | What the **software** must do. Typically traces up to a product requirement and down to tests. | ✅ |
| `REQ_HD` | Requirement Document | — | A requirement **document/header** — the root of a containment tree (Introduction → User Requirements → …). Browsed with `Get_Children`, **not** with relations. | ✅ |

### 4.5 Test

| Code | Type | Custom | What it represents | Conf. |
|---|---|---|---|---|
| `T_CASE` | Test Case | `TC` | The **defined** test — steps and expected results. Proves *coverage*: a test exists. | ✅ |
| `T_CASE` | Test Run | (same key as its case) | The **execution** of a test case, carrying the result (Pass / Fail / Fail (Stop) / Blocker / No run). Proves *execution*. **Not directly creatable** — produced by running a case. See §3.3. | ✅ |

### 4.6 Quality events

| Code | Type | Custom | What it represents | Conf. |
|---|---|---|---|---|
| `DEFECT` | Defect | — | A bug or product defect. **Its name is in `Synopsis`, not `Obj_name`.** | ✅ |
| — | Complaint | `COMP` | Customer complaint. Commonly the entry point of a chain: Complaint → CAPA / Non-Conformance / Risk. | ◐ |
| — | CAPA | — | Corrective and Preventive Action. Commonly traces from a complaint or non-conformance, and on to a change order. | ◐ |
| — | Non Conformance | `NCR` | A recorded non-conformance. | ◐ |
| — | Risk | — | A risk record (ISO 14971). Commonly traces down to the requirements that mitigate it. | ◐ |
| — | Engineering Change Order | `ECO` | A controlled change. Commonly the outcome of a CAPA. | ◐ |

> All six are **real types on the orca60 tenant** — they appear in that tenant's data and in its Ask
> Paul prompt names. **The original codes are inferred and must be confirmed** before use in a call.

### 4.7 Modules known to exist — codes must be read from `QW_Login`

Orcanos ships these as an eQMS; the item types exist, but no code here is confirmed. Fill in as they
are verified, and give each its own module skill.

`Audit` · `Supplier / Vendor` · `Design Review` · `Change Request` · `Hazard / FMEA` ·
`Test Set / Test Suite` · `Release` · `Project` · `Task` · `DHF / Design History File`

**Seen live in a tenant's item-type navigator** (labels only — codes still unread):
`Document` · `Equipment` · `License` · `Question` · `Heading` · `RF Risk` ·
`Return Merchandise Authorization` · `Folder` · `AI Insight` · `Clear Capital Rule`.
Note `Folder` and `Heading` — **structure is itself a work item**, which is how the containment tree
of §3.4 is built.

---

## 5. Who owes training — the join nothing computes

The DMS item's **Training Details** section names who must be trained; the User Profile says what a
person is. **`Roles` and `Job Title` are the same field and the same vocabulary** (product owner,
2026-08-25) — so this is an **exact match**, not a fuzzy one:

```
DMS_ITEM .Roles      →  roles that must be trained on this document
USRP     .Roles      →  roles this person holds        ( = "Job Title" — one vocabulary)
           ∩            →  the people who owe training
TRN_TSK              →  the tasks that actually exist
```

Orcanos stores every side and **never computes that join across the estate**. So a person who should
have received a `TRN_TSK` and didn't is **invisible** — there is no record to report on, and existing
reports count only *created* tasks.

**The rule, as scoped for v1:**

```
MISSING(user, dms_item)  ⟺   user.Roles ∩ dms_item.Roles ≠ ∅
                         AND  no TRN_TSK exists for (user, dms_item)
                              — evaluated on the CURRENT / last approved revision
```

Two things to keep in mind when reading a result:

1. **Duplicate suppression.** Orcanos will not create a second task for a user who already holds one
   for the **same DMS revision** — so an absent task is not automatically a gap.
2. **`Trainees`** on the DMS item names individuals directly, alongside `Roles`. Real, but **parked**
   outside the v1 rule above.

> Full mechanics and the decisions behind this: `orcanos-processes/orcanos-training-process.md` §0.1, §5, §12.

---

## 6. Getting the authoritative list for a tenant

**`QW_Login` is the only ground truth.** Its response carries, per project, every item type the
signed-in user can see:

```
Data.Projects.Project[].Item_type[]  →  { Code, Label, Permission, … }
```

- **`Code`** — the original code to use in API calls
- **`Label`** — the description, wanted by `QW_Add_Object` and `GetFilterList`
- **`Permission`** — the per-type, per-project letter string

Three things to remember when reading it:

1. **It is per project.** A user may be able to add a type in one project and not another. There is no global type list.
2. **It is per user.** A type the signed-in user cannot see does not appear. An empty list is not proof the type doesn't exist.
3. **`Projects` is not an array** in the XML→JSON conversion — access `Projects.Project[]` and normalise single vs. multiple.

> **This is how to fill in every ◐ and ○ above.** Sign in to the tenant, dump `Item_type[]`, and
> promote the rows to ✅ with the real codes.

---

## 7. Related

| Need | Go to |
|---|---|
| Calling any endpoint | `orcanos-api/SKILL.md` |
| The login response in detail, incl. permission letters | `orcanos-api/qw-login.md` |
| Fields of a given type on a given tenant | `orcanos-form-builder` |
| Creating an item and tracing it | `orcanos-api/qw-add-item.md`, `qw-add-trace.md` |
| The relations graph vs the children tree | `orcanos-api/qw-get-object-relations.md`, `get-children.md` |
