---
name: ui-ux
description: Design system and UI/UX patterns derived from the Orcanos QMS project. Covers color tokens, typography, layout, buttons, modals, inputs, pills, tabs, tables, sidebar, chat bubbles, and interaction rules. Use when implementing or reviewing any React/CSS UI work.
license: MIT
---

# UI/UX Design System Skill

## When to invoke
- Building a new component or page
- Reviewing UI code for visual/interaction regressions
- Implementing modals, forms, lists, tabs, or navigation
- Auditing a design for consistency with this system

---

## 1. Color Tokens

Define these CSS variables in your root stylesheet:

```css
:root {
  --orc-purple:        #5C35A8;
  --orc-purple-light:  #7B52C8;
  --orc-purple-dark:   #3D2070;
  --orc-purple-bg:     #EAE5F5;
  --orc-purple-hover:  rgba(92,53,168,0.08);
  --orc-orange:        #F5A623;
  --orc-orange-hover:  #E08B00;
  --orc-border:        #D4D0E0;
  --orc-text:          #1A1631;
  --orc-text-mid:      #6B6580;
  --orc-text-light:    #A8A1BE;

  /* light-outline nav/tab variant (§9, §10) */
  --orc-purple-border:      rgba(92,53,168,0.28);
  --orc-purple-border-soft: rgba(92,53,168,0.14);
  --orc-purple-tint:        #F4F1FB;
}
```

`--orc-orange` in the light-outline nav/tab pattern (§9, §10) has exactly two jobs: the accent bar on the **active** row/pill, and the **hover** icon color on any row/pill (including inactive ones). It is never a background/fill color for rows or panels, and never the border color.

**Semantic color palette:**
| Purpose | Value |
|---|---|
| Primary action | `#4285F4` (blue) |
| Danger / destructive | `#d93025` (red) |
| Warning / Orcanos | `#e37400` (amber) |
| Success / new | `#1e7d34` (green) |
| Admin / advanced | `#7b5ea7` (purple) |
| Neutral / secondary | `#5f6368` (slate) |

---

## 2. Typography

```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
-webkit-font-smoothing: antialiased;
```

**Size scale:**
| Usage | Size |
|---|---|
| Page title | 18px, weight 600 |
| Modal title | 17–18px, weight 600 |
| Section heading (caps) | 13px, weight 600, uppercase, letter-spacing 0.4px |
| Body text | 14–14.5px |
| Form labels / secondary | 12–13px |
| Timestamps / meta | 11–12px |
| Micro-labels (pills, tags) | 11px |

---

## 3. Layout

### App shell
```
┌─ Sidebar (280px fixed left) ─┐ ┌─ Main content (margin-left: 280px) ─┐
│  Header: 56px (brand + nav)   │ │  Header: 56px (title + actions)      │
│  Scrollable content list      │ │  Content area: flex-1, overflow-y    │
│  Profile footer               │ │  Input/action bar: fixed bottom      │
└───────────────────────────────┘ └──────────────────────────────────────┘
```

### Content max-width
Constrain prose/chat content to `max-width: 860px`, centered with `margin: 0 auto`.

### Header bar
```css
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  border-bottom: 1px solid var(--orc-border);
  background: white;
  height: 56px;
  flex-shrink: 0;
}
```

---

## 4. Buttons

### Primary (Save / Create / Submit)
```css
padding: 8px 20px;
font-size: 13px;
font-weight: 500;
border-radius: 6px;
border: none;
background: #4285F4;
color: #fff;
cursor: pointer;
transition: background 0.15s;
/* hover: #3367d6 | disabled: opacity 0.55, cursor not-allowed */
```

### Cancel / Secondary
```css
padding: 8px 20px;
background: #fff;
border: 1px solid #d0d0d0;
border-radius: 6px;
font-size: 13px;
font-weight: 500;
color: #444;
cursor: pointer;
/* hover: background #f5f5f5, border-color #bbb */
```

### Danger (Delete / Remove)
```css
background: #d93025; color: white; border: none;
border-radius: 6px; padding: 6px 14px; font-size: 13px;
/* hover: #b71c1c */
```

### Icon button (toolbar / header)
```css
background: none; border: none;
width: 36px; height: 36px; border-radius: 8px;
cursor: pointer; font-size: 18px;
display: flex; align-items: center; justify-content: center;
color: var(--orc-text-mid); transition: all 0.15s;
/* hover: background var(--orc-purple-bg), color var(--orc-purple) */
```

