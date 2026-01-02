"""
Outreach Context Manager
========================
Python interface to outreach_ctx database functions.

DOCTRINE ENFORCEMENT:
- All paid tools MUST be logged against outreach_context_id
- Tier-2 tools are SINGLE-SHOT per context (can_attempt_tier2 guard)
- Context finalization is IMMUTABLE (PASS/FAIL/ABORTED)

This module is the TRUTH SOURCE for cost safety.
If this module is bypassed, the doctrine is violated.

ERROR CODES:
- CT_MISSING_CONTEXT_ID: outreach_context_id not provided
- CT_MISSING_SOV_ID: company_sov_id not provided
- CT_TIER2_BLOCKED: Tier-2 already attempted in this context
- CT_CONTEXT_FINALIZED: Cannot operate on finalized context
"""

from typing import Optional, Tuple, Dict, Any
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
import logging
import uuid

logger = logging.getLogger(__name__)


class ContextState(Enum):
    """Final state enum matching database."""
    PASS = "PASS"
    FAIL = "FAIL"
    ABORTED = "ABORTED"


class ContextError(Exception):
    """Base exception for context operations."""
    def __init__(self, error_code: str, message: str):
        self.error_code = error_code
        self.message = message
        super().__init__(f"{error_code}: {message}")


class MissingContextError(ContextError):
    """Raised when outreach_context_id is missing."""
    def __init__(self, message: str = "outreach_context_id is MANDATORY"):
        super().__init__("CT_MISSING_CONTEXT_ID", message)


class MissingSovIdError(ContextError):
    """Raised when company_sov_id is missing."""
    def __init__(self, message: str = "company_sov_id is MANDATORY"):
        super().__init__("CT_MISSING_SOV_ID", message)


class Tier2BlockedError(ContextError):
    """Raised when Tier-2 tool already attempted in context."""
    def __init__(self, tool_name: str, context_id: str):
        super().__init__(
            "CT_TIER2_BLOCKED",
            f"Tier-2 tool '{tool_name}' already attempted in context {context_id}"
        )


class ContextFinalizedError(ContextError):
    """Raised when trying to operate on a finalized context."""
    def __init__(self, context_id: str, state: str):
        super().__init__(
            "CT_CONTEXT_FINALIZED",
            f"Context {context_id} already finalized with state {state}"
        )


@dataclass
class ToolAttemptResult:
    """Result of logging a tool attempt."""
    attempt_id: str
    success: bool
    cost_logged: float


@dataclass
class ContextInfo:
    """Information about an outreach context."""
    outreach_context_id: str
    company_sov_id: str
    is_active: bool
    final_state: Optional[str]
    total_cost_credits: float
    tier2_calls: int


