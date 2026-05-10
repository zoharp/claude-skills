---
name: new-project
description: Use at the start of any new project to collect project details and generate a CLAUDE.md. Invoke when asked to set up a new project, initialize a repo, or create a CLAUDE.md from scratch.
---

# New Project Setup

When starting a new project, collect the following information from the user, then generate a `CLAUDE.md` tailored to the project.

---

## Step 1 — Collect project details

Ask the user for:

### Required
- **Project name** — short slug (e.g. `orcanos-qms`, `gap-scanner`)
- **Project description** — one sentence: what does it do?
- **Git repo URL** — e.g. `https://github.com/zoharp/my-project`

### Project type (pick all that apply)
- `RAG` — retrieval-augmented generation / document Q&A
- `API` — backend API / microservice
- `SaaS` — multi-tenant web application
- `CLI` — command line tool
- `Chrome Extension` — browser extension
- `Data Pipeline` — ETL / data processing
- `Other` — describe

### Tech stack
- **Backend** — e.g. FastAPI, Node/Express, .NET, none
- **Frontend** — e.g. React/Vite, Next.js, none
- **Database** — e.g. Supabase/pgvector, SQL Server, none
- **AI/LLM** — e.g. OpenAI GPT-4o, Anthropic Claude, none

### Deployment (pick all that apply)
- `deploy.bat` / `deploy.sh` — git push triggers Cloud Build automatically
- `Vercel` — frontend auto-deploys on push to main
- `GCP Cloud Run` — backend via Cloud Build pipeline
- `AWS` — Lambda / EC2 / other
- `Manual` — no automation yet / local only

### Optional
- **Related standards/compliance** — e.g. ISO 13485, FDA 21 CFR, none
- **Skills to reference** — which global skills apply? (pick all that apply)
  - `release-management` — if project has versioned components
  - `orcanos-rag-architecture` — if project is RAG-based
  - `supabase-patterns` — if using Supabase
  - `gcp-deployment` — if deploying to GCP
  - `fastapi-streaming` — if using FastAPI with streaming
  - `deploy` — always include if using deploy.bat / deploy.sh

---

## Step 2 — Generate CLAUDE.md

Use the collected info to produce a `CLAUDE.md` with this structure:

```markdown
# <Project Name> — Claude Code Instructions

## Project type
<e.g. SaaS + RAG>

## Skills in use
- **`deploy`** — git commit, push, deployment checklist
- **`release-management`** — version bumping and release notes  <- only if versioning needed
- **`<other-skills>`** — <description>

---

## Release Management  <- only if project has versioned components
Use the `release-management` skill after every code change.

### Current versions
- Backend: 1.0.0
- Frontend: 1.0.0

---

## Project
<One sentence description>

**Git repo:** <URL>

## Tech Stack
- **Backend:** <value>
- **Frontend:** <value>
- **Database:** <value>
- **AI/LLM:** <value>

## Deployment
- **Frontend:** <e.g. Vercel — auto-deploys on push to main>
- **Backend:** <e.g. GCP Cloud Run — via Cloud Build>
- **Deploy:** run deploy.bat (Windows) or ./deploy.sh (Mac/Linux)

---

## Project Structure
<project-name>/
├── CLAUDE.md
├── .env                <- secrets (never commit)
├── .env.example
└── ...                 <- add structure as project grows

---

## Environment Variables (.env)
# Add required env vars here as they are defined

---

## How to Run
# Add run instructions as the project is set up
```

---

## Step 3 — Create supporting files

After generating CLAUDE.md, also offer to create:
- `.env.example` — template with all required env var keys (empty values)
- `deploy.bat` — Windows deploy script
- `deploy.sh` — Mac/Linux deploy script
- `.gitignore` — with .env, node_modules, __pycache__, etc.
- `README.md` — basic project readme

---

## deploy.bat template
```bat
@echo off
cd /d "%~dp0"

set /p MSG="Commit message: "
if "%MSG%"=="" (
    echo No message provided, aborting.
    exit /b 1
)

echo === Staging changes ===
git add -A
git status --short

echo === Committing ===
git commit -m "%MSG%"
if errorlevel 1 (
    echo Commit failed.
    exit /b 1
)

echo === Pushing to GitHub ===
git push
if errorlevel 1 (
    echo Push failed.
    exit /b 1
)

echo === Done! Deployed successfully. ===
pause
```

## deploy.sh template (Mac/Linux)
```bash
#!/bin/bash
cd "$(dirname "$0")"

read -p "Commit message: " MSG
if [ -z "$MSG" ]; then
  echo "No message provided, aborting."
  exit 1
fi

echo "=== Staging changes ==="
git add -A
git status --short

echo "=== Committing ==="
git commit -m "$MSG"
if [ $? -ne 0 ]; then
  echo "Commit failed."
  exit 1
fi

echo "=== Pushing to GitHub ==="
git push
if [ $? -ne 0 ]; then
  echo "Push failed."
  exit 1
fi

echo "=== Done! Deployed successfully. ==="
```

## .gitignore template
```
.env
*.env
__pycache__/
*.pyc
node_modules/
.DS_Store
Thumbs.db
dist/
.vite/
```
