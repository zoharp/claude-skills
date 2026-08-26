@echo off
cd /d "%~dp0"

:: Prompt for commit message
set "MSG="
set /p MSG="Commit message: "
if not defined MSG (
    echo No message provided, aborting.
    goto :fail
)

echo.
echo === Staging changes ===
git add -A
if errorlevel 1 (
    echo git add failed - is this folder a git repository?
    goto :fail
)
git status --short

:: git commit exits 1 when nothing is staged - catch that with a clear message
git diff --cached --quiet
if not errorlevel 1 (
    echo Nothing to commit - working tree is already clean.
    goto :fail
)

echo.
echo === Committing ===
git commit -m "%MSG%"
if errorlevel 1 (
    echo Commit failed - see the git error above.
    goto :fail
)

echo.
echo === Pushing to GitHub ===
git push
if errorlevel 1 (
    echo Plain push failed, retrying with upstream set...
    git push -u origin HEAD
    if errorlevel 1 (
        echo Push failed - see the git error above.
        goto :fail
    )
)

echo.
echo === Done! Deployed successfully. ===
pause
exit /b 0

:fail
echo.
echo === DEPLOY FAILED ===
pause
exit /b 1
