# Database Migrations - Quick Reference

## Summary

All migrations successfully applied to **Marketing DB** on Neon.

**Database:** white-union-26418370 (aws-us-east-1)
**Total Migrations:** 4
**Status:** ✅ All Complete
**Date:** 2025-10-24

---

## Migration Overview

| # | Name | Status | Records Affected |
|---|------|--------|-----------------|
| 001 | Add Validation + State Tracking Columns | ✅ Complete | 446 companies |
| 002 | Create Validation Log + Company Slots | ✅ Complete | 446 slots created |
| 003 | Create Doctrinal Promotion Function | ✅ Complete | Function + Schema |
| 004 | Add email_verified Column | ✅ Complete | 1 column + index |

---

## Key Achievements

### ✅ Database is Now Production-Ready For:

1. **Batch Import Tracking**
   - `import_batch_id` on both intake and master tables
   - Can track source of every company

2. **Data Validation Workflow**
   - `validated` flag and timestamps
   - `shq_validation_log` for audit trail
   - Validation notes for debugging

3. **State-Level Provenance**
   - `state_abbrev` for geographic tracking
   - Ready for multi-state expansion

4. **Quality Scoring**
   - `data_quality_score` (0-100) on master table
   - Can prioritize high-quality leads

5. **Executive Enrichment Ready**
   - 446 company slots created
   - `people_master` constraint satisfied
   - Ready for Apify/LinkedIn scraping

6. **Database Cleanup Complete (2025-10-24)**
   - ✅ Archived 45 obsolete tables (48,687 rows)
   - ✅ Dropped 5 empty schemas
   - ✅ 90% reduction in active tables (50 → 5)
   - ✅ Only core doctrinal tables remain
   - 📦 All obsolete data safely archived in `archive` schema

---

## Files

- **001_add_validation_state_tracking.sql** - Validation columns
- **002_create_validation_log_slots.sql** - Slots & logging
- **003_create_promotion_function.sql** - Automated promotion function
- **004_add_email_verified.sql** - Email verification tracking
- **MIGRATION_LOG.md** - Complete documentation
- **SCHEMA_VERIFICATION_REPORT.md** - Schema compliance audit
- **DATABASE_CLEANUP_REPORT.md** - Database cleanup audit (45 tables archived)
- **README.md** - This file

---

## Quick Commands

### Connect to Database
```bash
psql "postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech/Marketing%20DB?channel_binding=require&sslmode=require"
```

### Check Migration Status
```sql
-- Verify validation columns exist
SELECT column_name FROM information_schema.columns
WHERE table_schema = 'intake' AND table_name = 'company_raw_intake'
AND column_name IN ('validated', 'state_abbrev', 'import_batch_id');

-- Verify slots exist
SELECT COUNT(*) as total_slots FROM marketing.company_slots;

-- Check validation log
SELECT * FROM shq_validation_log ORDER BY executed_at DESC;
```

### View Slot Assignments
```sql
SELECT
  cm.company_name,
  cm.company_unique_id,
  cs.company_slot_unique_id,
  cs.slot_label
FROM marketing.company_master cm
JOIN marketing.company_slots cs ON cm.company_unique_id = cs.company_unique_id
LIMIT 10;
```

### Promote Validated Records
```sql
-- Promote all validated records from a batch
SELECT shq.promote_company_records('20251024-WV-BATCH1', 'system-auto');

-- Check promotion results
SELECT * FROM shq_validation_log ORDER BY executed_at DESC LIMIT 5;
```

### View Archive Status
```sql
-- View all archived tables
SELECT
  original_schema || '.' || original_table as original_location,
  row_count,
  archived_at,
  notes
FROM archive.archive_log
ORDER BY archived_at DESC;

-- Archive summary by schema
SELECT
  original_schema,
  COUNT(*) as tables_archived,
  SUM(row_count) as total_rows
FROM archive.archive_log
GROUP BY original_schema
ORDER BY total_rows DESC;

-- Current active tables
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema IN ('intake', 'marketing', 'public')
  AND table_type = 'BASE TABLE'
ORDER BY table_schema, table_name;
```

---

## Next Steps (Recommended)

