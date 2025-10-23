<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/analysis
Barton ID: 06.01.01
Unique ID: CTB-F2B5E2E6
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
-->

# 🚀 Intelligence Tables Migration Guide

**Status**: ✅ Migration files created and committed
**Date**: 2025-10-22
**Commit**: b33c134

---

## 📋 What Was Created

Two new Barton Doctrine-compliant migration files:

1. **`2025-10-22_create_marketing_company_intelligence.sql`**
   - Barton ID: 06.01.01
   - Purpose: Track company intelligence signals for BIT (Buyer Intent Tool)
   - Features: 7 intelligence types, confidence scoring, impact levels
   - Helper functions: 3 insert/query functions

2. **`2025-10-22_create_marketing_people_intelligence.sql`**
   - Barton ID: 06.01.01
   - Purpose: Track executive movements for PLE (Promoted Lead Enrichment)
   - Features: 5 change types, verification workflow, audit trail
   - Helper functions: 5 insert/query/detection functions

---

## 🎯 Migration Execution - COMPOSIO MCP ONLY

**🚨 GLOBAL POLICY**: All database operations MUST go through Composio MCP. Direct database connections are FORBIDDEN.

**Authority**: imo-creator repo global configuration
**See**: `analysis/COMPOSIO_MCP_GLOBAL_POLICY.md`

### Via Composio MCP (REQUIRED METHOD)

```bash
# From apps/outreach-process-manager/scripts directory
cd apps/outreach-process-manager/scripts
node execute-intelligence-migrations-via-composio.js
```

**What This Does**:
1. Loads migration SQL files
2. Posts to `http://localhost:3001/tool?user_id={COMPOSIO_USER_ID}`
3. Uses `neon_execute_sql` Composio tool
4. Includes HEIR/ORBT metadata for Barton Doctrine compliance
5. Returns detailed execution results

**Requirements**:
- Composio MCP server running on `localhost:3001`
- `COMPOSIO_USER_ID` in environment variables (required after Nov 1st, 2025)
- `NEON_DATABASE_URL` in environment variables

**Environment Variables**:
```bash
COMPOSIO_MCP_URL=http://localhost:3001/tool
COMPOSIO_USER_ID=usr_your_generated_id
NEON_DATABASE_URL=postgresql://...
```

---

## ✅ Verification Queries

After running migrations, verify everything was created correctly:

### Check Tables Exist

```sql
SELECT
    table_schema,
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_schema = t.table_schema
     AND table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_name IN ('company_intelligence', 'people_intelligence')
  AND table_schema = 'marketing'
ORDER BY table_name;
```

**Expected Result**: 2 rows (both tables with appropriate column counts)

### Check Indexes

```sql
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE tablename IN ('company_intelligence', 'people_intelligence')
  AND schemaname = 'marketing'
ORDER BY tablename, indexname;
```

**Expected Result**: ~14 indexes total (7 per table)

### Check Helper Functions

```sql
SELECT
    proname as function_name,
    pg_get_function_arguments(oid) as arguments
FROM pg_proc
WHERE proname ILIKE '%intelligence%'
  AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'marketing')
ORDER BY proname;
```

**Expected Result**: 8 functions total
- `generate_company_intelligence_barton_id()`
- `generate_people_intelligence_barton_id()`
- `insert_company_intelligence(...)`
- `insert_people_intelligence(...)`
- `get_company_intelligence(...)`
- `get_people_intelligence(...)`
- `get_high_impact_signals(...)`
- `get_recent_executive_movements(...)`
- `detect_title_changes()`
- `get_unverified_intelligence(...)`

### Test Barton ID Generation

```sql
-- Test company intelligence ID generation
SELECT marketing.generate_company_intelligence_barton_id();
-- Expected format: 04.04.03.XX.XXXXX.XXX

-- Test people intelligence ID generation
SELECT marketing.generate_people_intelligence_barton_id();
-- Expected format: 04.04.04.XX.XXXXX.XXX
```

---

## 🧪 Testing the Tables

### Insert Test Company Intelligence

```sql
-- Assuming you have a company in company_master
SELECT marketing.insert_company_intelligence(
    '04.04.01.84.48151.001',  -- Replace with actual company_unique_id
    'funding_round',
    '2025-10-20'::DATE,
    'Series B funding round of $50M from Acme Ventures',
    'https://techcrunch.com/example',
    'news',
    0.95,
    'high',
    '{"amount": "$50M", "round": "Series B", "investors": ["Acme Ventures"]}'::jsonb
);
```

