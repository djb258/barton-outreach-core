"""
Provider Utilities
==================
API provider wrappers for email pattern discovery.
Implements tiered waterfall: Tier 0 (free) → Tier 1 (low cost) → Tier 2 (premium).

Integrated with Provider Benchmark Engine (PBE) for metrics tracking.
"""

import re
import time
import json
import logging
import requests
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from urllib.parse import urljoin, quote

# Provider Benchmark Engine (System-Level) - Optional import
try:
    from ctb.sys.enrichment.provider_benchmark import ProviderBenchmarkEngine
    _PBE_AVAILABLE = True
except ImportError:
    _PBE_AVAILABLE = False


class ProviderTier(Enum):
    """Provider tier classification."""
    TIER_0 = 0  # Free
    TIER_1 = 1  # Low cost
    TIER_2 = 2  # Premium


class ProviderStatus(Enum):
    """Provider availability status."""
    AVAILABLE = "available"
    RATE_LIMITED = "rate_limited"
    UNAVAILABLE = "unavailable"
    NO_API_KEY = "no_api_key"
    ERROR = "error"


@dataclass
class EmailSample:
    """A sample email found by provider."""
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    confidence: float = 0.0
    source: str = ""


@dataclass
class ProviderResult:
    """Result from a provider API call."""
    success: bool
    pattern: Optional[str] = None
    sample_emails: List[EmailSample] = field(default_factory=list)
    confidence: float = 0.0
    provider_name: str = ""
    tier: ProviderTier = ProviderTier.TIER_0
    cost_credits: float = 0.0
    raw_response: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    request_time_ms: int = 0

    def has_pattern(self) -> bool:
        """Check if a valid pattern was found."""
        return self.success and self.pattern is not None and len(self.pattern) > 0


