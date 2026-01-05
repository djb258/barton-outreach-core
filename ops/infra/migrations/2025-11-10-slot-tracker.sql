-- ═══════════════════════════════════════════════════════════════════════════
-- SVG-PLE Doctrine Alignment — Slot Tracker Module (SlotWatch)
-- ═══════════════════════════════════════════════════════════════════════════
-- Altitude: 10,000 ft (Execution Layer)
-- Doctrine: Barton / SVG-PLE / SlotWatch Module
-- Owner: Data Automation / LOM
-- Generated: 2025-11-10
-- Barton ID: 04.04.02.04.15000.001
-- Module: slotwatch (Future extraction: barton-slotwatch)
--
-- Purpose: Track executive-level role vacancies and fills (CEO, CFO, HR).
--          Automatically trigger BIT scoring events when slots are filled.
--          Self-contained module designed for future extraction into standalone repo.
--
-- Architecture:
--   Hub: marketing.company_master + marketing.people_master
--   Module: svg_marketing.slot_tracker (this migration)
--   Integration: bit.events (BIT scoring on slot fill)
--
-- Components:
--   1. svg_marketing.slot_tracker — Executive role slot tracking
--   2. Indexes for performance
--   3. Constraints and validation rules
--
-- Compatibility: PostgreSQL 15+ (Neon)
-- Idempotent: Yes (IF NOT EXISTS / IF EXISTS)
-- Future-Proof: Fully swappable into barton-slotwatch repo
-- ═══════════════════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────────────────
-- 🎯 SECTION 1: Schema Verification
-- ───────────────────────────────────────────────────────────────────────────

-- Verify svg_marketing schema exists (created by talent-flow migration)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'svg_marketing') THEN
        CREATE SCHEMA svg_marketing;
        COMMENT ON SCHEMA svg_marketing IS 'SVG Marketing Analytics — PLE spoke and module container';
    END IF;
END
$$;

