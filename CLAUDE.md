# Orcanos QMS — Claude Code Instructions

## Skills in use
This project uses the following global skills (from `~/.claude/skills/`):
- **`release-management`** — version bumping rules and release_notes.json updates
- **`orcanos-rag-architecture`** — RAG pipeline, router, chunking, retrieval, ETL
- **`supabase-patterns`** — auth, pgvector, live settings, multi-tenant patterns
- **`gcp-deployment`** — Cloud Run, Cloud Build, Vercel, secrets handling
- **`fastapi-streaming`** — NDJSON streaming, React fetch consumer, module testing

---

## Release Management — MANDATORY
After every code change, use the `release-management` skill.

### Current versions (update after every bump)
- **Backend:** `2.6.3`
- **Frontend:** `1.7.0`

---

## Project Goal
Multi-tenant, multi-standard compliance QMS powered by RAG (Retrieval-Augmented Generation):
1. Manages multiple **repositories** of ISO compliance documents (ISO 27001, 13485, 14971)
2. Indexes documents from **Google Drive** with automatic chunking, summarization, metadata extraction, and vector embedding
3. Answers natural language questions about compliance documents via a 2-stage routing pipeline + hybrid search
4. Identifies **coverage gaps** — which ISO clauses are not covered by documents
5. Supports **multi-user** access with role-based permissions (owner/editor/viewer)
6. Tracks **token costs** and query analytics

## Tech Stack
- **Python 3.11+**
- **OpenAI API** — embeddings (`text-embedding-3-small`) + GPT-4o for routing and answers
- **Supabase** — pgvector storage, vector search, auth, settings, conversations
- **FastAPI** — local API server (streaming NDJSON responses)
- **React + Vite** — chat UI with conversation history, sources, token/cost tracking

> **Full DB schema (all tables, indexes, RPC functions):** see [`SCHEMA.md`](./SCHEMA.md)

---

## Project Structure

```
orcanos-qms/
├── CLAUDE.md               ← this file
├── SCHEMA.md               ← full Supabase SQL schema
├── .env                    ← secrets (never commit)
├── .env.example            ← template
├── requirements.txt
├── Dockerfile
├── cloudbuild.yaml
├── deploy.bat
├── docs/                   ← put PDF/DOCX files here (local indexing)
├── backend/
│   ├── config.py           ← env-based config constants
│   ├── settings.py         ← live settings from rag_settings table
│   ├── auth.py             ← JWT authentication middleware
│   ├── embeddings.py       ← OpenAI embedding wrapper
│   ├── chunker.py          ← PDF/DOCX → chunks
│   ├── gdrive.py           ← Google Drive integration
│   ├── supabase_client.py  ← all DB operations
│   ├── summarizer.py       ← AI doc summary + metadata extraction
│   ├── etl.py              ← orchestrate indexing pipeline
│   ├── router.py           ← 2-stage query routing
│   ├── rag.py              ← streaming RAG pipeline
│   └── api.py              ← FastAPI: 30+ endpoints
└── frontend/
    ├── src/
    │   ├── App.jsx                  ← main chat UI
    │   ├── Auth.jsx                 ← Supabase Google Sign-In
    │   ├── Settings.jsx             ← settings panel
    │   ├── AdminPanel.jsx           ← admin: users, analytics, settings
    │   ├── DebugPanel.jsx           ← debug info overlay
    │   ├── ThinkingPanel.jsx        ← live step-by-step pipeline status
    │   ├── ChatHistory.jsx          ← sidebar: conversations + repo switcher
    │   ├── RepositoryDetail.jsx     ← repo mgmt tabs
    │   ├── MarketplaceModal.jsx     ← browse and import skills from GitHub
    │   ├── ReleaseNotes.jsx         ← in-app release notes panel
    │   └── companyDetailsTemplate.js
    └── ...
```

---

## Environment Variables (`.env`)

```
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=...
SUPABASE_JWT_SECRET=...
AUTH_DISABLED=false
DOCS_FOLDER=./docs
EMBED_MODEL=text-embedding-3-small
CHAT_MODEL=gpt-4o
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K=5
```

> Fallback defaults only. `rag_settings` DB values take precedence at runtime.

---

## One-time Setup
1. Set `.env` with all keys above
2. Run all SQL from `SCHEMA.md` in Supabase SQL editor
3. Create a user in the `users` table
4. Add PDF/DOCX files to `docs/` OR connect a Google Drive folder via a repository
5. `POST http://localhost:8000/index` or use the Index button in the UI
