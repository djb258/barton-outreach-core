# -*- coding: utf-8 -*-
"""
Four-Tier Enrichment Waterfall - Barton Outreach Core
Attempts to enrich company data using progressively more expensive APIs

Tier 0 (FREE):       Direct Scraper, Google CSE ($0.00-$0.005)
Tier 1 (CHEAP):      ScraperAPI ($0.001), Firecrawl ($0.20), SerpAPI ($0.20)
Tier 2 (MID-COST):   Abacus.ai, Clearbit, Clay ($1.50 avg)
Tier 3 (EXPENSIVE):  Apify, RocketReach, People Data Labs ($3.00 avg)

IMPORTANT: Within Tier 1, ScraperAPI runs FIRST because it's 200x cheaper!
- ScraperAPI: $0.001/request ($49/mo for 100K)
- Firecrawl:  $0.20/request
- SerpAPI:    $0.20/request

Business Rule: Try each tier in order. Return immediately after first success.
If all 4 tiers fail, return failure.

Usage:
    from enrichment_waterfall import attempt_enrichment

    result = attempt_enrichment(company_record, "missing_website")

    if result['success']:
        print(f"Enriched with {result['tier']} for ${result['cost']}")
        print(f"Found: {result['enriched_data']}")
    else:
        print(f"All tiers failed. Errors: {result['errors']}")
"""

import os
import sys

# Fix Unicode encoding on Windows console
if sys.platform == 'win32':
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except (AttributeError, TypeError):
        # Already wrapped or running in an environment without buffer
        pass
import time
import json
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path


def safe_str(text: str, max_len: int = None) -> str:
    """
    Safely encode a string for console output on Windows.
    Replaces non-ASCII characters with '?' to prevent UnicodeEncodeError.

    Args:
        text: The string to encode
        max_len: Optional maximum length to truncate to

    Returns:
        ASCII-safe string
    """
    if text is None:
        return ""
    # Encode to ASCII, replacing non-ASCII chars with '?'
    safe = text.encode('ascii', 'replace').decode('ascii')
    if max_len and len(safe) > max_len:
        return safe[:max_len]
    return safe

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import safety mechanisms
try:
    from rate_limiter import rate_limiter, get_rate_limiter_status
    from retry_handler import retry_with_backoff, is_retryable_http_status
    SAFETY_ENABLED = True
    print("[SAFETY] Rate limiter and retry handler loaded")
except ImportError:
    SAFETY_ENABLED = False
    print("[WARNING] Safety mechanisms not available - running without throttling")

# Import Tier 0 agents (FREE/near-free)
try:
    from agents.tier0.direct_scraper import enrich_with_direct_scrape
    from agents.tier0.google_cse_agent import enrich_with_google_cse
    TIER0_ENABLED = True
    print("[TIER 0] Free enrichment agents loaded (direct_scrape, google_cse)")
except ImportError as e:
    TIER0_ENABLED = False
    print(f"[WARNING] Tier 0 agents not available: {e}")


class EnrichmentResult:
    """Result from enrichment attempt"""

    def __init__(self, success: bool, tier: Optional[str] = None,
                 enriched_data: Optional[Dict] = None, cost: float = 0.0,
                 errors: Optional[List[str]] = None, agent_name: Optional[str] = None):
        self.success = success
        self.tier = tier
        self.enriched_data = enriched_data or {}
        self.cost = cost
        self.errors = errors or []
        self.agent_name = agent_name
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "tier": self.tier,
            "enriched_data": self.enriched_data,
            "cost": self.cost,
            "errors": self.errors,
            "agent_name": self.agent_name,
            "timestamp": self.timestamp.isoformat()
        }


