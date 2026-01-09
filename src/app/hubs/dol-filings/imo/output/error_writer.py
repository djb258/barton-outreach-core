"""
DOL Error Writer — IMO Output Layer (Error-Only)
=================================================

═══════════════════════════════════════════════════════════════════════════════
DOCTRINE (v1.1 - Error-Only Enforcement)
═══════════════════════════════════════════════════════════════════════════════

The DOL Sub-Hub emits facts only.
All failures are DATA DEFICIENCIES, not system failures.
Therefore, the DOL Sub-Hub NEVER writes to AIR.

ALL DOL failures route EXCLUSIVELY to `shq.error_master`.
AIR logging is FORBIDDEN in the DOL Sub-Hub.

═══════════════════════════════════════════════════════════════════════════════
"""

from typing import Any, Dict, Optional, Set
from datetime import datetime, timezone
import json
import logging
import hashlib
import uuid

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# GEOGRAPHIC TARGETS (8 Target States)
# ═══════════════════════════════════════════════════════════════════════════

TARGET_STATES: Set[str] = frozenset({
    'WV',  # West Virginia
    'VA',  # Virginia
    'PA',  # Pennsylvania
    'MD',  # Maryland
    'OH',  # Ohio
    'KY',  # Kentucky
    'DE',  # Delaware
    'NC',  # North Carolina
})


def is_in_scope(state: Optional[str]) -> bool:
    """
    Check if a state is in target scope.
    
    Args:
        state: Two-letter state code
        
    Returns:
        True if state is in TARGET_STATES, False otherwise
    """
    if not state:
        return False
    return state.upper().strip() in TARGET_STATES


# ═══════════════════════════════════════════════════════════════════════════
# DOL ERROR CODES (LOCKED ENUM)
# ═══════════════════════════════════════════════════════════════════════════

class DOLErrorCode:
    """Standard DOL error codes. No new codes. No renaming."""
    
    # EIN Resolution Failures
    EIN_UNRESOLVED = "EIN_UNRESOLVED"
    EIN_MISMATCH = "EIN_MISMATCH"
    MULTI_EIN_FOUND = "MULTI_EIN_FOUND"
    EIN_FORMAT_INVALID = "EIN_FORMAT_INVALID"
    
    # EIN Enforcement Gate (Post-Resolution)
    DOL_EIN_MISSING = "DOL_EIN_MISSING"      # Zero EINs for context
    DOL_EIN_AMBIGUOUS = "DOL_EIN_AMBIGUOUS"  # Multiple EINs for context
    
    # Context Resolution Failures
    NO_OUTREACH_CONTEXT = "NO_OUTREACH_CONTEXT"
    NO_COMPANY_UNIQUE_ID = "NO_COMPANY_UNIQUE_ID"
    
    # Upstream Data Failures
    COMPANY_TARGET_NOT_PASS = "COMPANY_TARGET_NOT_PASS"
    UPSTREAM_DATA_MISSING = "UPSTREAM_DATA_MISSING"
    AMBIGUOUS_MATCH = "AMBIGUOUS_MATCH"
    
    # Filing Failures
    DOL_FILING_NOT_CONFIRMED = "DOL_FILING_NOT_CONFIRMED"
    FILING_TTL_EXCEEDED = "FILING_TTL_EXCEEDED"
    
    # Validation Failures
    HASH_VERIFICATION_FAILED = "HASH_VERIFICATION_FAILED"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    
    # Identity Failures
    IDENTITY_GATE_FAILED = "IDENTITY_GATE_FAILED"
    CROSS_CONTEXT_CONTAMINATION = "CROSS_CONTEXT_CONTAMINATION"
    
    # Violation-specific
    VIOLATION_EIN_NOT_FOUND = "VIOLATION_EIN_NOT_FOUND"


# Valid error codes set for validation
_VALID_ERROR_CODES = frozenset([
    DOLErrorCode.EIN_UNRESOLVED,
    DOLErrorCode.EIN_MISMATCH,
    DOLErrorCode.MULTI_EIN_FOUND,
    DOLErrorCode.EIN_FORMAT_INVALID,
    DOLErrorCode.NO_OUTREACH_CONTEXT,
    DOLErrorCode.NO_COMPANY_UNIQUE_ID,
    DOLErrorCode.COMPANY_TARGET_NOT_PASS,
    DOLErrorCode.UPSTREAM_DATA_MISSING,
    DOLErrorCode.AMBIGUOUS_MATCH,
    DOLErrorCode.DOL_FILING_NOT_CONFIRMED,
    DOLErrorCode.FILING_TTL_EXCEEDED,
    DOLErrorCode.HASH_VERIFICATION_FAILED,
    DOLErrorCode.SOURCE_UNAVAILABLE,
    DOLErrorCode.VALIDATION_FAILED,
    DOLErrorCode.IDENTITY_GATE_FAILED,
    DOLErrorCode.CROSS_CONTEXT_CONTAMINATION,
    DOLErrorCode.VIOLATION_EIN_NOT_FOUND,
    # EIN Enforcement Gate codes
    DOLErrorCode.DOL_EIN_MISSING,
    DOLErrorCode.DOL_EIN_AMBIGUOUS,
])


# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

DOL_PROCESS_ID = "01.04.02.04.22000"
DOL_AGENT_NAME = "DOL_EIN_SUBHUB"

# Severity levels
SEVERITY_HARD_FAIL = "HARD_FAIL"
SEVERITY_SOFT_FAIL = "SOFT_FAIL"


# ═══════════════════════════════════════════════════════════════════════════
# SUPPRESSION KEY GENERATION
# ═══════════════════════════════════════════════════════════════════════════

def generate_suppression_key(
    ein_raw: Optional[str],
    state: Optional[str],
    filing_year: Optional[int],
    error_code: str
) -> str:
    """
    Generate a stable suppression key for deduplication.
    
    Same (EIN, state, year, error) = same key = deduplicated.
    
    Args:
        ein_raw: Raw EIN value (before normalization)
        state: State code
        filing_year: Filing year
        error_code: Error code
        
    Returns:
        SHA256 hash of concatenated values
    """
    components = [
        str(ein_raw or '').strip(),
        str(state or '').upper().strip(),
        str(filing_year or ''),
        error_code,
    ]
    key_string = '|'.join(components)
    return hashlib.sha256(key_string.encode()).hexdigest()[:32]


# ═══════════════════════════════════════════════════════════════════════════
# EIN NORMALIZATION
# ═══════════════════════════════════════════════════════════════════════════

def normalize_ein(ein_raw: Optional[str]) -> Optional[str]:
    """
    Normalize EIN to 9-digit numeric string.
    
    Args:
        ein_raw: Raw EIN value
        
    Returns:
        Normalized 9-digit EIN, or None if invalid
    """
    if not ein_raw:
        return None
    
    # Strip non-numeric
    numeric_only = ''.join(c for c in str(ein_raw) if c.isdigit())
    
    # Require exactly 9 digits
    if len(numeric_only) != 9:
        return None
    
    return numeric_only


# ═══════════════════════════════════════════════════════════════════════════
# ERROR-ONLY WRITER (NO AIR)
# ═══════════════════════════════════════════════════════════════════════════

