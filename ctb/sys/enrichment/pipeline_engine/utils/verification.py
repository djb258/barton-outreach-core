"""
Email Verification Utilities
============================
Email and domain verification functions.
MX lookup, SMTP verification, domain health checks.
"""

import re
import socket
import smtplib
import logging
import dns.resolver
import dns.exception
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed


class VerificationStatus(Enum):
    """Email verification status."""
    VALID = "valid"           # Email exists and can receive mail
    INVALID = "invalid"       # Email definitely doesn't exist
    UNKNOWN = "unknown"       # Could not determine (timeout, error)
    RISKY = "risky"           # Email might not exist (catch-all, etc.)
    CATCH_ALL = "catch_all"   # Domain accepts all emails


class DomainHealthStatus(Enum):
    """Domain health status."""
    HEALTHY = "healthy"       # MX records valid, responsive
    DEGRADED = "degraded"     # Some issues but may work
    UNHEALTHY = "unhealthy"   # Major issues
    PARKED = "parked"         # Domain parked/for sale
    DEAD = "dead"             # No DNS records


@dataclass
class VerificationResult:
    """Result of email verification."""
    email: str
    status: VerificationStatus
    format_valid: bool = False
    domain_valid: bool = False
    mx_found: bool = False
    smtp_check: Optional[bool] = None
    is_catch_all: bool = False
    is_disposable: bool = False
    is_role_based: bool = False
    confidence: float = 0.0
    mx_records: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


@dataclass
class DomainVerificationResult:
    """Result of domain verification."""
    domain: str
    status: DomainHealthStatus
    has_mx: bool = False
    has_a_record: bool = False
    has_website: bool = False
    mx_records: List[str] = field(default_factory=list)
    a_records: List[str] = field(default_factory=list)
    is_catch_all: bool = False
    is_parked: bool = False
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None


# Disposable email domains (partial list - expand as needed)
DISPOSABLE_DOMAINS = {
    'mailinator.com', 'guerrillamail.com', 'tempmail.com', 'throwaway.email',
    '10minutemail.com', 'fakeinbox.com', 'trashmail.com', 'getnada.com',
    'sharklasers.com', 'maildrop.cc', 'dispostable.com', 'yopmail.com',
    'temp-mail.org', 'mintemail.com', 'mytemp.email', 'mohmal.com'
}

# Role-based email prefixes
ROLE_BASED_PREFIXES = {
    'info', 'admin', 'support', 'sales', 'help', 'contact', 'office',
    'service', 'webmaster', 'postmaster', 'hostmaster', 'abuse',
    'noreply', 'no-reply', 'mailer-daemon', 'marketing', 'billing',
    'feedback', 'team', 'hr', 'careers', 'jobs', 'press', 'media',
    'legal', 'compliance', 'privacy', 'security', 'accounting',
    'newsletter', 'subscribe', 'unsubscribe', 'orders', 'invoice'
}

# Parked domain indicators
PARKED_INDICATORS = [
    'parked', 'for sale', 'buy this domain', 'domain parking',
    'this domain is for sale', 'domain may be for sale',
    'hugedomains', 'godaddy', 'sedo', 'afternic', 'dan.com'
]

logger = logging.getLogger(__name__)


def verify_email_format(email: str) -> bool:
    """
    Verify email has valid format.

    Checks:
    - Contains exactly one @
    - Local part is valid (1-64 chars, valid chars)
    - Domain part is valid (1-255 chars, valid format)
    - Overall length is reasonable

    Args:
        email: Email to verify

    Returns:
        True if format is valid
    """
    if not email or not isinstance(email, str):
        return False

    email = email.strip().lower()

    # Basic length check
    if len(email) > 254 or len(email) < 3:
        return False

    # Must have exactly one @
    if email.count('@') != 1:
        return False

    local_part, domain_part = email.rsplit('@', 1)

    # Local part validation
    if not local_part or len(local_part) > 64:
        return False

    # Domain part validation
    if not domain_part or len(domain_part) > 253:
        return False

    # Must have at least one dot in domain
    if '.' not in domain_part:
        return False

    # Check for consecutive dots
    if '..' in email:
        return False

    # Regex for more detailed validation
    email_pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    return bool(email_pattern.match(email))


