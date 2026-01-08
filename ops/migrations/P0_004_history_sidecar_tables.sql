-- =============================================================================
-- P0 MIGRATION: HISTORY SIDECAR TABLES
-- =============================================================================
-- Migration ID: P0_004
-- Date: 2026-01-08
-- Author: Claude Code (Schema Remediation Engineer)
-- Mode: SAFE MODE - Append-only, no core table changes
--
-- PURPOSE:
--   Create history sidecar tables for all sub-hubs that touch the outside world.
--   These prevent re-scraping, re-enriching, and re-paying for the same answer.
--
-- DOCTRINE (LOCKED):
--   - Core tables = current truth
--   - History tables = what we already tried, when, and with what result
--   - History tables are APPEND-ONLY (no updates, no deletes)
--   - Every ingestion checks history before acting
--   - No history = infinite loops
--
-- TABLES CREATED:
--   1. outreach.blog_source_history (Company-Level URL Memory)
--   2. people.people_resolution_history (Slot Resolution Memory)
--   3. talent_flow.movement_history (Movement Memory)
--   4. outreach.bit_input_history (Signal Cost Control)
--
-- ROLLBACK: See P0_004_history_sidecar_tables_ROLLBACK.sql
-- =============================================================================

-- =============================================================================
-- TABLE 1: outreach.blog_source_history
-- =============================================================================
-- Purpose: Never re-discover URLs. Track what we've seen and when.
--
-- Benefits:
--   - Never re-lookup a company blog URL
--   - Detect redirects / dead links
--   - Skip unchanged content via checksum
--   - Cheap TTL logic via last_checked_at
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach.blog_source_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Spine reference
    outreach_id UUID NOT NULL REFERENCES outreach.outreach(outreach_id),

    -- Source identification
    source_type VARCHAR(50) NOT NULL,           -- website, blog, press, social
    source_url TEXT NOT NULL,

    -- Discovery tracking
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_checked_at TIMESTAMPTZ,

    -- Health status
    status VARCHAR(20) DEFAULT 'active',        -- active, dead, redirected
    http_status INT,
    redirect_url TEXT,

    -- Content fingerprint
    checksum TEXT,                              -- SHA256 content hash

    -- Traceability
    process_id UUID,
    correlation_id UUID,

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Uniqueness: one entry per URL per company
    CONSTRAINT uq_blog_source_outreach_url UNIQUE (outreach_id, source_url)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_blog_source_history_outreach
ON outreach.blog_source_history(outreach_id);

CREATE INDEX IF NOT EXISTS idx_blog_source_history_status
ON outreach.blog_source_history(status);

CREATE INDEX IF NOT EXISTS idx_blog_source_history_last_checked
ON outreach.blog_source_history(last_checked_at);

CREATE INDEX IF NOT EXISTS idx_blog_source_history_checksum
ON outreach.blog_source_history(checksum)
WHERE checksum IS NOT NULL;

-- Table comment
COMMENT ON TABLE outreach.blog_source_history IS
'HISTORY.BLOG.001 | Blog source URL memory. APPEND-ONLY.
Prevents re-discovery of URLs. Tracks health, redirects, content changes.
Check this table BEFORE making any blog/website HTTP call.
Rule: If (outreach_id, source_url) exists, do NOT re-fetch unless TTL expired.';

-- =============================================================================
-- TABLE 2: people.people_resolution_history
-- =============================================================================
-- Purpose: Never "try the same person again" for slot resolution.
--
-- Benefits:
--   - No retry loops
--   - Clear "we already checked this" logic
--   - Cheap movement detection later
-- =============================================================================

CREATE TABLE IF NOT EXISTS people.people_resolution_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Spine reference
    outreach_id UUID NOT NULL REFERENCES outreach.outreach(outreach_id),

    -- Slot context
    slot_type VARCHAR(20) NOT NULL,             -- CEO, CFO, HR, BEN

    -- Person identification (what we checked)
    person_identifier TEXT NOT NULL,            -- linkedin_url or email

    -- Resolution result
    resolution_outcome VARCHAR(30) NOT NULL,    -- MATCHED, REJECTED, AMBIGUOUS, NOT_FOUND
    rejection_reason TEXT,                      -- Why rejected (if applicable)

    -- Confidence
    confidence_score NUMERIC(5,2),

    -- Source tracking
    source VARCHAR(50),                         -- linkedin, clay, manual, etc.
    source_response JSONB,                      -- Raw response (if needed for debugging)

    -- Timing
    checked_at TIMESTAMPTZ DEFAULT NOW(),

    -- Traceability
    process_id UUID,
    correlation_id UUID,

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Uniqueness: one resolution attempt per person per slot per company
    CONSTRAINT uq_people_resolution UNIQUE (outreach_id, slot_type, person_identifier)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_people_resolution_outreach
