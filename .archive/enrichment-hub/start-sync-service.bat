@echo off
REM Start Auto-Sync Background Service
REM This will run the sync service in the background

echo Starting Auto-Sync Background Service...
echo Check logs/sync-service.log for output
echo.

REM Start PowerShell script in hidden window
start /B powershell -WindowStyle Hidden -ExecutionPolicy Bypass -File "%~dp0start-sync-service.ps1"

echo Service started! Check logs/sync-service.log for status.
echo To stop the service, run: stop-sync-service.bat
pause
