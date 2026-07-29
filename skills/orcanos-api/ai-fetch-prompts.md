# Fetch_AI_Prompts — List Ask Paul Prompts

Returns every configured **Ask Paul** AI prompt (paginated). Each prompt says which
source **item type** it runs on and what it produces (e.g. *test cases from a software
requirement*). Use this to pick the right `AI_Prompt_Id` for [Get_AI_Response](ai-get-response.md).

> ⚠️ **Different base path.** The AI endpoints live under **`/api/v2/OrcanosAI/`**, not
> `/api/v2/Json/`. Swagger UI: `https://<instance>/<tenant>/api/swagger/ui/index#!/OrcanosAI/`.

## Endpoint

```
GET <base>/api/v2/OrcanosAI/Fetch_AI_Prompts?iPageNo=1&iPageSize=50
Authorization: Basic <base64(username:password)> OR Bearer <api-key>
OrcanosAPIKey: <api-key>   (alternative header)
```

`<base>` includes the tenant, e.g. `https://app.orcanos.com/orca60`.
Full URL: `https://app.orcanos.com/orca60/api/v2/OrcanosAI/Fetch_AI_Prompts`.

**Auth:** See [main skill](SKILL.md). **Prerequisite:** [QW_Login](qw-login.md) — Ask Paul is
gated on the **`O` ("Enable Ask Paul")** permission letter in the login permission string; hide
AI actions when it's absent.

---

## Query parameters (verified against swagger, orca60)

| Param | In | Type | Required | Notes |
|---|---|---|---|---|
| `iPageNo` | query | integer | **Yes** | 1-based page number |
| `iPageSize` | query | integer | **Yes** | Rows per page (use a large value, e.g. 50, to pull all in one call — there are ~11 prompts) |
| `OrderBy` | query | string | No | Sort expression |
| `SearchQuery` | query | string | No | Server-side search over prompts |

---

## Success Response

```json
{
  "total_records": 11,
  "current_page": 1,
  "page_size": 10,
  "lstPrompt": [
    {
      "ID": 5,
      "Name": "Test Case Based on Software Requirement",
      "Display_Name": "Test Case Based on Software Requirement",
      "Prompt_String": "For the software requirement titled [*Name*], please provide up to 5 verification test cases ... The requirement is described as follows: [*Description*]. ...",
      "item_type": "Software Requirement",
      "prompt_type": "Create & Trace",
      "lstPromptType": null,
      "lstWorkItems": null,
      "lstFields": null
    }
  ]
}
```

### Per-prompt fields that matter

| Field | Use |
|---|---|
| `ID` | ⭐ Pass as `AI_Prompt_Id` to [Get_AI_Response](ai-get-response.md) |
| `item_type` | **Human label** of the *source* type this prompt runs on (`Software Requirement`, `Risk`, `Product Requirement`, `Complaint`, …). NOT the original code — see mapping note below |
| `Name` / `Display_Name` | What the prompt produces — match on this to pick a prompt (e.g. contains `Test Case`) |
| `prompt_type` | Currently all `Create & Trace` — the AI **creates** items and **traces** them back to the source |
| `Prompt_String` | The template. `[*Name*]` / `[*Description*]` placeholders are filled from the source item's **name / description**, so the item's Description drives the output |

> **`item_type` is a label, not a code.** The prompt's `item_type` is the display label
> (`Software Requirement`), while `Get_AI_Response`'s `ItemType` param wants the source item's
> **original code** (e.g. `SRS`). Map label→code via `QW_Login`'s `Item_type[]` (`.Label` ↔ `.Code`).

---

## Picking the right prompt (Create-&-Trace flow)

⚠️ **Ask Paul needs one prompt per (source type → target type) PAIR.** A prompt is
usable only when **both** hold:

1. its source **`item_type`** is the type of the item you run it on (`Risk`, `Software Requirement`, …), **and**
2. its **`Name`** names the **target** type you want to create (`… Test Case …`, `… Product Requirement …`).

So to create a Product Requirement from a User Requirement, the tenant must have a prompt with
`item_type: "User Requirement"` whose `Name` contains "Product Requirement". If it doesn't exist,
**that pairing is simply not AI-generatable** — there is nothing to fall back to.

**Match the source STRICTLY, the target FUZZILY.** The source must be exactly right (a wrong
source corrupts data — see below), but the target lives inside a free-text `Name` an admin
typed by hand, so an exact substring test is too brittle (a single typo hides the prompt).
Key on the target type's **distinctive word(s)**, fuzzy-matched:

