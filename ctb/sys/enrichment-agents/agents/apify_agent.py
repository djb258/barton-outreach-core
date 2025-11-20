"""
Apify Agent - LinkedIn and Google Maps Scraping
Barton Doctrine ID: 04.04.02.04.50000.001

Capabilities:
- linkedin_company_scraper: Scrape LinkedIn company pages
- linkedin_profile_scraper: Scrape LinkedIn personal profiles
- google_maps_scraper: Scrape Google Maps for business info
"""

import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from .base_agent import BaseEnrichmentAgent


class ApifyAgent(BaseEnrichmentAgent):
    """
    Apify agent for web scraping via actors
    """

    def __init__(self, config: Dict, api_key: Optional[str] = None):
        super().__init__(config, api_key)
        self.base_url = config.get('base_url', 'https://api.apify.com/v2')

    def get_capabilities(self) -> List[str]:
        """Return list of Apify capabilities"""
        return list(self.config.get('capabilities', {}).keys())

    async def enrich(
        self,
        capability: str,
        input_data: Dict[str, Any],
        timeout_override: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute Apify actor enrichment

        Args:
            capability: 'linkedin_company_scraper', 'linkedin_profile_scraper', 'google_maps_scraper'
            input_data: Input for the actor
            timeout_override: Override timeout

        Returns:
            Enrichment result with extracted data
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
        actor_id = cap_config.get('actor_id')

        # Route to appropriate handler
        if capability == 'linkedin_company_scraper':
            result = await self._linkedin_company_scraper(actor_id, input_data)
        elif capability == 'linkedin_profile_scraper':
            result = await self._linkedin_profile_scraper(actor_id, input_data)
        elif capability == 'google_maps_scraper':
            result = await self._google_maps_scraper(actor_id, input_data)
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

    async def _run_actor(
        self,
        actor_id: str,
        input_data: Dict[str, Any],
        wait_for_finish: bool = True
    ) -> Dict[str, Any]:
        """
        Run an Apify actor

        Args:
            actor_id: Actor ID (e.g., 'apify/linkedin-company-scraper')
            input_data: Input for the actor
            wait_for_finish: Wait for actor to complete

        Returns:
            Actor run results
        """
        url = f"{self.base_url}/acts/{actor_id}/runs"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        async with aiohttp.ClientSession() as session:
            # Start actor
            async with session.post(url, json=input_data, headers=headers) as response:
                if response.status != 201:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'data': {},
                        'error': f"Failed to start actor: {error_text}"
                    }

                run_data = await response.json()
                run_id = run_data['data']['id']

            if not wait_for_finish:
                return {
                    'success': True,
                    'data': {'run_id': run_id},
                    'error': None
                }

            # Wait for completion (poll every 3 seconds)
            for _ in range(40):  # Max 2 minutes
                await asyncio.sleep(3)

                status_url = f"{self.base_url}/acts/{actor_id}/runs/{run_id}"
                async with session.get(status_url, headers=headers) as response:
                    if response.status != 200:
                        continue

                    status_data = await response.json()
                    status = status_data['data']['status']

                    if status == 'SUCCEEDED':
                        # Get dataset items
                        dataset_id = status_data['data'].get('defaultDatasetId')
                        if dataset_id:
                            items_url = f"{self.base_url}/datasets/{dataset_id}/items"
                            async with session.get(items_url, headers=headers) as items_response:
                                if items_response.status == 200:
                                    items = await items_response.json()
                                    return {
                                        'success': True,
                                        'data': items[0] if items else {},
                                        'error': None
                                    }

                        return {
                            'success': True,
                            'data': {},
                            'error': 'No dataset returned'
                        }

                    elif status in ['FAILED', 'ABORTED', 'TIMED-OUT']:
                        return {
                            'success': False,
                            'data': {},
                            'error': f"Actor run {status}"
                        }

            return {
                'success': False,
                'data': {},
                'error': 'Actor timeout (2 minutes)'
            }

    async def _linkedin_company_scraper(
        self,
        actor_id: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Scrape LinkedIn company page

        Input: company_name or linkedin_url
        Output: linkedin_url, employee_count, industry, website
        """
        company_name = input_data.get('company_name', '')
        linkedin_url = input_data.get('linkedin_url', '')

        # Build Apify input
        apify_input = {
            'startUrls': [
                {'url': linkedin_url} if linkedin_url else
                {'url': f'https://www.linkedin.com/company/{company_name.lower().replace(" ", "-")}'}
            ]
        }

        result = await self._run_actor(actor_id, apify_input)

        if not result['success']:
            return result

        # Extract relevant fields
        data = result['data']
        enriched = {}

        if 'companyUrl' in data:
            enriched['linkedin_url'] = data['companyUrl']
        if 'employeesOnLinkedIn' in data:
            enriched['employee_count'] = data['employeesOnLinkedIn']
        if 'industries' in data and data['industries']:
            enriched['industry'] = data['industries'][0]
        if 'website' in data:
            enriched['website'] = data['website']

        return {
            'success': True,
            'data': enriched,
            'error': None
        }

    async def _linkedin_profile_scraper(
        self,
        actor_id: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Scrape LinkedIn personal profile

        Input: linkedin_url
        Output: full_name, title, linkedin_url
        """
        linkedin_url = input_data.get('linkedin_url', '')

        if not linkedin_url:
            return {
                'success': False,
                'data': {},
                'error': 'linkedin_url required'
            }

        apify_input = {
            'startUrls': [{'url': linkedin_url}]
        }

        result = await self._run_actor(actor_id, apify_input)

        if not result['success']:
            return result

        data = result['data']
        enriched = {}

        if 'fullName' in data:
            enriched['full_name'] = data['fullName']
        if 'title' in data:
            enriched['title'] = data['title']
        if 'profileUrl' in data:
            enriched['linkedin_url'] = data['profileUrl']

        return {
            'success': True,
            'data': enriched,
            'error': None
        }

    async def _google_maps_scraper(
        self,
        actor_id: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Scrape Google Maps for business info

        Input: company_name, city, state
        Output: address, city, state, zip, phone, website
        """
        company_name = input_data.get('company_name', '')
        city = input_data.get('city', '')
        state = input_data.get('state', '')

        search_query = f"{company_name} {city} {state}".strip()

        if not search_query:
            return {
                'success': False,
                'data': {},
                'error': 'company_name required'
            }

        apify_input = {
            'searchStringsArray': [search_query],
            'maxCrawledPlacesPerSearch': 1
        }

        result = await self._run_actor(actor_id, apify_input)

        if not result['success']:
            return result

        data = result['data']
        enriched = {}

        if 'address' in data:
            enriched['address'] = data['address']
        if 'city' in data:
            enriched['city'] = data['city']
        if 'state' in data:
            enriched['state'] = data['state']
        if 'postalCode' in data:
            enriched['zip'] = data['postalCode']
        if 'phone' in data:
            enriched['phone'] = data['phone']
        if 'website' in data:
            enriched['website'] = data['website']

        return {
            'success': True,
            'data': enriched,
            'error': None
        }
