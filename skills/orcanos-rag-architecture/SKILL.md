---
name: orcanos-rag-architecture
description: Use when working on the Orcanos RAG pipeline, query router, chunking, retrieval, or ETL indexing. Provides architectural context for the 2-stage router, hybrid search, streaming pipeline, and Google Drive indexing.
revision: 1.0.0
---

# Orcanos RAG Architecture

## Overview
Multi-tenant compliance QMS powered by RAG:
- Manages multiple **repositories** of ISO compliance documents
- Indexes from **Google Drive** with chunking, summarization, metadata extraction, and vector embedding
- Answers questions via a 2-stage routing pipeline + hybrid search
- Identifies **coverage gaps** — ISO clauses not covered by documents
- Tracks token costs and query analytics

## Tech Stack
- **Python 3.11+**
- **OpenAI API** — `text-embedding-3-small` (embeddings) + `gpt-4o` (routing + answers)
- **Supabase** — pgvector, vector search, auth, settings, conversations
- **FastAPI** — local API server, streaming NDJSON responses
- **React + Vite** — chat UI

---

## Router Architecture (`router.py`)

2-stage pipeline that classifies every query and picks the right document.

### Query types
| Type | Meaning |
|---|---|
| `meta` | List/count documents — no RAG needed |
| `specific_doc` | Question about one specific document |
| `general` | Cross-document or general ISO question |
| `search_only` | Return raw chunks without generating an answer |
| `aggregation` | Count/list items within documents (requirements, test cases) |
| `coverage_analysis` | ISO clause coverage gap analysis |
| `theme_analysis` | "What are the main issues?" — score-ranked FTS + stratified sample → themed LLM summary |
| `unknown` | Gibberish / nonsensical query |

### Stage 1 — fast pre-checks (no LLM)
- `_is_theme_analysis()` — checked first; phrases like "what are the main", "most common issues", "common bugs" → `router_rule: "_is_theme_analysis"`
- `_is_coverage_analysis()` — detect coverage/gap analysis requests → `router_rule: "_is_coverage_analysis"`
- `_is_aggregation()` — detect item-count queries → `router_rule: "_is_aggregation"`
- `_is_obvious_meta()` — regex for "list all documents" with no qualifiers → `router_rule: "_is_obvious_meta"`
- `_detect_filtered_meta()` — regex for "list all <doc_type>" with no topic → `router_rule: "_detect_filtered_meta"`

Rule-based paths return immediately with `router_system_prompt: None`, `router_raw_output: None`, `router_candidates: []`.

### Stage 2 — vector search on document names
Embeds the query → calls `search_documents_by_name()` (Supabase RPC, scoped to repository) → returns top 5 candidate documents as `router_candidates`.

### Stage 3 — single LLM call (classify + pick doc)
One GPT-4o call with candidate documents + classification rules.
Returns JSON: `{query_type, doc_name (EXACT from list or null), search_text, chapter_filter}`

### Full return shape of `route_query()`
Every return path (rule-based and LLM) includes these debug fields:

```python
{
    "query_type":           "specific_doc",
    "doc_name":             "Doc.pdf",
    "search_text":          "password policy",
    "confidence":           0.87,             # name-similarity of top candidate; 1.0 for rule-based
    "usage":                {...},
    "router_rule":          None,             # e.g. "_is_coverage_analysis" for rule-based, None for LLM path
    "router_candidates":    [{"doc_name": "...", "similarity": 0.87}, ...],  # top-5; [] for rule-based
    "router_system_prompt": "You are a query router...",  # None for rule-based
    "router_user_message":  "what is the password policy?",
    "router_raw_output":    '{"query_type": "specific_doc", ...}',  # None for rule-based or on error
}
```

### Flow
```
User query
  → _is_theme_analysis / _is_coverage_analysis / _is_aggregation / _is_obvious_meta / _detect_filtered_meta?
      → return early with router_rule set, skip LLM
  → embed query → search_documents_by_name(repo_id) → top 5 candidates (router_candidates)
  → LLM(system=candidates + rules, user=query)
  → {query_type, doc_name, search_text, confidence, router_candidates, router_system_prompt, router_raw_output}
  → rag.py uses doc_name + repo_id as filters for chunk search
```

---

## RAG Pipeline (`rag.py`)

`rag_answer_stream()` — yields NDJSON events:

```json
{"type": "step",   "step": {"key": "routing",   "text": "Routing query...",  "duration_ms": 145, "detail": "specific_doc, conf=0.82"}}
{"type": "step",   "step": {"key": "embedding",  "text": "Embedding...",      "duration_ms": 23,  "detail": "12 tokens"}}
{"type": "step",   "step": {"key": "search",     "text": "Searching...",      "duration_ms": 67,  "detail": "8 chunks"}}
{"type": "step",   "step": {"key": "generating", "text": "Generating...",     "duration_ms": 890, "detail": "890ms"}}
{"type": "result", "data": { ... }}
```

