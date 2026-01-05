-- ============================================================================
-- Migration: 0010_create_funnel_functions.sql
-- Description: Create helper functions for the 4-Funnel GTM System
-- Version: 1.0.0
-- Created: 2025-12-05
-- ============================================================================

-- ============================================================================
-- FUNCTION: Get current funnel membership for a contact
-- ============================================================================

CREATE OR REPLACE FUNCTION funnel.get_funnel_membership(p_person_id UUID)
RETURNS funnel.funnel_membership AS $$
DECLARE
    v_state funnel.lifecycle_state;
    v_membership funnel.funnel_membership;
BEGIN
    SELECT funnel_state, funnel_membership INTO v_state, v_membership
    FROM funnel.suspect_universe
    WHERE person_id = p_person_id;

    RETURN v_membership;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- FUNCTION: Check if state transition is valid
-- ============================================================================

CREATE OR REPLACE FUNCTION funnel.is_valid_transition(
    p_from_state funnel.lifecycle_state,
    p_to_state funnel.lifecycle_state,
    p_event_type funnel.event_type
)
RETURNS BOOLEAN AS $$
BEGIN
    -- Define valid transitions based on state machine
    RETURN CASE
        -- From SUSPECT
        WHEN p_from_state = 'SUSPECT' AND p_to_state = 'WARM'
            AND p_event_type IN ('EVENT_REPLY', 'EVENT_OPENS_X3', 'EVENT_CLICKS_X2', 'EVENT_BIT_THRESHOLD')
            THEN TRUE
        WHEN p_from_state = 'SUSPECT' AND p_to_state = 'TALENTFLOW_WARM'
            AND p_event_type = 'EVENT_TALENTFLOW_MOVE'
            THEN TRUE

        -- From WARM
        WHEN p_from_state = 'WARM' AND p_to_state = 'APPOINTMENT'
            AND p_event_type = 'EVENT_APPOINTMENT'
            THEN TRUE
        WHEN p_from_state = 'WARM' AND p_to_state = 'TALENTFLOW_WARM'
            AND p_event_type = 'EVENT_TALENTFLOW_MOVE'
            THEN TRUE
        WHEN p_from_state = 'WARM' AND p_to_state = 'REENGAGEMENT'
            AND p_event_type = 'EVENT_INACTIVITY_30D'
            THEN TRUE

        -- From TALENTFLOW_WARM
        WHEN p_from_state = 'TALENTFLOW_WARM' AND p_to_state = 'APPOINTMENT'
            AND p_event_type = 'EVENT_APPOINTMENT'
            THEN TRUE
        WHEN p_from_state = 'TALENTFLOW_WARM' AND p_to_state = 'REENGAGEMENT'
            AND p_event_type = 'EVENT_INACTIVITY_30D'
            THEN TRUE

        -- From REENGAGEMENT
        WHEN p_from_state = 'REENGAGEMENT' AND p_to_state = 'WARM'
            AND p_event_type = 'EVENT_REPLY'
            THEN TRUE
        WHEN p_from_state = 'REENGAGEMENT' AND p_to_state = 'TALENTFLOW_WARM'
            AND p_event_type = 'EVENT_TALENTFLOW_MOVE'
            THEN TRUE
        WHEN p_from_state = 'REENGAGEMENT' AND p_to_state = 'APPOINTMENT'
            AND p_event_type = 'EVENT_APPOINTMENT'
            THEN TRUE
        WHEN p_from_state = 'REENGAGEMENT' AND p_to_state = 'SUSPECT'
            AND p_event_type = 'EVENT_REENGAGEMENT_EXHAUSTED'
            THEN TRUE

        -- From APPOINTMENT
        WHEN p_from_state = 'APPOINTMENT' AND p_to_state = 'CLIENT'
            AND p_event_type = 'EVENT_CLIENT_SIGNED'
            THEN TRUE
        WHEN p_from_state = 'APPOINTMENT' AND p_to_state = 'REENGAGEMENT'
            AND p_event_type = 'EVENT_INACTIVITY_30D'
            THEN TRUE

        -- Manual override always valid
        WHEN p_event_type = 'EVENT_MANUAL_OVERRIDE'
            THEN TRUE

        -- Suppression events
        WHEN p_to_state = 'UNSUBSCRIBED' AND p_event_type = 'EVENT_UNSUBSCRIBE'
            THEN TRUE
        WHEN p_to_state = 'DISQUALIFIED' AND p_event_type = 'EVENT_HARD_BOUNCE'
            THEN TRUE

        ELSE FALSE
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- FUNCTION: Get funnel membership for a state
-- ============================================================================

CREATE OR REPLACE FUNCTION funnel.state_to_funnel(p_state funnel.lifecycle_state)
RETURNS funnel.funnel_membership AS $$
BEGIN
    RETURN CASE p_state
        WHEN 'SUSPECT' THEN 'COLD_UNIVERSE'::funnel.funnel_membership
        WHEN 'WARM' THEN 'WARM_UNIVERSE'::funnel.funnel_membership
        WHEN 'TALENTFLOW_WARM' THEN 'TALENTFLOW_UNIVERSE'::funnel.funnel_membership
        WHEN 'REENGAGEMENT' THEN 'REENGAGEMENT_UNIVERSE'::funnel.funnel_membership
        ELSE NULL
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- FUNCTION: Check if contact is in cooldown
-- ============================================================================

