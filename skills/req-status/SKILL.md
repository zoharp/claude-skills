---
name: req-status
description: Show a compliance status dashboard for all current requirements.
---

# req-status

## When to use
Quick health check on requirements — before a push, audit, or sprint review.

## What to do

1. Read `requirements/_index.json`
2. Produce a dashboard with:
   - Total REQs, breakdown by status and safety class
   - **Needs attention**: draft status / no verification_method / no orcanos_id / no orcanos_test_id
   - Class B and C requirements with their verification status
   - REQs updated in the last 30 days
   - Overall health grade (A/B/C/D) with one-line justification

## Output format
Markdown. Keep it scannable — tables over prose.
