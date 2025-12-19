"""
Standardized Error Codes Module
================================
DOCTRINE: All errors must use PRD-compliant error codes.

Error Code Format: {SPOKE}-{PHASE}-{SEQUENCE}
- SPOKE: Component identifier (PSH=People Spoke Hub, DOL=DOL Spoke, HUB=Company Hub)
- PHASE: Phase number (P0-P8) or category (GEN=General)
- SEQUENCE: 3-digit sequence number

Examples:
- PSH-P0-001: People Spoke Phase 0, error #001
- DOL-GEN-001: DOL Spoke general error #001
- HUB-P1-001: Company Hub Phase 1, error #001
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional


class ErrorSeverity(Enum):
    """Error severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ErrorDefinition:
    """Definition of an error code."""
    code: str
    message: str
    severity: ErrorSeverity
    recoverable: bool
    category: str
    details: str = ""


# ============================================================================
# COMPANY HUB ERROR CODES (HUB-*)
# ============================================================================
class HubErrorCodes:
    """Company Hub error codes."""

    # Phase 1: Company Matching
    HUB_P1_001 = ErrorDefinition(
        code="HUB-P1-001",
        message="Company matching failed - no correlation_id",
        severity=ErrorSeverity.CRITICAL,
        recoverable=False,
        category="correlation_id",
        details="Phase 1 requires correlation_id per Barton Doctrine"
    )
    HUB_P1_002 = ErrorDefinition(
        code="HUB-P1-002",
        message="Company matching failed - invalid input data",
        severity=ErrorSeverity.ERROR,
        recoverable=True,
        category="validation"
    )
    HUB_P1_003 = ErrorDefinition(
        code="HUB-P1-003",
        message="Company matching failed - no company found",
        severity=ErrorSeverity.WARNING,
        recoverable=True,
        category="matching"
    )

    # Phase 2: Domain Resolution
    HUB_P2_001 = ErrorDefinition(
        code="HUB-P2-001",
        message="Domain resolution failed - no correlation_id",
        severity=ErrorSeverity.CRITICAL,
        recoverable=False,
        category="correlation_id"
    )
    HUB_P2_002 = ErrorDefinition(
        code="HUB-P2-002",
        message="Domain resolution failed - invalid domain format",
        severity=ErrorSeverity.ERROR,
        recoverable=True,
        category="validation"
    )

    # Phase 3: Email Pattern Waterfall
    HUB_P3_001 = ErrorDefinition(
        code="HUB-P3-001",
        message="Pattern waterfall failed - no correlation_id",
        severity=ErrorSeverity.CRITICAL,
        recoverable=False,
        category="correlation_id"
    )
    HUB_P3_002 = ErrorDefinition(
        code="HUB-P3-002",
        message="Pattern waterfall failed - no provider available",
        severity=ErrorSeverity.ERROR,
        recoverable=True,
        category="provider"
    )

    # Phase 4: Pattern Verification
    HUB_P4_001 = ErrorDefinition(
        code="HUB-P4-001",
        message="Pattern verification failed - no correlation_id",
        severity=ErrorSeverity.CRITICAL,
        recoverable=False,
        category="correlation_id"
    )
    HUB_P4_002 = ErrorDefinition(
        code="HUB-P4-002",
        message="Pattern verification failed - invalid pattern format",
        severity=ErrorSeverity.ERROR,
        recoverable=True,
        category="validation"
    )


