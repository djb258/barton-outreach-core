-- ============================================================================
-- Phase 4A — Cadence Governor (Frequency Caps + Time Windows)
-- ============================================================================
-- WORK_PACKET: WP_20260224T0930_PHASE4A_CADENCE_GOVERNOR_FREQUENCY_CAPS_TIME_WINDOWS
-- Doctrine:    2.8.0
-- Date:        2026-02-24
--
-- Creates:
--   Table:    lcs.cadence_policy_registry (REGISTRY, CTB-registered)
--   Table:    lcs.dispatch_attempt_log (SUPPORTING, CTB-registered, append-only)
--   Function: lcs.fn_cadence_check(uuid, text) → jsonb
--
-- Integration: Option B — READY remains channel-agnostic. fn_cadence_check is
--   a standalone evaluator called at send-attempt time. fn_finalize_dispatch_batch
--   will wire this in Phase 4B. Blocked/allowed decisions are logged to
--   dispatch_attempt_log with deterministic error behavior.
--
-- No RAISE-after-DML.
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. CTB Registration
-- ============================================================================

INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, is_frozen, registered_by, notes)
VALUES ('lcs', 'cadence_policy_registry', 'REGISTRY', FALSE, 'phase4a_cadence_governor',
    'Cadence policy registry — frequency caps, time windows, and timezone modes per lifecycle_stage + channel.')
ON CONFLICT (table_schema, table_name) DO NOTHING;

INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, is_frozen, registered_by, notes)
VALUES ('lcs', 'dispatch_attempt_log', 'SUPPORTING', FALSE, 'phase4a_cadence_governor',
    'Dispatch attempt log — append-only record of ALLOWED/BLOCKED cadence decisions with policy snapshots.')
ON CONFLICT (table_schema, table_name) DO NOTHING;

-- ============================================================================
-- 1b. Extend lcs_errors CHECK constraints for cadence_check stage
-- ============================================================================

ALTER TABLE lcs.lcs_errors DROP CONSTRAINT IF EXISTS chk_lcs_errors_stage;
ALTER TABLE lcs.lcs_errors ADD CONSTRAINT chk_lcs_errors_stage
    CHECK (error_stage IN ('cid_processing', 'sid_creation', 'mid_minting',
        'dispatch_finalization', 'canonical_update', 'emission_validation',
        'emission_processing', 'cadence_check'));

-- ============================================================================
-- 2. lcs.cadence_policy_registry — Frequency caps + time windows per stage/channel
-- ============================================================================

CREATE TABLE lcs.cadence_policy_registry (
    lifecycle_stage     TEXT        NOT NULL,
    channel             TEXT        NOT NULL,
    min_gap_hours       INTEGER     NOT NULL,
    max_sends_7d        INTEGER     NOT NULL,
    max_sends_30d       INTEGER     NOT NULL,
    allowed_days        INTEGER[]   NOT NULL,
    allowed_start_local TIME        NOT NULL,
    allowed_end_local   TIME        NOT NULL,
    timezone_mode       TEXT        NOT NULL DEFAULT 'ACCOUNT',
    is_enabled          BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (lifecycle_stage, channel)
);

ALTER TABLE lcs.cadence_policy_registry ADD CONSTRAINT chk_cadence_channel
    CHECK (channel IN ('EMAIL', 'LINKEDIN'));

ALTER TABLE lcs.cadence_policy_registry ADD CONSTRAINT chk_cadence_lifecycle_stage
    CHECK (lifecycle_stage IN ('SUSPECT', 'IDENTIFIED', 'QUALIFIED', 'ENGAGED', 'CONVERTED', 'SUPPRESSED'));

ALTER TABLE lcs.cadence_policy_registry ADD CONSTRAINT chk_cadence_timezone_mode
    CHECK (timezone_mode IN ('ACCOUNT', 'COMPANY', 'FIXED'));

ALTER TABLE lcs.cadence_policy_registry ADD CONSTRAINT chk_cadence_min_gap_positive
    CHECK (min_gap_hours >= 0);

ALTER TABLE lcs.cadence_policy_registry ADD CONSTRAINT chk_cadence_max_sends_positive
    CHECK (max_sends_7d > 0 AND max_sends_30d > 0);

ALTER TABLE lcs.cadence_policy_registry ADD CONSTRAINT chk_cadence_time_order
    CHECK (allowed_start_local < allowed_end_local);

-- Auto-maintain updated_at
CREATE OR REPLACE FUNCTION lcs.fn_cadence_policy_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_cadence_policy_updated_at
    BEFORE UPDATE ON lcs.cadence_policy_registry
    FOR EACH ROW
    EXECUTE FUNCTION lcs.fn_cadence_policy_updated_at();

