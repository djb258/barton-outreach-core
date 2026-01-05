-- ═══════════════════════════════════════════════════════════════════════════
-- Talent Flow Schema Definition
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Document: Talent-Flow-Doctrine.md (doctrine/ple/Talent-Flow-Doctrine.md)
-- Barton ID Prefix: 01.04.02.04.20000 (reserved for future use)
-- Version: 1.0.0
-- Last Updated: 2025-11-07
-- Status: Production Ready
--
-- Purpose:
--   Define the database schema for Talent Flow, a spoke in the SVG-PLE
--   architecture responsible for detecting, classifying, and tracking people
--   movement events (hires, departures, promotions, transfers) that feed into
--   the BIT (Buyer Intent Tool) axle.
--
-- Architecture:
--   - HUB: people.contact, people.contact_employment, marketing.company_master
--   - SPOKE (Talent Flow): talent_flow.movements, talent_flow.movement_audit
--   - AXLE (BIT): bit.events (receives high-impact movements)
--   - WHEEL: Outreach automation (based on BIT scores)
--
-- References:
--   - Section 4: Schema Explanation (Talent-Flow-Doctrine.md)
--   - Section 5: Trigger Logic → Insert BIT Event
--   - Section 6: Numbering + ID Examples
--   - Section 8: Audit + Data Lineage Rules
--
-- ═══════════════════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────────────────
-- SCHEMA CREATION
-- ───────────────────────────────────────────────────────────────────────────

CREATE SCHEMA IF NOT EXISTS talent_flow;

COMMENT ON SCHEMA talent_flow IS 'Talent Flow Spoke - People movement detection and classification for BIT';

-- ═══════════════════════════════════════════════════════════════════════════
-- TABLE 1: talent_flow.movements
-- ═══════════════════════════════════════════════════════════════════════════
-- Reference: Section 4 (Schema Explanation)
-- Purpose: Central repository for all detected people movements across companies

