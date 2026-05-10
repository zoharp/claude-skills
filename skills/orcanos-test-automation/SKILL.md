---
name: orcanos-test-automation
description: Use when setting up or running the test automation infrastructure for any Orcanos project. Covers pytest project layout, conftest.py patterns, run_tests.py (spin up test backend + run pytest + generate HTML report), and JSON-driven test definitions. Extracted from the Orcanos QMS test suite.
---

# Orcanos Test Automation

Every Orcanos project with a FastAPI backend uses the same test infrastructure. The skill ships ready-to-use template files — **copy them rather than regenerating from scratch**.

---

## Setting up tests on a new project

This skill's `templates/tests/` folder contains all the files you need. Copy them directly:

```
skill-folder/orcanos-test-automation/templates/tests/
    conftest.py                  → <project>/tests/conftest.py
    run_tests.py                 → <project>/tests/run_tests.py
    run_ui.bat                   → <project>/tests/run_ui.bat
    start_test_backend.bat       → <project>/tests/start_test_backend.bat
    test_definitions.json        → <project>/tests/test_definitions.json
    app/
        test_queries.py          → <project>/tests/app/test_queries.py
```

Also create the empty reports folder:
```
<project>/tests/reports/.gitkeep
```

After copying:
1. In `run_tests.py` — update `FE_VERSION` and `TEST_FILE` name if you renamed `test_queries.py`
2. In `test_queries.py` — replace placeholder queries (marked with comments) with project-specific ones
3. In `test_definitions.json` — add your project's specific test cases
4. Extend `TC_MAP` in `run_tests.py` if you add new test classes

The runner spins up an isolated test backend on a separate port, runs pytest, then generates a self-contained HTML report.

---

## Folder layout

```
project-root/
├── tests/
│   ├── conftest.py          ← shared fixtures and startup health check
│   ├── run_tests.py         ← entry point: start backend → run pytest → HTML report
│   ├── run_ui.bat           ← Windows: open latest.html in browser
│   ├── start_test_backend.bat ← Windows: start test backend on port 8001
│   ├── test_definitions.json ← JSON-driven test cases (optional but recommended)
│   ├── app/
│   │   └── test_user_queries.py  ← main test file (or split by feature)
│   └── reports/
│       └── latest.html      ← always overwritten by last run
├── backend/
│   └── api.py               ← FastAPI app
└── run.bat                  ← full stack startup
```

---

## conftest.py

Fail fast: if the backend is unreachable at session start, abort immediately rather than letting all tests hang.

```python
"""tests/conftest.py — shared pytest config and fixtures."""

import os
import pytest
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with -m 'not slow')")
    config.addinivalue_line("markers", "integration: marks tests that require a live backend")


def pytest_sessionstart(session):
    """Abort the entire run if the backend is not reachable."""
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=5)
        resp.raise_for_status()
    except Exception as e:
        pytest.exit(
            f"\n❌ Backend not reachable at {BACKEND_URL}.\n"
            f"   Start it with: uvicorn backend.api:app --reload\n"
            f"   Error: {e}",
            returncode=1,
        )
```

---

## run_tests.py

The main entry point. Does three things: starts a clean test backend on port 8001, runs pytest against it, generates an HTML report.

