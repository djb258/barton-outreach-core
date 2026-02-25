-- ============================================================================
-- Phase 3D — Retry + Dead-Letter Governor (Deterministic)
-- ============================================================================
-- WORK_PACKET: WP_20260224T0920_PHASE3D_RETRY_DEAD_LETTER_GOVERNOR_DETERMINISTIC
-- Doctrine:    2.8.0
-- Date:        2026-02-24
--
-- Creates:
--   Table:    lcs.retry_queue (SUPPORTING, CTB-registered)
--   Function: lcs.fn_enqueue_retry(text, uuid, uuid, text, int) → uuid
--   Function: lcs.fn_process_retry_batch(int) → jsonb
--   View:     lcs.v_dead_letter_queue
--
-- Modifies:
--   Table:    lcs.lcs_errors — adds is_retryable, retry_strategy columns
--
-- Retry strategies: IMMEDIATE, BACKOFF_5M, BACKOFF_1H, BACKOFF_1D
-- Strategy escalation: IMMEDIATE → BACKOFF_5M → BACKOFF_1H → BACKOFF_1D
-- Dead-letter: attempt_count >= max_attempts → DEAD
-- No RAISE-after-DML.
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. CTB Registration
-- ============================================================================

INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, is_frozen, registered_by, notes)
VALUES ('lcs', 'retry_queue', 'SUPPORTING', FALSE, 'phase3d_retry_governor',
    'Retry queue — deterministic retry scheduling with strategy escalation and dead-letter quarantine.')
ON CONFLICT (table_schema, table_name) DO NOTHING;

-- ============================================================================
-- 2. Extend lcs.lcs_errors with retry eligibility fields
-- ============================================================================

ALTER TABLE lcs.lcs_errors ADD COLUMN IF NOT EXISTS is_retryable BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE lcs.lcs_errors ADD COLUMN IF NOT EXISTS retry_strategy TEXT;

-- ============================================================================
-- 3. lcs.retry_queue — Deterministic retry scheduling
-- ============================================================================

