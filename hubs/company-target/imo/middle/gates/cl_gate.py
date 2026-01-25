"""
CL Upstream Gate
================
Enforces upstream Company Lifecycle (CL) existence verification.

DOCTRINE ENFORCEMENT:
- Outreach is a CONSUMER of CL truth, not a creator
- If CL did not mint a sovereign ID, Outreach MUST NOT proceed
- Missing upstream signals are NOT an Outreach error to fix

This module is the HARD GATE for CL contract enforcement.
If this gate fails, Company Target logic MUST NOT execute.

ERROR CODES:
- CT_UPSTREAM_CL_NOT_VERIFIED: Company does not exist in CL
"""

from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)


class UpstreamCLError(Exception):
    """Base exception for CL upstream gate failures."""
    def __init__(self, error_code: str, message: str):
        self.error_code = error_code
        self.message = message
        super().__init__(f"{error_code}: {message}")


class CLNotVerifiedError(UpstreamCLError):
    """Raised when company does not exist in CL."""
    def __init__(self, company_sov_id: str):
        super().__init__(
            "CT_UPSTREAM_CL_NOT_VERIFIED",
            f"Company {company_sov_id} not found in CL. "
            "Upstream existence verification required."
        )
        self.company_sov_id = company_sov_id


class CLGate:
    """
    Enforces upstream CL existence verification.

    DOCTRINE:
    - Outreach assumes Company Life Cycle existence verification has passed
    - Outreach will not execute without a verified sovereign ID in CL
    - Missing upstream signals are NOT an Outreach error to fix

    Usage:
        # At Company Target entry point (BEFORE any logic):
        CLGate.enforce_or_fail(company_sov_id, outreach_context_id)

        # Or check without exception:
        if CLGate.check_existence(company_sov_id):
            # Proceed
        else:
            # Handle missing

    Option B Implementation:
        If company_unique_id exists in cl.company_identity → EXISTENCE_PASS
        If missing → EXISTENCE_FAIL
    """

    _connection = None
    _mock_mode = False
    _mock_verified_ids = set()  # For testing

    @classmethod
    def set_connection(cls, connection):
        """Set database connection for CL queries."""
        cls._connection = connection
        cls._mock_mode = False

    @classmethod
    def set_mock_mode(cls, verified_ids: set = None):
        """Enable mock mode for testing."""
        cls._mock_mode = True
        cls._mock_verified_ids = verified_ids or set()

    @classmethod
    def reset(cls):
        """Reset state (for testing)."""
        cls._connection = None
        cls._mock_mode = False
        cls._mock_verified_ids = set()

    @classmethod
    def check_existence(cls, company_sov_id: str) -> bool:
        """
        Check if company exists in CL (EXISTENCE_PASS).

        Option B: Sovereign ID existence = verified.
        If CL minted the ID, existence was verified.

        Args:
            company_sov_id: Company sovereign ID to check

        Returns:
            True if exists in CL (EXISTENCE_PASS)
            False if missing (EXISTENCE_FAIL)
        """
        if not company_sov_id:
            return False

        sov_id = str(company_sov_id).strip()
        if not sov_id:
            return False

        # Mock mode for testing
        if cls._mock_mode:
            return sov_id in cls._mock_verified_ids

        # Real database check
        conn = cls._connection
        if not conn:
            # Try to get connection from environment
            try:
                import psycopg2
                database_url = os.getenv('DATABASE_URL')
                if not database_url:
                    host = os.getenv('NEON_HOST', 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech')
                    database = os.getenv('NEON_DATABASE', 'Marketing DB')
                    user = os.getenv('NEON_USER', 'Marketing DB_owner')
                    password = os.getenv('NEON_PASSWORD', '')
                    conn = psycopg2.connect(
                        host=host,
                        database=database,
                        user=user,
                        password=password,
                        sslmode='require'
                    )
                else:
                    conn = psycopg2.connect(database_url)
                cls._connection = conn
            except Exception as e:
                logger.error(f"Failed to connect to CL database: {e}")
                # DOCTRINE: On connection error, FAIL SAFE by blocking
                return False

        try:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT EXISTS(
                        SELECT 1 FROM cl.company_identity
                        WHERE company_unique_id = %s::uuid
                    )""",
                    (sov_id,)
                )
                result = cur.fetchone()
                return result[0] if result else False
        except Exception as e:
            logger.error(f"CL existence check failed: {e}")
            # DOCTRINE: On query error, FAIL SAFE by blocking
            return False

    @classmethod
    def enforce_or_fail(
        cls,
        company_sov_id: str,
        outreach_context_id: str,
        write_error: bool = True
    ) -> None:
        """
        HARD GATE: Enforce CL existence verification.

        If company does not exist in CL:
        1. Optionally write error to outreach_errors.company_target_errors
        2. Raise CLNotVerifiedError

        DOCTRINE:
        - Do NOT attempt any Company Target logic if this fails
        - Do NOT re-verify domains, LinkedIn, name, or state
        - Missing upstream signals are NOT an Outreach error to fix

        Args:
            company_sov_id: Company sovereign ID to verify
            outreach_context_id: Current execution context
            write_error: Whether to write error to database (default True)

        Raises:
            CLNotVerifiedError: If company not in CL
        """
        if cls.check_existence(company_sov_id):
            logger.debug(f"CL gate PASS for {company_sov_id}")
            return

        # EXISTENCE_FAIL path
        logger.warning(
            f"CL gate FAIL: {company_sov_id} not found in CL. "
            f"Context: {outreach_context_id}"
        )

        # Write error to database if requested
        if write_error:
            cls._write_error(company_sov_id, outreach_context_id)

        raise CLNotVerifiedError(company_sov_id)

    @classmethod
    def _write_error(
        cls,
        company_sov_id: Optional[str],
        outreach_context_id: str
    ) -> None:
        """
        Write UPSTREAM_CL_NOT_VERIFIED error to error table.

        Args:
            company_sov_id: Company sovereign ID (may be None/invalid)
            outreach_context_id: Current execution context
        """
        if cls._mock_mode:
            logger.info(f"[MOCK] Would write CL gate error for {company_sov_id}")
            return

        conn = cls._connection
        if not conn:
            logger.error("Cannot write CL gate error: no database connection")
            return

        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO outreach_errors.company_target_errors (
                        company_sov_id,
                        outreach_context_id,
                        hub_name,
                        pipeline_stage,
                        failure_code,
                        blocking_reason,
                        severity,
                        raw_input
                    ) VALUES (
                        %s::uuid,
                        %s::uuid,
                        'company-target',
                        'upstream_cl_gate',
                        'CT_UPSTREAM_CL_NOT_VERIFIED',
                        'Company does not exist in Company Lifecycle (CL). Upstream existence verification required before Outreach can proceed.',
                        'blocking',
                        %s::jsonb
                    )""",
                    (
                        company_sov_id if company_sov_id else None,
                        outreach_context_id,
                        f'{{"expected_signal": "EXISTENCE_PASS", "company_sov_id": "{company_sov_id}"}}'
                    )
                )
                conn.commit()
                logger.info(f"CL gate error written for {company_sov_id}")
        except Exception as e:
            logger.error(f"Failed to write CL gate error: {e}")
            # Don't block on error write failure - the raise will still happen


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "CLGate",
    "CLNotVerifiedError",
    "UpstreamCLError",
]
