@echo off
REM Setup CTB Enforcement Git Hooks (Windows)
REM Run this once after cloning the repository to enable automatic CTB validation

echo Setting up CTB enforcement git hooks...

REM Get repository root
for /f "delims=" %%i in ('git rev-parse --show-toplevel') do set REPO_ROOT=%%i

REM Convert Unix path to Windows path
set REPO_ROOT=%REPO_ROOT:/=\%

REM Path to hooks directory
set HOOKS_DIR=%REPO_ROOT%\.githooks

REM Check if .githooks directory exists
if not exist "%HOOKS_DIR%" (
    echo ERROR: .githooks directory not found
    exit /b 1
)

REM Configure git to use .githooks directory
echo Configuring git to use .githooks directory...
git config core.hooksPath "%HOOKS_DIR%"

echo.
echo CTB enforcement hooks installed successfully!
echo.
echo What happens now:
echo   - Every commit will auto-tag new files
echo   - CTB compliance will be checked automatically
echo   - Commits will be blocked if compliance ^< 70/100
echo.
echo To bypass hook (NOT RECOMMENDED):
echo   git commit --no-verify
echo.
echo To uninstall hooks:
echo   git config --unset core.hooksPath
echo.

pause
