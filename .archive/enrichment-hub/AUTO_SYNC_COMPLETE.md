# Auto-Sync System - Installation Complete! 🎉

## Summary

A complete automated synchronization system has been installed that keeps Obsidian, GitKraken, and Git automatically updated whenever the repository changes.

## What Was Created

### 🔄 Auto-Sync Scripts

**Main sync scripts:**
- `auto-sync.ps1` - PowerShell version for Windows
- `auto-sync.sh` - Bash version for macOS/Linux

**Features:**
- One-time sync mode
- Watch mode (continuous monitoring)
- Force mode (skip pulling)
- Configurable intervals
- Smart pull management (auto-stash/pop)
- Tool detection (checks if running)
- Error handling and logging

### 🎯 Background Service

**Service scripts:**
- `start-sync-service.ps1` / `.sh` - Start background service
- `start-sync-service.bat` - Windows batch launcher
- `stop-sync-service.bat` / `.sh` - Stop background service

**Features:**
- Runs continuously in background
- Checks for updates every 5 minutes (configurable)
- Logs all operations to `logs/sync-service.log`
- PID tracking for process management
- Graceful shutdown handling

### 🪝 Git Hooks (Automatic Triggers)

**Hooks created:**
- `.git/hooks/post-merge` - Runs after git pull/merge
- `.git/hooks/post-checkout` - Runs after branch checkout

**Behavior:**
- Automatically trigger sync after Git operations
- No manual intervention required
- Runs silently in background
- Shows only important messages

### 📚 Obsidian Integration

**Configuration:**
- `.obsidian/plugins/obsidian-git/data.json` - Git plugin config

**Settings:**
- Auto-save every 5 minutes
- Auto-pull every 5 minutes
- Auto-pull on Obsidian startup
- Always pull before push
- List changed files in commits

### 🐙 GitKraken Integration

**Configuration files:**
- `.gitkraken/config.json` - Project configuration
- `.gitkraken/profiles.json` - Development profiles

**Features:**
- Auto-updates repository metadata
- Tracks current branch
- Records last sync time
- GitFlow presets

### 📋 Documentation

- `AUTO_SYNC_GUIDE.md` - Complete user guide
- Updated `README.md` - Added auto-sync section
- Updated `QUICK_START.md` - Added setup step

## How It Works

### Automatic Syncing (3 Methods)

**1. Git Hooks (Instant)**
```bash
git pull      # ✅ Auto-syncs immediately
git merge     # ✅ Auto-syncs immediately
git checkout  # ✅ Auto-syncs immediately
```

**2. Background Service (Continuous)**
```bash
./start-sync-service.sh  # Checks every 5 min
```

**3. Manual Sync (On-Demand)**
```bash
./auto-sync.sh           # Sync now
./auto-sync.sh --watch   # Watch mode
```

### What Gets Synced

When sync runs, it automatically:

✅ **Pulls latest changes** from remote (with auto-stash)
✅ **Updates Obsidian workspace** with recent files
✅ **Refreshes GitKraken config** with current branch
✅ **Updates Git hooks** permissions
✅ **Syncs CTB registry** with file counts
✅ **Logs all operations** for tracking

## Quick Start

### Option 1: Background Service (Recommended)

**Windows:**
```batch
start-sync-service.bat
```

**macOS/Linux:**
```bash
./start-sync-service.sh
```

Check logs: `logs/sync-service.log`

Stop service: `stop-sync-service.bat` or `./stop-sync-service.sh`

### Option 2: Manual Sync

**Windows:**
```powershell
# One-time sync
powershell -File auto-sync.ps1

# Watch mode
powershell -File auto-sync.ps1 -Watch

# Force (no pull)
powershell -File auto-sync.ps1 -Force
```

**macOS/Linux:**
```bash
# One-time sync
./auto-sync.sh

# Watch mode
./auto-sync.sh --watch

# Force (no pull)
./auto-sync.sh --force
```

### Option 3: Git Hooks Only

Already enabled by default! Just use Git normally:

```bash
git pull origin main  # Auto-syncs after pull
git checkout develop  # Auto-syncs after checkout
```

No configuration needed - it just works!

## Usage Examples

### During Active Development

Start watch mode in terminal:
```bash
./auto-sync.sh --watch
```

Or background service:
```bash
./start-sync-service.sh
```

### Before Starting Work

Manual sync to ensure up-to-date:
```bash
./auto-sync.sh
```

### When Switching Branches

Just switch - auto-sync runs automatically:
```bash
git checkout feature/new-feature  # Syncs automatically
```

### Team Collaboration

Everyone runs background service:
```bash
./start-sync-service.sh
```

All team members stay synced automatically!

## Configuration

### Change Sync Interval

**Background service:**
```bash
# 3 minutes
./start-sync-service.sh 180

# 10 minutes
./start-sync-service.sh 600
```

**Watch mode:**
```bash
# 2 minutes
./auto-sync.sh --watch --interval=120
```

### Customize Sync Operations

Edit `auto-sync.ps1` or `auto-sync.sh`:

```bash
# Add custom sync function
sync_custom_tool() {
    echo "Syncing custom tool..."
    # Your code here
}

# Call it in full_sync()
sync_custom_tool
```

### Obsidian Git Settings

Edit `.obsidian/plugins/obsidian-git/data.json`:

```json
{
  "autoSaveInterval": 5,      // Change to 10 for 10 min
  "autoPullInterval": 5,      // Change to 10 for 10 min
  "autoPullOnBoot": true      // Set false to disable
}
```

