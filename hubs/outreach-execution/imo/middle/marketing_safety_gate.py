"""
###############################################################################
#                  DO NOT MODIFY WITHOUT CHANGE REQUEST
###############################################################################
#
# STATUS: FROZEN (v1.0 Operational Baseline)
# FREEZE DATE: 2026-01-20
# REFERENCE: docs/GO-LIVE_STATE_v1.0.md
#
# This file contains AUTHORITATIVE safety gate logic that is FROZEN at v1.0.
# Any modification requires:
#   1. Formal Change Request with justification
#   2. Impact analysis on all marketing send paths
#   3. Full re-certification after changes
#   4. Technical lead sign-off
#
###############################################################################

Marketing Safety Gate — HARD FAIL Enforcement
==============================================

Doctrine: CL Parent-Child v1.1
Hub ID: outreach-execution
Purpose: PREVENT ALL outbound sends to ineligible companies

ENFORCEMENT POINTS (HARD FAIL):
    1. effective_tier = -1 → HARD_FAIL (INELIGIBLE)
    2. marketing_disabled = true → HARD_FAIL (KILL SWITCH)
    3. has_active_override = true (blocking type) → HARD_FAIL

DATA SOURCE:
    MUST read from: outreach.vw_marketing_eligibility_with_overrides
    NO FALLBACK to underlying views or tables
    NO BYPASS under any circumstance

AUDIT LOGGING:
    Every send attempt MUST be logged to outreach.send_attempt_audit
    Append-only, no updates, no deletes
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


# =============================================================================
# HARD FAIL ERROR TYPES
# =============================================================================

class MarketingSafetyError(Exception):
    """Base exception for marketing safety violations."""

    def __init__(
        self,
        message: str,
        company_unique_id: str,
        error_code: str,
        effective_tier: int = -1,
        override_snapshot: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.company_unique_id = company_unique_id
        self.error_code = error_code
        self.effective_tier = effective_tier
        self.override_snapshot = override_snapshot or {}


class IneligibleTierError(MarketingSafetyError):
    """HARD_FAIL: Company has effective_tier = -1."""
    pass


class MarketingDisabledError(MarketingSafetyError):
    """HARD_FAIL: Company has marketing_disabled = true."""
    pass


class ActiveOverrideError(MarketingSafetyError):
    """HARD_FAIL: Company has active blocking override."""
    pass


class EligibilityCheckError(MarketingSafetyError):
    """HARD_FAIL: Could not verify eligibility (no fallback)."""
    pass


# =============================================================================
# SEND ATTEMPT STATUS
# =============================================================================

class SendAttemptStatus(Enum):
    """Status of a send attempt for audit logging."""
    BLOCKED_INELIGIBLE = "blocked_ineligible"
    BLOCKED_DISABLED = "blocked_disabled"
    BLOCKED_OVERRIDE = "blocked_override"
    BLOCKED_CHECK_FAILED = "blocked_check_failed"
    ALLOWED = "allowed"
    SENT = "sent"
    SEND_FAILED = "send_failed"


# =============================================================================
# ELIGIBILITY RESULT
# =============================================================================

@dataclass
class MarketingEligibilityResult:
    """Result of marketing eligibility check from authoritative view."""
    company_unique_id: str
    effective_tier: int
    computed_tier: int
    has_active_override: bool
    override_types: Optional[List[str]] = None
    override_reasons: Optional[List[str]] = None
    tier_cap: Optional[int] = None
    overall_status: str = "UNKNOWN"
    bit_score: float = 0.0

    # Raw data snapshot for audit
    raw_data: Optional[Dict[str, Any]] = field(default_factory=dict)

    @property
    def is_eligible(self) -> bool:
        """Check if company is eligible for marketing."""
        return self.effective_tier >= 0 and not self.has_active_override

    @property
    def is_blocked(self) -> bool:
        """Check if company is blocked from marketing."""
        return self.effective_tier == -1 or self.has_active_override

    def to_override_snapshot(self) -> Dict[str, Any]:
        """Create snapshot for audit logging."""
        return {
            'effective_tier': self.effective_tier,
            'computed_tier': self.computed_tier,
            'has_active_override': self.has_active_override,
            'override_types': self.override_types,
            'override_reasons': self.override_reasons,
            'tier_cap': self.tier_cap,
            'overall_status': self.overall_status,
            'bit_score': self.bit_score,
            'checked_at': datetime.utcnow().isoformat(),
        }


# =============================================================================
# SEND ATTEMPT AUDIT RECORD
# =============================================================================

@dataclass
class SendAttemptAuditRecord:
    """
    Append-only audit record for every send attempt.

    DOCTRINE: This record MUST be written BEFORE any send attempt.
    No updates, no deletes - append only.
    """
    audit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_unique_id: str = ""
    campaign_id: str = ""
    effective_tier: int = -1
    computed_tier: int = -1
    override_snapshot: Dict[str, Any] = field(default_factory=dict)
    status: str = ""
    failure_reason: Optional[str] = None
    correlation_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for database insertion."""
        return {
            'audit_id': self.audit_id,
            'company_unique_id': self.company_unique_id,
            'campaign_id': self.campaign_id,
            'effective_tier': self.effective_tier,
            'computed_tier': self.computed_tier,
            'override_snapshot': self.override_snapshot,
            'status': self.status,
            'failure_reason': self.failure_reason,
            'correlation_id': self.correlation_id,
            'created_at': self.created_at,
        }


