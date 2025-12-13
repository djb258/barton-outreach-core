"""
Clay Agent - Unified Data Enrichment Platform
Barton Doctrine ID: 04.04.02.04.50000.009
Tier: 2 (Mid-Cost Precision)

Capabilities:
- enrich_company: Unified company enrichment
- find_person: Find person by company + title
- waterfall_enrichment: Multi-provider waterfall enrichment
"""

import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from .base_agent import BaseEnrichmentAgent


class ClayAgent(BaseEnrichmentAgent):
    """
    Clay agent for unified multi-source enrichment
    """

    def __init__(self, config: Dict, api_key: Optional[str] = None):
        super().__init__(config, api_key)
        self.base_url = config.get('base_url', 'https://api.clay.com/v1')

    def get_capabilities(self) -> List[str]:
        """Return list of Clay capabilities"""
        return list(self.config.get('capabilities', {}).keys())

    async def enrich(
        self,
        capability: str,
        input_data: Dict[str, Any],
        timeout_override: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute Clay enrichment

        Args:
            capability: 'enrich_company', 'find_person', 'waterfall_enrichment'
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
        if capability == 'enrich_company':
            result = await self._enrich_company(input_data)
        elif capability == 'find_person':
            result = await self._find_person(input_data)
        elif capability == 'waterfall_enrichment':
            result = await self._waterfall_enrichment(input_data)
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
        endpoint: str,
        method: str = 'POST',
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make Clay API request

        Args:
            endpoint: API endpoint
            method: HTTP method
            data: Request payload

        Returns:
            API response
        """
        url = f'{self.base_url}/{endpoint}'
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        async with aiohttp.ClientSession() as session:
            try:
                if method == 'POST':
                    async with session.post(url, json=data, headers=headers) as response:
                        return await self._handle_response(response)
                elif method == 'GET':
                    async with session.get(url, params=data, headers=headers) as response:
                        return await self._handle_response(response)
            except Exception as e:
                return {
                    'success': False,
                    'data': {},
                    'error': str(e)
                }

    async def _handle_response(self, response) -> Dict[str, Any]:
        """Handle API response"""
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

    async def _enrich_company(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enrich company via Clay's unified enrichment

        Input: company_name or domain
        Output: Unified company data from multiple sources
        """
        company_name = input_data.get('company_name')
        domain = input_data.get('domain') or input_data.get('website')

        if not company_name and not domain:
            return {
                'success': False,
                'data': {},
                'error': 'company_name or domain required'
            }

        payload = {
            'enrichment_type': 'company',
            'inputs': {
                'company_name': company_name,
                'domain': domain
            }
        }

        result = await self._make_request('enrich', 'POST', payload)

        if not result['success']:
            return result

        data = result['data']
        enriched = {
            'company_name': data.get('name'),
            'domain': data.get('domain'),
            'website': data.get('website'),
            'industry': data.get('industry'),
            'employee_count': data.get('employee_count'),
            'linkedin_url': data.get('linkedin_url'),
            'address': data.get('address'),
            'city': data.get('city'),
            'state': data.get('state'),
            'country': data.get('country'),
            'phone': data.get('phone'),
            'description': data.get('description'),
            'founded': data.get('founded_year'),
            'revenue': data.get('revenue')
        }

        # Clean up None values
        enriched = {k: v for k, v in enriched.items() if v is not None}

        return {
            'success': True,
            'data': enriched,
            'error': None
        }

    async def _find_person(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Find person by company and title

        Input: company_name, title (e.g., "CEO", "CFO")
        Output: Person details
        """
        company_name = input_data.get('company_name')
        title = input_data.get('title')

        if not company_name or not title:
            return {
                'success': False,
                'data': {},
                'error': 'company_name and title required'
            }

        payload = {
            'search_type': 'person',
            'filters': {
                'company': company_name,
                'title': title
            }
        }

        result = await self._make_request('search', 'POST', payload)

        if not result['success']:
            return result

        data = result['data']
        results = data.get('results', [])

        if not results:
            return {
                'success': False,
                'data': {},
                'error': f'No {title} found at {company_name}'
            }

        # Return first match
        person = results[0]
        enriched = {
            'full_name': person.get('name'),
            'email': person.get('email'),
            'title': person.get('title'),
            'linkedin_url': person.get('linkedin_url'),
            'company_name': company_name
        }

        # Clean up None values
        enriched = {k: v for k, v in enriched.items() if v is not None}

        return {
            'success': True,
            'data': enriched,
            'error': None
        }

    async def _waterfall_enrichment(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Waterfall enrichment - tries multiple providers in sequence

        Input: company_name or domain, fields_needed
        Output: Enriched data from first successful provider
        """
        company_name = input_data.get('company_name')
        domain = input_data.get('domain')
        fields_needed = input_data.get('fields_needed', [])

        if not company_name and not domain:
            return {
                'success': False,
                'data': {},
                'error': 'company_name or domain required'
            }

        payload = {
            'enrichment_type': 'waterfall',
            'inputs': {
                'company_name': company_name,
                'domain': domain
            },
            'providers': ['clearbit', 'apollo', 'peopledatalabs'],  # Clay tries in order
            'required_fields': fields_needed
        }

        result = await self._make_request('enrich/waterfall', 'POST', payload)

        if not result['success']:
            return result

        data = result['data']

        # Clay returns unified data + metadata about which provider succeeded
        enriched = data.get('enriched_data', {})
        metadata = {
            'provider_used': data.get('provider'),
            'providers_tried': data.get('providers_tried', [])
        }

        return {
            'success': True,
            'data': enriched,
            'metadata': metadata,
            'error': None
        }
