#!/usr/bin/env python3
"""
Domain Construction + HEAD Validation
Takes company name, constructs likely domains, validates with HTTP HEAD
"""
import csv
import re
import asyncio
import aiohttp
from urllib.parse import urlparse
import time

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

# Words to remove from domain generation
NOISE_WORDS = ['THE', 'AND', 'OF', 'FOR', 'A', 'AN', '&']

def clean_company_name(name: str) -> str:
    """Clean company name for domain generation"""
    name = name.upper().strip()
    
    # Remove suffixes
    for suffix in SUFFIXES:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
    
    # Remove noise words
    words = name.split()
    words = [w for w in words if w not in NOISE_WORDS]
    
    return ' '.join(words)

def generate_domain_candidates(name: str) -> list:
    """Generate likely domain patterns from company name"""
    cleaned = clean_company_name(name)
    
    # Normalize to lowercase, remove special chars
    normalized = re.sub(r'[^a-zA-Z0-9\s]', '', cleaned.lower())
    words = normalized.split()
    
    if not words:
        return []
    
    candidates = []
    
    # Pattern 1: All words joined (minutemenstaffing.com)
    joined = ''.join(words)
    candidates.append(f"{joined}.com")
    
    # Pattern 2: Words with hyphens (minutemen-staffing.com)
    if len(words) > 1:
        hyphenated = '-'.join(words)
        candidates.append(f"{hyphenated}.com")
    
    # Pattern 3: First word only (minutemen.com)
    if len(words[0]) > 3:
        candidates.append(f"{words[0]}.com")
    
    # Pattern 4: Initials + last word (mstaffing.com)
    if len(words) > 1:
        initials = ''.join(w[0] for w in words[:-1])
        candidates.append(f"{initials}{words[-1]}.com")
    
    # Pattern 5: First two words joined
    if len(words) >= 2:
        candidates.append(f"{words[0]}{words[1]}.com")
    
    # Pattern 6: Abbreviated (first 3 chars of each word)
    if len(words) > 1:
        abbrev = ''.join(w[:3] for w in words if len(w) >= 3)
        if len(abbrev) >= 4:
            candidates.append(f"{abbrev}.com")
    
    # Dedupe while preserving order
    seen = set()
    unique = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    
    return unique

async def check_domain(session: aiohttp.ClientSession, domain: str, timeout: float = 5.0) -> dict:
    """Check if domain exists via HEAD request"""
    for protocol in ['https://', 'http://']:
        url = f"{protocol}{domain}"
        try:
            async with session.head(url, timeout=aiohttp.ClientTimeout(total=timeout), 
                                    allow_redirects=True, ssl=False) as resp:
                # Any response (even 403/404) means domain exists
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
    """Try to resolve company domain from name"""
    candidates = generate_domain_candidates(company_name)
    
    for candidate in candidates:
        result = await check_domain(session, candidate)
        if result['valid']:
            return {
                'found': True,
                'domain': result['domain'],
                'url': result['url'],
                'candidate_tried': candidate,
                'candidates_count': len(candidates)
            }
    
    return {
        'found': False,
        'domain': None,
        'url': None,
        'candidates_tried': candidates,
        'candidates_count': len(candidates)
    }

async def process_batch(rows: list, batch_size: int = 50) -> list:
    """Process rows in batches"""
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
                result['company_name'] = row['company_name']
                result['ein'] = row['ein']
                results.append(result)
            
            print(f"  Processed {min(i+batch_size, len(rows))}/{len(rows)}", end='\r')
    
    return results

def main():
    # Load original data
    with open('scripts/dol_url_discovery_sample.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Load Clay results for comparison
    clay_results = {}
    with open('scripts/clay_results.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            clay_results[r['ein']] = r.get('Domain', '')
    
    print("Domain Construction URL Discovery")
    print("=" * 70)
    print(f"Testing {len(rows)} companies...")
    print()
    
    start = time.time()
    results = asyncio.run(process_batch(rows, batch_size=50))
    elapsed = time.time() - start
    
    print()
    print(f"Completed in {elapsed:.1f}s ({len(rows)/elapsed:.1f} companies/sec)")
    print()
    
    # Analyze results
    found = [r for r in results if r.get('found')]
    not_found = [r for r in results if not r.get('found')]
    
    print("=" * 70)
    print("RESULTS:")
    print(f"  Found: {len(found)} ({len(found)/len(rows)*100:.1f}%)")
    print(f"  Not Found: {len(not_found)} ({len(not_found)/len(rows)*100:.1f}%)")
    print()
    
    # Compare with Clay
    matches = 0
    mismatches = []
    for r in found:
        clay_domain = clay_results.get(r['ein'], '').lower()
        our_domain = (r.get('domain') or '').lower()
        
        # Normalize for comparison (strip www.)
        clay_norm = clay_domain.replace('www.', '')
        our_norm = our_domain.replace('www.', '')
        
        if clay_norm == our_norm:
            matches += 1
        else:
            if len(mismatches) < 20:
                mismatches.append({
                    'name': r['company_name'],
                    'ours': our_domain,
                    'clay': clay_domain
                })
    
    print("COMPARISON WITH CLAY:")
    print(f"  Our found that match Clay: {matches} ({matches/len(found)*100:.1f}%)")
    print(f"  Our found that differ from Clay: {len(found) - matches}")
    print()
    
    print("Sample differences (ours vs Clay):")
    print("-" * 70)
    for m in mismatches[:15]:
        print(f"  {m['name'][:35]:<35}")
        print(f"    Ours: {m['ours']}")
        print(f"    Clay: {m['clay']}")
        print()
    
    # Save results
    with open('scripts/domain_construction_results.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ein', 'company_name', 'found', 'our_domain', 'clay_domain', 'match'])
        for r in results:
            clay_domain = clay_results.get(r['ein'], '')
            our_domain = r.get('domain', '')
            match = clay_domain.lower().replace('www.', '') == (our_domain or '').lower().replace('www.', '')
            writer.writerow([r['ein'], r['company_name'], r.get('found'), our_domain, clay_domain, match])
    
    print("Results saved to scripts/domain_construction_results.csv")

if __name__ == "__main__":
    main()
