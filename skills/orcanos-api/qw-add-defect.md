# QW_Add_Defect — Create a Defect

> Defects live in their **own table**, not the work-item table. So they have their own create
> method — **not** `QW_Add_Object` — with its own field names. It behaves like `QW_Add_Object`
> otherwise (one call, standard fields + up to 60 custom-field pairs).

## Endpoint

```
POST <base>/api/v2/Json/QW_Add_Defect
Authorization: Basic <base64(username:password)> OR OrcanosAPIKey: <key>
Content-Type: application/json
```

`<base>` includes the tenant, e.g. `https://app.orcanos.com/orca60`.

**Spec sources:** knowledgebase https://help.orcanos.com/knowledgebase/qw_add_defect-rest-api/ ·
Swagger `…/api/swagger/docs/v1` (model `Defects`).
**Update sibling:** [QW_Update_Defect](qw-update-defect.md).

> ✅ **Verified live** on orca60, 2026-10-18 (project *Agile SCRUM* 14667, version 1.0 / `Ver_id` 438;
> created DEFECT-2852 and DEFECT-2853).

---

## ⚠️ How it differs from `QW_Add_Object`

| | `QW_Add_Object` | `QW_Add_Defect` |
|---|---|---|
| Project | `Project_ID` (number) | **`Project_Name`** (the project's **name**, e.g. `"Agile SCRUM"`). `Project_ID` is ignored → `Project not found.` |
| Name | `Object_Name` | **`Synopsis`** |
| Type | `Object_Type` (label) | none — the method *is* the type |
| Assignee | optional | **required** — omitting it fails (`User  (Assigned to) is not in the project.`) |
| Extra fields | — | `Severity`, `Defect_type`, `Found_version`, `Fixed_version`, `Target_version`, `Solution`, `Work_around` |
| Integration refs | `Migration_Reference`, `External_ID` | **`MigrationReference`**, **`external_id`** (different spelling) |

`Project_Name` comes from `QW_Login` → `Projects.Project[].Project_name`. The version is
`Major_Version` + `Minor_Version` from the version **label** (`"1.0"` → `1`, `0`), like `QW_Add_Object`.

---

## Request Body (minimal — every field here is required)

```json
{
  "Project_Name": "Agile SCRUM",
  "Major_Version": 1,
  "Minor_Version": 0,
  "Synopsis": "Login button does nothing on Safari",
  "Description": "<p>Steps: …</p>",
  "Assigned_to": "orca"
}
```

## All fields (Swagger `Defects`)

| Field | Type | Notes |
|---|---|---|
| `Project_Name` | string | **Required.** Project **name** |
| `Major_Version`, `Minor_Version` | int | **Required.** From the version label |
| `Release_Release` | int | In Swagger, not in the KB — untested |
| `Synopsis` | string | **Required.** The defect's title |
| `Description` | string | **Required.** Plain text or HTML |
| `Assigned_to` | string | **Required.** User name (`"orca"`); must be in the project |
| `Parent_ID` | string | Parent item; defaults to the project (pool) |
| `Defect_type` | string | `Internal` (default) / `External` (customer-reported) |
| `Severity`, `Priority`, `Category`, `Status` | string | Picklist **labels** (`"High"`, `"3 - High"`, `"Gui"`). Defaults from the system tables / workflow |
| `Found_version`, `Fixed_version`, `Target_version` | string | Format `99.99.999.9999`, e.g. `"01.02.000.0000"` |
| `Solution` | string | Shown on the form as **"Fixes"** (on update the key is `Fixes`) |
| `Work_around` | string | "Work Around" |
| `Created_date`, `Created_by`, `Start_date`, `Due_date`, `Effort_estimation` | string | Dates in the server's format (orca60: `dd/mm/yyyy`) |
| `CS1_Name`…`CS60_Name` / `CS1_value`…`CS60_value` | string | Custom fields — **title** in `_Name`, value in `_value` |
| `MigrationReference`, `external_id`, `SpecialCustomFields` | string | Integration references |

### What the server filled in (verified)

With only the minimal body: Status `Open`, Severity `Not set`, Priority `- Not Set -`,
Category `Performance` (the tenant's default), **Found Version = the project version
(`01.00.000.0000`)**, Fixed/Target Version `00.00.000.0000`, Detected By = calling user.

### Custom fields — same rule as QW_Add_Object

`CS<n>_Name` = the field **title** (from `QW_Get_Item_Add_Edit`, e.g. `"JIRA ID"`), `CS<n>_value` =
the value. A picklist custom field takes the option **label** (`"Is Risk Invloved": "No"` ✅).
A value put in `CS1_Name` fails: `Custom field PROJ-9 not found.`

---

## Response

```json
{ "IsSuccess": true, "Data": 2852, "Message": "Defect created successfully.", "HttpCode": 200 }
```

`Data` is the new defect's id; its key is `DEFECT-<Data>`. Errors come back **HTTP 200** with
`IsSuccess: false`, `HttpCode: 500`, and the reason in `Message` (also in `Data.ErrorInfo`). The
message often starts with a newline — `.strip()` it.

## Errors seen (all live)

| Message | Cause |
|---|---|
| `Project not found.` | Wrong `Project_Name`, **or** `Project_ID` sent instead of `Project_Name` |
| `User  (Assigned to) is not in the project.` | `Assigned_to` missing/empty |
| `User nobody_here (Assigned to) is not exist.` | Unknown user name |
| `Defect severity not found.` | `Severity` not a valid value |
| `Defect description cannot be empty.` | `Description` empty or missing — send at least the synopsis |
| `Custom field <X> not found.` | `CS<n>_Name` is not a field title |

---

## Reading the defect back

- ✅ `QW_Get_Item_Add_Edit` with `Item_Type: "DEFECT"`, `Item_id`, `Project_id`, `VersionId` —
  every field incl. custom ones, with `title` + `Text`. **Use this.**
- ⚠️ `QW_Get_Object_View` (`Item_Type: "DEFECT"`, `Ver_Id`) works but shows `Description` as
  `![CDATA[]]` even when it is set.
- ❌ `QW_Get_Object/<id>` answers `IsSuccess: true` with an **empty `Field[]`** — it reads the
  work-item table, not the defect table.

---

## Full Example (Python)

```python
def add_defect(api_url, auth, project_name, version_label, synopsis, description, assignee, **extra):
    major, minor = (int(x) for x in version_label.split(".")[:2])
    body = {"Project_Name": project_name, "Major_Version": major, "Minor_Version": minor,
            "Synopsis": synopsis, "Description": description, "Assigned_to": assignee, **extra}
    data = requests.post(f"{api_url}/QW_Add_Defect", json=body,
                         headers={"Authorization": auth, "Content-Type": "application/json"}).json()
    if not data.get("IsSuccess"):
        raise RuntimeError((data.get("Message") or "Add defect failed").strip())
    return data["Data"]   # numeric id → key DEFECT-<id>

# add_defect(api, auth, "Agile SCRUM", "1.0", "Crash on save", "<p>…</p>", "orca",
#            Severity="High", CS1_Name="JIRA ID", CS1_value="PROJ-9")
```

## See also
- [QW_Update_Defect](qw-update-defect.md) — change an existing defect
- [QW_Add_Object](qw-add-item.md) — create any *other* work item
- [QW_Get_Item_Add_Edit](qw-get-item-add-edit.md) — field titles, picklist labels, read-back
- [QW_Login](qw-login.md) — project names and version labels
