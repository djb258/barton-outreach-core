"""
Google Custom Search Engine Agent - Tier 0 Enrichment
Cost: 100 queries/day FREE, then $5/1000 = $0.005 per query

Uses Google Custom Search API to find company websites.
40X cheaper than SerpAPI ($0.005 vs $0.20)!

Setup Required:
1. Get API key: https://developers.google.com/custom-search/v1/overview
2. Create Custom Search Engine: https://programmablesearchengine.google.com/
3. Get CX (Search Engine ID)
4. Add to .env:
   GOOGLE_CSE_API_KEY=your_key
   GOOGLE_CSE_CX=your_cx_id

Usage:
    from agents.tier0.google_cse_agent import enrich_with_google_cse

    result = enrich_with_google_cse(company_record, "missing_website")
    if result:
        print(f"Found website: {result['website']}")

Barton Doctrine ID: 04.04.02.04.enrichment.agents.tier0.google_cse
"""

import os
import re
from typing import Dict, Optional, List
from urllib.parse import urlparse

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("[WARNING] google_cse_agent requires: pip install requests")


# Configuration
GOOGLE_CSE_ENDPOINT = "https://www.googleapis.com/customsearch/v1"
REQUEST_TIMEOUT = 15  # seconds

# Domains to exclude from results (directories, not company websites)
EXCLUDED_DOMAINS = [
    "linkedin.com",
    "facebook.com",
    "twitter.com",
    "instagram.com",
    "youtube.com",
    "yelp.com",
    "yellowpages.com",
    "bbb.org",
    "manta.com",
    "dnb.com",
    "zoominfo.com",
    "crunchbase.com",
    "glassdoor.com",
    "indeed.com",
    "wikipedia.org",
    "bloomberg.com",
    "google.com",
    "mapquest.com",
    "apple.com",
    "wv.gov",
    "state.wv.us",
    "findlaw.com",
    "justia.com",
    "superpages.com",
    "whitepages.com",
    "angieslist.com",
    "thumbtack.com",
    "houzz.com",
    "homeadvisor.com",
]


def enrich_with_google_cse(company_record: Dict, failure_reason: str) -> Optional[Dict]:
    """
    Use Google Custom Search API to find company website.

    Args:
        company_record: Dict with company data (company_name, state, city, etc.)
        failure_reason: Why validation failed (e.g., "missing_website")

    Returns:
        Dict with enriched data or None if nothing found
        Example: {"website": "https://company.com"}
    """
    if not REQUESTS_AVAILABLE:
        return None

    # Get API credentials
    api_key = os.getenv("GOOGLE_CSE_API_KEY")
    cx = os.getenv("GOOGLE_CSE_CX")

    if not api_key or api_key == "your_google_cse_api_key_here":
        print("  [GoogleCSE] API key not configured")
        return None

    if not cx or cx == "your_custom_search_engine_id_here":
        print("  [GoogleCSE] Search engine ID (CX) not configured")
        return None

    company_name = company_record.get("company_name", "")
    state = company_record.get("state", "")
    city = company_record.get("city", "")

    if not company_name:
        print("  [GoogleCSE] No company name provided")
        return None

    print(f"  [GoogleCSE] Searching for: {company_name}")

    # Build search query
    query = _build_search_query(company_name, city, state, failure_reason)

    try:
        response = requests.get(
            GOOGLE_CSE_ENDPOINT,
            params={
                "key": api_key,
                "cx": cx,
                "q": query,
                "num": 5,  # Get top 5 results
            },
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])

            if not items:
                print("  [GoogleCSE] No results found")
                return None

            # Find best matching result
            website = _find_best_website(items, company_name)

            if website:
                print(f"  [GoogleCSE SUCCESS] Found: {website}")
                return {"website": website}
            else:
                print("  [GoogleCSE] No valid company website in results")
                return None

        elif response.status_code == 403:
            error_data = response.json()
            error_reason = error_data.get("error", {}).get("errors", [{}])[0].get("reason", "")

            if error_reason == "dailyLimitExceeded":
                print("  [GoogleCSE] Daily quota exceeded (100 free queries)")
            elif error_reason == "rateLimitExceeded":
                print("  [GoogleCSE] Rate limit exceeded")
            else:
                print(f"  [GoogleCSE] Access denied: {error_reason}")
            return None

        elif response.status_code == 400:
            print(f"  [GoogleCSE] Bad request - check API key and CX")
            return None

        else:
            print(f"  [GoogleCSE] API error: {response.status_code}")
            return None

    except requests.exceptions.Timeout:
        print("  [GoogleCSE] Request timeout")
        return None
    except requests.exceptions.ConnectionError:
        print("  [GoogleCSE] Connection error")
        return None
    except Exception as e:
        print(f"  [GoogleCSE] Error: {str(e)}")
        return None