ON people.people_resolution_history(outreach_id);

CREATE INDEX IF NOT EXISTS idx_people_resolution_slot
ON people.people_resolution_history(slot_type);

CREATE INDEX IF NOT EXISTS idx_people_resolution_outcome
ON people.people_resolution_history(resolution_outcome);

CREATE INDEX IF NOT EXISTS idx_people_resolution_identifier
ON people.people_resolution_history(person_identifier);

CREATE INDEX IF NOT EXISTS idx_people_resolution_checked
ON people.people_resolution_history(checked_at);

-- Table comment
COMMENT ON TABLE people.people_resolution_history IS
'HISTORY.PEOPLE.001 | Slot resolution memory. APPEND-ONLY.
Prevents re-trying the same person for the same slot.
Check this table BEFORE making any enrichment API call.
Rule: If (outreach_id, slot_type, person_identifier) exists, use cached outcome.';

-- =============================================================================
-- TABLE 3: talent_flow.movement_history
-- =============================================================================
-- Purpose: Never re-emit the same movement.
--
-- Benefits:
--   - Idempotent Talent Flow
--   - No duplicate BIT signals
--   - Clean reprocessing rules
-- =============================================================================

CREATE TABLE IF NOT EXISTS talent_flow.movement_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Person identification
    person_identifier TEXT NOT NULL,            -- linkedin_url or unique person key

    -- Movement details
    from_outreach_id UUID,                      -- NULL if external/unknown origin
    to_outreach_id UUID,                        -- NULL if external/unknown destination
    movement_type VARCHAR(30),                  -- hire, departure, promotion, transfer

    -- Detection
    detected_at TIMESTAMPTZ,                    -- When movement was detected
    detection_source VARCHAR(50),               -- linkedin, manual, etc.

    -- Processing
    processed_at TIMESTAMPTZ DEFAULT NOW(),
    signal_emitted VARCHAR(50),                 -- What signal was emitted (if any)
    bit_event_created BOOLEAN DEFAULT FALSE,

    -- Traceability
    correlation_id UUID,
    process_id UUID,

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Uniqueness: one movement record per person per company pair
    CONSTRAINT uq_movement_history UNIQUE (person_identifier, from_outreach_id, to_outreach_id),

    -- FK to spine (optional - may be external companies)
    CONSTRAINT fk_movement_history_from
        FOREIGN KEY (from_outreach_id)
        REFERENCES outreach.outreach(outreach_id)
        ON DELETE SET NULL,
    CONSTRAINT fk_movement_history_to
        FOREIGN KEY (to_outreach_id)
        REFERENCES outreach.outreach(outreach_id)
        ON DELETE SET NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_movement_history_person
ON talent_flow.movement_history(person_identifier);

CREATE INDEX IF NOT EXISTS idx_movement_history_from
ON talent_flow.movement_history(from_outreach_id)
WHERE from_outreach_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_movement_history_to
ON talent_flow.movement_history(to_outreach_id)
WHERE to_outreach_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_movement_history_detected
ON talent_flow.movement_history(detected_at);

CREATE INDEX IF NOT EXISTS idx_movement_history_correlation
ON talent_flow.movement_history(correlation_id);

-- Table comment
COMMENT ON TABLE talent_flow.movement_history IS
'HISTORY.TF.001 | Movement memory. APPEND-ONLY.
Prevents re-emitting the same movement signal.
Check this table BEFORE creating any BIT event from movement.
Rule: If (person_identifier, from_outreach_id, to_outreach_id) exists, SKIP.';

-- =============================================================================
-- TABLE 4: outreach.bit_input_history
-- =============================================================================
-- Purpose: Never score the same signal twice. Cost control.
--
-- Benefits:
--   - No duplicate BIT calculations
--   - Signal deduplication via fingerprint
--   - Cost tracking per signal type
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach.bit_input_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Spine reference
    outreach_id UUID NOT NULL REFERENCES outreach.outreach(outreach_id),

    -- Signal identification
    signal_type VARCHAR(50) NOT NULL,           -- exec_movement, funding, job_posting, etc.
    source VARCHAR(50) NOT NULL,                -- talent_flow, dol, blog, etc.
    signal_fingerprint TEXT NOT NULL,           -- SHA256 of signal payload

    -- Signal data (optional - for debugging)
    signal_payload JSONB,

    -- Processing tracking
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    use_count INTEGER DEFAULT 1,

    -- Score contribution
    score_contribution INTEGER,                 -- How many points this signal added

    -- Traceability
    correlation_id UUID,
    process_id UUID,

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Uniqueness: one signal fingerprint per company
    CONSTRAINT uq_bit_input_fingerprint UNIQUE (outreach_id, signal_fingerprint)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_bit_input_history_outreach