```python
"""
tests/run_tests.py
Starts a test backend (AUTH_DISABLED=true, port 8001), runs pytest,
generates an HTML report in tests/reports/<timestamp>/index.html.

Usage:
    python tests/run_tests.py
"""

import os, sys, io, time, signal, subprocess, datetime, argparse, requests
import xml.etree.ElementTree as ET
from pathlib import Path

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

FE_VERSION = "1.0.0"          # update to match your frontend version
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT   = SCRIPT_DIR.parent
TEST_FILE   = SCRIPT_DIR / "app" / "test_user_queries.py"
REPORTS_DIR = SCRIPT_DIR / "reports"
TEST_BACKEND_PORT = 8001
TEST_BACKEND_URL  = f"http://localhost:{TEST_BACKEND_PORT}"


# ── Backend lifecycle ────────────────────────────────────────────────────────

def start_test_backend() -> subprocess.Popen:
    env = os.environ.copy()
    env["AUTH_DISABLED"] = "true"
    # Load .env so secrets are available without exporting them globally
    dotenv_path = REPO_ROOT / ".env"
    if dotenv_path.exists():
        for line in dotenv_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env.setdefault(k.strip(), v.strip())

    cmd = [
        sys.executable, "-m", "uvicorn",
        "backend.api:app",
        "--host", "127.0.0.1",
        "--port", str(TEST_BACKEND_PORT),
        "--log-level", "warning",
    ]
    print(f"[*] Starting test backend on port {TEST_BACKEND_PORT} (AUTH_DISABLED=true)...")
    proc = subprocess.Popen(cmd, cwd=str(REPO_ROOT), env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in range(30):
        time.sleep(1)
        try:
            r = requests.get(f"{TEST_BACKEND_URL}/health", timeout=2)
            if r.status_code == 200:
                print(f"[OK] Test backend ready ({i+1}s)")
                return proc
        except Exception:
            pass
        print(f"[*] Waiting... ({i+1}/30)")
    proc.terminate()
    raise RuntimeError("Test backend failed to start within 30s")


def stop_test_backend(proc: subprocess.Popen):
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def get_backend_version(url: str) -> str:
    try:
        return requests.get(f"{url}/health", timeout=5).json().get("backend_version", "unknown")
    except Exception as e:
        return f"unreachable ({e})"


# ── pytest runner ─────────────────────────────────────────────────────────────

def run_pytest(backend_url: str, junit_xml_path: Path) -> tuple[int, str]:
    env = os.environ.copy()
    env["AUTH_DISABLED"] = "true"
    env["BACKEND_URL"] = backend_url

    # Load .env into env
    dotenv_path = REPO_ROOT / ".env"
    if dotenv_path.exists():
        for line in dotenv_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env.setdefault(k.strip(), v.strip())

    cmd = [
        sys.executable, "-m", "pytest", str(TEST_FILE),
        "-v", "--tb=short", f"--junit-xml={junit_xml_path}",
        "--no-header", "-p", "no:warnings",
    ]
    lines = []
    MAX_CONSECUTIVE_ERRORS = 5
    consecutive_bad = 0
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True,
                            encoding="utf-8", errors="replace", cwd=str(REPO_ROOT))
    for line in proc.stdout:
        s = line.rstrip()
        if   " PASSED" in s: print(f"  \033[32mPASS\033[0m {s}"); consecutive_bad = 0
        elif " FAILED" in s: print(f"  \033[31mFAIL\033[0m {s}"); consecutive_bad = 0
        elif " ERROR"  in s: print(f"  \033[33m!\033[0m {s}"); consecutive_bad += 1
        else:                print(f"  {s}")
        lines.append(s)
        if consecutive_bad >= MAX_CONSECUTIVE_ERRORS:
            print(f"\n[!] {MAX_CONSECUTIVE_ERRORS} consecutive ERRORs — aborting.\n")
            proc.terminate()
            break
    proc.wait()
    return proc.returncode, "\n".join(lines)


# ── JUnit XML parser ─────────────────────────────────────────────────────────

def parse_junit(xml_path: Path) -> dict:
    if not xml_path.exists():
        return {}
    tree = ET.parse(xml_path)
    root = tree.getroot()
    suites_el = root.findall("testsuite") if root.tag == "testsuites" else [root]
    suites = {}
    for suite in suites_el:
        for tc in suite.findall("testcase"):
            cls = tc.get("classname", "unknown").split(".")[-1]
            failure = tc.find("failure")
            error   = tc.find("error")
            skipped = tc.find("skipped")
            if failure is not None:  status, detail = "FAIL",  failure.text or failure.get("message","")
            elif error is not None:  status, detail = "ERROR", error.text   or error.get("message","")
            elif skipped is not None: status, detail = "SKIP", skipped.get("message","")
            else:                    status, detail = "PASS",  ""
            suites.setdefault(cls, []).append({
                "name": tc.get("name",""), "status": status,
                "time_s": float(tc.get("time", 0)), "detail": detail,
            })
    return suites


# ── HTML report ───────────────────────────────────────────────────────────────

STATUS_COLOR = {"PASS":"#22c55e","FAIL":"#ef4444","ERROR":"#f97316","SKIP":"#a3a3a3"}
STATUS_ICON  = {"PASS":"✓","FAIL":"✗","ERROR":"!","SKIP":"–"}

# Map pytest class names → human-readable test-case labels
# Extend this dict when you add new test classes
TC_MAP = {
    "TestConnectivity":          "TC-00 — Connectivity / Sanity",
    "TestListAllDocuments":      "TC-01 — List ALL Documents",
    "TestKeywordSearch":         "TC-02 — Keyword / Full-text Search",
    "TestGeneralRAGQueries":     "TC-03 — General RAG Queries",
    "TestSpecificDocQueries":    "TC-04 — Specific Document Queries",
    "TestEdgeCases":             "TC-05 — Edge Cases & Robustness",
    "TestPerformance":           "TC-06 — Performance (soft thresholds)",
    "TestFromDefinitions":       "All Tests (JSON-driven)",
}


def render_suite(classname: str, tests: list) -> str:
    passed  = sum(1 for t in tests if t["status"] == "PASS")
    failed  = sum(1 for t in tests if t["status"] in ("FAIL","ERROR"))
    suite_ok = failed == 0
    color = STATUS_COLOR["PASS"] if suite_ok else STATUS_COLOR["FAIL"]
    tc_label = TC_MAP.get(classname, classname)
    rows = ""
    for t in tests:
        sc   = STATUS_COLOR[t["status"]]
        icon = STATUS_ICON[t["status"]]
        detail_html = ""
        if t["detail"]:
            esc = t["detail"].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
            detail_html = f'<pre class="detail">{esc[:800]}</pre>'
        rows += f"""
        <tr>
          <td><span class="badge" style="background:{sc}">{icon}</span></td>
          <td class="test-name">{t["name"]}</td>
          <td class="test-time">{t["time_s"]:.2f}s</td>
        </tr>
        {'<tr><td colspan="3">'+detail_html+'</td></tr>' if detail_html else ''}
        """
    pills = (f'<span class="pill pass">{passed} passed</span> '
             f'<span class="pill fail">{failed} failed</span>')
    collapsed = " collapsed" if suite_ok else ""
    return f"""
    <div class="suite{collapsed}">
      <div class="suite-header" onclick="this.parentElement.classList.toggle('collapsed')">
        <span class="suite-icon" style="color:{color}">{'✓' if suite_ok else '✗'}</span>
        <span class="suite-title">{tc_label}</span>
        <span class="suite-summary">{pills}</span>
        <span class="chevron">▾</span>
      </div>
      <div class="suite-body"><table class="test-table">{rows}</table></div>
    </div>
    """


def generate_html(suites, fe_version, be_version, backend_url, run_ts, console_output) -> str:
    all_tests     = [t for tests in suites.values() for t in tests]
    total_passed  = sum(1 for t in all_tests if t["status"] == "PASS")
    total_failed  = sum(1 for t in all_tests if t["status"] in ("FAIL","ERROR"))
    total         = len(all_tests)
    overall       = "PASS" if total_failed == 0 else "FAIL"
    overall_color = STATUS_COLOR["PASS"] if overall == "PASS" else STATUS_COLOR["FAIL"]
    suites_html   = "".join(render_suite(cls, tests) for cls, tests in suites.items())
    esc_console   = console_output.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/>
<title>Test Report {run_ts}</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f172a;color:#e2e8f0}}
  .header{{background:#1e293b;border-bottom:1px solid #334155;padding:20px 28px;display:flex;justify-content:space-between;align-items:center}}
  .header h1{{font-size:1.3rem;font-weight:700;color:#f1f5f9}}
  .header .meta{{font-size:0.78rem;color:#94a3b8;text-align:right;line-height:1.8}}
  .overall{{padding:20px 28px}}
  .overall-card{{background:#1e293b;border-radius:10px;padding:18px 24px;display:flex;align-items:center;gap:18px;border-left:5px solid {overall_color}}}
  .overall-status{{font-size:2.2rem;font-weight:800;color:{overall_color}}}
  .overall-counts{{font-size:0.95rem;color:#94a3b8}}
  .overall-counts strong{{color:#f1f5f9;font-size:1rem}}
  .versions{{display:flex;gap:10px;margin-left:auto}}
  .vtag{{background:#334155;border-radius:6px;padding:5px 12px;font-size:0.78rem;font-weight:600}}
  .vtag span{{color:#94a3b8;margin-right:5px}}
  .content{{padding:0 28px 40px}}
  .suite{{background:#1e293b;border-radius:8px;margin-bottom:10px;overflow:hidden;border:1px solid #334155;border-left:4px solid #22c55e}}
  .suite:not(.collapsed) .suite-body{{display:block}}
  .suite.collapsed .suite-body{{display:none}}
  .suite-header{{display:flex;align-items:center;gap:10px;padding:12px 16px;cursor:pointer;user-select:none}}
  .suite-header:hover{{background:#263344}}
  .suite-icon{{font-size:1rem;font-weight:700;width:18px;text-align:center}}
  .suite-title{{font-weight:600;font-size:0.9rem;flex:1}}
  .suite-summary{{font-size:0.78rem;color:#94a3b8}}
  .chevron{{color:#64748b;transition:transform 0.2s;font-size:0.8rem}}
  .suite.collapsed .chevron{{transform:rotate(-90deg)}}
  .suite-body{{padding:0 16px 12px}}
  .test-table{{width:100%;border-collapse:collapse;font-size:0.82rem}}
  .test-table tr{{border-top:1px solid #263344}}
  .test-table td{{padding:5px 6px;vertical-align:top}}
  .test-name{{color:#cbd5e1;font-family:monospace;word-break:break-all}}
  .test-time{{color:#64748b;text-align:right;white-space:nowrap}}
  .badge{{display:inline-block;width:16px;height:16px;border-radius:3px;color:#fff;font-weight:700;font-size:0.65rem;text-align:center;line-height:16px}}
  .pill{{display:inline-block;border-radius:4px;padding:1px 7px;font-size:0.72rem;font-weight:600}}
  .pill.pass{{background:#14532d;color:#86efac}}
  .pill.fail{{background:#7f1d1d;color:#fca5a5}}
  pre.detail{{background:#0f172a;border-radius:5px;padding:8px;font-size:0.72rem;color:#fca5a5;white-space:pre-wrap;margin:3px 0 6px;border-left:3px solid #ef4444}}
  .console-section{{margin-top:20px}}
  .console-section h2{{font-size:0.85rem;color:#64748b;margin-bottom:6px}}
  .console{{background:#0f172a;border-radius:6px;padding:14px;font-size:0.72rem;font-family:monospace;color:#94a3b8;white-space:pre-wrap;max-height:350px;overflow-y:auto;border:1px solid #1e293b}}
</style></head><body>
  <div class="header">
    <h1>Test Report</h1>
    <div class="meta">Run: {run_ts}<br/>Backend: {backend_url}</div>
  </div>
  <div class="overall"><div class="overall-card">
    <div class="overall-status">{overall}</div>
    <div class="overall-counts"><strong>{total_passed}/{total}</strong> tests passed<br/>
      <span style="color:#ef4444">{total_failed} failed</span></div>
    <div class="versions">
      <div class="vtag"><span>FE</span>v{fe_version}</div>
      <div class="vtag"><span>BE</span>v{be_version}</div>
    </div>
  </div></div>
  <div class="content">
    {suites_html}
    <div class="console-section">
      <h2>Console output</h2>
      <div class="console">{esc_console[:10000]}</div>
    </div>
  </div>
</body></html>"""


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    proc = start_test_backend()
    try:
        be_version = get_backend_version(TEST_BACKEND_URL)
        run_ts     = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_dir = REPORTS_DIR / run_ts
        report_dir.mkdir(parents=True, exist_ok=True)
        junit_xml  = report_dir / "junit.xml"

        returncode, console_output = run_pytest(TEST_BACKEND_URL, junit_xml)

        suites = parse_junit(junit_xml)
        html   = generate_html(suites, FE_VERSION, be_version, TEST_BACKEND_URL, run_ts, console_output)

        report_path = report_dir / "index.html"
        report_path.write_text(html, encoding="utf-8")
        (REPORTS_DIR / "latest.html").write_text(html, encoding="utf-8")

        print(f"\nReport: {report_path}")
        sys.exit(returncode)
    finally:
        stop_test_backend(proc)


if __name__ == "__main__":
    main()
```

