"""
Email and Domain Verification Utilities
=======================================
Tools 5 & 8: DNS/MX Validation and Email Verification Light

Implements deterministic verification per Pipeline Tool Doctrine:
- Tool 5: DNS/MX Validator (direct lookup)
- Tool 8: Email Verifier Light (DNS + SMTP handshake)

NO LLM ALLOWED - All verification is deterministic.
"""

import re
import socket
import smtplib
import dns.resolver
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class DomainHealthStatus(Enum):
    """Domain health status codes."""
    VALID = "valid"                    # Domain resolves, has MX records
    VALID_NO_MX = "valid_no_mx"        # Domain resolves, no MX (catch-all possible)
    PARKED = "parked"                  # Domain is parked/for sale
    UNREACHABLE = "unreachable"        # Domain doesn't resolve
    TIMEOUT = "timeout"                # DNS lookup timed out
    INVALID = "invalid"                # Invalid domain format
    ERROR = "error"                    # Unexpected error


class VerificationStatus(Enum):
    """Email verification status codes."""
    VALID = "valid"                    # Email is deliverable
    INVALID = "invalid"                # Email is not deliverable
    RISKY = "risky"                    # Email may be deliverable (catch-all)
    UNKNOWN = "unknown"                # Could not determine
    TIMEOUT = "timeout"                # Verification timed out
    ERROR = "error"                    # Unexpected error


class SMTPStatus(Enum):
    """SMTP verification status codes."""
    DELIVERABLE = "deliverable"        # 250 response
    UNDELIVERABLE = "undeliverable"    # 550/551/552/553 response
    CATCH_ALL = "catch_all"            # Server accepts all addresses
    GREYLISTED = "greylisted"          # Temporary rejection (try again)
    BLOCKED = "blocked"                # Server blocked our request
    TIMEOUT = "timeout"                # Connection timed out
    ERROR = "error"                    # Unexpected error


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class DomainVerificationResult:
    """Result of domain verification."""
    domain: str
    status: DomainHealthStatus
    has_dns: bool = False
    has_mx: bool = False
    mx_records: List[str] = field(default_factory=list)
    a_records: List[str] = field(default_factory=list)
    is_parked: bool = False
    parked_indicators: List[str] = field(default_factory=list)
    verification_time_ms: int = 0
    error_message: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def is_valid(self) -> bool:
        """Check if domain is valid for email."""
        return self.status in [DomainHealthStatus.VALID, DomainHealthStatus.VALID_NO_MX]


@dataclass
class VerificationResult:
    """Result of email verification."""
    email: str
    status: VerificationStatus
    is_valid: bool = False
    is_deliverable: Optional[bool] = None
    is_catch_all: bool = False
    is_role_based: bool = False
    is_disposable: bool = False
    smtp_status: Optional[SMTPStatus] = None
    smtp_response: Optional[str] = None
    mx_host: Optional[str] = None
    verification_time_ms: int = 0
    error_message: Optional[str] = None


# =============================================================================
# CONSTANTS
# =============================================================================

# Common parked domain indicators
PARKED_INDICATORS = [
    "parked", "for sale", "buy this domain", "domain parking",
    "godaddy", "sedoparking", "parkingcrew", "hugedomains",
    "dan.com", "afternic", "bodis", "undeveloped"
]

# Role-based email prefixes
ROLE_PREFIXES = [
    "info", "contact", "support", "sales", "admin", "help",
    "office", "team", "hello", "mail", "enquiries", "careers",
    "jobs", "hr", "marketing", "press", "media", "legal",
    "billing", "accounts", "webmaster", "postmaster", "abuse"
]

# Disposable email domains (subset)
DISPOSABLE_DOMAINS = [
    "mailinator.com", "guerrillamail.com", "10minutemail.com",
    "tempmail.com", "throwaway.email", "fakeinbox.com",
    "trashmail.com", "maildrop.cc", "yopmail.com"
]

# DNS timeout settings
DNS_TIMEOUT = 5.0
SMTP_TIMEOUT = 10.0


# =============================================================================
# TOOL 5: DNS/MX VALIDATOR
# =============================================================================