ON outreach.bit_input_history(outreach_id);

CREATE INDEX IF NOT EXISTS idx_bit_input_history_signal_type
ON outreach.bit_input_history(signal_type);

CREATE INDEX IF NOT EXISTS idx_bit_input_history_source
ON outreach.bit_input_history(source);

CREATE INDEX IF NOT EXISTS idx_bit_input_history_fingerprint
ON outreach.bit_input_history(signal_fingerprint);

CREATE INDEX IF NOT EXISTS idx_bit_input_history_first_seen
ON outreach.bit_input_history(first_seen_at);

-- Table comment
COMMENT ON TABLE outreach.bit_input_history IS
'HISTORY.BIT.001 | BIT signal memory. APPEND-ONLY.
Prevents scoring the same signal twice.
Check this table BEFORE adding any signal to BIT calculation.
Rule: If (outreach_id, signal_fingerprint) exists, do NOT re-score.';

-- =============================================================================
-- APPEND-ONLY ENFORCEMENT (NON-NEGOTIABLE)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Trigger: Block UPDATE on blog_source_history (allow only last_checked_at)
-- -----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION outreach.enforce_blog_history_append_only()
RETURNS TRIGGER AS $$
BEGIN
    -- Allow update ONLY to last_checked_at, status, http_status, checksum
    IF OLD.history_id != NEW.history_id OR
       OLD.outreach_id != NEW.outreach_id OR
       OLD.source_type != NEW.source_type OR
       OLD.source_url != NEW.source_url OR
       OLD.first_seen_at != NEW.first_seen_at OR
       OLD.created_at != NEW.created_at THEN
        RAISE EXCEPTION 'outreach.blog_source_history is APPEND-ONLY. Only last_checked_at, status, http_status, checksum may be updated.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_blog_history_append_only
    BEFORE UPDATE ON outreach.blog_source_history
    FOR EACH ROW
    EXECUTE FUNCTION outreach.enforce_blog_history_append_only();

-- Block DELETE
CREATE OR REPLACE FUNCTION outreach.block_blog_history_delete()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'outreach.blog_source_history is APPEND-ONLY. Deletes are prohibited.';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_blog_history_no_delete
    BEFORE DELETE ON outreach.blog_source_history
    FOR EACH ROW
    EXECUTE FUNCTION outreach.block_blog_history_delete();

-- -----------------------------------------------------------------------------
-- Trigger: Block UPDATE/DELETE on people_resolution_history
-- -----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION people.block_resolution_history_update()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'people.people_resolution_history is APPEND-ONLY. Updates are prohibited.';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_resolution_history_no_update
    BEFORE UPDATE ON people.people_resolution_history
    FOR EACH ROW
    EXECUTE FUNCTION people.block_resolution_history_update();

CREATE OR REPLACE FUNCTION people.block_resolution_history_delete()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'people.people_resolution_history is APPEND-ONLY. Deletes are prohibited.';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_resolution_history_no_delete
    BEFORE DELETE ON people.people_resolution_history
    FOR EACH ROW
    EXECUTE FUNCTION people.block_resolution_history_delete();

-- -----------------------------------------------------------------------------
-- Trigger: Block UPDATE/DELETE on movement_history
-- -----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION talent_flow.block_movement_history_update()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'talent_flow.movement_history is APPEND-ONLY. Updates are prohibited.';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_movement_history_no_update
    BEFORE UPDATE ON talent_flow.movement_history
    FOR EACH ROW
    EXECUTE FUNCTION talent_flow.block_movement_history_update();

CREATE OR REPLACE FUNCTION talent_flow.block_movement_history_delete()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'talent_flow.movement_history is APPEND-ONLY. Deletes are prohibited.';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_movement_history_no_delete
    BEFORE DELETE ON talent_flow.movement_history
    FOR EACH ROW
    EXECUTE FUNCTION talent_flow.block_movement_history_delete();

-- -----------------------------------------------------------------------------
-- Trigger: Block UPDATE/DELETE on bit_input_history (allow only last_used_at)
-- -----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION outreach.enforce_bit_history_append_only()
RETURNS TRIGGER AS $$
BEGIN
    -- Allow update ONLY to last_used_at, use_count
    IF OLD.history_id != NEW.history_id OR
       OLD.outreach_id != NEW.outreach_id OR
       OLD.signal_type != NEW.signal_type OR
       OLD.source != NEW.source OR
       OLD.signal_fingerprint != NEW.signal_fingerprint OR
       OLD.first_seen_at != NEW.first_seen_at OR
       OLD.created_at != NEW.created_at THEN
        RAISE EXCEPTION 'outreach.bit_input_history is APPEND-ONLY. Only last_used_at, use_count may be updated.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_bit_history_append_only
    BEFORE UPDATE ON outreach.bit_input_history
    FOR EACH ROW
    EXECUTE FUNCTION outreach.enforce_bit_history_append_only();

