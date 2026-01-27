"""
Audit all tables and their join paths to outreach_id.
Creates definitive documentation of how tables connect.
"""
import psycopg2
import os
from collections import defaultdict

def get_conn():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def main():
    conn = get_conn()
    cur = conn.cursor()
    
    print("=" * 80)
    print("OUTREACH JOIN PATH AUDIT")
    print("=" * 80)
    
    # Core schemas we care about
    schemas = ['outreach', 'company', 'people', 'dol', 'cl']
    
    # Step 1: Find all tables with outreach_id column
    print("\n[1] TABLES WITH outreach_id COLUMN:")
    print("-" * 60)
    
    cur.execute("""
        SELECT table_schema, table_name, data_type
        FROM information_schema.columns
        WHERE column_name = 'outreach_id'
        AND table_schema IN ('outreach', 'company', 'people', 'dol', 'cl')
        ORDER BY table_schema, table_name
    """)
    
    outreach_id_tables = cur.fetchall()
    for schema, table, dtype in outreach_id_tables:
        cur.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
        count = cur.fetchone()[0]
        print(f"  {schema}.{table}: {count:,} rows (type: {dtype})")
    
    # Step 2: Find all tables WITHOUT outreach_id but with company_unique_id
    print("\n[2] TABLES WITH company_unique_id BUT NOT outreach_id:")
    print("-" * 60)
    
    cur.execute("""
        SELECT c1.table_schema, c1.table_name, c1.data_type
        FROM information_schema.columns c1
        WHERE c1.column_name = 'company_unique_id'
        AND c1.table_schema IN ('outreach', 'company', 'people', 'dol', 'cl')
        AND NOT EXISTS (
            SELECT 1 FROM information_schema.columns c2
            WHERE c2.table_schema = c1.table_schema
            AND c2.table_name = c1.table_name
            AND c2.column_name = 'outreach_id'
        )
        ORDER BY c1.table_schema, c1.table_name
    """)
    
    company_id_only = cur.fetchall()
    for schema, table, dtype in company_id_only:
        cur.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
        count = cur.fetchone()[0]
        print(f"  {schema}.{table}: {count:,} rows (type: {dtype})")
    
    # Step 3: Check the MASTER table - outreach.outreach
    print("\n[3] MASTER TABLE: outreach.outreach")
    print("-" * 60)
    
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'outreach' AND table_name = 'outreach'
        ORDER BY ordinal_position
    """)
    
    for col, dtype, nullable in cur.fetchall():
        print(f"  {col}: {dtype} {'(nullable)' if nullable == 'YES' else ''}")
    
    cur.execute("SELECT COUNT(*) FROM outreach.outreach")
    print(f"\n  Total rows: {cur.fetchone()[0]:,}")
    
    # Step 4: Check each subhub table structure
    subhubs = [
        ('outreach', 'company_target'),
        ('outreach', 'dol'),
        ('outreach', 'blog'),
        ('outreach', 'people'),
        ('outreach', 'bit_scores'),
    ]
    
    print("\n[4] SUBHUB TABLES (Must FK to outreach.outreach via outreach_id):")
    print("-" * 60)
    
    for schema, table in subhubs:
        try:
            cur.execute(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = '{schema}' AND table_name = '{table}'
                ORDER BY ordinal_position
            """)
            cols = cur.fetchall()
            
            cur.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
            count = cur.fetchone()[0]
            
            # Check if outreach_id exists
            has_outreach_id = any(c[0] == 'outreach_id' for c in cols)
            
            print(f"\n  {schema}.{table}: {count:,} rows")
            print(f"  Has outreach_id: {'✓' if has_outreach_id else '✗ MISSING!'}")
            
            # Show key columns
            key_cols = ['outreach_id', 'company_unique_id', 'ein', 'domain', 'email']
            for col, dtype in cols:
                if col in key_cols or 'id' in col.lower():
                    print(f"    - {col}: {dtype}")
                    
        except Exception as e:
            print(f"\n  {schema}.{table}: ERROR - {e}")
    
    # Step 5: Check company.company_master - the bridge table
    print("\n[5] BRIDGE TABLE: company.company_master")
    print("-" * 60)
    
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'company' AND table_name = 'company_master'
        ORDER BY ordinal_position
    """)
    
    cols = cur.fetchall()
    for col, dtype in cols:
        if 'id' in col.lower() or col in ['ein', 'domain', 'company_name']:
            print(f"  {col}: {dtype}")
    
    cur.execute("SELECT COUNT(*) FROM company.company_master")
    print(f"\n  Total rows: {cur.fetchone()[0]:,}")
    
    # Check if company_master.outreach_id actually matches outreach.outreach
    cur.execute("""
        SELECT 
            (SELECT COUNT(*) FROM company.company_master WHERE outreach_id IS NOT NULL) as with_outreach_id,
            (SELECT COUNT(DISTINCT cm.outreach_id) 
             FROM company.company_master cm
             JOIN outreach.outreach o ON cm.outreach_id = o.outreach_id) as matched_to_spine
    """)
    with_id, matched = cur.fetchone()
    print(f"  With outreach_id: {with_id:,}")
    print(f"  Matched to spine: {matched:,}")
    
    # Step 6: Verify join paths work
    print("\n[6] JOIN PATH VERIFICATION:")
    print("-" * 60)
    
    # Test: outreach -> company_target
    cur.execute("""
        SELECT COUNT(*) FROM outreach.outreach o
        JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
    """)
    print(f"  outreach → company_target (via outreach_id): {cur.fetchone()[0]:,}")
    
    # Test: outreach -> dol
    cur.execute("""
        SELECT COUNT(*) FROM outreach.outreach o
        JOIN outreach.dol d ON o.outreach_id = d.outreach_id
    """)
    print(f"  outreach → dol (via outreach_id): {cur.fetchone()[0]:,}")
    
    # Test: outreach -> blog
    cur.execute("""
        SELECT COUNT(*) FROM outreach.outreach o
        JOIN outreach.blog b ON o.outreach_id = b.outreach_id
    """)
    print(f"  outreach → blog (via outreach_id): {cur.fetchone()[0]:,}")
    
    # Test: outreach -> company_master
    cur.execute("""
        SELECT COUNT(*) FROM outreach.outreach o
        JOIN company.company_master cm ON o.outreach_id = cm.outreach_id
    """)
    print(f"  outreach → company_master (via outreach_id): {cur.fetchone()[0]:,}")
    
    # Test: company_master -> company_slots
    cur.execute("""
        SELECT COUNT(*) FROM company.company_master cm
        JOIN company.company_slots cs ON cm.company_unique_id = cs.company_unique_id
    """)
    print(f"  company_master → company_slots (via company_unique_id): {cur.fetchone()[0]:,}")
    
    # Test: company_slots -> people_master
    cur.execute("""
        SELECT COUNT(*) FROM company.company_slots cs
        JOIN people.people_master pm ON cs.company_slot_unique_id = pm.company_slot_unique_id
    """)
    print(f"  company_slots → people_master (via company_slot_unique_id): {cur.fetchone()[0]:,}")
    
    # Step 7: Sample IDs to show format
    print("\n[7] ID FORMAT SAMPLES:")
    print("-" * 60)
    
    cur.execute("SELECT outreach_id FROM outreach.outreach LIMIT 1")
    print(f"  outreach.outreach_id: {cur.fetchone()[0]}")
    
    cur.execute("SELECT company_unique_id FROM company.company_master LIMIT 1")
    print(f"  company_master.company_unique_id: {cur.fetchone()[0]}")
    
    cur.execute("SELECT company_slot_unique_id FROM company.company_slots LIMIT 1")
    print(f"  company_slots.company_slot_unique_id: {cur.fetchone()[0]}")
    
    cur.execute("SELECT unique_id FROM people.people_master LIMIT 1")
    print(f"  people_master.unique_id: {cur.fetchone()[0]}")
    
    # Step 8: EIN paths
    print("\n[8] EIN DATA LOCATIONS:")
    print("-" * 60)
    
    cur.execute("""
        SELECT 'outreach.dol' as source, COUNT(*) as total, COUNT(ein) as with_ein
        FROM outreach.dol
        UNION ALL
        SELECT 'company.company_master', COUNT(*), COUNT(ein)
        FROM company.company_master
        UNION ALL
        SELECT 'dol.ein_urls', COUNT(*), COUNT(ein)
        FROM dol.ein_urls
    """)
    
    for source, total, with_ein in cur.fetchall():
        pct = (with_ein / total * 100) if total > 0 else 0
        print(f"  {source}: {with_ein:,} / {total:,} ({pct:.1f}%)")
    
    conn.close()
    print("\n" + "=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
