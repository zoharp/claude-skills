# QW_Login — Orcanos Authentication

## Endpoint

```
POST <base>api/v2/Json/QW_Login
Authorization: Basic <base64(username:password)>
Content-Type: application/json
(empty body — no JSON needed)
```

**Example:**
```
POST https://app.orcanos.com/orca60/api/v2/Json/QW_Login
```

**Auth:** Use **Basic HTTP Auth** — see [main skill](SKILL.md) for encoding details (UTF-8 safe base64, API key alternative).

---

## Success Response

**CRITICAL:** `Data.Projects` is NOT a plain array. It's XML-to-JSON wrapped: `{"Project": [...]}`. The actual array is at `Data.Projects.Project`.

```json
{
  "IsSuccess": true,
  "Data": {
    "User_details": {
      "User_name": "orca",
      "Display_name": "Zohar Peretz",
      "Virtual_dir": "orca60",
      "Is_admin": "1",
      "Add_workitem": "1"
    },
    "Projects": {
      "Project": [
        {
          "Id": "14667",
          "Project_name": "Agile SCRUM",
          "Is_solution": "0",
          "Display": "Y",
          "Version": [
            {
              "Ver_id": "438",
              "Version_label": "1.0",
              "List_label": "Agile SCRUM (1.0.0)",
              "Is_lock": "N"
            }
          ],
          "Item_type": [
            { "Code": "REQ",    "Label": "Product Requirement", "Permission": "DUOTAYXBF" },
            { "Code": "T_CASE", "Label": "Test Case",           "Permission": "DUOTYXABF" },
            { "Code": "DEFECT", "Label": "Defect",              "Permission": "AUTB" }
          ]
        }
      ]
    },
    "Configurations": {
      "Idle_time": "45"
    }
  }
}
```

### What to extract

| Field | Use | Notes |
|---|---|---|
| `User_details.Virtual_dir` | Build tenant path for all future calls | e.g. `orca60` |
| `User_details.Display_name` | Display to user | |
| `User_details.Is_admin` | ⭐ Orcanos administrator flag (`0`/`1`) | **Present even when `User_details.Permission` is absent.** Distinct from the per-type `Permission` letters — gate *admin-only module writes* on this, not on `A`/`O`. See **Admin flag** below |
| `Projects.Project[]` | Populate project selector | See extraction pattern below |
| `Project.Item_type[].Code` | **Original work-item code** | ⭐ This is the ORIGINAL code — use it for `QW_AddRelation` (see below) |
| `Project.Item_type[].Label` | Human label for the type | e.g. `Product Requirement` |
| `Project.Item_type[].Permission` | ⭐ Gate Add/Edit/Delete **for that type in that project** | Compact letter string, e.g. `DUOTAYXBF`. **This is where permissions live** — see **Permissions** below |
| `Configurations.Idle_time` | Session timeout (minutes) | Warn user before expiry |

### Extract projects safely

```js
const raw = data.Data?.Projects;
let projectList = [];
if (Array.isArray(raw)) {
  projectList = raw;
} else if (raw?.Project) {
  projectList = Array.isArray(raw.Project) ? raw.Project : [raw.Project];
}

// Normalize: expand multi-version projects
const projects = [];
for (const p of projectList) {
  const versions = Array.isArray(p.Version) ? p.Version
    : p.Version ? [p.Version] : [];
  
  if (versions.length <= 1) {
    projects.push({
      ...p,
      Version_id: versions[0]?.Ver_id ?? p.Id
    });
  } else {
    // Multi-version: create a row per version
    for (const v of versions) {
      const label = v.Version_label || '';
      projects.push({
        ...p,
        Version_id: v.Ver_id,
        Project_name: label ? `${p.Project_name} (${label})` : p.Project_name
      });
    }
  }
}
return projects;
```

**Key insight:** `Version_id` (from `Version[N].Ver_id`) is what you pass to `QW_Get_Filter_Results`, NOT the project `Id`.

---

## ⭐ Work-item type code (for building relation keys)

`Project.Item_type[].Code` (e.g. `T_CASE`, `SRS`, `REQ`) is the code to build relation keys from —
but it is resolved by **`QW_Add_Relations_Custom_Code`**, **not** `QW_AddRelation`.

