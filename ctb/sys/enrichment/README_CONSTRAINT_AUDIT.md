# PLE Constraint Audit - Quick Reference

**Barton ID:** 04.04.02.04.50000.000
**Last Updated:** 2025-11-26
**Status:** Initial Audit Complete - Data Cleanup Required

---

## TLDR - What You Need to Know

1. **82% of NOT NULL constraints are compliant** (9/11) - Need to add NOT NULL to `created_at` columns
2. **0% of CHECK constraints exist** (0/4) - All business validation rules are missing
3. **100% of UNIQUE constraints are compliant** (3/3) - No duplicates found
4. **16 data violations found** - Must fix before adding constraints
5. **71 existing CHECK constraints** - Auto-generated from migrations, plus some business rules

---

## Files Overview

### Reports (Root Directory)

```
C:/Users/CUSTOM PC/Desktop/Cursor Builds/barton-outreach-core/
├── PLE_CONSTRAINT_AUDIT_REPORT.md       # Detailed audit results with all tables
└── PLE_CONSTRAINT_AUDIT_SUMMARY.md      # Executive summary with action plan
```

### Scripts (ctb/sys/enrichment/)

```
C:/Users/CUSTOM PC/Desktop/Cursor Builds/barton-outreach-core/ctb/sys/enrichment/
├── ple_constraint_audit.js                 # Node.js audit script (REUSABLE)
├── ple_constraint_migration.sql            # SQL to add missing constraints
├── ple_data_violations_detailed.sql        # Query to find specific violations
└── README_CONSTRAINT_AUDIT.md              # This file
```

---

## Quick Start Guide

### Step 1: Review the Audit Report

```bash
# Open the executive summary
code "C:/Users/CUSTOM PC/Desktop/Cursor Builds/barton-outreach-core/PLE_CONSTRAINT_AUDIT_SUMMARY.md"

# Open the detailed report
code "C:/Users/CUSTOM PC/Desktop/Cursor Builds/barton-outreach-core/PLE_CONSTRAINT_AUDIT_REPORT.md"
```

### Step 2: Identify Specific Violations

**Option A: Using Node.js (Easiest)**

```bash
cd "C:/Users/CUSTOM PC/Desktop/Cursor Builds/barton-outreach-core"
node ctb/sys/enrichment/ple_constraint_audit.js

# This regenerates all reports with current data
```

**Option B: Using SQL Queries**

```bash
# Connect to Neon
psql "postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing%20DB?sslmode=require"

# Run violation detection
\i C:/Users/CUSTOM PC/Desktop/Cursor Builds/barton-outreach-core/ctb/sys/enrichment/ple_data_violations_detailed.sql
```

**Option C: Using DBeaver/pgAdmin**

1. Open DBeaver/pgAdmin
2. Connect to Neon PostgreSQL (credentials in .env)
3. Open `ple_data_violations_detailed.sql`
4. Execute and review results

### Step 3: Clean Up Data

**Review the violations, then execute cleanup:**

```sql
-- Example: Fix employee_count violations (set to NULL)
BEGIN;

UPDATE marketing.company_master
SET employee_count = NULL, updated_at = NOW()
WHERE employee_count IS NOT NULL
AND (employee_count < 50 OR employee_count > 2000);

-- Verify
SELECT COUNT(*) as remaining_violations
FROM marketing.company_master
WHERE employee_count IS NOT NULL
AND (employee_count < 50 OR employee_count > 2000);

-- If 0, commit. Otherwise, rollback.
COMMIT;
-- ROLLBACK;
```

**Fix created_at NULL values:**

```sql
BEGIN;

-- Use promoted_from_intake_at if available
UPDATE marketing.company_master
SET created_at = promoted_from_intake_at, updated_at = NOW()
WHERE created_at IS NULL AND promoted_from_intake_at IS NOT NULL;

UPDATE marketing.people_master
SET created_at = promoted_from_intake_at, updated_at = NOW()
WHERE created_at IS NULL AND promoted_from_intake_at IS NOT NULL;

-- Use NOW() for remaining
UPDATE marketing.company_master
SET created_at = NOW(), updated_at = NOW()
WHERE created_at IS NULL;

UPDATE marketing.people_master
SET created_at = NOW(), updated_at = NOW()
WHERE created_at IS NULL;

-- Verify 0 remaining
SELECT COUNT(*) FROM marketing.company_master WHERE created_at IS NULL;
SELECT COUNT(*) FROM marketing.people_master WHERE created_at IS NULL;

COMMIT;
-- ROLLBACK;
```