@dataclass
class ProviderStats:
    """Statistics for a provider."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_credits_used: float = 0.0
    avg_response_time_ms: float = 0.0
    patterns_found: int = 0
    rate_limit_hits: int = 0


class ProviderBase(ABC):
    """
    Base class for email pattern providers.

    All providers must implement:
    - discover_pattern(): Find email pattern for domain
    - get_tier(): Return provider tier
    - get_cost(): Return cost per request
    """

    def __init__(self, api_key: str = None, config: Dict[str, Any] = None):
        """
        Initialize provider.

        Args:
            api_key: API key for provider
            config: Additional configuration
        """
        self.api_key = api_key or ""
        self.config = config or {}
        self.stats = ProviderStats()
        self.logger = logging.getLogger(f"provider.{self.__class__.__name__}")

        # Rate limiting
        self.rate_limit_per_minute = self.config.get('rate_limit', 60)
        self.request_timestamps: List[float] = []

        # Retry settings
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1.0)
        self.timeout = self.config.get('timeout', 30)

    @abstractmethod
    def discover_pattern(self, domain: str,
                         company_name: str = None) -> ProviderResult:
        """
        Discover email pattern for domain.

        Args:
            domain: Domain to discover pattern for
            company_name: Optional company name for context

        Returns:
            ProviderResult with pattern info
        """
        pass

    @abstractmethod
    def get_tier(self) -> ProviderTier:
        """Return provider tier."""
        pass

    @abstractmethod
    def get_cost(self) -> float:
        """Return cost per request in credits."""
        pass

    @property
    def name(self) -> str:
        """Get provider name."""
        return self.__class__.__name__.replace('Provider', '').lower()

    def is_available(self) -> Tuple[bool, ProviderStatus]:
        """
        Check if provider is configured and available.

        Returns:
            Tuple of (is_available, status)
        """
        # Check API key
        if self.requires_api_key() and not self.api_key:
            return (False, ProviderStatus.NO_API_KEY)

        # Check rate limiting
        if self._is_rate_limited():
            return (False, ProviderStatus.RATE_LIMITED)

        return (True, ProviderStatus.AVAILABLE)

    def requires_api_key(self) -> bool:
        """Check if this provider requires an API key."""
        # Override in subclass if provider doesn't need API key
        return True

    def _is_rate_limited(self) -> bool:
        """Check if we've hit rate limits."""
        now = time.time()
        # Remove timestamps older than 1 minute
        self.request_timestamps = [
            ts for ts in self.request_timestamps
            if now - ts < 60
        ]
        return len(self.request_timestamps) >= self.rate_limit_per_minute

    def _record_request(self) -> None:
        """Record a request for rate limiting."""
        self.request_timestamps.append(time.time())
        self.stats.total_requests += 1

    def _record_pbe_metrics(
        self,
        success: bool,
        pattern_found: bool,
        verified: bool,
        latency_ms: float
    ) -> None:
        """
        Record metrics to Provider Benchmark Engine (PBE).

        Args:
            success: Whether the API call succeeded
            pattern_found: Whether a pattern was discovered
            verified: Whether the pattern was verified
            latency_ms: Response time in milliseconds
        """
        if not _PBE_AVAILABLE:
            return

        try:
            engine = ProviderBenchmarkEngine.get_instance()
            cost = self.get_cost()

            if success:
                engine.record_result(
                    provider_name=self.name,
                    pattern_found=pattern_found,
                    verified=verified,
                    latency=latency_ms,
                    cost=cost
                )
            else:
                engine.record_call(self.name, cost=cost)
                engine.record_error(self.name, error_type='error')
        except Exception:
            # Silently ignore PBE errors - metrics are non-critical
            pass

    def _record_pbe_timeout(self) -> None:
        """Record a timeout to PBE."""
        if not _PBE_AVAILABLE:
            return

        try:
            engine = ProviderBenchmarkEngine.get_instance()
            engine.record_call(self.name, cost=self.get_cost())
            engine.record_error(self.name, error_type='timeout')
        except Exception:
            pass

    def _make_request(self, method: str, url: str,
                      headers: Dict = None, params: Dict = None,
                      data: Dict = None, json_data: Dict = None) -> Tuple[bool, Any]:
        """
        Make HTTP request with retries.

        Args:
            method: HTTP method (GET, POST)
            url: Request URL
            headers: HTTP headers
            params: Query parameters
            data: Form data
            json_data: JSON body

        Returns:
            Tuple of (success, response_or_error)
        """
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()

                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    data=data,
                    json=json_data,
                    timeout=self.timeout
                )

                elapsed_ms = int((time.time() - start_time) * 1000)
                self._record_request()

                # Handle rate limiting
                if response.status_code == 429:
                    self.stats.rate_limit_hits += 1
                    wait_time = self.retry_delay * (2 ** attempt)
                    self.logger.warning(f"Rate limited, waiting {wait_time}s")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()

                return (True, {
                    'data': response.json() if response.text else {},
                    'elapsed_ms': elapsed_ms,
                    'status_code': response.status_code
                })

            except requests.exceptions.Timeout:
                self.logger.warning(f"Request timeout (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    return (False, str(e))

            except json.JSONDecodeError as e:
                return (False, f"Invalid JSON response: {e}")

        return (False, "Max retries exceeded")

    def _extract_pattern_from_emails(self, emails: List[EmailSample],
                                      domain: str) -> Optional[str]:
        """
        Analyze sample emails to extract pattern.

        Args:
            emails: List of sample emails
            domain: Company domain

        Returns:
            Detected pattern or None
        """
        if not emails:
            return None

        patterns_found = {}

        for sample in emails:
            if not sample.email or '@' not in sample.email:
                continue

            local_part = sample.email.split('@')[0].lower()
            first = (sample.first_name or '').lower()
            last = (sample.last_name or '').lower()

            if not first or not last:
                continue

            # Check common patterns
            pattern = None

            if local_part == f"{first}.{last}":
                pattern = "{first}.{last}"
            elif local_part == f"{first}{last}":
                pattern = "{first}{last}"
            elif local_part == f"{first[0]}{last}" if first else None:
                pattern = "{f}{last}"
            elif local_part == f"{first}{last[0]}" if last else None:
                pattern = "{first}{l}"
            elif local_part == f"{first[0]}.{last}" if first else None:
                pattern = "{f}.{last}"
            elif local_part == f"{first}_{last}":
                pattern = "{first}_{last}"
            elif local_part == f"{last}.{first}":
                pattern = "{last}.{first}"
            elif local_part == f"{last}{first}":
                pattern = "{last}{first}"
            elif local_part == first:
                pattern = "{first}"
            elif local_part == last:
                pattern = "{last}"

            if pattern:
                patterns_found[pattern] = patterns_found.get(pattern, 0) + 1

        if not patterns_found:
            return None

        # Return most common pattern
        return max(patterns_found, key=patterns_found.get)


# =============================================================================
# TIER 0: Free Providers
# =============================================================================

class FirecrawlProvider(ProviderBase):
    """
    Firecrawl web scraping provider.

    Tier: 0 (Free)
    Method: Scrape website for email patterns from contact pages
    """

    BASE_URL = "https://api.firecrawl.dev/v0"

    def discover_pattern(self, domain: str,
                         company_name: str = None) -> ProviderResult:
        """Scrape website to find email patterns."""
        start_time = time.time()

        available, status = self.is_available()
        if not available:
            return ProviderResult(
                success=False,
                provider_name=self.name,
                tier=self.get_tier(),
                error_message=f"Provider unavailable: {status.value}"
            )

        # Target pages to scrape
        pages_to_try = [
            f"https://{domain}",
            f"https://{domain}/contact",
            f"https://{domain}/about",
            f"https://{domain}/team",
            f"https://www.{domain}",
            f"https://www.{domain}/contact"
        ]

        all_emails = []
        raw_response = {}

        for page_url in pages_to_try:
            success, response = self._make_request(
                method='POST',
                url=f"{self.BASE_URL}/scrape",
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json_data={
                    'url': page_url,
                    'formats': ['markdown', 'html']
                }
            )

            if success and response.get('data'):
                raw_response[page_url] = response['data']

                # Extract emails from scraped content
                content = response['data'].get('data', {})
                markdown = content.get('markdown', '')
                html = content.get('html', '')

                emails = self._extract_emails_from_text(markdown + ' ' + html, domain)
                all_emails.extend(emails)

        # Deduplicate
        seen = set()
        unique_emails = []
        for email in all_emails:
            if email.email not in seen:
                seen.add(email.email)
                unique_emails.append(email)

        elapsed_ms = int((time.time() - start_time) * 1000)

        if unique_emails:
            pattern = self._extract_pattern_from_emails(unique_emails, domain)
            self.stats.successful_requests += 1
            if pattern:
                self.stats.patterns_found += 1

            # PBE Hook: Record successful pattern discovery
            self._record_pbe_metrics(
                success=True,
                pattern_found=pattern is not None,
                verified=False,  # Not verified yet
                latency_ms=elapsed_ms
            )

            return ProviderResult(
                success=True,
                pattern=pattern,
                sample_emails=unique_emails,
                confidence=0.7 if pattern else 0.3,
                provider_name=self.name,
                tier=self.get_tier(),
                cost_credits=self.get_cost(),
                raw_response=raw_response,
                request_time_ms=elapsed_ms
            )

        self.stats.failed_requests += 1

        # PBE Hook: Record failed pattern discovery
        self._record_pbe_metrics(
            success=True,  # API call succeeded, but no pattern
            pattern_found=False,
            verified=False,
            latency_ms=elapsed_ms
        )

        return ProviderResult(
            success=False,
            provider_name=self.name,
            tier=self.get_tier(),
            cost_credits=self.get_cost(),
            raw_response=raw_response,
            error_message="No emails found on website",
            request_time_ms=elapsed_ms
        )

    def _extract_emails_from_text(self, text: str, domain: str) -> List[EmailSample]:
        """Extract emails from text content."""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        found = re.findall(email_pattern, text)

        emails = []
        for email in found:
            email = email.lower()
            # Only include emails from the target domain
            if email.endswith(f"@{domain}"):
                # Try to extract name parts
                local = email.split('@')[0]
                first, last = self._parse_name_from_local(local)

                emails.append(EmailSample(
                    email=email,
                    first_name=first,
                    last_name=last,
                    confidence=0.6,
                    source='firecrawl_scrape'
                ))

        return emails

    def _parse_name_from_local(self, local: str) -> Tuple[Optional[str], Optional[str]]:
        """Try to parse first/last name from email local part."""
        # Common separators
        for sep in ['.', '_', '-']:
            if sep in local:
                parts = local.split(sep)
                if len(parts) >= 2:
                    return (parts[0].title(), parts[-1].title())

        return (None, None)

    def get_tier(self) -> ProviderTier:
        return ProviderTier.TIER_0

    def get_cost(self) -> float:
        return 0.0


class GooglePlacesProvider(ProviderBase):
    """
    Google Places API provider.

    Tier: 0 (Free tier available)
    Method: Get business info including website and contact
    """

    BASE_URL = "https://maps.googleapis.com/maps/api/place"

    def discover_pattern(self, domain: str,
                         company_name: str = None) -> ProviderResult:
        """Get business email from Google Places."""
        start_time = time.time()

        available, status = self.is_available()
        if not available:
            return ProviderResult(
                success=False,
                provider_name=self.name,
                tier=self.get_tier(),
                error_message=f"Provider unavailable: {status.value}"
            )

        if not company_name:
            return ProviderResult(
                success=False,
                provider_name=self.name,
                tier=self.get_tier(),
                error_message="Company name required for Google Places search"
            )

        # Search for the business
        search_success, search_response = self._make_request(
            method='GET',
            url=f"{self.BASE_URL}/findplacefromtext/json",
            params={
                'input': company_name,
                'inputtype': 'textquery',
                'fields': 'place_id,name,formatted_address',
                'key': self.api_key
            }
        )

        elapsed_ms = int((time.time() - start_time) * 1000)

        if not search_success:
            self.stats.failed_requests += 1
            return ProviderResult(
                success=False,
                provider_name=self.name,
                tier=self.get_tier(),
                error_message=str(search_response),
                request_time_ms=elapsed_ms
            )

        candidates = search_response.get('data', {}).get('candidates', [])
        if not candidates:
            self.stats.failed_requests += 1
            return ProviderResult(
                success=False,
                provider_name=self.name,
                tier=self.get_tier(),
                raw_response=search_response.get('data', {}),
                error_message="No business found",
                request_time_ms=elapsed_ms
            )

        # Get place details
        place_id = candidates[0].get('place_id')
        details_success, details_response = self._make_request(
            method='GET',
            url=f"{self.BASE_URL}/details/json",
            params={
                'place_id': place_id,
                'fields': 'name,website,formatted_phone_number',
                'key': self.api_key
            }
        )

        if not details_success:
            self.stats.failed_requests += 1
            return ProviderResult(
                success=False,
                provider_name=self.name,
                tier=self.get_tier(),
                error_message=str(details_response),
                request_time_ms=elapsed_ms
            )

        result = details_response.get('data', {}).get('result', {})
        website = result.get('website', '')

        self.stats.successful_requests += 1

        # Google Places doesn't provide emails directly
        # but confirms the domain and provides business verification
        return ProviderResult(
            success=True,
            pattern=None,  # No pattern from Places
            sample_emails=[],
            confidence=0.5,  # Just domain verification
            provider_name=self.name,
            tier=self.get_tier(),
            cost_credits=self.get_cost(),
            raw_response={'search': search_response.get('data'), 'details': result},
            request_time_ms=elapsed_ms
        )

    def get_tier(self) -> ProviderTier:
        return ProviderTier.TIER_0

    def get_cost(self) -> float:
        return 0.0


class WebScraperProvider(ProviderBase):
    """
    Generic web scraper for contact page emails.

    Tier: 0 (Free)
    Method: Direct HTTP scraping of contact pages
    """

    def discover_pattern(self, domain: str,
                         company_name: str = None) -> ProviderResult:
        """Scrape website contact pages for emails."""
        start_time = time.time()

        pages = [
            f"https://{domain}/contact",
            f"https://{domain}/about",
            f"https://{domain}/team",
            f"https://www.{domain}/contact",
            f"https://{domain}/contact-us",
        ]

        all_emails = []

        for url in pages:
            try:
                response = requests.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; EmailBot/1.0)'
                })
                if response.status_code == 200:
                    emails = self._extract_emails(response.text, domain)
                    all_emails.extend(emails)
            except Exception:
                continue

        elapsed_ms = int((time.time() - start_time) * 1000)

        # Deduplicate
        seen = set()
        unique = []
        for e in all_emails:
            if e.email not in seen:
                seen.add(e.email)
                unique.append(e)

        if unique:
            pattern = self._extract_pattern_from_emails(unique, domain)
            self.stats.successful_requests += 1
            return ProviderResult(
                success=True,
                pattern=pattern,
                sample_emails=unique,
                confidence=0.6 if pattern else 0.3,
                provider_name=self.name,
                tier=self.get_tier(),
                cost_credits=0.0,
                request_time_ms=elapsed_ms
            )

        self.stats.failed_requests += 1
        return ProviderResult(
            success=False,
            provider_name=self.name,
            tier=self.get_tier(),
            error_message="No emails found",
            request_time_ms=elapsed_ms
        )

    def _extract_emails(self, html: str, domain: str) -> List[EmailSample]:
        """Extract emails from HTML."""
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        found = re.findall(pattern, html)

        emails = []
        for email in set(found):
            email = email.lower()
            if email.endswith(f"@{domain}"):
                local = email.split('@')[0]
                first, last = None, None
                if '.' in local:
                    parts = local.split('.')
                    first, last = parts[0].title(), parts[-1].title()

                emails.append(EmailSample(
                    email=email,
                    first_name=first,
                    last_name=last,
                    confidence=0.5,
                    source='web_scrape'
                ))

        return emails

    def requires_api_key(self) -> bool:
        return False

    def get_tier(self) -> ProviderTier:
        return ProviderTier.TIER_0

    def get_cost(self) -> float:
        return 0.0


