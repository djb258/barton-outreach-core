"""
Direct Scraper - Tier 0 Enrichment Agent
Cost: $0.00 (completely FREE - just HTTP requests)

Scrapes company websites directly to extract:
- Email addresses
- LinkedIn company URLs
- Phone numbers
- Physical addresses

Strategy:
1. If website exists in company_record, scrape it directly
2. If website missing, try to guess: company_name.com
3. Check common paths: /contact, /about, /contact-us

Usage:
    from agents.tier0.direct_scraper import enrich_with_direct_scrape

    result = enrich_with_direct_scrape(company_record, "missing_email")
    if result:
        print(f"Found: {result}")

Barton Doctrine ID: 04.04.02.04.enrichment.agents.tier0.direct_scraper
"""

import re
import time
from typing import Dict, Optional, List
from urllib.parse import urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    print("[WARNING] direct_scraper requires: pip install requests beautifulsoup4")


# Configuration
REQUEST_TIMEOUT = 10  # seconds
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Common contact page paths to check
CONTACT_PATHS = [
    "/contact",
    "/contact-us",
    "/contactus",
    "/about",
    "/about-us",
    "/aboutus",
    "/company",
    "/team",
    "/leadership",
]

# Email patterns to exclude (not real contact emails)
EXCLUDED_EMAIL_PATTERNS = [
    r".*@example\.com",
    r".*@test\.com",
    r".*@localhost",
    r"noreply@.*",
    r"no-reply@.*",
    r"donotreply@.*",
    r"unsubscribe@.*",
    r"mailer-daemon@.*",
    r"postmaster@.*",
    r"webmaster@.*",
    r".*@sentry\.io",
    r".*@google\.com",
    r".*@facebook\.com",
    r".*@twitter\.com",
]

# Priority email prefixes (most likely to be contact emails)
PRIORITY_EMAIL_PREFIXES = [
    "contact",
    "info",
    "hello",
    "support",
    "sales",
    "hr",
    "careers",
    "jobs",
    "recruiting",
    "admin",
    "office",
]


def enrich_with_direct_scrape(company_record: Dict, failure_reason: str) -> Optional[Dict]:
    """
    Direct HTTP scraping with BeautifulSoup.
    Completely FREE.

    Args:
        company_record: Dict with company data (company_name, website, etc.)
        failure_reason: Why validation failed (e.g., "missing_email")

    Returns:
        Dict with enriched data or None if nothing found
        Example: {"email": "contact@company.com", "linkedin_url": "https://linkedin.com/company/xyz"}
    """
    if not DEPENDENCIES_AVAILABLE:
        return None

    company_name = company_record.get("company_name", "")
    website = company_record.get("website", "")

    print(f"  [DirectScrape] Attempting free scrape for: {company_name}")

    # Strategy 1: If we have a website, scrape it
    if website:
        result = _scrape_website(website, failure_reason)
        if result:
            print(f"  [DirectScrape SUCCESS] Found data from existing website")
            return result

    # Strategy 2: Try to guess the website
    guessed_websites = _guess_website_from_name(company_name)
    for guessed_url in guessed_websites:
        print(f"  [DirectScrape] Trying guessed URL: {guessed_url}")
        result = _scrape_website(guessed_url, failure_reason)
        if result:
            # Also return the discovered website
            result["website"] = guessed_url
            print(f"  [DirectScrape SUCCESS] Found data from guessed website: {guessed_url}")
            return result

    print(f"  [DirectScrape] No data found")
    return None


def _scrape_website(base_url: str, failure_reason: str) -> Optional[Dict]:
    """
    Scrape a website and its contact pages for data.

    Args:
        base_url: Website URL to scrape
        failure_reason: What we're looking for

    Returns:
        Dict with found data or None
    """
    # Normalize URL
    if not base_url.startswith("http"):
        base_url = f"https://{base_url}"

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    results = {}

    # Pages to scrape (homepage + contact pages)
    pages_to_check = [base_url] + [urljoin(base_url, path) for path in CONTACT_PATHS]

    for page_url in pages_to_check:
        try:
            response = requests.get(
                page_url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True
            )

            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract data based on what we need
            if "email" in failure_reason.lower() or "missing_email" in failure_reason.lower():
                email = _extract_email_from_soup(soup, base_url)
                if email and "email" not in results:
                    results["email"] = email

            if "linkedin" in failure_reason.lower() or "missing_linkedin" in failure_reason.lower():
                linkedin = _extract_linkedin_from_soup(soup)
                if linkedin and "linkedin_url" not in results:
                    results["linkedin_url"] = linkedin

            # Always try to find LinkedIn if we're scraping anyway
            if "linkedin_url" not in results:
                linkedin = _extract_linkedin_from_soup(soup)
                if linkedin:
                    results["linkedin_url"] = linkedin

            # If we found what we need, return early
            if results:
                return results

        except requests.exceptions.Timeout:
            continue
        except requests.exceptions.ConnectionError:
            continue
        except Exception as e:
            continue

        # Small delay between pages to be polite
        time.sleep(0.2)

    return results if results else None


