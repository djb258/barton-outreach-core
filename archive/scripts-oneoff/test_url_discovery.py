#!/usr/bin/env python3
"""
Test URL Discovery Methods - Diagnose what works for Tier 0 FREE.

The DuckDuckGo approach is timing out/blocking.
This tests alternative approaches:
1. Domain construction + validation
2. Check existing records in DB
"""

import os
import re
import httpx
import psycopg2
from urllib.parse import urlparse

def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def construct_likely_domains(company_name: str) -> list:
    """Construct likely domain patterns from company name."""
    name = company_name.lower()
    # Remove common suffixes
    for suffix in [' inc', ' llc', ' corp', ' corporation', ' company', ' co', 
                   ' ltd', ' limited', ' lp', ' associates', ' group', ' services', 
                   ' consulting', ' enterprises', ' holdings', ' partners']:
        name = name.replace(suffix, '')
    name = name.strip()
    
    # Create slug versions
    slug1 = re.sub(r'[^a-z0-9]', '', name)  # nospacesnospecial
    slug2 = re.sub(r'[^a-z0-9]+', '-', name).strip('-')  # with-dashes
    
    # Generate possible domains
    domains = []
    for slug in [slug1, slug2]:
        if slug and len(slug) >= 3:
            domains.extend([
                f"https://www.{slug}.com",
                f"https://{slug}.com",
            ])
    
    # Also try first word if multi-word
    words = name.split()
    if len(words) > 1 and len(words[0]) >= 3:
        domains.append(f"https://www.{words[0]}.com")
    
    return list(dict.fromkeys(domains))[:6]


def validate_url(url: str, timeout: float = 5.0) -> bool:
    """Check if URL is reachable."""
    try:
        with httpx.Client() as client:
            resp = client.head(url, timeout=timeout, follow_redirects=True)
            return resp.status_code < 400
    except:
        return False


def main():
    print("="*70)
    print("URL DISCOVERY DIAGNOSTIC")
    print("="*70)
    
    # Get sample DOL records
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT DISTINCT sponsor_dfe_ein, sponsor_dfe_name, spons_dfe_mail_us_city, spons_dfe_mail_us_state
        FROM dol.form_5500
        WHERE spons_dfe_mail_us_state = 'NC'
        AND sponsor_dfe_ein IS NOT NULL
        AND sponsor_dfe_name IS NOT NULL
        LIMIT 20
    """)
    
    records = cur.fetchall()
    print(f"\nSample DOL records from NC: {len(records)}")
    
    # Test domain construction
    print("\n" + "="*70)
    print("TESTING DOMAIN CONSTRUCTION + VALIDATION")
    print("="*70)
    
    found = 0
    for ein, name, city, state in records[:10]:
        domains = construct_likely_domains(name)
        print(f"\n{name[:50]}")
        print(f"  Candidates: {domains[:3]}")
        
        # Try to validate
        for url in domains:
            if validate_url(url):
                print(f"  ✓ VALID: {url}")
                found += 1
                break
        else:
            print(f"  ✗ No valid URL found")
    
    print(f"\n\nRESULT: Found {found}/10 via domain construction")
    
    # Alternative: Check what's already matched
    print("\n" + "="*70)
    print("CHECK: DOL records already matched to company_master")
    print("="*70)
    
    cur.execute("""
        SELECT COUNT(*) 
        FROM company.company_master 
        WHERE ein IS NOT NULL AND website_url IS NOT NULL
    """)
    matched = cur.fetchone()[0]
    
    cur.execute("""
        SELECT COUNT(DISTINCT sponsor_dfe_ein) FROM dol.form_5500 
        WHERE spons_dfe_mail_us_state IN ('NC', 'PA', 'OH', 'VA', 'MD', 'KY', 'OK', 'WV', 'DE')
    """)
    dol_total = cur.fetchone()[0]
    
    print(f"Company master with EIN + URL: {matched:,}")
    print(f"DOL records in target states: {dol_total:,}")
    
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
