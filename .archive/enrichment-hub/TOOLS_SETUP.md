# Project Tools Setup Guide

This guide will help you set up and use Obsidian, GitKraken, and Git for the enricha-vision project.

## Quick Installation

### Windows

**Option 1: PowerShell (Recommended)**
```powershell
# Run as Administrator
powershell -ExecutionPolicy Bypass -File install-tools.ps1
```

**Option 2: Batch File**
```batch
# Run as Administrator
install-tools.bat
```

### macOS / Linux

```bash
chmod +x install-tools.sh
./install-tools.sh
```

## Manual Installation

If automatic installation doesn't work, install tools manually:

### Git
- **Windows**: https://git-scm.com/download/win
- **macOS**: `brew install git`
- **Linux**: `sudo apt-get install git`

### Obsidian
- **All Platforms**: https://obsidian.md/download

### GitKraken
- **All Platforms**: https://www.gitkraken.com/download

### Node.js
- **All Platforms**: https://nodejs.org/

## Tool Configuration

### 1. Git Setup

After installation, configure Git:

```bash
# Set your identity
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Configure default branch name
git config --global init.defaultBranch main

# Enable credential caching
git config --global credential.helper cache

# Use VS Code as default editor (optional)
git config --global core.editor "code --wait"
```

**Initialize the repository** (if not already done):
```bash
git init
git remote add origin https://github.com/djb258/enricha-vision.git
```

### 2. Obsidian Setup

**Open Vault:**
1. Launch Obsidian
2. Click "Open folder as vault"
3. Select the `enricha-vision` directory
4. The vault is pre-configured with CTB documentation

**Recommended Plugins:**
- **Git**: Auto-commit and sync
- **Dataview**: Query and display data
- **Kanban**: Project management boards
- **Calendar**: Daily notes and timeline
- **Advanced Tables**: Better Markdown tables
- **Templater**: Advanced templating

**Install Plugins:**
1. Settings → Community plugins
2. Turn off Safe mode
3. Browse and install plugins

**Vault Structure:**
```
enricha-vision/
├── CTB_README.md          # Main CTB documentation
├── ENV_SETUP.md           # Environment setup
├── SECURITY.md            # Security policies
├── ctb/
│   └── docs/              # All documentation
│       ├── api/           # API docs
│       ├── architecture/  # System architecture
│       ├── guides/        # How-to guides
│       ├── tutorials/     # Tutorials
│       └── templates/     # Note templates
```

**Using Templates:**
1. Create new note
2. Use command palette (Ctrl/Cmd + P)
3. Select "Templates: Insert template"
4. Choose from:
   - Feature documentation
   - Bug reports
   - Meeting notes

### 3. GitKraken Setup

**Open Repository:**
1. Launch GitKraken
2. File → Open Repo
3. Select `enricha-vision` directory

**Connect GitHub:**
1. Preferences → Integrations
2. Connect GitHub account
3. Authenticate with GitHub

**Configure Preferences:**
- **Profile**: Use "CTB Development" profile
- **Commit Template**: Pre-filled with conventional format
- **Auto-fetch**: Enabled (every 5 minutes)
- **Auto-prune**: Enabled

**GitFlow:**
GitKraken is pre-configured with GitFlow:
- Main branch: `main`
- Development branch: `develop`
- Feature prefix: `feature/`
- Bugfix prefix: `bugfix/`
- Hotfix prefix: `hotfix/`

**Using GitFlow in GitKraken:**
1. Click GitFlow icon in toolbar
2. Initialize GitFlow (if needed)
3. Start feature: GitFlow → Start Feature
4. Finish feature: GitFlow → Finish Feature

## Git Workflow

### Branch Naming Conventions

```
feature/feature-name      # New features
bugfix/issue-description  # Bug fixes
hotfix/critical-fix       # Urgent fixes
ctb/component-update      # CTB system updates
docs/documentation-update # Documentation changes
```

### Commit Message Format

Follow Conventional Commits:

