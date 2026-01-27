#!/usr/bin/env python3
"""
Debug BBB.org JSON structure
"""
import httpx
import re
import json
from urllib.parse import quote

company = 'Minutemen'
city = 'Cleveland'
state = 'OH'

url = f'https://www.bbb.org/search?find_country=USA&find_loc={city}%2C%20{state}&find_text={quote(company)}&find_type=Category&page=1'

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
r = httpx.get(url, headers=headers, timeout=15, follow_redirects=True)

print(f"Status: {r.status_code}")
print(f"URL: {url}")

# Check if Minutemen is in the text
if 'Minutemen' in r.text:
    print("✓ 'Minutemen' found in response")
    
# Extract Next.js data
match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', r.text)
if match:
    data = json.loads(match.group(1))
    print("\nJSON Structure (pageProps keys):")
    page_props = data.get('props', {}).get('pageProps', {})
    for key in page_props.keys():
        print(f"  - {key}")
        
    # Check searchResults structure
    search_results = page_props.get('searchResults', {})
    print(f"\nsearchResults keys: {list(search_results.keys())}")
    
    # Print full structure
    print("\nFull searchResults:")
    print(json.dumps(search_results, indent=2)[:2000])
else:
    print("No __NEXT_DATA__ found")
    
    # Try to find any JSON in the page
    print("\nLooking for other JSON structures...")
    json_matches = re.findall(r'\{[^{}]+websiteUrl[^{}]+\}', r.text)
    print(f"Found {len(json_matches)} potential matches with websiteUrl")