def verify_mx_records(domain: str, timeout: float = 5.0) -> List[str]:
    """
    Get MX records for domain.

    Args:
        domain: Domain to check
        timeout: DNS query timeout

    Returns:
        List of MX server hostnames (sorted by priority)
    """
    if not domain:
        return []

    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = timeout
        resolver.lifetime = timeout

        mx_records = resolver.resolve(domain, 'MX')

        # Sort by priority (lower = higher priority)
        sorted_records = sorted(mx_records, key=lambda r: r.preference)

        return [str(r.exchange).rstrip('.') for r in sorted_records]

    except dns.resolver.NXDOMAIN:
        logger.debug(f"Domain {domain} does not exist")
        return []
    except dns.resolver.NoAnswer:
        logger.debug(f"No MX records for {domain}")
        return []
    except dns.resolver.Timeout:
        logger.warning(f"DNS timeout for {domain}")
        return []
    except dns.exception.DNSException as e:
        logger.error(f"DNS error for {domain}: {e}")
        return []


def verify_a_records(domain: str, timeout: float = 5.0) -> List[str]:
    """
    Get A records for domain.

    Args:
        domain: Domain to check
        timeout: DNS query timeout

    Returns:
        List of IP addresses
    """
    if not domain:
        return []

    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = timeout
        resolver.lifetime = timeout

        a_records = resolver.resolve(domain, 'A')
        return [str(r) for r in a_records]

    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
        return []
    except dns.exception.DNSException:
        return []


def verify_domain_dns(domain: str, timeout: float = 5.0) -> Dict[str, Any]:
    """
    Verify domain has valid DNS records.

    Checks:
    - MX records exist
    - A records exist
    - Domain resolves

    Args:
        domain: Domain to verify
        timeout: DNS query timeout

    Returns:
        Dict with DNS verification results
    """
    if not domain:
        return {
            'valid': False,
            'mx_records': [],
            'a_records': [],
            'has_mx': False,
            'has_a': False,
            'error': 'No domain provided'
        }

    domain = domain.lower().strip()

    # Remove any protocol or www prefix
    if domain.startswith('http://'):
        domain = domain[7:]
    if domain.startswith('https://'):
        domain = domain[8:]
    if domain.startswith('www.'):
        domain = domain[4:]

    # Remove trailing slash
    domain = domain.rstrip('/')

    mx_records = verify_mx_records(domain, timeout)
    a_records = verify_a_records(domain, timeout)

    return {
        'valid': bool(mx_records) or bool(a_records),
        'mx_records': mx_records,
        'a_records': a_records,
        'has_mx': bool(mx_records),
        'has_a': bool(a_records),
        'domain': domain,
        'error': None
    }


def smtp_check(email: str, timeout: int = 10,
               from_email: str = "verify@example.com") -> Tuple[Optional[bool], str]:
    """
    Verify email via SMTP handshake.

    WARNING: Can be slow and may be rate-limited.
    Should only be used for spot-checking.

    Steps:
    1. Connect to MX server
    2. Send HELO
    3. Send MAIL FROM
    4. Send RCPT TO
    5. Check response

    Args:
        email: Email to verify
        timeout: Connection timeout in seconds
        from_email: Email to use in MAIL FROM

    Returns:
        Tuple of (result, message)
        - True if valid
        - False if invalid
        - None if unknown/error
    """
    if not verify_email_format(email):
        return (False, "Invalid email format")

    domain = email.split('@')[1]
    mx_records = verify_mx_records(domain)

    if not mx_records:
        return (None, "No MX records found")

    # Try each MX server
    for mx_host in mx_records[:3]:  # Try top 3 MX servers
        try:
            # Connect to SMTP server
            smtp = smtplib.SMTP(timeout=timeout)
            smtp.set_debuglevel(0)

            code, message = smtp.connect(mx_host, 25)
            if code != 220:
                smtp.quit()
                continue

            # HELO
            smtp.helo('verify.local')

            # MAIL FROM
            code, message = smtp.mail(from_email)
            if code != 250:
                smtp.quit()
                continue

            # RCPT TO - this is where we check if email exists
            code, message = smtp.rcpt(email)
            smtp.quit()

            if code == 250:
                return (True, "Email accepted by server")
            elif code == 550:
                return (False, "Email rejected - user unknown")
            elif code == 552:
                return (False, "Email rejected - mailbox full")
            elif code == 553:
                return (False, "Email rejected - invalid")
            else:
                return (None, f"Unexpected response: {code}")

        except socket.timeout:
            logger.warning(f"SMTP timeout connecting to {mx_host}")
            continue
        except smtplib.SMTPServerDisconnected:
            continue
        except smtplib.SMTPConnectError:
            continue
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            continue

    return (None, "Could not verify - all MX servers failed")