---

## test_definitions.json — JSON-driven tests

Define test cases as data, not code. The test runner reads this file and parametrizes pytest cases automatically. Add new test cases without touching Python.

```json
[
  {
    "id": "TC-00-A",
    "group": "Connectivity",
    "title": "Backend health check",
    "description": "GET /health must return HTTP 200.",
    "prompt": null,
    "endpoint": "/health",
    "method": "GET",
    "expected": { "http_status": 200 },
    "tags": ["sanity", "no-llm"]
  },
  {
    "id": "TC-00-B",
    "group": "Connectivity",
    "title": "Documents endpoint returns list",
    "description": "GET /documents must return a non-empty array.",
    "prompt": null,
    "endpoint": "/documents",
    "method": "GET",
    "expected": { "http_status": 200, "result_min_count": 1 },
    "tags": ["sanity", "no-llm"]
  },
  {
    "id": "TC-01-A",
    "group": "General Queries",
    "title": "Basic question answered",
    "description": "POST /query with a general question must return HTTP 200 and a non-empty answer.",
    "prompt": "What is the purpose of this system?",
    "endpoint": "/query",
    "method": "POST",
    "expected": { "http_status": 200, "answer_min_length": 50 },
    "tags": ["rag"]
  }
]
```

### Loading and running in pytest

