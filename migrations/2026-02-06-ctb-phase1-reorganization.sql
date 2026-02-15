-- ============================================
-- CTB PHASE 1: STRUCTURAL REORGANIZATION
-- Date: 2026-02-06
-- Type: READ-WRITE MIGRATION
-- Rule: NO data deletion, NO column drops
-- ============================================

BEGIN;

-- ============================================
-- PRE-FLIGHT: Add discriminator columns to target tables
-- ============================================

-- Add source_hub to pipeline_audit_log
ALTER TABLE outreach.pipeline_audit_log
ADD COLUMN IF NOT EXISTS source_hub VARCHAR(50);

-- Add error_type to error tables if not exists
ALTER TABLE outreach.company_target_errors
ADD COLUMN IF NOT EXISTS error_type VARCHAR(100);

ALTER TABLE people.people_errors
ADD COLUMN IF NOT EXISTS error_type VARCHAR(100);

ALTER TABLE cl.cl_err_existence
ADD COLUMN IF NOT EXISTS error_type VARCHAR(100);

-- Add queue_type to entity_resolution_queue
ALTER TABLE outreach.entity_resolution_queue
ADD COLUMN IF NOT EXISTS queue_type VARCHAR(50);

-- Add signal_source to bit_signals
ALTER TABLE outreach.bit_signals
ADD COLUMN IF NOT EXISTS signal_source VARCHAR(50);

-- ============================================
-- PHASE 1A: DUPLICATE TRUTH TABLES → ARCHIVE
-- ============================================

-- Archive company.company_master
CREATE TABLE IF NOT EXISTS archive.company_company_master_ctb AS
SELECT *, NOW() as archived_at, 'ctb_phase1' as archive_reason
FROM company.company_master;

-- Archive marketing.company_master
CREATE TABLE IF NOT EXISTS archive.marketing_company_master_ctb AS
SELECT *, NOW() as archived_at, 'ctb_phase1' as archive_reason
FROM marketing.company_master;

-- Archive marketing.people_master
CREATE TABLE IF NOT EXISTS archive.marketing_people_master_ctb AS
SELECT *, NOW() as archived_at, 'ctb_phase1' as archive_reason
FROM marketing.people_master;

-- Archive company.company_slots
CREATE TABLE IF NOT EXISTS archive.company_company_slots_ctb AS
SELECT *, NOW() as archived_at, 'ctb_phase1' as archive_reason
FROM company.company_slots;

-- Archive company.message_key_reference
CREATE TABLE IF NOT EXISTS archive.company_message_key_reference_ctb AS
SELECT *, NOW() as archived_at, 'ctb_phase1' as archive_reason
FROM company.message_key_reference;

-- ============================================
-- PHASE 1B: ORPHANED ERROR TABLES → MERGE
-- ============================================

-- Merge marketing.failed_company_match → outreach.company_target_errors
INSERT INTO outreach.company_target_errors (error_type, error_message, created_at)
SELECT
    'failed_company_match' as error_type,
    COALESCE(to_json(fcm)::text, '{}') as error_message,
    COALESCE(fcm.created_at, NOW()) as created_at
FROM marketing.failed_company_match fcm
ON CONFLICT DO NOTHING;

-- Merge marketing.failed_no_pattern → outreach.company_target_errors
INSERT INTO outreach.company_target_errors (error_type, error_message, created_at)
SELECT
    'failed_no_pattern' as error_type,
    COALESCE(to_json(fnp)::text, '{}') as error_message,
    COALESCE(fnp.created_at, NOW()) as created_at
FROM marketing.failed_no_pattern fnp
ON CONFLICT DO NOTHING;

-- Merge marketing.failed_email_verification → people.people_errors
INSERT INTO people.people_errors (error_type, error_message, created_at)
SELECT
    'failed_email_verification' as error_type,
    COALESCE(to_json(fev)::text, '{}') as error_message,
    COALESCE(fev.created_at, NOW()) as created_at
FROM marketing.failed_email_verification fev
ON CONFLICT DO NOTHING;

-- Merge marketing.failed_slot_assignment → people.people_errors
INSERT INTO people.people_errors (error_type, error_message, created_at)
SELECT
    'failed_slot_assignment' as error_type,
    COALESCE(to_json(fsa)::text, '{}') as error_message,
    COALESCE(fsa.created_at, NOW()) as created_at
FROM marketing.failed_slot_assignment fsa
ON CONFLICT DO NOTHING;

-- Merge marketing.failed_low_confidence → cl.cl_err_existence
INSERT INTO cl.cl_err_existence (error_type, error_message, created_at)
SELECT
    'failed_low_confidence' as error_type,
    COALESCE(to_json(flc)::text, '{}') as error_message,
    COALESCE(flc.created_at, NOW()) as created_at
FROM marketing.failed_low_confidence flc
ON CONFLICT DO NOTHING;

-- Archive the merged tables
CREATE TABLE IF NOT EXISTS archive.marketing_failed_company_match_ctb AS
SELECT *, NOW() as archived_at FROM marketing.failed_company_match;

CREATE TABLE IF NOT EXISTS archive.marketing_failed_no_pattern_ctb AS
SELECT *, NOW() as archived_at FROM marketing.failed_no_pattern;

CREATE TABLE IF NOT EXISTS archive.marketing_failed_email_verification_ctb AS
SELECT *, NOW() as archived_at FROM marketing.failed_email_verification;

CREATE TABLE IF NOT EXISTS archive.marketing_failed_slot_assignment_ctb AS
SELECT *, NOW() as archived_at FROM marketing.failed_slot_assignment;

