"""
Email Pattern Utilities
=======================
Email pattern detection, validation, and application.
Supports all common email formats with confidence scoring.
"""

import re
import unicodedata
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from collections import Counter


# Common email patterns (most to least common, with likelihood scores)
COMMON_PATTERNS = [
    ("{first}.{last}", 0.95),        # john.smith@domain.com
    ("{first}{last}", 0.85),         # johnsmith@domain.com
    ("{f}{last}", 0.80),             # jsmith@domain.com
    ("{first}_{last}", 0.75),        # john_smith@domain.com
    ("{first}-{last}", 0.70),        # john-smith@domain.com
    ("{f}.{last}", 0.70),            # j.smith@domain.com
    ("{last}.{first}", 0.65),        # smith.john@domain.com
    ("{last}{first}", 0.60),         # smithjohn@domain.com
    ("{last}{f}", 0.55),             # smithj@domain.com
    ("{first}", 0.50),               # john@domain.com
    ("{last}", 0.45),                # smith@domain.com
    ("{first}{l}", 0.45),            # johns@domain.com
    ("{f}{l}{last}", 0.40),          # jssmith@domain.com
    ("{first}.{l}", 0.40),           # john.s@domain.com
    ("{f}.{l}.{last}", 0.35),        # j.s.smith@domain.com
    ("{ff}{last}", 0.35),            # josmith@domain.com (first 2 chars)
    ("{last}.{f}", 0.30),            # smith.j@domain.com
    ("{last}_{first}", 0.30),        # smith_john@domain.com
    ("{last}-{first}", 0.25),        # smith-john@domain.com
]

# Pattern to likelihood mapping (for quick lookup)
PATTERN_SCORES = {pattern: score for pattern, score in COMMON_PATTERNS}

# Valid pattern placeholders
VALID_PLACEHOLDERS = {
    '{first}', '{last}', '{f}', '{l}', '{ff}', '{ll}',
    '{fff}', '{lll}', '{first_initial}', '{last_initial}',
    '{first_2}', '{first_3}', '{last_2}', '{last_3}'
}

# Placeholder regex pattern
PLACEHOLDER_REGEX = re.compile(r'\{[a-z_0-9]+\}')


@dataclass
class PatternMatch:
    """Result of pattern detection."""
    pattern: str
    confidence: float
    match_count: int
    sample_emails: List[str]


def normalize_for_pattern(name: str) -> str:
    """
    Normalize name for pattern matching/application.

    - Lowercase
    - Remove special characters
    - Handle accents
    - Handle hyphenated names (keep first part)

    Args:
        name: Name to normalize

    Returns:
        Normalized name suitable for email local part
    """
    if not name or not isinstance(name, str):
        return ""

    # Lowercase
    result = name.lower().strip()

    # Remove Unicode accents/diacritics
    result = unicodedata.normalize('NFKD', result)
    result = ''.join(c for c in result if not unicodedata.combining(c))

    # Handle hyphenated names - take first part for email
    if '-' in result:
        result = result.split('-')[0]

    # Remove apostrophes (O'Brien -> OBrien)
    result = result.replace("'", "")

    # Keep only alphanumeric characters
    result = re.sub(r'[^a-z0-9]', '', result)

    return result


def extract_pattern_from_email(email: str, first_name: str,
                               last_name: str) -> Optional[str]:
    """
    Extract email pattern from a known email.

    Given: john.smith@domain.com, John, Smith
    Returns: {first}.{last}

    Args:
        email: Known email address
        first_name: Person's first name
        last_name: Person's last name

    Returns:
        Pattern string or None if not detected
    """
    if not email or '@' not in email:
        return None

    if not first_name or not last_name:
        return None

    local_part = email.split('@')[0].lower()
    first = normalize_for_pattern(first_name)
    last = normalize_for_pattern(last_name)

    if not first or not last:
        return None

    return detect_pattern_from_local_part(local_part, first, last)


