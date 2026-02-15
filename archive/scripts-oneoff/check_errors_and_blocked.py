#!/usr/bin/env python3
"""Check error tables and analyze blocked DOL records."""

import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    'host': 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    'port': 5432,
    'database': 'Marketing DB',
    'user': 'Marketing DB_owner',
    'password': 'npg_OsE4Z2oPCpiT',
    'sslmode': 'require'
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor(cursor_factory=RealDictCursor)

# 1. Check error tables
print("=" * 60)
print("ERROR TABLES INVENTORY")
print("=" * 60)

cur.execute("""
    SELECT table_schema, table_name 
    FROM information_schema.tables 
    WHERE table_name LIKE '%error%'
    ORDER BY table_schema, table_name
""")
error_tables = cur.fetchall()
print(f"\nFound {len(error_tables)} error tables:")
for row in error_tables:
    print(f"  {row['table_schema']}.{row['table_name']}")

# 2. Check counts in each error table
print("\n" + "=" * 60)
print("ERROR TABLE COUNTS")
print("=" * 60)

for row in error_tables:
    schema = row['table_schema']
    table = row['table_name']
    try:
        cur.execute(f"SELECT COUNT(*) as cnt FROM {schema}.{table}")
        cnt = cur.fetchone()['cnt']
        if cnt > 0:
            print(f"\n  {schema}.{table}: {cnt:,} records")
            # Show sample of error reasons if there's an error column
            cur.execute(f"""
                SELECT column_name FROM information_schema.columns 
                WHERE table_schema = %s AND table_name = %s
                AND column_name LIKE '%error%' OR column_name LIKE '%reason%' OR column_name LIKE '%status%'
            """, (schema, table))
            cols = [c['column_name'] for c in cur.fetchall()]
            if cols:
                for col in cols[:1]:  # Just first error-like column
                    cur.execute(f"""
                        SELECT {col}, COUNT(*) as cnt 
                        FROM {schema}.{table}
                        GROUP BY {col}
                        ORDER BY cnt DESC
                        LIMIT 5
                    """)
                    print(f"    Breakdown by {col}:")
                    for r in cur.fetchall():
                        print(f"      {r[col]}: {r['cnt']:,}")
        else:
            print(f"  {schema}.{table}: EMPTY")
    except Exception as e:
        print(f"  {schema}.{table}: Error - {e}")

# 3. Analyze blocked DOL records
print("\n" + "=" * 60)
print("BLOCKED DOL RECORDS ANALYSIS")
print("=" * 60)

# Check what the diagnostic view uses for blocking
cur.execute("""
    SELECT 
        CASE 
            WHEN d.dol_status = 'BLOCKED' THEN 
                COALESCE(d.dol_error_code, 'UNKNOWN')
            ELSE d.dol_status
        END as status_detail,
        COUNT(*) as cnt
    FROM outreach.v_outreach_diagnostic d
    WHERE d.dol_status = 'BLOCKED'
    GROUP BY 1
    ORDER BY cnt DESC
""")
print("\nBlocked by error_code:")
for row in cur.fetchall():
    print(f"  {row['status_detail']:<30}: {row['cnt']:>8,}")

# 4. Check the dol_errors table specifically
print("\n" + "=" * 60)
print("DOL ERRORS TABLE DETAIL")
print("=" * 60)

cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'outreach' AND table_name = 'dol_errors'
    ORDER BY ordinal_position
""")
cols = cur.fetchall()
if cols:
    print("\nColumns in outreach.dol_errors:")
    for c in cols:
        print(f"  {c['column_name']}: {c['data_type']}")
    
    cur.execute("SELECT COUNT(*) as cnt FROM outreach.dol_errors")
    print(f"\nTotal records: {cur.fetchone()['cnt']:,}")
    
    # Check error distribution
    cur.execute("""
        SELECT error_code, COUNT(*) as cnt 
        FROM outreach.dol_errors
        GROUP BY error_code
        ORDER BY cnt DESC
    """)
    print("\nError code distribution:")
    for row in cur.fetchall():
        print(f"  {row['error_code']:<30}: {row['cnt']:>8,}")

# 5. Cross-reference: blocked records that now have EIN
print("\n" + "=" * 60)
print("BLOCKED BUT NOW HAVE EIN (could be cleared)")
print("=" * 60)

cur.execute("""
    SELECT COUNT(*) as cnt
    FROM outreach.dol_errors de
    JOIN outreach.outreach o ON de.outreach_id = o.outreach_id
    JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
    JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
    WHERE cm.ein IS NOT NULL
""")
can_clear = cur.fetchone()['cnt']
print(f"\nBlocked records that NOW have EIN in company_master: {can_clear:,}")

# 6. Check if we need to clear errors and create dol records
cur.execute("""
    SELECT de.error_code, COUNT(*) as cnt
    FROM outreach.dol_errors de
    JOIN outreach.outreach o ON de.outreach_id = o.outreach_id
    JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
    JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
    WHERE cm.ein IS NOT NULL
    GROUP BY de.error_code
    ORDER BY cnt DESC
""")
print("\nBy error code:")
for row in cur.fetchall():
    print(f"  {row['error_code']:<30}: {row['cnt']:>8,}")

conn.close()
