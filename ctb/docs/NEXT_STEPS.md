<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs
Barton ID: 06.01.00
Unique ID: CTB-1BA2485B
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
-->

# Next Steps - Doctrinal Compliance Fixes

This document outlines the remaining steps to achieve 100% compliance with the Outreach Doctrine A→Z standard.

**Current Status**: 90%+ compliance (documentation fixes complete, database migration pending)

---

## 🚀 Automated Method (Recommended)

**ONE-COMMAND COMPLETION** via Composio MCP:

```bash
# Complete all remaining fixes automatically (100% compliance in ~30 seconds)
npm run compliance:complete

# Dry run first (recommended)
npm run compliance:complete -- --dry-run
```

This automated script executes all remaining fixes through Composio MCP:
- ✅ Creates `shq_error_log` table via Composio database connector
- ✅ Refreshes schema map automatically
- ✅ Tests error sync script
- ✅ Generates compliance report

**Prerequisites**:
- Composio MCP server running on port 3001
- `COMPOSIO_MCP_URL` environment variable set
- `COMPOSIO_API_KEY` environment variable set (if required)
- Neon database connected to Composio

**See**: `scripts/complete-compliance-via-composio.ts` for implementation details

---

## 📋 Manual Method (Alternative)

If you prefer manual execution or Composio is not available:

### Phase 1: Database Migration (REQUIRED)

The `shq_error_log` table must be created before the error monitoring system can function.

### Step 1: Set DATABASE_URL

```bash
# Set your Neon PostgreSQL connection string
export DATABASE_URL="postgresql://user:password@host/database?sslmode=require"

# Verify it's set
echo $DATABASE_URL
```

### Step 2: Run Migration

```bash
# Execute the error log table creation script
psql $DATABASE_URL -f infra/2025-10-20_create_shq_error_log.sql

# Expected output:
# CREATE TABLE
# CREATE INDEX (6 indexes)
# CREATE FUNCTION
# CREATE TRIGGER
# COMMENT (multiple comments)
# status | index_count
# --------+-------------
# shq_error_log table created successfully | 6
```

### Step 3: Verify Table Creation

```bash
# Connect to database and check table exists
psql $DATABASE_URL -c "\d shq_error_log"

# Expected output: Table structure with all columns and indexes
```

---

## Phase 2: Schema Documentation Update

After creating the table, regenerate the schema map to include `shq_error_log`:

```bash
# Regenerate schema map (includes new error log table)
npm run schema:refresh

# Verify shq_error_log appears in schema_map.json
grep -A 5 "shq_error_log" docs/schema_map.json
```

**Expected Output**:
```json
"shq_error_log": {
  "description": "Centralized error tracking for all agents and processes (Barton Doctrine v1.3.2)",
  "columns": {
    "id": { "type": "SERIAL", "primary_key": true },
    "error_id": { "type": "TEXT", "unique": true },
    ...
  }
}
```

---

## Phase 3: Test Error Sync Script

Test the Firebase sync script to ensure it connects properly:

```bash
# Dry run (no actual writes)
npm run sync:errors -- --dry-run --limit 5

# Expected output if no errors exist:
# 🚀 Starting Firebase Error Sync...
# ⚠️  DRY RUN MODE - No data will be written
# 📥 Fetching up to 5 unsynced errors from Neon...
# ✅ Fetched 0 unsynced error(s)
# ✨ No unsynced errors found. All up to date!
# ✅ Sync completed successfully
```

### Test with Sample Error (Optional)

If you want to test end-to-end, insert a sample error:

```sql
-- Insert test error
INSERT INTO shq_error_log (
    agent_name,
    process_id,
    unique_id,
    severity,
    message
) VALUES (
    'Doctrine Maintenance Agent',
    'Test Error Monitoring',
    '04.01.99.10.01000.999',
    'info',
    'Test error inserted to verify sync functionality'
);

-- Verify insertion
SELECT error_id, severity, message FROM shq_error_log WHERE agent_name = 'Doctrine Maintenance Agent';
```

Then run the sync script again (without `--dry-run`):

```bash
npm run sync:errors -- --limit 5

# Expected output:
# 🚀 Starting Firebase Error Sync...
# 📥 Fetched 1 unsynced error(s)
# [1/1] Syncing <error_id>... (info → #28A745)
#   ✅ Successfully synced <error_id>
# 📊 SYNC SUMMARY: 1 fetched, 1 synced, 0 failed
# ✅ Sync completed successfully
```

---

## Phase 4: Verify Dashboards

### Firebase Dashboard

1. Navigate to Firebase Console → Firestore → `error_log` collection
2. Verify test error appears with all fields (including `color: "#28A745"`)
3. Check dashboard widgets in `firebase/error_dashboard_spec.json` configuration

### Lovable.dev Dashboard

