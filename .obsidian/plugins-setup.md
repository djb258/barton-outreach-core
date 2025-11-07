# ⚙️ Obsidian Plugin Setup — SVG-PLE Doctrine Vault

**Version**: 1.0.0
**Last Updated**: 2025-11-07
**Target Obsidian Version**: 1.4+

---

## 📦 Required Plugins

| Plugin | Purpose | Priority |
|--------|---------|----------|
| ✅ **Dataview** | Auto-lists doctrines, schemas, tasks | **Required** |
| ✅ **Mermaid** | Renders Hub–Spoke–Axle diagrams | **Required** |
| ✅ **Obsidian Git** | Syncs doctrine edits to GitHub | **Required** |
| ⚙️ **Periodic Notes** | Daily build logs | Optional |
| ⚙️ **Canvas** | Visual node mapping | Optional |
| ⚙️ **Templater** | Doctrine templates | Optional |
| ⚙️ **Tag Wrangler** | Organize doctrine tags | Optional |

**Install from**: Settings → Community Plugins → Browse

---

## 🔧 Plugin Configuration

### 1. Dataview

**Installation**:
1. Settings → Community Plugins → Browse
2. Search "Dataview"
3. Install by Michael Brenan
4. Enable plugin (toggle ON)

**Configuration**:
- Settings → Dataview
- ✅ Enable JavaScript Queries: ON
- ✅ Enable Inline Queries: ON
- ✅ Enable Inline JavaScript Queries: ON
- Default Date Format: `YYYY-MM-DD`
- Default Date + Time Format: `YYYY-MM-DD HH:mm`

**Usage in Dashboard**:
```markdown
\`\`\`dataview
TABLE file.link AS "Doctrine", file.size AS "Size"
FROM "doctrine/ple"
SORT file.name ASC
\`\`\`
```

**Test**: Open [[DOCTRINE_DASHBOARD]] and verify tables render

---

### 2. Mermaid (Built-in)

**No Installation Required**: Obsidian 1.4+ has built-in Mermaid support

**Usage**:
```markdown
\`\`\`mermaid
graph LR
  A[Hub] --> B[Spoke]
  B --> C[Axle]
  C --> D[Wheel Rim]
\`\`\`
```

**Test**: Open `doctrine/diagrams/PLE-Hub-Spoke-Axle.mmd` and verify diagram renders

