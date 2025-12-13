# Barton Outreach Core - Obsidian Vault

This Obsidian vault contains the knowledge base and documentation for the Barton Outreach Core project.

## 📁 Structure

```
obsidian-vault/
├── .obsidian/          # Obsidian configuration
├── notes/              # Daily notes and meeting notes
├── architecture/       # System architecture documentation
│   ├── Hub-Spoke-Schema-Architecture.md   # PLE Hub + Spoke DB design
│   ├── PLE-Data-Catalog.md                # AI-searchable metadata layer
│   ├── Schema-Export-System.md            # Neon schema export system
│   └── CTB-Phase-6-Completion.md          # CTB completion notes
├── processes/          # Process documentation and runbooks
├── research/           # Research notes and findings
├── templates/          # Note templates
└── assets/             # Images and attachments
```

## Architecture Documentation

### Core Schema Documentation

| Document | Description |
|----------|-------------|
| [[architecture/Hub-Spoke-Schema-Architecture]] | Hub + Spoke database design with 5 schemas, 31 tables, 2.4M+ rows |
| [[architecture/PLE-Data-Catalog]] | AI & human searchable metadata layer (725 columns documented) |
| [[architecture/Schema-Export-System]] | Automated Neon schema export to JSON/MD |

## 🔧 Setup

### 1. Install Obsidian
Download from: https://obsidian.md/download

### 2. Open Vault
1. Launch Obsidian
2. Click "Open folder as vault"
3. Select this directory: `ctb/docs/obsidian-vault`

### 3. Enable Community Plugins
Required plugins (auto-configured):
- **obsidian-git**: Auto-sync vault with Git
- **dataview**: Query and display data from notes
- **templater**: Create dynamic note templates
- **table-editor-obsidian**: Enhanced table editing
- **obsidian-kanban**: Kanban boards for task management

## 🎯 Usage Patterns

### Daily Notes
Create daily standup notes:
```
## 2025-11-06 Daily Note

### Done Yesterday
- [ ] Task 1
- [ ] Task 2

### Doing Today
- [ ] Task 3
- [ ] Task 4

### Blockers
- None
```

### Architecture Documentation
Link system components and diagrams:
```
# Component: Composio MCP Server

Status: #active
Doctrine ID: 04.04.00

## Overview
[[MCP Architecture]] integration hub managing 100+ tools.

## Related
- [[Firebase MCP]]
- [[Neon Database]]
- [[Outreach Process Manager]]
```

### Research Notes
Capture investigation findings:
```
# Research: LinkedIn Refresh Jobs

Date: 2025-11-06
Tags: #research #linkedin #apify

## Question
How to efficiently refresh stale LinkedIn profiles?

## Findings
1. Use Apify Actors for batch processing
2. Store results in [[Neon Database]]
3. Track via [[shq_error_log]]

## Next Steps
- [ ] Implement batch processor
- [ ] Add error handling
```

## 🔗 Integration with CTB

### Git Integration
The vault automatically syncs with Git via obsidian-git plugin:
- Auto-commit: Every 5 minutes
- Auto-pull: On vault open
- Auto-push: After commit

### Linking to Code
Reference code files in notes:
```markdown
See implementation in [[../ai/garage-bay/main.py]]
```

### Diagram Links
Link Eraser.io diagrams:
```markdown
![Architecture](../diagrams/eraser/system-architecture.svg)
```

## 🚀 Workflows

### New Feature Documentation
1. Create note: `architecture/Feature-Name.md`
2. Add front matter with metadata
3. Link related components
4. Update graph connections

### Meeting Notes
1. Create daily note (Ctrl/Cmd + T)
2. Use meeting template
3. Tag attendees: @person
4. Link to relevant docs

### Research Synthesis
1. Create research note in `research/`
2. Add tags and metadata
3. Create dataview query to aggregate findings
4. Export to formal documentation

## 📊 Dataview Queries

### Active Tasks
```dataview
TASK
WHERE !completed
GROUP BY file.link
```

### Recent Architecture Changes
```dataview
TABLE file.mtime as "Modified"
FROM "architecture"
SORT file.mtime DESC
LIMIT 10
```

### Research by Tag
```dataview
LIST
FROM #research
SORT file.ctime DESC
```

## 🛠️ Templates

See `templates/` for:
- Daily Note Template
- Architecture Doc Template
- Meeting Notes Template
- Research Note Template
- Process Runbook Template

## 📱 Mobile Access

Install Obsidian mobile app and sync via:
- Obsidian Sync (paid)
- Git + Working Copy (iOS)
- Git + MGit (Android)

---

**Created:** 2025-11-06
**CTB Branch:** sys/obsidian
**Doctrine ID:** 04.04.12