1. Open Lovable.dev project sidebar
2. Navigate to Error Center widget
3. Verify real-time error list displays with color-coded badges
4. Test "Mark Resolved" action

---

## Phase 5: Run Compliance Audit

Re-run the doctrinal compliance audit to verify 100% compliance:

```bash
# The audit checks will now pass for:
# - Schema Validation: ✅ 100% (shq_error_log table exists)
# - Error Logging: ✅ 100% (table created, sync tested)
# - Documentation Cross-Links: ✅ 100% (Section 14 added)

# Expected final compliance: 100%
```

---

## Phase 6: Production Deployment

Once 100% compliance is achieved:

### 1. Environment Variables

Set required environment variables in Vercel:

```bash
# In Vercel Project Settings → Environment Variables
NEON_DATABASE_URL=postgresql://...
COMPOSIO_MCP_URL=http://localhost:3001
COMPOSIO_API_KEY=your_api_key_here
FIREBASE_PROJECT_ID=barton-outreach
```

### 2. Automated Sync

Set up automated error sync (choose one option):

**Option A: Vercel Cron Job** (Recommended)
```json
// vercel.json
{
  "crons": [{
    "path": "/api/sync-errors",
    "schedule": "*/1 * * * *"
  }]
}
```

**Option B: Firebase Scheduled Function**
```bash
cd firebase/functions
firebase deploy --only functions:scheduledErrorSync
```

**Option C: External Cron Service**
```bash
# Use cron-job.org or similar to hit endpoint every 60 seconds
curl -X POST https://your-domain.vercel.app/api/sync-errors
```

### 3. Monitor Dashboard

- Firebase Dashboard: Real-time error tracking with 11 widgets
- Lovable.dev: Sidebar integration with 6 sections
- Alert channels: Configure Slack/email/SMS in dashboard spec

---

## Troubleshooting

### Migration Fails

**Error**: `relation "shq_error_log" already exists`
```bash
# Drop and recreate (CAUTION: destroys data)
psql $DATABASE_URL -c "DROP TABLE IF EXISTS shq_error_log CASCADE;"
psql $DATABASE_URL -f infra/2025-10-20_create_shq_error_log.sql
```

### Sync Script Fails

**Error**: `NEON_DATABASE_URL not set`
```bash
# Set environment variable
export NEON_DATABASE_URL="postgresql://..."
npm run sync:errors -- --dry-run
```

**Error**: `Firebase write failed`
```bash
# Check Composio MCP is running
curl http://localhost:3001/mcp/health

# Verify Firebase credentials
composio integration list | grep firebase
```

### Schema Refresh Fails

**Error**: `Cannot find module 'tsx'`
```bash
# Install dependencies
npm install --save-dev tsx
npm run schema:refresh
```

---

## Compliance Checklist

Use this checklist to track progress toward 100% compliance:

- [x] Create `shq_error_log` SQL migration file
- [ ] Run migration against Neon database
- [ ] Verify table creation with `\d shq_error_log`
- [ ] Refresh schema map with `npm run schema:refresh`
- [ ] Verify `shq_error_log` in `docs/schema_map.json`
- [x] Add cross-links to `outreach-doctrine-a2z.md` (Section 14)
- [x] Add cross-links to `error_handling.md`
- [x] Add cross-reference comments to `sync-errors-to-firebase.ts`
- [x] Archive legacy Render files to `archive/render-legacy/`
- [x] Update README.md with deployment platform clarification
- [ ] Test sync script with `npm run sync:errors -- --dry-run`
- [ ] Insert test error and verify sync
- [ ] Verify Firebase dashboard displays errors
- [ ] Configure automated sync (cron/scheduled function)
- [ ] Run final compliance audit
- [ ] Achieve 100% compliance

---

## Quick Commands Summary

```bash
# 1. Database setup
export DATABASE_URL="postgresql://..."
psql $DATABASE_URL -f infra/2025-10-20_create_shq_error_log.sql

# 2. Schema refresh
npm run schema:refresh

# 3. Test sync (dry run)
npm run sync:errors -- --dry-run --limit 5

# 4. Real sync
npm run sync:errors

# 5. Verify in Firestore
# Open Firebase Console → Firestore → error_log collection

# 6. Check compliance
cat docs/audit_report.md
```

---

## Support

If you encounter issues:

1. Review [Troubleshooting Guide](./docs/TROUBLESHOOTING.md)
2. Check [Error Handling Guide](./docs/error_handling.md)
3. Consult [Audit Report](./docs/audit_report.md) for detailed findings
4. Review [Outreach Doctrine A→Z](./docs/outreach-doctrine-a2z.md) for system overview

---

**Document Version**: 1.0
**Created**: 2025-10-20
**Purpose**: Guide for completing doctrinal compliance fixes
**Related**: [docs/audit_report.md](./docs/audit_report.md) - Fix 1, 2, 3, 4
