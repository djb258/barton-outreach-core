-- ============================================================================
-- Migration: Rename unique_id to people_unique_id in marketing.people_master
-- Date: 2025-10-23
-- Issue: Column named unique_id breaks naming consistency with company_unique_id
-- Fix: Rename to people_unique_id for Barton Doctrine compliance
-- Doctrine Segment: 04.04.02
-- ============================================================================

/**
 * NAMING CONSISTENCY FIX
 *
 * Problem:
 *   marketing.people_master uses column name "unique_id"
 *   marketing.company_master uses column name "company_unique_id"
 *   marketing.company_intelligence uses "intel_unique_id"
 *   marketing.people_intelligence uses "intel_unique_id"
 *
 * Expected Pattern: {table}_unique_id
 *
 * Impact: This is a BREAKING CHANGE
 *   - All FKs referencing unique_id must be updated
 *   - All application code referencing unique_id must be updated
 *   - Views and functions referencing unique_id must be updated
 *
 * Doctrine Decision: Apply fix for v1.1 to achieve schema consistency
 */

-- ==============================================================================
-- STEP 1: Drop dependent foreign keys
-- ==============================================================================

-- Drop FK from people_intelligence
ALTER TABLE marketing.people_intelligence
    DROP CONSTRAINT IF EXISTS people_intelligence_person_unique_id_fkey;

-- Drop FK from scoring tables if exists
ALTER TABLE marketing.contact_scoring
    DROP CONSTRAINT IF EXISTS fk_contact_scoring_people;

ALTER TABLE marketing.outreach_scoring
    DROP CONSTRAINT IF EXISTS fk_outreach_scoring_people;

-- ==============================================================================
-- STEP 2: Rename the column
-- ==============================================================================

ALTER TABLE marketing.people_master
    RENAME COLUMN unique_id TO people_unique_id;

-- ==============================================================================
-- STEP 3: Recreate foreign keys with correct column reference
-- ==============================================================================

-- Recreate FK from people_intelligence
ALTER TABLE marketing.people_intelligence
    ADD CONSTRAINT people_intelligence_person_unique_id_fkey
    FOREIGN KEY (person_unique_id)
    REFERENCES marketing.people_master(people_unique_id)
    ON DELETE CASCADE;

-- Recreate FK from scoring tables if they exist
DO $$
BEGIN
    -- contact_scoring FK
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_schema = 'marketing'
               AND table_name = 'contact_scoring') THEN
        ALTER TABLE marketing.contact_scoring
            ADD CONSTRAINT fk_contact_scoring_people
            FOREIGN KEY (people_barton_id)
            REFERENCES marketing.people_master(people_unique_id)
            ON DELETE SET NULL;
    END IF;

    -- outreach_scoring FK
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_schema = 'marketing'
               AND table_name = 'outreach_scoring') THEN
        ALTER TABLE marketing.outreach_scoring
            ADD CONSTRAINT fk_outreach_scoring_people
            FOREIGN KEY (people_barton_id)
            REFERENCES marketing.people_master(people_unique_id)
            ON DELETE SET NULL;
    END IF;
END $$;

-- ==============================================================================
-- STEP 4: Update CHECK constraints if any reference the column name
-- ==============================================================================

/**
 * NOTE: CHECK constraints with regex don't reference column names directly,
 * they reference the column value. No action needed for CHECK constraints.
 *
 * Example: CHECK (people_unique_id ~ '^04\.04\.02\.[0-9]{2}...')
 * The constraint name may contain "unique_id" but the logic is unaffected.
 */

-- ==============================================================================
-- STEP 5: Update views that reference the column
-- ==============================================================================

-- Recreate outreach_history view if it exists and references people_master.unique_id
CREATE OR REPLACE VIEW marketing.outreach_history AS
SELECT
  c.campaign_id,
  c.campaign_type,
  c.trigger_event,
  c.company_unique_id,
  c.status AS campaign_status,
  c.created_at AS campaign_created_at,
  c.launched_at AS campaign_launched_at,
  ce.execution_step,
  ce.step_type,
  ce.scheduled_at,
  ce.executed_at,
  ce.status AS execution_status,
  ce.target_person_id,
  ce.target_email AS execution_target_email,
  ce.target_linkedin,
  ce.response AS execution_response,
  ce.error_message AS execution_error,
  ml.message_log_id,
  ml.contact_id AS message_contact_id,
  ml.direction AS message_direction,
  ml.channel AS message_channel,
  ml.subject AS message_subject,
  ml.body AS message_body,
  ml.sent_at AS message_sent_at
FROM marketing.campaigns c
LEFT JOIN marketing.campaign_executions ce ON c.campaign_id = ce.campaign_id
LEFT JOIN marketing.message_log ml ON c.campaign_id::text = ml.campaign_id::text;

-- ==============================================================================
-- VERIFICATION QUERIES
-- ==============================================================================

/**
 * Verify column rename:
 *
 * SELECT column_name, data_type, is_nullable
 * FROM information_schema.columns
 * WHERE table_schema = 'marketing'
 *     AND table_name = 'people_master'
 *     AND column_name = 'people_unique_id';
 *
 * Expected: 1 row returned with column_name = 'people_unique_id'
 *
 * Verify no old column exists:
 *
 * SELECT column_name
 * FROM information_schema.columns
 * WHERE table_schema = 'marketing'
 *     AND table_name = 'people_master'
 *     AND column_name = 'unique_id';
 *
 * Expected: 0 rows (column no longer exists)
 *
 * Verify FK integrity:
 *
 * SELECT tc.constraint_name, tc.table_name, kcu.column_name,
 *        ccu.table_name AS foreign_table_name,
 *        ccu.column_name AS foreign_column_name
 * FROM information_schema.table_constraints tc
 * JOIN information_schema.key_column_usage kcu
 *     ON tc.constraint_name = kcu.constraint_name
 * JOIN information_schema.constraint_column_usage ccu
 *     ON tc.constraint_name = ccu.constraint_name
 * WHERE tc.constraint_type = 'FOREIGN KEY'
 *     AND (tc.table_name = 'people_intelligence'
 *          OR ccu.table_name = 'people_master');
 *
 * Expected: All FKs show foreign_column_name = 'people_unique_id'
 */

-- ==============================================================================
-- COMMENTS
-- ==============================================================================

COMMENT ON COLUMN marketing.people_master.people_unique_id IS
    'Barton ID format: 04.04.02.XX.XXXXX.XXX (renamed from unique_id 2025-10-23 for naming consistency).
    Primary key for people_master table.';

-- ==============================================================================
-- MIGRATION COMPLETE
-- ==============================================================================
-- Table: marketing.people_master
-- Issue: Column named unique_id (inconsistent with company_unique_id pattern)
-- Resolution: Renamed to people_unique_id, updated all FKs
-- Status: ✅ Schema consistency achieved per Doctrine 04.04.02
-- Breaking Change: YES - Application code must update references
-- ============================================================================
