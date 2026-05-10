"""
tests/run_tests.py
==================
Starts a test backend (AUTH_DISABLED=true, port 8001), runs the full pytest
suite, generates an HTML report in tests/reports/<timestamp>/index.html.

Usage:
    python tests/run_tests.py
"""

import os, sys, io, time, subprocess, datetime, requests
import xml.etree.ElementTree as ET
from pathlib import Path

# Force UTF-8 stdout so unicode test output doesn't crash on Windows cp1252
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ── Config ────────────────────────────────────────────────────────────────────
# Update these to match your project versions (keep in sync with CLAUDE.md)
FE_VERSION = "1.0.0"
BE_VERSION_FALLBACK = "1.0.0"

SCRIPT_DIR        = Path(__file__).parent
REPO_ROOT         = SCRIPT_DIR.parent
TEST_FILE         = SCRIPT_DIR / "app" / "test_queries.py"
REPORTS_DIR       = SCRIPT_DIR / "reports"
TEST_BACKEND_PORT = 8001
TEST_BACKEND_URL  = f"http://localhost:{TEST_BACKEND_PORT}"


# ── Backend lifecycle ─────────────────────────────────────────────────────────

def _load_dotenv(env: dict) -> None:
    """Load .env into env dict without overwriting already-set vars."""
    dotenv_path = REPO_ROOT / ".env"
    if dotenv_path.exists():
        for line in dotenv_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env.setdefault(k.strip(), v.strip())


def start_test_backend() -> subprocess.Popen:
    env = os.environ.copy()
    env["AUTH_DISABLED"] = "true"
    _load_dotenv(env)

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
                print(f"[OK] Test backend ready ({i + 1}s)")
                return proc
        except Exception:
            pass
        print(f"[*] Waiting... ({i + 1}/30)")
    proc.terminate()
    raise RuntimeError("Test backend failed to start within 30s")


def stop_test_backend(proc: subprocess.Popen) -> None:
    print("[*] Stopping test backend...")
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def get_backend_version(url: str) -> str:
    try:
        return requests.get(f"{url}/health", timeout=5).json().get("backend_version", BE_VERSION_FALLBACK)
    except Exception as e:
        return f"unreachable ({e})"


# ── pytest runner ─────────────────────────────────────────────────────────────

def run_pytest(backend_url: str, junit_xml_path: Path) -> tuple[int, str]:
    env = os.environ.copy()
    env["AUTH_DISABLED"] = "true"
    env["BACKEND_URL"] = backend_url
    _load_dotenv(env)

    cmd = [
        sys.executable, "-m", "pytest", str(TEST_FILE),
        "-v", "--tb=short", f"--junit-xml={junit_xml_path}",
        "--no-header", "-p", "no:warnings",
    ]
    lines = []
    MAX_CONSECUTIVE_ERRORS = 5
    consecutive_errors = 0

    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace", cwd=str(REPO_ROOT))

    print(f"\n{'=' * 60}\nRunning tests against: {backend_url}\n{'=' * 60}\n")

    for line in proc.stdout:
        s = line.rstrip()
        if   " PASSED" in s: print(f"  \033[32mPASS\033[0m {s}"); consecutive_errors = 0
        elif " FAILED" in s: print(f"  \033[31mFAIL\033[0m {s}"); consecutive_errors = 0
        elif " ERROR"  in s: print(f"  \033[33m!\033[0m {s}");    consecutive_errors += 1
        else:                print(f"  {s}")
        lines.append(s)
        if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
            print(f"\n[!] {MAX_CONSECUTIVE_ERRORS} consecutive ERRORs — aborting.\n")
            proc.terminate()
            break

    proc.wait()
    return proc.returncode, "\n".join(lines)


# ── JUnit XML parser ──────────────────────────────────────────────────────────

def parse_junit(xml_path: Path) -> dict:
    if not xml_path.exists():
        return {}
    root = ET.parse(xml_path).getroot()
    suites_el = root.findall("testsuite") if root.tag == "testsuites" else [root]
    suites: dict = {}
    for suite in suites_el:
        for tc in suite.findall("testcase"):
            cls     = tc.get("classname", "unknown").split(".")[-1]
            failure = tc.find("failure")
            error   = tc.find("error")
            skipped = tc.find("skipped")
            if   failure is not None: status, detail = "FAIL",  failure.text or failure.get("message", "")
            elif error   is not None: status, detail = "ERROR", error.text   or error.get("message", "")
            elif skipped is not None: status, detail = "SKIP",  skipped.get("message", "")
            else:                     status, detail = "PASS",  ""
            suites.setdefault(cls, []).append({
                "name":   tc.get("name", ""),
                "status": status,
                "time_s": float(tc.get("time", 0)),
                "detail": detail,
            })
    return suites


