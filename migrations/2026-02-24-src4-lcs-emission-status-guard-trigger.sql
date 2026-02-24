-- ============================================================================
-- SRC 4 — LCS Emission Status Guard Trigger
-- ============================================================================
-- WORK_PACKET: WP_20260224T0740_SRC4_LCS_EMISSION_STATUS_GUARD_TRIGGER
-- Doctrine:    2.8.0
-- Date:        2026-02-24
--
-- Replaces Phase 2A status-based trigger with column-level immutability guard.
-- Adds reject_reason column. Blocks UPDATE on identity/evidence columns.
-- Allows: status, reject_reason, promoted_cid, error_id, processed_at.
-- DELETE remains fully blocked.
--
-- NOTE: WP references ingest_status; existing schema uses status (Phase 2A).
-- Same semantic — adapted to live schema.
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. ADD reject_reason column
-- ============================================================================

ALTER TABLE lcs.movement_emission_intake
    ADD COLUMN IF NOT EXISTS reject_reason TEXT;

-- ============================================================================
-- 2. REPLACE trigger — column-level immutability guard
-- ============================================================================

-- Drop the Phase 2A status-based trigger (less strict)
DROP TRIGGER IF EXISTS trg_emission_intake_no_update ON lcs.movement_emission_intake;

-- New guard: identity and evidence columns are immutable after insert.
-- Allowed mutable columns: status, reject_reason, promoted_cid, error_id, processed_at.
CREATE OR REPLACE FUNCTION lcs.fn_emission_intake_guard()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.emission_id        != OLD.emission_id        OR
       NEW.source_hub         != OLD.source_hub         OR
       NEW.movement_type_code != OLD.movement_type_code OR
       NEW.outreach_id        IS DISTINCT FROM OLD.outreach_id  OR
       NEW.sovereign_id       IS DISTINCT FROM OLD.sovereign_id OR
       NEW.evidence           != OLD.evidence            OR
       NEW.dedupe_key         != OLD.dedupe_key          OR
       NEW.created_at         != OLD.created_at          THEN
        RAISE EXCEPTION
            'lcs.movement_emission_intake: identity/evidence columns are immutable. '
            'Only status, reject_reason, promoted_cid, error_id, processed_at may change. '
            'emission_id=%', OLD.emission_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_emission_intake_guard
    BEFORE UPDATE ON lcs.movement_emission_intake
    FOR EACH ROW
    EXECUTE FUNCTION lcs.fn_emission_intake_guard();

-- DELETE trigger unchanged from Phase 2A (trg_emission_intake_no_delete remains)

-- ============================================================================
-- 3. COMMENTS
-- ============================================================================

COMMENT ON FUNCTION lcs.fn_emission_intake_guard() IS
    'Column-level immutability guard. Blocks changes to identity/evidence columns. Allows: status, reject_reason, promoted_cid, error_id, processed_at.';

COMMIT;