### Submit / CTA gradient button
```css
width: 40px; height: 40px; border-radius: 10px;
background: linear-gradient(135deg, var(--orc-purple-light), var(--orc-orange));
border: none; color: white; cursor: pointer;
box-shadow: 0 2px 8px rgba(92,53,168,0.25);
transition: all 0.2s; align-self: flex-end;
/* hover: translateY(-2px), box-shadow stronger */
/* disabled: background #E2DEEF, color #bbb, cursor not-allowed */
```

### Button order in modals
Always: `[secondary actions left] → [Cancel] → [Primary action rightmost]`
Group all buttons together — never use `margin-left: auto` to push Cancel away.

---

## 5. Modals

### Structure
```jsx
<div style={overlayStyle} onMouseDown={e => { if (e.target === e.currentTarget) onClose(); }}>
  <div style={modalStyle}>
    {/* Header */}
    <div style={headerStyle}>
      <h2>Modal Title</h2>
      <button onClick={onClose}>×</button>
    </div>
    {/* Body — scrollable */}
    <div style={{ overflowY: 'auto', flex: 1, padding: '0 24px 20px' }}>
      {children}
    </div>
    {/* Footer actions */}
    <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', padding: '14px 24px', borderTop: '1px solid #f0f0f0' }}>
      <button className="acl-btn-cancel" onClick={onClose}>Cancel</button>
      <button className="btn-primary" onClick={onSave}>Save</button>
    </div>
  </div>
</div>
```

### Backdrop close rule
**Always use `onMouseDown` on the overlay, never `onClick`.** This prevents accidental close when the user drags to select text across the modal boundary.

```jsx
onMouseDown={e => { if (e.target === e.currentTarget) onClose(); }}
```
No `stopPropagation` needed on the modal content div.

### Modal sizing
| Type | Width |
|---|---|
| Full / list | 860px |
| Detail / create | 620px |
| Narrow / confirm | 340–480px |
| Always | `max-width: 90–96vw`, `max-height: 85–88vh` |

### Overlay
```css
position: fixed; inset: 0;
background: rgba(0,0,0,0.5);
display: flex; align-items: center; justify-content: center;
z-index: 1000;
```

### Modal shell
```css
background: #fff; border-radius: 12px;
display: flex; flex-direction: column;
box-shadow: 0 8px 40px rgba(0,0,0,0.2);
position: relative;
```

---

## 6. Forms & Inputs

### Field row layout (label + input side-by-side)
```css
.acl-field-row { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 10px; }
.acl-label { width: 130px; flex-shrink: 0; font-size: 12px; font-weight: 600; color: #666; padding-top: 9px; }
```

### Input / select
```css
padding: 8px 10px;
border: 1px solid #ddd;
border-radius: 6px;
font-size: 13px;
outline: none;
transition: border-color 0.15s;
font-family: inherit;
background: #fff;
/* focus: border-color var(--orc-purple-light) */
/* disabled: background #f9f9f9, color #888 */
```

### Textarea
Same as input + `resize: vertical; min-height: 52px;`

### Section dividers in forms
```css
.acl-section { padding: 18px 0; border-bottom: 1px solid #f0f0f0; }
.acl-section:last-child { border-bottom: none; }
.acl-section-title {
  font-size: 13px; font-weight: 600; color: #555;
  text-transform: uppercase; letter-spacing: 0.4px; margin: 0 0 14px;
}
```

### Combo / searchable picker — the ONE rule set (we keep getting this wrong)

**Every** choice list that can hold more than ~6 entries (projects, versions, work item types,
filters, fields, users, Jira projects / issue types / fields, picklist values, conditions) is a
**searchable combo**. Never a plain `<select>`, never an `<input list>` + `<datalist>`.
A fixed 2–6 choice set (direction, yes/no, poll interval) is a segmented control instead.

Must-haves — a combo that misses any of these is a bug:

1. **Fully visible — the list is PORTALLED.** Render the open list with
   `createPortal(list, document.body)` and `position: fixed` coordinates from the field's
   `getBoundingClientRect()`. An `absolute` list inside a table, a card with `overflow`, a
   modal body or a horizontally scrolling wrapper is CLIPPED (it happened in the Jira field map:
   the list opened upward and was cut to two rows). `z-index` above modals (4000).
