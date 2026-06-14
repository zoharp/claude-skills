---
name: spec-review
description: High-signal review of technical specifications. Focuses on breaking risks, schema/API consistency, migration safety, frontend/backend alignment, architectural gaps, and implementation feasibility. Use for backend specs, APIs, database changes, architecture designs, migrations, and multi-layer system changes.
license: MIT
---

# Spec Review Skill

## Core Principles

- Prioritize critical risks over completeness
- Do not assume undocumented behavior
- Flag ambiguity instead of guessing
- Quote exact contradictions when possible
- Focus on implementation reality, not theory
- Prefer actionable findings over generic comments
- Detect hidden breaking changes
- Review from production impact perspective

---

# Review Priority Order

Always review in this order:

1. Data loss / migration risks
2. Breaking API/schema changes
3. Frontend/backend mismatches
4. Auth / permission gaps
5. Concurrency / state risks
6. Performance bottlenecks
7. Architecture consistency
8. Naming / style

---

# High-Risk Review Areas

## 1. Migration & Data Safety

### Critical Checks
- [ ] No destructive migrations without rollback
- [ ] Backfill runs before NOT NULL constraints
- [ ] Old data remains compatible
- [ ] Rollback path documented
- [ ] Cascade delete behavior intentional
- [ ] Long-running migrations identified
- [ ] Downtime requirements stated
- [ ] Existing production data considered
- [ ] Migration order safe

### Common Failure Patterns
- Adding NOT NULL before backfill
- Renaming columns without compatibility layer
- Recreating tables instead of ALTER TABLE
- Silent data truncation
- Missing transaction boundaries
- Non-idempotent migrations

---

## 2. API Contract Validation

### Required Checks
- [ ] Endpoint purpose clear
- [ ] Request schema documented
- [ ] Success + error responses shown
- [ ] Validation rules explicit
- [ ] Pagination/filtering documented
- [ ] Versioning/backward compatibility addressed
- [ ] Auth/permission requirements defined
- [ ] Rate limits mentioned if relevant

### Contract Consistency
- [ ] API field names match DB/domain terminology
- [ ] Types consistent across requests/responses
- [ ] Enum values documented
- [ ] Nullability consistent
- [ ] Error format standardized

### Breaking Change Detection
- [ ] Removed fields identified
- [ ] Changed response shapes identified
- [ ] Old clients still supported
- [ ] Deprecation strategy documented

---

## 3. Frontend / Backend Alignment

### Data Flow Validation
- [ ] Frontend state maps to API responses
- [ ] Form fields map to backend schema
- [ ] Error states handled
- [ ] Loading/retry behavior defined
- [ ] Empty states defined
- [ ] Streaming behavior documented if used

### Mismatch Detection
- [ ] Frontend expects fields backend does not return
- [ ] Backend requires fields UI does not provide
- [ ] Inconsistent naming between layers
- [ ] Incompatible enum values
- [ ] Pagination assumptions mismatch

---

## 4. Architecture Review

### Structure Validation
- [ ] Layer responsibilities clear
- [ ] Dependency direction consistent
- [ ] Shared utilities identified
- [ ] Module boundaries clear
- [ ] Extensibility path reasonable

### Architecture Risk Checks
- [ ] No circular dependencies
- [ ] No business logic duplicated across layers
- [ ] Background jobs ownership defined
- [ ] Cache invalidation strategy defined
- [ ] Event flow understandable

---

## 5. Concurrency & State Risks

### Required Checks
- [ ] Simultaneous edits considered
- [ ] Race conditions addressed
- [ ] Retry/idempotency behavior defined
- [ ] Locking/versioning strategy defined
- [ ] Async state transitions valid

### Common Failure Patterns
- Double processing jobs
- Stale frontend state overwriting updates
- Missing optimistic locking
- Duplicate webhook handling
- Multi-tab update conflicts

---

## 6. Performance & Scalability

### Required Checks
- [ ] Expected scale stated
- [ ] Query/index strategy defined
- [ ] N+1 risks reviewed
- [ ] Heavy operations identified
- [ ] Background processing used appropriately
- [ ] File/upload limits documented

### Production Reality Checks
- [ ] Works with realistic dataset sizes
- [ ] Migration runtime acceptable
- [ ] API response size controlled
- [ ] Expensive joins/index scans considered

---

## 7. Security & Permissions

### Required Checks
- [ ] Tenant/account scoping enforced
- [ ] Delete permissions defined
- [ ] Auth middleware behavior clear
- [ ] Sensitive data exposure reviewed
- [ ] Internal vs public errors separated

### Multi-Tenant Checks
- [ ] Queries scoped by account/repository/project
- [ ] No cross-tenant joins/leaks
- [ ] Access control enforced server-side

---

# Cross-Section Consistency Review

## Mandatory Consistency Checks

- [ ] API fields match schema
- [ ] UI examples match API responses
- [ ] Migration matches final schema
- [ ] Permissions model consistent everywhere
- [ ] Naming terminology consistent
- [ ] Done criteria align with implementation
- [ ] Architecture diagrams match written behavior

---

# Implementation Reality Check

## Feasibility Validation

- [ ] Existing architecture can support design
- [ ] Complexity reasonable for scope
- [ ] Rollout can happen incrementally
- [ ] Dependencies realistic
- [ ] Operational burden understood
- [ ] Monitoring/logging considered
- [ ] Failure recovery possible

---

# Ambiguity Detection

## Flag Missing Information

Immediately flag:
- Undefined API responses
- Missing auth behavior
- Undefined ownership
- Missing retry logic
- Missing rollback strategy
- Undefined background job behavior
- Undefined cache behavior
- Missing edge case handling

Never assume the answer.

---

# Spec Quality Rules

## Good Specification Traits

- Concrete examples
- Explicit schemas
- Measurable outcomes
- Defined ownership
- Clear rollout plan
- Consistent terminology

## Bad Specification Traits

- “Handle errors appropriately”
- “Optimize later”
- “Should scale”
- “Eventually consistent”
- “Frontend will adapt”
- “Migration TBD”

---

# Severity Levels

| Severity | Meaning | Action |
|---|---|---|
| CRITICAL | Data loss, security issue, production outage risk | Block release |
| HIGH | Breaking behavior or major inconsistency | Must resolve |
| MEDIUM | Missing clarity or incomplete handling | Resolve before implementation complete |
| LOW | Improvement or maintainability issue | Optional |

---

# Required Review Output

```md
# Spec Review: [Name]

## Final Verdict
- READY
- READY WITH CHANGES
- NOT READY

## Summary
[Short assessment]

## Top Risks
1.
2.
3.

## Critical Findings

### [Title]
Severity: CRITICAL | HIGH | MEDIUM | LOW

Issue:
[What is wrong]

Impact:
[Why this matters]

Recommendation:
[Concrete fix]

Affected Sections:
[References]

---

## Missing Information
- [Missing item]
- [Missing item]

---

## Contradictions
- [Conflict]
- [Conflict]

---

## Questions Requiring Decisions
- [Question]
- Recommended direction: [Answer]

---

## Risk Scores

| Area | Risk |
|---|---|
| Architecture | LOW/MEDIUM/HIGH |
| Migration | LOW/MEDIUM/HIGH |
| Operational | LOW/MEDIUM/HIGH |
| Security | LOW/MEDIUM/HIGH |

---

## Release Readiness Checklist

- [ ] Migration safe
- [ ] APIs consistent
- [ ] Frontend/backend aligned
- [ ] Permissions defined
- [ ] Rollback documented
- [ ] Edge cases handled
- [ ] Monitoring/logging covered
- [ ] Done criteria measurable