"""
ScraperAPI Agent - Web Scraping with Proxy Rotation
Barton Doctrine ID: 04.04.02.04.50000.004

Capabilities:
- scrape_website: Scrape any website with proxy rotation
- render_javascript: Scrape websites requiring JavaScript execution
- extract_structured: Extract structured data from websites
"""

import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from .base_agent import BaseEnrichmentAgent
import re


class ScraperAPIAgent(BaseEnrichmentAgent):
    """
    ScraperAPI agent for web scraping with proxy rotation
    """

    def __init__(self, config: Dict, api_key: Optional[str] = None):
        super().__init__(config, api_key)
        self.base_url = config.get('base_url', 'http://api.scraperapi.com')

    def get_capabilities(self) -> List[str]:
        """Return list of ScraperAPI capabilities"""
        return list(self.config.get('capabilities', {}).keys())

    async def enrich(
        self,
        capability: str,
        input_data: Dict[str, Any],
        timeout_override: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute ScraperAPI enrichment

        Args:
            capability: 'scrape_website', 'render_javascript', 'extract_structured'
            input_data: Input data
            timeout_override: Override timeout

        Returns:
            Enrichment result
        """
        start_time = asyncio.get_event_loop().time()

        # Get capability config
        capabilities = self.config.get('capabilities', {})
        if capability not in capabilities:
            return {
                'success': False,
                'data': {},
                'cost': 0.0,
                'duration_seconds': 0.0,
                'error': f"Unknown capability: {capability}"
            }

        # Route to appropriate handler
        if capability == 'scrape_website':
            result = await self._scrape_website(input_data)
        elif capability == 'render_javascript':
            result = await self._render_javascript(input_data)
        elif capability == 'extract_structured':
            result = await self._extract_structured(input_data)
        else:
            result = {
                'success': False,
                'data': {},
                'error': f"Handler not implemented for: {capability}"
            }

        # Calculate duration
        duration = asyncio.get_event_loop().time() - start_time

        result['duration_seconds'] = round(duration, 2)
        result['cost'] = result.get('cost', self.estimate_cost(capability))

        return result

    async def _make_request(
        self,
        url: str,
        render_js: bool = False,
        premium: bool = False
    ) -> Dict[str, Any]:
        """
        Make ScraperAPI request

        Args:
            url: URL to scrape
            render_js: Enable JavaScript rendering
            premium: Use premium proxy

        Returns:
            API response
        """
        params = {
            'api_key': self.api_key,
            'url': url,
            'render': 'true' if render_js else 'false',
            'premium': 'true' if premium else 'false',
            'country_code': 'us'
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        html = await response.text()
                        return {
                            'success': True,
                            'html': html,
                            'error': None
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'html': '',
                            'error': f"HTTP {response.status}: {error_text}"
                        }
            except Exception as e:
                return {
                    'success': False,
                    'html': '',
                    'error': str(e)
                }

    async def _scrape_website(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Scrape website for company data

        Input: website or company_name
        Output: employee_count, industry, phone, address (extracted from HTML)
        """
        website = input_data.get('website', '')

        if not website:
            company_name = input_data.get('company_name', '')
            if company_name:
                # Search for company website first
                website = await self._search_company_website(company_name)
                if not website:
                    return {
                        'success': False,
                        'data': {},
                        'error': 'Could not find company website'
                    }
            else:
                return {
                    'success': False,
                    'data': {},
                    'error': 'website or company_name required'
                }

        # Ensure website has protocol
        if not website.startswith('http'):
            website = f'https://{website}'

        result = await self._make_request(website, render_js=False)

        if not result['success']:
            return {
                'success': False,
                'data': {},
                'error': result['error']
            }

        # Extract structured data from HTML
        html = result['html']
        enriched = {}

        # Extract employee count
        employee_patterns = [
            r'(\d+[,\d]*)\s*(?:employees|team members|staff)',
            r'team of (\d+[,\d]*)',
            r'(\d+[,\d]*)\+?\s*people'
        ]
        for pattern in employee_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                try:
                    count_str = match.group(1).replace(',', '')
                    enriched['employee_count'] = int(count_str)
                    break
                except:
                    pass

        # Extract phone numbers
        phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phone_match = re.search(phone_pattern, html)
        if phone_match:
            enriched['phone'] = phone_match.group(0)

        # Extract industry from meta tags
        industry_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)', html, re.IGNORECASE)
        if industry_match:
            desc = industry_match.group(1).lower()
            industries = ['technology', 'finance', 'healthcare', 'education', 'retail', 'manufacturing', 'consulting']
            for ind in industries:
                if ind in desc:
                    enriched['industry'] = ind.capitalize()
                    break

        # Extract address
        address_pattern = r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)[,\s]+[A-Za-z\s]+[,\s]+[A-Z]{2}\s+\d{5}'
        address_match = re.search(address_pattern, html)
        if address_match:
            enriched['address'] = address_match.group(0)

        enriched['website'] = website

        return {
            'success': True,
            'data': enriched,
            'error': None
        }

    async def _render_javascript(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Scrape website with JavaScript rendering

        For websites that require JavaScript (React, Vue, etc.)
        """
        website = input_data.get('website', '')

        if not website:
            return {
                'success': False,
                'data': {},
                'error': 'website required'
            }

        if not website.startswith('http'):
            website = f'https://{website}'

        result = await self._make_request(website, render_js=True)

        if not result['success']:
            return {
                'success': False,
                'data': {},
                'error': result['error']
            }

        # Extract data (similar to scrape_website but from rendered HTML)
        html = result['html']
        enriched = {'website': website}

        # Basic extraction (can be enhanced)
        if 'employee' in html.lower():
            enriched['has_employee_data'] = True

        return {
            'success': True,
            'data': enriched,
            'error': None
        }

    async def _extract_structured(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract structured data using custom selectors

        Input: website, selectors (CSS/XPath)
        Output: Extracted data
        """
        website = input_data.get('website', '')
        selectors = input_data.get('selectors', {})

        if not website:
            return {
                'success': False,
                'data': {},
                'error': 'website required'
            }

        if not website.startswith('http'):
            website = f'https://{website}'

        result = await self._make_request(website, render_js=False)

        if not result['success']:
            return {
                'success': False,
                'data': {},
                'error': result['error']
            }

        # In production, you'd use BeautifulSoup or lxml here
        # For now, basic extraction
        html = result['html']
        enriched = {'website': website}

        return {
            'success': True,
            'data': enriched,
            'error': None
        }

    async def _search_company_website(self, company_name: str) -> Optional[str]:
        """
        Search for company website using Google

        Args:
            company_name: Company name

        Returns:
            Website URL or None
        """
        # Use ScraperAPI to search Google
        search_url = f"https://www.google.com/search?q={company_name}+official+website"

        result = await self._make_request(search_url, render_js=False)

        if not result['success']:
            return None

        html = result['html']

        # Extract first non-Google URL from search results
        url_pattern = r'href="(https?://[^"]+)"'
        matches = re.findall(url_pattern, html)

        for url in matches:
            if 'google.com' not in url and 'gstatic.com' not in url:
                # Clean up Google redirect URL
                if 'url?q=' in url:
                    url = url.split('url?q=')[1].split('&')[0]
                return url

        return None