def detect_pattern_from_local_part(local_part: str,
                                   first_name: str,
                                   last_name: str) -> Optional[str]:
    """
    Detect pattern from email local part (before @).

    Args:
        local_part: Email local part (already lowercased)
        first_name: Person's first name (already normalized)
        last_name: Person's last name (already normalized)

    Returns:
        Detected pattern or None
    """
    first = first_name.lower()
    last = last_name.lower()
    local = local_part.lower()

    # Get initials and substrings
    f = first[0] if first else ''
    l = last[0] if last else ''
    ff = first[:2] if len(first) >= 2 else first
    ll = last[:2] if len(last) >= 2 else last
    fff = first[:3] if len(first) >= 3 else first
    lll = last[:3] if len(last) >= 3 else last

    # Check patterns in order of likelihood (most common first)
    pattern_checks = [
        # {first}.{last} patterns
        (f"{first}.{last}", "{first}.{last}"),
        (f"{first}_{last}", "{first}_{last}"),
        (f"{first}-{last}", "{first}-{last}"),

        # {first}{last} patterns
        (f"{first}{last}", "{first}{last}"),

        # Initial patterns
        (f"{f}{last}", "{f}{last}"),
        (f"{f}.{last}", "{f}.{last}"),
        (f"{first}{l}", "{first}{l}"),
        (f"{first}.{l}", "{first}.{l}"),

        # Reverse patterns
        (f"{last}.{first}", "{last}.{first}"),
        (f"{last}{first}", "{last}{first}"),
        (f"{last}_{first}", "{last}_{first}"),
        (f"{last}-{first}", "{last}-{first}"),
        (f"{last}{f}", "{last}{f}"),
        (f"{last}.{f}", "{last}.{f}"),

        # First or last only
        (first, "{first}"),
        (last, "{last}"),

        # Double initial patterns
        (f"{ff}{last}", "{ff}{last}"),
        (f"{f}{l}{last}", "{f}{l}{last}"),
        (f"{first}{ll}", "{first}{ll}"),

        # Triple character patterns
        (f"{fff}{last}", "{fff}{last}"),
        (f"{first}{lll}", "{first}{lll}"),
    ]

    for generated, pattern in pattern_checks:
        if local == generated:
            return pattern

    return None


def detect_pattern_from_sample(email: str, first_name: str, last_name: str) -> Optional[str]:
    """
    Alias for extract_pattern_from_email for backward compatibility.
    """
    return extract_pattern_from_email(email, first_name, last_name)


def extract_patterns_from_multiple(emails: List[Dict[str, str]],
                                   domain: str) -> Optional[PatternMatch]:
    """
    Extract common pattern from multiple emails.

    Args:
        emails: List of dicts with email, first_name, last_name
        domain: Expected domain

    Returns:
        PatternMatch with most common pattern or None
    """
    if not emails:
        return None

    pattern_counts = Counter()
    sample_by_pattern: Dict[str, List[str]] = {}

    for record in emails:
        email = record.get('email', '')
        first_name = record.get('first_name', '')
        last_name = record.get('last_name', '')

        # Verify email matches expected domain
        if not email or '@' not in email:
            continue

        email_domain = email.split('@')[1].lower()
        if email_domain != domain.lower():
            continue

        pattern = extract_pattern_from_email(email, first_name, last_name)
        if pattern:
            pattern_counts[pattern] += 1
            if pattern not in sample_by_pattern:
                sample_by_pattern[pattern] = []
            sample_by_pattern[pattern].append(email)

    if not pattern_counts:
        return None

    # Get most common pattern
    most_common = pattern_counts.most_common(1)[0]
    pattern, count = most_common

    # Calculate confidence based on:
    # 1. How many emails matched this pattern
    # 2. Base likelihood of the pattern
    # 3. Consistency (ratio of matching to total)
    total_valid = sum(pattern_counts.values())
    consistency = count / total_valid if total_valid > 0 else 0

    base_likelihood = PATTERN_SCORES.get(pattern, 0.5)
    confidence = (base_likelihood * 0.5) + (consistency * 0.5)

    # Boost confidence if multiple matches
    if count >= 3:
        confidence = min(confidence + 0.1, 0.99)
    if count >= 5:
        confidence = min(confidence + 0.1, 0.99)

    return PatternMatch(
        pattern=pattern,
        confidence=round(confidence, 3),
        match_count=count,
        sample_emails=sample_by_pattern.get(pattern, [])[:5]
    )


def apply_pattern(pattern: str, first_name: str, last_name: str,
                  domain: str) -> Optional[str]:
    """
    Apply pattern to generate email address.

    Pattern placeholders:
    - {first} - Full first name
    - {last} - Full last name
    - {f} - First initial (1 char)
    - {l} - Last initial (1 char)
    - {ff} - First 2 chars of first name
    - {ll} - First 2 chars of last name
    - {fff} - First 3 chars of first name
    - {lll} - First 3 chars of last name

    Args:
        pattern: Email pattern
        first_name: Person's first name
        last_name: Person's last name
        domain: Company domain

    Returns:
        Generated email address or None if invalid input
    """
    if not pattern or not first_name or not last_name or not domain:
        return None

    first = normalize_for_pattern(first_name)
    last = normalize_for_pattern(last_name)

    if not first or not last:
        return None

    # Build replacement map
    replacements = {
        '{first}': first,
        '{last}': last,
        '{f}': first[0] if first else '',
        '{l}': last[0] if last else '',
        '{ff}': first[:2] if len(first) >= 2 else first,
        '{ll}': last[:2] if len(last) >= 2 else last,
        '{fff}': first[:3] if len(first) >= 3 else first,
        '{lll}': last[:3] if len(last) >= 3 else last,
        '{first_initial}': first[0] if first else '',
        '{last_initial}': last[0] if last else '',
        '{first_2}': first[:2] if len(first) >= 2 else first,
        '{first_3}': first[:3] if len(first) >= 3 else first,
        '{last_2}': last[:2] if len(last) >= 2 else last,
        '{last_3}': last[:3] if len(last) >= 3 else last,
    }

    local_part = pattern.lower()
    for placeholder, value in replacements.items():
        local_part = local_part.replace(placeholder, value)

    # Clean up any remaining placeholders (shouldn't happen with valid input)
    if '{' in local_part or '}' in local_part:
        return None

    # Normalize domain
    domain = domain.lower().strip()
    if domain.startswith('www.'):
        domain = domain[4:]

    return f"{local_part}@{domain}"


