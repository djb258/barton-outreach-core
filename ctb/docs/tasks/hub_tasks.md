# Hub Tasks (SVG-PLE)

**Last Updated**: 2025-11-07
**Status**: Active Task Tracking
**Syncs To**: Obsidian Dashboard (via Dataview)

---

## 🎯 High Priority Tasks

### Infrastructure

- [ ] Finalize Grafana connection to Neon (configure data source)
- [ ] Deploy BIT schema to Neon PostgreSQL (`bit-schema.sql`)
- [ ] Deploy Talent Flow schema to Neon PostgreSQL (`talent_flow-schema.sql`)
- [ ] Test BIT score calculation with sample data
- [ ] Verify enrichment agents can write to `data_enrichment_log`

### Integration

- [ ] Verify Talent Flow trigger → BIT event (test `create_bit_event_from_movement`)
- [ ] Test Composio MCP connectivity (port 3001)
- [ ] Configure Apify LinkedIn scraper for target companies
- [ ] Set up Slack alerts for Hot leads (BIT score >= 80)
- [ ] Configure Salesforce sync for BIT scores

### Documentation

- [ ] Review doctrine numbering and Barton ID registry
- [ ] Update schema_map.json with BIT and Talent Flow tables
- [ ] Create Renewal-Doctrine.md (Spoke 2 - planned Q1 2026)
- [ ] Create Compliance-Doctrine.md (Spoke 3 - planned Q2 2026)
- [ ] Add BIT panels to Grafana dashboard

---

## 📅 Planned Tasks (Next Quarter)

### Spoke 2: Renewal Intelligence (Q1 2026)

- [ ] Design renewal tracking database schema
- [ ] Create `renewal-schema.sql` with contract_windows table
- [ ] Write Renewal-Doctrine.md (9 sections)
- [ ] Implement renewal window detection (120d/90d/60d/30d)
- [ ] Create BIT rules for renewal events (35-70 points)
- [ ] Test renewal → BIT event creation

### Spoke 3: Compliance Monitor (Q2 2026)

- [ ] Identify DOL violation data sources
- [ ] Design compliance tracking schema
- [ ] Create `compliance-schema.sql` with violations table
- [ ] Write Compliance-Doctrine.md (9 sections)
- [ ] Implement violation detection logic
- [ ] Create BIT rules for compliance events (25-30 points)

### Wheel Rim: Outreach Automation

- [ ] Design email sequence templates (Hot/Warm/Cold)
- [ ] Implement Salesforce task creation for 80+ scores
- [ ] Configure Slack webhook for Hot lead alerts
- [ ] Create outreach tracking table
- [ ] Measure response rates by score category

---

## 🔄 Recurring Tasks

### Daily

- [ ] Monitor enrichment agent performance (Grafana)
- [ ] Check for failed enrichment jobs (`status='failed'`)
- [ ] Review new executive movements (Talent Flow)
- [ ] Check Hot leads (BIT score >= 80)

### Weekly

- [ ] Review BIT score distribution (Hot/Warm/Cold)
- [ ] Audit unprocessed high-confidence movements
- [ ] Check Grafana dashboard health
- [ ] Review Obsidian Git sync status

### Monthly

- [ ] Run compliance audit: `npm run compliance:complete`
- [ ] Review Barton ID allocation (check for collisions)
- [ ] Audit data quality scores (minimum 70 threshold)
- [ ] Update system hierarchy table in PLE-Doctrine.md
- [ ] Sync with IMO-creator global config

---

## 🐛 Known Issues

### Active Issues

- [ ] **Issue #1**: Enrichment log trigger not creating Talent Flow movements
  - **Status**: Investigating
  - **Priority**: High
  - **Assigned**: TBD
  - **Related**: `talent_flow.create_event_from_enrichment()` trigger

- [ ] **Issue #2**: BIT scores view performance slow for 500+ companies
  - **Status**: Optimization needed
  - **Priority**: Medium
  - **Solution**: Add materialized view or caching layer

- [ ] **Issue #3**: Duplicate BIT events being created
  - **Status**: Fixed (added EXISTS check in trigger)
  - **Priority**: High
  - **Resolution**: Updated `create_bit_event_from_movement()` trigger

