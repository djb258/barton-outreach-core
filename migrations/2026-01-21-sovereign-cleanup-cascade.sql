-- ============================================================================
-- SOVEREIGN CLEANUP CASCADE - COMPREHENSIVE
-- ============================================================================
-- Date: 2026-01-21
-- Purpose: Archive orphaned records after CL sovereign cleanup
-- Handles ALL FK dependencies in proper order
-- ============================================================================
-- Authority: claude-opus-4-5-20251101
-- Doctrine: CL Parent-Child v1.1
-- ============================================================================

BEGIN;

-- ============================================================================
-- PHASE 1: IDENTIFY ORPHANED OUTREACH_IDS
-- ============================================================================

CREATE TEMP TABLE orphaned_outreach_ids AS
SELECT o.outreach_id, o.sovereign_id
FROM outreach.outreach o
WHERE NOT EXISTS (
    SELECT 1 FROM cl.company_identity ci
    WHERE ci.company_unique_id = o.sovereign_id
    AND ci.identity_status = 'PASS'
);

CREATE INDEX idx_orphaned_outreach_ids ON orphaned_outreach_ids(outreach_id);

-- Report count
DO $$
DECLARE
    orphan_count INT;
BEGIN
    SELECT COUNT(*) INTO orphan_count FROM orphaned_outreach_ids;
    RAISE NOTICE 'Identified % orphaned outreach_ids', orphan_count;
END $$;

-- ============================================================================
-- PHASE 2: DELETE FROM LEAF TABLES (No FK references to them)
-- ============================================================================

-- 2.1 Error tables (no downstream FK)
DELETE FROM outreach.company_target_errors
WHERE outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids);

DELETE FROM outreach.dol_errors
WHERE outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids);

DELETE FROM outreach.people_errors
WHERE outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids);

DELETE FROM outreach.blog_errors
WHERE outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids);

DELETE FROM outreach.bit_errors
WHERE outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids);

-- 2.2 BIT tables
DELETE FROM outreach.bit_signals
WHERE outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids);

DELETE FROM outreach.bit_scores
WHERE outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids);

DELETE FROM outreach.bit_input_history
WHERE outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids);

-- 2.3 Blog tables
DELETE FROM outreach.blog_source_history
WHERE outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids);

DELETE FROM outreach.blog
WHERE outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids);

-- 2.4 DOL table
DELETE FROM outreach.dol
WHERE outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids);

-- 2.5 Engagement events (references target_id, person_id, outreach_id)
DELETE FROM outreach.engagement_events
WHERE outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids);

-- 2.6 Send log (references target_id, person_id, campaign_id, sequence_id)
DELETE FROM outreach.send_log
WHERE target_id IN (
    SELECT target_id FROM outreach.company_target
    WHERE outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids)
);

-- 2.7 Sequences - No outreach_id link, skip
-- 2.8 Campaigns - No outreach_id link, skip

-- 2.9 Company hub status
DELETE FROM outreach.company_hub_status
WHERE company_unique_id IN (
    SELECT sovereign_id::text FROM orphaned_outreach_ids
);

-- 2.10 People resolution history
DELETE FROM people.people_resolution_history
WHERE outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids);

-- 2.11 Talent flow movement history
DELETE FROM talent_flow.movement_history
WHERE to_outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids)
   OR from_outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids);

DO $$ BEGIN RAISE NOTICE 'Completed leaf table cleanup'; END $$;

-- ============================================================================
-- PHASE 3: CREATE ARCHIVE TABLES
-- ============================================================================

-- 3.1 Archive for outreach.outreach
CREATE TABLE IF NOT EXISTS outreach.outreach_archive (
    LIKE outreach.outreach INCLUDING ALL,
    archived_at TIMESTAMPTZ DEFAULT NOW(),
    archive_reason TEXT DEFAULT 'sovereign_cleanup_2026-01-21'
);

-- 3.2 Archive for outreach.company_target
CREATE TABLE IF NOT EXISTS outreach.company_target_archive (
    LIKE outreach.company_target INCLUDING ALL,
    archived_at TIMESTAMPTZ DEFAULT NOW(),
    archive_reason TEXT DEFAULT 'sovereign_cleanup_2026-01-21'
);

