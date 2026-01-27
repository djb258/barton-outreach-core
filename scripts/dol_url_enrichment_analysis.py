#!/usr/bin/env python3
"""
Analyze DOL enrichment opportunity: Find URLs for DOL records, match back to company_master.

The idea:
1. DOL has ~18,600 unmatched EINs in our target states (PA, OH, VA, NC, MD, etc.)
2. If we could find URLs for those DOL company names
3. We could match back to our 73k companies that have URLs

Options per SNAP_ON_TOOLBOX:
- GooglePlaces (Tier 1): $0.017/call, 1000/day - could validate/lookup business
- Firecrawl (Tier 1): Free 500/month - scrape search results
- Free options: Use domain heuristics from company name
"""

import psycopg2
import os
import re

def extract_domain_candidates(company_name: str) -> list[str]:
    """
    Generate possible domain candidates from a company name.
    This is FREE (Tier 0) - just string manipulation.
    """
    candidates = []
    
    # Clean the name
    name = company_name.lower()
    name = re.sub(r',?\s*(inc\.?|llc|corp\.?|ltd\.?|co\.?|l\.?p\.?)$', '', name, flags=re.I)
    name = re.sub(r'^the\s+', '', name, flags=re.I)
    name = re.sub(r'[^a-z0-9\s]', '', name)
    name = name.strip()
    
    # Generate candidates
    words = name.split()
    
    if len(words) >= 1:
        # Single word / first word
        candidates.append(f"{words[0]}.com")
        
        # All words concatenated
        candidates.append(f"{''.join(words)}.com")
        
        # First letters (acronym)
        if len(words) >= 2:
            acronym = ''.join(w[0] for w in words if w)
            if len(acronym) >= 2:
                candidates.append(f"{acronym}.com")
        
        # First two words
        if len(words) >= 2:
            candidates.append(f"{words[0]}{words[1]}.com")
            candidates.append(f"{words[0]}-{words[1]}.com")
    
    return candidates

