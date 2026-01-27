#!/usr/bin/env python3
"""
Test FREE APIs for company URL discovery
Tier 0 - Zero cost options
"""
import httpx
import urllib.parse

def test_opencorporates(company: str, state: str):
    """OpenCorporates - FREE API (no key needed for basic search)"""
    print("=" * 60)
    print("OPENCORPORATES (FREE - no API key)")
    print("=" * 60)
    
    url = f'https://api.opencorporates.com/v0.4/companies/search'
    params = {
        'q': company,
        'jurisdiction_code': f'us_{state.lower()}'
    }
    
    try:
        r = httpx.get(url, params=params, timeout=10)
        print(f'Status: {r.status_code}')
        
        if r.status_code == 200:
            data = r.json()
            companies = data.get('results', {}).get('companies', [])
            print(f'Found: {len(companies)} results')
            for c in companies[:3]:
                co = c.get('company', {})
                print(f"  - {co.get('name')}")
                print(f"    Jurisdiction: {co.get('jurisdiction_code')}")
                print(f"    Status: {co.get('current_status')}")
                print(f"    Address: {co.get('registered_address_in_full')}")
                # Check if website is available
                print(f"    Company URL: {co.get('opencorporates_url')}")
                print()
        else:
            print(f"Response: {r.text[:500]}")
    except Exception as e:
        print(f'Error: {e}')


def test_yelp_business_search(company: str, city: str, state: str):
    """Yelp Fusion API - FREE 5,000 calls/day (needs API key)"""
    import os
    
    print("=" * 60)
    print("YELP FUSION API (FREE - 5,000/day - needs key)")
    print("=" * 60)
    
    api_key = os.environ.get('YELP_API_KEY', '')
    if not api_key:
        print("YELP_API_KEY not configured")
        print("Get one at: https://www.yelp.com/developers/v3/manage_app")
        return
    
    url = 'https://api.yelp.com/v3/businesses/search'
    headers = {'Authorization': f'Bearer {api_key}'}
    params = {
        'term': company,
        'location': f'{city}, {state}',
        'limit': 5
    }
    
    try:
        r = httpx.get(url, headers=headers, params=params, timeout=10)
        print(f'Status: {r.status_code}')
        
        if r.status_code == 200:
            data = r.json()
            businesses = data.get('businesses', [])
            print(f'Found: {len(businesses)} results')
            for b in businesses[:3]:
                print(f"  - {b.get('name')}")
                print(f"    Phone: {b.get('phone')}")
                print(f"    URL: {b.get('url')}")  # Yelp page
                # Note: website is in business details endpoint
                print()
    except Exception as e:
        print(f'Error: {e}')


def test_google_custom_search():
    """Google Custom Search - FREE 100/day"""
    print("=" * 60)
    print("GOOGLE CUSTOM SEARCH (FREE - 100/day)")
    print("=" * 60)
    print("Requires: GOOGLE_API_KEY + Custom Search Engine ID")
    print("Too limited for bulk (100/day)")
    print()


def test_duckduckgo_instant(company: str, city: str, state: str):
    """DuckDuckGo Instant Answer API - FREE (no key)"""
    print("=" * 60)
    print("DUCKDUCKGO INSTANT (FREE - no key)")
    print("=" * 60)
    
    query = f'{company} {city} {state}'
    url = 'https://api.duckduckgo.com/'
    params = {
        'q': query,
        'format': 'json',
        'no_html': 1,
        'skip_disambig': 1
    }
    
    try:
        r = httpx.get(url, params=params, timeout=10)
        print(f'Status: {r.status_code}')
        
        if r.status_code == 200:
            data = r.json()
            print(f"Abstract: {data.get('Abstract', 'None')[:200]}")
            print(f"AbstractURL: {data.get('AbstractURL', 'None')}")
            print(f"Related topics: {len(data.get('RelatedTopics', []))}")
            
            # Check for official website
            if data.get('Infobox'):
                print(f"Infobox: {data.get('Infobox')}")
    except Exception as e:
        print(f'Error: {e}')


if __name__ == '__main__':
    # Test with Minutemen example
    company = "Minutemen"
    city = "Cleveland"
    state = "OH"
    
    print(f"\nTesting FREE APIs for: {company}, {city}, {state}\n")
    
    test_opencorporates(company, state)
    print()
    
    test_duckduckgo_instant(company, city, state)
    print()
    
    test_yelp_business_search(company, city, state)
    print()
    
    # Summary
    print("=" * 60)
    print("FREE API OPTIONS SUMMARY")
    print("=" * 60)
    print("""
    1. YELP FUSION API
       - FREE: 5,000 calls/day
       - Returns: name, phone, website, address
       - Needs API key (free to get)
       - BEST FOR: B2C businesses with storefronts
    
    2. OPENCORPORATES
       - FREE: Basic search (rate limited)
       - Returns: company name, status, address
       - NO website field
       - BEST FOR: Confirming entity existence
    
    3. DUCKDUCKGO INSTANT
       - FREE: Unlimited (unofficial)
       - Returns: Abstract, sometimes URL
       - Limited business data
       - BEST FOR: Quick entity check
    
    4. BBB.org SCRAPE (not tested)
       - FREE: Public pages
       - Returns: website, phone, reviews
       - Needs httpx + selectolax
       - BEST FOR: Accredited businesses
    """)
