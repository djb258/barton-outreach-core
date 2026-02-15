"""Check URL discovery script results in Neon database"""
import psycopg2
import os
from psycopg2.extras import RealDictCursor

def main():
    # Connect to Neon
    conn = psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )

    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Query 1: Overall counts
    print('=== URL Discovery Stats ===')
    cur.execute("""
        SELECT COUNT(*) as total_urls,
               COUNT(*) FILTER (WHERE discovered_from = 'url_pattern_discovery') as discovery_script_urls,
               MAX(created_at) as latest_created
        FROM company.company_source_urls;
    """)
    result = cur.fetchone()
    print(f"Total URLs: {result['total_urls']}")
    print(f"From Discovery Script: {result['discovery_script_urls']}")
    print(f"Latest Created: {result['latest_created']}")
    print()

    # Query 2: Source type breakdown
    print('=== Source Type Breakdown (Discovery Script) ===')
    cur.execute("""
        SELECT source_type, COUNT(*) as count
        FROM company.company_source_urls
        WHERE discovered_from = 'url_pattern_discovery'
        GROUP BY source_type
        ORDER BY count DESC;
    """)
    results = cur.fetchall()
    if results:
        for row in results:
            print(f"{row['source_type']}: {row['count']}")
    else:
        print('No URLs found from url_pattern_discovery')

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
