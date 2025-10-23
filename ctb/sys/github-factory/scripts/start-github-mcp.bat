# ─────────────────────────────────────────────
# 📁 CTB Classification Metadata
# ─────────────────────────────────────────────
# CTB Branch: sys/github-factory
# Barton ID: 04.04.06
# Unique ID: CTB-52C593CF
# Blueprint Hash:
# Last Updated: 2025-10-23
# Enforcement: None
# ─────────────────────────────────────────────

@echo off
echo ========================================
echo UI Composio MCP Server Startup
echo ========================================
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo [OK] Node.js is available
echo.

REM Install dependencies if needed
if not exist "mcp-servers\node_modules" (
    echo Installing MCP server dependencies...
    cd mcp-servers
    npm install @modelcontextprotocol/sdk @composio/core axios dotenv express cors
    cd ..
    echo.
)

REM Check environment variables
if "%COMPOSIO_API_KEY%"=="" (
    if not exist ".env" (
        echo [ERROR] No .env file found and COMPOSIO_API_KEY not set!
        echo Please create a .env file with COMPOSIO_API_KEY
        pause
        exit /b 1
    )
    echo [OK] Using .env file for configuration
) else (
    echo [OK] COMPOSIO_API_KEY found in environment
)

echo.
echo Starting UI Composio MCP Server...
echo Press Ctrl+C to stop the server
echo.
echo Features:
echo   - Outreach Process Manager UI (6-step workflow)
echo   - Data Intake Dashboard
echo   - STAMPED Validation Console
echo   - Manual Adjustment Console
echo   - Data Promotion with Audit Logging
echo   - Audit Log Viewer
echo   - Scraping Console
echo.
echo Available MCP integrations:
echo   - Neon database operations (via Composio)
echo   - Apify web scraping integration
echo   - Email validation services
echo   - GitHub repository management
echo   - Vercel deployment automation
echo.
echo Plus complete IMO doctrine compliance!
echo.

REM Start the UI MCP server
node mcp-servers/ui-composio-server.js

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] UI MCP server failed to start!
    echo.
    echo Troubleshooting:
    echo 1. Check your COMPOSIO_API_KEY is valid
    echo 2. Ensure you have set up Neon/Apify authentication with Composio
    echo 3. Run: node scripts/setup-ui-composio.js
    echo.
    pause
    exit /b 1
)

echo.
echo MCP server stopped.
pause