2. **Fits the window.** Measure room below vs above; open upward only when below is short
   AND above is bigger; cap `max-height` to the room it has (min 120px, preferred 320px).
   Width = field width, at least 220px, never past the window's right edge. Re-place on
   `resize` and on `scroll` (capture phase), so it follows the field.
3. **Outside click checks BOTH the field and the portalled list** — the list is no longer a DOM
   child of the field, so `box.contains(e.target)` alone closes it before the click lands.
4. **Searchable.** Typing filters; every word must match (`words.every(w => label.includes(w))`),
   case-insensitive. Cap rendered rows (~200). Show "No matches" when empty.
5. **Keyboard.** ↓/↑ move the active row (scrolled into view), Enter picks, Esc closes.
   `role="combobox"` + `aria-expanded` + `aria-controls`; the list `role="listbox"`, rows
   `role="option"` with `aria-selected`.
6. **Options:** `onMouseDown={e => e.preventDefault()}` so the input keeps focus; pick on click.
7. **Designed, same as a text box:** same height, border, radius, padding and font as the inputs
   beside it; a ▾ caret on the right (`pointer-events: none`) with `padding-right: 28px`; the
   chosen label shown when closed, the placeholder in muted grey; the chosen row bold/purple,
   the active row lavender (`#F0EBFA`); long labels WRAP inside the list (never cut).
   **The input itself must be `width: 100%`** of its picker, and the picker `width: 100%; min-width: 0`
   of its column — unset, the input keeps its intrinsic ~280px while the absolutely placed ▾ sits at
   the column's far edge, floating outside the box (Doc Import "Set a field", 2026-10-27).
   **Page standard (traceability-matrix Doc Import, 2026-10-27 — copy it for any page):** one block,
   last in the page's stylesheet and scoped to the page root so it beats per-section rules, styling
   BOTH `select` and `.drv-combo-input` the same:
   ```css
   .X-page select, .X-page .drv-combo-input {
     font: inherit; font-size: 13px; height: 34px; box-sizing: border-box;
     border: 1px solid var(--orc-border); border-radius: 8px; background-color: #fff;
     padding: 0 30px 0 10px; text-overflow: ellipsis; cursor: pointer; min-width: 0; max-width: 100%;
   }
   .X-page select { appearance: none; /* + an SVG chevron background at right 11px center, #6B6580 */ }
   .X-page .drv-combo-input { width: 100%; }
   /* hover/focus border var(--orc-purple), focus ring rgba(92,53,168,.12); disabled #F3F2F6 + #8A8698 */
   .X-page .drv-combo-arrow { right: 11px; font-size: 11px; }
   ```
   Then size per place: **fill the column in forms** (`width: 100%`), a **fixed width** (220–320px)
   where the combo sits in a row of other controls or a table cell, and `height: 30px` inside dense
   tables. The native-select arrow and the combo's ▾ must sit at the same spot so the two look alike.
   Reference: the last block of `src/frontend/src/styles/DocImport.css`.
8. **Sorted A→Z** by the visible label (`localeCompare(..., {sensitivity:'base', numeric:true})`).
   Solution projects labelled "(Solution)" and **bold** (`strong: true`).
9. **A saved value missing from the list still shows** — add it as an extra option so the field
   never looks empty after a reload.
10. **Disabled state says why** ("Choose a project first") in the placeholder.

Reference implementation (traceability-matrix): `SearchSelect` in
`src/frontend/src/pages/review/reviewUi.jsx` + `utils/useDropdownFit.js` with `{ fixed: true }`
(options `{value, label, strong}`, CSS in `styles/DocReview.css`). Reuse it; don't write another.

Before calling a screen done, open every combo on it — including ones inside tables, value-map
rows and modals — near the bottom of the window, and confirm the whole list is readable.

---

## 7. Pills & Badges

### Standard pill
```css
font-size: 11px; padding: 2px 9px; border-radius: 20px;
white-space: nowrap; font-weight: 500;
```

