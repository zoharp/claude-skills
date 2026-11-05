# TEMPLATE — copied from the Traceability Matrix validation (validation/automation/conftest.py).
# Generic and reusable as-is: Config (+ need/password -> BLOCK), browser/context/page fixtures,
# the Orcanos oracle client (QW_Login, QW_Get_Filter_Results paging, QW_Update_Object), traced_keys.
# APP-SPECIFIC and to be replaced per project: sign_in*, api, find_panel_id, panel_id, open_matrix,
# wait_matrix, page_indicator, read_*, parse_export_* — keep the rule: never import the app's code.

"""
Project fixtures for the automated validation tests (VAL-CS).

Everything here drives the add-on the way a user does — a real browser on the real UI — and
reads Orcanos through its own REST API as the independent oracle. Nothing imports the add-on's
code: a bug in the add-on must not be able to hide itself by also being in the checker.

Configuration: validation/config.json (copy config.example.json). Passwords come only from the
environment variables it names. A missing value BLOCKS the tests that need it — never passes them.
"""

import base64
import html as htmllib
import json
import os
import re
from pathlib import Path

import pytest
import requests

HERE = Path(__file__).resolve().parent
CONFIG_PATH = Path(os.environ.get("VT_CONFIG", HERE.parent / "config.json"))
KEY_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*-\d+")

# Shared between tests of one run (pack.run_order makes VT-005 run before the tests that use it).
STATE = {}


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

class Config(dict):
    def need(self, *path):
        """A config value, or BLOCK the test that needs it."""
        cur = self
        for p in path:
            if not isinstance(cur, dict) or cur.get(p) in (None, ""):
                pytest.skip(f"config.json has no value for {'.'.join(path)}")
            cur = cur[p]
        return cur

    def password(self, user):
        env = self.need("users", user, "password_env")
        pw = os.environ.get(env)
        if not pw:
            pytest.skip(f"environment variable {env} (password of user {user}) is not set")
        return pw

    def key(self, logical):
        """Real Orcanos key for a logical TDS name (REQ-01 → PR-1234)."""
        return self.need("items", logical)


