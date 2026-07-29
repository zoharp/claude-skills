# Get_AI_Response — Run Ask Paul on an Item

Sends one source item + a chosen prompt to the LLM ("Ask Paul") and returns generated child
items (e.g. up to 5 test cases from a software requirement). With the **Create & Trace** prompts,
the intent is to then create those children in Orcanos and trace them back to the source.

> ⚠️ **Base path is `/api/v2/OrcanosAI/`** (not `/api/v2/Json/`).

## Endpoint

```
GET <base>/api/v2/OrcanosAI/Get_AI_Response
    ?ItemId=26469&ItemType=SRS&VersionId=438&AI_Prompt_Id=5&IsTechUser=0
Authorization: Basic <base64(username:password)> OR Bearer <api-key>
OrcanosAPIKey: <api-key>   (alternative header)
```

`<base>` includes the tenant, e.g. `https://app.orcanos.com/orca60`.

**Auth:** See [main skill](SKILL.md). **Prerequisites:**
- [QW_Login](qw-login.md) — for `VersionId` (`Version[].Ver_id`) and the type `Code`; also gates on
  the **`O` ("Enable Ask Paul")** permission.
- [Fetch_AI_Prompts](ai-fetch-prompts.md) — for `AI_Prompt_Id`.

> **Latency:** this is a live LLM call — expect several seconds. Call it off-thread / with a
> generous timeout and a spinner, not on a fast request path.

---

## Query parameters (verified against swagger, orca60)

| Param | In | Type | Required | Notes |
|---|---|---|---|---|
| `ItemId` | query | integer | **Yes** | Numeric id of the **source** item (the record Ask Paul reads). Parse from a displayed key `SRS-26469 (26470)` → the canonical number |
| `ItemType` | query | string | **Yes** | The source item's **original code** (e.g. `SRS`, `REQ`, `RISK`) — the `Item_type[].Code` from `QW_Login`, **not** the human label the prompt lists |
| `VersionId` | query | integer | **Yes** | The item's version — `Version[].Ver_id` from `QW_Login` (⚠️ not in the original brief; it's required) |
| `AI_Prompt_Id` | query | integer | **Yes** | `ID` of the chosen prompt from [Fetch_AI_Prompts](ai-fetch-prompts.md) |
| `IsTechUser` | query | integer | **Yes** | `0` for normal use |
| `prompt` | query | string | No | Override / free-text prompt (leave empty to use the stored prompt template) |

### Mapping the brief's inputs → params

| Brief said | Param |
|---|---|
| item id | `ItemId` |
| itemtype — the original code | `ItemType` (the `Code`, e.g. `SRS`) |
| prompt id (matched entry) | `AI_Prompt_Id` |
| istechuser=0 | `IsTechUser=0` |
| *(implicit)* | `VersionId` — **also required**, from `QW_Login` |

---

## Response

Swagger only declares `{"type":"object"}`, but the **live orca60 shape is verified (2026-07-11)**.
The generated items are a list at **`ai_response.Data`**, each `{ name, description }` where
`description` is **HTML** (`<ol><li>` steps for test cases):

```json
{
  "ItemId": 26478,
  "ItemType": "SRS",
  "VersionId": 341,
  "AI_Prompt_Id": 12,
  "item": "SR-26478  The user shall be able to login…",
  "link_type": "Test Verification",
  "source": "Test Case",
  "target": "Software Requirement",
  "ai_response": {
    "Data": [
      {
        "name": "Successful Login with Valid Credentials",
        "description": "<p><strong>Objective:</strong> …</p><ol><li><strong>Step #1:</strong> Power on the system…<br/><strong>Expected Result:</strong> The login screen is shown.</li>…</ol>"
      }
    ]
  },
  "display_name": "Test Case Based on Software Requirement",
  "prompt": "…the resolved prompt text…",
  "ErrorMessage": null
}
```

Notes for parsing:
- The item list is **nested** at `ai_response.Data` — not top-level `Data`. Don't grab the
  top-level `prompt` string by mistake (recursively find the list of `{name, description}` dicts).
- **Test-case steps come in two HTML shapes** — handle both:
  - **`<ol><li>`**: each `<li>` is a step; split its inner HTML on **"Expected Result:"**, and
    strip the leading `Step #N:` label + tags.
  - **`<table>`**: rows are steps with columns *(Step #, Step Description, Expected Result)* — skip
    the header row (`<th>` / a row whose cells are the column titles); map `[num, desc, expected]`.
- Keep the **intro/objective** (the `<p>` before the step block) as the item's description; remove
  the `<table>`/`<ol>`/`<ul>` block from it so the steps aren't duplicated.
- `link_type` / `source` / `target` describe the relation Ask Paul intends (e.g. Test Case →
  Software Requirement, `Test Verification`).
- On failure `ErrorMessage` is set (and/or `ai_response` is empty).

Treat this as **a draft** — the endpoint returns text; it does **not** create the items. Do the
create + trace yourself so the user can review/edit first:

1. For each generated item → [QW_Add_Object](qw-add-item.md) at the child level (type **label**,
   `Major`/`Minor` version, `Insert_to_Pool: "Y"`).
2. Trace child → source via [QW_Add_Relations_Custom_Code](qw-add-trace.md)
   (`{childCode}-{newId}` → `{sourceCode}-{ItemId}`, `RelationType` empty).

This reuses the exact add-item / add-trace path the matrix inline-add already uses (critical note
#10 in `CLAUDE.md`).

---

## End-to-end flow

```
QW_Login ──► permission has 'O'? version Ver_id? type Code?
   │
Fetch_AI_Prompts ──► pickPrompt(sourceTypeLabel, "Test Case") ──► AI_Prompt_Id
   │
Get_AI_Response(ItemId, ItemType=Code, VersionId, AI_Prompt_Id, IsTechUser=0)
   │                                   └─► draft [{Name, Description}, ...]
   ▼  (user reviews / edits)
for each draft: QW_Add_Object ──► QW_Add_Relations_Custom_Code (child ► source)
```

---

## Full Example (JavaScript)

```js
async function askPaul({ baseUrl, authHeader, itemId, itemTypeCode, versionId, promptId }) {
  const qs = new URLSearchParams({
    ItemId: String(itemId),
    ItemType: itemTypeCode,      // original Code, e.g. "SRS"
    VersionId: String(versionId),
    AI_Prompt_Id: String(promptId),
    IsTechUser: '0',
  });
  const url = `${baseUrl}/api/v2/OrcanosAI/Get_AI_Response?${qs}`;
  const r = await fetch(url, {
    headers: { Authorization: authHeader, 'Content-Type': 'application/json' },
  });
  if (r.status === 401) throw new Error('Session expired');
  const data = await r.json();
  if (data.IsSuccess === false) throw new Error(data.Message || 'Ask Paul failed');
  return data; // inspect .Data shape against the live API
}
```

---

## See also
- [Main Skill](SKILL.md) — Base URL, auth, permission decoding
- [Fetch_AI_Prompts](ai-fetch-prompts.md) — Pick `AI_Prompt_Id`
- [QW_Add_Object](qw-add-item.md) + [QW_Add_Relations_Custom_Code](qw-add-trace.md) — Persist & trace the drafts
- [QW_Login](qw-login.md) — `VersionId`, type `Code`, `O` permission
