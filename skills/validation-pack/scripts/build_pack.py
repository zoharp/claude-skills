#!/usr/bin/env python3
"""
build_pack.py — render a validation package from its JSON source.

One source (pack.json + one JSON file per module) renders six controlled documents:

    VP   Validation Plan (scope, approach, Part 11 / AI / security / data-integrity assessment)
    URS  User Requirements Specification
    SRS  Software Requirements Specification
    STD  Software Test Description (the validation test protocol)
    RTM  Requirements Traceability Matrix
    STR  Software Test Report

The STR and the status column of the RTM come ONLY from a results.json written by
run_validation.py. With no results file, they say "Not executed" — this script never
invents a result.

Usage:
    python build_pack.py --pack validation/pack.json [--results validation/results/<run>/results.json]
                         [--out validation/docs]
"""

import argparse
import datetime
import hashlib
import html
import json
import os
import sys
from pathlib import Path

DOCS = [
    ("VP", "Validation Plan"),
    ("URS", "User Requirements Specification"),
    ("SRS", "Software Requirements Specification"),
    ("STD", "Software Test Description"),
    ("RTM", "Requirements Traceability Matrix"),
    ("STR", "Software Test Report"),
]
STATUS_ORDER = ["Fail", "Blocked", "Not run", "Pass"]


def esc(s):
    return html.escape("" if s is None else str(s))


# ─────────────────────────────────────────────────────────────────────────────
# Loading
# ─────────────────────────────────────────────────────────────────────────────

def load_pack(pack_path: Path) -> dict:
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    base = pack_path.parent
    for m in pack.get("modules", []):
        if m.get("file"):
            m.update(json.loads((base / m["file"]).read_text(encoding="utf-8")))
        for k in ("urs", "srs", "tests"):
            m.setdefault(k, [])
    _check(pack)
    return pack


def _check(pack):
    """Fail loudly on a broken trace — a dangling ID would render as a clean-looking gap."""
    errors = []
    urs_ids, srs_ids, test_ids = set(), set(), set()
    for m in pack["modules"]:
        for u in m["urs"]:
            if u["id"] in urs_ids:
                errors.append(f"duplicate URS id {u['id']}")
            urs_ids.add(u["id"])
        for s in m["srs"]:
            if s["id"] in srs_ids:
                errors.append(f"duplicate SRS id {s['id']}")
            srs_ids.add(s["id"])
        for t in m["tests"]:
            if t["id"] in test_ids:
                errors.append(f"duplicate test id {t['id']}")
            test_ids.add(t["id"])
    for m in pack["modules"]:
        for s in m["srs"]:
            if s["urs"] not in urs_ids:
                errors.append(f"{s['id']} traces to unknown {s['urs']}")
        for t in m["tests"]:
            for s in t["srs"]:
                if s not in srs_ids:
                    errors.append(f"{t['id']} traces to unknown {s}")
    tested = {s for m in pack["modules"] for t in m["tests"] for s in t["srs"]}
    for s in srs_ids - tested:
        print(f"WARNING: {s} has no validation test", file=sys.stderr)
    if errors:
        sys.exit("pack.json errors:\n  " + "\n  ".join(errors))


def load_results(path):
    if not path:
        return None
    p = Path(path)
    raw = p.read_bytes()
    res = json.loads(raw.decode("utf-8"))
    res["_sha256"] = hashlib.sha256(raw).hexdigest()
    res["_path"] = p
    return res


# ─────────────────────────────────────────────────────────────────────────────
# Lookups
# ─────────────────────────────────────────────────────────────────────────────

class Index:
    def __init__(self, pack, results):
        self.pack = pack
        self.results = results
        self.urs = {u["id"]: (m, u) for m in pack["modules"] for u in m["urs"]}
        self.srs = {s["id"]: (m, s) for m in pack["modules"] for s in m["srs"]}
        self.tests = {t["id"]: (m, t) for m in pack["modules"] for t in m["tests"]}

    def srs_of(self, urs_id):
        return [s for _, s in self.srs.values() if s["urs"] == urs_id]

    def tests_of_srs(self, srs_id):
        return [t for _, t in self.tests.values() if srs_id in t["srs"]]

    def tests_of_urs(self, urs_id):
        ids = {s["id"] for s in self.srs_of(urs_id)}
        return [t for _, t in self.tests.values() if ids & set(t["srs"])]

    def urs_of_test(self, t):
        return sorted({self.srs[s][1]["urs"] for s in t["srs"]})

    def risk_of_test(self, t):
        levels = [self.urs[u][1].get("risk", "") for u in self.urs_of_test(t)]
        return "High" if "High" in levels else (levels[0] if levels else "")

    def result(self, test_id):
        if not self.results:
            return None
        return self.results.get("tests", {}).get(test_id)

    def status(self, test_id):
        r = self.result(test_id)
        return r["status"] if r else "Not run"

    def rollup(self, tests):
        sts = [self.status(t["id"]) for t in tests]
        if not sts:
            return "Not run"
        for s in STATUS_ORDER[:3]:
            if s in sts:
                return s
        return "Pass"


