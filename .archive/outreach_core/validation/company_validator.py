#!/usr/bin/env python3
"""
Company Validation Agent - Barton Outreach Core
================================================

DOCTRINE:
- A company must be **fully valid** before any associated people can be loaded or enriched.
- Any missing or contradictory data sends the company into Garage 2.0 for enrichment repair.

Author: Claude Code
Created: 2025-11-18
Barton ID: 04.04.02.04.50000.###
"""

import re
import hashlib
import socket
import requests
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse

# ============================================================================
# CONFIGURATION
# ============================================================================

REQUIRED_FIELDS = [
    'company_name',
    'domain',
    'linkedin_url',
    'employee_count',
    'industry',
    'location',
]

# Industry categories for .edu, .org, .gov domains
EDUCATION_INDUSTRIES = {'Education', 'Higher Education', 'E-Learning', 'Primary/Secondary Education'}
NONPROFIT_INDUSTRIES = {'Nonprofit Organization Management', 'Philanthropy', 'Religious Institutions', 'Civic & Social Organization'}
GOVERNMENT_INDUSTRIES = {'Government Administration', 'Government Relations', 'Military', 'Public Safety', 'Public Policy'}

# Corporate-style domains (large enterprises)
CORPORATE_DOMAINS = {
    'raytheon.com', 'lockheed.com', 'boeing.com', 'ge.com', 'microsoft.com',
    'amazon.com', 'google.com', 'apple.com', 'ibm.com', 'oracle.com'
}

# Validation result status
STATUS_PASSED = 'passed'
STATUS_FAILED = 'failed'

# Garage bay assignments
BAY_A = 'bay_a'  # Missing fields
BAY_B = 'bay_b'  # Contradictions

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_sha256_hash(company_name: str, domain: str, linkedin_url: str, apollo_id: Optional[str]) -> str:
    """
    Generate SHA256 hash from company data + current timestamp.
    Used for deduplication and versioning.
    """
    timestamp = datetime.utcnow().isoformat()
    apollo_str = apollo_id if apollo_id else ''
    hash_input = f"{company_name}{domain}{linkedin_url}{apollo_str}{timestamp}"
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

def is_null_or_empty(value) -> bool:
    """Check if value is None, empty string, or whitespace only."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == '':
        return True
    return False

def is_placeholder(value) -> bool:
    """Check if value matches common placeholder patterns."""
    if is_null_or_empty(value):
        return True

    placeholder_patterns = [
        r'^\s*$', r'^n/?a$', r'^none$', r'^null$', r'^unknown$',
        r'^tbd$', r'^test', r'^example', r'^placeholder', r'^pending$',
    ]

    value_str = str(value).lower().strip()
    for pattern in placeholder_patterns:
        if re.match(pattern, value_str, re.IGNORECASE):
            return True
    return False

# ============================================================================
# FIELD VALIDATORS
# ============================================================================

def validate_company_name(name) -> Tuple[bool, Optional[str]]:
    """
    Validate company name.

    Returns: (is_valid, error_message)
    """
    if is_null_or_empty(name):
        return False, "company_name_missing"
    if is_placeholder(name):
        return False, "company_name_placeholder"
    if len(str(name).strip()) < 2:
        return False, "company_name_too_short"
    return True, None

def validate_domain(domain) -> Tuple[bool, Optional[str]]:
    """
    Validate domain format.

    Returns: (is_valid, error_message)
    """
    if is_null_or_empty(domain):
        return False, "domain_missing"
    if is_placeholder(domain):
        return False, "domain_placeholder"

    domain_str = str(domain).strip().lower()

    # Remove protocol if present
    domain_str = re.sub(r'^https?://', '', domain_str)
    domain_str = re.sub(r'^www\.', '', domain_str)

    # Must have TLD
    if '.' not in domain_str:
        return False, "domain_no_tld"

    # Extract domain part (before first slash)
    domain_part = domain_str.split('/')[0]

    # Basic domain validation
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-\.]*[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$'
    if not re.match(domain_pattern, domain_part):
        return False, "domain_invalid_format"

    return True, None

def validate_domain_resolution(domain, check_live: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Validate that domain resolves to a real website.

    Args:
        domain: Domain to check
        check_live: If True, perform live DNS/HTTP checks (use in prod)

    Returns: (is_valid, error_message)
    """
    if not check_live:
        # In dev/test mode, skip live checks
        return True, None

    try:
        # Clean domain
        domain_str = str(domain).strip().lower()
        domain_str = re.sub(r'^https?://', '', domain_str)
        domain_str = re.sub(r'^www\.', '', domain_str)
        domain_part = domain_str.split('/')[0]

        # DNS check
        try:
            socket.gethostbyname(domain_part)
        except socket.gaierror:
            return False, "domain_dns_not_found"

        # HTTP HEAD check
        try:
            response = requests.head(f"https://{domain_part}", timeout=5, allow_redirects=True)
            if response.status_code >= 400:
                return False, f"domain_http_error_{response.status_code}"
        except requests.exceptions.RequestException:
            # Try HTTP if HTTPS fails
            try:
                response = requests.head(f"http://{domain_part}", timeout=5, allow_redirects=True)
                if response.status_code >= 400:
                    return False, f"domain_http_error_{response.status_code}"
            except requests.exceptions.RequestException:
                return False, "domain_http_unreachable"

        return True, None

    except Exception as e:
        return False, f"domain_resolution_error_{str(e)[:20]}"

