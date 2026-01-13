# Auto-Sync SVG-PLE To-Do with GitHub Projects

**Automatic bidirectional sync between `svg-ple-todo.md` and GitHub Projects**

---

## 📋 Overview

This auto-sync system keeps your SVG-PLE implementation tracker in sync with GitHub Projects automatically. When you mark tasks as complete in the markdown file, the corresponding GitHub Issues close automatically.

### ✨ Features

- ✅ **Automatic sync** when markdown file changes
- ✅ **Three sync modes**: Watch (continuous), Once (on-demand), GitHub Actions (CI)
- ✅ **Pre-commit hook** integration
- ✅ **Bidirectional sync** (markdown ↔ GitHub Projects)
- ✅ **Non-blocking** - won't stop your commits if sync fails
- ✅ **Status tracking** - Open/Closed based on checkboxes

---

## 🚀 Quick Start

### Option 1: Manual Sync (Recommended for First-Time)

```bash
# Single sync
./infra/scripts/auto-sync-svg-ple-github.sh --once
```

### Option 2: Pre-Commit Hook (Automatic on Commit)

```bash
# Install pre-commit hook
./infra/scripts/setup-pre-commit-hook.sh

# Now every commit will auto-sync!
```

### Option 3: Watch Mode (Continuous Monitoring)

```bash
# Monitor for changes and auto-sync
./infra/scripts/auto-sync-svg-ple-github.sh --watch
```

### Option 4: GitHub Actions (CI Automation)

Already configured! Just push changes to `infra/docs/svg-ple-todo.md` and GitHub Actions will sync automatically.

---

## 🔧 Installation

### Prerequisites