# =============================================================================
# TIER 1: Low Cost Providers
# =============================================================================

class HunterProvider(ProviderBase):
    """
    Hunter.io email finder provider.

    Tier: 1 (Low cost)
    Method: Domain search API returns email pattern and samples
    """

    BASE_URL = "https://api.hunter.io/v2"

    def discover_pattern(self, domain: str,
                         company_name: str = None) -> ProviderResult:
        """Find email pattern via Hunter.io API."""
        start_time = time.time()

        available, status = self.is_available()
        if not available:
            return ProviderResult(
                success=False,
                provider_name=self.name,
                tier=self.get_tier(),
                error_message=f"Provider unavailable: {status.value}"
            )

        success, response = self._make_request(
            method='GET',
            url=f"{self.BASE_URL}/domain-search",
            params={
                'domain': domain,
                'api_key': self.api_key
            }
        )

        elapsed_ms = int((time.time() - start_time) * 1000)
        self.stats.total_credits_used += self.get_cost()

        if not success:
            self.stats.failed_requests += 1
            return ProviderResult(
                success=False,
                provider_name=self.name,
                tier=self.get_tier(),
                cost_credits=self.get_cost(),
                error_message=str(response),
                request_time_ms=elapsed_ms
            )

        data = response.get('data', {}).get('data', {})

        # Hunter provides pattern directly
        pattern = data.get('pattern')
        emails_data = data.get('emails', [])

        sample_emails = []
        for e in emails_data[:10]:  # Limit to 10 samples
            sample_emails.append(EmailSample(
                email=e.get('value', ''),
                first_name=e.get('first_name'),
                last_name=e.get('last_name'),
                title=e.get('position'),
                confidence=e.get('confidence', 0) / 100.0,
                source='hunter'
            ))

        self.stats.successful_requests += 1
        if pattern:
            self.stats.patterns_found += 1

        # PBE Hook: Record Hunter.io result
        self._record_pbe_metrics(
            success=True,
            pattern_found=pattern is not None,
            verified=False,
            latency_ms=elapsed_ms
        )

        return ProviderResult(
            success=True,
            pattern=self._normalize_hunter_pattern(pattern) if pattern else None,
            sample_emails=sample_emails,
            confidence=0.9 if pattern else 0.5,
            provider_name=self.name,
            tier=self.get_tier(),
            cost_credits=self.get_cost(),
            raw_response=data,
            request_time_ms=elapsed_ms
        )

    def _normalize_hunter_pattern(self, hunter_pattern: str) -> str:
        """Convert Hunter pattern format to our format."""
        # Hunter uses {first}{last}, {f}{last}, etc.
        # Ensure consistent format
        pattern = hunter_pattern.lower()
        pattern = pattern.replace('{first}', '{first}')
        pattern = pattern.replace('{last}', '{last}')
        pattern = pattern.replace('{f}', '{f}')
        pattern = pattern.replace('{l}', '{l}')
        return pattern

    def get_tier(self) -> ProviderTier:
        return ProviderTier.TIER_1

    def get_cost(self) -> float:
        return 1.0