-- ============================================================================
-- 3. lcs.dispatch_attempt_log — Append-only decision log
-- ============================================================================

CREATE TABLE lcs.dispatch_attempt_log (
    attempt_id      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    mid             UUID        NOT NULL REFERENCES lcs.mid_ledger(mid),
    sovereign_id    UUID        NOT NULL,
    channel         TEXT        NOT NULL,
    lifecycle_stage TEXT        NOT NULL,
    attempted_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    decision        TEXT        NOT NULL,
    block_reason    TEXT,
    policy_snapshot JSONB
);

ALTER TABLE lcs.dispatch_attempt_log ADD CONSTRAINT chk_attempt_decision
    CHECK (decision IN ('ALLOWED', 'BLOCKED'));

ALTER TABLE lcs.dispatch_attempt_log ADD CONSTRAINT chk_attempt_channel
    CHECK (channel IN ('EMAIL', 'LINKEDIN'));

-- Append-only: no UPDATE
CREATE OR REPLACE FUNCTION lcs.fn_dispatch_attempt_log_no_update()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'dispatch_attempt_log is append-only — UPDATE is forbidden';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_dispatch_attempt_log_no_update
    BEFORE UPDATE ON lcs.dispatch_attempt_log
    FOR EACH ROW
    EXECUTE FUNCTION lcs.fn_dispatch_attempt_log_no_update();

-- Append-only: no DELETE
CREATE OR REPLACE FUNCTION lcs.fn_dispatch_attempt_log_no_delete()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'dispatch_attempt_log is append-only — DELETE is forbidden';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_dispatch_attempt_log_no_delete
    BEFORE DELETE ON lcs.dispatch_attempt_log
    FOR EACH ROW
    EXECUTE FUNCTION lcs.fn_dispatch_attempt_log_no_delete();

-- Indexes for cadence lookups (sovereign + channel + time window)
CREATE INDEX idx_dispatch_attempt_sovereign_channel
    ON lcs.dispatch_attempt_log(sovereign_id, channel, attempted_at DESC);

CREATE INDEX idx_dispatch_attempt_mid
    ON lcs.dispatch_attempt_log(mid, attempted_at DESC);

-- ============================================================================
-- 4. fn_cadence_check — Deterministic cadence evaluator
-- ============================================================================
-- Evaluates frequency caps and time windows for a MID + channel.
-- Returns JSON decision: {allowed, block_reason, policy, metrics}
-- Does NOT mutate dispatch_state — caller decides.
-- Logs ALLOWED/BLOCKED row to dispatch_attempt_log.
-- No RAISE-after-DML.
-- ============================================================================

CREATE OR REPLACE FUNCTION lcs.fn_cadence_check(
    p_mid       UUID,
    p_channel   TEXT
)
RETURNS JSONB AS $$
DECLARE
    v_sovereign_id      UUID;
    v_lifecycle_stage    TEXT;
    v_policy             RECORD;
    v_last_send_at       TIMESTAMPTZ;
    v_count_7d           INTEGER;
    v_count_30d          INTEGER;
    v_hours_since_last   NUMERIC;
    v_current_dow        INTEGER;
    v_current_time       TIME;
    v_block_reason       TEXT := NULL;
    v_decision           TEXT;
    v_policy_json        JSONB;
    v_metrics_json       JSONB;