def is_catch_all_domain(domain: str, timeout: int = 10) -> bool:
    """
    Check if domain accepts all emails (catch-all).

    Catch-all domains will accept any email, so verification
    cannot confirm if specific email exists.

    Args:
        domain: Domain to check
        timeout: SMTP timeout

    Returns:
        True if catch-all domain
    """
    if not domain:
        return False

    # Generate a random email that shouldn't exist
    import uuid
    random_email = f"test_{uuid.uuid4().hex[:8]}_invalid@{domain}"

    result, _ = smtp_check(random_email, timeout)

    # If random email is accepted, it's a catch-all
    return result is True


def is_disposable_domain(domain: str) -> bool:
    """
    Check if domain is a disposable email provider.

    Args:
        domain: Domain to check

    Returns:
        True if disposable domain
    """
    if not domain:
        return False

    domain = domain.lower().strip()

    # Direct match
    if domain in DISPOSABLE_DOMAINS:
        return True

    # Check subdomain
    parts = domain.split('.')
    if len(parts) >= 2:
        root_domain = '.'.join(parts[-2:])
        if root_domain in DISPOSABLE_DOMAINS:
            return True

    return False


def is_role_based_email(email: str) -> bool:
    """
    Check if email is role-based (not personal).

    Role-based: info@, support@, admin@, sales@, etc.

    Args:
        email: Email to check

    Returns:
        True if role-based
    """
    if not email or '@' not in email:
        return False

    local_part = email.split('@')[0].lower()

    # Check against known prefixes
    if local_part in ROLE_BASED_PREFIXES:
        return True

    # Check for common patterns
    for prefix in ROLE_BASED_PREFIXES:
        if local_part.startswith(prefix + '.') or local_part.startswith(prefix + '_'):
            return True

    return False


def verify_email(email: str, check_smtp: bool = False,
                 smtp_timeout: int = 10) -> VerificationResult:
    """
    Comprehensive email verification.

    Args:
        email: Email to verify
        check_smtp: Whether to perform SMTP verification (slow)
        smtp_timeout: SMTP check timeout

    Returns:
        VerificationResult with all checks
    """
    result = VerificationResult(
        email=email,
        status=VerificationStatus.UNKNOWN,
        confidence=0.0
    )

    # Format check
    result.format_valid = verify_email_format(email)
    if not result.format_valid:
        result.status = VerificationStatus.INVALID
        result.confidence = 1.0
        result.error_message = "Invalid email format"
        return result

    # Extract domain
    domain = email.split('@')[1].lower()

    # Check disposable
    result.is_disposable = is_disposable_domain(domain)
    if result.is_disposable:
        result.status = VerificationStatus.RISKY
        result.confidence = 0.9
        result.error_message = "Disposable email domain"
        return result

    # Check role-based
    result.is_role_based = is_role_based_email(email)

    # DNS verification
    dns_result = verify_domain_dns(domain)
    result.domain_valid = dns_result['valid']
    result.mx_found = dns_result['has_mx']
    result.mx_records = dns_result['mx_records']

    if not result.mx_found:
        result.status = VerificationStatus.INVALID
        result.confidence = 0.95
        result.error_message = "No MX records found"
        return result

    # SMTP check (optional)
    if check_smtp:
        smtp_result, smtp_message = smtp_check(email, smtp_timeout)
        result.smtp_check = smtp_result

        if smtp_result is True:
            result.status = VerificationStatus.VALID
            result.confidence = 0.95
        elif smtp_result is False:
            result.status = VerificationStatus.INVALID
            result.confidence = 0.9
            result.error_message = smtp_message
        else:
            result.status = VerificationStatus.UNKNOWN
            result.confidence = 0.5
            result.error_message = smtp_message
    else:
        # Without SMTP, best we can do is confirm domain
        result.status = VerificationStatus.UNKNOWN
        result.confidence = 0.6

    # Adjust confidence for role-based
    if result.is_role_based:
        result.confidence = max(result.confidence - 0.1, 0.0)

    return result


def bulk_verify(emails: List[str], use_smtp: bool = False,
                max_concurrent: int = 10) -> List[VerificationResult]:
    """
    Bulk verify multiple emails.

    Args:
        emails: List of emails to verify
        use_smtp: Whether to perform SMTP checks
        max_concurrent: Maximum concurrent verifications

    Returns:
        List of VerificationResult for each email
    """
    if not emails:
        return []

    results = []

    with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        future_to_email = {
            executor.submit(verify_email, email, use_smtp): email
            for email in emails
        }

        for future in as_completed(future_to_email):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                email = future_to_email[future]
                results.append(VerificationResult(
                    email=email,
                    status=VerificationStatus.UNKNOWN,
                    error_message=str(e)
                ))

    return results


