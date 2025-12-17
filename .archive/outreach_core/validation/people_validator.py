#!/usr/bin/env python3
"""
People Validation Agent - Barton Outreach Core
===============================================

DOCTRINE:
- A person record must be **fully valid** before enrichment.
- Any missing or contradictory data sends the person into Garage 2.0 for enrichment repair.
- Person validation depends on company being validated first.

Author: Claude Code
Created: 2025-11-18
Barton ID: 04.04.02.04.50000.###
"""

import re
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# ============================================================================
# CONFIGURATION
# ============================================================================

REQUIRED_FIELDS = [
    'full_name',
    'email',
    'linkedin_url',
    'title',
    'company_unique_id',
]

# C-suite titles
CSUITE_KEYWORDS = ['ceo', 'cfo', 'cto', 'coo', 'chief', 'president', 'founder']

# VP/Director titles
VP_KEYWORDS = ['vp', 'vice president', 'svp', 'evp']
DIRECTOR_KEYWORDS = ['director', 'head of']

# Validation result status
STATUS_PASSED = 'passed'
STATUS_FAILED = 'failed'

# Garage bay assignments
BAY_A = 'bay_a'  # Missing fields
BAY_B = 'bay_b'  # Contradictions

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_sha256_hash(full_name: str, email: str, linkedin_url: str, company_unique_id: str) -> str:
    """
    Generate SHA256 hash from person data + current timestamp.
    Used for deduplication and versioning.
    """
    timestamp = datetime.utcnow().isoformat()
    hash_input = f"{full_name}{email}{linkedin_url}{company_unique_id}{timestamp}"
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

def validate_full_name(name) -> Tuple[bool, Optional[str]]:
    """
    Validate person's full name.

    Returns: (is_valid, error_message)
    """
    if is_null_or_empty(name):
        return False, "full_name_missing"
    if is_placeholder(name):
        return False, "full_name_placeholder"

    name_str = str(name).strip()
    if len(name_str) < 2:
        return False, "full_name_too_short"

    # Should have at least first and last name (space separated)
    if ' ' not in name_str:
        return False, "full_name_single_word"

    return True, None

def validate_email(email) -> Tuple[bool, Optional[str]]:
    """
    Validate email address.

    Returns: (is_valid, error_message)
    """
    if is_null_or_empty(email):
        return False, "email_missing"
    if is_placeholder(email):
        return False, "email_placeholder"

    email_str = str(email).strip().lower()

    # Must have @ symbol
    if '@' not in email_str:
        return False, "email_no_at_symbol"

    # Basic email pattern validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email_str):
        return False, "email_invalid_format"

    return True, None

