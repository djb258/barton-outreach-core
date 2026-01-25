"""
Normalization Utilities
=======================
Text normalization functions for company names, domains, cities, and emails.
Implements deterministic, repeatable normalization per doctrine.
"""

import re
import unicodedata
from typing import Optional
from urllib.parse import urlparse


# Company suffixes to remove for matching (order matters - longest first)
COMPANY_SUFFIXES = [
    "incorporated", "corporation", "limited liability company",
    "limited liability partnership", "professional limited liability company",
    "professional corporation", "limited partnership", "general partnership",
    "public limited company", "private limited company",
    "limited", "company", "inc", "llc", "llp", "pllc", "corp", "co",
    "ltd", "pc", "pa", "lp", "gp", "plc", "pvt", "pty",
    "sa", "ag", "gmbh", "bv", "nv"
]

# Personal email domains to detect
PERSONAL_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
    "icloud.com", "mail.com", "protonmail.com", "zoho.com", "yandex.com",
    "live.com", "msn.com", "comcast.net", "verizon.net", "att.net",
    "sbcglobal.net", "bellsouth.net", "cox.net", "charter.net",
    "earthlink.net", "juno.com", "netzero.com", "aim.com"
}

# State abbreviations for normalization
STATE_ABBREVIATIONS = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY", "district of columbia": "DC"
}


def normalize_company_name(name: str, remove_suffixes: bool = True) -> str:
    """
    Normalize company name for matching per doctrine.

    Steps:
    1. Lowercase
    2. Remove LLC, Inc, Corp, Co, Ltd suffixes
    3. Strip punctuation
    4. Collapse whitespace
    5. Remove leading "the"
    6. Keep alphanumeric + spaces only

    Args:
        name: Company name to normalize
        remove_suffixes: Whether to remove Inc, LLC, etc.

    Returns:
        Normalized company name
    """
    if not name or not isinstance(name, str):
        return ""

    # Step 1: Lowercase
    result = name.lower().strip()

    # Step 2: Remove Unicode accents/diacritics
    result = unicodedata.normalize('NFKD', result)
    result = ''.join(c for c in result if not unicodedata.combining(c))

    # Step 3: Remove company suffixes if requested
    if remove_suffixes:
        # Sort by length descending to match longest first
        for suffix in sorted(COMPANY_SUFFIXES, key=len, reverse=True):
            # Match suffix at end with word boundary
            pattern = r'\b' + re.escape(suffix) + r'\.?\s*$'
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)
            # Also try with comma before
            pattern = r',?\s*\b' + re.escape(suffix) + r'\.?\s*$'
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)

    # Step 4: Remove punctuation (keep alphanumeric and spaces)
    result = re.sub(r'[^\w\s]', ' ', result)

    # Step 5: Collapse whitespace
    result = re.sub(r'\s+', ' ', result).strip()

    # Step 6: Remove leading "the"
    if result.startswith('the '):
        result = result[4:]

    return result.strip()


def normalize_domain(domain: str) -> str:
    """
    Normalize domain for comparison.

    Steps:
    1. Lowercase
    2. Remove protocol (http/https)
    3. Remove www prefix
    4. Remove trailing path/slash
    5. Remove port numbers
    6. Strip whitespace

    Args:
        domain: Domain or URL to normalize

    Returns:
        Clean domain (e.g., 'example.com')
    """
    if not domain or not isinstance(domain, str):
        return ""

    result = domain.lower().strip()

    # If it looks like a URL, parse it
    if '://' in result or result.startswith('www.'):
        if not result.startswith('http'):
            result = 'https://' + result

        try:
            parsed = urlparse(result)
            result = parsed.netloc or parsed.path.split('/')[0]
        except Exception:
            pass

    # Remove www. prefix
    if result.startswith('www.'):
        result = result[4:]

    # Remove port
    if ':' in result:
        result = result.split(':')[0]

    # Remove trailing slashes and paths
    result = result.split('/')[0]

    # Remove any remaining whitespace
    result = result.strip()

    # Validate it looks like a domain
    if '.' not in result or len(result) < 4:
        return ""

    return result


def normalize_city(city: str) -> str:
    """
    Normalize city name for matching.

    Steps:
    1. Lowercase
    2. Remove punctuation
    3. Normalize common abbreviations (St. → Saint)
    4. Collapse whitespace
    5. Remove directional prefixes if not part of name

    Args:
        city: City name to normalize

    Returns:
        Normalized city name
    """
    if not city or not isinstance(city, str):
        return ""

    result = city.lower().strip()

    # Remove Unicode accents
    result = unicodedata.normalize('NFKD', result)
    result = ''.join(c for c in result if not unicodedata.combining(c))

    # Common abbreviation expansions
    abbreviations = {
        r'\bst\.?\s': 'saint ',
        r'\bmt\.?\s': 'mount ',
        r'\bft\.?\s': 'fort ',
        r'\bpt\.?\s': 'point ',
        r'\bn\.?\s': 'north ',
        r'\bs\.?\s': 'south ',
        r'\be\.?\s': 'east ',
        r'\bw\.?\s': 'west ',
    }

    for abbr, expansion in abbreviations.items():
        result = re.sub(abbr, expansion, result, flags=re.IGNORECASE)

    # Remove punctuation (keep alphanumeric and spaces)
    result = re.sub(r'[^\w\s]', ' ', result)

    # Collapse whitespace
    result = re.sub(r'\s+', ' ', result).strip()

    return result