def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    print('='*80)
    print('DOL ENRICHMENT ANALYSIS: URL MATCHING OPPORTUNITY')
    print('='*80)
    
    # 1. Get all URLs from company_master (normalized)
    print()
    print('1. BUILDING URL INDEX FROM COMPANY_MASTER...')
    print('-'*60)
    cur.execute('''
        SELECT 
            company_unique_id,
            website_url,
            company_name,
            ein
        FROM company.company_master
        WHERE website_url IS NOT NULL AND website_url != ''
    ''')
    
    url_to_company = {}
    for r in cur.fetchall():
        company_id, url, name, ein = r
        # Normalize URL to domain
        domain = url.lower()
        domain = re.sub(r'^https?://', '', domain)
        domain = re.sub(r'^www\.', '', domain)
        domain = domain.split('/')[0]
        
        if domain and domain not in url_to_company:
            url_to_company[domain] = {
                'company_unique_id': company_id,
                'company_name': name,
                'ein': ein
            }
    
    print(f'  Unique domains indexed: {len(url_to_company):,}')
    
    # 2. Try to match DOL records using domain heuristics (FREE!)
    print()
    print('2. TESTING DOMAIN HEURISTIC MATCHING (FREE):')
    print('-'*60)
    
    cur.execute('''
        WITH matched_eins AS (
            SELECT DISTINCT ein FROM company.company_master WHERE ein IS NOT NULL
        )
        SELECT DISTINCT ON (f.sponsor_dfe_ein)
            f.sponsor_dfe_ein,
            f.sponsor_dfe_name,
            f.spons_dfe_mail_us_state
        FROM dol.form_5500 f
        WHERE f.sponsor_dfe_ein IS NOT NULL
        AND f.spons_dfe_mail_us_state IN ('PA', 'OH', 'VA', 'NC', 'MD', 'KY', 'OK', 'WV', 'DE')
        AND f.sponsor_dfe_ein NOT IN (SELECT ein FROM matched_eins)
        LIMIT 1000
    ''')
    
    matches_found = []
    tested = 0
    
    for r in cur.fetchall():
        ein, name, state = r
        tested += 1
        
        candidates = extract_domain_candidates(name)
        for domain in candidates:
            if domain in url_to_company:
                company = url_to_company[domain]
                if not company['ein']:  # Only match if company doesn't have EIN yet
                    matches_found.append({
                        'dol_ein': ein,
                        'dol_name': name,
                        'dol_state': state,
                        'domain': domain,
                        'company_id': company['company_unique_id'],
                        'company_name': company['company_name']
                    })
                break
    
    print(f'  DOL records tested: {tested}')
    print(f'  Matches found via domain heuristic: {len(matches_found)}')
    
    if matches_found:
        print()
        print('  Sample matches:')
        for m in matches_found[:10]:
            print(f"    DOL: {m['dol_name'][:30]:30} -> {m['domain']:25} -> CM: {m['company_name'][:25]}")
    
    # 3. Estimate potential with GooglePlaces lookup
    print()
    print('3. GOOGLEPLACES ENRICHMENT ESTIMATE:')
    print('-'*60)
    print('  Per SNAP_ON_TOOLBOX (TOOL-015):')
    print('    - Tier 1: $0.017/call')
    print('    - Rate limit: 1000/day')
    print('    - Monthly budget cap: $50')
    print()
    
    cur.execute('''
        WITH matched_eins AS (
            SELECT DISTINCT ein FROM company.company_master WHERE ein IS NOT NULL
        )
        SELECT COUNT(DISTINCT f.sponsor_dfe_ein) as unmatched
        FROM dol.form_5500 f
        WHERE f.sponsor_dfe_ein IS NOT NULL
        AND f.spons_dfe_mail_us_state IN ('PA', 'OH', 'VA', 'NC', 'MD', 'KY', 'OK', 'WV', 'DE')
        AND f.sponsor_dfe_ein NOT IN (SELECT ein FROM matched_eins)
    ''')
    unmatched = cur.fetchone()[0]
    
    print(f'  Unmatched DOL EINs in target states: {unmatched:,}')
    print(f'  Cost to lookup all: ${unmatched * 0.017:,.2f}')
    print(f'  Days at 1000/day: {unmatched // 1000}')
    print()
    print('  Strategy: Sample first, then scale if high match rate')
    
    # 4. Alternative: Use company_master URL patterns to infer DOL URLs
    print()
    print('4. REVERSE DOMAIN INFERENCE:')
    print('-'*60)
    print('  Many company URLs follow patterns:')
    print('    - companyname.com')
    print('    - companynamegroup.com')
    print('    - companyname-state.com')
    print()
    
    # Check if any DOL names contain ".com" or similar (some might!)
    cur.execute('''
        SELECT sponsor_dfe_name, spons_dfe_dba_name
        FROM dol.form_5500
        WHERE sponsor_dfe_name ILIKE '%.com%' 
           OR sponsor_dfe_name ILIKE '%.net%'
           OR sponsor_dfe_name ILIKE '%.org%'
        LIMIT 10
    ''')
    results = cur.fetchall()
    if results:
        print('  DOL names containing domain-like strings:')
        for r in results:
            print(f'    {r[0]}')
    else:
        print('  No DOL names contain obvious domain strings')
    
    conn.close()
    
    print()
    print('='*80)
    print('RECOMMENDATIONS')
    print('='*80)
    print('''
1. DOMAIN HEURISTIC (FREE - Tier 0):
   - Generate domain candidates from DOL company names
   - Match against company_master URL index
   - Expected hit rate: ~5-10%
   
2. GOOGLEPLACES LOOKUP (Tier 1 - $0.017/call):
   - Search: "{company_name} {city} {state}"
   - Get business website from results
   - Match website to company_master
   - Gated: Only for high-value unmatched records
   
3. DNS/WHOIS CHECK (FREE - Tier 0):
   - Check if generated domains actually exist
   - Filter candidates before matching
   - Use MXLookup (TOOL-004) as proxy for domain validity
''')

if __name__ == '__main__':
    main()
