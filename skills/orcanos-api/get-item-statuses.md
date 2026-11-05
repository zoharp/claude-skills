# Full Status List for an Item Type — GetSystemTable + GetSystemTableValues

`QW_Get_Item_Add_Edit` returns, for the `Status` field, **only the statuses reachable from the item's
CURRENT state** (the workflow's allowed next states) — never the whole list. So it cannot be used to
map statuses (e.g. "which of our CAPA statuses is the closed one?"). Every item type instead has a
**status system table** holding *all* its statuses, and `GetSystemTableValues` reads it.

**Verified live on orca60, 2026-10-15** (Basic auth, read-only). Concretely: the Software Requirement
**Add** form's status field (`name: "Obj_status"`, `ws_add_col_name: "Status"`, `type: combobox`) offered
**2** statuses (New, Under Review); `REF_SRS_STATUS` holds **5** (+ Approved, Reopen, Reviewed).

**Used in production:** traceability-matrix `OrcanoClient.get_item_statuses()` → the Integrations
(Jira) status value-mapping (`GET /api/integrations/{id}/orcanos/fields` replaces the `Obj_status`
options with the full table, keeping any form label not in it, and flags `all_statuses: true`).

Other tables found by the same `"<label> Status"` rule: `REF_DEFECT_STATUS` (11), `REF_CAPA_STATUS` (6),
`REF_SRS_STATUS` (5), `REF_T_CASE_STATUS` ("Test Case Status", 3).

---

## The two calls

Both are `GET`, no `QW_` prefix, base is `<base>/api/v2/Json`. Auth: see [SKILL.md](SKILL.md).

### 1. Resolve the table code — `GetSystemTable`

The status table is described as **`<Work Item Name> Status`** (e.g. "CAPA Status", "Complaint Status").
Its **code is NOT derivable from the name** — `REF_CAPA_STATUS`, `REF_COMP_STATUS`, `REF_CA_STATUS`,
`REF_DEFECT_STATUS` — so look it up:

```
GET <base>/api/v2/Json/GetSystemTable?PageNo=1&PageSize=100&Description=CAPA%20Status
```

```json
{ "TotalRecords": 1, "CurrentPage": 1, "PageSize": 100,
  "SystemTables": [ { "TableName": "REF_CAPA_STATUS", "Description": "CAPA Status",
                      "UserTable": 1, "RelinkTableName": "OBJECTS", "IsCustom": 0,
                      "IsEdit": 0, "IsDelete": 0, "IsView": 1 } ] }
```

`Description` is a **contains** match (`Description=Status` returns all 87 status-ish tables), so pick the
row whose `Description` equals `"<item type label> Status"` case-insensitively; never take row 0 blindly.
No match → that item type has no dedicated status table (report it, don't guess a code).

### 2. Read every status — `GetSystemTableValues`

```
GET <base>/api/v2/Json/GetSystemTableValues?TableName=REF_CAPA_STATUS&PageNo=1&PageSize=100
```

```json
{ "TotalRecords": 6, "CurrentPage": 1, "PageSize": 100, "IsObjStatus": 1, "IsEdit": 1, "IsTableEdit": 0,
  "SystemValues": [
    { "Code": "NEW",        "Description": "New",                "IsDefault": 1, "ItemOrder": 0, "IsActive": 1,
      "IsComplete": 0, "IsFreeze": 0, "UserDefinitionCode": 0, "ShowInGrid": 0, "EarnedValue": 0,
      "Color": 16554839, "IsEdit": 1, "IsDelete": 1 },
    { "Code": "IN_PROCESS", "Description": "CAPA Investigation", "ItemOrder": 1, "UserDefinitionCode": 1, "...": "..." },
    { "Code": "CODE_2",     "Description": "CAPA Closed - Effectiveness Verified", "ItemOrder": 5,
      "IsActive": 0, "IsComplete": 1, "...": "..." } ] }
```

`IsObjStatus: 1` marks a table that backs a work item's status field.

---

## Traps (all observed)

1. **`TableName` must be the code.** `TableName=CAPA Status` → HTTP **400** `{"Message":"Enter a valid TableName."}`.
   An unknown code gives the same 400 (not an empty list).
2. **`Code` ≠ label, and the codes are legacy.** CAPA's "QA Review" has `Code: "DONE"`, "CAPA Plan Approved -
   Implementation" has `Code: "VERIFIED"`, later ones are `CODE_1`, `CODE_2`. The **`Description`** is what
   users see and what `QW_Update_Object` / `QW_Add_Object` take (picklists take labels — see
   [qw-update-item.md](qw-update-item.md)). Map on `Description`; keep `Code` only as the stable id.
3. **Do not filter on `IsActive` when mapping.** In this CAPA table the *final* status ("CAPA Closed -
   Effectiveness Verified") has `IsActive: 0` and `IsComplete: 1`. Dropping inactive rows loses the closed
   state. Return all rows with the flags; filter only when building a "pick a status to move to" picker.
4. **Terminal state = `IsComplete: 1`**, not the last `ItemOrder` and not a status named "Closed".
   `IsFreeze: 1` = the item locks.
5. **Order by `ItemOrder`** (starts at 0 in one table, 1 in another — only the relative order matters).
   ⚠️ It can be **0 on every row** (orca60 `REF_DEFECT_STATUS`, `REF_SRS_STATUS`, 2026-10-15) — then
   the order is meaningless and the rows come back alphabetical; never read "last row = final state".
6. **`Color` is an integer**, not hex text (`16554839`). It is not the "hex without `#`" the older
   [get-system-table-values.md](get-system-table-values.md) said; treat it as an OLE-style colour int.
7. **The table is the full set; the workflow is the reachable set.** This answers "what statuses exist".
   For "which transitions are allowed, and which e-signature gates them" use
   `orcanos-workflow-chart` (states + transitions are UI-only, no API).
8. Page through `TotalRecords` if > 100 (never seen for a status table, but cheap to loop).

---

## Reference implementation

```python
import base64, requests

def get_item_statuses(base, user, pwd, item_label):
    """All statuses of an item type, in workflow order. base = https://app.orcanos.com/<tenant>/api/v2/Json"""
    H = {"Authorization": "Basic " + base64.b64encode(f"{user}:{pwd}".encode()).decode()}
    want = f"{item_label} Status".strip().lower()

    r = requests.get(f"{base}/GetSystemTable", headers=H, timeout=30,
                     params={"PageNo": 1, "PageSize": 100, "Description": f"{item_label} Status"})
    r.raise_for_status()
    tables = [t for t in r.json().get("SystemTables") or []
              if (t.get("Description") or "").strip().lower() == want]
    if not tables:
        return None                                   # no dedicated status table — say so, don't guess
    code = tables[0]["TableName"]

    out, page = [], 1
    while page <= 20:
        v = requests.get(f"{base}/GetSystemTableValues", headers=H, timeout=30,
                         params={"TableName": code, "PageNo": page, "PageSize": 100})
        v.raise_for_status()
        body = v.json()
        rows = body.get("SystemValues") or []
        out += rows
        if not rows or len(out) >= int(body.get("TotalRecords") or 0):
            break
        page += 1
    return {"table": code,
            "statuses": sorted(out, key=lambda s: s.get("ItemOrder") or 0)}
```

`item_label` is the item type's **label** ("CAPA", "Complaint", "Corrective Action"), as returned in the
project's item-type list — not its code (`CA`).

## See also
- [get-system-table-values.md](get-system-table-values.md) — the generic endpoint (any system table)
- [qw-get-item-add-edit.md](qw-get-item-add-edit.md) — the form; its Status `val` is current-state-only
- [qw-update-item.md](qw-update-item.md) — writing a status (label, not code; may be e-signature-gated)
- `orcanos-workflow-chart` — transitions and the e-signature process on each

## Not on every server (2026-10-29)

`us.orcanos.com` answers `GetSystemTable` / `GetSystemTableValues` with **HTTP 404 "No HTTP resource was found"** (route missing from that build; app.orcanos.com answers 401 without login = exists). A 404 here means *cannot read*, not *no table* — the traceability DHF reports it as "could not be read" (`get_item_statuses_ex`).
