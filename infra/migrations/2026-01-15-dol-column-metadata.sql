-- ============================================================================
-- DOL Column Metadata - AI & Human Ready Documentation
--
-- Purpose: Create searchable metadata for all DOL table columns with:
--   - Unique column identifiers
--   - Human-readable descriptions
--   - Data format specifications
--   - Search keywords
--
-- Created: 2026-01-15
-- ============================================================================

-- Enable import mode to allow table creation
SET session dol.import_mode = 'active';

-- ============================================================================
-- 1. CREATE METADATA TABLE
-- ============================================================================

DROP TABLE IF EXISTS dol.column_metadata CASCADE;

CREATE TABLE dol.column_metadata (
    id SERIAL PRIMARY KEY,

    -- Identification
    table_name VARCHAR(50) NOT NULL,
    column_name VARCHAR(100) NOT NULL,
    column_id VARCHAR(100) NOT NULL,  -- Unique identifier: DOL_F5500_SPONSOR_NAME

    -- Documentation
    description TEXT NOT NULL,
    category VARCHAR(50),              -- Sponsor, Admin, Insurance, Welfare, Pension, etc.

    -- Format
    data_type VARCHAR(50) NOT NULL,    -- VARCHAR, NUMERIC, DATE, BOOLEAN, UUID
    format_pattern VARCHAR(100),       -- e.g., "YYYY-MM-DD", "9 digits", "Y/N"
    max_length INTEGER,

    -- Search optimization
    search_keywords TEXT[],            -- Array of search terms
    is_pii BOOLEAN DEFAULT FALSE,      -- Personal Identifiable Information flag
    is_searchable BOOLEAN DEFAULT TRUE,

    -- Examples
    example_values TEXT[],

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(table_name, column_name)
);

-- Create indexes for fast searching
CREATE INDEX idx_col_meta_table ON dol.column_metadata(table_name);
CREATE INDEX idx_col_meta_category ON dol.column_metadata(category);
CREATE INDEX idx_col_meta_keywords ON dol.column_metadata USING GIN(search_keywords);
CREATE INDEX idx_col_meta_column_id ON dol.column_metadata(column_id);

-- Full text search index
CREATE INDEX idx_col_meta_description ON dol.column_metadata
    USING GIN(to_tsvector('english', description));

COMMENT ON TABLE dol.column_metadata IS
    'AI & Human-ready documentation for all DOL table columns. Searchable by keywords, category, or full-text.';

-- ============================================================================
-- 2. CREATE HELPER FUNCTION FOR SEARCHING COLUMNS
-- ============================================================================

CREATE OR REPLACE FUNCTION dol.search_columns(search_term TEXT)
RETURNS TABLE(
    table_name VARCHAR,
    column_name VARCHAR,
    column_id VARCHAR,
    description TEXT,
    category VARCHAR,
    data_type VARCHAR,
    format_pattern VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cm.table_name,
        cm.column_name,
        cm.column_id,
        cm.description,
        cm.category,
        cm.data_type,
        cm.format_pattern
    FROM dol.column_metadata cm
    WHERE
        cm.column_id ILIKE '%' || search_term || '%'
        OR cm.description ILIKE '%' || search_term || '%'
        OR cm.column_name ILIKE '%' || search_term || '%'
        OR search_term = ANY(cm.search_keywords)
        OR to_tsvector('english', cm.description) @@ plainto_tsquery('english', search_term)
    ORDER BY
        CASE WHEN cm.column_id ILIKE '%' || search_term || '%' THEN 0 ELSE 1 END,
        cm.table_name,
        cm.column_name;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION dol.search_columns(TEXT) IS
    'Search DOL columns by keyword, description, or column ID. Returns matching columns with metadata.';

-- ============================================================================
-- 3. CREATE FUNCTION TO GET TABLE SCHEMA
-- ============================================================================

CREATE OR REPLACE FUNCTION dol.get_table_schema(p_table_name TEXT)
RETURNS TABLE(
    column_name VARCHAR,
    column_id VARCHAR,
    description TEXT,
    data_type VARCHAR,
    format_pattern VARCHAR,
    category VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cm.column_name,
        cm.column_id,
        cm.description,
        cm.data_type,
        cm.format_pattern,
        cm.category
    FROM dol.column_metadata cm
    WHERE cm.table_name = p_table_name
    ORDER BY cm.id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION dol.get_table_schema(TEXT) IS
    'Get full schema documentation for a DOL table. Usage: SELECT * FROM dol.get_table_schema(''form_5500'')';

-- Reset import mode
RESET dol.import_mode;