### Insert Test People Intelligence

```sql
-- Assuming you have a person in people_master
SELECT marketing.insert_people_intelligence(
    '04.04.02.84.48151.001',  -- Replace with actual person unique_id
    '04.04.01.84.48151.001',  -- Replace with actual company unique_id
    'promotion',
    'VP of Sales',
    'Chief Revenue Officer',
    NULL,
    NULL,
    '2025-10-01'::TIMESTAMPTZ,
    TRUE,
    'linkedin_confirmed'
);
```

### Query Recent Signals

```sql
-- Get high-impact company signals from last 7 days
SELECT * FROM marketing.get_high_impact_signals(7);

-- Get recent executive movements from last 30 days
SELECT * FROM marketing.get_recent_executive_movements(30);
```

---

## 📊 Schema Compliance Update

### Before Migration
- ✅ 1 Fully Compliant: `marketing.company_slot`
- ⚠️ 3 Partial/Alternative: audit_log, validation_queue, outreach_history
- ❌ 2 Missing: **company_intelligence**, **people_intelligence**

### After Migration
- ✅ 3 Fully Compliant: `marketing.company_slot`, `marketing.company_intelligence`, `marketing.people_intelligence`
- ⚠️ 3 Partial/Alternative: audit_log, validation_queue, outreach_history
- ❌ 0 Missing: **ALL CRITICAL TABLES PRESENT**

**Overall Compliance**: **50% Fully Compliant** | **50% Partial** | **0% Missing**

---

## 🎯 Next Steps

1. **Run Migrations** (choose method above)

2. **Verify Tables Created** (run verification queries)

3. **Update Enrichment Workflow**
   - Integrate intelligence tracking into Apify enrichment process
   - Add intelligence logging to campaign triggers
   - Enable BIT signal detection

4. **Test Executive Enrichment**
   - Run 3-company trial with Apify
   - Verify intelligence tables receive data
   - Test BIT and PLE triggers

5. **Address Remaining Schema Issues** (Optional)
   - Resolve `shq.audit_log` vs `marketing.unified_audit_log`
   - Consolidate validation queue tables
   - Create unified `marketing.outreach_history` view

---

## 🚨 Troubleshooting

### Composio MCP Server Not Running

If you see connection refused errors:
```bash
# Start Composio MCP server
cd path/to/imo-creator/mcp-server
node server.js
```

### Missing user_id Parameter

If migrations fail after November 1st, 2025:
- Add `COMPOSIO_USER_ID` to `.env` file
- Generate via Composio Platform or API (see COMPOSIO_INTEGRATION.md)

### Tool Not Found

If you see "Unknown tool: neon_execute_sql":
- Verify Composio MCP server is up to date
- Check available tools: `curl http://localhost:3001/tools`
- Ensure Neon integration is configured in imo-creator repo

### Permission Issues

If you see permission denied errors:
- Verify `NEON_DATABASE_URL` has correct credentials
- Check that marketing schema exists
- Ensure Composio has database access configured

---

## 📚 Files Created

1. `apps/outreach-process-manager/migrations/2025-10-22_create_marketing_company_intelligence.sql` (305 lines)
2. `apps/outreach-process-manager/migrations/2025-10-22_create_marketing_people_intelligence.sql` (428 lines)
3. `analysis/SCHEMA_COMPLIANCE_AUDIT.md` (895 lines)
4. `analysis/run_intelligence_migrations.js` (Node.js migration runner)
5. `analysis/INTELLIGENCE_MIGRATION_GUIDE.md` (this file)

**Total Added**: 1,628+ lines of SQL and documentation

---

## ✅ Success Criteria

After running migrations, you should have:

- [x] `marketing.company_intelligence` table created
- [x] `marketing.people_intelligence` table created
- [x] All indexes created (14 total)
- [x] All helper functions created (10 total)
- [x] All triggers created (timestamp auto-update)
- [x] All CHECK constraints enforcing Barton ID format
- [x] All foreign keys properly referenced
- [x] Ready for BIT and PLE integration

---

**Migration Status**: ✅ READY TO DEPLOY
**Doctrine Compliance**: ✅ CRITICAL TABLES COMPLETE
**Next Action**: Choose migration method and execute