def _build_search_query(company_name: str, city: str, state: str, failure_reason: str) -> str:
    """
    Build optimized search query for finding company website.

    Args:
        company_name: Company name
        city: City (optional)
        state: State (optional)
        failure_reason: What we're looking for

    Returns:
        Search query string
    """
    # Base query
    query = company_name

    # Add location for disambiguation
    if city and state:
        query += f" {city} {state}"
    elif state:
        query += f" {state}"

    # Add search modifiers based on what we need
    if "website" in failure_reason.lower():
        query += " official website"
    elif "linkedin" in failure_reason.lower():
        query += " site:linkedin.com/company"

    return query


def _find_best_website(items: List[Dict], company_name: str) -> Optional[str]:
    """
    Find the best matching company website from search results.

    Args:
        items: List of Google CSE result items
        company_name: Company name for matching

    Returns:
        Best website URL or None
    """
    # Clean company name for matching
    clean_name = company_name.lower()
    clean_name = re.sub(r"[^a-z0-9]", "", clean_name)

    for item in items:
        url = item.get("link", "")

        if not url:
            continue

        # Parse URL
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]

        # Check if domain is excluded
        is_excluded = False
        for excluded in EXCLUDED_DOMAINS:
            if excluded in domain:
                is_excluded = True
                break

        if is_excluded:
            continue

        # Valid URL found
        return url

    return None


def check_quota_status() -> Dict:
    """
    Check Google CSE quota status.

    Returns:
        Dict with quota information
    """
    api_key = os.getenv("GOOGLE_CSE_API_KEY")
    cx = os.getenv("GOOGLE_CSE_CX")

    status = {
        "configured": False,
        "api_key_set": bool(api_key and api_key != "your_google_cse_api_key_here"),
        "cx_set": bool(cx and cx != "your_custom_search_engine_id_here"),
        "free_tier": "100 queries/day",
        "paid_tier": "$5/1000 queries ($0.005 each)",
    }

    status["configured"] = status["api_key_set"] and status["cx_set"]

    return status


# ============================================================================
# CLI Testing
# ============================================================================

if __name__ == "__main__":
    print("Testing Google CSE Agent (Tier 0)...")
    print("=" * 60)

    # Check configuration
    status = check_quota_status()
    print("\nConfiguration Status:")
    print(f"  API Key Set: {status['api_key_set']}")
    print(f"  CX Set: {status['cx_set']}")
    print(f"  Configured: {status['configured']}")
    print(f"  Free Tier: {status['free_tier']}")
    print(f"  Paid Tier: {status['paid_tier']}")

    if not status["configured"]:
        print("\n[ERROR] Google CSE not configured!")
        print("Add to .env:")
        print("  GOOGLE_CSE_API_KEY=your_api_key")
        print("  GOOGLE_CSE_CX=your_search_engine_id")
        print("\nGet credentials at:")
        print("  https://developers.google.com/custom-search/v1/overview")
        print("  https://programmablesearchengine.google.com/")
    else:
        # Test with a company
        test_company = {
            "company_name": "First Choice Services",
            "state": "West Virginia",
            "city": "Parkersburg"
        }

        print(f"\nTest Search: {test_company['company_name']}")
        result = enrich_with_google_cse(test_company, "missing_website")
        print(f"Result: {result}")

    print("\n" + "=" * 60)
    print("Google CSE test complete")
