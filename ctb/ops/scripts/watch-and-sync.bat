@echo off
REM ============================================================================
REM Continuous Watch and Sync - All Tools
REM ============================================================================
REM CTB Branch: ops/scripts
REM Barton ID: 07.02.02
REM Purpose: Watch for changes and auto-sync Obsidian, GitKraken, GitHub Projects
REM Platform: Windows 10/11
REM ============================================================================

echo.
echo ============================================================================
echo   CONTINUOUS WATCH AND SYNC - ALL TOOLS
echo ============================================================================
echo.
echo This script will continuously monitor and sync:
echo   - Obsidian vault changes (every 5 minutes)
echo   - GitHub Projects updates (every 10 minutes)
echo   - Database schema changes (when detected)
echo.
echo Press Ctrl+C to stop watching
echo.
echo Starting watchers...
echo.

REM Check if we're in the repo root
if not exist "ctb\" (
    echo [ERROR] Must be run from repository root
    pause
    exit /b 1
)

REM Set watch intervals (in seconds)
set OBSIDIAN_INTERVAL=300
set GITHUB_INTERVAL=600
set SCHEMA_INTERVAL=1800

REM Initialize counters
set /a OBSIDIAN_COUNTER=0
set /a GITHUB_COUNTER=0
set /a SCHEMA_COUNTER=0

echo [INFO] Watch started at %TIME%
echo.

:WATCH_LOOP

REM Increment counters
set /a OBSIDIAN_COUNTER+=30
set /a GITHUB_COUNTER+=30
set /a SCHEMA_COUNTER+=30

REM Check Obsidian sync (every 5 minutes)
if %OBSIDIAN_COUNTER% geq %OBSIDIAN_INTERVAL% (
    echo [%TIME%] Syncing Obsidian vault...
    cd ctb\docs\obsidian-vault
    git add -A
    git diff --staged --quiet
    if %ERRORLEVEL% neq 0 (
        git commit -m "docs(obsidian): auto-sync vault %DATE% %TIME%"
        git push
        echo [OK] Obsidian changes synced
    ) else (
        echo [INFO] No Obsidian changes to sync
    )
    cd ..\..\..
    set /a OBSIDIAN_COUNTER=0
)

REM Check GitHub Projects sync (every 10 minutes)
if %GITHUB_COUNTER% geq %GITHUB_INTERVAL% (
    echo [%TIME%] Syncing GitHub Projects...
    bash infra\scripts\auto-sync-svg-ple-github.sh --once 2>nul
    if %ERRORLEVEL% equ 0 (
        echo [OK] GitHub Projects synced
    ) else (
        echo [WARNING] GitHub Projects sync failed or skipped
    )
    set /a GITHUB_COUNTER=0
)

REM Check schema changes (every 30 minutes)
if %SCHEMA_COUNTER% geq %SCHEMA_INTERVAL% (
    echo [%TIME%] Checking for schema changes...
    REM Check if migration files changed
    git diff --name-only HEAD~1 HEAD | findstr /C:"migration" >nul
    if %ERRORLEVEL% equ 0 (
        echo [INFO] Migration detected, refreshing schema...
        npm run schema:export
        git add ctb\docs\schema_map.json ctb\data\SCHEMA_REFERENCE.md
        git diff --staged --quiet
        if %ERRORLEVEL% neq 0 (
            git commit -m "chore(schema): auto-refresh after migration"
            git push
            echo [OK] Schema refreshed and pushed
        )
    ) else (
        echo [INFO] No schema changes detected
    )
    set /a SCHEMA_COUNTER=0
)

REM Wait 30 seconds before next check
timeout /t 30 /nobreak >nul

REM Loop forever
goto WATCH_LOOP
