---
name: deploy
description: Use when deploying code to GitHub, triggering Cloud Build, or pushing releases. Handles git commit, push, and deployment verification. Invoke when asked to deploy, release, push, or ship code.
---

# Deploy

## Standard deploy (deploy.bat / deploy.sh)
Run the deploy script from the project root. It will:
1. Prompt for a commit message
2. Stage all changes (`git add -A`)
3. Commit with the message
4. Push to GitHub (triggers Cloud Build automatically if configured)

**Windows:**
```bat
deploy.bat
```

**Mac/Linux:**
```bash
./deploy.sh
```

---

## deploy.bat contents (reference)
```bat
@echo off
cd /d "%~dp0"

set /p MSG="Commit message: "
if "%MSG%"=="" (
    echo No message provided, aborting.
    exit /b 1
)

git add -A
git status --short
git commit -m "%MSG%"
git push
```

---

## Before deploying — checklist
- [ ] Version bumped in all changed components (use `release-management` skill)
- [ ] `release_notes.json` updated
- [ ] `.env` is NOT staged (`git status` should not show it)
- [ ] No secrets or API keys in any changed files
- [ ] App runs locally without errors

## After deploying
- Cloud Build triggers automatically on push to `main`
- Monitor build: GCP Console → Cloud Build → History
- Verify backend: `curl https://<your-cloud-run-url>/health`
- Check frontend: Vercel dashboard or your deployment URL

---

## Manual git deploy (no script)
```bash
git add -A
git status --short
git commit -m "your message here"
git push origin main
```

## Rollback
```bash
# Revert last commit (keeps changes staged)
git revert HEAD
git push origin main
```

---

## Common issues

### Push rejected
```bash
git pull --rebase origin main
git push origin main
```

### Nothing to commit
Check `git status` — changes may already be committed or files may be gitignored.

### Cloud Build not triggering
- Verify the trigger is set to watch the `main` branch
- Check GCP Console → Cloud Build → Triggers → is it enabled?
