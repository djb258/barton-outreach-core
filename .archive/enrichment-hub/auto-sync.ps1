# Auto-Sync Script for Obsidian, GitKraken, and Git
# Automatically updates tools when repo changes are detected
# Run this script: powershell -ExecutionPolicy Bypass -File auto-sync.ps1

param(
    [switch]$Watch,
    [switch]$Force,
    [int]$Interval = 60
)

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Auto-Sync for Obsidian, GitKraken & Git" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$repoPath = Get-Location

# Function to check if Git repo has updates
function Test-GitUpdates {
    Write-Host "🔍 Checking for Git updates..." -ForegroundColor Gray

    # Fetch from remote
    git fetch origin 2>&1 | Out-Null

    # Check if local is behind remote
    $localCommit = git rev-parse HEAD
    $remoteCommit = git rev-parse origin/main 2>$null
    if (-not $remoteCommit) {
        $remoteCommit = git rev-parse origin/master 2>$null
    }

    if ($localCommit -ne $remoteCommit) {
        return $true
    }

    return $false
}

# Function to sync Obsidian vault
function Sync-ObsidianVault {
    Write-Host "📚 Syncing Obsidian vault..." -ForegroundColor Yellow

    # Check if .obsidian folder exists
    if (-not (Test-Path ".obsidian")) {
        Write-Host "⚠️  Obsidian vault not found, skipping..." -ForegroundColor Yellow
        return
    }

    # Update workspace to reflect latest files
    $workspaceFile = ".obsidian/workspace.json"
    if (Test-Path $workspaceFile) {
        $workspace = Get-Content $workspaceFile -Raw | ConvertFrom-Json

        # Update lastOpenFiles with recent changes
        $recentFiles = @(
            "CTB_README.md",
            "README.md",
            "TOOLS_SETUP.md",
            "ENV_SETUP.md"
        )

        $workspace.lastOpenFiles = $recentFiles
        $workspace | ConvertTo-Json -Depth 10 | Set-Content $workspaceFile

        Write-Host "✅ Obsidian workspace updated" -ForegroundColor Green
    }

    # Update app cache (if Obsidian is closed)
    $obsidianRunning = Get-Process -Name "Obsidian" -ErrorAction SilentlyContinue
    if (-not $obsidianRunning) {
        Write-Host "💡 Obsidian is not running. Changes will apply on next launch." -ForegroundColor Cyan
    } else {
        Write-Host "⚠️  Obsidian is running. Restart to apply changes." -ForegroundColor Yellow
    }
}

# Function to sync GitKraken configuration
function Sync-GitKrakenConfig {
    Write-Host "🐙 Syncing GitKraken configuration..." -ForegroundColor Yellow

    if (-not (Test-Path ".gitkraken")) {
        Write-Host "⚠️  GitKraken config not found, skipping..." -ForegroundColor Yellow
        return
    }

    # Update GitKraken config with latest repo info
    $configFile = ".gitkraken/config.json"
    if (Test-Path $configFile) {
        $config = Get-Content $configFile -Raw | ConvertFrom-Json

        # Update last sync time
        $config.project.lastSync = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

        # Get current branch
        $currentBranch = git rev-parse --abbrev-ref HEAD
        $config.project.currentBranch = $currentBranch

        $config | ConvertTo-Json -Depth 10 | Set-Content $configFile

        Write-Host "✅ GitKraken config updated" -ForegroundColor Green
    }

    # Check if GitKraken is running
    $gitkrakenRunning = Get-Process -Name "GitKraken" -ErrorAction SilentlyContinue
    if (-not $gitkrakenRunning) {
        Write-Host "💡 GitKraken is not running. Changes will apply on next launch." -ForegroundColor Cyan
    } else {
        Write-Host "⚠️  GitKraken is running. Refresh repository to see changes." -ForegroundColor Yellow
    }
}

# Function to update Git hooks
function Update-GitHooks {
    Write-Host "🔧 Updating Git hooks..." -ForegroundColor Yellow

    if (-not (Test-Path ".git/hooks")) {
        Write-Host "⚠️  Git hooks directory not found, skipping..." -ForegroundColor Yellow
        return
    }

    # Make hooks executable (Git Bash compatibility)
    $hooks = @("pre-commit", "commit-msg", "pre-push", "post-merge", "post-checkout")
    foreach ($hook in $hooks) {
        $hookPath = ".git/hooks/$hook"
        if (Test-Path $hookPath) {
            # Set execute permission via Git
            git update-index --chmod=+x ".git/hooks/$hook" 2>$null
        }
    }

    Write-Host "✅ Git hooks updated" -ForegroundColor Green
}

