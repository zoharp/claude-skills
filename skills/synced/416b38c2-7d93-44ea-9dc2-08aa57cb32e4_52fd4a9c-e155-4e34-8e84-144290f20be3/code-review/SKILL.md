---
name: code-review
description: Comprehensive code review for any full-stack project. Covers backend (Python/Node/any), frontend (React/any), SQL/DB scripts, API contracts, error handling, security, performance, and spec alignment. Use when reviewing any code change, PR, or implementation against a spec or design document.
license: MIT
---

# Code Review Skill

## Overview

Full-stack code review framework covering:
- **Spec alignment** — does the code match the agreed design?
- **Backend** — patterns, error handling, streaming, async
- **Frontend** — component structure, state management, API calls
- **Database** — DBA standards, query efficiency, index usage, migrations
- **Security** — auth, input validation, secrets, injection attacks
- **Performance** — bottlenecks, N+1 queries, blocking calls, unbounded results
- **Error handling** — every layer must handle and propagate errors correctly
- **Code quality** — naming, structure, testability, maintainability

---

## Step 0 — Before Reviewing

1. **Read the spec** — if a spec file exists, read it first
2. **Understand the stack** — identify languages, frameworks, DB in use
3. **Read relevant docs** — architecture, patterns, schema files if available
4. **Note the scope** — what changed? what files? what layers?

---

## Review Checklist

### 1. Spec Alignment
- [ ] Every feature described in spec is implemented
- [ ] No scope creep (extra features not in spec)
- [ ] API endpoint paths match spec (method, path, params)
- [ ] Request/response shapes match spec (field names, types)
- [ ] DB schema matches spec (table names, columns, types, constraints)
- [ ] Error responses match spec (HTTP codes, message format)
- [ ] Permission checks implemented as specified
- [ ] All done criteria from spec satisfied

### 2. Backend (Any Language)

#### Structure & Patterns
- [ ] New code follows existing project patterns and conventions
- [ ] Business logic separated from routing/controllers
- [ ] No hardcoded values — use config/env vars
- [ ] Function names descriptive and consistent with codebase
- [ ] No unused imports, variables, or dead code
- [ ] Type hints / signatures on all functions
- [ ] No functions over ~50 lines — split if longer

#### Error Handling — MANDATORY on every endpoint and service function
- [ ] Every route/controller has try/catch or equivalent
- [ ] Specific exceptions caught before generic ones
- [ ] HTTP status codes correct (400, 401, 403, 404, 409, 500)
- [ ] Error messages are user-friendly (no raw stack traces to client)
- [ ] Errors logged before raising/returning
- [ ] Streaming endpoints handle mid-stream errors gracefully

#### Security
- [ ] No secrets in source code — always from env vars
- [ ] All user input validated before use
- [ ] Parameterized queries only — no string interpolation in SQL
- [ ] File uploads: validate type + size before processing
- [ ] Auth token validated on every protected endpoint
- [ ] Permission checks happen BEFORE data access, not after
- [ ] No sensitive data in logs

#### Performance
- [ ] No N+1 DB queries (loop calling DB per item)
- [ ] Batch inserts for multiple rows
- [ ] No blocking calls inside async functions
- [ ] Large datasets paginated — always use LIMIT
- [ ] Expensive operations run async or streamed — never block a request
- [ ] External API calls have timeouts set

#### Async / Streaming
- [ ] Async functions don't block
- [ ] Streaming responses send incremental progress events
- [ ] Stream always sends a final complete/error event before closing
- [ ] Generator functions use yield, not return

### 3. Frontend (Any Framework)

#### Structure & Patterns
- [ ] New components follow existing naming convention
- [ ] Props clearly defined and destructured
- [ ] No inline styles — use existing CSS classes/variables
- [ ] Components focused (one responsibility)
- [ ] No hardcoded colors, sizes, or strings

#### State Management
- [ ] Loading states handled
- [ ] Error states handled and shown to user
- [ ] No state mutations — always use setters
- [ ] No storing derived data in state unnecessarily

#### API Calls + Error Handling — MANDATORY
- [ ] All API calls wrapped in try/catch
- [ ] Loading state set before fetch, cleared in finally
- [ ] Error state shown to user (not just console.log)
- [ ] Auth headers included on every protected call
- [ ] Streaming responses parsed incrementally
- [ ] 403, 409, network errors all handled with user-visible messages

#### UI Completeness
- [ ] Empty state shown when list is empty
- [ ] Loading indicator shown during fetch
- [ ] Disabled states on buttons when action unavailable
- [ ] Destructive actions have confirmation dialog

#### Performance
- [ ] No redundant API calls on every render
- [ ] List items use stable keys (key={item.id}, not key={index})
- [ ] Streaming updates don't cause excessive re-renders

### 4. Database / SQL — DBA Standards

#### Schema
- [ ] Table names snake_case, plural
- [ ] All tables have a primary key
- [ ] All tables have created_at timestamp
- [ ] Foreign keys defined explicitly with ON DELETE behavior documented
- [ ] NOT NULL on required fields, defaults on optional fields
- [ ] Enum/text fields have documented valid values

#### Indexes
- [ ] Every FK column has an index
- [ ] Composite indexes for common query patterns
- [ ] Correct index type for column type (B-tree, GIN, GiST, etc.)
- [ ] Partial indexes used where appropriate

#### Query Quality
- [ ] No SELECT * — always select specific columns
- [ ] LIMIT on all queries that could return large results
- [ ] Joins use indexed columns
- [ ] No subqueries that could be JOINs
- [ ] No full table scans (mentally apply EXPLAIN ANALYZE)

#### Migrations
- [ ] Uses ADD COLUMN IF NOT EXISTS (not DROP + CREATE)
- [ ] Backfill SQL provided for existing rows
- [ ] Migration is idempotent (safe to run twice)
- [ ] Old columns dropped only after code no longer references them

### 5. Code Quality & Maintainability
- [ ] No magic numbers — use named constants
- [ ] No duplicated logic — extract to shared utility
- [ ] Variable names self-documenting
- [ ] No commented-out code in final PR
- [ ] No print/console.log left in production code
- [ ] Tests added or updated for changed behavior

---

## Review Output Format

```
# Code Review: [Feature / PR Name]
Spec: [spec file, or "no spec"]
Files reviewed: [list]
Stack: [e.g. Python/FastAPI, React, PostgreSQL]

## Summary
[1 paragraph: overall quality, critical issues, recommendation]

## What's Good
- [Point]

## Critical Issues (must fix before merge)
[File: function/line]
- Issue: [description]
- Impact: [what breaks]
- Fix: [recommendation]

## Important Issues (should fix)
[File: function/line]
- Issue: [description]
- Fix: [recommendation]

## Suggestions (nice to have)
- [Minor improvement]

## Checklist
- Spec alignment: pass / fail / n/a
- Error handling backend: pass / fail
- Error handling frontend: pass / fail / n/a
- Security: pass / fail
- Performance: pass / fail
- DB standards: pass / fail / n/a
- Code quality: pass / fail

## Verdict
[ ] Approved
[ ] Approved with suggestions
[ ] Changes required
```

---

## Severity Levels

| Level | Meaning | Action |
|-------|---------|--------|
| Critical | Security hole, data loss, crash, auth bypass | Block merge. Must fix. |
| Important | Missing error handling, performance issue, spec deviation | Fix before merge |
| Suggestion | Style, naming, minor optimization | Nice to have |
