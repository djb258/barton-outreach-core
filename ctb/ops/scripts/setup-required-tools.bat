@echo off
REM ============================================================================
REM Setup Required Tools for Barton Outreach Core
REM ============================================================================
REM CTB Branch: ops/scripts
REM Barton ID: 07.02.00
REM Purpose: Install Obsidian, GitKraken, and GitHub CLI for CTB workflow
REM Platform: Windows 10/11
REM ============================================================================

echo.
echo ============================================================================
echo   BARTON OUTREACH CORE - REQUIRED TOOLS INSTALLER
echo ============================================================================
echo.
echo This script will install the following tools:
echo   1. Obsidian       - Documentation and knowledge management
echo   2. GitKraken      - Visual Git client for CTB navigation
echo   3. Git Extensions - Advanced Git GUI with visual diff/merge
echo   4. GitHub CLI     - Command-line GitHub Projects integration
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause >nul

echo.
echo [1/5] Checking if winget is available...
where winget >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] winget not found!
    echo Please install Windows Package Manager from:
    echo https://aka.ms/getwinget
    pause
    exit /b 1
)
echo [OK] winget is available

echo.
echo [2/5] Installing Obsidian...
winget install --id Obsidian.Obsidian --silent --accept-package-agreements --accept-source-agreements
if %ERRORLEVEL% equ 0 (
    echo [OK] Obsidian installed successfully
) else (
    echo [WARNING] Obsidian installation returned code %ERRORLEVEL%
    echo This may mean it's already installed or needs manual intervention
)

echo.
echo [3/5] Installing GitKraken...
winget install --id Axosoft.GitKraken --silent --accept-package-agreements --accept-source-agreements
if %ERRORLEVEL% equ 0 (
    echo [OK] GitKraken installed successfully
) else (
    echo [WARNING] GitKraken installation returned code %ERRORLEVEL%
    echo This may mean it's already installed or needs manual intervention
)

echo.
echo [4/5] Installing Git Extensions...
winget install --id GitExtensionsTeam.GitExtensions --silent --accept-package-agreements --accept-source-agreements
if %ERRORLEVEL% equ 0 (
    echo [OK] Git Extensions installed successfully
) else (
    echo [WARNING] Git Extensions installation returned code %ERRORLEVEL%
    echo This may mean it's already installed or needs manual intervention
)

echo.
echo [5/5] Installing GitHub CLI...
winget install --id GitHub.cli --silent --accept-package-agreements --accept-source-agreements
if %ERRORLEVEL% equ 0 (
    echo [OK] GitHub CLI installed successfully
) else (
    echo [WARNING] GitHub CLI installation returned code %ERRORLEVEL%
    echo This may mean it's already installed or needs manual intervention
)

echo.
echo ============================================================================
echo   INSTALLATION COMPLETE
echo ============================================================================
echo.
echo Next steps:
echo.
echo 1. RESTART YOUR TERMINAL to refresh PATH variables
echo.
echo 2. Verify installations:
echo    obsidian --version
echo    gitkraken --version
echo    gh --version
echo.
echo 3. Set up GitHub CLI authentication:
echo    gh auth login
echo.
echo 4. Open Obsidian vault:
echo    - Launch Obsidian
echo    - Click "Open folder as vault"
echo    - Select: ctb/docs/obsidian-vault
echo.
echo 5. Run GitHub Projects sync:
echo    bash infra/scripts/auto-sync-svg-ple-github.sh --once
echo.
echo See ctb/ops/scripts/POST_INSTALL_GUIDE.md for detailed instructions
echo.
echo ============================================================================
pause
