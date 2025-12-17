# Auto-Sync System Guide

Complete guide for the automated synchronization system for Obsidian, GitKraken, and Git.

## Overview

The auto-sync system automatically keeps your tools up-to-date whenever the repository changes:

- **Obsidian**: Auto-updates vault workspace and files
- **GitKraken**: Auto-refreshes repository configuration
- **Git**: Auto-updates hooks and permissions
- **CTB Registry**: Auto-updates file counts and metadata

## How It Works

### Automatic Triggers

**1. Git Hooks (Automatic)**
- After pulling changes (`post-merge` hook)
- After switching branches (`post-checkout` hook)
- Runs sync immediately after Git operations

**2. Background Service (Optional)**
- Continuously monitors for remote changes
- Checks every 5 minutes (configurable)
- Automatically pulls and syncs when updates detected

**3. Manual Sync (On-Demand)**
- Run sync script manually anytime
- Force sync without pulling
- Watch mode for continuous monitoring

### What Gets Synced

✅ **Obsidian Vault**
- Workspace configuration
- Recent file list
- Plugin settings

✅ **GitKraken Config**
- Repository metadata
- Current branch info
- Last sync timestamp

✅ **Git Hooks**
- File permissions
- Executable flags

✅ **CTB Registry**
- File counts
- Last update time
- Statistics

## Usage

### Quick Start - Manual Sync

**Windows:**
```powershell
# One-time sync (pulls first)
powershell -ExecutionPolicy Bypass -File auto-sync.ps1

# Force sync (no pull)
powershell -ExecutionPolicy Bypass -File auto-sync.ps1 -Force

# Watch mode (continuous)
powershell -ExecutionPolicy Bypass -File auto-sync.ps1 -Watch

# Custom interval (seconds)
powershell -ExecutionPolicy Bypass -File auto-sync.ps1 -Watch -Interval 120
```

**macOS/Linux:**
```bash
# One-time sync (pulls first)
./auto-sync.sh

# Force sync (no pull)
./auto-sync.sh --force

# Watch mode (continuous)
./auto-sync.sh --watch

# Custom interval (seconds)
./auto-sync.sh --watch --interval=120
```

### Background Service (Recommended)

Run sync continuously in the background:

**Windows:**
```batch
REM Start service
start-sync-service.bat

REM Stop service
stop-sync-service.bat

REM Check logs
type logs\sync-service.log
```

**macOS/Linux:**
```bash
# Start service (default 5 min interval)
./start-sync-service.sh

# Start with custom interval
./start-sync-service.sh 180  # 3 minutes

# Stop service
./stop-sync-service.sh

# Check logs
tail -f logs/sync-service.log
```

### Automatic Git Hooks

Hooks run automatically on Git operations:

```bash
# These trigger auto-sync automatically:
git pull          # Triggers post-merge hook
git merge         # Triggers post-merge hook
git checkout main # Triggers post-checkout hook

# Sync runs automatically, no action needed!
```

## Configuration

### Sync Interval

**Manual sync scripts:**
- Default: Pull and sync once
- Watch mode: Check every 60 seconds

**Background service:**
- Default: Check every 300 seconds (5 minutes)
- Configurable via command line argument

**Obsidian Git Plugin:**
- Auto-save: Every 5 minutes
- Auto-pull: Every 5 minutes
- Auto-push: Disabled (manual)

### Customizing Behavior

**Edit auto-sync.ps1 or auto-sync.sh:**

```bash
# Change default interval
INTERVAL=120  # 2 minutes

# Add custom sync operations
sync_custom_tool() {
    echo "Syncing custom tool..."
    # Your code here
}
```

**Edit Obsidian Git settings:**

File: `.obsidian/plugins/obsidian-git/data.json`

```json
{
  "autoSaveInterval": 5,       // Minutes
  "autoPullInterval": 5,       // Minutes
  "autoPullOnBoot": true,      // Pull on Obsidian start
  "pullBeforePush": true       // Always pull first
}
```

## Features

### Smart Pull Management

- **Auto-stash**: Stashes local changes before pull
- **Auto-pop**: Restores changes after pull
- **Conflict detection**: Warns about merge conflicts
- **Branch awareness**: Only pulls current branch

### Tool Detection

- Checks if Obsidian is running
- Checks if GitKraken is running
- Provides appropriate restart warnings
- Non-blocking operations

### Error Handling

