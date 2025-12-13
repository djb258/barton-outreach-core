"""
PeopleDataLabs Agent - Deep Person/Company Matching
Barton Doctrine ID: 04.04.02.04.50000.011
Tier: 3 (High-Accuracy, High-Cost - Last Resort)

Capabilities:
- enrich_company: Deep company data matching
- enrich_person: Deep person data matching
- find_contacts: Find contacts by fuzzy matching
"""

import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from .base_agent import BaseEnrichmentAgent


class PeopleDataLabsAgent(BaseEnrichmentAgent):
    """
    PeopleDataLabs agent for deep matching and enrichment
    """

    def __init__(self, config: Dict, api_key: Optional[str] = None):
        super().__init__(config, api_key)
        self.base_url = config.get('base_url', 'https://api.peopledatalabs.com/v5')

    def get_capabilities(self) -> List[str]:
        """Return list of PeopleDataLabs capabilities"""
        return list(self.config.get('capabilities', {}).keys())

    async def enrich(
        self,
        capability: str,
        input_data: Dict[str, Any],
        timeout_override: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute PeopleDataLabs enrichment

        Args:
            capability: 'enrich_company', 'enrich_person', 'find_contacts'
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
        elif capability == 'find_contacts':
            result = await self._find_contacts(input_data)
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
        method: str = 'GET',
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make PeopleDataLabs API request

        Args:
            endpoint: API endpoint
            method: HTTP method
            params: Query parameters
            data: Request body

        Returns:
            API response
        """
        url = f'{self.base_url}/{endpoint}'
        headers = {
            'X-Api-Key': self.api_key,
            'Content-Type': 'application/json'
        }

        async with aiohttp.ClientSession() as session:
            try:
                if method == 'GET':
                    async with session.get(url, params=params, headers=headers) as response:
                        return await self._handle_response(response)
                elif method == 'POST':
                    async with session.post(url, json=data, headers=headers) as response:
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

            # Check if match was found
            if data.get('status') == 200 and data.get('data'):
                return {
                    'success': True,
                    'data': data.get('data'),
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'data': {},
                    'error': 'No match found'
                }
        elif response.status == 404:
            return {
                'success': False,
                'data': {},
                'error': 'Not found'
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
        Deep company enrichment with fuzzy matching

        Input: company_name or website
        Output: Deep company metadata
        """
        company_name = input_data.get('company_name')
        website = input_data.get('website')

        if not company_name and not website:
            return {
                'success': False,
                'data': {},
                'error': 'company_name or website required'
            }

        params = {}
        if company_name:
            params['name'] = company_name
        if website:
            params['website'] = website

        # Use fuzzy matching
        params['pretty'] = 'true'
        params['min_likelihood'] = 6  # High confidence matches only

        result = await self._make_request('company/enrich', 'GET', params=params)

        if not result['success']:
            return result

        data = result['data']
        enriched = {
            'company_name': data.get('name'),
            'website': data.get('website'),
            'domain': data.get('domain'),
            'industry': data.get('industry'),
            'employee_count': data.get('employee_count'),
            'founded': data.get('founded'),
            'linkedin_url': data.get('linkedin_url'),
            'facebook_url': data.get('facebook_url'),
            'twitter_url': data.get('twitter_url'),
            'location': data.get('location', {}).get('name'),
            'city': data.get('location', {}).get('locality'),
            'state': data.get('location', {}).get('region'),
            'country': data.get('location', {}).get('country'),
            'tags': data.get('tags', []),
            'type': data.get('type'),
            'size': data.get('size')
        }

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
        Deep person enrichment with fuzzy matching

        Input: full_name, company_name, email, or linkedin_url
        Output: Deep person metadata
        """
        params = {}

        # Add all available identifiers for best matching
        if input_data.get('full_name'):
            params['name'] = input_data['full_name']
        if input_data.get('company_name'):
            params['company'] = input_data['company_name']
        if input_data.get('email'):
            params['email'] = input_data['email']
        if input_data.get('linkedin_url'):
            params['profile'] = input_data['linkedin_url']

        if not params:
            return {
                'success': False,
                'data': {},
                'error': 'At least one identifier required (name, email, linkedin_url)'
            }

        params['pretty'] = 'true'
        params['min_likelihood'] = 7  # Very high confidence for people

        result = await self._make_request('person/enrich', 'GET', params=params)

        if not result['success']:
            return result

        data = result['data']
        enriched = {
            'full_name': data.get('full_name'),
            'email': data.get('emails', [{}])[0].get('address') if data.get('emails') else None,
            'title': data.get('job_title'),
            'company_name': data.get('job_company_name'),
            'linkedin_url': data.get('linkedin_url'),
            'github_url': data.get('github_url'),
            'facebook_url': data.get('facebook_url'),
            'twitter_url': data.get('twitter_url'),
            'phone': data.get('phone_numbers', [{}])[0] if data.get('phone_numbers') else None,
            'location': data.get('location_name'),
            'industry': data.get('industry'),
            'skills': data.get('skills', []),
            'experience': data.get('experience', [])
        }

        # Clean up None values
        enriched = {k: v for k, v in enriched.items() if v is not None}

        return {
            'success': True,
            'data': enriched,
            'error': None
        }

    async def _find_contacts(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Find contacts using search with fuzzy matching

        Input: company_name, title, location (any combination)
        Output: List of matching contacts
        """
        query_filters = []

        if input_data.get('company_name'):
            query_filters.append(f"job_company_name:\"{input_data['company_name']}\"")

        if input_data.get('title'):
            query_filters.append(f"job_title:\"{input_data['title']}\"")

        if input_data.get('location'):
            query_filters.append(f"location_name:\"{input_data['location']}\"")

        if not query_filters:
            return {
                'success': False,
                'data': {},
                'error': 'At least one search criterion required'
            }

        payload = {
            'query': ' AND '.join(query_filters),
            'size': 10,  # Return up to 10 matches
            'pretty': True
        }

        result = await self._make_request('person/search', 'POST', data=payload)

        if not result['success']:
            return result

        data = result['data']
        contacts = []

        for person in data:
            contact = {
                'full_name': person.get('full_name'),
                'email': person.get('emails', [{}])[0].get('address') if person.get('emails') else None,
                'title': person.get('job_title'),
                'company_name': person.get('job_company_name'),
                'linkedin_url': person.get('linkedin_url')
            }
            # Clean up None values
            contact = {k: v for k, v in contact.items() if v is not None}
            contacts.append(contact)

        return {
            'success': True,
            'data': {'contacts': contacts, 'total_found': len(contacts)},
            'error': None
        }