def validate_linkedin_url(url) -> Tuple[bool, Optional[str]]:
    """
    Validate LinkedIn company URL.

    Returns: (is_valid, error_message)
    """
    if is_null_or_empty(url):
        return False, "linkedin_missing"
    if is_placeholder(url):
        return False, "linkedin_placeholder"

    url_str = str(url).strip().lower()

    # Must be linkedin.com
    if 'linkedin.com' not in url_str:
        return False, "linkedin_not_linkedin_domain"

    # Must have company profile path
    if '/company/' not in url_str:
        return False, "linkedin_not_company_profile"

    return True, None

def validate_employee_count(count) -> Tuple[bool, Optional[str]]:
    """
    Validate employee count (numeric or range).

    Returns: (is_valid, error_message)
    """
    if is_null_or_empty(count):
        return False, "employee_count_missing"
    if is_placeholder(count):
        return False, "employee_count_placeholder"

    # Accept numeric values
    try:
        int_count = int(count)
        if int_count < 0:
            return False, "employee_count_negative"
        return True, None
    except (ValueError, TypeError):
        pass

    # Accept ranges like "11-50", "201-500"
    count_str = str(count).strip()
    range_pattern = r'^\d+-\d+$'
    if re.match(range_pattern, count_str):
        return True, None

    # Accept descriptive ranges
    valid_ranges = ['1-10', '11-50', '51-200', '201-500', '501-1000', '1001-5000', '5001-10000', '10000+']
    if count_str in valid_ranges:
        return True, None

    return False, "employee_count_invalid_format"

def validate_industry(industry) -> Tuple[bool, Optional[str]]:
    """
    Validate industry category.

    Returns: (is_valid, error_message)
    """
    if is_null_or_empty(industry):
        return False, "industry_missing"
    if is_placeholder(industry):
        return False, "industry_placeholder"

    # Basic check: industry should be at least 3 characters
    if len(str(industry).strip()) < 3:
        return False, "industry_too_short"

    return True, None

def validate_location(location) -> Tuple[bool, Optional[str]]:
    """
    Validate location (city and state minimum).

    Returns: (is_valid, error_message)
    """
    if is_null_or_empty(location):
        return False, "location_missing"
    if is_placeholder(location):
        return False, "location_placeholder"

    # Location should have at least city or state
    location_str = str(location).strip()
    if len(location_str) < 2:
        return False, "location_too_short"

    return True, None