def verify_domain_dns(domain: str, timeout: float = DNS_TIMEOUT) -> bool:
    """
    Tool 5: Verify domain has valid DNS records.

    Args:
        domain: Domain to verify
        timeout: DNS lookup timeout in seconds

    Returns:
        True if domain resolves, False otherwise
    """
    if not domain or not _is_valid_domain_format(domain):
        return False

    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = timeout
        resolver.lifetime = timeout

        # Try A record first
        try:
            resolver.resolve(domain, 'A')
            return True
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            pass

        # Try AAAA record
        try:
            resolver.resolve(domain, 'AAAA')
            return True
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            pass

        # Try MX record (domain might only have mail)
        try:
            resolver.resolve(domain, 'MX')
            return True
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            pass

        return False

    except dns.resolver.Timeout:
        logger.warning(f"DNS timeout for domain: {domain}")
        return False
    except Exception as e:
        logger.error(f"DNS error for domain {domain}: {e}")
        return False


def verify_mx_records(domain: str, timeout: float = DNS_TIMEOUT) -> List[str]:
    """
    Tool 5: Get MX records for domain.

    Args:
        domain: Domain to check
        timeout: DNS lookup timeout in seconds

    Returns:
        List of MX hostnames (sorted by priority)
    """
    if not domain or not _is_valid_domain_format(domain):
        return []

    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = timeout
        resolver.lifetime = timeout

        answers = resolver.resolve(domain, 'MX')

        # Sort by priority (lower = higher priority)
        mx_records = sorted(
            [(r.preference, str(r.exchange).rstrip('.')) for r in answers],
            key=lambda x: x[0]
        )

        return [mx[1] for mx in mx_records]

    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        return []
    except dns.resolver.Timeout:
        logger.warning(f"MX lookup timeout for domain: {domain}")
        return []
    except Exception as e:
        logger.error(f"MX lookup error for domain {domain}: {e}")
        return []


def verify_domain_health(domain: str, timeout: float = DNS_TIMEOUT) -> DomainVerificationResult:
    """
    Tool 5: Comprehensive domain health check.

    Args:
        domain: Domain to verify
        timeout: DNS lookup timeout in seconds

    Returns:
        DomainVerificationResult with full details
    """
    start_time = time.time()

    # Initialize result
    result = DomainVerificationResult(
        domain=domain,
        status=DomainHealthStatus.INVALID
    )

    # Validate format
    if not domain or not _is_valid_domain_format(domain):
        result.error_message = "Invalid domain format"
        result.verification_time_ms = int((time.time() - start_time) * 1000)
        return result

    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = timeout
        resolver.lifetime = timeout

        # Check A records
        try:
            a_answers = resolver.resolve(domain, 'A')
            result.a_records = [str(r) for r in a_answers]
            result.has_dns = True
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            pass
        except dns.resolver.Timeout:
            result.status = DomainHealthStatus.TIMEOUT
            result.error_message = "DNS A record timeout"
            result.verification_time_ms = int((time.time() - start_time) * 1000)
            return result

        # Check MX records
        try:
            mx_answers = resolver.resolve(domain, 'MX')
            result.mx_records = sorted(
                [str(r.exchange).rstrip('.') for r in mx_answers],
                key=lambda x: next((r.preference for r in mx_answers if str(r.exchange).rstrip('.') == x), 99)
            )
            result.has_mx = len(result.mx_records) > 0
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            pass
        except dns.resolver.Timeout:
            pass

        # Determine status
        if not result.has_dns and not result.has_mx:
            result.status = DomainHealthStatus.UNREACHABLE
        elif result.has_mx:
            result.status = DomainHealthStatus.VALID
        else:
            result.status = DomainHealthStatus.VALID_NO_MX

        # Check for parked indicators (basic check)
        result.is_parked = _check_parked_domain(domain, result.a_records)
        if result.is_parked:
            result.status = DomainHealthStatus.PARKED

    except Exception as e:
        result.status = DomainHealthStatus.ERROR
        result.error_message = str(e)
        logger.error(f"Domain health check error for {domain}: {e}")

    result.verification_time_ms = int((time.time() - start_time) * 1000)
    return result


# =============================================================================
# TOOL 8: EMAIL VERIFIER LIGHT (DNS + SMTP)
# =============================================================================

def verify_email_format(email: str) -> bool:
    """
    Verify email format is valid.

    Args:
        email: Email address to verify

    Returns:
        True if format is valid
    """
    if not email:
        return False

    # RFC 5322 compliant regex (simplified)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.lower().strip()))


