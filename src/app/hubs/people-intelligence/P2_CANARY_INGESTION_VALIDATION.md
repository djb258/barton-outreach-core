# P2 Canary Ingestion — Validation Checklist

**Migration:** `2026-01-08-people-slot-canary-ingestion.sql`  
**Hub:** people-intelligence  
**Status:** CANARY MODE (Scoped Ingestion)

---

## Pre-Flight Checks

- [ ] P1 Slot Structure migration applied and validated
- [ ] Connected to correct Neon database
- [ ] Running on `cc-purification/v1.1.0` branch
- [ ] Backup taken (if production)

---

## Post-Migration Validation

### 1. Canary Allowlist Table

```sql
-- Verify table exists
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'people' AND table_name = 'slot_ingress_canary'
ORDER BY ordinal_position;

-- Expected columns: outreach_id, added_by, added_at, notes
```

- [ ] Table `people.slot_ingress_canary` exists
- [ ] Table is EMPTY (no auto-population)

### 2. Guard Function (Canary-Aware)

```sql
-- Test 1: Kill switch OFF → should fail
SELECT * FROM people.slot_can_accept_candidate(
    '00000000-0000-0000-0000-000000000000'::UUID, 
    'CEO'
);
-- Expected: can_accept = FALSE, reason = 'KILL_SWITCH_OFF'
```

- [ ] Guard function returns FALSE when kill switch OFF

### 3. Canary Mode Column

```sql
-- Verify canary_mode column added
SELECT switch_name, is_enabled, canary_mode
FROM people.slot_ingress_control;

-- Expected: is_enabled = FALSE, canary_mode = TRUE
```

- [ ] `canary_mode` column exists
- [ ] `canary_mode = TRUE`
- [ ] `is_enabled = FALSE` (still off)

### 4. Observability Views

```sql
-- Verify views exist
SELECT table_name 
FROM information_schema.views 
WHERE table_schema = 'people' 
AND table_name IN ('v_candidate_canary_activity', 'v_canary_queue_depth');

-- Expected: 2 rows
```

- [ ] `people.v_candidate_canary_activity` exists
- [ ] `people.v_canary_queue_depth` exists

---

## Human Actions Required

### Step 1: Populate Canary (10-25 outreach_ids)

```sql
-- Find valid outreach_ids with open slots
SELECT DISTINCT cs.outreach_id, cs.company_unique_id, cs.slot_type
FROM people.company_slot cs
WHERE cs.outreach_id IS NOT NULL
  AND cs.slot_status = 'open'
LIMIT 25;

-- Insert into canary allowlist
INSERT INTO people.slot_ingress_canary (outreach_id, added_by, notes)
VALUES 
    ('xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', 'your_name', 'Canary test #1'),
    ('yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy', 'your_name', 'Canary test #2');
-- ... add 10-25 total
```

- [ ] Canary populated with 10-25 outreach_ids
- [ ] All outreach_ids have corresponding open slots

### Step 2: Enable Kill Switch

```sql
-- HUMAN-ONLY: Enable kill switch
UPDATE people.slot_ingress_control
SET is_enabled = TRUE,
    enabled_by = 'your_name',
    enabled_at = NOW()
WHERE switch_name = 'slot_ingress';

-- Verify
SELECT switch_name, is_enabled, canary_mode, enabled_by, enabled_at
FROM people.slot_ingress_control;
```

- [ ] Kill switch enabled (`is_enabled = TRUE`)
- [ ] Enabled by human operator (name recorded)

### Step 3: Verify Guard Function

```sql
-- Test with canary outreach_id (should pass if slot is open)
SELECT * FROM people.slot_can_accept_candidate(
    '<canary_outreach_id>'::UUID, 
    'CEO'
);
-- Expected: can_accept = TRUE (or FALSE with valid reason)

-- Test with NON-canary outreach_id (should fail)
SELECT * FROM people.slot_can_accept_candidate(
    '<non_canary_outreach_id>'::UUID, 
    'CEO'
);
-- Expected: can_accept = FALSE, reason = 'NOT_IN_CANARY'
```

- [ ] Canary outreach_id passes guard (or fails with valid slot reason)
- [ ] Non-canary outreach_id fails with `NOT_IN_CANARY`

---

## Full Health Check Query

```sql
-- Single query to verify all P2 components
SELECT 
    'canary_table' AS check_type,
    EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'people' AND table_name = 'slot_ingress_canary') AS passed
UNION ALL
SELECT 
    'canary_mode_column',
    EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'people' AND table_name = 'slot_ingress_control' AND column_name = 'canary_mode')
UNION ALL
SELECT 
    'v_candidate_canary_activity',
    EXISTS (SELECT 1 FROM information_schema.views WHERE table_schema = 'people' AND table_name = 'v_candidate_canary_activity')
UNION ALL
SELECT 
    'v_canary_queue_depth',
    EXISTS (SELECT 1 FROM information_schema.views WHERE table_schema = 'people' AND table_name = 'v_canary_queue_depth')
UNION ALL
SELECT 
    'guard_function_exists',
    EXISTS (SELECT 1 FROM pg_proc p JOIN pg_namespace n ON p.pronamespace = n.oid WHERE n.nspname = 'people' AND p.proname = 'slot_can_accept_candidate');

-- Expected: All rows show passed = TRUE
```

---

## HARD STOP Verification

Confirm constraints are enforced:

```sql
-- Verify no candidates accepted outside canary
SELECT pc.* 
FROM people.people_candidate pc
LEFT JOIN people.slot_ingress_canary c ON pc.outreach_id = c.outreach_id
WHERE c.outreach_id IS NULL
  AND pc.status = 'accepted';
-- Expected: 0 rows (no candidates outside canary)

-- Verify no writes to people_master (row count unchanged)
SELECT COUNT(*) FROM people.people_master;
-- Expected: Same as before migration (170)

-- Verify candidate table is empty (no auto-population)
SELECT COUNT(*) FROM people.people_candidate;
-- Expected: 0 (no candidates ingested yet)
```

- [ ] No candidates accepted outside canary
- [ ] `people.people_master` unchanged
- [ ] `people.people_candidate` empty (structure only)

---

## Sign-Off

| Validator | Date | Status |
|-----------|------|--------|
| _________ | _____ | ☐ PASS / ☐ FAIL |

---

## End State Verification

| Capability | Status |
|------------|--------|
| Slot structure | ✅ |
| Candidate ingestion | ✅ (Canary only) |
| Slot resolution | ❌ |
| Movement detection | ❌ |
| Enrichment | ❌ |

---

**Rollback Available:** `2026-01-08-people-slot-canary-ingestion_ROLLBACK.sql`  
**Next Phase:** P3 Slot Resolution (DISABLED)
