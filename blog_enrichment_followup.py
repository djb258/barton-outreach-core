"""
Blog Enrichment Data Follow-up Investigation
Additional queries to understand blog data status
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json

def execute_query(query_name, sql):
    """Execute a query in its own connection to avoid transaction issues"""
    conn = psycopg2.connect(
        host=os.getenv('NEON_HOST'),
        database=os.getenv('NEON_DATABASE'),
        user=os.getenv('NEON_USER'),
        password=os.getenv('NEON_PASSWORD'),
        sslmode='require'
    )

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            print('=' * 80)
            print(query_name)
            print('=' * 80)
            cur.execute(sql)
            result = cur.fetchall()

            if len(result) == 0:
                print("No results found")
                return None
            elif len(result) == 1:
                print(json.dumps(dict(result[0]), indent=2, default=str))
                return dict(result[0])
            else:
                for row in result:
                    print(json.dumps(dict(row), indent=2, default=str))
                return [dict(r) for r in result]
    except Exception as e:
        print(f'ERROR: {e}')
        return {'error': str(e)}
    finally:
        conn.close()
        print()

# Check source_type distribution in outreach.blog
execute_query(
    'Q1: outreach.blog source_type distribution',
    """
    SELECT source_type,
           COUNT(*) as count,
           COUNT(source_url) as with_url,
           COUNT(context_summary) as with_summary
    FROM outreach.blog
    GROUP BY source_type
    ORDER BY count DESC;
    """
)

# Check for any non-empty URLs
execute_query(
    'Q2: outreach.blog records with actual URLs',
    """
    SELECT blog_id, outreach_id, source_type, source_url, context_summary, created_at
    FROM outreach.blog
    WHERE source_url IS NOT NULL
      AND source_url != ''
      AND source_url != 'pending'
    LIMIT 10;
    """
)

# Check for any non-null context_summary
execute_query(
    'Q3: outreach.blog records with context_summary',
    """
    SELECT blog_id, outreach_id, source_type, source_url, context_summary, created_at
    FROM outreach.blog
    WHERE context_summary IS NOT NULL
    LIMIT 10;
    """
)

# Check total outreach.blog vs outreach.outreach alignment
execute_query(
    'Q4: outreach.blog vs outreach.outreach alignment',
    """
    SELECT
        (SELECT COUNT(*) FROM outreach.outreach) as total_outreach,
        (SELECT COUNT(*) FROM outreach.blog) as total_blog,
        (SELECT COUNT(DISTINCT outreach_id) FROM outreach.blog) as unique_blog_outreach,
        (SELECT COUNT(*) FROM outreach.blog WHERE source_url IS NOT NULL AND source_url != '') as blog_with_url,
        (SELECT COUNT(*) FROM outreach.blog WHERE context_summary IS NOT NULL) as blog_with_summary;
    """
)

# Check if there's a blog_content or blog_signals table anywhere
execute_query(
    'Q5: Check for other blog-related tables',
    """
    SELECT table_schema, table_name
    FROM information_schema.tables
    WHERE table_name LIKE '%blog%'
       OR table_name LIKE '%content%'
       OR table_name LIKE '%signal%'
       OR table_name LIKE '%news%'
       OR table_name LIKE '%pressure%'
    ORDER BY table_schema, table_name;
    """
)

# Check outreach.bit_signals table structure
execute_query(
    'Q6: outreach.bit_signals table structure',
    """
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'outreach'
      AND table_name = 'bit_signals'
    ORDER BY ordinal_position;
    """
)

# Check if bit_signals exists and has any data
execute_query(
    'Q7: outreach.bit_signals record count',
    """
    SELECT COUNT(*) as total,
           COUNT(DISTINCT outreach_id) as unique_outreach
    FROM outreach.bit_signals;
    """
)

# Check pressure signal enums
execute_query(
    'Q8: Check pressure domain enum values',
    """
    SELECT e.enumlabel as enum_value
    FROM pg_type t
    JOIN pg_enum e ON t.oid = e.enumtypid
    WHERE t.typname = 'pressure_domain_enum'
    ORDER BY e.enumsortorder;
    """
)

execute_query(
    'Q9: Check pressure class enum values',
    """
    SELECT e.enumlabel as enum_value
    FROM pg_type t
    JOIN pg_enum e ON t.oid = e.enumtypid
    WHERE t.typname = 'pressure_class_enum'
    ORDER BY e.enumsortorder;
    """
)

print('=' * 80)
print('FOLLOW-UP INVESTIGATION COMPLETE')
print('=' * 80)
