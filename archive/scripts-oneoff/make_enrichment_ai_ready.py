#!/usr/bin/env python3
"""
Make enrichment tables AI-ready with proper structure, 
embeddings support, normalized fields, and clean data.
"""
import psycopg2
import os

def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    # Check for vector extension
    cur.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
    has_vector = cur.fetchone()[0]
    print(f'pgvector extension available: {has_vector}')
    
    if not has_vector:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        print('Created vector extension')
    
    # ========================================
    # ENHANCED COMPANY TABLE
    # ========================================
    print('\n--- Upgrading hunter_company ---')
    
    # Add AI-ready columns
    alter_statements = [
        "ALTER TABLE enrichment.hunter_company ADD COLUMN IF NOT EXISTS company_embedding vector(1536)",
        "ALTER TABLE enrichment.hunter_company ADD COLUMN IF NOT EXISTS industry_normalized VARCHAR(100)",
        "ALTER TABLE enrichment.hunter_company ADD COLUMN IF NOT EXISTS headcount_min INTEGER",
        "ALTER TABLE enrichment.hunter_company ADD COLUMN IF NOT EXISTS headcount_max INTEGER",
        "ALTER TABLE enrichment.hunter_company ADD COLUMN IF NOT EXISTS location_full TEXT",
        "ALTER TABLE enrichment.hunter_company ADD COLUMN IF NOT EXISTS data_quality_score DECIMAL(3,2)",
        "ALTER TABLE enrichment.hunter_company ADD COLUMN IF NOT EXISTS tags TEXT[]",
        "ALTER TABLE enrichment.hunter_company ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'hunter'",
    ]
    
    for stmt in alter_statements:
        try:
            cur.execute(stmt)
        except Exception as e:
            print(f'  Note: {e}')
    
    # ========================================
    # ENHANCED CONTACT TABLE
    # ========================================
    print('--- Upgrading hunter_contact ---')
    
    alter_statements = [
        "ALTER TABLE enrichment.hunter_contact ADD COLUMN IF NOT EXISTS contact_embedding vector(1536)",
        "ALTER TABLE enrichment.hunter_contact ADD COLUMN IF NOT EXISTS title_normalized VARCHAR(100)",
        "ALTER TABLE enrichment.hunter_contact ADD COLUMN IF NOT EXISTS seniority_level VARCHAR(50)",
        "ALTER TABLE enrichment.hunter_contact ADD COLUMN IF NOT EXISTS department_normalized VARCHAR(50)",
        "ALTER TABLE enrichment.hunter_contact ADD COLUMN IF NOT EXISTS is_decision_maker BOOLEAN DEFAULT FALSE",
        "ALTER TABLE enrichment.hunter_contact ADD COLUMN IF NOT EXISTS full_name VARCHAR(200)",
        "ALTER TABLE enrichment.hunter_contact ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT TRUE",
        "ALTER TABLE enrichment.hunter_contact ADD COLUMN IF NOT EXISTS data_quality_score DECIMAL(3,2)",
        "ALTER TABLE enrichment.hunter_contact ADD COLUMN IF NOT EXISTS outreach_priority INTEGER",
        "ALTER TABLE enrichment.hunter_contact ADD COLUMN IF NOT EXISTS tags TEXT[]",
        "ALTER TABLE enrichment.hunter_contact ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'hunter'",
    ]
    
    for stmt in alter_statements:
        try:
            cur.execute(stmt)
        except Exception as e:
            print(f'  Note: {e}')
    
    conn.commit()
    
    # ========================================
    # NORMALIZE DATA
    # ========================================
    print('\n--- Normalizing data ---')
    
    # Populate full_name
    cur.execute("""
        UPDATE enrichment.hunter_contact
        SET full_name = TRIM(COALESCE(first_name, '') || ' ' || COALESCE(last_name, ''))
        WHERE full_name IS NULL
    """)
    print(f'  Set full_name: {cur.rowcount:,} rows')
    
    # Normalize headcount to min/max
    cur.execute("""
        UPDATE enrichment.hunter_company
        SET headcount_min = CASE 
            WHEN headcount = '1-10' THEN 1
            WHEN headcount = '11-50' THEN 11
            WHEN headcount = '51-200' THEN 51
            WHEN headcount = '201-500' THEN 201
            WHEN headcount = '501-1000' THEN 501
            WHEN headcount = '1001-5000' THEN 1001
            WHEN headcount = '5001-10000' THEN 5001
            WHEN headcount = '10001+' THEN 10001
            ELSE NULL
        END,
        headcount_max = CASE 
            WHEN headcount = '1-10' THEN 10
            WHEN headcount = '11-50' THEN 50
            WHEN headcount = '51-200' THEN 200
            WHEN headcount = '201-500' THEN 500
            WHEN headcount = '501-1000' THEN 1000
            WHEN headcount = '1001-5000' THEN 5000
            WHEN headcount = '5001-10000' THEN 10000
            WHEN headcount = '10001+' THEN 100000
            ELSE NULL
        END
        WHERE headcount IS NOT NULL
    """)
    print(f'  Normalized headcount: {cur.rowcount:,} rows')
    
    # Build location_full
    cur.execute("""
        UPDATE enrichment.hunter_company
        SET location_full = TRIM(
            COALESCE(street || ', ', '') ||
            COALESCE(city || ', ', '') ||
            COALESCE(state || ' ', '') ||
            COALESCE(postal_code || ', ', '') ||
            COALESCE(country, '')
        )
        WHERE location_full IS NULL
    """)
    print(f'  Built location_full: {cur.rowcount:,} rows')
    
    # ========================================
    # SENIORITY LEVEL CLASSIFICATION
    # ========================================
    print('\n--- Classifying seniority levels ---')
    
    cur.execute("""
        UPDATE enrichment.hunter_contact
        SET seniority_level = CASE
            WHEN LOWER(job_title) ~ '(ceo|cfo|cto|coo|cmo|chief|president|owner|founder|partner)' THEN 'C-Level/Owner'
            WHEN LOWER(job_title) ~ '(vp|vice president|evp|svp)' THEN 'VP'
            WHEN LOWER(job_title) ~ '(director|head of)' THEN 'Director'
            WHEN LOWER(job_title) ~ '(manager|supervisor|lead|principal)' THEN 'Manager'
            WHEN LOWER(job_title) ~ '(senior|sr\.|sr )' THEN 'Senior'
            WHEN LOWER(job_title) ~ '(associate|assistant|junior|jr\.|jr )' THEN 'Junior'
            ELSE 'Individual Contributor'
        END
        WHERE job_title IS NOT NULL AND seniority_level IS NULL
    """)
    print(f'  Classified seniority: {cur.rowcount:,} rows')
    
    # ========================================
    # DECISION MAKER FLAG
    # ========================================
    print('\n--- Flagging decision makers ---')
    
    cur.execute("""
        UPDATE enrichment.hunter_contact
        SET is_decision_maker = TRUE
        WHERE (
            LOWER(job_title) ~ '(ceo|cfo|cto|coo|cmo|chief|president|owner|founder|partner|vp|vice president|director|head of|manager|general manager|operations manager|project manager|construction manager|superintendent|estimator|procurement|purchasing|buyer)'
            OR LOWER(department) IN ('executive', 'management', 'operations', 'purchasing', 'procurement')
        )
        AND job_title IS NOT NULL
    """)
    print(f'  Flagged decision makers: {cur.rowcount:,} rows')
    
    # ========================================
    # DEPARTMENT NORMALIZATION
    # ========================================
    print('\n--- Normalizing departments ---')
    
    cur.execute("""
        UPDATE enrichment.hunter_contact
        SET department_normalized = CASE
            WHEN LOWER(department) ~ '(executive|management|c-level)' THEN 'Executive'
            WHEN LOWER(department) ~ '(sales|business development)' THEN 'Sales'
            WHEN LOWER(department) ~ '(marketing|communications)' THEN 'Marketing'
            WHEN LOWER(department) ~ '(operations|production|manufacturing)' THEN 'Operations'
            WHEN LOWER(department) ~ '(engineering|technical|it|technology)' THEN 'Engineering'
            WHEN LOWER(department) ~ '(finance|accounting)' THEN 'Finance'
            WHEN LOWER(department) ~ '(hr|human resources|people)' THEN 'HR'
            WHEN LOWER(department) ~ '(legal|compliance)' THEN 'Legal'
            WHEN LOWER(department) ~ '(purchasing|procurement|supply)' THEN 'Procurement'
            WHEN LOWER(department) ~ '(project|construction)' THEN 'Project Management'
            ELSE department
        END
        WHERE department IS NOT NULL AND department_normalized IS NULL
    """)
    print(f'  Normalized departments: {cur.rowcount:,} rows')
    
    # ========================================
    # DATA QUALITY SCORE
    # ========================================
    print('\n--- Computing data quality scores ---')
    
    # Contact quality score (0-1)
    cur.execute("""
        UPDATE enrichment.hunter_contact
        SET data_quality_score = (
            (CASE WHEN email IS NOT NULL THEN 0.3 ELSE 0 END) +
            (CASE WHEN first_name IS NOT NULL AND last_name IS NOT NULL THEN 0.2 ELSE 0 END) +
            (CASE WHEN job_title IS NOT NULL THEN 0.2 ELSE 0 END) +
            (CASE WHEN linkedin_url IS NOT NULL THEN 0.15 ELSE 0 END) +
            (CASE WHEN confidence_score >= 90 THEN 0.15 WHEN confidence_score >= 70 THEN 0.10 ELSE 0 END)
        )
    """)
    print(f'  Contact quality scores: {cur.rowcount:,} rows')
    
    # Company quality score (0-1)
    cur.execute("""
        UPDATE enrichment.hunter_company
        SET data_quality_score = (
            (CASE WHEN email_pattern IS NOT NULL THEN 0.25 ELSE 0 END) +
            (CASE WHEN organization IS NOT NULL THEN 0.2 ELSE 0 END) +
            (CASE WHEN industry IS NOT NULL THEN 0.2 ELSE 0 END) +
            (CASE WHEN headcount IS NOT NULL THEN 0.15 ELSE 0 END) +
            (CASE WHEN city IS NOT NULL AND state IS NOT NULL THEN 0.2 ELSE 0 END)
        )
    """)
    print(f'  Company quality scores: {cur.rowcount:,} rows')
    
    # ========================================
    # OUTREACH PRIORITY (1-5, 5 = highest)
    # ========================================
    print('\n--- Computing outreach priority ---')
    
    cur.execute("""
        UPDATE enrichment.hunter_contact
        SET outreach_priority = CASE
            WHEN seniority_level = 'C-Level/Owner' AND is_decision_maker THEN 5
            WHEN seniority_level = 'VP' AND is_decision_maker THEN 5
            WHEN seniority_level = 'Director' AND is_decision_maker THEN 4
            WHEN seniority_level = 'Manager' AND is_decision_maker THEN 4
            WHEN is_decision_maker THEN 3
            WHEN confidence_score >= 90 THEN 3
            WHEN confidence_score >= 70 THEN 2
            ELSE 1
        END
    """)
    print(f'  Set outreach priority: {cur.rowcount:,} rows')
    
    conn.commit()
    
    # ========================================
    # CREATE INDEXES FOR AI/SEARCH
    # ========================================
    print('\n--- Creating indexes ---')
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_hunter_contact_seniority ON enrichment.hunter_contact(seniority_level)",
        "CREATE INDEX IF NOT EXISTS idx_hunter_contact_decision_maker ON enrichment.hunter_contact(is_decision_maker) WHERE is_decision_maker = TRUE",
        "CREATE INDEX IF NOT EXISTS idx_hunter_contact_priority ON enrichment.hunter_contact(outreach_priority DESC)",
        "CREATE INDEX IF NOT EXISTS idx_hunter_contact_quality ON enrichment.hunter_contact(data_quality_score DESC)",
        "CREATE INDEX IF NOT EXISTS idx_hunter_contact_department ON enrichment.hunter_contact(department_normalized)",
        "CREATE INDEX IF NOT EXISTS idx_hunter_company_industry ON enrichment.hunter_company(industry_normalized)",
        "CREATE INDEX IF NOT EXISTS idx_hunter_company_headcount ON enrichment.hunter_company(headcount_min, headcount_max)",
        "CREATE INDEX IF NOT EXISTS idx_hunter_company_quality ON enrichment.hunter_company(data_quality_score DESC)",
    ]
    
    for idx in indexes:
        cur.execute(idx)
        print(f'  Created index')
    
    conn.commit()
    
    # ========================================
    # SUMMARY STATS
    # ========================================
    print('\n' + '='*50)
    print('AI-READY DATABASE SUMMARY')
    print('='*50)
    
    cur.execute("SELECT COUNT(*) FROM enrichment.hunter_contact WHERE is_decision_maker = TRUE")
    print(f'Decision Makers: {cur.fetchone()[0]:,}')
    
    cur.execute("""
        SELECT seniority_level, COUNT(*) 
        FROM enrichment.hunter_contact 
        WHERE seniority_level IS NOT NULL
        GROUP BY seniority_level 
        ORDER BY COUNT(*) DESC
    """)
    print('\nBy Seniority:')
    for level, cnt in cur.fetchall():
        print(f'  {level}: {cnt:,}')
    
    cur.execute("""
        SELECT outreach_priority, COUNT(*) 
        FROM enrichment.hunter_contact 
        WHERE outreach_priority IS NOT NULL
        GROUP BY outreach_priority 
        ORDER BY outreach_priority DESC
    """)
    print('\nBy Outreach Priority:')
    for pri, cnt in cur.fetchall():
        print(f'  Priority {pri}: {cnt:,}')
    
    cur.execute("""
        SELECT AVG(data_quality_score), MIN(data_quality_score), MAX(data_quality_score)
        FROM enrichment.hunter_contact
    """)
    avg, mn, mx = cur.fetchone()
    print(f'\nContact Quality Scores: avg={avg:.2f}, min={mn:.2f}, max={mx:.2f}')
    
    cur.execute("""
        SELECT COUNT(*) FROM enrichment.hunter_contact 
        WHERE data_quality_score >= 0.8
    """)
    print(f'High Quality Contacts (>=0.8): {cur.fetchone()[0]:,}')
    
    conn.close()
    print('\nDone! Database is AI-ready.')

if __name__ == '__main__':
    main()
