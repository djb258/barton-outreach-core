<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ops/scripts
Barton ID: 07.02.01
Unique ID: CTB-POST-INSTALL
Blueprint Hash:
Last Updated: 2025-11-07
Enforcement: None
─────────────────────────────────────────────
-->

# 🚀 Post-Installation Configuration Guide

After running `setup-required-tools.bat`, follow these steps to complete the setup.

---

## ✅ Step 1: Verify Installations

**Close and reopen your terminal** to refresh PATH variables, then verify:

```bash
# Check Obsidian
obsidian --version

# Check GitKraken
gitkraken --version

# Check GitHub CLI
gh --version
```

If any command fails, the tool may need to be in your PATH. Try:
- Restarting your terminal/IDE
- Logging out and back in to Windows
- Manually adding tool paths to System Environment Variables

---

## 🔐 Step 2: Authenticate GitHub CLI

GitHub CLI needs authentication to access GitHub Projects:

```bash
# Start authentication flow
gh auth login

# Follow prompts:
# ? What account do you want to log into? GitHub.com
# ? What is your preferred protocol for Git operations? HTTPS
# ? Authenticate Git with your GitHub credentials? Yes
# ? How would you like to authenticate GitHub CLI? Login with a web browser
```

**Copy the one-time code** and press Enter to open your browser. Paste the code to complete authentication.

### Verify Authentication

```bash
# Check login status
gh auth status

# Test API access
gh repo view djb258/barton-outreach-core
```

---

## 📓 Step 3: Open Obsidian Vault

### First Launch

1. **Launch Obsidian** (Start Menu → Obsidian)
2. Click **"Open folder as vault"**
3. Navigate to your repository:
   ```
   C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\ctb\docs\obsidian-vault
   ```
4. Click **"Select Folder"**

### Enable Community Plugins

Obsidian will prompt about community plugins:

1. Click **"Turn on community plugins"**
2. Go to **Settings → Community Plugins → Browse**
3. Install these plugins:
   - **obsidian-git** - Auto-sync with Git
   - **dataview** - Query notes
   - **templater** - Dynamic templates
   - **table-editor-obsidian** - Enhanced tables
   - **obsidian-kanban** - Task boards

### Configure Git Plugin

1. Open **Settings → Community Plugins → Obsidian Git**
2. Set **Automatic backup interval**: `5` minutes
3. Enable **Auto pull on startup**
4. Enable **Auto push after commit**
5. Click **"Save"**

---

## 🎨 Step 4: Configure GitKraken

### First Launch

1. **Launch GitKraken** (Start Menu → GitKraken)
2. Sign in with GitHub account
3. Click **"Open a Repository"**
4. Navigate to:
   ```
   C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core
   ```
5. Click **"Open"**

### Recommended Settings

**View → Graph Settings:**
- Show all branches: ✅
- Show commit author: ✅
- Show commit date: ✅

**Preferences → UI Customization:**
- Theme: Dark (or your preference)
- Graph orientation: Vertical

### Using GitKraken for CTB

GitKraken makes CTB navigation visual:

- **All branches visible** at once (main + feature branches)
- **Drag & drop** to merge branches
- **Visual diff** for file changes
- **Commit graph** shows CTB history

---

## 🔗 Step 5: Set Up GitHub Projects Integration

### Create GitHub Project (if not exists)

Via GitHub Web:
1. Go to: https://github.com/djb258/barton-outreach-core
2. Click **"Projects"** tab
3. Click **"New project"**
4. Select **"Board"** view
5. Name: **"Barton Outreach Core"**
6. Click **"Create project"**

Via GitHub CLI:
```bash
# List existing projects
gh project list --owner djb258

# Create new project (if needed)
gh project create --owner djb258 --title "Barton Outreach Core"
```

### Configure Environment Variables

Add to your `.env` file:

```bash
# GitHub Projects Integration
GITHUB_TOKEN=<your_github_token>
GITHUB_PROJECT_ID=<your_project_id>
GITHUB_REPO_OWNER=djb258
GITHUB_REPO_NAME=barton-outreach-core
```

