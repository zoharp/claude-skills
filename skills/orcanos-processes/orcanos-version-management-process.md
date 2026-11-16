---
name: orcanos-version-management-process
description: The version / baseline management process in Orcanos ALM — opening a release version, freezing / locking the baseline, branch-on-change decisions, planning future versions (1.x maintenance beside 2.0), Move to View, Cancel Branch. Who does what and in which admin screen.
revision: 1.0.0
---

# Version Management — process

> **Source:** KB *Version (Baseline) Management* https://help.orcanos.com/knowledgebase/version-baseline-management
> (read 2026-11-15). The object model behind it: `Orcanos-infra/orcanos-version-management.md` (rules) and
> `Orcanos-infra/orcanos-database.md` (tables). **Configured vs inherent:** the version numbers, which versions are
> active, *Allow Branch on Change* and *Force Branch* are tenant / project setup; inheritance and branching are
> product behaviour.

## 1. Roles

| Role | Does |
|---|---|
| **Project admin** | opens, edits, locks, freezes, hides, deletes versions (*Admin → Project → Versions*); sets *Allow Branch on Change*; grants group access per version and *Force Branch [Work Item]* (*Admin → Project → Groups*) |
| **User** | logs in to a View (project + version), edits items; chooses Save or Branch when allowed; *Move to View*, *Cancel Branch* in the tree |
| **Orcanos support** | runs a script to insert intermediate versions when many changes already exist (use case 4) |

## 2. Lifecycle of a release version

1. **Work in version N** (e.g. 1.0). Items are created in the View or in the Pool and moved in.
2. **Release N** → **freeze** it (no more changes) and/or **lock** it (no login; later edits must branch).
3. **Open N+1** (*Admin → Project → Versions*). Nothing is copied; every item is inherited and keeps its *N* label.
4. **Change in N+1:**
   - new item → exists from N+1 on;
   - edit of an inherited item → **Branch** (N stays as released) or **Save** (changes N too — only if N is not locked
     and the user has no *Force Branch*).
5. **Mistaken branch** → *Cancel Branch* (not for DEFECT); history is kept.
6. Repeat. Parallel open versions are allowed: changes in an earlier open version flow into later ones.

## 3. Planning future versions — the KB's four use cases

| # | Situation | Steps |
|---|---|---|
| 1 | Working on **2.0** while the **1.x** maintenance releases are not yet known | Create 1.1, 1.2, 1.3 ahead → create 2.0 → disable 1.1–1.3 (only 1.0 + 2.0 visible). A change in 1.0 reaches every version; in 2.0 only 2.0. Later enable 1.1: its changes reach 1.2, 1.3 and 2.0, not 1.0. |
| 2 | Earlier releases needed, **2.0 has no items** yet | *Admin → Project → Versions*: relabel 2.0 → **1.1** → add 1.2 … 1.5 → create a new 2.0 → hide 1.2+; keep 1.0, 1.1, 2.0 active. |
| 3 | Same, but **items already exist in 2.0** | Steps 1–3 of #2 → **Move to View** the items labelled 1.1 from 1.1 to 2.0 → hide the extras; keep 1.0, 1.1, 2.0. |
| 4 | **Many changes** already in 2.0 | Ask Orcanos support to run the script that inserts 1.1, 1.2, 1.3. |

The key point all four rest on: **changes flow forward** through the version order, never backward — so the order
the versions are created in decides which release a change reaches.

## 4. Evidence / compliance

- A frozen version is the released baseline; its content can't change (Part 11 / design-control evidence).
- Branching keeps the released content and records the change in the new version; *Cancel Branch* keeps history.
- ❓ Not in the KB: baseline compare screens, signing a baseline, how traces behave across a branch.

## 5. Open questions

- ❓ Whether the API (`QW_Update_Object`) on an inherited item branches or saves, and whether it honours *Force Branch*.
- ❓ What *active / inactive* means exactly vs *hidden* vs *disabled* (the KB uses all three).
