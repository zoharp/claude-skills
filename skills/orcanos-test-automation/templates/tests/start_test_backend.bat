@echo off
REM Start the test backend manually on port 8001 (AUTH_DISABLED=true).
REM Use this for debugging tests without running the full test suite.
REM Press Ctrl+C to stop.

cd /d "%~dp0.."
set AUTH_DISABLED=true

echo Starting test backend on http://127.0.0.1:8001 ...
echo Press Ctrl+C to stop.
echo.

python -m uvicorn backend.api:app --host 127.0.0.1 --port 8001 --reload
