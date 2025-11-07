-- ═══════════════════════════════════════════════════════════════════════════
-- BIT (Buyer Intent Tool) Schema Definition
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Document: BIT-Doctrine.md (doctrine/ple/BIT-Doctrine.md)
-- Barton ID Prefix: 01.04.03.04.10000
-- Version: 1.0.0
-- Last Updated: 2025-11-07
-- Status: Production Ready
--
-- Purpose:
--   Define the database schema for the Buyer Intent Tool (BIT), the axle of
--   the SVG-PLE marketing core. BIT converts discrete business events into
--   quantified intent scores that drive lead prioritization and outreach.
--
-- Architecture:
--   - HUB: marketing.company_master, people_master, company_slot
--   - SPOKES: Talent Flow, Renewal, Compliance
--   - AXLE (BIT): bit.rule_reference, bit.events, bit.scores
--   - WHEEL: Outreach automation (Hot/Warm/Cold cycles)
--
-- References:
--   - Section 4: Numbering Convention (BIT-Doctrine.md)
--   - Section 5: Schema Summary (BIT-Doctrine.md)
--   - Section 7: Doctrine Relationships (BIT-Doctrine.md)
--
-- ═══════════════════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────────────────
-- SCHEMA CREATION
-- ───────────────────────────────────────────────────────────────────────────

CREATE SCHEMA IF NOT EXISTS bit;

COMMENT ON SCHEMA bit IS 'Buyer Intent Tool (BIT) - Scoring engine for lead prioritization';

-- ───────────────────────────────────────────────────────────────────────────
-- SEQUENCES
-- ───────────────────────────────────────────────────────────────────────────
-- Reference: Section 4 (Numbering Convention)

-- Event ID sequence (001-999 range)
CREATE SEQUENCE IF NOT EXISTS bit.event_id_seq
  START WITH 1
  INCREMENT BY 1
  MINVALUE 1
  MAXVALUE 999
  CYCLE;

COMMENT ON SEQUENCE bit.event_id_seq IS 'Sequence for BIT event IDs (001-999)';

-- Snapshot ID sequence (801-899 range)
CREATE SEQUENCE IF NOT EXISTS bit.snapshot_id_seq
  START WITH 801
  INCREMENT BY 1
  MINVALUE 801
  MAXVALUE 899
  CYCLE;

COMMENT ON SEQUENCE bit.snapshot_id_seq IS 'Sequence for score snapshot IDs (801-899)';

-- ═══════════════════════════════════════════════════════════════════════════
-- TABLE 1: bit.rule_reference
-- ═══════════════════════════════════════════════════════════════════════════
-- Reference: Section 3 (Scoring Logic and Weight Table)
-- Purpose: Defines scoring rules with weights, decay parameters, and descriptions

