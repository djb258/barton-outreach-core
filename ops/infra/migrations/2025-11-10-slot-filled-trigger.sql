-- ═══════════════════════════════════════════════════════════════════════════
-- SVG-PLE Doctrine Alignment — Slot Tracker Trigger Logic
-- ═══════════════════════════════════════════════════════════════════════════
-- Altitude: 10,000 ft (Execution Layer)
-- Doctrine: Barton / SVG-PLE / SlotWatch Module
-- Owner: Data Automation / LOM
-- Generated: 2025-11-10
-- Barton ID: 04.04.02.04.15000.002
-- Module: slotwatch (Future extraction: barton-slotwatch)
--
-- Purpose: Trigger BIT scoring events when executive slots are filled.
--          Implements spoke-to-axle integration for SlotWatch module.
--
-- Dependencies:
--   - svg_marketing.slot_tracker (created by 2025-11-10-slot-tracker.sql)
--   - bit.events (BIT axle table)
--   - bit.rule_reference (BIT rules)
--
-- Compatibility: PostgreSQL 15+ (Neon)
-- Idempotent: Yes (CREATE OR REPLACE)
-- Future-Proof: Fully swappable into barton-slotwatch repo
-- ═══════════════════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────────────────
-- 🌱 SEED BIT RULES FOR SLOT FILLS
-- ───────────────────────────────────────────────────────────────────────────
-- Doctrine: Define BIT scoring rules for executive slot fills.
--           Higher weights = stronger buyer intent signal.
--
-- Rule Design Rationale:
--   - CEO slot filled: 30 points (highest, entire company direction shifts)
--   - CFO slot filled: 25 points (finance/procurement decisions, budget authority)
--   - HR slot filled: 20 points (HR tech, benefits platforms, recruiting tools)
--
-- All rules active by default, 90-day detection window recommended.
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
        'ceo_slot_filled',
        'CEO executive slot filled - New chief executive hired',
        30,
        'executive',
        true,
        'Triggered when slot_tracker status changes from vacant → filled for CEO role. Indicates highest-level decision-maker change and potential vendor reevaluation.',
        0.95
    ),
    (
        'cfo_slot_filled',
        'CFO executive slot filled - New chief financial officer hired',
        25,
        'executive',
        true,
        'Triggered when slot_tracker status changes from vacant → filled for CFO role. Finance/procurement decisions, budget allocation shifts expected.',
        0.95
    ),
    (
        'hr_slot_filled',
        'HR executive slot filled - New chief HR officer hired',
        20,
        'executive',
        true,
        'Triggered when slot_tracker status changes from vacant → filled for HR role. HR tech stack, benefits platforms, recruiting tools under review.',
        0.90
    )
ON CONFLICT (rule_name) DO UPDATE SET
    rule_description = EXCLUDED.rule_description,
    weight = EXCLUDED.weight,
    category = EXCLUDED.category,
    detection_logic = EXCLUDED.detection_logic,
    confidence_threshold = EXCLUDED.confidence_threshold,
    updated_at = NOW();

