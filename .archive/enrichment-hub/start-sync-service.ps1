# Background Sync Service for Windows
# Runs auto-sync continuously in the background
# Usage: powershell -WindowStyle Hidden -File start-sync-service.ps1

param(
    [int]$Interval = 300,  # 5 minutes default
    [string]$LogFile = "logs/sync-service.log"
)

# Ensure logs directory exists
$logDir = Split-Path -Path $LogFile -Parent
if ($logDir -and -not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Write-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Add-Content -Path $LogFile -Value $logMessage
    Write-Host $logMessage
}

Write-Log "========================================="
Write-Log "Starting Auto-Sync Background Service"
Write-Log "Interval: $Interval seconds"
Write-Log "========================================="

# Create PID file
$pidFile = "logs/sync-service.pid"
$PID | Out-File -FilePath $pidFile

Write-Log "Service PID: $PID (saved to $pidFile)"

# Main loop
$iteration = 0
while ($true) {
    try {
        $iteration++
        Write-Log "--- Iteration $iteration ---"

        # Run auto-sync
        $syncOutput = & powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\auto-sync.ps1" 2>&1

        # Log important messages
        $syncOutput | Where-Object { $_ -match "^(✅|❌|⚠️|🆕)" } | ForEach-Object {
            Write-Log $_
        }

        Write-Log "Sync completed. Waiting $Interval seconds..."

    } catch {
        Write-Log "ERROR: $($_.Exception.Message)"
    }

    Start-Sleep -Seconds $Interval
}
