---
name: pr-review
description: Efficient senior-level PR/code review focused on correctness, regressions, edge cases, maintainability, security, and production risk. Reviews changed code and directly impacted areas only. Avoids low-value style nitpicks and unrelated architecture criticism.
license: MIT
---

# PR Review Skill

## Goal

Review code changes like a strong senior engineer:
- Find bugs and regressions
- Validate spec/ticket alignment
- Identify edge cases and failure paths
- Catch security/performance risks
- Ensure maintainable implementation

Focus ONLY on:
- Changed code
- Directly impacted areas
- Real production risk

Do NOT:
- Rewrite unrelated code
- Suggest large refactors unless necessary
- Nitpick formatting or subjective style
- Criticize architecture unrelated to the change

---

# Review Strategy

## Step 1 — Understand Context

Before reviewing:
- What problem is being solved?
- What behavior changed?
- What files changed?
- Is there a spec, ticket, or expected behavior?
- What parts of the system are impacted?

If a spec/design exists:
- Read it first
- Validate implementation against it

---

## Step 2 — Review Like Production Will Break

Assume this code may fail in production.

Ask:
- What breaks first?
- What happens on invalid input?
- What happens on timeout?
- What happens on partial failure?
- What happens with null/empty data?
- Can this corrupt data?
- Can this create inconsistent state?
- Can this break existing flows?

This is more important than style.

---

# Core Review Areas

## 1. Correctness
- [ ] Logic works as intended
- [ ] Matches spec/ticket
- [ ] Handles edge cases
- [ ] Handles async/concurrency safely
- [ ] No obvious broken flows

Focus on:
- null/undefined
- empty collections
- retries
- duplicate actions
- stale state
- race conditions
- incorrect assumptions

---

## 2. Regression Risk
- [ ] Existing flows still work
- [ ] Existing callers still work
- [ ] Contracts remain compatible
- [ ] Changes don't silently alter behavior

Pay extra attention to:
- shared utilities
- auth flows
- DB schema changes
- state management
- caching
- API response shapes

---

## 3. Error Handling
- [ ] Failures handled explicitly
- [ ] No silent failures
- [ ] User sees meaningful errors
- [ ] Logs contain useful debugging info
- [ ] Timeouts/retries handled where needed
- [ ] Async/streaming failures handled cleanly

Check:
- backend endpoints
- frontend fetches
- background jobs
- queues/events
- external API calls

---

## 4. Security
Review ONLY if relevant to the change.

Check for:
- missing auth/permission checks
- injection risks
- unsafe input handling
- secrets exposure
- sensitive logging
- insecure file handling
- unsafe AI/LLM behavior
- PII leakage

Prioritize:
- auth bypass
- privilege escalation
- data exposure

---

## 5. Performance
Review ONLY if relevant.

Check for:
- unnecessary DB/API calls
- unbounded queries
- N+1 queries
- blocking async flows
- excessive rendering
- memory-heavy logic
- large payloads
- missing pagination
- expensive operations inside loops

Focus on realistic bottlenecks.

---

## 6. Maintainability
- [ ] Code is understandable
- [ ] Naming is clear
- [ ] Logic is not duplicated
- [ ] Complexity is reasonable
- [ ] Follows existing project patterns
- [ ] Debug/dead code removed

Prefer:
- clarity
- consistency
- simplicity

Avoid overengineering.

---

## 7. Tests
- [ ] Tests cover changed behavior
- [ ] Edge cases tested
- [ ] Failure paths tested where important
- [ ] Regression coverage exists

Focus on:
- business logic
- critical flows
- risky changes

Do not demand unnecessary test duplication.

---

# Optional Deep Checks

Run ONLY when relevant.

## Database
- migration safety
- query efficiency
- index usage
- transaction correctness

## Frontend
- accessibility
- render performance
- state consistency

## Infrastructure
- deployment safety
- config/env correctness
- backward compatibility

## AI/LLM
- prompt injection
- hallucination risk
- timeout/cost control
- source validation

---

# Anti-Noise Rules

Do NOT generate low-value comments:
- trivial formatting opinions
- subjective style preferences
- comments without impact
- repeated comments for same pattern
- unnecessary rewrite suggestions
- theoretical problems with no practical risk

Every issue should answer:
- What is wrong?
- Why does it matter?
- What could break?
- How should it be fixed?

---

# Severity Levels

## Critical
Must fix before merge.
Examples:
- security vulnerability
- data corruption
- auth bypass
- crash
- production-breaking regression
- silent failure

## Important
Should fix before merge.
Examples:
- missing edge case
- incorrect behavior
- performance concern
- maintainability problem
- missing error handling

## Suggestion
Nice-to-have improvement.
Examples:
- readability
- simplification
- minor cleanup

---

# Review Output Format

## Summary
2-5 sentences:
- overall quality
- major risks
- merge confidence

## Critical Issues
For each:
- Location
- Problem
- Impact
- Recommended fix

## Important Issues
For each:
- Location
- Problem
- Recommended fix

## Suggestions
Minor improvements only if valuable.

## Regression Risks
List existing behaviors that could break.

## Verdict
- Approved
- Approved with suggestions
- Changes required

---

# Reviewer Principles

Good reviews:
- prioritize correctness over style
- focus on production risk
- explain impact clearly
- suggest concrete fixes
- stay concise
- review pragmatically
- avoid perfectionism

The goal is safer, more reliable code — not personal preference.