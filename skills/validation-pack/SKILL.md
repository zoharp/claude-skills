---
name: validation-pack
description: Create, extend, run and report a software VALIDATION package (VP, URS, SRS, STD, RTM, STR) for any Orcanos project or add-on — one JSON source, one section per module, Part 11 / AI / security / data-integrity assessment, every test automated with Playwright and checked against Orcanos, results written into the test report. Use when asked for a validation package, URS/SRS/test protocol/trace matrix/test report, IQ/OQ/PQ-style evidence, Part 11 assessment, or to add a module or requirement to an existing package, or to run it.
revision: 1.0.0
---

# validation-pack — validation package generator and runner

One source of truth renders six controlled documents, and one runner executes the automated
validation tests and writes their results into the report. Reusable across projects: the
**scripts are generic**; each project supplies its own JSON and its own Playwright tests.

```
<project>/validation/
  pack.json              plan, modules list, compliance (Part 11, AI, security, ALCOA+), references
  modules/<module>.json  per module: URS, SRS, test data set (TDS), tests (steps + automation link)
  config.example.json    target URL, tenant, users (password env-var NAMES), TDS key mapping
  config.json            the real one — git-ignored
  automation/            conftest.py (drives the app + independent oracle) + test_<module>.py
  docs/                  generated: VP.html URS.html SRS.html STD.html RTM.html STR.html
  results/<RUN-…>/       results.json + evidence/ per run — a record, never edited
```

Scripts (in this skill's `scripts/` folder — call them by absolute path):

| Script | Does |
|---|---|
| `build_pack.py --pack P [--results R]` | Renders the six documents into `<pack dir>/docs/`. Checks every ID links up (dangling trace = hard error, untested SRS = warning). |
| `run_validation.py --pack P --tests T [--include-slow] [-k EXPR] [--headed]` | Runs the tests with `vt_plugin`, writes `results/<RUN-id>/results.json` + evidence, rebuilds the docs with the results. |
| `vt_plugin.py` | pytest plugin: the `vt` fixture records each step (status, observed value, screenshot), orders tests by `pack.run_order`, writes results.json. |

Templates in `templates/` — copy, don't regenerate: `pack.template.json` (incl. the full Part 11
clause list), `module.template.json`, `conftest.template.py`, `pytest.ini`, `config.example.json`.

---

## Validation, not verification — the rule every document and test must follow

- **Verification** = built to spec (developer unit / API / E2E tests). Not part of this package.
- **Validation** = meets the *user's need* in *real use*. So every test:
  - is written as a **user scenario** through the **normal UI** (Playwright drives a real browser —
    automation is only the execution method);
  - runs on a **production-equivalent** install against a **real Orcanos account** with a
    **defined test data set**, so every expected result is known in advance;
  - checks its result against **Orcanos itself through its REST API**, with checker code that
    **never imports the application's code** (a bug must not hide by also being in the checker).
- URS are user needs ("As a …, I need …, so that …") with a **risk level** (High / Medium / Low)
  and a one-line risk rationale. SRS say *how*, testably. Each SRS item has ≥ 1 test.
- The base system (Orcanos ALM/QMS) has its own validation: **rely on it, don't re-test it**, and
  say so in the plan. Part 11 rows met by Orcanos are marked `Base`.

## Honesty rules (non-negotiable)

1. **Never write a result by hand.** The STR and RTM status come only from a `results.json`
   produced by a run. No results ⇒ the STR says "Not executed".
