"""
COMPANY TARGET — IMO GATE (DOCTRINE LOCK)
==========================================
PRD: Company Target (Execution Prep Sub-Hub) v3.0
Doctrine: Spine-First Architecture
Authoritative Diagrams: PRD_COMPANY_HUB.md §"Company Target Internal Logic (IMO)"

This module implements a SINGLE-PASS IMO.

HARD LAWS:
- Operates ONLY on outreach_id
- NEVER references sovereign_id or CL tables
- NEVER mints IDs
- NO fuzzy matching
- NO retries
- FAIL is terminal and written to outreach.company_target_errors

If this file violates the PRD v3.0 diagrams, the code is WRONG.

ENTRYPOINT:
    run_company_target_imo(outreach_id: UUID) -> None

Tool Registry: SNAP_ON_TOOLBOX.yaml (LOCKED)
    - TOOL-004: MXLookup (Tier 0 - FREE)
    - TOOL-005: SMTPCheck (Tier 0 - FREE)
    - TOOL-019: EmailVerifier (Tier 2 - GATED)
"""

import logging
import time
import dns.resolver
import smtplib
import socket
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Tuple
from uuid import UUID

# =============================================================================
# HARD GUARD - ENFORCE OUTREACH SPINE ONLY
# =============================================================================
ENFORCE_OUTREACH_SPINE_ONLY = True
assert ENFORCE_OUTREACH_SPINE_ONLY is True, "DOCTRINE VIOLATION: Spine enforcement disabled"

# NOTE:
# Company Target consumes Outreach Context via read-only view (outreach.v_context_current).
# It must never mutate shared context. It reads a SNAPSHOT, not a live query.
# Footprint growth happens UPSTREAM (CL) or ALONGSIDE (spine metadata), never DURING the IMO.

# =============================================================================
# CONFIGURATION
# =============================================================================

logger = logging.getLogger("company_target_imo")


class IMOStage(str, Enum):
    """IMO pipeline stages."""
    INPUT = "I"
    MIDDLE = "M"
    OUTPUT = "O"


class ErrorCode(str, Enum):
    """Company Target error codes per PRD v3.0."""
    # Input stage errors
    CT_I_NOT_FOUND = "CT-I-NOT-FOUND"
    CT_I_NO_DOMAIN = "CT-I-NO-DOMAIN"
    CT_I_ALREADY_PROCESSED = "CT-I-ALREADY-PROCESSED"

    # Middle stage errors
    CT_M_NO_MX = "CT-M-NO-MX"
    CT_M_NO_PATTERN = "CT-M-NO-PATTERN"
    CT_M_SMTP_FAIL = "CT-M-SMTP-FAIL"
    CT_M_VERIFY_FAIL = "CT-M-VERIFY-FAIL"


class MethodType(str, Enum):
    """Email pattern method types (fixed order per spec)."""
    FIRST_DOT_LAST = "first.last"
    FIRSTLAST = "firstlast"
    F_DOT_LAST = "f.last"
    FIRST_DOT_L = "first.l"
    FIRST = "first"
    LAST = "last"
    INFO = "info"
    CONTACT = "contact"


@dataclass
class SpineRecord:
    """Record from outreach.outreach spine (read-only)."""
    outreach_id: UUID
    domain: Optional[str]
    created_at: datetime


@dataclass
class IMOResult:
    """Result of IMO pass."""
    outreach_id: UUID
    success: bool
    stage: IMOStage
    email_method: Optional[str] = None
    method_type: Optional[MethodType] = None
    confidence_score: float = 0.0
    is_catchall: bool = False
    error_code: Optional[ErrorCode] = None
    error_reason: Optional[str] = None
    duration_ms: int = 0
    tools_used: List[str] = field(default_factory=list)


# =============================================================================
# DATABASE OPERATIONS (outreach.* ONLY)
# =============================================================================