# ─────────────────────────────────────────────────────────────────────────────
# HTML scaffolding
# ─────────────────────────────────────────────────────────────────────────────

CSS = """
:root{--bg:#fff;--surface:#f6f8fa;--surface-2:#eef2f6;--text:#1b2430;--muted:#5b6776;--border:#d5dce4;
--accent:#1f5fa8;--accent-soft:#e5eefa;--pass:#1e7a46;--pass-soft:#e3f4ea;--fail:#b3261e;--fail-soft:#fbe6e4;
--warn:#8a5a00;--warn-soft:#fdf1d8}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#12161c;--surface:#1a2029;--surface-2:#212935;
--text:#e3e8ee;--muted:#9aa6b4;--border:#333d4a;--accent:#7fb0ec;--accent-soft:#1d2c40;--pass:#6fcf97;--pass-soft:#173426;
--fail:#f2938b;--fail-soft:#3b1d1b;--warn:#f0c062;--warn-soft:#382c12}}
:root[data-theme="dark"]{--bg:#12161c;--surface:#1a2029;--surface-2:#212935;--text:#e3e8ee;--muted:#9aa6b4;--border:#333d4a;
--accent:#7fb0ec;--accent-soft:#1d2c40;--pass:#6fcf97;--pass-soft:#173426;--fail:#f2938b;--fail-soft:#3b1d1b;--warn:#f0c062;--warn-soft:#382c12}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:14px/1.55 "Segoe UI",system-ui,-apple-system,sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:0 16px 64px}
nav.docs{border-bottom:1px solid var(--border);background:var(--surface)}
nav.docs .wrap{display:flex;flex-wrap:wrap;gap:4px 18px;padding-top:10px;padding-bottom:10px}
nav.docs a{color:var(--muted);text-decoration:none;font-size:13px}
nav.docs a.on{color:var(--accent);font-weight:600}
header.doc{padding:28px 0 6px}
header.doc h1{margin:0 0 4px;font-size:25px}
header.doc .sub{color:var(--muted)}
h2{font-size:20px;margin:36px 0 12px;padding-bottom:6px;border-bottom:2px solid var(--accent)}
h3{font-size:16px;margin:22px 0 8px}
p{margin:8px 0}
.muted{color:var(--muted)}
table{width:100%;border-collapse:collapse;margin:8px 0 16px;font-size:13px}
th,td{border:1px solid var(--border);padding:6px 8px;text-align:left;vertical-align:top}
th{background:var(--surface-2);font-weight:600}
.scroll{overflow-x:auto}
.meta td:first-child{width:200px;font-weight:600;background:var(--surface)}
.callout{border-left:4px solid var(--accent);background:var(--accent-soft);padding:10px 14px;border-radius:0 6px 6px 0;margin:12px 0}
.callout.warn{border-color:var(--warn);background:var(--warn-soft)}
.id{font-family:Consolas,"Cascadia Mono",monospace;font-weight:600;white-space:nowrap}
code{font-family:Consolas,"Cascadia Mono",monospace;font-size:12.5px;background:var(--surface-2);padding:1px 4px;border-radius:4px}
.pill{display:inline-block;padding:1px 8px;border-radius:10px;font-size:12px;font-weight:600;white-space:nowrap}
.risk-High,.st-Fail,.p11-Gap{background:var(--fail-soft);color:var(--fail)}
.risk-Medium,.st-Blocked,.p11-Partial{background:var(--warn-soft);color:var(--warn)}
.risk-Low,.st-Pass,.p11-Met{background:var(--pass-soft);color:var(--pass)}
.st-Notrun,.p11-NA,.p11-Base{background:var(--surface-2);color:var(--muted)}
.card{border:1px solid var(--border);border-radius:8px;padding:14px 16px;margin:14px 0}
.card h3{margin-top:0}
.kv{display:grid;grid-template-columns:140px 1fr;gap:2px 12px;margin:6px 0}
.kv>div:nth-child(odd){color:var(--muted)}
.tiles{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin:12px 0}
.tile{border:1px solid var(--border);border-radius:8px;padding:10px 12px;background:var(--surface)}
.tile .n{font-size:24px;font-weight:700}.tile .l{font-size:12px;color:var(--muted)}
.module-planned{opacity:.75}
.sign td{height:44px}
@media (max-width:720px){.tiles{grid-template-columns:repeat(2,minmax(0,1fr))}.kv{grid-template-columns:1fr}}
@media print{nav.docs{display:none}body{font-size:11px;background:#fff;color:#000}.card{break-inside:avoid}h2{break-before:page}h2.first{break-before:auto}}
"""


