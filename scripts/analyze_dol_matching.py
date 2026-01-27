#!/usr/bin/env python3
"""
DOL-to-Outreach Matching Analysis
==================================
Understand why we can't match more EINs to outreach_ids and explore enrichment paths.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys

DB_CONFIG = {
    'host': 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    'port': 5432,
    'database': 'Marketing DB',
    'user': 'Marketing DB_owner',
    'password': 'npg_OsE4Z2oPCpiT',
    'sslmode': 'require'
}

def main():
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("DOL-TO-OUTREACH MATCHING ANALYSIS")
    print("=" * 80)
    
    # =========================================================================
    # SECTION 1: Current State Overview
    # =========================================================================
    print("\n" + "=" * 80)
    print("1. CURRENT STATE OVERVIEW")
    print("=" * 80)
    
    # Outreach universe
    cur.execute("SELECT COUNT(*) as cnt FROM outreach.outreach")
    outreach_total = cur.fetchone()['cnt']
    
    # Outreach with DOL data (via diagnostic view)
    cur.execute("""
        SELECT dol_status, COUNT(*) as cnt
        FROM outreach.v_outreach_diagnostic
        GROUP BY dol_status
        ORDER BY cnt DESC
    """)
    dol_status = cur.fetchall()
    
    print(f"\nOutreach Universe: {outreach_total:,}")
    print("\nDOL Status Distribution:")
    for row in dol_status:
        pct = 100 * row['cnt'] / outreach_total
        print(f"  {row['dol_status']:<15}: {row['cnt']:>8,} ({pct:>5.1f}%)")
    
    # =========================================================================
    # SECTION 2: THE MATCHING CHAIN
    # =========================================================================
    print("\n" + "=" * 80)
    print("2. THE MATCHING CHAIN: outreach → outreach.dol → dol.form_5500")
    print("=" * 80)
    
    # outreach.dol is the linkage table - it has ein
    cur.execute("""
        SELECT 
            COUNT(*) as total_dol,
            COUNT(CASE WHEN ein IS NOT NULL THEN 1 END) as with_ein
        FROM outreach.dol
    """)
    dol_table = cur.fetchone()
    print(f"\noutreach.dol (linkage table):")
    print(f"  Total records: {dol_table['total_dol']:,}")
    print(f"  With EIN: {dol_table['with_ein']:,}")
    
    # Check form_5500 table
    cur.execute("SELECT COUNT(*) as cnt FROM dol.form_5500")
    total_5500 = cur.fetchone()['cnt']
    
    cur.execute("SELECT COUNT(DISTINCT sponsor_dfe_ein) as cnt FROM dol.form_5500 WHERE sponsor_dfe_ein IS NOT NULL")
    unique_eins_5500 = cur.fetchone()['cnt']
    
    print(f"\nDOL Form 5500:")
    print(f"  Total filings: {total_5500:,}")
    print(f"  Unique EINs: {unique_eins_5500:,}")
    
    # =========================================================================
    # SECTION 3: EIN DATA FLOW
    # =========================================================================
    print("\n" + "=" * 80)
    print("3. EIN DATA FLOW")
    print("=" * 80)
    
    # outreach.dol links to form_5500 via EIN
    cur.execute("""
        SELECT COUNT(*) as matchable
        FROM outreach.dol od
        JOIN dol.form_5500 f ON od.ein = f.sponsor_dfe_ein
    """)
    matched = cur.fetchone()['matchable']
    print(f"\noutreach.dol → form_5500 via EIN: {matched:,} matched")
    
    # Check if we can match through company_master
    cur.execute("""
        SELECT COUNT(*) as cnt
        FROM company.company_master
        WHERE ein IS NOT NULL
    """)
    cm_with_ein = cur.fetchone()['cnt']
    
    cur.execute("SELECT COUNT(*) as cnt FROM company.company_master")
    cm_total = cur.fetchone()['cnt']
    
    print(f"\ncompany_master (potential EIN source):")
    print(f"  Total: {cm_total:,}")
    print(f"  With EIN: {cm_with_ein:,} ({100*cm_with_ein/cm_total:.1f}%)" if cm_total > 0 else "  With EIN: 0")
    
    # =========================================================================
    # SECTION 4: THE LINKAGE OPPORTUNITY
    # =========================================================================
    print("\n" + "=" * 80)
    print("4. THE LINKAGE OPPORTUNITY")
    print("=" * 80)
    
    # How many outreach_ids are missing DOL data?
    cur.execute("""
        SELECT COUNT(*) as missing_dol
        FROM outreach.outreach o
        LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
        WHERE d.dol_id IS NULL
    """)
    missing_dol = cur.fetchone()['missing_dol']
    print(f"\nOutreach_ids missing DOL record: {missing_dol:,}")
    
    # Check via identity bridge - can we get EIN from company_master?
    cur.execute("""
        SELECT COUNT(DISTINCT o.outreach_id) as linkable
        FROM outreach.outreach o
        LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
        JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
        JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
        WHERE d.dol_id IS NULL
          AND cm.ein IS NOT NULL
    """)
    linkable_via_bridge = cur.fetchone()['linkable']
    print(f"Outreach_ids we can get EIN for via bridge: {linkable_via_bridge:,}")
    
    # Direct check: how many unique EINs in company_master match 5500?
    cur.execute("""
        SELECT COUNT(DISTINCT cm.ein) as matching_eins
        FROM company.company_master cm
        JOIN dol.form_5500 f ON cm.ein = f.sponsor_dfe_ein
    """)
    matching_eins = cur.fetchone()['matching_eins']
    print(f"\nEINs in company_master that exist in 5500: {matching_eins:,}")
    
    # =========================================================================
    # SECTION 5: Where are the unmatched outreach_ids?
    # =========================================================================
    print("\n" + "=" * 80)
    print("5. UNMATCHED OUTREACH ANALYSIS")
    print("=" * 80)
    
    # Get the count from diagnostic view
    cur.execute("""
        SELECT 
            dol_status,
            COUNT(*) as cnt,
            COUNT(CASE WHEN ct_status = 'PASS' THEN 1 END) as ct_ready
        FROM outreach.v_outreach_diagnostic
        WHERE dol_status != 'PASS'
        GROUP BY dol_status
        ORDER BY cnt DESC
    """)
    unmatched = cur.fetchall()
    print("\nOutreach_ids without DOL data:")
    for row in unmatched:
        print(f"  {row['dol_status']}: {row['cnt']:,} (CT ready: {row['ct_ready']:,})")
    
    # =========================================================================
    # SECTION 6: DOL Error Analysis
    # =========================================================================
    print("\n" + "=" * 80)
    print("6. DOL ERROR ANALYSIS")
    print("=" * 80)
    
    # Check if error table exists
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'outreach_errors' 
            AND table_name = 'dol_errors'
        )
    """)
    if cur.fetchone()['exists']:
        cur.execute("""
            SELECT failure_code, COUNT(*) as cnt
            FROM outreach_errors.dol_errors
            WHERE resolved_at IS NULL
            GROUP BY failure_code
            ORDER BY cnt DESC
        """)
        errors = cur.fetchall()
        print("\nUnresolved DOL errors:")
        for row in errors:
            print(f"  {row['failure_code']}: {row['cnt']:,}")
    else:
        print("\nNo DOL error table found (outreach_errors.dol_errors)")
        print("Checking diagnostic view for blocked reasons...")
        
        cur.execute("""
            SELECT dol_error, COUNT(*) as cnt
            FROM outreach.v_outreach_diagnostic
            WHERE dol_status = 'BLOCKED'
            GROUP BY dol_error
            ORDER BY cnt DESC
            LIMIT 10
        """)
        errors = cur.fetchall()
        print("\nBlocked DOL reasons (from diagnostic view):")
        for row in errors:
            print(f"  {row['dol_error'] or 'NULL'}: {row['cnt']:,}")
    
    # =========================================================================
    # SECTION 7: Enrichment Opportunities
    # =========================================================================
    print("\n" + "=" * 80)
    print("7. ENRICHMENT OPPORTUNITIES")
    print("=" * 80)
    
    # Option 1: Get EIN via bridge and create outreach.dol records
    cur.execute("""
        SELECT COUNT(DISTINCT o.outreach_id) as can_create
        FROM outreach.outreach o
        LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
        JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
        JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
        JOIN dol.form_5500 f ON cm.ein = f.sponsor_dfe_ein
        WHERE d.dol_id IS NULL
    """)
    can_create = cur.fetchone()['can_create']
    print(f"\n[OPTION 1] Create outreach.dol via bridge + EIN match:")
    print(f"  Outreach_ids we can create DOL records for: {can_create:,}")
    print(f"  Path: outreach → bridge → company_master.ein → form_5500")
    
    # Option 2: Domain matching to 5500 web address - check if column exists
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'dol' AND table_name = 'form_5500' 
        AND column_name LIKE '%web%'
    """)
    web_cols = [r['column_name'] for r in cur.fetchall()]
    
    if web_cols:
        web_col = web_cols[0]
        cur.execute(f"""
            SELECT COUNT(*) as has_web
            FROM dol.form_5500
            WHERE {web_col} IS NOT NULL
              AND {web_col} != ''
        """)
        has_web = cur.fetchone()['has_web']
        print(f"\n[OPTION 2] Domain matching via 5500 web address ({web_col}):")
        print(f"  5500 filings with web address: {has_web:,}")
    else:
        has_web = 0
        print(f"\n[OPTION 2] Domain matching: No web address column in form_5500")
    
    # Option 3: Name + State + City fuzzy matching 
    print(f"\n[OPTION 3] Fuzzy name matching (ein_matcher.py):")
    print(f"  Already implemented - matches State+City+Name with >0.8 similarity")
    
    # Count potential fuzzy matches - companies in outreach without EIN
    cur.execute("""
        SELECT COUNT(*) as potential
        FROM outreach.outreach o
        LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
        JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
        JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
        WHERE d.dol_id IS NULL
          AND cm.ein IS NULL
          AND cm.address_state IS NOT NULL
    """)
    fuzzy_potential = cur.fetchone()['potential']
    print(f"  Outreach with company_master but no EIN (fuzzy candidates): {fuzzy_potential:,}")
    
    # =========================================================================
    # SECTION 8: Summary & Recommendations
    # =========================================================================
    print("\n" + "=" * 80)
    print("8. SUMMARY & RECOMMENDATIONS")
    print("=" * 80)
    
    print(f"""