### 1. Bulk Update State Abbreviations
```sql
UPDATE intake.company_raw_intake
SET state_abbrev = 'WV'
WHERE company_state = 'West Virginia';

UPDATE marketing.company_master cm
SET state_abbrev = 'WV'
FROM intake.company_raw_intake cri
WHERE cm.source_record_id = cri.id::text;
```

### 2. Set Batch IDs
```sql
UPDATE intake.company_raw_intake
SET import_batch_id = 'LEGACY-2025-05-19'
WHERE import_batch_id IS NULL;

UPDATE marketing.company_master
SET import_batch_id = 'LEGACY-2025-05-19'
WHERE import_batch_id IS NULL;
```

### 3. Calculate Data Quality Scores
```sql
UPDATE marketing.company_master
SET data_quality_score =
  (CASE WHEN website_url IS NOT NULL AND website_url != 'https://example.com' THEN 30 ELSE 0 END +
   CASE WHEN linkedin_url IS NOT NULL THEN 30 ELSE 0 END +
   CASE WHEN company_phone IS NOT NULL THEN 20 ELSE 0 END +
   CASE WHEN industry IS NOT NULL THEN 20 ELSE 0 END)
WHERE data_quality_score IS NULL;
```

### 4. Add Performance Indexes
```sql
CREATE INDEX IF NOT EXISTS idx_intake_batch_id ON intake.company_raw_intake(import_batch_id);
CREATE INDEX IF NOT EXISTS idx_intake_validated ON intake.company_raw_intake(validated);
CREATE INDEX IF NOT EXISTS idx_intake_state ON intake.company_raw_intake(state_abbrev);

CREATE INDEX IF NOT EXISTS idx_master_batch_id ON marketing.company_master(import_batch_id);
CREATE INDEX IF NOT EXISTS idx_master_state ON marketing.company_master(state_abbrev);
CREATE INDEX IF NOT EXISTS idx_master_quality ON marketing.company_master(data_quality_score);

CREATE INDEX IF NOT EXISTS idx_company_slots_company_id ON marketing.company_slots(company_unique_id);
CREATE INDEX IF NOT EXISTS idx_validation_log_executed ON shq_validation_log(executed_at DESC);
```

### 5. Start Executive Enrichment
Now that slots exist, you can safely insert executives:
```sql
INSERT INTO marketing.people_master (
  unique_id,
  company_unique_id,
  company_slot_unique_id,
  first_name,
  last_name,
  title,
  email,
  linkedin_url,
  source_system
)
SELECT
  '04.04.02.' ||
  LPAD((EXTRACT(EPOCH FROM NOW())::BIGINT % 100)::TEXT, 2, '0') || '.' ||
  LPAD((RANDOM() * 100000)::INT::TEXT, 5, '0') || '.' ||
  '001' as unique_id,
  cm.company_unique_id,
  cs.company_slot_unique_id,
  'John' as first_name,
  'Smith' as last_name,
  'CEO' as title,
  'john.smith@example.com' as email,
  'https://linkedin.com/in/johnsmith' as linkedin_url,
  'apify_leads_finder' as source_system
FROM marketing.company_master cm
JOIN marketing.company_slots cs ON cm.company_unique_id = cs.company_unique_id
WHERE cm.company_name = 'Concord University';
```

---

## Database Schema Summary

### Tables Modified
- ✅ `intake.company_raw_intake` (+6 columns)
- ✅ `marketing.company_master` (+5 columns)

### Tables Created
- ✅ `shq_validation_log` (9 columns)
- ✅ `marketing.company_slots` (5 columns, 446 records)

### Total New Columns: 20
### Total New Records: 447 (446 slots + 1 test log entry)

---

## Troubleshooting

### If slot assignment fails for new companies
```sql
-- Manually create slot
INSERT INTO marketing.company_slots (
  company_slot_unique_id,
  company_unique_id,
  slot_type,
  slot_label
) VALUES (
  '04.04.05.' || /* generate Barton ID */,
  'COMPANY_BARTON_ID_HERE',
  'default',
  'Primary Slot'
);
```

### If validation log query fails
```sql
-- Check if table exists
SELECT * FROM information_schema.tables
WHERE table_name = 'shq_validation_log';

-- If missing, re-run migration 002
```

---

**Last Updated:** 2025-10-24
**Maintained By:** Claude Code
**Documentation:** See MIGRATION_LOG.md for complete details