-- 3.3 Archive for outreach.people
CREATE TABLE IF NOT EXISTS outreach.people_archive (
    LIKE outreach.people INCLUDING ALL,
    archived_at TIMESTAMPTZ DEFAULT NOW(),
    archive_reason TEXT DEFAULT 'sovereign_cleanup_2026-01-21'
);

-- 3.4 Archive for people.company_slot
CREATE TABLE IF NOT EXISTS people.company_slot_archive (
    LIKE people.company_slot INCLUDING ALL,
    archived_at TIMESTAMPTZ DEFAULT NOW(),
    archive_reason TEXT DEFAULT 'sovereign_cleanup_2026-01-21'
);

-- 3.5 Archive for people.people_master (without generated columns)
CREATE TABLE IF NOT EXISTS people.people_master_archive (
    unique_id TEXT,
    company_unique_id TEXT,
    company_slot_unique_id TEXT,
    first_name TEXT,
    last_name TEXT,
    full_name_stored TEXT,
    title TEXT,
    seniority TEXT,
    department TEXT,
    email TEXT,
    work_phone_e164 TEXT,
    personal_phone_e164 TEXT,
    linkedin_url TEXT,
    twitter_url TEXT,
    facebook_url TEXT,
    bio TEXT,
    skills TEXT,
    education TEXT,
    certifications TEXT,
    source_system TEXT,
    source_record_id TEXT,
    promoted_from_intake_at TIMESTAMPTZ,
    promotion_audit_log_id INTEGER,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    email_verified BOOLEAN,
    message_key_scheduled TEXT,
    email_verification_source TEXT,
    email_verified_at TIMESTAMPTZ,
    validation_status_stored TEXT,
    last_verified_at TIMESTAMPTZ,
    last_enrichment_attempt TIMESTAMPTZ,
    archived_at TIMESTAMPTZ DEFAULT NOW(),
    archive_reason TEXT DEFAULT 'sovereign_cleanup_2026-01-21'
);

DO $$ BEGIN RAISE NOTICE 'Created archive tables'; END $$;

-- ============================================================================
-- PHASE 4: ARCHIVE MAIN TABLES (Bottom-up order)
-- ============================================================================

-- 4.1 Archive outreach.people
INSERT INTO outreach.people_archive
SELECT p.*, NOW(), 'sovereign_cleanup_2026-01-21'
FROM outreach.people p
WHERE p.outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids);

-- 4.2 Archive people.company_slot
INSERT INTO people.company_slot_archive
SELECT cs.*, NOW(), 'sovereign_cleanup_2026-01-21'
FROM people.company_slot cs
WHERE cs.outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids);

-- 4.3 Archive people.people_master (only those exclusively in orphaned slots)
INSERT INTO people.people_master_archive (
    unique_id, company_unique_id, company_slot_unique_id, first_name, last_name,
    full_name_stored, title, seniority, department, email, work_phone_e164,
    personal_phone_e164, linkedin_url, twitter_url, facebook_url, bio, skills,
    education, certifications, source_system, source_record_id, promoted_from_intake_at,
    promotion_audit_log_id, created_at, updated_at, email_verified, message_key_scheduled,
    email_verification_source, email_verified_at, validation_status_stored,
    last_verified_at, last_enrichment_attempt, archived_at, archive_reason
)
SELECT
    pm.unique_id, pm.company_unique_id, pm.company_slot_unique_id, pm.first_name, pm.last_name,
    pm.full_name, pm.title, pm.seniority, pm.department, pm.email, pm.work_phone_e164,
    pm.personal_phone_e164, pm.linkedin_url, pm.twitter_url, pm.facebook_url, pm.bio, pm.skills,
    pm.education, pm.certifications, pm.source_system, pm.source_record_id, pm.promoted_from_intake_at,
    pm.promotion_audit_log_id, pm.created_at, pm.updated_at, pm.email_verified, pm.message_key_scheduled,
    pm.email_verification_source, pm.email_verified_at, pm.validation_status,
    pm.last_verified_at, pm.last_enrichment_attempt, NOW(), 'sovereign_cleanup_2026-01-21'
FROM people.people_master pm
WHERE pm.unique_id IN (
    SELECT DISTINCT cs.person_unique_id
    FROM people.company_slot cs
    WHERE cs.outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids)
)
AND pm.unique_id NOT IN (
    SELECT DISTINCT cs2.person_unique_id
    FROM people.company_slot cs2
    WHERE cs2.outreach_id NOT IN (SELECT outreach_id FROM orphaned_outreach_ids)
);

