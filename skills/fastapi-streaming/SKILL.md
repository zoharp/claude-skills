---
name: fastapi-streaming
description: Use when working on FastAPI streaming endpoints, NDJSON event streams, or React fetch-based streaming consumers. Covers the Orcanos streaming pattern with step events and result events.
---

# FastAPI Streaming (NDJSON)

## Pattern Overview
Backend streams NDJSON line-by-line. Frontend reads with `fetch()` + `response.body.getReader()`.

---

## Backend (FastAPI)

### StreamingResponse with NDJSON
```python
from fastapi.responses import StreamingResponse
import json

async def event_generator():
    yield json.dumps({"type": "step", "step": {"text": "Routing...", "duration_ms": 120}}) + "\n"
    yield json.dumps({"type": "step", "step": {"text": "Searching...", "duration_ms": 210}}) + "\n"
    yield json.dumps({"type": "result", "data": {...}}) + "\n"

@app.post("/query")
async def query(request: QueryRequest):
    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
```

### Event types
```json
{"type": "step", "step": {"text": "Routing query...", "duration_ms": 120, "detail": "specific_doc, conf=0.82"}}
{"type": "step", "step": {"text": "Embedding...", "duration_ms": 45, "detail": "8 tokens"}}
{"type": "step", "step": {"text": "Searching...", "duration_ms": 210, "detail": "5 chunks"}}
{"type": "step", "step": {"text": "Generating...", "duration_ms": 890, "detail": "312 tokens"}}
{"type": "result", "data": {"answer": "...", "sources": [], "usage": {}}}
```

---

## Frontend (React)

### fetch() with ReadableStream
```javascript
const response = await fetch(`${API_URL}/query`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
  body: JSON.stringify({ question, conversation_history, repository_id })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const lines = decoder.decode(value).split('\n').filter(Boolean);
  for (const line of lines) {
    const event = JSON.parse(line);
    if (event.type === 'step') {
      // Update ThinkingPanel
    } else if (event.type === 'result') {
      // Render answer + sources
    }
  }
}
```

---

## Auth on all endpoints
```python
from backend.auth import verify_token

@app.get("/protected")
async def protected(user=Depends(verify_token)):
    return {"user": user}
```
Exception: `GET /health` — no auth required.

---

## Running locally
```bash
# Terminal 1 — Backend
python -m uvicorn backend.api:app --reload
# http://localhost:8000  |  Swagger: http://localhost:8000/docs

# Terminal 2 — Frontend
cd frontend && npm run dev
# http://localhost:5173
```

## Module testing
```bash
python -m backend.chunker       # print chunks from docs/
python -m backend.embeddings    # test OpenAI embedding
python -m backend.supabase_client  # test DB + vector search
python -m backend.etl           # full indexing pipeline
python -m backend.rag           # test Q&A
python -m backend.router        # test query routing
python -m backend.settings      # print current live settings
python -m backend.config        # validate env vars
```