class EnrichmentWaterfall:
    """Three-tier enrichment waterfall"""

    # Cost estimates per tier (average)
    TIER_1_COST = 0.20
    TIER_2_COST = 1.50
    TIER_3_COST = 3.00

    def __init__(self):
        # Load API keys from environment
        self.firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
        self.serpapi_key = os.getenv("SERPAPI_API_KEY")
        self.scraperapi_key = os.getenv("SCRAPERAPI_API_KEY")
        self.zenrows_key = os.getenv("ZENROWS_API_KEY")
        self.scrapingbee_key = os.getenv("SCRAPINGBEE_API_KEY")

        self.abacus_key = os.getenv("ABACUS_API_KEY")
        self.clearbit_key = os.getenv("CLEARBIT_API_KEY")
        self.clay_key = os.getenv("CLAY_API_KEY")

        self.apify_key = os.getenv("APIFY_API_KEY")
        self.rocketreach_key = os.getenv("ROCKETREACH_API_KEY")
        self.peopledatalabs_key = os.getenv("PEOPLEDATALABS_API_KEY")

    def attempt_enrichment(self, company_record: Dict, failure_reason: str) -> EnrichmentResult:
        """
        Main entry point: Attempt enrichment across all 3 tiers

        Args:
            company_record: Dict with company data (company_name, state, city, etc.)
            failure_reason: Why validation failed (e.g., "missing_website")

        Returns:
            EnrichmentResult with success flag, enriched data, and cost
        """
        company_name = company_record.get("company_name", "Unknown")
        state = company_record.get("state", "")
        city = company_record.get("city", "")

        print(f"\n{'='*80}")
        print(f"ENRICHMENT ATTEMPT: {safe_str(company_name)}")
        print(f"Reason: {safe_str(failure_reason)}")
        print(f"Location: {safe_str(city)}, {safe_str(state)}")
        print(f"{'='*80}")

        # ═══════════════════════════════════════════════════════════════════
        # TIER 0: FREE/NEAR-FREE (Try these FIRST!)
        # ═══════════════════════════════════════════════════════════════════
        if TIER0_ENABLED:
            print("\n[TIER 0] Attempting FREE enrichment ($0.00-$0.005)...")
            result = self._tier_0_enrichment(company_record, failure_reason)
            if result.success:
                print(f"[TIER 0 SUCCESS] Enriched with {result.agent_name} for ${result.cost:.3f}")
                return result
            print(f"[TIER 0 FAILED] Free agents failed. Errors: {result.errors}")
        else:
            print("\n[TIER 0] Skipped (agents not available)")

        # ═══════════════════════════════════════════════════════════════════
        # TIER 1: PAID ($0.20 per call)
        # ═══════════════════════════════════════════════════════════════════
        print("\n[TIER 1] Attempting paid scrapers ($0.20 avg)...")
        result = self._tier_1_enrichment(company_record, failure_reason)
        if result.success:
            print(f"[TIER 1 SUCCESS] Enriched with {result.agent_name} for ${result.cost:.2f}")
            return result

        print(f"[TIER 1 FAILED] All paid scrapers failed. Errors: {result.errors}")

        # Tier 2: Mid-cost precision tools (only if Tier 1 failed)
        print("\n[TIER 2] Attempting mid-cost precision tools ($1.50 avg)...")
        result = self._tier_2_enrichment(company_record, failure_reason)
        if result.success:
            print(f"[TIER 2 SUCCESS] Enriched with {result.agent_name} for ${result.cost:.2f}")
            return result

        print(f"[TIER 2 FAILED] All mid-cost tools failed. Errors: {result.errors}")

        # Tier 3: High-cost, high-accuracy (last resort)
        print("\n[TIER 3] Attempting high-cost, high-accuracy tools ($3.00 avg)...")
        result = self._tier_3_enrichment(company_record, failure_reason)
        if result.success:
            print(f"[TIER 3 SUCCESS] Enriched with {result.agent_name} for ${result.cost:.2f}")
            return result

        print(f"[TIER 3 FAILED] All tiers exhausted. Total failures: {len(result.errors)}")

        # All tiers failed
        return EnrichmentResult(
            success=False,
            tier=None,
            enriched_data={},
            cost=0.0,
            errors=result.errors,
            agent_name=None
        )

    # ========================================================================
    # TIER 0: FREE/NEAR-FREE ENRICHMENT
    # ========================================================================

    # Cost constants for Tier 0
    TIER_0_DIRECT_SCRAPE_COST = 0.00   # Completely free
    TIER_0_GOOGLE_CSE_COST = 0.005     # $0.005 after free tier

    def _tier_0_enrichment(self, company_record: Dict, failure_reason: str) -> EnrichmentResult:
        """
        Tier 0: FREE/Near-Free enrichment
        - Direct scraping (FREE)
        - Google Custom Search ($0.005 after 100/day free)

        These run FIRST before any paid APIs.
        Target: Handle 70-90% of enrichment at near-zero cost.
        """
        errors = []

        # Agent 1: Direct Scrape (completely FREE)
        print("  [Tier0] Trying direct scrape (FREE)...")
        if SAFETY_ENABLED:
            rate_limiter.wait_if_needed("direct_scrape")

        try:
            result = enrich_with_direct_scrape(company_record, failure_reason)
            if result:
                # Validate the result has what we need
                if self._validate_tier0_result(result, failure_reason):
                    if SAFETY_ENABLED:
                        rate_limiter.record_success("direct_scrape")
                    return EnrichmentResult(
                        success=True,
                        tier="tier_0",
                        agent_name="direct_scrape",
                        enriched_data=result,
                        cost=self.TIER_0_DIRECT_SCRAPE_COST
                    )
            errors.append("direct_scrape: No valid data found")
            if SAFETY_ENABLED:
                rate_limiter.record_failure("direct_scrape")
        except Exception as e:
            errors.append(f"direct_scrape: {str(e)}")
            if SAFETY_ENABLED:
                rate_limiter.record_failure("direct_scrape")

        # Agent 2: Google Custom Search ($0.005)
        print("  [Tier0] Trying Google CSE ($0.005)...")
        if SAFETY_ENABLED:
            rate_limiter.wait_if_needed("google_cse")

        try:
            result = enrich_with_google_cse(company_record, failure_reason)
            if result:
                if self._validate_tier0_result(result, failure_reason):
                    if SAFETY_ENABLED:
                        rate_limiter.record_success("google_cse")
                    return EnrichmentResult(
                        success=True,
                        tier="tier_0",
                        agent_name="google_cse",
                        enriched_data=result,
                        cost=self.TIER_0_GOOGLE_CSE_COST
                    )
            errors.append("google_cse: No valid data found")
            if SAFETY_ENABLED:
                rate_limiter.record_failure("google_cse")
        except Exception as e:
            errors.append(f"google_cse: {str(e)}")
            if SAFETY_ENABLED:
                rate_limiter.record_failure("google_cse")

        # All Tier 0 agents failed
        return EnrichmentResult(
            success=False,
            tier="tier_0",
            cost=0.0,
            errors=errors
        )

    def _validate_tier0_result(self, result: Dict, failure_reason: str) -> bool:
        """
        Validate that Tier 0 result contains what we need.

        Args:
            result: Dict with enriched data
            failure_reason: What we're looking for

        Returns:
            True if result is valid for our needs
        """
        if not result:
            return False

        failure_lower = failure_reason.lower()

        # Check if we found what we need
        if "website" in failure_lower or "url" in failure_lower:
            website = result.get("website")
            if website and website.startswith("http"):
                return True

        if "email" in failure_lower:
            email = result.get("email")
            if email and "@" in email:
                return True

        if "linkedin" in failure_lower:
            linkedin = result.get("linkedin_url")
            if linkedin and "linkedin.com" in linkedin:
                return True

        # If failure reason is generic, accept any valid data
        if result.get("website") or result.get("email") or result.get("linkedin_url"):
            return True

        return False

    def _tier_1_enrichment(self, company_record: Dict, failure_reason: str) -> EnrichmentResult:
        """
        Tier 1: Paid scrapers (ordered by cost, cheapest first!)

        Cost Order:
        1. ScraperAPI  - $0.001/request (200x cheaper than others!)
        2. Firecrawl   - $0.20/request
        3. SerpAPI     - $0.20/request
        4. ZenRows     - $0.20/request (not implemented)
        5. ScrapingBee - $0.20/request (not implemented)
        """
        errors = []

        # ═══════════════════════════════════════════════════════════════════
        # PRIORITY 1: ScraperAPI ($0.001/request) - TRY THIS FIRST!
        # 200x cheaper than Firecrawl/SerpAPI!
        # ═══════════════════════════════════════════════════════════════════
        if self.scraperapi_key and self.scraperapi_key != "your_scraperapi_api_key_here":
            try:
                result = self._try_scraperapi(company_record)
                if result.success:
                    return result
                errors.extend(result.errors)
            except Exception as e:
                errors.append(f"ScraperAPI error: {str(e)}")

        # ═══════════════════════════════════════════════════════════════════
        # PRIORITY 2: Firecrawl ($0.20/request) - Only if ScraperAPI fails
        # ═══════════════════════════════════════════════════════════════════
        if failure_reason == "missing_website" or failure_reason == "Website URL is empty":
            if self.firecrawl_key and self.firecrawl_key != "your_firecrawl_api_key_here":
                try:
                    result = self._try_firecrawl(company_record)
                    if result.success:
                        return result
                    errors.extend(result.errors)
                except Exception as e:
                    errors.append(f"Firecrawl error: {str(e)}")

        # ═══════════════════════════════════════════════════════════════════
        # PRIORITY 3: SerpAPI ($0.20/request) - Last resort in Tier 1
        # ═══════════════════════════════════════════════════════════════════
        if self.serpapi_key and self.serpapi_key != "your_serpapi_api_key_here":
            try:
                result = self._try_serpapi(company_record)
                if result.success:
                    return result
                errors.extend(result.errors)
            except Exception as e:
                errors.append(f"SerpAPI error: {str(e)}")

        # All Tier 1 failed
        return EnrichmentResult(
            success=False,
            tier="tier_1",
            cost=0.0,
            errors=errors or ["No Tier 1 API keys configured"]
        )

    def _tier_2_enrichment(self, company_record: Dict, failure_reason: str) -> EnrichmentResult:
        """
        Tier 2: Mid-cost precision tools
        - Abacus.ai
        - Clearbit
        - Clay
        """
        errors = []

        # Try Clearbit Enrichment API
        if self.clearbit_key and self.clearbit_key != "your_clearbit_api_key_here":
            try:
                result = self._try_clearbit(company_record)
                if result.success:
                    return result
                errors.extend(result.errors)
            except Exception as e:
                errors.append(f"Clearbit error: {str(e)}")

        # Try Abacus.ai (if available)
        if self.abacus_key and self.abacus_key != "your_abacus_api_key_here":
            try:
                result = self._try_abacus(company_record)
                if result.success:
                    return result
                errors.extend(result.errors)
            except Exception as e:
                errors.append(f"Abacus error: {str(e)}")

        # All Tier 2 failed
        return EnrichmentResult(
            success=False,
            tier="tier_2",
            cost=0.0,
            errors=errors or ["No Tier 2 API keys configured"]
        )

    def _tier_3_enrichment(self, company_record: Dict, failure_reason: str) -> EnrichmentResult:
        """
        Tier 3: High-cost, high-accuracy
        - Apify
        - RocketReach
        - People Data Labs
        """
        errors = []

        # Try People Data Labs Company Enrichment
        if self.peopledatalabs_key and self.peopledatalabs_key != "your_peopledatalabs_api_key_here":
            try:
                result = self._try_peopledatalabs(company_record)
                if result.success:
                    return result
                errors.extend(result.errors)
            except Exception as e:
                errors.append(f"People Data Labs error: {str(e)}")

        # Try RocketReach
        if self.rocketreach_key and self.rocketreach_key != "your_rocketreach_api_key_here":
            try:
                result = self._try_rocketreach(company_record)
                if result.success:
                    return result
                errors.extend(result.errors)
            except Exception as e:
                errors.append(f"RocketReach error: {str(e)}")

        # Try Apify (web scraping)
        if self.apify_key and self.apify_key != "your_apify_api_key_here":
            try:
                result = self._try_apify(company_record)
                if result.success:
                    return result
                errors.extend(result.errors)
            except Exception as e:
                errors.append(f"Apify error: {str(e)}")

        # All Tier 3 failed
        return EnrichmentResult(
            success=False,
            tier="tier_3",
            cost=0.0,
            errors=errors or ["No Tier 3 API keys configured"]
        )

    # ========================================================================
    # TIER 1 IMPLEMENTATIONS
    # ========================================================================

    def _try_firecrawl(self, company_record: Dict) -> EnrichmentResult:
        """
        Try Firecrawl for website discovery via Google search.

        Firecrawl can search Google and extract the first result URL.
        API Docs: https://docs.firecrawl.dev/
        """
        print("  [Firecrawl] Searching for company website...")

        # SAFETY: Rate limit check
        if SAFETY_ENABLED:
            waited = rate_limiter.wait_if_needed("firecrawl")
            if waited > 0:
                print(f"  [Firecrawl] Rate limited, waited {waited:.1f}s")

        company_name = company_record.get("company_name", "")
        state = company_record.get("state", "")
        city = company_record.get("city", "")

        if not company_name:
            return EnrichmentResult(
                success=False,
                tier="tier_1",
                agent_name="Firecrawl",
                cost=0.0,
                errors=["Firecrawl: No company name provided"]
            )

        # Build search query
        search_query = f"{company_name}"
        if city and state:
            search_query += f" {city} {state}"
        elif state:
            search_query += f" {state}"
        search_query += " official website"

        try:
            # Firecrawl search endpoint
            response = requests.post(
                "https://api.firecrawl.dev/v1/search",
                headers={
                    "Authorization": f"Bearer {self.firecrawl_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "query": search_query,
                    "limit": 5,
                    "scrapeOptions": {
                        "formats": ["markdown"]
                    }
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("data", [])

                if results and len(results) > 0:
                    # Get the first result URL
                    first_result = results[0]
                    website = first_result.get("url", "")

                    # Verify it's a real website (not a directory listing)
                    if website and self._is_valid_company_website(website, company_name):
                        print(f"  [Firecrawl SUCCESS] Found: {website}")
                        # SAFETY: Record success
                        if SAFETY_ENABLED:
                            rate_limiter.record_success("firecrawl")
                        return EnrichmentResult(
                            success=True,
                            tier="tier_1",
                            agent_name="Firecrawl",
                            enriched_data={"website": website},
                            cost=self.TIER_1_COST
                        )

                    # Try second result if first was invalid
                    if len(results) > 1:
                        second_result = results[1]
                        website = second_result.get("url", "")
                        if website and self._is_valid_company_website(website, company_name):
                            print(f"  [Firecrawl SUCCESS] Found (2nd result): {website}")
                            # SAFETY: Record success
                            if SAFETY_ENABLED:
                                rate_limiter.record_success("firecrawl")
                            return EnrichmentResult(
                                success=True,
                                tier="tier_1",
                                agent_name="Firecrawl",
                                enriched_data={"website": website},
                                cost=self.TIER_1_COST
                            )

                # SAFETY: Record failure (no valid result)
                if SAFETY_ENABLED:
                    rate_limiter.record_failure("firecrawl")
                return EnrichmentResult(
                    success=False,
                    tier="tier_1",
                    agent_name="Firecrawl",
                    cost=0.0,
                    errors=["Firecrawl: No valid company website found in results"]
                )

            elif response.status_code == 401:
                # SAFETY: Record failure
                if SAFETY_ENABLED:
                    rate_limiter.record_failure("firecrawl")
                return EnrichmentResult(
                    success=False,
                    tier="tier_1",
                    agent_name="Firecrawl",
                    cost=0.0,
                    errors=["Firecrawl: Invalid API key"]
                )
            elif response.status_code == 429:
                # SAFETY: Rate limited - record failure to trigger circuit breaker
                if SAFETY_ENABLED:
                    rate_limiter.record_failure("firecrawl")
                return EnrichmentResult(
                    success=False,
                    tier="tier_1",
                    agent_name="Firecrawl",
                    cost=0.0,
                    errors=[f"Firecrawl: Rate limited (429) - {response.text[:100]}"]
                )
            else:
                # SAFETY: Record failure
                if SAFETY_ENABLED:
                    rate_limiter.record_failure("firecrawl")
                return EnrichmentResult(
                    success=False,
                    tier="tier_1",
                    agent_name="Firecrawl",
                    cost=0.0,
                    errors=[f"Firecrawl: API error {response.status_code} - {response.text[:200]}"]
                )

        except requests.exceptions.Timeout:
            # SAFETY: Record failure
            if SAFETY_ENABLED:
                rate_limiter.record_failure("firecrawl")
            return EnrichmentResult(
                success=False,
                tier="tier_1",
                agent_name="Firecrawl",
                cost=0.0,
                errors=["Firecrawl: Request timeout"]
            )
        except Exception as e:
            # SAFETY: Record failure
            if SAFETY_ENABLED:
                rate_limiter.record_failure("firecrawl")
            return EnrichmentResult(
                success=False,
                tier="tier_1",
                agent_name="Firecrawl",
                cost=0.0,
                errors=[f"Firecrawl: {str(e)}"]
            )

    def _is_valid_company_website(self, url: str, company_name: str) -> bool:
        """Check if URL looks like a valid company website (not a directory)"""
        # Exclude common directory/listing sites
        excluded_domains = [
            "linkedin.com", "facebook.com", "twitter.com", "instagram.com",
            "yelp.com", "yellowpages.com", "bbb.org", "manta.com",
            "dnb.com", "zoominfo.com", "crunchbase.com", "glassdoor.com",
            "indeed.com", "wikipedia.org", "bloomberg.com", "google.com",
            "mapquest.com", "apple.com/maps", "wv.gov", "state.wv.us"
        ]

        url_lower = url.lower()
        for domain in excluded_domains:
            if domain in url_lower:
                return False

        # Must be http/https
        if not url.startswith("http"):
            return False

        return True

    def _try_serpapi(self, company_record: Dict) -> EnrichmentResult:
        """Try SerpAPI Google search for website"""
        print("  [SerpAPI] Searching Google for company website...")

        company_name = company_record.get("company_name", "")
        state = company_record.get("state", "")
        city = company_record.get("city", "")

        if not company_name:
            return EnrichmentResult(
                success=False,
                tier="tier_1",
                agent_name="SerpAPI",
                cost=0.0,
                errors=["SerpAPI: No company name provided"]
            )

        # Build search query
        query = f"{company_name}"
        if city and state:
            query += f" {city} {state}"
        elif state:
            query += f" {state}"
        query += " official website"

        try:
            # Call SerpAPI
            response = requests.get(
                "https://serpapi.com/search",
                params={
                    "q": query,
                    "api_key": self.serpapi_key,
                    "engine": "google"
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()

                # Extract website from organic results
                organic_results = data.get("organic_results", [])
                if organic_results:
                    first_result = organic_results[0]
                    website = first_result.get("link", "")

                    if website and website.startswith("http"):
                        print(f"  [SerpAPI SUCCESS] Found: {website}")
                        return EnrichmentResult(
                            success=True,
                            tier="tier_1",
                            agent_name="SerpAPI",
                            enriched_data={"website": website},
                            cost=self.TIER_1_COST
                        )

            return EnrichmentResult(
                success=False,
                tier="tier_1",
                agent_name="SerpAPI",
                cost=0.0,
                errors=[f"SerpAPI: No website found in search results"]
            )

        except requests.exceptions.Timeout:
            return EnrichmentResult(
                success=False,
                tier="tier_1",
                agent_name="SerpAPI",
                cost=0.0,
                errors=["SerpAPI: Request timeout"]
            )
        except Exception as e:
            return EnrichmentResult(
                success=False,
                tier="tier_1",
                agent_name="SerpAPI",
                cost=0.0,
                errors=[f"SerpAPI: {str(e)}"]
            )

    def _try_scraperapi(self, company_record: Dict) -> EnrichmentResult:
        """
        Try ScraperAPI to scrape Google search results for company website.

        Cost: $0.001 per request ($49/month for 100K requests)
        Much cheaper than Firecrawl ($0.20) or SerpAPI ($0.20)!

        API: https://api.scraperapi.com/?api_key=KEY&url=ENCODED_URL
        """
        print("  [ScraperAPI] Scraping Google for company website...")

        # SAFETY: Rate limit check
        if SAFETY_ENABLED:
            waited = rate_limiter.wait_if_needed("scraperapi")
            if waited > 0:
                print(f"  [ScraperAPI] Rate limited, waited {waited:.1f}s")

        company_name = company_record.get("company_name", "")
        state = company_record.get("state", "")
        city = company_record.get("city", "")

        if not company_name:
            return EnrichmentResult(
                success=False,
                tier="tier_1",
                agent_name="ScraperAPI",
                cost=0.0,
                errors=["ScraperAPI: No company name provided"]
            )

        # Build Google search query
        search_query = f"{company_name}"
        if city and state:
            search_query += f" {city} {state}"
        elif state:
            search_query += f" {state}"
        search_query += " official website"

        # URL encode the Google search URL
        from urllib.parse import quote
        google_url = f"https://www.google.com/search?q={quote(search_query)}"

        try:
            # ScraperAPI endpoint
            response = requests.get(
                "https://api.scraperapi.com/",
                params={
                    "api_key": self.scraperapi_key,
                    "url": google_url,
                    "render": "false",  # Don't need JS rendering for Google
                },
                timeout=30
            )

            if response.status_code == 200:
                html = response.text

                # Parse Google search results to extract URLs
                website = self._parse_google_results_for_website(html, company_name)

                if website:
                    print(f"  [ScraperAPI SUCCESS] Found: {safe_str(website)}")
                    if SAFETY_ENABLED:
                        rate_limiter.record_success("scraperapi")
                    return EnrichmentResult(
                        success=True,
                        tier="tier_1",
                        agent_name="ScraperAPI",
                        enriched_data={"website": website},
                        cost=0.001  # ScraperAPI cost per request
                    )

                # No valid website found
                if SAFETY_ENABLED:
                    rate_limiter.record_failure("scraperapi")
                return EnrichmentResult(
                    success=False,
                    tier="tier_1",
                    agent_name="ScraperAPI",
                    cost=0.001,  # Still costs money even on failure
                    errors=["ScraperAPI: No valid company website found in Google results"]
                )

            elif response.status_code == 401:
                if SAFETY_ENABLED:
                    rate_limiter.record_failure("scraperapi")
                return EnrichmentResult(
                    success=False,
                    tier="tier_1",
                    agent_name="ScraperAPI",
                    cost=0.0,
                    errors=["ScraperAPI: Invalid API key"]
                )

            elif response.status_code == 429:
                if SAFETY_ENABLED:
                    rate_limiter.record_failure("scraperapi")
                return EnrichmentResult(
                    success=False,
                    tier="tier_1",
                    agent_name="ScraperAPI",
                    cost=0.0,
                    errors=[f"ScraperAPI: Rate limited (429)"]
                )

            elif response.status_code == 403:
                if SAFETY_ENABLED:
                    rate_limiter.record_failure("scraperapi")
                return EnrichmentResult(
                    success=False,
                    tier="tier_1",
                    agent_name="ScraperAPI",
                    cost=0.0,
                    errors=[f"ScraperAPI: Access forbidden - check account status"]
                )

            else:
                if SAFETY_ENABLED:
                    rate_limiter.record_failure("scraperapi")
                return EnrichmentResult(
                    success=False,
                    tier="tier_1",
                    agent_name="ScraperAPI",
                    cost=0.0,
                    errors=[f"ScraperAPI: API error {response.status_code}"]
                )

        except requests.exceptions.Timeout:
            if SAFETY_ENABLED:
                rate_limiter.record_failure("scraperapi")
            return EnrichmentResult(
                success=False,
                tier="tier_1",
                agent_name="ScraperAPI",
                cost=0.0,
                errors=["ScraperAPI: Request timeout (30s)"]
            )
        except Exception as e:
            if SAFETY_ENABLED:
                rate_limiter.record_failure("scraperapi")
            return EnrichmentResult(
                success=False,
                tier="tier_1",
                agent_name="ScraperAPI",
                cost=0.0,
                errors=[f"ScraperAPI: {str(e)}"]
            )

    def _parse_google_results_for_website(self, html: str, company_name: str) -> Optional[str]:
        """
        Parse Google search results HTML to extract company website URL.

        Args:
            html: Raw HTML from Google search
            company_name: Company name for validation

        Returns:
            Website URL or None
        """
        import re
        from urllib.parse import unquote

        # List of patterns to try (in order of preference)
        patterns = [
            # Pattern 1: Google's /url?q= redirect links
            r'/url\?q=(https?://[^&"]+)',
            # Pattern 2: Direct href links (excluding Google domains)
            r'href="(https?://(?!www\.google|accounts\.google|support\.google|maps\.google|play\.google)[^"]+)"',
            # Pattern 3: URLs in JSON-like structures (Google sometimes uses these)
            r'"url":"(https?://[^"]+)"',
            # Pattern 4: Cite/source URLs in search results
            r'<cite[^>]*>(https?://[^<]+)</cite>',
        ]

        all_urls = []

        for pattern in patterns:
            matches = re.findall(pattern, html)
            for url in matches:
                url = unquote(url)
                # Clean up any HTML entities
                url = url.replace('&amp;', '&')
                if url not in all_urls:
                    all_urls.append(url)

        # Filter and validate URLs
        for url in all_urls:
            # Skip Google-related URLs
            if 'google.com' in url or 'googleapis.com' in url or 'googleadservices.com' in url:
                continue
            if 'gstatic.com' in url:
                continue

            # Check if it's a valid company website
            if self._is_valid_company_website(url, company_name):
                return url

        # If no valid URL found with strict validation, try a more lenient approach
        # Accept any URL that's not in our excluded list
        for url in all_urls:
            if 'google' in url.lower():
                continue
            if not url.startswith('http'):
                continue

            # Check against excluded domains only (not company name matching)
            is_excluded = False
            excluded_domains = [
                "linkedin.com", "facebook.com", "twitter.com", "instagram.com",
                "youtube.com", "yelp.com", "yellowpages.com", "bbb.org",
                "manta.com", "dnb.com", "zoominfo.com", "crunchbase.com",
                "glassdoor.com", "indeed.com", "wikipedia.org", "bloomberg.com",
                "mapquest.com", "apple.com", "wv.gov", "state.wv.us",
                "findlaw.com", "justia.com", "superpages.com", "whitepages.com",
                "angieslist.com", "thumbtack.com", "houzz.com", "homeadvisor.com",
                "support.google", "accounts.google", "play.google", "maps.google",
            ]

            for domain in excluded_domains:
                if domain in url.lower():
                    is_excluded = True
                    break

            if not is_excluded:
                return url

        return None

    # ========================================================================
    # TIER 2 IMPLEMENTATIONS
    # ========================================================================

    def _try_clearbit(self, company_record: Dict) -> EnrichmentResult:
        """Try Clearbit Company API"""
        print("  [Clearbit] Looking up company...")

        # Not implemented yet
        return EnrichmentResult(
            success=False,
            tier="tier_2",
            agent_name="Clearbit",
            cost=0.0,
            errors=["Clearbit: Not implemented yet"]
        )

    def _try_abacus(self, company_record: Dict) -> EnrichmentResult:
        """Try Abacus.ai"""
        print("  [Abacus.ai] Querying...")

        # Not implemented yet
        return EnrichmentResult(
            success=False,
            tier="tier_2",
            agent_name="Abacus.ai",
            cost=0.0,
            errors=["Abacus.ai: Not implemented yet"]
        )

    # ========================================================================
    # TIER 3 IMPLEMENTATIONS
    # ========================================================================

    def _try_peopledatalabs(self, company_record: Dict) -> EnrichmentResult:
        """Try People Data Labs Company Enrichment API"""
        print("  [People Data Labs] Enriching company...")

        # Not implemented yet
        return EnrichmentResult(
            success=False,
            tier="tier_3",
            agent_name="People Data Labs",
            cost=0.0,
            errors=["People Data Labs: Not implemented yet"]
        )

    def _try_rocketreach(self, company_record: Dict) -> EnrichmentResult:
        """Try RocketReach"""
        print("  [RocketReach] Searching...")

        # Not implemented yet
        return EnrichmentResult(
            success=False,
            tier="tier_3",
            agent_name="RocketReach",
            cost=0.0,
            errors=["RocketReach: Not implemented yet"]
        )

    def _try_apify(self, company_record: Dict) -> EnrichmentResult:
        """Try Apify web scraping"""
        print("  [Apify] Running scraper...")

        # Not implemented yet
        return EnrichmentResult(
            success=False,
            tier="tier_3",
            agent_name="Apify",
            cost=0.0,
            errors=["Apify: Not implemented yet"]
        )


# ============================================================================
# PUBLIC API
# ============================================================================

def attempt_enrichment(company_record: Dict, failure_reason: str) -> Dict:
    """
    Public API: Attempt to enrich a company record

    Args:
        company_record: Dict with company data
        failure_reason: Why validation failed

    Returns:
        Dict with success, enriched_data, cost, errors
    """
    waterfall = EnrichmentWaterfall()
    result = waterfall.attempt_enrichment(company_record, failure_reason)
    return result.to_dict()


# ============================================================================
# CLI TESTING
# ============================================================================

if __name__ == "__main__":
    # Test with a sample company
    test_company = {
        "company_name": "Mountaineer Casino Resort",
        "state": "West Virginia",
        "city": "New Cumberland",
        "employee_count": 280
    }

    print("Testing enrichment waterfall...")
    result = attempt_enrichment(test_company, "missing_website")

    print("\n" + "="*80)
    print("FINAL RESULT:")
    print(json.dumps(result, indent=2))
    print("="*80)
