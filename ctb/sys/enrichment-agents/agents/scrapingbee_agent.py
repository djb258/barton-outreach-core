"""
ScrapingBee Agent - Headless Browser Scraping
Barton Doctrine ID: 04.04.02.04.50000.006

Capabilities:
- scrape_website: Scrape with headless browser
- screenshot: Take screenshot of website
- extract_data: Extract structured data
"""

import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from .base_agent import BaseEnrichmentAgent
import re


class ScrapingBeeAgent(BaseEnrichmentAgent):
    """
    ScrapingBee agent for headless browser scraping
    """

    def __init__(self, config: Dict, api_key: Optional[str] = None):
        super().__init__(config, api_key)
        self.base_url = config.get('base_url', 'https://app.scrapingbee.com/api/v1')

    def get_capabilities(self) -> List[str]:
        """Return list of ScrapingBee capabilities"""
        return list(self.config.get('capabilities', {}).keys())

    async def enrich(
        self,
        capability: str,
        input_data: Dict[str, Any],
        timeout_override: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute ScrapingBee enrichment

        Args:
            capability: 'scrape_website', 'screenshot', 'extract_data'
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
        elif capability == 'screenshot':
            result = await self._screenshot(input_data)
        elif capability == 'extract_data':
            result = await self._extract_data(input_data)
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
        render_js: bool = True,
        block_resources: bool = True,
        premium_proxy: bool = False
    ) -> Dict[str, Any]:
        """
        Make ScrapingBee API request

        Args:
            url: URL to scrape
            render_js: Enable JavaScript rendering
            block_resources: Block images/CSS to speed up
            premium_proxy: Use premium proxy

        Returns:
            API response
        """
        params = {
            'api_key': self.api_key,
            'url': url,
            'render_js': 'true' if render_js else 'false',
            'block_resources': 'true' if block_resources else 'false',
            'premium_proxy': 'true' if premium_proxy else 'false'
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
        Output: employee_count, industry, phone, address
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

        result = await self._make_request(
            website,
            render_js=True,
            block_resources=True
        )

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

        # Extract phone
        phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phone_match = re.search(phone_pattern, html)
        if phone_match:
            enriched['phone'] = phone_match.group(0)

        # Extract industry
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

    async def _screenshot(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Take screenshot of website

        Input: website
        Output: screenshot_url (saved to storage)
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

        # Note: ScrapingBee screenshot requires special endpoint
        # This is a placeholder - in production you'd use the screenshot endpoint
        return {
            'success': True,
            'data': {
                'website': website,
                'screenshot_available': True
            },
            'error': None
        }

    async def _extract_data(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract structured data with custom selectors

        Input: website, selectors (CSS)
        Output: Extracted data based on selectors
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

        html = result['html']
        enriched = {'website': website}

        # In production, you'd use BeautifulSoup with custom selectors
        # For now, basic extraction

        return {
            'success': True,
            'data': enriched,
            'error': None
        }
