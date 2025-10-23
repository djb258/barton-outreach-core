-- ─────────────────────────────────────────────
-- 📁 CTB Classification Metadata
-- ─────────────────────────────────────────────
-- CTB Branch: data/migrations
-- Barton ID: 05.01.02
-- Unique ID: CTB-F5FF28EB
-- Blueprint Hash:
-- Last Updated: 2025-10-23
-- Enforcement: HEIR
-- ─────────────────────────────────────────────


-- Updated At Trigger Function
CREATE OR REPLACE FUNCTION trigger_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Barton ID Generator Function
-- Generates format: NN.NN.NN.NN.NNNNN.NNN
CREATE OR REPLACE FUNCTION generate_barton_id()
RETURNS VARCHAR(23) AS $$
DECLARE
    segment1 VARCHAR(2);
    segment2 VARCHAR(2);
    segment3 VARCHAR(2);
    segment4 VARCHAR(2);
    segment5 VARCHAR(5);
    segment6 VARCHAR(3);
BEGIN
    -- Use timestamp and random for uniqueness
    segment1 := LPAD((EXTRACT(EPOCH FROM NOW())::BIGINT % 100)::TEXT, 2, '0');
    segment2 := LPAD((EXTRACT(MICROSECONDS FROM NOW()) % 100)::TEXT, 2, '0');
    segment3 := LPAD((RANDOM() * 100)::INT::TEXT, 2, '0');
    segment4 := '07'; -- Fixed segment for database records
    segment5 := LPAD((RANDOM() * 100000)::INT::TEXT, 5, '0');
    segment6 := LPAD((RANDOM() * 1000)::INT::TEXT, 3, '0');

    RETURN segment1 || '.' || segment2 || '.' || segment3 || '.' || segment4 || '.' || segment5 || '.' || segment6;
END;
$$ LANGUAGE plpgsql;

-- Barton Doctrine Migration
-- File: create_schema_registry
-- Purpose: Database schema migration with Barton ID compliance
-- Requirements: All tables must have unique_id (Barton ID) and audit columns
-- MCP: All access via Composio bridge, no direct connections

/**
 * Schema Registry Table Migration
 * Creates the shq.schema_registry table for storing database metadata
 * Part of the Schema Registry and Visualization system
 */

-- Create shq schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS shq;

-- Create the main schema registry table
CREATE TABLE IF NOT EXISTS shq.schema_registry (id SERIAL PRIMARY KEY,
    schema_name TEXT NOT NULL,
    table_name TEXT NOT NULL,
    column_name TEXT NOT NULL,
    data_type TEXT NOT NULL,
    is_nullable BOOLEAN DEFAULT true,
    column_default TEXT,
    max_length INTEGER,
    numeric_precision INTEGER,
    numeric_scale INTEGER,
    ordinal_position INTEGER,
    is_primary_key BOOLEAN DEFAULT false,
    is_foreign_key BOOLEAN DEFAULT false,
    constraint_name TEXT,
    table_type TEXT DEFAULT 'BASE TABLE',
    doctrine_tag JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Ensure unique constraint for schema/table/column combination
    UNIQUE(schema_name, table_name, column_name),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW());

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_schema_registry_schema_table
    ON shq.schema_registry(schema_name, table_name);

CREATE INDEX IF NOT EXISTS idx_schema_registry_doctrine_tag
    ON shq.schema_registry USING GIN(doctrine_tag);

CREATE INDEX IF NOT EXISTS idx_schema_registry_updated
    ON shq.schema_registry(last_updated);

-- Create relationships tracking table
CREATE TABLE IF NOT EXISTS shq.table_relationships (id SERIAL PRIMARY KEY,
    source_schema TEXT NOT NULL,
    source_table TEXT NOT NULL,
    target_schema TEXT NOT NULL,
    target_table TEXT NOT NULL,
    relationship_type TEXT NOT NULL, -- 'promotion', 'foreign_key', 'join', 'reference'
    relationship_data JSONB DEFAULT '{}',
    confidence_score NUMERIC(3,2) DEFAULT 1.0,
    created_by TEXT DEFAULT 'system',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Ensure unique constraint for relationship pairs
    UNIQUE(source_schema, source_table, target_schema, target_table, relationship_type),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW());

-- Create index for relationships
CREATE INDEX IF NOT EXISTS idx_table_relationships_source
    ON shq.table_relationships(source_schema, source_table);

CREATE INDEX IF NOT EXISTS idx_table_relationships_target
    ON shq.table_relationships(target_schema, target_table);

CREATE INDEX IF NOT EXISTS idx_table_relationships_type
    ON shq.table_relationships(relationship_type);

-- Create audit log for schema changes
CREATE TABLE IF NOT EXISTS shq.schema_audit_log (id SERIAL PRIMARY KEY,
    operation TEXT NOT NULL, -- 'scan', 'sync', 'update', 'relationship_add'
    schema_name TEXT,
    table_name TEXT,
    column_name TEXT,
    old_data JSONB,
    new_data JSONB,
    change_summary TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by TEXT DEFAULT 'system',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW());

-- Create index for audit log
CREATE INDEX IF NOT EXISTS idx_schema_audit_log_operation
    ON shq.schema_audit_log(operation, created_at);

-- Create trigger function for automatic last_updated
CREATE OR REPLACE FUNCTION update_schema_registry_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for schema registry
DROP TRIGGER IF EXISTS trigger_update_schema_registry_timestamp ON shq.schema_registry;
CREATE TRIGGER trigger_update_schema_registry_timestamp
    BEFORE UPDATE ON shq.schema_registry
    FOR EACH ROW
    EXECUTE FUNCTION update_schema_registry_timestamp();

-- Create trigger function for relationships timestamp
CREATE OR REPLACE FUNCTION update_table_relationships_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for relationships
DROP TRIGGER IF EXISTS trigger_update_table_relationships_timestamp ON shq.table_relationships;
CREATE TRIGGER trigger_update_table_relationships_timestamp
    BEFORE UPDATE ON shq.table_relationships
    FOR EACH ROW
    EXECUTE FUNCTION update_table_relationships_timestamp();

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA shq TO your_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA shq TO your_user;

-- Insert initial metadata about the registry itself
INSERT INTO shq.schema_audit_log (operation, schema_name, table_name, change_summary, metadata)
VALUES (
    'create_registry',
    'shq',
    'schema_registry',
    'Created schema registry and visualization system tables',
    '{"altitude": 10000, "doctrine": "STAMPED", "version": "1.0"}'::jsonb
) ON CONFLICT DO NOTHING;
-- Trigger for IF
CREATE TRIGGER trigger_IF_updated_at
    BEFORE UPDATE ON IF
    FOR EACH ROW
    EXECUTE FUNCTION trigger_updated_at();

-- Trigger for IF
CREATE TRIGGER trigger_IF_updated_at
    BEFORE UPDATE ON IF
    FOR EACH ROW
    EXECUTE FUNCTION trigger_updated_at();

-- Trigger for IF
CREATE TRIGGER trigger_IF_updated_at
    BEFORE UPDATE ON IF
    FOR EACH ROW
    EXECUTE FUNCTION trigger_updated_at();