```
type(scope): description

feat(auth): add OAuth2 login support
fix(ui): resolve button alignment issue
docs: update installation guide
ctb(sys): add new integration config
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style/formatting
- `refactor`: Code refactoring
- `test`: Tests
- `chore`: Maintenance
- `ctb`: CTB system changes
- `perf`: Performance
- `ci`: CI/CD changes

### Git Hooks

The project has automated hooks:

**Pre-commit:**
- ✅ Checks for exposed secrets
- ✅ Prevents committing .env files
- ✅ Warns about large files
- ✅ Runs linting

**Commit-msg:**
- ✅ Validates commit message format
- ✅ Enforces conventional commits

**Pre-push:**
- ✅ Warns when pushing to main
- ✅ Runs tests (if available)
- ✅ Checks CTB compliance

## Integrated Workflow

### Daily Development Flow

1. **Start your day:**
   ```bash
   git checkout develop
   git pull origin develop
   ```

2. **Create feature branch:**
   - In GitKraken: GitFlow → Start Feature
   - Or CLI: `git checkout -b feature/your-feature`

3. **Document in Obsidian:**
   - Create feature doc from template
   - Document requirements and design
   - Track progress

4. **Develop & Commit:**
   ```bash
   git add .
   git commit -m "feat(component): add new functionality"
   ```

5. **Push & Create PR:**
   - In GitKraken: Push button
   - Create pull request on GitHub
   - Link to Obsidian documentation

6. **Review & Merge:**
   - Code review in GitHub
   - Merge when approved
   - Update documentation

### Using Obsidian for Project Management

**Create Kanban Board:**
1. Create new note: `Project Board.md`
2. Add frontmatter:
   ```yaml
   ---
   kanban-plugin: basic
   ---
   ```
3. Create columns: To Do, In Progress, Done
4. Add cards as tasks

**Daily Notes:**
1. Enable Daily Notes plugin
2. Use for:
   - Daily standup notes
   - Progress tracking
   - Blockers and issues

**Link Everything:**
- Link code commits to docs: `[[Feature Documentation]]`
- Link issues to notes: `#123` or `[[Bug Report - Issue 123]]`
- Create knowledge graph

### GitKraken Tips

**Visual History:**
- See full commit graph
- Understand branch relationships
- Identify merge conflicts early

**Interactive Rebase:**
- Right-click commit → Interactive Rebase
- Squash commits before PR
- Keep history clean

**WIP Nodes:**
- Temporary save of work
- Quickly switch branches
- No commit needed

**File Blame:**
- Right-click file → Blame
- See who changed what
- Understand code history

**GitHub Integration:**
- View PRs in GitKraken
- See CI/CD status
- Review code inline

## Troubleshooting

### Git Hooks Not Running

**Windows:**
```powershell
# Ensure hooks are executable
icacls .git\hooks\* /grant:r %USERNAME%:F
```

**macOS/Linux:**
```bash
chmod +x .git/hooks/*
```

### Obsidian Vault Issues

**Vault not loading:**
1. Check .obsidian folder exists
2. Verify folder permissions
3. Try "Open another vault" → "Open folder as vault"

**Plugins not working:**
1. Settings → Community plugins
2. Disable Safe mode
3. Reload plugin

### GitKraken Connection Issues

**GitHub authentication failed:**
1. Preferences → Integrations
2. Disconnect GitHub
3. Reconnect and re-authenticate

**Repository not loading:**
1. Check .git folder exists
2. Verify Git is installed
3. Try "Open Repo" again

## Advanced Tips

### Obsidian + Git Auto-Sync

Install Obsidian Git plugin:
1. Auto-commits every X minutes
2. Syncs with remote
3. Keeps documentation backed up

### GitKraken + GitHub Actions

View CI/CD in GitKraken:
1. Pull Requests tab
2. See checks status
3. View workflow results

### Git Aliases

Add useful aliases to `.gitconfig`:
```bash
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.unstage 'reset HEAD --'
git config --global alias.visual 'log --graph --oneline --decorate --all'
```

## Resources

### Documentation
- Git: https://git-scm.com/doc
- Obsidian: https://help.obsidian.md/
- GitKraken: https://help.gitkraken.com/

### Tutorials
- Git basics: https://www.atlassian.com/git/tutorials
- Obsidian guide: https://www.youtube.com/c/Obsidian
- GitKraken guide: https://www.gitkraken.com/learn

### CTB Documentation
- See `ctb/docs/` for project-specific guides
- Read `CTB_README.md` for CTB overview
- Check `ENV_SETUP.md` for environment setup

## Support

Having issues? Check:
1. This guide's troubleshooting section
2. Tool-specific documentation
3. GitHub issues
4. Project maintainers

---

**Happy developing with your new tools!** 🚀
