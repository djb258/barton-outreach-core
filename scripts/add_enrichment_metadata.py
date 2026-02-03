#!/usr/bin/env python3
"""
Add AI-ready metadata to enrichment tables:
- Column descriptions (COMMENT ON COLUMN)
- Create column registry table for AI reference
- Document formats and constraints
"""
import psycopg2
import os

def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    # ========================================
    # 1. CREATE COLUMN REGISTRY TABLE
    # ========================================
    print('Creating column registry table...')
    cur.execute("""
        CREATE TABLE IF NOT EXISTS enrichment.column_registry (
            id SERIAL PRIMARY KEY,
            table_name VARCHAR(100) NOT NULL,
            column_name VARCHAR(100) NOT NULL,
            column_id VARCHAR(50) NOT NULL UNIQUE,
            data_type VARCHAR(50) NOT NULL,
            format_pattern VARCHAR(255),
            description TEXT NOT NULL,
            example_value TEXT,
            is_required BOOLEAN DEFAULT FALSE,
            is_pii BOOLEAN DEFAULT FALSE,
            ai_usage_hint TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(table_name, column_name)
        )
    """)
    conn.commit()
    
    # ========================================
    # 2. HUNTER_COMPANY COLUMN DEFINITIONS
    # ========================================
    hunter_company_columns = [
        ('id', 'HC_ID', 'integer', 'auto-increment', 'Primary key, auto-generated sequential ID', '12345', True, False, 'Use for joins, not for display'),
        ('domain', 'HC_DOMAIN', 'varchar(255)', 'lowercase, no protocol', 'Company website domain - primary identifier', 'acme.com', True, False, 'Primary lookup key for company matching'),
        ('organization', 'HC_ORG_NAME', 'varchar(500)', 'title case', 'Legal or common company name from Hunter', 'Acme Corporation', False, False, 'Use for display and fuzzy matching'),
        ('headcount', 'HC_HEADCOUNT_RAW', 'varchar(50)', 'range format: X-Y', 'Employee count range as string', '51-200', False, False, 'Use headcount_min/max for filtering'),
        ('country', 'HC_COUNTRY', 'varchar(10)', 'ISO 3166-1 alpha-2', 'Two-letter country code', 'US', False, False, 'Filter by geography'),
        ('state', 'HC_STATE', 'varchar(50)', 'US state abbreviation or full name', 'State/province/region', 'PA', False, False, 'Key for regional targeting'),
        ('city', 'HC_CITY', 'varchar(100)', 'title case', 'City name', 'Pittsburgh', False, False, 'Local market targeting'),
        ('postal_code', 'HC_POSTAL', 'varchar(20)', 'varies by country', 'ZIP or postal code', '15213', False, False, 'Precision geo-targeting'),
        ('street', 'HC_STREET', 'varchar(255)', 'street address format', 'Street address line', '123 Main St', False, False, 'Full address construction'),
        ('email_pattern', 'HC_EMAIL_PATTERN', 'varchar(100)', '{first}.{last} format', 'Email pattern for generating addresses', '{first}.{last}', False, False, 'Critical for email generation'),
        ('company_type', 'HC_COMPANY_TYPE', 'varchar(100)', 'Hunter classification', 'Company ownership type', 'privately held', False, False, 'ICP filtering'),
        ('industry', 'HC_INDUSTRY', 'varchar(255)', 'Hunter industry taxonomy', 'Industry classification from Hunter', 'Construction', False, False, 'Primary ICP signal'),
        ('enriched_at', 'HC_ENRICHED_TS', 'timestamp', 'ISO 8601', 'When Hunter data was fetched', '2026-02-03T12:00:00Z', False, False, 'Data freshness indicator'),
        ('created_at', 'HC_CREATED_TS', 'timestamp', 'ISO 8601', 'Record creation timestamp', '2026-02-03T12:00:00Z', True, False, 'Audit trail'),
        ('updated_at', 'HC_UPDATED_TS', 'timestamp', 'ISO 8601', 'Last update timestamp', '2026-02-03T12:00:00Z', True, False, 'Audit trail'),
        ('company_embedding', 'HC_EMBEDDING', 'vector(1536)', 'OpenAI ada-002 format', 'Semantic embedding for similarity search', '[0.1, 0.2, ...]', False, False, 'Semantic search and clustering'),
        ('industry_normalized', 'HC_INDUSTRY_NORM', 'varchar(100)', 'standardized taxonomy', 'Cleaned/mapped industry category', 'Construction', False, False, 'Consistent ICP filtering'),
        ('headcount_min', 'HC_HEADCOUNT_MIN', 'integer', 'positive integer', 'Minimum employee count from range', '51', False, False, 'Filter: headcount_min >= X'),
        ('headcount_max', 'HC_HEADCOUNT_MAX', 'integer', 'positive integer', 'Maximum employee count from range', '200', False, False, 'Filter: headcount_max <= Y'),
        ('location_full', 'HC_LOCATION_FULL', 'text', 'concatenated address', 'Full address string for display', '123 Main St, Pittsburgh, PA 15213, US', False, False, 'Display and geocoding'),
        ('data_quality_score', 'HC_QUALITY', 'decimal(3,2)', '0.00 to 1.00', 'Composite data completeness score', '0.85', False, False, 'Prioritize high-quality records'),
        ('tags', 'HC_TAGS', 'text[]', 'array of strings', 'Custom classification tags', '["target", "priority"]', False, False, 'Custom filtering and segmentation'),
        ('source', 'HC_SOURCE', 'varchar(50)', 'source identifier', 'Data source system', 'hunter', True, False, 'Data provenance'),
        ('company_unique_id', 'HC_CT_ID', 'varchar(50)', 'UUID format', 'Link to company_target.company_unique_id', 'a1b2c3d4-...', False, False, 'Join to company_target'),
        ('outreach_id', 'HC_OUTREACH_ID', 'uuid', 'UUID format', 'Link to outreach.outreach.outreach_id', 'a1b2c3d4-...', False, False, 'Primary foreign key to outreach'),
    ]
    
    # ========================================
    # 3. HUNTER_CONTACT COLUMN DEFINITIONS  
    # ========================================
    hunter_contact_columns = [
        ('id', 'HCT_ID', 'integer', 'auto-increment', 'Primary key, auto-generated sequential ID', '12345', True, False, 'Use for joins, not for display'),
        ('domain', 'HCT_DOMAIN', 'varchar(255)', 'lowercase, no protocol', 'Company domain this contact belongs to', 'acme.com', True, False, 'Join to hunter_company'),
        ('email', 'HCT_EMAIL', 'varchar(255)', 'valid email format', 'Verified email address from Hunter', 'john.smith@acme.com', False, True, 'Primary contact method - PII'),
        ('first_name', 'HCT_FIRST_NAME', 'varchar(100)', 'title case', 'Contact first name', 'John', False, True, 'Personalization - PII'),
        ('last_name', 'HCT_LAST_NAME', 'varchar(100)', 'title case', 'Contact last name', 'Smith', False, True, 'Personalization - PII'),
        ('department', 'HCT_DEPT_RAW', 'varchar(100)', 'Hunter department taxonomy', 'Department from Hunter', 'Executive', False, False, 'Raw department classification'),
        ('job_title', 'HCT_TITLE_RAW', 'varchar(255)', 'free text', 'Job title from Hunter', 'Chief Executive Officer', False, False, 'Raw title for display'),
        ('position_raw', 'HCT_POSITION_RAW', 'varchar(500)', 'free text', 'Full position description from source', 'CEO and Founder', False, False, 'Extended title context'),
        ('linkedin_url', 'HCT_LINKEDIN', 'varchar(500)', 'https://linkedin.com/in/...', 'LinkedIn profile URL', 'https://linkedin.com/in/johnsmith', False, True, 'Multi-channel outreach - PII'),
        ('twitter_handle', 'HCT_TWITTER', 'varchar(100)', '@handle format', 'Twitter/X handle', '@johnsmith', False, True, 'Social engagement - PII'),
        ('phone_number', 'HCT_PHONE', 'varchar(50)', 'E.164 or formatted', 'Phone number if available', '+1-412-555-1234', False, True, 'Direct contact - PII'),
        ('confidence_score', 'HCT_CONFIDENCE', 'integer', '0-100', 'Hunter email confidence score', '95', False, False, 'Filter: confidence_score >= 80'),
        ('email_type', 'HCT_EMAIL_TYPE', 'varchar(20)', 'personal|generic', 'Whether email is personal or generic', 'personal', False, False, 'Filter out generic emails'),
        ('num_sources', 'HCT_NUM_SOURCES', 'integer', 'positive integer', 'Number of sources confirming this email', '5', False, False, 'Higher = more reliable'),
        ('created_at', 'HCT_CREATED_TS', 'timestamp', 'ISO 8601', 'Record creation timestamp', '2026-02-03T12:00:00Z', True, False, 'Audit trail'),
        ('contact_embedding', 'HCT_EMBEDDING', 'vector(1536)', 'OpenAI ada-002 format', 'Semantic embedding for similarity search', '[0.1, 0.2, ...]', False, False, 'Find similar contacts'),
        ('title_normalized', 'HCT_TITLE_NORM', 'varchar(100)', 'standardized title', 'Normalized job title', 'CEO', False, False, 'Consistent title filtering'),
        ('seniority_level', 'HCT_SENIORITY', 'varchar(50)', 'enum: C-Level/Owner|VP|Director|Manager|Senior|Junior|Individual Contributor', 'Seniority classification', 'C-Level/Owner', False, False, 'Key targeting filter'),
        ('department_normalized', 'HCT_DEPT_NORM', 'varchar(50)', 'standardized taxonomy', 'Normalized department', 'Executive', False, False, 'Consistent dept filtering'),
        ('is_decision_maker', 'HCT_IS_DM', 'boolean', 'true/false', 'Whether contact is a decision maker', 'true', False, False, 'Primary targeting flag'),
        ('full_name', 'HCT_FULL_NAME', 'varchar(200)', 'First Last format', 'Combined full name', 'John Smith', False, True, 'Display and personalization - PII'),
        ('email_verified', 'HCT_EMAIL_VERIFIED', 'boolean', 'true/false', 'Hunter verification status', 'true', False, False, 'All Hunter emails are verified'),
        ('data_quality_score', 'HCT_QUALITY', 'decimal(3,2)', '0.00 to 1.00', 'Composite data completeness score', '0.92', False, False, 'Prioritize complete records'),
        ('outreach_priority', 'HCT_PRIORITY', 'integer', '1-5 (5=highest)', 'Computed outreach priority', '5', False, False, 'Sort by priority DESC'),
        ('tags', 'HCT_TAGS', 'text[]', 'array of strings', 'Custom classification tags', '["hot-lead", "construction"]', False, False, 'Custom segmentation'),
        ('source', 'HCT_SOURCE', 'varchar(50)', 'source identifier', 'Data source system', 'hunter', True, False, 'Data provenance'),
        ('company_unique_id', 'HCT_CT_ID', 'varchar(50)', 'UUID format', 'Link to company_target.company_unique_id', 'a1b2c3d4-...', False, False, 'Join to company_target'),
        ('outreach_id', 'HCT_OUTREACH_ID', 'uuid', 'UUID format', 'Link to outreach.outreach.outreach_id', 'a1b2c3d4-...', False, False, 'Primary foreign key to outreach'),
    ]
    
    # ========================================
    # 4. INSERT COLUMN DEFINITIONS
    # ========================================
    print('Populating column registry...')
    
    # Clear existing
    cur.execute("DELETE FROM enrichment.column_registry WHERE table_name IN ('hunter_company', 'hunter_contact')")
    
    # Insert hunter_company columns
    for col in hunter_company_columns:
        col_name, col_id, dtype, fmt, desc, example, required, pii, hint = col
        cur.execute("""
            INSERT INTO enrichment.column_registry 
            (table_name, column_name, column_id, data_type, format_pattern, description, example_value, is_required, is_pii, ai_usage_hint)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (table_name, column_name) DO UPDATE SET
                column_id = EXCLUDED.column_id,
                data_type = EXCLUDED.data_type,
                format_pattern = EXCLUDED.format_pattern,
                description = EXCLUDED.description,
                example_value = EXCLUDED.example_value,
                is_required = EXCLUDED.is_required,
                is_pii = EXCLUDED.is_pii,
                ai_usage_hint = EXCLUDED.ai_usage_hint
        """, ('hunter_company', col_name, col_id, dtype, fmt, desc, example, required, pii, hint))
    
    # Insert hunter_contact columns
    for col in hunter_contact_columns:
        col_name, col_id, dtype, fmt, desc, example, required, pii, hint = col
        cur.execute("""
            INSERT INTO enrichment.column_registry 
            (table_name, column_name, column_id, data_type, format_pattern, description, example_value, is_required, is_pii, ai_usage_hint)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (table_name, column_name) DO UPDATE SET
                column_id = EXCLUDED.column_id,
                data_type = EXCLUDED.data_type,
                format_pattern = EXCLUDED.format_pattern,
                description = EXCLUDED.description,
                example_value = EXCLUDED.example_value,
                is_required = EXCLUDED.is_required,
                is_pii = EXCLUDED.is_pii,
                ai_usage_hint = EXCLUDED.ai_usage_hint
        """, ('hunter_contact', col_name, col_id, dtype, fmt, desc, example, required, pii, hint))
    
    conn.commit()
    print(f'  Registered {len(hunter_company_columns)} hunter_company columns')
    print(f'  Registered {len(hunter_contact_columns)} hunter_contact columns')
    
    # ========================================
    # 5. ADD POSTGRES COLUMN COMMENTS
    # ========================================
    print('\nAdding PostgreSQL column comments...')
    
    for col in hunter_company_columns:
        col_name, col_id, dtype, fmt, desc, example, required, pii, hint = col
        comment = f"{col_id}: {desc}. Format: {fmt}. Example: {example}"
        cur.execute(f"COMMENT ON COLUMN enrichment.hunter_company.{col_name} IS %s", (comment,))
    
    for col in hunter_contact_columns:
        col_name, col_id, dtype, fmt, desc, example, required, pii, hint = col
        comment = f"{col_id}: {desc}. Format: {fmt}. Example: {example}"
        cur.execute(f"COMMENT ON COLUMN enrichment.hunter_contact.{col_name} IS %s", (comment,))
    
    # Table-level comments
    cur.execute("""
        COMMENT ON TABLE enrichment.hunter_company IS 
        'Company-level enrichment data from Hunter.io. One row per domain. Contains org info, location, industry, email patterns. Primary key: domain. Links to outreach via outreach_id.'
    """)
    
    cur.execute("""
        COMMENT ON TABLE enrichment.hunter_contact IS 
        'Contact-level enrichment data from Hunter.io. Multiple contacts per domain. Contains verified emails, names, titles, LinkedIn. Primary key: id. Links to hunter_company via domain, to outreach via outreach_id.'
    """)
    
    conn.commit()
    print('  Added comments to all columns')
    
    # ========================================
    # 6. CREATE AI-FRIENDLY VIEW
    # ========================================
    print('\nCreating AI-friendly metadata view...')
    
    cur.execute("""
        CREATE OR REPLACE VIEW enrichment.v_column_metadata AS
        SELECT 
            table_name,
            column_name,
            column_id,
            data_type,
            format_pattern,
            description,
            example_value,
            is_required,
            is_pii,
            ai_usage_hint,
            CASE 
                WHEN is_pii THEN 'SENSITIVE - handle with care'
                WHEN is_required THEN 'REQUIRED field'
                ELSE 'OPTIONAL field'
            END as field_status
        FROM enrichment.column_registry
        ORDER BY table_name, column_id
    """)
    
    conn.commit()
    
    # ========================================
    # 7. SUMMARY
    # ========================================
    print('\n' + '='*60)
    print('AI-READY METADATA COMPLETE')
    print('='*60)
    
    cur.execute("SELECT COUNT(*) FROM enrichment.column_registry")
    print(f'Total columns registered: {cur.fetchone()[0]}')
    
    cur.execute("SELECT COUNT(*) FROM enrichment.column_registry WHERE is_pii = TRUE")
    print(f'PII columns flagged: {cur.fetchone()[0]}')
    
    cur.execute("SELECT COUNT(*) FROM enrichment.column_registry WHERE is_required = TRUE")
    print(f'Required columns: {cur.fetchone()[0]}')
    
    print('\nSample from column registry:')
    cur.execute("""
        SELECT column_id, column_name, description, ai_usage_hint 
        FROM enrichment.column_registry 
        WHERE table_name = 'hunter_contact' 
        AND column_id IN ('HCT_EMAIL', 'HCT_SENIORITY', 'HCT_IS_DM', 'HCT_PRIORITY')
    """)
    for row in cur.fetchall():
        print(f'  {row[0]}: {row[1]}')
        print(f'    Desc: {row[2]}')
        print(f'    Hint: {row[3]}')
        print()
    
    conn.close()
    print('Done!')

if __name__ == '__main__':
    main()
