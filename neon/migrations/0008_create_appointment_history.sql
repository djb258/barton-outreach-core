-- ============================================================================
-- Migration: 0008_create_appointment_history.sql
-- Description: Create appointment_history table (Sales Pipeline: Meetings)
-- Version: 1.0.0
-- Created: 2025-12-05
-- ============================================================================

-- ============================================================================
-- ENUM: Appointment status
-- ============================================================================

CREATE TYPE funnel.appointment_status AS ENUM (
    'scheduled',
    'confirmed',
    'completed',
    'no_show',
    'cancelled',
    'rescheduled'
);

CREATE TYPE funnel.appointment_outcome AS ENUM (
    'positive',        -- Moving forward (proposal, contract)
    'neutral',         -- Need more info, follow-up scheduled
    'negative',        -- Not interested
    'no_decision',     -- Meeting happened but no clear outcome
    'pending'          -- Not yet determined
);

-- ============================================================================
-- TABLE: appointment_history
-- Purpose: Track all meetings/appointments in the sales pipeline
-- State: APPOINTMENT lifecycle state tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS funnel.appointment_history (
    -- Primary key
    appointment_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign keys
    company_id              UUID NOT NULL,
    person_id               UUID NOT NULL,
    suspect_id              UUID REFERENCES funnel.suspect_universe(suspect_id),

    -- Appointment scheduling
    appointment_ts          TIMESTAMPTZ NOT NULL,
    appointment_end_ts      TIMESTAMPTZ,
    timezone                VARCHAR(50) DEFAULT 'America/New_York',

    -- Status tracking
    status                  funnel.appointment_status NOT NULL DEFAULT 'scheduled',
    outcome                 funnel.appointment_outcome NOT NULL DEFAULT 'pending',

    -- Meeting details
    meeting_type            VARCHAR(50),  -- 'intro', 'discovery', 'demo', 'proposal', 'close'
    meeting_format          VARCHAR(50),  -- 'video', 'phone', 'in_person'
    meeting_link            VARCHAR(500),
    meeting_location        VARCHAR(255),

    -- External references
    ac_meeting_id           VARCHAR(100),  -- ActiveCampaign meeting ID
    calendar_event_id       VARCHAR(255),
    calendly_event_id       VARCHAR(255),
    hubspot_meeting_id      VARCHAR(100),

    -- Meeting notes
    meeting_notes           TEXT,
    pre_meeting_notes       TEXT,
    follow_up_notes         TEXT,

    -- Attendees
    attendee_count          INTEGER DEFAULT 1,
    attendee_names          TEXT[],
    attendee_titles         TEXT[],

    -- Source tracking
    source_funnel           funnel.funnel_membership,  -- Which funnel they came from
    booking_source          VARCHAR(100),  -- 'calendly', 'manual', 'reply_booking'
    triggering_event_id     UUID REFERENCES funnel.engagement_events(event_id),

    -- Follow-up tracking
    follow_up_scheduled     BOOLEAN NOT NULL DEFAULT FALSE,
    follow_up_date          DATE,
    next_steps              TEXT,

    -- Reschedule tracking
    reschedule_count        INTEGER NOT NULL DEFAULT 0,
    original_appointment_ts TIMESTAMPTZ,
    reschedule_reason       TEXT,

    -- Lifecycle tracking
    promoted_to_client      BOOLEAN NOT NULL DEFAULT FALSE,
    promoted_at             TIMESTAMPTZ,
    demoted_to_reengagement BOOLEAN NOT NULL DEFAULT FALSE,
    demoted_at              TIMESTAMPTZ,

    -- Metadata
    metadata                JSONB NOT NULL DEFAULT '{}',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_reschedule_count CHECK (reschedule_count >= 0),
    CONSTRAINT chk_appointment_times CHECK (
        appointment_end_ts IS NULL OR appointment_end_ts > appointment_ts
    )
);

-- ============================================================================
-- INDEXES (Aggressive indexing as specified)
-- ============================================================================

-- Primary lookup indexes
CREATE INDEX idx_appt_company_id ON funnel.appointment_history(company_id);
CREATE INDEX idx_appt_person_id ON funnel.appointment_history(person_id);
CREATE INDEX idx_appt_suspect_id ON funnel.appointment_history(suspect_id);

-- Status indexes
CREATE INDEX idx_appt_status ON funnel.appointment_history(status);
CREATE INDEX idx_appt_outcome ON funnel.appointment_history(outcome);

-- Time-based indexes
CREATE INDEX idx_appt_ts ON funnel.appointment_history(appointment_ts);
CREATE INDEX idx_appt_created_at ON funnel.appointment_history(created_at);

-- Composite indexes
CREATE INDEX idx_appt_person_ts ON funnel.appointment_history(person_id, appointment_ts);
CREATE INDEX idx_appt_company_ts ON funnel.appointment_history(company_id, appointment_ts);
CREATE INDEX idx_appt_status_ts ON funnel.appointment_history(status, appointment_ts);
CREATE INDEX idx_appt_outcome_ts ON funnel.appointment_history(outcome, appointment_ts);

