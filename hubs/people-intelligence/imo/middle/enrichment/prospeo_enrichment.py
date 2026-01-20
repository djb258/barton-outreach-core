#!/usr/bin/env python3
"""
Prospeo Enrichment Integration - Complete API Client
=====================================================
Full integration with Prospeo API for person and company enrichment.

REPLACES: Clay.com for enrichment

API Documentation: https://prospeo.io/api-docs

ENDPOINTS SUPPORTED:
    - enrich-person: Single person enrichment
    - bulk-enrich-person: Up to 50 persons per request
    - enrich-company: Single company enrichment
    - bulk-enrich-company: Up to 50 companies per request
    - account-info: Check credits and account status

AUTHENTICATION:
    Header: X-KEY: <api_key>
    Environment: PROSPEO_API_KEY

RATE LIMITS:
    - Varies by plan (see https://prospeo.io/api-docs/rate-limits)
    - Bulk endpoints: max 50 records per request

BILLING:
    - 1 credit per matched record
    - No charge for: duplicates (lifetime), no-match results

MINIMUM MATCHING REQUIREMENTS:
    Person: (first_name + last_name + company_*) OR linkedin_url OR email OR person_id
    Company: company_website OR company_linkedin_url OR company_name (website preferred)

Usage:
    # Single person
    from hubs.people_intelligence.imo.middle.enrichment import ProspeoClient
    client = ProspeoClient()
    result = client.enrich_person(first_name="John", last_name="Doe", company_website="acme.com")

    # Bulk persons
    results = client.bulk_enrich_persons([...], only_verified_email=True)

    # Single company
    company = client.enrich_company(company_website="intercom.com")

    # Bulk companies
    companies = client.bulk_enrich_companies([...])

    # From CSV
    doppler run -- python prospeo_enrichment.py input.csv --limit 100

    # From Neon
    doppler run -- python prospeo_enrichment.py --from-neon --limit 100

Created: 2026-01-14
Author: Barton Outreach Core
"""

import os
import sys
import csv
import json
import requests
import time
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Tuple

# Windows encoding fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# =============================================================================
# API CONFIGURATION
# =============================================================================

PROSPEO_BASE_URL = "https://api.prospeo.io"

# Endpoints
ENDPOINTS = {
    'enrich_person': f"{PROSPEO_BASE_URL}/enrich-person",
    'bulk_enrich_person': f"{PROSPEO_BASE_URL}/bulk-enrich-person",
    'enrich_company': f"{PROSPEO_BASE_URL}/enrich-company",
    'bulk_enrich_company': f"{PROSPEO_BASE_URL}/bulk-enrich-company",
    'account_info': f"{PROSPEO_BASE_URL}/account-info",
}

# Limits
BULK_LIMIT = 50  # Max records per bulk request