def _get_db_connection():
    """Get database connection via Doppler secrets."""
    import os
    import psycopg2

    return psycopg2.connect(
        host=os.environ.get("NEON_HOST"),
        database=os.environ.get("NEON_DATABASE"),
        user=os.environ.get("NEON_USER"),
        password=os.environ.get("NEON_PASSWORD"),
        sslmode="require"
    )


def _load_spine_record(outreach_id: UUID) -> Optional[SpineRecord]:
    """
    Load record from outreach.outreach spine.

    HARD LAW: Read from spine ONLY. Never touch CL tables.
    """
    conn = _get_db_connection()
    try:
        with conn.cursor() as cur:
            # ONLY read from outreach.outreach - NEVER CL
            cur.execute("""
                SELECT outreach_id, domain, created_at
                FROM outreach.outreach
                WHERE outreach_id = %s
            """, (str(outreach_id),))

            row = cur.fetchone()
            if row:
                return SpineRecord(
                    outreach_id=UUID(str(row[0])),
                    domain=row[1],
                    created_at=row[2]
                )
            return None
    finally:
        conn.close()


def _check_already_processed(outreach_id: UUID) -> Tuple[bool, Optional[str]]:
    """
    Check if outreach_id was already processed (PASS or FAIL).

    Returns: (is_processed, status)
    """
    conn = _get_db_connection()
    try:
        with conn.cursor() as cur:
            # Check company_target for existing result
            cur.execute("""
                SELECT execution_status
                FROM outreach.company_target
                WHERE outreach_id = %s
                  AND execution_status IN ('ready', 'failed')
            """, (str(outreach_id),))

            row = cur.fetchone()
            if row:
                return True, row[0]

            # Check error table for existing failure
            cur.execute("""
                SELECT failure_code
                FROM outreach.company_target_errors
                WHERE outreach_id = %s
                  AND resolved_at IS NULL
            """, (str(outreach_id),))

            row = cur.fetchone()
            if row:
                return True, "failed"

            return False, None
    finally:
        conn.close()


