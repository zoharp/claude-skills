"""
vt_plugin.py — pytest plugin that turns automated validation tests into a step-level record.

Loaded by run_validation.py with `-p vt_plugin`. It is project-agnostic: the project's own
conftest.py drives the application; this plugin only records what happened.

In a test:

    def test_vt_001_sign_in(vt, page):
        vt.attach(page)                       # screenshots come from this page
        page.goto(url)
        vt.step(1, page.locator("#orcanos_url").is_visible(), "Login screen shown")
        ...

Rules enforced here, so a report can never claim more than was checked:
  * A test PASSES only if it passed AND recorded every step of its protocol, each as Pass.
    A test that returns early without recording step N fails with "step N not recorded".
  * When a test fails mid-way, the first unrecorded step is marked Fail with the error, and
    the remaining steps "Not run".
  * A skipped test (missing prerequisite / config) is Blocked, with the skip reason.
  * results.json is written once, at session end, with the run's metadata.
"""

import datetime
import getpass
import json
import os
import platform
import re
import shutil
import sys
import time
from pathlib import Path

import pytest

_RESULTS = {}
_META = {}


def pytest_addoption(parser):
    g = parser.getgroup("validation")
    g.addoption("--vt-run-dir", help="Folder for this run's results.json and evidence")
    g.addoption("--vt-pack", help="pack.json — maps test functions to protocol IDs and step counts")


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: long real-time test, excluded unless --include-slow")
    config.addinivalue_line("markers", "vt(id): validation test ID, when the function name does not carry it")
    config.vt_meta = _META
    config.vt_tests = {}
    config.vt_order = []
    pack = config.getoption("--vt-pack")
    if pack:
        sys.path.insert(0, str(Path(__file__).parent))
        from build_pack import load_pack  # noqa: E402  (same folder)
        p = load_pack(Path(pack))
        for m in p["modules"]:
            for t in m["tests"]:
                fn = t.get("automation", {}).get("function")
                if fn:
                    config.vt_tests[fn] = t
        config.vt_order = p.get("run_order") or [t["id"] for m in p["modules"] for t in m["tests"]]
        _META["pack_revision"] = p["meta"]["revision"]


def _test_for(item):
    t = item.config.vt_tests.get(item.originalname or item.name)
    if t:
        return t["id"], len(t["steps"])
    mk = item.get_closest_marker("vt")
    if mk:
        return mk.args[0], None
    m = re.match(r"test_vt_(\d+)", item.name)
    return (f"VT-{m.group(1)}", None) if m else (None, None)


def pytest_collection_modifyitems(config, items):
    """Run in protocol order (pack.run_order), not file order — later tests use earlier ones' output."""
    order = {tid: i for i, tid in enumerate(config.vt_order)}
    items.sort(key=lambda it: order.get(_test_for(it)[0], 10_000))


class Recorder:
    def __init__(self, test_id, n_steps, run_dir: Path):
        self.test_id = test_id
        self.n_steps = n_steps
        self.run_dir = run_dir
        self.ev_dir = run_dir / "evidence"
        self.ev_dir.mkdir(parents=True, exist_ok=True)
        self.steps = {}
        self.files = []
        self.page = None
        self.t0 = time.time()

    def attach(self, page):
        """Screenshots for following steps are taken from this page."""
        self.page = page

    def _shot(self, n):
        if self.page is None:
            return None
        rel = f"evidence/{self.test_id}_s{n}.png"
        try:
            self.page.screenshot(path=str(self.run_dir / rel), full_page=False)
            return rel
        except Exception:
            return None

    def step(self, n, ok, actual, page=None):
        """Record step n. `actual` is what was observed, in plain words. Raises if not ok."""
        if page is not None:
            self.page = page
        self.steps[n] = {"n": n, "status": "Pass" if ok else "Fail", "actual": str(actual),
                         "evidence": self._shot(n), "at_utc": _utc()}
        if not ok:
            raise AssertionError(f"{self.test_id} step {n}: {actual}")

    def file(self, path, name=None):
        """Keep a produced file (e.g. an export) with the run."""
        dest = self.ev_dir / (name or f"{self.test_id}_{Path(path).name}")
        shutil.copyfile(path, dest)
        self.files.append(f"evidence/{dest.name}")
        return dest

    def data(self, name, obj):
        """Keep machine-readable evidence (e.g. what the base system returned)."""
        dest = self.ev_dir / f"{self.test_id}_{name}.json"
        dest.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        self.files.append(f"evidence/{dest.name}")
        return dest