class ClearbitProvider(ProviderBase):
    """
    Clearbit company enrichment provider.

    Tier: 1 (Low cost)
    Method: Company enrichment API
    """

    BASE_URL = "https://company.clearbit.com/v2"

    def discover_pattern(self, domain: str,
                         company_name: str = None) -> ProviderResult:
        """Get company info via Clearbit (no direct email pattern)."""
        start_time = time.time()

        available, status = self.is_available()
        if not available:
            return ProviderResult(
                success=False,
                provider_name=self.name,
                tier=self.get_tier(),
                error_message=f"Provider unavailable: {status.value}"
            )

        success, response = self._make_request(
            method='GET',
            url=f"{self.BASE_URL}/companies/find",
            headers={'Authorization': f'Bearer {self.api_key}'},
            params={'domain': domain}
        )

        elapsed_ms = int((time.time() - start_time) * 1000)
        self.stats.total_credits_used += self.get_cost()

        if not success:
            self.stats.failed_requests += 1
            return ProviderResult(
                success=False,
                provider_name=self.name,
                tier=self.get_tier(),
                cost_credits=self.get_cost(),
                error_message=str(response),
                request_time_ms=elapsed_ms
            )

        data = response.get('data', {})
        self.stats.successful_requests += 1

        # Clearbit doesn't provide email patterns directly
        # but provides company enrichment data
        return ProviderResult(
            success=True,
            pattern=None,
            sample_emails=[],
            confidence=0.5,
            provider_name=self.name,
            tier=self.get_tier(),
            cost_credits=self.get_cost(),
            raw_response=data,
            request_time_ms=elapsed_ms
        )

    def get_tier(self) -> ProviderTier:
        return ProviderTier.TIER_1

    def get_cost(self) -> float:
        return 1.0