### Semantic pill colors
| Purpose | Background | Text |
|---|---|---|
| Doc type | `#e8f0fe` | `#1a73e8` (blue) |
| Department | `#fef3e2` | `#b45309` (amber) |
| Version | `#e6f7f5` | `#0d7a6e` (teal) |
| Page number | `#f1f3f4` | `#5f6368` (slate) |
| ISO clause | `#EAE5F5` | `#5C35A8` (purple) |
| Status: idle | `#f1f3f4` | `#5f6368` |
| Status: active | `#e8f0fe` | `#1a73e8` |
| Status: error | `#fce8e6` | `#d93025` |
| Status: success | `#e8f5e9` | `#2e7d32` |

### Badge (table / list)
```css
background: #eef2ff; color: #4338ca;
font-size: 11px; font-weight: 500;
padding: 2px 7px; border-radius: 4px;
text-transform: uppercase; letter-spacing: 0.3px;
```

### Toggle (on/off)
```css
.toggle--on  { background: #dcfce7; color: #16a34a; }
.toggle--off { background: #f3f4f6; color: #6b7280; }
font-size: 11px; font-weight: 500; padding: 3px 8px; border-radius: 12px; border: none;
```

---

## 8. Tables

```css
.acl-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.acl-table th {
  text-align: left; padding: 10px 12px;
  border-bottom: 2px solid #eee;
  font-weight: 600; font-size: 12px; color: #555;
  text-transform: uppercase; letter-spacing: 0.3px;
}
.acl-table td { padding: 10px 12px; border-bottom: 1px solid #f5f5f5; vertical-align: middle; }
.acl-row { cursor: pointer; }
.acl-row:hover td { background: #f9fafb; }
```

No card borders, no shadow on rows — only hairline separators.

---

## 9. Tabs

### Underline tabs (in-page section switcher, e.g. inside a table or panel)
```css
.tab-bar { display: flex; gap: 4px; padding: 12px 24px 0; border-bottom: 1px solid #e8e8e8; }

.tab-btn {
  padding: 8px 18px; border: none; background: none;
  cursor: pointer; font-size: 14px; color: #666;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px; border-radius: 4px 4px 0 0;
  transition: all 0.15s;
}
.tab-btn:hover { color: #333; background: #f5f5f5; }
.tab-btn.active { color: #2563eb; border-bottom-color: #2563eb; font-weight: 500; }
```
Active tab: 2px bottom border flush with container border via `margin-bottom: -1px`.

### Light-outline pill tabs (preferred for admin/config tab bars — revised 2026-09-23)
Outlined pills instead of an underline row. **No border color change on the active pill** — the
active pill is marked by its purple fill/text plus a **purple** accent bar (not orange; orange is
reserved for the sidebar's active accent, §10, so the two active-state cues read as distinct
surfaces). Orange still marks hover only.
```css
.tab-row { display: flex; gap: 8px; flex-wrap: wrap; }

.tab-pill {
  position: relative; overflow: hidden;
  display: flex; align-items: center; gap: 7px;
  padding: 9px 16px; border-radius: 10px;
  border: 1px solid var(--orc-border); background: #fff;
  font-size: 13.5px; font-weight: 500; color: var(--orc-text-mid);
  cursor: pointer; transition: all 0.15s;
}
.tab-pill:hover { border-color: var(--orc-purple-border-soft); background: rgba(92,53,168,0.03); }
.tab-pill:hover .tab-pill-icon { stroke: var(--orc-orange); }
.tab-pill.active {
  border-color: var(--orc-border); background: var(--orc-purple-tint);
  color: var(--orc-purple); font-weight: 600;
}
.tab-pill.active .tab-pill-icon { stroke: var(--orc-purple); }
/* purple accent bar, active only — bottom edge, inside the pill */
.tab-pill.active::after {
  content: ''; position: absolute; left: 0; right: 0; bottom: 0;
  height: 2.5px; background: var(--orc-purple);
}
```
Icon default: `stroke: var(--orc-purple)` at `opacity: 0.7` (app-wide icons are purple by default,
not neutral gray — keeps every nav/tab surface reading as one system). **Hover turns the icon
orange** (`.tab-pill:hover .tab-pill-icon`, `opacity: 1`) — this is the hover feedback, not a
border/background change on the icon itself. Active overrides hover and keeps/returns the icon to
purple at full opacity. `background: #fff` on the pill is correct here because tabs sit on the
admin-content panel, which really is white — don't copy that value onto a sidebar or any surface
that sits on the lavender wash (§10).