**Get your GitHub token:**
```bash
# GitHub CLI will use your authenticated token
gh auth token
```

**Find your project ID:**
```bash
# List projects and copy the ID
gh project list --owner djb258 --format json
```

### Run First Sync

```bash
# One-time sync
bash infra/scripts/auto-sync-svg-ple-github.sh --once

# Or watch mode (continuous sync)
bash infra/scripts/auto-sync-svg-ple-github.sh --watch
```

---

## 📊 Step 6: Verify Everything Works

### Test Obsidian
1. Create a new note: `Ctrl+N`
2. Type: `# Test Note - [[AGENT_GUIDE]]`
3. Press `Ctrl+click` on the link - should open AGENT_GUIDE.md
4. Wait 5 minutes - Git plugin should auto-commit

### Test GitKraken
1. Open GitKraken
2. View commit history - should see today's commits
3. Check all branches - should see main + feature branches
4. Click on a commit - should see file changes

### Test GitHub CLI
```bash
# View repository
gh repo view djb258/barton-outreach-core

# List recent issues
gh issue list --limit 5

# Check project status
gh project list --owner djb258
```

---

## 🎯 Daily Workflow

### Morning Routine
1. **Open Obsidian** - Review yesterday's notes
2. **Open GitKraken** - Check new commits
3. **Run sync script** - Update GitHub Projects

### During Development
1. **Make code changes** - Use your IDE
2. **Document in Obsidian** - Add notes/architecture docs
3. **Commit via Git** - GitKraken or command line
4. **Auto-sync runs** - GitHub Projects updates automatically

### End of Day
1. **Review in GitKraken** - Check all commits
2. **Update Obsidian** - Daily summary note
3. **Check GitHub Projects** - Verify task status

---

## 🆘 Troubleshooting

### Obsidian: Git plugin not working
```bash
# Check Git is installed
git --version

# Check repository status
cd ctb/docs/obsidian-vault
git status
```

### GitKraken: Repository not loading
- Ensure you're opening the **root directory** (barton-outreach-core)
- Not a subdirectory like `ctb/`

### GitHub CLI: Authentication failed
```bash
# Re-authenticate
gh auth logout
gh auth login

# Check status
gh auth status
```

### Sync script: Permission denied
```bash
# Make script executable
chmod +x infra/scripts/auto-sync-svg-ple-github.sh

# Or run with bash explicitly
bash infra/scripts/auto-sync-svg-ple-github.sh --once
```

---

## 📚 Additional Resources

### Obsidian
- **Vault README**: `ctb/docs/obsidian-vault/README.md`
- **Templates**: `ctb/docs/obsidian-vault/templates/`
- **Help**: https://help.obsidian.md/

### GitKraken
- **Keyboard Shortcuts**: Press `?` in GitKraken
- **Documentation**: https://help.gitkraken.com/

### GitHub Projects
- **Project README**: `ctb/sys/github-projects/README.md`
- **Automation Rules**: `ctb/sys/github-projects/automation-rules.json`
- **API Docs**: https://docs.github.com/en/graphql

---

## ✅ Success Checklist

Before you start working, verify:

- [ ] Obsidian vault opens correctly
- [ ] Obsidian Git plugin is auto-committing
- [ ] GitKraken shows repository with all branches
- [ ] GitHub CLI is authenticated (`gh auth status`)
- [ ] Sync script runs without errors
- [ ] GitHub Projects shows recent commits
- [ ] All tools in PATH (`obsidian --version`, `gh --version`, `gitkraken --version`)

---

**Created**: 2025-11-07
**CTB Branch**: ops/scripts
**Barton ID**: 07.02.01

If you encounter issues not covered here, check:
- `CLAUDE.md` (root) - Bootstrap guide
- `TROUBLESHOOTING.md` - Common issues
- `required_tools.yaml` - Tool specifications
