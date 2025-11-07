@echo off
REM ====================================================================
REM GRAFANA PASSWORD RESET SCRIPT (Windows Batch)
REM ====================================================================
REM Purpose: Reset Grafana admin password to 'changeme'
REM Usage: Double-click this file or run from command prompt
REM ====================================================================

echo ================================================================
echo   GRAFANA PASSWORD RESET UTILITY
echo ================================================================
echo.
echo This script will reset your Grafana admin password to: changeme
echo.
echo Container: barton-outreach-grafana
echo Username: admin
echo New Password: changeme
echo.
pause

echo.
echo [1/3] Checking if Docker is running...
docker ps >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Docker is not running or not installed
    echo.
    echo Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)
echo OK: Docker is running

echo.
echo [2/3] Checking if Grafana container exists...
docker ps -a --filter "name=barton-outreach-grafana" --format "{{.Names}}" | findstr "barton-outreach-grafana" >nul
if errorlevel 1 (
    echo.
    echo ERROR: Grafana container 'barton-outreach-grafana' not found
    echo.
    echo Please start Grafana first with: docker compose up -d
    echo.
    pause
    exit /b 1
)
echo OK: Container found

echo.
echo [3/3] Resetting admin password...
docker exec -it barton-outreach-grafana grafana-cli admin reset-admin-password changeme

if errorlevel 1 (
    echo.
    echo ERROR: Password reset failed
    echo.
    echo Try these alternatives:
    echo 1. Restart Grafana: docker compose restart grafana
    echo 2. Recreate container: docker compose down ^&^& docker compose up -d
    echo 3. See GRAFANA_LOGIN_TROUBLESHOOTING.md for more options
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   SUCCESS! Password reset complete
echo ================================================================
echo.
echo You can now login to Grafana with:
echo.
echo   URL: http://localhost:3000
echo   Username: admin
echo   Password: changeme
echo.
echo Grafana will prompt you to change the password after login.
echo.
echo ================================================================
pause