```python
# tests/app/test_user_queries.py
import json
import pytest
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
DEFINITIONS_PATH = Path(__file__).parent.parent / "test_definitions.json"


def load_definitions():
    if not DEFINITIONS_PATH.exists():
        return []
    return json.loads(DEFINITIONS_PATH.read_text(encoding="utf-8"))


class TestFromDefinitions:
    """JSON-driven test cases — add cases to test_definitions.json."""

    @pytest.mark.parametrize("tc", load_definitions(), ids=lambda tc: tc["id"])
    def test_case(self, tc):
        if tc["method"] == "GET":
            resp = requests.get(f"{BACKEND_URL}{tc['endpoint']}", timeout=30)
        else:
            body = {"query": tc["prompt"]} if tc.get("prompt") else {}
            resp = requests.post(f"{BACKEND_URL}{tc['endpoint']}", json=body, timeout=60)

        expected = tc.get("expected", {})

        if "http_status" in expected:
            assert resp.status_code == expected["http_status"], \
                f"Expected {expected['http_status']}, got {resp.status_code}"

        if "result_min_count" in expected:
            data = resp.json()
            assert len(data) >= expected["result_min_count"], \
                f"Expected ≥{expected['result_min_count']} items, got {len(data)}"

        if "answer_min_length" in expected:
            data = resp.json()
            answer = data.get("answer", "")
            assert len(answer) >= expected["answer_min_length"], \
                f"Answer too short ({len(answer)} chars): {answer[:100]}"
```

