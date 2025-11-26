-- ============================================================================
-- PLE CONSTRAINT MIGRATION SCRIPT
-- ============================================================================
-- Barton ID: 04.04.02.04.50000.002
-- Purpose: Add missing NOT NULL, CHECK, and UNIQUE constraints
--
-- Generated: 2025-11-26T12:44:31.211Z
--
-- IMPORTANT: Review audit report before executing!
-- This script will FAIL if data violations exist.
-- ============================================================================

BEGIN;

-- ============================================================================
-- PHASE 1: DATA CLEANUP (Run if violations detected)
-- ============================================================================

-- 1. Set default values for NULL required fields (REVIEW CAREFULLY!)
-- UPDATE marketing.company_master SET source_system = 'unknown' WHERE source_system IS NULL;
-- UPDATE marketing.people_master SET first_name = 'Unknown' WHERE first_name IS NULL;
-- UPDATE marketing.people_master SET last_name = 'Unknown' WHERE last_name IS NULL;

-- 2. Fix employee_count range violations
-- UPDATE marketing.company_master SET employee_count = NULL WHERE employee_count < 50 OR employee_count > 2000;

-- 3. Fix state violations (set to NULL or correct value)
-- UPDATE marketing.company_master SET address_state = NULL
-- WHERE address_state IS NOT NULL
-- AND address_state NOT IN ('PA','VA','MD','OH','WV','KY','Pennsylvania','Virginia','Maryland','Ohio','West Virginia','Kentucky');

-- 4. Fix slot_type violations (set to NULL or correct value)
-- UPDATE marketing.company_slot SET slot_type = UPPER(slot_type)
-- WHERE LOWER(slot_type) IN ('ceo','cfo','hr') AND slot_type != UPPER(slot_type);

-- 5. Delete people_master records with no contact info (or add dummy email)
-- DELETE FROM marketing.people_master WHERE linkedin_url IS NULL AND email IS NULL;
-- OR
-- UPDATE marketing.people_master SET email = 'noemail@example.com' WHERE linkedin_url IS NULL AND email IS NULL;

-- 6. Resolve duplicate company_slot records (keep most recent)
-- DELETE FROM marketing.company_slot
-- WHERE company_slot_unique_id IN (
--   SELECT company_slot_unique_id FROM (
--     SELECT company_slot_unique_id,
--            ROW_NUMBER() OVER (PARTITION BY company_unique_id, slot_type ORDER BY created_at DESC NULLS LAST) as rn
--     FROM marketing.company_slot
--   ) sub WHERE rn > 1
-- );

-- ============================================================================
-- PHASE 2: ADD NOT NULL CONSTRAINTS
-- ============================================================================

-- Table: company_master
ALTER TABLE marketing.company_master
  ALTER COLUMN created_at SET NOT NULL;

-- Table: company_slot
-- Table: people_master
ALTER TABLE marketing.people_master
  ALTER COLUMN created_at SET NOT NULL;

-- ============================================================================
-- PHASE 3: ADD CHECK CONSTRAINTS
-- ============================================================================

-- Employee count must be between 50 and 2000
ALTER TABLE marketing.company_master
  ADD CONSTRAINT chk_employee_range
  CHECK (employee_count >= 50 AND employee_count <= 2000);

-- State must be valid mid-Atlantic abbreviation or full name
ALTER TABLE marketing.company_master
  ADD CONSTRAINT chk_state_valid
  CHECK (address_state IN ('PA','VA','MD','OH','WV','KY','Pennsylvania','Virginia','Maryland','Ohio','West Virginia','Kentucky'));

-- Slot type must be CEO, CFO, or HR (case-insensitive)
ALTER TABLE marketing.company_slot
  ADD CONSTRAINT chk_slot_type
  CHECK (LOWER(slot_type) IN ('ceo','cfo','hr'));

-- At least one of LinkedIn URL or email must be provided
ALTER TABLE marketing.people_master
  ADD CONSTRAINT chk_contact_required
  CHECK (linkedin_url IS NOT NULL OR email IS NOT NULL);

-- ============================================================================
-- PHASE 4: ADD UNIQUE CONSTRAINTS
-- ============================================================================

-- ============================================================================
-- PHASE 5: VERIFICATION
-- ============================================================================

-- Verify NOT NULL constraints
SELECT table_name, column_name, is_nullable
FROM information_schema.columns
WHERE table_schema = 'marketing'
AND table_name IN ('company_master', 'company_slot', 'people_master')
AND is_nullable = 'NO'
ORDER BY table_name, column_name;

-- Verify CHECK constraints
SELECT tc.table_name, tc.constraint_name, cc.check_clause
FROM information_schema.table_constraints tc
JOIN information_schema.check_constraints cc ON tc.constraint_name = cc.constraint_name
WHERE tc.table_schema = 'marketing'
AND tc.constraint_type = 'CHECK'
ORDER BY tc.table_name, tc.constraint_name;

-- Verify UNIQUE constraints
SELECT tc.table_name, tc.constraint_name, tc.constraint_type,
       string_agg(kcu.column_name, ', ' ORDER BY kcu.ordinal_position) as columns
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
WHERE tc.table_schema = 'marketing'
AND tc.constraint_type IN ('UNIQUE', 'PRIMARY KEY')
GROUP BY tc.table_name, tc.constraint_name, tc.constraint_type
ORDER BY tc.table_name, tc.constraint_type;

-- If all looks good, commit. Otherwise, rollback.
-- COMMIT;
ROLLBACK; -- Change to COMMIT after review

-- ============================================================================
-- END OF MIGRATION SCRIPT
-- ============================================================================