# GitHub Projects Integration Setup — SVG-PLE Tracker

Complete setup guide for syncing the SVG-PLE implementation tracker with GitHub Projects.

---

## 📋 Overview

This integration automatically syncs tasks from `infra/docs/svg-ple-todo.md` to a GitHub Projects board for better project management and team collaboration.

**Features:**
- ✅ Auto-create GitHub Issues for each task
- ✅ Organize tasks by phase with color-coded labels
- ✅ Track completion status (Todo vs Done)
- ✅ Maintain sync between markdown file and GitHub Projects
- ✅ Support for team collaboration and assignments

---

## 🔧 Prerequisites

### 1. GitHub CLI (gh)

The GitHub CLI is required to interact with GitHub Projects programmatically.

#### Installation

**Windows (PowerShell as Administrator):**
```powershell
winget install --id GitHub.cli
```

**macOS:**
```bash
brew install gh
```

**Linux (Debian/Ubuntu):**
```bash
type -p curl >/dev/null || (sudo apt update && sudo apt install curl -y)
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh -y
```

**Other Linux distributions:**
See [GitHub CLI installation docs](https://github.com/cli/cli/blob/trunk/docs/install_linux.md)

#### Verify Installation
```bash
gh --version
```

Expected output:
```
gh version 2.x.x (xxxx-xx-xx)
```

### 2. jq (JSON processor)

Required for parsing JSON responses from GitHub API.

**Windows (PowerShell as Administrator):**
```powershell
winget install jqlang.jq
```

**macOS:**
```bash
brew install jq
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt-get install jq
```

#### Verify Installation
```bash
jq --version
```

Expected output:
```
jq-1.x
```

### 3. Git Bash (Windows Only)

If you're on Windows, you'll need Git Bash to run the bash script.

**Installation:**
```powershell
winget install --id Git.Git
```

Or download from [git-scm.com](https://git-scm.com/download/win)

---

## 🔑 Authentication

### Step 1: Authenticate with GitHub CLI

```bash
gh auth login
```

**Follow the prompts:**
1. **What account do you want to log into?** → `GitHub.com`
2. **What is your preferred protocol for Git operations?** → `HTTPS` or `SSH`
3. **Authenticate GitHub CLI with your GitHub credentials?** → `Login with a web browser`
4. Copy the one-time code shown
5. Press Enter to open browser
6. Paste the code in the browser
7. Click "Authorize gh"

### Step 2: Verify Authentication

```bash
gh auth status
```

Expected output:
```
github.com
  ✓ Logged in to github.com as YOUR_USERNAME (/path/to/config.yml)
  ✓ Git operations for github.com configured to use https protocol.
  ✓ Token: *******************
```

### Step 3: Set Repository Context

Navigate to your repository:
```bash
cd /path/to/barton-outreach-core
```

Verify GitHub recognizes the repo:
```bash
gh repo view
```

---

## 🚀 Running the Sync Script

### Method 1: Using Git Bash (Recommended for Windows)

1. **Open Git Bash** (not PowerShell or CMD)
2. **Navigate to repository:**
   ```bash
   cd /c/Users/CUSTOM\ PC/Desktop/Cursor\ Builds/barton-outreach-core
   ```

3. **Run the sync script:**
   ```bash
   ./infra/scripts/sync-svg-ple-to-github-projects.sh
   ```

### Method 2: Using WSL (Windows Subsystem for Linux)

1. **Open WSL terminal**
2. **Navigate to repository:**
   ```bash
   cd /mnt/c/Users/CUSTOM\ PC/Desktop/Cursor\ Builds/barton-outreach-core
   ```

3. **Run the sync script:**
   ```bash
   ./infra/scripts/sync-svg-ple-to-github-projects.sh
   ```

### Method 3: Using macOS/Linux Terminal

1. **Open Terminal**
2. **Navigate to repository:**
   ```bash
   cd ~/path/to/barton-outreach-core
   ```

3. **Run the sync script:**
   ```bash
   ./infra/scripts/sync-svg-ple-to-github-projects.sh
   ```

---

## 📊 What the Script Does

### Step 1: Pre-flight Checks
- ✅ Verifies `gh` CLI is installed
- ✅ Verifies `jq` is installed
- ✅ Checks GitHub authentication status
- ✅ Validates repository context
- ✅ Confirms `svg-ple-todo.md` exists

### Step 2: Find or Create Project
- 🔍 Searches for existing project named "SVG-PLE Doctrine Alignment"
- 🆕 Creates new project if not found
- 📌 Retrieves project ID for subsequent operations

### Step 3: Parse Tasks
- 📝 Reads `infra/docs/svg-ple-todo.md`
- 🔍 Extracts all tasks (lines starting with `- [ ]` or `- [x]`)
- 📊 Counts completed vs pending tasks

### Step 4: Create Issues
- 🎫 Creates GitHub Issue for each task (if not already exists)
- 🏷️ Adds labels: `svg-ple`, `automation`
- 📋 Links issues to the GitHub Project
- ✅ Sets status based on checkbox state (Done vs Todo)

### Step 5: Create Phase Labels
- 🎨 Creates color-coded labels for each phase:
  - `phase-1` (Environment) - Blue (#0052CC)
  - `phase-2` (BIT Infrastructure) - Purple (#5319E7)
  - `phase-3` (Enrichment Spoke) - Blue (#1D76DB)
  - `phase-4` (Renewal & PLE) - Green (#0E8A16)
  - `phase-5` (Grafana Dashboard) - Orange (#D93F0B)
  - `phase-6` (Verification & QA) - Pink (#E99695)

### Step 6: Summary
- 📊 Displays statistics (total tasks, completed, pending)
- 🔗 Provides links to project and issues
- ✅ Confirms successful sync

---

## 📋 Expected Output

```
═══════════════════════════════════════════════════════════
  SVG-PLE TO-DO TRACKER → GITHUB PROJECTS SYNC
═══════════════════════════════════════════════════════════

🔍 Running pre-flight checks...
✅ GitHub CLI installed
✅ jq installed
✅ Authenticated with GitHub
✅ To-do file found
✅ Repository: your-username/barton-outreach-core

📋 Checking for existing project...
✅ Found existing project #1

Project ID: PVT_kwDOAbCdEfg12345

📝 Parsing to-do file...
  [Done] Install & connect Grafana to Neon
    ✅ Created issue #101 and added to project
  [Done] Validate schemas (company, people, marketing, bit, intake, vault, ple)
    ✅ Created issue #102 and added to project
  [Todo] Import svg-ple-dashboard.json
    ✅ Created issue #103 and added to project
  ...

✅ Processed 30 tasks
   • Completed: 16
   • Pending: 14

🏷️  Creating phase labels...
  ✅ Created label: phase-1
  ✅ Created label: phase-2
  ...

═══════════════════════════════════════════════════════════
  ✅ SYNC COMPLETE
═══════════════════════════════════════════════════════════

Project: SVG-PLE Doctrine Alignment
Project Number: #1
Repository: your-username/barton-outreach-core
Tasks Processed: 30
  • Completed: 16
  • Pending: 14

View project:
https://github.com/users/your-username/projects/1

View issues:
https://github.com/your-username/barton-outreach-core/issues?q=label%3Asvg-ple

💡 TIP: You can manually update issue status in GitHub Projects UI
   and it will be reflected across all views.
```

---

## 🎯 Using GitHub Projects

### Accessing the Project

1. **Via Script Output:**
   - Click the project URL provided in the script output
   - Example: `https://github.com/users/YOUR_USERNAME/projects/1`

2. **Via GitHub UI:**
   - Navigate to your profile or repository
   - Click "Projects" tab
   - Select "SVG-PLE Doctrine Alignment"

### Managing Tasks

#### Change Task Status
1. Drag tasks between columns (Todo, In Progress, Done)
2. Or click task → Change "Status" field
3. Status updates are visible to all team members

#### Assign Tasks
1. Click task card
2. Click "Assignees"
3. Select team member(s)

#### Add Labels
1. Click task card
2. Click "Labels"
3. Add phase labels or custom labels

#### Set Priority
1. Click task card
2. Add "Priority" field (if not exists)
3. Set as High, Medium, or Low

#### Add Milestone
1. Click task card
2. Link to repository milestone
3. Track progress toward milestone goals

---

## 🔄 Keeping in Sync

### Option 1: Manual Re-sync (Recommended)

After updating `svg-ple-todo.md`, re-run the script:

```bash
./infra/scripts/sync-svg-ple-to-github-projects.sh
```

**Note:** The script is idempotent — it won't create duplicate issues if they already exist.

### Option 2: Scheduled Sync (Advanced)

Set up a GitHub Actions workflow to auto-sync on schedule or on push.

**Example:** `.github/workflows/sync-svg-ple.yml`

```yaml
name: Sync SVG-PLE Tracker

on:
  push:
    paths:
      - 'infra/docs/svg-ple-todo.md'
  schedule:
    - cron: '0 8 * * *'  # Daily at 8am UTC
  workflow_dispatch:  # Manual trigger

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install jq
        run: sudo apt-get install -y jq

      - name: Run Sync Script
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          chmod +x infra/scripts/sync-svg-ple-to-github-projects.sh
          ./infra/scripts/sync-svg-ple-to-github-projects.sh
```

---

## 🐛 Troubleshooting

### Issue: "GitHub CLI (gh) is not installed"

**Solution:**
```bash
# Windows
winget install --id GitHub.cli

# macOS
brew install gh

# Linux
# See installation instructions above
```

### Issue: "jq is not installed"

**Solution:**
```bash
# Windows
winget install jqlang.jq

# macOS
brew install jq

# Linux
sudo apt-get install jq
```

### Issue: "Not authenticated with GitHub CLI"

**Solution:**
```bash
gh auth login
# Follow the prompts
```

### Issue: "To-do file not found"

**Solution:**
- Ensure you're in the repository root directory
- Verify file exists: `ls infra/docs/svg-ple-todo.md`
- Run script from repository root

### Issue: "Permission denied" when running script

**Solution:**
```bash
chmod +x infra/scripts/sync-svg-ple-to-github-projects.sh
```

### Issue: "Failed to create project"

**Possible causes:**
1. Insufficient permissions (need write access to repo)
2. Project already exists under different owner
3. GitHub API rate limit reached

**Solution:**
```bash
# Check permissions
gh repo view --json permissions

# Check existing projects
gh project list --owner YOUR_USERNAME --limit 100

# Check rate limit
gh api rate_limit
```

### Issue: Git Bash not recognized on Windows

**Solution:**
1. Install Git for Windows: `winget install --id Git.Git`
2. Restart terminal
3. Or use full path: `"C:\Program Files\Git\bin\bash.exe" ./infra/scripts/sync-svg-ple-to-github-projects.sh`

---

## 📚 Additional Resources

### GitHub CLI Documentation
- [Official GitHub CLI Docs](https://cli.github.com/manual/)
- [GitHub CLI Repository](https://github.com/cli/cli)
- [GitHub Projects CLI Commands](https://cli.github.com/manual/gh_project)

### GitHub Projects Documentation
- [About Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects)
- [Creating a Project](https://docs.github.com/en/issues/planning-and-tracking-with-projects/creating-projects/creating-a-project)
- [Managing Items in Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/managing-items-in-your-project)

### Related Documentation (This Repo)
- **To-Do Tracker:** `infra/docs/svg-ple-todo.md`
- **Implementation Summary:** `infra/SVG-PLE-IMPLEMENTATION-SUMMARY.md`
- **Grafana Setup:** `grafana/README.md`
- **Schema Reference:** `SCHEMA_QUICK_REFERENCE.md`

---

## 🎯 Next Steps

After setup is complete:

1. ✅ **Run the sync script** to create initial project
2. ✅ **Access GitHub Projects** via the provided URL
3. ✅ **Customize project views** (add columns, filters, grouping)
4. ✅ **Assign tasks** to team members
5. ✅ **Update task statuses** as work progresses
6. ✅ **Re-run sync script** when `svg-ple-todo.md` is updated

---

## 💡 Tips & Best Practices

### For Solo Development
- Use the markdown file as source of truth
- Sync to GitHub Projects for visual progress tracking
- Re-run sync script after updating markdown

### For Team Collaboration
- Use GitHub Projects as primary interface
- Update task statuses in Projects UI (not markdown)
- Assign tasks to team members
- Use comments on issues for discussions
- Link pull requests to issues

### For Project Management
- Create custom fields (Sprint, Priority, Estimate)
- Use project views to filter by phase or status
- Set up project insights for progress tracking
- Create milestones for major releases

---

**Last Updated:** 2025-11-06
**Script Version:** 1.0.0
**GitHub CLI Version:** 2.x+
**Status:** Production-Ready
