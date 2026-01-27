#!/usr/bin/env python3
"""
Domain Construction for a single state
Usage: python domain_construction_by_state.py <STATE>
"""
import psycopg2
import csv
import re
import asyncio
import aiohttp
from urllib.parse import urlparse
import time
import sys
import os

# Common suffixes to strip
SUFFIXES = [
    ' INC.', ' INC', ' LLC', ' LLC.', ' LLP', ' LLP.', ' LP', ' LP.',
    ' CORP.', ' CORP', ' CORPORATION', ' CO.', ' CO', ' COMPANY',
    ' PC', ' P.C.', ' PA', ' P.A.', ' PLLC', ' P.L.L.C.',
    ' LTD.', ' LTD', ' LIMITED', ' GROUP', ' HOLDINGS',
    ' SERVICES', ' SOLUTIONS', ' ENTERPRISES', ' ASSOCIATES',
    ' MANAGEMENT', ' CONSULTING', ' INTERNATIONAL', ' GLOBAL',
    ',', '.', "'", '"'
]

NOISE_WORDS = ['THE', 'AND', 'OF', 'FOR', 'A', 'AN', '&']

def clean_company_name(name: str) -> str:
    name = name.upper().strip()
    for suffix in SUFFIXES:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
    words = name.split()
    words = [w for w in words if w not in NOISE_WORDS]
    return ' '.join(words)

def generate_domain_candidates(name: str) -> list:
    cleaned = clean_company_name(name)
    normalized = re.sub(r'[^a-zA-Z0-9\s]', '', cleaned.lower())
    words = normalized.split()
    
    if not words:
        return []
    
    candidates = []
    joined = ''.join(words)
    candidates.append(f"{joined}.com")
    
    if len(words) > 1:
        hyphenated = '-'.join(words)
        candidates.append(f"{hyphenated}.com")
    
    if len(words[0]) > 3:
        candidates.append(f"{words[0]}.com")
    
    if len(words) > 1:
        initials = ''.join(w[0] for w in words[:-1])
        candidates.append(f"{initials}{words[-1]}.com")
    
    if len(words) >= 2:
        candidates.append(f"{words[0]}{words[1]}.com")
    
    if len(words) > 1:
        abbrev = ''.join(w[:3] for w in words if len(w) >= 3)
        if len(abbrev) >= 4:
            candidates.append(f"{abbrev}.com")
    
    seen = set()
    unique = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique

async def check_domain(session: aiohttp.ClientSession, domain: str, timeout: float = 5.0) -> dict:
    for protocol in ['https://', 'http://']:
        url = f"{protocol}{domain}"
        try:
            async with session.head(url, timeout=aiohttp.ClientTimeout(total=timeout), 
                                    allow_redirects=True, ssl=False) as resp:
                final_url = str(resp.url)
                return {
                    'valid': True,
                    'url': final_url,
                    'status': resp.status,
                    'domain': urlparse(final_url).netloc
                }
        except Exception:
            continue
    return {'valid': False, 'url': None, 'status': None, 'domain': None}

async def resolve_company_domain(session: aiohttp.ClientSession, company_name: str) -> dict:
    candidates = generate_domain_candidates(company_name)
    for candidate in candidates:
        result = await check_domain(session, candidate)
        if result['valid']:
            return {
                'found': True,
                'domain': result['domain'],
                'url': result['url'],
                'candidate_tried': candidate
            }
    return {'found': False, 'domain': None, 'url': None, 'candidates_tried': candidates}

async def process_batch(rows: list, batch_size: int = 100) -> list:
    results = []
    connector = aiohttp.TCPConnector(limit=batch_size, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]
            tasks = [resolve_company_domain(session, r['company_name']) for r in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for row, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    result = {'found': False, 'domain': None, 'error': str(result)}
                result['ein'] = row['ein']
                result['company_name'] = row['company_name']
                result['city'] = row['city']
                result['state'] = row['state']
                results.append(result)
            
            pct = min(i+batch_size, len(rows)) / len(rows) * 100
            print(f"  [{rows[0]['state']}] {min(i+batch_size, len(rows)):,}/{len(rows):,} ({pct:.1f}%)")
    return results

def main(state: str):
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    print(f"=" * 70)
    print(f"DOMAIN CONSTRUCTION - STATE: {state}")
    print(f"=" * 70)
    
    # Get unmatched DOL records for this state
    query = """
    WITH matched_eins AS (
        SELECT DISTINCT ein FROM company.company_master WHERE ein IS NOT NULL
    ),
    dol_5500 AS (
        SELECT DISTINCT ON (sponsor_dfe_ein)
            sponsor_dfe_ein as ein,
            sponsor_dfe_name as company_name,
            spons_dfe_mail_us_city as city,
            spons_dfe_mail_us_state as state
        FROM dol.form_5500
        WHERE spons_dfe_mail_us_state = %s
        AND sponsor_dfe_ein NOT IN (SELECT ein FROM matched_eins)
        ORDER BY sponsor_dfe_ein, date_received DESC
    ),
    dol_sf AS (
        SELECT DISTINCT ON (sf_spons_ein)
            sf_spons_ein as ein,
            sf_sponsor_name as company_name,
            sf_spons_us_city as city,
            sf_spons_us_state as state
        FROM dol.form_5500_sf
        WHERE sf_spons_us_state = %s
        AND sf_spons_ein NOT IN (SELECT ein FROM matched_eins)
        AND sf_spons_ein NOT IN (SELECT ein FROM dol_5500)
        ORDER BY sf_spons_ein, date_received DESC
    )
    SELECT * FROM dol_5500
    UNION ALL
    SELECT * FROM dol_sf
    """
    
    cur.execute(query, (state, state))
    rows = [{'ein': r[0], 'company_name': r[1], 'city': r[2], 'state': r[3]} for r in cur.fetchall()]
    cur.close()
    conn.close()
    
    print(f"Found {len(rows):,} companies in {state}")
    print()
    
    if not rows:
        print("No records to process")
        return
    
    start = time.time()
    results = asyncio.run(process_batch(rows, batch_size=100))
    elapsed = time.time() - start
    
    found = [r for r in results if r.get('found')]
    not_found = [r for r in results if not r.get('found')]
    
    print()
    print(f"Completed {state} in {elapsed:.1f}s ({len(rows)/elapsed:.1f}/sec)")
    print(f"  Found: {len(found):,} ({len(found)/len(rows)*100:.1f}%)")
    print(f"  Not Found: {len(not_found):,}")
    
    # Save results
    output_file = f'scripts/domain_results_{state}.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ein', 'company_name', 'city', 'state', 'found', 'domain', 'url'])
        for r in results:
            writer.writerow([r['ein'], r['company_name'], r['city'], r['state'], 
                           r.get('found'), r.get('domain'), r.get('url')])
    
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python domain_construction_by_state.py <STATE>")
        print("States: NC, PA, OH, VA, MD, KY, OK, WV, DE")
        sys.exit(1)
    
    state = sys.argv[1].upper()
    main(state)
