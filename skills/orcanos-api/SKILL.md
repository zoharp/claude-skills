---
name: orcanos-api
description: Reference guide for Orcanos QMS REST API — base URL, authentication, CORS/proxy patterns, and routing to specific API skills. Start here when building Orcanos integrations.
revision: 1.1.0
---

# Orcanos REST API — Router & Reference

**Reference docs:** `https://help.orcanos.com/knowledgebase/`

**Machine-readable contract:** `https://<instance>/<tenant>/api/swagger/docs/v1` — the raw OpenAPI
JSON behind the Swagger UI (e.g. `https://app.orcanos.com/orca60/api/swagger/docs/v1`). No auth
needed, ~140 KB, every path + parameter + definition. **Pull this whenever an endpoint here is
under-documented or missing** — it's authoritative about verbs, required params and header names in
a way the knowledgebase often isn't. Note the Swagger *UI* is a SPA, so its `#!/Json/<op>` fragment
URLs can't be fetched — grep the JSON instead. (`docs/v2` 404s; the spec is `v1` even though the
routes live under `/v2/`.)

This skill covers API fundamentals. For specific endpoint details, see the per-API skills listed below.

---

## Base URL & Endpoint pattern

Most endpoints are under:
```
https://<instance>/<tenant>/api/v2/Json/<endpoint>
```

Example:
```
https://app.orcanos.com/orca60/api/v2/Json/QW_Login
https://us.orcanos.com/acme/api/v2/Json/QW_Get_Filter_Results
```

The tenant path (e.g. `orca60`, `acme`) is returned in `QW_Login` response as `User_details.Virtual_dir`.

**AI (Ask Paul) endpoints use a different sub-path** — `/api/v2/OrcanosAI/` instead of `/api/v2/Json/`:
```
https://app.orcanos.com/orca60/api/v2/OrcanosAI/Fetch_AI_Prompts
https://app.orcanos.com/orca60/api/v2/OrcanosAI/Get_AI_Response
```
Swagger UI: `https://<instance>/<tenant>/api/swagger/ui/index#!/OrcanosAI/`.

---

## Authentication

Orcanos supports two authentication methods. Choose one for all requests.

### Option 1: Basic HTTP Auth (username/password)

Used with `QW_Login` endpoint or directly with other endpoints.

**Base64 encoding (UTF-8 safe):**
```js
function utf8ToBase64(s) {
  const bytes = new TextEncoder().encode(s);
  let bin = '';
  const CHUNK = 0x8000;
  for (let i = 0; i < bytes.length; i += CHUNK)
    bin += String.fromCharCode.apply(null, bytes.subarray(i, i + CHUNK));
  return btoa(bin);
}

const authHeader = 'Basic ' + utf8ToBase64(`${username}:${password}`);
```

**Headers:**
```
Authorization: Basic <base64(username:password)>
Content-Type: application/json
```

**Non-ASCII characters:** `btoa()` alone breaks on accented usernames/passwords. **Always use the UTF-8 helper above.**

### Option 2: API Key Auth

Some Orcanos instances support API key authentication.

**Headers:**
```
Authorization: Bearer <api-key>
Content-Type: application/json
```

**Key generation:** Create API keys in Orcanos admin settings (specific to your Orcanos version).

---

## Session Management

**HTTP 401 handling:** Any endpoint can return 401 when the session expires or auth is invalid.
- Clear stored credentials
- Redirect user to re-authenticate
- For Basic Auth: re-call `QW_Login` to get a fresh session
- For API Key: verify the key is still valid in admin settings

**Session timeout (Basic Auth only):** The `QW_Login` response includes `Data.Configurations.Idle_time` (minutes). Warn user or auto-logout before expiry.

---

## Standard Headers for all Requests

```
Authorization: Basic <base64> OR Authorization: Bearer <api-key>
Content-Type: application/json
```

---

## CORS & Backend Proxy

Browser-direct calls to Orcanos fail with CORS errors — Orcanos does not send CORS headers. **Use a server-side proxy.**

The Orcanos QMS FastAPI backend proxies these endpoints:

| Backend route | Proxies to | Purpose |
|---|---|---|
| `POST /orcanos/proxy/login` | `QW_Login` | Authenticate and list projects |
| `POST /orcanos/proxy/filter` | `QW_Get_Filter_Results` | Fetch items from a saved filter |
| `GET /orcanos/auth` | — | Check saved credentials (no Orcanos call) |
| `POST /orcanos/save-creds` | — | Store encrypted credentials (no Orcanos call) |

**Debugging CORS errors:** A CORS error in the browser often masks a **backend 500** that occurred before CORS headers were injected. Check the backend logs first.

---

## API Documentation

**All API docs are in this folder. Click the file name to open:**

