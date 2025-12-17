@echo off
REM ====================================================================
REM RESTART GRAFANA - APPLY NO-AUTH CHANGES
REM ====================================================================
REM Purpose: Restart Grafana to apply authentication disable
REM Usage: Double-click this file
REM ====================================================================

echo ================================================================
echo   RESTARTING GRAFANA TO DISABLE AUTHENTICATION
echo ================================================================
echo.
echo This will restart Grafana so you can access it without login
echo.
pause

echo.
echo [1/2] Stopping Grafana...
docker compose down

echo.
echo [2/2] Starting Grafana with no-auth configuration...
docker compose up -d

echo.
echo Waiting for Grafana to start (30 seconds)...
timeout /t 30 /nobreak

echo.
echo ================================================================
echo   SUCCESS! Grafana is now running without authentication
echo ================================================================
echo.
echo You can now access Grafana without login:
echo.
echo   URL: http://localhost:3000
echo.
echo Just open that URL in your browser - no credentials needed!
echo.
echo Your dashboards:
echo   Overview: http://localhost:3000/d/barton-outreach-overview
echo   All Dashboards: http://localhost:3000/dashboards
echo.
echo ================================================================
pause
