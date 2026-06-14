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
    yield json.dumps({"type": "step", "step": {"key": "routing",  "text": "Routing...",  "duration_ms": 120}}) + "\n"
    yield json.dumps({"type": "step", "step": {"key": "search",   "text": "Searching...", "duration_ms": 210}}) + "\n"
    yield json.dumps({"type": "result", "data": {...}}) + "\n"

@app.post("/query")
async def query(request: QueryRequest):
    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
```

### Event types — query pipeline
Step events carry a stable `key` field used by the frontend for timing lookup. Never match on `text` (fragile).

```json
{"type": "step",   "step": {"key": "routing",   "text": "Routing query...",  "duration_ms": 145, "detail": "specific_doc, conf=0.82"}}
{"type": "step",   "step": {"key": "embedding",  "text": "Embedding...",      "duration_ms": 23,  "detail": "12 tokens"}}
{"type": "step",   "step": {"key": "search",     "text": "Searching...",      "duration_ms": 67,  "detail": "8 chunks"}}
{"type": "step",   "step": {"key": "generating", "text": "Generating...",     "duration_ms": 890, "detail": "890ms"}}
{"type": "result", "data": {"answer": "...", "sources": [], "query_type": "specific_doc", "usage": {}, ...}}
{"type": "error",  "message": "Something went wrong"}
```

---

## Frontend (React)

### fetch() with ReadableStream — query consumer (App.jsx)
```javascript
let _stepTimings = [];   // local array — survives after loading ends, fed into lastQueryInfo
setThinkingSteps([]);    // React state — drives ThinkingPanel during loading only

const reader = response.body.getReader();
const decoder = new TextDecoder();
let buffer = '';
let resultData = null;

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  buffer += decoder.decode(value, { stream: true });
  const lines = buffer.split('\n');
  buffer = lines.pop();
  for (const line of lines) {
    if (!line.trim()) continue;
    let event;
    try { event = JSON.parse(line); } catch { continue; }
    if (event.type === 'step') {
      const s = { ...event.step, status: 'complete' };
      _stepTimings.push(s);                          // captured for debug panel
      setThinkingSteps(prev => [...prev, s]);        // shown in ThinkingPanel
    } else if (event.type === 'result') {
      resultData = event.data;
    } else if (event.type === 'error') {
      throw new Error(event.message);
    }
  }
}

// After stream ends — save timing alongside result data
setLastQueryInfo({
  ...resultData fields...,
  step_timings: _stepTimings,   // keyed by step.key for findTiming() in DebugPanel
});
```

**Why two collections?** `thinkingSteps` drives the live ThinkingPanel and is reset on each new query. `_stepTimings` is a local variable captured at the end of streaming and persisted in `lastQueryInfo` so the debug panel can show timings after loading completes.

### Buffer pattern — handles chunks split across read() calls
```javascript
buffer += decoder.decode(value, { stream: true });
const lines = buffer.split('\n');
buffer = lines.pop();   // keep incomplete last line for next iteration
for (const line of lines) { /* process complete lines */ }
```
Always use `{ stream: true }` on `decode()` and buffer across reads. Never assume one `read()` = one complete line.

---

## Upload streaming (zip_processor.py pattern)

Different event schema used for ZIP and direct-file upload endpoints:

```python
def generate():
    for event in process_zip_upload(repo_id, file_bytes, user_id):
        yield json.dumps(event) + "\n"
return StreamingResponse(generate(), media_type="application/x-ndjson")
```

### Upload event types
```json
{"type": "start",    "total_files": 5}
{"type": "progress", "current": 2, "file_name": "doc.pdf", "status": "uploaded"}
{"type": "result",   "upload_id": "uuid", "summary": {"uploaded":3,"updated":1,"skipped":1,"failed":0}, "errors": [], "halted": false}
{"type": "fatal",    "error": "Invalid ZIP file: ..."}
```
`status` values: `uploaded` | `updated` | `skipped` | `failed`

### React consumer (UploadZipModal.jsx)
```javascript
const reader = response.body.getReader();
const decoder = new TextDecoder();
let buffer = '';
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  buffer += decoder.decode(value, { stream: true });
  const lines = buffer.split('\n');
  buffer = lines.pop();
  for (const line of lines) {
    if (!line.trim()) continue;
    const event = JSON.parse(line);
    if (event.type === 'start') setTotalFiles(event.total_files);
    else if (event.type === 'progress') setProgress(prev => [...prev, event]);
    else if (event.type === 'result') { setSummary(event.summary); setErrors(event.errors || []); }
    else if (event.type === 'fatal') setFatalError(event.error);
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
python -m backend.chunker
python -m backend.embeddings
python -m backend.supabase_client
python -m backend.etl
python -m backend.rag
python -m backend.router
python -m backend.settings
python -m backend.config
```