---

## Standard test categories

Organize tests into these groups (add more as the project grows):

| Pytest class | Category | What it tests |
|---|---|---|
| `TestConnectivity` | TC-00 | `/health`, `/documents` — no LLM needed |
| `TestListQueries` | TC-01 | Meta queries — listing documents by type |
| `TestKeywordSearch` | TC-02 | Full-text and fuzzy search |
| `TestGeneralRAGQueries` | TC-03 | Cross-document questions |
| `TestSpecificDocQueries` | TC-04 | Questions about a named document |
| `TestEdgeCases` | TC-05 | Empty input, gibberish, very long queries |
| `TestPerformance` | TC-06 | Soft latency assertions (warn, don't fail) |
| `TestFromDefinitions` | All | JSON-driven parametrized tests from `test_definitions.json` |

---

## Windows helper scripts

**`tests/run_ui.bat`** — open the latest report in the browser:
```bat
@echo off
start "" "%~dp0reports\latest.html"
```

**`tests/start_test_backend.bat`** — start the test backend manually for debugging:
```bat
@echo off
cd /d "%~dp0.."
set AUTH_DISABLED=true
python -m uvicorn backend.api:app --host 127.0.0.1 --port 8001 --reload
```

---

## Running the tests

```bat
# Full run — starts backend, runs tests, opens report
python tests/run_tests.py

# Run against already-running backend
set BACKEND_URL=http://localhost:8000
python -m pytest tests/app/test_user_queries.py -v

# Skip slow tests
python -m pytest tests/app/ -v -m "not slow"

# Open the last report
tests\run_ui.bat
```

---

## Required backend endpoint: /health

Every Orcanos project must expose a `/health` endpoint. The test runner calls it before every run:

```python
# FastAPI
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
def health():
    return {
        "status": "ok",
        "backend_version": "1.0.0",   # match CLAUDE.md current versions
    }
```

---

## What NOT to do

- **Don't run tests against production.** The runner always uses port 8001 with `AUTH_DISABLED=true`. Never point `BACKEND_URL` at the live environment.
- **Don't skip conftest.py health check.** Tests hanging for 60s each when the backend is down wastes everyone's time.
- **Don't hardcode credentials in test files.** Tests read `.env` the same way the backend does — via the `load .env` block in `run_tests.py`.
- **Don't assert on exact LLM output.** Assert on HTTP status, minimum length, presence of key phrases, or structural properties — not the exact answer text.
