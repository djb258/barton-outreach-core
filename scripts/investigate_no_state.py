#!/usr/bin/env python3
"""
Investigate NO_STATE errors in DOL matching.
Why are 11,900 records blocked for missing state when companies were loaded by state?
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
    print("INVESTIGATING NO_STATE ERRORS")
    print("=" * 80)
    
    # Get the blocked outreach_ids
    cur.execute("""
        SELECT COUNT(*) as blocked
        FROM outreach.v_outreach_diagnostic
        WHERE dol_status = 'BLOCKED'
          AND dol_error = 'NO_STATE'
    """)
    blocked = cur.fetchone()['blocked']
    print(f"\nOutreach_ids blocked with NO_STATE: {blocked:,}")
    
    # Question 1: Check the dol_errors table structure
    print("\n" + "=" * 80)
    print("1. WHERE DO NO_STATE ERRORS COME FROM?")
    print("=" * 80)
    
    # Check outreach_errors.dol_errors
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'outreach_errors' 
            AND table_name = 'dol_errors'
        )
    """)
    has_dol_errors = cur.fetchone()['exists']
    
    if has_dol_errors:
        cur.execute("""
            SELECT failure_code, COUNT(*) as cnt
            FROM outreach_errors.dol_errors
            WHERE failure_code = 'NO_STATE'
            GROUP BY failure_code
        """)
        errors = cur.fetchall()
        print(f"outreach_errors.dol_errors NO_STATE count: {errors[0]['cnt'] if errors else 0:,}")
        
        # Sample error records
        cur.execute("""
            SELECT *
            FROM outreach_errors.dol_errors
            WHERE failure_code = 'NO_STATE'
            LIMIT 3
        """)
        for row in cur.fetchall():
            print(f"\n  Sample error:")
            for k, v in row.items():
                if v is not None:
                    print(f"    {k}: {v}")
    else:
        print("outreach_errors.dol_errors table does not exist")
    
    # Question 2: Check company_master state coverage
    print("\n" + "=" * 80)
    print("2. COMPANY_MASTER STATE COVERAGE")
    print("=" * 80)
    
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(address_state) as with_state,
            COUNT(*) - COUNT(address_state) as missing_state
        FROM company.company_master
    """)
    cm = cur.fetchone()
    print(f"\ncompany_master:")
    print(f"  Total: {cm['total']:,}")
    print(f"  With state: {cm['with_state']:,}")
    print(f"  Missing state: {cm['missing_state']:,}")
    
    # Question 3: Trace blocked outreach through the chain
    print("\n" + "=" * 80)
    print("3. TRACING BLOCKED RECORDS")
    print("=" * 80)
    
    # Get blocked outreach_ids with full chain info
    cur.execute("""
        SELECT 
            d.outreach_id,
            d.domain,
            o.sovereign_id,
            b.source_company_id,
            cm.company_name,
            cm.address_state,
            cm.address_city,
            cm.ein
        FROM outreach.v_outreach_diagnostic d
        JOIN outreach.outreach o ON d.outreach_id = o.outreach_id
        LEFT JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
        LEFT JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
        WHERE d.dol_status = 'BLOCKED'
          AND d.dol_error = 'NO_STATE'
        LIMIT 10
    """)
    
    print("\nSample blocked records with chain data:")
    for row in cur.fetchall():
        print(f"\n  {row['domain']}")
        print(f"    sovereign_id: {str(row['sovereign_id'])[:20]}...")
        print(f"    bridge_source: {row['source_company_id'] or 'NOT IN BRIDGE'}")
        if row['company_name']:
            print(f"    company_master: {row['company_name'][:40]}")
            print(f"    state: {row['address_state'] or 'NULL'}")
            print(f"    ein: {row['ein'] or 'NULL'}")
    
    # Question 4: How many blocked records are NOT in bridge?
    print("\n" + "=" * 80)
    print("4. BLOCKED RECORDS - BRIDGE COVERAGE")
    print("=" * 80)
    
    cur.execute("""
        SELECT 
            COUNT(*) as total_blocked,
            COUNT(b.source_company_id) as in_bridge,
            COUNT(*) - COUNT(b.source_company_id) as not_in_bridge
        FROM outreach.v_outreach_diagnostic d
        JOIN outreach.outreach o ON d.outreach_id = o.outreach_id
        LEFT JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
        WHERE d.dol_status = 'BLOCKED'
          AND d.dol_error = 'NO_STATE'
    """)
    bridge_cov = cur.fetchone()
    print(f"\nBlocked NO_STATE records:")
    print(f"  Total: {bridge_cov['total_blocked']:,}")
    print(f"  In bridge: {bridge_cov['in_bridge']:,}")
    print(f"  NOT in bridge: {bridge_cov['not_in_bridge']:,}")
    
    # Question 5: For those IN bridge, what's their company_master state?
    print("\n" + "=" * 80)
    print("5. BLOCKED RECORDS IN BRIDGE - STATE DISTRIBUTION")
    print("=" * 80)
    
    cur.execute("""
        SELECT 
            cm.address_state,
            COUNT(*) as cnt,
            COUNT(cm.ein) as with_ein
        FROM outreach.v_outreach_diagnostic d
        JOIN outreach.outreach o ON d.outreach_id = o.outreach_id
        JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
        JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
        WHERE d.dol_status = 'BLOCKED'
          AND d.dol_error = 'NO_STATE'
        GROUP BY cm.address_state
        ORDER BY cnt DESC
    """)
    
    print(f"\n{'State':<10} {'Count':>10} {'With EIN':>10}")
    print("-" * 32)
    total_blocked_in_bridge = 0
    for row in cur.fetchall():
        state = row['address_state'] or 'NULL'
        print(f"{state:<10} {row['cnt']:>10,} {row['with_ein']:>10,}")
        total_blocked_in_bridge += row['cnt']
    print(f"{'TOTAL':<10} {total_blocked_in_bridge:>10,}")
    
    # Question 6: What about the form_5500 filing - does IT have state?
    print("\n" + "=" * 80)
    print("6. 5500 FILING STATE FOR COMPANIES WITH EIN")
    print("=" * 80)
    
    cur.execute("""
        SELECT 
            f.spons_dfe_mail_us_state as filing_state,
            cm.address_state as company_state,
            COUNT(*) as cnt
        FROM outreach.v_outreach_diagnostic d
        JOIN outreach.outreach o ON d.outreach_id = o.outreach_id
        JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
        JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
        JOIN dol.form_5500 f ON cm.ein = f.sponsor_dfe_ein
        WHERE d.dol_status = 'BLOCKED'
          AND d.dol_error = 'NO_STATE'
        GROUP BY f.spons_dfe_mail_us_state, cm.address_state
        ORDER BY cnt DESC
        LIMIT 15
    """)
    
    results = cur.fetchall()
    if results:
        print(f"\n{'5500 State':<12} {'Company State':<15} {'Count':>10}")
        print("-" * 40)
        for row in results:
            f_state = row['filing_state'] or 'NULL'
            c_state = row['company_state'] or 'NULL'
            print(f"{f_state:<12} {c_state:<15} {row['cnt']:>10,}")
    else:
        print("\nNo results - these blocked records don't have EIN matches in form_5500")
    
    # Check how many blocked records don't have EIN match
    cur.execute("""
        SELECT COUNT(*) as no_5500_match
        FROM outreach.v_outreach_diagnostic d
        JOIN outreach.outreach o ON d.outreach_id = o.outreach_id
        JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
        JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
        LEFT JOIN dol.form_5500 f ON cm.ein = f.sponsor_dfe_ein
        WHERE d.dol_status = 'BLOCKED'
          AND d.dol_error = 'NO_STATE'
          AND f.filing_id IS NULL
    """)
    no_match = cur.fetchone()['no_5500_match']
    print(f"\nBlocked NO_STATE records with NO form_5500 match: {no_match:,}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"""
Blocked NO_STATE: {blocked:,}
  - Not in bridge: {bridge_cov['not_in_bridge']:,}
  - In bridge: {bridge_cov['in_bridge']:,}
    - With EIN in company_master: TBD
    - Without EIN: TBD

The 'NO_STATE' error likely means:
  - The ERROR was logged when trying to match, but the FILING doesn't have state
  - OR the COMPANY doesn't have state in the system that tracks this
  
Let's check the actual error table to see what it records...
""")
    
    conn.close()

if __name__ == '__main__':
    main()
