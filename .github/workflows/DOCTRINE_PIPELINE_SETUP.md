# Doctrine Pipeline Sync - Setup Guide

**Version**: 1.0.0
**Last Updated**: 2025-11-07
**Workflow File**: `.github/workflows/doctrine-project-sync.yml`

---

## 📋 Overview

The **Doctrine Pipeline Sync** workflow automatically creates GitHub Issues whenever doctrine files are modified, providing a visual Kanban board of all doctrine changes in your repository.

**What It Does**:
- ✅ Monitors changes to doctrine files (`.md`, `.sql`, `.mmd`)
- ✅ Creates GitHub Issue with detailed change summary
- ✅ Adds labels for easy filtering (`doctrine`, `auto-sync`, `documentation`)
- ✅ Assigns issue to the person who made the changes
- ✅ Adds issue to "Doctrine Pipeline" project board
- ✅ Provides links to changed files and commit diff

---

## 🚀 Setup Instructions

### Step 1: Create GitHub Project Board

**Option A: Organization Project** (Recommended for teams)

1. Go to your GitHub organization page
2. Click "Projects" tab → "New Project"
3. Name: `Doctrine Pipeline`
4. Template: Choose "Board" (Kanban-style)
5. Create columns:
   - 📥 **To Review** (default)
   - 🔍 **In Review**
   - ✅ **Verified**
   - 🚀 **Deployed**

**Option B: Repository Project** (For single repo)

1. Go to your repository → "Projects" tab
2. Click "Link a project" → "New Project"
3. Name: `Doctrine Pipeline`
4. Template: Choose "Board"
5. Create columns as above

**Note**: Update workflow file line 170 if using repository project:
```yaml
# Change this line:
project-url: https://github.com/orgs/${{ github.repository_owner }}/projects/1

# To this:
project-url: https://github.com/users/${{ github.repository_owner }}/projects/1
```

---

### Step 2: Configure Repository Permissions

**Enable Workflow Permissions**:

1. Go to repository Settings
2. Navigate to: Actions → General
3. Scroll to "Workflow permissions"
4. Select: **"Read and write permissions"**
5. Check: ✅ "Allow GitHub Actions to create and approve pull requests"
6. Click "Save"

**Why This Is Needed**:
- Workflow needs to create issues (`issues: write`)
- Workflow needs to add issues to project board (`projects: write`)
- Workflow needs to read commit history (`contents: read`)

---

### Step 3: Verify Workflow File

**Check File Location**:
```bash
# File must be at this exact path:
.github/workflows/doctrine-project-sync.yml
```

**Verify YAML Syntax**:
```bash
# Install yamllint (optional)
pip install yamllint

# Check syntax
yamllint .github/workflows/doctrine-project-sync.yml
```

Or use online: https://www.yamllint.com/

---

### Step 4: Test the Workflow

**Method 1: Push a Doctrine Change**

```bash
# Make a small change to any doctrine file
echo "" >> doctrine/README.md

# Commit and push
git add doctrine/README.md
git commit -m "test: trigger doctrine pipeline workflow"
git push origin main
```

**Method 2: Manual Workflow Trigger** (if enabled)

1. Go to repository → Actions tab
2. Select "Doctrine Pipeline Sync" workflow
3. Click "Run workflow" button
4. Select branch → "Run workflow"

**What Should Happen**:
1. Workflow runs (visible in Actions tab)
2. New issue created: "Doctrine Update #1 – 1 file(s) changed"
3. Issue has labels: `doctrine`, `auto-sync`, `documentation`
4. Issue appears in "Doctrine Pipeline" project board
5. Issue is assigned to you (the pusher)

---

### Step 5: Verify Integration

**Check GitHub Issue**:
- [ ] Issue created with title "Doctrine Update #X"
- [ ] Issue body contains list of changed files
- [ ] Issue has correct labels
- [ ] Issue assigned to committer
- [ ] Links to files are working

**Check Project Board**:
- [ ] Issue appears in "To Review" column
- [ ] Can drag issue between columns
- [ ] Issue links back to commit

**Check Actions Log**:
- [ ] Workflow shows green checkmark
- [ ] All steps completed successfully
- [ ] Summary shows file count and issue number

---

## 🔧 Configuration Options

### Customize Triggers

**Watch Additional Branches**:
```yaml
on:
  push:
    branches:
      - main
      - master
      - develop
      - feature/**  # Watch all feature branches
    paths:
      - 'doctrine/**/*.md'
      - 'doctrine/**/*.sql'
      - 'doctrine/**/*.mmd'
```

