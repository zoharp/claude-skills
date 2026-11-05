# Orcanos Risk Management — the process

**Part of:** `orcanos-processes` · **Objects:** `Orcanos-infra` · **API:** `orcanos-api`
**Built on it:** the Risk Management module of the traceability-matrix platform
(`c:\AI Projects\traceability-matrix` — `docs/RISK_MANAGEMENT.md`, Critical Notes #87–#95).

---

## 0. Sources and precedence

| Ref | Source | Role |
|---|---|---|
| **[KB]** | *FMEA Settings* — https://help.orcanos.com/knowledgebase/fmea-settings-2/ | What each FMEA setting means. **Governs** the meaning of a setting. |
| **[LIVE]** | orca60, measured 2026-10-07/08: Risk form (`QW_Get_Item_Add_Edit`, fixture `tests/fixtures/risk_form_orca60.json`), FMEA settings tab (fixture `risk_fmea_settings_orca60.html`), relations (`risk_relations_orca60.json`) | **Beats every document on facts** — field names, codes, values. |
| **[PO]** | Product owner (Zohar), 2026-10-08 | Import rules in §6 — they govern. |
| **[STD]** | ISO 14971:2019 (risk management for medical devices), IEC 60812 (FMEA) | The vocabulary. Orcanos implements it; it does not redefine it. |

Configured vs inherent (house rule 4): **the scoring method, the scales, the level names and the
tables are per-project configuration.** Everything in §3 is the *machinery*; orca60's values are
an example, never a default to assume for another tenant.

---

## 1. The process in one picture (ISO 14971 as Orcanos runs it)

```
Hazard ─► Hazardous situation ─► Harm            (risk ANALYSIS — the Risk item's text fields)
              │
              ▼
   P (probability) × S (severity) [× D]  ─►  Risk level BEFORE control   (risk EVALUATION — "Pre")
              │                                      │ unacceptable / ALAP?
              ▼                                      ▼
   Risk control (mitigation) = a REQUIREMENT traced to the risk           (risk CONTROL)
              │   "Risk Mitigation" link: SR-12851 → RISK-21937
              ▼
   Verification = a TEST CASE traced to that requirement ─► its last TEST RUN result
              │   "Test Verification" link: TC-8788 → SR-12851
              ▼
   P₂ × S₂ [× D₂] ─► Risk level AFTER control ("Post", residual)          (residual EVALUATION)
              │
              ▼
   Acceptable? · New risk introduced after mitigation? · overall residual risk / benefit-risk
              │
              ▼
   Production & post-production: complaints (COMP), CAPAs, recalls traced back to the risk
```

A risk is **controlled** only when the whole chain holds: mitigation → test → a *passed* run. A
mitigation with no test is *mitigated*, not *verified* (Critical Note #89).

---

## 2. The Risk item [LIVE orca60]

Item type code **`RISK`**, key `RISK-<id>`. Fields of the Add/Edit form (`name` | title | type):

| Area | Fields |
|---|---|
| Identity | `Obj_name` Name · `Obj_status` Status (`NEW` Identify Hazard → `IN_PROGRESS` Estimation; workflow is per tenant) · `Assigned_to` · `Obj_category` Category (`CODE_1` 01 - Intended Use … ISO 14971 Annex C questions) · `Obj_description` |
| Analysis | `CS94` Hazard · `CS310` Hazardous Situation · `CS1` Failure Mode · `CS2` Cause Of Failure · `CS16` Affected (Patient, Operator, Bystanders…) · `CS65` Applicable Component · `CS10` FMEA Type (DFMEA, FMEA, UFMEA, FTA, HACCP) |
| Before control | `CS3` P1 · `CS4` S1 · `CS5` D1 · `CS357` P Hazard (pre) · `CS358` P Harm (pre) · **calc:** `CS6` RPN1, `CS44` RPN Pre (the level) |
| Control | `CS15` Risk Control (text) · `CS43` Control Type (Safety By Design / Protective Measure / Information For Safety — the ISO 14971 7.1 order) |
| After control | `CS11` P2 · `CS12` S2 · `CS13` D2 · `CS359` P Hazard (post) · `CS360` P Harm (post) · **calc:** `CS14` RPN2, `CS45` RPN Post |
| Decision | `CS129` Acceptable? (checkbox) · `CS121` New Risk Introduced After Mitigation? (checkbox) |
| Links (pickers) | `CS96` Harm Analysis · `CS76` Risk List · `CS217` Complaint List |

**There is no Harm text field on orca60** — harm lives in a linked *Harm Analysis* item (`HA`).
Hazard, hazardous situation, harm, cause and failure mode are five different ISO 14971 concepts;
never put one into another's field.

### Codes and labels — the trap
Every score list has a **code** and a **description** [LIVE]:

| Field | code | label |
|---|---|---|
| P1 / P2 | `1`…`5` | `1-Improbable` `2-Remote` `3-Occasional` `4-Probable` `5-Frequent` |
| S1 / S2 | `1`…`5` | `1-Negligible` `2-Minor` `3-Serious` `4-Critical` `5-Catastrophic` |
| D1 / D2 | `1`…`5` | `1-Almost Certain` `2-High` `3-Moderate` `4-Low` `5-Remote` |
| P Hazard | `1`…`5` | `1-Improbable / Unlikely` … `5-Frequent` |
| P Harm | `1`…`5` | `1-Extremely Rare` `2-Rare` `3-Unusal` `4-Sometimes` `5-Always` |
| RPN Pre / Post | `LEVEL_0`…`LEVEL_4` | `Low` `Acceptable` `ALAP` `Unacceptable` `Very High` |

- **The code of a score IS the score.** Match a number to the code, never to digits inside the
  label: [KB] *Layout presentation* lets a project show *Code, Description or Both*, and labels are
  editable in System tables — a label may be just "Occasional".
- Writing (`QW_Add_Object` `CS<n>_value`) sends the **code** (`"3"`), never the label — S1/P1 are
  2-character columns and a label is refused (*"Max length of custom field S1 is 2"*, live 2026-10-08); reading a filter returns the
  **label** (`"5-Frequent"`; unset is `"None"` or `"0-0"`).
- **ALAP** is Orcanos's spelling of ALARP. Accept both.
- The risk level's codes are `LEVEL_n`, ordered lowest → highest; zones come from the tenant's
  labels and order, never fixed numbers.

---

## 3. FMEA settings — how a project scores a risk [KB] [LIVE]

*Admin → project → **FMEA** tab* (new-project defaults: *Admin → New Project Defaults → FMEA
Settings*). Per project. **There is no API**: the tab is a web form
(`web/admin/fmeasettingspartial?ProjectId=…`), readable only with project-admin rights
(Critical Note #87).

| Setting | Form field | Meaning |
|---|---|---|
| **RPN calculation method** | `rpn` = `RPN` (scalar) / `RESIDUAL` (tabular) | Scalar: RPN = S × P (× D), a number banded into ranges. Tabular: the level is read from the **RPN table** (P row × S column). |
| **Range** | `rpn_range` 5 / 10 | Scales 1–5 or 1–10. |
| **Same Severity for Initial/Residual RPN** | `same_severity` | S after control **cannot be edited** and equals S before. A control can lower P (and D), never S. |
| **Use ALAP** | `use_alarp` | An ALAP (ALARP) band between acceptable and unacceptable. |
| **Use P-hazard × P-harm = P-total** | `Use_PHZ_PHM` | P is not entered; it is **P total**, read from the P-total table of P hazard × P harm (ISO 14971 Annex C: P1 = probability the hazardous situation occurs, P2 = probability it leads to harm). **Tabular method only.** |
| **Use detectability** | `use_detectible` | Scalar only: RPN = S × P × D. |
| Acceptability ranges (scalar) | `range_N_display/_from/_to/_color_html` | Up to five bands of the RPN number. |
| RPN table (tabular) | `risk_prn[i].{freq,severity,result}` | P × S → `LEVEL_n`. |
| P-total table | `risk_ptotal[i].{hazard,harm,result}` | P hazard × P harm → P. |

### The four calculation shapes

| Project setting | Inputs per phase | Calculated by Orcanos |
|---|---|---|
| Tabular | P, S | Level = RPN table[P][S] |
| Tabular + P-hazard × P-harm | **P hazard, P harm**, S | P = P-total[Phz][Phm]; Level = RPN table[P][S] |
| Scalar | P, S | RPN = P × S; Level = range of RPN |
| Scalar + detectability | P, S, **D** | RPN = P × S × D; Level = range of RPN |

Add *same severity* to any of them: S after = S before, calculated.

**Calculated, never entered:** RPN1 / RPN2, RPN Pre / RPN Post (the level), P1 / P2 when P is
P total, S2 with same severity.

### orca60 example [LIVE 2026-10-07] — not a default

Tabular, range 5, same severity **on**, ALAP **on**, P-hazard × P-harm **on**, detectability off.

```
P-total (rows P hazard, cols P harm)      RPN table (rows P, cols S)
     1 2 3 4 5                                 1    2    3    4    5
  1  1 1 1 2 3                            1  Acc  Acc  Acc  ALAP ALAP
  2  1 1 2 3 4                            2  Acc  ALAP ALAP ALAP Unac
  3  1 2 3 4 5                            3  Acc  ALAP ALAP Unac Unac
  4  2 3 4 5 5                            4  ALAP ALAP Unac Unac Unac
  5  3 4 5 5 5                            5  ALAP Unac Unac Unac Unac
```
Levels: Low (<1) · Acceptable (1–8) · ALAP (9–11) · Unacceptable (12–1000) · Very High (>1000).

Orcanos's **stored** level can disagree with its own table (3 of 33 orca60 risks): show the stored
one, flag the mismatch, and gate on the **worse** of the two (Critical Note #88).

---

## 4. Risk control and verification — the trace chain [LIVE]

- A mitigation is a **requirement** (SR, UR, MecRS, …) related to the risk. `QW_Get_Object_Relations`
  returns the link type: `SR-12851 → RISK-21937 "Risk Mitigation"`, `TC-8788 → SR-12851 "Test
  Verification"`, `RECAL → RISK "Relates To"`. Tenants that link everything "Dependent On" have no
  typed links — only gate on type when the tenant uses it (Critical Note #92).
- `Traced Items Info` on the risk lists its traced keys, but **not** cross-project ones, and can miss
  relations — walk the relations too.
- Not a mitigation: complaints (`COMP`), CAPAs, defects, other risks, harm analyses, recalls. A
  complaint traced to a risk is **field signal** (post-production), not a control.
- Verification is a **test case** traced to the mitigation; its result is the last **test run**
  (`T_RUN`, a filter column `Last_Run_Status`) — no API returns it on the item.

Control status: *uncontrolled* (needs a control, has none) → *mitigated* (control, no test) →
*verified-failing* / *controlled* (test passed). No test filter ⇒ never "controlled".

---

## 5. Risk records and reports

- Risk list (`CS76`) / Harm Analysis (`CS96`) are item pickers — the analysis hierarchy is items
  linked to items, not text.
- Baselines freeze the risk file at a moment; a report compares two baselines (what moved, which
  levels changed, which controls were added). An export renders the snapshot, never a live re-read.
- ISO 14971 asks for the **overall residual risk** evaluation and the risk management report —
  outside the single Risk item.

---

## 6. Importing a risk file from Excel — the rules [PO 2026-10-08]

1. **Scores map by CODE.** A file's `3` is the option whose Orcanos code is `3`, whatever its
   label shows.
2. **Read the project's method first** (§3) and compare it to the file's columns. When they differ,
   **stop and say why** — never convert:
   - file has a single **P**, project uses **P hazard × P harm** → one number cannot be split back;
   - file has **P hazard / P harm**, project uses a single P → no P-total table to combine them;
   - project is **S × P × D**, file has no **D** → every RPN would be wrong;
   - file has **D**, project does not use it → a file scored S × P × D would get another level;
   - project has **same severity**, file's S changes after control → another method.
   The person resolves it: change the file, change the project's FMEA settings, or keep those
   columns as text in the description (the risk is then created without scores).
3. **Calculated fields are never imported** — RPN, risk level, P total, S after (same severity).
   Show them disabled: *Automatic calculation*. They are filled from the imported scores by the
   project's own method.
4. A 1–10 file into a 1–5 project is a **banding the person confirms** (Critical Note #90).

---

## 7. Traps (each one has cost a release)

| # | Trap | Note |
|---|---|---|
| 1 | FMEA settings read as a web form; a non-admin gets a 200 page that is not the form | #87 |
| 2 | Stored level ≠ computed level; show stored, gate on the worse | #88 |
| 3 | Values arrive as labels; `0-0` / `None` = unset | #88 |
| 4 | Every miss in the control walk is silent | #89 |
| 5 | An import that applies a banding nobody confirmed | #90 |
| 6 | A score matched by the digit in its label, on a project that shows descriptions only | #95 |
| 7 | A single-P file imported into a P-hazard × P-harm project: P lands nowhere, every level blank | #95 |