```js
// sourceTypeLabel: label of the record we run Ask Paul ON  (e.g. "User Requirement")
// targetTypeLabel: what the user wants to create           (e.g. "Software Requirement")
// targetCode:      the target type's original code         (e.g. "SRS", "NCR", "T_CASE")
function pickPrompt(prompts, sourceTypeLabel, targetTypeLabel, targetCode = '') {
  const norm = s => (s || '').toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ').trim()
    .split(/\s+/).map(w => (w.length > 3 && w.endsWith('s')) ? w.slice(0, -1) : w) // singularise
    .join(' ');
  const toks = s => norm(s).split(' ').filter(Boolean);

  // Words shared by many type names — they can't tell one target type from another,
  // so they don't count as a match ("…Requirement" is in half the prompts).
  const GENERIC = new Set(['requirement','based','base','from','on','of','the','a','an',
                           'create','and','to','for','with','new','user']);
  let distinctive = new Set(toks(targetTypeLabel).filter(w => !GENERIC.has(w)));
  if ((targetCode || '').toUpperCase() === 'T_CASE') { distinctive.add('test'); distinctive.add('case'); }
  const codeNorm = norm(targetCode);

  const ratio = (a, b) => {           // crude Levenshtein-ish similarity in [0,1]
    if (a === b) return 1;
    const m = [...a].filter((c, i) => b[i] === c).length;
    return m / Math.max(a.length, b.length);
  };
  const fuzzy = (tok, w) =>
    tok === w ||
    (tok.length >= 4 && (w.includes(tok) || tok.includes(w))) ||
    (tok.length >= 4 && w.length >= 4 && ratio(tok, w) >= 0.8);  // 'requreimetn' ≈ 'requirement'

  const scored = [];
  for (const p of prompts) {
    if (norm(p.item_type) !== norm(sourceTypeLabel)) continue;   // SOURCE is strict
    const nw = toks(p.Name);
    const codeHit = codeNorm && nw.includes(codeNorm);            // e.g. "NCR from Complaint"
    const matched = distinctive.size
      ? [...distinctive].filter(t => nw.some(w => fuzzy(t, w))).length
      : (norm(p.Name).includes(norm(targetTypeLabel)) ? 1 : 0);
    if (codeHit || matched >= 1) scored.push({ p, strength: matched + (codeHit ? 1 : 0) });
  }
  // Strongest target match wins; break ties by newest ID (the data has dups: 2&11, 5&12).
  scored.sort((a, b) => b.strength - a.strength || b.p.ID - a.p.ID);
  return scored[0]?.p || null;
}
```

Why distinctive-word + fuzzy, not `Name.includes("software requirement")`:
- **Discriminates same-source pairs.** `User Requirement` has both #15 (→ Product Requirement)
  and #16 (→ Software Requirement). Their names share the `…requirement` tail, so the *distinctive*
  word (`product` vs `software`) is the only thing that tells them apart — an exact full-label
  substring on "requirement" alone would match both.
- **Survives typos.** The live orca60 prompt #16 is named `"Create software requreimetn from user
  requirement"` (sic). `Name.includes("software requirement")` → **false** → button vanished
  (this was a real bug). `software` (the distinctive word) is spelled right, and even if it weren't,
  the ≥0.8 fuzzy ratio catches it.

Note the live data has **duplicates** (IDs 2 & 11, 5 & 12 are same-named) — the tie-break on
newest ID handles that; surface a chooser only if you want the user to decide.

### ⚠️ Three traps — each makes a real pair look unconfigured (so the AI action vanishes)

1. **`item_type` is the human LABEL, never the code.** A panel/level usually stores the **code**
   (`SRS`, `T_CASE`, `NCR`). Comparing `"SRS" == "Software Requirement"` is always false. Resolve
   code → label from **`QW_Login`**'s per-project `Item_type[]` (`.Code` ↔ `.Label`) — live, at
   match time. Don't trust a local project cache: if it's empty, every label silently degrades to
   its raw code and nothing matches.
2. **Prompt names are written by humans**, so normalise: lowercase, punctuation → space, and
   singularise (`"Software Requirements Mitigations Based on Risk"` must match the label
   *Software Requirement*). Some names use the **code/abbreviation** for the target — the live
   orca60 tenant has `"NCR from Complaint"` for the type labelled *Non Conformance* — so accept
   the target's **code** as a name token too.
