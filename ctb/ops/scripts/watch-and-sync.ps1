# ============================================================================
# Continuous Watch and Sync - All Tools (PowerShell)
# ============================================================================
# CTB Branch: ops/scripts
# Barton ID: 07.02.03
# Purpose: Watch for changes and auto-sync Obsidian, GitKraken, GitHub Projects
# Platform: Windows 10/11 (PowerShell 5.1+)
# ============================================================================

param(
    [switch]$Background,
    [int]$ObsidianInterval = 300,  # 5 minutes
    [int]$GitHubInterval = 600,     # 10 minutes
    [int]$SchemaInterval = 1800     # 30 minutes
)

# Set up logging
$LogFile = "ctb\ops\logs\watch-and-sync.log"
$LogDir = Split-Path $LogFile -Parent
if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] [$Level] $Message"
    Write-Host $LogMessage
    Add-Content -Path $LogFile -Value $LogMessage
}

function Sync-Obsidian {
    Write-Log "Syncing Obsidian vault..." "INFO"

    Push-Location "ctb\docs\obsidian-vault"

    git add -A
    $changes = git diff --staged --quiet

    if ($LASTEXITCODE -ne 0) {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        git commit -m "docs(obsidian): auto-sync vault $timestamp`n`n🤖 Auto-committed by watch-and-sync script`n`nCo-Authored-By: Watch Script <noreply@barton-outreach.local>"
        git push
        Write-Log "Obsidian changes synced successfully" "OK"
    } else {
        Write-Log "No Obsidian changes to sync" "INFO"
    }

    Pop-Location
}

function Sync-GitHubProjects {
    Write-Log "Syncing GitHub Projects..." "INFO"

    if (Test-Path "infra\scripts\auto-sync-svg-ple-github.sh") {
        $result = bash "infra\scripts\auto-sync-svg-ple-github.sh" --once 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "GitHub Projects synced successfully" "OK"
        } else {
            Write-Log "GitHub Projects sync failed: $result" "WARNING"
        }
    } else {
        Write-Log "GitHub Projects sync script not found" "WARNING"
    }
}

function Sync-Schema {
    Write-Log "Checking for schema changes..." "INFO"

    # Check if recent commits mention migrations
    $recentCommits = git log -5 --oneline

    if ($recentCommits -match "migration|schema") {
        Write-Log "Migration detected, refreshing schema..." "INFO"

        npm run schema:export

        git add "ctb\docs\schema_map.json" "ctb\data\SCHEMA_REFERENCE.md"
        $changes = git diff --staged --quiet

        if ($LASTEXITCODE -ne 0) {
            git commit -m "chore(schema): auto-refresh after migration`n`n🤖 Auto-committed by watch-and-sync script`n`nCo-Authored-By: Watch Script <noreply@barton-outreach.local>"
            git push
            Write-Log "Schema refreshed and pushed" "OK"
        } else {
            Write-Log "No schema changes to commit" "INFO"
        }
    } else {
        Write-Log "No schema changes detected" "INFO"
    }
}

# Main watch loop
Write-Host @"

============================================================================
  CONTINUOUS WATCH AND SYNC - ALL TOOLS
============================================================================

This script will continuously monitor and sync:
  - Obsidian vault changes (every $($ObsidianInterval/60) minutes)
  - GitHub Projects updates (every $($GitHubInterval/60) minutes)
  - Database schema changes (every $($SchemaInterval/60) minutes)

Press Ctrl+C to stop watching

Logging to: $LogFile

============================================================================

"@

Write-Log "Watch-and-sync started" "INFO"

$obsidianTimer = [System.Diagnostics.Stopwatch]::StartNew()
$githubTimer = [System.Diagnostics.Stopwatch]::StartNew()
$schemaTimer = [System.Diagnostics.Stopwatch]::StartNew()

try {
    while ($true) {
        # Check Obsidian sync
        if ($obsidianTimer.Elapsed.TotalSeconds -ge $ObsidianInterval) {
            try {
                Sync-Obsidian
            } catch {
                Write-Log "Obsidian sync error: $_" "ERROR"
            }
            $obsidianTimer.Restart()
        }

        # Check GitHub Projects sync
        if ($githubTimer.Elapsed.TotalSeconds -ge $GitHubInterval) {
            try {
                Sync-GitHubProjects
            } catch {
                Write-Log "GitHub Projects sync error: $_" "ERROR"
            }
            $githubTimer.Restart()
        }

        # Check schema sync
        if ($schemaTimer.Elapsed.TotalSeconds -ge $SchemaInterval) {
            try {
                Sync-Schema
            } catch {
                Write-Log "Schema sync error: $_" "ERROR"
            }
            $schemaTimer.Restart()
        }

        # Show next sync times
        $nextObsidian = [math]::Round($ObsidianInterval - $obsidianTimer.Elapsed.TotalSeconds)
        $nextGitHub = [math]::Round($GitHubInterval - $githubTimer.Elapsed.TotalSeconds)
        $nextSchema = [math]::Round($SchemaInterval - $schemaTimer.Elapsed.TotalSeconds)

        Write-Host "`r[$(Get-Date -Format 'HH:mm:ss')] Next sync - Obsidian: ${nextObsidian}s | GitHub: ${nextGitHub}s | Schema: ${nextSchema}s    " -NoNewline

        # Sleep for 30 seconds
        Start-Sleep -Seconds 30
    }
} catch {
    Write-Log "Watch-and-sync stopped: $_" "INFO"
} finally {
    Write-Log "Watch-and-sync ended" "INFO"
}
