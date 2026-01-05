-- ═══════════════════════════════════════════════════════════════════════════
-- SVG-PLE Doctrine Alignment — Talent Flow Spoke Infrastructure
-- ═══════════════════════════════════════════════════════════════════════════
-- Altitude: 10,000 ft (Execution Layer)
-- Doctrine: Barton / SVG-PLE / Talent-Flow-Spoke
-- Owner: Data Automation / LOM
-- Generated: 2025-11-10
-- Barton ID: 04.01.02.04.20000.001
--
-- Purpose: Create Talent Flow spoke to detect executive movements and trigger
--          BIT scoring events. This spoke monitors hiring, departures, and
--          role changes in C-suite and VP-level positions.
--
-- Architecture:
--   Hub: marketing.company_master + marketing.people_master
--   Spoke: svg_marketing.talent_flow_movements (this migration)
--   Axle: bit.events (triggered by movements)
--
-- Components:
--   1. svg_marketing.talent_flow_movements — Executive movement tracking
--   2. fn_insert_bit_event() — Trigger function to create BIT events
--   3. trg_talent_flow_to_bit — Trigger on movements table
--   4. vw_talent_flow_summary — Analytics view for Lovable.dev dashboards
--   5. Indexes and constraints for performance
--
-- Compatibility: PostgreSQL 15+ (Neon)
-- Idempotent: Yes (IF NOT EXISTS / IF EXISTS)
-- ═══════════════════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────────────────
-- 🎯 SECTION 1: Schema Setup
-- ───────────────────────────────────────────────────────────────────────────

-- Create svg_marketing schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS svg_marketing;

COMMENT ON SCHEMA svg_marketing IS 'SVG Marketing Analytics — Talent Flow spoke for executive movement detection';

