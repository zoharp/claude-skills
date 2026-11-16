---
name: orcanos-processes
description: How Orcanos QMS processes actually run end to end — training, risk management (FMEA / ISO 14971 scoring), document control, CAPA and the rest. The workflow layer: triggers, states, roles, who signs what. Use with Orcanos-infra (what the objects are) and orcanos-api (how to call them).
revision: 1.0.0
---

# Orcanos Processes — Router

This skill family describes **how a QMS process runs inside Orcanos** — what fires it, what gets
created, who signs, and where the records land.

| Layer | Skill | Answers |
|---|---|---|
| **Process** | **this skill** | *What happens when a document is approved? Who signs the training record?* |
| **Objects** | `Orcanos-infra` | *What is a work item? What does `TRN_TSK` mean?* |
| **API** | `orcanos-api` | *How do I call `QW_Login` / `QW_Add_Object`?* |

## Files in this skill

| File | Process | Status |
|---|---|---|
| `orcanos-training-process.md` | **Training Management** — Read & Understand automation, formal/manual training, launch paths, evidence | Written from customer-facing decks |
| `orcanos-supplier-process.md` | **Supplier Management** — ISO 13485 §7.4: approval, periodic review (Last Reviewed Date + interval), SCAR lifecycle (NCR → SCAR → Action Items → effectiveness → optional CAPA), certificate expiry; maps onto `Orcanos-infra/orcanos-supplier.md` | Live orca60 forms (2026-11-12) + Supplier Portal design D1–D18 |
| `orcanos-document-control-process.md` | **Document Control (DMS)** — Routing State is THE state (Status unused): Draft · In Work · Approved · Pending Approved (signed, waiting for its ECO) · Obsolete · Cancel · Reject; revisions, ECO columns per revision, the Training section (hide Training List, show Roles + Trainees), Doc Review | Product owner 2026-11-13 + live orca60 |
| `orcanos-version-management-process.md` | **Version / baseline management** — open / freeze / lock versions, Branch vs Save, planning 1.x beside 2.0 (KB's 4 use cases), Move to View, Cancel Branch; roles + admin screens | KB *Version (Baseline) Management* (2026-11-15) |
| `orcanos-risk-process.md` | **Risk Management** — ISO 14971 / FMEA as Orcanos runs it: the Risk item's fields and codes, FMEA settings and the four calculation shapes (P×S table, P hazard × P harm = P total, S×P×D, same severity), mitigation → test → run, Excel import rules | KB *FMEA Settings* + live orca60 + product owner |

## Planned

`capa-process.md` · `complaint-process.md` ·
`change-control-process.md` · `audit-process.md`

---

## House rules for this family

1. **Cite the source.** Every process claim carries a reference to the deck/slide, KB page or live
   observation it came from. A process description with no provenance cannot be checked later.
2. **Name the conflicts, don't smooth them.** Where two sources disagree, record both, state which
   one governs and why. Silently picking one is how a wrong workflow gets built.
3. **A screenshot beats a bullet.** Rendered keys, field names and status values in a screenshot are
   evidence; a prose bullet describing them is a claim.
4. **Separate configured from inherent.** Much of what a tenant sees is template and admin setup, not
   product behaviour. Say which is which, or the next customer's install reads as broken.