-- ───────────────────────────────────────────────────────────────────────────
-- 📋 TABLE: svg_marketing.slot_tracker
-- ───────────────────────────────────────────────────────────────────────────
-- Doctrine: Tracks executive-level role slots (CEO, CFO, HR) across target
--           companies. Detects vacancies and fills, triggering marketing
--           automation and BIT scoring events.
--
-- Slot Lifecycle:
--   1. Slot created (initial state: vacant or filled)
--   2. Executive departs → status = 'vacant', vacated_at = NOW()
--   3. Replacement hired → status = 'filled', filled_at = NOW()
--   4. BIT event triggered → marketing_triggered = true
--
-- Role Types:
--   - CEO: Chief Executive Officer (highest priority)
--   - CFO: Chief Financial Officer (finance decision-maker)
--   - HR: Chief Human Resources Officer (benefits/HR tech buyer)
--
-- Future Extraction Note:
--   This table is designed to be self-contained. When extracting to
--   barton-slotwatch repo, only dependencies are:
--   - marketing.company_master (for company_id FK)
--   - marketing.people_master (for contact_id FK)
--   - bit.events (for BIT integration, optional)
-- ───────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS svg_marketing.slot_tracker (
    -- Primary Key
    slot_id BIGSERIAL PRIMARY KEY,

    -- Foreign Key: Company
    company_id TEXT NOT NULL,

    -- Role Definition
    role TEXT NOT NULL CHECK (role IN ('CEO', 'CFO', 'HR')),

    -- Current Occupant (NULL if vacant)
    contact_id TEXT,

    -- Slot Status
    status TEXT NOT NULL DEFAULT 'vacant' CHECK (status IN ('filled', 'vacant')),

    -- Timing Fields
    filled_at TIMESTAMPTZ,
    vacated_at TIMESTAMPTZ,

    -- Marketing Integration
    marketing_triggered BOOLEAN NOT NULL DEFAULT false,

    -- Audit Fields
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by TEXT DEFAULT 'system',

    -- Metadata
    slot_metadata JSONB DEFAULT '{}'::jsonb,

    -- Foreign Key Constraints
    CONSTRAINT fk_slot_tracker_company
        FOREIGN KEY (company_id)
        REFERENCES marketing.company_master(company_unique_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_slot_tracker_contact
        FOREIGN KEY (contact_id)
        REFERENCES marketing.people_master(unique_id)
        ON DELETE SET NULL,

    -- Business Rules
    CONSTRAINT slot_tracker_one_per_company_role
        UNIQUE (company_id, role),

    CONSTRAINT slot_tracker_filled_requires_contact
        CHECK (
            (status = 'filled' AND contact_id IS NOT NULL AND filled_at IS NOT NULL)
            OR
            (status = 'vacant' AND contact_id IS NULL)
        ),

    CONSTRAINT slot_tracker_dates_not_future
        CHECK (
            (filled_at IS NULL OR filled_at <= NOW())
            AND
            (vacated_at IS NULL OR vacated_at <= NOW())
        ),

    CONSTRAINT slot_tracker_vacated_before_filled
        CHECK (
            vacated_at IS NULL
            OR filled_at IS NULL
            OR vacated_at < filled_at
        )
);

-- ───────────────────────────────────────────────────────────────────────────
-- 📇 INDEXES
-- ───────────────────────────────────────────────────────────────────────────

-- Index: Company lookup (most common query)
CREATE INDEX IF NOT EXISTS idx_slot_tracker_company_id
    ON svg_marketing.slot_tracker(company_id);

-- Index: Status filtering (find all vacant slots)
CREATE INDEX IF NOT EXISTS idx_slot_tracker_status
    ON svg_marketing.slot_tracker(status);

-- Index: Role filtering (find all CEO slots)
CREATE INDEX IF NOT EXISTS idx_slot_tracker_role
    ON svg_marketing.slot_tracker(role);

-- Index: Contact lookup (find all slots for a person)
CREATE INDEX IF NOT EXISTS idx_slot_tracker_contact_id
    ON svg_marketing.slot_tracker(contact_id)
    WHERE contact_id IS NOT NULL;

-- Index: Marketing trigger flag (find slots needing marketing action)
CREATE INDEX IF NOT EXISTS idx_slot_tracker_marketing_triggered
    ON svg_marketing.slot_tracker(marketing_triggered)
    WHERE marketing_triggered = false;

-- Index: Recently filled slots (for reporting)
CREATE INDEX IF NOT EXISTS idx_slot_tracker_filled_at
    ON svg_marketing.slot_tracker(filled_at DESC)
    WHERE filled_at IS NOT NULL;

-- Index: Recently vacated slots (for alert generation)
CREATE INDEX IF NOT EXISTS idx_slot_tracker_vacated_at
    ON svg_marketing.slot_tracker(vacated_at DESC)
    WHERE vacated_at IS NOT NULL;

-- Index: Last updated (for incremental sync)
CREATE INDEX IF NOT EXISTS idx_slot_tracker_last_updated
    ON svg_marketing.slot_tracker(last_updated DESC);

-- JSONB GIN index for metadata search
CREATE INDEX IF NOT EXISTS idx_slot_tracker_metadata_gin
    ON svg_marketing.slot_tracker USING GIN(slot_metadata);

-- ───────────────────────────────────────────────────────────────────────────
-- 💬 COMMENTS
-- ───────────────────────────────────────────────────────────────────────────

COMMENT ON TABLE svg_marketing.slot_tracker IS 'SlotWatch Module — Tracks executive role vacancies and fills, triggers BIT events on slot fill';
COMMENT ON COLUMN svg_marketing.slot_tracker.slot_id IS 'Primary key: Unique identifier for this slot';
COMMENT ON COLUMN svg_marketing.slot_tracker.company_id IS 'Foreign key to marketing.company_master (Barton ID format)';
COMMENT ON COLUMN svg_marketing.slot_tracker.role IS 'Executive role type: CEO, CFO, or HR';
COMMENT ON COLUMN svg_marketing.slot_tracker.contact_id IS 'Current occupant: Foreign key to marketing.people_master (NULL if vacant)';
COMMENT ON COLUMN svg_marketing.slot_tracker.status IS 'Slot status: filled (has occupant) or vacant (open position)';
COMMENT ON COLUMN svg_marketing.slot_tracker.filled_at IS 'Timestamp when slot was last filled (NULL if never filled)';
COMMENT ON COLUMN svg_marketing.slot_tracker.vacated_at IS 'Timestamp when slot was last vacated (NULL if never vacated)';
COMMENT ON COLUMN svg_marketing.slot_tracker.marketing_triggered IS 'Flag: Has BIT event been created for this slot fill? (reset on vacancy)';
COMMENT ON COLUMN svg_marketing.slot_tracker.last_updated IS 'Timestamp of last modification (auto-updated by trigger)';
COMMENT ON COLUMN svg_marketing.slot_tracker.slot_metadata IS 'JSONB field for extensible metadata (e.g., salary range, reporting structure)';

-- ───────────────────────────────────────────────────────────────────────────
-- 🔧 AUTO-UPDATE TRIGGER for last_updated
-- ───────────────────────────────────────────────────────────────────────────

DROP TRIGGER IF EXISTS trigger_slot_tracker_last_updated ON svg_marketing.slot_tracker;

CREATE TRIGGER trigger_slot_tracker_last_updated
    BEFORE UPDATE ON svg_marketing.slot_tracker
    FOR EACH ROW
    EXECUTE FUNCTION trigger_updated_at();

COMMENT ON TRIGGER trigger_slot_tracker_last_updated ON svg_marketing.slot_tracker IS 'Auto-update last_updated timestamp on row modification';

-- ───────────────────────────────────────────────────────────────────────────
-- 🌱 SEED DATA: Initialize Slots for Existing Companies
-- ───────────────────────────────────────────────────────────────────────────
-- Doctrine: For each company in company_master, create 3 slots (CEO, CFO, HR).
--           Default status = 'vacant' unless we can determine occupancy.
--
-- Note: This is optional initial seeding. In production, slots should be
--       created dynamically via talent_flow_movements or manual data entry.
-- ───────────────────────────────────────────────────────────────────────────

-- Commented out by default - uncomment to seed existing companies
/*
INSERT INTO svg_marketing.slot_tracker (company_id, role, status)
SELECT
    cm.company_unique_id,
    roles.role,
    'vacant' AS status
FROM marketing.company_master cm
CROSS JOIN (
    VALUES ('CEO'), ('CFO'), ('HR')
) AS roles(role)
ON CONFLICT (company_id, role) DO NOTHING;
*/

-- ───────────────────────────────────────────────────────────────────────────
-- 📝 BARTON AUDIT LOG ENTRY
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
    '04.04.02.04.15000.001',
    'schema_migration',
    'slotwatch_module',
    'svg_marketing.slot_tracker',
    'SlotWatch module initialization — Executive role slot tracking with BIT integration',
    jsonb_build_object(
        'migration_file', '2025-11-10-slot-tracker.sql',
        'module_name', 'slotwatch',
        'future_repo', 'barton-slotwatch',
        'components', jsonb_build_array(
            'svg_marketing.slot_tracker'
        ),
        'indexes_created', 9,
        'role_types', jsonb_build_array('CEO', 'CFO', 'HR'),
        'bit_integration', true,
        'self_contained', true
    ),
    NOW(),
    'system'
)
ON CONFLICT (audit_id) DO UPDATE SET
    description = EXCLUDED.description,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

-- ═══════════════════════════════════════════════════════════════════════════
-- ✅ MIGRATION COMPLETE — PART 1/2
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Summary:
-- • Schema: svg_marketing (verified/created)
-- • Table: slot_tracker (created with 9 indexes)
-- • Constraints: 5 business rules + 2 FK constraints
-- • Unique constraint: One slot per company/role combination
-- • Audit Log: Barton ID 04.04.02.04.15000.001 registered
--
-- Next Steps:
-- 1. Run: 2025-11-10-slot-filled-trigger.sql (BIT event integration)
-- 2. Run verification queries from infra/VERIFICATION_QUERIES.sql
-- 3. Review Slot-Tracker-Doctrine.md for operational guidance
-- 4. Seed initial slot data (optional, see commented section above)
--
-- Module Boundary:
-- • Self-contained: Yes
-- • Dependencies: marketing.company_master, marketing.people_master, bit.events
-- • Future extraction: Ready for barton-slotwatch repo
--
-- ═══════════════════════════════════════════════════════════════════════════
