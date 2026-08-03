---
name: orcanos-form-builder
description: Build a rendered Add/Edit form UI for any Orcanos item type (CAPA, REQ, DEFECT, …) from a live QW_Get_Item_Add_Edit response — field layout, sections, picklists, and mandatory rules. Wraps orcanos-api for the API call and ui-ux for styling. Use when asked to "build/mock up/show the form for <item type>", "what fields does <item type> have", or to scaffold a real Add/Edit screen in the app.
revision: 1.0.0
---

# Orcanos Form Builder

Turns a live `QW_Get_Item_Add_Edit` response into a rendered form — either a styled **mockup**
(HTML artifact, for design review / "what does this look like") or the basis for a **real**
React Add/Edit screen in this codebase. This skill is glue: it does not duplicate the API or
design-system docs, it sequences them.

**Depends on:**
- [`orcanos-api`](../orcanos-api/SKILL.md) → [`qw-get-item-add-edit.md`](../orcanos-api/qw-get-item-add-edit.md) for the endpoint contract, and [`qw-login.md`](../orcanos-api/qw-login.md) for resolving `Project_id` / `VersionId` / `Item_Type` codes
- `ui-ux` for color tokens, typography, input/button/pill styles (mockups should look like the rest of the app, not a generic form)
- `artifact-design` — load it before writing any mockup HTML, if publishing as an Artifact

---

## 1. Resolve inputs

You need four things before calling the endpoint:

| Input | Where it comes from |
|---|---|
| Credentials | Ask the user, or — inside the Orcanos QMS project only — `.env.test` (`ORCANOS_TEST_URL`, `ORCANOS_TEST_USER`, `ORCANOS_TEST_PASS`). Never assume test creds exist in other projects. |
| `Item_Type` | The item type code the user names (e.g. "CAPA" → `CAPA`). If ambiguous, call `QW_Login` and match against `Item_type[].Label`/`Code` for the target project. |
| `Project_id`, `VersionId` | From `QW_Login` → `Projects.Project[]` → pick the project the user means (ask if more than one plausible match) → `Id` and `Version[].Ver_id`. |
| `Item_id` | `"0"` for the **Add** form (the default). A real numeric id for the **Edit** form of an existing item. |

Call `QW_Login` first if you don't already have `Project_id`/`VersionId`/`Item_Type` confirmed —
don't guess these values.

---

## 2. Fetch the form definition

POST `QW_Get_Item_Add_Edit` per [qw-get-item-add-edit.md](../orcanos-api/qw-get-item-add-edit.md):

```json
{ "Item_id": "0", "Item_Type": "<CODE>", "Project_id": <id>, "VersionId": <verId>, "CustomerId": "", "EditFieldName": "" }
```

Save the raw response to a scratch file rather than pulling it fully into context — `Data.field[]`
can include multi-KB HTML default values (see step 3). Parse it out-of-band with a small Node
script (below), not by eyeballing the raw JSON.

---

## 3. Parse fields (Node helper)

```js
const fs = require('fs');
const raw = JSON.parse(fs.readFileSync(RAW_RESPONSE_PATH, 'utf-8'));
let fields = raw.Data.field;
if (!Array.isArray(fields)) fields = [fields]; // XML->JSON single-item quirk

const clean = fields.map(f => ({
  name: f.name,
  title: f.title,                 // tenant-customized label — render this, not default_title
  type: f.type,                   // text | combobox | date | html | multiline | multiSelect | numeric | richEditor | ...
  section: f.section || '',       // NUMERIC ID ONLY — API gives no section label, see step 4
  web_order: f.web_order ?? 0,
  max_length: f.max_length,
  is_mandatory: f.is_mandatory,               // "1" = always required
  dependent_field_name: f.dependent_field_name,       // controls this field's mandatory state
  dependent_mandatory_value: f.dependent_mandatory_value,
  ws_add_col_name: f.ws_add_col_name,         // payload key for QW_Add_Object
  options: Array.isArray(f.val) ? f.val.map(o => ({ code: o.code, label: o.label, auto_assign: o.auto_assign })) : (f.val ? [f.val] : []),
  has_default_html: f.type === 'html' && typeof f.Text === 'string' && f.Text.length > 500,
}));

clean.sort((a, b) => a.section.localeCompare(b.section) || a.web_order - b.web_order);

// Group into sections, ordered by each section's lowest web_order (renders in the form's real flow)
const bySection = {};
for (const f of clean) (bySection[f.section] ??= []).push(f);
const sectionOrder = Object.entries(bySection)
  .sort((a, b) => Math.min(...a[1].map(f => f.web_order)) - Math.min(...b[1].map(f => f.web_order)))
  .map(([id]) => id);
```