BEGIN
    -- -----------------------------------------------------------------------
    -- 1. Resolve sovereign_id + lifecycle_stage from mid_ledger + lcs_canonical
    -- -----------------------------------------------------------------------
    SELECT ml.sovereign_id, lc.current_lifecycle_stage::text
    INTO v_sovereign_id, v_lifecycle_stage
    FROM lcs.mid_ledger ml
    JOIN lcs.lcs_canonical lc ON ml.sovereign_id = lc.sovereign_id
    WHERE ml.mid = p_mid;

    IF v_sovereign_id IS NULL THEN
        -- MID not found or canonical missing — log error, return blocked
        -- mid FK: cannot reference non-existent MID, use NULL
        INSERT INTO lcs.lcs_errors (error_stage, error_type, error_payload)
        VALUES ('cadence_check', 'validation',
            jsonb_build_object('channel', p_channel, 'reason', 'MID not found or canonical record missing',
                'attempted_mid', p_mid::text));

        RETURN jsonb_build_object(
            'allowed', FALSE,
            'block_reason', 'MID_NOT_FOUND',
            'policy', NULL::jsonb,
            'metrics', NULL::jsonb
        );
    END IF;

    -- -----------------------------------------------------------------------
    -- 2. Fetch policy from cadence_policy_registry
    -- -----------------------------------------------------------------------
    SELECT * INTO v_policy
    FROM lcs.cadence_policy_registry
    WHERE lifecycle_stage = v_lifecycle_stage
      AND channel = p_channel
      AND is_enabled = TRUE;

    IF v_policy IS NULL THEN
        -- No policy = no restriction. Log ALLOWED, return.
        INSERT INTO lcs.dispatch_attempt_log
            (mid, sovereign_id, channel, lifecycle_stage, decision, block_reason, policy_snapshot)
        VALUES (p_mid, v_sovereign_id, p_channel, v_lifecycle_stage, 'ALLOWED', NULL,
            jsonb_build_object('reason', 'NO_POLICY'));

        RETURN jsonb_build_object(
            'allowed', TRUE,
            'block_reason', NULL,
            'policy', jsonb_build_object('reason', 'NO_POLICY'),
            'metrics', jsonb_build_object('last_send_at', NULL, 'count_7d', 0, 'count_30d', 0)
        );
    END IF;

    -- -----------------------------------------------------------------------
    -- 3. Compute send metrics from dispatch_attempt_log (ALLOWED decisions only)
    -- -----------------------------------------------------------------------
    SELECT MAX(attempted_at) INTO v_last_send_at
    FROM lcs.dispatch_attempt_log
    WHERE sovereign_id = v_sovereign_id
      AND channel = p_channel
      AND decision = 'ALLOWED';

    SELECT count(*) INTO v_count_7d
    FROM lcs.dispatch_attempt_log
    WHERE sovereign_id = v_sovereign_id
      AND channel = p_channel
      AND decision = 'ALLOWED'
      AND attempted_at >= NOW() - INTERVAL '7 days';

    SELECT count(*) INTO v_count_30d
    FROM lcs.dispatch_attempt_log
    WHERE sovereign_id = v_sovereign_id
      AND channel = p_channel
      AND decision = 'ALLOWED'
      AND attempted_at >= NOW() - INTERVAL '30 days';

    -- -----------------------------------------------------------------------
    -- 4. Evaluate: min_gap_hours
    -- -----------------------------------------------------------------------
    IF v_last_send_at IS NOT NULL THEN
        v_hours_since_last := EXTRACT(EPOCH FROM (NOW() - v_last_send_at)) / 3600.0;
        IF v_hours_since_last < v_policy.min_gap_hours THEN
            v_block_reason := 'MIN_GAP_HOURS';
        END IF;
    END IF;

    -- -----------------------------------------------------------------------
    -- 5. Evaluate: max_sends_7d
    -- -----------------------------------------------------------------------
    IF v_block_reason IS NULL AND v_count_7d >= v_policy.max_sends_7d THEN
        v_block_reason := 'MAX_SENDS_7D';
    END IF;

    -- -----------------------------------------------------------------------
    -- 6. Evaluate: max_sends_30d
    -- -----------------------------------------------------------------------
    IF v_block_reason IS NULL AND v_count_30d >= v_policy.max_sends_30d THEN
        v_block_reason := 'MAX_SENDS_30D';
    END IF;

    -- -----------------------------------------------------------------------
    -- 7. Evaluate: allowed_days (0=Sunday .. 6=Saturday, PostgreSQL DOW)
    -- -----------------------------------------------------------------------
    IF v_block_reason IS NULL THEN
        v_current_dow := EXTRACT(DOW FROM NOW())::INTEGER;
        IF NOT (v_current_dow = ANY(v_policy.allowed_days)) THEN
            v_block_reason := 'OUTSIDE_ALLOWED_DAYS';
        END IF;
    END IF;

    -- -----------------------------------------------------------------------
    -- 8. Evaluate: allowed_start_local / allowed_end_local
    --    Uses UTC for FIXED mode; ACCOUNT/COMPANY modes stub to UTC
    --    (timezone resolution deferred to Phase 4B)
    -- -----------------------------------------------------------------------
    IF v_block_reason IS NULL THEN
        v_current_time := NOW()::TIME;
        IF v_current_time < v_policy.allowed_start_local
           OR v_current_time > v_policy.allowed_end_local THEN
            v_block_reason := 'OUTSIDE_TIME_WINDOW';
        END IF;
    END IF;

    -- -----------------------------------------------------------------------
    -- 9. Build result
    -- -----------------------------------------------------------------------
    v_decision := CASE WHEN v_block_reason IS NULL THEN 'ALLOWED' ELSE 'BLOCKED' END;

    v_policy_json := jsonb_build_object(
        'lifecycle_stage', v_policy.lifecycle_stage,
        'channel', v_policy.channel,
        'min_gap_hours', v_policy.min_gap_hours,
        'max_sends_7d', v_policy.max_sends_7d,
        'max_sends_30d', v_policy.max_sends_30d,
        'allowed_days', to_jsonb(v_policy.allowed_days),
        'allowed_start_local', v_policy.allowed_start_local::text,
        'allowed_end_local', v_policy.allowed_end_local::text,
        'timezone_mode', v_policy.timezone_mode
    );

    v_metrics_json := jsonb_build_object(
        'last_send_at', v_last_send_at,
        'count_7d', v_count_7d,
        'count_30d', v_count_30d
    );

    -- -----------------------------------------------------------------------
    -- 10. Log decision to dispatch_attempt_log
    -- -----------------------------------------------------------------------
    INSERT INTO lcs.dispatch_attempt_log
        (mid, sovereign_id, channel, lifecycle_stage, decision, block_reason, policy_snapshot)
    VALUES (p_mid, v_sovereign_id, p_channel, v_lifecycle_stage, v_decision, v_block_reason, v_policy_json);

    -- -----------------------------------------------------------------------
    -- 11. If blocked, also log to lcs_errors for visibility
    -- -----------------------------------------------------------------------
    IF v_decision = 'BLOCKED' THEN
        INSERT INTO lcs.lcs_errors (error_stage, error_type, sovereign_id, mid, error_payload)
        VALUES ('cadence_check', 'conflict', v_sovereign_id, p_mid,
            jsonb_build_object(
                'channel', p_channel,
                'block_reason', v_block_reason,
                'policy', v_policy_json,
                'metrics', v_metrics_json
            ));
    END IF;

    RETURN jsonb_build_object(
        'allowed', (v_decision = 'ALLOWED'),
        'block_reason', v_block_reason,
        'policy', v_policy_json,
        'metrics', v_metrics_json
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 5. Seed default cadence policies
-- ============================================================================
-- Conservative defaults for email channel. LinkedIn deferred.

INSERT INTO lcs.cadence_policy_registry
    (lifecycle_stage, channel, min_gap_hours, max_sends_7d, max_sends_30d,
     allowed_days, allowed_start_local, allowed_end_local, timezone_mode)
VALUES
    ('QUALIFIED', 'EMAIL', 72, 2, 5, ARRAY[1,2,3,4,5], '08:00', '17:00', 'FIXED'),
    ('ENGAGED',   'EMAIL', 48, 3, 8, ARRAY[1,2,3,4,5], '08:00', '18:00', 'FIXED'),
    ('CONVERTED', 'EMAIL', 24, 5, 12, ARRAY[1,2,3,4,5], '08:00', '18:00', 'FIXED')
ON CONFLICT (lifecycle_stage, channel) DO NOTHING;

-- ============================================================================
-- 6. PERMISSIONS — lcs_worker function-mediated access
-- ============================================================================

GRANT EXECUTE ON FUNCTION lcs.fn_cadence_check(UUID, TEXT) TO lcs_worker;

-- No direct table writes for worker
REVOKE ALL ON lcs.cadence_policy_registry FROM lcs_worker;
REVOKE ALL ON lcs.dispatch_attempt_log FROM lcs_worker;
REVOKE ALL ON lcs.cadence_policy_registry FROM lcs_transport;
REVOKE ALL ON lcs.dispatch_attempt_log FROM lcs_transport;

-- ============================================================================
-- 7. COMMENTS
-- ============================================================================

COMMENT ON TABLE lcs.cadence_policy_registry IS
    'REGISTRY — Cadence policies per lifecycle_stage + channel. Frequency caps (min_gap_hours, max_sends_7d/30d) and time windows (allowed_days, start/end local). PK: (lifecycle_stage, channel).';
COMMENT ON TABLE lcs.dispatch_attempt_log IS
    'SUPPORTING — Append-only log of cadence decisions (ALLOWED/BLOCKED) with policy snapshots and metrics. No UPDATE, no DELETE.';
COMMENT ON FUNCTION lcs.fn_cadence_check(UUID, TEXT) IS
    'Deterministic cadence evaluator. Resolves sovereign lifecycle, fetches policy, computes send metrics, evaluates frequency caps + time windows. Logs decision to dispatch_attempt_log. Returns JSON {allowed, block_reason, policy, metrics}. No RAISE-after-DML.';

COMMIT;
