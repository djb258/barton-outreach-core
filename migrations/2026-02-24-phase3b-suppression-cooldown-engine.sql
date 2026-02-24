-- ============================================================================
-- Phase 3B — Suppression + Cooldown Engine (Foundational Layer)
-- ============================================================================
-- WORK_PACKET: WP_20260224T0900_PHASE3B_SUPPRESSION_COOLDOWN_ENGINE_FOUNDATIONAL_LAYER
-- Doctrine:    2.8.0
-- Date:        2026-02-24
--
-- Creates:
--   Table:    lcs.suppression_registry (CANONICAL, 1 row per sovereign)
--   Trigger:  trg_suppression_registry_no_delete
--
-- Replaces:
--   Function: lcs.fn_mid_suppression_check(uuid) — real implementation
--
-- fn_mark_mid_ready (Phase 3A) already calls fn_mid_suppression_check
-- and handles FALSE by logging error + returning cleanly. No changes needed
-- to fn_mark_mid_ready — the interface is unchanged, only the implementation.
--
-- Suppression rules:
--   global_suppressed = TRUE → FALSE (blocked)
--   cooldown_until > NOW()   → FALSE (blocked)
--   Otherwise                → TRUE  (allowed)
--   No registry row          → TRUE  (not suppressed)
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. CTB Registration
-- ============================================================================

INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, is_frozen, registered_by, notes)
VALUES ('lcs', 'suppression_registry', 'CANONICAL', FALSE, 'phase3b_suppression_engine',
    'Sovereign-scoped suppression and cooldown state. One row per sovereign_id.')
ON CONFLICT (table_schema, table_name) DO NOTHING;

-- ============================================================================
-- 2. lcs.suppression_registry — Sovereign suppression state
-- ============================================================================
-- One row per sovereign. UPDATE allowed (governance surface). No DELETE.
-- Checked by fn_mid_suppression_check during READY gate.
-- ============================================================================

CREATE TABLE lcs.suppression_registry (
    sovereign_id        UUID        PRIMARY KEY REFERENCES cl.company_identity(company_unique_id),
    global_suppressed   BOOLEAN     NOT NULL DEFAULT FALSE,
    suppression_reason  TEXT,
    suppressed_at       TIMESTAMPTZ,
    cooldown_until      TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- NOTE: Partial index predicate cannot reference NOW() (volatile). Index covers all
-- rows; the query in fn_mid_suppression_check filters in-function, which is correct.
CREATE INDEX idx_suppression_registry_active
    ON lcs.suppression_registry(sovereign_id)
    WHERE global_suppressed = TRUE;

-- No DELETE
CREATE OR REPLACE FUNCTION lcs.fn_suppression_registry_no_delete()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'lcs.suppression_registry rows cannot be deleted. sovereign_id=%', OLD.sovereign_id;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_suppression_registry_no_delete
    BEFORE DELETE ON lcs.suppression_registry
    FOR EACH ROW
    EXECUTE FUNCTION lcs.fn_suppression_registry_no_delete();

-- ============================================================================
-- 3. Replace fn_mid_suppression_check stub with real implementation
-- ============================================================================
-- Resolves sovereign_id from mid_ledger, checks suppression_registry.
-- Returns FALSE if suppressed or in cooldown. TRUE otherwise.
-- No RAISE. No side effects.
-- ============================================================================

CREATE OR REPLACE FUNCTION lcs.fn_mid_suppression_check(p_mid UUID)
RETURNS BOOLEAN AS $$
DECLARE
    v_sovereign_id      UUID;
    v_global_suppressed BOOLEAN;
    v_cooldown_until    TIMESTAMPTZ;
BEGIN
    -- 1. Resolve sovereign_id from mid_ledger
    SELECT sovereign_id INTO v_sovereign_id
    FROM lcs.mid_ledger
    WHERE mid = p_mid;

    IF v_sovereign_id IS NULL THEN
        -- MID not found — cannot determine suppression. Return FALSE (safe default).
        RETURN FALSE;
    END IF;

    -- 2. Lookup suppression_registry
    SELECT global_suppressed, cooldown_until
    INTO v_global_suppressed, v_cooldown_until
    FROM lcs.suppression_registry
    WHERE sovereign_id = v_sovereign_id;

    IF NOT FOUND THEN
        -- No suppression row = not suppressed
        RETURN TRUE;
    END IF;

    -- 3. Check global suppression
    IF v_global_suppressed THEN
        RETURN FALSE;
    END IF;

    -- 4. Check cooldown window
    IF v_cooldown_until IS NOT NULL AND v_cooldown_until > NOW() THEN
        RETURN FALSE;
    END IF;

    -- 5. Not suppressed, cooldown expired or not set
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 4. COMMENTS
-- ============================================================================

COMMENT ON TABLE lcs.suppression_registry IS
    'CANONICAL — Sovereign-scoped suppression and cooldown state. One row per sovereign_id. Checked by fn_mid_suppression_check during READY gate.';
COMMENT ON FUNCTION lcs.fn_mid_suppression_check(UUID) IS
    'Phase 3B: Real suppression check. Resolves sovereign from mid_ledger, checks global_suppressed and cooldown_until. Returns FALSE if blocked, TRUE if clear. No RAISE.';
COMMENT ON FUNCTION lcs.fn_suppression_registry_no_delete() IS
    'Blocks DELETE on suppression_registry. Governance updates via UPDATE only.';

COMMIT;