# ============================================================================
# PEOPLE SPOKE ERROR CODES (PSH-*)
# ============================================================================
class PeopleErrorCodes:
    """People Spoke Hub error codes."""

    # Phase 0: People Ingest
    PSH_P0_001 = ErrorDefinition(
        code="PSH-P0-001",
        message="People ingest failed - no correlation_id",
        severity=ErrorSeverity.CRITICAL,
        recoverable=False,
        category="correlation_id",
        details="Phase 0 requires correlation_id per Barton Doctrine"
    )
    PSH_P0_002 = ErrorDefinition(
        code="PSH-P0-002",
        message="People ingest failed - hub gate validation failed",
        severity=ErrorSeverity.WARNING,
        recoverable=True,
        category="hub_gate",
        details="Record lacks company anchor, classified as SUSPECT"
    )
    PSH_P0_003 = ErrorDefinition(
        code="PSH-P0-003",
        message="People ingest failed - missing required fields",
        severity=ErrorSeverity.ERROR,
        recoverable=True,
        category="validation"
    )

    # Phase 5: Email Generation
    PSH_P5_001 = ErrorDefinition(
        code="PSH-P5-001",
        message="Email generation failed - no correlation_id",
        severity=ErrorSeverity.CRITICAL,
        recoverable=False,
        category="correlation_id"
    )
    PSH_P5_002 = ErrorDefinition(
        code="PSH-P5-002",
        message="Email generation failed - no pattern for company",
        severity=ErrorSeverity.WARNING,
        recoverable=True,
        category="pattern"
    )
    PSH_P5_003 = ErrorDefinition(
        code="PSH-P5-003",
        message="Email generation failed - hub gate validation failed",
        severity=ErrorSeverity.ERROR,
        recoverable=True,
        category="hub_gate"
    )

    # Phase 6: Slot Assignment
    PSH_P6_001 = ErrorDefinition(
        code="PSH-P6-001",
        message="Slot assignment failed - no correlation_id",
        severity=ErrorSeverity.CRITICAL,
        recoverable=False,
        category="correlation_id"
    )
    PSH_P6_002 = ErrorDefinition(
        code="PSH-P6-002",
        message="Slot assignment failed - hub gate validation failed",
        severity=ErrorSeverity.ERROR,
        recoverable=True,
        category="hub_gate"
    )
    PSH_P6_003 = ErrorDefinition(
        code="PSH-P6-003",
        message="Slot assignment failed - title not recognized",
        severity=ErrorSeverity.WARNING,
        recoverable=True,
        category="classification"
    )

    # Phase 7: Enrichment Queue
    PSH_P7_001 = ErrorDefinition(
        code="PSH-P7-001",
        message="Enrichment queue failed - no correlation_id",
        severity=ErrorSeverity.CRITICAL,
        recoverable=False,
        category="correlation_id"
    )
    PSH_P7_002 = ErrorDefinition(
        code="PSH-P7-002",
        message="Enrichment queue failed - waterfall exhausted",
        severity=ErrorSeverity.WARNING,
        recoverable=True,
        category="enrichment"
    )

    # Phase 8: Output Writer
    PSH_P8_001 = ErrorDefinition(
        code="PSH-P8-001",
        message="Output writer failed - no correlation_id",
        severity=ErrorSeverity.CRITICAL,
        recoverable=False,
        category="correlation_id"
    )
    PSH_P8_002 = ErrorDefinition(
        code="PSH-P8-002",
        message="Output writer failed - file write error",
        severity=ErrorSeverity.ERROR,
        recoverable=True,
        category="io"
    )


# ============================================================================
# DOL SPOKE ERROR CODES (DOL-*)
# ============================================================================
class DOLErrorCodes:
    """DOL Spoke error codes."""

    # General
    DOL_GEN_001 = ErrorDefinition(
        code="DOL-GEN-001",
        message="DOL processing failed - no correlation_id",
        severity=ErrorSeverity.CRITICAL,
        recoverable=False,
        category="correlation_id"
    )
    DOL_GEN_002 = ErrorDefinition(
        code="DOL-GEN-002",
        message="DOL processing failed - hub gate validation failed",
        severity=ErrorSeverity.ERROR,
        recoverable=True,
        category="hub_gate"
    )

    # EIN Matching
    DOL_EIN_001 = ErrorDefinition(
        code="DOL-EIN-001",
        message="EIN lookup failed - no EIN in record",
        severity=ErrorSeverity.WARNING,
        recoverable=True,
        category="ein"
    )
    DOL_EIN_002 = ErrorDefinition(
        code="DOL-EIN-002",
        message="EIN lookup failed - invalid EIN format",
        severity=ErrorSeverity.WARNING,
        recoverable=True,
        category="ein"
    )
    DOL_EIN_003 = ErrorDefinition(
        code="DOL-EIN-003",
        message="EIN lookup failed - no company found for EIN",
        severity=ErrorSeverity.WARNING,
        recoverable=True,
        category="ein"
    )

    # Form 5500
    DOL_5500_001 = ErrorDefinition(
        code="DOL-5500-001",
        message="Form 5500 processing failed - invalid record",
        severity=ErrorSeverity.ERROR,
        recoverable=True,
        category="form_5500"
    )

    # Schedule A
    DOL_SCHA_001 = ErrorDefinition(
        code="DOL-SCHA-001",
        message="Schedule A processing failed - invalid record",
        severity=ErrorSeverity.ERROR,
        recoverable=True,
        category="schedule_a"
    )