def _utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.fixture
def vt(request):
    run_dir = request.config.getoption("--vt-run-dir")
    tid, n = _test_for(request.node)
    rec = Recorder(tid or request.node.name, n, Path(run_dir) if run_dir else Path(".vt-scratch"))
    request.node._vt = rec
    return rec


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    tid, n_steps = _test_for(item)
    if not tid:
        return
    rec = getattr(item, "_vt", None)
    steps = dict(rec.steps) if rec else {}
    n = n_steps or (max(steps) if steps else 0)

    if rep.when == "setup" and rep.skipped:
        reason = _reason(rep)
        _RESULTS[tid] = _finish(tid, "Blocked", steps, n, rec, error=f"Prerequisite not met: {reason}")
    elif rep.when == "setup" and rep.failed:
        _RESULTS[tid] = _finish(tid, "Blocked", steps, n, rec, error=f"Set-up failed: {_short(rep)}")
    elif rep.when == "call":
        if rep.skipped:
            reason = _reason(rep)
            _RESULTS[tid] = _finish(tid, "Blocked", steps, n, rec, error=f"Prerequisite not met: {reason}")
        elif rep.failed:
            _RESULTS[tid] = _finish(tid, "Fail", steps, n, rec, error=_short(rep))
        else:
            missing = [i for i in range(1, n + 1) if i not in steps]
            if missing:
                _RESULTS[tid] = _finish(tid, "Fail", steps, n, rec,
                                        error=f"Step {missing[0]} not recorded — the test did not check it")
            else:
                _RESULTS[tid] = _finish(tid, "Pass", steps, n, rec)


def _reason(rep):
    r = rep.longrepr[2] if isinstance(rep.longrepr, tuple) else str(rep.longrepr)
    return r[len("Skipped: "):] if r.startswith("Skipped: ") else r


def _short(rep):
    msg = getattr(rep, "longreprtext", "") or str(rep.longrepr)
    lines = [l for l in msg.splitlines() if l.startswith("E ")]
    return (" ".join(l[2:].strip() for l in lines[:4]) or msg[-600:]).strip()


def _finish(tid, status, steps, n, rec, error=None):
    out, failed_marked = [], False
    for i in range(1, n + 1):
        if i in steps:
            out.append(steps[i])
            failed_marked |= steps[i]["status"] == "Fail"
        elif status == "Fail" and not failed_marked:
            out.append({"n": i, "status": "Fail", "actual": error or "", "evidence": None})
            failed_marked = True
        else:
            out.append({"n": i, "status": "Not run", "actual": "", "evidence": None})
    return {"status": status, "steps": out, "error": error,
            "files": rec.files if rec else [],
            "duration_s": round(time.time() - rec.t0, 1) if rec else 0}


def pytest_sessionfinish(session, exitstatus):
    run_dir = session.config.getoption("--vt-run-dir")
    if not run_dir:
        return
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "run_id": run_dir.name,
        "started_utc": _META.pop("started_utc", None) or os.environ.get("VT_STARTED_UTC", ""),
        "finished_utc": _utc(),
        "host": platform.node(),
        "os_user": getpass.getuser(),
        "python": platform.python_version(),
        "command": os.environ.get("VT_COMMAND", ""),
    }
    meta.update(_META)
    meta["tests"] = _RESULTS
    (run_dir / "results.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