def pill(text, cls_prefix):
    cls = cls_prefix + str(text).replace(" ", "").replace("/", "")
    return f'<span class="pill {cls}">{esc(text)}</span>'


def risk_pill(level):
    return f'<span class="pill risk-{esc(level)}">{esc(level)} risk</span>'


def st_pill(s):
    return pill(s, "st-")


def page(pack, code, title, body):
    meta = pack["meta"]
    doc_id = f'{meta["doc_prefix"]}-{code}'
    nav = "".join(
        f'<a href="{c}.html" class="{"on" if c == code else ""}">{c} · {esc(t)}</a>' for c, t in DOCS)
    head_tbl = f"""
<table class="meta">
  <tr><td>Document</td><td>{esc(title)}</td></tr>
  <tr><td>Document ID</td><td class="id">{esc(doc_id)}</td></tr>
  <tr><td>Revision / status</td><td>{esc(meta["revision"])} — {esc(meta["status"])}</td></tr>
  <tr><td>Product / version</td><td>{esc(meta["product"])}, v{esc(meta["product_version"])}</td></tr>
  <tr><td>Base system</td><td>{esc(meta.get("base_system", ""))}</td></tr>
  <tr><td>Date</td><td>{esc(meta["date"])}</td></tr>
  <tr><td>Package</td><td>{" · ".join(f'<span class="id">{meta["doc_prefix"]}-{c}</span>' for c, _ in DOCS)}</td></tr>
</table>"""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(code)} {esc(meta.get("short_name", meta["product"]))}</title><style>{CSS}</style></head>
<body><nav class="docs"><div class="wrap">{nav}</div></nav>
<div class="wrap"><header class="doc"><h1>{esc(title)}</h1><div class="sub">{esc(meta["product"])}</div></header>
{head_tbl}
{body}
{approval_block(meta)}
</div></body></html>"""


def approval_block(meta=None):
    # meta.signing = "electronic": the pack is e-signed in the tool that serves it, which prints its own
    # signature table at the TOP of every document — so no blank paper table at the bottom (2026-11-04).
    if (meta or {}).get("signing") == "electronic":
        return ""
    return """<h2>Approval</h2><table class="sign">
