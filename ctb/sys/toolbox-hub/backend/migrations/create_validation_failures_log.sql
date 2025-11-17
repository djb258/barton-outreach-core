-- Migration: Create validation_failures_log table
-- Purpose: Store validation failures from WV pipeline for Google Sheets export
-- Date: 2025-11-17

CREATE TABLE IF NOT EXISTS marketing.validation_failures_log (
    id SERIAL PRIMARY KEY,
    company_id TEXT,
    person_id TEXT,
    company_name TEXT,
    person_name TEXT,
    fail_reason TEXT NOT NULL,
    state TEXT,
    validation_timestamp TIMESTAMPTZ,
    pipeline_id TEXT NOT NULL,
    failure_type TEXT NOT NULL CHECK (failure_type IN ('company', 'person')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    exported_to_sheets BOOLEAN DEFAULT FALSE,
    exported_at TIMESTAMPTZ,
    UNIQUE(company_id, pipeline_id, failure_type),
    UNIQUE(person_id, pipeline_id, failure_type)
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_validation_failures_log_pipeline_id
    ON marketing.validation_failures_log(pipeline_id);

CREATE INDEX IF NOT EXISTS idx_validation_failures_log_failure_type
    ON marketing.validation_failures_log(failure_type);

CREATE INDEX IF NOT EXISTS idx_validation_failures_log_exported
    ON marketing.validation_failures_log(exported_to_sheets);

CREATE INDEX IF NOT EXISTS idx_validation_failures_log_created_at
    ON marketing.validation_failures_log(created_at DESC);

-- Add comment
COMMENT ON TABLE marketing.validation_failures_log IS 'Stores validation failures from outreach pipeline for tracking and Google Sheets export';

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON marketing.validation_failures_log TO "Marketing DB_owner";
GRANT USAGE, SELECT ON SEQUENCE marketing.validation_failures_log_id_seq TO "Marketing DB_owner";