class ApolloProvider(ProviderBase):
    """
    Apollo.io email provider.

    Tier: 1 (Low cost)
    Method: People search API with email enrichment
    """

    BASE_URL = "https://api.apollo.io/v1"

    def discover_pattern(self, domain: str,
                         company_name: str = None) -> ProviderResult:
        """Find email pattern via Apollo.io."""
        start_time = time.time()

        available, status = self.is_available()
        if not available:
            return ProviderResult(
                success=False,
                provider_name=self.name,
                tier=self.get_tier(),
                error_message=f"Provider unavailable: {status.value}"
            )

        # Search for people at the company
        success, response = self._make_request(
            method='POST',
            url=f"{self.BASE_URL}/mixed_people/search",
            headers={
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache'
            },
            json_data={
                'api_key': self.api_key,
                'q_organization_domains': domain,
                'page': 1,
                'per_page': 10
            }
        )

        elapsed_ms = int((time.time() - start_time) * 1000)
        self.stats.total_credits_used += self.get_cost()

        if not success:
            self.stats.failed_requests += 1
            return ProviderResult(
                success=False,
                provider_name=self.name,
                tier=self.get_tier(),
                cost_credits=self.get_cost(),
                error_message=str(response),
                request_time_ms=elapsed_ms
            )

        data = response.get('data', {})
        people = data.get('people', [])

        sample_emails = []
        for person in people:
            email = person.get('email')
            if email and email.endswith(f"@{domain}"):
                sample_emails.append(EmailSample(
                    email=email,
                    first_name=person.get('first_name'),
                    last_name=person.get('last_name'),
                    title=person.get('title'),
                    confidence=0.85,
                    source='apollo'
                ))

        pattern = self._extract_pattern_from_emails(sample_emails, domain)

        self.stats.successful_requests += 1
        if pattern:
            self.stats.patterns_found += 1

        return ProviderResult(
            success=True,
            pattern=pattern,
            sample_emails=sample_emails,
            confidence=0.85 if pattern else 0.4,
            provider_name=self.name,
            tier=self.get_tier(),
            cost_credits=self.get_cost(),
            raw_response=data,
            request_time_ms=elapsed_ms
        )

    def get_tier(self) -> ProviderTier:
        return ProviderTier.TIER_1

    def get_cost(self) -> float:
        return 1.0