---

## 10. Sidebar Navigation

```css
.sidebar {
  position: fixed; left: 0; top: 0; width: 280px; height: 100vh;
  background: #EAE5F5; border-right: 1px solid #D4D0E0;
  display: flex; flex-direction: column; z-index: 90;
}
```

### Light-outline nav item (preferred — revised 2026-09-23)
Rows sit directly on the sidebar's real ground — **`var(--orc-purple-wash)` (`#F0EBFA`), never white** (`.admin-nav` in `AdminScreen.css` confirms this; do not put a white card behind the rows). Rows are transparent at rest, so the wash shows through. Hover doesn't change the border color — **it turns the icon orange**, which is the hover feedback. **Active does not get a purple border** — it gets a soft purple fill plus a thin **orange** accent bar on the left edge; the sidebar is the one surface in the system where orange marks the active state itself (everywhere else — tabs, §9 — the active accent is purple, so orange stays a hover-only or sidebar-only signal and never means "active" in two different colors on the same screen).
```css
.sidebar { background: var(--orc-purple-wash); } /* ground — not white */

.sidebar-item {
  position: relative;
  padding: 10px 12px; margin: 1px 8px;
  background: transparent; border: 1px solid transparent;
  border-radius: 10px; cursor: pointer; transition: all 0.15s;
  display: flex; align-items: flex-start; gap: 10px;
}
.sidebar-item:hover { border-color: var(--orc-purple-border-soft); background: rgba(92,53,168,0.03); }
.sidebar-item:hover .sidebar-item-icon { stroke: var(--orc-orange); opacity: 1; }
.sidebar-item.active {
  border-color: transparent; background: var(--orc-purple-bg);
  padding-left: 15px; /* room for the accent bar */
}
/* orange accent bar, active only — left edge */
.sidebar-item.active::before {
  content: ''; position: absolute; left: 0; top: 8px; bottom: 8px;
  width: 3px; border-radius: 2px; background: var(--orc-orange);
}
.sidebar-item-icon { stroke: var(--orc-purple); opacity: 0.7; transition: stroke 0.15s, opacity 0.15s; }
.sidebar-item.active .sidebar-item-icon { opacity: 1; }
```
Icon default is purple (not neutral gray) at reduced opacity, going full-opacity on hover/active —
app-wide icon color is purple, per §1's admin/advanced semantic entry; orange is reserved for
hover feedback and the sidebar's own active bar. `.sidebar-item.active:hover` keeps the purple
icon (active state wins over hover) — don't let the hover rule turn an already-active icon orange.