CREATE TABLE IF NOT EXISTS bit.rule_reference (
  -- Primary Key (Barton ID: 01.04.03.04.10000.1##)
  rule_reference_id VARCHAR(50) PRIMARY KEY,

  -- Rule Identification
  rule_name VARCHAR(100) NOT NULL UNIQUE,
  event_type VARCHAR(100) NOT NULL,

  -- Scoring Parameters
  weight INTEGER NOT NULL CHECK (weight >= 0 AND weight <= 100),
  decay_days INTEGER NOT NULL CHECK (decay_days > 0),

  -- Description
  description TEXT,

  -- Status
  is_active BOOLEAN DEFAULT true NOT NULL,

  -- Audit Fields
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  created_by VARCHAR(100),
  updated_by VARCHAR(100),

  -- Constraints
  CONSTRAINT chk_rule_id_format CHECK (
    rule_reference_id ~ '^01\.04\.03\.04\.10000\.1\d{2}$'
  )
);

-- Indexes
CREATE INDEX idx_rule_reference_event_type ON bit.rule_reference(event_type);
CREATE INDEX idx_rule_reference_is_active ON bit.rule_reference(is_active);
CREATE INDEX idx_rule_reference_rule_name ON bit.rule_reference(rule_name);

-- Comments
COMMENT ON TABLE bit.rule_reference IS 'BIT scoring rules with weights and decay parameters (Section 3)';
COMMENT ON COLUMN bit.rule_reference.rule_reference_id IS 'Barton ID: 01.04.03.04.10000.1## (101-199 range)';
COMMENT ON COLUMN bit.rule_reference.rule_name IS 'Human-readable rule name (e.g., executive_movement)';
COMMENT ON COLUMN bit.rule_reference.event_type IS 'Event type identifier for matching events';
COMMENT ON COLUMN bit.rule_reference.weight IS 'Base score points (0-100)';
COMMENT ON COLUMN bit.rule_reference.decay_days IS 'Days until score reaches zero';
COMMENT ON COLUMN bit.rule_reference.is_active IS 'Enable/disable rule without deletion';

-- ═══════════════════════════════════════════════════════════════════════════
-- TABLE 2: bit.events
-- ═══════════════════════════════════════════════════════════════════════════
-- Reference: Section 6 (Example Trigger - Executive Movement)
-- Purpose: Logs individual buyer intent events for companies

CREATE TABLE IF NOT EXISTS bit.events (
  -- Primary Key (Barton ID: 01.04.03.04.10000.###)
  event_id VARCHAR(50) PRIMARY KEY DEFAULT CONCAT(
    '01.04.03.04.10000.',
    LPAD(NEXTVAL('bit.event_id_seq')::TEXT, 3, '0')
  ),

  -- Foreign Keys
  company_unique_id VARCHAR(50) NOT NULL,
  rule_reference_id VARCHAR(50) NOT NULL,

  -- Event Details
  event_type VARCHAR(100) NOT NULL,
  event_payload JSONB,

  -- Timing
  detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- Data Quality
  data_quality_score INTEGER NOT NULL CHECK (data_quality_score >= 50 AND data_quality_score <= 100),

  -- Audit
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

  -- Constraints
  CONSTRAINT chk_event_id_format CHECK (
    event_id ~ '^01\.04\.03\.04\.10000\.\d{3}$'
  ),
  CONSTRAINT fk_company FOREIGN KEY (company_unique_id)
    REFERENCES marketing.company_master(company_unique_id)
    ON DELETE CASCADE,
  CONSTRAINT fk_rule_reference FOREIGN KEY (rule_reference_id)
    REFERENCES bit.rule_reference(rule_reference_id)
    ON DELETE RESTRICT
);

-- Indexes
CREATE INDEX idx_events_company_id ON bit.events(company_unique_id);
CREATE INDEX idx_events_event_type ON bit.events(event_type);
CREATE INDEX idx_events_detected_at ON bit.events(detected_at DESC);
CREATE INDEX idx_events_rule_reference_id ON bit.events(rule_reference_id);
CREATE INDEX idx_events_quality_score ON bit.events(data_quality_score);
CREATE INDEX idx_events_payload ON bit.events USING GIN(event_payload);

-- Comments
COMMENT ON TABLE bit.events IS 'Individual buyer intent events for companies (Section 6)';
COMMENT ON COLUMN bit.events.event_id IS 'Barton ID: 01.04.03.04.10000.### (001-999 range), auto-generated';
COMMENT ON COLUMN bit.events.company_unique_id IS 'Links to marketing.company_master (04.04.02.04.30000.###)';
COMMENT ON COLUMN bit.events.rule_reference_id IS 'Links to bit.rule_reference (01.04.03.04.10000.1##)';
COMMENT ON COLUMN bit.events.event_type IS 'Type of event (must match rule_reference.event_type)';
COMMENT ON COLUMN bit.events.event_payload IS 'Additional event data (JSONB for flexibility)';
COMMENT ON COLUMN bit.events.detected_at IS 'Timestamp when event occurred (used for decay calculation)';
COMMENT ON COLUMN bit.events.data_quality_score IS 'Quality of data source (50-100, minimum 50 enforced)';

-- ═══════════════════════════════════════════════════════════════════════════
-- TABLE 3: bit.score_snapshots (Optional - for historical tracking)
-- ═══════════════════════════════════════════════════════════════════════════
-- Reference: Section 4 (Numbering Convention - 801-899 range)
-- Purpose: Historical snapshots of company scores for trend analysis

CREATE TABLE IF NOT EXISTS bit.score_snapshots (
  -- Primary Key (Barton ID: 01.04.03.04.10000.8##)
  snapshot_id VARCHAR(50) PRIMARY KEY DEFAULT CONCAT(
    '01.04.03.04.10000.',
    LPAD(NEXTVAL('bit.snapshot_id_seq')::TEXT, 3, '0')
  ),

  -- Foreign Key
  company_unique_id VARCHAR(50) NOT NULL,

  -- Snapshot Data
  snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,
  total_score NUMERIC(5,2) NOT NULL CHECK (total_score >= 0 AND total_score <= 100),
  score_category VARCHAR(10) NOT NULL CHECK (score_category IN ('Hot', 'Warm', 'Cold')),
  event_count INTEGER NOT NULL DEFAULT 0,
  score_breakdown JSONB,

  -- Audit
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

  -- Constraints
  CONSTRAINT chk_snapshot_id_format CHECK (
    snapshot_id ~ '^01\.04\.03\.04\.10000\.8\d{2}$'
  ),
  CONSTRAINT fk_snapshot_company FOREIGN KEY (company_unique_id)
    REFERENCES marketing.company_master(company_unique_id)
    ON DELETE CASCADE,
  CONSTRAINT uq_company_date UNIQUE (company_unique_id, snapshot_date)
);

-- Indexes
CREATE INDEX idx_snapshots_company_id ON bit.score_snapshots(company_unique_id);
CREATE INDEX idx_snapshots_date ON bit.score_snapshots(snapshot_date DESC);
CREATE INDEX idx_snapshots_category ON bit.score_snapshots(score_category);
CREATE INDEX idx_snapshots_score ON bit.score_snapshots(total_score DESC);

-- Comments
COMMENT ON TABLE bit.score_snapshots IS 'Historical snapshots of company intent scores';
COMMENT ON COLUMN bit.score_snapshots.snapshot_id IS 'Barton ID: 01.04.03.04.10000.8## (801-899 range)';
COMMENT ON COLUMN bit.score_snapshots.snapshot_date IS 'Date of snapshot (one per company per day)';
COMMENT ON COLUMN bit.score_snapshots.total_score IS 'Intent score at time of snapshot (0-100)';
COMMENT ON COLUMN bit.score_snapshots.score_category IS 'Hot (80-100), Warm (50-79), Cold (0-49)';
COMMENT ON COLUMN bit.score_snapshots.score_breakdown IS 'JSONB with per-event contributions';

-- ═══════════════════════════════════════════════════════════════════════════
-- VIEW: bit.scores
-- ═══════════════════════════════════════════════════════════════════════════
-- Reference: Section 3 (Scoring Logic and Weight Table)
-- Purpose: Real-time calculated intent scores for all companies

CREATE OR REPLACE VIEW bit.scores AS
SELECT
  cm.company_unique_id,
  cm.company_name,

  -- Total Score Calculation
  LEAST(
    COALESCE(
      SUM(
        rr.weight *
        -- Decay factor: (1 - days_since/decay_days)
        GREATEST(0, 1.0 - (EXTRACT(DAY FROM NOW() - e.detected_at)::NUMERIC / rr.decay_days)) *
        -- Quality modifier: (quality_score / 100)
        (e.data_quality_score::NUMERIC / 100.0)
      ),
      0
    ),
    100 -- Cap at 100
  ) AS total_score,

  -- Score Category
  CASE
    WHEN COALESCE(
      SUM(
        rr.weight *
        GREATEST(0, 1.0 - (EXTRACT(DAY FROM NOW() - e.detected_at)::NUMERIC / rr.decay_days)) *
        (e.data_quality_score::NUMERIC / 100.0)
      ),
      0
    ) >= 80 THEN 'Hot'
    WHEN COALESCE(
      SUM(
        rr.weight *
        GREATEST(0, 1.0 - (EXTRACT(DAY FROM NOW() - e.detected_at)::NUMERIC / rr.decay_days)) *
        (e.data_quality_score::NUMERIC / 100.0)
      ),
      0
    ) >= 50 THEN 'Warm'
    ELSE 'Cold'
  END AS score_category,

  -- Event Count (active events only)
  COUNT(e.event_id) AS event_count,

  -- Latest Event Date
  MAX(e.detected_at) AS latest_event_date,

  -- Score Breakdown (JSON with per-event contributions)
  COALESCE(
    JSONB_OBJECT_AGG(
      e.event_type,
      JSONB_BUILD_OBJECT(
        'event_id', e.event_id,
        'detected_at', e.detected_at,
        'base_weight', rr.weight,
        'decay_factor', GREATEST(0, 1.0 - (EXTRACT(DAY FROM NOW() - e.detected_at)::NUMERIC / rr.decay_days)),
        'quality_modifier', (e.data_quality_score::NUMERIC / 100.0),
        'final_contribution', ROUND(
          rr.weight *
          GREATEST(0, 1.0 - (EXTRACT(DAY FROM NOW() - e.detected_at)::NUMERIC / rr.decay_days)) *
          (e.data_quality_score::NUMERIC / 100.0),
          2
        )
      )
    ) FILTER (WHERE e.event_id IS NOT NULL),
    '{}'::JSONB
  ) AS score_breakdown

FROM marketing.company_master cm

LEFT JOIN bit.events e ON cm.company_unique_id = e.company_unique_id
  AND e.detected_at >= NOW() - INTERVAL '1 year' -- Only consider events from last year

LEFT JOIN bit.rule_reference rr ON e.rule_reference_id = rr.rule_reference_id
  AND rr.is_active = true -- Only active rules

GROUP BY cm.company_unique_id, cm.company_name

ORDER BY total_score DESC;

-- Comments
COMMENT ON VIEW bit.scores IS 'Real-time calculated intent scores for all companies (Section 3, Section 5)';

-- ═══════════════════════════════════════════════════════════════════════════
-- TRIGGERS
-- ═══════════════════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────────────────
-- Trigger 1: Auto-update updated_at on bit.rule_reference
-- ───────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION bit.update_rule_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_rule_reference_updated_at
  BEFORE UPDATE ON bit.rule_reference
  FOR EACH ROW
  EXECUTE FUNCTION bit.update_rule_updated_at();

COMMENT ON FUNCTION bit.update_rule_updated_at() IS 'Auto-update updated_at timestamp on rule changes';

-- ───────────────────────────────────────────────────────────────────────────
-- Trigger 2: Audit log for rule changes
-- ───────────────────────────────────────────────────────────────────────────
-- Reference: Section 9 (Audit & Compliance Rules)

CREATE OR REPLACE FUNCTION bit.audit_rule_changes()
RETURNS TRIGGER AS $$
BEGIN
  -- Log to shq_error_log (using 'audit' severity)
  INSERT INTO public.shq_error_log (
    error_id,
    error_code,
    error_message,
    severity,
    component,
    stack_trace,
    resolution_status,
    created_at
  ) VALUES (
    CONCAT('04.04.02.04.40000.', LPAD(NEXTVAL('public.error_id_seq')::TEXT, 3, '0')),
    'BIT_RULE_CHANGE',
    CASE TG_OP
      WHEN 'INSERT' THEN CONCAT('New rule created: ', NEW.rule_name, ' (weight: ', NEW.weight, ')')
      WHEN 'UPDATE' THEN CONCAT('Rule updated: ', NEW.rule_name, ' (old weight: ', OLD.weight, ', new weight: ', NEW.weight, ')')
      WHEN 'DELETE' THEN CONCAT('Rule deleted: ', OLD.rule_name)
    END,
    'audit',
    'bit.rule_reference',
    CONCAT('Operation: ', TG_OP, ', Rule ID: ', COALESCE(NEW.rule_reference_id, OLD.rule_reference_id)),
    'logged',
    NOW()
  );

  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_rule_reference_audit
  AFTER INSERT OR UPDATE OR DELETE ON bit.rule_reference
  FOR EACH ROW
  EXECUTE FUNCTION bit.audit_rule_changes();

COMMENT ON FUNCTION bit.audit_rule_changes() IS 'Audit trail for all rule_reference changes (Section 9)';

-- ───────────────────────────────────────────────────────────────────────────
-- Trigger 3: Create BIT event from enrichment log (Optional automation)
-- ───────────────────────────────────────────────────────────────────────────
-- Reference: Section 6 (Example Trigger - Executive Movement)

CREATE OR REPLACE FUNCTION bit.create_event_from_enrichment()
RETURNS TRIGGER AS $$
BEGIN
  -- Only trigger if movement_detected = true
  IF NEW.movement_detected = true AND NEW.status = 'success' THEN
    INSERT INTO bit.events (
      company_unique_id,
      event_type,
      rule_reference_id,
      event_payload,
      detected_at,
      data_quality_score
    )
    SELECT
      NEW.company_unique_id,
      'executive_movement',
      '01.04.03.04.10000.101', -- Standard executive_movement rule
      NEW.result_data,
      NEW.completed_at,
      NEW.data_quality_score
    WHERE NEW.data_quality_score >= 50 -- Only if quality meets minimum
      AND NOT EXISTS (
        -- Prevent duplicate events (same company, same day)
        SELECT 1 FROM bit.events
        WHERE company_unique_id = NEW.company_unique_id
          AND event_type = 'executive_movement'
          AND DATE(detected_at) = DATE(NEW.completed_at)
      );
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_enrichment_to_bit_event
  AFTER INSERT OR UPDATE ON marketing.data_enrichment_log
  FOR EACH ROW
  EXECUTE FUNCTION bit.create_event_from_enrichment();

COMMENT ON FUNCTION bit.create_event_from_enrichment() IS 'Auto-create BIT events from enrichment detections (Section 6)';

-- ═══════════════════════════════════════════════════════════════════════════
-- SEED DATA - Standard Rules
-- ═══════════════════════════════════════════════════════════════════════════
-- Reference: Section 3 (Scoring Logic and Weight Table)

INSERT INTO bit.rule_reference (rule_reference_id, rule_name, event_type, weight, decay_days, description, is_active)
VALUES
  -- Executive Movement (Rule ID: 101)
  (
    '01.04.03.04.10000.101',
    'executive_movement',
    'executive_movement',
    40,
    365,
    'New executive (CFO/CEO/HR) hired or departed. High likelihood of vendor evaluation during transition period.',
    true
  ),

  -- Renewal Windows (Rule IDs: 102-105)
  (
    '01.04.03.04.10000.102',
    'renewal_window_120d',
    'renewal_window_120d',
    35,
    120,
    'Contract renewal window opens (120 days before expiration). Early evaluation phase.',
    true
  ),
  (
    '01.04.03.04.10000.103',
    'renewal_window_90d',
    'renewal_window_90d',
    45,
    90,
    'Contract renewal window at 90 days. Higher urgency, vendor shortlisting likely.',
    true
  ),
  (
    '01.04.03.04.10000.104',
    'renewal_window_60d',
    'renewal_window_60d',
    55,
    60,
    'Contract renewal window at 60 days. Critical decision timeframe.',
    true
  ),
  (
    '01.04.03.04.10000.105',
    'renewal_window_30d',
    'renewal_window_30d',
    70,
    30,
    'Contract renewal window at 30 days. Urgent, immediate opportunity.',
    true
  ),

  -- Compliance Events (Rule ID: 106)
  (
    '01.04.03.04.10000.106',
    'dol_violation',
    'dol_violation',
    30,
    180,
    'Department of Labor violation detected. Compliance pain point creates buying urgency.',
    true
  ),

  -- Growth Signals (Rule IDs: 107-108)
  (
    '01.04.03.04.10000.107',
    'hiring_surge',
    'hiring_surge',
    25,
    180,
    'Significant increase in hiring activity. Growth indicator, potential need for scaling tools.',
    true
  ),
  (
    '01.04.03.04.10000.108',
    'funding_round',
    'funding_round',
    50,
    270,
    'Company raised funding round. Budget availability signal, modernization likely.',
    true
  ),

  -- Technology Changes (Rule ID: 109)
  (
    '01.04.03.04.10000.109',
    'tech_stack_change',
    'tech_stack_change',
    35,
    180,
    'Technology stack change detected (new HR software, infrastructure modernization).',
    true
  ),

  -- Competitive Intelligence (Rule ID: 110)
  (
    '01.04.03.04.10000.110',
    'competitor_switch',
    'competitor_switch',
    60,
    365,
    'Company switched from competitor solution. Actively seeking alternatives.',
    true
  )

ON CONFLICT (rule_reference_id) DO NOTHING;

-- ═══════════════════════════════════════════════════════════════════════════
-- HELPER FUNCTIONS
-- ═══════════════════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────────────────
-- Function: bit.calculate_company_score(company_id)
-- ───────────────────────────────────────────────────────────────────────────
-- Purpose: Calculate current intent score for a specific company
-- Reference: Section 3 (Scoring Formula)

CREATE OR REPLACE FUNCTION bit.calculate_company_score(p_company_id VARCHAR)
RETURNS TABLE (
  company_unique_id VARCHAR,
  total_score NUMERIC,
  score_category VARCHAR,
  event_count BIGINT,
  latest_event_date TIMESTAMPTZ
) AS $$
BEGIN
  RETURN QUERY
  SELECT *
  FROM bit.scores
  WHERE bit.scores.company_unique_id = p_company_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION bit.calculate_company_score(VARCHAR) IS 'Calculate current intent score for specific company';

-- ───────────────────────────────────────────────────────────────────────────
-- Function: bit.get_hot_leads(min_score)
-- ───────────────────────────────────────────────────────────────────────────
-- Purpose: Retrieve all companies with score above threshold
-- Reference: Section 7 (Wheel - Lead Cycles)

CREATE OR REPLACE FUNCTION bit.get_hot_leads(p_min_score NUMERIC DEFAULT 80)
RETURNS TABLE (
  company_unique_id VARCHAR,
  company_name VARCHAR,
  total_score NUMERIC,
  score_category VARCHAR,
  event_count BIGINT,
  latest_event_date TIMESTAMPTZ,
  score_breakdown JSONB
) AS $$
BEGIN
  RETURN QUERY
  SELECT *
  FROM bit.scores
  WHERE bit.scores.total_score >= p_min_score
  ORDER BY bit.scores.total_score DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION bit.get_hot_leads(NUMERIC) IS 'Retrieve companies with score above threshold (default: 80)';

-- ═══════════════════════════════════════════════════════════════════════════
-- PERMISSIONS (Example - adjust based on your roles)
-- ═══════════════════════════════════════════════════════════════════════════

-- Grant read access to bit schema
-- GRANT USAGE ON SCHEMA bit TO readonly_role;
-- GRANT SELECT ON ALL TABLES IN SCHEMA bit TO readonly_role;

-- Grant write access to application role
-- GRANT USAGE ON SCHEMA bit TO app_role;
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA bit TO app_role;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA bit TO app_role;

-- ═══════════════════════════════════════════════════════════════════════════
-- VERIFICATION QUERIES (Run after schema creation)
-- ═══════════════════════════════════════════════════════════════════════════
-- Reference: Section 9 (Audit & Compliance Rules)

-- 1. Verify tables created
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'bit';
-- Expected: rule_reference, events, score_snapshots

-- 2. Verify sequences created
-- SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'bit';
-- Expected: event_id_seq, snapshot_id_seq

-- 3. Verify seed data inserted
-- SELECT COUNT(*) FROM bit.rule_reference WHERE is_active = true;
-- Expected: 10 (standard rule set)

-- 4. Verify view exists
-- SELECT COUNT(*) FROM bit.scores;
-- Expected: Number of companies in marketing.company_master

-- 5. Verify triggers created
-- SELECT trigger_name FROM information_schema.triggers WHERE event_object_schema = 'bit';
-- Expected: trg_rule_reference_updated_at, trg_rule_reference_audit, trg_enrichment_to_bit_event

-- ═══════════════════════════════════════════════════════════════════════════
-- EXAMPLE QUERIES (for testing)
-- ═══════════════════════════════════════════════════════════════════════════

-- Example 1: Get all active rules
-- SELECT * FROM bit.rule_reference WHERE is_active = true ORDER BY weight DESC;

-- Example 2: Get intent scores for all companies
-- SELECT * FROM bit.scores ORDER BY total_score DESC LIMIT 20;

-- Example 3: Get hot leads (80+ score)
-- SELECT * FROM bit.get_hot_leads(80);

-- Example 4: Get events for specific company
-- SELECT * FROM bit.events WHERE company_unique_id = '04.04.02.04.30000.042' ORDER BY detected_at DESC;

-- Example 5: Calculate score for specific company
-- SELECT * FROM bit.calculate_company_score('04.04.02.04.30000.042');

-- Example 6: Get score breakdown for company
-- SELECT company_name, total_score, score_breakdown FROM bit.scores WHERE company_unique_id = '04.04.02.04.30000.042';

-- ═══════════════════════════════════════════════════════════════════════════
-- END OF BIT SCHEMA
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Next Steps:
-- 1. Run this script against your Neon PostgreSQL database
-- 2. Verify all tables/views/triggers created successfully
-- 3. Test with sample data (insert test event, query bit.scores)
-- 4. Review BIT-Doctrine.md for operational procedures
-- 5. Configure Grafana dashboards to visualize BIT scores
--
-- Related Files:
-- - doctrine/ple/BIT-Doctrine.md - Complete documentation
-- - infra/grafana/svg-ple-dashboard.json - Grafana dashboard
-- - infra/docs/ENRICHMENT_TRACKING_QUERIES.sql - Related queries
--
-- ═══════════════════════════════════════════════════════════════════════════
