-- ─────────────────────────────────────────────
-- 📁 CTB Classification Metadata
-- ─────────────────────────────────────────────
-- CTB Branch: data/infra
-- Barton ID: 05.01.01
-- Unique ID: CTB-CDF89EF3
-- Blueprint Hash:
-- Last Updated: 2025-10-23
-- Enforcement: ORBT
-- ─────────────────────────────────────────────

-- Migration: Create shq_error_log table for centralized error tracking
-- Version: 1.3.2
-- Date: 2025-10-20
-- Audit Reference: docs/audit_report.md (Fix 1 - Critical Blocker)
--
-- This table implements the Master Error Table from Section 12 of the
-- Outreach Doctrine A→Z documentation. All errors from HEIR agents and
-- processes must be logged here for Firebase/Lovable visualization.
--
-- Related Documentation:
-- - /docs/outreach-doctrine-a2z.md (Section 12 & 13)
-- - /docs/error_handling.md (Complete error management guide)
-- - /scripts/sync-errors-to-firebase.ts (Sync script)
-- - /firebase/error_dashboard_spec.json (Dashboard configuration)

-- Drop table if exists (for re-running migration)
DROP TABLE IF EXISTS shq_error_log CASCADE;

-- Create main error log table
CREATE TABLE shq_error_log (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Unique error identifier (UUID for global tracking)
    error_id TEXT UNIQUE NOT NULL DEFAULT gen_random_uuid()::TEXT,

    -- Timestamp fields
    timestamp TIMESTAMPTZ DEFAULT now() NOT NULL,
    last_touched TIMESTAMPTZ DEFAULT now() NOT NULL,

    -- Agent and process identification
    agent_name TEXT,
    process_id TEXT,
    unique_id TEXT, -- 6-part Barton Doctrine ID (e.g., 04.01.02.05.10000.001)

    -- Error details
    severity TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    message TEXT NOT NULL,
    stack_trace TEXT,

    -- Resolution tracking
    resolved BOOLEAN DEFAULT false NOT NULL,
    resolution_notes TEXT,

    -- Firebase sync tracking (for idempotency in sync-errors-to-firebase.ts)
    firebase_synced BOOLEAN DEFAULT FALSE NOT NULL
);

-- Performance indexes
CREATE INDEX idx_error_log_severity
    ON shq_error_log(severity);

CREATE INDEX idx_error_log_resolved
    ON shq_error_log(resolved);

CREATE INDEX idx_error_log_timestamp
    ON shq_error_log(timestamp DESC);

-- Partial index for efficient sync queries (only unsynced rows)
CREATE INDEX idx_error_log_firebase_synced
    ON shq_error_log(firebase_synced)
    WHERE firebase_synced IS FALSE;

CREATE INDEX idx_error_log_agent
    ON shq_error_log(agent_name);

CREATE INDEX idx_error_log_unique_id
    ON shq_error_log(unique_id);

-- Auto-update last_touched timestamp on row updates
CREATE OR REPLACE FUNCTION update_error_log_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_touched = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_error_log_timestamp
BEFORE UPDATE ON shq_error_log
FOR EACH ROW
EXECUTE FUNCTION update_error_log_timestamp();

-- Table and column comments for schema documentation
COMMENT ON TABLE shq_error_log IS 'Centralized error tracking for all agents and processes (Barton Doctrine v1.3.2)';
COMMENT ON COLUMN shq_error_log.error_id IS 'UUID for error tracking across systems (synced to Firebase)';
COMMENT ON COLUMN shq_error_log.unique_id IS '6-part Barton Doctrine ID (e.g., 04.01.02.05.10000.001)';
COMMENT ON COLUMN shq_error_log.process_id IS 'Human-readable process identifier (e.g., "Enrich Contacts from Apify")';
COMMENT ON COLUMN shq_error_log.severity IS 'Error severity level: info, warning, error, critical (maps to dashboard colors)';
COMMENT ON COLUMN shq_error_log.firebase_synced IS 'Flag for sync-errors-to-firebase.ts idempotency (prevents duplicate syncs)';
COMMENT ON COLUMN shq_error_log.last_touched IS 'Auto-updated timestamp (via trigger) for resolution tracking';

-- Verification query
SELECT
    'shq_error_log table created successfully' AS status,
    COUNT(*) AS index_count
FROM pg_indexes
WHERE tablename = 'shq_error_log';

-- Sample insert for testing (optional - comment out if not needed)
-- INSERT INTO shq_error_log (
--     agent_name,
--     process_id,
--     unique_id,
--     severity,
--     message
-- ) VALUES (
--     'Doctrine Maintenance Agent',
--     'Create Error Log Table',
--     '04.01.99.10.01000.001',
--     'info',
--     'shq_error_log table migration completed successfully'
-- );