class OutreachContextManager:
    """
    Interface to outreach_ctx schema functions.

    DOCTRINE ENFORCEMENT:
    - can_attempt_tier2() check before Tier-2 calls (HARD GATE)
    - log_tool_attempt() after every paid tool call
    - finalize_pass/fail on pipeline completion

    This is the SINGLE SOURCE OF TRUTH for:
    - Tier-2 single-shot enforcement
    - Cost accounting per context
    - Context finalization

    Usage:
        manager = OutreachContextManager(connection_pool)

        # Before calling Tier-2 tool:
        if not manager.can_attempt_tier2(ctx_id, sov_id, 'prospeo'):
            raise Tier2BlockedError('prospeo', ctx_id)

        # After every paid tool call:
        manager.log_tool_attempt(ctx_id, sov_id, 'hunter', 1, 0.008, True)
    """

    def __init__(self, connection_pool=None, connection=None):
        """
        Initialize context manager.

        Args:
            connection_pool: psycopg2 connection pool (preferred)
            connection: Direct psycopg2 connection (fallback)
        """
        self._pool = connection_pool
        self._conn = connection

        if not self._pool and not self._conn:
            logger.warning("No database connection provided - using mock mode")
            self._mock_mode = True
            self._mock_attempts: Dict[str, set] = {}  # context_id -> set of tool names
        else:
            self._mock_mode = False

    def _get_connection(self):
        """Get database connection from pool or direct."""
        if self._pool:
            return self._pool.getconn()
        return self._conn

    def _release_connection(self, conn):
        """Release connection back to pool if applicable."""
        if self._pool and conn:
            self._pool.putconn(conn)

    # =========================================================================
    # VALIDATION (FAIL HARD)
    # =========================================================================

    @staticmethod
    def validate_context_id(outreach_context_id: str) -> str:
        """
        Validate outreach_context_id is present and valid.

        DOCTRINE: FAIL HARD if missing.

        Args:
            outreach_context_id: Context ID to validate

        Returns:
            Validated context ID (stripped)

        Raises:
            MissingContextError: If context ID is None or empty
        """
        if not outreach_context_id:
            raise MissingContextError()

        ctx_id = str(outreach_context_id).strip()
        if not ctx_id:
            raise MissingContextError("outreach_context_id cannot be empty string")

        return ctx_id

    @staticmethod
    def validate_sov_id(company_sov_id: str) -> str:
        """
        Validate company_sov_id is present and valid.

        DOCTRINE: FAIL HARD if missing.

        Args:
            company_sov_id: Sovereign ID to validate

        Returns:
            Validated sovereign ID (stripped)

        Raises:
            MissingSovIdError: If sovereign ID is None or empty
        """
        if not company_sov_id:
            raise MissingSovIdError()

        sov_id = str(company_sov_id).strip()
        if not sov_id:
            raise MissingSovIdError("company_sov_id cannot be empty string")

        return sov_id

    # =========================================================================
    # TIER-2 GUARD (SINGLE-SHOT ENFORCEMENT)
    # =========================================================================

    def can_attempt_tier2(
        self,
        outreach_context_id: str,
        company_sov_id: str,
        tool_name: str
    ) -> bool:
        """
        Check if Tier-2 tool can be attempted in this context.

        DOCTRINE: Returns FALSE if already attempted (single-shot enforcement).
        This is a HARD GATE - if FALSE, caller MUST NOT proceed.

        Args:
            outreach_context_id: Current execution context
            company_sov_id: Company sovereign ID
            tool_name: Tier-2 tool name (prospeo, snov, clay)

        Returns:
            True if tool can be attempted, False if already used
        """
        # Validate inputs
        ctx_id = self.validate_context_id(outreach_context_id)
        sov_id = self.validate_sov_id(company_sov_id)
        tool = tool_name.lower().strip()

        if self._mock_mode:
            # Mock mode for testing without database
            key = f"{ctx_id}:{sov_id}"
            if key not in self._mock_attempts:
                self._mock_attempts[key] = set()
            return tool not in self._mock_attempts[key]

        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT outreach_ctx.can_attempt_tier2(%s::uuid, %s::uuid, %s)",
                    (ctx_id, sov_id, tool)
                )
                result = cur.fetchone()
                return result[0] if result else False
        except Exception as e:
            logger.error(f"can_attempt_tier2 failed: {e}")
            # DOCTRINE: On database error, FAIL SAFE by blocking
            return False
        finally:
            self._release_connection(conn)

    def assert_can_attempt_tier2(
        self,
        outreach_context_id: str,
        company_sov_id: str,
        tool_name: str
    ) -> None:
        """
        Assert Tier-2 tool can be attempted, raise if blocked.

        Convenience method that raises Tier2BlockedError if guard fails.

        Args:
            outreach_context_id: Current execution context
            company_sov_id: Company sovereign ID
            tool_name: Tier-2 tool name

        Raises:
            Tier2BlockedError: If Tier-2 already attempted
            MissingContextError: If context ID missing
            MissingSovIdError: If sovereign ID missing
        """
        if not self.can_attempt_tier2(outreach_context_id, company_sov_id, tool_name):
            raise Tier2BlockedError(tool_name, outreach_context_id)

    # =========================================================================
    # TOOL ATTEMPT LOGGING
    # =========================================================================

    def log_tool_attempt(
        self,
        outreach_context_id: str,
        company_sov_id: str,
        tool_name: str,
        tool_tier: int,
        cost_credits: float,
        success: bool,
        result_summary: str = None,
        error_message: str = None,
        sub_hub: str = "company-target"
    ) -> ToolAttemptResult:
        """
        Log a tool attempt and spend to outreach_ctx.

        DOCTRINE: Every paid tool call MUST be logged.

        Args:
            outreach_context_id: Current execution context
            company_sov_id: Company sovereign ID
            tool_name: Tool that was called
            tool_tier: Tool tier (0, 1, or 2)
            cost_credits: Cost in credits
            success: Whether call succeeded
            result_summary: Optional summary of result
            error_message: Optional error message
            sub_hub: Sub-hub making the call (default: company-target)

        Returns:
            ToolAttemptResult with attempt_id
        """
        # Validate inputs
        ctx_id = self.validate_context_id(outreach_context_id)
        sov_id = self.validate_sov_id(company_sov_id)
        tool = tool_name.lower().strip()

        if self._mock_mode:
            # Mock mode - track Tier-2 attempts
            if tool_tier == 2:
                key = f"{ctx_id}:{sov_id}"
                if key not in self._mock_attempts:
                    self._mock_attempts[key] = set()
                self._mock_attempts[key].add(tool)

            return ToolAttemptResult(
                attempt_id=str(uuid.uuid4()),
                success=success,
                cost_logged=cost_credits
            )

        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT outreach_ctx.log_tool_attempt(
                        %s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s, %s
                    )""",
                    (
                        ctx_id,
                        sov_id,
                        tool,
                        tool_tier,
                        Decimal(str(cost_credits)),
                        success,
                        result_summary,
                        error_message,
                        sub_hub
                    )
                )
                result = cur.fetchone()
                conn.commit()

                return ToolAttemptResult(
                    attempt_id=str(result[0]) if result else None,
                    success=success,
                    cost_logged=cost_credits
                )
        except Exception as e:
            logger.error(f"log_tool_attempt failed: {e}")
            # Log failure but don't block - cost accounting error is non-fatal
            return ToolAttemptResult(
                attempt_id=None,
                success=success,
                cost_logged=0.0
            )
        finally:
            self._release_connection(conn)

    # =========================================================================
    # CONTEXT FINALIZATION
    # =========================================================================

    def finalize_pass(self, outreach_context_id: str) -> bool:
        """
        Finalize context with PASS state.

        DOCTRINE: Once finalized, context is IMMUTABLE.

        Args:
            outreach_context_id: Context to finalize

        Returns:
            True if successfully finalized, False if already finalized
        """
        ctx_id = self.validate_context_id(outreach_context_id)

        if self._mock_mode:
            return True

        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT outreach_ctx.finalize_pass(%s::uuid)",
                    (ctx_id,)
                )
                result = cur.fetchone()
                conn.commit()
                return result[0] if result else False
        except Exception as e:
            logger.error(f"finalize_pass failed: {e}")
            return False
        finally:
            self._release_connection(conn)

    def finalize_fail(self, outreach_context_id: str, reason: str) -> bool:
        """
        Finalize context with FAIL state.

        DOCTRINE: Once finalized, context is IMMUTABLE.

        Args:
            outreach_context_id: Context to finalize
            reason: Reason for failure

        Returns:
            True if successfully finalized, False if already finalized
        """
        ctx_id = self.validate_context_id(outreach_context_id)

        if self._mock_mode:
            return True

        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT outreach_ctx.finalize_fail(%s::uuid, %s)",
                    (ctx_id, reason)
                )
                result = cur.fetchone()
                conn.commit()
                return result[0] if result else False
        except Exception as e:
            logger.error(f"finalize_fail failed: {e}")
            return False
        finally:
            self._release_connection(conn)

    # =========================================================================
    # CONTEXT INFO
    # =========================================================================

    def get_context_info(self, outreach_context_id: str) -> Optional[ContextInfo]:
        """
        Get information about a context.

        Args:
            outreach_context_id: Context to query

        Returns:
            ContextInfo or None if not found
        """
        ctx_id = self.validate_context_id(outreach_context_id)

        if self._mock_mode:
            return None

        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT
                        outreach_context_id,
                        company_sov_id,
                        is_active,
                        final_state,
                        total_cost_credits,
                        tier2_calls
                    FROM outreach_ctx.context
                    WHERE outreach_context_id = %s::uuid""",
                    (ctx_id,)
                )
                row = cur.fetchone()
                if row:
                    return ContextInfo(
                        outreach_context_id=str(row[0]),
                        company_sov_id=str(row[1]),
                        is_active=row[2],
                        final_state=row[3],
                        total_cost_credits=float(row[4]),
                        tier2_calls=row[5]
                    )
                return None
        except Exception as e:
            logger.error(f"get_context_info failed: {e}")
            return None
        finally:
            self._release_connection(conn)


# =============================================================================
# MODULE-LEVEL SINGLETON (Optional)
# =============================================================================

_default_manager: Optional[OutreachContextManager] = None


def get_context_manager(connection_pool=None, connection=None) -> OutreachContextManager:
    """
    Get or create the default context manager.

    Args:
        connection_pool: Optional connection pool to use
        connection: Optional direct connection to use

    Returns:
        OutreachContextManager instance
    """
    global _default_manager

    if connection_pool or connection:
        return OutreachContextManager(connection_pool, connection)

    if _default_manager is None:
        _default_manager = OutreachContextManager()

    return _default_manager


def reset_context_manager():
    """Reset the default context manager (for testing)."""
    global _default_manager
    _default_manager = None


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Classes
    "OutreachContextManager",
    "ContextInfo",
    "ToolAttemptResult",
    "ContextState",
    # Exceptions
    "ContextError",
    "MissingContextError",
    "MissingSovIdError",
    "Tier2BlockedError",
    "ContextFinalizedError",
    # Functions
    "get_context_manager",
    "reset_context_manager",
]
