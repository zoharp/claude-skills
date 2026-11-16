---
name: jira-api
description: Jira Cloud REST API quirks as used by the Orcanos Integrations connector (traceability-matrix `jira_client.py`) — createmeta required-with-default fields, ADF image names via REST v2, and where the rest is documented. Use when writing or debugging code that calls a Jira Cloud site.
---

# Jira Cloud REST API — what the Orcanos connector learned

The full connector design lives in the traceability-matrix repo: `design/docs/INTEGRATIONS.md` (as built) and trap
notes #102, #105, #107, #111 in `design/docs/notes/INTEGRATIONS.md`. This skill keeps the API facts verified live.

## Create metadata — a "required" field with a default is NOT mandatory (live, ZST, 2026-11-15)

`GET /rest/api/3/issue/createmeta/{projectKey}/issuetypes/{issueTypeId}` returns each field with `required` and
`hasDefaultValue`. A field with `required: true` **and** `hasDefaultValue: true` (e.g. *Assignee* on a Bug with a
default assignee) is filled by Jira itself when it is left out of the create body — checked by creating ZST-265
without an Assignee.

- Treat it as optional: `required = required and not hasDefaultValue` (`jira_client.fields_meta`, key `has_default`).
- Before this, the connector refused every create with "needs Assignee".

## Images in rich text — the file name only comes from REST v2 (live, ZST-270, 2026-11-15)

- REST v3 returns `description` (and other rich fields) as **ADF**. An image is a `media` node whose attrs are only
  `id, type, collection, width, height` — the `alt` that used to carry the file name is **no longer sent**.
- REST v2 returns the same field as **wiki markup**, where each image is `!filename!` or `!filename|width=…!`, in the
  same order as the ADF media nodes.
- Call: `GET /rest/api/2/issue/{issueId}?fields=<field ids>` (the field ids that hold ADF with media).
- Pair names to media nodes **by position per field**; when the counts differ, skip that field — never guess.
- Then match the name to the issue's `attachment[]` to download the file.
- In code: `JiraClient.media_names(issue)` → `{media id: filename}`, used by `integrations_media.pull_images`.

## Permissions

Reading an issue through v2 needs the same *Browse projects* permission as v3; no extra scope with a 3LO app
(`read:jira-work`).

## See also

- `orcanos-api/qw-add-defect.md`, `orcanos-api/qw-update-defect.md` — the Orcanos side of a Jira ⇄ Defect pair
- `azure-devops-api` — the third connector on the same engine