**Watch Additional File Types**:
```yaml
on:
  push:
    paths:
      - 'doctrine/**/*.md'
      - 'doctrine/**/*.sql'
      - 'doctrine/**/*.mmd'
      - 'doctrine/**/*.json'  # Add JSON
      - 'doctrine/**/*.yaml'  # Add YAML
```

### Customize Labels

**Change Labels** (line 158):
```yaml
labels: |
  doctrine
  auto-sync
  documentation
  high-priority  # Add additional label
```

### Customize Issue Template

**Modify Summary Generation** (line 83-125):
- Add more sections to the summary
- Include commit author, date, time
- Add links to Grafana dashboards
- Include compliance checklist

### Customize Project Board

**Change Project URL** (line 170):
```yaml
# For organization project (default):
project-url: https://github.com/orgs/YOUR-ORG/projects/PROJECT-NUMBER

# For user project:
project-url: https://github.com/users/YOUR-USERNAME/projects/PROJECT-NUMBER

# For repository project:
project-url: https://github.com/YOUR-ORG/YOUR-REPO/projects/PROJECT-NUMBER
```

**Find Project Number**:
1. Go to your project board
2. Look at URL: `https://github.com/orgs/YOUR-ORG/projects/5`
3. Project number is `5`

---

## 📊 Workflow Integration

### Integration with Other Tools

```
┌─────────────────────────────────────────────────────────────┐
│                  Doctrine Editing Workflow                   │
└─────────────────────────────────────────────────────────────┘

1. Edit Doctrine (Obsidian)
   ↓
2. Auto-Commit (Obsidian Git)
   ↓
3. Push to GitHub (automatic)
   ↓
4. Trigger Workflow (GitHub Actions)
   ↓
5. Create Issue (GitHub)
   ↓
6. Add to Project Board (GitHub Projects)
   ↓
7. Team Review (Kanban workflow)
   ↓
8. Close Issue (after verification)
```

### Dashboard Visibility

**Obsidian Dashboard**:
- Open tasks show in DOCTRINE_DASHBOARD.md
- Dataview queries list open issues
- Links to GitHub Project board

**GitHub Projects**:
- Kanban board shows all doctrine changes
- Drag cards between columns (Review → Verified)
- Filter by label, assignee, date

**Grafana**:
- Monitor doctrine update frequency
- Track time to verification
- Alert if changes not reviewed within 24h

---

## 🐛 Troubleshooting

### Issue: Workflow Not Triggering

**Symptoms**: No workflow run appears in Actions tab

**Solutions**:
1. Check file path: `.github/workflows/doctrine-project-sync.yml` (exact path)
2. Check branch: Workflow only runs on `main`, `master`, `develop`
3. Check file types: Only `.md`, `.sql`, `.mmd` in `doctrine/` directory
4. Check YAML syntax: Use https://www.yamllint.com/
5. Check Actions enabled: Settings → Actions → "Allow all actions"

### Issue: No Issue Created

**Symptoms**: Workflow runs but no issue appears

**Solutions**:
1. Check permissions: Settings → Actions → "Read and write permissions"
2. Check step log: Actions tab → Workflow run → "Create doctrine tracking issue"
3. Check GITHUB_TOKEN: Should be automatic, no manual setup needed
4. Check if issue limit reached: Repositories have rate limits

### Issue: Issue Not Added to Project

**Symptoms**: Issue created but not on project board

**Solutions**:
1. Verify project exists: Name must be exactly "Doctrine Pipeline"
2. Check project URL: Update line 170 with correct project number
3. Check project permissions: Settings → Projects → "Allow actions"
4. Manually add first issue: This sets up the connection
5. Check labels: Workflow adds issue by `doctrine` label

### Issue: Permission Denied

**Symptoms**: Workflow fails with "Resource not accessible by integration"

**Solutions**:
1. Enable write permissions: Settings → Actions → Workflow permissions → "Read and write"
2. Check token scopes: GITHUB_TOKEN needs `issues:write`, `projects:write`
3. Check branch protection: Protected branches may block workflow
4. Check organization settings: Org may restrict Actions permissions

### Issue: Duplicate Issues Created

**Symptoms**: Multiple issues for same commit

**Solutions**:
1. Check workflow triggers: Should not trigger on same commit twice
2. Check if manually re-running: Don't manually re-run for same commit
3. Add deduplication: Check existing issues before creating

---

## 📈 Usage Examples

### Example 1: Update BIT Doctrine

**Scenario**: You update BIT scoring logic

```bash
# Edit doctrine
vim doctrine/ple/BIT-Doctrine.md

# Obsidian Git auto-commits (or manual)
git add doctrine/ple/BIT-Doctrine.md
git commit -m "docs(doctrine): update BIT scoring weights"
git push origin main
```