# =============================================================================
# TIER 2: Premium Providers
# =============================================================================

class ProspeoProvider(ProviderBase):
    """
    Prospeo email finder provider.

    Tier: 2 (Premium)
    Method: Email finder API with domain search
    """

    BASE_URL = "https://api.prospeo.io/v1"

    def discover_pattern(self, domain: str,
                         company_name: str = None) -> ProviderResult:
        """Find email pattern via Prospeo."""
        start_time = time.time()

        available, status = self.is_available()
        if not available:
            return ProviderResult(
                success=False,
                provider_name=self.name,
                tier=self.get_tier(),
                error_message=f"Provider unavailable: {status.value}"
            )

        success, response = self._make_request(
            method='POST',
            url=f"{self.BASE_URL}/domain-search",
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            },
            json_data={'domain': domain}
        )

        elapsed_ms = int((time.time() - start_time) * 1000)
        self.stats.total_credits_used += self.get_cost()

        if not success:
            self.stats.failed_requests += 1
            return ProviderResult(
                success=False,
                provider_name=self.name,
                tier=self.get_tier(),
                cost_credits=self.get_cost(),
                error_message=str(response),
                request_time_ms=elapsed_ms
            )

        data = response.get('data', {})
        emails_data = data.get('emails', [])

        sample_emails = []
        for e in emails_data[:10]:
            sample_emails.append(EmailSample(
                email=e.get('email', ''),
                first_name=e.get('first_name'),
                last_name=e.get('last_name'),
                title=e.get('position'),
                confidence=e.get('score', 0) / 100.0,
                source='prospeo'
            ))

        pattern = data.get('pattern') or self._extract_pattern_from_emails(sample_emails, domain)

        self.stats.successful_requests += 1
        if pattern:
            self.stats.patterns_found += 1

        return ProviderResult(
            success=True,
            pattern=pattern,
            sample_emails=sample_emails,
            confidence=0.92 if pattern else 0.5,
            provider_name=self.name,
            tier=self.get_tier(),
            cost_credits=self.get_cost(),
            raw_response=data,
            request_time_ms=elapsed_ms
        )

    def get_tier(self) -> ProviderTier:
        return ProviderTier.TIER_2

    def get_cost(self) -> float:
        return 5.0


