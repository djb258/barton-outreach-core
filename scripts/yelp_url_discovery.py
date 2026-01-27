#!/usr/bin/env python3
"""
Yelp Fusion API - FREE URL Discovery
5,000 calls/day = plenty for enrichment

Get API key: https://www.yelp.com/developers/v3/manage_app
"""
import httpx
import os
from typing import Optional

def search_yelp(company: str, city: str, state: str, api_key: str) -> list:
    """Search Yelp for a business"""
    url = 'https://api.yelp.com/v3/businesses/search'
    headers = {'Authorization': f'Bearer {api_key}'}
    params = {
        'term': company,
        'location': f'{city}, {state}',
        'limit': 5
    }
    
    r = httpx.get(url, headers=headers, params=params, timeout=10)
    if r.status_code == 200:
        return r.json().get('businesses', [])
    return []


def get_business_details(business_id: str, api_key: str) -> dict:
    """Get business details including website"""
    url = f'https://api.yelp.com/v3/businesses/{business_id}'
    headers = {'Authorization': f'Bearer {api_key}'}
    
    r = httpx.get(url, headers=headers, timeout=10)
    if r.status_code == 200:
        return r.json()
    return {}


def demo_without_key():
    """Show what Yelp API returns"""
    print("=" * 60)
    print("YELP FUSION API - FREE URL DISCOVERY")
    print("=" * 60)
    print("""
    SETUP:
    1. Go to: https://www.yelp.com/developers/v3/manage_app
    2. Create a free app
    3. Get API key
    4. Add to Doppler: YELP_API_KEY
    
    LIMITS:
    - 5,000 API calls/day (FREE)
    - 137,000 DOL records / 5,000 = 28 days to process all
    
    WORKFLOW:
    1. Search by company name + city + state
    2. Get top match business ID
    3. Fetch business details (includes website)
    4. Match website to company_master or create new
    
    SAMPLE RESPONSE (business/search):
    {
        "id": "minutemen-staffing-cleveland",
        "name": "Minutemen Staffing",
        "phone": "+12165551234",
        "url": "https://www.yelp.com/biz/minutemen-staffing-cleveland",
        "location": {
            "city": "Cleveland",
            "state": "OH",
            "address1": "123 Main St"
        }
    }
    
    SAMPLE RESPONSE (business/{id}):
    {
        "id": "minutemen-staffing-cleveland",
        "name": "Minutemen Staffing",
        "url": "https://www.yelp.com/biz/...",
        "website": "https://www.minutemenstaffing.com"  <-- THIS!
    }
    """)


if __name__ == '__main__':
    api_key = os.environ.get('YELP_API_KEY', '')
    
    if not api_key:
        demo_without_key()
        print("\nTo test with real data, set YELP_API_KEY environment variable")
    else:
        # Test with Minutemen
        company = 'Minutemen'
        city = 'Cleveland' 
        state = 'OH'
        
        print(f"Searching Yelp for: {company} in {city}, {state}")
        print("=" * 60)
        
        results = search_yelp(company, city, state, api_key)
        print(f"Found {len(results)} results")
        
        for biz in results:
            print(f"\nName: {biz.get('name')}")
            print(f"  ID: {biz.get('id')}")
            print(f"  Phone: {biz.get('phone')}")
            print(f"  Yelp URL: {biz.get('url')}")
            
            # Get details for website
            details = get_business_details(biz.get('id'), api_key)
            if details:
                website = details.get('url', 'N/A')
                print(f"  Website: {website}")