def validate_linkedin_url(url) -> Tuple[bool, Optional[str]]:
    """
    Validate LinkedIn person URL.

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

    # Must have person profile path (/in/)
    if '/in/' not in url_str:
        return False, "linkedin_not_person_profile"

    return True, None

def validate_title(title) -> Tuple[bool, Optional[str]]:
    """
    Validate job title.

    Returns: (is_valid, error_message)
    """
    if is_null_or_empty(title):
        return False, "title_missing"
    if is_placeholder(title):
        return False, "title_placeholder"

    title_str = str(title).strip()
    if len(title_str) < 2:
        return False, "title_too_short"

    return True, None

def validate_company_unique_id(company_id) -> Tuple[bool, Optional[str]]:
    """
    Validate company foreign key (must exist in company_master).

    Returns: (is_valid, error_message)
    """
    if is_null_or_empty(company_id):
        return False, "company_unique_id_missing"
    if is_placeholder(company_id):
        return False, "company_unique_id_placeholder"

    # Should match Barton ID format: 04.04.01.XX.XXXXX.XXX
    company_id_str = str(company_id).strip()
    if not company_id_str.startswith('04.04.01.'):
        return False, "company_unique_id_invalid_format"

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

def detect_email_domain_mismatch(email: str, company_domain: str) -> Optional[str]:
    """
    Detect mismatch between email domain and company domain.

    Returns: error_message if mismatch detected, None otherwise
    """
    if is_null_or_empty(email) or is_null_or_empty(company_domain):
        return None

    email_str = str(email).lower().strip()
    company_domain_str = str(company_domain).lower().strip()

    # Extract email domain
    if '@' in email_str:
        email_domain = email_str.split('@')[1]

        # Clean company domain
        company_domain_clean = re.sub(r'^https?://', '', company_domain_str)
        company_domain_clean = re.sub(r'^www\.', '', company_domain_clean)
        company_domain_clean = company_domain_clean.split('/')[0]

        # Check if email domain matches company domain
        if email_domain not in company_domain_clean and company_domain_clean not in email_domain:
            # Allow common exceptions (gmail, yahoo, etc.)
            generic_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com']
            if email_domain not in generic_domains:
                return f"email_domain_{email_domain}_mismatch_company_domain_{company_domain_clean}"

    return None

def detect_title_seniority_mismatch(title: str, seniority: str) -> Optional[str]:
    """
    Detect mismatch between job title and seniority level.

    Returns: error_message if mismatch detected, None otherwise
    """
    if is_null_or_empty(title):
        return None

    title_lower = str(title).lower()
    seniority_str = str(seniority).lower() if seniority else ''

    # Check for C-suite in title but seniority != c-suite
    if any(keyword in title_lower for keyword in CSUITE_KEYWORDS):
        if seniority_str and 'c-suite' not in seniority_str and 'executive' not in seniority_str:
            return f"title_suggests_csuite_but_seniority_{seniority_str.replace(' ', '_')}"

    # Check for VP in title but seniority != vp
    if any(keyword in title_lower for keyword in VP_KEYWORDS):
        if seniority_str and 'vp' not in seniority_str and 'vice' not in seniority_str:
            return f"title_suggests_vp_but_seniority_{seniority_str.replace(' ', '_')}"

    # Check for Director in title but seniority != director
    if any(keyword in title_lower for keyword in DIRECTOR_KEYWORDS):
        if seniority_str and 'director' not in seniority_str:
            return f"title_suggests_director_but_seniority_{seniority_str.replace(' ', '_')}"

    return None

def detect_title_department_mismatch(title: str, department: str) -> Optional[str]:
    """
    Detect mismatch between job title and department.

    Returns: error_message if mismatch detected, None otherwise
    """
    if is_null_or_empty(title) or is_null_or_empty(department):
        return None

    title_lower = str(title).lower()
    department_lower = str(department).lower()

    # Engineering keywords in title but department != Engineering
    engineering_keywords = ['engineer', 'developer', 'programmer', 'software', 'architect', 'devops']
    if any(keyword in title_lower for keyword in engineering_keywords):
        if 'engineering' not in department_lower and 'it' not in department_lower and 'technology' not in department_lower:
            return f"title_suggests_engineering_but_department_{department_lower.replace(' ', '_')}"

    # Sales keywords in title but department != Sales
    sales_keywords = ['sales', 'account executive', 'business development', 'account manager']
    if any(keyword in title_lower for keyword in sales_keywords):
        if 'sales' not in department_lower and 'revenue' not in department_lower:
            return f"title_suggests_sales_but_department_{department_lower.replace(' ', '_')}"

    # Marketing keywords in title but department != Marketing
    marketing_keywords = ['marketing', 'brand', 'content', 'digital marketing', 'growth']
    if any(keyword in title_lower for keyword in marketing_keywords):
        if 'marketing' not in department_lower:
            return f"title_suggests_marketing_but_department_{department_lower.replace(' ', '_')}"

    return None

# ============================================================================
# MAIN VALIDATION FUNCTION
# ============================================================================

def validate_person(person: Dict) -> Dict:
    """
    Validate a single person record according to Barton Outreach Doctrine.

    Args:
        person: Dictionary containing person fields

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

    # Full name
    is_valid, error = validate_full_name(person.get('full_name'))
    if not is_valid:
        missing_fields.append(error)

    # Email
    is_valid, error = validate_email(person.get('email'))
    if not is_valid:
        missing_fields.append(error)

    # LinkedIn URL
    is_valid, error = validate_linkedin_url(person.get('linkedin_url'))
    if not is_valid:
        missing_fields.append(error)

    # Title
    is_valid, error = validate_title(person.get('title'))
    if not is_valid:
        missing_fields.append(error)

    # Company unique ID
    is_valid, error = validate_company_unique_id(person.get('company_unique_id'))
    if not is_valid:
        missing_fields.append(error)

    # Apollo ID (required for Apollo-sourced records)
    source_type = person.get('source_type', 'apollo')  # Default to 'apollo' if not specified
    is_valid, error = validate_apollo_id(person.get('apollo_id'), source_type)
    if not is_valid:
        missing_fields.append(error)
    elif error:  # Warning case (non-Apollo source without apollo_id)
        # Log warning but don't fail validation
        pass  # Warning is tracked in validation logs

    # ========================================================================
    # CONTRADICTION DETECTION
    # ========================================================================

    email = person.get('email')
    company_domain = person.get('company_domain')
    title = person.get('title')
    seniority = person.get('seniority')
    department = person.get('department')

    # Email domain vs Company domain
    if email and company_domain:
        error = detect_email_domain_mismatch(email, company_domain)
        if error:
            contradictions.append(error)

    # Title vs Seniority
    if title and seniority:
        error = detect_title_seniority_mismatch(title, seniority)
        if error:
            contradictions.append(error)

    # Title vs Department
    if title and department:
        error = detect_title_department_mismatch(title, department)
        if error:
            contradictions.append(error)

    # ========================================================================
    # CHRONIC BAD CHECK
    # ========================================================================

    enrichment_attempt = person.get('enrichment_attempt', 0)
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
            person.get('full_name', ''),
            person.get('email', ''),
            person.get('linkedin_url', ''),
            person.get('company_unique_id', '')
        )

    return result

# ============================================================================
# BATCH VALIDATION
# ============================================================================

def validate_people(people: List[Dict]) -> List[Dict]:
    """
    Validate a list of person records.

    Args:
        people: List of person dictionaries

    Returns:
        List of validation results (same order as input)
    """
    return [validate_person(person) for person in people]
