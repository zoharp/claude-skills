---
name: markdown-to-docx
description: Convert Markdown to Word documents instantly. Use whenever you need to export markdown as .docx, convert markdown files to Word format, or turn markdown content into professional Word documents. Just say "convert" and point to the file — automatic cleanup + conversion in one command.
compatibility: pandoc (system utility), Node.js
---

# Markdown to Word Conversion Skill

Convert markdown (.md) files to professional Word documents (.docx) with proper formatting, hyperlinks, lists, and spacing.

## Quick Start

**One command:**
```bash
node convert.js input.md output.docx
```

Done. Cleans + converts automatically.

Or use the manual steps below if needed.

## When to Use This Skill

✅ **Use this skill when:**
- User wants to export markdown as Word document
- User needs a .docx version of markdown content
- User has a multi-section markdown file (like DD, contracts, reports)
- User needs professional formatting, lists, hyperlinks, and tables preserved
- User has experienced markdown formatting issues before

❌ **Don't use if:**
- File is already .docx
- User only needs a PDF
- Content is primarily HTML/CSS (use PDF skill instead)

---

## The Workflow

### Step 1: Validate & Clean Markdown

Before converting, fix common markdown issues:

**Check for:**
- Stray characters or incomplete markup (`0`, `###` without text)
- Inline lists that should be bullet points (lines with multiple ` - ` separators)
- Missing blank lines between sections
- Malformed tables or links

**Fixes:**
```bash
# Remove stray single characters on own lines
sed -i '/^[0-9]$/d' file.md

# Remove duplicate/broken headings
sed -i '/^###[^[:space:]]/d' file.md

# Ensure blank lines before Supporting Dataroom, etc.
sed -i 's/\n\*\*Supporting/\n\n**Supporting/g' file.md

# Convert inline list items to bullet format
# Pattern: "Text - Item1 - Item2 - Item3" → separate bullets
```

### Step 2: Convert with Pandoc

Use pandoc (the industry standard for markdown conversion):

```bash
pandoc input.md -o output.docx \
  --from=markdown \
  --to=docx \
  --wrap=preserve
```

**Pandoc options explained:**
- `--from=markdown` — Parse input as markdown
- `--to=docx` — Output Word format
- `--wrap=preserve` — Keep line breaks intact (important for lists)

### Step 3: Verify Output

Check the Word document for:
- ✅ Headings are properly sized (H1, H2, H3)
- ✅ Lists have proper bullets and indentation
- ✅ Bold text displays correctly (`**text**` → bold)
- ✅ Hyperlinks are clickable and blue
- ✅ Tables render with proper columns and headers
- ✅ Line breaks exist between list items
- ✅ No text duplication

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Text duplication | Markdown processor double-adds content | Clean markdown with `sed` before converting |
| Collapsed lists | Missing blank lines between items | Add `\n` after each list item |
| Broken links | Malformed markdown links | Use format `[text](url)` exactly |
| Stray characters | Incomplete markup or leftover text | Remove with `sed '/^[0-9]$/d'` |
| No line breaks | Pandoc collapsing paragraphs | Use `--wrap=preserve` flag |
| Tables broken | Pipe-separated table not formatted correctly | Ensure pipes `\|` separate columns consistently |

---

## Pre-Conversion Cleanup Script

Use this Node.js script for automated cleanup:

```javascript
const fs = require('fs');

let content = fs.readFileSync('input.md', 'utf8');

// Remove stray single lines (0, 1, ###, etc)
content = content.replace(/^[0-9]$/gm, '');
content = content.replace(/^###[^[:space:]]/gm, '');

// Add spacing before key sections
content = content.replace(/\n\*\*Supporting/g, '\n\n**Supporting');
content = content.replace(/\n\*\*Confirmed:/g, '\n\n**Confirmed:');

// Convert inline lists (Text - Item1 - Item2) to bullets
const lines = content.split('\n');
const processed = [];

for (const line of lines) {
  if (line.includes(' - ') && !line.startsWith('- ') && !line.includes('|')) {
    const parts = line.split(' - ');
    if (parts.length > 1) {
      processed.push(parts[0].trim());
      for (let i = 1; i < parts.length; i++) {
        processed.push('- ' + parts[i].trim());
      }
      continue;
    }
  }
  processed.push(line);
}

fs.writeFileSync('input.md', processed.join('\n'));
console.log('✅ Markdown cleaned');
```

---

## Markdown Formatting Reference

Ensure your markdown uses proper syntax:

```markdown
# Heading 1 (H1)
## Heading 2 (H2)
### Heading 3 (H3)

**Bold text**
*Italic text*

- Bullet point
  - Nested bullet
    - Deeply nested

[Link text](https://example.com)

| Column 1 | Column 2 |
|----------|----------|
| Cell 1   | Cell 2   |
```

---

## Output

The converted Word document will have:
- ✅ Professional formatting with proper spacing
- ✅ Clickable hyperlinks in blue
- ✅ Proper heading hierarchy
- ✅ Bullet lists and numbered lists
- ✅ Formatted tables with headers
- ✅ Bold and italic text preserved
- ✅ Page breaks as needed
- ✅ US Letter page size (8.5" x 11")

---

## Full Conversion Workflow (CLI)

```bash
#!/bin/bash

# Clean markdown
node cleanup.js

# Convert to Word
pandoc input.md -o output.docx \
  --from=markdown \
  --to=docx \
  --wrap=preserve

# Verify (on Mac/Linux)
open output.docx  # or 'xdg-open' on Linux

# Or just download the file from outputs
```

---

## When You Use This Skill

1. **Validate the markdown** — Check for stray characters, incomplete markup
2. **Run cleanup if needed** — Use the script above to fix common issues
3. **Convert with pandoc** — Single command, no configuration needed
4. **Verify the output** — Open .docx and spot-check formatting
5. **Return to user** — Present the .docx file

That's it. No more manual conversions through custom scripts.
