@echo off
REM Start Enrichment API for n8n Integration (Windows)

echo Starting Enrichment API...
echo.

REM Check if .env exists
if not exist "..\..\..\..env" (
    echo ERROR: .env file not found in project root
    echo Please create .env with DATABASE_URL and API keys
    exit /b 1
)

REM Set default port
if "%ENRICHMENT_API_PORT%"=="" set ENRICHMENT_API_PORT=8001

echo Configuration loaded
echo    API Port: %ENRICHMENT_API_PORT%
echo    Database: Check .env for DATABASE_URL
echo.
echo API Documentation: http://localhost:%ENRICHMENT_API_PORT%/docs
echo Health Check: http://localhost:%ENRICHMENT_API_PORT%/health
echo.

REM Start API
python api\enrichment_api.py