# ── HTML report ───────────────────────────────────────────────────────────────

STATUS_COLOR = {"PASS": "#22c55e", "FAIL": "#ef4444", "ERROR": "#f97316", "SKIP": "#a3a3a3"}
STATUS_ICON  = {"PASS": "✓",       "FAIL": "✗",       "ERROR": "!",       "SKIP": "–"}

# Map pytest class names → human-readable labels.
# Add your own test class names here as the project grows.
TC_MAP = {
    "TestConnectivity":       "TC-00 — Connectivity / Sanity",
    "TestListQueries":        "TC-01 — List / Meta Queries",
    "TestKeywordSearch":      "TC-02 — Keyword Search",
    "TestGeneralQueries":     "TC-03 — General Queries",
    "TestSpecificDocQueries": "TC-04 — Specific Document Queries",
    "TestEdgeCases":          "TC-05 — Edge Cases & Robustness",
    "TestPerformance":        "TC-06 — Performance (soft thresholds)",
    "TestFromDefinitions":    "All Tests (JSON-driven)",
}


def _render_suite(classname: str, tests: list) -> str:
    passed   = sum(1 for t in tests if t["status"] == "PASS")
    failed   = sum(1 for t in tests if t["status"] in ("FAIL", "ERROR"))
    suite_ok = failed == 0
    color    = STATUS_COLOR["PASS"] if suite_ok else STATUS_COLOR["FAIL"]
    label    = TC_MAP.get(classname, classname)
    rows     = ""
    for t in tests:
        sc   = STATUS_COLOR[t["status"]]
        icon = STATUS_ICON[t["status"]]
        detail_html = ""
        if t["detail"]:
            esc = (t["detail"].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"))
            detail_html = f'<pre class="detail">{esc[:800]}</pre>'
        rows += (
            f'<tr><td><span class="badge" style="background:{sc}">{icon}</span></td>'
            f'<td class="test-name">{t["name"]}</td>'
            f'<td class="test-time">{t["time_s"]:.2f}s</td></tr>'
            + (f'<tr><td colspan="3">{detail_html}</td></tr>' if detail_html else "")
        )
    pills     = f'<span class="pill pass">{passed} passed</span> <span class="pill fail">{failed} failed</span>'
    collapsed = " collapsed" if suite_ok else ""
    return (
        f'<div class="suite{collapsed}">'
        f'<div class="suite-header" onclick="this.parentElement.classList.toggle(\'collapsed\')">'
        f'<span class="suite-icon" style="color:{color}">{"✓" if suite_ok else "✗"}</span>'
        f'<span class="suite-title">{label}</span>'
        f'<span class="suite-summary">{pills}</span>'
        f'<span class="chevron">▾</span></div>'
        f'<div class="suite-body"><table class="test-table">{rows}</table></div></div>'
    )


def generate_html(suites: dict, fe_ver: str, be_ver: str, backend_url: str, run_ts: str, console: str) -> str:
    all_tests = [t for tests in suites.values() for t in tests]
    passed    = sum(1 for t in all_tests if t["status"] == "PASS")
    failed    = sum(1 for t in all_tests if t["status"] in ("FAIL", "ERROR"))
    total     = len(all_tests)
    overall   = "PASS" if failed == 0 else "FAIL"
    oc        = STATUS_COLOR["PASS"] if overall == "PASS" else STATUS_COLOR["FAIL"]
    suites_h  = "".join(_render_suite(cls, tests) for cls, tests in suites.items())
    esc_con   = console.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/>
<title>Test Report {run_ts}</title><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f172a;color:#e2e8f0}}
.header{{background:#1e293b;border-bottom:1px solid #334155;padding:20px 28px;display:flex;justify-content:space-between;align-items:center}}
.header h1{{font-size:1.3rem;font-weight:700;color:#f1f5f9}}
.header .meta{{font-size:0.78rem;color:#94a3b8;text-align:right;line-height:1.8}}
.overall{{padding:20px 28px}}
.oc{{background:#1e293b;border-radius:10px;padding:18px 24px;display:flex;align-items:center;gap:18px;border-left:5px solid {oc}}}
.os{{font-size:2.2rem;font-weight:800;color:{oc}}}
.counts{{font-size:0.95rem;color:#94a3b8}}.counts strong{{color:#f1f5f9;font-size:1rem}}
.versions{{display:flex;gap:10px;margin-left:auto}}
.vtag{{background:#334155;border-radius:6px;padding:5px 12px;font-size:0.78rem;font-weight:600}}
.vtag span{{color:#94a3b8;margin-right:5px}}
.content{{padding:0 28px 40px}}
.suite{{background:#1e293b;border-radius:8px;margin-bottom:10px;border:1px solid #334155;border-left:4px solid #22c55e;overflow:hidden}}
.suite:not(.collapsed) .suite-body{{display:block}}
.suite.collapsed .suite-body{{display:none}}
.suite-header{{display:flex;align-items:center;gap:10px;padding:12px 16px;cursor:pointer;user-select:none}}
.suite-header:hover{{background:#263344}}
.suite-icon{{font-size:1rem;font-weight:700;width:18px;text-align:center}}
.suite-title{{font-weight:600;font-size:0.9rem;flex:1}}
.suite-summary,.chevron{{font-size:0.78rem;color:#94a3b8}}
.suite.collapsed .chevron{{transform:rotate(-90deg)}}
.suite-body{{padding:0 16px 12px}}
.test-table{{width:100%;border-collapse:collapse;font-size:0.82rem}}
.test-table tr{{border-top:1px solid #263344}}
.test-table td{{padding:5px 6px;vertical-align:top}}
.test-name{{color:#cbd5e1;font-family:monospace;word-break:break-all}}
.test-time{{color:#64748b;text-align:right;white-space:nowrap}}
.badge{{display:inline-block;width:16px;height:16px;border-radius:3px;color:#fff;font-weight:700;font-size:0.65rem;text-align:center;line-height:16px}}
.pill{{display:inline-block;border-radius:4px;padding:1px 7px;font-size:0.72rem;font-weight:600}}
.pill.pass{{background:#14532d;color:#86efac}}.pill.fail{{background:#7f1d1d;color:#fca5a5}}
pre.detail{{background:#0f172a;border-radius:5px;padding:8px;font-size:0.72rem;color:#fca5a5;white-space:pre-wrap;margin:3px 0 6px;border-left:3px solid #ef4444}}
.console-section{{margin-top:20px}}
.console-section h2{{font-size:0.85rem;color:#64748b;margin-bottom:6px}}
.console{{background:#0f172a;border-radius:6px;padding:14px;font-size:0.72rem;font-family:monospace;color:#94a3b8;white-space:pre-wrap;max-height:350px;overflow-y:auto;border:1px solid #1e293b}}
</style></head><body>
<div class="header"><h1>Test Report</h1><div class="meta">Run: {run_ts}<br/>Backend: {backend_url}</div></div>
<div class="overall"><div class="oc">
  <div class="os">{overall}</div>
  <div class="counts"><strong>{passed}/{total}</strong> tests passed<br/><span style="color:#ef4444">{failed} failed</span></div>
  <div class="versions"><div class="vtag"><span>FE</span>v{fe_ver}</div><div class="vtag"><span>BE</span>v{be_ver}</div></div>
</div></div>
<div class="content">{suites_h}
  <div class="console-section"><h2>Console output</h2><div class="console">{esc_con[:10000]}</div></div>
</div></body></html>"""


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    proc = start_test_backend()
    try:
        be_ver   = get_backend_version(TEST_BACKEND_URL)
        run_ts   = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        rep_dir  = REPORTS_DIR / run_ts
        rep_dir.mkdir(parents=True, exist_ok=True)
        junit_xml = rep_dir / "junit.xml"

        rc, console = run_pytest(TEST_BACKEND_URL, junit_xml)
        suites = parse_junit(junit_xml)
        html   = generate_html(suites, FE_VERSION, be_ver, TEST_BACKEND_URL, run_ts, console)

        report_path = rep_dir / "index.html"
        report_path.write_text(html, encoding="utf-8")
        (REPORTS_DIR / "latest.html").write_text(html, encoding="utf-8")

        print(f"\nReport: {report_path}")
        sys.exit(rc)
    finally:
        stop_test_backend(proc)


if __name__ == "__main__":
    main()
