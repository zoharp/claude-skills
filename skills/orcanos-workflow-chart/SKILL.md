# Orcanos Workflow / Process Flow — reading an item type's lifecycle

How to get an Orcanos item type's **states, transitions, and the e-signature processes that gate
them** — the "process flow" an SOP is supposed to describe.

> **Verified end-to-end against `orca60` on 2026-09-10** — `Ver_Id 422`, item types `CAPA`
> (6 states / 6 edges), `COMP` (6 / 10), `NCR` (3 / 3). Every claim below was observed, not
> inferred.

---

## There is no API for this

`/api/swagger/docs/v1` lists **75 endpoints and not one of them returns workflows, states,
transitions, or signature gates**. `QW_Get_Item_Add_Edit` gives you the *form*; the Status field's
picklist gives you a list of status **values**, which is not the same thing — it says nothing about
which transitions are allowed, in what order, or which need a signature.

The only machine-readable source is a **UI page**:

```
<tenant base>/web/<Ver_Id>/items/workflowchart?ItemType=<ORIGINAL CODE>
```

```
https://app.orcanos.com/orca60/web/422/items/workflowchart?ItemType=CAPA
```

- **tenant base** — `https://app.orcanos.com/orca60`. Strip `/api/v2/Json` off the stored API URL;
  the account segment is already in it.
- **`Ver_Id`** — the **numeric** version id from `QW_Login`'s `Projects.Project[].Version[].Ver_id`
  (`422`), never the version *label* (`1.0`).
- **`ItemType`** — the work-item **ORIGINAL CODE** (`CAPA`, `COMP`, `NCR`), not the
  DESCRIPTION/Label. Same convention as the other `/web/` deep links, and the **opposite** of
  `GetFilterList` / `QW_Get_Item_Add_Edit`, which key on the label.

---

## Auth: forms-auth session cookie, not Basic

This is a UI route. It behaves exactly like
[`/web/Download/ViewAttachment`](../orcanos-api/get-section-data/download-attachment.md): an
`Authorization: Basic` header is **ignored** and you are redirected to the login page. A backend
must log in the way the browser does and reuse the session cookie — the credentials are the same
account, it is the *mechanism* that differs.

Reuse `orcanos_web_session()` from the download-attachment doc verbatim: GET
`/web/account/login` for the `__RequestVerificationToken`, then POST it to
`/web/Account/Login/form-login` with `Username`, `Password`, `IsShowSavePassword`, `failed_count`.

⚠️ **Log in once and cache the session.** A rejected login posts a `failed_count` and can count
toward lockout — never retry a bad credential in a loop.

---

## Parse the embedded JSON, not the HTML table

The page renders a Process Flow table and a cytoscape diagram, but both are built from **two JSON
literals embedded in a `<script>` block**. Parse those — they are stable, and they carry **more
than the table shows**:

```js
const NodeEdgeContents = [ {...}, ... ];   // the transitions
let nodes = [ {"data":{"id":"NEW","label":"New", ...}}, ... ];   // the states
```

```python
_EDGES_RE = re.compile(r"const\s+NodeEdgeContents\s*=\s*(\[.*?\])\s*;", re.DOTALL)
_NODES_RE = re.compile(r"let\s+nodes\s*=\s*(\[.*?\])\s*;", re.DOTALL)
```

### One edge, in full

```json
{"From_val":"DONE","To_val":"VERIFIED",
 "From_status":"QA Review","To_status":"CAPA Plan Approved - Implementation",
 "Transition_name":"","Auto_assigner":"(No Change)",
 "Process_ID":"38","process_name":"Single Signer",
 "ColorCode":"5477921","Is_Freeze":0,
 "is_default_status":0,"is_complete_status":0}
```