# =============================================================================
# MARKETING SAFETY GATE
# =============================================================================

class MarketingSafetyGate:
    """
    HARD FAIL safety gate for all marketing sends.

    DOCTRINE ENFORCEMENT:
        - MUST read from vw_marketing_eligibility_with_overrides
        - NO FALLBACK to underlying views
        - NO BYPASS under any circumstance
        - EVERY attempt MUST be audit logged

    Usage:
        gate = MarketingSafetyGate(db_connection)

        # Check eligibility (HARD FAIL on ineligible)
        eligibility = gate.check_eligibility_or_fail(company_id, campaign_id)

        # If we get here, company is eligible
        # Proceed with send...

        # After send, record result
        gate.record_send_result(company_id, campaign_id, success=True)
    """

    # =========================================================================
    # ENFORCEMENT POINT: AUTHORITATIVE VIEW NAME (LOCKED)
    # =========================================================================
    AUTHORITATIVE_VIEW = "outreach.vw_marketing_eligibility_with_overrides"

    def __init__(self, db_connection=None):
        """
        Initialize safety gate.

        Args:
            db_connection: Database connection (required for production)
        """
        self._conn = db_connection
        self._audit_buffer: List[SendAttemptAuditRecord] = []

    def set_connection(self, conn):
        """Set database connection."""
        self._conn = conn

    # =========================================================================
    # ENFORCEMENT POINT: CHECK ELIGIBILITY OR HARD FAIL
    # =========================================================================

    def check_eligibility_or_fail(
        self,
        company_unique_id: str,
        campaign_id: str,
        correlation_id: Optional[str] = None
    ) -> MarketingEligibilityResult:
        """
        Check marketing eligibility. HARD FAIL if ineligible.

        ENFORCEMENT POINTS:
            1. effective_tier = -1 → HARD_FAIL
            2. has_active_override = true (blocking) → HARD_FAIL
            3. View query fails → HARD_FAIL (no fallback)

        Args:
            company_unique_id: Company to check
            campaign_id: Campaign ID for audit
            correlation_id: Trace ID

        Returns:
            MarketingEligibilityResult if eligible

        Raises:
            IneligibleTierError: If effective_tier = -1
            ActiveOverrideError: If has blocking override
            EligibilityCheckError: If check fails (no fallback)
        """
        # =====================================================================
        # ENFORCEMENT POINT: Query authoritative view ONLY
        # =====================================================================
        eligibility = self._query_eligibility_view(company_unique_id)

        if eligibility is None:
            # HARD_FAIL: Could not verify eligibility (NO FALLBACK)
            audit_record = SendAttemptAuditRecord(
                company_unique_id=company_unique_id,
                campaign_id=campaign_id,
                effective_tier=-1,
                computed_tier=-1,
                status=SendAttemptStatus.BLOCKED_CHECK_FAILED.value,
                failure_reason="Could not verify eligibility - company not found in authoritative view",
                correlation_id=correlation_id,
            )
            self._write_audit_record(audit_record)

            raise EligibilityCheckError(
                message=f"HARD_FAIL: Could not verify eligibility for {company_unique_id}. "
                        f"Company not found in {self.AUTHORITATIVE_VIEW}. NO FALLBACK.",
                company_unique_id=company_unique_id,
                error_code="SAFETY_GATE_CHECK_FAILED",
            )

        # =====================================================================
        # ENFORCEMENT POINT: Check effective_tier = -1
        # =====================================================================
        if eligibility.effective_tier == -1:
            audit_record = SendAttemptAuditRecord(
                company_unique_id=company_unique_id,
                campaign_id=campaign_id,
                effective_tier=eligibility.effective_tier,
                computed_tier=eligibility.computed_tier,
                override_snapshot=eligibility.to_override_snapshot(),
                status=SendAttemptStatus.BLOCKED_INELIGIBLE.value,
                failure_reason=f"effective_tier = -1 (INELIGIBLE)",
                correlation_id=correlation_id,
            )
            self._write_audit_record(audit_record)

            raise IneligibleTierError(
                message=f"HARD_FAIL: Company {company_unique_id} has effective_tier = -1. "
                        f"Marketing is INELIGIBLE. Overall status: {eligibility.overall_status}",
                company_unique_id=company_unique_id,
                error_code="SAFETY_GATE_TIER_INELIGIBLE",
                effective_tier=eligibility.effective_tier,
                override_snapshot=eligibility.to_override_snapshot(),
            )

        # =====================================================================
        # ENFORCEMENT POINT: Check blocking overrides
        # =====================================================================
        if eligibility.has_active_override and eligibility.override_types:
            blocking_types = {'marketing_disabled', 'legal_hold', 'customer_requested', 'cooldown'}
            active_blocking = set(eligibility.override_types or []) & blocking_types

            if active_blocking:
                audit_record = SendAttemptAuditRecord(
                    company_unique_id=company_unique_id,
                    campaign_id=campaign_id,
                    effective_tier=eligibility.effective_tier,
                    computed_tier=eligibility.computed_tier,
                    override_snapshot=eligibility.to_override_snapshot(),
                    status=SendAttemptStatus.BLOCKED_OVERRIDE.value,
                    failure_reason=f"Active blocking override(s): {list(active_blocking)}",
                    correlation_id=correlation_id,
                )
                self._write_audit_record(audit_record)

                raise ActiveOverrideError(
                    message=f"HARD_FAIL: Company {company_unique_id} has active blocking override(s): "
                            f"{list(active_blocking)}. Reasons: {eligibility.override_reasons}",
                    company_unique_id=company_unique_id,
                    error_code="SAFETY_GATE_OVERRIDE_ACTIVE",
                    effective_tier=eligibility.effective_tier,
                    override_snapshot=eligibility.to_override_snapshot(),
                )

        # =====================================================================
        # ALLOWED: Log successful eligibility check
        # =====================================================================
        audit_record = SendAttemptAuditRecord(
            company_unique_id=company_unique_id,
            campaign_id=campaign_id,
            effective_tier=eligibility.effective_tier,
            computed_tier=eligibility.computed_tier,
            override_snapshot=eligibility.to_override_snapshot(),
            status=SendAttemptStatus.ALLOWED.value,
            correlation_id=correlation_id,
        )
        self._write_audit_record(audit_record)

        logger.info(
            f"SAFETY_GATE_PASS: Company {company_unique_id} eligible for campaign {campaign_id}. "
            f"effective_tier={eligibility.effective_tier}"
        )

        return eligibility

    def record_send_result(
        self,
        company_unique_id: str,
        campaign_id: str,
        success: bool,
        error_message: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Record the result of a send attempt.

        Called AFTER the actual send to record success/failure.

        Args:
            company_unique_id: Company sent to
            campaign_id: Campaign ID
            success: Whether send succeeded
            error_message: Error message if failed
            correlation_id: Trace ID
        """
        audit_record = SendAttemptAuditRecord(
            company_unique_id=company_unique_id,
            campaign_id=campaign_id,
            effective_tier=-1,  # Not relevant for result logging
            computed_tier=-1,
            status=SendAttemptStatus.SENT.value if success else SendAttemptStatus.SEND_FAILED.value,
            failure_reason=error_message if not success else None,
            correlation_id=correlation_id,
        )
        self._write_audit_record(audit_record)

    # =========================================================================
    # ENFORCEMENT POINT: QUERY AUTHORITATIVE VIEW (NO FALLBACK)
    # =========================================================================

    def _query_eligibility_view(
        self,
        company_unique_id: str
    ) -> Optional[MarketingEligibilityResult]:
        """
        Query the AUTHORITATIVE view for eligibility.

        DOCTRINE: NO FALLBACK to underlying views or tables.
        If this query fails, the send MUST NOT proceed.
        """
        if not self._conn:
            logger.error("SAFETY_GATE: No database connection - HARD FAIL")
            return None

        query = f"""
            SELECT
                company_unique_id,
                effective_tier,
                computed_tier,
                has_active_override,
                override_types,
                override_reasons,
                tier_cap,
                overall_status,
                bit_score
            FROM {self.AUTHORITATIVE_VIEW}
            WHERE company_unique_id = %s
        """

        try:
            # Support both psycopg2 and asyncpg
            if hasattr(self._conn, 'cursor'):
                # psycopg2
                with self._conn.cursor() as cursor:
                    cursor.execute(query, (company_unique_id,))
                    row = cursor.fetchone()
                    if not row:
                        return None

                    columns = [desc[0] for desc in cursor.description]
                    data = dict(zip(columns, row))
            else:
                # This path should not be used in production sync code
                logger.error("SAFETY_GATE: Async connection not supported in sync context")
                return None

            return MarketingEligibilityResult(
                company_unique_id=str(data['company_unique_id']),
                effective_tier=int(data['effective_tier']),
                computed_tier=int(data['computed_tier']),
                has_active_override=bool(data['has_active_override']),
                override_types=data.get('override_types'),
                override_reasons=data.get('override_reasons'),
                tier_cap=data.get('tier_cap'),
                overall_status=str(data.get('overall_status', 'UNKNOWN')),
                bit_score=float(data.get('bit_score', 0)),
                raw_data=data,
            )

        except Exception as e:
            # HARD_FAIL: Log error but do NOT fallback
            logger.error(f"SAFETY_GATE: Failed to query {self.AUTHORITATIVE_VIEW}: {e}")
            return None

    # =========================================================================
    # AUDIT LOGGING (APPEND-ONLY)
    # =========================================================================

    def _write_audit_record(self, record: SendAttemptAuditRecord) -> None:
        """
        Write audit record to database (append-only).

        DOCTRINE: Every send attempt MUST be logged.
        This is append-only - no updates, no deletes.
        """
        if not self._conn:
            # Buffer for later if no connection
            self._audit_buffer.append(record)
            logger.warning(f"SAFETY_GATE: Audit record buffered (no connection): {record.audit_id}")
            return

        insert_query = """
            INSERT INTO outreach.send_attempt_audit (
                audit_id,
                company_unique_id,
                campaign_id,
                effective_tier,
                computed_tier,
                override_snapshot,
                status,
                failure_reason,
                correlation_id,
                created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """

        try:
            import json

            if hasattr(self._conn, 'cursor'):
                with self._conn.cursor() as cursor:
                    cursor.execute(insert_query, (
                        record.audit_id,
                        record.company_unique_id,
                        record.campaign_id,
                        record.effective_tier,
                        record.computed_tier,
                        json.dumps(record.override_snapshot),
                        record.status,
                        record.failure_reason,
                        record.correlation_id,
                        record.created_at,
                    ))
                self._conn.commit()

            logger.debug(f"SAFETY_GATE: Audit record written: {record.audit_id}")

        except Exception as e:
            # Log but don't fail - audit is critical but shouldn't block sends
            logger.error(f"SAFETY_GATE: Failed to write audit record: {e}")
            self._audit_buffer.append(record)

    def flush_audit_buffer(self) -> int:
        """Flush any buffered audit records. Returns count flushed."""
        if not self._conn or not self._audit_buffer:
            return 0

        count = 0
        for record in self._audit_buffer[:]:
            try:
                self._write_audit_record(record)
                self._audit_buffer.remove(record)
                count += 1
            except Exception as e:
                logger.error(f"Failed to flush audit record {record.audit_id}: {e}")

        return count


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_safety_gate(db_connection=None) -> MarketingSafetyGate:
    """Create a new MarketingSafetyGate instance."""
    return MarketingSafetyGate(db_connection)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Gate
    'MarketingSafetyGate',
    'create_safety_gate',
    # Results
    'MarketingEligibilityResult',
    'SendAttemptAuditRecord',
    'SendAttemptStatus',
    # Errors (HARD FAIL)
    'MarketingSafetyError',
    'IneligibleTierError',
    'MarketingDisabledError',
    'ActiveOverrideError',
    'EligibilityCheckError',
]