### Core APIs
- **[QW_Login](qw-login.md)** — Authenticate with username/password, receive projects & user details
- **[QW_Get_Filter_Results](qw-get-filter-results.md)** — Fetch items from a saved filter, with pagination & SQL filtering
- **[Filter-result fields](filter-result-fields.md)** — **the `Field[]` dictionary**: what all ~46 returned columns mean (identity, content, workflow, tree-vs-trace, revision/branching, routing/e-signature, ECO, audit), per-field `Text` semantics and blank sentinels, plus the item envelope (`Type` / `Version` / `Freeze`). ⚠️ `Order` is **alphabetical by Title**, not the column order; `Web_order` is the column order but is **not unique**; `CS<n>` field names are **tenant-specific slots** — match those on `Title`. Load when *interpreting* results; [qw-get-filter-results.md](qw-get-filter-results.md) stays the how-to-call doc
- **[GetFilterList](get-filter-list.md)** — List the saved filters a user can pick for a `(ProjectId, ItemType)` pair, to power a filter-picker dropdown. ⚠️ `ItemType` is the work-item **DESCRIPTION/Label** ("Software Requirement"), **not** the code (`SRS`) — the code returns an empty list, not an error. ⚠️ Optional per tenant — a bare JSON array (no `IsSuccess` wrapper); treat a 404 / non-array as "not available" and fall back to a manual filter-ID input
- **[GetSystemTableValues](get-system-table-values.md)** — The **values of one system table** (the picklist source behind combo-box / multi-select custom fields), paged. ⚠️ A **`GET` with query params**, not a POST body; **no `QW_` prefix**. Required param is `TableName` (the *table's* code) — `Code` is a separate optional filter on a single *value*. Keep `PageSize` in **1–100** and pass `PageNo` explicitly. Also covers the sibling `GetSystemTable` (list the tables) and `SystemTableValue_Get` (⚠️ body property is misspelled `TabelName`)

### Item & Traceability Management
- **[QW_Add_Object](qw-add-item.md)** — Create a work item (⚠️ the method is `QW_Add_Object`; `QW_Add_Item` does not exist / 404s)
- **[QW_Add_Relations_Custom_Code / QW_AddRelation](qw-add-trace.md)** — Create a traceability link. Use `QW_Add_Relations_Custom_Code` for keys built from `Item_type.Code` / displayed codes; `QW_AddRelation` only accepts true original codes
- **[QW_Get_Object_Relations](qw-get-object-relations.md)** — Read an item's relations (edge ids only), incl. items outside a filter's scope. Cycle-safe recursive expansion pattern included
- **[QW_Get_Object](qw-get-object.md)** — Fetch a single item's full field details by id (path form `QW_Get_Object/<id>`). Powers item info cards / hover previews and enriches a relations id into a named node
- **[Get_Children](get-children.md)** — An item's **direct children** (the containment/outline tree, *not* trace links), pre-enriched with Name/Type/Status/`ItemURL`. ⚠️ Method has **no `QW_` prefix**; a child's `Ver_Id` can differ from the parent's — recurse with the child's own version and use the returned `ItemURL` as-is
- **[QW_Add_Step](qw-add-step.md)** — Append a test step (action + expected result) to a test case; call once per step in order
- **[QW_Get_Item_Add_Edit](qw-get-item-add-edit.md)** — Fetch an item type's Add/Edit **form definition**: fields, sections, display order, picklist values, and mandatory/conditional-mandatory rules. Use to render a dynamic form or validate a payload before `QW_Add_Object`

### AI — Ask Paul (base path `/api/v2/OrcanosAI/`)
- **[Fetch_AI_Prompts](ai-fetch-prompts.md)** — List Create-&-Trace AI prompts; pick `AI_Prompt_Id` by matching source `item_type` label + child keyword (e.g. "Test Case")
- **[Get_AI_Response](ai-get-response.md)** — Run a prompt on a source item → draft children (Name+Description); then create & trace them via `QW_Add_Object` + `QW_Add_Relations_Custom_Code`. Gated on the `O` ("Enable Ask Paul") permission from `QW_Login`

### Additional APIs
Add more as needed (remaining ~96 APIs):
- `qw-create-project.md`
- `qw-update-item.md`
- `qw-get-item.md`
- ... etc

---

## XML-to-JSON quirks

Orcanos returns XML that is converted to JSON. This causes a common gotcha:

- **Arrays of one element** arrive as a single object, not a 1-element array
- **All arrays** arrive wrapped in a named key: `"Projects": { "Project": [...] }` not `"Projects": [...]`

**Safe extraction pattern (JavaScript):**
```js
function ensureArray(val) {
  if (Array.isArray(val)) return val;
  if (val == null) return [];
  return [val];  // single object → [object]
}

// Usage:
const projects = ensureArray(data.Data?.Projects?.Project);
```

---

## Common patterns

### Store credentials securely
Do not store plaintext passwords in localStorage. In the QMS project:
1. Call `POST /orcanos/proxy/login` with credentials
2. On success, call `POST /orcanos/save-creds` with URL + username
3. Backend encrypts and stores in `accounts` table
4. Frontend clears plaintext password from memory

### Extract field values by name or title
Items return a `Field` array. Fields can have different internal names across item types:

```js
function fieldValue(item, nameOrTitle) {
  const f = item.Field?.find(f => f.Name === nameOrTitle || f.Title === nameOrTitle);
  return f?.Display_text || f?.Display || f?.Text || f?.Value || '';
}
```

Prefer `Display_text` for picklists — it shows the human label instead of the internal id.

### Parse item IDs
The `Id` field is a string like `"46584 (42195)"` — the parenthetical number is the canonical id:

```js
const id = String(itemId).match(/\((\d+)\)/)?.[1];
```

### Build web URLs
```js
function itemUrl(baseUrl, versionId, type, itemId) {
  return `${baseUrl}web/${versionId}/items/view?Item=${encodeURIComponent(type)}&ItemId=${encodeURIComponent(itemId)}`;
}
```

---

## Error handling

| HTTP | Meaning | Action |
|---|---|---|
| `401` | Session expired | Clear auth, redirect to login |
| `404` | Endpoint not found (or missing tenant path) | Verify base URL includes tenant |
| `200` + `IsSuccess: false` | API-level error | Check `data.Message` or `data.Data` |

---

## See also
- API reference: https://help.orcanos.com/knowledgebase/
- Rate limits: (check documentation)
- Orcanos QMS project backend proxy: `backend/api.py`
- [`orcanos-form-builder`](../orcanos-form-builder/SKILL.md) — builds a rendered Add/Edit form (mockup or real React screen) from `QW_Get_Item_Add_Edit`, using this skill for the API call

