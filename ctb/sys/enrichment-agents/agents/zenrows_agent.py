"""
ZenRows Agent - Advanced Web Scraping with AI
Barton Doctrine ID: 04.04.02.04.50000.005

Capabilities:
- scrape_website: Scrape with AI-powered content extraction
- bypass_cloudflare: Bypass Cloudflare and anti-bot protection
- extract_data: AI-powered data extraction
"""

import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from .base_agent import BaseEnrichmentAgent
import re


class ZenRowsAgent(BaseEnrichmentAgent):
    """
    ZenRows agent for advanced web scraping with AI
    """

    def __init__(self, config: Dict, api_key: Optional[str] = None):
        super().__init__(config, api_key)
        self.base_url = config.get('base_url', 'https://api.zenrows.com/v1')

    def get_capabilities(self) -> List[str]:
        """Return list of ZenRows capabilities"""
        return list(self.config.get('capabilities', {}).keys())

    async def enrich(
        self,
        capability: str,
        input_data: Dict[str, Any],
        timeout_override: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute ZenRows enrichment

        Args:
            capability: 'scrape_website', 'bypass_cloudflare', 'extract_data'
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
        elif capability == 'bypass_cloudflare':
            result = await self._bypass_cloudflare(input_data)
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
        js_render: bool = False,
        premium_proxy: bool = False,
        ai_extract: bool = False
    ) -> Dict[str, Any]:
        """
        Make ZenRows API request

        Args:
            url: URL to scrape
            js_render: Enable JavaScript rendering
            premium_proxy: Use premium proxy
            ai_extract: Use AI-powered extraction

        Returns:
            API response
        """
        params = {
            'apikey': self.api_key,
            'url': url,
            'js_render': 'true' if js_render else 'false',
            'premium_proxy': 'true' if premium_proxy else 'false',
            'autoparse': 'true' if ai_extract else 'false'
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        if ai_extract:
                            data = await response.json()
                            return {
                                'success': True,
                                'data': data,
                                'html': '',
                                'error': None
                            }
                        else:
                            html = await response.text()
                            return {
                                'success': True,
                                'html': html,
                                'data': {},
                                'error': None
                            }
                    else:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'html': '',
                            'data': {},
                            'error': f"HTTP {response.status}: {error_text}"
                        }
            except Exception as e:
                return {
                    'success': False,
                    'html': '',
                    'data': {},
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

        result = await self._make_request(website, js_render=True, premium_proxy=False)

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

        enriched['website'] = website

        return {
            'success': True,
            'data': enriched,
            'error': None
        }

    async def _bypass_cloudflare(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Scrape website protected by Cloudflare

        Input: website
        Output: Scraped content bypassing Cloudflare
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

        # Use premium proxy and JS rendering to bypass Cloudflare
        result = await self._make_request(
            website,
            js_render=True,
            premium_proxy=True
        )

        if not result['success']:
            return {
                'success': False,
                'data': {},
                'error': result['error']
            }

        html = result['html']
        enriched = {'website': website}

        # Check if we successfully bypassed
        if 'cloudflare' not in html.lower():
            enriched['bypass_success'] = True
        else:
            enriched['bypass_success'] = False

        return {
            'success': True,
            'data': enriched,
            'error': None
        }

    async def _extract_data(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        AI-powered data extraction

        Input: website
        Output: Structured data extracted by AI
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

        # Use AI extraction
        result = await self._make_request(
            website,
            js_render=True,
            ai_extract=True
        )

        if not result['success']:
            return {
                'success': False,
                'data': {},
                'error': result['error']
            }

        # ZenRows AI extraction returns structured data
        data = result['data']
        enriched = {}

        # Map ZenRows fields to our schema
        if 'company' in data:
            company_data = data['company']
            if 'employees' in company_data:
                enriched['employee_count'] = company_data['employees']
            if 'industry' in company_data:
                enriched['industry'] = company_data['industry']
            if 'phone' in company_data:
                enriched['phone'] = company_data['phone']
            if 'address' in company_data:
                enriched['address'] = company_data['address']

        enriched['website'] = website

        return {
            'success': True,
            'data': enriched,
            'error': None
        }