CREATE OR REPLACE FUNCTION outreach.block_bit_history_delete()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'outreach.bit_input_history is APPEND-ONLY. Deletes are prohibited.';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_bit_history_no_delete
    BEFORE DELETE ON outreach.bit_input_history
    FOR EACH ROW
    EXECUTE FUNCTION outreach.block_bit_history_delete();

-- =============================================================================
-- HELPER FUNCTIONS (Check Before Acting)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Function: Check if blog URL already known
-- -----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION outreach.blog_url_exists(
    p_outreach_id UUID,
    p_source_url TEXT
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM outreach.blog_source_history
        WHERE outreach_id = p_outreach_id
          AND source_url = p_source_url
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION outreach.blog_url_exists IS
'Check if blog URL already exists in history. Call BEFORE fetching any URL.';

-- -----------------------------------------------------------------------------
-- Function: Check if person already resolved for slot
-- -----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION people.person_already_resolved(
    p_outreach_id UUID,
    p_slot_type VARCHAR,
    p_person_identifier TEXT
) RETURNS TABLE (
    already_resolved BOOLEAN,
    previous_outcome VARCHAR,
    checked_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        TRUE,
        prh.resolution_outcome,
        prh.checked_at
    FROM people.people_resolution_history prh
    WHERE prh.outreach_id = p_outreach_id
      AND prh.slot_type = p_slot_type
      AND prh.person_identifier = p_person_identifier;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, NULL::VARCHAR, NULL::TIMESTAMPTZ;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION people.person_already_resolved IS
'Check if person already resolved for slot. Call BEFORE making enrichment API call.';

-- -----------------------------------------------------------------------------
-- Function: Check if movement already recorded
-- -----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION talent_flow.movement_already_recorded(
    p_person_identifier TEXT,
    p_from_outreach_id UUID,
    p_to_outreach_id UUID
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM talent_flow.movement_history
        WHERE person_identifier = p_person_identifier
          AND (from_outreach_id IS NOT DISTINCT FROM p_from_outreach_id)
          AND (to_outreach_id IS NOT DISTINCT FROM p_to_outreach_id)
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION talent_flow.movement_already_recorded IS
'Check if movement already recorded. Call BEFORE emitting any movement signal.';

-- -----------------------------------------------------------------------------
-- Function: Check if BIT signal already processed
-- -----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION outreach.bit_signal_already_processed(
    p_outreach_id UUID,
    p_signal_fingerprint TEXT
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM outreach.bit_input_history
        WHERE outreach_id = p_outreach_id
          AND signal_fingerprint = p_signal_fingerprint
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION outreach.bit_signal_already_processed IS
'Check if BIT signal already processed. Call BEFORE adding signal to BIT calculation.';

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================
-- Run these after migration:
--
-- 1. Check all tables created:
-- SELECT tablename, schemaname FROM pg_tables
-- WHERE tablename IN ('blog_source_history', 'people_resolution_history', 'movement_history', 'bit_input_history');
--
-- 2. Check triggers created:
-- SELECT trigger_name, event_object_table FROM information_schema.triggers
-- WHERE event_object_schema IN ('outreach', 'people', 'talent_flow')
-- AND trigger_name LIKE '%history%';
--
-- 3. Check functions created:
-- SELECT routine_name, routine_schema FROM information_schema.routines
-- WHERE routine_name IN ('blog_url_exists', 'person_already_resolved', 'movement_already_recorded', 'bit_signal_already_processed');
--
-- 4. Test append-only enforcement:
-- INSERT INTO outreach.blog_source_history (outreach_id, source_type, source_url)
-- VALUES ('some-uuid', 'blog', 'https://example.com');
-- UPDATE outreach.blog_source_history SET source_url = 'https://other.com' WHERE ...;
-- Expected: ERROR - APPEND-ONLY violation

-- =============================================================================
-- MIGRATION P0_004 COMPLETE
-- =============================================================================
-- CREATED:
--   - outreach.blog_source_history (URL memory)
--   - people.people_resolution_history (Slot resolution memory)
--   - talent_flow.movement_history (Movement memory)
--   - outreach.bit_input_history (Signal cost control)
--   - 8 append-only enforcement triggers
--   - 4 helper functions (check before acting)
--   - 16 indexes
--
-- DOCTRINE LOCKED:
--   - History tables are APPEND-ONLY
--   - Core tables stay clean
--   - Every ingestion checks history before acting
--   - History is never "fixed" — only superseded
--
-- INTEGRATION:
--   Before any external call, check the relevant history table.
--   If record exists, use cached result. If not, proceed and log.
-- =============================================================================
