# Orcanos Supplier Management — the process

**Part of:** `orcanos-processes` · **Objects:** `Orcanos-infra/orcanos-supplier.md` · **API:** `orcanos-api`
**Built on it:** the Supplier Portal of the traceability-matrix platform
(`c:\AI Projects\traceability-matrix` — `design/DESIGN_SUPPLIER_PORTAL.md`, `src/backend/supplier_portal_map.py`).
Design only as of 2026-11-12: licence, nav entry and the field / status mapping screen are built; no SCAR flow yet.

---

## 0. Sources and precedence

| Ref | Source | Role |
|---|---|---|
| **[LIVE]** | orca60, 2026-11-12: QMS E-Forms tree, Supplier form, Action Item form | **Beats every document on facts** — field titles, codes, values. |
| **[PO]** | Product owner (Zohar), design chat 2026-11-12 — decisions D1–D18 of the design | Governs how the portal runs the process. |
| **[DESIGN]** | `design/DESIGN_SUPPLIER_PORTAL.md` §1, §1a, §2a | Intended SCAR fields / statuses; not yet seen live. |
| **[STD]** | ISO 13485:2016 §7.4 (Purchasing) · §8.3 (nonconforming product) · §8.5.2 (corrective action) | The vocabulary. Orcanos implements it; it does not redefine it. |

Configured vs inherent (house rule 4): **the Supplier form, status names, categories and review
intervals are per-customer configuration.** orca60's values are an example, never a default.

---

## 1. Why the process exists (ISO 13485 §7.4, in brief)

The manufacturer must **evaluate and select suppliers** by their ability to supply to requirements,
with criteria **proportionate to the risk** of what they supply; **monitor and re-evaluate** them;
keep **records** of evaluation, selection, monitoring and re-evaluation and of the actions taken; and
act on a supplier's failure to meet requirements — proportionate to the risk, and in line with the
regulatory requirements. A SCAR is the record of that action with the supplier.

---

## 2. The process in one picture

```
Supplier item (SUPLR-, QMS E-Forms → Suppliers)
   │  1. APPROVAL ─ criticality + quality system + certificate + (audit) + (quality agreement)
   │               → Approval Status routed and signed                       [§3]
   │
   │  2. PERIODIC REVIEW ─ due = Last Reviewed Date + interval (per category)
   │               → questionnaire / evaluation → result → new Last Reviewed Date  [§4]
   │
   │  3. CERTIFICATES ─ ISO cert validity watched → renewal before expiry     [§7]
   │
   ▼  4. A PROBLEM IN WHAT THEY SUPPLIED
NCR (Non Conformities) ──trace──► SCAR (SCAR-)                                [§5]
                                   Draft → Sent to supplier → Containment submitted
                                   → Root cause submitted → Effectiveness check → Closed
                                   │ children
                                   ├─ ACTION_ITEM  Category = Corrective Actions   [§6]
                                   └─ ACTION_ITEM  Category = Preventive Action
                                   │ optional trace, only when the cause is ALSO internal
                                   ▼
                                  CAPA
```

The SCAR outcome and the supplier's record feed the next periodic review (design proposal P1: the
review score counts the supplier's SCARs and NCRs of the last 12 months — **not confirmed**).

---

## 3. Approval [LIVE fields · STD]

Done on the **Supplier** item. The fields that carry it on orca60:

| Question | Field(s) |
|---|---|
| What do they supply, how much does it matter? | Product/Service provided · Quality impact rank of part/service on product · Final product risk severity · **Critical Supplier** |
| Is their quality system adequate? | Supplier Quality System · Quality Certification type and number · ISO cert validity |
| Audited? | Audit Approval · Audit approval date · Next Audit Date |
| Quality agreement? | Quality agreement applicable? · quality agreement status · Quality agreement signed date |
| **Decision** | **Approval Status** — a workflow field (seen "Under Review"), with **Start Routing**, so approval is routed and signed in Orcanos |

Criticality decides how deep the evaluation goes and how often the supplier is reviewed (§4).
Design proposal P2 (not confirmed): an *Approved with conditions* value for Approval Status and a
*Review score* number field.

---

## 4. Periodic (annual) review

```
next review due  =  Last Reviewed Date  +  interval(category)
```

- **There is no interval field on the orca60 Supplier form** [LIVE]. The interval is a rule kept
  outside the form — in the Supplier Portal, per category (e.g. Critical 365 d · Major 730 d · Minor
  1095 d) [PO D13]. If a customer's form has an interval field, it wins.
- Category comes from the matched field (Critical Supplier checkbox, or a category picklist).
- Orcanos already runs an annual supplier review **task** for quality; what Orcanos does not have is
  a place for the **supplier** to answer.
- Portal flow [PO D7, D14]: a questionnaire per category (versioned; a review keeps the version it
  opened with) → supplier answers → quality scores, sets the result and signs → Orcanos gets **the
  new Last Reviewed Date**, Approval Status, (score), and the answers as a **PDF attachment**. The
  answers themselves stay in the portal.
- Moving Last Reviewed Date moves the next due date — that is the whole schedule.

---

## 5. The SCAR lifecycle [DESIGN §1 · PO D3, D4, D9]

⚠️ The SCAR type exists on orca60 (added 2026-11-12) but **its live field titles and status names are
not recorded**. The statuses below are the design; each customer's names are mapped to these steps
(`supplier_portal_map.py` `STEPS`; two steps may share one status — then filled fields tell them apart).