<tr><th style="width:26%">Role</th><th>Name</th><th>Signature</th><th style="width:18%">Date</th></tr>
<tr><td>Author</td><td></td><td></td><td></td></tr>
<tr><td>Reviewer (QA)</td><td></td><td></td><td></td></tr>
<tr><td>Approver (QA / RA)</td><td></td><td></td><td></td></tr></table>"""


def table(cols, rows, raw=False):
    head = "".join(f"<th>{esc(c)}</th>" for c in cols)
    body = "".join(
        "<tr>" + "".join(f"<td>{c if raw else esc(c)}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="scroll"><table><tr>{head}</tr>{body}</table></div>'


def ulist(items):
    return "<ul>" + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>"


def module_header(m):
    planned = m.get("status") != "in-scope"
    tag = "" if not planned else ' <span class="pill st-Notrun">planned — not in this revision</span>'
    return f'<h2 id="{esc(m["id"])}">{esc(m["name"])}{tag}</h2><p class="muted">{esc(m.get("summary", ""))}</p>', planned


# ─────────────────────────────────────────────────────────────────────────────
# Documents
# ─────────────────────────────────────────────────────────────────────────────

def doc_vp(pack, ix):
    plan = pack["plan"]
    c = pack.get("compliance", {})
    out = ['<h2 class="first">1. Purpose</h2>', f"<p>{esc(plan['purpose'])}</p>",
           "<h3>Intended use</h3>", f"<p>{esc(plan['intended_use'])}</p>"]
    if plan.get("validation_not_verification"):
        out.append(f'<div class="callout">{esc(plan["validation_not_verification"])}</div>')
    if plan.get("base_system_reliance"):
        out += ["<h3>Reliance on the base-system validation</h3>", f"<p>{esc(plan['base_system_reliance'])}</p>"]

    out.append("<h2>2. Scope — modules</h2>")
    rows = []
    for m in pack["modules"]:
        in_scope = m.get("status") == "in-scope"
        scope = (f'<span class="pill {"st-Pass" if in_scope else "st-Notrun"}">'
                 f'{"In scope" if in_scope else "Planned"}</span>')
        rows.append([f'<span class="id">{esc(m["id"])}</span>', esc(m["name"]), scope,
                     str(len(m["urs"])), str(len(m["tests"])), esc(m.get("summary", ""))])
    out.append(table(["ID", "Module", "This revision", "URS", "Tests", "What it does"], rows, raw=True))
    if plan.get("out_of_scope"):
        out += ["<h3>Out of scope</h3>", ulist(plan["out_of_scope"])]

    out.append("<h2>3. Approach</h2>")
    out.append(f"<p>{esc(plan.get('approach', ''))}</p>")
    if plan.get("risk_levels"):
        out.append(table(["Risk", "Meaning", "Assurance applied"],
                         [[pill(r["level"], "risk-"), esc(r["meaning"]), esc(r["assurance"])]
                          for r in plan["risk_levels"]], raw=True))
    if plan.get("automation"):
        out += ["<h3>Automated execution</h3>", f"<p>{esc(plan['automation'])}</p>"]
    if plan.get("execution_rules"):
        out += ["<h3>Execution and acceptance rules</h3>", ulist(plan["execution_rules"])]
    if plan.get("roles"):
        out += ["<h3>Roles</h3>", table(["Role", "Responsibility"], [[r["role"], r["duty"]] for r in plan["roles"]])]
    if pack.get("environment"):
        out += ["<h3>Environment</h3>", table(["Item", "Value"], [[e["item"], e["value"]] for e in pack["environment"]])]

    n = 4
    p11 = c.get("part11")
    if p11:
        out.append(f"<h2>{n}. 21 CFR Part 11 assessment</h2>")
        n += 1
        out.append(f"<p>{esc(p11.get('intro', ''))}</p>")
        out.append(table(["Clause", "Requirement", "Base system", "This add-on", "Evidence", "Status"],
                         [[f'<span class="id">{esc(r["clause"])}</span>', esc(r["requirement"]), esc(r["base"]),
                           esc(r["addon"]), esc(r.get("evidence", "")), pill(r["status"], "p11-")]
                          for r in p11["rows"]], raw=True))
        if p11.get("legend"):
            out.append(f'<p class="muted">{esc(p11["legend"])}</p>')

    ai = c.get("ai")
    if ai:
        out.append(f"<h2>{n}. Use of artificial intelligence</h2>")
        n += 1
        out.append(f"<p>{esc(ai.get('intro', ''))}</p>")
        if ai.get("features"):
            out.append(table(["Module", "AI function", "What the model receives", "Human control"],
                             [[f["module"], f["feature"], f["data_sent"], f["control"]] for f in ai["features"]]))
        if ai.get("controls"):
            out += ["<h3>Controls common to every AI function</h3>", ulist(ai["controls"])]
        if ai.get("validation"):
            out += ["<h3>How AI functions are validated</h3>", f"<p>{esc(ai['validation'])}</p>"]
        if ai.get("gaps"):
            out += ["<h3>Open items</h3>", ulist(ai["gaps"])]

    sec = c.get("security")
    if sec:
        out.append(f"<h2>{n}. Security</h2>")
        n += 1
        out.append(f"<p>{esc(sec.get('intro', ''))}</p>")
        if sec.get("controls"):
            out.append(table(["Area", "Control", "Reference"], [[s["area"], s["summary"], s["ref"]] for s in sec["controls"]]))
        if sec.get("gaps"):
            out += ["<h3>Known gaps and residual risk</h3>",
                    table(["#", "Gap", "Status"], [[g["id"], g["gap"], g["status"]] for g in sec["gaps"]])]

    di = c.get("data_integrity")
    if di:
        out.append(f"<h2>{n}. Data integrity (ALCOA+)</h2>")
        n += 1
        out.append(f"<p>{esc(di.get('intro', ''))}</p>")
        out.append(table(["Principle", "How it is met"], [[r["principle"], r["how"]] for r in di["rows"]]))

    if pack.get("references"):
        out.append(f"<h2>{n}. References</h2>")
        out.append(table(["Ref", "Document", "Relevance"], [[r["id"], r["title"], r.get("note", "")] for r in pack["references"]]))
    return "".join(out)


def doc_urs(pack, ix):
    out = ['<p class="muted">User needs, written from the user\'s side and grouped by module. '
           'The <i>how</i> is in the SRS.</p>']
    for m in pack["modules"]:
        hdr, planned = module_header(m)
        out.append(hdr)
        if planned and not m["urs"]:
            continue
        for u in m["urs"]:
            out.append(f"""<div class="card"><h3><span class="id">{esc(u["id"])}</span> — {esc(u["title"])}
 {risk_pill(u["risk"])}</h3>