class SnovProvider(ProviderBase):
    """
    Snov.io email finder provider.

    Tier: 2 (Premium)
    Method: Domain email search
    """

    BASE_URL = "https://api.snov.io/v1"

    def discover_pattern(self, domain: str,
                         company_name: str = None) -> ProviderResult:
        """Find email pattern via Snov.io."""
        start_time = time.time()

        available, status = self.is_available()
        if not available:
            return ProviderResult(
                success=False,
                provider_name=self.name,
                tier=self.get_tier(),
                error_message=f"Provider unavailable: {status.value}"
            )

        # Get domain emails count first
        success, response = self._make_request(
            method='POST',
            url=f"{self.BASE_URL}/get-domain-emails-count",
            data={
                'access_token': self.api_key,
                'domain': domain
            }
        )

        if not success:
            elapsed_ms = int((time.time() - start_time) * 1000)
            self.stats.failed_requests += 1
            return ProviderResult(
                success=False,
                provider_name=self.name,
                tier=self.get_tier(),
                cost_credits=self.get_cost(),
                error_message=str(response),
                request_time_ms=elapsed_ms
            )

        # Get actual emails
        success, response = self._make_request(
            method='POST',
            url=f"{self.BASE_URL}/get-domain-emails-with-info",
            data={
                'access_token': self.api_key,
                'domain': domain,
                'type': 'all',
                'limit': 10
            }
        )

        elapsed_ms = int((time.time() - start_time) * 1000)
        self.stats.total_credits_used += self.get_cost()

        if not success:
            self.stats.failed_requests += 1
            return ProviderResult(
                success=False,
                provider_name=self.name,
                tier=self.get_tier(),
                cost_credits=self.get_cost(),
                error_message=str(response),
                request_time_ms=elapsed_ms
            )

        data = response.get('data', {})
        emails_data = data.get('emails', [])

        sample_emails = []
        for e in emails_data:
            sample_emails.append(EmailSample(
                email=e.get('email', ''),
                first_name=e.get('firstName'),
                last_name=e.get('lastName'),
                title=e.get('position'),
                confidence=0.9,
                source='snov'
            ))

        pattern = self._extract_pattern_from_emails(sample_emails, domain)

        self.stats.successful_requests += 1
        if pattern:
            self.stats.patterns_found += 1

        return ProviderResult(
            success=True,
            pattern=pattern,
            sample_emails=sample_emails,
            confidence=0.9 if pattern else 0.5,
            provider_name=self.name,
            tier=self.get_tier(),
            cost_credits=self.get_cost(),
            raw_response=data,
            request_time_ms=elapsed_ms
        )

    def get_tier(self) -> ProviderTier:
        return ProviderTier.TIER_2

    def get_cost(self) -> float:
        return 5.0


class ClayProvider(ProviderBase):
    """
    Clay.com enrichment provider.

    Tier: 2 (Premium)
    Method: Full enrichment API with waterfall
    """

    BASE_URL = "https://api.clay.com/v1"

    def discover_pattern(self, domain: str,
                         company_name: str = None) -> ProviderResult:
        """Get email pattern via Clay."""
        start_time = time.time()

        available, status = self.is_available()
        if not available:
            return ProviderResult(
                success=False,
                provider_name=self.name,
                tier=self.get_tier(),
                error_message=f"Provider unavailable: {status.value}"
            )

        # Clay uses company enrichment
        success, response = self._make_request(
            method='POST',
            url=f"{self.BASE_URL}/enrich/company",
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            },
            json_data={
                'domain': domain,
                'name': company_name
            }
        )

        elapsed_ms = int((time.time() - start_time) * 1000)
        self.stats.total_credits_used += self.get_cost()

        if not success:
            self.stats.failed_requests += 1
            return ProviderResult(
                success=False,
                provider_name=self.name,
                tier=self.get_tier(),
                cost_credits=self.get_cost(),
                error_message=str(response),
                request_time_ms=elapsed_ms
            )

        data = response.get('data', {})

        # Clay may provide email pattern in enrichment
        pattern = data.get('email_pattern')
        sample_emails = []

        if data.get('sample_emails'):
            for e in data.get('sample_emails', []):
                sample_emails.append(EmailSample(
                    email=e.get('email', ''),
                    first_name=e.get('first_name'),
                    last_name=e.get('last_name'),
                    title=e.get('title'),
                    confidence=0.95,
                    source='clay'
                ))

        self.stats.successful_requests += 1
        if pattern:
            self.stats.patterns_found += 1

        return ProviderResult(
            success=True,
            pattern=pattern,
            sample_emails=sample_emails,
            confidence=0.95 if pattern else 0.6,
            provider_name=self.name,
            tier=self.get_tier(),
            cost_credits=self.get_cost(),
            raw_response=data,
            request_time_ms=elapsed_ms
        )

    def get_tier(self) -> ProviderTier:
        return ProviderTier.TIER_2

    def get_cost(self) -> float:
        return 10.0


# =============================================================================
# Provider Registry & Waterfall
# =============================================================================

