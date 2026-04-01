---
name: orcanos-rag-architecture
description: Use when working on the Orcanos RAG pipeline, query router, chunking, retrieval, or ETL indexing. Provides architectural context for the 2-stage router, hybrid search, streaming pipeline, and Google Drive indexing.
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
| `coverage_analysis` | ISO clause coverage gap analysis |
| `unknown` | Gibberish / nonsensical query |

### Stage 1 — fast pre-checks (no LLM)
- `_is_obvious_meta()` — regex for "list all documents" with no qualifiers
- `_detect_filtered_meta()` — regex for "list all <doc_type>" with no topic
- `_is_coverage_analysis()` — detect coverage/gap analysis requests
- `_is_search_only()` — detect "which documents mention X"

### Stage 2 — vector search on document names
Embeds the query → calls `search_documents_by_name()` (Supabase RPC, scoped to repository) → returns top 5 candidate documents.

### Stage 3 — single LLM call (classify + pick doc)
One GPT-4o call with candidate documents + classification rules.
Returns JSON: `{query_type, doc_name (EXACT from list or null), search_text, chapter_filter, confidence}`

### Flow
```
User query
  → _is_obvious_meta()? → return {meta}
  → embed query → search_documents_by_name(repo_id) → top 5 candidates
  → LLM(system=candidates + rules, user=query)
  → {query_type, doc_name, search_text, confidence}
  → rag.py uses doc_name + repo_id as filters for chunk search
```

---

## RAG Pipeline (`rag.py`)

`rag_answer_stream()` — yields NDJSON events:

```json
{"type": "step", "step": {"text": "Routing query...", "duration_ms": 120, "detail": "specific_doc, conf=0.82"}}
{"type": "step", "step": {"text": "Embedding...", "duration_ms": 45, "detail": "8 tokens"}}
{"type": "step", "step": {"text": "Searching...", "duration_ms": 210, "detail": "5 chunks"}}
{"type": "step", "step": {"text": "Generating...", "duration_ms": 890, "detail": "312 tokens"}}
{"type": "result", "data": {}}
```

### Pipeline steps
1. Load live settings from `rag_settings`
2. Route query → `route_query(question, repository_id)`
3. Handle `meta` / `coverage_analysis` queries inline
4. `expand_query()` — synonym expansion
5. Adjust `top_k` based on router confidence
6. Embed search_text → `get_embedding_with_usage()`
7. Search → `search_chunks_hybrid()` or `search_chunks()` (scoped to repo)
8. Filter by similarity threshold, sort descending
9. Handle `search_only` (return chunks, skip generation)
10. `limit_context()` — cap at 12,000 chars
11. Build GPT-4o messages: system prompt + conversation history + context + question
12. Generate answer → stream step event → yield result

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

### Google Drive indexing fails
- Ensure user granted Google Drive OAuth scope
- Check folder URL is accessible
- 3 consecutive errors halt indexing — check progress log for first error
