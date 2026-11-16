---
name: azure-devops-api
description: Azure DevOps Services REST API (work items, WIQL, fields, service hooks, identities) as used by the Orcanos Integrations connector. Use when writing or debugging code that calls dev.azure.com — auth with a PAT, JSON Patch writes, WIQL polling, service-hook subscriptions.
---

# Azure DevOps REST API (Services, api-version 7.1)

Used by traceability-matrix `src/backend/azure_devops_client.py` (Integrations connector, 2026-11-09).
**Status: everything below is from Microsoft's REST docs and exercised only against a FAKE dev.azure.com
(`tests/test_integrations_ado.py`). Nothing has been verified live yet** — update this file after the first
live run (mark each item *verified live YYYY-MM-DD*).

See also: `orcanos-api` (the Orcanos side of every integration), traceability-matrix Critical Note #126,
`design/docs/INTEGRATIONS.md` §12.

## Base, auth, versions

- Org base: `https://dev.azure.com/{org}` (legacy `https://{org}.visualstudio.com` = same org). Identity API is on
  `https://vssps.dev.azure.com/{org}`. Azure DevOps **Server** (on-prem) is a different host the admin types — not supported.
- Every call: `?api-version=7.1` (connectionData: `7.1-preview`).
- PAT auth: `Authorization: Basic base64(":" + PAT)` (empty user name). Add `X-TFS-FedAuthRedirect: Suppress`.
- ⚠️ **A bad / expired PAT is NOT a 401**: typically **203 Non-Authoritative + the HTML sign-in page** (or 302).
  Treat any 203/302 or `text/html` success as "token refused". Parsing it as JSON gives `{}` → silent empty lists.
- PAT scopes the connector asks for: Work Items (Read, write & manage) `vso.work_full`; Project and Team (Read);
  Service Hooks (Read, write & manage) `vso.hooks_write`; Identity (Read). A PAT is per org (unless "all orgs"),
  expires (max 1 year) and **cannot report its own expiry** — ask the admin to type the date.
- Rate limit: 429 + `Retry-After`; on success a `X-RateLimit-Delay` header asks you to slow down.

## Calls

| What | Call | Notes |
|---|---|---|
| Who am I | `GET {org}/_apis/connectionData` | `authenticatedUser.id`, `.providerDisplayName`, `.properties.Account.$value` (email). Answers for ANY valid token, so also list projects to prove scopes |
| Projects | `GET {org}/_apis/projects?$top=500[&continuationToken=]` | `value[] {id, name, state}`; skip `state != wellFormed` |
| Work item types | `GET {org}/{project}/_apis/wit/workitemtypes` | `value[] {name, referenceName, isDisabled}`. Hide Test Plan / Test Suite / Shared Steps / Code Review / Feedback types |
| Fields of a type | `GET {org}/{project}/_apis/wit/workitemtypes/{type}/fields?$expand=allowedValues` | `referenceName, name, alwaysRequired, defaultValue, allowedValues` — **no field TYPE here** |
| Field catalogue | `GET {org}/_apis/wit/fields` | `type` (string, plainText, html, integer, double, boolean, dateTime, treePath, identity…), `readOnly`, `isIdentity` |
| Area paths | `GET {org}/{project}/_apis/wit/classificationnodes/areas?$depth=10` | tree `{name, children[]}` → `Proj\Area\Sub` |
| Query | `POST {org}/{project}/_apis/wit/wiql?timePrecision=true&$top=500` body `{"query": "SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = @project AND [System.WorkItemType] = 'Bug' AND [System.ChangedDate] >= '2026-11-09T10:00:00Z' [AND [System.AreaPath] UNDER 'Proj\\Area'] ORDER BY [System.ChangedDate] DESC"}` | returns ids only `workItems[{id}]`. ⚠️ without `timePrecision=true` dates are DAY precision. Single quotes doubled inside strings |
| Read many | `POST {org}/_apis/wit/workitemsbatch` body `{"ids":[…≤200], "$expand":"Relations", "errorPolicy":"Omit"}` | `value[]` full items |
| Read one | `GET {org}/_apis/wit/workitems/{id}?$expand=relations` | `{id, rev, fields{…}, relations[], _links.html.href}`; 404 if deleted |
| Create | `POST {org}/{project}/_apis/wit/workitems/${type}` `Content-Type: application/json-patch+json` body `[{"op":"add","path":"/fields/System.Title","value":"…"}, …]` | returns the item |
| Update | `PATCH {org}/_apis/wit/workitems/{id}` same JSON Patch | `add` on a field REPLACES; optional `{"op":"test","path":"/rev","value":N}` for concurrency (not used yet) |
| Link out | PATCH op `add` path `/relations/-` value `{"rel":"Hyperlink","url":"…","attributes":{"comment":"…"}}` | duplicate URL → 400; check relations first |
| Person by email | `GET https://vssps.dev.azure.com/{org}/_apis/identities?searchFilter=General&filterValue={email}&queryMembership=None` | `properties.Account.$value`; an identity field accepts the email/unique name string |
| Service hook | `POST {org}/_apis/hooks/subscriptions` body `{"publisherId":"tfs","eventType":"workitem.updated","resourceVersion":"1.0","consumerId":"webHooks","consumerActionId":"httpRequest","publisherInputs":{"projectId":"<guid>","workItemType":"Bug","areaPath":"…"},"consumerInputs":{"url":"https://…","httpHeaders":"X-Orcanos-Token:<secret>","resourceDetailsToSend":"minimal"}}` | one per event: `workitem.created/updated/deleted`. Needs Service Hooks scope + project rights (else 403). Project GUID from `GET {org}/_apis/projects/{name}` |
| Hook health | `GET {org}/_apis/hooks/subscriptions/{id}` | `status`: `enabled`, `onProbation`, `disabledBySystem`, `disabledByUser`… ⚠️ ADO disables a failing hook and tells nobody — poll it |
| Remove hook | `DELETE {org}/_apis/hooks/subscriptions/{id}` | 204 |

## Payload and field quirks

- Service-hook delivery: `{eventType, resource, resourceContainers}`. For **`workitem.updated` `resource.id` is the
  REVISION id** — the work item is `resource.workItemId`. Created/deleted: `resource.id` is the work item id.
- No signature on deliveries: put a secret in `httpHeaders` (or the URL) and check it.
- A **Bug** (Agile/Scrum/CMMI) has **no Description** — body is `Microsoft.VSTS.TCM.ReproSteps`. User Story/Task use
  `System.Description`. Both are HTML.
- `System.State` values and allowed moves come from the PROCESS; an illegal move is a 400.
- `System.Tags` is one string, `"a; b"`.
- `System.AssignedTo` reads back as `{displayName, uniqueName, id}`.
- `System.ChangedDate` is UTC ISO with `Z`.