**Troubleshooting**:
- If diagram doesn't render, check for syntax errors
- Use [Mermaid Live Editor](https://mermaid.live/) to validate syntax
- Ensure triple backticks use `mermaid` language tag

---

### 3. Obsidian Git

**Installation**:
1. Settings → Community Plugins → Browse
2. Search "Obsidian Git"
3. Install by Denis Olehov
4. Enable plugin (toggle ON)

**Configuration**:
- Settings → Obsidian Git

**General Settings**:
- ✅ Auto-pull on startup: ON
- ✅ Auto-pull interval: 10 minutes
- ✅ Pull updates on startup: ON

**Commit Settings**:
- ✅ Vault backup interval: 10 minutes
- ✅ Auto-backup after file change: ON
- Commit message: `docs(doctrine): auto-update {{numFiles}} files`
- Commit message on manual commit: `docs(doctrine): update {{files}}`

**Advanced Settings**:
- ✅ Disable push: OFF (allow push to remote)
- ✅ Pull before push: ON
- Git path (Windows): `C:\Program Files\Git\bin\git.exe`
- Git path (Mac/Linux): `/usr/bin/git`

**Custom Commit Message Templates**:
```
docs(doctrine): update {{file_name}} at {{date}}
feat(doctrine): add {{file_name}}
fix(doctrine): correct {{file_name}}
```

**Usage**:
- Auto-commits every 10 minutes
- Manual commit: `Ctrl+P` → "Obsidian Git: Commit all changes"
- Push to remote: `Ctrl+P` → "Obsidian Git: Push"
- Pull from remote: `Ctrl+P` → "Obsidian Git: Pull"

**Test**:
1. Edit any doctrine file
2. Wait 10 minutes (or manually commit)
3. Check GitHub for commit
4. Use GitKraken to visualize history

---

### 4. Periodic Notes (Optional)

**Installation**:
1. Settings → Community Plugins → Browse
2. Search "Periodic Notes"
3. Install by Liam Cain
4. Enable plugin (toggle ON)

**Configuration**:
- Settings → Periodic Notes

**Daily Notes**:
- Folder: `journal/daily/`
- Template: `.obsidian/templates/daily-note.md`
- Format: `YYYY-MM-DD`

**Weekly Notes**:
- Folder: `journal/weekly/`
- Template: `.obsidian/templates/weekly-note.md`
- Format: `YYYY-[W]WW`

**Template Example** (`.obsidian/templates/daily-note.md`):
```markdown
# {{date:YYYY-MM-DD}} - Daily Build Log

## 📋 Today's Focus
- [ ]

## 🔧 Doctrine Updates
-

## 🐛 Issues Encountered
-

## ✅ Completed
-

## 🔗 Related
- [[PLE-Doctrine]]
- [[BIT-Doctrine]]
- [[Talent-Flow-Doctrine]]
```

---

### 5. Canvas (Built-in)

**No Installation Required**: Obsidian 1.4+ has built-in Canvas

**Usage**:
1. Right-click `doctrine/` folder → New Canvas
2. Name: `PLE-Architecture-Visual.canvas`
3. Drag doctrine files onto canvas
4. Draw connections between components
5. Color-code by layer (Hub=Blue, Axle=Gold, Spokes=Crimson)

**Example Canvas Layout**:
```
┌─────────────────────────────────────────┐
│           PLE-Doctrine                  │  ← Top center
│         (Master System)                 │
└─────────────────────────────────────────┘
          │
    ┌─────┼─────┐
    │     │     │
    ▼     ▼     ▼
┌────────┬────────┬────────┐
│  BIT   │ Talent │ Renewal│  ← Middle row
│ (Axle) │  Flow  │  (TBD) │
└────────┴────────┴────────┘
    │     │     │
    └─────┼─────┘
          ▼
    ┌──────────┐
    │   Hub    │  ← Bottom
    │  (Data)  │
    └──────────┘
```

---

### 6. Templater (Optional)

**Installation**:
1. Settings → Community Plugins → Browse
2. Search "Templater"
3. Install by SilentVoid
4. Enable plugin (toggle ON)

**Configuration**:
- Template folder: `.obsidian/templates/`
- ✅ Automatic jump to cursor: ON
- ✅ Trigger Templater on new file creation: ON

**Template: New Spoke Doctrine**:

File: `.obsidian/templates/spoke-doctrine-template.md`

```markdown
# {{title}} Doctrine — {{subtitle}}
## Barton Doctrine Framework | SVG-PLE Marketing Core

**Document ID**: `01.04.02.04.{{barton_id}}.001`
**Version**: 1.0.0
**Last Updated**: {{date:YYYY-MM-DD}}
**Altitude**: 20,000 ft (Category / Spoke Layer)
**Role**: {{role}} spoke feeding BIT Axle
**Status**: Active | Production Ready

---

## Section 1: Purpose and Doctrine Position
{{cursor}}

## Section 2: Logical Flow (Hub → Spoke → BIT)


## Section 3: Event Classification Table


## Section 4: Schema Explanation


## Section 5: Trigger Logic → Insert BIT Event


## Section 6: Numbering + ID Examples


## Section 7: Relationship to PLE and Outreach


## Section 8: Audit + Data Lineage Rules


## Section 9: Example Scenario

```

**Usage**:
1. Create new file: `doctrine/ple/Renewal-Doctrine.md`
2. `Ctrl+P` → "Templater: Insert Template"
3. Select "spoke-doctrine-template"
4. Fill in prompts: title, subtitle, barton_id, role
5. Cursor jumps to Section 1 for editing

---

### 7. Tag Wrangler (Optional)

**Installation**:
1. Settings → Community Plugins → Browse
2. Search "Tag Wrangler"
3. Install by PJ Eby
4. Enable plugin (toggle ON)

**Usage**:
- Right-click tag in file explorer
- Rename tags across all files
- Merge duplicate tags

**Suggested Tags**:
- `#doctrine/master` - PLE-Doctrine
- `#doctrine/spoke` - Talent Flow, Renewal, Compliance
- `#doctrine/axle` - BIT-Doctrine
- `#schema/bit` - BIT schema files
- `#schema/spoke` - Spoke schema files
- `#diagram/mermaid` - Mermaid diagrams
- `#task/urgent` - High priority tasks
- `#task/planned` - Planned features

---

## 🔄 Obsidian Git Configuration

### Initial Setup

**1. Verify Git Installation**:
```bash
git --version
# Expected: git version 2.x.x
```

**2. Configure Git User** (if not already set):
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

**3. Open Obsidian Vault**:
- File → Open Vault
- Navigate to: `C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\doctrine\`
- Open as vault

**4. Enable Obsidian Git**:
- Settings → Community Plugins → Obsidian Git
- Toggle ON
- Configure settings (see above)

---

### Git Workflow

**Automatic Workflow** (Recommended):
1. Edit doctrines in Obsidian
2. Plugin auto-commits every 10 minutes
3. Plugin auto-pushes to GitHub
4. GitKraken visualizes commit history

**Manual Workflow**:
1. Edit doctrines in Obsidian
2. `Ctrl+P` → "Obsidian Git: Commit all changes"
3. Enter commit message: `docs(doctrine): update BIT scoring logic`
4. `Ctrl+P` → "Obsidian Git: Push"

**Pull Latest Changes**:
- On startup: Automatic (if enabled)
- Manual: `Ctrl+P` → "Obsidian Git: Pull"

**View Git Status**:
- `Ctrl+P` → "Obsidian Git: Open source control view"
- Shows staged/unstaged changes

---

## 🧭 Usage Flow

### Daily Workflow

**Morning**:
1. Open Obsidian (auto-pulls latest changes)
2. Review [[DOCTRINE_DASHBOARD]] for updates
3. Check tasks in `docs/tasks/hub_tasks.md`

**During Work**:
1. Edit doctrines as needed
2. Add `[[links]]` to related doctrines
3. Update Dataview frontmatter (if tracking metrics)

**Evening**:
1. Review auto-commits (check bottom-right status)
2. Manually commit if urgent: `Ctrl+P` → Commit
3. Verify GitHub has latest changes

---

### Integration with Other Tools

**GitKraken**:
- Open repo in GitKraken
- Visualize doctrine commit history
- Create feature branches for new spokes
- Merge PRs after review

**GitHub Projects**:
- Track tasks from `docs/tasks/` folder
- Link commits to project board
- Auto-update task status on commit

**Grafana**:
- View real-time metrics from Neon
- Monitor BIT scores, enrichment performance
- Dashboard links in [[DOCTRINE_DASHBOARD]]

**Neon Database**:
- Schema definitions in `doctrine/schemas/`
- Run migrations: `psql $DATABASE_URL -f doctrine/schemas/bit-schema.sql`

---

## ✅ Setup Verification Checklist

### Plugins Installed

- [ ] Dataview installed and enabled
- [ ] Mermaid rendering (built-in, no install needed)
- [ ] Obsidian Git installed and enabled
- [ ] Periodic Notes installed (optional)
- [ ] Canvas available (built-in)
- [ ] Templater installed (optional)
- [ ] Tag Wrangler installed (optional)

### Configuration Complete

- [ ] Dataview: JavaScript queries enabled
- [ ] Obsidian Git: Auto-commit every 10 minutes
- [ ] Obsidian Git: Auto-pull on startup
- [ ] Obsidian Git: Git path configured
- [ ] Periodic Notes: Template folder set (if using)

### Verification Tests

- [ ] Open [[DOCTRINE_DASHBOARD]] → Dataview tables render
- [ ] Open `PLE-Hub-Spoke-Axle.mmd` → Mermaid diagram renders
- [ ] Edit any doctrine file → Auto-commits within 10 minutes
- [ ] Check GitHub → See auto-commit from Obsidian
- [ ] Graph View (`Ctrl+G`) → See doctrine connections

---

## 🆘 Troubleshooting

### Dataview Not Rendering

**Problem**: Tables show as code blocks
**Solution**:
1. Install Dataview plugin
2. Enable plugin (toggle ON)
3. Restart Obsidian
4. Refresh note (close/reopen)

### Mermaid Diagrams Not Showing

**Problem**: Diagram shows as text
**Solution**:
1. Update Obsidian to 1.4+ (has built-in Mermaid)
2. Check syntax: Use triple backticks + `mermaid` tag
3. Validate at [mermaid.live](https://mermaid.live/)

### Obsidian Git Not Syncing

**Problem**: Changes not in GitHub
**Solution**:
1. Check auto-commit is ON (Settings → Obsidian Git)
2. Verify Git credentials: `git config --list`
3. Manual commit: `Ctrl+P` → Commit all changes
4. Check network connection

### Plugin Installation Failed

**Problem**: "Failed to load plugin" error
**Solution**:
1. Disable Safe Mode: Settings → Community Plugins → Turn off Safe Mode
2. Update Obsidian to latest version
3. Reinstall plugin
4. Check `.obsidian/plugins/` folder exists

---

## 📚 Additional Resources

### Official Documentation

- **Dataview**: https://blacksmithgu.github.io/obsidian-dataview/
- **Obsidian Git**: https://github.com/denolehov/obsidian-git
- **Mermaid**: https://mermaid.js.org/
- **Obsidian Forums**: https://forum.obsidian.md/

### Community Resources

- **Obsidian Discord**: https://discord.gg/veuWUTm
- **Reddit r/ObsidianMD**: https://reddit.com/r/ObsidianMD
- **YouTube Tutorials**: Search "Obsidian Dataview tutorial"

---

## 🎯 This Vault Makes the Repo a Living, Versioned Doctrine Hub

**Benefits**:
- ✅ Version-controlled (every doctrine edit is Git-tracked)
- ✅ Searchable (full-text search across all doctrines)
- ✅ Visualized (Graph View shows connections)
- ✅ Synced (GitHub + GitKraken + Obsidian)
- ✅ Queryable (Dataview auto-generates dashboards)

**Workflow**:
1. **Edit** doctrines in Obsidian (beautiful markdown editor)
2. **Obsidian Git** auto-commits changes (every 10 min)
3. **GitKraken** visualizes version history (visual Git client)
4. **GitHub Projects** tracks tasks from `docs/tasks/` (project management)
5. **Grafana** reflects live data from Neon (real-time monitoring)

---

**Last Updated**: 2025-11-07
**Maintained By**: Barton Outreach Team
**Obsidian Vault**: SVG-PLE Doctrine Library