- Continues on errors (doesn't halt)
- Logs all operations
- Provides clear error messages
- Graceful degradation

### Logging

All operations logged to:
- **Service logs**: `logs/sync-service.log`
- **Console output**: Real-time feedback
- **Timestamps**: All log entries timestamped

## Troubleshooting

### Sync Not Working

**Check if scripts are executable:**
```bash
# macOS/Linux
chmod +x auto-sync.sh
chmod +x .git/hooks/post-merge
chmod +x .git/hooks/post-checkout

# Windows - ensure execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Check for errors:**
```bash
# Run with verbose output
./auto-sync.sh 2>&1 | tee sync-debug.log
```

### Background Service Issues

**Service won't start:**
```bash
# Check if already running
cat logs/sync-service.pid

# Force stop and restart
./stop-sync-service.sh
./start-sync-service.sh
```

**High CPU usage:**
```bash
# Increase interval
./start-sync-service.sh 600  # 10 minutes
```

### Obsidian Not Syncing

**Check plugin installation:**
1. Open Obsidian
2. Settings → Community plugins
3. Ensure "Obsidian Git" is installed
4. Check plugin settings

**Manual plugin install:**
```bash
# Create plugin directory
mkdir -p .obsidian/plugins/obsidian-git

# The plugin will auto-install on first Obsidian launch
```

### GitKraken Not Updating

**Refresh repository:**
1. Open GitKraken
2. Right-click repository
3. Select "Refresh"

**Or restart GitKraken:**
- Close GitKraken completely
- Reopen and load repository

### Git Hooks Not Running

**Check hook permissions:**
```bash
# Make hooks executable
chmod +x .git/hooks/post-merge
chmod +x .git/hooks/post-checkout

# On Windows (Git Bash)
git update-index --chmod=+x .git/hooks/post-merge
git update-index --chmod=+x .git/hooks/post-checkout
```

**Test hooks manually:**
```bash
# Trigger post-merge
.git/hooks/post-merge

# Trigger post-checkout
.git/hooks/post-checkout prev_ref new_ref 1
```

## Advanced Usage

### Multiple Repositories

Run background service for multiple repos:

```powershell
# Windows - Start in each repo directory
cd C:\path\to\repo1
start-sync-service.bat

cd C:\path\to\repo2
start-sync-service.bat
```

### Custom Sync Operations

Add your own sync operations to the scripts:

**In auto-sync.ps1:**
```powershell
function Sync-CustomTool {
    Write-Host "📦 Syncing custom tool..." -ForegroundColor Yellow
    # Your code here
}

# Add to full sync:
Sync-CustomTool
```

**In auto-sync.sh:**
```bash
sync_custom_tool() {
    echo -e "${YELLOW}📦 Syncing custom tool...${NC}"
    # Your code here
}

# Add to full sync:
sync_custom_tool
```

### Scheduled Sync (Windows Task Scheduler)

Create a scheduled task:

```powershell
# Run every hour
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
    -Argument "-ExecutionPolicy Bypass -File auto-sync.ps1"

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Hours 1)

Register-ScheduledTask -TaskName "EnrichaVisionSync" `
    -Action $action -Trigger $trigger -Description "Auto-sync Enricha Vision repo"
```

### Scheduled Sync (Linux/macOS cron)

Add to crontab:

```bash
# Edit crontab
crontab -e

# Add line (runs every hour)
0 * * * * cd /path/to/enricha-vision && ./auto-sync.sh --force >> logs/cron-sync.log 2>&1
```

## Best Practices

### Recommended Setup

1. **Enable background service** for automatic sync
2. **Keep Obsidian Git plugin enabled** for vault sync
3. **Use Git hooks** for immediate sync on pull/merge
4. **Check logs occasionally** to verify operation

### When to Use Each Method

**Background Service:**
- Best for: Continuous development
- Use when: Working throughout the day
- Benefit: Always up-to-date

**Git Hooks:**
- Best for: Automatic sync on Git operations
- Use when: Already enabled (default)
- Benefit: Zero-effort sync

**Manual Sync:**
- Best for: On-demand updates
- Use when: Before important work
- Benefit: Full control

**Watch Mode:**
- Best for: Active development sessions
- Use when: Making frequent changes
- Benefit: Immediate updates

### Performance Tips

1. **Adjust intervals** based on your workflow
   - Frequent updates: 60-120 seconds
   - Normal use: 300 seconds (5 min)
   - Light use: 600+ seconds (10+ min)

2. **Use force mode** when pulling isn't needed
   - Saves time on local-only changes
   - Skip if no remote updates

3. **Monitor log file size**
   - Rotate logs periodically
   - Keep last 30 days

## Security Considerations

### What's Safe

✅ Scripts only read/write local files
✅ No external network calls (except Git)
✅ No credential storage
✅ No sensitive data in logs

### Permissions

- Scripts need read/write access to:
  - `.obsidian/` folder
  - `.gitkraken/` folder
  - `.git/hooks/` folder
  - `ctb/` folder
  - `logs/` folder

### Logs

Logs may contain:
- File paths
- Branch names
- Timestamps
- Sync status

Logs do NOT contain:
- Passwords
- API keys
- File contents
- Credentials

## Support

### Getting Help

1. Check this guide
2. Review log files
3. Test scripts manually
4. Check Git hook execution
5. Verify tool installations

### Common Solutions

| Issue | Solution |
|-------|----------|
| Scripts won't run | Check permissions/execution policy |
| Hooks not triggering | Verify hook permissions |
| Service won't start | Check for existing PID file |
| Obsidian not syncing | Restart Obsidian or check plugin |
| GitKraken not updating | Refresh repository |

### Debug Mode

Enable verbose output:

```bash
# Add debug flag to scripts
./auto-sync.sh --debug

# Or redirect all output
./auto-sync.sh 2>&1 | tee debug.log
```

## FAQ

**Q: Will this commit my changes automatically?**
A: No, only Obsidian Git plugin can auto-commit. The sync scripts only pull and update configs.

**Q: Can I run multiple sync processes?**
A: Not recommended. Use one background service OR manual syncs, not both simultaneously.

**Q: Does this work offline?**
A: Yes, local syncs work offline. Remote pull/push requires internet.

**Q: Will this overwrite my local changes?**
A: No, it stashes local changes before pulling and restores them after.

**Q: Can I customize what gets synced?**
A: Yes, edit the sync scripts to add/remove sync operations.

**Q: How do I disable auto-sync?**
A: Stop the background service and disable Git hooks (rename them).

---

**Built with automation in mind!** 🤖

For more info, see:
- `TOOLS_SETUP.md` - Tool configuration
- `CTB_README.md` - CTB system overview
- `QUICK_START.md` - Getting started
