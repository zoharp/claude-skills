---
name: gcp-deployment
description: Use when deploying to Google Cloud Run, configuring Cloud Build pipelines, managing Vercel frontend deployments, or handling GCP secrets and substitution variables. Invoke when working on Dockerfile, cloudbuild.yaml, or deploy scripts.
---

# GCP Deployment

## Stack
- **Frontend** → Vercel (connect GitHub repo, set root dir to `frontend`)
- **Backend** → Google Cloud Run (auto-deploys via Cloud Build on push to `main`)

## Key Files
| File | Purpose |
|---|---|
| `Dockerfile` | Builds the FastAPI backend |
| `.dockerignore` | Excludes frontend/docs/secrets |
| `cloudbuild.yaml` | Cloud Build pipeline: build → push → deploy to Cloud Run |
| `frontend/vercel.json` | SPA routing for React |
| `deploy.bat` | Local deploy script: enter commit message → push → triggers Cloud Build |

## Deploy
```bash
# Just run:
deploy.bat
# Prompts for commit message → git push → Cloud Build triggers automatically
```

---

## Secrets — CRITICAL RULE

**Never use `availableSecrets/secretManager` in `cloudbuild.yaml`** — causes PermissionDenied errors.

### Correct approach: Substitution variables in Cloud Build trigger
1. GCP Console → Cloud Build → Triggers → Edit trigger
2. Scroll to **Substitution variables**
3. Add variables with actual values:
   - `_OPENAI_API_KEY`
   - `_SUPABASE_URL`
   - `_SUPABASE_SERVICE_KEY`
   - `_SUPABASE_JWT_SECRET`
4. Reference in `cloudbuild.yaml` as `${_OPENAI_API_KEY}` etc.

### Example cloudbuild.yaml pattern
```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/api', '.']
    env:
      - 'OPENAI_API_KEY=${_OPENAI_API_KEY}'
      - 'SUPABASE_URL=${_SUPABASE_URL}'
```

---

## Future: Swap to AWS Bedrock
Only change `embeddings.py`:
- Replace OpenAI client with boto3 `bedrock-runtime`
- Model: `amazon.titan-embed-text-v2:0`
- Same 1536 dimensions — no schema changes needed
