-- Talent Flow Database Tables
-- Barton Doctrine ID: 04.04.02.04.60000.###

-- ==============================================================
-- Table: talent_flow_snapshots
-- Purpose: Store monthly snapshots of person state (for hash comparison)
-- ==============================================================
CREATE TABLE IF NOT EXISTS marketing.talent_flow_snapshots (
    snapshot_id BIGSERIAL PRIMARY KEY,
    person_unique_id TEXT NOT NULL,
    enrichment_hash TEXT NOT NULL,
    snapshot_data JSONB NOT NULL,
    snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (person_unique_id, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_tf_snapshots_person ON marketing.talent_flow_snapshots(person_unique_id);
CREATE INDEX IF NOT EXISTS idx_tf_snapshots_date ON marketing.talent_flow_snapshots(snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_tf_snapshots_hash ON marketing.talent_flow_snapshots(enrichment_hash);

COMMENT ON TABLE marketing.talent_flow_snapshots IS 'Monthly snapshots of person state for movement detection';
COMMENT ON COLUMN marketing.talent_flow_snapshots.enrichment_hash IS 'MD5 hash of key fields for change detection';
COMMENT ON COLUMN marketing.talent_flow_snapshots.snapshot_data IS 'Full person record at time of snapshot';

-- ==============================================================
-- Table: talent_flow_movements
-- Purpose: Store detected movements (hire/exit/promotion/transfer)
-- ==============================================================
CREATE TABLE IF NOT EXISTS marketing.talent_flow_movements (
    movement_id BIGSERIAL PRIMARY KEY,
    person_unique_id TEXT NOT NULL,
    movement_type TEXT NOT NULL CHECK (movement_type IN ('hire', 'exit', 'promotion', 'transfer')),
    confidence NUMERIC(5,3) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    old_state JSONB,
    new_state JSONB NOT NULL,
    data_source TEXT,
    metadata JSONB,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    FOREIGN KEY (person_unique_id) REFERENCES marketing.people_master(unique_id)
);

CREATE INDEX IF NOT EXISTS idx_tf_movements_person ON marketing.talent_flow_movements(person_unique_id);
CREATE INDEX IF NOT EXISTS idx_tf_movements_type ON marketing.talent_flow_movements(movement_type);
CREATE INDEX IF NOT EXISTS idx_tf_movements_detected ON marketing.talent_flow_movements(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_tf_movements_confidence ON marketing.talent_flow_movements(confidence DESC);

COMMENT ON TABLE marketing.talent_flow_movements IS 'Detected talent movements (hires, exits, promotions, transfers)';
COMMENT ON COLUMN marketing.talent_flow_movements.confidence IS 'Confidence score (0.0 - 1.0) based on data quality';
COMMENT ON COLUMN marketing.talent_flow_movements.metadata IS 'Movement-specific data (e.g., promotion details, new company info)';

-- ==============================================================
-- Table: bit_signal (if not already exists)
-- Purpose: Store BIT signals generated from movements
-- ==============================================================
CREATE TABLE IF NOT EXISTS marketing.bit_signal (
    signal_id BIGSERIAL PRIMARY KEY,
    person_unique_id TEXT NOT NULL,
    company_unique_id TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    signal_weight INTEGER NOT NULL,
    source_id BIGINT,
    source_type TEXT,
    metadata JSONB,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    FOREIGN KEY (person_unique_id) REFERENCES marketing.people_master(unique_id),
    FOREIGN KEY (company_unique_id) REFERENCES marketing.company_master(company_unique_id)
);

CREATE INDEX IF NOT EXISTS idx_bit_signal_person ON marketing.bit_signal(person_unique_id);
CREATE INDEX IF NOT EXISTS idx_bit_signal_company ON marketing.bit_signal(company_unique_id);
CREATE INDEX IF NOT EXISTS idx_bit_signal_type ON marketing.bit_signal(signal_type);
CREATE INDEX IF NOT EXISTS idx_bit_signal_detected ON marketing.bit_signal(detected_at DESC);

COMMENT ON TABLE marketing.bit_signal IS 'Buyer Intent Tracking signals from various sources';
COMMENT ON COLUMN marketing.bit_signal.signal_weight IS 'Numeric weight for BIT scoring (higher = stronger signal)';
COMMENT ON COLUMN marketing.bit_signal.source_id IS 'ID of source record (e.g., movement_id, event_id)';
COMMENT ON COLUMN marketing.bit_signal.source_type IS 'Type of source (e.g., talent_flow_movement, email_open)';

-- ==============================================================
-- Table: shq.audit_log (if not already exists in shq schema)
-- Purpose: Audit trail for all agent operations
-- ==============================================================
CREATE SCHEMA IF NOT EXISTS shq;

CREATE TABLE IF NOT EXISTS shq.audit_log (
    audit_id BIGSERIAL PRIMARY KEY,
    worker_id TEXT NOT NULL,
    process_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_data JSONB,
    severity TEXT NOT NULL DEFAULT 'INFO' CHECK (severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_worker ON shq.audit_log(worker_id);
CREATE INDEX IF NOT EXISTS idx_audit_process ON shq.audit_log(process_id);
CREATE INDEX IF NOT EXISTS idx_audit_event_type ON shq.audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_created ON shq.audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_severity ON shq.audit_log(severity);

COMMENT ON TABLE shq.audit_log IS 'System-wide audit trail for agent operations';

-- ==============================================================
-- Table: garage.contradictions (if not already exists)
-- Purpose: Store contradictions detected during movement analysis
-- ==============================================================
CREATE SCHEMA IF NOT EXISTS garage;

CREATE TABLE IF NOT EXISTS garage.contradictions (
    contradiction_id BIGSERIAL PRIMARY KEY,
    person_unique_id TEXT NOT NULL,
    contradiction_type TEXT NOT NULL,
    description TEXT,
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high')),
    old_state JSONB,
    new_state JSONB,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_contradictions_person ON garage.contradictions(person_unique_id);
CREATE INDEX IF NOT EXISTS idx_contradictions_type ON garage.contradictions(contradiction_type);
CREATE INDEX IF NOT EXISTS idx_contradictions_resolved ON garage.contradictions(resolved);

COMMENT ON TABLE garage.contradictions IS 'Data contradictions flagged by Talent Flow Agent (Garage B)';

-- ==============================================================
-- Grant permissions
-- ==============================================================
-- GRANT SELECT, INSERT, UPDATE ON marketing.talent_flow_snapshots TO marketing_app_user;
-- GRANT SELECT, INSERT, UPDATE ON marketing.talent_flow_movements TO marketing_app_user;
-- GRANT SELECT, INSERT ON marketing.bit_signal TO marketing_app_user;
-- GRANT INSERT ON shq.audit_log TO marketing_app_user;
-- GRANT INSERT ON garage.contradictions TO marketing_app_user;
