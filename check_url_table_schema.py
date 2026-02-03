"""Check company_source_urls table schema"""
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

    # Check table schema
    print('=== company.company_source_urls Schema ===')
    cur.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'company'
        AND table_name = 'company_source_urls'
        ORDER BY ordinal_position;
    """)
    results = cur.fetchall()
    for row in results:
        nullable = "NULL" if row['is_nullable'] == 'YES' else "NOT NULL"
        default = f" DEFAULT {row['column_default']}" if row['column_default'] else ""
        print(f"{row['column_name']:<30} {row['data_type']:<20} {nullable}{default}")
    print()

    # Check 10 most recent URLs with correct columns
    print('=== 10 Most Recent URLs ===')
    cur.execute("""
        SELECT *
        FROM company.company_source_urls
        ORDER BY created_at DESC
        LIMIT 10;
    """)
    results = cur.fetchall()
    if results:
        print(f"Columns: {list(results[0].keys())}")
        for row in results:
            print(row)

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
