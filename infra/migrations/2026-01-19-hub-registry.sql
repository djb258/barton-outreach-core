-- =============================================================================
-- HUB REGISTRY - Foundation for Sovereign Completion
-- =============================================================================
--
-- PURPOSE:
--   Define required vs optional hubs for marketing eligibility computation.
--   This is the foundation truth for vw_sovereign_completion.
--
-- DOCTRINE:
--   - Required hubs MUST pass for a company to be "Complete"
--   - Optional hubs enhance but don't gate completion
--   - BIT is a GATE (computed metric), not a hub
--
-- =============================================================================

-- Create hub registry table
CREATE TABLE IF NOT EXISTS outreach.hub_registry (
    hub_id VARCHAR(50) PRIMARY KEY,
    hub_name VARCHAR(100) NOT NULL,
    doctrine_id VARCHAR(20) NOT NULL,
    classification VARCHAR(20) NOT NULL CHECK (classification IN ('required', 'optional')),
    gates_completion BOOLEAN NOT NULL DEFAULT FALSE,
    waterfall_order INTEGER NOT NULL,
    core_metric VARCHAR(50) NOT NULL,
    metric_healthy_threshold DECIMAL(5,2),
    metric_critical_threshold DECIMAL(5,2),
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE outreach.hub_registry IS 
'Sub-hub: SHARED | Hub registry defining required vs optional hubs for completion tracking. Read-only after initial seed.';

-- Seed required hubs
INSERT INTO outreach.hub_registry (
    hub_id, hub_name, doctrine_id, classification, gates_completion, 
    waterfall_order, core_metric, metric_healthy_threshold, metric_critical_threshold, description
) VALUES 
-- Required hubs (gate completion)
('company-target', 'Company Target', '04.04.01', 'required', TRUE, 1, 
 'BIT_SCORE', 0.70, 0.40, 
 'Internal anchor for outreach. Domain resolution, email pattern discovery.'),

('dol-filings', 'DOL Filings', '04.04.03', 'required', TRUE, 2, 
 'FILING_MATCH_RATE', 0.90, 0.70, 
 'EIN resolution, Form 5500 data, renewal calendar.'),

('people-intelligence', 'People Intelligence', '04.04.02', 'required', TRUE, 3, 
 'SLOT_FILL_RATE', 0.80, 0.50, 
 'Slot assignments, email generation, verification.'),

('talent-flow', 'Talent Flow', '04.04.06', 'required', TRUE, 4, 
 'MOVEMENT_DETECTION_RATE', 0.70, 0.40, 
 'Movement detection, churn tracking, vacancy signals.'),

-- Optional hubs (enhance but don't gate)
('blog-content', 'Blog Content', '04.04.05', 'optional', FALSE, 5, 
 'CONTENT_SIGNAL_RATE', 0.50, 0.20, 
 'News monitoring, content signals, BIT modulation.'),

('outreach-execution', 'Outreach Execution', '04.04.04', 'optional', FALSE, 6, 
 'ENGAGEMENT_RATE', 0.30, 0.10, 
 'Campaign execution, send log, engagement tracking.')
ON CONFLICT (hub_id) DO UPDATE SET
    hub_name = EXCLUDED.hub_name,
    classification = EXCLUDED.classification,
    gates_completion = EXCLUDED.gates_completion,
    waterfall_order = EXCLUDED.waterfall_order,
    updated_at = NOW();

-- Create BIT gate entry (not a hub, but a gate)
CREATE TABLE IF NOT EXISTS outreach.gate_registry (
    gate_id VARCHAR(50) PRIMARY KEY,
    gate_name VARCHAR(100) NOT NULL,
    gate_type VARCHAR(20) NOT NULL CHECK (gate_type IN ('metric', 'status', 'composite')),
    threshold_pass DECIMAL(10,2),
    threshold_fail DECIMAL(10,2),
    applies_to_tier INTEGER[], -- Which marketing tiers require this gate
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE outreach.gate_registry IS 
'Sub-hub: SHARED | Gate definitions for marketing tier eligibility. BIT is a gate, not a hub.';

INSERT INTO outreach.gate_registry (
    gate_id, gate_name, gate_type, threshold_pass, threshold_fail, applies_to_tier, description
) VALUES
('bit-warm', 'BIT Warm Gate', 'metric', 25, 0, ARRAY[1,2,3], 
 'BIT score >= 25 required for Tier 1+ marketing'),
('bit-hot', 'BIT Hot Gate', 'metric', 50, 25, ARRAY[2,3], 
 'BIT score >= 50 required for Tier 2+ marketing'),
('bit-burning', 'BIT Burning Gate', 'metric', 75, 50, ARRAY[3], 
 'BIT score >= 75 required for Tier 3 (aggressive) marketing'),
('all-required-pass', 'All Required Hubs Pass', 'composite', NULL, NULL, ARRAY[3], 
 'All required hubs must have status=PASS for Tier 3')
ON CONFLICT (gate_id) DO NOTHING;

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_hub_registry_classification 
ON outreach.hub_registry(classification);

CREATE INDEX IF NOT EXISTS idx_hub_registry_waterfall 
ON outreach.hub_registry(waterfall_order);

-- Add RLS (consistent with other outreach tables)
ALTER TABLE outreach.hub_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE outreach.gate_registry ENABLE ROW LEVEL SECURITY;

CREATE POLICY hub_registry_select ON outreach.hub_registry 
FOR SELECT TO public USING (true);

CREATE POLICY hub_registry_insert ON outreach.hub_registry 
FOR INSERT TO public WITH CHECK (true);

CREATE POLICY gate_registry_select ON outreach.gate_registry 
FOR SELECT TO public USING (true);

-- =============================================================================
-- HUB STATUS ENUM
-- =============================================================================

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'hub_status_enum') THEN
        CREATE TYPE outreach.hub_status_enum AS ENUM (
            'PASS',        -- Hub requirements met
            'IN_PROGRESS', -- Hub processing, not yet complete
            'FAIL',        -- Hub failed validation/processing
            'BLOCKED'      -- Blocked by upstream dependency
        );
    END IF;
END $$;

-- =============================================================================
-- COMPANY HUB STATUS TABLE
-- =============================================================================
-- Tracks hub status per company (populated by hub processors)

CREATE TABLE IF NOT EXISTS outreach.company_hub_status (
    company_unique_id UUID NOT NULL,
    hub_id VARCHAR(50) NOT NULL REFERENCES outreach.hub_registry(hub_id),
    status outreach.hub_status_enum NOT NULL DEFAULT 'IN_PROGRESS',
    status_reason TEXT,
    metric_value DECIMAL(10,4),
    last_processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (company_unique_id, hub_id)
);

COMMENT ON TABLE outreach.company_hub_status IS 
'Sub-hub: SHARED | Per-company hub status tracking. Updated by each hub processor.';

CREATE INDEX IF NOT EXISTS idx_company_hub_status_company 
ON outreach.company_hub_status(company_unique_id);

CREATE INDEX IF NOT EXISTS idx_company_hub_status_hub 
ON outreach.company_hub_status(hub_id);

CREATE INDEX IF NOT EXISTS idx_company_hub_status_status 
ON outreach.company_hub_status(status);

-- RLS
ALTER TABLE outreach.company_hub_status ENABLE ROW LEVEL SECURITY;

CREATE POLICY company_hub_status_select ON outreach.company_hub_status 
FOR SELECT TO public USING (true);

CREATE POLICY company_hub_status_insert ON outreach.company_hub_status 
FOR INSERT TO public WITH CHECK (true);

CREATE POLICY company_hub_status_update ON outreach.company_hub_status 
FOR UPDATE TO public USING (true) WITH CHECK (true);

-- =============================================================================
-- HUB STATUS LOG (Append-Only Audit)
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach.hub_status_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_unique_id UUID NOT NULL,
    hub_id VARCHAR(50) NOT NULL,
    old_status outreach.hub_status_enum,
    new_status outreach.hub_status_enum NOT NULL,
    status_reason TEXT,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    correlation_id UUID
);

COMMENT ON TABLE outreach.hub_status_log IS 
'Sub-hub: SHARED | Append-only audit log of hub status changes. Never delete.';

CREATE INDEX IF NOT EXISTS idx_hub_status_log_company 
ON outreach.hub_status_log(company_unique_id);

CREATE INDEX IF NOT EXISTS idx_hub_status_log_changed 
ON outreach.hub_status_log(changed_at);

-- RLS (read-only for auditors, insert for system)
ALTER TABLE outreach.hub_status_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY hub_status_log_select ON outreach.hub_status_log 
FOR SELECT TO public USING (true);

CREATE POLICY hub_status_log_insert ON outreach.hub_status_log 
FOR INSERT TO public WITH CHECK (true);

-- =============================================================================
-- TRIGGER: Auto-log status changes
-- =============================================================================

CREATE OR REPLACE FUNCTION outreach.fn_log_hub_status_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Only log if status actually changed
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO outreach.hub_status_log (
            company_unique_id, hub_id, old_status, new_status, status_reason
        ) VALUES (
            NEW.company_unique_id, NEW.hub_id, OLD.status, NEW.status, NEW.status_reason
        );
    END IF;
    
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_log_hub_status_change ON outreach.company_hub_status;
CREATE TRIGGER trg_log_hub_status_change
    BEFORE UPDATE ON outreach.company_hub_status
    FOR EACH ROW
    EXECUTE FUNCTION outreach.fn_log_hub_status_change();