## Monitoring

### Check Service Status

**Windows:**
```batch
type logs\sync-service.log
```

**macOS/Linux:**
```bash
tail -f logs/sync-service.log
```

### Verify Sync is Working

Look for these messages:
- `✅ Full sync completed!`
- `✅ Obsidian workspace updated`
- `✅ GitKraken config updated`
- `✅ Git hooks updated`
- `✅ CTB registry updated`

### Check Background Service

**Windows:**
```batch
REM Check if running
type logs\sync-service.pid

REM View PID
```

**macOS/Linux:**
```bash
# Check if running
cat logs/sync-service.pid

# Check process
ps -p $(cat logs/sync-service.pid)
```

## Troubleshooting

### Scripts Won't Run

**Windows:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**macOS/Linux:**
```bash
chmod +x auto-sync.sh
chmod +x start-sync-service.sh
chmod +x stop-sync-service.sh
```

### Git Hooks Not Running

```bash
chmod +x .git/hooks/post-merge
chmod +x .git/hooks/post-checkout

# Test manually
.git/hooks/post-merge
```

### Service Won't Start

```bash
# Stop any existing service
./stop-sync-service.sh

# Remove stale PID
rm -f logs/sync-service.pid

# Start fresh
./start-sync-service.sh
```

### Obsidian Not Syncing

1. Open Obsidian
2. Settings → Community plugins
3. Install "Obsidian Git" plugin
4. Enable the plugin
5. Restart Obsidian

### Check for Errors

```bash
# Run with full output
./auto-sync.sh 2>&1 | tee sync-debug.log

# Check for errors
grep -i error sync-debug.log
```

## Best Practices

### Recommended Setup

1. ✅ **Enable background service** - Set and forget
2. ✅ **Keep Git hooks enabled** - Already done
3. ✅ **Install Obsidian Git plugin** - Auto-vault sync
4. ✅ **Check logs occasionally** - Verify operations

### When to Use Each Method

| Method | Best For | Use When |
|--------|----------|----------|
| Background Service | Daily work | Always running |
| Git Hooks | Auto-sync | Using Git |
| Watch Mode | Active dev | Short sessions |
| Manual Sync | On-demand | Before key work |

### Performance Tips

1. **Adjust intervals** based on your needs:
   - Active dev: 60-120 seconds
   - Normal: 300 seconds (5 min)
   - Light: 600+ seconds (10+ min)

2. **Use force mode** when appropriate:
   - Local-only changes
   - No remote updates expected

3. **Monitor resource usage**:
   - Check CPU usage if slow
   - Increase interval if needed

## Files Created

```
enricha-vision/
├── auto-sync.ps1                          # Windows sync script
├── auto-sync.sh                           # Linux/Mac sync script
├── start-sync-service.ps1                 # Windows service
├── start-sync-service.sh                  # Linux/Mac service
├── start-sync-service.bat                 # Windows launcher
├── stop-sync-service.bat                  # Windows stop
├── stop-sync-service.sh                   # Linux/Mac stop
├── AUTO_SYNC_GUIDE.md                     # Complete guide
├── AUTO_SYNC_COMPLETE.md                  # This file
├── .git/hooks/
│   ├── post-merge                         # Auto-sync on merge
│   └── post-checkout                      # Auto-sync on checkout
├── .obsidian/plugins/obsidian-git/
│   └── data.json                          # Git plugin config
└── logs/
    ├── sync-service.log                   # Service logs
    └── sync-service.pid                   # Process ID
```

## What's Next

### Immediate Actions

1. **Start the background service:**
   ```bash
   ./start-sync-service.sh
   ```

2. **Test auto-sync:**
   ```bash
   git pull
   # Should see auto-sync messages
   ```

3. **Check logs:**
   ```bash
   tail -f logs/sync-service.log
   ```

### Optional Enhancements

1. **Schedule with cron/Task Scheduler** for system startup
2. **Customize sync operations** for your workflow
3. **Add notifications** for important events
4. **Integrate with CI/CD** pipelines

## Support

### Documentation

- **Full Guide**: [AUTO_SYNC_GUIDE.md](./AUTO_SYNC_GUIDE.md)
- **Quick Start**: [QUICK_START.md](./QUICK_START.md)
- **Tools Setup**: [TOOLS_SETUP.md](./TOOLS_SETUP.md)

### Getting Help

1. Check `AUTO_SYNC_GUIDE.md` troubleshooting
2. Review log files for errors
3. Test scripts manually
4. Verify tool installations

### Common Issues

| Issue | Solution |
|-------|----------|
| Script won't execute | Check permissions |
| Hooks not running | Make executable |
| Service won't start | Remove stale PID |
| No sync happening | Check logs for errors |

## Success Indicators

You'll know auto-sync is working when:

✅ Logs show regular sync operations
✅ Git pulls trigger automatic sync
✅ Branch switches trigger sync
✅ Obsidian vault stays updated
✅ GitKraken shows current info
✅ CTB registry stays current

## Congratulations! 🎊

You now have a fully automated synchronization system that:

- ✅ Keeps all tools up-to-date
- ✅ Runs automatically in background
- ✅ Syncs on every Git operation
- ✅ Handles conflicts gracefully
- ✅ Logs everything for transparency
- ✅ Requires zero manual intervention

**Your development environment stays synchronized automatically!** 🚀

---

**Questions?** See [AUTO_SYNC_GUIDE.md](./AUTO_SYNC_GUIDE.md) for comprehensive documentation.

**Built with automation in mind!** 🤖
