-- ═══════════════════════════════════════════════════════════════════════════
-- Migration: Slot Assignment History (Append-Only Audit Log)
-- ═══════════════════════════════════════════════════════════════════════════
-- Purpose: Preserve deterministic history for People Slot assignments
--          Enable movement detection without rediscovery
--
-- Requirements Addressed:
--   1. History must be append-only (no updates, no deletes)
--   2. Slot mutations emit DISPLACED/ASSIGNED events
--   3. Answer: Who held slot before? When displaced? Why?
--
-- Tables Created:
--   - people.slot_assignment_history (append-only audit log)
--
-- Triggers Created:
--   - trg_slot_assignment_history (captures all slot mutations)
--
-- Note: Uses people.company_slot as the source table (not marketing.company_slot)
--
-- Compatibility: PostgreSQL 15+ (Neon)
-- Idempotent: Yes (IF NOT EXISTS / CREATE OR REPLACE)
-- ═══════════════════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────────────────
-- TABLE: people.slot_assignment_history
-- ───────────────────────────────────────────────────────────────────────────
-- APPEND-ONLY audit log for slot assignment events.
-- Never updated. Never deleted. Only inserted.
--
-- Event Types:
--   - ASSIGNED: Person assigned to slot (first assignment or after vacancy)
--   - DISPLACED: Person removed from slot by higher-seniority candidate
--   - VACATED: Slot explicitly vacated (departure detection)
-- ───────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS people.slot_assignment_history (
    -- Primary Key (immutable)
    history_id              BIGSERIAL PRIMARY KEY,

    -- Event Classification
    event_type              TEXT NOT NULL CHECK (event_type IN (
                                'ASSIGNED',    -- New holder assigned
                                'DISPLACED',   -- Removed by higher seniority
                                'VACATED'      -- Slot explicitly vacated
                            )),

    -- Slot Identification
    company_slot_unique_id  TEXT NOT NULL,      -- FK to company_slot
    company_unique_id       TEXT NOT NULL,
    slot_type               TEXT NOT NULL,

    -- Person Involved in This Event
    person_unique_id        TEXT,
    confidence_score        NUMERIC(5,2),

    -- Displacement Context (only for DISPLACED events)
    displaced_by_person_id  TEXT,               -- Who took the slot (for DISPLACED)
    displacement_reason     TEXT,               -- e.g., "person_change"

    -- Provenance (uses source_system from company_slot)
    source_system           TEXT NOT NULL DEFAULT 'people_pipeline',

    -- Timing (immutable after insert)
    event_ts                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Original Assignment Reference (for tracking lineage)
    original_filled_at      TIMESTAMPTZ,        -- When this person first got the slot
    tenure_days             INTEGER,            -- How long they held it (computed on DISPLACED)

    -- Metadata (extensible)
    event_metadata          JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- ───────────────────────────────────────────────────────────────────────────
-- IMMUTABILITY CONSTRAINTS
-- ───────────────────────────────────────────────────────────────────────────
-- Append-only enforcement: Block UPDATE and DELETE operations

CREATE OR REPLACE FUNCTION people.fn_slot_history_immutable()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'slot_assignment_history is append-only. UPDATE and DELETE are prohibited.';
    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS trg_slot_history_no_update ON people.slot_assignment_history;
CREATE TRIGGER trg_slot_history_no_update
    BEFORE UPDATE ON people.slot_assignment_history
    FOR EACH ROW
    EXECUTE FUNCTION people.fn_slot_history_immutable();

DROP TRIGGER IF EXISTS trg_slot_history_no_delete ON people.slot_assignment_history;
CREATE TRIGGER trg_slot_history_no_delete
    BEFORE DELETE ON people.slot_assignment_history
    FOR EACH ROW
    EXECUTE FUNCTION people.fn_slot_history_immutable();

COMMENT ON TABLE people.slot_assignment_history IS
    'APPEND-ONLY audit log for slot assignments. Captures ASSIGNED/DISPLACED/VACATED events. Never updated or deleted.';

-- ───────────────────────────────────────────────────────────────────────────
-- INDEXES
-- ───────────────────────────────────────────────────────────────────────────

-- Primary lookups
CREATE INDEX IF NOT EXISTS idx_slot_history_company
    ON people.slot_assignment_history(company_unique_id);

CREATE INDEX IF NOT EXISTS idx_slot_history_person
    ON people.slot_assignment_history(person_unique_id);

CREATE INDEX IF NOT EXISTS idx_slot_history_slot
    ON people.slot_assignment_history(company_unique_id, slot_type);

CREATE INDEX IF NOT EXISTS idx_slot_history_slot_id
    ON people.slot_assignment_history(company_slot_unique_id);

-- Event type filtering
CREATE INDEX IF NOT EXISTS idx_slot_history_event_type
    ON people.slot_assignment_history(event_type);

-- Time-based queries (movement detection)
CREATE INDEX IF NOT EXISTS idx_slot_history_event_ts
    ON people.slot_assignment_history(event_ts DESC);

-- Displacement tracking
CREATE INDEX IF NOT EXISTS idx_slot_history_displaced_by
    ON people.slot_assignment_history(displaced_by_person_id)
    WHERE displaced_by_person_id IS NOT NULL;

-- Composite for "who held this slot" queries
CREATE INDEX IF NOT EXISTS idx_slot_history_slot_person_ts
    ON people.slot_assignment_history(company_unique_id, slot_type, event_ts DESC);

-- JSONB index for metadata queries
CREATE INDEX IF NOT EXISTS idx_slot_history_metadata_gin
    ON people.slot_assignment_history USING GIN(event_metadata);

-- ───────────────────────────────────────────────────────────────────────────
-- TRIGGER: Capture Slot Mutations from people.company_slot
-- ───────────────────────────────────────────────────────────────────────────
-- Fires on INSERT/UPDATE to people.company_slot
-- Emits history events for all slot changes
-- ───────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION people.fn_emit_slot_history_event()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_old_filled_at TIMESTAMPTZ;
    v_tenure_days INTEGER;
BEGIN
    -- ═══════════════════════════════════════════════════════════════════
    -- CASE 1: INSERT with a person assigned (new slot fill)
    -- ═══════════════════════════════════════════════════════════════════
    IF TG_OP = 'INSERT' AND NEW.person_unique_id IS NOT NULL THEN
        INSERT INTO people.slot_assignment_history (
            event_type,
            company_slot_unique_id,
            company_unique_id,
            slot_type,
            person_unique_id,
            confidence_score,
            source_system,
            original_filled_at,
            event_metadata
        ) VALUES (
            'ASSIGNED',
            NEW.company_slot_unique_id,
            NEW.company_unique_id,
            NEW.slot_type,
            NEW.person_unique_id,
            NEW.confidence_score,
            COALESCE(NEW.source_system, 'people_pipeline'),
            COALESCE(NEW.filled_at, NOW()),
            jsonb_build_object(
                'trigger_op', 'INSERT',
                'is_filled', NEW.is_filled,
                'status', NEW.status
            )
        );

        RETURN NEW;
    END IF;

    -- ═══════════════════════════════════════════════════════════════════
    -- CASE 2: UPDATE with person change (displacement)
    -- ═══════════════════════════════════════════════════════════════════
    IF TG_OP = 'UPDATE' AND OLD.person_unique_id IS DISTINCT FROM NEW.person_unique_id THEN

        -- Calculate tenure of displaced person
        v_old_filled_at := OLD.filled_at;
        IF v_old_filled_at IS NOT NULL THEN
            v_tenure_days := EXTRACT(DAY FROM (NOW() - v_old_filled_at))::INTEGER;
        END IF;

        -- Record DISPLACED event for the OLD holder (if there was one)
        IF OLD.person_unique_id IS NOT NULL THEN
            INSERT INTO people.slot_assignment_history (
                event_type,
                company_slot_unique_id,
                company_unique_id,
                slot_type,
                person_unique_id,
                confidence_score,
                displaced_by_person_id,
                displacement_reason,
                source_system,
                original_filled_at,
                tenure_days,
                event_metadata
            ) VALUES (
                'DISPLACED',
                OLD.company_slot_unique_id,
                OLD.company_unique_id,
                OLD.slot_type,
                OLD.person_unique_id,
                OLD.confidence_score,
                NEW.person_unique_id,           -- Who took their slot
                'person_change',
                COALESCE(NEW.source_system, 'people_pipeline'),
                v_old_filled_at,
                v_tenure_days,
                jsonb_build_object(
                    'trigger_op', 'UPDATE',
                    'old_status', OLD.status,
                    'new_status', NEW.status,
                    'old_is_filled', OLD.is_filled,
                    'new_is_filled', NEW.is_filled
                )
            );
        END IF;

        -- Record ASSIGNED event for the NEW holder (if there is one)
        IF NEW.person_unique_id IS NOT NULL THEN
            INSERT INTO people.slot_assignment_history (
                event_type,
                company_slot_unique_id,
                company_unique_id,
                slot_type,
                person_unique_id,
                confidence_score,
                displaced_by_person_id,
                displacement_reason,
                source_system,
                original_filled_at,
                event_metadata
            ) VALUES (
                'ASSIGNED',
                NEW.company_slot_unique_id,
                NEW.company_unique_id,
                NEW.slot_type,
                NEW.person_unique_id,
                NEW.confidence_score,
                OLD.person_unique_id,               -- Who they displaced (if any)
                CASE WHEN OLD.person_unique_id IS NOT NULL THEN 'replaced_existing' ELSE 'new_assignment' END,
                COALESCE(NEW.source_system, 'people_pipeline'),
                COALESCE(NEW.filled_at, NOW()),
                jsonb_build_object(
                    'trigger_op', 'UPDATE',
                    'displaced_prior_holder', OLD.person_unique_id IS NOT NULL,
                    'status', NEW.status
                )
            );
        END IF;

        -- Record VACATED event if person was removed without replacement
        IF OLD.person_unique_id IS NOT NULL AND NEW.person_unique_id IS NULL THEN
            INSERT INTO people.slot_assignment_history (
                event_type,
                company_slot_unique_id,
                company_unique_id,
                slot_type,
                person_unique_id,
                confidence_score,
                source_system,
                original_filled_at,
                tenure_days,
                event_metadata
            ) VALUES (
                'VACATED',
                OLD.company_slot_unique_id,
                OLD.company_unique_id,
                OLD.slot_type,
                OLD.person_unique_id,
                OLD.confidence_score,
                COALESCE(NEW.source_system, 'people_pipeline'),
                v_old_filled_at,
                v_tenure_days,
                jsonb_build_object(
                    'trigger_op', 'UPDATE',
                    'vacated_at', NEW.vacated_at,
                    'reason', 'person_removed'
                )
            );
        END IF;

        RETURN NEW;
    END IF;

    -- ═══════════════════════════════════════════════════════════════════
    -- CASE 3: UPDATE without person change (metadata update only)
    -- ═══════════════════════════════════════════════════════════════════
    -- No history event needed for non-person-change updates
    RETURN NEW;

END;
$$;

COMMENT ON FUNCTION people.fn_emit_slot_history_event() IS
    'Trigger function: Emits ASSIGNED/DISPLACED/VACATED events to slot_assignment_history on company_slot mutations';

-- ───────────────────────────────────────────────────────────────────────────
-- ATTACH TRIGGER TO people.company_slot
-- ───────────────────────────────────────────────────────────────────────────

DROP TRIGGER IF EXISTS trg_slot_assignment_history ON people.company_slot;

CREATE TRIGGER trg_slot_assignment_history
    AFTER INSERT OR UPDATE ON people.company_slot
    FOR EACH ROW
    EXECUTE FUNCTION people.fn_emit_slot_history_event();

COMMENT ON TRIGGER trg_slot_assignment_history ON people.company_slot IS
    'Captures all slot mutations and emits history events to slot_assignment_history';

-- ───────────────────────────────────────────────────────────────────────────
-- VIEW: Slot Tenure Summary
-- ───────────────────────────────────────────────────────────────────────────
-- Answers: Who held this slot? How long? Who displaced them?

CREATE OR REPLACE VIEW people.v_slot_tenure_summary AS
SELECT
    company_unique_id,
    slot_type,
    person_unique_id,
    event_type,
    confidence_score,
    displaced_by_person_id,
    displacement_reason,
    original_filled_at,
    event_ts AS event_timestamp,
    tenure_days,
    source_system
FROM people.slot_assignment_history
ORDER BY company_unique_id, slot_type, event_ts DESC;

COMMENT ON VIEW people.v_slot_tenure_summary IS
    'Summarizes slot tenure history - who held each slot, for how long, and why they were displaced';

-- ───────────────────────────────────────────────────────────────────────────
-- VIEW: Recent Displacements (Movement Watch)
-- ───────────────────────────────────────────────────────────────────────────
-- Answers: What should be re-checked next month?

CREATE OR REPLACE VIEW people.v_recent_slot_displacements AS
SELECT
    h.company_unique_id,
    h.slot_type,
    h.person_unique_id AS displaced_person_id,
    h.displaced_by_person_id AS new_holder_id,
    h.confidence_score AS displaced_confidence,
    h.displacement_reason,
    h.tenure_days,
    h.event_ts AS displaced_at,
    h.source_system,
    -- Current slot state
    cs.person_unique_id AS current_holder,
    cs.is_filled AS slot_currently_filled
FROM people.slot_assignment_history h
LEFT JOIN people.company_slot cs
    ON h.company_slot_unique_id = cs.company_slot_unique_id
WHERE h.event_type = 'DISPLACED'
    AND h.event_ts > NOW() - INTERVAL '90 days'
ORDER BY h.event_ts DESC;

COMMENT ON VIEW people.v_recent_slot_displacements IS
    'Recent slot displacements (last 90 days) for movement monitoring and re-check scheduling';

-- ───────────────────────────────────────────────────────────────────────────
-- COLUMN COMMENTS
-- ───────────────────────────────────────────────────────────────────────────

COMMENT ON COLUMN people.slot_assignment_history.history_id IS 'Immutable primary key';
COMMENT ON COLUMN people.slot_assignment_history.event_type IS 'ASSIGNED, DISPLACED, or VACATED';
COMMENT ON COLUMN people.slot_assignment_history.company_slot_unique_id IS 'FK to company_slot';
COMMENT ON COLUMN people.slot_assignment_history.company_unique_id IS 'Company anchor (FK to company_master)';
COMMENT ON COLUMN people.slot_assignment_history.slot_type IS 'Slot type: CEO, HR, CFO, etc.';
COMMENT ON COLUMN people.slot_assignment_history.person_unique_id IS 'Person involved in this event';
COMMENT ON COLUMN people.slot_assignment_history.confidence_score IS 'Confidence score at time of event';
COMMENT ON COLUMN people.slot_assignment_history.displaced_by_person_id IS 'For DISPLACED: who took the slot';
COMMENT ON COLUMN people.slot_assignment_history.displacement_reason IS 'Why displacement occurred';
COMMENT ON COLUMN people.slot_assignment_history.source_system IS 'Origin: clay, dol, blog, manual, people_pipeline';
COMMENT ON COLUMN people.slot_assignment_history.original_filled_at IS 'When this person originally got the slot';
COMMENT ON COLUMN people.slot_assignment_history.tenure_days IS 'Days held before displacement (computed on DISPLACED)';
COMMENT ON COLUMN people.slot_assignment_history.event_metadata IS 'Extensible JSONB for additional context';

-- ═══════════════════════════════════════════════════════════════════════════
-- MIGRATION COMPLETE
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Summary:
-- * Table: people.slot_assignment_history (append-only, immutable)
-- * Triggers: trg_slot_assignment_history (emits events on company_slot changes)
-- * Immutability: UPDATE/DELETE blocked by trigger
-- * Views: v_slot_tenure_summary, v_recent_slot_displacements
-- * Indexes: 9 indexes for query performance
--
-- Questions Now Answerable:
-- 1. Who held this slot before? -> Query slot_assignment_history WHERE event_type = 'DISPLACED'
-- 2. When were they displaced? -> event_ts column
-- 3. Why were they displaced? -> displacement_reason column
-- 4. What should be re-checked? -> v_recent_slot_displacements view
--
-- ═══════════════════════════════════════════════════════════════════════════