def _guess_website_from_name(company_name: str) -> List[str]:
    """
    Guess possible website URLs from company name.

    Args:
        company_name: Company name to convert to domain

    Returns:
        List of possible URLs to try
    """
    if not company_name:
        return []

    # Clean company name
    clean_name = company_name.lower()

    # Remove common suffixes
    suffixes_to_remove = [
        " inc", " inc.", " incorporated",
        " llc", " l.l.c.", " l.l.c",
        " ltd", " ltd.", " limited",
        " corp", " corp.", " corporation",
        " co", " co.", " company",
        " pllc", " p.l.l.c.",
        " lp", " l.p.",
        " llp", " l.l.p.",
        " pc", " p.c.",
        " pa", " p.a.",
        " of west virginia", " of wv",
        " west virginia", " wv",
    ]

    for suffix in suffixes_to_remove:
        if clean_name.endswith(suffix):
            clean_name = clean_name[:-len(suffix)]

    # Remove special characters and spaces
    clean_name = re.sub(r"[^a-z0-9]", "", clean_name)

    if not clean_name:
        return []

    # Generate possible URLs
    urls = [
        f"https://{clean_name}.com",
        f"https://www.{clean_name}.com",
        f"https://{clean_name}.org",
        f"https://{clean_name}.net",
    ]

    return urls


def _extract_email_from_soup(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    """
    Extract email addresses from page content.

    Args:
        soup: BeautifulSoup parsed page
        base_url: Base URL for context

    Returns:
        Best email found or None
    """
    # Get all text content
    text = soup.get_text(separator=" ")

    # Also check mailto: links
    mailto_links = soup.find_all("a", href=re.compile(r"^mailto:", re.I))
    for link in mailto_links:
        href = link.get("href", "")
        email_match = re.search(r"mailto:([^\?&]+)", href, re.I)
        if email_match:
            email = email_match.group(1).strip()
            if _is_valid_email(email):
                return email

    # Regex for email addresses
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    emails = re.findall(email_pattern, text)

    # Filter and prioritize
    valid_emails = [e for e in emails if _is_valid_email(e)]

    if not valid_emails:
        return None

    # Prioritize by prefix
    for prefix in PRIORITY_EMAIL_PREFIXES:
        for email in valid_emails:
            if email.lower().startswith(prefix):
                return email

    # Return first valid email
    return valid_emails[0]


def _is_valid_email(email: str) -> bool:
    """Check if email is valid and not excluded."""
    email_lower = email.lower()

    # Check against exclusion patterns
    for pattern in EXCLUDED_EMAIL_PATTERNS:
        if re.match(pattern, email_lower):
            return False

    # Basic format check
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        return False

    return True


def _extract_linkedin_from_soup(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract LinkedIn company URL from page.

    Args:
        soup: BeautifulSoup parsed page

    Returns:
        LinkedIn company URL or None
    """
    # Find all links
    links = soup.find_all("a", href=True)

    for link in links:
        href = link.get("href", "")

        # Look for LinkedIn company pages
        linkedin_match = re.search(
            r"https?://(?:www\.)?linkedin\.com/company/([a-zA-Z0-9_-]+)",
            href,
            re.I
        )
        if linkedin_match:
            # Normalize URL
            company_slug = linkedin_match.group(1)
            return f"https://www.linkedin.com/company/{company_slug}"

    # Also check for LinkedIn in text (might be plain text URL)
    text = soup.get_text()
    linkedin_text_match = re.search(
        r"linkedin\.com/company/([a-zA-Z0-9_-]+)",
        text,
        re.I
    )
    if linkedin_text_match:
        company_slug = linkedin_text_match.group(1)
        return f"https://www.linkedin.com/company/{company_slug}"

    return None


# ============================================================================
# CLI Testing
# ============================================================================

if __name__ == "__main__":
    print("Testing Direct Scraper (Tier 0)...")
    print("=" * 60)

    # Test 1: Company with known website
    test_company_1 = {
        "company_name": "Mountaineer Casino",
        "website": "https://www.cnty.com/mountaineer/",
        "state": "West Virginia"
    }

    print(f"\nTest 1: {test_company_1['company_name']}")
    print(f"Website: {test_company_1['website']}")
    result = enrich_with_direct_scrape(test_company_1, "missing_email")
    print(f"Result: {result}")

    # Test 2: Company without website (guess)
    test_company_2 = {
        "company_name": "First Choice Services",
        "state": "West Virginia"
    }

    print(f"\nTest 2: {test_company_2['company_name']}")
    print("Website: (none - will guess)")
    result = enrich_with_direct_scrape(test_company_2, "missing_website")
    print(f"Result: {result}")

    # Test 3: Guess URL generation
    print("\nTest 3: URL guessing")
    test_names = [
        "First Choice WV PLLC",
        "Mountaineer Casino Resort",
        "West Virginia Department of Highways"
    ]
    for name in test_names:
        urls = _guess_website_from_name(name)
        print(f"  {name} -> {urls[:2]}")

    print("\n" + "=" * 60)
    print("Direct Scraper test complete")