CREATE TABLE lcs.retry_queue (
    retry_id        UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type     TEXT        NOT NULL,
    entity_id       UUID        NOT NULL,
    error_id        UUID        REFERENCES lcs.lcs_errors(error_id),
    retry_strategy  TEXT        NOT NULL,
    attempt_count   INTEGER     NOT NULL DEFAULT 0,
    max_attempts    INTEGER     NOT NULL DEFAULT 5,
    next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status          TEXT        NOT NULL DEFAULT 'PENDING',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE lcs.retry_queue ADD CONSTRAINT chk_retry_entity_type
    CHECK (entity_type IN ('EMISSION', 'MID'));

ALTER TABLE lcs.retry_queue ADD CONSTRAINT chk_retry_strategy
    CHECK (retry_strategy IN ('IMMEDIATE', 'BACKOFF_5M', 'BACKOFF_1H', 'BACKOFF_1D'));

ALTER TABLE lcs.retry_queue ADD CONSTRAINT chk_retry_status
    CHECK (status IN ('PENDING', 'IN_PROGRESS', 'SUCCEEDED', 'DEAD'));

-- One active retry item per entity (PENDING or IN_PROGRESS)
CREATE UNIQUE INDEX idx_retry_queue_active_entity
    ON lcs.retry_queue(entity_type, entity_id)
    WHERE status IN ('PENDING', 'IN_PROGRESS');

CREATE INDEX idx_retry_queue_pending
    ON lcs.retry_queue(next_attempt_at, created_at)
    WHERE status = 'PENDING';

CREATE INDEX idx_retry_queue_dead
    ON lcs.retry_queue(entity_type, updated_at DESC)
    WHERE status = 'DEAD';

-- ============================================================================
-- 4. fn_enqueue_retry — Idempotent retry enqueue
-- ============================================================================
-- Upserts into retry_queue. If an active item (PENDING/IN_PROGRESS) already
-- exists for the entity, returns existing retry_id (idempotent).
-- Otherwise inserts new row with next_attempt_at from strategy.
-- No RAISE-after-DML.
-- ============================================================================

CREATE OR REPLACE FUNCTION lcs.fn_enqueue_retry(
    p_entity_type   TEXT,
    p_entity_id     UUID,
    p_error_id      UUID DEFAULT NULL,
    p_retry_strategy TEXT DEFAULT 'IMMEDIATE',
    p_max_attempts  INTEGER DEFAULT 5
)
RETURNS UUID AS $$
DECLARE
    v_retry_id      UUID;
    v_next_attempt  TIMESTAMPTZ;
BEGIN
    -- Check for existing active retry
    SELECT retry_id INTO v_retry_id
    FROM lcs.retry_queue
    WHERE entity_type = p_entity_type
      AND entity_id = p_entity_id
      AND status IN ('PENDING', 'IN_PROGRESS');

    IF v_retry_id IS NOT NULL THEN
        RETURN v_retry_id;
    END IF;

    -- Compute next_attempt_at from strategy
    v_next_attempt := NOW() + CASE p_retry_strategy
        WHEN 'IMMEDIATE'  THEN INTERVAL '0 seconds'
        WHEN 'BACKOFF_5M' THEN INTERVAL '5 minutes'
        WHEN 'BACKOFF_1H' THEN INTERVAL '1 hour'
        WHEN 'BACKOFF_1D' THEN INTERVAL '1 day'
        ELSE INTERVAL '0 seconds'
    END;

    INSERT INTO lcs.retry_queue (entity_type, entity_id, error_id, retry_strategy, max_attempts, next_attempt_at)
    VALUES (p_entity_type, p_entity_id, p_error_id, p_retry_strategy, p_max_attempts, v_next_attempt)
    RETURNING retry_id INTO v_retry_id;

    RETURN v_retry_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 5. fn_process_retry_batch — SKIP LOCKED retry processor
-- ============================================================================
-- Selects PENDING rows where next_attempt_at <= NOW().
-- Marks IN_PROGRESS, increments attempt_count.
-- Routes: EMISSION → fn_promote_emission, MID → fn_mark_mid_ready.
-- On success: SUCCEEDED. On failure: DEAD if at max_attempts, else PENDING
-- with strategy escalation.
-- Returns JSON summary. No RAISE-after-DML.
-- ============================================================================

CREATE OR REPLACE FUNCTION lcs.fn_process_retry_batch(p_limit INTEGER DEFAULT 200)
RETURNS JSONB AS $$
DECLARE
    v_row           lcs.retry_queue%ROWTYPE;
    v_attempted     INTEGER := 0;
    v_succeeded     INTEGER := 0;
    v_dead          INTEGER := 0;
    v_remaining     INTEGER;
    v_success       BOOLEAN;
    v_entity_status TEXT;
    v_next_strategy TEXT;
    v_next_attempt  TIMESTAMPTZ;
BEGIN
    FOR v_row IN
        SELECT * FROM lcs.retry_queue
        WHERE status = 'PENDING'
          AND next_attempt_at <= NOW()
        ORDER BY next_attempt_at, created_at
        LIMIT p_limit
        FOR UPDATE SKIP LOCKED
    LOOP
        v_attempted := v_attempted + 1;

        -- Mark IN_PROGRESS and increment attempt_count
        UPDATE lcs.retry_queue
        SET status = 'IN_PROGRESS',
            attempt_count = attempt_count + 1,
            updated_at = NOW()
        WHERE retry_id = v_row.retry_id;

        -- Route by entity_type
        v_success := FALSE;

        IF v_row.entity_type = 'EMISSION' THEN
            PERFORM lcs.fn_promote_emission(v_row.entity_id);
            SELECT status INTO v_entity_status
            FROM lcs.movement_emission_intake WHERE emission_id = v_row.entity_id;
            v_success := (v_entity_status = 'PROMOTED');

        ELSIF v_row.entity_type = 'MID' THEN
            PERFORM lcs.fn_mark_mid_ready(v_row.entity_id);
            SELECT dispatch_state::text INTO v_entity_status
            FROM lcs.mid_ledger WHERE mid = v_row.entity_id;
            v_success := (v_entity_status = 'READY');
        END IF;

        IF v_success THEN
            -- Mark SUCCEEDED
            UPDATE lcs.retry_queue
            SET status = 'SUCCEEDED', updated_at = NOW()
            WHERE retry_id = v_row.retry_id;
            v_succeeded := v_succeeded + 1;

        ELSIF (v_row.attempt_count + 1) >= v_row.max_attempts THEN
            -- Max attempts reached → DEAD
            UPDATE lcs.retry_queue
            SET status = 'DEAD', updated_at = NOW()
            WHERE retry_id = v_row.retry_id;
            v_dead := v_dead + 1;

        ELSE
            -- Escalate strategy and return to PENDING
            v_next_strategy := CASE v_row.retry_strategy
                WHEN 'IMMEDIATE'  THEN 'BACKOFF_5M'
                WHEN 'BACKOFF_5M' THEN 'BACKOFF_1H'
                WHEN 'BACKOFF_1H' THEN 'BACKOFF_1D'
                WHEN 'BACKOFF_1D' THEN 'BACKOFF_1D'
            END;

            v_next_attempt := NOW() + CASE v_next_strategy
                WHEN 'IMMEDIATE'  THEN INTERVAL '0 seconds'
                WHEN 'BACKOFF_5M' THEN INTERVAL '5 minutes'
                WHEN 'BACKOFF_1H' THEN INTERVAL '1 hour'
                WHEN 'BACKOFF_1D' THEN INTERVAL '1 day'
            END;

            UPDATE lcs.retry_queue
            SET status = 'PENDING',
                retry_strategy = v_next_strategy,
                next_attempt_at = v_next_attempt,
                updated_at = NOW()
            WHERE retry_id = v_row.retry_id;
        END IF;

    END LOOP;

    -- Count remaining pending
    SELECT count(*) INTO v_remaining
    FROM lcs.retry_queue WHERE status = 'PENDING';

    RETURN jsonb_build_object(
        'attempted', v_attempted,
        'succeeded', v_succeeded,
        'dead', v_dead,
        'remaining_pending', v_remaining
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 6. v_dead_letter_queue — DEAD items with error context
-- ============================================================================

CREATE OR REPLACE VIEW lcs.v_dead_letter_queue AS
SELECT
    rq.retry_id,
    rq.entity_type,
    rq.entity_id,
    rq.error_id,
    rq.retry_strategy,
    rq.attempt_count,
    rq.max_attempts,
    rq.created_at        AS retry_created_at,
    rq.updated_at        AS retry_updated_at,
    le.error_stage,
    le.error_type,
    le.error_payload     AS error_context,
    le.created_at        AS error_created_at
FROM lcs.retry_queue rq
LEFT JOIN lcs.lcs_errors le ON rq.error_id = le.error_id
WHERE rq.status = 'DEAD';

-- ============================================================================
-- 7. PERMISSIONS — lcs_worker function-mediated access
-- ============================================================================

GRANT EXECUTE ON FUNCTION lcs.fn_enqueue_retry(TEXT, UUID, UUID, TEXT, INTEGER) TO lcs_worker;
GRANT EXECUTE ON FUNCTION lcs.fn_process_retry_batch(INTEGER) TO lcs_worker;

-- No direct table writes
REVOKE ALL ON lcs.retry_queue FROM lcs_worker;
REVOKE ALL ON lcs.retry_queue FROM lcs_transport;

-- ============================================================================
-- 8. COMMENTS
-- ============================================================================

COMMENT ON TABLE lcs.retry_queue IS
    'SUPPORTING — Deterministic retry queue with strategy escalation. One active item per entity. DEAD at max_attempts.';
COMMENT ON FUNCTION lcs.fn_enqueue_retry(TEXT, UUID, UUID, TEXT, INTEGER) IS
    'Idempotent retry enqueue. Returns existing retry_id if active item exists. Computes next_attempt_at from strategy. No RAISE-after-DML.';
COMMENT ON FUNCTION lcs.fn_process_retry_batch(INTEGER) IS
    'SKIP LOCKED retry processor. Routes EMISSION→fn_promote_emission, MID→fn_mark_mid_ready. Escalates strategy on failure. Returns JSON summary.';
COMMENT ON VIEW lcs.v_dead_letter_queue IS
    'Dead letter view — DEAD retry items joined with error context from lcs_errors.';

COMMIT;
