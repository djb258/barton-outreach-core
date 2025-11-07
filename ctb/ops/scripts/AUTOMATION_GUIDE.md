<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ops/scripts
Barton ID: 07.02.04
Unique ID: CTB-AUTO-GUIDE
Blueprint Hash:
Last Updated: 2025-11-07
Enforcement: None
─────────────────────────────────────────────
-->

# 🤖 Automation Guide - Auto-Sync All Tools

Complete automation system that keeps Obsidian, GitKraken, and GitHub Projects automatically updated as you work.

---

## 🎯 What Gets Automated

### 1. Obsidian Vault
- **What**: Auto-commit and push changes every 5 minutes
- **How**: Obsidian Git plugin + PowerShell watcher
- **When**: Continuous while working

### 2. GitHub Projects
- **What**: Sync to-do items and track progress
- **How**: GitHub Actions workflow + manual sync scripts
- **When**: On push, PR, issues + every 6 hours

### 3. Database Schema
- **What**: Refresh schema documentation after migrations
- **How**: Python export script triggered by commits
- **When**: When commit message contains "migration" or "schema"

### 4. GitKraken
- **What**: Automatically reflects Git changes (no setup needed)
- **How**: Desktop app auto-refreshes
- **When**: Real-time

---

## 🚀 Quick Start

### Option 1: Automated Watch (Recommended)

```bash
# Install tools first (if not done)
npm run tools:install

# Start continuous auto-sync (PowerShell)
npm run tools:watch

# Or use batch version
npm run tools:watch:batch
```

**What it does**:
- Checks Obsidian vault every 5 minutes
- Syncs GitHub Projects every 10 minutes
- Refreshes schema every 30 minutes
- Runs continuously in terminal
- Logs everything to `ctb/ops/logs/watch-and-sync.log`

### Option 2: Manual Sync

```bash
# Sync just GitHub Projects
npm run sync:svg-ple

# Export schema manually
npm run schema:export

# Commit Obsidian changes manually
cd ctb/docs/obsidian-vault
git add -A && git commit -m "docs: manual sync" && git push
```

### Option 3: GitHub Actions (Automatic)

Push to GitHub and Actions handle everything:
```bash
git push origin main
# GitHub Actions automatically:
# - Syncs GitHub Projects
# - Commits Obsidian changes
# - Refreshes schema (if migrations detected)
# - Updates documentation timestamps
```

---

## 📋 Automation Components

### 1. GitHub Actions Workflow

**File**: `.github/workflows/auto-sync-tools.yml`

**Triggers**:
- `push` to main or feature branches
- `pull_request` opened/closed
- `issues` opened/closed/labeled
- `schedule` every 6 hours
- `workflow_dispatch` manual trigger

**Jobs**:
1. **sync-github-projects** - Updates GitHub Projects board
2. **auto-commit-obsidian** - Commits vault changes
3. **refresh-schema** - Exports schema after migrations
4. **update-documentation** - Updates timestamps in docs

**Configuration**:
```yaml
# Requires GitHub secrets (auto-configured):
# - GITHUB_TOKEN (automatic)
# - DATABASE_URL (add manually for schema refresh)
```

### 2. Obsidian Git Plugin

**File**: `ctb/docs/obsidian-vault/.obsidian/plugins/obsidian-git/data.json`

**Settings**:
```json
{
  "autoSaveInterval": 5,      // Auto-commit every 5 min
  "autoPushInterval": 5,      // Auto-push every 5 min
  "autoPullInterval": 5,      // Auto-pull every 5 min
  "autoPullOnBoot": true,     // Pull on startup
  "pullBeforePush": true      // Avoid conflicts
}
```

**Installation**:
1. Open Obsidian
2. Settings → Community Plugins → Browse
3. Search "Obsidian Git"
4. Install and Enable
5. Configuration already set (data.json)

### 3. PowerShell Watcher

**File**: `ctb/ops/scripts/watch-and-sync.ps1`