@pytest.fixture(scope="session")
def cfg(pytestconfig):
    if not CONFIG_PATH.exists():
        pytest.skip(f"{CONFIG_PATH} not found — copy config.example.json and fill it in")
    c = Config(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    pytestconfig.vt_meta.update({"target_url": c.get("app_url", ""), "tenant": c.get("orcanos_url", "")})
    return c


# ─────────────────────────────────────────────────────────────────────────────
# Browser
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def browser(pytestconfig):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(headless=os.environ.get("VT_HEADED") != "1")
        pytestconfig.vt_meta["browser"] = f"Chromium {b.version}"
        yield b
        b.close()


@pytest.fixture
def context(browser):
    """A fresh browser profile per test — no saved session, no saved accounts."""
    ctx = browser.new_context(viewport={"width": 1600, "height": 1000}, accept_downloads=True)
    ctx.set_default_timeout(30_000)
    yield ctx
    ctx.close()


@pytest.fixture
def page(context, vt, cfg, pytestconfig):
    pg = context.new_page()
    vt.attach(pg)
    if "app_version" not in pytestconfig.vt_meta:
        pytestconfig.vt_meta["app_version"] = app_version(pg, cfg)
    return pg


def app_version(page, cfg):
    """The version the target says it runs — recorded in the report, not assumed."""
    for path in ("/release_notes.json", "/api/health", "/api/version"):
        try:
            r = page.request.get(cfg["app_url"].rstrip("/") + path, timeout=10_000)
            if r.ok:
                data = r.json()
                if isinstance(data, dict):
                    v = data.get("version") or data.get("app_version") or (data.get("releases") or [{}])[0].get("version")
                elif isinstance(data, list) and data:
                    v = data[0].get("version")
                else:
                    v = None
                if v:
                    return str(v)
        except Exception:
            pass
    return "not reported by target"


# ─────────────────────────────────────────────────────────────────────────────
# Add-on UI helpers
# ─────────────────────────────────────────────────────────────────────────────

def sign_in(page, cfg, user="A", password=None):
    page.goto(cfg["app_url"].rstrip("/") + "/")
    url = page.locator("#orcanos_url")
    url.fill(cfg.need("orcanos_url"))
    url.press("Tab")
    page.locator("#username:enabled").wait_for()
    page.fill("#username", cfg.need("users", user, "username"))
    page.fill("#password", password if password is not None else cfg.password(user))
    page.click("button.login-button")


def sign_in_ok(page, cfg, user="A"):
    sign_in(page, cfg, user)
    page.wait_for_url(re.compile(r".*/trace/dashboard.*"), timeout=30_000)


def api(page, method, path, cfg, **kw):
    """Call the add-on's API with the browser's session (CSRF header on writes)."""
    url = cfg["app_url"].rstrip("/") + path
    headers = kw.pop("headers", {})
    if method != "GET":
        csrf = next((c["value"] for c in page.context.cookies() if c["name"] == "csrf_token"), "")
        headers["X-CSRF-Token"] = csrf
    return page.request.fetch(url, method=method, headers=headers, **kw)


def find_panel_id(page, cfg, name):
    r = api(page, "GET", "/api/config/panels", cfg)
    if not r.ok:
        return None
    data = r.json()
    panels = data if isinstance(data, list) else (data.get("panels") or data.get("items") or data.get("setups") or [])
    for p in panels:
        if p.get("name") == name:
            return p.get("id") or p.get("setup_id")
    return None


@pytest.fixture
def panel_id(page, cfg):
    """The P-VAL-01 panel id — from VT-005 in this run, else looked up by name; else BLOCK."""
    sign_in_ok(page, cfg)
    pid = STATE.get("panel_id") or find_panel_id(page, cfg, cfg.get("panel_name", "P-VAL-01"))
    if not pid:
        pytest.skip("panel P-VAL-01 does not exist — VT-005 must pass first")
    STATE["panel_id"] = pid
    return pid


def open_matrix(page, cfg, pid, refresh=False, rows_per_page=None):
    page.goto(f'{cfg["app_url"].rstrip("/")}/trace/matrix/{pid}')
    wait_matrix(page)
    if rows_per_page:
        sel = page.locator("select.footer-rows-select")
        if sel.input_value() != str(rows_per_page):
            sel.select_option(str(rows_per_page))
            wait_matrix(page)
    if refresh:
        page.click("button.toolbar-refresh")
        wait_matrix(page)


def wait_matrix(page):
    page.locator("table.matrix-table tbody tr").first.wait_for(timeout=120_000)
    page.wait_for_load_state("networkidle")


def page_indicator(page):
    m = re.search(r"Page\s+(\d+)\s+of\s+(\d+)", page.locator(".matrix-footer").inner_text())
    return (int(m.group(1)), int(m.group(2))) if m else (1, 1)


def goto_first_page(page):
    while page_indicator(page)[0] > 1:
        page.locator(".footer-pagination").get_by_role("button", name=re.compile("Prev")).click()
        wait_matrix(page)


_READ_JS = """() => [...document.querySelectorAll('table.matrix-table tbody tr[data-req]')].map(tr => ({
  req: tr.dataset.req, l1: tr.classList.contains('l1-row'),
  cells: [...tr.querySelectorAll('td[data-level]')].map(td => ({
    level: +td.dataset.level,
    lead: td.classList.contains('item-lead') || td.classList.contains('l1-cell'),
    text: (td.innerText || '').trim(),
    missing: !!td.querySelector('.missing-indicator'),
    notexec: !!td.querySelector('.notexec-indicator')}))}))"""


def read_page(page):
    """The current matrix page as rows of level cells, straight from the DOM the user sees."""
    exp = page.get_by_role("button", name="Expand all rows")
    if exp.count() and exp.first.is_visible():
        exp.first.click()
    return page.evaluate(_READ_JS)


def read_matrix(page, shots=None):
    """Every page of the matrix → {L1 key: {...}}. `shots(n)` is called on each page for evidence."""
    goto_first_page(page)
    groups, n = {}, 1
    while True:
        rows = read_page(page)
        if shots:
            shots(n)
        _fold(rows, groups)
        cur, total = page_indicator(page)
        if cur >= total:
            break
        page.locator(".footer-pagination").get_by_role("button", name=re.compile("Next")).click()
        wait_matrix(page)
        n += 1
    return groups


def _lead_key(cells, level):
    for c in cells:
        if c["level"] == level and c["lead"]:
            m = KEY_RE.search(c["text"])
            if m:
                return m.group(0)
    return None


def _fold(rows, groups):
    by_req = {}
    for r in rows:
        by_req.setdefault(r["req"], []).append(r)
    for req, rs in by_req.items():
        l1 = next((_lead_key(r["cells"], 1) for r in rs if r["l1"]), None) or _lead_key(rs[0]["cells"], 1)
        g = groups.setdefault(l1, {"children": set(), "runs": {}, "missing": set(), "notexec": set(),
                                   "text": {}, "rows": 0})
        cur_l2 = None
        for r in rs:
            g["rows"] += 1
            k2 = _lead_key(r["cells"], 2)
            if k2:
                g["children"].add(k2)
                cur_l2 = k2
            for c in r["cells"]:
                g["text"].setdefault(c["level"], "")
                g["text"][c["level"]] += " " + c["text"]
                if c["missing"]:
                    g["missing"].add(c["level"])
                if c["notexec"]:
                    g["notexec"].add(cur_l2 or "?")
                if c["level"] == 3 and cur_l2:
                    g["runs"][cur_l2] = (g["runs"].get(cur_l2, "") + " " + c["text"]).strip()
    return groups


# ─────────────────────────────────────────────────────────────────────────────
# Orcanos — the independent oracle (its REST API, not the add-on's code)
# ─────────────────────────────────────────────────────────────────────────────

class Orcanos:
    def __init__(self, base, username, password):
        self.base = base.rstrip("/")
        tok = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode()
        self.h = {"Authorization": f"Basic {tok}", "Content-Type": "application/json"}

    def call(self, name, body):
        r = requests.post(f"{self.base}/api/v2/Json/{name}", headers=self.h, json=body, timeout=120)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and data.get("IsSuccess") is False:
            raise AssertionError(f"Orcanos {name}: {data.get('Message')}")
        return data

    def login(self):
        return self.call("QW_Login", {})

    def filter_items(self, filter_id, item_type, version_id):
        out, page = [], 1
        while True:
            d = self.call("QW_Get_Filter_Results", {
                "Filter_id": str(filter_id), "Page_no": str(page), "Page_Size": "100",
                "Item_Type": item_type, "Version_id": str(version_id), "Filter_By": "", "Order_By": "",
                "IsNewPaging": "0", "IsReturnPageCount": "yes", "DashboardItemId": "0",
                "IncludeProtectedCol": "true"})["Data"]
            objs = d.get("Object") or []
            objs = objs if isinstance(objs, list) else [objs]
            out += [self._item(o) for o in objs]
            total = int(d.get("Total_records") or len(out))
            if not objs or len(out) >= total:
                return out
            page += 1

    @staticmethod
    def _field(o, *names):
        for f in o.get("Field") or []:
            if f.get("Name") in names or f.get("Title") in names:
                return f.get("Display_text") or f.get("Text") or ""
        return ""

    def _item(self, o):
        m = re.search(r"\((\d+)\)\s*$", str(o.get("Id", "")))
        key = KEY_RE.search(self._field(o, "Key"))
        return {"id": m.group(1) if m else re.sub(r"\D", "", str(o.get("Id", ""))),
                "key": key.group(0) if key else "",
                "name": self._field(o, "Obj_name", "Name", "Synopsis"),
                "traced": traced_keys(self._field(o, "Traced Items Info"))}

    def rename(self, item_id, version_id, new_name):
        return self.call("QW_Update_Object", {"Object_ID": int(item_id), "View_Version": str(version_id),
                                              "Object_Name": new_name})


def traced_keys(raw):
    """Keys out of a Traced Items Info value — plain, 'KEY (text)', or <a> markup, maybe double-encoded."""
    s = raw or ""
    for _ in range(3):
        s = htmllib.unescape(s)
        s = re.sub(r"</\s*(a|p|div|li|tr|span)\s*>|<\s*br\s*/?>", ",", s, flags=re.I)
        s = re.sub(r"<[^>]+>", " ", s)
    return sorted(set(KEY_RE.findall(s)))


@pytest.fixture(scope="session")
def orcanos(cfg):
    return Orcanos(cfg.need("orcanos_url"), cfg.need("users", "A", "username"), cfg.password("A"))


@pytest.fixture(scope="session")
def oracle(cfg, orcanos):
    """What Orcanos says, read once per run: the four filters' items, keyed by item key."""
    ver = cfg.need("project", "version_id")
    out = {}
    for f in ("F1", "F2", "F3", "F4"):
        spec = cfg.need("filters", f)
        out[f] = {i["key"]: i for i in orcanos.filter_items(spec["id"], spec["item_type"], ver)}
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Export file readers (independent of the add-on's export code)
# ─────────────────────────────────────────────────────────────────────────────

def parse_export_html(path, l1_keys):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(Path(path).read_text(encoding="utf-8"), "html.parser")
    req_to_key, missing, notexec = {}, set(), set()
    for tr in soup.select("tr[data-req]"):
        req = tr["data-req"]
        if "l1-row" in (tr.get("class") or []):
            k = next((k for k in KEY_RE.findall(tr.get_text(" ")) if k in l1_keys), None)
            if k:
                req_to_key[req] = k
    for tr in soup.select("tr[data-req]"):
        k = req_to_key.get(tr["data-req"])
        if tr.select_one(".missing-indicator"):
            missing.add(k)
        if tr.select_one(".notexec-indicator"):
            notexec.add(k)
    return {"l1": set(req_to_key.values()), "missing": missing, "notexec": notexec}


def parse_export_xlsx(path, l1_keys):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    cur, l1, missing, notexec = None, set(), set(), set()
    for row in ws.iter_rows(values_only=True):
        text = " ".join(str(v) for v in row if v is not None)
        k = next((k for k in KEY_RE.findall(text) if k in l1_keys), None)
        if k:
            cur = k
            l1.add(k)
        if "Missing" in text and cur:
            missing.add(cur)
        if "Not Executed" in text and cur:
            notexec.add(cur)
    return {"l1": l1, "missing": missing, "notexec": notexec}
