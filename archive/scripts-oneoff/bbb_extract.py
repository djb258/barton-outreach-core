#!/usr/bin/env python3
"""
Extract BBB search results with website URLs - FREE approach
"""
import httpx
import re
import json
from urllib.parse import quote

def get_bbb_websites(company: str, city: str, state: str):
    """Search BBB and extract website URLs"""
    url = f'https://www.bbb.org/search?find_country=USA&find_loc={city}%2C%20{state}&find_text={quote(company)}&find_type=Category&page=1'
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    r = httpx.get(url, headers=headers, timeout=15, follow_redirects=True)
    
    # Extract Next.js data
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', r.text)
    if match:
        data = json.loads(match.group(1))
        results = data.get('props', {}).get('pageProps', {}).get('searchResults', {}).get('results', [])
        return results
    return []


if __name__ == '__main__':
    company = 'Minutemen'
    city = 'Cleveland'
    state = 'OH'
    
    print(f"Searching BBB.org for: {company} in {city}, {state}")
    print("=" * 60)
    
    results = get_bbb_websites(company, city, state)
    
    print(f"Found {len(results)} BBB business results:")
    print()
    
    for biz in results[:10]:
        name = biz.get('businessName', 'N/A')
        website = biz.get('websiteUrl', '')
        phone = biz.get('phone', 'N/A')
        bbb_city = biz.get('city', 'N/A')
        
        print(f"Name: {name}")
        print(f"  Website: {website if website else 'N/A'}")
        print(f"  Phone: {phone}")
        print(f"  City: {bbb_city}")
        print()
