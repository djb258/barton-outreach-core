#!/usr/bin/env python3
"""
DOL URL Discovery - Tier 0 FREE approach.

Uses free web search to find company URLs from DOL name + location.
Runs per state for parallelization.

SNAP_ON_TOOLBOX compliant:
- Tier 0: Free web search + httpx validation
- No paid APIs
- Throttled to respect rate limits
"""

import os
import re
import time
import asyncio
import argparse
from urllib.parse import urlparse, quote_plus
import psycopg2
import httpx

# Rate limiting
SEARCH_DELAY = 2.0  # seconds between searches (be nice to search engines)
BATCH_SIZE = 50     # commit every N records
MAX_PER_RUN = 500   # limit per run to avoid timeouts

def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def get_unmatched_dol_for_state(cur, state: str, limit: int = MAX_PER_RUN):
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
        LIMIT %s
    """, (state, state, limit))
    return cur.fetchall()


async def search_duckduckgo(client: httpx.AsyncClient, query: str) -> list[str]:
    """
    Search DuckDuckGo HTML and extract URLs.
    Returns list of potential company URLs.
    """
    try:
        # DuckDuckGo HTML search
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        resp = await client.get(url, headers=headers, timeout=10.0)
        if resp.status_code != 200:
            return []
        
        html = resp.text
        
        # Extract URLs from results
        # DuckDuckGo HTML returns URLs in result links
        urls = re.findall(r'href="(https?://[^"]+)"', html)
        
        # Filter to likely company domains (not search engines, social, etc)
        skip_domains = {
            'duckduckgo.com', 'google.com', 'bing.com', 'yahoo.com',
            'facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com',
            'youtube.com', 'wikipedia.org', 'yelp.com', 'yellowpages.com',
            'bbb.org', 'glassdoor.com', 'indeed.com', 'zoominfo.com',
            'dnb.com', 'bloomberg.com', 'crunchbase.com', 'manta.com'
        }
        
        filtered = []
        for u in urls:
            try:
                parsed = urlparse(u)
                domain = parsed.netloc.lower().replace('www.', '')
                if domain and domain not in skip_domains:
                    # Get base domain (e.g., company.com)
                    base_url = f"https://{parsed.netloc}"
                    if base_url not in filtered:
                        filtered.append(base_url)
            except:
                pass
        
        return filtered[:5]  # Return top 5 candidates
        
    except Exception as e:
        return []


async def validate_url(client: httpx.AsyncClient, url: str) -> bool:
    """Check if URL is reachable."""
    try:
        resp = await client.head(url, timeout=5.0, follow_redirects=True)
        return resp.status_code < 400
    except:
        return False


def extract_domain(url: str) -> str:
    """Extract clean domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower().replace('www.', '')
    except:
        return ""


async def discover_url_for_company(
    client: httpx.AsyncClient,
    name: str,
    city: str,
    state: str
) -> tuple[str | None, float]:
    """
    Search for company URL and return (url, confidence).
    """
    # Build search query
    query = f"{name} {city} {state}"
    
    # Search
    candidates = await search_duckduckgo(client, query)
    
    if not candidates:
        return None, 0.0
    
    # Try to validate top candidates
    for url in candidates:
        if await validate_url(client, url):
            # Simple confidence based on domain matching company name
            domain = extract_domain(url)
            name_clean = re.sub(r'[^a-z0-9]', '', name.lower())
            domain_clean = re.sub(r'[^a-z0-9]', '', domain.split('.')[0])
            
            # Check if domain contains significant part of name
            if domain_clean in name_clean or name_clean[:4] in domain_clean:
                return url, 0.9  # High confidence
            else:
                return url, 0.6  # Medium confidence - first valid result
    
    return None, 0.0


async def process_state(state: str, dry_run: bool = False):
    """Process all unmatched DOL records for a state."""
    
    print(f"\n{'='*70}")
    print(f"PROCESSING STATE: {state}")
    print(f"{'='*70}")
    
    conn = get_conn()
    cur = conn.cursor()
    
    # Get unmatched records
    records = get_unmatched_dol_for_state(cur, state)
    print(f"Unmatched DOL records to process: {len(records)}")
    
    if not records:
        print("No records to process!")
        return
    
    # Results tracking
    found = 0
    not_found = 0
    results = []
    
    async with httpx.AsyncClient() as client:
        for i, (ein, name, city, st) in enumerate(records):
            # Rate limit
            if i > 0:
                await asyncio.sleep(SEARCH_DELAY)
            
            # Search for URL
            url, confidence = await discover_url_for_company(client, name, city, st)
            
            if url and confidence >= 0.6:
                found += 1
                results.append({
                    'ein': ein,
                    'name': name,
                    'city': city,
                    'state': st,
                    'url': url,
                    'confidence': confidence
                })
                status = "✓"
            else:
                not_found += 1
                status = "✗"
            
            # Progress
            if (i + 1) % 10 == 0:
                print(f"  [{i+1}/{len(records)}] Found: {found}, Not found: {not_found}")
            
            # Early sample output
            if i < 5:
                print(f"  {status} {name[:40]:<40} -> {url or 'NOT FOUND'}")
    
    # Summary
    print(f"\nRESULTS FOR {state}:")
    print(f"  Total processed: {len(records)}")
    print(f"  URLs found: {found} ({100*found/len(records):.1f}%)")
    print(f"  Not found: {not_found}")
    
    if not dry_run and results:
        print(f"\nSaving {len(results)} results...")
        # Save to a staging table or directly update
        # For now, just print sample
        print("\nSample high-confidence matches:")
        for r in sorted(results, key=lambda x: -x['confidence'])[:10]:
            print(f"  {r['name'][:35]:<35} | {r['url']:<40} | conf={r['confidence']:.2f}")
    
    cur.close()
    conn.close()
    
    return results


def main():
    parser = argparse.ArgumentParser(description='DOL URL Discovery - Tier 0 FREE')
    parser.add_argument('--state', required=True, help='State abbreviation (NC, PA, etc)')
    parser.add_argument('--dry-run', action='store_true', help='Just search, do not save')
    parser.add_argument('--limit', type=int, default=MAX_PER_RUN, help='Max records to process')
    args = parser.parse_args()
    
    print("=" * 70)
    print("DOL URL DISCOVERY - TIER 0 FREE")
    print("=" * 70)
    print(f"State: {args.state}")
    print(f"Limit: {args.limit}")
    print(f"Dry run: {args.dry_run}")
    print()
    print("Using: DuckDuckGo HTML search (FREE)")
    print("Rate limit: 1 search per 2 seconds")
    print()
    
    # Run async
    asyncio.run(process_state(args.state, args.dry_run))


if __name__ == "__main__":
    main()