CREATE TABLE IF NOT EXISTS archive.marketing_failed_low_confidence_ctb AS
SELECT *, NOW() as archived_at FROM marketing.failed_low_confidence;

-- ============================================
-- PHASE 1H: TEMP TABLES → ARCHIVE
-- ============================================

-- Archive temp migration tables
CREATE TABLE IF NOT EXISTS archive.people_slot_orphan_snapshot_ctb AS
SELECT *, NOW() as archived_at FROM people.slot_orphan_snapshot_r0_002;

CREATE TABLE IF NOT EXISTS archive.people_slot_quarantine_ctb AS
SELECT *, NOW() as archived_at FROM people.slot_quarantine_r0_002;

-- ============================================
-- PHASE 1I: OUT OF SCOPE TABLES → ARCHIVE
-- ============================================

-- Archive Sales namespace tables
CREATE TABLE IF NOT EXISTS archive.public_sn_meeting_ctb AS
SELECT *, NOW() as archived_at FROM public.sn_meeting;

CREATE TABLE IF NOT EXISTS archive.public_sn_meeting_outcome_ctb AS
SELECT *, NOW() as archived_at FROM public.sn_meeting_outcome;

CREATE TABLE IF NOT EXISTS archive.public_sn_prospect_ctb AS
SELECT *, NOW() as archived_at FROM public.sn_prospect;

CREATE TABLE IF NOT EXISTS archive.public_sn_sales_process_ctb AS
SELECT *, NOW() as archived_at FROM public.sn_sales_process;

-- Archive talent_flow tables
CREATE TABLE IF NOT EXISTS archive.talent_flow_movement_history_ctb AS
SELECT *, NOW() as archived_at FROM talent_flow.movement_history;

CREATE TABLE IF NOT EXISTS archive.talent_flow_movements_ctb AS
SELECT *, NOW() as archived_at FROM talent_flow.movements;

-- ============================================
-- PHASE 1K: STRUCTURAL FIXES - ADD MISSING PKs
-- ============================================

-- Add PK to dol.form_5500_icp_filtered
ALTER TABLE dol.form_5500_icp_filtered
ADD COLUMN IF NOT EXISTS filter_id SERIAL;

-- Only add PK constraint if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'form_5500_icp_filtered_pkey'
    ) THEN
        ALTER TABLE dol.form_5500_icp_filtered
        ADD CONSTRAINT form_5500_icp_filtered_pkey PRIMARY KEY (filter_id);
    END IF;
END $$;

-- Add PK to people.people_master_archive
ALTER TABLE people.people_master_archive
ADD COLUMN IF NOT EXISTS archive_id SERIAL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'people_master_archive_pkey'
    ) THEN
        ALTER TABLE people.people_master_archive
        ADD CONSTRAINT people_master_archive_pkey PRIMARY KEY (archive_id);
    END IF;
END $$;

-- ============================================
-- PHASE 1J: DUPLICATE ARCHIVES → MERGE
-- ============================================

-- Merge outreach_orphan_archive into outreach_archive
INSERT INTO outreach.outreach_archive
SELECT * FROM outreach.outreach_orphan_archive
ON CONFLICT (outreach_id) DO NOTHING;

-- Merge company_target_orphaned_archive into company_target_archive
INSERT INTO outreach.company_target_archive
SELECT * FROM outreach.company_target_orphaned_archive
ON CONFLICT (target_id) DO NOTHING;

-- Archive the source tables before potential future cleanup
CREATE TABLE IF NOT EXISTS archive.outreach_orphan_archive_ctb AS
SELECT *, NOW() as archived_at FROM outreach.outreach_orphan_archive;

CREATE TABLE IF NOT EXISTS archive.company_target_orphaned_archive_ctb AS
SELECT *, NOW() as archived_at FROM outreach.company_target_orphaned_archive;

-- ============================================
-- PHASE 1L: AMBIGUOUS EMPTY TABLES → ARCHIVE
-- ============================================

-- Archive empty ambiguous tables for later decision
CREATE TABLE IF NOT EXISTS archive.company_company_events_ctb AS
SELECT *, NOW() as archived_at FROM company.company_events;

CREATE TABLE IF NOT EXISTS archive.company_company_sidecar_ctb AS
SELECT *, NOW() as archived_at FROM company.company_sidecar;

CREATE TABLE IF NOT EXISTS archive.company_contact_enrichment_ctb AS
SELECT *, NOW() as archived_at FROM company.contact_enrichment;

CREATE TABLE IF NOT EXISTS archive.company_email_verification_ctb AS
SELECT *, NOW() as archived_at FROM company.email_verification;

CREATE TABLE IF NOT EXISTS archive.company_pipeline_errors_ctb AS
SELECT *, NOW() as archived_at FROM company.pipeline_errors;

CREATE TABLE IF NOT EXISTS archive.company_validation_failures_log_ctb AS
SELECT *, NOW() as archived_at FROM company.validation_failures_log;

-- ============================================
-- LOG MIGRATION
-- ============================================

INSERT INTO public.migration_log (migration_name, executed_at, notes)
VALUES (
    '2026-02-06-ctb-phase1-reorganization',
    NOW(),
    'CTB Phase 1: Archives created, error tables merged, PKs added, discriminator columns added'
);

COMMIT;

-- ============================================
-- POST-MIGRATION VERIFICATION QUERIES
-- ============================================

-- Run these after migration to verify:
-- SELECT COUNT(*) FROM archive.company_company_master_ctb;
-- SELECT COUNT(*) FROM archive.marketing_company_master_ctb;
-- SELECT schemaname, tablename FROM pg_tables WHERE schemaname = 'archive' AND tablename LIKE '%_ctb' ORDER BY tablename;
