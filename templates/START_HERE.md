# [Project Name] - Quick Start Guide

## 🚀 Running the Application

### Full Stack
```bash
run.bat          # Windows
./run.sh         # Mac/Linux
```

### Backend Only
```bash
run-backend.bat
# API: http://localhost:8000
# Swagger: http://localhost:8000/docs
```

### Frontend Only
```bash
frontend\run.bat
# App: http://localhost:3000
```

---

## 📋 Files

| File | Purpose |
|------|---------|
| `run.bat` | Start everything |
| `run-backend.bat` | Start only the backend |
| `frontend/run.bat` | Start only the frontend |
| `deploy.bat` | Commit + push to GitHub |

---

## 🛑 Stopping
Close the command windows or press **Ctrl+C**.

---

## 🔧 Troubleshooting

| Problem | Fix |
|---|---|
| Port already in use | Close all command windows and try again |
| `npm` not found | Install Node.js from nodejs.org |
| `python` not found | Install Python from python.org |
| Missing dependencies | `pip install -r requirements.txt` or `npm install` |

---

## 🔗 Links

| | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |
