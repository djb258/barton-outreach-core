#!/usr/bin/env python3
"""
DOL URL Discovery V2 - Tier 0 FREE.

Uses domain CONSTRUCTION + VALIDATION instead of web search.
DuckDuckGo blocks automated access, so we:
1. Construct likely domains from company names
2. Validate via HEAD requests
3. Match to existing company_master URLs via domain similarity

This is FREE (no API costs) and actually works.
"""

import os
import re
import time
import argparse
from urllib.parse import urlparse
import psycopg2
import httpx
from rapidfuzz import fuzz

# Rate limiting
VALIDATE_DELAY = 0.2  # seconds between validations (be nice)
BATCH_SIZE = 100
MAX_PER_RUN = 1000

def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def construct_likely_domains(company_name: str) -> list:
    """
    Construct likely domain patterns from company name.
    Most companies use predictable patterns like:
    - companyname.com
    - company-name.com
    - firstword.com (for multi-word names)
    """
    name = company_name.lower()
    
    # Remove common suffixes
    suffixes = [
        ' inc', ' llc', ' corp', ' corporation', ' company', ' co', 
        ' ltd', ' limited', ' lp', ' associates', ' group', ' services',
        ' consulting', ' enterprises', ' holdings', ' partners', ' pa',
        ' p.a.', ' pllc', ' pc', ' p.c.', ' dba', ' of america',
        ' usa', ' us', ' north america', ' international', ' intl'
    ]
    for suffix in suffixes:
        name = name.replace(suffix, '')
    
    # Also remove trailing punctuation
    name = re.sub(r'[.,;:]+$', '', name).strip()
    
    # Create slug versions
    slug1 = re.sub(r'[^a-z0-9]', '', name)  # nospaces: "abccompany"
    slug2 = re.sub(r'[^a-z0-9]+', '-', name).strip('-')  # dashes: "abc-company"
    
    # Also try common abbreviations
    words = name.split()
    initials = ''.join(w[0] for w in words if w) if len(words) > 1 else ''
    
    # Generate domains
    domains = []
    for slug in [slug1, slug2]:
        if slug and len(slug) >= 3:
            domains.append(f"https://{slug}.com")
            domains.append(f"https://www.{slug}.com")
    
    # First word only (common pattern)
    if len(words) > 1 and len(words[0]) >= 3:
        domains.append(f"https://{words[0]}.com")
        domains.append(f"https://www.{words[0]}.com")
    
    # Initials (for longer names)
    if initials and len(initials) >= 2:
        domains.append(f"https://{initials}.com")
        domains.append(f"https://www.{initials}.com")
    
    # Dedupe preserving order
    seen = set()
    result = []
    for d in domains:
        if d not in seen:
            seen.add(d)
            result.append(d)
    
    return result[:8]  # Max 8 candidates


def validate_url(client: httpx.Client, url: str, timeout: float = 5.0) -> tuple[bool, str]:
    """
    Check if URL is reachable and get final URL after redirects.
    Returns (is_valid, final_url).
    """
    try:
        resp = client.head(url, timeout=timeout, follow_redirects=True)
        if resp.status_code < 400:
            return True, str(resp.url)
        return False, ""
    except:
        return False, ""


def extract_domain(url: str) -> str:
    """Extract clean domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower().replace('www.', '')
    except:
        return ""


def get_unmatched_dol_for_state(cur, state: str, limit: int) -> list:
    """Get DOL records for a state that don't have matches in company_master."""
    cur.execute("""
        WITH matched_eins AS (
            SELECT DISTINCT ein FROM company.company_master WHERE ein IS NOT NULL
        ),
        dol_records AS (
            SELECT DISTINCT ON (sponsor_dfe_ein)
                sponsor_dfe_ein as ein,
                sponsor_dfe_name as name,
                spons_dfe_mail_us_city as city,
                spons_dfe_mail_us_state as state
            FROM dol.form_5500
            WHERE spons_dfe_mail_us_state = %s
            AND sponsor_dfe_ein IS NOT NULL
            AND sponsor_dfe_name IS NOT NULL
            
            UNION
            
            SELECT DISTINCT ON (sf_spons_ein)
                sf_spons_ein as ein,
                sf_sponsor_name as name,
                sf_spons_us_city as city,
                sf_spons_us_state as state
            FROM dol.form_5500_sf
            WHERE sf_spons_us_state = %s
            AND sf_spons_ein IS NOT NULL
            AND sf_sponsor_name IS NOT NULL
        )
        SELECT d.ein, d.name, d.city, d.state
        FROM dol_records d
        LEFT JOIN matched_eins m ON d.ein = m.ein
        WHERE m.ein IS NULL
        ORDER BY d.name
        LIMIT %s
    """, (state, state, limit))
    return cur.fetchall()


