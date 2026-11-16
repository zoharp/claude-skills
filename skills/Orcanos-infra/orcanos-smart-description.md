# The Description field is a SMART rich-text field (template with embedded fields + filters)

**What** `Description` (`obj_description` in the Orcanos database) really holds, and how to treat it.
**Part of:** `Orcanos-infra` · **API:** `orcanos-api` (`QW_Get_Object`, `QW_Get_Filter_Results`, `QW_Get_Object_View`)

> Source: **[PO]** product owner, 2026-11-12, with screenshots of `SUPLR-25937` (Record tab, *Show Data* /
> *Hide Data*) and the raw HTML of a Supplier type's description. Placeholder syntax below is copied from
> that HTML. **Not yet verified:** which API calls return the raw template vs. the rendered (parsed) text.

---

## 1. What it is

`Description` is a rich-text (CKEditor) field, but it is also a **template**. While editing, the author can
embed:

| Embedded thing | Stored HTML | Edit mode shows | Review / print mode shows |
|---|---|---|---|
| A **field of this item's form** | `<a name="FIELD_<field code>">Field label</a>` — e.g. `FIELD_Obj_name`, `FIELD_Obj_status`, `FIELD_CS163` (custom fields are `CS<n>`) | the field's **label**, as a blue link | the item's **value** of that field (`Test supplier`, `New`, `Not Set` …) |
| A **saved filter** | `<a name="FILTER_<filter id>" obj-type="<type code>" version_id="<ver id>">Text</a>` — e.g. `FILTER_805 obj-type="SAR" version_id="422"` | the link text | the filter's **results** for this item (e.g. the supplier's annual reviews), or *No `<type label>` were found.* |

Everything around the anchors is ordinary HTML (tables, bold labels, headings). So a type's description is
often a **print / report layout** of the item — a table of "Label: [field]" pairs — not prose a person wrote.

The *Record* tab in Orcanos toggles the two modes: **Show Data** = rendered values, **Hide Data** =
field / filter names.

## 2. Traps

1. **The raw HTML duplicates the form and says nothing.** Read raw, it is a grid of field *labels*
   (`Manufacturer`, `Vendor Name:`, `Approval Status`) — it looks like data but is the template. Never show
   it as the item's description to a user; it confuses them (user, 2026-11-12, Supplier Portal).
2. **Don't parse it as content** (AI prompts, search text, diff/compare, import matching). Strip
   `<a name="FIELD_…">` / `<a name="FILTER_…">` anchors — or skip the field — before using a description
   as text. An AI fed the template will "find" requirements that are just field labels.
3. **Don't write it back blindly.** Editing the text must keep the anchors exactly (`name`, `obj-type`,
   `version_id`); a rewrite through a plain-text path destroys the template for every later print.
4. **An anchor can repeat or be empty** (`<a name="FIELD_CS88"></a>` appears twice in the sample) —
   harmless leftovers of the editor; not an error.
5. **Rendering it yourself** = replace each `FIELD_<code>` anchor with the item's value of that field
   (from `QW_Get_Object` / the form) and each `FILTER_<id>` with that filter's rows for the item. Not built
   anywhere in our code; prefer Orcanos's own rendered view if one is needed.
6. Plain types still use Description as **real text** (requirements, defects …). Tell the two apart by the
   anchors: no `FIELD_` / `FILTER_` anchor ⇒ ordinary rich text (still HTML, still often double-encoded —
   see `orcanos-work-items.md` §2).

## 3. Where it matters in our code

| Place | Decision |
|---|---|
| traceability-matrix → Supplier Portal → one supplier (`SupplierPortalSupplier.jsx`) | **Description is hidden** (2026-11-12, user: "confusing — used here only for printing"). |
| Any new screen showing an item's Description | Check for `FIELD_` / `FILTER_` anchors; if present, hide it or show Orcanos's rendered view — never the raw template. |
