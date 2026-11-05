---
name: test-writing
description: Write clear, complete test cases a reviewer understands without reading code — name, pre-conditions, one-action steps, observable expected results — for validation tests (user scenarios) and verification tests (developer tests described in plain words). Use whenever writing or rewriting test cases, test protocols, STD/VT/VER files, or test cases pushed to Orcanos.
---

# test-writing — clear test cases

A test case is read by a **QA reviewer or auditor who has never seen the code**. If they cannot tell
from the test alone what is checked, how, and what counts as a pass, the test is not finished.
This skill is the wording standard; `validation-pack` holds the validation rules (user scenarios,
real UI, checked against Orcanos, never hand-written results). Use both.

## The five parts

| Part | Rule | Bad | Good |
|---|---|---|---|
| **Name** | A plain sentence of the **behaviour checked**, user language, ≤ 100 chars. No ids, no code names, no "Verify:", no "Developer tests for…". | `Developer tests for SRS-210.1` · `Per-side compare, no echo` | `Calculated risk fields are never imported from the spreadsheet` |
| **Pre-conditions** | The **concrete state** before step 1: which data exists (with the property that matters), which user, which settings. Things a tester can set up or check. No tool instructions. | `Repository checkout; pytest from the repo root` | `A risk panel with two risks in the same matrix cell at different stored levels, and one risk whose stored level disagrees with the risk table.` |
| **Steps — action** | **One** action per step, imperative, naming the screen / control / data used. | `Run tests/test_risk.py::test_legend…` | `Open the risk matrix and look at the cell that holds the two risks.` |
| **Steps — expected** | An **observable** result with the value to compare. A sentence, not a code note. Pass/fail must be decidable by looking. | `legend sum = cell numbers` · `mapping 400` · `OK` | `The total of the legend equals the sum of the numbers in the cells; risks without a level are not counted.` |
| **Automation ID** | Where the test is automated: the developer test id(s) (`tests/x.py::test_y`) or the Playwright test. **Only here** — never in the name or steps. | | `tests/test_risk.py::test_legend_adds_up_to_the_matrix_cells` |

## Validation test (VT) vs verification test (VER)

- **Validation** = the user's scenario in the real UI. Steps are clicks and reads a user does; expected
  results are what the user sees, checked against Orcanos.
- **Verification** = what the developer tests prove, **described as the behaviour** they exercise:
  the input situation → the action → the result. Write it as if a person did it by hand (it could be);
  the pytest ids go only into Automation ID. A VER step may describe a server-side result ("The server
  refuses the request with *403 — Add permission needed*") when there is no screen for it.
- One developer test that checks three things = three steps. Five developer tests that check one thing
  = one step. Steps follow **behaviours**, not test functions.

## Checklist before saving

1. Could a reviewer who never saw the code run this by hand from the text alone?
2. Does the name say what is checked — not which requirement or which function?
3. Is every pre-condition something the tester can create or confirm?
4. One action per step? Every expected result observable and specific (values, messages in *italics*
   quoted from the source, counts)?
5. Negative cases present where the requirement has a "never" / "only" / "refuses"?
6. No requirement ids, file paths, function names or jargon (`409`, `Filter_By`, `snapshot`) outside
   Automation ID — unless the reader of that test really sees it (an error code shown on screen).
7. Every message text and behaviour **read from the code or docs**, never guessed.

## Example (before → after)

Before (unreadable):
```
VER-203.4 Verify: Matrix cells take the worst stored level; the legend adds up
Pre-conditions: Repository checkout; pytest from the repo root …
1 Run tests/test_risk.py::test_heatmap_cell_shows_the_stored_level_not_the_settings_one | occupied cell shows stored level and mismatch
2 Run tests/test_risk.py::test_legend_adds_up_to_the_matrix_cells | legend sum = cell numbers
```
After:
```
Name: Risk matrix cell shows the worst stored risk level, and the legend totals match the cells
Pre-conditions: A risk panel whose risks have stored levels in Orcanos, including two risks in the same
  matrix cell with different levels, and one risk whose stored level disagrees with the project's risk table.
1 Open the risk matrix and look at the cell holding the two risks. | The cell has the colour of the worse of the two stored levels, not the colour of the risk table.
2 Look at the cell holding the disagreeing risk. | The cell shows a mark saying 1 risk disagrees with the table.
3 Look at an empty cell. | It has the colour the risk table gives it.
4 Add up the numbers in the legend. | The total equals the sum of the numbers in the cells; risks without a level are not counted.
Automation ID: tests/test_risk.py::test_heatmap_cell_shows_the_stored_level_not_the_settings_one, tests/test_risk.py::test_legend_adds_up_to_the_matrix_cells
```

## In Orcanos (Test Case item)

- **Name** → `Object_Name` (a project may prefix its own id, e.g. `[VT-210] …`, to match the source file).
- **Description** → **Pre-conditions only**. No purpose, evidence, requirement ids — the traces show the links.
- **Steps** → real steps (`QW_Add_Step`); rewrite with `UpdateStep` / `DeleteStep`, `ObjectType: "OBJECT"`
  (see `orcanos-api/qw-add-step.md`).
- **Automation ID** → custom field `CS1_Name: "Automation ID"` on `QW_Add_Object` / `QW_Update_Object`.

## See also
- [`validation-pack`](../validation-pack/SKILL.md) — validation package rules, generator, runner.
- [`orcanos-api/qw-add-step.md`](../orcanos-api/qw-add-step.md) — step add / update / delete.