def validate_apollo_id(apollo_id, source_type: str = "apollo") -> Tuple[bool, Optional[str]]:
    """
    Validate Apollo ID based on source type.

    NEW DOCTRINE (2025-11-18):
    - If source_type == "apollo" and apollo_id is missing → FAIL validation
    - If source_type != "apollo" and apollo_id is missing → PASS with warning
    - Enrichment-based records can skip apollo_id requirement

    Args:
        apollo_id: Apollo.io identifier
        source_type: Source of the record ("apollo", "enrichment", "csv", etc.)

    Returns: (is_valid, error_message)
    """
    # Check if this is an Apollo-sourced record
    source_is_apollo = str(source_type).lower() == "apollo"

    if is_null_or_empty(apollo_id):
        if source_is_apollo:
            # Apollo-sourced records MUST have apollo_id
            return False, "apollo_id_missing"
        else:
            # Enrichment/other sources can skip apollo_id (log warning)
            return True, "apollo_id_missing_non_apollo_source_warning"

    if is_placeholder(apollo_id):
        return False, "apollo_id_placeholder"

    return True, None

# ============================================================================
# CONTRADICTION DETECTION (BAY B)
# ============================================================================

def detect_domain_industry_mismatch(domain: str, industry: str) -> Optional[str]:
    """
    Detect contradictions between domain TLD and industry.

    Returns: error_message if mismatch detected, None otherwise
    """
    domain_str = str(domain).lower().strip()
    industry_str = str(industry).strip()

    # .edu domains should be Education industry
    if domain_str.endswith('.edu'):
        if industry_str not in EDUCATION_INDUSTRIES:
            return f"domain_edu_but_industry_{industry_str.replace(' ', '_')}"

    # .org domains should be Nonprofit
    if domain_str.endswith('.org'):
        if industry_str not in NONPROFIT_INDUSTRIES:
            return f"domain_org_but_industry_{industry_str.replace(' ', '_')}"

    # .gov domains should be Government
    if domain_str.endswith('.gov'):
        if industry_str not in GOVERNMENT_INDUSTRIES:
            return f"domain_gov_but_industry_{industry_str.replace(' ', '_')}"

    return None

def detect_employee_domain_mismatch(employee_count, domain: str) -> Optional[str]:
    """
    Detect mismatch between employee count and corporate domain.

    Returns: error_message if mismatch detected, None otherwise
    """
    domain_str = str(domain).lower().strip()

    # Extract numeric employee count
    try:
        if isinstance(employee_count, int):
            count = employee_count
        elif '-' in str(employee_count):
            # Take lower bound of range
            count = int(str(employee_count).split('-')[0])
        else:
            count = int(employee_count)

        # Corporate-style domains with < 10 employees is suspicious
        if count < 10 and domain_str in CORPORATE_DOMAINS:
            return f"employee_count_{count}_but_corporate_domain"

    except (ValueError, TypeError):
        pass

    return None

def detect_name_industry_mismatch(company_name: str, industry: str) -> Optional[str]:
    """
    Detect contradictions between company name and industry.

    Returns: error_message if mismatch detected, None otherwise
    """
    name_str = str(company_name).lower()
    industry_str = str(industry).strip()

    # Educational institutions
    edu_keywords = ['school', 'university', 'college', 'academy', 'institute']
    if any(keyword in name_str for keyword in edu_keywords):
        if industry_str not in EDUCATION_INDUSTRIES:
            return f"name_suggests_education_but_industry_{industry_str.replace(' ', '_')}"

    # Religious institutions
    religious_keywords = ['church', 'temple', 'mosque', 'synagogue', 'ministry']
    if any(keyword in name_str for keyword in religious_keywords):
        if industry_str not in NONPROFIT_INDUSTRIES and industry_str not in EDUCATION_INDUSTRIES:
            return f"name_suggests_religious_but_industry_{industry_str.replace(' ', '_')}"

    return None

# ============================================================================
# MAIN VALIDATION FUNCTION
# ============================================================================