def verify_domain_health(domain: str, timeout: float = 10.0) -> DomainVerificationResult:
    """
    Comprehensive domain health check.

    Args:
        domain: Domain to check
        timeout: Overall timeout

    Returns:
        DomainVerificationResult with health status
    """
    result = DomainVerificationResult(
        domain=domain,
        status=DomainHealthStatus.UNHEALTHY
    )

    if not domain:
        result.error_message = "No domain provided"
        return result

    # DNS checks
    dns_result = verify_domain_dns(domain, timeout / 2)
    result.has_mx = dns_result['has_mx']
    result.has_a_record = dns_result['has_a']
    result.mx_records = dns_result['mx_records']
    result.a_records = dns_result['a_records']

    # Determine status
    if not result.has_mx and not result.has_a_record:
        result.status = DomainHealthStatus.DEAD
        result.error_message = "No DNS records found"
        return result

    if result.has_mx:
        result.status = DomainHealthStatus.HEALTHY
    elif result.has_a_record:
        result.status = DomainHealthStatus.DEGRADED
        result.error_message = "No MX records, only A records"

    return result


def calculate_email_risk_score(result: VerificationResult) -> float:
    """
    Calculate risk score for email.

    Lower score = safer to send
    Higher score = more risk

    Factors:
    - Verification status
    - Catch-all status
    - Disposable domain
    - Role-based

    Args:
        result: Verification result

    Returns:
        Risk score 0.0-1.0 (lower is better)
    """
    risk_score = 0.0

    # Base risk by status
    status_risk = {
        VerificationStatus.VALID: 0.1,
        VerificationStatus.INVALID: 1.0,
        VerificationStatus.UNKNOWN: 0.5,
        VerificationStatus.RISKY: 0.7,
        VerificationStatus.CATCH_ALL: 0.4,
    }
    risk_score = status_risk.get(result.status, 0.5)

    # Additional factors
    if result.is_disposable:
        risk_score = min(risk_score + 0.3, 1.0)

    if result.is_role_based:
        risk_score = min(risk_score + 0.1, 1.0)

    if result.is_catch_all:
        risk_score = min(risk_score + 0.2, 1.0)

    if not result.format_valid:
        risk_score = 1.0

    if not result.mx_found:
        risk_score = min(risk_score + 0.3, 1.0)

    return round(risk_score, 3)


def verify_pattern_with_sample(pattern: str, sample_email: str,
                               first_name: str, last_name: str,
                               domain: str) -> Tuple[bool, float]:
    """
    Verify that a pattern produces a valid email when applied to a sample.

    Args:
        pattern: Email pattern to test
        sample_email: Known valid email for comparison
        first_name: First name to use with pattern
        last_name: Last name to use with pattern
        domain: Company domain

    Returns:
        Tuple of (pattern_matches, confidence)
    """
    # Import here to avoid circular dependency
    from .patterns import apply_pattern

    generated = apply_pattern(pattern, first_name, last_name, domain)

    if not generated:
        return (False, 0.0)

    # Check if generated matches sample
    if generated.lower() == sample_email.lower():
        return (True, 1.0)

    return (False, 0.0)


def get_mx_provider(mx_records: List[str]) -> Optional[str]:
    """
    Identify email provider from MX records.

    Args:
        mx_records: List of MX record hostnames

    Returns:
        Provider name or None if unknown
    """
    if not mx_records:
        return None

    # Common provider patterns
    providers = {
        'google': ['google.com', 'googlemail.com', 'aspmx.l.google.com'],
        'microsoft': ['outlook.com', 'protection.outlook.com', 'mail.protection.outlook.com'],
        'amazon_ses': ['amazonses.com', 'inbound-smtp.us-east-1.amazonaws.com'],
        'proofpoint': ['pphosted.com', 'proofpoint.com'],
        'mimecast': ['mimecast.com'],
        'barracuda': ['barracudanetworks.com'],
        'zoho': ['zoho.com'],
        'fastmail': ['fastmail.com'],
        'rackspace': ['emailsrvr.com'],
    }

    mx_lower = [mx.lower() for mx in mx_records]

    for provider, patterns in providers.items():
        for pattern in patterns:
            for mx in mx_lower:
                if pattern in mx:
                    return provider

    return 'unknown'