# Function to pull latest changes
function Pull-LatestChanges {
    Write-Host "⬇️  Pulling latest changes from remote..." -ForegroundColor Yellow

    $currentBranch = git rev-parse --abbrev-ref HEAD
    Write-Host "   Current branch: $currentBranch" -ForegroundColor Gray

    # Stash any local changes
    $hasChanges = git status --porcelain
    if ($hasChanges) {
        Write-Host "   Stashing local changes..." -ForegroundColor Gray
        git stash push -m "Auto-stash before sync $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    }

    # Pull changes
    $pullResult = git pull origin $currentBranch 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Successfully pulled latest changes" -ForegroundColor Green

        # Pop stash if we stashed
        if ($hasChanges) {
            Write-Host "   Applying stashed changes..." -ForegroundColor Gray
            git stash pop
        }

        return $true
    } else {
        Write-Host "❌ Failed to pull changes: $pullResult" -ForegroundColor Red
        return $false
    }
}

# Function to sync CTB registry
function Sync-CTBRegistry {
    Write-Host "📋 Syncing CTB registry..." -ForegroundColor Yellow

    $registryFile = "ctb/meta/registry.json"
    if (Test-Path $registryFile) {
        $registry = Get-Content $registryFile -Raw | ConvertFrom-Json

        # Update last sync time
        $registry.registry.last_updated = Get-Date -Format "yyyy-MM-dd"

        # Count files in CTB directories
        $ctbDirs = @("sys", "ai", "data", "docs", "ui", "meta")
        $totalFiles = 0
        foreach ($dir in $ctbDirs) {
            $path = "ctb/$dir"
            if (Test-Path $path) {
                $fileCount = (Get-ChildItem -Path $path -Recurse -File).Count
                $totalFiles += $fileCount
            }
        }

        $registry.registry.statistics.total_files = $totalFiles

        $registry | ConvertTo-Json -Depth 10 | Set-Content $registryFile

        Write-Host "✅ CTB registry updated (Total files: $totalFiles)" -ForegroundColor Green
    }
}

# Function to perform full sync
function Start-FullSync {
    param([bool]$PullFirst = $true)

    Write-Host ""
    Write-Host "🔄 Starting full sync..." -ForegroundColor Cyan
    Write-Host ""

    # Pull latest changes if requested
    if ($PullFirst) {
        $pulled = Pull-LatestChanges
        if (-not $pulled) {
            Write-Host "⚠️  Pull failed, but continuing with local sync..." -ForegroundColor Yellow
        }
        Write-Host ""
    }

    # Sync all tools
    Sync-ObsidianVault
    Write-Host ""

    Sync-GitKrakenConfig
    Write-Host ""

    Update-GitHooks
    Write-Host ""

    Sync-CTBRegistry
    Write-Host ""

    Write-Host "✅ Full sync completed!" -ForegroundColor Green
    Write-Host "   Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
}

# Watch mode - continuous monitoring
function Start-WatchMode {
    Write-Host "👁️  Starting watch mode (checking every $Interval seconds)..." -ForegroundColor Cyan
    Write-Host "   Press Ctrl+C to stop" -ForegroundColor Gray
    Write-Host ""

    $lastSyncTime = Get-Date

    while ($true) {
        try {
            # Check for updates
            $hasUpdates = Test-GitUpdates

            if ($hasUpdates) {
                Write-Host ""
                Write-Host "🆕 Updates detected!" -ForegroundColor Green
                Start-FullSync -PullFirst $true
                $lastSyncTime = Get-Date
            } else {
                $timeSinceSync = [math]::Round(((Get-Date) - $lastSyncTime).TotalMinutes, 1)
                Write-Host "✓ No updates (Last sync: $timeSinceSync min ago) - $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Gray
            }

            # Wait before next check
            Start-Sleep -Seconds $Interval

        } catch {
            Write-Host "⚠️  Error during watch: $($_.Exception.Message)" -ForegroundColor Yellow
            Start-Sleep -Seconds $Interval
        }
    }
}

# Main execution
if ($Watch) {
    # Watch mode - continuous monitoring
    Start-WatchMode
} else {
    # One-time sync
    $pullFirst = -not $Force
    Start-FullSync -PullFirst $pullFirst

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "💡 Tip: Run with -Watch flag for continuous sync:" -ForegroundColor Yellow
    Write-Host "   powershell -ExecutionPolicy Bypass -File auto-sync.ps1 -Watch" -ForegroundColor Gray
    Write-Host ""
}
