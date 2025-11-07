# 🚀 Quick Start — GitHub Projects Integration for SVG-PLE

**5-Minute Setup Guide**

---

## ✅ What You Get

- 📋 **GitHub Project Board** with 30 tasks organized by phase
- 🎫 **GitHub Issues** for each task (automatic creation)
- 🏷️ **Color-coded labels** for 6 implementation phases
- 📊 **Visual progress tracking** (53% complete: 16/30 tasks)
- 👥 **Team collaboration** (assignments, comments, discussions)

---

## 🔧 Installation (One-Time Setup)

### Step 1: Install GitHub CLI

**Windows (PowerShell as Administrator):**
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

### Step 2: Install jq (JSON processor)

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

### Step 3: Authenticate

```bash
gh auth login
```

Follow the prompts and login with web browser.

---

## 🏃 Running the Sync (2 Minutes)

### Windows (Git Bash):
```bash
cd "/c/Users/CUSTOM PC/Desktop/Cursor Builds/barton-outreach-core"
./infra/scripts/sync-svg-ple-to-github-projects.sh
```

### macOS/Linux:
```bash
cd ~/path/to/barton-outreach-core
./infra/scripts/sync-svg-ple-to-github-projects.sh
```

---

## 📊 What Happens

1. ✅ **Verifies prerequisites** (gh, jq, authentication)
2. ✅ **Creates project** "SVG-PLE Doctrine Alignment" (if needed)
3. ✅ **Parses markdown** `infra/docs/svg-ple-todo.md`
4. ✅ **Creates 30 GitHub Issues** (one per task)
5. ✅ **Adds color-coded labels** (6 phases)
6. ✅ **Links issues to project**
7. ✅ **Sets status** (Done vs Todo)

**Output includes project URL** — click to view your board!

---

## 🎯 Access Your Project

After sync completes, you'll see:

```
View project:
https://github.com/users/YOUR_USERNAME/projects/PROJECT_NUMBER
```

Click the link to access your kanban board!

---

## 📋 Project Structure

### 6 Phases (Color-Coded)

| Phase | Tasks | Status | Color |
|-------|-------|--------|-------|
| Phase 1: Environment | 4 | ✅ 100% | Blue |
| Phase 2: BIT Infrastructure | 5 | ✅ 100% | Purple |
| Phase 3: Enrichment Spoke | 4 | 🔄 80% | Blue |
| Phase 4: Renewal & PLE | 3 | 🔄 40% | Green |
| Phase 5: Grafana Dashboard | 6 | 🎯 0% (Next) | Orange |
| Phase 6: Verification & QA | 6 | 🔲 17% | Pink |

**Overall:** 53% complete (16/30 tasks)

---

## 💡 Using the Project

### View Tasks
- **Board View:** Drag-and-drop kanban
- **Table View:** Spreadsheet-style list
- **Roadmap View:** Timeline visualization

### Manage Tasks
- **Change Status:** Drag between columns or update Status field
- **Assign Tasks:** Click task → Assignees → Select member
- **Add Comments:** Discuss implementation details
- **Link PRs:** Connect pull requests to issues

### Filter & Sort
- **By Phase:** Filter by phase-1, phase-2, etc. labels
- **By Status:** Todo, In Progress, Done
- **By Assignee:** Show only your tasks

---

## 🔄 Keeping in Sync

### Option 1: Manual Re-sync (Recommended)

After updating `infra/docs/svg-ple-todo.md`:

```bash
./infra/scripts/sync-svg-ple-to-github-projects.sh
```

**Note:** Won't create duplicate issues.

### Option 2: GitHub Actions (Auto-sync)

Set up workflow to sync on push or schedule:

```yaml
# .github/workflows/sync-svg-ple.yml
name: Sync SVG-PLE
on:
  push:
    paths: ['infra/docs/svg-ple-todo.md']
  schedule:
    - cron: '0 8 * * *'  # Daily at 8am UTC

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: sudo apt-get install -y jq
      - run: ./infra/scripts/sync-svg-ple-to-github-projects.sh
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## 🐛 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| `gh` not found | Install GitHub CLI (see Step 1 above) |
| `jq` not found | Install jq (see Step 2 above) |
| Not authenticated | Run `gh auth login` |
| Permission denied | Run `chmod +x infra/scripts/sync-svg-ple-to-github-projects.sh` |
| Git Bash not found (Windows) | Install Git for Windows: `winget install --id Git.Git` |

**Full troubleshooting:** See `infra/docs/GITHUB_PROJECTS_SETUP.md`

---

## 📚 Full Documentation

- **To-Do Tracker:** `infra/docs/svg-ple-todo.md`
- **Setup Guide:** `infra/docs/GITHUB_PROJECTS_SETUP.md` (500+ lines)
- **Implementation Summary:** `infra/docs/SVG-PLE-TRACKER-COMPLETE.md`
- **Sync Script:** `infra/scripts/sync-svg-ple-to-github-projects.sh`

---

## ✅ You're Done!

**Next Steps:**
1. Click the project URL from script output
2. Explore the kanban board
3. Assign tasks to team members
4. Start tracking progress visually

**Current Priority:** Phase 5 — Import Grafana Dashboard

---

**Questions?** See full documentation in `infra/docs/GITHUB_PROJECTS_SETUP.md`
