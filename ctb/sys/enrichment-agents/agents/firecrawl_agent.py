"""
Firecrawl Agent - Website Scraping and Search
Barton Doctrine ID: 04.04.02.04.50000.003

Capabilities:
- scrape_company_website: Extract structured data from company website
- search_company: Search for company website and LinkedIn
"""

import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from .base_agent import BaseEnrichmentAgent


class FirecrawlAgent(BaseEnrichmentAgent):
    """
    Firecrawl agent for website scraping
    """

    def __init__(self, config: Dict, api_key: Optional[str] = None):
        super().__init__(config, api_key)
        self.base_url = config.get('base_url', 'https://api.firecrawl.dev')

    def get_capabilities(self) -> List[str]:
        """Return list of Firecrawl capabilities"""
        return list(self.config.get('capabilities', {}).keys())

    async def enrich(
        self,
        capability: str,
        input_data: Dict[str, Any],
        timeout_override: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute Firecrawl enrichment

        Args:
            capability: 'scrape_company_website', 'search_company'
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

        cap_config = capabilities[capability]
        endpoint = cap_config.get('endpoint')

        # Route to appropriate handler
        if capability == 'scrape_company_website':
            result = await self._scrape_company_website(endpoint, input_data)
        elif capability == 'search_company':
            result = await self._search_company(endpoint, input_data)
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

    async def _api_request(
        self,
        endpoint: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make API request to Firecrawl

        Args:
            endpoint: API endpoint
            data: Request payload

        Returns:
            API response
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'data': result,
                            'error': None
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'data': {},
                            'error': f"HTTP {response.status}: {error_text}"
                        }
            except Exception as e:
                return {
                    'success': False,
                    'data': {},
                    'error': str(e)
                }

    async def _scrape_company_website(
        self,
        endpoint: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Scrape company website for structured data

        Input: website
        Output: employee_count, industry, address, phone (extracted from page)
        """
        website = input_data.get('website', '')

        if not website:
            return {
                'success': False,
                'data': {},
                'error': 'website required'
            }

        # Ensure website has protocol
        if not website.startswith('http'):
            website = f'https://{website}'

        payload = {
            'url': website,
            'formats': ['markdown', 'html'],
            'onlyMainContent': True
        }

        result = await self._api_request(endpoint, payload)

        if not result['success']:
            return result

        data = result['data']
        enriched = {}

        # Extract structured data from scraped content
        content = data.get('markdown', '') or data.get('html', '')
        metadata = data.get('metadata', {})

        # Try to extract fields from metadata first
        if 'description' in metadata:
            desc = metadata['description'].lower()
            if 'industry' not in enriched:
                # Simple industry detection
                industries = ['technology', 'finance', 'healthcare', 'education', 'retail', 'manufacturing']
                for ind in industries:
                    if ind in desc:
                        enriched['industry'] = ind.capitalize()
                        break

        # Extract from content
        if content:
            content_lower = content.lower()

            # Look for employee count patterns
            import re
            employee_patterns = [
                r'(\d+[,\d]*)\s*(?:employees|team members)',
                r'team of (\d+[,\d]*)',
                r'staff of (\d+[,\d]*)'
            ]
            for pattern in employee_patterns:
                match = re.search(pattern, content_lower)
                if match:
                    try:
                        count_str = match.group(1).replace(',', '')
                        enriched['employee_count'] = int(count_str)
                        break
                    except:
                        pass

            # Look for phone numbers
            phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
            phone_match = re.search(phone_pattern, content)
            if phone_match:
                enriched['phone'] = phone_match.group(0)

            # Look for address (simplified)
            address_pattern = r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)[,\s]+[A-Za-z\s]+[,\s]+[A-Z]{2}\s+\d{5}'
            address_match = re.search(address_pattern, content)
            if address_match:
                enriched['address'] = address_match.group(0)

        # Add the website itself
        enriched['website'] = website

        return {
            'success': True,
            'data': enriched,
            'error': None
        }

    async def _search_company(
        self,
        endpoint: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Search for company website and LinkedIn URL

        Input: company_name
        Output: website, linkedin_url
        """
        company_name = input_data.get('company_name', '')

        if not company_name:
            return {
                'success': False,
                'data': {},
                'error': 'company_name required'
            }

        payload = {
            'query': f'{company_name} official website',
            'limit': 5
        }

        result = await self._api_request(endpoint, payload)

        if not result['success']:
            return result

        data = result['data']
        enriched = {}

        # Parse search results
        results = data.get('results', [])

        for res in results:
            url = res.get('url', '')
            title = res.get('title', '').lower()

            # Look for official website
            if not enriched.get('website'):
                if 'linkedin.com' not in url:
                    # Likely the company website
                    enriched['website'] = url

            # Look for LinkedIn
            if not enriched.get('linkedin_url'):
                if 'linkedin.com/company/' in url:
                    enriched['linkedin_url'] = url

            # Stop if we have both
            if enriched.get('website') and enriched.get('linkedin_url'):
                break

        return {
            'success': True,
            'data': enriched,
            'error': None
        }