def _write_pass(result: IMOResult) -> None:
    """
    Write PASS result to outreach.company_target.

    HARD LAW: Only write to outreach.* tables.
    """
    assert ENFORCE_OUTREACH_SPINE_ONLY, "DOCTRINE VIOLATION"

    conn = _get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE outreach.company_target
                SET email_method = %s,
                    method_type = %s,
                    confidence_score = %s,
                    execution_status = 'ready',
                    is_catchall = %s,
                    imo_completed_at = NOW(),
                    updated_at = NOW()
                WHERE outreach_id = %s
            """, (
                result.email_method,
                result.method_type.value if result.method_type else None,
                result.confidence_score,
                result.is_catchall,
                str(result.outreach_id)
            ))

            # If no row updated, insert new record
            if cur.rowcount == 0:
                cur.execute("""
                    INSERT INTO outreach.company_target (
                        outreach_id, email_method, method_type,
                        confidence_score, execution_status, is_catchall,
                        imo_completed_at, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, 'ready', %s, NOW(), NOW(), NOW()
                    )
                """, (
                    str(result.outreach_id),
                    result.email_method,
                    result.method_type.value if result.method_type else None,
                    result.confidence_score,
                    result.is_catchall
                ))

            conn.commit()
            logger.info(f"PASS: {result.outreach_id} -> outreach.company_target")
    finally:
        conn.close()


def _write_fail(result: IMOResult) -> None:
    """
    Write FAIL result to outreach.company_target_errors.

    HARD LAW:
    - Only write to outreach.* tables
    - FAIL is FOREVER - no retry
    """
    assert ENFORCE_OUTREACH_SPINE_ONLY, "DOCTRINE VIOLATION"

    conn = _get_db_connection()
    try:
        with conn.cursor() as cur:
            # Write to error table
            cur.execute("""
                INSERT INTO outreach.company_target_errors (
                    outreach_id, pipeline_stage, failure_code,
                    blocking_reason, severity, imo_stage,
                    retry_allowed, created_at
                ) VALUES (
                    %s, 'company_target_imo', %s, %s, 'blocking', %s, FALSE, NOW()
                )
            """, (
                str(result.outreach_id),
                result.error_code.value if result.error_code else "UNKNOWN",
                result.error_reason or "Unknown error",
                result.stage.value
            ))

            # Also update company_target status if exists
            cur.execute("""
                UPDATE outreach.company_target
                SET execution_status = 'failed',
                    imo_completed_at = NOW(),
                    updated_at = NOW()
                WHERE outreach_id = %s
            """, (str(result.outreach_id),))

            conn.commit()
            logger.warning(f"FAIL: {result.outreach_id} -> outreach.company_target_errors [{result.error_code}]")
    finally:
        conn.close()


# =============================================================================
# I — INPUT STAGE (SPINE ASSERT)
# =============================================================================

def _input_stage(outreach_id: UUID) -> Tuple[Optional[SpineRecord], Optional[IMOResult]]:
    """
    INPUT stage: Load and validate from spine.

    Rules:
    - If outreach_id not found -> CT-I-NOT-FOUND -> FAIL
    - If domain missing -> CT-I-NO-DOMAIN -> FAIL
    - Do NOT touch CL tables
    - Do NOT read sovereign_id
    """
    logger.info(f"[I] INPUT stage: {outreach_id}")

    # Check if already processed (idempotency)
    is_processed, status = _check_already_processed(outreach_id)
    if is_processed:
        logger.info(f"[I] Already processed ({status}), exiting")
        return None, IMOResult(
            outreach_id=outreach_id,
            success=False,
            stage=IMOStage.INPUT,
            error_code=ErrorCode.CT_I_ALREADY_PROCESSED,
            error_reason=f"Already processed with status: {status}"
        )

    # Load from spine
    spine = _load_spine_record(outreach_id)

    if spine is None:
        return None, IMOResult(
            outreach_id=outreach_id,
            success=False,
            stage=IMOStage.INPUT,
            error_code=ErrorCode.CT_I_NOT_FOUND,
            error_reason="outreach_id not found in spine"
        )

    if not spine.domain:
        return None, IMOResult(
            outreach_id=outreach_id,
            success=False,
            stage=IMOStage.INPUT,
            error_code=ErrorCode.CT_I_NO_DOMAIN,
            error_reason="No domain in spine record"
        )

    logger.info(f"[I] Loaded: domain={spine.domain}")
    return spine, None


# =============================================================================
# M — MIDDLE (EMAIL METHOD ENGINE)
# =============================================================================

def _mx_lookup(domain: str) -> bool:
    """
    M1 — MX Gate (TOOL-004: MXLookup)

    Tool: dnspython (Tier 0 - FREE)
    Throttle: 50/second, 50000/day
    """
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        return len(answers) > 0
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        return False
    except Exception as e:
        logger.warning(f"MX lookup error for {domain}: {e}")
        return False


def _generate_patterns(domain: str) -> List[Tuple[str, MethodType]]:
    """
    M2 — Pattern Generation (No Tool)

    Generate patterns in FIXED ORDER per spec.
    """
    patterns = [
        (f"{{first}}.{{last}}@{domain}", MethodType.FIRST_DOT_LAST),
        (f"{{first}}{{last}}@{domain}", MethodType.FIRSTLAST),
        (f"{{f}}.{{last}}@{domain}", MethodType.F_DOT_LAST),
        (f"{{first}}.{{l}}@{domain}", MethodType.FIRST_DOT_L),
        (f"{{first}}@{domain}", MethodType.FIRST),
        (f"{{last}}@{domain}", MethodType.LAST),
        (f"info@{domain}", MethodType.INFO),
        (f"contact@{domain}", MethodType.CONTACT),
    ]
    return patterns


def _smtp_check(email: str, domain: str) -> Tuple[str, bool]:
    """
    M3 — SMTP Validation (TOOL-005: SMTPCheck)

    Tool: smtplib (stdlib, Tier 0 - FREE)
    Throttle: 1 per domain per 2s, 10000/day

    Returns: (result_type, is_catchall)
    - "accept" = strong accept
    - "reject" = rejected
    - "catchall" = accepts all
    - "error" = connection error
    """
    try:
        # Get MX record
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_host = str(mx_records[0].exchange).rstrip('.')

        # Connect to mail server
        with smtplib.SMTP(mx_host, 25, timeout=10) as server:
            server.ehlo()

            # Test with sender
            code, _ = server.mail('test@example.com')
            if code != 250:
                return "error", False

            # Test recipient
            code, message = server.rcpt(email)

            if code == 250:
                # Check for catch-all by testing invalid address
                fake_email = f"definitely_invalid_xyz123@{domain}"
                fake_code, _ = server.rcpt(fake_email)

                if fake_code == 250:
                    return "catchall", True
                return "accept", False
            elif code in (550, 551, 552, 553, 554):
                return "reject", False
            else:
                return "error", False

    except socket.timeout:
        return "error", False
    except Exception as e:
        logger.warning(f"SMTP check error for {email}: {e}")
        return "error", False


def _middle_stage(spine: SpineRecord) -> IMOResult:
    """
    MIDDLE stage: Email Method Engine

    Steps:
    - M1: MX Gate
    - M2: Pattern Generation
    - M3: SMTP Validation
    - M4: Catch-All Handling

    Rules:
    - Stop on first strong accept
    - One pass only
    - Respect tool throttles
    """
    logger.info(f"[M] MIDDLE stage: {spine.outreach_id}")
    tools_used = []
    domain = spine.domain

    # M1 — MX Gate
    logger.info(f"[M1] MX lookup for {domain}")
    tools_used.append("TOOL-004:MXLookup")

    if not _mx_lookup(domain):
        return IMOResult(
            outreach_id=spine.outreach_id,
            success=False,
            stage=IMOStage.MIDDLE,
            error_code=ErrorCode.CT_M_NO_MX,
            error_reason=f"No MX records for domain: {domain}",
            tools_used=tools_used
        )

    # M2 — Pattern Generation
    logger.info(f"[M2] Generating patterns for {domain}")
    patterns = _generate_patterns(domain)

    # M3 — SMTP Validation
    logger.info(f"[M3] SMTP validation for {domain}")
    tools_used.append("TOOL-005:SMTPCheck")

    is_catchall = False
    found_pattern = None
    found_method = None

    for pattern, method_type in patterns:
        # Throttle: 1 per domain per 2s
        time.sleep(2)

        result, catchall = _smtp_check(pattern, domain)

        if result == "accept":
            found_pattern = pattern
            found_method = method_type
            logger.info(f"[M3] ACCEPT: {pattern}")
            break
        elif result == "catchall":
            is_catchall = True
            # M4 — Catch-All Handling: use first.last
            if found_pattern is None:
                found_pattern = patterns[0][0]  # first.last
                found_method = patterns[0][1]
                logger.info(f"[M3] CATCHALL: defaulting to {found_pattern}")
            break
        elif result == "reject":
            logger.info(f"[M3] REJECT: {pattern}")
            continue
        else:
            # Error - try next
            continue

    # Check if we found a pattern
    if found_pattern is None:
        return IMOResult(
            outreach_id=spine.outreach_id,
            success=False,
            stage=IMOStage.MIDDLE,
            error_code=ErrorCode.CT_M_NO_PATTERN,
            error_reason=f"No valid email pattern found for {domain}",
            tools_used=tools_used
        )

    # Calculate confidence
    if is_catchall:
        confidence = 0.5  # Reduced confidence for catch-all
    elif found_method == MethodType.FIRST_DOT_LAST:
        confidence = 0.95
    elif found_method in (MethodType.FIRSTLAST, MethodType.F_DOT_LAST, MethodType.FIRST_DOT_L):
        confidence = 0.90
    elif found_method in (MethodType.FIRST, MethodType.LAST):
        confidence = 0.85
    else:
        confidence = 0.70  # info/contact

    return IMOResult(
        outreach_id=spine.outreach_id,
        success=True,
        stage=IMOStage.MIDDLE,
        email_method=found_pattern,
        method_type=found_method,
        confidence_score=confidence,
        is_catchall=is_catchall,
        tools_used=tools_used
    )


# =============================================================================
# O — OUTPUT
# =============================================================================

def _output_stage(result: IMOResult) -> None:
    """
    OUTPUT stage: Route to PASS or FAIL table.

    PASS -> outreach.company_target
    FAIL -> outreach.company_target_errors -> STOP FOREVER
    """
    logger.info(f"[O] OUTPUT stage: success={result.success}")

    if result.success:
        _write_pass(result)
    else:
        _write_fail(result)


# =============================================================================
# ENTRYPOINT
# =============================================================================

def run_company_target_imo(outreach_id: UUID) -> None:
    """
    Single-pass IMO gate for Company Target.

    This is the ONLY way Company Target runs.

    HARD LAWS:
    - Operate ONLY on outreach_id
    - NEVER reference sovereign_id
    - NEVER mint any IDs
    - NO fuzzy matching
    - NO retries
    - ONE IMO pass per outreach_id
    - FAIL -> write to outreach.company_target_errors -> STOP FOREVER

    Args:
        outreach_id: UUID from outreach.outreach spine
    """
    assert ENFORCE_OUTREACH_SPINE_ONLY is True, "DOCTRINE VIOLATION"

    start_time = time.time()
    logger.info(f"=== IMO START: {outreach_id} ===")

    try:
        # I — INPUT
        spine, error_result = _input_stage(outreach_id)

        if error_result:
            # Already processed or input error
            if error_result.error_code != ErrorCode.CT_I_ALREADY_PROCESSED:
                error_result.duration_ms = int((time.time() - start_time) * 1000)
                _output_stage(error_result)
            return

        # M — MIDDLE
        result = _middle_stage(spine)
        result.duration_ms = int((time.time() - start_time) * 1000)

        # O — OUTPUT
        _output_stage(result)

    except Exception as e:
        logger.exception(f"IMO EXCEPTION: {outreach_id}")
        error_result = IMOResult(
            outreach_id=outreach_id,
            success=False,
            stage=IMOStage.MIDDLE,
            error_code=ErrorCode.CT_M_SMTP_FAIL,
            error_reason=f"Unexpected error: {str(e)}",
            duration_ms=int((time.time() - start_time) * 1000)
        )
        _output_stage(error_result)

    finally:
        duration = int((time.time() - start_time) * 1000)
        logger.info(f"=== IMO END: {outreach_id} ({duration}ms) ===")


# =============================================================================
# BATCH RUNNER (for processing queue)
# =============================================================================

def run_pending_batch(limit: int = 100) -> int:
    """
    Process pending outreach records through IMO.

    Returns: Number of records processed
    """
    conn = _get_db_connection()
    processed = 0

    try:
        with conn.cursor() as cur:
            # Get pending records from spine that haven't been processed
            cur.execute("""
                SELECT o.outreach_id
                FROM outreach.outreach o
                LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
                LEFT JOIN outreach.company_target_errors cte ON o.outreach_id = cte.outreach_id
                WHERE o.domain IS NOT NULL
                  AND (ct.outreach_id IS NULL OR ct.execution_status = 'pending')
                  AND cte.outreach_id IS NULL
                LIMIT %s
            """, (limit,))

            rows = cur.fetchall()

        for row in rows:
            outreach_id = UUID(str(row[0]))
            run_company_target_imo(outreach_id)
            processed += 1

    finally:
        conn.close()

    logger.info(f"Batch complete: {processed} records processed")
    return processed


if __name__ == "__main__":
    # CLI usage
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    if len(sys.argv) > 1:
        outreach_id = UUID(sys.argv[1])
        run_company_target_imo(outreach_id)
    else:
        print("Usage: python company_target_imo.py <outreach_id>")
        print("       python company_target_imo.py --batch [limit]")