def write_error_master(
    conn,
    *,
    error_code: str,
    message: str,
    severity: str = SEVERITY_HARD_FAIL,
    ein_raw: Optional[str] = None,
    ein_normalized: Optional[str] = None,
    state: Optional[str] = None,
    filing_year: Optional[int] = None,
    company_unique_id: Optional[str] = None,
    outreach_context_id: Optional[str] = None,
    eligible_for_enrichment: bool = True,
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Write DOL failure to shq.error_master (ERROR-ONLY, NO AIR).
    
    DOCTRINE: The DOL Sub-Hub NEVER writes to AIR.
    All failures are data deficiencies routed to error_master.
    
    Args:
        conn: Database connection
        error_code: One of DOLErrorCode constants
        message: Human-readable error description
        severity: HARD_FAIL or SOFT_FAIL
        ein_raw: Raw EIN before normalization
        ein_normalized: Normalized EIN (9 digits)
        state: State code
        filing_year: Filing year
        company_unique_id: Sovereign company ID (if known)
        outreach_context_id: Outreach context (if known)
        eligible_for_enrichment: Whether error can be resolved via enrichment
        context: Additional context payload
        
    Returns:
        error_id (UUID string)
        
    Raises:
        ValueError: If error_code is not in valid set
    """
    # Validate error code
    if error_code not in _VALID_ERROR_CODES:
        raise ValueError(
            f"Invalid DOL error code: {error_code}. "
            f"Valid codes: {', '.join(sorted(_VALID_ERROR_CODES))}"
        )
    
    # Generate suppression key for deduplication
    suppression_key = generate_suppression_key(
        ein_raw=ein_raw,
        state=state,
        filing_year=filing_year,
        error_code=error_code
    )
    
    # Build context payload
    context_payload = context or {}
    context_payload.update({
        'ein_raw': ein_raw,
        'ein_normalized': ein_normalized,
        'state': state,
        'filing_year': filing_year,
        'eligible_for_enrichment': eligible_for_enrichment,
        'suppression_key': suppression_key,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    })
    
    error_id = str(uuid.uuid4())
    cursor = conn.cursor()
    
    try:
        # Check for existing error with same suppression key (deduplication)
        cursor.execute("""
            SELECT error_id FROM shq.error_master
            WHERE context->>'suppression_key' = %s
              AND resolved_at IS NULL
            LIMIT 1
        """, (suppression_key,))
        
        existing = cursor.fetchone()
        if existing:
            logger.debug(
                f"Suppressed duplicate error: {error_code} "
                f"(suppression_key={suppression_key[:8]}...)"
            )
            return existing[0]
        
        # Insert new error
        cursor.execute("""
            INSERT INTO shq.error_master (
                error_id,
                process_id,
                agent_id,
                severity,
                error_type,
                message,
                company_unique_id,
                outreach_context_id,
                air_event_id,
                context,
                created_at,
                resolved_at,
                resolution_type
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, NULL, %s, NOW(), NULL, NULL
            )
            RETURNING error_id
        """, (
            error_id,
            DOL_PROCESS_ID,
            DOL_AGENT_NAME,
            severity,
            error_code,
            f"[{error_code}] {message}",
            company_unique_id,
            outreach_context_id,
            json.dumps(context_payload),
        ))
        
        conn.commit()
        
        logger.info(
            f"DOL ERROR: {error_code} - {message[:60]}... "
            f"(error_id={error_id[:8]}, suppression={suppression_key[:8]})"
        )
        
        return error_id
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to write DOL error: {e}")
        raise


# ═══════════════════════════════════════════════════════════════════════════
# AIR PROHIBITION (HARD KILL)
# ═══════════════════════════════════════════════════════════════════════════

def write_air(*args, **kwargs):
    """
    AIR logging is FORBIDDEN in the DOL Sub-Hub.
    
    DOCTRINE: All failures are data deficiencies, not system failures.
    Therefore, the DOL Sub-Hub NEVER writes to AIR.
    
    Raises:
        RuntimeError: Always. This function exists only to trap AIR calls.
    """
    raise RuntimeError(
        "DOCTRINE VIOLATION: AIR logging is FORBIDDEN in the DOL Sub-Hub. "
        "All failures must write to shq.error_master. "
        "Remove all references to: dol.air_log, write_air, AIR_EVENT"
    )


def write_air_log(*args, **kwargs):
    """AIR logging trap. See write_air()."""
    return write_air(*args, **kwargs)


def write_air_info_event(*args, **kwargs):
    """AIR logging trap. See write_air()."""
    return write_air(*args, **kwargs)


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE WRAPPERS
# ═══════════════════════════════════════════════════════════════════════════

def log_ein_unresolved(
    conn,
    *,
    ein_raw: str,
    state: Optional[str] = None,
    filing_year: Optional[int] = None,
    context: Optional[Dict] = None,
) -> str:
    """Log EIN resolution failure."""
    ein_normalized = normalize_ein(ein_raw)
    return write_error_master(
        conn,
        error_code=DOLErrorCode.EIN_UNRESOLVED,
        message=f"Cannot resolve EIN: {ein_raw}",
        ein_raw=ein_raw,
        ein_normalized=ein_normalized,
        state=state,
        filing_year=filing_year,
        eligible_for_enrichment=True,
        context=context,
    )


def log_no_outreach_context(
    conn,
    *,
    company_unique_id: str,
    ein: Optional[str] = None,
    state: Optional[str] = None,
    context: Optional[Dict] = None,
) -> str:
    """Log missing outreach context."""
    return write_error_master(
        conn,
        error_code=DOLErrorCode.NO_OUTREACH_CONTEXT,
        message=f"No outreach_context_id for company: {company_unique_id}",
        company_unique_id=company_unique_id,
        ein_raw=ein,
        ein_normalized=normalize_ein(ein),
        state=state,
        eligible_for_enrichment=True,
        context=context,
    )


def log_validation_failed(
    conn,
    *,
    reason: str,
    ein: Optional[str] = None,
    state: Optional[str] = None,
    context: Optional[Dict] = None,
) -> str:
    """Log validation failure."""
    return write_error_master(
        conn,
        error_code=DOLErrorCode.VALIDATION_FAILED,
        message=f"Validation failed: {reason}",
        ein_raw=ein,
        ein_normalized=normalize_ein(ein),
        state=state,
        eligible_for_enrichment=False,
        context=context,
    )