def normalize_state(state: str) -> str:
    """
    Normalize state to 2-letter abbreviation.

    Args:
        state: State name or abbreviation

    Returns:
        2-letter state code or empty string
    """
    if not state or not isinstance(state, str):
        return ""

    result = state.lower().strip()

    # If already 2 letters, uppercase and return
    if len(result) == 2:
        return result.upper()

    # Look up full name
    if result in STATE_ABBREVIATIONS:
        return STATE_ABBREVIATIONS[result]

    return result.upper()[:2] if len(result) >= 2 else ""


def normalize_email(email: str) -> str:
    """
    Normalize email address.

    Steps:
    1. Lowercase
    2. Strip whitespace
    3. Validate basic format

    Args:
        email: Email to normalize

    Returns:
        Normalized email address or empty string if invalid
    """
    if not email or not isinstance(email, str):
        return ""

    result = email.lower().strip()

    # Basic format validation
    if '@' not in result or '.' not in result.split('@')[-1]:
        return ""

    # Remove any surrounding angle brackets
    result = result.strip('<>')

    return result


def normalize_name(name: str) -> str:
    """
    Normalize person name for email generation.

    Steps:
    1. Lowercase
    2. Remove accents/diacritics
    3. Handle hyphenated names (keep hyphen)
    4. Remove titles (Dr., Mr., etc.)
    5. Remove suffixes (Jr., Sr., III, etc.)
    6. Strip special characters except hyphen

    Args:
        name: Person name to normalize

    Returns:
        Normalized name suitable for email local part
    """
    if not name or not isinstance(name, str):
        return ""

    result = name.lower().strip()

    # Remove Unicode accents
    result = unicodedata.normalize('NFKD', result)
    result = ''.join(c for c in result if not unicodedata.combining(c))

    # Remove titles
    titles = ['dr', 'mr', 'mrs', 'ms', 'miss', 'prof', 'rev', 'sir', 'dame']
    for title in titles:
        result = re.sub(rf'^{title}\.?\s+', '', result, flags=re.IGNORECASE)

    # Remove suffixes
    suffixes = ['jr', 'sr', 'ii', 'iii', 'iv', 'v', 'phd', 'md', 'esq', 'cpa']
    for suffix in suffixes:
        result = re.sub(rf',?\s*{suffix}\.?\s*$', '', result, flags=re.IGNORECASE)

    # Keep only alphanumeric, spaces, and hyphens
    result = re.sub(r'[^\w\s\-]', '', result)

    # Collapse whitespace
    result = re.sub(r'\s+', ' ', result).strip()

    return result


def clean_text(text: str) -> str:
    """
    General text cleaning utility.

    Steps:
    1. Remove non-printable characters
    2. Normalize unicode
    3. Collapse whitespace
    4. Strip

    Args:
        text: Text to clean

    Returns:
        Cleaned text
    """
    if not text or not isinstance(text, str):
        return ""

    # Remove non-printable characters
    result = ''.join(c for c in text if c.isprintable() or c.isspace())

    # Normalize unicode
    result = unicodedata.normalize('NFC', result)

    # Collapse whitespace
    result = re.sub(r'\s+', ' ', result).strip()

    return result


def extract_domain_from_url(url: str) -> Optional[str]:
    """
    Extract domain from full URL.

    Args:
        url: Full URL (e.g., 'https://www.example.com/page')

    Returns:
        Domain (e.g., 'example.com') or None if invalid
    """
    if not url or not isinstance(url, str):
        return None

    domain = normalize_domain(url)
    return domain if domain else None


def extract_domain_from_email(email: str) -> Optional[str]:
    """
    Extract domain from email address.

    Args:
        email: Email address

    Returns:
        Domain part of email or None if invalid
    """
    if not email or not isinstance(email, str):
        return None

    normalized = normalize_email(email)
    if not normalized or '@' not in normalized:
        return None

    return normalized.split('@')[-1]


def is_personal_email(domain: str) -> bool:
    """
    Check if domain is a personal email provider.

    Personal domains: gmail.com, yahoo.com, hotmail.com, etc.

    Args:
        domain: Domain to check

    Returns:
        True if personal email domain
    """
    if not domain:
        return False

    normalized = normalize_domain(domain)
    return normalized.lower() in PERSONAL_EMAIL_DOMAINS


def normalize_for_matching(text: str) -> str:
    """
    Aggressive normalization for matching purposes.
    Removes all non-alphanumeric characters.

    Args:
        text: Text to normalize

    Returns:
        Alphanumeric-only string
    """
    if not text or not isinstance(text, str):
        return ""

    result = text.lower().strip()

    # Remove accents
    result = unicodedata.normalize('NFKD', result)
    result = ''.join(c for c in result if not unicodedata.combining(c))

    # Keep only alphanumeric
    result = re.sub(r'[^a-z0-9]', '', result)

    return result


# Alias for backward compatibility
def remove_company_suffix(name: str) -> str:
    """Alias for normalize_company_name with remove_suffixes=True."""
    return normalize_company_name(name, remove_suffixes=True)


def clean_company_name(name: str) -> str:
    """Alias for normalize_company_name."""
    return normalize_company_name(name)