-- ───────────────────────────────────────────────────────────────────────────
-- 🔧 FUNCTION: fn_marketing_on_slot_filled()
-- ───────────────────────────────────────────────────────────────────────────
-- Doctrine: Trigger function that fires when executive slot status changes
--           from 'vacant' → 'filled'. Creates BIT event and sets marketing
--           trigger flag.
--
-- Trigger Logic Flow:
--   1. Detect status change: OLD.status = 'vacant' AND NEW.status = 'filled'
--   2. Check idempotency: Skip if marketing_triggered already true
--   3. Map role to BIT rule: CEO → ceo_slot_filled, etc.
--   4. Insert BIT event with slot metadata
--   5. Set NEW.marketing_triggered = true
--   6. Set NEW.filled_at = NOW() if not already set
--
-- Integration Points:
--   - bit.events (axle): Creates new event record
--   - bit.rule_reference: Looks up rule_id and weight
--   - slot_tracker: Updates marketing_triggered flag
--
-- Future Extraction Note:
--   This function is self-contained. When extracting to barton-slotwatch,
--   only dependency is bit.events table structure (or mock interface).
-- ───────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION svg_marketing.fn_marketing_on_slot_filled()
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
    -- ═══════════════════════════════════════════════════════════════════
    -- STEP 1: Detect Status Change (vacant → filled)
    -- ═══════════════════════════════════════════════════════════════════

    -- Only trigger on INSERT or UPDATE where status becomes 'filled'
    IF TG_OP = 'INSERT' THEN
        -- On INSERT, trigger if status = 'filled'
        IF NEW.status != 'filled' THEN
            RETURN NEW;
        END IF;
    ELSIF TG_OP = 'UPDATE' THEN
        -- On UPDATE, only trigger if status changed from vacant → filled
        IF OLD.status = 'filled' OR NEW.status != 'filled' THEN
            RETURN NEW;
        END IF;
    ELSE
        -- Should not happen (DELETE not configured), but return anyway
        RETURN NEW;
    END IF;

    -- ═══════════════════════════════════════════════════════════════════
    -- STEP 2: Idempotency Check
    -- ═══════════════════════════════════════════════════════════════════

    -- Skip if marketing already triggered for this slot fill
    IF NEW.marketing_triggered = true THEN
        RETURN NEW;
    END IF;

    -- ═══════════════════════════════════════════════════════════════════
    -- STEP 3: Map Role to BIT Rule
    -- ═══════════════════════════════════════════════════════════════════

    v_rule_name := CASE NEW.role
        WHEN 'CEO' THEN 'ceo_slot_filled'
        WHEN 'CFO' THEN 'cfo_slot_filled'
        WHEN 'HR' THEN 'hr_slot_filled'
        ELSE NULL
    END;

    -- Skip if no matching rule (should not happen given CHECK constraint)
    IF v_rule_name IS NULL THEN
        RAISE WARNING 'Unknown role type for slot_id %: %', NEW.slot_id, NEW.role;
        RETURN NEW;
    END IF;

    -- ═══════════════════════════════════════════════════════════════════
    -- STEP 4: Lookup BIT Rule Details
    -- ═══════════════════════════════════════════════════════════════════

    SELECT rule_id, weight
    INTO v_rule_id, v_weight
    FROM bit.rule_reference
    WHERE rule_name = v_rule_name
      AND is_active = true
    LIMIT 1;

    -- Skip if rule not found or inactive (warn but don't fail)
    IF v_rule_id IS NULL THEN
        RAISE WARNING 'BIT rule not found or inactive for role %: %', NEW.role, v_rule_name;
        RETURN NEW;
    END IF;

    -- ═══════════════════════════════════════════════════════════════════
    -- STEP 5: Build Event Payload
    -- ═══════════════════════════════════════════════════════════════════

    v_event_payload := jsonb_build_object(
        'slot_id', NEW.slot_id,
        'role', NEW.role,
        'contact_id', NEW.contact_id,
        'filled_at', COALESCE(NEW.filled_at, NOW()),
        'vacated_at', NEW.vacated_at,
        'slot_metadata', COALESCE(NEW.slot_metadata, '{}'::jsonb),
        'reason', 'slot_filled',
        'module', 'slotwatch'
    );

    -- ═══════════════════════════════════════════════════════════════════
    -- STEP 6: Insert BIT Event
    -- ═══════════════════════════════════════════════════════════════════

    INSERT INTO bit.events (
        company_unique_id,
        rule_id,
        weight,
        event_payload,
        detection_source,
        detected_at
    )
    VALUES (
        NEW.company_id,
        v_rule_id,
        v_weight,
        v_event_payload,
        'slotwatch_module',
        COALESCE(NEW.filled_at, NOW())
    )
    RETURNING event_id INTO v_event_id;

    -- ═══════════════════════════════════════════════════════════════════
    -- STEP 7: Update Slot Tracker Record
    -- ═══════════════════════════════════════════════════════════════════

    -- Set marketing_triggered flag
    NEW.marketing_triggered := true;

    -- Ensure filled_at is set (in case it wasn't provided)
    IF NEW.filled_at IS NULL THEN
        NEW.filled_at := NOW();
    END IF;

    -- Store BIT event ID in metadata for cross-reference
    NEW.slot_metadata := COALESCE(NEW.slot_metadata, '{}'::jsonb) ||
                         jsonb_build_object('bit_event_id', v_event_id);

    -- ═══════════════════════════════════════════════════════════════════
    -- STEP 8: Return Updated Row
    -- ═══════════════════════════════════════════════════════════════════

    RETURN NEW;

EXCEPTION
    WHEN OTHERS THEN
        -- Log error but don't fail the slot update
        RAISE WARNING 'Failed to create BIT event for slot_id %: %', NEW.slot_id, SQLERRM;
        RETURN NEW;
END;
$$;

COMMENT ON FUNCTION svg_marketing.fn_marketing_on_slot_filled() IS 'SlotWatch Module — Trigger function: Auto-creates BIT events when executive slots are filled';

-- ───────────────────────────────────────────────────────────────────────────
-- ⚡ TRIGGER: trg_slot_filled_to_bit
-- ───────────────────────────────────────────────────────────────────────────
-- Doctrine: Fires on INSERT or UPDATE to slot_tracker when status becomes
--           'filled'. Implements module-to-axle integration pattern.
--
-- Timing: BEFORE INSERT/UPDATE (allows modification of NEW row)
-- Scope: FOR EACH ROW
-- ───────────────────────────────────────────────────────────────────────────

DROP TRIGGER IF EXISTS trg_slot_filled_to_bit ON svg_marketing.slot_tracker;

CREATE TRIGGER trg_slot_filled_to_bit
    BEFORE INSERT OR UPDATE ON svg_marketing.slot_tracker
    FOR EACH ROW
    EXECUTE FUNCTION svg_marketing.fn_marketing_on_slot_filled();

COMMENT ON TRIGGER trg_slot_filled_to_bit ON svg_marketing.slot_tracker IS 'SlotWatch Module — Auto-trigger: Creates BIT events when slots are filled';

-- ───────────────────────────────────────────────────────────────────────────
-- 🔄 HELPER FUNCTION: Reset Marketing Trigger on Vacancy
-- ───────────────────────────────────────────────────────────────────────────
-- Doctrine: When a slot becomes vacant, reset marketing_triggered flag.
--           This allows the next fill to trigger marketing again.
--
-- Use Case: CEO departs → slot vacant → new CEO hired → trigger marketing
-- ───────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION svg_marketing.fn_reset_marketing_on_vacancy()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- Only trigger on UPDATE where status changes to 'vacant'
    IF TG_OP = 'UPDATE' AND NEW.status = 'vacant' AND OLD.status = 'filled' THEN
        -- Reset marketing trigger flag
        NEW.marketing_triggered := false;

        -- Set vacated_at timestamp
        IF NEW.vacated_at IS NULL THEN
            NEW.vacated_at := NOW();
        END IF;

        -- Clear contact_id (enforced by CHECK constraint anyway)
        NEW.contact_id := NULL;
    END IF;

    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION svg_marketing.fn_reset_marketing_on_vacancy() IS 'SlotWatch Module — Reset marketing trigger flag when slot becomes vacant';

-- ───────────────────────────────────────────────────────────────────────────
-- ⚡ TRIGGER: trg_reset_marketing_on_vacancy
-- ───────────────────────────────────────────────────────────────────────────

DROP TRIGGER IF EXISTS trg_reset_marketing_on_vacancy ON svg_marketing.slot_tracker;

CREATE TRIGGER trg_reset_marketing_on_vacancy
    BEFORE UPDATE ON svg_marketing.slot_tracker
    FOR EACH ROW
    EXECUTE FUNCTION svg_marketing.fn_reset_marketing_on_vacancy();

COMMENT ON TRIGGER trg_reset_marketing_on_vacancy ON svg_marketing.slot_tracker IS 'SlotWatch Module — Reset marketing_triggered flag on vacancy';

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
    '04.04.02.04.15000.002',
    'schema_migration',
    'slotwatch_module',
    'svg_marketing.fn_marketing_on_slot_filled',
    'SlotWatch module trigger logic — BIT event integration for slot fills',
    jsonb_build_object(
        'migration_file', '2025-11-10-slot-filled-trigger.sql',
        'module_name', 'slotwatch',
        'future_repo', 'barton-slotwatch',
        'components', jsonb_build_array(
            'svg_marketing.fn_marketing_on_slot_filled()',
            'svg_marketing.fn_reset_marketing_on_vacancy()',
            'trg_slot_filled_to_bit',
            'trg_reset_marketing_on_vacancy'
        ),
        'bit_rules_added', 3,
        'rule_names', jsonb_build_array('ceo_slot_filled', 'cfo_slot_filled', 'hr_slot_filled'),
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
-- ✅ MIGRATION COMPLETE — PART 2/2
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Summary:
-- • BIT Rules: 3 new rules (ceo_slot_filled, cfo_slot_filled, hr_slot_filled)
-- • Functions: 2 created (fn_marketing_on_slot_filled, fn_reset_marketing_on_vacancy)
-- • Triggers: 2 created (trg_slot_filled_to_bit, trg_reset_marketing_on_vacancy)
-- • Audit Log: Barton ID 04.04.02.04.15000.002 registered
--
-- Integration Flow:
--   slot_tracker.status (vacant → filled)
--     └─ TRIGGER: trg_slot_filled_to_bit
--         └─ FUNCTION: fn_marketing_on_slot_filled()
--             ├─ Maps role → BIT rule
--             ├─ Inserts into bit.events
--             └─ Sets marketing_triggered = true
--
-- Next Steps:
-- 1. Run verification queries from infra/VERIFICATION_QUERIES.sql
-- 2. Review Slot-Tracker-Doctrine.md for operational guidance
-- 3. Test slot fill workflow (INSERT with status='filled' or UPDATE vacant→filled)
-- 4. Monitor bit.events for detection_source = 'slotwatch_module'
--
-- Module Status:
-- • SlotWatch module: Complete (2/2 migrations)
-- • Self-contained: Yes
-- • Ready for extraction: Yes (barton-slotwatch)
--
-- ═══════════════════════════════════════════════════════════════════════════
