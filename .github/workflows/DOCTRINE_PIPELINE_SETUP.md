# Doctrine Pipeline Sync - Setup Guide

**Last Updated**: 2026-02-16
**Workflow File**: `.github/workflows/doctrine-project-sync.yml`

---

## What It Does

Automatically creates GitHub Issues when doctrine files are modified on push.
Each issue includes a change summary, links to changed files, labels, and assignee.

## Triggers

Runs on push to `main` or `develop` when files match:
- `doctrine/**/*.md`
- `doctrine/**/*.sql`
- `doctrine/**/*.mmd`

## Required Permissions

Set in repository Settings > Actions > General > Workflow permissions:

| Permission | Why |
|------------|-----|
| `contents: read` | Read commit history and changed files |
| `issues: write` | Create tracking issues |
| `projects: write` | Add issues to project board |

Select **"Read and write permissions"** and check **"Allow GitHub Actions to create and approve pull requests"**.

## How to Test

```bash
# Make a small change to any doctrine file
echo "" >> doctrine/README.md
git add doctrine/README.md
git commit -m "test: trigger doctrine pipeline workflow"
git push origin main
```

Expected result:
1. Workflow runs (visible in Actions tab)
2. Issue created: "Doctrine Update #N - X file(s) changed"
3. Issue labeled: `doctrine`, `auto-sync`, `documentation`
4. Issue assigned to pusher

## Troubleshooting

**Workflow not triggering**
- Verify file is at exact path: `.github/workflows/doctrine-project-sync.yml`
- Confirm push was to `main` or `develop`
- Confirm changed files are `.md`, `.sql`, or `.mmd` inside `doctrine/`
- Check Actions are enabled: Settings > Actions > "Allow all actions"

**Issue not created**
- Check workflow permissions (see Required Permissions above)
- Review step logs: Actions tab > workflow run > "Create doctrine tracking issue"
- `GITHUB_TOKEN` is automatic — no manual secret setup needed

**Issue not added to project board**
- Verify project exists with name "Doctrine Pipeline"
- Update project URL in workflow file (line ~170) with correct project number
- Manually add first issue to establish the connection

**Permission denied errors**
- Enable write permissions in Settings > Actions > Workflow permissions
- Check organization-level Actions restrictions if applicable