CURRENT STATE:
- Outreach Universe: {outreach_total:,}
- With DOL data (PASS): {dol_table['with_ein']:,} ({100*dol_table['with_ein']/outreach_total:.1f}%)
- DOL Form 5500 filings: {total_5500:,} with {unique_eins_5500:,} unique EINs
- company_master with EIN: {cm_with_ein:,}

THE MATCHING CHAIN:
  outreach.outreach
       ↓ (sovereign_id)
  cl.company_identity_bridge  
       ↓ (source_company_id)
  company.company_master
       ↓ (ein)
  dol.form_5500
       ↓ 
  outreach.dol (created with filing data)

ENRICHMENT PATHS (Priority Order):

[A] IMMEDIATE - Create DOL records via bridge + existing EIN:
    - Path: outreach → bridge → company_master.ein → form_5500 → outreach.dol
    - {can_create:,} outreach_ids can be enriched NOW
    - Script: promote_dol_via_bridge.py
    
[B] SHORT-TERM - Fuzzy match to get more EINs:
    - Path: company_master (State+City+Name) → form_5500.ein
    - Then run [A] again
    - ein_matcher.py exists, run: --threshold 0.75

[C] MEDIUM-TERM - Domain matching:
    - Match outreach.domain → 5500.spons_dfe_web_addr
    - {has_web:,} filings have web addresses
    - Extract domain, normalize, join
    
[D] LONG-TERM - External enrichment:
    - IRS Business Master File (EIN lookup by name)
    - Commercial data providers (Clearbit, ZoomInfo)
    - Google Places API for business verification
""".format(
        outreach_total=outreach_total,
        total_5500=total_5500,
        unique_eins_5500=unique_eins_5500,
        cm_with_ein=cm_with_ein,
        can_create=can_create,
        has_web=has_web
    ))
    
    conn.close()

if __name__ == '__main__':
    main()