### Step 4: Re-run Audit (Verify 0 Violations)

```bash
cd "C:/Users/CUSTOM PC/Desktop/Cursor Builds/barton-outreach-core"
node ctb/sys/enrichment/ple_constraint_audit.js

# Check the summary - should show 0 violations
```

### Step 5: Add Constraints

**Only after Step 4 shows 0 violations:**

```bash
# Review the migration script first
code ctb/sys/enrichment/ple_constraint_migration.sql

# Execute (using psql or DBeaver)
psql "postgresql://..." -f ctb/sys/enrichment/ple_constraint_migration.sql

# Or in psql:
\i C:/Users/CUSTOM PC/Desktop/Cursor Builds/barton-outreach-core/ctb/sys/enrichment/ple_constraint_migration.sql
```

**IMPORTANT:** The migration script defaults to ROLLBACK. Change to COMMIT after verifying.

### Step 6: Final Verification

```bash
# Re-run audit one more time
node ctb/sys/enrichment/ple_constraint_audit.js

# Should show 100% compliance:
# - NOT NULL: 11/11 (100%)
# - CHECK: 4/4 (100%)
# - UNIQUE: 3/3 (100%)
# - Violations: 0
```

---

## Constraint Details

### NOT NULL Constraints (2 needed)

| Table | Column | Action |
|-------|--------|--------|
| company_master | created_at | `ALTER TABLE marketing.company_master ALTER COLUMN created_at SET NOT NULL;` |
| people_master | created_at | `ALTER TABLE marketing.people_master ALTER COLUMN created_at SET NOT NULL;` |

### CHECK Constraints (4 needed)

| Name | Table | Purpose | Condition |
|------|-------|---------|-----------|
| chk_employee_range | company_master | PLE targeting range | `employee_count >= 50 AND employee_count <= 2000` |
| chk_state_valid | company_master | Mid-Atlantic region | `address_state IN ('PA','VA','MD','OH','WV','KY',...)` |
| chk_slot_type | company_slot | Valid roles | `LOWER(slot_type) IN ('ceo','cfo','hr')` |
| chk_contact_required | people_master | Outreach requirement | `linkedin_url IS NOT NULL OR email IS NOT NULL` |

### UNIQUE Constraints (3 exist - all compliant)

| Name | Table | Columns | Status |
|------|-------|---------|--------|
| company_master_pkey | company_master | company_unique_id | ✅ Active |
| unique_company_slot | company_slot | company_unique_id, slot_type | ✅ Active |
| people_master_pkey | people_master | unique_id | ✅ Active |

---

## Current Violations (16 Total)

1. **Employee Count Range** - 16 companies with values < 50 or > 2000
   - Action: Set to NULL or correct values
   - Query: See `ple_data_violations_detailed.sql` (Section 1)

2. **NULL created_at (company_master)** - Unknown count
   - Action: Set from `promoted_from_intake_at` or NOW()
   - Query: See `ple_data_violations_detailed.sql` (Section 2)

3. **NULL created_at (people_master)** - Unknown count
   - Action: Set from `promoted_from_intake_at` or NOW()
   - Query: See `ple_data_violations_detailed.sql` (Section 3)

---

## Constraint Conflict Warning

### Duplicate slot_type CHECK Constraint

**Issue:** Two constraints named `company_slot_slot_type_check` exist with different rules:
1. Constraint 1: CEO/CFO/HR only (3 values)
2. Constraint 2: CEO/CFO/HR/CTO/CMO/COO/VP_SALES/VP_MARKETING/DIRECTOR/MANAGER (10 values)

**Resolution:**

```sql
-- Drop existing duplicate constraints
ALTER TABLE marketing.company_slot
DROP CONSTRAINT IF EXISTS company_slot_slot_type_check;

-- Add the PLE-specific constraint
ALTER TABLE marketing.company_slot
ADD CONSTRAINT chk_slot_type
CHECK (LOWER(slot_type) IN ('ceo','cfo','hr'));
```

**Decision Required:** Should PLE support 3 roles or 10 roles? Current spec says 3.

---

## Useful Commands

### Re-run Full Audit

```bash
cd "C:/Users/CUSTOM PC/Desktop/Cursor Builds/barton-outreach-core"
node ctb/sys/enrichment/ple_constraint_audit.js
```

### Check Constraint Status

```sql
-- List all CHECK constraints
SELECT tc.table_name, tc.constraint_name, cc.check_clause
FROM information_schema.table_constraints tc
JOIN information_schema.check_constraints cc ON tc.constraint_name = cc.constraint_name
WHERE tc.table_schema = 'marketing'
AND tc.table_name IN ('company_master','company_slot','people_master')
ORDER BY tc.table_name, tc.constraint_name;
```

