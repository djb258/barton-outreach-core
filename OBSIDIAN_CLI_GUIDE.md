# Obsidian Global CLI Guide

**Setup Date:** 2025-11-03  
**Status:** ✅ **OBSIDIAN CLI READY**

---

## ✅ Global Setup Complete

Obsidian is now available globally from any terminal!

**CLI Location:** `C:\Users\CUSTOMER PC\AppData\Roaming\Python\Scripts\obsidian.py`  
**PATH:** Already configured (restart terminal to use directly)

---

## 🚀 Usage

### **After Restarting Terminal:**

```bash
# Open default vault
obsidian vault
obsidian open

# Open specific vault
obsidian open "C:\path\to\vault"

# Create new note
obsidian new "Meeting Notes"
obsidian new "Project Plan" Projects

# Create today's daily note
obsidian daily

# List available vaults
obsidian list
```

---

## 📝 Commands

### **`obsidian vault` or `obsidian open`**
Opens your default Obsidian vault.

```bash
obsidian vault
obsidian open
obsidian open "C:\Users\CUSTOMER PC\Documents\MyVault"
```

### **`obsidian new <name> [folder]`**
Creates a new note in the specified folder (default: Inbox).

```bash
# Create in Inbox (default)
obsidian new "Quick Note"

# Create in specific folder
obsidian new "Project Alpha" Projects
obsidian new "Daily Review" Daily
obsidian new "Resource" Resources
```

### **`obsidian daily`**
Creates today's daily note in the `01-Daily/` folder.

```bash
obsidian daily
# Creates: 01-Daily/2025-11-03.md
```

### **`obsidian list`**
Lists all available vaults in your Documents folder.

```bash
obsidian list
```

---

## 💡 Examples

### **Quick Note Capture**
```bash
# Quick idea - goes to Inbox
obsidian new "Great idea for project"

# Project planning
obsidian new "Q4 Planning" Projects

# Daily journal
obsidian daily
```

### **Workflow Integration**
```bash
# After meeting
obsidian new "Team Meeting $(date +%Y-%m-%d)" Projects

# Daily standup
obsidian daily
# Then edit the note that opens
```

### **From Scripts**
```python
import subprocess

# Open vault
subprocess.run(["obsidian", "vault"])

# Create note
subprocess.run(["obsidian", "new", "Script Note", "Inbox"])
```

---

## 🔧 Default Vault

**Default Location:**
```
C:\Users\CUSTOMER PC\Documents\Obsidian Vault
```

**To Change Default:**
Edit `obsidian.py` and update `DEFAULT_VAULT` variable.

---

## 📂 Folder Structure

Your vault uses this structure:
- `00-Inbox/` - Quick capture (default for new notes)
- `01-Daily/` - Daily notes
- `02-Projects/` - Projects
- `03-Areas/` - Ongoing areas
- `04-Resources/` - Resources
- `05-Archive/` - Archive

---

## ⌨️ Keyboard Shortcuts (In Obsidian)

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New note |
| `Ctrl+O` | Quick switcher |
| `Ctrl+P` | Command palette |
| `Ctrl+G` | Graph view |
| `Ctrl+Shift+F` | Search |

---

## 🔗 Integration with Your Workflow

### **With AI Agents**
```bash
# Generate content with Codex
codex "Write meeting agenda template" > agenda.txt

# Create note from it
obsidian new "Meeting Agenda" Projects
# Paste content into note
```

### **With Git**
```bash
# Document changes
obsidian new "Git Commit Notes" Projects

# Link to commits
obsidian new "Release v1.0" Projects
```

### **Daily Routine**
```bash
# Morning
obsidian daily

# Throughout day
obsidian new "Quick thought" Inbox

# End of day
obsidian new "Daily Review" Daily
```

---

## 🆘 Troubleshooting

### **"obsidian: command not found"**
- Restart your terminal after setup
- Check PATH includes: `C:\Users\CUSTOMER PC\AppData\Roaming\Python\Scripts`
- Try: `python C:\Users\CUSTOMER PC\AppData\Roaming\Python\Scripts\obsidian.py vault`

### **"Vault not found"**
- Check vault path is correct
- Create vault first: `obsidian vault` (will create if missing)
- Or specify path: `obsidian open "C:\path\to\vault"`

### **Note not opening**
- Obsidian opens the vault
- Navigate to note manually in Obsidian
- Or use `Ctrl+O` in Obsidian to find note

---

## ✅ Verification

Test your setup:

```bash
# Test 1: List vaults
obsidian list

# Test 2: Open vault
obsidian vault

# Test 3: Create note
obsidian new "Test Note"

# Test 4: Create daily note
obsidian daily
```

---

**Your Obsidian CLI is ready!** 🎉

**Restart terminal, then use `obsidian` command from anywhere!**