def smtp_check(
    email: str,
    mx_host: str = None,
    timeout: float = SMTP_TIMEOUT
) -> Tuple[SMTPStatus, Optional[str]]:
    """
    Tool 8: SMTP handshake verification.

    Performs RCPT TO check without sending actual email.

    Args:
        email: Email address to verify
        mx_host: MX host to connect to (auto-detected if None)
        timeout: SMTP connection timeout

    Returns:
        Tuple of (SMTPStatus, response_message)
    """
    if not verify_email_format(email):
        return (SMTPStatus.ERROR, "Invalid email format")

    domain = email.split('@')[1]

    # Get MX host if not provided
    if not mx_host:
        mx_records = verify_mx_records(domain)
        if not mx_records:
            return (SMTPStatus.ERROR, "No MX records found")
        mx_host = mx_records[0]

    try:
        # Connect to SMTP server
        smtp = smtplib.SMTP(timeout=timeout)
        smtp.connect(mx_host, 25)

        # Say hello
        code, msg = smtp.helo("verify.local")
        if code != 250:
            smtp.quit()
            return (SMTPStatus.BLOCKED, f"HELO rejected: {msg}")

        # Set sender (use generic address)
        code, msg = smtp.mail("verify@verify.local")
        if code != 250:
            smtp.quit()
            return (SMTPStatus.BLOCKED, f"MAIL FROM rejected: {msg}")

        # Check recipient
        code, msg = smtp.rcpt(email)
        smtp.quit()

        if code == 250:
            # Additional check: test invalid address to detect catch-all
            return _detect_catch_all(email, mx_host, timeout)
        elif code in [550, 551, 552, 553, 554]:
            return (SMTPStatus.UNDELIVERABLE, f"RCPT TO rejected: {msg}")
        elif code in [450, 451, 452]:
            return (SMTPStatus.GREYLISTED, f"Temporary rejection: {msg}")
        else:
            return (SMTPStatus.UNKNOWN, f"Unexpected response {code}: {msg}")

    except smtplib.SMTPConnectError:
        return (SMTPStatus.BLOCKED, "Connection refused")
    except socket.timeout:
        return (SMTPStatus.TIMEOUT, "Connection timed out")
    except Exception as e:
        logger.error(f"SMTP check error for {email}: {e}")
        return (SMTPStatus.ERROR, str(e))


def verify_email(
    email: str,
    check_smtp: bool = True,
    smtp_timeout: float = SMTP_TIMEOUT
) -> VerificationResult:
    """
    Tool 8: Complete email verification (light).

    Verification steps:
    1. Format validation
    2. Domain DNS check
    3. MX record check
    4. SMTP verification (optional)

    Args:
        email: Email address to verify
        check_smtp: Whether to perform SMTP check
        smtp_timeout: SMTP timeout in seconds

    Returns:
        VerificationResult with full details
    """
    start_time = time.time()

    result = VerificationResult(
        email=email,
        status=VerificationStatus.UNKNOWN
    )

    # Step 1: Format validation
    if not verify_email_format(email):
        result.status = VerificationStatus.INVALID
        result.error_message = "Invalid email format"
        result.verification_time_ms = int((time.time() - start_time) * 1000)
        return result

    email = email.lower().strip()
    local_part, domain = email.split('@')

    # Check for role-based email
    result.is_role_based = local_part.lower() in ROLE_PREFIXES

    # Check for disposable domain
    result.is_disposable = domain.lower() in DISPOSABLE_DOMAINS
    if result.is_disposable:
        result.status = VerificationStatus.INVALID
        result.error_message = "Disposable email domain"
        result.verification_time_ms = int((time.time() - start_time) * 1000)
        return result

    # Step 2: Domain DNS check
    if not verify_domain_dns(domain):
        result.status = VerificationStatus.INVALID
        result.error_message = "Domain does not resolve"
        result.verification_time_ms = int((time.time() - start_time) * 1000)
        return result

    # Step 3: MX record check
    mx_records = verify_mx_records(domain)
    if not mx_records:
        result.status = VerificationStatus.RISKY
        result.error_message = "No MX records (may use A record for mail)"
        result.verification_time_ms = int((time.time() - start_time) * 1000)
        return result

    result.mx_host = mx_records[0]

    # Step 4: SMTP verification (if enabled)
    if check_smtp:
        smtp_status, smtp_response = smtp_check(email, result.mx_host, smtp_timeout)
        result.smtp_status = smtp_status
        result.smtp_response = smtp_response

        if smtp_status == SMTPStatus.DELIVERABLE:
            result.status = VerificationStatus.VALID
            result.is_valid = True
            result.is_deliverable = True
        elif smtp_status == SMTPStatus.CATCH_ALL:
            result.status = VerificationStatus.RISKY
            result.is_catch_all = True
            result.is_deliverable = True  # Likely deliverable
        elif smtp_status == SMTPStatus.UNDELIVERABLE:
            result.status = VerificationStatus.INVALID
            result.is_valid = False
            result.is_deliverable = False
        elif smtp_status == SMTPStatus.GREYLISTED:
            result.status = VerificationStatus.RISKY
            # Greylisting is temporary, email likely valid
        elif smtp_status == SMTPStatus.TIMEOUT:
            result.status = VerificationStatus.UNKNOWN
            result.error_message = "SMTP timeout"
        else:
            result.status = VerificationStatus.UNKNOWN
    else:
        # Without SMTP check, assume valid if MX exists
        result.status = VerificationStatus.RISKY
        result.is_valid = True

    result.verification_time_ms = int((time.time() - start_time) * 1000)
    return result


