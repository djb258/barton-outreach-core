# Barton Outreach Doctrine - Machine Ingestion Guide

**Manifest Entry**: [./manifest.json](./manifest.json)

## 🎯 Purpose

This directory contains machine-ingestible metadata for the complete Barton Outreach Doctrine A→Z system. It is designed for:

- **LOMs (Large Output Models)**: Claude, GPT, Gemini, Abacus, and other AI agents
- **HEIR Agents**: All 12 specialized agents in the HEIR system
- **Doctrine Maintenance**: Automated validation and compliance checking
- **Onboarding**: Quick context loading for new agents and developers

## 📋 Quick Start

### For LOMs and Agents

1. **Load Manifest**: Start by reading `manifest.json` to understand:
   - System purpose and architecture
   - Schema and tool registry
   - Automation hooks and scripts
   - Dashboard mappings and visualization
   - Doctrine version and compliance status

2. **Load Core Documentation**: Follow the `entry_docs` path:
   - `docs/outreach-doctrine-a2z.md` - Complete system documentation (14 sections)
   - `docs/error_handling.md` - Error monitoring and resolution guide
   - `docs/schema_map.json` - Database schema with 8 schemas, 15+ tables

3. **Validate Environment**: Before executing operations:
   ```bash
   # Check environment variables
   echo $COMPOSIO_MCP_URL
   echo $NEON_DATABASE_URL
   echo $FIREBASE_PROJECT_ID

   # Test Composio MCP connectivity
   curl http://localhost:3001/mcp/health

   # Validate schema
   npm run schema:refresh
   ```

4. **Register Your Process**: Use Barton Doctrine numbering:
   ```
   unique_id: XX.XX.XX.XX.XXXXX.XXX
   process_id: [Verb] + [Object] + [Context]
   ```

5. **Log Errors Properly**: All errors must be logged to `shq_error_log`:
   ```sql
   INSERT INTO shq_error_log (
     agent_name, process_id, unique_id,
     severity, message, stack_trace
   ) VALUES (
     'Your Agent Name',
     'Your Process ID',
     'Your Unique ID',
     'error',  -- info, warning, error, critical
     'Error description',
     'Stack trace if available'
   );
   ```

## 🗂️ Manifest Contents

The `manifest.json` file contains:

### 1. Doctrine Metadata
- Name, version, compliance score
- Audit report and summary locations
- Entry documentation paths

### 2. Structure Definition
- Altitude-based architecture (30k → 1k)
- Core directories and schemas
- Main database schemas (8 total)

### 3. Tool Registry
- 9 registered tools (Neon, Apify, VibeOS, etc.)
- Severity color doctrine (4 levels)
- Tool IDs and purposes

### 4. Automation Scripts
- `schema:refresh` - Regenerate schema map
- `sync:errors` - Sync errors to Firebase
- Cron job definitions

### 5. Visualization Config
- Firebase dashboard (11 widgets)
- Lovable dashboard (6 sections)
- Dashboard tabs and refresh intervals

### 6. Database Schema
- Primary database: Neon PostgreSQL
- 8 schemas, 15 tables
- Error table: `shq_error_log` (8 indexes)

### 7. Integration Requirements
- Composio MCP as integration bus
- Required environment variables
- Prohibited integrations (Render)

### 8. Monitoring Setup
- Dashboard types and locations
- Severity levels and alert channels
- Data flow: Neon → Composio → Firebase → Dashboard

### 9. Compliance Status
- Current score: 100%
- Last audit: 2025-10-20
- Next audit due: 2025-10-21

### 10. Usage Notes
- Specific guidance for LOMs, agents, and humans
- Validation requirements
- Best practices

## 🚀 Automated Validation

Before making any changes to the system:

```bash
# Run compliance validation
npm run compliance:complete -- --dry-run

# Check schema integrity
npm run schema:refresh

# Test error sync
npm run sync:errors -- --dry-run --limit 5
```

## 📊 Key Metrics (as of commit bbc1c67)

- **Compliance Score**: 100%
- **Database Tables**: 15
- **Automation Scripts**: 3
- **Dashboard Widgets**: 17 (11 Firebase + 6 Lovable)
- **Tool Registry**: 9 tools
- **Schemas**: 8 (company, people, marketing, intake, vault, bit, ple, shq)
- **Indexes**: 8 (on shq_error_log alone)

## 🔗 Related Documentation

### Primary Documentation
- [Outreach Doctrine A→Z](../docs/outreach-doctrine-a2z.md) - Complete system guide
- [Error Handling Guide](../docs/error_handling.md) - Error monitoring and resolution
- [Schema Map](../docs/schema_map.json) - Database structure

### Implementation Files
- [Error Sync Script](../scripts/sync-errors-to-firebase.ts)
- [Schema Refresh Script](../scripts/refresh-schema-map.ts)
- [Compliance Script](../scripts/complete-compliance-via-composio.ts)

### Database Files
- [Error Log Migration](../infra/2025-10-20_create_shq_error_log.sql)

### Configuration Files
- [Firebase Dashboard Spec](../firebase/error_dashboard_spec.json)
- [Lovable Dashboard Layout](../lovable/dashboard_layout.json)
- [Composio Integration](../COMPOSIO_INTEGRATION.md)
- [MCP Registry](../config/mcp_registry.json)

### Audit & Compliance
- [Audit Report](../docs/audit_report.md) - Initial audit (81.25%)
- [Final Audit Summary](../FINAL_AUDIT_SUMMARY.md) - Journey to 100%
- [Compliance Status](../COMPLIANCE_STATUS.md) - Current status

## ⚠️ Critical Rules

### MUST DO
✅ Read manifest.json FIRST before any operations
✅ Use Composio MCP for ALL external service integrations
✅ Register unique_id and process_id before execution
✅ Log ALL errors to shq_error_log with proper severity
✅ Follow color doctrine for severity levels
✅ Test with --dry-run before live execution

### MUST NOT DO
❌ Create direct API integrations (use Composio MCP)
❌ Skip error logging for any operation
❌ Use Render deployment platform (deprecated)
❌ Modify database schema without migration script
❌ Execute operations without unique_id/process_id
❌ Ignore validation failures

## 🎓 Learning Path

### For First-Time LOMs
1. Read `manifest.json` (5 min)
2. Read `docs/outreach-doctrine-a2z.md` Section 1-3 (10 min)
3. Review `docs/schema_map.json` (5 min)
4. Test Composio MCP connectivity (2 min)
5. Run validation scripts (3 min)

**Total Onboarding Time**: ~25 minutes

### For Experienced Agents
1. Load `manifest.json` (instant context)
2. Verify compliance score = 100%
3. Check last_audit date
4. Review any changes since last session

**Total Refresh Time**: ~2 minutes

## 📞 Support

For issues or questions:
1. Check [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)
2. Review [Error Handling Guide](../docs/error_handling.md)
3. Consult [Audit Report](../docs/audit_report.md)
4. Reference [Outreach Doctrine A→Z](../docs/outreach-doctrine-a2z.md)

---

**Manifest Version**: 1.0.0
**Doctrine Version**: 1.3.2
**Last Updated**: 2025-10-20
**Commit**: bbc1c67
**Status**: Production-ready, 100% compliant

🤖 Generated for machine ingestion and automated validation
