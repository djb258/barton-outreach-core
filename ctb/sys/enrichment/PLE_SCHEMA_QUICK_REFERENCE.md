# PLE Schema Quick Reference

## Current Status: 3/6 Tables Exist ✅⚠❌

### ✅ Existing Tables (with column name differences)
1. `marketing.company_master` → PLE: `companies`
2. `marketing.company_slot` → PLE: `company_slots`
3. `marketing.people_master` → PLE: `people`

### ❌ Missing Tables
4. `person_movement_history` - Career movements & job changes
5. `person_scores` - BIT scores & confidence
6. `company_events` - Funding, expansions, layoffs, etc.

---

## Column Name Mapping (Use This for Queries)

### Companies
```python
# PLE name → Current name (marketing.company_master)
id              → company_unique_id
company_uid     → company_unique_id
name            → company_name
linkedin_url    → linkedin_url        # ✓ Same
employee_count  → employee_count      # ✓ Same
state           → address_state (or state_abbrev)
city            → address_city
industry        → industry            # ✓ Same
source          → source_system
created_at      → created_at          # ✓ Same
updated_at      → updated_at          # ✓ Same
```

### Company Slots
```python
# PLE name → Current name (marketing.company_slot)
id          → company_slot_unique_id
slot_uid    → company_slot_unique_id
company_id  → company_unique_id
slot_type   → slot_type               # ✓ Same
person_id   → person_unique_id
assigned_at → filled_at
vacated_at  → ❌ MISSING (add this!)
```

### People
```python
# PLE name → Current name (marketing.people_master)
id                      → unique_id
person_uid              → unique_id
company_id              → company_unique_id
linkedin_url            → linkedin_url            # ✓ Same
email                   → email                   # ✓ Same
first_name              → first_name              # ✓ Same
last_name               → last_name               # ✓ Same
title                   → title                   # ✓ Same
validation_status       → ❌ MISSING (add this!)
last_verified_at        → ❌ MISSING (add this!)
last_enrichment_attempt → ❌ MISSING (add this!)
created_at              → created_at              # ✓ Same
updated_at              → updated_at              # ✓ Same
```

---

## Migration Script Usage

### Step 1: Add Missing Columns
```bash
psql $DATABASE_URL -f ctb/sys/enrichment/ple_schema_migration.sql
# Or run Phase 1 only:
psql $DATABASE_URL <<SQL
-- Phase 1: Add columns
ALTER TABLE marketing.people_master
ADD COLUMN IF NOT EXISTS validation_status TEXT DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS last_verified_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS last_enrichment_attempt TIMESTAMPTZ;

ALTER TABLE marketing.company_slot
ADD COLUMN IF NOT EXISTS vacated_at TIMESTAMPTZ;
SQL
```

### Step 2: Create PLE Views (Recommended!)
```sql
-- After Phase 2, you can use PLE names:
SELECT * FROM ple.companies WHERE industry = 'Technology';
SELECT * FROM ple.company_slots WHERE slot_type = 'CEO';
SELECT * FROM ple.people WHERE validation_status = 'pending';
```

### Step 3: Create Sidecar Tables
```bash
# Run Phase 3 from migration script
# Creates: person_movement_history, person_scores, company_events
```

---

## Quick Queries (After Migration)

### Find Pending Validations
```sql
SELECT * FROM ple.people
WHERE validation_status = 'pending'
ORDER BY created_at DESC
LIMIT 10;
```

### Find Empty Slots
```sql
SELECT * FROM ple.company_slots
WHERE person_id IS NULL
ORDER BY created_at DESC;
```

### Find Companies Needing Enrichment
```sql
SELECT c.name, c.industry, c.employee_count
FROM ple.companies c
LEFT JOIN ple.company_slots s ON c.id = s.company_id
WHERE s.person_id IS NULL;
```

### Track Career Movements (After Phase 3)
```sql
SELECT
    p.first_name,
    p.last_name,
    h.movement_type,
    h.title_from,
    h.title_to,
    h.detected_at
FROM ple.person_movement_history h
JOIN ple.people p ON h.person_id = p.id
ORDER BY h.detected_at DESC
LIMIT 10;
```

### Find High-Intent Contacts (After Phase 3)
```sql
SELECT
    p.first_name,
    p.last_name,
    p.email,
    s.bit_score,
    s.confidence_score
FROM ple.person_scores s
JOIN ple.people p ON s.person_id = p.id
WHERE s.bit_score > 70
  AND s.confidence_score > 80
ORDER BY s.bit_score DESC;
```

---

## Files Generated

1. **PLE_SCHEMA_VERIFICATION_REPORT.md** - Full detailed report (10+ pages)
2. **ple_schema_migration.sql** - All SQL migration scripts (4 phases)
3. **PLE_SCHEMA_QUICK_REFERENCE.md** - This file (1 page)

---

## Next Steps

1. ✅ Review verification report
2. 🔧 Run Phase 1 (add columns)
3. 👁 Run Phase 2 (create views)
4. 🏗 Run Phase 3 (create sidecar tables)
5. ⚡ Run Phase 4 (add indexes)
6. 🧪 Test queries with new PLE views
7. 📊 Backfill validation_status for existing records

---

**Last Updated**: 2025-11-26
**Database**: Neon PostgreSQL - Marketing DB
**Full Report**: `PLE_SCHEMA_VERIFICATION_REPORT.md`
**Migration Script**: `ple_schema_migration.sql`
