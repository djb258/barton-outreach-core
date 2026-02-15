#!/usr/bin/env python3
"""
NC Company vs 5500 Match Analysis
==================================
Find matches between NC companies (without EIN) and Form 5500 filings.
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
    print("NC COMPANIES vs FORM 5500 MATCHING ANALYSIS")
    print("=" * 80)
    
    # How many NC companies do we have?
    cur.execute("""
        SELECT COUNT(*) as total,
               COUNT(ein) as with_ein
        FROM company.company_master
        WHERE address_state = 'NC'
    """)
    nc_companies = cur.fetchone()
    print(f"\nNC Companies in company_master:")
    print(f"  Total: {nc_companies['total']:,}")
    print(f"  With EIN: {nc_companies['with_ein']:,}")
    print(f"  Without EIN: {nc_companies['total'] - nc_companies['with_ein']:,}")
    
    # How many NC 5500 filings do we have?
    cur.execute("""
        SELECT COUNT(*) as total,
               COUNT(DISTINCT sponsor_dfe_ein) as unique_eins
        FROM dol.form_5500
        WHERE spons_dfe_mail_us_state = 'NC'
    """)
    nc_filings = cur.fetchone()
    print(f"\nNC Form 5500 filings:")
    print(f"  Total filings: {nc_filings['total']:,}")
    print(f"  Unique EINs: {nc_filings['unique_eins']:,}")
    
    # Try fuzzy matching NC companies to NC 5500s
    print("\n" + "=" * 80)
    print("FUZZY MATCHING: NC Companies → NC 5500 Filings")
    print("=" * 80)
    
    # Match by State + City + Name similarity
    cur.execute("""
        WITH nc_companies_no_ein AS (
            SELECT company_unique_id, company_name, address_city
            FROM company.company_master
            WHERE address_state = 'NC'
              AND ein IS NULL
              AND address_city IS NOT NULL
        ),
        nc_filings AS (
            SELECT DISTINCT ON (sponsor_dfe_ein)
                sponsor_dfe_ein,
                sponsor_dfe_name,
                spons_dfe_mail_us_city
            FROM dol.form_5500
            WHERE spons_dfe_mail_us_state = 'NC'
              AND sponsor_dfe_ein IS NOT NULL
            ORDER BY sponsor_dfe_ein, form_year DESC NULLS LAST
        ),
        matches AS (
            SELECT 
                c.company_unique_id,
                c.company_name,
                c.address_city,
                f.sponsor_dfe_ein,
                f.sponsor_dfe_name,
                f.spons_dfe_mail_us_city,
                SIMILARITY(LOWER(c.company_name), LOWER(f.sponsor_dfe_name)) as name_sim
            FROM nc_companies_no_ein c
            JOIN nc_filings f 
                ON LOWER(TRIM(c.address_city)) = LOWER(TRIM(f.spons_dfe_mail_us_city))
            WHERE SIMILARITY(LOWER(c.company_name), LOWER(f.sponsor_dfe_name)) > 0.5
        )
        SELECT * FROM matches
        ORDER BY name_sim DESC
        LIMIT 50
    """)
    
    matches = cur.fetchall()
    print(f"\nFound {len(matches)} potential matches (similarity > 0.5):")
    print(f"\n{'Sim':>5} {'Company Name':<35} {'5500 Name':<35} {'City':<15}")
    print("-" * 95)
    
    for m in matches[:30]:
        cname = (m['company_name'] or '')[:33]
        fname = (m['sponsor_dfe_name'] or '')[:33]
        city = (m['address_city'] or '')[:13]
        print(f"{m['name_sim']:>5.2f} {cname:<35} {fname:<35} {city:<15}")
    
    if len(matches) > 30:
        print(f"... and {len(matches) - 30} more")
    
    # Similarity distribution
    print("\n" + "=" * 80)
    print("SIMILARITY DISTRIBUTION")
    print("=" * 80)
    
    cur.execute("""
        WITH nc_companies_no_ein AS (
            SELECT company_unique_id, company_name, address_city
            FROM company.company_master
            WHERE address_state = 'NC'
              AND ein IS NULL
              AND address_city IS NOT NULL
        ),
        nc_filings AS (
            SELECT DISTINCT ON (sponsor_dfe_ein)
                sponsor_dfe_ein,
                sponsor_dfe_name,
                spons_dfe_mail_us_city
            FROM dol.form_5500
            WHERE spons_dfe_mail_us_state = 'NC'
              AND sponsor_dfe_ein IS NOT NULL
            ORDER BY sponsor_dfe_ein, form_year DESC NULLS LAST
        ),
        matches AS (
            SELECT 
                c.company_unique_id,
                SIMILARITY(LOWER(c.company_name), LOWER(f.sponsor_dfe_name)) as name_sim
            FROM nc_companies_no_ein c
            JOIN nc_filings f 
                ON LOWER(TRIM(c.address_city)) = LOWER(TRIM(f.spons_dfe_mail_us_city))
            WHERE SIMILARITY(LOWER(c.company_name), LOWER(f.sponsor_dfe_name)) > 0.4
        )
        SELECT 
            CASE 
                WHEN name_sim >= 0.95 THEN '0.95-1.00 (Excellent)'
                WHEN name_sim >= 0.90 THEN '0.90-0.95 (Very High)'
                WHEN name_sim >= 0.85 THEN '0.85-0.90 (High)'
                WHEN name_sim >= 0.80 THEN '0.80-0.85 (Good)'
                WHEN name_sim >= 0.75 THEN '0.75-0.80 (Moderate)'
                WHEN name_sim >= 0.70 THEN '0.70-0.75 (Low)'
                WHEN name_sim >= 0.60 THEN '0.60-0.70 (Very Low)'
                ELSE '0.40-0.60 (Marginal)'
            END as bracket,
            COUNT(*) as cnt
        FROM matches
        GROUP BY 1
        ORDER BY 1 DESC
    """)
    
    print(f"\n{'Bracket':<25} {'Count':>10}")
    print("-" * 37)
    total_matches = 0
    for row in cur.fetchall():
        print(f"{row['bracket']:<25} {row['cnt']:>10,}")
        total_matches += row['cnt']
    print(f"{'TOTAL':<25} {total_matches:>10,}")
    
    # Now let's check why existing fuzzy matching isn't finding these
    print("\n" + "=" * 80)
    print("DIAGNOSIS: WHY AREN'T THESE BEING MATCHED?")
    print("=" * 80)
    
    # Check if these NC companies are in the outreach universe
    cur.execute("""
        SELECT COUNT(DISTINCT o.outreach_id) as in_outreach
        FROM company.company_master cm
        JOIN cl.company_identity_bridge b ON cm.company_unique_id = b.source_company_id
        JOIN outreach.outreach o ON b.company_sov_id = o.sovereign_id
        WHERE cm.address_state = 'NC'
          AND cm.ein IS NULL
    """)
    in_outreach = cur.fetchone()['in_outreach']
    print(f"\nNC companies without EIN that are in outreach: {in_outreach:,}")
    
    # Check what the ein_matcher is doing
    print("\nein_matcher.py uses State + City + Name matching")
    print("Let's verify the exact query it runs...")
    
    # Run the EXACT same query as ein_matcher for NC
    cur.execute("""
        WITH ranked_matches AS (
            SELECT
                cm.company_unique_id,
                cm.company_name,
                cm.address_city,
                cm.address_state,
                d.sponsor_dfe_ein as dol_ein,
                d.sponsor_dfe_name as dol_name,
                SIMILARITY(LOWER(cm.company_name), LOWER(d.sponsor_dfe_name)) as similarity,
                ROW_NUMBER() OVER (
                    PARTITION BY cm.company_unique_id
                    ORDER BY SIMILARITY(LOWER(cm.company_name), LOWER(d.sponsor_dfe_name)) DESC
                ) as rn
            FROM company.company_master cm
            JOIN dol.form_5500 d
                ON cm.address_state = d.spons_dfe_mail_us_state
                AND LOWER(TRIM(cm.address_city)) = LOWER(TRIM(d.spons_dfe_mail_us_city))
            WHERE cm.ein IS NULL
              AND cm.company_unique_id IS NOT NULL
              AND d.sponsor_dfe_ein IS NOT NULL
              AND cm.address_state = 'NC'
              AND SIMILARITY(LOWER(cm.company_name), LOWER(d.sponsor_dfe_name)) > 0.75
        )
        SELECT * FROM ranked_matches WHERE rn = 1
        ORDER BY similarity DESC
        LIMIT 20
    """)
    
    ein_matches = cur.fetchall()
    print(f"\nein_matcher query (threshold 0.75) for NC: {len(ein_matches)} matches")
    
    if ein_matches:
        print(f"\n{'Sim':>5} {'Company':<30} {'5500 Name':<30} {'City':<15}")
        print("-" * 85)
        for m in ein_matches[:15]:
            print(f"{m['similarity']:>5.2f} {m['company_name'][:28]:<30} {m['dol_name'][:28]:<30} {m['address_city'][:13]:<15}")
    
    # Total count at 0.75
    cur.execute("""
        SELECT COUNT(*) as cnt
        FROM company.company_master cm
        JOIN dol.form_5500 d
            ON cm.address_state = d.spons_dfe_mail_us_state
            AND LOWER(TRIM(cm.address_city)) = LOWER(TRIM(d.spons_dfe_mail_us_city))
        WHERE cm.ein IS NULL
          AND cm.company_unique_id IS NOT NULL
          AND d.sponsor_dfe_ein IS NOT NULL
          AND cm.address_state = 'NC'
          AND SIMILARITY(LOWER(cm.company_name), LOWER(d.sponsor_dfe_name)) > 0.75
    """)
    total_75 = cur.fetchone()['cnt']
    print(f"\nTotal NC matches at 0.75 threshold: {total_75:,}")
    
    # At 0.70
    cur.execute("""
        SELECT COUNT(*) as cnt
        FROM company.company_master cm
        JOIN dol.form_5500 d
            ON cm.address_state = d.spons_dfe_mail_us_state
            AND LOWER(TRIM(cm.address_city)) = LOWER(TRIM(d.spons_dfe_mail_us_city))
        WHERE cm.ein IS NULL
          AND cm.company_unique_id IS NOT NULL
          AND d.sponsor_dfe_ein IS NOT NULL
          AND cm.address_state = 'NC'
          AND SIMILARITY(LOWER(cm.company_name), LOWER(d.sponsor_dfe_name)) > 0.70
    """)
    total_70 = cur.fetchone()['cnt']
    print(f"Total NC matches at 0.70 threshold: {total_70:,}")
    
    # At 0.60
    cur.execute("""
        SELECT COUNT(*) as cnt
        FROM company.company_master cm
        JOIN dol.form_5500 d
            ON cm.address_state = d.spons_dfe_mail_us_state
            AND LOWER(TRIM(cm.address_city)) = LOWER(TRIM(d.spons_dfe_mail_us_city))
        WHERE cm.ein IS NULL
          AND cm.company_unique_id IS NOT NULL
          AND d.sponsor_dfe_ein IS NOT NULL
          AND cm.address_state = 'NC'
          AND SIMILARITY(LOWER(cm.company_name), LOWER(d.sponsor_dfe_name)) > 0.60
    """)
    total_60 = cur.fetchone()['cnt']
    print(f"Total NC matches at 0.60 threshold: {total_60:,}")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print(f"""
1. Run ein_matcher.py for NC at lower thresholds:
   - At 0.75: {total_75:,} matches available
   - At 0.70: {total_70:,} matches available  
   - At 0.60: {total_60:,} matches available

2. Command to run:
   python hubs/dol-filings/imo/middle/ein_matcher.py --state NC --threshold 0.70

3. After EIN backfill, run promote_dol_via_bridge.py to create DOL records
""")

if __name__ == '__main__':
    main()