2. A test **passes only if it recorded every protocol step as Pass**. A test that returns early
   fails with "step N not recorded" (the plugin enforces this — don't work around it).
3. A missing prerequisite (config value, password env var, earlier test's output) is **Blocked**
   via `pytest.skip(...)`, never a pass. `Config.need()` in the conftest does this.
4. Every step's `actual` text states **what was observed**, with the values compared — not "OK".
5. Don't claim a feature, message text or selector without reading the code; selectors and
   message texts in tests must be quoted from the source (`file:line`) when written.
6. A Part 11 / security row is only `Met` with evidence cited (a test ID or a document section).
   Unknown ⇒ `Partial` or `Gap` with the open item named. List known gaps plainly.

---

## Workflows

### A. Start a package in a new project
1. Create `validation/` with `pack.json` from `templates/pack.template.json`, `modules/`,
   `automation/` (copy `conftest.template.py` → `conftest.py`, `pytest.ini`), `config.example.json`.
2. Add `validation/config.json` and `validation/results/` to `.gitignore`.
3. Fill `meta`, `plan` (intended use, base-system reliance), `modules[]` — **every module of the
   product listed**, the ones not yet written as `"status": "planned"`.
4. Fill `compliance`: Part 11 (assess every clause: Base / Met / Partial / Gap / NA), AI (each AI
   function: data sent, human control; plus how AI is validated — the *controls*, not the content),
   security (summary + known gaps, pointing at the project's security doc), data integrity (ALCOA+).
5. `python <skill>/scripts/build_pack.py --pack validation/pack.json` and open `docs/VP.html`.

### B. Add a module section or requirements
1. Create/extend `modules/<module>.json` (see `module.template.json`); set the module's
   `status` to `in-scope` and `file` in `pack.json`.
2. Per user need: URS (risk!), its SRS items, then tests. Test = `id`, `title`, `srs[]`, `pre`,
   `evidence`, `steps[[action, expected], …]`, `automation{file,function}`, optional `slow`.
3. Extend the module's TDS so every expected value is known before the run.
4. Add the test IDs to `pack.run_order` where order matters (tests that use another's output).
5. Write the automated test (C). Rebuild (`build_pack.py`) — it errors on a dangling ID.

### C. Write an automated validation test
- Function name `test_vt_NNN_<what>` in `automation/test_<module>.py`, matching `automation.function`.
- Signature takes `vt` and `page` (+ `cfg`, `oracle`/`orcanos`, shared fixtures).
- One `vt.step(n, ok, actual)` per protocol step, **in order, all of them**. `ok` = the expected
  result from the STD; `actual` = the observed values.
- Keep produced files with `vt.file(path)` and compared base-system data with `vt.data(name, obj)`.
- Clean up anything the test changes in Orcanos in a `finally:` (e.g. rename → restore), so the
  run is repeatable. Prefer changes that can be undone through the API.
- Read the UI with locators taken from the source; read Orcanos through its API (see the
  `orcanos-api` skill: QW_Login, QW_Get_Filter_Results paging rule, QW_Update_Object rules).

### D. Run and report
```bash
set VAL_USER_A_PASSWORD=...        # names come from config.json
python <skill>/scripts/run_validation.py --pack validation/pack.json --tests validation/automation
#   --include-slow   long real-time tests (idle time-out)      -k "vt_006"   a subset
#   --headed         watch the browser
```
Then: open `docs/STR.html`, review every step's screenshot, write a deviation for each Fail /
Blocked, and hand the package for approval. Report to the user: run ID, counts, each failure with
its observed value — never summarise a run you did not execute.

**Results into Orcanos** (when the tests are Orcanos test cases): use an Execution Set. Read it ONCE, add EVERY test
case that is in Orcanos but not in the set, put each step's result into the XML, then send it ONCE with
`Record_Execution_Results_New` and read it back. On **deploy** run the FULL regression, not only the linked tests;
while developing, run only the tests a change touches. Reference implementation:
`traceability-matrix/validation/scripts/release_run.py --full`.
See `orcanos-api/test-execution.md`. The local results and the STR are still written every time.

### E. Never
- Never mark a test Pass, edit `results.json`, or delete a failed run to hide it.
- Never put a password in `config.json`, `pack.json` or a test.
- Never run against a customer's production data — use a validation account/project.
- Never start long-lived dev servers to run the tests (the user's own servers hold the ports).

## Signing — paper or electronic

By default every document ends with a blank **Approval** table (Author / Reviewer / Approver) to sign on paper.
Set `meta.signing: "electronic"` in `pack.json` when the pack is e-signed in a tool that prints its own signature
table at the TOP of each document (traceability-matrix *Release validation*, 2026-11-04): the bottom table is left
out and the STR conclusion says "Subject to the signatures at the top of this document".

## Wording
Every test (VT and VER) follows the [`test-writing`](../test-writing/SKILL.md) skill: plain name of the
behaviour, concrete pre-conditions, one action per step, observable expected result, code ids only in Automation ID.

## Output to the user
Short: what was added/changed in the pack, documents regenerated (path), run ID and counts if a
run happened, open items (config values needed, tests not yet run against a live target).
