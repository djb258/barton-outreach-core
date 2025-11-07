# 🧭 SVG-PLE Doctrine Dashboard

> **Purpose:** Central view of all doctrines, schemas, diagrams, and tasks
> for the Perpetual Lead Engine (PLE).
> This vault forms the "medical record" of marketing intelligence doctrine.

**Last Updated**: 2025-11-07
**Barton Doctrine Compliance**: 100% ✅
**Obsidian Version**: 1.4+

---

## 📂 Doctrine Files

```dataview
TABLE
  file.link AS "Doctrine File",
  file.size AS "Size (KB)",
  file.mtime AS "Last Modified"
FROM "doctrine/ple"
WHERE file.ext = "md" AND file.name != "DOCTRINE_DASHBOARD"
SORT file.name ASC
```

**Manual Links** (if Dataview not active):
- [[PLE-Doctrine]] - Master system overview (Altitude 30k-5k ft)
- [[BIT-Doctrine]] - Buyer Intent Tool (Axle)
- [[Talent-Flow-Doctrine]] - Movement detection (Spoke 1)

---

## 📊 Doctrine Schemas

```dataview
TABLE
  file.link AS "Schema File",
  file.size AS "Size (KB)",
  file.mtime AS "Last Modified"
FROM "doctrine/schemas"
WHERE file.ext = "sql"
SORT file.name ASC
```

**Manual Links** (if Dataview not active):
- `bit-schema.sql` - BIT scoring engine (3 tables, 1 view, 3 triggers)
- `talent_flow-schema.sql` - Talent Flow spoke (2 tables, 1 view, 3 triggers)

---

## 🧩 Diagrams

```dataview
TABLE
  file.link AS "Diagram",
  file.size AS "Size (KB)"
FROM "doctrine/diagrams"
WHERE file.ext = "mmd"
SORT file.name ASC
```

**Manual Links** (if Dataview not active):
- `PLE-Hub-Spoke-Axle.mmd` - Color-coded PLE architecture (Hub/Spoke/Axle/Wheel)

