-- ============================================================================
-- Migration: 0001_create_funnel_schema.sql
-- Description: Create the 'funnel' schema for 4-Funnel GTM System
-- Version: 1.0.0
-- Created: 2025-12-05
-- ============================================================================

-- Create the funnel schema
CREATE SCHEMA IF NOT EXISTS funnel;

-- Add schema comment
COMMENT ON SCHEMA funnel IS '4-Funnel GTM System - Lifecycle state management for Cold, TalentFlow, Warm, and Re-Engagement universes';

-- ============================================================================
-- ENUM TYPES
-- ============================================================================

-- Funnel state enum (lifecycle states)
CREATE TYPE funnel.lifecycle_state AS ENUM (
    'SUSPECT',
    'WARM',
    'TALENTFLOW_WARM',
    'REENGAGEMENT',
    'APPOINTMENT',
    'CLIENT',
    'DISQUALIFIED',
    'UNSUBSCRIBED'
);

-- Event type enum (movement events)
CREATE TYPE funnel.event_type AS ENUM (
    'EVENT_REPLY',
    'EVENT_CLICKS_X2',
    'EVENT_OPENS_X3',
    'EVENT_TALENTFLOW_MOVE',
    'EVENT_BIT_THRESHOLD',
    'EVENT_REENGAGEMENT_TRIGGER',
    'EVENT_APPOINTMENT',
    'EVENT_CLIENT_SIGNED',
    'EVENT_INACTIVITY_30D',
    'EVENT_REENGAGEMENT_EXHAUSTED',
    'EVENT_UNSUBSCRIBE',
    'EVENT_HARD_BOUNCE',
    'EVENT_MANUAL_OVERRIDE'
);

-- TalentFlow signal type enum
CREATE TYPE funnel.talentflow_signal_type AS ENUM (
    'job_change',
    'promotion',
    'lateral',
    'startup',
    'company_change'
);

-- Funnel membership enum
CREATE TYPE funnel.funnel_membership AS ENUM (
    'COLD_UNIVERSE',
    'TALENTFLOW_UNIVERSE',
    'WARM_UNIVERSE',
    'REENGAGEMENT_UNIVERSE'
);

COMMENT ON TYPE funnel.lifecycle_state IS 'Valid lifecycle states for contacts in the 4-Funnel system';
COMMENT ON TYPE funnel.event_type IS 'Events that trigger state transitions';
COMMENT ON TYPE funnel.talentflow_signal_type IS 'Types of TalentFlow movement signals';
COMMENT ON TYPE funnel.funnel_membership IS 'Funnel universe membership categories';
