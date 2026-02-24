-- ============================================================================
-- LCS CTB Registry Fix
-- ============================================================================
-- WORK_PACKET: WP_20260224_LCS_SPINE_V1_REGISTRY_FIX
-- Doctrine:    2.8.0
-- Date:        2026-02-24
--
-- Ensures all 6 LCS tables are registered in ctb.table_registry with
-- correct leaf types. Idempotent via INSERT ... ON CONFLICT DO UPDATE.
--
-- No schema changes. No enforcement changes. No function changes.
-- ============================================================================

BEGIN;

INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, is_frozen, registered_by, notes)
VALUES
    ('lcs', 'cid_intake',              'STAGING',   FALSE, 'lcs_v1_registry_fix', 'LCS INTAKE — movement event intake, append-only'),
    ('lcs', 'lcs_canonical',           'CANONICAL', FALSE, 'lcs_v1_registry_fix', 'LCS CANONICAL — single authoritative row per company'),
    ('lcs', 'lcs_errors',              'ERROR',     FALSE, 'lcs_v1_registry_fix', 'LCS ERROR — cantonal error capture for function failures'),
    ('lcs', 'sid_registry',            'SUPPORTING',FALSE, 'lcs_v1_registry_fix', 'LCS LEDGER — company lifecycle state, one row per company'),
    ('lcs', 'mid_ledger',              'SUPPORTING',FALSE, 'lcs_v1_registry_fix', 'LCS LEDGER — dispatch tracking, forward-only state machine'),
    ('lcs', 'movement_type_registry',  'REGISTRY',  FALSE, 'lcs_v1_registry_fix', 'LCS REGISTRY — valid movement type lookup')
ON CONFLICT (table_schema, table_name) DO UPDATE
SET leaf_type      = EXCLUDED.leaf_type,
    registered_by  = EXCLUDED.registered_by,
    notes          = EXCLUDED.notes;

COMMIT;