3. **Prompt names have TYPOS.** They're free text, so an exact `Name.includes("software
   requirement")` is fragile. orca60 prompt **#16** is literally `"Create software requreimetn
   from user requirement"` (sic) — the exact-substring test failed and the ✨ button vanished for
   *User Requirement → Software Requirement* even though the prompt exists. Match the target on its
   **distinctive word(s)** (`software`), **fuzzy** (edit-similarity ≥ 0.8), not on the full phrase.
   The distinctive word is also what discriminates same-source pairs (#15 `product` vs #16
   `software`, both from *User Requirement*).

Real orca60 prompt list, for calibration (note the deliberate typos — they must still resolve):

| ID | `item_type` (source) | `Name` (target) | Resolves for |
|---|---|---|---|
| 16 | User Requirement | Create software **requreimetn** from user requirement | UR → Software Requirement |
| 15 | User Requirement | Product Requirement based on User Requirement | UR → Product Requirement |
| 13 | Complaint | NCR from Complaint | Complaint → Non Conformance (by **code**) |
| 12 / 5 | Software Requirement | Test Case Based on Software Requirement | SR → Test Case |
| 11 / 2 | Risk | Software Requirements Mitigations Based on Risk | Risk → Software Requirement |
| 10 / 1 | Product Requirement | Test Case Validation Base on **Prouct** Requirement | PR → Test Case |
| 9 | CAPA | Risk based on CAPA | CAPA → Risk |
| 7 | Non Conformance | CAPA based on Non Conformance | Non Conformance → CAPA |
| 4 | Recall | Recall Related Risks | Recall → Risk |
| 3 | Risk | Risk Related Recalls | Risk → Recall |

Note what's **absent**: Product Requirement → Software Requirement, Complaint → CAPA, CAPA → ECO.
Those pairs are genuinely not AI-generatable in this tenant — the correct answer is "no prompt",
not a fallback. A correct matcher resolves all the rows above **and** still returns nothing for
these three.

### 🚫 Never relax the match to "source only"

A tempting fallback — "no exact pair, so take any prompt whose `item_type` is the source" — is a
**data-corruption bug**, not a graceful degradation. `prompt_type` is **Create & Trace**: the
prompt both *creates* the items it was written to produce **and traces them to the source**. Run
the "Test Case from Software Requirement" prompt because the user asked for a *Product
Requirement* from that same SR, and you create test cases and trace them into the requirement
chain. The same goes for matching on `Name` alone (right target, wrong source item).

**No pair ⇒ no call.**

### Pre-flight: check the pair before calling Get_AI_Response

`Fetch_AI_Prompts` is a fast list call; [Get_AI_Response](ai-get-response.md) runs an LLM and can
take **tens of seconds** (client timeouts are set to ~180 s). Always resolve the prompt first, and
only offer / run the AI action when the pair resolves:

```js
const prompt = pickPrompt(await fetchAiPrompts({ baseUrl, authHeader }),
                          sourceTypeLabel, targetTypeLabel);
if (!prompt) {
  // Don't call Get_AI_Response. Tell the user this pairing has no prompt and
  // point them at manual creation.
  return { available: false };
}
const ai = await getAiResponse({ promptId: prompt.ID, itemId, itemType: sourceCode, versionId });
```

Best practice for a UI: run this check **when the add dialog opens** and only render the
"Generate with AI" affordance when `available` — an AI button that always dead-ends on
"no prompt configured" is worse than no button.

> **Test Run ⇒ Test Case.** A Test Run can't be created directly (it's the *execution* of a Test
> Case), so when the target level is a Test Run, resolve the prompt for **Test Case** — that's
> what actually gets created. See [QW_Add_Item](qw-add-item.md).

---

## Full Example (JavaScript)

```js
async function fetchAiPrompts({ baseUrl, authHeader, pageSize = 50 }) {
  const url = `${baseUrl}/api/v2/OrcanosAI/Fetch_AI_Prompts?iPageNo=1&iPageSize=${pageSize}`;
  const r = await fetch(url, {
    headers: { Authorization: authHeader, 'Content-Type': 'application/json' },
  });
  if (r.status === 401) throw new Error('Session expired');
  const data = await r.json();
  return data.lstPrompt || [];
}
```

---

## See also
- [Main Skill](SKILL.md) — Base URL, auth, permission decoding (`O` = Enable Ask Paul)
- [Get_AI_Response](ai-get-response.md) — Run a prompt on an item and get generated children
- [QW_Login](qw-login.md) — Map `item_type` label ↔ original `Code`