**View in**:
- GitHub (auto-renders Mermaid)
- Obsidian (Mermaid plugin required)
- [Mermaid Live Editor](https://mermaid.live/) (export to PNG)

---

## ✅ Current Tasks

```dataview
TASK
FROM "docs/tasks" OR "doctrine"
WHERE !completed
SORT file.mtime DESC
```

**Manual Task List** (if Dataview not active):
- [ ] Finalize Grafana connection to Neon
- [ ] Verify Talent Flow trigger → BIT event
- [ ] Review doctrine numbering and Barton ID registry
- [ ] Implement Renewal Intelligence spoke (Q1 2026)
- [ ] Implement Compliance Monitor spoke (Q2 2026)

---

## 🔗 Quick Links

### External Resources

- **GitHub Repository**: [barton-outreach-core](https://github.com/your-org/barton-outreach-core)
- **GitHub Project Board**: [SVG-PLE Development](https://github.com/your-org/projects/1)
- **Grafana Dashboard**: [SVG-PLE Overview](https://dbarton.grafana.net/d/svg-ple-dashboard)
- **Neon Database**: ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech

### Internal Documentation

- [[README]] - Doctrine library index
- [[OUTREACH_DOCTRINE_A_Z_v1.3.2]] - Complete system documentation
- [[GLOBAL_CONFIG_IMPLEMENTATION]] - Global configuration details
- [[CLAUDE]] - Bootstrap guide for new team members

---

## 🧱 System Hierarchy

| Layer | Component | Role | Barton ID | Status | File |
|-------|-----------|------|-----------|--------|------|
| **Vision** | PLE Master | Perpetual Lead Engine | `01.04.01.04.30000` | ✅ Active | [[PLE-Doctrine]] |
| **Spoke 1** | Talent Flow | Movement Detection | `01.04.02.04.20000` | ✅ Active | [[Talent-Flow-Doctrine]] |
| **Spoke 2** | Renewal | Contract Tracking | `01.04.02.04.21000` | 📅 Planned | (to be created) |
| **Spoke 3** | Compliance | Regulatory Events | `01.04.02.04.22000` | 📅 Planned | (to be created) |
| **Spoke 4** | Tech Stack | Infrastructure Changes | `01.04.02.04.23000` | 🔮 Future | (to be created) |
| **Spoke 5** | Funding | Investment Events | `01.04.02.04.24000` | 🔮 Future | (to be created) |
| **Axle** | BIT | Buyer Intent Scoring | `01.04.03.04.10000` | ✅ Active | [[BIT-Doctrine]] |
| **Wheel Rim** | Outreach | Campaign Execution | - | ⚙️ In Progress | (see PLE-Doctrine) |

**Legend**:
- ✅ Active: Fully implemented, production-ready
- ⚙️ In Progress: Partially implemented
- 📅 Planned: Design complete, implementation pending
- 🔮 Future: Vision only, no design yet

---

## 📈 System Metrics

### BIT Score Distribution

```dataview
TABLE
  file.link AS "Company",
  bit_score AS "Score",
  score_category AS "Category"
FROM "companies"
WHERE bit_score
SORT bit_score DESC
LIMIT 10
```

**Note**: Requires Dataview frontmatter in company notes. Example:
```yaml
---
company_unique_id: 04.04.02.04.30000.042
bit_score: 89
score_category: Hot
---
```

### Recent Movements

```dataview
TABLE
  file.link AS "Movement",
  movement_type AS "Type",
  confidence_score AS "Confidence",
  detected_at AS "Detected"
FROM "movements"
WHERE detected_at
SORT detected_at DESC
LIMIT 5
```

---

## 🎯 Quick Actions

### For New Team Members

1. Read [[PLE-Doctrine]] - Start with Vision (Altitude 30k ft)
2. View `PLE-Hub-Spoke-Axle.mmd` - Visual architecture
3. Review [[BIT-Doctrine]] - Understand intent scoring
4. Explore [[Talent-Flow-Doctrine]] - See spoke implementation
5. Check [[README]] - Use as navigation hub

### For Developers

1. Clone repo: `git clone https://github.com/your-org/barton-outreach-core.git`
2. Open Obsidian vault: Point to `doctrine/` directory
3. Install plugins: See [[plugins-setup]]
4. Enable Obsidian Git: Auto-sync to GitHub
5. Create feature branch: `feature/[spoke-name]-doctrine`

### For Architects

1. Review system hierarchy table (above)
2. Check Barton ID registry in [[README]]
3. Use spoke template for new components
4. Follow compliance checklist before merge
5. Update Mermaid diagram if architecture changes

---

## 🛠️ Maintenance

### Weekly Tasks

- [ ] Review open tasks in `docs/tasks/`
- [ ] Check Grafana dashboards for anomalies
- [ ] Verify enrichment agent performance
- [ ] Monitor BIT score distribution (Hot/Warm/Cold)

### Monthly Tasks

- [ ] Run compliance audit: `npm run compliance:complete`
- [ ] Review doctrine updates (via Git blame)
- [ ] Update system hierarchy table if changes
- [ ] Sync with IMO-creator global config

### Quarterly Tasks

- [ ] Evaluate new spoke requirements
- [ ] Review Barton ID allocation
- [ ] Update 5-year vision (PLE-Doctrine Altitude 30k ft)
- [ ] Conduct architecture review

---

## 📚 Related Documentation

### Doctrine Files

- [[PLE-Doctrine]] - Master system overview
- [[BIT-Doctrine]] - Intent scoring engine
- [[Talent-Flow-Doctrine]] - Movement detection spoke
- [[README]] - Doctrine library index

### Database Documentation

- `bit-schema.sql` - BIT scoring tables
- `talent_flow-schema.sql` - Movement tracking tables
- [[schema_map.json]] - Complete database schema map
- [[ENRICHMENT_TRACKING_QUERIES]] - Grafana SQL queries

### Configuration Files

- [[global-config.yaml]] - Master configuration
- [[GLOBAL_CONFIG_IMPLEMENTATION]] - Implementation details
- [[.env.example]] - Environment variables template

### Guides

- [[CLAUDE]] - Bootstrap guide
- [[plugins-setup]] - Obsidian plugin configuration
- [[OUTREACH_DOCTRINE_A_Z_v1.3.2]] - Complete system documentation

---

## 🔄 Auto-Updates

This dashboard auto-updates via Dataview queries. If queries don't render:

1. **Install Dataview**: Settings → Community Plugins → Browse → Dataview
2. **Enable Plugin**: Toggle Dataview to ON
3. **Refresh View**: Close and reopen this note
4. **Check Syntax**: Dataview uses triple backticks with `dataview` language tag

Edits to doctrines sync to GitHub automatically through **Obsidian Git** plugin.

---

## 💡 Tips & Tricks

### Graph View

- Press `Ctrl+G` (Windows) or `Cmd+G` (Mac) to open Graph View
- See connections between doctrines via `[[links]]`
- Filter by tag: `tag:#doctrine` or `tag:#schema`

### Search

- Press `Ctrl+Shift+F` (Windows) or `Cmd+Shift+F` (Mac) for global search
- Search query: `path:doctrine/ "Barton ID"` to find all ID references
- Regular expressions supported: `/"01\.04\.\d{2}\.04\.\d{5}"/`

### Daily Notes

- Use Periodic Notes plugin for daily build logs
- Template location: `.obsidian/templates/daily-note.md`
- Automatically link to active doctrine work

### Canvas

- Visual node mapping of doctrine relationships
- Create canvas: Right-click folder → New Canvas
- Drag doctrine files onto canvas to create visual map

---

## 🆘 Troubleshooting

### Dataview Queries Not Rendering

**Symptoms**: Seeing code blocks instead of tables/lists

**Fix**:
1. Install Dataview plugin (Settings → Community Plugins)
2. Enable plugin (toggle to ON)
3. Restart Obsidian
4. Refresh this note (close/reopen)

### Mermaid Diagrams Not Rendering

**Symptoms**: Seeing text instead of diagram

**Fix**:
1. Obsidian has built-in Mermaid support (v1.4+)
2. Ensure diagram uses triple backticks with `mermaid` language tag
3. View raw file in text editor to check syntax

### Obsidian Git Not Syncing

**Symptoms**: Changes not appearing in GitHub

**Fix**:
1. Check plugin settings: Auto-commit enabled?
2. Verify Git credentials: `git config --list`
3. Manual commit: Open command palette (`Ctrl+P`) → "Obsidian Git: Commit all changes"
4. Check `.gitignore`: Ensure doctrine files not excluded

### Links Not Working

**Symptoms**: `[[Doctrine]]` shows as plain text

**Fix**:
1. Enable Wiki-style links: Settings → Files & Links → Use `[[Wikilinks]]`
2. Check file exists: File must be in vault
3. Try path: `[[doctrine/ple/PLE-Doctrine|PLE-Doctrine]]`

---

**Last Updated**: 2025-11-07
**Maintained By**: Barton Outreach Team
**Obsidian Vault**: SVG-PLE Doctrine Library