<p class="muted">{esc(u.get("feature", ""))}</p>
<div class="kv"><div>User</div><div>{esc(u.get("actor", ""))}</div>
<div>User need</div><div>{esc(u["need"])}</div>
<div>Risk rationale</div><div>{esc(u.get("risk_why", ""))}</div>
<div>Met by</div><div>{", ".join(f'<span class="id">{esc(s["id"])}</span>' for s in ix.srs_of(u["id"]))}</div></div></div>""")
    return "".join(out)


def doc_srs(pack, ix):
    out = ['<p class="muted">How the software meets each user requirement. Every item is checked by at least one validation test (see RTM).</p>']
    for m in pack["modules"]:
        hdr, planned = module_header(m)
        out.append(hdr)
        for u in m["urs"]:
            out.append(f'<h3><span class="id">{esc(u["id"])}</span> — {esc(u["title"])}</h3>')
            out.append(table(["ID", "Specification", "Validated by"],
                             [[f'<span class="id">{esc(s["id"])}</span>', esc(s["text"]),
                               ", ".join(f'<span class="id">{esc(t["id"])}</span>' for t in ix.tests_of_srs(s["id"]))]
                              for s in ix.srs_of(u["id"])], raw=True))
    return "".join(out)


def tds_block(m):
    tds = m.get("tds")
    if not tds:
        return ""
    out = [f'<h3>Test data set</h3><p>{esc(tds.get("intro", ""))}</p>']
    for t in tds.get("tables", []):
        out.append(f"<p><b>{esc(t['title'])}</b></p>")
        out.append(table(t["columns"], t["rows"]))
    return "".join(out)


def doc_std(pack, ix):
    out = []
    if pack["plan"].get("execution_rules"):
        out += ['<h2 class="first">Execution rules</h2>', ulist(pack["plan"]["execution_rules"])]
    for m in pack["modules"]:
        hdr, planned = module_header(m)
        out.append(hdr)
        if not m["tests"]:
            continue
        if m.get("execution_order"):
            out.append(f'<p class="muted">Execution order: {esc(m["execution_order"])}</p>')
        out.append(tds_block(m))
        for t in m["tests"]:
            a = t.get("automation", {})
            auto = f'<code>{esc(a.get("file", ""))}::{esc(a.get("function", ""))}</code>' if a else "Manual"
            risk = ix.risk_of_test(t)
            steps = "".join(f"<tr><td>{i}</td><td>{esc(s[0])}</td><td>{esc(s[1])}</td></tr>"
                            for i, s in enumerate(t["steps"], 1))
            slow = ' <span class="pill st-Blocked">long-running</span>' if t.get("slow") else ""
            out.append(f"""<div class="card"><h3><span class="id">{esc(t["id"])}</span> — {esc(t["title"])}
 {risk_pill(risk)}{slow}</h3>
<div class="kv"><div>Validates</div><div>{", ".join(f'<span class="id">{u}</span>' for u in ix.urs_of_test(t))} ·
 {", ".join(f'<span class="id">{esc(s)}</span>' for s in t["srs"])}</div>
<div>Prerequisites</div><div>{esc(t.get("pre", ""))}</div>
<div>Evidence</div><div>{esc(t.get("evidence", ""))}</div>
<div>Automated by</div><div>{auto}</div></div>
<div class="scroll"><table><tr><th style="width:32px">#</th><th>Action</th><th>Expected result</th></tr>{steps}</table></div></div>""")
    return "".join(out)


