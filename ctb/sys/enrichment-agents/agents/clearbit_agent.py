"""
Clearbit Agent - Company and Person Enrichment API
Barton Doctrine ID: 04.04.02.04.50000.008
Tier: 2 (Mid-Cost Precision)

Capabilities:
- enrich_company: Get structured company metadata by domain
- enrich_person: Get person data by email
- company_logo: Get company logo URL
"""

import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from .base_agent import BaseEnrichmentAgent


class ClearbitAgent(BaseEnrichmentAgent):
    """
    Clearbit agent for structured company/person enrichment
    """

    def __init__(self, config: Dict, api_key: Optional[str] = None):
        super().__init__(config, api_key)
        self.base_url = config.get('base_url', 'https://company.clearbit.com/v2')
        self.person_url = 'https://person.clearbit.com/v2'

    def get_capabilities(self) -> List[str]:
        """Return list of Clearbit capabilities"""
        return list(self.config.get('capabilities', {}).keys())

    async def enrich(
        self,
        capability: str,
        input_data: Dict[str, Any],
        timeout_override: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute Clearbit enrichment

        Args:
            capability: 'enrich_company', 'enrich_person', 'company_logo'
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
        elif capability == 'enrich_person':
            result = await self._enrich_person(input_data)
        elif capability == 'company_logo':
            result = await self._get_company_logo(input_data)
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
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make Clearbit API request

        Args:
            url: API endpoint URL
            params: Query parameters

        Returns:
            API response
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'success': True,
                            'data': data,
                            'error': None
                        }
                    elif response.status == 202:
                        # Clearbit is still processing - retry after delay
                        await asyncio.sleep(2)
                        return await self._make_request(url, params)
                    elif response.status == 404:
                        return {
                            'success': False,
                            'data': {},
                            'error': 'Company/person not found in Clearbit'
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

    async def _enrich_company(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enrich company by domain

        Input: domain or website
        Output: Structured company metadata
        """
        domain = input_data.get('domain') or input_data.get('website', '')

        if not domain:
            return {
                'success': False,
                'data': {},
                'error': 'domain or website required'
            }

        # Clean domain
        domain = domain.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]

        result = await self._make_request(
            f'{self.base_url}/companies/domain/{domain}',
            {}
        )

        if not result['success']:
            return result

        data = result['data']
        enriched = {
            'company_name': data.get('name'),
            'domain': data.get('domain'),
            'website': f"https://{data.get('domain')}",
            'industry': data.get('category', {}).get('industry'),
            'employee_count': data.get('metrics', {}).get('employees'),
            'founded': data.get('foundedYear'),
            'linkedin_url': data.get('linkedin', {}).get('handle'),
            'twitter': data.get('twitter', {}).get('handle'),
            'facebook': data.get('facebook', {}).get('handle'),
            'phone': data.get('phone'),
            'description': data.get('description'),
            'logo_url': data.get('logo'),
            'tags': data.get('tags', []),
            'tech_stack': data.get('tech', [])
        }

        # Parse location
        location = data.get('location', '')
        if location:
            enriched['address'] = location

        # Clean up None values
        enriched = {k: v for k, v in enriched.items() if v is not None}

        return {
            'success': True,
            'data': enriched,
            'error': None
        }

    async def _enrich_person(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enrich person by email

        Input: email
        Output: Person data (name, title, company, social profiles)
        """
        email = input_data.get('email', '')

        if not email:
            return {
                'success': False,
                'data': {},
                'error': 'email required'
            }

        result = await self._make_request(
            f'{self.person_url}/people/find',
            {'email': email}
        )

        if not result['success']:
            return result

        data = result['data']
        enriched = {
            'full_name': data.get('name', {}).get('fullName'),
            'email': data.get('email'),
            'title': data.get('employment', {}).get('title'),
            'company_name': data.get('employment', {}).get('name'),
            'linkedin_url': data.get('linkedin', {}).get('handle'),
            'twitter': data.get('twitter', {}).get('handle'),
            'github': data.get('github', {}).get('handle'),
            'location': data.get('location'),
            'bio': data.get('bio')
        }

        # Clean up None values
        enriched = {k: v for k, v in enriched.items() if v is not None}

        return {
            'success': True,
            'data': enriched,
            'error': None
        }

    async def _get_company_logo(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get company logo URL

        Input: domain
        Output: logo_url
        """
        domain = input_data.get('domain') or input_data.get('website', '')

        if not domain:
            return {
                'success': False,
                'data': {},
                'error': 'domain required'
            }

        # Clean domain
        domain = domain.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]

        logo_url = f'https://logo.clearbit.com/{domain}'

        return {
            'success': True,
            'data': {
                'logo_url': logo_url,
                'domain': domain
            },
            'error': None
        }
