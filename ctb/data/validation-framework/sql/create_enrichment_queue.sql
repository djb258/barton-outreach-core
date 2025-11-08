-- ========================================
-- Enrichment Queue Table
-- ========================================
-- Purpose: Track incomplete records that need agent enrichment
-- After agents enrich → re-validate immediately → move to master if complete

CREATE TABLE IF NOT EXISTS marketing.enrichment_queue (
    id BIGSERIAL PRIMARY KEY,

    -- Entity info
    entity_type TEXT NOT NULL CHECK (entity_type IN ('company', 'person')),
    entity_id TEXT NOT NULL,
    company_name TEXT,
    person_name TEXT,

    -- What's missing
    missing_fields JSONB NOT NULL,
    enrichment_tasks JSONB NOT NULL,  -- Array of tasks for agents

    -- Priority
    priority TEXT NOT NULL CHECK (priority IN ('low', 'medium', 'high', 'critical')),

    -- Status tracking
    status TEXT NOT NULL CHECK (status IN ('pending', 'in_progress', 'complete', 'failed')),
    assigned_agent TEXT,
    attempts INT DEFAULT 0,
    max_attempts INT DEFAULT 3,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Results
    enrichment_results JSONB,
    error_message TEXT,

    -- Batch tracking
    batch_id TEXT,

    -- Unique constraint
    CONSTRAINT unique_entity UNIQUE (entity_type, entity_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_enrichment_queue_status
    ON marketing.enrichment_queue(status);

CREATE INDEX IF NOT EXISTS idx_enrichment_queue_priority
    ON marketing.enrichment_queue(priority, created_at);

CREATE INDEX IF NOT EXISTS idx_enrichment_queue_entity
    ON marketing.enrichment_queue(entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_enrichment_queue_pending
    ON marketing.enrichment_queue(status, priority, created_at)
    WHERE status = 'pending';

-- Auto-update timestamp
CREATE OR REPLACE FUNCTION update_enrichment_queue_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enrichment_queue_updated_at
    BEFORE UPDATE ON marketing.enrichment_queue
    FOR EACH ROW
    EXECUTE FUNCTION update_enrichment_queue_updated_at();

-- Add completeness tracking to company_master
ALTER TABLE marketing.company_master
ADD COLUMN IF NOT EXISTS completeness_validated BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS completeness_validated_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS needs_enrichment BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS enrichment_queued_at TIMESTAMP;

-- Comments
COMMENT ON TABLE marketing.enrichment_queue IS 'Queue of incomplete records for agent enrichment';
COMMENT ON COLUMN marketing.enrichment_queue.missing_fields IS 'JSON array of missing field names';
COMMENT ON COLUMN marketing.enrichment_queue.enrichment_tasks IS 'JSON array of tasks: {task, priority, agent, details}';
COMMENT ON COLUMN marketing.enrichment_queue.priority IS 'Task priority: critical (missing execs) > high (missing core data) > medium > low (nice-to-have)';
COMMENT ON COLUMN marketing.enrichment_queue.status IS 'pending → in_progress → complete/failed';
