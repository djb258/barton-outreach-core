"""
Blog Enrichment Data Investigation Script
Queries Neon PostgreSQL to locate Blog enrichment data storage
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

# Query 1: First check what columns exist in blog.pressure_signals
execute_query(
    'QUERY 1a: blog.pressure_signals table structure',
    """
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'blog'
      AND table_name = 'pressure_signals'
    ORDER BY ordinal_position;
    """
)

# Query 1b: Check blog.pressure_signals with correct columns
execute_query(
    'QUERY 1b: blog.pressure_signals statistics',
    """
    SELECT COUNT(*) as total_count,
           MIN(created_at) as earliest,
           MAX(created_at) as latest
    FROM blog.pressure_signals;
    """
)

# Query 2: Check outreach.bit_signals table
execute_query(
    'QUERY 2: outreach.bit_signals by signal_type',
    """
    SELECT COUNT(*) as count,
           COUNT(DISTINCT outreach_id) as unique_outreach,
           signal_type,
           MIN(created_at) as earliest,
           MAX(created_at) as latest
    FROM outreach.bit_signals
    GROUP BY signal_type
    ORDER BY COUNT(*) DESC;
    """
)

# Query 3: Check all blog schema tables
execute_query(
    'QUERY 3: blog schema tables list',
    """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'blog'
    ORDER BY table_name;
    """
)

# Query 4: Check blog schema columns
execute_query(
    'QUERY 4: blog schema column structure',
    """
    SELECT table_name, column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'blog'
    ORDER BY table_name, ordinal_position;
    """
)

# Query 5: Check all blog tables with row counts
execute_query(
    'QUERY 5: blog schema tables with row counts',
    """
    SELECT schemaname, tablename, n_tup_ins as row_count
    FROM pg_stat_user_tables
    WHERE schemaname = 'blog'
    ORDER BY n_tup_ins DESC;
    """
)

# Query 6: Sample blog.pressure_signals data
execute_query(
    'QUERY 6: Sample blog.pressure_signals data',
    'SELECT * FROM blog.pressure_signals LIMIT 5;'
)

# Query 7: Check outreach.blog table structure
execute_query(
    'QUERY 7: outreach.blog table structure',
    """
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'outreach'
      AND table_name = 'blog'
    ORDER BY ordinal_position;
    """
)

# Query 8: Check outreach.blog for URL/content data
execute_query(
    'QUERY 8: outreach.blog URL and content coverage',
    """
    SELECT
        COUNT(*) as total,
        COUNT(source_url) as with_url,
        COUNT(context_summary) as with_summary,
        COUNT(CASE WHEN source_type != 'pending' THEN 1 END) as not_pending
    FROM outreach.blog;
    """
)

# Query 9: Sample outreach.blog data
execute_query(
    'QUERY 9: Sample outreach.blog data',
    'SELECT * FROM outreach.blog LIMIT 5;'
)

print('=' * 80)
print('INVESTIGATION COMPLETE')
print('=' * 80)