CREATE TABLE IF NOT EXISTS talent_flow.movements (
  -- Primary Key (using BIGSERIAL for high-volume inserts)
  movement_id BIGSERIAL PRIMARY KEY,

  -- Foreign Keys
  contact_id BIGINT NOT NULL,
  old_company_id VARCHAR(50), -- Barton ID format (04.04.02.04.30000.###), nullable for new hires from unknown
  new_company_id VARCHAR(50), -- Barton ID format (04.04.02.04.30000.###), nullable for departures to unknown

  -- Movement Classification
  movement_type VARCHAR(20) NOT NULL CHECK (movement_type IN ('hire', 'departure', 'promotion', 'transfer')),

  -- Title Information
  old_title TEXT,
  new_title TEXT,

  -- Detection Metadata
  detected_source TEXT NOT NULL,
  confidence_score NUMERIC(5,2) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 100),

  -- Timing
  detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  effective_date DATE, -- Actual movement date (if known, e.g., from LinkedIn start_date)

  -- Processing Status
  processed BOOLEAN DEFAULT FALSE NOT NULL,

  -- Additional Data
  payload JSONB, -- Raw data from enrichment source

  -- Audit Fields
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

  -- Constraints
  CONSTRAINT fk_contact FOREIGN KEY (contact_id)
    REFERENCES people.contact(contact_id)
    ON DELETE CASCADE,
  CONSTRAINT fk_old_company FOREIGN KEY (old_company_id)
    REFERENCES marketing.company_master(company_unique_id)
    ON DELETE SET NULL,
  CONSTRAINT fk_new_company FOREIGN KEY (new_company_id)
    REFERENCES marketing.company_master(company_unique_id)
    ON DELETE SET NULL,
  CONSTRAINT chk_at_least_one_company CHECK (
    old_company_id IS NOT NULL OR new_company_id IS NOT NULL
  ),
  CONSTRAINT chk_confidence_range CHECK (
    confidence_score >= 0 AND confidence_score <= 100
  )
);

-- Indexes for performance
CREATE INDEX idx_movements_contact_id ON talent_flow.movements(contact_id);
CREATE INDEX idx_movements_old_company_id ON talent_flow.movements(old_company_id);
CREATE INDEX idx_movements_new_company_id ON talent_flow.movements(new_company_id);
CREATE INDEX idx_movements_movement_type ON talent_flow.movements(movement_type);
CREATE INDEX idx_movements_detected_at ON talent_flow.movements(detected_at DESC);
CREATE INDEX idx_movements_effective_date ON talent_flow.movements(effective_date DESC);
CREATE INDEX idx_movements_processed ON talent_flow.movements(processed);
CREATE INDEX idx_movements_confidence ON talent_flow.movements(confidence_score DESC);
CREATE INDEX idx_movements_payload ON talent_flow.movements USING GIN(payload);

-- Composite index for common query pattern (unprocessed high-confidence movements)
CREATE INDEX idx_movements_unprocessed_high_conf ON talent_flow.movements(processed, confidence_score DESC)
WHERE processed = FALSE AND confidence_score >= 70;

-- Comments
COMMENT ON TABLE talent_flow.movements IS 'Detected people movements across companies (hire, departure, promotion, transfer)';
COMMENT ON COLUMN talent_flow.movements.movement_id IS 'Auto-incrementing primary key (BIGSERIAL)';
COMMENT ON COLUMN talent_flow.movements.contact_id IS 'Links to people.contact (person who moved)';
COMMENT ON COLUMN talent_flow.movements.old_company_id IS 'Previous company (Barton ID: 04.04.02.04.30000.###), NULL if hire from unknown';
COMMENT ON COLUMN talent_flow.movements.new_company_id IS 'New company (Barton ID: 04.04.02.04.30000.###), NULL if departure to unknown';
COMMENT ON COLUMN talent_flow.movements.movement_type IS 'Type: hire (external join), departure (leave), promotion (internal up), transfer (internal lateral)';
COMMENT ON COLUMN talent_flow.movements.old_title IS 'Previous job title';
COMMENT ON COLUMN talent_flow.movements.new_title IS 'New job title';
COMMENT ON COLUMN talent_flow.movements.detected_source IS 'Where movement was detected (e.g., Apify - LinkedIn, Abacus, Manual)';
COMMENT ON COLUMN talent_flow.movements.confidence_score IS 'Data quality confidence (0-100), minimum 70 for BIT event creation';
COMMENT ON COLUMN talent_flow.movements.detected_at IS 'When movement was detected by system';
COMMENT ON COLUMN talent_flow.movements.effective_date IS 'Actual movement date (if known, e.g., from LinkedIn start_date)';
COMMENT ON COLUMN talent_flow.movements.processed IS 'Has this movement been sent to BIT? (set to TRUE after BIT event creation)';
COMMENT ON COLUMN talent_flow.movements.payload IS 'Raw data from enrichment source (JSONB for flexibility)';

-- ═══════════════════════════════════════════════════════════════════════════
-- TABLE 2: talent_flow.movement_audit
-- ═══════════════════════════════════════════════════════════════════════════
-- Reference: Section 8 (Audit + Data Lineage Rules)
-- Purpose: Immutable audit trail for all changes to movement records

CREATE TABLE IF NOT EXISTS talent_flow.movement_audit (
  -- Primary Key
  audit_id BIGSERIAL PRIMARY KEY,

  -- Foreign Key
  movement_id BIGINT NOT NULL,

  -- Audit Details
  operation VARCHAR(10) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
  old_data JSONB, -- Record before change (NULL for INSERT)
  new_data JSONB, -- Record after change (NULL for DELETE)

  -- Metadata
  changed_by VARCHAR(100), -- User or system that made change
  changed_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

  -- Constraints
  CONSTRAINT fk_movement FOREIGN KEY (movement_id)
    REFERENCES talent_flow.movements(movement_id)
    ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_movement_audit_movement_id ON talent_flow.movement_audit(movement_id);
CREATE INDEX idx_movement_audit_changed_at ON talent_flow.movement_audit(changed_at DESC);
CREATE INDEX idx_movement_audit_operation ON talent_flow.movement_audit(operation);

-- Comments
COMMENT ON TABLE talent_flow.movement_audit IS 'Immutable audit trail for all movement record changes (Section 8)';
COMMENT ON COLUMN talent_flow.movement_audit.audit_id IS 'Auto-incrementing primary key';
COMMENT ON COLUMN talent_flow.movement_audit.movement_id IS 'Links to talent_flow.movements';
COMMENT ON COLUMN talent_flow.movement_audit.operation IS 'Type of change: INSERT, UPDATE, or DELETE';
COMMENT ON COLUMN talent_flow.movement_audit.old_data IS 'Record state before change (NULL for INSERT)';
COMMENT ON COLUMN talent_flow.movement_audit.new_data IS 'Record state after change (NULL for DELETE)';
COMMENT ON COLUMN talent_flow.movement_audit.changed_by IS 'User or system that made the change';
COMMENT ON COLUMN talent_flow.movement_audit.changed_at IS 'Timestamp of change';

-- ═══════════════════════════════════════════════════════════════════════════
-- VIEW: talent_flow.executive_movements
-- ═══════════════════════════════════════════════════════════════════════════
-- Reference: Section 4 (Schema Explanation)
-- Purpose: Pre-filtered view of high-impact movements (C-Suite + VP/Director)

CREATE OR REPLACE VIEW talent_flow.executive_movements AS
SELECT
  m.*,
  c.first_name,
  c.last_name,
  c.email,
  c.linkedin_url,
  old_cm.company_name AS old_company_name,
  new_cm.company_name AS new_company_name
FROM talent_flow.movements m
LEFT JOIN people.contact c ON m.contact_id = c.contact_id
LEFT JOIN marketing.company_master old_cm ON m.old_company_id = old_cm.company_unique_id
LEFT JOIN marketing.company_master new_cm ON m.new_company_id = new_cm.company_unique_id
WHERE (
  -- Check if new title is executive-level
  m.new_title ~* 'chief|ceo|cfo|coo|chro|cto|vp|vice president|director|head of'
  OR
  -- Check if old title is executive-level
  m.old_title ~* 'chief|ceo|cfo|coo|chro|cto|vp|vice president|director|head of'
)
AND m.confidence_score >= 70 -- Only high-confidence movements
ORDER BY m.detected_at DESC;

COMMENT ON VIEW talent_flow.executive_movements IS 'Pre-filtered view of high-impact executive movements (confidence >= 70)';

-- ═══════════════════════════════════════════════════════════════════════════
-- TRIGGERS
-- ═══════════════════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────────────────
-- Trigger 1: Auto-update updated_at timestamp
-- ───────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION talent_flow.update_movements_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_movements_updated_at
  BEFORE UPDATE ON talent_flow.movements
  FOR EACH ROW
  EXECUTE FUNCTION talent_flow.update_movements_updated_at();

COMMENT ON FUNCTION talent_flow.update_movements_updated_at() IS 'Auto-update updated_at timestamp on movement record changes';

-- ───────────────────────────────────────────────────────────────────────────
-- Trigger 2: Audit trail for all movement changes
-- ───────────────────────────────────────────────────────────────────────────
-- Reference: Section 8 (Audit + Data Lineage Rules)

CREATE OR REPLACE FUNCTION talent_flow.audit_movement_changes()
RETURNS TRIGGER AS $$
BEGIN
  -- Insert audit record
  INSERT INTO talent_flow.movement_audit (
    movement_id,
    operation,
    old_data,
    new_data,
    changed_by
  ) VALUES (
    COALESCE(NEW.movement_id, OLD.movement_id),
    TG_OP,
    CASE WHEN TG_OP = 'INSERT' THEN NULL ELSE row_to_json(OLD)::jsonb END,
    CASE WHEN TG_OP = 'DELETE' THEN NULL ELSE row_to_json(NEW)::jsonb END,
    CURRENT_USER
  );

  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_movements_audit
  AFTER INSERT OR UPDATE OR DELETE ON talent_flow.movements
  FOR EACH ROW
  EXECUTE FUNCTION talent_flow.audit_movement_changes();

COMMENT ON FUNCTION talent_flow.audit_movement_changes() IS 'Audit trail for all movement record changes (Section 8)';

-- ───────────────────────────────────────────────────────────────────────────
-- Trigger 3: Create BIT event from high-impact movements
-- ───────────────────────────────────────────────────────────────────────────
-- Reference: Section 5 (Trigger Logic → Insert BIT Event)

CREATE OR REPLACE FUNCTION talent_flow.create_bit_event_from_movement()
RETURNS TRIGGER AS $$
DECLARE
  target_company VARCHAR(50);
  is_executive BOOLEAN;
BEGIN
  -- Only process unprocessed movements with sufficient confidence
  IF NEW.processed = FALSE AND NEW.confidence_score >= 70 THEN

    -- Check if movement type qualifies for BIT event
    IF NEW.movement_type IN ('hire', 'departure') THEN

      -- Check if title is executive-level (C-Suite, VP, Director, Head of)
      is_executive := (
        NEW.new_title ~* 'chief|ceo|cfo|coo|chro|cto|vp|vice president|director|head of'
        OR
        NEW.old_title ~* 'chief|ceo|cfo|coo|chro|cto|vp|vice president|director|head of'
      );

      IF is_executive THEN

        -- Determine target company for BIT event
        -- For hires: new company gets the intent signal (new exec evaluating vendors)
        -- For departures: old company gets the intent signal (losing exec, re-evaluation likely)
        target_company := CASE
          WHEN NEW.movement_type = 'hire' THEN NEW.new_company_id
          WHEN NEW.movement_type = 'departure' THEN NEW.old_company_id
        END;

        -- Create BIT event (if target company exists and no duplicate)
        IF target_company IS NOT NULL THEN
          INSERT INTO bit.events (
            company_unique_id,
            event_type,
            rule_reference_id,
            event_payload,
            detected_at,
            data_quality_score
          )
          SELECT
            target_company,
            'executive_movement',
            '01.04.03.04.10000.101', -- Executive movement rule (40 points, 365 day decay)
            jsonb_build_object(
              'movement_id', NEW.movement_id,
              'contact_id', NEW.contact_id,
              'movement_type', NEW.movement_type,
              'old_title', NEW.old_title,
              'new_title', NEW.new_title,
              'old_company_id', NEW.old_company_id,
              'new_company_id', NEW.new_company_id,
              'confidence_score', NEW.confidence_score,
              'detected_source', NEW.detected_source,
              'effective_date', NEW.effective_date
            ),
            NEW.detected_at,
            NEW.confidence_score::INTEGER
          WHERE NOT EXISTS (
            -- Prevent duplicate BIT events for same movement
            SELECT 1 FROM bit.events
            WHERE event_payload->>'movement_id' = NEW.movement_id::TEXT
          );

          -- Mark movement as processed (only if BIT event was created)
          IF FOUND THEN
            NEW.processed := TRUE;
          END IF;
        END IF;

      END IF;
    END IF;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_movements_create_bit_event
  BEFORE INSERT OR UPDATE ON talent_flow.movements
  FOR EACH ROW
  EXECUTE FUNCTION talent_flow.create_bit_event_from_movement();

COMMENT ON FUNCTION talent_flow.create_bit_event_from_movement() IS 'Auto-create BIT events for high-impact executive movements (Section 5)';

-- ═══════════════════════════════════════════════════════════════════════════
-- HELPER FUNCTIONS
-- ═══════════════════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────────────────
-- Function: talent_flow.get_unprocessed_movements(min_confidence)
-- ───────────────────────────────────────────────────────────────────────────
-- Purpose: Retrieve unprocessed movements above confidence threshold

CREATE OR REPLACE FUNCTION talent_flow.get_unprocessed_movements(p_min_confidence NUMERIC DEFAULT 70)
RETURNS TABLE (
  movement_id BIGINT,
  contact_id BIGINT,
  person_name TEXT,
  old_company_name VARCHAR,
  new_company_name VARCHAR,
  movement_type VARCHAR,
  old_title TEXT,
  new_title TEXT,
  confidence_score NUMERIC,
  detected_at TIMESTAMPTZ
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    m.movement_id,
    m.contact_id,
    CONCAT(c.first_name, ' ', c.last_name) AS person_name,
    old_cm.company_name AS old_company_name,
    new_cm.company_name AS new_company_name,
    m.movement_type,
    m.old_title,
    m.new_title,
    m.confidence_score,
    m.detected_at
  FROM talent_flow.movements m
  LEFT JOIN people.contact c ON m.contact_id = c.contact_id
  LEFT JOIN marketing.company_master old_cm ON m.old_company_id = old_cm.company_unique_id
  LEFT JOIN marketing.company_master new_cm ON m.new_company_id = new_cm.company_unique_id
  WHERE m.processed = FALSE
    AND m.confidence_score >= p_min_confidence
  ORDER BY m.detected_at DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION talent_flow.get_unprocessed_movements(NUMERIC) IS 'Retrieve unprocessed movements above confidence threshold (default: 70)';

-- ───────────────────────────────────────────────────────────────────────────
-- Function: talent_flow.get_recent_executive_hires(days_back, min_confidence)
-- ───────────────────────────────────────────────────────────────────────────
-- Purpose: Retrieve recent executive hires for outreach prioritization

CREATE OR REPLACE FUNCTION talent_flow.get_recent_executive_hires(
  p_days_back INTEGER DEFAULT 30,
  p_min_confidence NUMERIC DEFAULT 80
)
RETURNS TABLE (
  movement_id BIGINT,
  person_name TEXT,
  new_company_name VARCHAR,
  new_title TEXT,
  confidence_score NUMERIC,
  detected_at TIMESTAMPTZ,
  bit_score NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    m.movement_id,
    CONCAT(c.first_name, ' ', c.last_name) AS person_name,
    new_cm.company_name AS new_company_name,
    m.new_title,
    m.confidence_score,
    m.detected_at,
    COALESCE(bs.total_score, 0) AS bit_score
  FROM talent_flow.movements m
  LEFT JOIN people.contact c ON m.contact_id = c.contact_id
  LEFT JOIN marketing.company_master new_cm ON m.new_company_id = new_cm.company_unique_id
  LEFT JOIN bit.scores bs ON m.new_company_id = bs.company_unique_id
  WHERE m.movement_type = 'hire'
    AND m.confidence_score >= p_min_confidence
    AND m.detected_at >= NOW() - (p_days_back || ' days')::INTERVAL
    AND m.new_title ~* 'chief|ceo|cfo|coo|chro|cto|vp|vice president|director|head of'
  ORDER BY bs.total_score DESC NULLS LAST, m.detected_at DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION talent_flow.get_recent_executive_hires(INTEGER, NUMERIC) IS 'Retrieve recent executive hires with BIT scores for outreach prioritization';

-- ───────────────────────────────────────────────────────────────────────────
-- Function: talent_flow.classify_movement_impact(movement_id)
-- ───────────────────────────────────────────────────────────────────────────
-- Purpose: Analyze movement impact and determine if it should create BIT event

CREATE OR REPLACE FUNCTION talent_flow.classify_movement_impact(p_movement_id BIGINT)
RETURNS TABLE (
  movement_id BIGINT,
  impact_level VARCHAR,
  should_create_bit_event BOOLEAN,
  estimated_bit_score NUMERIC,
  reasoning TEXT
) AS $$
DECLARE
  v_movement RECORD;
  v_impact VARCHAR;
  v_should_create BOOLEAN;
  v_estimated_score NUMERIC;
  v_reasoning TEXT;
BEGIN
  -- Fetch movement record
  SELECT * INTO v_movement
  FROM talent_flow.movements m
  WHERE m.movement_id = p_movement_id;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Movement ID % not found', p_movement_id;
  END IF;

  -- Classify impact based on title and movement type
  IF v_movement.new_title ~* 'chief|ceo|cfo|coo|chro|cto' OR
     v_movement.old_title ~* 'chief|ceo|cfo|coo|chro|cto' THEN
    v_impact := 'HIGH (C-Suite)';
    v_should_create := TRUE;
    v_estimated_score := 40;
    v_reasoning := 'C-Suite executive movement - highest impact on vendor evaluation';

  ELSIF v_movement.new_title ~* 'vp|vice president|director|head of' OR
        v_movement.old_title ~* 'vp|vice president|director|head of' THEN
    v_impact := 'MEDIUM (VP/Director)';
    v_should_create := (v_movement.movement_type IN ('hire', 'departure') AND v_movement.confidence_score >= 80);
    v_estimated_score := 30;
    v_reasoning := 'VP/Director level - moderate impact, requires high confidence (80+)';

  ELSE
    v_impact := 'LOW (Manager/IC)';
    v_should_create := FALSE;
    v_estimated_score := 0;
    v_reasoning := 'Non-executive role - no BIT event created';
  END IF;

  -- Check confidence threshold
  IF v_movement.confidence_score < 70 THEN
    v_should_create := FALSE;
    v_reasoning := v_reasoning || '. Confidence score below threshold (< 70)';
  END IF;

  -- Check if already processed
  IF v_movement.processed THEN
    v_should_create := FALSE;
    v_reasoning := v_reasoning || '. Already processed - BIT event already created';
  END IF;

  RETURN QUERY SELECT
    p_movement_id,
    v_impact,
    v_should_create,
    v_estimated_score,
    v_reasoning;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION talent_flow.classify_movement_impact(BIGINT) IS 'Analyze movement impact and determine BIT event eligibility';

-- ═══════════════════════════════════════════════════════════════════════════
-- PERMISSIONS (Example - adjust based on your roles)
-- ═══════════════════════════════════════════════════════════════════════════

-- Grant read access to talent_flow schema
-- GRANT USAGE ON SCHEMA talent_flow TO readonly_role;
-- GRANT SELECT ON ALL TABLES IN SCHEMA talent_flow TO readonly_role;

-- Grant write access to application role
-- GRANT USAGE ON SCHEMA talent_flow TO app_role;
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA talent_flow TO app_role;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA talent_flow TO app_role;

-- ═══════════════════════════════════════════════════════════════════════════
-- VERIFICATION QUERIES (Run after schema creation)
-- ═══════════════════════════════════════════════════════════════════════════
-- Reference: Section 8 (Audit + Data Lineage Rules)

-- 1. Verify tables created
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'talent_flow';
-- Expected: movements, movement_audit

-- 2. Verify view exists
-- SELECT table_name FROM information_schema.views WHERE table_schema = 'talent_flow';
-- Expected: executive_movements

-- 3. Verify triggers created
-- SELECT trigger_name, event_manipulation, event_object_table
-- FROM information_schema.triggers
-- WHERE event_object_schema = 'talent_flow';
-- Expected: trg_movements_updated_at, trg_movements_audit, trg_movements_create_bit_event

-- 4. Verify foreign key constraints
-- SELECT constraint_name, table_name, constraint_type
-- FROM information_schema.table_constraints
-- WHERE table_schema = 'talent_flow' AND constraint_type = 'FOREIGN KEY';
-- Expected: fk_contact, fk_old_company, fk_new_company

-- 5. Verify indexes created
-- SELECT indexname FROM pg_indexes WHERE schemaname = 'talent_flow';
-- Expected: 10+ indexes (see table definitions above)

-- ═══════════════════════════════════════════════════════════════════════════
-- EXAMPLE TEST DATA (for development/testing only)
-- ═══════════════════════════════════════════════════════════════════════════

-- Example 1: CFO Hire (High Impact)
-- INSERT INTO talent_flow.movements (
--   contact_id, old_company_id, new_company_id, movement_type,
--   old_title, new_title, detected_source, confidence_score, effective_date
-- ) VALUES (
--   12345, '04.04.02.04.30000.999', '04.04.02.04.30000.042', 'hire',
--   'CFO', 'Chief Financial Officer', 'Apify - LinkedIn', 95.0, '2025-11-01'
-- );

-- Example 2: VP HR Departure (Medium Impact)
-- INSERT INTO talent_flow.movements (
--   contact_id, old_company_id, new_company_id, movement_type,
--   old_title, new_title, detected_source, confidence_score, effective_date
-- ) VALUES (
--   67890, '04.04.02.04.30000.042', NULL, 'departure',
--   'VP of Human Resources', 'Unknown', 'Abacus', 88.0, '2025-10-15'
-- );

-- Example 3: Manager Promotion (Low Impact - no BIT event)
-- INSERT INTO talent_flow.movements (
--   contact_id, old_company_id, new_company_id, movement_type,
--   old_title, new_title, detected_source, confidence_score, effective_date
-- ) VALUES (
--   11111, '04.04.02.04.30000.042', '04.04.02.04.30000.042', 'promotion',
--   'HR Manager', 'Senior HR Manager', 'Manual Entry', 100.0, '2025-11-01'
-- );

-- ═══════════════════════════════════════════════════════════════════════════
-- EXAMPLE QUERIES (for testing)
-- ═══════════════════════════════════════════════════════════════════════════

-- Example 1: Get all executive movements in last 30 days
-- SELECT * FROM talent_flow.executive_movements
-- WHERE detected_at >= NOW() - INTERVAL '30 days'
-- ORDER BY detected_at DESC;

-- Example 2: Get unprocessed high-confidence movements
-- SELECT * FROM talent_flow.get_unprocessed_movements(80);

-- Example 3: Get recent executive hires with BIT scores
-- SELECT * FROM talent_flow.get_recent_executive_hires(30, 80);

-- Example 4: Classify impact of specific movement
-- SELECT * FROM talent_flow.classify_movement_impact(12345);

-- Example 5: Check audit trail for movement
-- SELECT * FROM talent_flow.movement_audit
-- WHERE movement_id = 12345
-- ORDER BY changed_at DESC;

-- Example 6: Count movements by type and confidence tier
-- SELECT
--   movement_type,
--   CASE
--     WHEN confidence_score >= 90 THEN '90-100 (Verified)'
--     WHEN confidence_score >= 80 THEN '80-89 (High)'
--     WHEN confidence_score >= 70 THEN '70-79 (Medium)'
--     ELSE '0-69 (Low)'
--   END AS confidence_tier,
--   COUNT(*) AS movement_count
-- FROM talent_flow.movements
-- GROUP BY movement_type, confidence_tier
-- ORDER BY movement_type, confidence_tier;

-- Example 7: Find movements that created BIT events
-- SELECT
--   m.movement_id,
--   m.movement_type,
--   m.new_title,
--   m.confidence_score,
--   be.event_id,
--   be.data_quality_score,
--   bs.total_score AS current_bit_score
-- FROM talent_flow.movements m
-- JOIN bit.events be ON (be.event_payload->>'movement_id')::BIGINT = m.movement_id
-- LEFT JOIN bit.scores bs ON be.company_unique_id = bs.company_unique_id
-- ORDER BY m.detected_at DESC
-- LIMIT 20;

-- ═══════════════════════════════════════════════════════════════════════════
-- END OF TALENT FLOW SCHEMA
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Next Steps:
-- 1. Run this script against your Neon PostgreSQL database
-- 2. Verify all tables/views/triggers created successfully (use verification queries)
-- 3. Test with sample data (use example INSERT statements above)
-- 4. Review Talent-Flow-Doctrine.md for operational procedures
-- 5. Configure enrichment agents to populate movements table
-- 6. Monitor bit.events for automatic creation from high-impact movements
--
-- Related Files:
-- - doctrine/ple/Talent-Flow-Doctrine.md - Complete documentation
-- - doctrine/ple/BIT-Doctrine.md - BIT integration documentation
-- - doctrine/schemas/bit-schema.sql - BIT schema (receives movement events)
-- - infra/docs/ENRICHMENT_TRACKING_QUERIES.sql - Enrichment monitoring queries
--
-- ═══════════════════════════════════════════════════════════════════════════
