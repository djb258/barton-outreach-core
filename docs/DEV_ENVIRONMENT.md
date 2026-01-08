# Developer Environment Configuration

**Version:** 1.0.0
**Date:** 2026-01-08
**Status:** ACTIVE

---

## PowerShell / PSReadLine Commit Crash Fix

### Symptom

When running `git commit` in PowerShell (especially with Claude Code or other integrated terminals), the commit may crash or hang due to PSReadLine's predictive rendering feature conflicting with inline editor invocations.

### Root Cause

PSReadLine's predictive text (`PredictionSource`) and certain edit modes can interfere with git's inline message editor, causing the terminal to freeze or crash.

### Fix (Copy-Paste for Operators)

Run these commands in PowerShell to disable problematic features:

```powershell
Set-PSReadLineOption -EditMode Windows
Set-PSReadLineOption -PredictionSource None
```

### Persistent Fix

To make this permanent, add to your PowerShell profile (`$PROFILE`):

```powershell
# Fix for git commit crash in integrated terminals
if ($env:TERM_PROGRAM -eq "vscode" -or $env:CLAUDE_CODE) {
    Set-PSReadLineOption -EditMode Windows
    Set-PSReadLineOption -PredictionSource None
}
```

### Verification

After applying, verify settings:

```powershell
Get-PSReadLineOption | Select-Object EditMode, PredictionSource
```

Expected output:
```
EditMode PredictionSource
-------- ----------------
Windows              None
```

---

## Git Editor Configuration

### Repo-Local Setting

This repo is configured to use VS Code as the git editor:

```bash
git config core.editor "code --wait"
```

This avoids inline editor conflicts in integrated terminals.

### Verification

```bash
git config --get core.editor
```

Expected output: `code --wait`

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Commit hangs | Apply PSReadLine fix above |
| Editor doesn't open | Verify `code` is in PATH |
| Commit message empty | Ensure `--wait` flag is set |

---

**Last Updated:** 2026-01-08