**Step events carry a stable `key` field** (`routing`, `embedding`, `search`, `generating`). The frontend `findTiming()` matches on `s.key === key` — never rely on `text` for matching.

### `_router_debug` — must be in every result event
`rag.py` builds a shared dict after routing and spreads it into **every** `yield {"type": "result"}`:

```python
_router_debug = {
    "confidence":           confidence,
    "router_rule":          router_rule,
    "router_candidates":    router_candidates,
    "router_system_prompt": router_system_prompt,
    "router_user_message":  router_user_message,
    "router_raw_output":    router_raw_output,
}
# Every result event includes **_router_debug and "llm_engine": resolved_engine
```

**Rule:** If you add a new early-exit path that yields a `result` event, always include `**_router_debug` and `"llm_engine": resolved_engine`. Missing these causes the debug panel to show "No LLM call" incorrectly.

### Full result event shape
```json
{
  "answer": "...",
  "sources": [...],
  "query_type": "specific_doc",
  "chunks_searched": 8,
  "search_text": "password policy",
  "doc_filter": "Password_Policy.pdf",
  "llm_engine": "gpt_4o",
  "system_prompt": "...",
  "confidence": 0.87,
  "router_rule": null,
  "router_candidates": [{"doc_name": "Password_Policy.pdf", "similarity": 0.87}],
  "router_system_prompt": "You are a query router...",
  "router_user_message": "what is the password policy?",
  "router_raw_output": "{\"query_type\": \"specific_doc\", ...}",
  "usage": {
    "router_tokens": {"prompt": 450, "completion": 32},
    "embedding_tokens": 12,
    "answer_tokens": {"prompt": 2100, "completion": 380},
    "total_tokens": 2974,
    "cost_usd": 0.0234
  }
}
```

### Pipeline steps
1. Load live settings from `rag_settings`
2. Route query → `route_query()` → extract all fields → build `_router_debug`
3. Handle `unknown` / `meta` / `coverage_analysis` / `aggregation` / `search_only` (FTS) inline — yield result with `**_router_debug`
4. `expand_query()` — synonym expansion
5. Adjust `top_k` based on router confidence
6. Embed search_text → `get_embedding_with_usage()` → yield `embedding` step
7. Search → `search_chunks_hybrid()` → yield `search` step
8. Filter by similarity threshold, sort descending
9. Handle `search_only` (vector path) — yield result with `**_router_debug`
10. `limit_context()` — cap at 12,000 chars
11. Build GPT-4o messages: system prompt + conversation history + context + question
12. Generate answer → yield `generating` step → yield main result

### Dynamic top_k scaling
- Low confidence (`< 0.5`): `top_k × 2`
- High confidence + doc filter (`> 0.8`): `max(3, top_k // 2)`

---

## Chunking (`chunker.py`)
- Chunk size: ~1000 chars, overlap ~200 chars (configurable in `rag_settings`)
- Chunks by paragraph/section boundaries first, falls back to sentences
- Each chunk stores: `text`, `vector`, `doc_name`, `chunk_index`, `chunk_type` (`summary`|`section`), `metadata` (`page_number`)
- One AI summary chunk per document (`chunk_type=summary`)
- Supports chunking from local file paths OR raw bytes (for Google Drive)
- **Supported file types**: `.pdf` (PyMuPDF), `.docx` (python-docx), `.txt` / `.md` / `.csv` (read as plain text)

---

## ZIP & Direct-File Upload (`zip_processor.py`)

Two generators, both yield the same NDJSON event types (consumed by React via `UploadZipModal.jsx`):

### `process_zip_upload(repo_id, file_bytes, user_id)`
- Extracts ZIP to a temp dir, collects files matching `SUPPORTED_EXTENSIONS`
- Halts after 3 consecutive failures

### `process_files_upload(repo_id, files, user_id)`
- `files`: list of `{"name": str, "suffix": str, "content": bytes}`
- No extraction — processes files directly

### Event stream
```json
{"type": "start",    "total_files": N}
{"type": "progress", "current": N, "file_name": "x.pdf", "status": "uploaded|updated|skipped|failed"}
{"type": "result",   "upload_id": "...", "summary": {"uploaded":1,"updated":0,"skipped":0,"failed":0}, "errors": [], "halted": false}
{"type": "fatal",    "error": "Invalid ZIP file: ..."}
```

