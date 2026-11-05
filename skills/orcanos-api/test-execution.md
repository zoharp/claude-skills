# Test execution — record automated test results in Orcanos

Record automated test results in an Orcanos **Execution Set** (work item type `T_EXEC`), with a result for every step.
The flow came from the user (2026-11-04). The request bodies are copied from the swagger (`/orca60/api/swagger/docs/v2`).
✅ **Verified live 2026-11-04** (account `orcanos`, execution set 102142, API key header `OrcanosAPIKey`): 106 tests
recorded in one call and read back. Working implementation: `traceability-matrix/validation/scripts/release_run.py`.

**Read the XML once per run.** Don't fetch it per test. Run all the tests, fill in the one XML, send it once.

### What the live calls showed
- `Get_Execution_Run_Details_XML` answers **raw XML, not JSON** (no `IsSuccess` wrapper). Each call makes a new
  `Run Name="RUN_<M>_<D>_<YYYY>_<h>_<mm>_<ss>_AM"`; send back the one you got.
- Shape: `<Execution_Set_Run_Results ID Name Cycle><Run Name Version Start End User Type TestCount>` →
  `<TestInExecLine ID Order>` (ID = line id) → `<Test ID Original_ID/>`, `<Name>`, `<LastRunStatus>` (`NO_RUN`/`PASS`/`FAIL`),
  `<LastRunVersion>`, `<Steps><Step ID=" 306054" Order>` (⚠️ leading space in the ID; keep it) → `<Description>`, `<Expected>`,
  `<Actual>`, `<Run Status=""/>`, `<Time Start="" End=""/>`.
- Fill in: step `Run Status` = `PASS` / `FAIL` / `SKIP`; `Actual` (CDATA or escaped text both work); step + Run
  `Start`/`End` = `DD/MM/YYYY HH:MM:SS`; Run `Version` = the version under test as `04.34.001.0000` (free text,
  taken as given; it then shows in `LastRunVersion`). The test's `LastRunStatus` is computed by Orcanos from the steps.
- You may **remove** `TestInExecLine`s you did not run (and set `TestCount`); the rest stay untouched.
- `Record_Execution_Results_New` → `{"IsSuccess":true,"Data":"60400"}` (Data = the new run id).
- `AddTestToExecutionSet` with 105 ids comma-separated in one call → `"Test case added to execution set successfully."`.
- Put **every** test case you have in Orcanos into the set (automated or not); the ones not run stay `NO_RUN`.
- Never record when the runner broke: a pytest that stopped on a collection error ran nothing, and recording that
  writes a false FAIL on every test (happened once, 2026-11-04). Check that the linked functions actually ran first.
- The steps in the XML are the test case's **current** Orcanos steps. Map results to those, not to a local copy.

## The flow

1. **Read the execution set**: `Get_Execution_Run_Details_XML`. You get every test in the set, its steps, and its line IDs.
2. **Add any test that is missing**: if an automated test's Orcanos test case is not in that answer, call
   `AddTestToExecutionSet`, then read the set again so the new line shows up.
3. **Map each automated test to its Orcanos test**, using the test case ID and line ID (`TestInExecLineID`) from the XML.
   Map steps by their order number.
4. **Run the tests** in our environment. As each step runs, write its result **into the XML**: status (Pass / Fail),
   actual result (always on a Fail), dates, and who ran it.
5. **Send it all at once**: post the edited XML to `Record_Execution_Results_New`. Orcanos reads the results out of the XML.
6. **Always keep a local copy too**: save every test's and step's result (with timestamps and screenshots) on disk,
   and write them into the validation / verification protocol (the STR). Keep the local copy even if the Orcanos
   call fails, because that copy is the evidence.

All calls are `POST <base>/api/v2/Json/<method>` unless stated otherwise; `<base>` includes the tenant
(`https://app.orcanos.com/orca60`). Authentication is the same as every other call: [main skill](SKILL.md).

---

## Get_Execution_Run_Details_XML — read the set

```json
{
  "Execution_Set_ID": 36373,
  "Run_Status_Filter": "",        // e.g. "No run, Fail"; empty = all
  "Assigned_Filter": "",          // users, comma-separated; empty = all
  "Work_Status_Filter": "",
  "Test_ID": "",                  // test case ids "12121, 343"; empty = all
  "TestInExecLineID": "",         // specific test instances (lines) in the set
  "Type": "Auto",                 // "Auto" (default) / "Manual"
  "convertHTMLtoText": true
}
```
Returns `ResultClass[String]`. The string is the **XML** of the run: each test in the set, its line ID, its steps and test data.
Keep the XML exactly as returned. It is the template you send back.

## AddTestToExecutionSet — add a missing test

```json
{ "VersionId": "1296", "ExecutionSetID": "36373", "TestCaseIDs": "109156,109157" }
```
All values are **strings**. `TestCaseIDs` accepts several IDs separated by commas, so one call covers every missing test.
Before adding, check the details XML first so a test never ends up in the set twice.

## Record_Execution_Results_New — write the results

```json
{ "sXML": "<the XML from Get_Execution_Run_Details_XML, with the results filled in>" }
```
The swagger says to escape `"` inside the XML as `\"`. A JSON serializer (`json.dumps`) does this already, so send the
XML as a normal JSON string and never escape it twice. After the call, read the set again (`Run_Status_Filter` empty)
and confirm the statuses changed. Treat `IsSuccess: true` alone as unproven.

## Related calls (from the swagger, not used in the flow)
- `GET /v2/Json/QW_Get_Execution_Set?VersionId=&ItemType=T_EXEC&ItemId=&PageNo=1&PageSize=10&SearchQuery=` lists the
  test cases in a set (JSON, paged).
- `RemoveTestFromExecutionSet` takes `{Version, ExecutionSetID, TestCaseID, LineID, KeepRunHistory: "Y"|"N"}`.

## See also
- [QW_Add_Step](qw-add-step.md): how the test case's steps were created (their order = the step mapping)
- [`validation-pack`](../validation-pack/SKILL.md): where the local results and the protocol (STR) live