### Resolved Issues

- [x] ~~**Issue #4**: Barton ID format validation not enforcing CHECK constraint~~
  - **Resolution**: Added regex CHECK constraints to all tables
  - **Date**: 2025-11-07

- [x] ~~**Issue #5**: Mermaid diagram not rendering in Obsidian~~
  - **Resolution**: Updated Obsidian to 1.4+ (built-in Mermaid support)
  - **Date**: 2025-11-07

---

## 📊 Task Metrics

### Completion Status

| Category | Total | Completed | Remaining | Progress |
|----------|-------|-----------|-----------|----------|
| High Priority | 10 | 0 | 10 | 0% |
| Planned (Q1-Q2) | 18 | 0 | 18 | 0% |
| Recurring | 12 | N/A | N/A | Ongoing |
| Issues (Active) | 3 | 1 | 2 | 33% |

### Priority Breakdown

- 🔴 **High**: 5 tasks (infrastructure, integration)
- 🟡 **Medium**: 3 tasks (documentation, optimization)
- 🟢 **Low**: 2 tasks (future planning)

### Timeline

- **This Week**: Complete high-priority infrastructure tasks
- **This Month**: Deploy schemas, test integrations
- **Q1 2026**: Implement Renewal Intelligence spoke
- **Q2 2026**: Implement Compliance Monitor spoke

---

## 🔗 Related Documentation

### Doctrines

- [[PLE-Doctrine]] - Master system overview
- [[BIT-Doctrine]] - Intent scoring engine
- [[Talent-Flow-Doctrine]] - Movement detection spoke

### Schemas

- `doctrine/schemas/bit-schema.sql` - BIT tables
- `doctrine/schemas/talent_flow-schema.sql` - Talent Flow tables

### Dashboards

- [[DOCTRINE_DASHBOARD]] - Obsidian navigation hub
- [Grafana: SVG-PLE Overview](https://dbarton.grafana.net/d/svg-ple-dashboard)
- [Grafana: Executive Enrichment](https://dbarton.grafana.net/d/executive-enrichment-monitoring)

### Configuration

- [[global-config.yaml]] - Master configuration
- [[GLOBAL_CONFIG_IMPLEMENTATION]] - Implementation details
- [[plugins-setup]] - Obsidian plugin configuration

---

## 💡 Task Management Tips

### Using Obsidian Dataview

This task file is auto-queried by [[DOCTRINE_DASHBOARD]]:

```markdown
\`\`\`dataview
TASK
FROM "docs/tasks"
WHERE !completed
SORT file.mtime DESC
\`\`\`
```

### Task Syntax

- `- [ ]` = Incomplete task (shows in dashboard)
- `- [x]` = Complete task (hidden from dashboard)
- `- [>]` = Forwarded task (moved to future date)
- `- [!]` = Important task (highlighted)

### GitHub Projects Integration

1. Create issue in GitHub: "Finalize Grafana connection"
2. Link to this task file
3. Update checkbox when complete
4. GitHub Projects auto-updates status

### Task Templates

**New Task**:
```markdown
- [ ] **Task Title** (Priority: High/Medium/Low)
  - **Status**: Not Started / In Progress / Blocked
  - **Assigned**: Name
  - **Due**: YYYY-MM-DD
  - **Related**: [[Doctrine-File]] or [[Schema-File]]
```

---

## 🆘 Support

### Task Questions

- **Architecture**: Review [[PLE-Doctrine]]
- **BIT Scoring**: Review [[BIT-Doctrine]]
- **Movement Detection**: Review [[Talent-Flow-Doctrine]]
- **Database**: Review schema files in `doctrine/schemas/`

### Report Issues

- **Doctrine Issues**: Open GitHub issue with label `doctrine`
- **Schema Bugs**: Open GitHub issue with label `schema`
- **Task Blockers**: Escalate in Slack #svg-ple channel

---

**Last Updated**: 2025-11-07
**Maintained By**: Barton Outreach Team
**Syncs To**: [[DOCTRINE_DASHBOARD]] (via Dataview)
