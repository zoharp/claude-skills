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
      "Virtual_dir": "orca60"
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
            { "Code": "REQ", "Label": "Product Requirement" },
            { "Code": "T_CASE", "Label": "Test Case" }
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
| `Projects.Project[]` | Populate project selector | See extraction pattern below |
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
- [Router & Auth Patterns](SKILL.md) — Base URL, CORS, common patterns
- [QW_Get_Filter_Results](qw-get-filter-results.md) — Fetch items from a filter
