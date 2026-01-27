#!/usr/bin/env python3
"""
Test BBB.org and Yelp for FREE company URL discovery
"""
import httpx
from urllib.parse import quote
import re

def test_bbb_search(company: str, city: str, state: str):
    """BBB.org - FREE public business directory"""
    print("=" * 60)
    print("BBB.org SEARCH (FREE - no API key)")
    print("=" * 60)
    
    search_query = quote(company)
    url = f'https://www.bbb.org/search?find_country=USA&find_loc={city}%2C%20{state}&find_text={search_query}&find_type=Category&page=1'
    
    print(f'Company: {company}')
    print(f'Location: {city}, {state}')
    print(f'URL: {url}')
    print()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        r = httpx.get(url, headers=headers, timeout=15, follow_redirects=True)
        print(f'Status: {r.status_code}')
        print(f'Content length: {len(r.text)} bytes')
        
        # Check for business results
        if company.lower() in r.text.lower():
            print(f'✓ Found "{company}" in results!')
        else:
            print(f'✗ "{company}" not found in results')
            
        # Check for website references
        if 'website' in r.text.lower():
            print('✓ Website field present in response')
            
        # BBB is JS-rendered, need to check if we get actual data or shell
        if '__NEXT_DATA__' in r.text:
            print('Note: BBB uses Next.js - data may be in JSON blob')
            # Try to extract JSON data
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', r.text)
            if match:
                import json
                data = json.loads(match.group(1))
                props = data.get('props', {}).get('pageProps', {})
                results = props.get('searchResults', {}).get('results', [])
                print(f'Found {len(results)} business results in JSON')
                for biz in results[:3]:
                    print(f"  - {biz.get('businessName')}")
                    print(f"    Website: {biz.get('websiteUrl', 'N/A')}")
                    print(f"    Phone: {biz.get('phone', 'N/A')}")
                    print()
                    
    except Exception as e:
        print(f'Error: {e}')


def test_yelp_website():
    """Show Yelp API capabilities"""
    print()
    print("=" * 60)
    print("YELP FUSION API (FREE - 5,000/day - needs key)")
    print("=" * 60)
    print("""
    GET https://api.yelp.com/v3/businesses/search
    
    Parameters:
    - term: company name
    - location: "city, state"
    - limit: 5
    
    Returns:
    - name, phone, website (on detail call)
    - address, coordinates
    - categories
    
    To get website, need separate call:
    GET https://api.yelp.com/v3/businesses/{id}
    
    COST: FREE (5,000 calls/day)
    """)


if __name__ == '__main__':
    # Test with Minutemen example
    test_bbb_search("Minutemen", "Cleveland", "OH")
    test_yelp_website()