-- ───────────────────────────────────────────────────────────────────────────
-- 📋 TABLE: svg_marketing.talent_flow_movements
-- ───────────────────────────────────────────────────────────────────────────
-- Doctrine: Tracks executive-level position changes (hires, departures, role
--           changes). Each movement represents a potential buying intent signal.
--
-- Movement Types:
--   - hire: New executive joins company
--   - departure: Executive leaves company
--   - promotion: Internal promotion to executive role
--   - role_change: Executive changes roles within company
--   - backfill: Replacement hire for departed executive
--
-- Detection Sources:
--   - linkedin_enrichment: LinkedIn profile scraping
--   - apify_agent: Apify LinkedIn enrichment
--   - manual_entry: Human-verified data entry
--   - crunchbase_api: Crunchbase people endpoint
--   - clearbit_enrichment: Clearbit person enrichment
-- ───────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS svg_marketing.talent_flow_movements (
    movement_id TEXT PRIMARY KEY DEFAULT '04.01.02.04.20000.' || LPAD(nextval('svg_marketing.seq_talent_flow_movements')::TEXT, 3, '0'),

    -- Entity references
    company_unique_id TEXT NOT NULL,
    person_unique_id TEXT,

    -- Movement details
    movement_type TEXT NOT NULL CHECK (movement_type IN ('hire', 'departure', 'promotion', 'role_change', 'backfill')),
    position_title TEXT NOT NULL,
    position_level TEXT NOT NULL CHECK (position_level IN ('C-suite', 'VP', 'Director', 'Senior Manager')),
    department TEXT,

    -- Previous state (for departures and role changes)
    previous_position_title TEXT,
    previous_company TEXT,

    -- Timing
    movement_date DATE NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Metadata
    detection_source TEXT NOT NULL,
    confidence_score NUMERIC(3,2) DEFAULT 0.85 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    verification_status TEXT NOT NULL DEFAULT 'pending' CHECK (verification_status IN ('pending', 'verified', 'rejected', 'needs_review')),

    -- BIT integration
    bit_event_created BOOLEAN NOT NULL DEFAULT false,
    bit_event_id TEXT,
    processed_at TIMESTAMPTZ,

    -- Data lineage
    source_url TEXT,
    source_payload JSONB,

    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by TEXT DEFAULT 'system',

    -- Foreign keys
    CONSTRAINT fk_talent_flow_company
        FOREIGN KEY (company_unique_id)
        REFERENCES marketing.company_master(company_unique_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_talent_flow_person
        FOREIGN KEY (person_unique_id)
        REFERENCES marketing.people_master(unique_id)
        ON DELETE SET NULL,

    -- Business rules
    CONSTRAINT talent_flow_movement_date_not_future
        CHECK (movement_date <= CURRENT_DATE)
);

-- Create sequence for movement IDs
CREATE SEQUENCE IF NOT EXISTS svg_marketing.seq_talent_flow_movements START 1;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_talent_flow_company
    ON svg_marketing.talent_flow_movements(company_unique_id);

CREATE INDEX IF NOT EXISTS idx_talent_flow_person
    ON svg_marketing.talent_flow_movements(person_unique_id);

CREATE INDEX IF NOT EXISTS idx_talent_flow_movement_date
    ON svg_marketing.talent_flow_movements(movement_date DESC);

CREATE INDEX IF NOT EXISTS idx_talent_flow_detected_at
    ON svg_marketing.talent_flow_movements(detected_at DESC);

CREATE INDEX IF NOT EXISTS idx_talent_flow_type
    ON svg_marketing.talent_flow_movements(movement_type);

CREATE INDEX IF NOT EXISTS idx_talent_flow_level
    ON svg_marketing.talent_flow_movements(position_level);

CREATE INDEX IF NOT EXISTS idx_talent_flow_bit_event_created
    ON svg_marketing.talent_flow_movements(bit_event_created)
    WHERE bit_event_created = false;

CREATE INDEX IF NOT EXISTS idx_talent_flow_verification_status
    ON svg_marketing.talent_flow_movements(verification_status);

-- JSONB GIN index for source_payload
CREATE INDEX IF NOT EXISTS idx_talent_flow_source_payload_gin
    ON svg_marketing.talent_flow_movements USING GIN(source_payload);

-- Comments
COMMENT ON TABLE svg_marketing.talent_flow_movements IS 'Talent Flow Spoke — Tracks executive movements to trigger BIT scoring events';
COMMENT ON COLUMN svg_marketing.talent_flow_movements.movement_id IS 'Barton ID: 04.01.02.04.20000.###';
COMMENT ON COLUMN svg_marketing.talent_flow_movements.movement_type IS 'Type: hire, departure, promotion, role_change, backfill';
COMMENT ON COLUMN svg_marketing.talent_flow_movements.position_level IS 'Level: C-suite, VP, Director, Senior Manager';
COMMENT ON COLUMN svg_marketing.talent_flow_movements.confidence_score IS 'Detection confidence (0-1): higher = more reliable signal';
COMMENT ON COLUMN svg_marketing.talent_flow_movements.bit_event_created IS 'Flag: Has this movement triggered a BIT event yet?';
COMMENT ON COLUMN svg_marketing.talent_flow_movements.verification_status IS 'Status: pending, verified, rejected, needs_review';

-- ───────────────────────────────────────────────────────────────────────────
-- 🔧 FUNCTION: fn_insert_bit_event()
-- ───────────────────────────────────────────────────────────────────────────
-- Doctrine: Trigger function that automatically creates BIT events when
--           executive movements are detected. This function implements the
--           spoke-to-axle integration pattern.
--
-- Trigger Logic:
--   1. Check if BIT event already created (idempotency)
--   2. Check if verification_status = 'verified' OR confidence_score >= 0.80
--   3. Map movement_type to BIT rule_name
--   4. Insert event into bit.events
--   5. Update talent_flow_movements with bit_event_id and processed_at
--
-- BIT Rule Mapping:
--   - hire (C-suite) → executive_movement (weight: 25)
--   - departure (C-suite) → executive_departure (weight: 20)
--   - hire (VP) → vp_hire (weight: 15)
--   - promotion → internal_promotion (weight: 10)
--   - role_change → executive_role_change (weight: 15)
-- ───────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION svg_marketing.fn_insert_bit_event()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_rule_name TEXT;
    v_rule_id INTEGER;
    v_weight INTEGER;
    v_event_id TEXT;
    v_event_payload JSONB;
BEGIN
    -- Skip if BIT event already created
    IF NEW.bit_event_created = true THEN
        RETURN NEW;
    END IF;

    -- Only process verified movements or high-confidence detections
    IF NEW.verification_status NOT IN ('verified') AND NEW.confidence_score < 0.80 THEN
        RETURN NEW;
    END IF;

    -- Map movement type + level to BIT rule
    v_rule_name := CASE
        WHEN NEW.movement_type = 'hire' AND NEW.position_level = 'C-suite' THEN 'executive_movement'
        WHEN NEW.movement_type = 'departure' AND NEW.position_level = 'C-suite' THEN 'executive_departure'
        WHEN NEW.movement_type = 'hire' AND NEW.position_level = 'VP' THEN 'vp_hire'
        WHEN NEW.movement_type = 'promotion' THEN 'internal_promotion'
        WHEN NEW.movement_type = 'role_change' THEN 'executive_role_change'
        WHEN NEW.movement_type = 'backfill' THEN 'executive_backfill'
        ELSE NULL
    END;

    -- Skip if no matching rule
    IF v_rule_name IS NULL THEN
        RETURN NEW;
    END IF;

    -- Get rule_id and weight from bit.rule_reference
    SELECT rule_id, weight
    INTO v_rule_id, v_weight
    FROM bit.rule_reference
    WHERE rule_name = v_rule_name
      AND is_active = true
    LIMIT 1;

    -- Skip if rule not found or inactive
    IF v_rule_id IS NULL THEN
        RETURN NEW;
    END IF;

    -- Build event payload
    v_event_payload := jsonb_build_object(
        'movement_id', NEW.movement_id,
        'movement_type', NEW.movement_type,
        'position_title', NEW.position_title,
        'position_level', NEW.position_level,
        'department', NEW.department,
        'previous_position_title', NEW.previous_position_title,
        'previous_company', NEW.previous_company,
        'movement_date', NEW.movement_date,
        'detection_source', NEW.detection_source,
        'confidence_score', NEW.confidence_score,
        'person_unique_id', NEW.person_unique_id,
        'source_url', NEW.source_url
    );

    -- Insert BIT event
    INSERT INTO bit.events (
        company_unique_id,
        rule_id,
        weight,
        event_payload,
        detection_source,
        detected_at
    )
    VALUES (
        NEW.company_unique_id,
        v_rule_id,
        v_weight,
        v_event_payload,
        'talent_flow_spoke',
        NEW.detected_at
    )
    RETURNING event_id INTO v_event_id;

    -- Update movement record with BIT event reference
    NEW.bit_event_created := true;
    NEW.bit_event_id := v_event_id;
    NEW.processed_at := NOW();

    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION svg_marketing.fn_insert_bit_event() IS 'Trigger function: Auto-creates BIT events from talent flow movements';

-- ───────────────────────────────────────────────────────────────────────────
-- ⚡ TRIGGER: trg_talent_flow_to_bit
-- ───────────────────────────────────────────────────────────────────────────
-- Doctrine: Fires on INSERT or UPDATE to talent_flow_movements.
--           Implements spoke-to-axle integration pattern.
-- ───────────────────────────────────────────────────────────────────────────

DROP TRIGGER IF EXISTS trg_talent_flow_to_bit ON svg_marketing.talent_flow_movements;

CREATE TRIGGER trg_talent_flow_to_bit
    BEFORE INSERT OR UPDATE ON svg_marketing.talent_flow_movements
    FOR EACH ROW
    EXECUTE FUNCTION svg_marketing.fn_insert_bit_event();

COMMENT ON TRIGGER trg_talent_flow_to_bit ON svg_marketing.talent_flow_movements IS 'Auto-trigger: Creates BIT events from executive movements';

-- ───────────────────────────────────────────────────────────────────────────
-- 📊 VIEW: vw_talent_flow_summary
-- ───────────────────────────────────────────────────────────────────────────
-- Doctrine: Analytics view for Lovable.dev dashboards. Provides aggregated
--           metrics on talent flow movements, BIT event creation rates, and
--           detection source performance.
--
-- Use Cases:
--   - Dashboard: Movement trend charts (last 30/90 days)
--   - Dashboard: Detection source accuracy comparison
--   - Dashboard: C-suite vs VP movement ratios
--   - Alert: Companies with multiple recent movements (churn risk)
-- ───────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW svg_marketing.vw_talent_flow_summary AS
SELECT
    -- Company info
    cm.company_unique_id,
    cm.company_name,
    cm.industry,
    cm.employee_count,

    -- Movement counts
    COUNT(*) AS total_movements,
    COUNT(*) FILTER (WHERE tfm.movement_type = 'hire') AS hire_count,
    COUNT(*) FILTER (WHERE tfm.movement_type = 'departure') AS departure_count,
    COUNT(*) FILTER (WHERE tfm.movement_type = 'promotion') AS promotion_count,
    COUNT(*) FILTER (WHERE tfm.movement_type = 'role_change') AS role_change_count,

    -- Level breakdown
    COUNT(*) FILTER (WHERE tfm.position_level = 'C-suite') AS csuite_movements,
    COUNT(*) FILTER (WHERE tfm.position_level = 'VP') AS vp_movements,
    COUNT(*) FILTER (WHERE tfm.position_level = 'Director') AS director_movements,

    -- BIT integration metrics
    COUNT(*) FILTER (WHERE tfm.bit_event_created = true) AS bit_events_created,
    ROUND(100.0 * COUNT(*) FILTER (WHERE tfm.bit_event_created = true) / NULLIF(COUNT(*), 0), 1) AS bit_creation_rate_pct,

    -- Verification metrics
    COUNT(*) FILTER (WHERE tfm.verification_status = 'verified') AS verified_movements,
    COUNT(*) FILTER (WHERE tfm.verification_status = 'pending') AS pending_verification,
    COUNT(*) FILTER (WHERE tfm.verification_status = 'rejected') AS rejected_movements,

    -- Detection source breakdown
    COUNT(*) FILTER (WHERE tfm.detection_source = 'linkedin_enrichment') AS linkedin_detections,
    COUNT(*) FILTER (WHERE tfm.detection_source = 'apify_agent') AS apify_detections,
    COUNT(*) FILTER (WHERE tfm.detection_source = 'manual_entry') AS manual_detections,

    -- Confidence metrics
    ROUND(AVG(tfm.confidence_score)::numeric, 2) AS avg_confidence_score,
    MIN(tfm.confidence_score) AS min_confidence_score,
    MAX(tfm.confidence_score) AS max_confidence_score,

    -- Timing
    MIN(tfm.movement_date) AS first_movement_date,
    MAX(tfm.movement_date) AS most_recent_movement_date,
    MAX(tfm.detected_at) AS last_detection_at,

    -- Churn risk indicator
    CASE
        WHEN COUNT(*) FILTER (WHERE tfm.movement_type = 'departure' AND tfm.movement_date >= CURRENT_DATE - INTERVAL '90 days') >= 2
        THEN 'high_churn_risk'
        WHEN COUNT(*) FILTER (WHERE tfm.movement_type = 'departure' AND tfm.movement_date >= CURRENT_DATE - INTERVAL '180 days') >= 1
        THEN 'moderate_churn_risk'
        ELSE 'stable'
    END AS churn_risk_level

FROM marketing.company_master cm
LEFT JOIN svg_marketing.talent_flow_movements tfm ON cm.company_unique_id = tfm.company_unique_id
GROUP BY cm.company_unique_id, cm.company_name, cm.industry, cm.employee_count
HAVING COUNT(tfm.movement_id) > 0
ORDER BY total_movements DESC, most_recent_movement_date DESC;

COMMENT ON VIEW svg_marketing.vw_talent_flow_summary IS 'Talent Flow Analytics — Aggregated movement metrics for Lovable.dev dashboards';

-- ───────────────────────────────────────────────────────────────────────────
-- 🌱 SEED DATA: BIT Rules for Talent Flow
-- ───────────────────────────────────────────────────────────────────────────
-- Doctrine: Insert BIT rules for executive movement detection.
--           These rules define scoring weights for different movement types.
-- ───────────────────────────────────────────────────────────────────────────

INSERT INTO bit.rule_reference (
    rule_name,
    rule_description,
    weight,
    category,
    is_active,
    detection_logic,
    confidence_threshold
)
VALUES
    (
        'executive_movement',
        'New C-suite executive hired (CEO, CFO, CTO, COO, CHRO)',
        25,
        'executive',
        true,
        'Detected via LinkedIn enrichment, Apify, or manual entry. Triggers on hire + C-suite level.',
        0.80
    ),
    (
        'executive_departure',
        'C-suite executive departed or role eliminated',
        20,
        'executive',
        true,
        'Detected via LinkedIn profile changes or manual entry. May indicate instability or opportunity.',
        0.80
    ),
    (
        'vp_hire',
        'New VP-level executive hired',
        15,
        'hiring',
        true,
        'Detected via LinkedIn enrichment. VP-level hires indicate growth or restructuring.',
        0.75
    ),
    (
        'internal_promotion',
        'Internal promotion to executive role',
        10,
        'executive',
        true,
        'Promotion from within indicates growth and succession planning.',
        0.70
    ),
    (
        'executive_role_change',
        'Executive changed roles within company',
        15,
        'executive',
        true,
        'Role change may indicate restructuring or strategic shift.',
        0.75
    ),
    (
        'executive_backfill',
        'Replacement hire for departed executive',
        18,
        'executive',
        true,
        'Backfill hire indicates stabilization after departure. Potential re-engagement opportunity.',
        0.80
    )
ON CONFLICT (rule_name) DO UPDATE SET
    rule_description = EXCLUDED.rule_description,
    weight = EXCLUDED.weight,
    category = EXCLUDED.category,
    detection_logic = EXCLUDED.detection_logic,
    confidence_threshold = EXCLUDED.confidence_threshold,
    updated_at = NOW();

-- ───────────────────────────────────────────────────────────────────────────
-- 🔧 AUTO-UPDATE TRIGGER for updated_at
-- ───────────────────────────────────────────────────────────────────────────

DROP TRIGGER IF EXISTS trigger_talent_flow_updated_at ON svg_marketing.talent_flow_movements;

CREATE TRIGGER trigger_talent_flow_updated_at
    BEFORE UPDATE ON svg_marketing.talent_flow_movements
    FOR EACH ROW
    EXECUTE FUNCTION trigger_updated_at();

-- ───────────────────────────────────────────────────────────────────────────
-- 📝 BARTON AUDIT LOG ENTRY
-- ───────────────────────────────────────────────────────────────────────────
-- Doctrine: Register this migration in the Barton audit system.
-- ───────────────────────────────────────────────────────────────────────────

INSERT INTO shq.audit_log (
    audit_id,
    event_type,
    entity_type,
    entity_id,
    description,
    metadata,
    created_at,
    created_by
)
VALUES (
    '04.01.02.04.20000.001',
    'schema_migration',
    'talent_flow_spoke',
    'svg_marketing.talent_flow_movements',
    'Talent Flow schema initialization — Executive movement detection spoke integrated with BIT axle',
    jsonb_build_object(
        'migration_file', '2025-11-10-talent-flow.sql',
        'components', jsonb_build_array(
            'svg_marketing.talent_flow_movements',
            'svg_marketing.fn_insert_bit_event()',
            'svg_marketing.vw_talent_flow_summary',
            'trg_talent_flow_to_bit'
        ),
        'bit_rules_added', 6,
        'indexes_created', 9,
        'spoke_type', 'talent_flow',
        'axle_integration', 'bit.events'
    ),
    NOW(),
    'system'
)
ON CONFLICT (audit_id) DO UPDATE SET
    description = EXCLUDED.description,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

-- ═══════════════════════════════════════════════════════════════════════════
-- ✅ MIGRATION COMPLETE
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Summary:
-- • Schema: svg_marketing (created)
-- • Table: talent_flow_movements (created with 9 indexes)
-- • Function: fn_insert_bit_event() (created)
-- • Trigger: trg_talent_flow_to_bit (created)
-- • View: vw_talent_flow_summary (created)
-- • BIT Rules: 6 new rules seeded
-- • Audit Log: Barton ID 04.01.02.04.20000.001 registered
--
-- Next Steps:
-- 1. Run verification queries from infra/VERIFICATION_QUERIES.sql
-- 2. Test movement insertion and BIT event creation
-- 3. Review Talent-Flow-Doctrine.md for operational guidance
-- 4. Configure Lovable.dev dashboard with vw_talent_flow_summary
--
-- ═══════════════════════════════════════════════════════════════════════════