def bulk_verify(
    emails: List[str],
    check_smtp: bool = True,
    max_workers: int = 10,
    smtp_timeout: float = SMTP_TIMEOUT
) -> List[VerificationResult]:
    """
    Bulk verify multiple email addresses.

    Args:
        emails: List of email addresses
        check_smtp: Whether to perform SMTP checks
        max_workers: Maximum concurrent verifications
        smtp_timeout: SMTP timeout per email

    Returns:
        List of VerificationResult objects
    """
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(verify_email, email, check_smtp, smtp_timeout): email
            for email in emails
        }

        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                email = futures[future]
                results.append(VerificationResult(
                    email=email,
                    status=VerificationStatus.ERROR,
                    error_message=str(e)
                ))

    return results


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _is_valid_domain_format(domain: str) -> bool:
    """Check if domain format is valid."""
    if not domain:
        return False

    # Basic domain format check
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain.lower().strip()))


def _check_parked_domain(domain: str, a_records: List[str]) -> bool:
    """
    Check if domain appears to be parked.

    This is a basic check - for production, consider using
    a dedicated parked domain detection service.
    """
    # Known parking service IPs (subset)
    parking_ips = {
        "52.119.104.167",   # Sedo
        "208.91.197.27",    # Bodis
        "66.96.162.92",     # GoDaddy
    }

    # Check if any A records match parking IPs
    for ip in a_records:
        if ip in parking_ips:
            return True

    return False


def _detect_catch_all(
    email: str,
    mx_host: str,
    timeout: float = SMTP_TIMEOUT
) -> Tuple[SMTPStatus, Optional[str]]:
    """
    Detect if server is catch-all by testing invalid address.
    """
    import random
    import string

    domain = email.split('@')[1]

    # Generate random invalid address
    random_local = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
    test_email = f"{random_local}@{domain}"

    try:
        smtp = smtplib.SMTP(timeout=timeout)
        smtp.connect(mx_host, 25)
        smtp.helo("verify.local")
        smtp.mail("verify@verify.local")

        code, msg = smtp.rcpt(test_email)
        smtp.quit()

        if code == 250:
            # Server accepts invalid address - catch-all
            return (SMTPStatus.CATCH_ALL, "Server accepts all addresses")
        else:
            # Server rejected invalid address - original email is deliverable
            return (SMTPStatus.DELIVERABLE, "Email verified")

    except Exception:
        # If detection fails, assume deliverable
        return (SMTPStatus.DELIVERABLE, "Email likely valid")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "DomainHealthStatus",
    "VerificationStatus",
    "SMTPStatus",
    # Data classes
    "DomainVerificationResult",
    "VerificationResult",
    # Tool 5: DNS/MX Validator
    "verify_domain_dns",
    "verify_mx_records",
    "verify_domain_health",
    # Tool 8: Email Verifier Light
    "verify_email_format",
    "smtp_check",
    "verify_email",
    "bulk_verify",
]
