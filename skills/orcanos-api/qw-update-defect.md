# QW_Update_Defect — Update a Defect

> Defects live in their **own table**, so they need this method — **`QW_Update_Object` on a defect
> id fails** with `There is no row at position 0.` It works like `QW_Update_Object` (partial
> update, labels, custom-field pairs) but is simpler: no version and no name are needed.

## Endpoint

```
POST <base>/api/v2/Json/QW_Update_Defect
Authorization: Basic <base64(username:password)> OR OrcanosAPIKey: <key>
Content-Type: application/json
```

**Spec sources:** knowledgebase https://help.orcanos.com/knowledgebase/qw_update_defect-rest-api/ ·
Swagger `…/api/swagger/docs/v1` (model `DefectUpdate`).
**Create sibling:** [QW_Add_Defect](qw-add-defect.md).

> ✅ **Verified live** on orca60, 2026-10-18 (DEFECT-2852 / DEFECT-2853, project *Agile SCRUM*).

---

## Minimum body

```json
{ "Defect_ID": 2852, "Severity": "High" }
```

Only `Defect_ID` is required. **It is a partial update**: fields you leave out keep their
values. Unlike `QW_Update_Object`, there is **no `View_Version`** and **no name to re-send**.
`Synopsis` renames the defect only when you send it.

## Fields (Swagger `DefectUpdate`)

| Field | Type | Notes |
|---|---|---|
| `Defect_ID` | int | **Required.** The numeric id (`2852`, not `DEFECT-2852`) |
| `Synopsis`, `Description` | string | Title; body as text or HTML |
| `Severity`, `Priority`, `Category`, `Defect_type` | string | Option **labels** (`"2 - Medium"`). Severity also took the code (`"LOW"` → Low) |
| `Status` | string | Label. ⚠️ See the workflow warning below |
| `Assigned_to` | string | User name. ⚠️ An unknown name is a **silent no-op** |
| `Found_version`, `Fixed_version`, `Target_version` | string | `99.99.999.9999` |
| `Fixes`, `Work_around` | string | ⚠️ The create field is `Solution`; on update it is **`Fixes`** |
| `Updated_Date`, `Updated_By` | string | Audit stamp overrides |
| `Start_Date`, `Effort_Estimation`, `Due_date` | string | ⚠️ Swagger spells these `Start_Date` / `Effort_Estimation` (create uses `Start_date` / `Effort_estimation`). Dates in the server format — orca60 took `"25/12/2026"` |
| `CS1_Name`…`CS60_Name` / `CS1_value`…`CS60_value` | string | Custom fields — **title** + value |

### Custom fields
`{"CS1_Name": "JIRA ID", "CS1_value": "PROJ-1"}` ✅. The internal name (`"CS99"`) fails:
`Custom field CS99 not found.` A picklist custom field takes the option label (`"Yes"`).

---

## ⚠️ Status ignores the workflow

`QW_Get_Item_Add_Edit` offered only `Open` as the next status, yet `QW_Update_Defect` accepted
**`Closed` → `Fixed` → `Rejected`** in a row and saved each one. The API writes any status label
directly; it does not enforce transitions or e-signatures. A sync or tool calling it must enforce
its own rules, or it can move a defect to a state the UI never allows.

## ⚠️ Success does not always mean a change

| Sent | Result |
|---|---|
| `"Assigned_to": "nobody_here"` | `IsSuccess: true`, **assignee unchanged** (create rejects the same name) |
| `"Severity": "Bogus"` | `IsSuccess: false` — `QPack cannot find the specified severity.` |

Read the defect back after updating (`QW_Get_Item_Add_Edit`, `Item_Type: "DEFECT"`) before you
report success. See [qw-add-defect.md → Reading the defect back](qw-add-defect.md#reading-the-defect-back).

---

## Response

```json
{ "IsSuccess": true, "Data": 2852, "Message": "Defect updated successfully", "HttpCode": 200 }
```

Errors come back as **HTTP 200** with `IsSuccess: false`:

| Message | Cause |
|---|---|
| `QPack could not find the object.` | No defect with that `Defect_ID` |
| `QPack cannot find the specified severity.` | Bad `Severity` |
| `Custom field <X> not found.` | `CS<n>_Name` is not a field title |
| `There is no row at position 0.` | You called **`QW_Update_Object`** with a defect id — use this method |

---

## Full Example (Python)

```python
def update_defect(api_url, auth, defect_id, **fields):
    body = {"Defect_ID": int(defect_id), **fields}
    data = requests.post(f"{api_url}/QW_Update_Defect", json=body,
                         headers={"Authorization": auth, "Content-Type": "application/json"}).json()
    if not data.get("IsSuccess"):
        raise RuntimeError((data.get("Message") or "Update defect failed").strip())
    # then read back with QW_Get_Item_Add_Edit and compare

# update_defect(api, auth, 2852, Severity="High", Fixes="Patched in 1.1",
#               CS1_Name="JIRA ID", CS1_value="PROJ-1")
```

## See also
- [QW_Add_Defect](qw-add-defect.md) — create a defect
- [QW_Update_Object](qw-update-item.md) — update any *other* work item
- [QW_Get_Item_Add_Edit](qw-get-item-add-edit.md) — titles, labels, read-back
