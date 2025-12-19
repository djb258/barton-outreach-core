"""
Correlation ID Enforcement Module
=================================
DOCTRINE: Every process MUST propagate correlation_id unchanged.
ENFORCEMENT: FAIL HARD if correlation_id is missing or invalid.

This module provides validation that MUST be called at the start of
every phase run() method. No exceptions. No defaults. No generation.
"""

import uuid
import re
from typing import Optional


class CorrelationIDError(Exception):
    """
    Raised when correlation_id validation fails.

    This is a FAIL HARD condition - execution must stop immediately.
    """

    def __init__(self, message: str, process_id: Optional[str] = None):
        self.message = message
        self.process_id = process_id
        super().__init__(self.message)


def validate_correlation_id(
    correlation_id: Optional[str],
    process_id: str,
    phase_name: str = "unknown"
) -> str:
    """
    Validate correlation_id per Barton Doctrine.

    DOCTRINE ENFORCEMENT (FAIL HARD):
    - correlation_id MUST be present
    - correlation_id MUST be valid UUID v4
    - correlation_id MUST NOT be empty or whitespace
    - No default generation allowed

    Args:
        correlation_id: The correlation ID to validate
        process_id: The process_id for error context (e.g., "company.identity.matching.phase1")
        phase_name: Human-readable phase name for error messages

    Returns:
        The validated correlation_id (unchanged)

    Raises:
        CorrelationIDError: If validation fails (FAIL HARD)
    """
    # FAIL HARD: None
    if correlation_id is None:
        raise CorrelationIDError(
            f"[{phase_name}] correlation_id is MANDATORY per Barton Doctrine. "
            f"FAIL HARD: Cannot execute phase without correlation_id. "
            f"Process: {process_id}",
            process_id=process_id
        )

    # FAIL HARD: Empty or whitespace
    if not correlation_id or not correlation_id.strip():
        raise CorrelationIDError(
            f"[{phase_name}] correlation_id cannot be empty or whitespace. "
            f"FAIL HARD: Cannot execute phase without valid correlation_id. "
            f"Process: {process_id}",
            process_id=process_id
        )

    # Normalize
    correlation_id = correlation_id.strip()

    # FAIL HARD: Invalid UUID format
    try:
        parsed_uuid = uuid.UUID(correlation_id)
        # Ensure it's the canonical lowercase format
        if str(parsed_uuid) != correlation_id.lower():
            # Accept but normalize
            correlation_id = str(parsed_uuid)
    except ValueError:
        raise CorrelationIDError(
            f"[{phase_name}] correlation_id must be valid UUID v4. "
            f"Got: '{correlation_id}'. "
            f"FAIL HARD: Invalid correlation_id format. "
            f"Process: {process_id}",
            process_id=process_id
        )

    return correlation_id


def generate_correlation_id() -> str:
    """
    Generate a new correlation_id.

    IMPORTANT: This should ONLY be called at the entry point of a pipeline.
    Phases must NEVER generate their own correlation_id - they must receive
    it from the caller and propagate it unchanged.

    Returns:
        New UUID v4 string
    """
    return str(uuid.uuid4())


def is_valid_correlation_id(correlation_id: Optional[str]) -> bool:
    """
    Check if correlation_id is valid without raising.

    Use this for conditional logic only. For enforcement, use validate_correlation_id().

    Args:
        correlation_id: The correlation ID to check

    Returns:
        True if valid, False otherwise
    """
    if not correlation_id or not correlation_id.strip():
        return False

    try:
        uuid.UUID(correlation_id.strip())
        return True
    except ValueError:
        return False
