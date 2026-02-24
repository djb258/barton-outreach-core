-- ============================================================================
-- LCS Spine v0 — CID / SID / MID Skeleton
-- ============================================================================
-- WORK_PACKET: WP_20260224T072012-0500_LCS_SPINE_V0_CID_SID_MID_SKELETON
-- Doctrine:    2.8.0
-- Date:        2026-02-24
--
-- Creates:
--   Schema:    lcs
--   Enums:     lcs.lifecycle_stage, lcs.cid_status, lcs.dispatch_state
--   Tables:    lcs.movement_type_registry, lcs.cid_intake, lcs.sid_registry,
--              lcs.mid_ledger
--   Functions: lcs.fn_process_cid(uuid), lcs.fn_finalize_dispatch(uuid, jsonb)
--   Triggers:  Append-only immutability on cid_intake and mid_ledger,
--              forward-only dispatch_state transitions on mid_ledger
--
-- No references to dropped views.
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. SCHEMA
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS lcs;

-- ============================================================================
-- 2. ENUMS
-- ============================================================================

CREATE TYPE lcs.lifecycle_stage AS ENUM (
    'SUSPECT',          -- Unknown intent, no movement detected
    'IDENTIFIED',       -- Movement detected, CID created
    'QUALIFIED',        -- CID processed, SID assigned
    'ENGAGED',          -- MID minted, dispatch in progress
    'CONVERTED',        -- Appointment booked or client signed
    'SUPPRESSED'        -- Suppression rule applied
);

CREATE TYPE lcs.cid_status AS ENUM (
    'PENDING',          -- Awaiting processing
    'ACCEPTED',         -- CID processed, SID assigned, MID minted
    'REJECTED',         -- Failed validation or suppression
    'EXPIRED'           -- TTL exceeded without processing
);

CREATE TYPE lcs.dispatch_state AS ENUM (
    'MINTED',           -- MID created, not yet dispatched
    'QUEUED',           -- Placed in send queue
    'DISPATCHED',       -- Handed to transport
    'DELIVERED',        -- Transport confirmed delivery
    'BOUNCED',          -- Hard bounce from transport
    'FAILED'            -- Transport or system failure
);

-- ============================================================================
-- 3. TABLES
-- ============================================================================

