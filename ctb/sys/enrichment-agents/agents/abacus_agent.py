"""
Abacus Agent - Data Validation and Enrichment
Barton Doctrine ID: 04.04.02.04.50000.002

Capabilities:
- email_validation: Validate and verify email addresses
- company_enrichment: Enrich company data
- person_enrichment: Enrich person data
"""

import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from .base_agent import BaseEnrichmentAgent


class AbacusAgent(BaseEnrichmentAgent):
    """
    Abacus agent for data validation and enrichment
    """

    def __init__(self, config: Dict, api_key: Optional[str] = None):
        super().__init__(config, api_key)
        self.base_url = config.get('base_url', 'https://api.abacus.ai')

    def get_capabilities(self) -> List[str]:
        """Return list of Abacus capabilities"""
        return list(self.config.get('capabilities', {}).keys())

    async def enrich(
        self,
        capability: str,
        input_data: Dict[str, Any],
        timeout_override: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute Abacus enrichment

        Args:
            capability: 'email_validation', 'company_enrichment', 'person_enrichment'
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
        if capability == 'email_validation':
            result = await self._email_validation(endpoint, input_data)
        elif capability == 'company_enrichment':
            result = await self._company_enrichment(endpoint, input_data)
        elif capability == 'person_enrichment':
            result = await self._person_enrichment(endpoint, input_data)
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
        Make API request to Abacus

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

    async def _email_validation(
        self,
        endpoint: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate email address

        Input: email
        Output: email (validated), is_valid, deliverability
        """
        email = input_data.get('email', '')

        if not email:
            return {
                'success': False,
                'data': {},
                'error': 'email required'
            }

        result = await self._api_request(endpoint, {'email': email})

        if not result['success']:
            return result

        data = result['data']
        enriched = {}

        # Abacus returns validation results
        if data.get('is_valid'):
            enriched['email'] = email
        if 'deliverability' in data:
            enriched['email_deliverability'] = data['deliverability']
        if 'score' in data:
            enriched['email_score'] = data['score']

        return {
            'success': True,
            'data': enriched,
            'error': None
        }

    async def _company_enrichment(
        self,
        endpoint: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enrich company data

        Input: company_name, domain (optional)
        Output: employee_count, industry, website, domain
        """
        company_name = input_data.get('company_name', '')
        domain = input_data.get('domain', '')

        if not company_name and not domain:
            return {
                'success': False,
                'data': {},
                'error': 'company_name or domain required'
            }

        payload = {}
        if company_name:
            payload['company_name'] = company_name
        if domain:
            payload['domain'] = domain

        result = await self._api_request(endpoint, payload)

        if not result['success']:
            return result

        data = result['data']
        enriched = {}

        # Extract fields
        if 'employee_count' in data:
            enriched['employee_count'] = data['employee_count']
        if 'employees' in data:
            enriched['employee_count'] = data['employees']
        if 'industry' in data:
            enriched['industry'] = data['industry']
        if 'website' in data:
            enriched['website'] = data['website']
        if 'domain' in data:
            enriched['domain'] = data['domain']
        if 'linkedin' in data:
            enriched['linkedin_url'] = data['linkedin']

        return {
            'success': True,
            'data': enriched,
            'error': None
        }

    async def _person_enrichment(
        self,
        endpoint: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enrich person data

        Input: full_name, company_name, email (optional)
        Output: email, title, linkedin_url
        """
        full_name = input_data.get('full_name', '')
        company_name = input_data.get('company_name', '')
        email = input_data.get('email', '')

        if not full_name:
            return {
                'success': False,
                'data': {},
                'error': 'full_name required'
            }

        payload = {
            'full_name': full_name
        }
        if company_name:
            payload['company_name'] = company_name
        if email:
            payload['email'] = email

        result = await self._api_request(endpoint, payload)

        if not result['success']:
            return result

        data = result['data']
        enriched = {}

        # Extract fields
        if 'email' in data:
            enriched['email'] = data['email']
        if 'title' in data:
            enriched['title'] = data['title']
        if 'linkedin' in data:
            enriched['linkedin_url'] = data['linkedin']
        if 'linkedin_url' in data:
            enriched['linkedin_url'] = data['linkedin_url']

        return {
            'success': True,
            'data': enriched,
            'error': None
        }