def run_banner(ix):
    r = ix.results
    if not r:
        return ('<div class="callout warn"><b>Not executed.</b> No validation run is attached. '
                'Statuses read “Not run” until <code>run_validation.py</code> has produced a results file.</div>')
    return (f'<div class="callout">Results from run <span class="id">{esc(r["run_id"])}</span> — '
            f'{esc(r.get("started_utc", ""))} UTC, target {esc(r.get("target_url", ""))}. '
            f'results.json SHA-256 <code>{esc(r["_sha256"][:16])}…</code></div>')


def doc_rtm(pack, ix):
    out = [run_banner(ix)]
    for m in pack["modules"]:
        hdr, planned = module_header(m)
        out.append(hdr)
        if not m["urs"]:
            continue
        rows = []
        for u in m["urs"]:
            srs = ix.srs_of(u["id"])
            for i, s in enumerate(srs):
                tests = ix.tests_of_srs(s["id"])
                cells = []
                if i == 0:
                    cells.append(f'<td rowspan="{len(srs)}"><span class="id">{esc(u["id"])}</span><br>{esc(u["title"])}</td>')
                    cells.append(f'<td rowspan="{len(srs)}">{pill(u["risk"], "risk-")}</td>')
                cells.append(f'<td><span class="id">{esc(s["id"])}</span></td>')
                cells.append("<td>" + ("<br>".join(f'<span class="id">{esc(t["id"])}</span> {st_pill(ix.status(t["id"]))}'
                                                   for t in tests) or pill("No test", "st-Fail")) + "</td>")
                cells.append("<td>" + "<br>".join(
                    f'<code>{esc(t.get("automation", {}).get("function", "manual"))}</code>' for t in tests) + "</td>")
                if i == 0:
                    cells.append(f'<td rowspan="{len(srs)}">{st_pill(ix.rollup(ix.tests_of_urs(u["id"])))}</td>')
                rows.append("<tr>" + "".join(cells) + "</tr>")
        out.append('<div class="scroll"><table><tr><th>User requirement</th><th>Risk</th><th>Software requirement</th>'
                   '<th>Validation test</th><th>Automated test</th><th>Status</th></tr>' + "".join(rows) + "</table></div>")
    return "".join(out)


