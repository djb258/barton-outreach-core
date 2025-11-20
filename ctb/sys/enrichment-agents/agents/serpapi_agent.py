"""
SerpAPI Agent - Google Search Results API
Barton Doctrine ID: 04.04.02.04.50000.007
Tier: 1 (Cheap Hammer)

Capabilities:
- search_company: Confirm company identity, domain, address via Google
- extract_knowledge_panel: Extract structured data from Google Knowledge Graph
"""

import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from .base_agent import BaseEnrichmentAgent
import re


class SerpAPIAgent(BaseEnrichmentAgent):
    """
    SerpAPI agent for Google search-based enrichment
    """

    def __init__(self, config: Dict, api_key: Optional[str] = None):
        super().__init__(config, api_key)
        self.base_url = config.get('base_url', 'https://serpapi.com/search')

    def get_capabilities(self) -> List[str]:
        """Return list of SerpAPI capabilities"""
        return list(self.config.get('capabilities', {}).keys())

    async def enrich(
        self,
        capability: str,
        input_data: Dict[str, Any],
        timeout_override: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute SerpAPI enrichment

        Args:
            capability: 'search_company', 'extract_knowledge_panel'
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
        if capability == 'search_company':
            result = await self._search_company(input_data)
        elif capability == 'extract_knowledge_panel':
            result = await self._extract_knowledge_panel(input_data)
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
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make SerpAPI request

        Args:
            query: Search query
            params: Additional parameters

        Returns:
            API response
        """
        request_params = {
            'api_key': self.api_key,
            'q': query,
            'engine': 'google',
            'num': 10
        }

        if params:
            request_params.update(params)

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.base_url, params=request_params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'success': True,
                            'data': data,
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

    async def _search_company(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Search for company to confirm identity, domain, address

        Input: company_name
        Output: website, domain, address, city, state, phone
        """
        company_name = input_data.get('company_name', '')

        if not company_name:
            return {
                'success': False,
                'data': {},
                'error': 'company_name required'
            }

        result = await self._make_request(company_name)

        if not result['success']:
            return result

        data = result['data']
        enriched = {}

        # Check for knowledge graph (right panel)
        knowledge_graph = data.get('knowledge_graph', {})
        if knowledge_graph:
            enriched['website'] = knowledge_graph.get('website')
            enriched['industry'] = knowledge_graph.get('type')

            # Extract address from knowledge graph
            address_parts = knowledge_graph.get('address')
            if address_parts:
                enriched['address'] = address_parts

        # Check organic results for additional data
        organic_results = data.get('organic_results', [])
        for result in organic_results[:3]:
            link = result.get('link', '')

            # Try to identify main company website
            if not enriched.get('website'):
                # Skip known aggregators
                if not any(x in link for x in ['linkedin.com', 'facebook.com', 'wikipedia.org', 'yelp.com']):
                    enriched['website'] = link

                    # Extract domain
                    domain_match = re.search(r'https?://(?:www\.)?([^/]+)', link)
                    if domain_match:
                        enriched['domain'] = domain_match.group(1)

            # Look for phone in snippet
            snippet = result.get('snippet', '')
            phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
            phone_match = re.search(phone_pattern, snippet)
            if phone_match and not enriched.get('phone'):
                enriched['phone'] = phone_match.group(0)

        return {
            'success': True,
            'data': enriched,
            'error': None
        }

    async def _extract_knowledge_panel(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract structured data from Google Knowledge Graph

        Input: company_name
        Output: Full structured company data from knowledge panel
        """
        company_name = input_data.get('company_name', '')

        if not company_name:
            return {
                'success': False,
                'data': {},
                'error': 'company_name required'
            }

        result = await self._make_request(company_name)

        if not result['success']:
            return result

        data = result['data']
        knowledge_graph = data.get('knowledge_graph', {})

        if not knowledge_graph:
            return {
                'success': False,
                'data': {},
                'error': 'No knowledge graph found'
            }

        enriched = {
            'company_name': knowledge_graph.get('title'),
            'website': knowledge_graph.get('website'),
            'industry': knowledge_graph.get('type'),
            'address': knowledge_graph.get('address'),
            'phone': knowledge_graph.get('customer_service'),
            'founded': knowledge_graph.get('founded'),
            'headquarters': knowledge_graph.get('headquarters')
        }

        # Clean up None values
        enriched = {k: v for k, v in enriched.items() if v is not None}

        return {
            'success': True,
            'data': enriched,
            'error': None
        }
