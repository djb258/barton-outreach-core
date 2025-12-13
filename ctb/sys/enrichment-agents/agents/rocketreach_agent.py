"""
RocketReach Agent - People-Level Contact Finder
Barton Doctrine ID: 04.04.02.04.50000.010
Tier: 3 (High-Accuracy, High-Cost - Last Resort)

Capabilities:
- find_executive: Find executive by company + title
- lookup_person: Lookup person by name + company
- verify_email: Verify email deliverability
"""

import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from .base_agent import BaseEnrichmentAgent


class RocketReachAgent(BaseEnrichmentAgent):
    """
    RocketReach agent for people-level contact discovery
    """

    def __init__(self, config: Dict, api_key: Optional[str] = None):
        super().__init__(config, api_key)
        self.base_url = config.get('base_url', 'https://api.rocketreach.co/v2')

    def get_capabilities(self) -> List[str]:
        """Return list of RocketReach capabilities"""
        return list(self.config.get('capabilities', {}).keys())

    async def enrich(
        self,
        capability: str,
        input_data: Dict[str, Any],
        timeout_override: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute RocketReach enrichment

        Args:
            capability: 'find_executive', 'lookup_person', 'verify_email'
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
        if capability == 'find_executive':
            result = await self._find_executive(input_data)
        elif capability == 'lookup_person':
            result = await self._lookup_person(input_data)
        elif capability == 'verify_email':
            result = await self._verify_email(input_data)
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
        Make RocketReach API request

        Args:
            endpoint: API endpoint
            method: HTTP method
            data: Request payload

        Returns:
            API response
        """
        url = f'{self.base_url}/{endpoint}'
        headers = {
            'Api-Key': self.api_key,
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
        elif response.status == 404:
            return {
                'success': False,
                'data': {},
                'error': 'Person not found'
            }
        else:
            error_text = await response.text()
            return {
                'success': False,
                'data': {},
                'error': f"HTTP {response.status}: {error_text}"
            }

    async def _find_executive(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Find executive by company and title

        Input: company_name, title (CEO/CFO/HR)
        Output: Executive contact details with verified email
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
            'query': {
                'current_employer': [company_name],
                'current_title': [title]
            },
            'page_size': 1,
            'start': 1
        }

        result = await self._make_request('api/search', 'POST', payload)

        if not result['success']:
            return result

        data = result['data']
        profiles = data.get('profiles', [])

        if not profiles:
            return {
                'success': False,
                'data': {},
                'error': f'No {title} found at {company_name}'
            }

        profile = profiles[0]
        enriched = {
            'full_name': profile.get('name'),
            'email': profile.get('emails', [{}])[0].get('email') if profile.get('emails') else None,
            'title': profile.get('current_title'),
            'company_name': profile.get('current_employer'),
            'linkedin_url': profile.get('linkedin_url'),
            'phone': profile.get('phones', [{}])[0].get('number') if profile.get('phones') else None,
            'location': profile.get('location')
        }

        # Clean up None values
        enriched = {k: v for k, v in enriched.items() if v is not None}

        return {
            'success': True,
            'data': enriched,
            'error': None
        }

    async def _lookup_person(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Lookup person by name and company

        Input: full_name, company_name
        Output: Person contact details
        """
        full_name = input_data.get('full_name')
        company_name = input_data.get('company_name')

        if not full_name:
            return {
                'success': False,
                'data': {},
                'error': 'full_name required'
            }

        payload = {
            'name': full_name
        }

        if company_name:
            payload['current_employer'] = company_name

        result = await self._make_request('api/lookupProfile', 'POST', payload)

        if not result['success']:
            return result

        data = result['data']
        enriched = {
            'full_name': data.get('name'),
            'email': data.get('emails', [{}])[0].get('email') if data.get('emails') else None,
            'title': data.get('current_title'),
            'company_name': data.get('current_employer'),
            'linkedin_url': data.get('linkedin_url'),
            'phone': data.get('phones', [{}])[0].get('number') if data.get('phones') else None
        }

        # Clean up None values
        enriched = {k: v for k, v in enriched.items() if v is not None}

        return {
            'success': True,
            'data': enriched,
            'error': None
        }

    async def _verify_email(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verify email deliverability

        Input: email
        Output: verification status and details
        """
        email = input_data.get('email')

        if not email:
            return {
                'success': False,
                'data': {},
                'error': 'email required'
            }

        payload = {
            'email': email
        }

        result = await self._make_request('api/verifyEmail', 'POST', payload)

        if not result['success']:
            return result

        data = result['data']
        enriched = {
            'email': email,
            'is_valid': data.get('status') == 'valid',
            'deliverable': data.get('deliverable'),
            'status': data.get('status')
        }

        return {
            'success': True,
            'data': enriched,
            'error': None
        }