def doc_str(pack, ix, out_dir: Path):
    r = ix.results
    out = [run_banner(ix)]
    all_tests = [t for m in pack["modules"] for t in m["tests"]]
    counts = {k: 0 for k in STATUS_ORDER}
    for t in all_tests:
        counts[ix.status(t["id"])] += 1
    out.append('<h2 class="first">1. Summary</h2><div class="tiles">' + "".join(
        f'<div class="tile"><div class="n">{n}</div><div class="l">{l}</div></div>'
        for l, n in [("Planned", len(all_tests)), ("Passed", counts["Pass"]), ("Failed", counts["Fail"]),
                     ("Blocked", counts["Blocked"]), ("Not run", counts["Not run"])]) + "</div>")
    if r:
        out.append(table(["Item", "Value"], [
            ["Run ID", r["run_id"]], ["Started (UTC)", r.get("started_utc", "")], ["Finished (UTC)", r.get("finished_utc", "")],
            ["Target", r.get("target_url", "")], ["Application version (as reported by target)", r.get("app_version", "")],
            ["Base-system account", r.get("tenant", "")], ["Browser", r.get("browser", "")],
            ["Executed on / by", f'{r.get("host", "")} / {r.get("os_user", "")}'],
            ["Command", r.get("command", "")], ["Results file SHA-256", r["_sha256"]]]))

    out.append("<h2>2. Requirement coverage</h2>")
    rows = []
    for m in pack["modules"]:
        for u in m["urs"]:
            tests = ix.tests_of_urs(u["id"])
            passed = sum(1 for t in tests if ix.status(t["id"]) == "Pass")
            rows.append([esc(m["name"]), f'<span class="id">{esc(u["id"])}</span> {esc(u["title"])}', pill(u["risk"], "risk-"),
                         f"{passed} / {len(tests)}", st_pill(ix.rollup(tests))])
    out.append(table(["Module", "User requirement", "Risk", "Tests passed", "Status"], rows, raw=True))

    out.append("<h2>3. Results by test</h2>")
    res_dir = ix.results["_path"].parent if r else None
    for m in pack["modules"]:
        if not m["tests"]:
            continue
        out.append(f"<h3>{esc(m['name'])}</h3>")
        for t in m["tests"]:
            res = ix.result(t["id"]) or {}
            steps_res = {s["n"]: s for s in res.get("steps", [])}
            rows = []
            for i, (action, expected) in enumerate(t["steps"], 1):
                s = steps_res.get(i, {})
                ev = ""
                if s.get("evidence") and res_dir:
                    rel = os.path.relpath(res_dir / s["evidence"], out_dir).replace("\\", "/")
                    ev = f'<a href="{esc(rel)}">{esc(Path(s["evidence"]).name)}</a>'
                rows.append([str(i), esc(expected), esc(s.get("actual", "")), st_pill(s.get("status", "Not run")), ev])
            files = ""
            if res.get("files") and res_dir:
                files = "<p class='muted'>Files kept: " + ", ".join(
                    f'<a href="{esc(os.path.relpath(res_dir / f, out_dir).replace(chr(92), "/"))}">{esc(Path(f).name)}</a>'
                    for f in res["files"]) + "</p>"
            err = f'<div class="callout warn">{esc(res["error"])}</div>' if res.get("error") else ""
            out.append(f"""<div class="card"><h3><span class="id">{esc(t["id"])}</span> — {esc(t["title"])} {st_pill(ix.status(t["id"]))}</h3>
<div class="kv"><div>Validates</div><div>{", ".join(ix.urs_of_test(t))}</div>
<div>Duration</div><div>{esc(res.get("duration_s", "—"))} s</div></div>{err}
{table(["#", "Expected result", "Actual result", "Status", "Evidence"], rows, raw=True)}{files}</div>""")

    out.append("<h2>4. Deviations</h2>")
    devs = (r or {}).get("deviations", [])
    failing = [t for t in all_tests if ix.status(t["id"]) in ("Fail", "Blocked")]
    if failing and not devs:
        out.append('<div class="callout warn">Each failed or blocked test below needs a deviation record '
                   '(description, impact on the requirement, resolution) before this report can be approved.</div>')
    out.append(table(["Test", "Status", "Recorded error", "Impact / resolution"],
                     [[t["id"], ix.status(t["id"]), (ix.result(t["id"]) or {}).get("error", ""), ""] for t in failing]
                     or [["—", "—", "No failed or blocked tests.", ""]]))

    out.append("<h2>5. Conclusion</h2>")
    if not r:
        out.append('<div class="callout warn">Not executed — no conclusion can be drawn.</div>')
    elif counts["Pass"] == len(all_tests):
        out.append(f'<div class="callout">All {len(all_tests)} validation tests passed in run {esc(r["run_id"])}. '
                   + ('Subject to the signatures at the top of this document' if pack['meta'].get('signing') == 'electronic'
                      else 'Subject to review and approval below')
                   + ', the in-scope modules meet their user requirements for the intended use.</div>')
    else:
        out.append(f'<div class="callout warn">{counts["Pass"]} of {len(all_tests)} tests passed '
                   f'({counts["Fail"]} failed, {counts["Blocked"]} blocked, {counts["Not run"]} not run). '
                   'The add-on is not validated for its intended use until every test passes or each deviation is resolved.</div>')
    return "".join(out)


# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pack", required=True)
    ap.add_argument("--results")
    ap.add_argument("--out")
    a = ap.parse_args()

    pack_path = Path(a.pack).resolve()
    pack = load_pack(pack_path)
    results = load_results(a.results)
    out_dir = Path(a.out).resolve() if a.out else pack_path.parent / "docs"
    out_dir.mkdir(parents=True, exist_ok=True)
    ix = Index(pack, results)

    builders = {"VP": doc_vp, "URS": doc_urs, "SRS": doc_srs, "STD": doc_std, "RTM": doc_rtm}
    for code, title in DOCS:
        body = doc_str(pack, ix, out_dir) if code == "STR" else builders[code](pack, ix)
        (out_dir / f"{code}.html").write_text(page(pack, code, title, body), encoding="utf-8")
    print(f"Wrote {len(DOCS)} documents to {out_dir}"
          + (f" (results: run {results['run_id']})" if results else " (no results — STR says Not executed)"))


if __name__ == "__main__":
    main()