> ✅ **Verified (orca60, 2026-07-10):** a key like `T_CASE-26470` / `SRS-26469`, built from
> `Item_type[].Code` + the item's numeric id, **works with `QW_Add_Relations_Custom_Code`** and is
> **rejected by `QW_AddRelation`** (which wants a different, true-original code). So treat
> `Item_type[].Code` as the code for the **custom-code** relation endpoint.

To build a relation key:

1. Take the item's **numeric id** — from `QW_Add_Object`'s returned `Data`, or the number in a
   displayed key (`SR-19832` → `19832`).
2. Prefix it with the type's `Code` → `T_CASE-26470`, `SRS-19832`.

```js
const key = `${itemTypeCode}-${numericId}`;   // use as Source/TargetIdKeys with QW_Add_Relations_Custom_Code
```

Because each configured level already stores its `Item_type.Code`, the code for any item in that
level is known without an extra lookup. See [qw-add-trace.md](qw-add-trace.md).

---

## Permissions

> 🛑 **CRITICAL — permissions are PER WORK-ITEM TYPE, PER PROJECT. There is no reliable global flag.**
> The authoritative field is **`Data.Projects.Project[].Item_type[].Permission`** — one compact
> letter string on **each** `Item_type` entry, e.g. `"DUOTAYXBF"`. A user can Add *Product
> Requirement* but not *Defect* in the same project, and their rights differ across projects.
> To gate an action on a specific type, read **that `Item_type`'s** `Permission`, in **that project**.
>
> ❌ **Do NOT gate on `User_details.Permission`.** On many tenants that field is **absent/null**
> (verified orca60, 2026-07-15 — it does not exist; `Is_admin` and `Add_workitem` do). Reading it
> yields "unknown" and, worse, **unioning every type's letters into one global flag is a security
> breach**: it shows a ＋ Add for a type the user cannot add, because *some other* type granted `A`.

A letter's **presence** grants that permission; its absence denies it. Order is not significant —
decode by testing whether each letter is in the string.

> ✅ **Verified (orca60, 2026-07-15):** `User_details.Permission` is **absent**. Per-type letters:
> `Product Requirement` = `"DUOTAYXBF"` (Add ✓), `Test Case` = `"DUOTYXABF"` (Add ✓),
> `Defect` = `"AUTB"` (Add ✓, no Delete). Values vary by type **and** by project.

### Gate a specific type in a specific project (the correct pattern)

```js
// Build a lookup: { [projectId]: { [typeCode]: permString } } from QW_Login.
function buildTypePermissions(loginData) {
  const out = {};
  const projects = ensureArray(loginData?.Data?.Projects?.Project);
  for (const p of projects) {
    const pid = String(p.Id);
    out[pid] = {};
    for (const it of ensureArray(p.Item_type)) {
      if (it.Code) out[pid][it.Code] = (it.Permission || '').toUpperCase();
    }
  }
  return out;
}

// Can this user ADD `typeCode` in `projectId`?  Fail-OPEN on unknown (missing field):
// Orcanos still enforces on the real QW_Add_Object call, so an undetected field degrades
// to "allowed" rather than hiding the button for everyone.
function canAddType(typePerms, projectId, typeCode) {
  const perm = typePerms?.[String(projectId)]?.[typeCode];
  if (perm == null) return true;           // unknown -> don't restrict
  return perm.includes('A');               // 'A' = Add
}
```

### Letter → permission map

| Letter | Permission |
|---|---|
| `D` | Delete |
| `U` | Edit |
| `A` | Add |
| `R` | Execute Test |
| `E` | Execute Test Case |
| `F` | Force Checkout |
| `B` | Force Branch |
| `X` | Start Routing |
| `Y` | Cancel Routing |
| `T` | Change Traceability for Freeze |
| `O` | Enable Ask Paul |
| `L` | Allow to Launch Training |

### Decode the permission string

