"""
Hub Gate Enforcement Module
===========================
DOCTRINE: Company Hub is the MASTER NODE. All spokes MUST validate
company anchor before processing.

GOLDEN RULE:
    IF company_id IS NULL OR domain IS NULL OR email_pattern IS NULL:
        STOP. DO NOT PROCEED.
        → Route to Company Identity Pipeline first.

This module provides the hub_gate validation that MUST be called
before any spoke phase execution.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class HubGateError(Exception):
    """
    Raised when hub gate validation fails.

    This is a FAIL HARD condition - spoke execution must stop immediately.
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        entity_id: Optional[str] = None,
        missing_fields: Optional[List[str]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.entity_id = entity_id
        self.missing_fields = missing_fields or []
        super().__init__(self.message)


class GateLevel(Enum):
    """Validation strictness levels."""
    COMPANY_ID_ONLY = "company_id_only"  # Just company_id required
    COMPANY_DOMAIN = "company_domain"     # company_id + domain required
    FULL = "full"                          # company_id + domain + email_pattern required


@dataclass
class HubGateResult:
    """Result of hub gate validation."""
    passed: bool
    company_id: Optional[str] = None
    domain: Optional[str] = None
    email_pattern: Optional[str] = None
    missing_fields: List[str] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.missing_fields is None:
            self.missing_fields = []


def validate_company_anchor(
    record: Dict[str, Any],
    level: GateLevel = GateLevel.COMPANY_ID_ONLY,
    process_id: str = "unknown",
    correlation_id: str = "unknown",
    fail_hard: bool = True
) -> HubGateResult:
    """
    Validate company anchor per Barton Doctrine.

    DOCTRINE ENFORCEMENT (FAIL HARD):
    - All spoke phases MUST call this before processing
    - No spoke may proceed without Company Hub authorization
    - Missing company_id → emit error → STOP

    Args:
        record: Dictionary containing company fields to validate
        level: Validation strictness level
        process_id: Process ID for error context
        correlation_id: Correlation ID for error context
        fail_hard: If True, raise HubGateError on failure. If False, return result.

    Returns:
        HubGateResult with validation outcome

    Raises:
        HubGateError: If fail_hard=True and validation fails
    """
    missing_fields = []

    # Extract fields (handle multiple possible column names)
    company_id = _extract_field(record, ['company_id', 'matched_company_id', 'company_unique_id'])
    domain = _extract_field(record, ['domain', 'resolved_domain', 'company_domain', 'website_url'])
    email_pattern = _extract_field(record, ['email_pattern', 'verified_pattern', 'pattern'])

    # Validate based on level
    if level in [GateLevel.COMPANY_ID_ONLY, GateLevel.COMPANY_DOMAIN, GateLevel.FULL]:
        if not company_id:
            missing_fields.append('company_id')

    if level in [GateLevel.COMPANY_DOMAIN, GateLevel.FULL]:
        if not domain:
            missing_fields.append('domain')

    if level == GateLevel.FULL:
        if not email_pattern:
            missing_fields.append('email_pattern')

    # Build result
    if missing_fields:
        error_msg = (
            f"HUB GATE FAILED: Missing required company anchor fields: {missing_fields}. "
            f"Process: {process_id}, Correlation: {correlation_id}. "
            f"DOCTRINE: No spoke may proceed without Company Hub authorization."
        )

        result = HubGateResult(
            passed=False,
            company_id=company_id,
            domain=domain,
            email_pattern=email_pattern,
            missing_fields=missing_fields,
            error_message=error_msg
        )

        if fail_hard:
            # Determine error code based on what's missing
            if 'company_id' in missing_fields:
                error_code = "GATE-001"  # Missing company_id
            elif 'domain' in missing_fields:
                error_code = "GATE-002"  # Missing domain
            else:
                error_code = "GATE-003"  # Missing email_pattern

            raise HubGateError(
                message=error_msg,
                error_code=error_code,
                entity_id=_extract_field(record, ['person_id', 'entity_id', 'id']),
                missing_fields=missing_fields
            )

        return result

    # Passed
    return HubGateResult(
        passed=True,
        company_id=company_id,
        domain=domain,
        email_pattern=email_pattern,
        missing_fields=[]
    )


def validate_company_anchor_batch(
    records: List[Dict[str, Any]],
    level: GateLevel = GateLevel.COMPANY_ID_ONLY,
    process_id: str = "unknown",
    correlation_id: str = "unknown"
) -> tuple:
    """
    Validate company anchor for a batch of records.

    Does NOT fail hard - separates valid from invalid records.
    Use this for batch processing where you want to continue with valid records.

    Args:
        records: List of record dictionaries to validate
        level: Validation strictness level
        process_id: Process ID for error context
        correlation_id: Correlation ID for error context

    Returns:
        Tuple of (valid_records, invalid_records_with_errors)
    """
    valid_records = []
    invalid_records = []

    for record in records:
        result = validate_company_anchor(
            record=record,
            level=level,
            process_id=process_id,
            correlation_id=correlation_id,
            fail_hard=False
        )

        if result.passed:
            valid_records.append(record)
        else:
            invalid_records.append({
                'record': record,
                'error': result.error_message,
                'missing_fields': result.missing_fields
            })

    return valid_records, invalid_records


def _extract_field(record: Dict[str, Any], field_names: List[str]) -> Optional[str]:
    """
    Extract field value from record, trying multiple possible column names.

    Args:
        record: Record dictionary
        field_names: List of possible field names to try

    Returns:
        Field value if found and non-empty, None otherwise
    """
    for name in field_names:
        value = record.get(name)
        if value is not None:
            str_value = str(value).strip()
            if str_value and str_value.lower() not in ('none', 'null', 'nan', ''):
                return str_value
    return None


# Convenience functions for common validation patterns

def require_company_id(
    record: Dict[str, Any],
    process_id: str,
    correlation_id: str
) -> str:
    """
    Require company_id and return it, or FAIL HARD.

    Args:
        record: Record dictionary
        process_id: Process ID for error context
        correlation_id: Correlation ID for error context

    Returns:
        The company_id value

    Raises:
        HubGateError: If company_id is missing
    """
    result = validate_company_anchor(
        record=record,
        level=GateLevel.COMPANY_ID_ONLY,
        process_id=process_id,
        correlation_id=correlation_id,
        fail_hard=True
    )
    return result.company_id


def require_company_domain(
    record: Dict[str, Any],
    process_id: str,
    correlation_id: str
) -> tuple:
    """
    Require company_id and domain, return both, or FAIL HARD.

    Args:
        record: Record dictionary
        process_id: Process ID for error context
        correlation_id: Correlation ID for error context

    Returns:
        Tuple of (company_id, domain)

    Raises:
        HubGateError: If company_id or domain is missing
    """
    result = validate_company_anchor(
        record=record,
        level=GateLevel.COMPANY_DOMAIN,
        process_id=process_id,
        correlation_id=correlation_id,
        fail_hard=True
    )
    return result.company_id, result.domain