-- External ID indexes
CREATE INDEX idx_appt_ac_meeting ON funnel.appointment_history(ac_meeting_id)
    WHERE ac_meeting_id IS NOT NULL;
CREATE INDEX idx_appt_calendar_event ON funnel.appointment_history(calendar_event_id)
    WHERE calendar_event_id IS NOT NULL;
CREATE INDEX idx_appt_calendly ON funnel.appointment_history(calendly_event_id)
    WHERE calendly_event_id IS NOT NULL;
CREATE INDEX idx_appt_hubspot ON funnel.appointment_history(hubspot_meeting_id)
    WHERE hubspot_meeting_id IS NOT NULL;

-- Meeting type indexes
CREATE INDEX idx_appt_meeting_type ON funnel.appointment_history(meeting_type);
CREATE INDEX idx_appt_meeting_format ON funnel.appointment_history(meeting_format);

-- Follow-up indexes
CREATE INDEX idx_appt_follow_up ON funnel.appointment_history(follow_up_scheduled, follow_up_date)
    WHERE follow_up_scheduled = TRUE;

-- Lifecycle tracking indexes
CREATE INDEX idx_appt_promoted ON funnel.appointment_history(promoted_to_client)
    WHERE promoted_to_client = TRUE;
CREATE INDEX idx_appt_demoted ON funnel.appointment_history(demoted_to_reengagement)
    WHERE demoted_to_reengagement = TRUE;

-- Source funnel index
CREATE INDEX idx_appt_source_funnel ON funnel.appointment_history(source_funnel);

-- Upcoming appointments index
CREATE INDEX idx_appt_upcoming ON funnel.appointment_history(appointment_ts)
    WHERE status IN ('scheduled', 'confirmed') AND appointment_ts > NOW();

-- JSONB index
CREATE INDEX idx_appt_metadata ON funnel.appointment_history USING GIN (metadata);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE TRIGGER trg_appt_updated_at
    BEFORE UPDATE ON funnel.appointment_history
    FOR EACH ROW
    EXECUTE FUNCTION funnel.update_suspect_timestamp();

-- Track original appointment time on reschedule
CREATE OR REPLACE FUNCTION funnel.track_reschedule()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.appointment_ts IS DISTINCT FROM NEW.appointment_ts THEN
        IF NEW.original_appointment_ts IS NULL THEN
            NEW.original_appointment_ts = OLD.appointment_ts;
        END IF;
        NEW.reschedule_count = OLD.reschedule_count + 1;
        NEW.status = 'rescheduled';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_appt_reschedule
    BEFORE UPDATE ON funnel.appointment_history
    FOR EACH ROW
    EXECUTE FUNCTION funnel.track_reschedule();

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Upcoming appointments
CREATE OR REPLACE VIEW funnel.v_upcoming_appointments AS
SELECT
    appointment_id,
    company_id,
    person_id,
    appointment_ts,
    status,
    meeting_type,
    meeting_format,
    meeting_link,
    pre_meeting_notes
FROM funnel.appointment_history
WHERE status IN ('scheduled', 'confirmed')
  AND appointment_ts > NOW()
ORDER BY appointment_ts ASC;

-- Appointment conversion rates
CREATE OR REPLACE VIEW funnel.v_appointment_outcomes AS
SELECT
    source_funnel,
    meeting_type,
    COUNT(*) as total_appointments,
    COUNT(*) FILTER (WHERE outcome = 'positive') as positive_outcomes,
    COUNT(*) FILTER (WHERE outcome = 'negative') as negative_outcomes,
    COUNT(*) FILTER (WHERE status = 'no_show') as no_shows,
    COUNT(*) FILTER (WHERE promoted_to_client = TRUE) as conversions,
    ROUND(100.0 * COUNT(*) FILTER (WHERE promoted_to_client = TRUE) / NULLIF(COUNT(*), 0), 2) as conversion_rate
FROM funnel.appointment_history
WHERE status IN ('completed', 'no_show')
GROUP BY source_funnel, meeting_type
ORDER BY total_appointments DESC;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE funnel.appointment_history IS 'Sales pipeline meeting tracking. APPOINTMENT lifecycle state management.';
COMMENT ON COLUMN funnel.appointment_history.appointment_id IS 'Primary key - unique identifier for each appointment';
COMMENT ON COLUMN funnel.appointment_history.appointment_ts IS 'Scheduled date/time of the meeting';
COMMENT ON COLUMN funnel.appointment_history.status IS 'Current appointment status';
COMMENT ON COLUMN funnel.appointment_history.outcome IS 'Meeting outcome (after completion)';
COMMENT ON COLUMN funnel.appointment_history.ac_meeting_id IS 'ActiveCampaign meeting/deal ID';
COMMENT ON COLUMN funnel.appointment_history.source_funnel IS 'Which funnel the contact came from before APPOINTMENT';
COMMENT ON COLUMN funnel.appointment_history.reschedule_count IS 'Number of times this appointment has been rescheduled';
COMMENT ON VIEW funnel.v_upcoming_appointments IS 'Upcoming scheduled and confirmed appointments';
COMMENT ON VIEW funnel.v_appointment_outcomes IS 'Appointment outcome and conversion rate analysis';
