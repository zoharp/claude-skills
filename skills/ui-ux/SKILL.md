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
}
```

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

### SearchableSelect (dropdown inside modal)
Dropdowns inside modals with `overflow: auto` **must use `position: fixed`** to avoid clipping.

```jsx
function SearchableSelect({ options, value, onChange, placeholder }) {
  const [open, setOpen] = React.useState(false);
  const [query, setQuery] = React.useState('');
  const [dropPos, setDropPos] = React.useState({ top: 0, left: 0, width: 0 });
  const inputRef = React.useRef(null);

  const openDropdown = () => {
    const r = inputRef.current.getBoundingClientRect();
    setDropPos({ top: r.bottom + 2, left: r.left, width: r.width });
    setQuery(''); setOpen(true);
  };

  // Dropdown: position: 'fixed', top/left/width from dropPos, zIndex: 9999
  // Option: onMouseDown={e => { e.preventDefault(); onChange(opt.value); setOpen(false); }}
  // Outside click: document mousedown listener → setOpen(false)
}
```
Rules:
- `onMouseDown` (not `onClick`) on options — prevents blur before selection
- `e.preventDefault()` on option mousedown keeps focus in input
- Filter: `options.filter(o => o.label.toLowerCase().includes(query.toLowerCase()))`

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

---

## 10. Sidebar Navigation

```css
.sidebar {
  position: fixed; left: 0; top: 0; width: 280px; height: 100vh;
  background: #EAE5F5; border-right: 1px solid #D4D0E0;
  display: flex; flex-direction: column; z-index: 90;
}

.sidebar-item {
  padding: 9px 12px; margin: 1px 8px;
  background: transparent; border: 1px solid transparent;
  border-radius: 8px; cursor: pointer; transition: all 0.15s;
  display: flex; align-items: center; gap: 4px;
}
.sidebar-item:hover { background: rgba(92,53,168,0.08); }
.sidebar-item.active {
  background: linear-gradient(135deg, rgba(92,53,168,0.12), rgba(245,166,35,0.06));
  border: 1px solid rgba(92,53,168,0.15);
}

.sidebar-item-title {
  font-size: 13px; font-weight: 500; color: #3D3858;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.sidebar-item.active .sidebar-item-title { color: #5C35A8; font-weight: 600; }

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
- [ ] Dropdowns inside scrolling modals: `position: fixed` + `getBoundingClientRect()`
- [ ] Tab active state: 2px bottom border, `margin-bottom: -1px`
- [ ] Pills: `border-radius: 20px`, semantic color by content type
- [ ] Mobile: test at 768px, stack field rows
- [ ] User menu: avatar 36px circle, dropdown 220px with 12px radius, icon+label items, highlighted item in lavender, sign-out neutral→red on hover, outside-click closes
