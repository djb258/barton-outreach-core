"""
Verification Module
===================
Email pattern and domain verification utilities.
"""

from .patterns import (
    COMMON_PATTERNS,
    PATTERN_SCORES,
    apply_pattern,
    validate_pattern_format,
    detect_pattern_from_sample,
    generate_email_from_pattern,
    rank_patterns_by_likelihood,
    extract_name_parts,
)

from .verification import (
    DomainHealthStatus,
    VerificationStatus,
    DomainHealth,
    EmailVerificationResult,
    verify_domain_health,
    verify_email_deliverable,
    batch_verify_domains,
    batch_verify_emails,
    check_mx_records,
    check_catch_all,
)

__all__ = [
    # patterns
    "COMMON_PATTERNS",
    "PATTERN_SCORES",
    "apply_pattern",
    "validate_pattern_format",
    "detect_pattern_from_sample",
    "generate_email_from_pattern",
    "rank_patterns_by_likelihood",
    "extract_name_parts",
    # verification
    "DomainHealthStatus",
    "VerificationStatus",
    "DomainHealth",
    "EmailVerificationResult",
    "verify_domain_health",
    "verify_email_deliverable",
    "batch_verify_domains",
    "batch_verify_emails",
    "check_mx_records",
    "check_catch_all",
]