| Field | Meaning |
|---|---|
| `From_status` / `To_status` | the human state names — **use these**, not `From_val`/`To_val` |
| `From_val` / `To_val` | internal status codes (`NEW`, `IN_PROCESS`, `CODE_1`) — tenant-specific slots |
| **`process_name`** | **the e-signature process gating this transition** (`"Single Signer"`), `""` when none |
| `Process_ID` | that process's id (`"38"`) |
| `is_default_status` | `1` marks the **synthetic creation edge** — see below |
| `is_complete_status` | `1` means `To_status` **closes** the workflow |
| `Is_Freeze` | the transition freezes the item |
| `Auto_assigner` | `(No Change)` or a target assignee |

⚠️ **`process_name` and the two status flags are NOT in the rendered table** — the table shows only
From / To / Transition Name / Auto Assigner. If you scrape the table you silently lose exactly the
field a compliance check needs: *which steps require an approval*.

### The `[Default Status]` row is not a transition

```json
{"From_status":"[Default Status]","To_status":"New","is_default_status":1, ...}
```

It records **which state an item is created in**, not a move a user can make. Filter it out of the
transition list and read it as `start_state`, or every path analysis starts from a state that
doesn't exist.

---

## ⚠️ Three silent failures — all return HTTP 200

None of these is an HTTP error. `raise_for_status()` catches none of them. Detect them by
**inspecting the page**, and use `<title>` as the discriminator.

| Input | What comes back | How to detect |
|---|---|---|
| **Wrong / nonexistent `Ver_Id`** (`1`, `99999`) | the **Dashboards page**, 343 KB, HTTP 200 | `<title>` is `Dashboards`, not `… Process flow` |
| **Unknown `ItemType`** (`BOGUS_XYZ`) | an empty Process Flow page, ~27 KB | title *is* `… Process flow`, but neither JSON literal is present |
| **Expired session** | the **login page**, HTTP 200 | body contains `__RequestVerificationToken` + `/Account/Login/form-login` |

```python
def _is_process_flow_page(html):
    m = re.search(r"<title>(.*?)</title>", html, re.DOTALL | re.I)
    return bool(m) and "process flow" in m.group(1).strip().lower()
```

The distinction that matters: **"not a Process Flow page" is an error** (you asked the wrong
question — almost always a wrong `Ver_Id`), while **"a Process Flow page with no JSON" is a real
answer** — this item type genuinely has no configured workflow. `DMS` is a legitimate example: it
returns the same empty page as a bogus code, because documents use revisions and routing rather
than a state workflow. You cannot distinguish "no workflow" from "unknown code" — say both in the
message.

---

## Reference implementation

`backend/orcanos_workflow.py` in the **Orcanos QMS** project: session caching with a 15-minute TTL,
one retry on the expired-session signature, the title guard, `[Default Status]` handling, and a
prompt formatter that surfaces signature gating per transition. It is wired into the agent runtime
as the read-only `orcanos_get_workflow` tool; the comparison rubric lives beside it as the
`workflow_sop_conformance` entry in `backend/agent_catalog.py`'s `SKILL_CATALOG`.

---

## Why this matters for compliance work

The workflow is the half of a QMS process that the eForm cannot show you. An eForm gap analysis
answers *"can we record it?"*; the workflow answers *"does the tool make us do it, in order, with
the approvals the procedure promises?"* The highest-value finding this data supports:

> The SOP says QA must approve the CAPA plan before implementation. The transition
> `QA Review -> CAPA Plan Approved - Implementation` carries `process_name: ""`.
> **The approval is procedural only — the tool does not enforce it.**

That is a defensible audit finding, and `process_name` is the only place it is visible.

---

## See also
- [`orcanos-api`](../orcanos-api/SKILL.md) — base URL, tenant path, the `/web/` deep-link conventions
- [download-attachment.md](../orcanos-api/get-section-data/download-attachment.md) — the same forms-auth session pattern, verified separately
- [qw-get-item-add-edit.md](../orcanos-api/qw-get-item-add-edit.md) — the eForm side of the same comparison
