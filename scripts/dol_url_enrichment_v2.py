#!/usr/bin/env python3
"""
DOL URL Enrichment - Refined approach with validation.

Strategy:
1. Build domain->company index from company_master
2. For unmatched DOL records, generate domain candidates
3. Validate match by checking name similarity too (not just domain)
4. Only accept high-confidence matches
"""

import psycopg2
import os
import re
from difflib import SequenceMatcher

def normalize_name(name: str) -> str:
    """Normalize company name for comparison."""
    name = name.lower()
    name = re.sub(r',?\s*(inc\.?|llc|corp\.?|ltd\.?|co\.?|l\.?p\.?|pllc|pc|lp)$', '', name, flags=re.I)
    name = re.sub(r'^the\s+', '', name, flags=re.I)
    name = re.sub(r'[^a-z0-9\s]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def name_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between two names."""
    n1 = normalize_name(name1)
    n2 = normalize_name(name2)
    return SequenceMatcher(None, n1, n2).ratio()

def extract_domain_from_url(url: str) -> str:
    """Extract clean domain from URL."""
    domain = url.lower()
    domain = re.sub(r'^https?://', '', domain)
    domain = re.sub(r'^www\.', '', domain)
    domain = domain.split('/')[0]
    return domain

def extract_domain_candidates(company_name: str) -> list[str]:
    """Generate possible domain candidates from company name."""
    candidates = []
    
    name = normalize_name(company_name)
    words = name.split()
    
    if not words:
        return []
    
    # Primary: all words joined
    candidates.append(f"{''.join(words)}.com")
    candidates.append(f"{'-'.join(words)}.com")
    
    # First word only (if distinctive)
    if len(words[0]) >= 4:
        candidates.append(f"{words[0]}.com")
    
    # First two words
    if len(words) >= 2:
        candidates.append(f"{words[0]}{words[1]}.com")
    
    # Acronym (only if 3+ chars)
    if len(words) >= 3:
        acronym = ''.join(w[0] for w in words if w)
        if len(acronym) >= 3:
            candidates.append(f"{acronym}.com")
    
    return list(set(candidates))

def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    print('='*80)
    print('DOL URL ENRICHMENT - REFINED MATCHING')
    print('='*80)
    
    # 1. Build domain->company index
    print()
    print('1. BUILDING DOMAIN INDEX...')
    print('-'*60)
    cur.execute('''
        SELECT 
            company_unique_id,
            website_url,
            company_name,
            address_state,
            ein
        FROM company.company_master
        WHERE website_url IS NOT NULL AND website_url != ''
        AND ein IS NULL  -- Only companies without EIN
    ''')
    
    domain_index = {}  # domain -> list of companies
    for r in cur.fetchall():
        company_id, url, name, state, ein = r
        domain = extract_domain_from_url(url)
        
        if domain:
            if domain not in domain_index:
                domain_index[domain] = []
            domain_index[domain].append({
                'company_unique_id': company_id,
                'company_name': name,
                'state': state,
                'ein': ein
            })
    
    print(f'  Domains indexed (companies without EIN): {len(domain_index):,}')
    
    # 2. Get unmatched DOL records
    print()
    print('2. MATCHING DOL RECORDS TO DOMAINS...')
    print('-'*60)
    
    cur.execute('''
        WITH matched_eins AS (
            SELECT DISTINCT ein FROM company.company_master WHERE ein IS NOT NULL
        )
        SELECT DISTINCT ON (f.sponsor_dfe_ein)
            f.sponsor_dfe_ein,
            f.sponsor_dfe_name,
            f.spons_dfe_mail_us_state,
            f.spons_dfe_mail_us_city
        FROM dol.form_5500 f
        WHERE f.sponsor_dfe_ein IS NOT NULL
        AND f.spons_dfe_mail_us_state IN ('PA', 'OH', 'VA', 'NC', 'MD', 'KY', 'OK', 'WV', 'DE')
        AND f.sponsor_dfe_ein NOT IN (SELECT ein FROM matched_eins)
    ''')
    
    high_confidence = []
    medium_confidence = []
    tested = 0
    
    for r in cur.fetchall():
        ein, dol_name, dol_state, dol_city = r
        tested += 1
        
        candidates = extract_domain_candidates(dol_name)
        
        for domain in candidates:
            if domain in domain_index:
                # Found domain match - validate with name similarity
                for company in domain_index[domain]:
                    sim = name_similarity(dol_name, company['company_name'])
                    state_match = (company['state'] == dol_state)
                    
                    match_data = {
                        'dol_ein': ein,
                        'dol_name': dol_name,
                        'dol_state': dol_state,
                        'dol_city': dol_city,
                        'domain': domain,
                        'company_id': company['company_unique_id'],
                        'company_name': company['company_name'],
                        'company_state': company['state'],
                        'similarity': sim,
                        'state_match': state_match
                    }
                    
                    # High confidence: same state AND similarity > 0.6
                    if state_match and sim > 0.6:
                        high_confidence.append(match_data)
                        break
                    # Medium confidence: similarity > 0.7 even if different state
                    elif sim > 0.7:
                        medium_confidence.append(match_data)
                        break
    
    print(f'  DOL records tested: {tested:,}')
    print(f'  High confidence matches (state + sim>0.6): {len(high_confidence)}')
    print(f'  Medium confidence matches (sim>0.7): {len(medium_confidence)}')
    
    if high_confidence:
        print()
        print('  HIGH CONFIDENCE MATCHES:')
        print('  ' + '-'*100)
        for m in high_confidence[:20]:
            print(f"    EIN {m['dol_ein']}: {m['dol_name'][:35]:35}")
            print(f"      -> {m['domain']:20} -> {m['company_name'][:35]:35} | sim={m['similarity']:.2f}")
            print()
    
    if medium_confidence:
        print()
        print('  MEDIUM CONFIDENCE MATCHES (review needed):')
        print('  ' + '-'*100)
        for m in medium_confidence[:10]:
            state_note = 'SAME' if m['state_match'] else f"DOL:{m['dol_state']} vs CM:{m['company_state']}"
            print(f"    EIN {m['dol_ein']}: {m['dol_name'][:35]:35}")
            print(f"      -> {m['domain']:20} -> {m['company_name'][:35]:35} | sim={m['similarity']:.2f} | {state_note}")
            print()
    
    # 3. Look for DOL companies that HAVE a domain in their name
    print()
    print('3. DOL COMPANIES WITH DOMAIN IN NAME:')
    print('-'*60)
    cur.execute('''
        WITH matched_eins AS (
            SELECT DISTINCT ein FROM company.company_master WHERE ein IS NOT NULL
        )
        SELECT DISTINCT
            f.sponsor_dfe_ein,
            f.sponsor_dfe_name,
            f.spons_dfe_mail_us_state
        FROM dol.form_5500 f
        WHERE f.sponsor_dfe_ein IS NOT NULL
        AND f.spons_dfe_mail_us_state IN ('PA', 'OH', 'VA', 'NC', 'MD', 'KY', 'OK', 'WV', 'DE')
        AND f.sponsor_dfe_ein NOT IN (SELECT ein FROM matched_eins)
        AND (
            f.sponsor_dfe_name ~* '\\.com'
            OR f.sponsor_dfe_name ~* '\\.net'
            OR f.sponsor_dfe_name ~* '\\.org'
            OR f.sponsor_dfe_name ~* '\\.io'
        )
    ''')
    
    domain_in_name = cur.fetchall()
    print(f'  Found: {len(domain_in_name)}')
    
    if domain_in_name:
        # Try to match these directly
        direct_matches = []
        for r in domain_in_name:
            ein, name, state = r
            # Extract domain from name
            match = re.search(r'([a-zA-Z0-9-]+\.(com|net|org|io))', name, re.I)
            if match:
                domain = match.group(1).lower()
                if domain in domain_index:
                    for company in domain_index[domain]:
                        direct_matches.append({
                            'dol_ein': ein,
                            'dol_name': name,
                            'domain': domain,
                            'company_name': company['company_name'],
                            'company_id': company['company_unique_id']
                        })
        
        print(f'  Direct domain matches from name: {len(direct_matches)}')
        for m in direct_matches[:10]:
            print(f"    {m['dol_name'][:40]:40} -> {m['company_name'][:30]}")
    
    # 4. Summary and recommendations
    print()
    print('='*80)
    print('SUMMARY')
    print('='*80)
    print(f'''
  FREE MATCHING RESULTS (Tier 0):
    - High confidence: {len(high_confidence)} companies can get EIN backfilled
    - Medium confidence: {len(medium_confidence)} (need review)
    - Direct domain match: {len(direct_matches) if domain_in_name else 0}
    
  NEXT STEPS:
    1. Apply high-confidence matches immediately (update company_master.ein)
    2. Review medium-confidence for manual approval
    3. Consider GooglePlaces for remaining ~18k unmatched
    
  COST ANALYSIS (if using GooglePlaces):
    - Remaining unmatched: ~{tested - len(high_confidence) - len(medium_confidence):,}
    - At $0.017/call: ~${(tested - len(high_confidence) - len(medium_confidence)) * 0.017:,.2f}
''')
    
    conn.close()

if __name__ == '__main__':
    main()
