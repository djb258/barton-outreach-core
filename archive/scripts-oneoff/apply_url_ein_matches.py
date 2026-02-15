#!/usr/bin/env python3
"""
Apply URL-based EIN matches to company_master.

Backfills EIN from DOL records where:
1. Domain heuristic from company name matches company_master URL
2. Same state
3. Name similarity > 0.6 (high confidence)

This is a Tier 0 FREE operation - no API calls.
"""

import os
import re
from difflib import SequenceMatcher
import psycopg2
from psycopg2.extras import execute_values

def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def extract_domain(url: str) -> str | None:
    """Extract domain from URL."""
    if not url:
        return None
    url = url.lower().strip()
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^www\.', '', url)
    domain = url.split('/')[0]
    return domain if domain else None

def name_to_domain_candidates(name: str) -> list[str]:
    """Generate potential domain candidates from company name."""
    if not name:
        return []
    
    name = name.lower()
    # Remove common suffixes
    for suffix in [', inc.', ', inc', ' inc.', ' inc', ', llc', ' llc', 
                   ', ltd', ' ltd', ', corp', ' corp', ' corporation',
                   ', co.', ' co.', ' company', ' companies', ' group',
                   ' holdings', ' partners', ' solutions', ' services',
                   ' technologies', ' technology', ', p.c.', ' p.c.',
                   ' international', ' consulting']:
        name = name.replace(suffix, '')
    
    # Clean special chars
    clean = re.sub(r'[^a-z0-9\s]', '', name).strip()
    words = clean.split()
    
    candidates = []
    if words:
        # Full name joined
        candidates.append(''.join(words) + '.com')
        # First word only
        candidates.append(words[0] + '.com')
        # First two words
        if len(words) >= 2:
            candidates.append(''.join(words[:2]) + '.com')
        # With hyphens
        candidates.append('-'.join(words) + '.com')
    
    return list(set(candidates))

def similarity(a: str, b: str) -> float:
    """Calculate string similarity."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def main():
    print("=" * 80)
    print("APPLYING URL-BASED EIN MATCHES TO COMPANY_MASTER")
    print("=" * 80)
    
    conn = get_conn()
    cur = conn.cursor()
    
    # Step 1: Build domain index from company_master (companies WITHOUT EIN)
    print("\n1. Building domain index from company_master (no EIN)...")
    cur.execute("""
        SELECT company_unique_id, company_name, website_url, address_state
        FROM company.company_master
        WHERE ein IS NULL
          AND website_url IS NOT NULL
          AND website_url != ''
    """)
    
    domain_index = {}  # domain -> list of (id, name, state)
    for row in cur.fetchall():
        cid, cname, url, state = row
        domain = extract_domain(url)
        if domain:
            if domain not in domain_index:
                domain_index[domain] = []
            domain_index[domain].append((cid, cname, state))
    
    print(f"   Domains indexed: {len(domain_index):,}")
    
    # Step 2: Get unmatched DOL EINs from target states
    print("\n2. Fetching unmatched DOL records from target states...")
    cur.execute("""
        WITH matched_eins AS (
            SELECT DISTINCT ein FROM company.company_master WHERE ein IS NOT NULL
        )
        SELECT DISTINCT f.sponsor_dfe_ein, f.sponsor_dfe_name, f.spons_dfe_mail_us_state
        FROM dol.form_5500 f
        LEFT JOIN matched_eins m ON f.sponsor_dfe_ein = m.ein
        WHERE m.ein IS NULL
          AND f.spons_dfe_mail_us_state IN ('NC', 'PA', 'OH', 'VA', 'MD', 'KY', 'OK', 'WV', 'DE')
          AND f.sponsor_dfe_ein IS NOT NULL
        
        UNION
        
        SELECT DISTINCT sf.sf_spons_ein, sf.sf_sponsor_name, sf.sf_spons_us_state  
        FROM dol.form_5500_sf sf
        LEFT JOIN matched_eins m ON sf.sf_spons_ein = m.ein
        WHERE m.ein IS NULL
          AND sf.sf_spons_us_state IN ('NC', 'PA', 'OH', 'VA', 'MD', 'KY', 'OK', 'WV', 'DE')
          AND sf.sf_spons_ein IS NOT NULL
    """)
    
    dol_records = cur.fetchall()
    print(f"   DOL records to test: {len(dol_records):,}")
    
    # Step 3: Match DOL records to domains
    print("\n3. Matching DOL records to company_master via domains...")
    
    matches = []  # (company_id, ein, dol_name, company_name, similarity)
    
    for ein, dol_name, dol_state in dol_records:
        if not dol_name:
            continue
            
        candidates = name_to_domain_candidates(dol_name)
        
        for candidate in candidates:
            if candidate in domain_index:
                for cid, cname, cstate in domain_index[candidate]:
                    # Must be same state for high confidence
                    if cstate and dol_state and cstate.upper() == dol_state.upper():
                        sim = similarity(dol_name, cname)
                        if sim > 0.6:  # High confidence threshold
                            matches.append((cid, ein, dol_name, cname, sim))
    
    # Deduplicate - take highest similarity per company
    best_matches = {}
    for cid, ein, dol_name, cname, sim in matches:
        if cid not in best_matches or sim > best_matches[cid][4]:
            best_matches[cid] = (cid, ein, dol_name, cname, sim)
    
    matches = list(best_matches.values())
    print(f"   High-confidence matches found: {len(matches)}")
    
    if not matches:
        print("\n   No matches to apply!")
        return
    
    # Step 4: Show sample matches
    print("\n4. Sample matches to be applied:")
    print("-" * 80)
    for cid, ein, dol_name, cname, sim in sorted(matches, key=lambda x: -x[4])[:15]:
        print(f"   {dol_name[:35]:<35} -> {cname[:25]:<25} | EIN: {ein} | sim={sim:.2f}")
    print("-" * 80)
    
    # Step 5: Apply updates
    print(f"\n5. Applying {len(matches)} EIN updates to company_master...")
    
    update_data = [(ein, cid) for cid, ein, _, _, _ in matches]
    
    cur.executemany("""
        UPDATE company.company_master
        SET ein = %s,
            updated_at = NOW()
        WHERE company_unique_id = %s
    """, update_data)
    
    updated = cur.rowcount
    conn.commit()
    
    print(f"   ✓ Updated {updated} companies with EIN")
    
    # Step 6: Verify new totals
    print("\n6. Verifying new totals...")
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(ein) as with_ein,
            ROUND(100.0 * COUNT(ein) / COUNT(*), 1) as pct
        FROM company.company_master
    """)
    total, with_ein, pct = cur.fetchone()
    print(f"   Total companies: {total:,}")
    print(f"   Companies with EIN: {with_ein:,} ({pct}%)")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("COMPLETE!")
    print(f"  - {updated} companies received EIN backfill (FREE - Tier 0)")
    print(f"  - New EIN coverage: {pct}%")
    print("=" * 80)

if __name__ == "__main__":
    main()