class ProviderRegistry:
    """
    Registry of all available providers.
    Manages provider instantiation and waterfall execution.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize registry with configuration.

        Args:
            config: Dict with provider API keys and settings
        """
        self.config = config or {}
        self._providers: Dict[str, ProviderBase] = {}
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initialize all configured providers."""
        # Tier 0 providers
        if self.config.get('firecrawl_api_key'):
            self._providers['firecrawl'] = FirecrawlProvider(
                api_key=self.config['firecrawl_api_key'],
                config=self.config.get('firecrawl', {})
            )

        if self.config.get('google_places_api_key'):
            self._providers['google_places'] = GooglePlacesProvider(
                api_key=self.config['google_places_api_key'],
                config=self.config.get('google_places', {})
            )

        # Always add web scraper (no API key needed)
        self._providers['web_scraper'] = WebScraperProvider(config=self.config.get('web_scraper', {}))

        # Tier 1 providers
        if self.config.get('hunter_api_key'):
            self._providers['hunter'] = HunterProvider(
                api_key=self.config['hunter_api_key'],
                config=self.config.get('hunter', {})
            )

        if self.config.get('clearbit_api_key'):
            self._providers['clearbit'] = ClearbitProvider(
                api_key=self.config['clearbit_api_key'],
                config=self.config.get('clearbit', {})
            )

        if self.config.get('apollo_api_key'):
            self._providers['apollo'] = ApolloProvider(
                api_key=self.config['apollo_api_key'],
                config=self.config.get('apollo', {})
            )

        # Tier 2 providers
        if self.config.get('prospeo_api_key'):
            self._providers['prospeo'] = ProspeoProvider(
                api_key=self.config['prospeo_api_key'],
                config=self.config.get('prospeo', {})
            )

        if self.config.get('snov_api_key'):
            self._providers['snov'] = SnovProvider(
                api_key=self.config['snov_api_key'],
                config=self.config.get('snov', {})
            )

        if self.config.get('clay_api_key'):
            self._providers['clay'] = ClayProvider(
                api_key=self.config['clay_api_key'],
                config=self.config.get('clay', {})
            )

    def get_provider(self, name: str) -> Optional[ProviderBase]:
        """Get a specific provider by name."""
        return self._providers.get(name.lower())

    def get_providers_by_tier(self, tier: ProviderTier) -> List[ProviderBase]:
        """Get all providers for a given tier."""
        return [p for p in self._providers.values() if p.get_tier() == tier]

    def get_all_providers(self) -> Dict[ProviderTier, List[ProviderBase]]:
        """Get all configured providers grouped by tier."""
        result = {
            ProviderTier.TIER_0: [],
            ProviderTier.TIER_1: [],
            ProviderTier.TIER_2: []
        }
        for provider in self._providers.values():
            result[provider.get_tier()].append(provider)
        return result

    def get_available_providers(self) -> List[ProviderBase]:
        """Get all providers that are currently available."""
        available = []
        for provider in self._providers.values():
            is_avail, _ = provider.is_available()
            if is_avail:
                available.append(provider)
        return available


def execute_tier_waterfall(registry: ProviderRegistry,
                           domain: str,
                           company_name: str = None,
                           max_tier: ProviderTier = ProviderTier.TIER_2,
                           stop_on_pattern: bool = True) -> List[ProviderResult]:
    """
    Execute tiered provider waterfall.

    Starts with Tier 0 (free), progresses to Tier 1, then Tier 2.
    Stops when a pattern is found (if stop_on_pattern=True).

    Args:
        registry: Provider registry
        domain: Domain to search
        company_name: Optional company name
        max_tier: Maximum tier to try
        stop_on_pattern: Stop when pattern found

    Returns:
        List of ProviderResults from each provider tried
    """
    results = []
    providers_by_tier = registry.get_all_providers()

    for tier in [ProviderTier.TIER_0, ProviderTier.TIER_1, ProviderTier.TIER_2]:
        if tier.value > max_tier.value:
            break

        for provider in providers_by_tier.get(tier, []):
            is_avail, _ = provider.is_available()
            if not is_avail:
                continue

            result = provider.discover_pattern(domain, company_name)
            results.append(result)

            if result.has_pattern() and stop_on_pattern:
                return results

    return results


def get_best_result(results: List[ProviderResult]) -> Optional[ProviderResult]:
    """
    Get the best result from a list of provider results.

    Prioritizes by:
    1. Has pattern
    2. Confidence score
    3. Number of sample emails

    Args:
        results: List of provider results

    Returns:
        Best result or None
    """
    if not results:
        return None

    # Filter to successful results with patterns
    with_pattern = [r for r in results if r.has_pattern()]

    if with_pattern:
        # Sort by confidence, then by sample count
        with_pattern.sort(
            key=lambda r: (r.confidence, len(r.sample_emails)),
            reverse=True
        )
        return with_pattern[0]

    # Fall back to any successful result with samples
    with_samples = [r for r in results if r.success and r.sample_emails]
    if with_samples:
        with_samples.sort(key=lambda r: len(r.sample_emails), reverse=True)
        return with_samples[0]

    # Return first successful result
    successful = [r for r in results if r.success]
    return successful[0] if successful else None