CREATE OR REPLACE FUNCTION funnel.is_in_cooldown(p_person_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    v_cooldown_until TIMESTAMPTZ;
BEGIN
    SELECT cooldown_until INTO v_cooldown_until
    FROM funnel.suspect_universe
    WHERE person_id = p_person_id;

    RETURN v_cooldown_until IS NOT NULL AND v_cooldown_until > NOW();
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- FUNCTION: Count engagement events within window
-- ============================================================================

CREATE OR REPLACE FUNCTION funnel.count_events_in_window(
    p_person_id UUID,
    p_event_type funnel.event_type,
    p_window_days INTEGER DEFAULT 30
)
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM funnel.engagement_events
    WHERE person_id = p_person_id
      AND event_type = p_event_type
      AND event_ts > NOW() - (p_window_days || ' days')::INTERVAL
      AND is_duplicate = FALSE;

    RETURN COALESCE(v_count, 0);
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- FUNCTION: Get latest BIT score for a contact
-- ============================================================================

CREATE OR REPLACE FUNCTION funnel.get_current_bit_score(p_person_id UUID)
RETURNS INTEGER AS $$
DECLARE
    v_score INTEGER;
BEGIN
    SELECT bit_score INTO v_score
    FROM funnel.bit_signal_log
    WHERE person_id = p_person_id
    ORDER BY detected_ts DESC
    LIMIT 1;

    RETURN COALESCE(v_score, 0);
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- FUNCTION: Check if TalentFlow signal is fresh (within 90 days)
-- ============================================================================

CREATE OR REPLACE FUNCTION funnel.has_fresh_talentflow_signal(p_person_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM funnel.talentflow_signal_log
    WHERE person_id = p_person_id
      AND is_expired = FALSE
      AND signal_ts > NOW() - INTERVAL '90 days';

    RETURN v_count > 0;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- FUNCTION: Get contact journey summary
-- ============================================================================

CREATE OR REPLACE FUNCTION funnel.get_journey_summary(p_person_id UUID)
RETURNS TABLE (
    current_state funnel.lifecycle_state,
    current_funnel funnel.funnel_membership,
    first_contact_ts TIMESTAMPTZ,
    total_movements INTEGER,
    total_events INTEGER,
    current_bit_score INTEGER,
    has_talentflow_signal BOOLEAN,
    days_in_funnel INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        su.funnel_state,
        su.funnel_membership,
        su.entered_suspect_ts,
        (SELECT COUNT(*)::INTEGER FROM funnel.prospect_movement pm WHERE pm.person_id = p_person_id),
        (SELECT COUNT(*)::INTEGER FROM funnel.engagement_events ee WHERE ee.person_id = p_person_id),
        su.current_bit_score,
        su.funnel_membership = 'TALENTFLOW_UNIVERSE'::funnel.funnel_membership OR
            EXISTS(SELECT 1 FROM funnel.talentflow_signal_log tfl WHERE tfl.person_id = p_person_id AND tfl.is_expired = FALSE),
        EXTRACT(DAY FROM NOW() - su.last_state_change_ts)::INTEGER
    FROM funnel.suspect_universe su
    WHERE su.person_id = p_person_id;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- FUNCTION: Generate event hash for deduplication
-- ============================================================================

CREATE OR REPLACE FUNCTION funnel.generate_event_hash(
    p_person_id UUID,
    p_event_type funnel.event_type,
    p_source_system VARCHAR,
    p_source_email_id VARCHAR,
    p_event_ts TIMESTAMPTZ
)
RETURNS VARCHAR(64) AS $$
BEGIN
    RETURN encode(
        sha256(
            (p_person_id::TEXT || p_event_type::TEXT ||
             COALESCE(p_source_system, '') ||
             COALESCE(p_source_email_id, '') ||
             DATE_TRUNC('hour', p_event_ts)::TEXT)::BYTEA
        ),
        'hex'
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON FUNCTION funnel.get_funnel_membership IS 'Get current funnel membership for a person';
COMMENT ON FUNCTION funnel.is_valid_transition IS 'Validate if a state transition is allowed per the state machine';
COMMENT ON FUNCTION funnel.state_to_funnel IS 'Map lifecycle state to funnel membership';
COMMENT ON FUNCTION funnel.is_in_cooldown IS 'Check if contact is in cooldown period (anti-thrashing)';
COMMENT ON FUNCTION funnel.count_events_in_window IS 'Count engagement events of a type within a time window';
COMMENT ON FUNCTION funnel.get_current_bit_score IS 'Get latest BIT score for a person';
COMMENT ON FUNCTION funnel.has_fresh_talentflow_signal IS 'Check if person has TalentFlow signal within 90 days';
COMMENT ON FUNCTION funnel.get_journey_summary IS 'Get comprehensive journey summary for a person';
COMMENT ON FUNCTION funnel.generate_event_hash IS 'Generate deduplication hash for engagement events';
