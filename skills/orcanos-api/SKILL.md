---
name: orcanos-api
description: Reference guide for Orcanos QMS REST API — base URL, authentication, CORS/proxy patterns, and routing to specific API skills. Start here when building Orcanos integrations.
revision: 1.0
---

# Orcanos REST API — Router & Reference

**Reference docs:** `https://help.orcanos.com/knowledgebase/`

This skill covers API fundamentals. For specific endpoint details, see the per-API skills listed below.

---

## Base URL & Endpoint pattern

All endpoints are under:
```
https://<instance>/<tenant>/api/v2/Json/<endpoint>
```

Example:
```
https://app.orcanos.com/orca60/api/v2/Json/QW_Login
https://us.orcanos.com/acme/api/v2/Json/QW_Get_Filter_Results
```

The tenant path (e.g. `orca60`, `acme`) is returned in `QW_Login` response as `User_details.Virtual_dir`.

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

### Item & Traceability Management
- **[QW_Add_Item](qw-add-item.md)** — Create or update work items (REQ, TC, DEF, etc.)
- **[QW_Add_Trace](qw-add-trace.md)** — Create traceability links between items

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