### Check NOT NULL Status

```sql
-- List all NOT NULL columns
SELECT table_name, column_name, is_nullable, data_type
FROM information_schema.columns
WHERE table_schema = 'marketing'
AND table_name IN ('company_master','company_slot','people_master')
AND is_nullable = 'NO'
ORDER BY table_name, column_name;
```

### Check UNIQUE Constraints

```sql
-- List all UNIQUE/PK constraints
SELECT tc.table_name, tc.constraint_name, tc.constraint_type,
       string_agg(kcu.column_name, ', ' ORDER BY kcu.ordinal_position) as columns
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
WHERE tc.table_schema = 'marketing'
AND tc.constraint_type IN ('UNIQUE', 'PRIMARY KEY')
GROUP BY tc.table_name, tc.constraint_name, tc.constraint_type
ORDER BY tc.table_name, tc.constraint_type;
```

---

## Troubleshooting

### Constraint Addition Fails

**Error:** `violates check constraint`

**Solution:**
1. Re-run the violation detection query
2. Identify records that violate the constraint
3. Fix or delete violating records
4. Try adding constraint again

### Transaction Rollback Issues

**Error:** `current transaction is aborted`

**Solution:**
```sql
ROLLBACK;  -- Reset transaction state
-- Start fresh
BEGIN;
-- Your queries here
COMMIT;
```

### Permission Denied

**Error:** `must be owner of table`

**Solution:** Ensure you're connected as `Marketing DB_owner`:
```bash
psql "postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@..."
```

---

## Integration with PLE Pipeline

### Pre-insertion Validation (Recommended)

Add validation in PLE ingestion pipeline BEFORE inserting to database:

```javascript
// Example validation (Node.js)
function validateCompany(company) {
  const errors = [];

  // Validate employee_count
  if (company.employee_count !== null) {
    if (company.employee_count < 50 || company.employee_count > 2000) {
      errors.push('employee_count must be between 50 and 2000');
    }
  }

  // Validate state
  const validStates = ['PA','VA','MD','OH','WV','KY','Pennsylvania','Virginia','Maryland','Ohio','West Virginia','Kentucky'];
  if (company.address_state && !validStates.includes(company.address_state)) {
    errors.push('address_state must be valid mid-Atlantic state');
  }

  // Ensure created_at is set
  if (!company.created_at) {
    company.created_at = new Date(); // Auto-set
  }

  return errors;
}
```

### Post-insertion Monitoring

Monitor constraint violations in error logs:

```sql
-- Check for constraint violation errors
SELECT *
FROM public.shq_error_log
WHERE error_message LIKE '%constraint%'
OR error_message LIKE '%violates%'
ORDER BY created_at DESC
LIMIT 20;
```

---

## Maintenance

### Schedule Regular Audits

Add to cron or scheduled tasks:

```bash
# Daily constraint audit (add to crontab)
0 2 * * * cd "/path/to/barton-outreach-core" && node ctb/sys/enrichment/ple_constraint_audit.js >> logs/constraint_audit.log 2>&1
```

### Monitor Constraint Violations

Create Grafana dashboard panel:

```sql
-- Panel: Constraint Violations Last 24h
SELECT COUNT(*) as violation_count
FROM public.shq_error_log
WHERE error_message LIKE '%constraint%'
AND created_at >= NOW() - INTERVAL '24 hours';
```

---

## Support

**Generated By:** PLE Constraint Audit Script (Barton ID: 04.04.02.04.50000.001)

**Documentation:**
- Full Report: `PLE_CONSTRAINT_AUDIT_REPORT.md`
- Executive Summary: `PLE_CONSTRAINT_AUDIT_SUMMARY.md`
- This Guide: `ctb/sys/enrichment/README_CONSTRAINT_AUDIT.md`

**Database:** Neon PostgreSQL (Marketing DB)
**Schema:** marketing
**Tables:** company_master, company_slot, people_master

**Last Audit:** 2025-11-26 7:44 AM

---

**Quick Action Summary:**

1. ✅ Review reports (5 min)
2. ⚠️ Run violation query (1 min)
3. ⚠️ Clean up data (10-30 min)
4. ⚠️ Re-run audit to verify 0 violations (1 min)
5. ⚠️ Add constraints (2 min)
6. ✅ Final verification (1 min)

**Total Time:** ~20-45 minutes