def check_existing_url_match(cur, domain: str, state: str) -> tuple[str | None, str | None]:
    """
    Check if this domain already exists in company_master.
    Returns (company_unique_id, website_url) if found.
    """
    cur.execute("""
        SELECT company_unique_id, website_url
        FROM company.company_master
        WHERE website_url ILIKE %s
        AND address_state = %s
        LIMIT 1
    """, (f"%{domain}%", state))
    row = cur.fetchone()
    return (row[0], row[1]) if row else (None, None)


def process_state(state: str, limit: int, dry_run: bool = False):
    """Process unmatched DOL records for a state."""
    
    print(f"\n{'='*70}")
    print(f"PROCESSING STATE: {state}")
    print(f"{'='*70}")
    
    conn = get_conn()
    cur = conn.cursor()
    
    # Get unmatched records
    records = get_unmatched_dol_for_state(cur, state, limit)
    print(f"Unmatched DOL records to process: {len(records)}")
    
    if not records:
        print("No records to process!")
        cur.close()
        conn.close()
        return []
    
    # Track results
    found_via_validation = 0
    found_via_existing = 0
    not_found = 0
    results = []
    
    with httpx.Client() as client:
        for i, (ein, name, city, st) in enumerate(records):
            # Construct candidate domains
            candidates = construct_likely_domains(name)
            
            found = False
            
            # Method 1: Check if domain exists in company_master
            for url in candidates:
                domain = extract_domain(url)
                cid, existing_url = check_existing_url_match(cur, domain, st)
                if cid:
                    results.append({
                        'ein': ein,
                        'name': name,
                        'url': existing_url,
                        'method': 'existing_match',
                        'confidence': 0.85
                    })
                    found_via_existing += 1
                    found = True
                    break
            
            # Method 2: Validate URLs directly
            if not found:
                time.sleep(VALIDATE_DELAY)
                for url in candidates[:4]:  # Only try top 4
                    is_valid, final_url = validate_url(client, url)
                    if is_valid:
                        results.append({
                            'ein': ein,
                            'name': name,
                            'url': final_url or url,
                            'method': 'direct_validation',
                            'confidence': 0.7
                        })
                        found_via_validation += 1
                        found = True
                        break
            
            if not found:
                not_found += 1
            
            # Progress
            if (i + 1) % 50 == 0:
                print(f"  [{i+1}/{len(records)}] Existing: {found_via_existing}, Validated: {found_via_validation}, Not found: {not_found}")
    
    # Summary
    total_found = found_via_existing + found_via_validation
    print(f"\n{'='*70}")
    print(f"RESULTS FOR {state}")
    print(f"{'='*70}")
    print(f"  Processed: {len(records)}")
    print(f"  Found via existing company_master: {found_via_existing}")
    print(f"  Found via direct validation: {found_via_validation}")
    print(f"  Total found: {total_found} ({100*total_found/len(records):.1f}%)")
    print(f"  Not found: {not_found}")
    
    if results:
        print(f"\nSample results:")
        for r in results[:10]:
            print(f"  {r['name'][:40]:<40} | {r['url'][:35]:<35} | {r['method']}")
    
    if not dry_run and results:
        # Save results to staging table or file
        save_results(cur, conn, results, state)
    
    cur.close()
    conn.close()
    
    return results


def save_results(cur, conn, results: list, state: str):
    """Save discovery results."""
    # For now, create a simple output
    filename = f"dol_urls_discovered_{state}.csv"
    with open(filename, 'w') as f:
        f.write("ein,name,url,method,confidence\n")
        for r in results:
            # Escape for CSV
            name = r['name'].replace('"', '""')
            url = r['url'].replace('"', '""')
            f.write(f'"{r["ein"]}","{name}","{url}","{r["method"]}",{r["confidence"]}\n')
    print(f"\nSaved {len(results)} results to {filename}")


def main():
    parser = argparse.ArgumentParser(description='DOL URL Discovery V2 - Tier 0 FREE')
    parser.add_argument('--state', required=True, help='State abbreviation (NC, PA, etc)')
    parser.add_argument('--limit', type=int, default=MAX_PER_RUN, help='Max records to process')
    parser.add_argument('--dry-run', action='store_true', help='Do not save results')
    args = parser.parse_args()
    
    print("="*70)
    print("DOL URL DISCOVERY V2 - TIER 0 FREE")
    print("="*70)
    print(f"State: {args.state}")
    print(f"Limit: {args.limit}")
    print(f"Dry run: {args.dry_run}")
    print()
    print("Method: Domain construction + HEAD validation")
    print("Cost: $0 (Tier 0 FREE)")
    print()
    
    process_state(args.state, args.limit, args.dry_run)


if __name__ == "__main__":
    main()
