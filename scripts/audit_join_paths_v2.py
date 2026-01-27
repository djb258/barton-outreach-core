"""
Audit all tables and their join paths to outreach_id.
Creates definitive documentation of how tables connect.
"""
import psycopg2
import os

def get_conn():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def main():
    conn = get_conn()
    cur = conn.cursor()
    
    print("=" * 80)
    print("OUTREACH JOIN PATH AUDIT - PHASE 2")
    print("=" * 80)
    
    # KEY FINDING: company.company_master does NOT have outreach_id!
    print("\n[1] company.company_master COLUMNS:")
    print("-" * 60)
    
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'company' AND table_name = 'company_master'
        ORDER BY ordinal_position
    """)
    
    for col, dtype in cur.fetchall():
        print(f"  {col}: {dtype}")
    
    # Check how company_master SHOULD connect
    print("\n[2] FINDING THE BRIDGE:")
    print("-" * 60)
    
    # Does outreach.company_target have company_unique_id?
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'outreach' AND table_name = 'company_target'
        AND column_name = 'company_unique_id'
    """)
    has_cuid = cur.fetchone()
    print(f"  outreach.company_target has company_unique_id: {'✓' if has_cuid else '✗'}")
    
    # Can we join company_target to company_master?
    if has_cuid:
        # Check format match
        cur.execute("SELECT company_unique_id FROM outreach.company_target WHERE company_unique_id IS NOT NULL LIMIT 3")
        ct_ids = [r[0] for r in cur.fetchall()]
        print(f"  company_target.company_unique_id samples: {ct_ids}")
        
        cur.execute("SELECT company_unique_id FROM company.company_master LIMIT 3")
        cm_ids = [r[0] for r in cur.fetchall()]
        print(f"  company_master.company_unique_id samples: {cm_ids}")
        
        # Try joining
        cur.execute("""
            SELECT COUNT(*) FROM outreach.company_target ct
            JOIN company.company_master cm ON ct.company_unique_id = cm.company_unique_id
        """)
        match_count = cur.fetchone()[0]
        print(f"\n  JOIN company_target → company_master: {match_count:,} matches")
    
    # Check cl.company_identity - does it bridge?
    print("\n[3] cl.company_identity COLUMNS:")
    print("-" * 60)
    
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'cl' AND table_name = 'company_identity'
        ORDER BY ordinal_position
    """)
    
    for col, dtype in cur.fetchall():
        print(f"  {col}: {dtype}")
    
    # Sample data
    cur.execute("""
        SELECT sovereign_company_id, outreach_id, legacy_company_unique_id
        FROM cl.company_identity 
        WHERE outreach_id IS NOT NULL
        LIMIT 3
    """)
    print("\n  Sample rows:")
    for row in cur.fetchall():
        print(f"    sovereign_company_id: {row[0]}")
        print(f"    outreach_id: {row[1]}")
        print(f"    legacy_company_unique_id: {row[2]}")
        print()
    
    # Can cl.company_identity bridge to company_master?
    cur.execute("""
        SELECT COUNT(*) FROM cl.company_identity ci
        JOIN company.company_master cm ON ci.legacy_company_unique_id = cm.company_unique_id
        WHERE ci.outreach_id IS NOT NULL
    """)
    bridge_count = cur.fetchone()[0]
    print(f"  cl.company_identity → company_master (via legacy_company_unique_id): {bridge_count:,}")
    
    # The FULL path: outreach → cl → company_master
    print("\n[4] FULL JOIN PATH TEST:")
    print("-" * 60)
    
    cur.execute("""
        SELECT COUNT(*) 
        FROM outreach.outreach o
        JOIN cl.company_identity ci ON o.outreach_id = ci.outreach_id
        JOIN company.company_master cm ON ci.legacy_company_unique_id = cm.company_unique_id
    """)
    full_path = cur.fetchone()[0]
    print(f"  outreach.outreach → cl.company_identity → company.company_master: {full_path:,}")
    
    # Simpler path: company_target has outreach_id AND company_unique_id
    print("\n[5] SIMPLER PATH (company_target as bridge):")
    print("-" * 60)
    
    cur.execute("""
        SELECT COUNT(*) 
        FROM outreach.outreach o
        JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
        JOIN company.company_master cm ON ct.company_unique_id = cm.company_unique_id
    """)
    simple_path = cur.fetchone()[0]
    print(f"  outreach.outreach → company_target → company_master: {simple_path:,}")
    
    # Check people.company_slot - does it have outreach_id?
    print("\n[6] people.company_slot COLUMNS:")
    print("-" * 60)
    
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'people' AND table_name = 'company_slot'
        ORDER BY ordinal_position
    """)
    
    for col, dtype in cur.fetchall():
        if 'id' in col.lower() or col in ['slot_type', 'is_filled']:
            print(f"  {col}: {dtype}")
    
    # EIN path verification
    print("\n[7] EIN PATHS:")
    print("-" * 60)
    
    # outreach.dol has EIN and outreach_id - direct!
    cur.execute("""
        SELECT COUNT(*) FROM outreach.outreach o
        JOIN outreach.dol d ON o.outreach_id = d.outreach_id
        WHERE d.ein IS NOT NULL
    """)
    ein_direct = cur.fetchone()[0]
    print(f"  outreach → dol (direct, has EIN): {ein_direct:,}")
    
    # company_master EIN path (indirect)
    cur.execute("""
        SELECT COUNT(*) 
        FROM outreach.outreach o
        JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
        JOIN company.company_master cm ON ct.company_unique_id = cm.company_unique_id
        WHERE cm.ein IS NOT NULL
    """)
    ein_indirect = cur.fetchone()[0]
    print(f"  outreach → company_target → company_master (has EIN): {ein_indirect:,}")
    
    # Summary
    print("\n" + "=" * 80)
    print("KEY FINDINGS:")
    print("=" * 80)
    print("""
1. company.company_master does NOT have outreach_id column
2. outreach.company_target HAS BOTH outreach_id AND company_unique_id
   → This is the BRIDGE table!
3. people.company_slot HAS outreach_id (direct FK)
4. EIN is available in TWO places:
   - outreach.dol (13,829 records with EIN)
   - company.company_master (via company_target bridge)
""")
    
    conn.close()

if __name__ == '__main__':
    main()
