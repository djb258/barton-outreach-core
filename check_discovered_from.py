"""Check what values exist in discovered_from column"""
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

    # Check all discovered_from values
    print('=== All discovered_from Values ===')
    cur.execute("""
        SELECT discovered_from, COUNT(*) as count
        FROM company.company_source_urls
        GROUP BY discovered_from
        ORDER BY count DESC;
    """)
    results = cur.fetchall()
    for row in results:
        print(f"{row['discovered_from']}: {row['count']}")
    print()

    # Check recent records
    print('=== 10 Most Recent URLs ===')
    cur.execute("""
        SELECT sovereign_company_id, source_url, source_type, discovered_from, created_at
        FROM company.company_source_urls
        ORDER BY created_at DESC
        LIMIT 10;
    """)
    results = cur.fetchall()
    for row in results:
        print(f"{row['created_at']} | {row['discovered_from']} | {row['source_type']} | {row['source_url'][:50]}")

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