### Hash-check dedup
SHA-256 of file content vs `get_document_hash()`. Same hash → `skipped`. Changed hash → `delete_document()` then re-index → `updated`.

### Endpoints (api.py)
- `POST /repositories/{repo_id}/upload-zip` — single ZIP, max 1 GB
- `POST /repositories/{repo_id}/upload-files` — multi-file form (`files[]`), each max 200 MB

### SUPPORTED_EXTENSIONS
`{".pdf", ".docx", ".txt", ".md", ".csv"}`

---

## Metadata Extraction
Each indexed document gets LLM-extracted structured metadata:
- `doc_type`: Form, Policy, Procedure, Work Instruction, Record, Checklist, Manual, Guideline
- `doc_id`, `doc_title`, `version`, `owner`, `department`, `effective_date`, `description`
- `topics`: 2–5 key subject tags
- `iso_controls`: list of clause section IDs e.g. `["7.3.2", "8.2.1"]`

---

## Retrieval
- **Hybrid search**: vector (pgvector cosine) + full-text (tsvector) merged with RRF
- Falls back to pure vector if no `keyword_query` provided
- All searches scoped to `repository_id`
- Similarity threshold filter applied after search (default 0.20)
- Context capped at 12,000 chars before sending to GPT-4o

---

## Item Scoring ()

Pre-computes an importance score (0–100) for every -type chunk using a user-defined formula.

### Formula format


-  — internal Orcanos field name (used by SQL RPC for matching against  JSONB)
-  — user-friendly display name (e.g. Severity instead of defect_severity); shown in UI, ignored by SQL
- Weights must sum to exactly 100;  raises  if not
-  is a special computed field:  (>400 chars),  (150–400),  (<150)

### Orcanos metadata field titles
Each Orcanos item has  (internal) and  (display caption) per field.  
ETL stores  in each chunk's  JSONB so the scoring panel can show captions.  
 merges these across sampled chunks → passed to  and attached to formula rules.

### API endpoints
-  — sample 1,000 row-chunks, aggregate metadata, LLM suggests formula
-  — load saved formula + staleness status
-  — save without running (marks scores stale)
-  — save + apply via  RPC (concurrency-guarded with 409)

### Staleness detection
 — shown as warning banner in ScoringPanel (State F).

### theme_analysis path in rag.py

If scoring has never run (all scores = 0), falls back to text-length ranking and appends a tip footer.

---

## ETL Pipeline (`etl.py`)

### Local indexing
For each doc in `docs/` (skips already-indexed unless `force_reindex=True`):
1. Chunk → list of `{text, chunk_index, doc_name, metadata}`
2. Summarize first 3 chunks → create summary chunk
3. `insert_document()` → upsert into `documents`
4. Embed doc name → `update_doc_name_vector()` (used by router Stage 2)
5. Embed all chunks in batch → `insert_chunks()` → bulk insert into `doc_chunks`

### Google Drive indexing
Generator that yields progress events `{type: "start"|"progress"|"result"|"fatal"}`:
1. Fetch standard sections for the repository's assigned standard
2. List all indexable files in Drive folder (recursively)
3. Delete documents no longer in Drive
4. For each file: download → chunk → extract metadata + ISO clauses → embed + insert
5. Stops after 3 consecutive errors

---

## Cost Tracking
- GPT-4o input: $5.00/M tokens, output: $15.00/M tokens
- Embeddings: $0.02/M tokens
- Returned in `usage.cost_usd` per response
- Logged to `usage_logs` table

---

## Settings
All tunable parameters live in `rag_settings` Supabase table, read **live on every request**.
Keys: `answer_temperature`, `router_temperature`, `fuzzy_match_threshold`, `chat_model`, `embedding_model`, `top_k_chunks`, `similarity_threshold`, `chunk_size`, `chunk_overlap`, `enable_debug_logging`

---

## Common Issues

### "0 chunks searched" / "information not available"
Router returned a `doc_name` not matching any document:
- `GET /documents?repository_id=X` — see actual doc names
- `python -m backend.router` — see what the router returns
- Check `search_documents_by_name` — `name_vector` may not be populated (re-index)

### Low similarity scores
- 0.20+ passes default threshold; 0.60+ is good relevance
- If all scores low, try re-indexing or verify embedding model matches

### Debug panel shows "No LLM call" for a routed query
An early-exit result event in `rag.py` is missing `**_router_debug`. Add it and `"llm_engine": resolved_engine` to the offending `yield {"type": "result", "data": {...}}`.

### Google Drive indexing fails
- Ensure user granted Google Drive OAuth scope
- Check folder URL is accessible
- 3 consecutive errors halt indexing — check progress log for first error