# Error codes
ERROR_CODES = {
    'INSUFFICIENT_CREDITS': 'Account lacks required credits',
    'INVALID_API_KEY': 'API key is invalid or disabled',
    'RATE_LIMITED': 'Rate limit exceeded for plan',
    'INVALID_REQUEST': 'Request format is invalid',
    'INTERNAL_ERROR': 'Server-side error occurred',
    'NO_MATCH': 'Data could not be matched',
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class PersonEnrichmentRequest:
    """
    Request for person enrichment.

    MINIMUM REQUIREMENTS (one of):
        - first_name + last_name + (company_website OR company_linkedin_url OR company_name)
        - linkedin_url
        - email
        - person_id (Prospeo internal ID)

    For bulk: include 'identifier' to track results
    """
    # Person identifiers
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    person_id: Optional[str] = None  # Prospeo internal ID

    # Company identifiers (at least one required with name)
    company_website: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    company_name: Optional[str] = None

    # Options
    only_verified_email: bool = True
    enrich_mobile: bool = False
    only_verified_mobile: bool = False

    # Tracking (for bulk)
    identifier: Optional[str] = None

    def to_api_payload(self) -> Dict[str, Any]:
        """Convert to API request format."""
        data = {}
        if self.first_name:
            data['first_name'] = self.first_name
        if self.last_name:
            data['last_name'] = self.last_name
        if self.full_name:
            data['full_name'] = self.full_name
        if self.linkedin_url:
            data['linkedin_url'] = self.linkedin_url
        if self.email:
            data['email'] = self.email
        if self.person_id:
            data['person_id'] = self.person_id
        if self.company_website:
            data['company_website'] = self.company_website
        if self.company_linkedin_url:
            data['company_linkedin_url'] = self.company_linkedin_url
        if self.company_name:
            data['company_name'] = self.company_name
        if self.identifier:
            data['identifier'] = self.identifier
        return data


@dataclass
class CompanyEnrichmentRequest:
    """
    Request for company enrichment.

    MINIMUM REQUIREMENTS (at least one, website preferred):
        - company_website (best accuracy)
        - company_linkedin_url
        - company_name (least accurate)

    For bulk: include 'identifier' to track results
    """
    company_website: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    company_name: Optional[str] = None
    identifier: Optional[str] = None

    def to_api_payload(self) -> Dict[str, Any]:
        """Convert to API request format."""
        data = {}
        if self.company_website:
            data['company_website'] = self.company_website
        if self.company_linkedin_url:
            data['company_linkedin_url'] = self.company_linkedin_url
        if self.company_name:
            data['company_name'] = self.company_name
        if self.identifier:
            data['identifier'] = self.identifier
        return data


@dataclass
class PersonResult:
    """
    Result from person enrichment.

    Contains person data, company data, and metadata.
    """
    # Request tracking
    identifier: Optional[str] = None
    request_first_name: Optional[str] = None
    request_last_name: Optional[str] = None
    request_company: Optional[str] = None

    # Person data
    person_id: Optional[str] = None
    email: Optional[str] = None
    email_status: Optional[str] = None  # 'verified', 'unverified', etc.
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    job_title: Optional[str] = None
    headline: Optional[str] = None
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None
    phone_status: Optional[str] = None

    # Company data (from enrichment)
    company_name: Optional[str] = None
    company_website: Optional[str] = None
    company_industry: Optional[str] = None
    company_employee_count: Optional[int] = None
    company_employee_range: Optional[str] = None
    company_location: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    company_type: Optional[str] = None
    company_founded: Optional[int] = None
    company_revenue_range: Optional[str] = None

    # Metadata
    success: bool = False
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    credits_used: int = 0
    enriched_at: Optional[str] = None

    @classmethod
    def from_api_response(cls, data: Dict[str, Any], identifier: str = None) -> 'PersonResult':
        """Parse API response into PersonResult."""
        result = cls(identifier=identifier, enriched_at=datetime.now().isoformat())

        if data.get('error'):
            result.success = False
            result.error_code = data.get('error_code', 'UNKNOWN')
            result.error_message = ERROR_CODES.get(result.error_code, data.get('message', 'Unknown error'))
            return result

        result.success = True
        result.credits_used = 1 if not data.get('free_enrichment') else 0

        # Parse person data
        person = data.get('person', {})
        if person:
            result.person_id = person.get('person_id')
            result.email = person.get('email')
            result.email_status = person.get('email_status')
            result.full_name = person.get('full_name')
            result.first_name = person.get('first_name')
            result.last_name = person.get('last_name')
            result.job_title = person.get('title') or person.get('current_job_title')
            result.headline = person.get('headline')
            result.linkedin_url = person.get('linkedin_url')
            result.phone = person.get('phone')
            result.phone_status = person.get('phone_status')

        # Parse company data
        company = data.get('company', {})
        if company:
            result.company_name = company.get('name')
            result.company_website = company.get('website')
            result.company_industry = company.get('industry')
            result.company_employee_count = company.get('employee_count')
            result.company_employee_range = company.get('employee_range')
            result.company_linkedin_url = company.get('linkedin_url')
            result.company_type = company.get('type')
            result.company_founded = company.get('founded')

            location = company.get('location', {})
            if location:
                parts = [location.get('city'), location.get('state'), location.get('country')]
                result.company_location = ', '.join(p for p in parts if p)

            revenue = company.get('revenue_range_printed')
            if revenue:
                result.company_revenue_range = revenue

        return result


@dataclass
class CompanyResult:
    """
    Result from company enrichment.

    Contains comprehensive company data.
    """
    # Request tracking
    identifier: Optional[str] = None
    request_website: Optional[str] = None

    # Core company data
    name: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    description_ai: Optional[str] = None
    industry: Optional[str] = None
    type: Optional[str] = None  # Private, Public, etc.

    # Size & financials
    employee_count: Optional[int] = None
    employee_range: Optional[str] = None
    founded: Optional[int] = None
    revenue_min: Optional[int] = None
    revenue_max: Optional[int] = None
    revenue_range: Optional[str] = None

    # Location
    country: Optional[str] = None
    country_code: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None

    # Social & contact
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    youtube_url: Optional[str] = None
    crunchbase_url: Optional[str] = None
    phone: Optional[str] = None

    # Technical
    email_domain: Optional[str] = None
    mx_provider: Optional[str] = None
    technologies: Optional[List[str]] = None
    technology_count: Optional[int] = None

    # Funding
    funding_total: Optional[int] = None
    funding_total_printed: Optional[str] = None
    funding_rounds: Optional[int] = None
    latest_funding_stage: Optional[str] = None
    latest_funding_date: Optional[str] = None

    # Classification
    sic_codes: Optional[List[str]] = None
    naics_codes: Optional[List[str]] = None
    keywords: Optional[List[str]] = None

    # Jobs
    active_job_count: Optional[int] = None
    active_job_titles: Optional[List[str]] = None

    # Metadata
    success: bool = False
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    credits_used: int = 0
    enriched_at: Optional[str] = None

    @classmethod
    def from_api_response(cls, data: Dict[str, Any], identifier: str = None) -> 'CompanyResult':
        """Parse API response into CompanyResult."""
        result = cls(identifier=identifier, enriched_at=datetime.now().isoformat())

        if data.get('error'):
            result.success = False
            result.error_code = data.get('error_code', 'UNKNOWN')
            result.error_message = ERROR_CODES.get(result.error_code, data.get('message', 'Unknown error'))
            return result

        result.success = True
        result.credits_used = 1 if not data.get('free_enrichment') else 0

        company = data.get('company', {})
        if not company:
            return result

        # Core data
        result.name = company.get('name')
        result.website = company.get('website')
        result.description = company.get('description')
        result.description_ai = company.get('description_ai')
        result.industry = company.get('industry')
        result.type = company.get('type')

        # Size
        result.employee_count = company.get('employee_count')
        result.employee_range = company.get('employee_range')
        result.founded = company.get('founded')

        # Revenue
        revenue = company.get('revenue_range', {})
        if revenue:
            result.revenue_min = revenue.get('min')
            result.revenue_max = revenue.get('max')
        result.revenue_range = company.get('revenue_range_printed')

        # Location
        location = company.get('location', {})
        if location:
            result.country = location.get('country')
            result.country_code = location.get('country_code')
            result.state = location.get('state')
            result.city = location.get('city')
            result.address = location.get('raw_address')

        # Social
        result.linkedin_url = company.get('linkedin_url')
        result.twitter_url = company.get('twitter_url')
        result.facebook_url = company.get('facebook_url')
        result.instagram_url = company.get('instagram_url')
        result.youtube_url = company.get('youtube_url')
        result.crunchbase_url = company.get('crunchbase_url')

        # Phone
        phone_hq = company.get('phone_hq', {})
        if phone_hq:
            result.phone = phone_hq.get('phone_hq')

        # Technical
        email_tech = company.get('email_tech', {})
        if email_tech:
            result.email_domain = email_tech.get('domain')
            result.mx_provider = email_tech.get('mx_provider')

        tech = company.get('technology', {})
        if tech:
            result.technology_count = tech.get('count')
            result.technologies = tech.get('technology_names', [])[:10]  # Limit to 10

        # Funding
        funding = company.get('funding', {})
        if funding:
            result.funding_total = funding.get('total_funding')
            result.funding_total_printed = funding.get('total_funding_printed')
            result.funding_rounds = funding.get('count')
            result.latest_funding_stage = funding.get('latest_funding_stage')
            result.latest_funding_date = funding.get('latest_funding_date')

        # Classification
        result.sic_codes = company.get('sic_codes')
        result.naics_codes = company.get('naics_codes')
        result.keywords = company.get('keywords', [])[:20]  # Limit to 20

        # Jobs
        jobs = company.get('job_postings', {})
        if jobs:
            result.active_job_count = jobs.get('active_count')
            result.active_job_titles = jobs.get('active_titles', [])[:5]  # Limit to 5

        return result


@dataclass
class EnrichmentStats:
    """Statistics for enrichment operations."""
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    emails_found: int = 0
    verified_emails: int = 0
    companies_enriched: int = 0
    credits_used: int = 0
    errors: List[str] = field(default_factory=list)


# =============================================================================
# PROSPEO API CLIENT
# =============================================================================

class ProspeoClient:
    """
    Complete Prospeo API client.

    Usage:
        client = ProspeoClient()  # Uses PROSPEO_API_KEY env var
        client = ProspeoClient(api_key="pk_...")  # Explicit key

        # Single enrichments
        person = client.enrich_person(first_name="John", last_name="Doe", company_website="acme.com")
        company = client.enrich_company(company_website="intercom.com")

        # Bulk enrichments (up to 50 records)
        persons = client.bulk_enrich_persons(requests_list, only_verified_email=True)
        companies = client.bulk_enrich_companies(requests_list)
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize client with API key."""
        self.api_key = api_key or os.getenv('PROSPEO_API_KEY')
        if not self.api_key:
            raise ValueError("PROSPEO_API_KEY not set. Pass api_key or set environment variable.")

        self.headers = {
            'Content-Type': 'application/json',
            'X-KEY': self.api_key
        }

    # -------------------------------------------------------------------------
    # Account
    # -------------------------------------------------------------------------

    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information including credits balance.

        Returns:
            {
                'credits': int,
                'plan': str,
                'renewal_date': str,
                ...
            }
        """
        try:
            response = requests.get(
                ENDPOINTS['account_info'],
                headers=self.headers,
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return {'error': True, 'status_code': response.status_code}
        except Exception as e:
            return {'error': True, 'message': str(e)}

    def check_credits(self) -> Tuple[bool, int]:
        """
        Check if account has credits available.

        Returns:
            (has_credits: bool, credit_count: int)
        """
        info = self.get_account_info()
        if info.get('error'):
            return False, 0
        credits = info.get('credits', 0)
        return credits > 0, credits

    # -------------------------------------------------------------------------
    # Person Enrichment
    # -------------------------------------------------------------------------

    def enrich_person(
        self,
        first_name: str = None,
        last_name: str = None,
        full_name: str = None,
        company_website: str = None,
        company_linkedin_url: str = None,
        company_name: str = None,
        linkedin_url: str = None,
        email: str = None,
        person_id: str = None,
        only_verified_email: bool = True,
        enrich_mobile: bool = False
    ) -> PersonResult:
        """
        Enrich a single person.

        MINIMUM REQUIREMENTS (one of):
            - first_name + last_name + company_website
            - linkedin_url
            - email
            - person_id

        Args:
            first_name: Person's first name
            last_name: Person's last name
            full_name: Full name (alternative to first+last)
            company_website: Company domain (preferred)
            company_linkedin_url: Company LinkedIn URL
            company_name: Company name (least accurate)
            linkedin_url: Person's LinkedIn URL (high accuracy)
            email: Known email to enrich
            person_id: Prospeo internal person ID
            only_verified_email: Only return if email is verified
            enrich_mobile: Also enrich mobile number

        Returns:
            PersonResult with enriched data or error
        """
        request = PersonEnrichmentRequest(
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            company_website=company_website,
            company_linkedin_url=company_linkedin_url,
            company_name=company_name,
            linkedin_url=linkedin_url,
            email=email,
            person_id=person_id,
            only_verified_email=only_verified_email,
            enrich_mobile=enrich_mobile
        )

        payload = {
            'only_verified_email': only_verified_email,
            'enrich_mobile': enrich_mobile,
            'data': request.to_api_payload()
        }

        try:
            response = requests.post(
                ENDPOINTS['enrich_person'],
                json=payload,
                headers=self.headers,
                timeout=60
            )
            result = PersonResult.from_api_response(response.json())
            result.request_first_name = first_name
            result.request_last_name = last_name
            result.request_company = company_website or company_name
            return result

        except requests.exceptions.Timeout:
            return PersonResult(
                success=False,
                error_code='TIMEOUT',
                error_message='Request timed out',
                request_first_name=first_name,
                request_last_name=last_name
            )
        except Exception as e:
            return PersonResult(
                success=False,
                error_code='EXCEPTION',
                error_message=str(e)[:100],
                request_first_name=first_name,
                request_last_name=last_name
            )

    def bulk_enrich_persons(
        self,
        requests_list: List[PersonEnrichmentRequest],
        only_verified_email: bool = True,
        enrich_mobile: bool = False
    ) -> Tuple[List[PersonResult], EnrichmentStats]:
        """
        Enrich multiple persons in bulk (up to 50 per request).

        For >50 records, automatically batches requests.

        Args:
            requests_list: List of PersonEnrichmentRequest objects
            only_verified_email: Only return verified emails
            enrich_mobile: Also enrich mobile numbers

        Returns:
            Tuple of (results list, stats)
        """
        all_results = []
        stats = EnrichmentStats(total_requests=len(requests_list))

        # Process in batches of 50 (with rate limiting)
        total_batches = (len(requests_list) + BULK_LIMIT - 1) // BULK_LIMIT
        for batch_idx, batch_start in enumerate(range(0, len(requests_list), BULK_LIMIT)):
            batch = requests_list[batch_start:batch_start + BULK_LIMIT]

            # Rate limiting: wait between batches (avoid rate limit)
            if batch_idx > 0:
                import time
                time.sleep(2)  # 2 second delay between batches

            print(f"  Batch {batch_idx + 1}/{total_batches} ({len(batch)} records)...")

            # Ensure all have identifiers
            for i, req in enumerate(batch):
                if not req.identifier:
                    req.identifier = f"record_{batch_start + i}"

            payload = {
                'only_verified_email': only_verified_email,
                'enrich_mobile': enrich_mobile,
                'data': [req.to_api_payload() for req in batch]
            }

            try:
                response = requests.post(
                    ENDPOINTS['bulk_enrich_person'],
                    json=payload,
                    headers=self.headers,
                    timeout=120
                )
                data = response.json()

                if data.get('error'):
                    # Whole batch failed
                    for req in batch:
                        result = PersonResult(
                            identifier=req.identifier,
                            success=False,
                            error_code=data.get('error_code', 'BATCH_ERROR'),
                            error_message=data.get('message', 'Batch request failed')
                        )
                        all_results.append(result)
                        stats.failed += 1
                    continue

                stats.credits_used += data.get('total_cost', 0)

                # Process matched results
                for matched in data.get('matched', []):
                    result = PersonResult.from_api_response(
                        {'person': matched.get('person'), 'company': matched.get('company')},
                        identifier=matched.get('identifier')
                    )
                    all_results.append(result)
                    stats.successful += 1
                    if result.email:
                        stats.emails_found += 1
                        if result.email_status == 'verified':
                            stats.verified_emails += 1

                # Process not matched
                for identifier in data.get('not_matched', []):
                    result = PersonResult(
                        identifier=identifier,
                        success=False,
                        error_code='NO_MATCH',
                        error_message='Person could not be matched'
                    )
                    all_results.append(result)
                    stats.failed += 1

                # Process invalid
                for identifier in data.get('invalid_datapoints', []):
                    result = PersonResult(
                        identifier=identifier,
                        success=False,
                        error_code='INVALID_REQUEST',
                        error_message='Invalid data provided'
                    )
                    all_results.append(result)
                    stats.failed += 1
                    stats.errors.append(f"Invalid: {identifier}")

            except Exception as e:
                for req in batch:
                    result = PersonResult(
                        identifier=req.identifier,
                        success=False,
                        error_code='EXCEPTION',
                        error_message=str(e)[:100]
                    )
                    all_results.append(result)
                    stats.failed += 1

        return all_results, stats

    # -------------------------------------------------------------------------
    # Company Enrichment
    # -------------------------------------------------------------------------

    def enrich_company(
        self,
        company_website: str = None,
        company_linkedin_url: str = None,
        company_name: str = None
    ) -> CompanyResult:
        """
        Enrich a single company.

        MINIMUM REQUIREMENTS (at least one, website preferred):
            - company_website (best accuracy)
            - company_linkedin_url
            - company_name (least accurate)

        Args:
            company_website: Company domain (e.g., 'intercom.com')
            company_linkedin_url: LinkedIn company URL
            company_name: Company name (fallback)

        Returns:
            CompanyResult with enriched data or error
        """
        request = CompanyEnrichmentRequest(
            company_website=company_website,
            company_linkedin_url=company_linkedin_url,
            company_name=company_name
        )

        payload = {'data': request.to_api_payload()}

        try:
            response = requests.post(
                ENDPOINTS['enrich_company'],
                json=payload,
                headers=self.headers,
                timeout=60
            )
            result = CompanyResult.from_api_response(response.json())
            result.request_website = company_website
            return result

        except requests.exceptions.Timeout:
            return CompanyResult(
                success=False,
                error_code='TIMEOUT',
                error_message='Request timed out',
                request_website=company_website
            )
        except Exception as e:
            return CompanyResult(
                success=False,
                error_code='EXCEPTION',
                error_message=str(e)[:100],
                request_website=company_website
            )

    def bulk_enrich_companies(
        self,
        requests_list: List[CompanyEnrichmentRequest]
    ) -> Tuple[List[CompanyResult], EnrichmentStats]:
        """
        Enrich multiple companies in bulk (up to 50 per request).

        For >50 records, automatically batches requests.

        Args:
            requests_list: List of CompanyEnrichmentRequest objects

        Returns:
            Tuple of (results list, stats)
        """
        all_results = []
        stats = EnrichmentStats(total_requests=len(requests_list))

        # Process in batches of 50
        for batch_start in range(0, len(requests_list), BULK_LIMIT):
            batch = requests_list[batch_start:batch_start + BULK_LIMIT]

            # Ensure all have identifiers
            for i, req in enumerate(batch):
                if not req.identifier:
                    req.identifier = f"company_{batch_start + i}"

            payload = {'data': [req.to_api_payload() for req in batch]}

            try:
                response = requests.post(
                    ENDPOINTS['bulk_enrich_company'],
                    json=payload,
                    headers=self.headers,
                    timeout=120
                )
                data = response.json()

                if data.get('error'):
                    for req in batch:
                        result = CompanyResult(
                            identifier=req.identifier,
                            success=False,
                            error_code=data.get('error_code', 'BATCH_ERROR'),
                            error_message=data.get('message', 'Batch request failed')
                        )
                        all_results.append(result)
                        stats.failed += 1
                    continue

                stats.credits_used += data.get('total_cost', 0)

                # Process matched
                for matched in data.get('matched', []):
                    result = CompanyResult.from_api_response(
                        {'company': matched.get('company')},
                        identifier=matched.get('identifier')
                    )
                    all_results.append(result)
                    stats.successful += 1
                    stats.companies_enriched += 1

                # Process not matched
                for identifier in data.get('not_matched', []):
                    result = CompanyResult(
                        identifier=identifier,
                        success=False,
                        error_code='NO_MATCH',
                        error_message='Company could not be matched'
                    )
                    all_results.append(result)
                    stats.failed += 1

                # Process invalid
                for identifier in data.get('invalid_datapoints', []):
                    result = CompanyResult(
                        identifier=identifier,
                        success=False,
                        error_code='INVALID_REQUEST',
                        error_message='Invalid data provided'
                    )
                    all_results.append(result)
                    stats.failed += 1

            except Exception as e:
                for req in batch:
                    result = CompanyResult(
                        identifier=req.identifier,
                        success=False,
                        error_code='EXCEPTION',
                        error_message=str(e)[:100]
                    )
                    all_results.append(result)
                    stats.failed += 1

        return all_results, stats


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def enrich_persons_from_csv(
    csv_path: str,
    output_dir: str,
    only_verified: bool = True,
    limit: Optional[int] = None,
    single_mode: bool = False,
    delay_seconds: float = 1.0
) -> Tuple[List[PersonResult], EnrichmentStats]:
    """
    Enrich persons from CSV file.

    Expected columns: First Name, Last Name, Company Domain (or Company Website)

    Args:
        csv_path: Input CSV path
        output_dir: Output directory
        only_verified: Only return verified emails
        limit: Max records to process
        single_mode: Use single enrichment calls (slower, more reliable)
        delay_seconds: Delay between calls in single mode
    """
    print("="*60)
    print("PROSPEO PERSON ENRICHMENT FROM CSV")
    print("="*60)

    client = ProspeoClient()

    # Check credits (note: account-info endpoint may not be available on all plans)
    has_credits, credit_count = client.check_credits()
    if credit_count > 0:
        print(f"Credits available: {credit_count}")
    else:
        print(f"Credits: Unable to verify (will proceed with enrichment)")

    # Load CSV
    requests_list = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if limit and i >= limit:
                break

            first_name = row.get('First Name', row.get('first_name', '')).strip()
            last_name = row.get('Last Name', row.get('last_name', '')).strip()
            domain = row.get('Company Domain', row.get('company_domain', row.get('Company Website', ''))).strip()
            domain = domain.lower().replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]

            if first_name and last_name and domain:
                requests_list.append(PersonEnrichmentRequest(
                    first_name=first_name,
                    last_name=last_name,
                    company_website=domain,
                    identifier=f"row_{i}",
                    only_verified_email=only_verified
                ))

    print(f"Records to enrich: {len(requests_list)}")
    if single_mode:
        print(f"Mode: Single (delay={delay_seconds}s)")
    else:
        print(f"Mode: Bulk")

    # Enrich
    if single_mode:
        import time
        results = []
        stats = EnrichmentStats(total_requests=len(requests_list))
        for i, req in enumerate(requests_list):
            if i > 0:
                time.sleep(delay_seconds)
            print(f"  [{i+1}/{len(requests_list)}] {req.first_name} {req.last_name} @ {req.company_website}...", end=" ")
            result = client.enrich_person(
                first_name=req.first_name,
                last_name=req.last_name,
                company_website=req.company_website,
                only_verified_email=only_verified
            )
            result.identifier = req.identifier  # Add identifier for output
            results.append(result)
            if result.success:
                stats.successful += 1
                if result.email:
                    stats.emails_found += 1
                    print(f"OK: {result.email}")
                else:
                    print("OK (no email)")
            else:
                stats.failed += 1
                print(f"FAIL: {result.error_code}")
    else:
        results, stats = client.bulk_enrich_persons(requests_list, only_verified_email=only_verified)

    # Write output
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_file = os.path.join(output_dir, f"prospeo_persons_{timestamp}.csv")
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'identifier', 'first_name', 'last_name', 'email', 'email_status',
            'job_title', 'linkedin_url', 'company_name', 'company_industry',
            'success', 'error_code'
        ])
        for r in results:
            writer.writerow([
                r.identifier, r.first_name, r.last_name, r.email, r.email_status,
                r.job_title, r.linkedin_url, r.company_name, r.company_industry,
                r.success, r.error_code
            ])

    print(f"\nOutput: {output_file}")
    print(f"Total: {stats.total_requests}, Success: {stats.successful}, Failed: {stats.failed}")
    print(f"Verified emails: {stats.verified_emails}, Credits used: {stats.credits_used}")

    return results, stats


def enrich_companies_from_csv(
    csv_path: str,
    output_dir: str,
    limit: Optional[int] = None
) -> Tuple[List[CompanyResult], EnrichmentStats]:
    """
    Enrich companies from CSV file.

    Expected columns: Company Domain (or Company Website or Domain)
    """
    print("="*60)
    print("PROSPEO COMPANY ENRICHMENT FROM CSV")
    print("="*60)

    client = ProspeoClient()

    # Check credits
    has_credits, credit_count = client.check_credits()
    print(f"Credits available: {credit_count}")

    # Load CSV
    requests_list = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if limit and i >= limit:
                break

            domain = row.get('Company Domain', row.get('company_domain', row.get('Domain', row.get('domain', '')))).strip()
            domain = domain.lower().replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]

            if domain:
                requests_list.append(CompanyEnrichmentRequest(
                    company_website=domain,
                    identifier=f"company_{i}"
                ))

    print(f"Companies to enrich: {len(requests_list)}")

    # Enrich
    results, stats = client.bulk_enrich_companies(requests_list)

    # Write output
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_file = os.path.join(output_dir, f"prospeo_companies_{timestamp}.csv")
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'identifier', 'name', 'website', 'industry', 'type',
            'employee_count', 'employee_range', 'founded', 'revenue_range',
            'city', 'state', 'country', 'linkedin_url', 'phone',
            'funding_total', 'technology_count', 'success', 'error_code'
        ])
        for r in results:
            writer.writerow([
                r.identifier, r.name, r.website, r.industry, r.type,
                r.employee_count, r.employee_range, r.founded, r.revenue_range,
                r.city, r.state, r.country, r.linkedin_url, r.phone,
                r.funding_total_printed, r.technology_count, r.success, r.error_code
            ])

    print(f"\nOutput: {output_file}")
    print(f"Total: {stats.total_requests}, Success: {stats.successful}, Failed: {stats.failed}")
    print(f"Credits used: {stats.credits_used}")

    return results, stats


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""
Prospeo Enrichment CLI
======================

USAGE:
    # Person enrichment from CSV
    python prospeo_enrichment.py persons <csv_path> [--limit N] [--include-unverified]

    # Company enrichment from CSV
    python prospeo_enrichment.py companies <csv_path> [--limit N]

    # Check account credits
    python prospeo_enrichment.py credits

    # Single person test
    python prospeo_enrichment.py test-person <first_name> <last_name> <domain>

    # Single company test
    python prospeo_enrichment.py test-company <domain>

ENVIRONMENT:
    PROSPEO_API_KEY - Required API key

EXAMPLES:
    doppler run -- python prospeo_enrichment.py persons leads.csv --limit 50
    doppler run -- python prospeo_enrichment.py companies domains.csv
    doppler run -- python prospeo_enrichment.py test-person "Elon" "Musk" "tesla.com"
    doppler run -- python prospeo_enrichment.py test-company "intercom.com"
""")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'credits':
        client = ProspeoClient()
        info = client.get_account_info()
        print(json.dumps(info, indent=2))

    elif command == 'test-person':
        if len(sys.argv) < 5:
            print("Usage: test-person <first_name> <last_name> <domain>")
            sys.exit(1)
        client = ProspeoClient()
        result = client.enrich_person(
            first_name=sys.argv[2],
            last_name=sys.argv[3],
            company_website=sys.argv[4]
        )
        print(f"Success: {result.success}")
        print(f"Email: {result.email} ({result.email_status})")
        print(f"Title: {result.job_title}")
        print(f"Company: {result.company_name}")
        if result.error_code:
            print(f"Error: {result.error_code} - {result.error_message}")

    elif command == 'test-company':
        if len(sys.argv) < 3:
            print("Usage: test-company <domain>")
            sys.exit(1)
        client = ProspeoClient()
        result = client.enrich_company(company_website=sys.argv[2])
        print(f"Success: {result.success}")
        print(f"Name: {result.name}")
        print(f"Industry: {result.industry}")
        print(f"Employees: {result.employee_count} ({result.employee_range})")
        print(f"Location: {result.city}, {result.state}, {result.country}")
        print(f"Revenue: {result.revenue_range}")
        print(f"Funding: {result.funding_total_printed}")
        if result.error_code:
            print(f"Error: {result.error_code} - {result.error_message}")

    elif command == 'persons':
        if len(sys.argv) < 3:
            print("Usage: persons <csv_path> [--limit N] [--single] [--delay N]")
            sys.exit(1)
        csv_path = sys.argv[2]
        limit = None
        if '--limit' in sys.argv:
            idx = sys.argv.index('--limit')
            limit = int(sys.argv[idx + 1])
        single_mode = '--single' in sys.argv
        delay = 1.0
        if '--delay' in sys.argv:
            idx = sys.argv.index('--delay')
            delay = float(sys.argv[idx + 1])
        only_verified = '--include-unverified' not in sys.argv
        output_dir = os.path.join(os.path.dirname(csv_path) or '.', "prospeo_output")
        enrich_persons_from_csv(csv_path, output_dir, only_verified=only_verified, limit=limit,
                               single_mode=single_mode, delay_seconds=delay)

    elif command == 'companies':
        if len(sys.argv) < 3:
            print("Usage: companies <csv_path> [--limit N]")
            sys.exit(1)
        csv_path = sys.argv[2]
        limit = None
        if '--limit' in sys.argv:
            idx = sys.argv.index('--limit')
            limit = int(sys.argv[idx + 1])
        output_dir = os.path.join(os.path.dirname(csv_path) or '.', "prospeo_output")
        enrich_companies_from_csv(csv_path, output_dir, limit=limit)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
