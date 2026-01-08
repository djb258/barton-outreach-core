# People Slot Structure — Validation Checklist

**Migration:** `2026-01-08-people-slot-structure.sql`  
**Hub:** people-intelligence  
**Status:** STRUCTURE ONLY (No Data Population)

---

## Pre-Flight Checks

- [ ] Connected to correct Neon database
- [ ] Running on `cc-purification/v1.1.0` branch
- [ ] Backup taken (if production)

---

## Post-Migration Validation

### 1. UNIQUE Constraint

```sql
-- Verify constraint exists
SELECT conname, contype 
FROM pg_constraint 
WHERE conname = 'uq_company_slot_outreach_slot_type';

-- Expected: 1 row with contype = 'u'
```

- [ ] Constraint `uq_company_slot_outreach_slot_type` exists
- [ ] Constraint type is 'u' (unique)

### 2. people.people_candidate Table

```sql
-- Verify table exists with correct columns
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'people' AND table_name = 'people_candidate'
ORDER BY ordinal_position;

-- Expected columns:
-- candidate_id, outreach_id, slot_type, person_name, person_title, 
-- person_email, linkedin_url, confidence_score, source, status,
-- rejection_reason, created_at, processed_at, expires_at
```

- [ ] Table `people.people_candidate` exists
- [ ] All 14 columns present
- [ ] `status` defaults to 'pending'
- [ ] `expires_at` defaults to NOW() + 7 days

### 3. Views

```sql
-- Verify v_open_slots
SELECT * FROM people.v_open_slots LIMIT 5;

-- Verify v_slot_fill_rate
SELECT * FROM people.v_slot_fill_rate;
```

- [ ] `people.v_open_slots` returns data (or empty if no open slots)
- [ ] `people.v_slot_fill_rate` shows aggregated metrics

### 4. Guard Function

```sql
-- Test guard function (should return FALSE with reason)
SELECT * FROM people.slot_can_accept_candidate(
    '00000000-0000-0000-0000-000000000000'::UUID, 
    'CEO'
);

-- Expected: can_accept = FALSE, reason contains 'KILL_SWITCH_OFF'
```

- [ ] Function `people.slot_can_accept_candidate()` exists
- [ ] Returns FALSE when kill switch is OFF
- [ ] Returns proper reason codes

### 5. Kill Switch

```sql
-- Verify kill switch table and default state
SELECT switch_name, is_enabled, description
FROM people.slot_ingress_control;

-- Expected: is_enabled = FALSE
```

- [ ] Table `people.slot_ingress_control` exists
- [ ] `slot_ingress` switch exists
- [ ] `is_enabled = FALSE` (OFF by default)

### 6. slot_status Constraint

```sql
-- Verify slot_status allows 'quarantined'
SELECT conname 
FROM pg_constraint 
WHERE conrelid = 'people.company_slot'::regclass 
AND conname LIKE '%slot_status%';
```

- [ ] `slot_status` constraint includes 'quarantined'

---

## Verification Queries

### Full Health Check

```sql
-- Run all checks in one query
SELECT 
    'constraint' AS check_type,
    EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_company_slot_outreach_slot_type') AS passed
UNION ALL
SELECT 
    'people_candidate',
    EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'people' AND table_name = 'people_candidate')
UNION ALL
SELECT 
    'v_open_slots',
    EXISTS (SELECT 1 FROM information_schema.views WHERE table_schema = 'people' AND table_name = 'v_open_slots')
UNION ALL
SELECT 
    'v_slot_fill_rate',
    EXISTS (SELECT 1 FROM information_schema.views WHERE table_schema = 'people' AND table_name = 'v_slot_fill_rate')
UNION ALL
SELECT 
    'guard_function',
    EXISTS (SELECT 1 FROM pg_proc p JOIN pg_namespace n ON p.pronamespace = n.oid WHERE n.nspname = 'people' AND p.proname = 'slot_can_accept_candidate')
UNION ALL
SELECT 
    'kill_switch_table',
    EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'people' AND table_name = 'slot_ingress_control')
UNION ALL
SELECT 
    'kill_switch_off',
    NOT COALESCE((SELECT is_enabled FROM people.slot_ingress_control WHERE switch_name = 'slot_ingress'), TRUE);

-- Expected: All rows show passed = TRUE
```

---

## HARD STOP Verification

Confirm NO data was populated:

```sql
-- Verify candidate table is empty
SELECT COUNT(*) FROM people.people_candidate;
-- Expected: 0

-- Verify people_master was not touched
-- (Compare row count with pre-migration, should be same: 170)
SELECT COUNT(*) FROM people.people_master;
-- Expected: Same as before migration
```

- [ ] `people.people_candidate` has 0 rows
- [ ] `people.people_master` row count unchanged

---

## Sign-Off

| Validator | Date | Status |
|-----------|------|--------|
| _________ | _____ | ☐ PASS / ☐ FAIL |

---

**Migration Hash:** (generate after commit)  
**Rollback Available:** `2026-01-08-people-slot-structure_ROLLBACK.sql`