# ============================================================================
# DOCTRINE ENFORCEMENT ERROR CODES (ENF-*)
# ============================================================================
class EnforcementErrorCodes:
    """Doctrine enforcement error codes."""

    # Correlation ID
    ENF_CID_001 = ErrorDefinition(
        code="ENF-CID-001",
        message="Correlation ID validation failed - missing",
        severity=ErrorSeverity.CRITICAL,
        recoverable=False,
        category="correlation_id",
        details="correlation_id is MANDATORY per Barton Doctrine"
    )
    ENF_CID_002 = ErrorDefinition(
        code="ENF-CID-002",
        message="Correlation ID validation failed - invalid format",
        severity=ErrorSeverity.CRITICAL,
        recoverable=False,
        category="correlation_id",
        details="Must be valid UUID v4"
    )

    # Hub Gate
    ENF_HUB_001 = ErrorDefinition(
        code="ENF-HUB-001",
        message="Hub gate validation failed - missing company_id",
        severity=ErrorSeverity.ERROR,
        recoverable=True,
        category="hub_gate"
    )
    ENF_HUB_002 = ErrorDefinition(
        code="ENF-HUB-002",
        message="Hub gate validation failed - missing domain",
        severity=ErrorSeverity.ERROR,
        recoverable=True,
        category="hub_gate"
    )
    ENF_HUB_003 = ErrorDefinition(
        code="ENF-HUB-003",
        message="Hub gate validation failed - missing email_pattern",
        severity=ErrorSeverity.ERROR,
        recoverable=True,
        category="hub_gate"
    )

    # Signal Idempotency
    ENF_SIG_001 = ErrorDefinition(
        code="ENF-SIG-001",
        message="Signal deduplicated - duplicate within window",
        severity=ErrorSeverity.INFO,
        recoverable=True,
        category="signal_dedup",
        details="Signal was dropped due to 24h/365d deduplication window"
    )


# ============================================================================
# ERROR CODE REGISTRY
# ============================================================================
ERROR_REGISTRY: Dict[str, ErrorDefinition] = {}

# Populate registry from all error code classes
for cls in [HubErrorCodes, PeopleErrorCodes, DOLErrorCodes, EnforcementErrorCodes]:
    for attr_name in dir(cls):
        if not attr_name.startswith('_'):
            attr = getattr(cls, attr_name)
            if isinstance(attr, ErrorDefinition):
                ERROR_REGISTRY[attr.code] = attr


def get_error_definition(code: str) -> Optional[ErrorDefinition]:
    """
    Get error definition by code.

    Args:
        code: Error code (e.g., "PSH-P0-001")

    Returns:
        ErrorDefinition if found, None otherwise
    """
    return ERROR_REGISTRY.get(code)


def format_error(code: str, **kwargs) -> str:
    """
    Format an error message with context.

    Args:
        code: Error code
        **kwargs: Additional context to include

    Returns:
        Formatted error string
    """
    error_def = get_error_definition(code)
    if not error_def:
        return f"[{code}] Unknown error code"

    msg = f"[{code}] {error_def.message}"

    if error_def.details:
        msg += f" - {error_def.details}"

    if kwargs:
        context_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        msg += f" ({context_str})"

    return msg


def is_critical(code: str) -> bool:
    """Check if error code is critical (fail hard)."""
    error_def = get_error_definition(code)
    return error_def and error_def.severity == ErrorSeverity.CRITICAL