**Features**:
- Continuous monitoring
- Configurable intervals
- Logging to file
- Error handling
- Status display

**Usage**:
```powershell
# Default intervals
.\ctb\ops\scripts\watch-and-sync.ps1

# Custom intervals (seconds)
.\ctb\ops\scripts\watch-and-sync.ps1 -ObsidianInterval 180 -GitHubInterval 300 -SchemaInterval 900
```

### 4. Batch Watcher (Alternative)

**File**: `ctb/ops/scripts/watch-and-sync.bat`

**Usage**:
```batch
ctb\ops\scripts\watch-and-sync.bat
```

Simpler version without PowerShell, same functionality.

---

## 🔧 Configuration

### Intervals

Edit in PowerShell script:
```powershell
param(
    [int]$ObsidianInterval = 300,  # 5 min (change here)
    [int]$GitHubInterval = 600,     # 10 min
    [int]$SchemaInterval = 1800     # 30 min
)
```

Or pass as parameters:
```bash
npm run tools:watch -- -ObsidianInterval 180
```

### GitHub Actions Schedule

Edit in `.github/workflows/auto-sync-tools.yml`:
```yaml
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours (change here)
```

### Obsidian Git Timing

Edit `ctb/docs/obsidian-vault/.obsidian/plugins/obsidian-git/data.json`:
```json
{
  "autoSaveInterval": 5,  // Change to desired minutes
  "autoPushInterval": 5,
  "autoPullInterval": 5
}
```

---

## 📊 Monitoring

### Watch Script Logs

```bash
# View live logs
tail -f ctb/ops/logs/watch-and-sync.log

# View last 50 lines
tail -50 ctb/ops/logs/watch-and-sync.log

# Search for errors
grep ERROR ctb/ops/logs/watch-and-sync.log
```

### GitHub Actions Logs

1. Go to: https://github.com/djb258/barton-outreach-core/actions
2. Click on latest workflow run
3. View job logs

### Obsidian Git Status

In Obsidian:
- Status bar shows last commit time
- Click status bar for manual operations
- View → Command Palette → "Git: View"

---

## 🐛 Troubleshooting

### Watch Script Not Running

**Issue**: Script fails to start
```bash
# Check PowerShell execution policy
Get-ExecutionPolicy

# If Restricted, set to RemoteSigned
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Obsidian Not Auto-Committing

**Checks**:
1. Git plugin installed? (Settings → Community Plugins)
2. Plugin enabled? (Toggle in plugin list)
3. Git configured? (`git config user.name`, `git config user.email`)
4. Vault is Git repo? (`cd ctb/docs/obsidian-vault && git status`)

**Fix**:
```bash
# Configure Git
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

# Initialize if needed
cd ctb/docs/obsidian-vault
git init
git remote add origin <your-repo-url>
```

### GitHub Actions Failing

**Check**:
1. Workflow file syntax: https://www.yamllint.com/
2. GitHub Actions tab for error messages
3. Secrets configured (Settings → Secrets)

**Common fixes**:
```yaml
# Ensure GITHUB_TOKEN has permissions
permissions:
  contents: write
  issues: write
  pull-requests: write
