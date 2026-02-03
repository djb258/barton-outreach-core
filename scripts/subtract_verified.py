#!/usr/bin/env python3
"""
Subtract verified domains from total to get domains needing pattern lookup.
"""
import psycopg2
import os

def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    print('='*60)
    print('SUBTRACT VERIFIED DOMAINS')
    print('='*60)
    print()
    
    # Check people_master structure first
    cur.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_schema = 'people' AND table_name = 'people_master'
        ORDER BY ordinal_position
    """)
    pm_cols = [r[0] for r in cur.fetchall()]
    print(f"people_master columns: {pm_cols}")
    print()
    
    # Total unique domains in outreach
    cur.execute("SELECT COUNT(DISTINCT domain) FROM outreach.outreach")
    total_domains = cur.fetchone()[0]
    print(f"Total outreach domains: {total_domains:,}")
    
    # Get domains with verified emails
    # Need to extract domain from email address
    cur.execute("""
        SELECT COUNT(DISTINCT SPLIT_PART(email, '@', 2))
        FROM people.people_master 
        WHERE email_verified = true 
        AND email IS NOT NULL
        AND email LIKE '%@%'
    """)
    verified_email_domains = cur.fetchone()[0]
    print(f"Domains with verified emails (people_master): {verified_email_domains:,}")
    
    # Also check outreach.people
    cur.execute("""
        SELECT COUNT(DISTINCT SPLIT_PART(email, '@', 2))
        FROM outreach.people 
        WHERE email_verified = true 
        AND email IS NOT NULL
        AND email LIKE '%@%'
    """)
    verified_outreach = cur.fetchone()[0]
    print(f"Domains with verified emails (outreach.people): {verified_outreach:,}")
    
    # Get INTERSECTION - domains that are BOTH in outreach AND have verified email
    cur.execute("""
        WITH verified_domains AS (
            SELECT DISTINCT SPLIT_PART(email, '@', 2) as domain
            FROM people.people_master 
            WHERE email_verified = true 
            AND email IS NOT NULL AND email LIKE '%@%'
            
            UNION
            
            SELECT DISTINCT SPLIT_PART(email, '@', 2) as domain
            FROM outreach.people 
            WHERE email_verified = true 
            AND email IS NOT NULL AND email LIKE '%@%'
        )
        SELECT COUNT(DISTINCT o.domain)
        FROM outreach.outreach o
        JOIN verified_domains v ON LOWER(o.domain) = LOWER(v.domain)
    """)
    outreach_with_verified = cur.fetchone()[0]
    
    print()
    print('='*60)
    print('FINAL CALCULATION')
    print('='*60)
    print(f"Total outreach domains:           {total_domains:,}")
    print(f"Domains with VERIFIED email:      {outreach_with_verified:,}")
    print(f"Domains NEEDING pattern lookup:   {total_domains - outreach_with_verified:,}")
    print()
    print(f"Cost @ $0.01/lookup: ${(total_domains - outreach_with_verified) * 0.01:.0f}")
    
    conn.close()

if __name__ == '__main__':
    main()