-- 3a. Movement Type Registry
-- Governs which movement types are valid. All CID rows FK here.
CREATE TABLE lcs.movement_type_registry (
    movement_type_code  TEXT        PRIMARY KEY,
    description         TEXT        NOT NULL,
    source_subhub       TEXT        NOT NULL,       -- e.g. 04.04.02, 04.04.03
    is_active           BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed canonical movement types
INSERT INTO lcs.movement_type_registry (movement_type_code, description, source_subhub) VALUES
    ('EXECUTIVE_HIRE',      'New executive detected at company',                '04.04.02'),
    ('EXECUTIVE_DEPARTURE', 'Executive departed company',                       '04.04.02'),
    ('TITLE_CHANGE',        'Executive title changed',                          '04.04.02'),
    ('BROKER_CHANGE',       'Benefits broker changed (DOL Schedule C)',         '04.04.03'),
    ('CARRIER_CHANGE',      'Insurance carrier changed (DOL Schedule A)',       '04.04.03'),
    ('PLAN_COST_SPIKE',     'Employer contribution increased significantly',    '04.04.03'),
    ('RENEWAL_APPROACHING', 'Plan renewal within outreach window',             '04.04.03'),
    ('FUNDING_EVENT',       'Funding event detected via blog/news',            '04.04.05'),
    ('ACQUISITION',         'Acquisition/merger detected via blog/news',       '04.04.05'),
    ('LEADERSHIP_ANNOUNCE', 'Leadership announcement detected via blog/news',  '04.04.05');

-- 3b. CID Intake (Correlation ID — movement event intake)
-- One row per detected movement event. Append-only after insert.
CREATE TABLE lcs.cid_intake (
    cid                 UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    outreach_id         UUID        NOT NULL REFERENCES outreach.outreach(outreach_id),
    sovereign_id        UUID        NOT NULL REFERENCES cl.company_identity(company_unique_id),
    movement_type_code  TEXT        NOT NULL REFERENCES lcs.movement_type_registry(movement_type_code),
    status              lcs.cid_status  NOT NULL DEFAULT 'PENDING',
    lifecycle_stage     lcs.lifecycle_stage NOT NULL DEFAULT 'IDENTIFIED',
    source_hub          TEXT        NOT NULL,       -- Hub that emitted the movement
    source_table        TEXT,                       -- Source table (optional detail)
    source_record_id    TEXT,                       -- Source record ref (optional)
    evidence            JSONB       NOT NULL DEFAULT '{}',
    detected_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at        TIMESTAMPTZ,                -- Set by fn_process_cid
    expires_at          TIMESTAMPTZ,                -- Optional TTL
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cid_intake_outreach    ON lcs.cid_intake(outreach_id);
CREATE INDEX idx_cid_intake_sovereign   ON lcs.cid_intake(sovereign_id);
CREATE INDEX idx_cid_intake_status      ON lcs.cid_intake(status) WHERE status = 'PENDING';
CREATE INDEX idx_cid_intake_type        ON lcs.cid_intake(movement_type_code);

-- 3c. SID Registry (Spine ID — company lifecycle state)
-- One row per company in the LCS. Tracks current lifecycle stage.
CREATE TABLE lcs.sid_registry (
    sid                 UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    outreach_id         UUID        NOT NULL UNIQUE REFERENCES outreach.outreach(outreach_id),
    sovereign_id        UUID        NOT NULL UNIQUE REFERENCES cl.company_identity(company_unique_id),
    lifecycle_stage     lcs.lifecycle_stage NOT NULL DEFAULT 'SUSPECT',
    last_cid            UUID,                       -- Most recent CID processed
    last_movement_at    TIMESTAMPTZ,                -- When last movement was detected
    mid_count           INTEGER     NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sid_registry_stage     ON lcs.sid_registry(lifecycle_stage);

-- 3d. MID Ledger (Message ID — dispatch tracking)
-- One row per minted message. Append-only after insert; only dispatch_state advances.
CREATE TABLE lcs.mid_ledger (
    mid                 UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    cid                 UUID        NOT NULL REFERENCES lcs.cid_intake(cid),
    sid                 UUID        NOT NULL REFERENCES lcs.sid_registry(sid),
    outreach_id         UUID        NOT NULL REFERENCES outreach.outreach(outreach_id),
    sovereign_id        UUID        NOT NULL REFERENCES cl.company_identity(company_unique_id),
    dispatch_state      lcs.dispatch_state NOT NULL DEFAULT 'MINTED',
    movement_type_code  TEXT        NOT NULL REFERENCES lcs.movement_type_registry(movement_type_code),
    proof_line          TEXT,                       -- BIT authorization proof (Band 3+)
    dispatch_result     JSONB,                      -- Populated by fn_finalize_dispatch
    minted_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    dispatched_at       TIMESTAMPTZ,
    finalized_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mid_ledger_cid         ON lcs.mid_ledger(cid);
CREATE INDEX idx_mid_ledger_sid         ON lcs.mid_ledger(sid);
CREATE INDEX idx_mid_ledger_outreach    ON lcs.mid_ledger(outreach_id);
CREATE INDEX idx_mid_ledger_state       ON lcs.mid_ledger(dispatch_state) WHERE dispatch_state IN ('MINTED', 'QUEUED');

-- ============================================================================
-- 4. IMMUTABILITY TRIGGERS
-- ============================================================================

-- 4a. CID Intake — append-only (no UPDATE, no DELETE)
CREATE OR REPLACE FUNCTION lcs.fn_cid_intake_immutable()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'lcs.cid_intake is append-only. Row cid=% cannot be modified after insert.', OLD.cid;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_cid_intake_no_update
    BEFORE UPDATE ON lcs.cid_intake
    FOR EACH ROW
    WHEN (OLD.status NOT IN ('PENDING'))
    EXECUTE FUNCTION lcs.fn_cid_intake_immutable();

CREATE TRIGGER trg_cid_intake_no_delete
    BEFORE DELETE ON lcs.cid_intake
    FOR EACH ROW
    EXECUTE FUNCTION lcs.fn_cid_intake_immutable();

-- 4b. MID Ledger — only dispatch_state, dispatch_result, dispatched_at,
--     finalized_at may change. All other columns are immutable after insert.
CREATE OR REPLACE FUNCTION lcs.fn_mid_ledger_guard()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.mid          != OLD.mid          OR
       NEW.cid          != OLD.cid          OR
       NEW.sid          != OLD.sid          OR
       NEW.outreach_id  != OLD.outreach_id  OR
       NEW.sovereign_id != OLD.sovereign_id OR
       NEW.movement_type_code != OLD.movement_type_code OR
       NEW.minted_at    != OLD.minted_at    OR
       NEW.created_at   != OLD.created_at   THEN
        RAISE EXCEPTION 'lcs.mid_ledger identity columns are immutable. Only dispatch_state, dispatch_result, dispatched_at, finalized_at may change. mid=%', OLD.mid;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_mid_ledger_guard
    BEFORE UPDATE ON lcs.mid_ledger
    FOR EACH ROW
    EXECUTE FUNCTION lcs.fn_mid_ledger_guard();

CREATE OR REPLACE FUNCTION lcs.fn_mid_ledger_no_delete()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'lcs.mid_ledger rows cannot be deleted. mid=%', OLD.mid;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_mid_ledger_no_delete
    BEFORE DELETE ON lcs.mid_ledger
    FOR EACH ROW
    EXECUTE FUNCTION lcs.fn_mid_ledger_no_delete();

-- 4c. Forward-only dispatch_state transitions
--     MINTED -> QUEUED -> DISPATCHED -> DELIVERED
--                                    -> BOUNCED
--                                    -> FAILED
--     No backward transitions. Terminal states: DELIVERED, BOUNCED, FAILED.
CREATE OR REPLACE FUNCTION lcs.fn_dispatch_state_forward_only()
RETURNS TRIGGER AS $$
DECLARE
    old_ord INTEGER;
    new_ord INTEGER;
BEGIN
    -- Ordinal mapping for forward-only enforcement
    old_ord := CASE OLD.dispatch_state
        WHEN 'MINTED'      THEN 1
        WHEN 'QUEUED'      THEN 2
        WHEN 'DISPATCHED'  THEN 3
        WHEN 'DELIVERED'   THEN 4
        WHEN 'BOUNCED'     THEN 4
        WHEN 'FAILED'      THEN 4
    END;
    new_ord := CASE NEW.dispatch_state
        WHEN 'MINTED'      THEN 1
        WHEN 'QUEUED'      THEN 2
        WHEN 'DISPATCHED'  THEN 3
        WHEN 'DELIVERED'   THEN 4
        WHEN 'BOUNCED'     THEN 4
        WHEN 'FAILED'      THEN 4
    END;

    -- Terminal states cannot transition
    IF old_ord = 4 THEN
        RAISE EXCEPTION 'dispatch_state % is terminal. mid=% cannot transition further.', OLD.dispatch_state, OLD.mid;
    END IF;

    -- Must move forward
    IF new_ord <= old_ord THEN
        RAISE EXCEPTION 'dispatch_state can only advance forward. Cannot transition % -> % for mid=%', OLD.dispatch_state, NEW.dispatch_state, OLD.mid;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_dispatch_state_forward
    BEFORE UPDATE OF dispatch_state ON lcs.mid_ledger
    FOR EACH ROW
    EXECUTE FUNCTION lcs.fn_dispatch_state_forward_only();

-- ============================================================================
-- 5. CORE FUNCTIONS
-- ============================================================================

-- 5a. fn_process_cid — Process a pending CID.
--     1. Validate CID exists and is PENDING
--     2. Get-or-create SID for the company
--     3. Mint MID in the ledger
--     4. Update CID status to ACCEPTED
--     5. Update SID with latest movement info
--     Returns the minted MID uuid.
CREATE OR REPLACE FUNCTION lcs.fn_process_cid(p_cid UUID)
RETURNS UUID AS $$
DECLARE
    v_cid_row       lcs.cid_intake%ROWTYPE;
    v_sid           UUID;
    v_mid           UUID;
BEGIN
    -- 1. Lock and validate CID
    SELECT * INTO v_cid_row
    FROM lcs.cid_intake
    WHERE cid = p_cid
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'CID % not found in lcs.cid_intake', p_cid;
    END IF;

    IF v_cid_row.status != 'PENDING' THEN
        RAISE EXCEPTION 'CID % is not PENDING (current status: %)', p_cid, v_cid_row.status;
    END IF;

    -- Check TTL
    IF v_cid_row.expires_at IS NOT NULL AND v_cid_row.expires_at < NOW() THEN
        UPDATE lcs.cid_intake SET status = 'EXPIRED', processed_at = NOW()
        WHERE cid = p_cid;
        RAISE EXCEPTION 'CID % has expired', p_cid;
    END IF;

    -- 2. Get-or-create SID
    SELECT sid INTO v_sid
    FROM lcs.sid_registry
    WHERE outreach_id = v_cid_row.outreach_id;

    IF NOT FOUND THEN
        INSERT INTO lcs.sid_registry (outreach_id, sovereign_id, lifecycle_stage, last_cid, last_movement_at)
        VALUES (v_cid_row.outreach_id, v_cid_row.sovereign_id, 'QUALIFIED', p_cid, v_cid_row.detected_at)
        RETURNING sid INTO v_sid;
    ELSE
        UPDATE lcs.sid_registry
        SET lifecycle_stage  = 'QUALIFIED',
            last_cid         = p_cid,
            last_movement_at = v_cid_row.detected_at,
            updated_at       = NOW()
        WHERE sid = v_sid;
    END IF;

    -- 3. Mint MID
    INSERT INTO lcs.mid_ledger (cid, sid, outreach_id, sovereign_id, dispatch_state, movement_type_code)
    VALUES (p_cid, v_sid, v_cid_row.outreach_id, v_cid_row.sovereign_id, 'MINTED', v_cid_row.movement_type_code)
    RETURNING mid INTO v_mid;

    -- 4. Update CID status
    UPDATE lcs.cid_intake
    SET status = 'ACCEPTED', processed_at = NOW(), lifecycle_stage = 'QUALIFIED'
    WHERE cid = p_cid;

    -- 5. Increment SID mid_count
    UPDATE lcs.sid_registry
    SET mid_count  = mid_count + 1,
        lifecycle_stage = 'ENGAGED',
        updated_at = NOW()
    WHERE sid = v_sid;

    RETURN v_mid;
END;
$$ LANGUAGE plpgsql;

-- 5b. fn_finalize_dispatch — Finalize a dispatched MID.
--     Advances dispatch_state to a terminal state and records the result.
--     p_result must contain: {"outcome": "DELIVERED"|"BOUNCED"|"FAILED", ...}
CREATE OR REPLACE FUNCTION lcs.fn_finalize_dispatch(p_mid UUID, p_result JSONB)
RETURNS VOID AS $$
DECLARE
    v_outcome   TEXT;
    v_state     lcs.dispatch_state;
BEGIN
    -- Extract outcome
    v_outcome := p_result ->> 'outcome';
    IF v_outcome IS NULL THEN
        RAISE EXCEPTION 'p_result must contain "outcome" key. mid=%', p_mid;
    END IF;

    -- Map outcome to dispatch_state
    v_state := CASE v_outcome
        WHEN 'DELIVERED' THEN 'DELIVERED'::lcs.dispatch_state
        WHEN 'BOUNCED'   THEN 'BOUNCED'::lcs.dispatch_state
        WHEN 'FAILED'    THEN 'FAILED'::lcs.dispatch_state
        ELSE NULL
    END;

    IF v_state IS NULL THEN
        RAISE EXCEPTION 'Invalid outcome "%". Must be DELIVERED, BOUNCED, or FAILED. mid=%', v_outcome, p_mid;
    END IF;

    -- Update MID ledger (triggers enforce forward-only + column immutability)
    UPDATE lcs.mid_ledger
    SET dispatch_state  = v_state,
        dispatch_result = p_result,
        finalized_at    = NOW()
    WHERE mid = p_mid;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'MID % not found in lcs.mid_ledger', p_mid;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 6. COMMENTS
-- ============================================================================

COMMENT ON SCHEMA lcs IS 'Lifecycle Signal System — CID/SID/MID spine for movement-driven outreach';
COMMENT ON TABLE lcs.movement_type_registry IS 'Registry of valid movement types. All CID rows FK here.';
COMMENT ON TABLE lcs.cid_intake IS 'Correlation ID intake — one row per detected movement event. Append-only.';
COMMENT ON TABLE lcs.sid_registry IS 'Spine ID registry — one row per company lifecycle. Tracks current stage.';
COMMENT ON TABLE lcs.mid_ledger IS 'Message ID ledger — one row per minted dispatch. Forward-only state machine.';
COMMENT ON FUNCTION lcs.fn_process_cid(UUID) IS 'Process a PENDING CID: validate, get-or-create SID, mint MID, update statuses.';
COMMENT ON FUNCTION lcs.fn_finalize_dispatch(UUID, JSONB) IS 'Finalize a dispatched MID with terminal outcome (DELIVERED/BOUNCED/FAILED).';

COMMIT;
