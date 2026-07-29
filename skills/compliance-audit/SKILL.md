---
name: compliance-audit
description: Runs an ISO 27001:2022 (and later SOC2) compliance audit for a tool/repo — scans code, Supabase, Fly.io, Vercel config, does a static/config-based pentest pass, asks the user for evidence on anything that can't be scanned, and produces a ledger + report. Use when the user asks to audit, check compliance, or get a tool "audit-ready" for ISO 27001/SOC2.
revision: 1.0.0
---

# Compliance Audit Skill

Cross-project, framework-agnostic compliance auditing modeled on how platforms like
Cypago work: connectors pull evidence from each surface, a control registry maps that
evidence to framework controls, a ledger tracks status over time, and a report
surfaces what's covered vs what still needs the user's input. The company's org-wide
ISMS is assumed to already exist — this skill audits whether a *specific tool* is
actually in scope and compliant, not whether the company's ISO 27001 program exists.

Same design philosophy as this project's own security-fix tracking pattern
(`SECURITY_FIXES.md` in Orcanos QMS): a status ledger that gets updated in place, not a
fresh wall of text every run.

## Files in this skill
- `controls/iso27001-2022-annex-a.yaml` — the 93 Annex A controls, each mapped to check_ids.
- `controls/soc2-tsc.yaml` — add when the user is ready for SOC2 (see § Adding SOC2).
- `checks/registry.yaml` — the actual work items: connector, automation type, what "pass" means.
- `connectors/{code,supabase,fly,vercel,pentest,org}.md` — exactly how each connector performs its checks.

## Per-project setup

Each audited repo needs a `compliance/scope.yaml`:

```yaml
system_name: "Orcanos QMS"
frameworks: [iso27001-2022]        # add soc2-tsc once onboarded
connectors:
  code: true
  supabase: true
  fly: false        # true once FLY_API_TOKEN is set below
  vercel: false
  pentest: true      # static/config only — see connectors/pentest.md
credentials:          # env VAR NAMES only, never actual values — read at run time
  supabase_management_token_env: SUPABASE_MANAGEMENT_TOKEN
  supabase_project_ref_env: SUPABASE_PROJECT_REF
  fly_api_token_env: FLY_API_TOKEN
  vercel_api_token_env: VERCEL_API_TOKEN
ledger_path: compliance/ledger.json
report_path: compliance/ISO27001_REPORT.md
```

If `compliance/scope.yaml` doesn't exist yet, create it with the user (ask which
connectors actually apply — don't assume Fly/Vercel apply if the project doesn't use
them) before the first run.

## Running an audit

This is a genuine multi-agent orchestration task — parallel connectors each producing
independent findings, then a synthesis pass — so use the **Workflow tool**, not manual
sequential agent calls. Rough shape:

```js
phase('Scan')
const connectorResults = await parallel(
  enabledConnectors.map(name => () => agent(connectorPrompt(name), {
    phase: 'Scan', label: `scan:${name}`, schema: CONNECTOR_RESULT_SCHEMA,
  }))
)
phase('Synthesize')
const controlStatus = mapChecksToControls(connectorResults.filter(Boolean), controlsRegistry)
// org.* attestation checks: batch into one AskUserQuestion-driven pass, not per-item
```

Read the relevant `connectors/*.md` file into each connector agent's prompt — that file
IS the agent's instructions, don't re-derive them from scratch each run.

## Result schema

Every connector check returns:
```json
{
  "check_id": "code.secret_scanning",
  "status": "pass | fail | partial | blocked | not_applicable",
  "evidence": [{"file": "backend/api.py", "line": 240, "note": "..."}],
  "finding": "one-sentence description if status != pass",
  "recommendation": "concrete fix, if applicable"
}
```
`attestation` checks (org connector) use the same shape; `evidence` holds the
attestation text or document reference instead of a file:line.

## Ledger (`compliance/ledger.json`)

One entry per control_id, carried forward across runs and updated in place:
```json
{
  "framework": "iso27001-2022",
  "controls": {
    "A.8.5": {"status": "pass", "check_ids": ["code.authentication_review"], "last_checked": "<run date>", "history": [...]}
  }
}
```
Never duplicate a control's row across runs — update `status`/`last_checked` and append
to `history` only on a status *change*, same "don't duplicate findings" rule as the
security-fix tracker.

## Report

Generate **both**:
1. `compliance/ISO27001_REPORT.md` — git-tracked, diffable, same tone as
   `SECURITY_FIXES.md`: a table per theme (Organizational/People/Physical/
   Technological), status, evidence citation, what's still needed.
2. An HTML Artifact dashboard (via the Artifact tool — load `artifact-design` skill
   first) — overall %-compliant, per-theme breakdown, drill-down per control. This is
   the shareable/readable view; the Markdown file is the source of truth.

Overall status categories to summarize: **Compliant** (pass), **Compensating control**
(mitigated but not textbook — mirrors this project's `⏭️ Mitigated via ...` pattern),
**Gap — action needed**, **Blocked** (missing credential/connector), **N/A**.

## Adding SOC2 later

Create `controls/soc2-tsc.yaml` (Trust Services Criteria: CC1–CC9 Common Criteria, plus
Availability/Confidentiality/Processing Integrity/Privacy if in scope) using the exact
same check_ids already defined in `checks/registry.yaml` wherever they apply — SOC2's
CC6.x (logical access) and CC7.x (system operations) overlap heavily with ISO Annex A
8.x. Add new check_ids only for genuinely SOC2-specific requirements (e.g. formal
vendor risk assessment cadence). Don't re-run connectors per framework — one scan run
updates both frameworks' ledgers from the same evidence.

## Safety rules
- Credentials are always read from env vars named in `scope.yaml` — never ask the user to paste a token into chat, never print a token/secret value into a report or ledger.
- Pentest connector is static/config-only by default (see `connectors/pentest.md`) — no live traffic to any target without an explicit, per-run, user-named test URL and confirmation.
- This skill reports gaps; it does not silently fix code. If a run turns up a fixable code issue, say so and ask/act per the project's own CLAUDE.md rules (most projects: routine reversible fixes just get made and reported, not asked-permission-for) — but a compliance-audit run itself is a *reporting* pass, not a fix-it pass.
