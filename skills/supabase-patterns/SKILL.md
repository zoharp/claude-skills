---
name: supabase-patterns
description: Use when working with Supabase auth, pgvector, RLS, settings tables, or JWT verification. Covers Orcanos-specific Supabase patterns including allowlist auth, live settings, and vector search.
---

# Supabase Patterns

## Auth (`auth.py`)
- **Google OAuth** with allowlist gate — only pre-registered emails can sign in
- JWT verified on every request in `auth.py`
- Dev mode: `AUTH_DISABLED=true` skips token verification (mock admin user)
- First login links `auth.users.id` → `public.users.auth_id`

### Auth error: "not on access list"
Create the user row in `public.users` table first — the auth hook blocks any Google login not pre-registered.

---

## Live Settings (`settings.py`)
- All tunable parameters live in `rag_settings` Supabase table
- Read **live on every request** — no restart needed
- Configurable via Settings UI (⚙️) or Admin Panel
- If changes don't take effect, confirm the DB row was actually updated: `GET /settings`

### Settings keys
`answer_temperature`, `router_temperature`, `fuzzy_match_threshold`, `chat_model`, `embedding_model`, `top_k_chunks`, `similarity_threshold`, `chunk_size`, `chunk_overlap`, `enable_debug_logging`

---

## pgvector / Vector Search
- Extension: `pgvector` with cosine similarity
- Embedding model: `text-embedding-3-small` → 1536 dimensions
- Hybrid search: vector (cosine) + full-text (tsvector) merged with RRF
- All searches scoped to `repository_id` (multi-tenant isolation)
- Key RPC: `search_documents_by_name()` — used by router Stage 2
- Key RPC: `search_chunks_hybrid()` — used by RAG pipeline

---

## Multi-tenant Isolation
- Every query, document, chunk, and conversation is scoped to `repository_id`
- Users can belong to multiple repositories with different permissions (`owner`/`editor`/`viewer`)
- Repository members managed via `repository_members` table

---

## Supabase Client (`supabase_client.py`)
All DB operations centralized here:
- `insert_document()` — upsert into `documents`
- `insert_chunks()` — bulk insert into `doc_chunks`
- `update_doc_name_vector()` — update name embedding for router
- `search_chunks_hybrid()` — hybrid vector + FTS search
- `search_documents_by_name()` — router name search RPC

---

## Environment Variables
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=...
SUPABASE_JWT_SECRET=...   # for local JWT verification
```

> Never commit these. Use substitution variables in Cloud Build trigger for production.
