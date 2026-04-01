---
name: new-project
description: Use at the start of any new project to collect project details and generate a CLAUDE.md. Invoke when asked to set up a new project, initialize a repo, or create a CLAUDE.md from scratch.
---

# New Project Setup

When starting a new project, collect the following information from the user, then generate a `CLAUDE.md` tailored to the project.

---

## Templates
Ready-made starting files live in the `claude-skills` repo under `templates/`:
- `templates/CLAUDE.md` — default CLAUDE.md template
- `templates/START_HERE.md` — quick start guide template

Use these as the base. Copy them into the new project folder and fill in the placeholders.

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

Start from `templates/CLAUDE.md` and fill in all placeholders with the collected info.

---

## Step 3 — Create supporting files

Copy from `templates/` and also offer to create:
- `START_HERE.md` — from `templates/START_HERE.md`, fill in project name and links
- `deploy.bat` — copy from `claude-skills/templates/deploy.bat` (root of repo)
- `deploy.sh` — copy from `claude-skills/templates/deploy.sh`
- `.env.example` — template with all required env var keys (empty values)
- `.gitignore` — with .env, node_modules, __pycache__, etc.
- `README.md` — basic project readme

---

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
