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
| `orcanos-risk-process.md` | **Risk Management** — ISO 14971 / FMEA as Orcanos runs it: the Risk item's fields and codes, FMEA settings and the four calculation shapes (P×S table, P hazard × P harm = P total, S×P×D, same severity), mitigation → test → run, Excel import rules | KB *FMEA Settings* + live orca60 + product owner |

## Planned

`document-control-process.md` · `capa-process.md` · `complaint-process.md` ·
`change-control-process.md` · `audit-process.md` · `supplier-process.md`

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