```

### Schema Refresh Not Working

**Issue**: Schema export fails in GitHub Actions

**Fix**: Add DATABASE_URL secret
1. Go to: Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `DATABASE_URL`
4. Value: Your Neon connection string

---

## 🎯 Best Practices

### Daily Workflow

**Morning**:
```bash
# Start watcher (keeps tools synced all day)
npm run tools:watch
```

**During Development**:
- Work normally in IDE
- Add notes to Obsidian
- Watcher handles syncing automatically

**End of Day**:
- Stop watcher (Ctrl+C)
- Review logs if needed
- Check GitHub Projects for status

### When to Manual Sync

Use manual sync when:
- Watcher not running
- Need immediate sync
- Testing sync scripts
- Debugging issues

```bash
npm run sync:svg-ple      # GitHub Projects
npm run schema:export     # Database schema
```

### Commit Message Triggers

Include these keywords to trigger auto-actions:

**"migration"** or **"schema"** → Schema refresh
```bash
git commit -m "feat: add user authentication migration"
# GitHub Actions will auto-refresh schema
```

**Regular commits** → Standard sync
```bash
git commit -m "docs: update architecture notes"
# GitHub Actions syncs Projects, Obsidian
```

---

## 📈 Performance Impact

### System Resources

**PowerShell Watcher**:
- CPU: <1% (idle most of time)
- Memory: ~50MB
- Disk: Minimal (only logs)

**GitHub Actions**:
- Free tier: 2,000 minutes/month
- Typical run: 2-3 minutes
- ~100 runs/month with current schedule

**Obsidian Git Plugin**:
- Negligible impact
- Only active during sync (5-10 seconds)

### Network Usage

- **Obsidian sync**: ~100KB per commit (small changes)
- **GitHub Projects**: ~50KB per API call
- **Schema export**: ~500KB (JSON + MD files)

**Total**: <1MB per hour with default intervals

---

## 🔐 Security Considerations

### Credentials

✅ **Safe**:
- GitHub token (automatic, scoped)
- Git credentials (user-configured)
- DATABASE_URL (stored in secrets)

❌ **Never commit**:
- `.env` files
- API keys in plaintext
- Personal access tokens

### Permissions

**GitHub Actions needs**:
- `contents: write` - Commit changes
- `issues: write` - Update Projects
- `pull-requests: write` - Manage PRs

**Obsidian Git needs**:
- Git read/write access
- Remote push permission

### Audit Trail

All automation commits include:
```
🤖 Auto-committed by [script name]

Co-Authored-By: [Bot Name] <email>
```

This makes automated changes traceable.

---

## 🚀 Advanced Usage

### Run Watcher as Windows Service

Create scheduled task to run on startup:
```powershell
# Create task
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\path\to\watch-and-sync.ps1"
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName "BartonAutoSync" -Action $action -Trigger $trigger
```

### Multiple Environments

Create environment-specific configs:
```bash
# Development
npm run tools:watch -- -ObsidianInterval 180 -GitHubInterval 300

# Production
npm run tools:watch -- -ObsidianInterval 600 -GitHubInterval 1800
```

### Custom Sync Logic

Edit `watch-and-sync.ps1` functions:
```powershell
function Sync-Custom {
    # Your custom sync logic here
    # Example: Sync to S3, backup database, etc.
}
```

---

## 📚 Related Documentation

**Setup**:
- `ctb/ops/scripts/POST_INSTALL_GUIDE.md` - Initial setup
- `ctb/ops/scripts/setup-required-tools.bat` - Tool installer

**Tools**:
- `ctb/docs/obsidian-vault/README.md` - Obsidian guide
- `ctb/sys/github-projects/README.md` - GitHub Projects guide
- `global-config/required_tools.yaml` - Tool specifications

**Scripts**:
- `ctb/ops/scripts/watch-and-sync.ps1` - PowerShell watcher
- `ctb/ops/scripts/watch-and-sync.bat` - Batch watcher
- `.github/workflows/auto-sync-tools.yml` - GitHub Actions

---

## ✅ Success Checklist

Automation is working when:

- [ ] Watch script running without errors
- [ ] Obsidian commits every 5 minutes (check Git log)
- [ ] GitHub Projects shows recent commits
- [ ] Schema refreshes after migrations
- [ ] Logs showing regular activity
- [ ] GitKraken reflects changes in real-time
- [ ] No authentication errors
- [ ] GitHub Actions passing

---

**Status**: Production Ready
**Maintenance**: Logs rotate daily (auto-cleanup)
**Support**: Check logs first, then POST_INSTALL_GUIDE.md

---

*Automation makes tools transparent - work naturally, let scripts handle the sync.*