| # | Status (design) | Who | What happens |
|---|---|---|---|
| 0 | **Draft** | Quality | SCAR raised, normally from an **NCR** (trace NCR → SCAR). Step 1 *Problem*: Supplier, Part, Lot / batch, Quantity affected, Defect description, **Severity** (Critical / Major / Minor), containment + root-cause due dates. |
| 1 | **Sent to supplier** | Quality | Set in Orcanos, or *Send* in the portal (sets the same status). The supplier's contacts are emailed. |
| 2 | **Containment submitted** | Supplier | Step 2: containment actions, stock at supplier / in transit, shipped parts disposition, containment date. |
| 3 | **Root cause submitted** | Supplier | Step 3: root cause, why not detected, and **at least one corrective action** (Action Items, §6). |
| 4 | **Effectiveness check** | Quality | Starts only when **every corrective action is Done**. Step 4: check method, **Effectiveness result** (Effective / Not effective). |
| 5 | **Closed** | Quality | Closed date. Quality's Accept / Close is the Part 11 e-signature (password re-checked through `QW_Login`) [PO D6]. |

- **Return** moves the SCAR back **one** status, with a comment to the supplier.
- **Nothing a supplier sends reaches Orcanos until quality accepts it**; each accept writes and reads
  back [PO D5].
- Evidence files go on the SCAR's **Attachments** tab.
- **SCAR → CAPA** only when the root cause is **also internal** (e.g. our spec, our incoming
  inspection missed it). A purely supplier-side cause is closed on the SCAR.
- *Not effective* at step 4 = the actions did not work: return to root cause / actions (design
  intent; the exact transition is the customer's workflow).

---

## 6. Actions = Action Items under the SCAR [LIVE form · PO D17]

- Each corrective or preventive action is an **Action Item** (`ACTION_ITEM`) created **under the
  SCAR** — as many as needed. Not text fields on the SCAR.
- **Category** says which kind: live values include **"Corrective Actions"** and **"Preventive
  Action"**. No such field on a customer's form → the kind goes in the name (`[CA] …` / `[PA] …`).
- Name + Description = the action; Due Date optional; owner at the supplier in a text field if one
  exists, else in the description.
- **Done = a status, never a date.** Move the item to a status with `IsComplete = 1`; Orcanos fills
  the **completion date** itself — never write it (`orcanos-api/get-item-statuses.md` rule 9).
  Done needs evidence (attachments on the action); quality accepts each one.
- Whether the actions *worked* is judged once, on the SCAR (step 4) — the action has no
  verification field.
- Orcanos also has separate **Corrective Action** / **Preventive Action** work item types (the CAPA
  family). They belong to an internal CAPA, not to a SCAR's supplier actions.

❓ **Open:** how to create an item **under a parent** through the API. `Parent_ID` via
`QW_Update_Object` answered success but **did not move** the item (traceability-matrix Critical Note
#118). An action counts only once `Get_Children` of the SCAR returns it.

---

## 7. Certificates

- On orca60 the certificate is **Quality Certification type and number** + **ISO cert validity**
  (the expiry) [LIVE].
- Watch the validity date: reminders before expiry (design: 60 / 30 / 7 days) → the supplier uploads
  a renewal → quality accepts → the field and the attachment are updated in Orcanos.
- An expired certificate is a re-evaluation trigger (§3), not just a data fix.
- ❓ `Add_Attachment` with `Object_Type = OBJECT` is unverified (Critical Note #111).

---

## 8. Traps

| # | Trap |
|---|---|
| 1 | Hard-coding Supplier field ids or titles — every customer's form differs; match **by title**, confirm with the admin. |
| 2 | Looking for a review-interval field — there isn't one on orca60; compute from Last Reviewed Date + a rule. |
| 3 | Confusing **Next Audit Date** with the next **review** date. |
| 4 | Writing an Action Item's completion date — Orcanos owns it; set an `IsComplete` status. |
| 5 | Using Corrective Action / Preventive Action types for SCAR actions — the chosen model is Action Items under the SCAR. |
| 6 | Treating a `Parent_ID` write's "success" as done — read back with `Get_Children`. |
| 7 | Finding QMS E-Forms by id — it is the same **name** in every account, not the same id. |
| 8 | Hard-coding SCAR status names — map the customer's statuses to the six steps. |
| 9 | Trusting the workflow to keep the SCAR's order — `QW_Update_Object` sets any status from any status (live 2026-11-12). Re-read the SCAR live before each write and refuse an answer for another step (traceability-matrix `supplier_portal_scar.live_scar`). |
| 10 | Matching a SCAR to its supplier by its shown text — the Supplier field is a *Work Item List Automation* list: stored = supplier item ID, shown = e.g. `25937-Test supplier`. Map text → ID through the form's options (`Orcanos-infra/orcanos-work-item-list-automation.md`); never a substring (traceability-matrix Note #131). |
| 11 | A SCAR filter without the Supplier column — the field comes back EMPTY, not as an error, so every SCAR is unmatched (orca60 filter 877, 2026-11-13). Check the filter selects it. |

---

## See also

- `Orcanos-infra/orcanos-supplier.md` — what the Supplier, SCAR and Action Item items are, their fields
- `orcanos-risk-process.md` — risk severity that drives supplier criticality
- `orcanos-api/get-item-statuses.md` — `IsComplete`, rule 9
- `orcanos-api/get-children.md` — a SCAR's Action Items
- `orcanos-workflow-chart` — status transitions and e-signature on a type
- traceability-matrix `design/DESIGN_SUPPLIER_PORTAL.md` — the implementation design (D1–D18, phases)
