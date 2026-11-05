#!/usr/bin/env python3
"""
run_validation.py — run the automated validation tests and regenerate the package with results.

    python run_validation.py --pack validation/pack.json --tests validation/automation
                             [--include-slow] [-k EXPR] [--headed]

Each run gets its own folder  <pack dir>/results/<run_id>/  holding results.json and the
evidence (screenshots, exported files, base-system data). The six documents are then rebuilt
into <pack dir>/docs/ with this run's results in the RTM and STR.

A run folder is a record: never edit results.json by hand — the STR prints its SHA-256.
"""

import argparse
import datetime
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pack", required=True)
    ap.add_argument("--tests", required=True, help="Folder with the project's automated validation tests")
    ap.add_argument("--include-slow", action="store_true", help="Also run long real-time tests (e.g. idle time-out)")
    ap.add_argument("-k", help="pytest -k expression, e.g. 'vt_006 or vt_008'")
    ap.add_argument("--headed", action="store_true", help="Show the browser")
    ap.add_argument("--no-build", action="store_true")
    a = ap.parse_args()

    pack = Path(a.pack).resolve()
    tests = Path(a.tests).resolve()
    now = datetime.datetime.now(datetime.timezone.utc)
    run_id = now.strftime("RUN-%Y%m%d-%H%M%SZ")
    run_dir = pack.parent / "results" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    cmd = [sys.executable, "-m", "pytest", str(tests), "-p", "vt_plugin",
           "--vt-run-dir", str(run_dir), "--vt-pack", str(pack),
           "--rootdir", str(tests), "-p", "no:cacheprovider", "-q", "-rA"]
    ini = tests / "pytest.ini"
    cmd += ["-c", str(ini)] if ini.exists() else ["-o", "addopts="]
    if not a.include_slow:
        cmd += ["-m", "not slow"]
    if a.k:
        cmd += ["-k", a.k]

    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(HERE), str(tests), env.get("PYTHONPATH", "")])
    env["VT_STARTED_UTC"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    env["VT_COMMAND"] = " ".join(["run_validation.py"] + sys.argv[1:])
    if a.headed:
        env["VT_HEADED"] = "1"

    print(f"Validation run {run_id}\n  results: {run_dir}\n")
    rc = subprocess.call(cmd, env=env)

    results = run_dir / "results.json"
    if not results.exists():
        print("No results.json was written — the run did not reach the end of the session.", file=sys.stderr)
        return rc or 1
    (pack.parent / "results" / "LATEST").write_text(run_id + "\n", encoding="utf-8")
    if not a.no_build:
        subprocess.check_call([sys.executable, str(HERE / "build_pack.py"), "--pack", str(pack),
                               "--results", str(results)])
    print(f"\nRun {run_id} finished (pytest exit code {rc}).")
    return rc


if __name__ == "__main__":
    sys.exit(main())