-- 4.4 Archive outreach.company_target
INSERT INTO outreach.company_target_archive
SELECT ct.*, NOW(), 'sovereign_cleanup_2026-01-21'
FROM outreach.company_target ct
WHERE ct.outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids);

-- 4.5 Archive outreach.outreach
INSERT INTO outreach.outreach_archive
SELECT o.*, NOW(), 'sovereign_cleanup_2026-01-21'
FROM outreach.outreach o
WHERE o.outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids);

DO $$ BEGIN RAISE NOTICE 'Completed archiving main tables'; END $$;

-- ============================================================================
-- PHASE 5: DELETE ARCHIVED RECORDS (Bottom-up)
-- ============================================================================

-- 5.1 Delete outreach.people
DELETE FROM outreach.people
WHERE outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids);

-- 5.2 Delete people.company_slot
DELETE FROM people.company_slot
WHERE outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids);

-- 5.3 Delete people.people_master (only those now without slots)
DELETE FROM people.people_master
WHERE unique_id IN (
    SELECT unique_id FROM people.people_master_archive
    WHERE archive_reason = 'sovereign_cleanup_2026-01-21'
);

-- 5.4 Delete outreach.company_target
DELETE FROM outreach.company_target
WHERE outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids);

-- 5.5 Delete outreach.outreach
DELETE FROM outreach.outreach
WHERE outreach_id IN (SELECT outreach_id FROM orphaned_outreach_ids);

DO $$ BEGIN RAISE NOTICE 'Completed deleting orphaned records'; END $$;

-- ============================================================================
-- PHASE 6: VERIFICATION
-- ============================================================================

DO $$
DECLARE
    outreach_count INT;
    ct_count INT;
    slot_count INT;
    people_count INT;
    pm_count INT;
    cl_pass INT;
BEGIN
    SELECT COUNT(*) INTO outreach_count FROM outreach.outreach;
    SELECT COUNT(*) INTO ct_count FROM outreach.company_target;
    SELECT COUNT(*) INTO slot_count FROM people.company_slot;
    SELECT COUNT(*) INTO people_count FROM outreach.people;
    SELECT COUNT(*) INTO pm_count FROM people.people_master;
    SELECT COUNT(*) INTO cl_pass FROM cl.company_identity WHERE identity_status = 'PASS';

    RAISE NOTICE '============================================================';
    RAISE NOTICE 'POST-CLEANUP VERIFICATION';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'cl.company_identity (PASS): %', cl_pass;
    RAISE NOTICE 'outreach.outreach: %', outreach_count;
    RAISE NOTICE 'outreach.company_target: %', ct_count;
    RAISE NOTICE 'people.company_slot: %', slot_count;
    RAISE NOTICE 'outreach.people: %', people_count;
    RAISE NOTICE 'people.people_master: %', pm_count;
    RAISE NOTICE '============================================================';

    IF outreach_count = cl_pass THEN
        RAISE NOTICE 'VERIFICATION: PASS - outreach.outreach aligned with CL';
    ELSE
        RAISE NOTICE 'VERIFICATION: outreach.outreach (%) vs cl.company_identity PASS (%)', outreach_count, cl_pass;
    END IF;
END $$;

-- Archive table counts
DO $$
DECLARE
    outreach_archive INT;
    ct_archive INT;
    slot_archive INT;
    people_archive INT;
    pm_archive INT;
BEGIN
    SELECT COUNT(*) INTO outreach_archive FROM outreach.outreach_archive;
    SELECT COUNT(*) INTO ct_archive FROM outreach.company_target_archive;
    SELECT COUNT(*) INTO slot_archive FROM people.company_slot_archive;
    SELECT COUNT(*) INTO people_archive FROM outreach.people_archive;
    SELECT COUNT(*) INTO pm_archive FROM people.people_master_archive;

    RAISE NOTICE '============================================================';
    RAISE NOTICE 'ARCHIVE TABLE COUNTS';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'outreach.outreach_archive: %', outreach_archive;
    RAISE NOTICE 'outreach.company_target_archive: %', ct_archive;
    RAISE NOTICE 'people.company_slot_archive: %', slot_archive;
    RAISE NOTICE 'outreach.people_archive: %', people_archive;
    RAISE NOTICE 'people.people_master_archive: %', pm_archive;
END $$;

-- Cleanup temp table
DROP TABLE IF EXISTS orphaned_outreach_ids;

COMMIT;