---

## 4. Section labels are NOT in the API

`section` is a bare numeric id (`"159"`, `"233"`, …) — Orcanos does not return a section title.
**Infer a human label from the fields grouped under it** (e.g. a section holding "Complaint List",
"Source", "NC Number" → "Non-Conformance & Source"), and **tag the rendered section with its raw
id** (small caption: `API section 233`) so the mockup is honest about what came from the API vs.
what you interpreted. Do not present an inferred label as if Orcanos provided it.

---

## 5. Field type → control mapping

| API `type` | Render as | Notes |
|---|---|---|
| `text` | `<input type="text" maxlength="{max_length}">` | |
| `date` | `<input type="date">` | |
| `numeric` | `<input type="number">` | If the field title implies a computed value ("Number of…", "Count") mark `readonly` and caption "Auto-calculated" — this is an inference, not an API flag; say so if asked. |
| `multiline` | `<textarea>` | |
| `html` | Rich-text mock (toolbar + textarea) | If `has_default_html`, don't dump the raw HTML into the page — summarize what the template contains and offer a collapsed "preview" disclosure instead. |
| `richEditor` | Rich-text mock (toolbar + textarea) | Same treatment as `html`, smaller default content is fine to show directly. |
| `combobox` | `<select>` populated from `options[]` (`code`=value, `label`=display) | If `options.length` is large (~50+, e.g. a template picker), render a search input with the count noted instead of dumping every option. |
| `multiSelect` | Toggle-chip group, one chip per option | `aria-pressed` toggle, matches `ui-ux` pill styling. |

An option's `auto_assign`/`auto_assign_id` (seen on Status values) means selecting it side-effects
another field — surface that as a caption ("Selecting **New** auto-assigns Assignee → Creator"),
don't silently implement it unless building a real (non-mockup) form.

---

## 6. Mandatory rules

- `is_mandatory === "1"` → red `*` next to the label, real HTML `required` if the control is wired.
- `dependent_field_name` set → this field becomes mandatory when that other field's value equals
  `dependent_mandatory_value`. In a **mockup**, note the rule inline ("required once Status =
  Closed") rather than implementing live logic. In a **real** form, wire a change listener on the
  dependency field that toggles `required`/the asterisk.
- If nothing on the fetched item type has `is_mandatory: "1"` or a populated
  `dependent_field_name` (common — many tenants don't configure these), **say so explicitly** in
  the output rather than inventing example rules. See the mandatory-field-rule reference in
  [qw-get-item-add-edit.md](../orcanos-api/qw-get-item-add-edit.md).

---

## 7. Build the output

**Mockup (default, when the ask is "show me"/"build a form for X"):**
1. Load `artifact-design` before writing HTML.
2. Load `ui-ux` and use its color tokens, input/select/textarea styling, pill/chip styling, section
   divider pattern (`.acl-section` / `.acl-section-title`) — a mockup for this app should look like
   this app, not a generic Bootstrap form.
3. Design/light+dark aware per `artifact-design`'s token conventions.
4. Include a small "source" panel: the exact `QW_Get_Item_Add_Edit` request payload used, and a
   field-count/type-breakdown summary — this is what makes it a *data-driven* mockup rather than a
   guess, and lets the user sanity-check it against the live tenant.
5. Publish with `Artifact` (private by default — tell the user that, and that they need to use the
   page's share menu if they want to hand out the link).

**Real form (when the ask is to scaffold an actual Add/Edit screen in the codebase):**
- Same field/section/type parsing (steps 3–6), but emit React using this project's existing form
  patterns (`ui-ux` §6 Forms & Inputs, `SearchableSelect` for large comboboxes) instead of static
  mockup HTML, and wire submission to `QW_Add_Object` ([qw-add-item.md](../orcanos-api/qw-add-item.md))
  using each field's `ws_add_col_name` as the payload key.
- This is a bigger change — confirm scope with the user before generating a full component (which
  screen, which item type(s), whether it replaces an existing form) rather than assuming "mockup"
  intent silently expanded into a code change.

---

## See also
- [orcanos-api/qw-get-item-add-edit.md](../orcanos-api/qw-get-item-add-edit.md) — endpoint contract this skill wraps
- [orcanos-api/qw-login.md](../orcanos-api/qw-login.md) — resolving `Project_id`/`VersionId`/`Item_Type`
- [orcanos-api/qw-add-item.md](../orcanos-api/qw-add-item.md) — submitting the item a real form would build
- `ui-ux` — design tokens and component patterns used for rendering
- `artifact-design` — required reading before writing mockup HTML