```js
const PERMISSION_MAP = {
  D: 'Delete',
  U: 'Edit',
  A: 'Add',
  R: 'Execute Test',
  E: 'Execute Test Case',
  F: 'Force Checkout',
  B: 'Force Branch',
  X: 'Start Routing',
  Y: 'Cancel Routing',
  T: 'Change Traceability for Freeze',
  O: 'Enable Ask Paul',
  L: 'Allow to Launch Training',
};

// Decode a permission string like "DUAR" into a set of names
function decodePermissions(permStr = '') {
  const chars = new Set(permStr.toUpperCase());
  return Object.entries(PERMISSION_MAP)
    .filter(([letter]) => chars.has(letter))
    .map(([, name]) => name);
}

// Gate on a SPECIFIC type's letters (permStr = that Item_type's Permission, in that project)
const canAdd = (permStr = '').toUpperCase().includes('A');    // Add
const canEdit = (permStr = '').toUpperCase().includes('U');   // Edit
const canDelete = (permStr = '').toUpperCase().includes('D'); // Delete
```

**Usage in this app:** the matrix inline ＋ Add gates on the Add (`A`) permission **of the exact type
being created, in that block's project** — `Item_type[].Permission` for `(project_id, work_item_type)`
— not a global flag. Every ＋ Add (L1 root, child cells, graph focus-strip add) resolves its target
block's `(project_id, type_code)` and hides the button when that type's letters lack `A`. The backend
re-checks the same per-type letters at `add-item` time (fresh `QW_Login`) and returns **403** — the UI
gate alone is never trusted. Unknown/absent letters **fail open** (Orcanos still enforces on the real
`QW_Add_Object`). See the app's Critical Note #11.

---

## Admin flag (`Is_admin`) — a SEPARATE, coarser gate

`Data.User_details.Is_admin` (`0`/`1`) is the Orcanos **administrator** flag. It is **not** one of the
`Item_type[].Permission` letters and must not be confused with them:

- **It is present even when `User_details.Permission` is absent** (verified orca60). So on tenants where
  the per-type letters are the only permission signal, `Is_admin` is still there and reliable.
- Use it to gate **admin-only areas / whole-module writes**, not individual item Add/Edit/Delete (those
  are the per-type letters above). In this app it gates **Product Knowledge + AI-prompt writes** (create/
  edit/delete products & sources, generate the document, manage prompts) — read access stays open to all.
- **Gate it FAIL-CLOSED**, opposite to the per-type letters: a missing/`0` value ⇒ **read-only**. Curation
  should lock down on uncertainty, not open up.

```js
// Tolerant read — Orcanos may send 1 (int), "1", "true", or "Y".
function isAdmin(loginData) {
  const v = loginData?.Data?.User_details?.Is_admin;
  if (typeof v === 'boolean') return v;
  if (typeof v === 'number') return v === 1;
  if (typeof v === 'string') return ['1', 'true', 'yes', 'y'].includes(v.trim().toLowerCase());
  return false;   // missing => NOT admin (fail closed)
}
```

Server side, capture it at login, persist it on the session, and **re-check on every write endpoint** — the
UI hiding the button is never the control. See the app's Critical Note #20.

---

## Failure Responses

| HTTP | Condition | Fix |
|---|---|---|
| `401` | Bad credentials | Verify username/password |
| `200` + `IsSuccess: false` | Auth rejected at application level | Check `data.Message` |
| `404` | Missing tenant path in URL | URL must include tenant: `/orca60/api/v2/Json` |

---

## Full Example (JavaScript + Proxy)

```js
// Via FastAPI backend proxy
const BASE = '/api/orcanos/';

// Use utf8ToBase64() from main skill docs to handle non-ASCII characters
async function login(username, password) {
  const auth = 'Basic ' + utf8ToBase64(`${username}:${password}`);
  const r = await fetch(BASE + 'login', {
    method: 'POST',
    headers: { Authorization: auth, 'Content-Type': 'application/json' },
  });
  
  if (r.status === 401) throw new Error('Bad credentials');
  const data = await r.json();
  if (!data.IsSuccess) throw new Error(data.Message || 'Login failed');
  
  // Save auth for future calls
  sessionStorage.setItem('auth', auth);
  sessionStorage.setItem('tenant', data.Data.User_details.Virtual_dir);
  
  return {
    user: data.Data.User_details,
    projects: extractProjects(data.Data),
    idleTimeMinutes: parseInt(data.Data.Configurations.Idle_time, 10)
  };
}
```

---

## See also
- [Main Skill](SKILL.md) — Base URL, auth, common patterns