def generate_email_from_pattern(pattern: str, first_name: str, last_name: str,
                                 domain: str) -> Optional[str]:
    """Alias for apply_pattern for backward compatibility."""
    return apply_pattern(pattern, first_name, last_name, domain)


def validate_pattern_format(pattern: str) -> bool:
    """
    Validate that pattern string is valid.

    Valid patterns contain only allowed placeholders and separators.

    Args:
        pattern: Pattern string to validate

    Returns:
        True if valid pattern format
    """
    if not pattern:
        return False

    # Check for valid placeholders
    placeholders = PLACEHOLDER_REGEX.findall(pattern)

    if not placeholders:
        return False

    # All placeholders must be valid
    valid_set = {
        '{first}', '{last}', '{f}', '{l}', '{ff}', '{ll}',
        '{fff}', '{lll}', '{first_initial}', '{last_initial}',
        '{first_2}', '{first_3}', '{last_2}', '{last_3}'
    }

    for placeholder in placeholders:
        if placeholder not in valid_set:
            return False

    # Remaining characters (separators) must be valid
    remaining = PLACEHOLDER_REGEX.sub('', pattern)
    valid_separators = set('.-_')

    for char in remaining:
        if char not in valid_separators:
            return False

    return True


def get_pattern_placeholders(pattern: str) -> List[str]:
    """
    Extract placeholders from pattern string.

    Args:
        pattern: Pattern string

    Returns:
        List of placeholder names (without braces)
    """
    placeholders = PLACEHOLDER_REGEX.findall(pattern)
    return [p[1:-1] for p in placeholders]  # Remove { and }


def score_pattern_likelihood(pattern: str) -> float:
    """
    Score how likely a pattern is based on common patterns.

    More common patterns (like {first}.{last}) get higher scores.

    Args:
        pattern: Pattern to score

    Returns:
        Likelihood score 0.0-1.0
    """
    if not pattern:
        return 0.0

    # Direct lookup
    if pattern in PATTERN_SCORES:
        return PATTERN_SCORES[pattern]

    # Check if it's a variation
    pattern_lower = pattern.lower()

    # Check for similar patterns
    for known_pattern, score in COMMON_PATTERNS:
        if known_pattern == pattern_lower:
            return score

    # Default score for unknown patterns
    return 0.3


def rank_patterns_by_likelihood(patterns: List[str]) -> List[Tuple[str, float]]:
    """
    Rank patterns by their likelihood scores.

    Args:
        patterns: List of pattern strings

    Returns:
        List of (pattern, score) tuples, sorted by score descending
    """
    scored = [(p, score_pattern_likelihood(p)) for p in patterns]
    return sorted(scored, key=lambda x: x[1], reverse=True)


def extract_name_parts(full_name: str) -> Tuple[str, str]:
    """
    Extract first and last name from a full name string.

    Args:
        full_name: Full name string (e.g., "John Smith")

    Returns:
        Tuple of (first_name, last_name)
    """
    if not full_name or not isinstance(full_name, str):
        return ("", "")

    parts = full_name.strip().split()
    if len(parts) == 0:
        return ("", "")
    elif len(parts) == 1:
        return (parts[0], "")
    else:
        return (parts[0], parts[-1])


def suggest_patterns_for_domain(domain: str) -> List[Tuple[str, float]]:
    """
    Suggest likely patterns based on domain characteristics.

    Factors:
    - Industry (tech tends toward first.last)
    - TLD (.gov = formal, .io = casual)
    - Domain length (shorter = more casual)

    Args:
        domain: Company domain

    Returns:
        List of (pattern, likelihood) tuples, most likely first
    """
    if not domain:
        return COMMON_PATTERNS[:5]

    domain = domain.lower()
    tld = domain.split('.')[-1] if '.' in domain else ''

    # Start with base patterns
    suggestions = list(COMMON_PATTERNS)

    # Adjust based on TLD
    if tld in ['gov', 'edu', 'org']:
        # Formal organizations tend toward first.last
        suggestions = [
            ("{first}.{last}", 0.98),
            ("{f}.{last}", 0.85),
            ("{first}_{last}", 0.75),
            ("{first}{last}", 0.70),
        ] + suggestions

    elif tld in ['io', 'co', 'ai']:
        # Tech startups often use simpler patterns
        suggestions = [
            ("{first}", 0.90),
            ("{first}.{last}", 0.85),
            ("{first}{last}", 0.80),
            ("{f}{last}", 0.75),
        ] + suggestions

    elif tld in ['com', 'net']:
        # Standard commercial - use default order
        pass

    # Deduplicate while preserving order
    seen = set()
    unique_suggestions = []
    for pattern, score in suggestions:
        if pattern not in seen:
            seen.add(pattern)
            unique_suggestions.append((pattern, score))

    return unique_suggestions[:10]