**Result**:
- ✅ Workflow triggers
- ✅ Issue created: "Doctrine Update #42 – 1 file(s) changed"
- ✅ Issue lists: `doctrine/ple/BIT-Doctrine.md`
- ✅ Issue added to "To Review" column
- ✅ Assigned to you

**Workflow**:
1. Team reviews changes in issue
2. Verifies Barton ID compliance
3. Tests BIT schema in Neon
4. Moves issue to "Verified" column
5. Closes issue

---

### Example 2: Create New Spoke Doctrine

**Scenario**: You create Renewal Intelligence doctrine

```bash
# Create new doctrine
touch doctrine/ple/Renewal-Doctrine.md
touch doctrine/schemas/renewal-schema.sql

# Edit files...

# Commit both files
git add doctrine/ple/Renewal-Doctrine.md doctrine/schemas/renewal-schema.sql
git commit -m "feat(doctrine): add Renewal Intelligence spoke"
git push origin main
```

**Result**:
- ✅ Workflow triggers
- ✅ Issue created: "Doctrine Update #43 – 2 file(s) changed"
- ✅ Issue lists both files
- ✅ Issue added to "To Review" column
- ✅ Assigned to you

**Workflow**:
1. Team reviews new spoke design
2. Validates schema against Barton Doctrine
3. Tests schema in Neon (staging)
4. Updates PLE-Doctrine.md with cross-references
5. Moves issue to "Verified" column
6. Deploys schema to production
7. Closes issue

---

### Example 3: Bulk Doctrine Update

**Scenario**: You update multiple doctrines after compliance audit

```bash
# Update multiple files
vim doctrine/ple/PLE-Doctrine.md
vim doctrine/ple/BIT-Doctrine.md
vim doctrine/ple/Talent-Flow-Doctrine.md

# Commit all changes
git add doctrine/ple/*.md
git commit -m "docs(doctrine): monthly compliance audit updates"
git push origin main
```

**Result**:
- ✅ Workflow triggers
- ✅ Issue created: "Doctrine Update #44 – 3 file(s) changed"
- ✅ Issue lists all 3 files
- ✅ Issue added to "To Review" column
- ✅ Assigned to you

**Workflow**:
1. Team reviews all compliance changes
2. Verifies audit requirements met
3. Cross-checks against FINAL_AUDIT_SUMMARY.md
4. Moves issue to "Verified" column
5. Updates compliance status in global-config.yaml
6. Closes issue

---

## 📚 Related Documentation

### Workflow Files

- **Workflow**: `.github/workflows/doctrine-project-sync.yml`
- **Setup Guide**: `.github/workflows/DOCTRINE_PIPELINE_SETUP.md` (this file)

### Doctrine Documentation

- **Dashboard**: `doctrine/DOCTRINE_DASHBOARD.md`
- **Index**: `doctrine/README.md`
- **Master Doctrine**: `doctrine/ple/PLE-Doctrine.md`

### Obsidian Integration

- **Plugin Setup**: `.obsidian/plugins-setup.md`
- **Git Sync**: Configured to auto-commit every 10 minutes
- **Dataview**: Auto-lists open doctrine tasks

### GitHub Projects

- **Board**: "Doctrine Pipeline" (create this manually)
- **Columns**: To Review → In Review → Verified → Deployed
- **Filters**: Filter by label, assignee, milestone

---

## 🔄 Maintenance

### Monthly Tasks

- [ ] Review closed issues (verify all changes deployed)
- [ ] Check workflow success rate (should be 95%+)
- [ ] Update project board columns if needed
- [ ] Audit doctrine change frequency

### Quarterly Tasks

- [ ] Review workflow configuration
- [ ] Update labels if needed
- [ ] Optimize issue template
- [ ] Gather team feedback on workflow

### Annual Tasks

- [ ] Update GitHub Actions versions
- [ ] Review and archive old issues
- [ ] Update workflow documentation
- [ ] Conduct retrospective on doctrine pipeline

---

## 🆘 Support

### Questions

- **Workflow Issues**: Check GitHub Actions logs
- **Project Board**: Review GitHub Projects documentation
- **Doctrine Changes**: Review DOCTRINE_DASHBOARD.md

### Escalation

- **Workflow Failures**: Open issue with label `workflow-bug`
- **Permission Issues**: Check with repository admin
- **Project Board Setup**: Review GitHub Projects docs

---

**Last Updated**: 2025-11-07
**Maintained By**: Barton Outreach Team
**Status**: Production Ready ✅
