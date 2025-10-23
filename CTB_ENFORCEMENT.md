# 🛡️ CTB Doctrine Enforcement System

**Zero exceptions. Every commit. Every PR. Every time.**

This document explains the automated enforcement system that ensures 100% CTB compliance across the repository with no manual intervention required.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Enforcement Layers](#enforcement-layers)
3. [Setup](#setup)
4. [How It Works](#how-it-works)
5. [Compliance Thresholds](#compliance-thresholds)
6. [Troubleshooting](#troubleshooting)
7. [Bypassing (Not Recommended)](#bypassing-not-recommended)

---

## Overview

The CTB Enforcement System provides **three layers of automated validation**:

```
Layer 1: Pre-commit Hook (Local)
   ↓ Auto-tags new files
   ↓ Validates compliance
   ↓ Blocks commits < 70/100

Layer 2: GitHub Actions (CI/CD)
   ↓ Auto-tags any missed files
   ↓ Validates compliance
   ↓ Blocks PR merges < 70/100
   ↓ Posts compliance report

Layer 3: Scheduled Audits (Weekly)
   ↓ Full repository audit
   ↓ Generates compliance reports
   ↓ Alerts on degradation
```

**Result**: It's impossible to merge code that doesn't follow CTB structure.

---

## Enforcement Layers

### Layer 1: Pre-commit Hook (Local Development)

**When**: Before every `git commit`

**What it does**:
1. Scans staged files for new files
2. Auto-tags any new files with Barton IDs
3. Runs CTB compliance audit
4. Blocks commit if score < 70/100
5. Shows exactly what needs to be fixed

**Why**: Catches issues before they reach GitHub

**Location**: `.githooks/pre-commit`

**Example output**:
```
🔍 CTB Structure Enforcement - Validating commit...
Step 1/3: Auto-tagging new files...
  Tagging: ctb/sys/api/routes/my-new-endpoint.js
✓ Auto-tagging complete

Step 2/3: Running CTB compliance audit...
Compliance Score: 75/100 (GOOD)

Step 3/3: Validating compliance threshold...
Checking for critical violations...

═══════════════════════════════════════════════════════
✓ CTB Compliance Validation Passed
═══════════════════════════════════════════════════════
Score: 75/100 (GOOD)
All files properly tagged and compliant.
═══════════════════════════════════════════════════════
```

---

### Layer 2: GitHub Actions CI/CD

**When**: On every push and pull request

**What it does**:
1. Auto-tags any untagged files (redundant safety)
2. Runs full CTB compliance audit
3. Blocks PR merge if score < 70/100
4. Posts detailed compliance report as PR comment
5. Uploads audit report as artifact

**Why**: Ensures compliance even if pre-commit hook is bypassed

**Location**: `ctb/sys/github-factory/.github/workflows/ctb_enforcement.yml`

**Triggers**:
- Push to `main`, `master`, or `develop`
- Pull requests to these branches
- Weekly schedule (Sunday at midnight)
- Manual trigger via GitHub Actions UI

**PR Comment Example**:
```markdown
## ✅ CTB Doctrine Compliance Report

**Score**: 72/100
**Grade**: FAIR
**Threshold**: 70/100
**Status**: ✅ PASSED

---

### Details
- **Files Auto-Tagged**: 3
- **Compliance Status**: All checks passed ✅

### 🎉 Success!
All CTB doctrine compliance checks passed. This PR is ready for review.

---

📊 [View Full Audit Report](https://github.com/.../actions/runs/123456)
```

---

### Layer 3: Scheduled Audits

**When**: Weekly (Sunday at midnight UTC)

**What it does**:
1. Full repository compliance audit
2. Generates historical compliance reports
3. Tracks compliance trends over time
4. Alerts if score drops below threshold

**Why**: Continuous monitoring and quality assurance

---

## Setup

### One-Time Setup (Required for Local Enforcement)

After cloning the repository, you **must** run the setup script to enable the pre-commit hook:

#### Linux/Mac:
```bash
cd .githooks
chmod +x setup-hooks.sh
./setup-hooks.sh
```

#### Windows:
```batch
cd .githooks
setup-hooks.bat
```

**Output**:
```
✅ CTB enforcement hooks installed successfully!

What happens now:
  • Every commit will auto-tag new files
  • CTB compliance will be checked automatically
  • Commits will be blocked if compliance < 70/100

To bypass hook (NOT RECOMMENDED):
  git commit --no-verify
```

### Verification

Test that the hook is working:

```bash
# Create a test file
echo "test" > ctb/sys/test.js

# Try to commit
git add ctb/sys/test.js
git commit -m "test"

# Should see enforcement output
```

---

## How It Works

### Auto-Tagging Process

When you create a new file in the `ctb/` directory:

1. **Pre-commit hook detects it**
   ```
   Found new files to tag:
   ctb/sys/api/routes/new-endpoint.js
   ```

2. **Runs metadata tagger**
   ```python
   python ctb_metadata_tagger.py ctb/sys/api/routes/new-endpoint.js
   ```

3. **Injects Barton ID header**
   ```javascript
   /**
    * CTB Metadata
    * Barton ID: 04.04.03.20251023.a1b2.001
    * Branch: sys
    * Altitude: 20k (ORBT)
    * ...
    */
   ```

4. **Re-stages the file**
   ```bash
   git add ctb/sys/api/routes/new-endpoint.js
   ```

### Compliance Audit Process

1. **Scans all files in ctb/**
   - Checks for Barton ID headers
   - Validates ID format
   - Checks altitude alignment
   - Validates branch placement

2. **Calculates score**
   ```
   Tagged files:     450/500 (90%)
   Correct format:    48/50 (96%)
   Proper placement: 500/500 (100%)
   Documentation:     40/50 (80%)

   Overall Score: 72/100 (FAIR)
   ```

3. **Compares to threshold**
   - Minimum required: 70/100
   - Current score: 72/100
   - Result: ✅ PASS

---

## Compliance Thresholds

### Current Thresholds

| Score Range | Grade | Status | Action |
|-------------|-------|--------|--------|
| 90-100 | EXCELLENT 🌟 | Pass | Commit/merge allowed |
| 70-89 | GOOD/FAIR ✅ | Pass | Commit/merge allowed |
| 60-69 | NEEDS WORK ⚠️ | **Block** | Must fix before commit |
| 0-59 | FAIL ❌ | **Block** | Must fix before commit |

### Minimum Threshold: 70/100

**Why 70?**
- Balances strictness with practicality
- Allows for gradual improvements
- Blocks egregious violations
- Permits minor issues that can be fixed later

**Can be changed** by editing:
- `.githooks/pre-commit` (line 77: `MIN_COMPLIANCE_SCORE=70`)
- `ctb_enforcement.yml` (line 95: `threshold=70`)

---

## Troubleshooting

### Problem: Commit blocked by pre-commit hook

**Symptom**:
```
❌ COMMIT BLOCKED - CTB Compliance Below Threshold
Current Score: 65/100
Required Score: 70/100
```

**Solution**:
```bash
# Run remediation script
python ctb/sys/github-factory/scripts/ctb_remediation.py ctb/

# Review changes
git diff

# Commit fixes
git add .
git commit -m "fix: Apply CTB remediation"
```

---

### Problem: GitHub Actions CI failing

**Symptom**:
PR shows red ❌ with "CTB compliance check failed"

**Solution**:

1. **View the audit report**
   - Click "Details" next to the failed check
   - Download the audit report artifact
   - Review specific violations

2. **Fix locally**
   ```bash
   # Run remediation
   python ctb/sys/github-factory/scripts/ctb_remediation.py ctb/

   # Commit and push
   git add .
   git commit -m "fix: Apply CTB remediation"
   git push
   ```

3. **Wait for CI to re-run**
   - CI will automatically re-run
   - Should pass if score now ≥ 70/100

---

### Problem: Files not being auto-tagged

**Symptom**:
Audit shows "Missing Barton ID" for your new files

**Solution**:

1. **Verify hook is installed**
   ```bash
   git config core.hooksPath
   # Should output: .githooks or absolute path to .githooks
   ```

2. **If not set, run setup again**
   ```bash
   cd .githooks
   ./setup-hooks.sh  # or setup-hooks.bat on Windows
   ```

3. **Manually tag files**
   ```bash
   python ctb/sys/github-factory/scripts/ctb_metadata_tagger.py ctb/path/to/file.js
   ```

---

### Problem: Hook not running at all

**Symptom**:
No enforcement output when committing

**Solution**:

1. **Check if hooks are enabled**
   ```bash
   git config core.hooksPath
   ```

2. **Check hook is executable**
   ```bash
   # Linux/Mac
   chmod +x .githooks/pre-commit

   # Windows - no action needed, git runs .bat files
   ```

3. **Re-run setup**
   ```bash
   cd .githooks
   ./setup-hooks.sh  # or .bat on Windows
   ```

4. **Verify Python is installed**
   ```bash
   python --version
   # or
   python3 --version
   ```

---

## Bypassing (Not Recommended)

### Why you shouldn't bypass

Bypassing enforcement:
- Degrades code quality
- Creates technical debt
- Makes repository harder to navigate
- Breaks CI/CD on GitHub
- Causes PR merge failures

### When bypassing is acceptable

**Only in emergencies**:
- Production hotfix required immediately
- CI infrastructure is broken
- Remediation script is broken

### How to bypass pre-commit hook

```bash
git commit --no-verify -m "emergency: Production hotfix"
```

**Warning**: This will still fail in GitHub Actions CI. You'll need to fix before PR can be merged.

### How to bypass GitHub Actions

**You cannot bypass GitHub Actions** without admin access. This is intentional.

To merge a PR with failing compliance:
1. Fix the compliance issues
2. Push the fixes
3. Wait for CI to pass

Or ask a repository admin to:
1. Manually merge with admin override
2. File a technical debt ticket to fix compliance

---

## Monitoring & Reporting

### View Current Compliance Score

```bash
# Run audit locally
cd ctb/sys/github-factory/scripts
python ctb_audit_generator.py ../../../../ctb/

# Output:
# CTB Compliance Score: 72/100 (FAIR)
```

### View Historical Compliance

- Check GitHub Actions → CTB Doctrine Enforcement workflow
- Download audit report artifacts
- Compare scores over time

### Scheduled Reports

Every Sunday at midnight:
- Full audit runs automatically
- Report uploaded as artifact
- Alerts sent if score drops

---

## Configuration

### Adjust Compliance Threshold

**Pre-commit hook**:
```bash
# Edit .githooks/pre-commit
MIN_COMPLIANCE_SCORE=70  # Change this value
```

**GitHub Actions**:
```yaml
# Edit ctb/sys/github-factory/.github/workflows/ctb_enforcement.yml
threshold=70  # Change this value (line 95)
```

### Disable Pre-commit Hook

```bash
# Temporarily disable
git config core.hooksPath ""

# Re-enable
git config core.hooksPath .githooks
```

**Warning**: Disabling local enforcement means you'll catch issues in CI instead, which is slower.

### Disable GitHub Actions

Edit `.github/workflows/ctb_enforcement.yml` and comment out the triggers:

```yaml
# on:
#   push:
#     branches: [ main, master, develop ]
```

**Warning**: Disabling CI enforcement removes the last safety net for compliance.

---

## Best Practices

### For Developers

1. **Install hooks immediately after cloning**
   ```bash
   cd .githooks && ./setup-hooks.sh
   ```

2. **Check compliance before pushing**
   ```bash
   python ctb/sys/github-factory/scripts/ctb_audit_generator.py ctb/
   ```

3. **Fix issues locally before PR**
   ```bash
   python ctb/sys/github-factory/scripts/ctb_remediation.py ctb/
   ```

4. **Never bypass enforcement** unless absolutely necessary

### For Repository Admins

1. **Monitor weekly audit reports**
   - Check GitHub Actions artifacts
   - Track compliance trends
   - Address degradation immediately

2. **Update enforcement thresholds as needed**
   - Gradually increase threshold (70 → 75 → 80 → 90)
   - Announce changes in advance
   - Provide time for fixes

3. **Review remediation effectiveness**
   - Check if auto-fixes are correct
   - Update remediation rules
   - Document common issues

---

## FAQ

### Q: What files get auto-tagged?

**A**: Any new file in the `ctb/` directory with extensions:
- `.js`, `.ts`, `.tsx`, `.jsx`
- `.py`
- `.sql`
- `.md`
- `.yml`, `.yaml`
- `.json` (configuration files)

Excluded:
- `node_modules/`
- `.git/`
- `*.min.js`, `*.min.css`
- `package-lock.json`
- `.env` (but `.env.example` is tagged)
- Log files

### Q: Can I change my file's Barton ID?

**A**: Yes, but maintain format:
```
Barton ID: database.subhive.table.timestamp.random.sequence
```

Example: `04.04.03.20251023.a1b2.001`

### Q: What if the tagger assigns the wrong ID?

**A**: Edit manually:
1. Open the file
2. Find the `Barton ID:` line
3. Update to correct ID following format
4. Commit the change

### Q: Does this slow down commits?

**A**: Slightly:
- Pre-commit hook adds ~2-5 seconds
- GitHub Actions adds ~30-60 seconds to PR CI

But the time saved from not having to fix compliance issues later makes it worthwhile.

### Q: Can I run the audit without committing?

**A**: Yes:
```bash
cd ctb/sys/github-factory/scripts
python ctb_audit_generator.py ../../../../ctb/
```

---

## Support

### Issues with enforcement system

1. Check this documentation
2. Check [TROUBLESHOOTING.md](ctb/docs/TROUBLESHOOTING.md)
3. File an issue: https://github.com/djb258/barton-outreach-core/issues
4. Tag with label: `ctb-enforcement`

### Improving enforcement

Suggestions for improving the enforcement system:
1. File an issue with label: `ctb-improvement`
2. Describe the problem and proposed solution
3. PR welcome after discussion

---

**Last Updated**: 2025-10-23
**Enforcement Version**: 2.0
**Maintained By**: Platform Team

**Related Docs**:
- [CTB Structure](ENTRYPOINT.md)
- [Compliance Report](CTB_AUDIT_REPORT.md)
- [Remediation Guide](CTB_REMEDIATION_SUMMARY.md)
