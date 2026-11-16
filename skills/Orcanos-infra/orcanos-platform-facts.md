---
name: orcanos-platform-facts
description: Facts about the Orcanos QMS platform itself (security certification, hosting, sign-in / SSO / MFA, module coverage) for answering customer RFIs, CRS / URS compliance matrices and security questionnaires. Use when a prospect asks "do you have / support X" about the platform, not the API.
revision: 1.0.0
---

# Orcanos platform facts — for RFIs, CRS answers and security questionnaires

Every fact here names its **source** and **date**. Use only these in a customer answer. Anything not listed
is **To confirm** with the product owner (Zohar), never filled from memory or marketing copy.
Never put one customer's name in this file (project rule: no customer names).

## Security & certification

| Topic | Fact | Source |
|---|---|---|
| Information security certification | **Orcanos holds ISO/IEC 27001** (current certificate). Answers a "SOC 2 Type II **or** ISO 27001" knockout. Attach the certificate + its scope statement. | Product owner, 2026-11-12 |
| SOC 2 Type II | Not stated — do not claim it. | — |

## Hosting

| Topic | Fact | Source |
|---|---|---|
| US customers | Hosted on **AWS in a US region**; backups **geo-replicated to a second US region** (data stays in the US). | Product owner, 2026-11-12 |
| RPO / RTO, BC/DR test cadence, pen-test cadence, incident-notice time | **To confirm** — don't quote numbers until confirmed. | — |

> The Traceability add-on (this repo) runs separately on Fly.io (US + EU regions, Note #55) — a different
> answer from the core Orcanos QMS hosting above. Say which product a hosting answer covers.

## Sign-in, SSO and MFA

| Topic | Fact | Source |
|---|---|---|
| SSO | Supported: **SAML 2.0**, **Google** (Workspace), **Microsoft / Office 365**, **Active Directory**, and similar identity providers. | Product owner, 2026-11-12 |
| MFA | **Enforced through the SSO identity provider** ("MFA is embedded there") — the customer's Google / Microsoft / AD policy applies MFA to Orcanos sign-in. | Product owner, 2026-11-12 |
| Answer pattern | "MFA required (knockout)" → *Yes — through SSO with the customer's identity provider (SAML 2.0 / Google / Microsoft / AD), which enforces MFA.* | — |

## Module coverage (QMS side)

| Area | Fact | Source |
|---|---|---|
| Equipment & calibration | **Configured** from work item types + workflows (no out-of-the-box module). Answer *Configurable*. | Product owner, 2026-11-12 |
| GLP (21 CFR 58: protocols, master schedule, QAU inspections) | **Configured** the same way. Answer *Configurable*. | Product owner, 2026-11-12 |
| MDR / eMDR | Complaint records the MDR decision + 30-day / 5-day due dates. eMDR **phased plan**: Phase 1 = build the eMDR (HL7 ICSR XML, Form 3500A fields) from the complaint, validate against FDA rules, download for ESG; Phase 2 = submit through the **ESG NextGen API** and track ACK1/2/3. RFI answer: *Export file* (Phase 1), *ESG submission* on the roadmap. Check Phase 1 is really there before a demo shows it. | Product owner, 2026-11-12 |

## Design-control side (shipped in the Traceability add-on — see this repo's CLAUDE.md for state)

Trace matrix L1–L6 + gap detection, Traceability Dashboard, DHF (document scoring, baselines, branches),
Risk Management (FMEA, ISO 14971), Software BOM (CycloneDX, OSV/KEV vulnerabilities, VEX), BOM Viewer +
product structures, Jira / GitHub / Azure DevOps two-way integrations, AI suggestions with confidence +
human accept/edit/reject log (AI Dashboard), Report booklets (HTML/PDF), release validation package
(VP/URS/SRS/STD/RTM/STR). Several are marked "fakes only / not live" in CLAUDE.md — say *available* only
for what has run live; otherwise *Released, rolling out* or demo-only.

## See also
- `orcanos-work-items.md` — item types and codes
- `compliance-audit` skill — ISO 27001 evidence ledger
