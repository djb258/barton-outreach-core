@echo off
REM Stop Auto-Sync Background Service

echo Stopping Auto-Sync Background Service...

REM Read PID from file
if exist "logs\sync-service.pid" (
    set /p PID=<logs\sync-service.pid
    echo Found service PID: %PID%

    REM Kill the process
    taskkill /PID %PID% /F 2>nul

    if %errorLevel% == 0 (
        echo Service stopped successfully!
        del logs\sync-service.pid
    ) else (
        echo Service may not be running or already stopped.
    )
) else (
    echo PID file not found. Service may not be running.
    echo Stopping all PowerShell sync processes...
    taskkill /FI "WINDOWTITLE eq auto-sync*" /F 2>nul
)

echo.
pause