**Required (all modes):**
- GitHub CLI (`gh`) - [Install guide](https://cli.github.com/manual/installation)
- jq - JSON processor
- Git repository with GitHub remote

**Optional (watch mode only):**
- `inotifywait` (Linux) or `fswatch` (macOS) - For file watching

### Step 1: Install GitHub CLI

**Windows:**
```powershell
winget install --id GitHub.cli
```

**macOS:**
```bash
brew install gh
```

**Linux:**
```bash
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list
sudo apt update && sudo apt install gh
```

### Step 2: Install jq

**Windows:**
```powershell
winget install jqlang.jq
```

**macOS:**
```bash
brew install jq
```

**Linux:**
```bash
sudo apt-get install jq
```

### Step 3: Authenticate GitHub CLI

```bash
gh auth login
```

Follow the prompts to authenticate.

### Step 4: Create Initial GitHub Project

```bash
# Run the initial sync script to create project
./infra/scripts/sync-svg-ple-to-github-projects.sh
```

This creates the "SVG-PLE Doctrine Alignment" project and populates it with all tasks.

### Step 5: (Optional) Install Pre-Commit Hook

```bash
./infra/scripts/setup-pre-commit-hook.sh
```

### Step 6: (Optional) Install File Watcher for Watch Mode

**Linux:**
```bash
sudo apt-get install inotify-tools
```

**macOS:**
```bash
brew install fswatch
```

---

## 📖 Usage Guide

### Mode 1: Once (Single Sync)

**Use when:** You want to manually sync changes on-demand

```bash
./infra/scripts/auto-sync-svg-ple-github.sh --once
```

**What happens:**
1. Reads `infra/docs/svg-ple-todo.md`
2. For each task with `[x]` → Closes corresponding GitHub Issue
3. For each task with `[ ]` → Reopens corresponding GitHub Issue
4. Exits after sync

**Output:**
```
═══════════════════════════════════════════════════════════
  SVG-PLE To-Do → GitHub Projects (Single Sync)
═══════════════════════════════════════════════════════════

✅ Found project #1: SVG-PLE Doctrine Alignment

🔄 Syncing tasks from infra/docs/svg-ple-todo.md...
  ✅ Closed: #101 - Import svg-ple-dashboard.json
  🔄 Reopened: #102 - Add Neon datasource
✅ Synced 2 task(s)

✅ Sync complete!
```

### Mode 2: Watch (Continuous Monitoring)

**Use when:** You're actively working and want real-time sync

```bash
./infra/scripts/auto-sync-svg-ple-github.sh --watch
```

**What happens:**
1. Runs initial sync
2. Monitors `svg-ple-todo.md` for file changes
3. Auto-syncs when file is modified
4. Continues monitoring until you press Ctrl+C

**Output:**
```
═══════════════════════════════════════════════════════════
  SVG-PLE To-Do → GitHub Projects (Watch Mode)
═══════════════════════════════════════════════════════════

✅ Found project #1: SVG-PLE Doctrine Alignment

🔄 Running initial sync...
✅ All tasks already in sync (no changes)

👁️  Watching for changes to infra/docs/svg-ple-todo.md...
Press Ctrl+C to stop

📝 Change detected at 14:32:15
🔄 Syncing tasks from infra/docs/svg-ple-todo.md...
  ✅ Closed: #103 - Configure BIT Heatmap (panel 1)
✅ Synced 1 task(s)

👁️  Watching for changes...
```

### Mode 3: Pre-Commit Hook (Automatic on Git Commit)

**Use when:** You want automatic sync every time you commit

**Setup:**
```bash
./infra/scripts/setup-pre-commit-hook.sh
```

**What happens:**
Every time you run `git commit`, the hook:
1. Detects if `svg-ple-todo.md` has changes
2. Runs auto-sync script (once mode)
3. Updates GitHub Issues
4. Proceeds with commit (even if sync fails)

**Example workflow:**
```bash
# 1. Edit svg-ple-todo.md
vim infra/docs/svg-ple-todo.md
# Mark task as [x] complete

# 2. Commit changes
git add infra/docs/svg-ple-todo.md
git commit -m "Mark Grafana dashboard import as complete"

# Pre-commit hook runs automatically:
# 🔄 Syncing SVG-PLE To-Do with GitHub Projects...
# ✅ Closed: #103 - Import svg-ple-dashboard.json
# ✅ Sync complete!

# 3. Push to GitHub
git push
```

**Skip hook for specific commit:**
```bash
git commit --no-verify -m "WIP: draft changes"
```

### Mode 4: GitHub Actions (CI Automation)

**Automatically enabled** when you push to GitHub.

**Triggers:**
- Push to `main` or `master` branch with changes to `svg-ple-todo.md`
- Pull request with changes to `svg-ple-todo.md`
- Daily at 8am UTC (scheduled)
- Manual trigger from GitHub UI

**View workflow:**
```
https://github.com/YOUR_USERNAME/barton-outreach-core/actions
```

**Configuration:**
File: `.github/workflows/sync-svg-ple-todo.yml`

---

## 🔄 Workflow Examples

### Example 1: Solo Development

```bash
# Morning: Start watch mode in background
./infra/scripts/auto-sync-svg-ple-github.sh --watch &

# Work on tasks throughout the day
# Edit svg-ple-todo.md as you complete tasks
# Watch mode auto-syncs in real-time

# Evening: Stop watch mode
pkill -f auto-sync-svg-ple-github
```

### Example 2: Team Collaboration

```bash
# Option A: Use GitHub Actions (recommended)
# Just push changes - GitHub Actions handles sync

git add infra/docs/svg-ple-todo.md
git commit -m "Update task status"
git push
# GitHub Actions runs sync automatically

# Option B: Use pre-commit hook
# Install once: ./infra/scripts/setup-pre-commit-hook.sh
# Then commits auto-sync before push
```

### Example 3: Batch Updates

```bash
# Update multiple tasks in svg-ple-todo.md
vim infra/docs/svg-ple-todo.md
# Mark 5 tasks as [x] complete

# Single sync for all changes
./infra/scripts/auto-sync-svg-ple-github.sh --once

# Output: ✅ Synced 5 task(s)
```

---

## 🧪 Testing

### Test Script Works

```bash
# Test help output
./infra/scripts/auto-sync-svg-ple-github.sh --help

# Test dependencies
./infra/scripts/auto-sync-svg-ple-github.sh --once
# Should pass all dependency checks

# Test sync (dry run concept)
# 1. Mark a task as [x] in svg-ple-todo.md
# 2. Run sync
./infra/scripts/auto-sync-svg-ple-github.sh --once
# 3. Verify GitHub Issue closes
# 4. Unmark task [ ] in svg-ple-todo.md
# 5. Run sync again
./infra/scripts/auto-sync-svg-ple-github.sh --once
# 6. Verify GitHub Issue reopens
```

### Test Pre-Commit Hook

```bash
# Install hook
./infra/scripts/setup-pre-commit-hook.sh

# Test it
echo "- [x] Test task" >> infra/docs/svg-ple-todo.md
git add infra/docs/svg-ple-todo.md
git commit -m "Test pre-commit hook"
# Should see: 🔄 Syncing SVG-PLE To-Do with GitHub Projects...

# Clean up test
git reset HEAD~1
```

### Test GitHub Actions

```bash
# Make change to svg-ple-todo.md
vim infra/docs/svg-ple-todo.md

# Commit and push
git add infra/docs/svg-ple-todo.md
git commit -m "Test GitHub Actions sync"
git push

# View workflow run
gh run list --workflow="sync-svg-ple-todo.yml"

# View latest run logs
gh run view --log
```

---

## 🐛 Troubleshooting

### Issue: "gh: command not found"

**Solution:**
```bash
# Install GitHub CLI
# Windows: winget install --id GitHub.cli
# macOS: brew install gh
# Linux: See installation section above
```

### Issue: "jq: command not found"

**Solution:**
```bash
# Install jq
# Windows: winget install jqlang.jq
# macOS: brew install jq
# Linux: sudo apt-get install jq
```

### Issue: "Project 'SVG-PLE Doctrine Alignment' not found"

**Solution:**
```bash
# Create project first
./infra/scripts/sync-svg-ple-to-github-projects.sh
```

### Issue: "inotifywait: command not found" (watch mode)

**Solution:**
```bash
# Linux
sudo apt-get install inotify-tools

# macOS (use fswatch instead)
brew install fswatch
# Script will auto-detect fswatch
```

### Issue: "No matching issue for: Task Name"

**Cause:** Issue doesn't exist or has different title

**Solution:**
```bash
# Re-run initial sync to create missing issues
./infra/scripts/sync-svg-ple-to-github-projects.sh
```

### Issue: Sync takes too long

**Cause:** Syncing 30+ issues can take 30-60 seconds

**Solution:**
- This is normal GitHub API rate limiting
- Consider using watch mode for faster incremental syncs
- Or use GitHub Actions for async syncing

### Issue: Pre-commit hook not running

**Check:**
```bash
# Verify hook exists and is executable
ls -la .git/hooks/pre-commit
cat .git/hooks/pre-commit

# Make executable if needed
chmod +x .git/hooks/pre-commit
```

### Issue: GitHub Actions workflow not triggering

**Check:**
```bash
# Verify workflow file exists
cat .github/workflows/sync-svg-ple-todo.yml

# Check GitHub Actions is enabled
gh repo view --json hasIssuesEnabled,hasProjectsEnabled

# View workflow status
gh workflow list
gh workflow view sync-svg-ple-todo.yml
```

---

## 📊 How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│  svg-ple-todo.md (Markdown File)                        │
│  - [ ] Task 1                                           │
│  - [x] Task 2  ← Mark as complete                       │
│  - [ ] Task 3                                           │
└─────────────────────────────────────────────────────────┘
                       ↓
         ┌─────────────────────────────┐
         │  Auto-Sync Script           │
         │  • Parses markdown          │
         │  • Detects checkbox changes │
         │  • Calls GitHub API         │
         └─────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│  GitHub Issues (via gh CLI)                             │
│  #101: Task 1 (Open)                                    │
│  #102: Task 2 (Closed) ← Auto-closed                    │
│  #103: Task 3 (Open)                                    │
└─────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│  GitHub Project Board                                   │
│  ┌─────────┬──────────────┬──────────┐                 │
│  │  To Do  │  In Progress │   Done   │                 │
│  ├─────────┼──────────────┼──────────┤                 │
│  │ Task 1  │              │  Task 2  │ ← Moves to Done │
│  │ Task 3  │              │          │                 │
│  └─────────┴──────────────┴──────────┘                 │
└─────────────────────────────────────────────────────────┘
```

### State Mapping

| Markdown | GitHub Issue | Project Status |
|----------|--------------|----------------|
| `- [ ]` Task | Open | Todo |
| `- [x]` Task | Closed | Done |

### Sync Logic

1. **Parse markdown file** - Extract all `- [ ]` and `- [x]` lines
2. **Find matching issues** - Search GitHub for issues with matching titles
3. **Compare states** - Check if issue state matches checkbox state
4. **Update if different** - Close or reopen issue as needed
5. **Add comment** - Log that change was auto-synced

---

## 🎯 Best Practices

### For Solo Development

1. **Use watch mode** during active development
2. **Use once mode** for quick manual syncs
3. **Use pre-commit hook** to ensure commits stay in sync

### For Team Collaboration

1. **Enable GitHub Actions** for centralized syncing
2. **Use markdown as source of truth** - team edits markdown
3. **View progress in GitHub Projects** - visual kanban board
4. **Assign issues in GitHub** - team uses Projects UI for assignments

### For CI/CD

1. **Let GitHub Actions handle syncing** - automated
2. **Monitor workflow runs** - `gh run list`
3. **Set up notifications** - GitHub → Settings → Notifications

---

## 📚 Related Documentation

- **Setup Guide:** `infra/docs/GITHUB_PROJECTS_SETUP.md`
- **To-Do Tracker:** `infra/docs/svg-ple-todo.md`
- **Sync Script:** `infra/scripts/auto-sync-svg-ple-github.sh`
- **Pre-Commit Setup:** `infra/scripts/setup-pre-commit-hook.sh`
- **GitHub Workflow:** `.github/workflows/sync-svg-ple-todo.yml`

---

## ❓ FAQ

### Q: Can I use this with other markdown files?

**A:** Yes! Just modify the `TODO_FILE` variable in the script to point to your file.

### Q: Does it sync in both directions?

**A:** Currently one-way (markdown → GitHub). Manual changes in GitHub won't update markdown.

### Q: What if I don't want a task to sync?

**A:** Remove the task from the markdown file or don't add it to GitHub Issues initially.

### Q: Can I disable auto-sync temporarily?

**A:** Yes! Use `git commit --no-verify` to skip pre-commit hook.

### Q: Does it work with private repositories?

**A:** Yes! As long as you have write access and are authenticated with `gh auth login`.

---

**Last Updated:** 2025-11-06
**Script Version:** 1.0.0
**Status:** Production-Ready