.sidebar-item-title {
  font-size: 13px; font-weight: 500; color: #3D3858;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.sidebar-item.active .sidebar-item-title { color: #5C35A8; font-weight: 600; }
```

### Legacy gradient variant (existing screens not yet migrated)
```css
.sidebar-item.active--legacy {
  background: linear-gradient(135deg, rgba(92,53,168,0.12), rgba(245,166,35,0.06));
  border: 1px solid rgba(92,53,168,0.15);
}
```

.sidebar-section-label {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  color: rgba(61,56,88,0.4); letter-spacing: 0.5px;
  padding: 10px 16px 4px;
}

.sidebar-cta {
  width: 100%; padding: 10px 12px;
  background: linear-gradient(135deg, #7B52C8, #5C35A8);
  border: none; border-radius: 8px;
  color: white; font-size: 13px; font-weight: 700;
  cursor: pointer; transition: all 0.2s;
  display: flex; align-items: center; justify-content: center; gap: 6px;
}
.sidebar-cta:hover { transform: translateY(-1px); box-shadow: 0 3px 12px rgba(92,53,168,0.3); }

.profile-avatar {
  width: 26px; height: 26px; border-radius: 50%; background: #5C35A8;
  color: white; font-size: 11px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
```

---

## 11. Chat Messages

### User bubble (right-aligned)
```css
background: linear-gradient(135deg, var(--orc-purple) 0%, var(--orc-purple-light) 100%);
color: white; padding: 10px 16px;
border-radius: 18px 18px 4px 18px;
display: inline-block; max-width: 72%;
font-weight: 500; font-size: 14px;
```

### Assistant bubble (left-aligned, full width)
```css
background: #F7F5FC; color: var(--orc-text);
border: 1px solid var(--orc-border); padding: 14px 18px;
border-radius: 4px 18px 18px 18px;
```

### Fade-in animation
```css
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
.message { animation: fadeIn 0.3s ease-in; }
```

---

## 12. Progress / Log Panel

For monospace log output (import progress, build logs):
```css
font-family: monospace; font-size: 12px;
background: #fafafa; max-height: 320px; overflow-y: auto;
```

Line color coding:
| Type | Color | Prefix |
|---|---|---|
| info | `#555` | — |
| skipped | `#999` | `–` |
| complete | `#1e7d34` | `✓` |
| warning | `#b45309` | `⚠` |
| error | `#d93025` | `✗` |

---

## 13. Toast / Inline Feedback

```css
.toast {
  position: absolute; bottom: 20px; right: 24px;
  padding: 10px 18px; border-radius: 8px;
  font-size: 13px; font-weight: 500;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12); z-index: 10;
}
.toast--ok  { background: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }
.toast--err { background: #ffebee; color: #c62828; border: 1px solid #ef9a9a; }
```

Inline banners:
```css
.error-banner { background: #fff0f0; border: 1px solid #ffcccc; border-radius: 6px; padding: 8px 12px; color: #c0392b; font-size: 12px; }
.info-banner  { background: #fef3e2; border: 1px solid #fde8b8; border-radius: 6px; padding: 8px 12px; color: #b45309; font-size: 12px; }
```

---

## 14. Scrollbars

```css
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #f1f1f1; }
::-webkit-scrollbar-thumb { background: rgba(92,53,168,0.2); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(92,53,168,0.4); }
/* Thin (sidebar): width: 4px */
```

---

## 15. Interaction Patterns

**Hover transitions:** Always `transition: all 0.15s` on interactive elements. Use `0.2s` for larger motion (translate, box-shadow).

**Focus rings:** `border-color: var(--orc-purple-light)` on focus. Add glow for primary inputs: `box-shadow: 0 0 0 3px rgba(123,82,200,0.1)`.

**Destructive confirmations:** Always `window.confirm()` before irreversible actions (delete, reindex-all). Never trigger without explicit confirmation.

**Permission gating:** Pass `onAction={undefined}` for unauthorized users — buttons don't render rather than rendering disabled.

**Hover-reveal controls:** List item actions start at `opacity: 0`, reveal on parent hover:
```css
.list-item-action { opacity: 0; transition: opacity 0.15s; }
.list-item:hover .list-item-action { opacity: 1; }
```

---

## 16. Mobile (≤768px)

- Message max-width: 85%
- Sidebar: overlay/sheet triggered by hamburger (not fixed in view)
- Field rows: `flex-direction: column; gap: 4px`
- Labels: `width: auto; padding-top: 0`
- Modal max-height: 95vh

---

## 17. Empty States

```css
.empty-state {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 40px; text-align: center; color: var(--orc-text-mid); flex: 1;
}
```
Structure: large muted icon (opacity 0.3, 48px) → heading (18px, weight 700, `#3D3858`) → body text (13px, `#7A7492`) → optional action card.

---

## 18. User Menu / Profile Dropdown

A header-mounted avatar that opens a compact dropdown for user actions.

### Avatar trigger
```css
.user-avatar {
  width: 36px; height: 36px; border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white; border: none;
  font-weight: 700; font-size: 15px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 2px 6px rgba(0,0,0,0.18);
  transition: box-shadow 0.2s ease, transform 0.15s ease;
}
.user-avatar:hover { transform: scale(1.06); box-shadow: 0 4px 12px rgba(0,0,0,0.25); }
.user-avatar:active { transform: scale(0.96); }
```

### Dropdown panel
```css
.user-menu-dropdown {
  position: absolute; right: 0; top: calc(100% + 8px);
  background: #ffffff;
  border: 1px solid #e8e8ef;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12), 0 2px 6px rgba(0,0,0,0.06);
  width: 220px; z-index: 1000;
  overflow: hidden; padding: 6px;
}
```

### User info row
Show a mini avatar + username at the top of the panel — not a heavy header.
```css
.menu-user-info { display: flex; align-items: center; gap: 10px; padding: 10px; }
.menu-user-avatar { width: 32px; height: 32px; border-radius: 50%; /* same gradient as trigger */ }
.menu-user-id { font-size: 13px; font-weight: 500; color: #374151; overflow: hidden; text-overflow: ellipsis; }
```

### Menu items
Items use flex with an SVG icon on the left. Rounded corners (8px), no border.
```css
.menu-item {
  display: flex; align-items: center; gap: 10px;
  width: 100%; padding: 9px 10px;
  background: transparent; border: none; border-radius: 8px;
  color: #374151; font-size: 14px; font-weight: 500;
  text-align: left; cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.menu-item:hover { background: #f5f5f8; color: #111827; }
.menu-item-icon { width: 17px; height: 17px; flex-shrink: 0; opacity: 0.65; }
```

### Highlighted item (Release Notes / active page)
Use lavender background + purple text. Always apply to the current section's item.
```css
.menu-item--highlighted {
  color: #6d28d9 !important;
  background: #ede9fe;
}
.menu-item--highlighted .menu-item-icon { opacity: 1; }
.menu-item--highlighted:hover { background: #ddd6fe !important; color: #5b21b6 !important; }
```

### Destructive item (Sign out)
Neutral gray at rest; turns red on hover.
```css
.menu-item--signout { color: #6b7280 !important; }
.menu-item--signout:hover { background: #fef2f2 !important; color: #dc2626 !important; }
```

### Dividers
`height: 1px; background: #f0f0f5; margin: 4px 0;` — use between sections, not between every item.

### Rules
- **Outside click closes** the dropdown — `mousedown` listener on `document`, removed on unmount.
- **Divider placement:** after the user info row, and before the destructive (sign-out) item only.
- **Icons:** inline SVG, 17×17px, `fill="currentColor"` so they inherit item text color.
- **Width:** 200–240px. Don't stretch to fill the header.
- **Position:** `top: calc(100% + 8px); right: 0` — aligns to the right edge of the avatar.

### JSX pattern
```jsx
<div className="user-menu" ref={containerRef}>
  <button className="user-avatar" onClick={() => setIsOpen(v => !v)}>{letter}</button>
  {isOpen && (
    <div className="user-menu-dropdown">
      <div className="menu-user-info">
        <div className="menu-user-avatar">{letter}</div>
        <span className="menu-user-id">{userId}</span>
      </div>
      <div className="menu-divider" />
      <button type="button" className="menu-item menu-item--highlighted" onClick={handleReleaseNotes}>
        <svg className="menu-item-icon" viewBox="0 0 20 20" fill="currentColor">…</svg>
        Release Notes
      </button>
      <div className="menu-divider" />
      <button type="button" className="menu-item menu-item--signout" onClick={onLogout}>
        <svg className="menu-item-icon" viewBox="0 0 20 20" fill="currentColor">…</svg>
        Sign out
      </button>
    </div>
  )}
</div>
```

---

## Quick Checklist

When implementing a new UI component:

- [ ] CSS variables for colors, not hardcoded hex
- [ ] Font: Inter, correct size from the scale
- [ ] Buttons: `8px 20px` padding, `6px` radius, right-aligned in modals
- [ ] Modal: `onMouseDown` backdrop close, `flex-direction: column`, scrollable body
- [ ] Inputs: `8px 10px` padding, focus border color, disabled state
- [ ] Destructive actions: confirmation required, red `#d93025`
- [ ] Transitions: `0.15s` on hover
- [ ] Hover-reveal: list action buttons start opacity 0
- [ ] Every combo: portalled + `position: fixed`, fits the window, searchable, keyboard, A→Z, styled like the inputs (see *Combo / searchable picker*); no plain `<select>` / `<datalist>`
- [ ] Tab active state: underline row uses 2px bottom border (`margin-bottom: -1px`); admin/config tab bars use light-outline pills (§9) with the orange accent on the active pill only
- [ ] Sidebar nav: ground is `var(--orc-purple-wash)`, never white; light-outline active state (§10) — purple border + tint + orange left accent bar; hover turns the icon orange (not the border/background)
- [ ] Pills: `border-radius: 20px`, semantic color by content type
- [ ] Mobile: test at 768px, stack field rows
- [ ] User menu: avatar 36px circle, dropdown 220px with 12px radius, icon+label items, highlighted item in lavender, sign-out neutral→red on hover, outside-click closes