def generate_all_pattern_variations(first_name: str, last_name: str,
                                     domain: str) -> List[str]:
    """
    Generate all possible email variations for a person.

    Useful for testing which email patterns might work.

    Args:
        first_name: Person's first name
        last_name: Person's last name
        domain: Company domain

    Returns:
        List of all possible email addresses
    """
    emails = []

    for pattern, _ in COMMON_PATTERNS:
        email = apply_pattern(pattern, first_name, last_name, domain)
        if email and email not in emails:
            emails.append(email)

    return emails


def infer_pattern_from_samples(sample_emails: List[str],
                               first_names: List[str],
                               last_names: List[str],
                               domain: str) -> Optional[PatternMatch]:
    """
    Infer email pattern from sample emails and name lists.

    Used when we have emails but don't know which names they belong to.
    Tries to match emails to names and detect pattern.

    Args:
        sample_emails: List of sample emails from the domain
        first_names: List of possible first names
        last_names: List of possible last names
        domain: Company domain

    Returns:
        PatternMatch if pattern detected, None otherwise
    """
    if not sample_emails or not first_names or not last_names:
        return None

    # Build name combinations
    name_pairs = []
    for first in first_names:
        for last in last_names:
            name_pairs.append((first, last))

    # Try to match each email
    matches = []
    for email in sample_emails:
        if '@' not in email:
            continue

        local_part = email.split('@')[0].lower()
        email_domain = email.split('@')[1].lower()

        if email_domain != domain.lower():
            continue

        for first, last in name_pairs:
            pattern = detect_pattern_from_local_part(
                local_part,
                normalize_for_pattern(first),
                normalize_for_pattern(last)
            )
            if pattern:
                matches.append({
                    'email': email,
                    'first_name': first,
                    'last_name': last
                })
                break

    if not matches:
        return None

    return extract_patterns_from_multiple(matches, domain)


def compare_patterns(pattern1: str, pattern2: str) -> bool:
    """
    Check if two patterns are equivalent.

    Handles different representations of the same pattern.

    Args:
        pattern1: First pattern
        pattern2: Second pattern

    Returns:
        True if patterns are equivalent
    """
    if not pattern1 or not pattern2:
        return False

    # Normalize both patterns
    p1 = pattern1.lower().strip()
    p2 = pattern2.lower().strip()

    if p1 == p2:
        return True

    # Check for equivalent placeholders
    equivalents = {
        '{first_initial}': '{f}',
        '{last_initial}': '{l}',
        '{first_2}': '{ff}',
        '{first_3}': '{fff}',
        '{last_2}': '{ll}',
        '{last_3}': '{lll}',
    }

    for old, new in equivalents.items():
        p1 = p1.replace(old, new)
        p2 = p2.replace(old, new)

    return p1 == p2


def pattern_to_readable(pattern: str) -> str:
    """
    Convert pattern to human-readable format.

    {first}.{last} -> "firstname.lastname"

    Args:
        pattern: Pattern string

    Returns:
        Human-readable description
    """
    readable_map = {
        '{first}': 'firstname',
        '{last}': 'lastname',
        '{f}': 'f',
        '{l}': 'l',
        '{ff}': 'fi',
        '{ll}': 'la',
        '{fff}': 'fir',
        '{lll}': 'las',
        '{first_initial}': 'f',
        '{last_initial}': 'l',
    }

    result = pattern.lower()
    for placeholder, readable in readable_map.items():
        result = result.replace(placeholder, readable)

    return result


def readable_to_pattern(readable: str) -> str:
    """
    Convert human-readable format back to pattern.

    "firstname.lastname" -> {first}.{last}

    Args:
        readable: Human-readable pattern

    Returns:
        Pattern string
    """
    # This is a best-effort conversion
    result = readable.lower()

    # Order matters - replace longer strings first
    replacements = [
        ('firstname', '{first}'),
        ('lastname', '{last}'),
        ('first', '{first}'),
        ('last', '{last}'),
    ]

    for old, new in replacements:
        result = result.replace(old, new)

    return result