def validate_company(company: Dict, check_live_dns: bool = False) -> Dict:
    """
    Validate a single company record according to Barton Outreach Doctrine.

    Args:
        company: Dictionary containing company fields
        check_live_dns: If True, perform live DNS/HTTP checks (use in prod)

    Returns:
        Dictionary with validation results:
        {
            'validation_status': 'passed' | 'failed',
            'garage_bay': 'bay_a' | 'bay_b' | None,
            'reasons': [list of error messages],
            'last_hash': 'sha256_hash' (only if passed),
            'is_chronic': bool,
        }
    """
    result = {
        'validation_status': STATUS_PASSED,
        'garage_bay': None,
        'reasons': [],
        'last_hash': None,
        'is_chronic': False,
    }

    # Track missing fields (Bay A)
    missing_fields = []

    # Track contradictions (Bay B)
    contradictions = []

    # ========================================================================
    # REQUIRED FIELD VALIDATION
    # ========================================================================

    # Company name
    is_valid, error = validate_company_name(company.get('company_name') or company.get('company'))
    if not is_valid:
        missing_fields.append(error)

    # Domain
    is_valid, error = validate_domain(company.get('domain') or company.get('website'))
    if not is_valid:
        missing_fields.append(error)
    else:
        # Domain resolution check (if enabled)
        is_valid, error = validate_domain_resolution(company.get('domain') or company.get('website'), check_live_dns)
        if not is_valid:
            contradictions.append(error)

    # LinkedIn URL
    is_valid, error = validate_linkedin_url(company.get('linkedin_url') or company.get('company_linkedin_url'))
    if not is_valid:
        missing_fields.append(error)

    # Employee count
    is_valid, error = validate_employee_count(company.get('employee_count') or company.get('num_employees'))
    if not is_valid:
        missing_fields.append(error)

    # Industry
    is_valid, error = validate_industry(company.get('industry'))
    if not is_valid:
        missing_fields.append(error)

    # Location
    location = company.get('location') or f"{company.get('company_city', '')}, {company.get('company_state', '')}".strip(', ')
    is_valid, error = validate_location(location)
    if not is_valid:
        missing_fields.append(error)

    # Apollo ID (required for Apollo-sourced records)
    source_type = company.get('source_type', 'apollo')  # Default to 'apollo' if not specified
    is_valid, error = validate_apollo_id(company.get('apollo_id'), source_type)
    if not is_valid:
        missing_fields.append(error)
    elif error:  # Warning case (non-Apollo source without apollo_id)
        # Log warning but don't fail validation
        pass  # Warning is tracked in validation logs

    # ========================================================================
    # CONTRADICTION DETECTION
    # ========================================================================

    domain = company.get('domain') or company.get('website')
    industry = company.get('industry')
    employee_count = company.get('employee_count') or company.get('num_employees')
    company_name = company.get('company_name') or company.get('company')

    # Domain vs Industry
    if domain and industry:
        error = detect_domain_industry_mismatch(domain, industry)
        if error:
            contradictions.append(error)

    # Employee count vs Domain
    if employee_count and domain:
        error = detect_employee_domain_mismatch(employee_count, domain)
        if error:
            contradictions.append(error)

    # Company name vs Industry
    if company_name and industry:
        error = detect_name_industry_mismatch(company_name, industry)
        if error:
            contradictions.append(error)

    # ========================================================================
    # CHRONIC BAD CHECK
    # ========================================================================

    enrichment_attempt = company.get('enrichment_attempt', 0)
    if enrichment_attempt >= 2:
        result['is_chronic'] = True
        contradictions.append('chronic_bad_3_plus_failures')

    # ========================================================================
    # DETERMINE RESULT
    # ========================================================================

    if missing_fields:
        # Bay A: Missing fields
        result['validation_status'] = STATUS_FAILED
        result['garage_bay'] = BAY_A
        result['reasons'] = missing_fields + contradictions

    elif contradictions:
        # Bay B: Contradictions
        result['validation_status'] = STATUS_FAILED
        result['garage_bay'] = BAY_B
        result['reasons'] = contradictions

    else:
        # PASSED: Generate hash
        result['validation_status'] = STATUS_PASSED
        result['last_hash'] = generate_sha256_hash(
            company_name or '',
            domain or '',
            company.get('linkedin_url') or company.get('company_linkedin_url') or '',
            company.get('apollo_id')
        )

    return result

# ============================================================================
# BATCH VALIDATION
# ============================================================================

def validate_companies(companies: List[Dict], check_live_dns: bool = False) -> List[Dict]:
    """
    Validate a list of company records.

    Args:
        companies: List of company dictionaries
        check_live_dns: If True, perform live DNS/HTTP checks

    Returns:
        List of validation results (same order as input)
    """
    return [validate_company(company, check_live_dns) for company in companies]
