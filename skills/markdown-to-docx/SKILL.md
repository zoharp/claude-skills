---
name: markdown-to-docx
description: Convert markdown files to professional Word documents. Use this skill whenever a user needs to export markdown (.md) files as Word documents (.docx), especially for reports, documentation, due diligence responses, or any markdown that needs to be shared as a formatted Word file. Handles bold, italic, hyperlinks, tables, bullet lists, and Unicode status indicators automatically. Just provide the markdown file and specify output location.
compatibility: Requires python-docx library
---

# Markdown to Word Converter Skill

Convert markdown (.md) files to professional Word documents (.docx) with full formatting support.

## What This Skill Does

Transforms markdown source files into properly formatted Word documents with:
- **Bold & italic text** — preserved exactly as marked
- **Hyperlinks** — rendered as blue underlined clickable text
- **Tables** — formatted with bold headers and proper alignment
- **Bullet lists** — proper indentation and hierarchy
- **Status indicators** — Unicode symbols (✓ ⚠ ▶ ↻ ● ⧗ ?) replace emoji for universal rendering
- **Clean formatting** — removes markdown separators (---), no rendering artifacts
- **Professional output** — ready for distribution to stakeholders, lawyers, investors

## When to Use This Skill

✓ Exporting due diligence responses to Word  
✓ Converting documentation for client delivery  
✓ Creating professional reports from markdown  
✓ Sharing structured content with non-technical stakeholders  
✓ Any markdown → Word conversion task

## How to Use

### Basic Command
```bash
python3 convert_md_to_docx.py input.md output.docx
```

### Examples

**Single file conversion:**
```bash
python3 convert_md_to_docx.py report.md report.docx
```

**Batch conversion:**
```bash
for file in *.md; do
  python3 convert_md_to_docx.py "$file" "${file%.md}.docx"
done
```

**In Claude Code:**
```bash
# Convert DD response
python3 convert_md_to_docx.py ORCANOS_DD_FINAL.md ORCANOS_DD_FINAL.docx

# Convert and move to outputs
python3 convert_md_to_docx.py input.md output.docx
```

## What Gets Converted

| Markdown | Word Output |
|----------|-----------|
| `**text**` | **text** (bold) |
| `*text*` | *text* (italic) |
| `[link](url)` | Blue underlined hyperlink |
| Tables | Formatted with shaded headers |
| Bullet lists | Proper indentation |
| `---` separator | Removed automatically |
| `✅` emoji | `✓` (Unicode checkmark) |
| `📁` emoji | `▶` (Unicode arrow) |
| `⚠️` emoji | `⚠` (Unicode warning) |

## Installation

### Required dependency
```bash
pip install python-docx
```

### Get the script
- Download `convert_md_to_docx.py` from this skill
- Place in your project directory or PATH

## File Structure

```
markdown-to-docx/
├── SKILL.md (this file)
└── scripts/
    └── convert_md_to_docx.py (the converter)
```

## Output Format

Generated .docx files include:
- Calibri font for body text
- Proper spacing and margins
- Professional table formatting
- Clickable hyperlinks
- Clean, readable typography

## Tips

- **Large documents**: Script handles files of any size
- **Unicode symbols**: Better compatibility than emoji across Windows/Mac/Linux
- **Batch processing**: Use loops for multiple files
- **Status tracking**: Use status indicators in markdown for visibility (✓ for done, ⚠ for warnings, etc.)

## Common Scenarios

**Due Diligence Documents**
```bash
python3 convert_md_to_docx.py DD_RESPONSE.md DD_RESPONSE.docx
# Perfect for sharing with lawyers, investors, acquirers
```

**Multi-file Reports**
```bash
for section in intro methodology findings; do
  python3 convert_md_to_docx.py $section.md output/$section.docx
done
```

**Integration with workflows**
```bash
# Generate markdown, then convert to Word for distribution
python3 script.py > report.md
python3 convert_md_to_docx.py report.md report.docx
```

---

Ready to use. No complications. Just markdown → professional Word documents.
