@echo off
setlocal

SET SKILLS_REPO=https://github.com/zoharp/claude-skills
SET CLONE_DIR=%USERPROFILE%\claude-skills
SET SKILLS_DIR=%USERPROFILE%\.claude\skills

echo ================================================
echo  Claude Skills Installer
echo ================================================
echo.

:: Step 1 — Clone or update the skills repo
IF EXIST "%CLONE_DIR%\.git" (
    echo [1/3] Updating skills repo...
    cd /d "%CLONE_DIR%"
    git pull
) ELSE (
    echo [1/3] Cloning skills repo...
    git clone %SKILLS_REPO% "%CLONE_DIR%"
    cd /d "%CLONE_DIR%"
)
IF errorlevel 1 (
    echo ERROR: git failed. Make sure git is installed and you have internet access.
    pause
    exit /b 1
)

:: Step 2 — Create skills directory
echo.
echo [2/3] Creating skills directory...
IF NOT EXIST "%SKILLS_DIR%" mkdir "%SKILLS_DIR%"

:: Step 3 — Copy all skills
echo.
echo [3/3] Installing skills...
FOR /D %%s IN ("%CLONE_DIR%\skills\*") DO (
    IF EXIST "%%s\SKILL.md" (
        IF NOT EXIST "%SKILLS_DIR%\%%~ns" mkdir "%SKILLS_DIR%\%%~ns"
        xcopy /E /Y /Q "%%s\*" "%SKILLS_DIR%\%%~ns\"
        echo    Installed: %%~ns
    )
)

echo.
echo ================================================
echo  Done! Skills installed to: %SKILLS_DIR%
echo.
echo  Next steps:
echo    1. Open your project folder in VS Code
echo    2. Open terminal and type: claude
echo    3. Say: use the new-project skill
echo ================================================
pause
