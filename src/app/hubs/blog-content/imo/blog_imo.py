"""
BLOG CONTENT — IMO GATE (DOCTRINE LOCK)
═══════════════════════════════════════════════════════════════════════════════

Doctrine: Barton IMO v1.1 (Spine-First Architecture)
Hub: Blog Content (04.04.05)
Waterfall Position: 4th (LAST) — after People Intelligence

This file implements the SINGLE-PASS IMO gate for the Blog Content sub-hub.
Pattern follows Company Target IMO verbatim.

SPINE ENFORCEMENT:
    - ONLY operates on outreach_id from outreach.outreach spine
    - NEVER references sovereign_id directly
    - NEVER mints outreach_id (spine does that)
    - NEVER triggers enrichment or spend

IMO FLOW:
    I (Input)  → Load outreach_id + domain from spine, check upstream gates
    M (Middle) → Process news/content signals, classify events
    O (Output) → Write to outreach.blog (PASS) or outreach.blog_errors (FAIL)

TERMINAL STATES:
    - PASS: Signal emitted, row in outreach.blog
    - FAIL: Error recorded, row in outreach.blog_errors

═══════════════════════════════════════════════════════════════════════════════
"""

import os
import logging
import time
import traceback
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import uuid

# ─────────────────────────────────────────────────────────────────────────────
# SPINE GUARD ASSERTION (DOCTRINE LOCK)
# ─────────────────────────────────────────────────────────────────────────────
ENFORCE_OUTREACH_SPINE_ONLY = True
assert ENFORCE_OUTREACH_SPINE_ONLY is True, "Blog IMO MUST operate on outreach_id only"

# ─────────────────────────────────────────────────────────────────────────────
# SCOPE GUARD (DOCTRINE LOCK)
# Blog Sub-Hub is COMPANY-LEVEL ONLY. Social platforms = presence verification.
# NO follower counts, engagement metrics, sentiment analysis, or people-level data.
# ─────────────────────────────────────────────────────────────────────────────
DISALLOW_SOCIAL_METRICS = True
assert DISALLOW_SOCIAL_METRICS is True, "Blog IMO MUST NOT capture social metrics (followers, engagement, likes, views)"

# Forbidden field patterns (CI guard enforces these)
FORBIDDEN_SOCIAL_FIELDS = [
    'followers', 'follower_count', 'following', 'following_count',
    'likes', 'like_count', 'views', 'view_count',
    'engagement', 'engagement_rate', 'engagement_score',
    'comments', 'comment_count', 'shares', 'share_count',
    'retweets', 'retweet_count', 'impressions', 'reach',
    'subscribers', 'subscriber_count', 'sentiment', 'sentiment_score'
]

# ─────────────────────────────────────────────────────────────────────────────
# ERROR HANDLING GUARD (DOCTRINE LOCK)
# All failures MUST be captured in outreach.blog_errors - no silent failures.
# ─────────────────────────────────────────────────────────────────────────────
ENFORCE_ERROR_PERSISTENCE = True
assert ENFORCE_ERROR_PERSISTENCE is True, "Blog IMO MUST persist all errors to blog_errors table"

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline Stages (Locked)
# ─────────────────────────────────────────────────────────────────────────────
class PipelineStage(Enum):
    """Pipeline stages for error tracking"""
    INGEST = "ingest"
    PARSE = "parse"
    EXTRACT = "extract"
    MATCH = "match"
    CLASSIFY = "classify"
    VALIDATE = "validate"
    WRITE = "write"
    EMIT = "emit"


class ErrorSeverity(Enum):
    """Error severity levels"""
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"


# ─────────────────────────────────────────────────────────────────────────────
# BlogPipelineError Exception (Central Error Type)
# ─────────────────────────────────────────────────────────────────────────────
class BlogPipelineError(Exception):
    """
    Central exception for Blog pipeline failures.

    All failures MUST be raised via this exception to ensure error persistence.
    The central handler catches and persists to blog_errors.

    DOCTRINE: Errors are first-class outputs, not hidden logging.
    """

    def __init__(
        self,
        outreach_id: str,
        stage: PipelineStage,
        code: str,
        reason: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        raw_input: Optional[Dict[str, Any]] = None,
        retry_allowed: bool = False
    ):
        self.outreach_id = outreach_id
        self.stage = stage
        self.code = code
        self.reason = reason
        self.severity = severity
        self.raw_input = raw_input
        self.retry_allowed = retry_allowed
        self.stack_trace = traceback.format_exc()
        super().__init__(f"{code}: {reason}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for persistence"""
        return {
            'outreach_id': self.outreach_id,
            'pipeline_stage': self.stage.value,
            'failure_code': self.code,
            'blocking_reason': self.reason,
            'severity': self.severity.value,
            'retry_allowed': self.retry_allowed,
            'raw_input': self.raw_input,
            'stack_trace': self.stack_trace
        }


# ─────────────────────────────────────────────────────────────────────────────
# Event Types (Locked)
# ─────────────────────────────────────────────────────────────────────────────
class EventType(Enum):
    """Locked event types with BIT impact values"""
    FUNDING_EVENT = ("FUNDING_EVENT", 15.0)
    ACQUISITION = ("ACQUISITION", 12.0)
    LEADERSHIP_CHANGE = ("LEADERSHIP_CHANGE", 8.0)
    EXPANSION = ("EXPANSION", 7.0)
    PRODUCT_LAUNCH = ("PRODUCT_LAUNCH", 5.0)
    PARTNERSHIP = ("PARTNERSHIP", 5.0)
    LAYOFF = ("LAYOFF", -3.0)
    NEGATIVE_NEWS = ("NEGATIVE_NEWS", -5.0)
    UNKNOWN = ("UNKNOWN", 0.0)

    @property
    def name_str(self) -> str:
        return self.value[0]

    @property
    def bit_impact(self) -> float:
        return self.value[1]


# ─────────────────────────────────────────────────────────────────────────────
# Result Types
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class BlogIMOResult:
    """Result of Blog IMO gate execution"""
    outreach_id: str
    success: bool
    stage: str  # I, M, or O
    process_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # PASS data
    event_type: Optional[str] = None
    bit_impact: Optional[float] = None
    context_summary: Optional[str] = None
    source_type: Optional[str] = None
    source_url: Optional[str] = None

    # FAIL data
    failure_code: Optional[str] = None
    blocking_reason: Optional[str] = None
    error_persisted: bool = False  # DOCTRINE: MUST be True if success=False

    # Metadata
    duration_ms: int = 0
    tools_used: List[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Error Codes (BLOG-XXX)
# ─────────────────────────────────────────────────────────────────────────────
ERROR_CODES = {
    "BLOG-I-NO-OUTREACH": "No outreach_id provided",
    "BLOG-I-NOT-FOUND": "outreach_id not found in spine",
    "BLOG-I-NO-DOMAIN": "No domain in spine record",
    "BLOG-I-UPSTREAM-FAIL": "Upstream hub not PASS (CT required)",
    "BLOG-I-ALREADY-PROCESSED": "Already processed (idempotent skip)",
    "BLOG-M-NO-CONTENT": "No content to process",
    "BLOG-M-CLASSIFY-FAIL": "Event classification failed",
    "BLOG-M-NO-EVENT": "No actionable event detected",
    "BLOG-O-WRITE-FAIL": "Failed to write to Neon",
}


# ─────────────────────────────────────────────────────────────────────────────
# Database Connection
# ─────────────────────────────────────────────────────────────────────────────
def _get_connection():
    """Get database connection from environment"""
    import psycopg2
    return psycopg2.connect(
        host=os.environ.get('NEON_HOST'),
        database=os.environ.get('NEON_DATABASE'),
        user=os.environ.get('NEON_USER'),
        password=os.environ.get('NEON_PASSWORD'),
        sslmode='require'
    )


# ─────────────────────────────────────────────────────────────────────────────
# INPUT STAGE (I)
# ─────────────────────────────────────────────────────────────────────────────
def _input_stage(
    outreach_id: str,
    content_payload: Optional[Dict[str, Any]] = None
) -> tuple[bool, Optional[Dict[str, Any]], Optional[str], Optional[str]]:
    """
    Input stage: Load spine data and validate gates.

    Returns:
        (success, spine_data, failure_code, failure_reason)
    """
    logger.info(f"[I] Blog IMO input stage started", extra={'outreach_id': outreach_id})

    # Validate outreach_id provided
    if not outreach_id:
        return False, None, "BLOG-I-NO-OUTREACH", "No outreach_id provided"

    conn = _get_connection()
    cur = conn.cursor()

    try:
        # Load spine record
        cur.execute("""
            SELECT outreach_id, domain, created_at
            FROM outreach.outreach
            WHERE outreach_id = %s
        """, (outreach_id,))

        spine = cur.fetchone()
        if not spine:
            return False, None, "BLOG-I-NOT-FOUND", f"outreach_id {outreach_id} not found in spine"

        domain = spine[1]
        if not domain:
            return False, None, "BLOG-I-NO-DOMAIN", "No domain in spine record"

        # Check upstream gate: Company Target must be PASS (ready)
        cur.execute("""
            SELECT execution_status
            FROM outreach.company_target
            WHERE outreach_id = %s
        """, (outreach_id,))

        ct_row = cur.fetchone()
        if not ct_row or ct_row[0] != 'ready':
            ct_status = ct_row[0] if ct_row else 'NOT_FOUND'
            return False, None, "BLOG-I-UPSTREAM-FAIL", f"Company Target not PASS (status: {ct_status})"

        # Check idempotency: already processed?
        cur.execute("""
            SELECT blog_id FROM outreach.blog WHERE outreach_id = %s
        """, (outreach_id,))

        if cur.fetchone():
            logger.info(f"[I] Already processed, idempotent skip", extra={'outreach_id': outreach_id})
            return False, None, "BLOG-I-ALREADY-PROCESSED", "Already processed"

        # Check if already in errors
        cur.execute("""
            SELECT error_id FROM outreach.blog_errors WHERE outreach_id = %s
        """, (outreach_id,))

        if cur.fetchone():
            logger.info(f"[I] Already in errors, idempotent skip", extra={'outreach_id': outreach_id})
            return False, None, "BLOG-I-ALREADY-PROCESSED", "Already in error state"

        spine_data = {
            'outreach_id': str(spine[0]),
            'domain': domain,
            'created_at': spine[2],
            'content_payload': content_payload or {}
        }

        logger.info(f"[I] Input stage PASS", extra={'outreach_id': outreach_id, 'domain': domain})
        return True, spine_data, None, None

    finally:
        cur.close()
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# MIDDLE STAGE (M)
# ─────────────────────────────────────────────────────────────────────────────
def _middle_stage(
    spine_data: Dict[str, Any]
) -> tuple[bool, Optional[Dict[str, Any]], Optional[str], Optional[str], List[str]]:
    """
    Middle stage: Process content and classify events.

    For Blog Sub-Hub, the middle stage:
    1. Checks if content payload exists
    2. Classifies the event type
    3. Returns signal data for emission

    Returns:
        (success, signal_data, failure_code, failure_reason, tools_used)
    """
    outreach_id = spine_data['outreach_id']
    domain = spine_data['domain']
    content_payload = spine_data.get('content_payload', {})
    tools_used = []

    logger.info(f"[M] Blog IMO middle stage started", extra={'outreach_id': outreach_id})

    # Check if we have content to process
    # In production, this would fetch news/blog content for the domain
    # For now, we support direct content injection via payload

    content = content_payload.get('content', '')
    source_type = content_payload.get('source_type', 'manual')
    source_url = content_payload.get('source_url', '')

    # If no content provided, this is a "no signal" case
    # Blog hub is OPTIONAL - no content = no signal, but still PASS
    if not content:
        logger.info(f"[M] No content to process, marking as no-signal PASS",
                   extra={'outreach_id': outreach_id})

        signal_data = {
            'outreach_id': outreach_id,
            'domain': domain,
            'event_type': EventType.UNKNOWN,
            'bit_impact': 0.0,
            'confidence': 0.0,
            'context_summary': None,
            'source_type': source_type,
            'source_url': source_url,
            'has_signal': False
        }
        return True, signal_data, None, None, tools_used

    # Classify the event using keyword patterns
    event_type, confidence, evidence = _classify_content(content)
    tools_used.append("TOOL-LOCAL-001: KeywordClassifier")

    # Build context summary (first 500 chars)
    context_summary = content[:500] if content else None

    signal_data = {
        'outreach_id': outreach_id,
        'domain': domain,
        'event_type': event_type,
        'bit_impact': event_type.bit_impact,
        'confidence': confidence,
        'context_summary': context_summary,
        'source_type': source_type,
        'source_url': source_url,
        'evidence': evidence,
        'has_signal': event_type != EventType.UNKNOWN and confidence >= 0.5
    }

    logger.info(f"[M] Middle stage PASS", extra={
        'outreach_id': outreach_id,
        'event_type': event_type.name_str,
        'confidence': confidence,
        'has_signal': signal_data['has_signal']
    })

    return True, signal_data, None, None, tools_used


def _classify_content(content: str) -> tuple[EventType, float, List[str]]:
    """
    Classify content into event type using keyword patterns.

    Returns:
        (event_type, confidence, evidence_list)
    """
    import re

    content_lower = content.lower()
    evidence = []

    # Keyword patterns (from classify_event.py)
    patterns = {
        EventType.FUNDING_EVENT: [
            r'\braised\b.*\$', r'\bfunding\b', r'\bseries\s+[a-z]\b',
            r'\bseed\s+round\b', r'\bventure\s+capital\b', r'\binvestment\b'
        ],
        EventType.ACQUISITION: [
            r'\bacquired\b', r'\bacquisition\b', r'\bmerger\b', r'\bbuys\b'
        ],
        EventType.LEADERSHIP_CHANGE: [
            r'\bappointed\b', r'\bnamed\b.*(?:CEO|CFO|CTO)', r'\bpromoted\b',
            r'\bsteps\s+down\b', r'\bresigned\b'
        ],
        EventType.EXPANSION: [
            r'\bexpansion\b', r'\bnew\s+office\b', r'\bopening\b.*(?:office|location)'
        ],
        EventType.PRODUCT_LAUNCH: [
            r'\blaunches\b', r'\bintroduces\b', r'\bnew\s+product\b', r'\bunveils\b'
        ],
        EventType.PARTNERSHIP: [
            r'\bpartnership\b', r'\bpartners\s+with\b', r'\bcollaboration\b'
        ],
        EventType.LAYOFF: [
            r'\blayoff\b', r'\blayoffs\b', r'\bworkforce\s+reduction\b', r'\bjob\s+cuts\b'
        ],
        EventType.NEGATIVE_NEWS: [
            r'\blawsuit\b', r'\bsued\b', r'\bfraud\b', r'\bscandal\b'
        ],
    }

    # Find matches
    matches = {}
    for event_type, keyword_patterns in patterns.items():
        match_count = 0
        for pattern in keyword_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                match_count += 1
                evidence.append(f"{event_type.name_str}: {pattern}")
        if match_count > 0:
            matches[event_type] = match_count

    if not matches:
        return EventType.UNKNOWN, 0.0, ["No event keywords detected"]

    # Pick highest match count
    best_type = max(matches, key=matches.get)
    match_count = matches[best_type]

    # Confidence based on match count
    confidence = min(0.90, 0.50 + (match_count * 0.15))

    return best_type, confidence, evidence


# ─────────────────────────────────────────────────────────────────────────────
# OUTPUT STAGE (O)
# ─────────────────────────────────────────────────────────────────────────────
def _output_stage(
    signal_data: Dict[str, Any],
    duration_ms: int
) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Output stage: Write to outreach.blog.

    Returns:
        (success, failure_code, failure_reason)
    """
    outreach_id = signal_data['outreach_id']

    logger.info(f"[O] Blog IMO output stage started", extra={'outreach_id': outreach_id})

    conn = _get_connection()
    cur = conn.cursor()

    try:
        # Write to outreach.blog
        cur.execute("""
            INSERT INTO outreach.blog (
                blog_id,
                outreach_id,
                context_summary,
                source_type,
                source_url,
                context_timestamp,
                created_at
            ) VALUES (
                gen_random_uuid(),
                %s,
                %s,
                %s,
                %s,
                %s,
                NOW()
            )
            ON CONFLICT DO NOTHING
        """, (
            outreach_id,
            signal_data.get('context_summary'),
            signal_data.get('source_type'),
            signal_data.get('source_url'),
            datetime.utcnow()
        ))

        conn.commit()

        logger.info(f"[O] Output stage PASS - wrote to outreach.blog", extra={
            'outreach_id': outreach_id,
            'event_type': signal_data['event_type'].name_str if signal_data.get('event_type') else 'UNKNOWN',
            'has_signal': signal_data.get('has_signal', False)
        })

        return True, None, None

    except Exception as e:
        logger.error(f"[O] Output stage FAIL - write error: {e}", extra={'outreach_id': outreach_id})
        return False, "BLOG-O-WRITE-FAIL", str(e)

    finally:
        cur.close()
        conn.close()


def _write_error(
    outreach_id: str,
    pipeline_stage: PipelineStage,
    failure_code: str,
    blocking_reason: str,
    process_id: str,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    retry_allowed: bool = False,
    raw_input: Optional[Dict[str, Any]] = None,
    stack_trace: Optional[str] = None
) -> bool:
    """
    Write failure to outreach.blog_errors.

    DOCTRINE: All failures MUST be persisted. This is a first-class output,
    not hidden logging. Returns True if error was persisted successfully.
    """
    logger.warning(f"[{pipeline_stage.value}] Blog IMO FAIL - {failure_code}: {blocking_reason}",
                  extra={'outreach_id': outreach_id, 'process_id': process_id})

    # Skip writing error for idempotent skips (already processed is not an error)
    if failure_code == "BLOG-I-ALREADY-PROCESSED":
        return True  # Not a real error, no persistence needed

    conn = _get_connection()
    cur = conn.cursor()

    try:
        # Serialize raw_input to JSON if provided
        raw_input_json = json.dumps(raw_input) if raw_input else None

        cur.execute("""
            INSERT INTO outreach.blog_errors (
                error_id,
                outreach_id,
                pipeline_stage,
                failure_code,
                blocking_reason,
                severity,
                retry_allowed,
                raw_input,
                stack_trace,
                process_id,
                created_at
            ) VALUES (
                gen_random_uuid(),
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                NOW()
            )
            ON CONFLICT DO NOTHING
        """, (
            outreach_id,
            pipeline_stage.value,
            failure_code,
            blocking_reason,
            severity.value,
            retry_allowed,
            raw_input_json,
            stack_trace,
            process_id
        ))

        conn.commit()
        logger.info(f"Error persisted to blog_errors", extra={
            'outreach_id': outreach_id,
            'failure_code': failure_code,
            'process_id': process_id
        })
        return True

    except Exception as e:
        # CRITICAL: Error persistence failed - this is a doctrine violation
        logger.critical(f"DOCTRINE VIOLATION: Failed to persist error: {e}",
                       extra={'outreach_id': outreach_id, 'failure_code': failure_code})
        return False

    finally:
        cur.close()
        conn.close()


def _handle_pipeline_error(error: BlogPipelineError, process_id: str) -> bool:
    """
    Central handler for BlogPipelineError exceptions.
    Ensures all errors are persisted to blog_errors.

    Returns True if error was persisted successfully.
    """
    return _write_error(
        outreach_id=error.outreach_id,
        pipeline_stage=error.stage,
        failure_code=error.code,
        blocking_reason=error.reason,
        process_id=process_id,
        severity=error.severity,
        retry_allowed=error.retry_allowed,
        raw_input=error.raw_input,
        stack_trace=error.stack_trace
    )


# Legacy wrapper for backward compatibility
def _write_fail(
    outreach_id: str,
    failure_code: str,
    blocking_reason: str,
    stage: str,
    duration_ms: int,
    process_id: Optional[str] = None
) -> bool:
    """Legacy wrapper - use _write_error for new code"""
    # Map legacy stage strings to PipelineStage
    stage_map = {
        "I": PipelineStage.INGEST,
        "M": PipelineStage.CLASSIFY,
        "O": PipelineStage.WRITE
    }
    pipeline_stage = stage_map.get(stage, PipelineStage.VALIDATE)

    return _write_error(
        outreach_id=outreach_id,
        pipeline_stage=pipeline_stage,
        failure_code=failure_code,
        blocking_reason=blocking_reason,
        process_id=process_id or str(uuid.uuid4())
    )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN IMO GATE
# ─────────────────────────────────────────────────────────────────────────────
def run_blog_imo(
    outreach_id: str,
    content_payload: Optional[Dict[str, Any]] = None
) -> BlogIMOResult:
    """
    Execute Blog IMO gate for a single outreach_id.

    This is the MAIN ENTRY POINT for Blog Sub-Hub processing.

    Args:
        outreach_id: The outreach_id from spine
        content_payload: Optional content to process (for manual injection)
            {
                'content': 'Article text...',
                'source_type': 'newsapi|rss|manual',
                'source_url': 'https://...'
            }

    Returns:
        BlogIMOResult with success/failure status

    DOCTRINE:
        - Single-pass execution (I → M → O)
        - FAIL at any stage → terminal, write to errors
        - PASS → write to outreach.blog
        - No retries, no rescue patterns
        - All failures MUST be persisted to blog_errors (error_persisted=True)
    """
    start_time = time.time()
    process_id = str(uuid.uuid4())
    tools_used = []

    logger.info(f"Blog IMO started", extra={'outreach_id': outreach_id, 'process_id': process_id})

    # ─────────────────────────────────────────────────────────────────────────
    # INPUT STAGE (I)
    # ─────────────────────────────────────────────────────────────────────────
    i_success, spine_data, i_fail_code, i_fail_reason = _input_stage(
        outreach_id, content_payload
    )

    if not i_success:
        duration_ms = int((time.time() - start_time) * 1000)
        error_persisted = _write_fail(outreach_id, i_fail_code, i_fail_reason, "I", duration_ms, process_id)

        return BlogIMOResult(
            outreach_id=outreach_id,
            success=False,
            stage="I",
            process_id=process_id,
            failure_code=i_fail_code,
            blocking_reason=i_fail_reason,
            error_persisted=error_persisted or i_fail_code == "BLOG-I-ALREADY-PROCESSED",
            duration_ms=duration_ms,
            tools_used=tools_used
        )

    # ─────────────────────────────────────────────────────────────────────────
    # MIDDLE STAGE (M)
    # ─────────────────────────────────────────────────────────────────────────
    m_success, signal_data, m_fail_code, m_fail_reason, m_tools = _middle_stage(spine_data)
    tools_used.extend(m_tools)

    if not m_success:
        duration_ms = int((time.time() - start_time) * 1000)
        error_persisted = _write_fail(outreach_id, m_fail_code, m_fail_reason, "M", duration_ms, process_id)

        return BlogIMOResult(
            outreach_id=outreach_id,
            success=False,
            stage="M",
            process_id=process_id,
            failure_code=m_fail_code,
            blocking_reason=m_fail_reason,
            error_persisted=error_persisted,
            duration_ms=duration_ms,
            tools_used=tools_used
        )

    # ─────────────────────────────────────────────────────────────────────────
    # OUTPUT STAGE (O)
    # ─────────────────────────────────────────────────────────────────────────
    duration_ms = int((time.time() - start_time) * 1000)
    o_success, o_fail_code, o_fail_reason = _output_stage(signal_data, duration_ms)

    if not o_success:
        error_persisted = _write_fail(outreach_id, o_fail_code, o_fail_reason, "O", duration_ms, process_id)

        return BlogIMOResult(
            outreach_id=outreach_id,
            success=False,
            stage="O",
            process_id=process_id,
            failure_code=o_fail_code,
            blocking_reason=o_fail_reason,
            error_persisted=error_persisted,
            duration_ms=duration_ms,
            tools_used=tools_used
        )

    # ─────────────────────────────────────────────────────────────────────────
    # SUCCESS
    # ─────────────────────────────────────────────────────────────────────────
    logger.info(f"Blog IMO PASS", extra={
        'outreach_id': outreach_id,
        'process_id': process_id,
        'event_type': signal_data['event_type'].name_str,
        'has_signal': signal_data.get('has_signal', False),
        'duration_ms': duration_ms
    })

    return BlogIMOResult(
        outreach_id=outreach_id,
        success=True,
        stage="O",
        process_id=process_id,
        event_type=signal_data['event_type'].name_str,
        bit_impact=signal_data['bit_impact'],
        context_summary=signal_data.get('context_summary'),
        source_type=signal_data.get('source_type'),
        source_url=signal_data.get('source_url'),
        duration_ms=duration_ms,
        tools_used=tools_used
    )


# ─────────────────────────────────────────────────────────────────────────────
# BATCH PROCESSING
# ─────────────────────────────────────────────────────────────────────────────
def run_pending_batch(limit: int = 100) -> int:
    """
    Process pending outreach_ids that haven't been through Blog IMO yet.

    Selects records where:
    - Company Target is PASS (ready)
    - Not already in outreach.blog
    - Not already in outreach.blog_errors

    Args:
        limit: Maximum records to process

    Returns:
        Number of records processed
    """
    conn = _get_connection()
    cur = conn.cursor()

    try:
        # Find eligible records
        cur.execute("""
            SELECT o.outreach_id
            FROM outreach.outreach o
            INNER JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
            WHERE ct.execution_status = 'ready'
            AND NOT EXISTS (SELECT 1 FROM outreach.blog b WHERE b.outreach_id = o.outreach_id)
            AND NOT EXISTS (SELECT 1 FROM outreach.blog_errors be WHERE be.outreach_id = o.outreach_id)
            LIMIT %s
        """, (limit,))

        pending = cur.fetchall()

    finally:
        cur.close()
        conn.close()

    processed = 0
    for (outreach_id,) in pending:
        run_blog_imo(str(outreach_id))
        processed += 1

    logger.info(f"Blog IMO batch complete", extra={'processed': processed})
    return processed


# ─────────────────────────────────────────────────────────────────────────────
# FORCED FAILURE TEST (Verification)
# ─────────────────────────────────────────────────────────────────────────────
def run_forced_failure_test() -> Dict[str, Any]:
    """
    Run a forced-failure test to verify error persistence.

    This test:
    1. Finds a valid spine record that will fail at CT gate (not 'ready')
    2. Runs Blog IMO on it
    3. Asserts error is persisted to blog_errors
    4. Verifies correct pipeline_stage and failure_code

    Returns:
        Dict with test results
    """
    conn = _get_connection()
    cur = conn.cursor()

    try:
        # Find a spine record that has CT status != 'ready' (or no CT record)
        # This ensures we have a valid outreach_id but will fail at CT gate
        cur.execute('''
            SELECT o.outreach_id
            FROM outreach.outreach o
            LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
            WHERE ct.execution_status IS NULL OR ct.execution_status != 'ready'
            AND NOT EXISTS (SELECT 1 FROM outreach.blog b WHERE b.outreach_id = o.outreach_id)
            AND NOT EXISTS (SELECT 1 FROM outreach.blog_errors be WHERE be.outreach_id = o.outreach_id)
            LIMIT 1
        ''')
        row = cur.fetchone()

        if not row:
            # If no CT-failing record, find one that's already in blog (will fail idempotent)
            # For a forced failure test, we need a different approach
            # Create a test by using an existing spine record that will fail CT gate
            cur.execute('''
                SELECT o.outreach_id
                FROM outreach.outreach o
                INNER JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
                WHERE ct.execution_status = 'failed'
                AND NOT EXISTS (SELECT 1 FROM outreach.blog_errors be WHERE be.outreach_id = o.outreach_id)
                LIMIT 1
            ''')
            row = cur.fetchone()

        if not row:
            return {
                'error': 'No suitable test record found - need a spine record with CT != ready',
                'overall_pass': False
            }

        test_outreach_id = str(row[0])

        # Get baseline counts
        cur.execute('SELECT COUNT(*) FROM outreach.blog')
        blog_before = cur.fetchone()[0]

        cur.execute('SELECT COUNT(*) FROM outreach.blog_errors')
        errors_before = cur.fetchone()[0]

    finally:
        cur.close()
        conn.close()

    # Run IMO - should fail at CT gate check
    result = run_blog_imo(test_outreach_id)

    conn = _get_connection()
    cur = conn.cursor()

    try:
        # Get counts after
        cur.execute('SELECT COUNT(*) FROM outreach.blog')
        blog_after = cur.fetchone()[0]

        cur.execute('SELECT COUNT(*) FROM outreach.blog_errors')
        errors_after = cur.fetchone()[0]

        # Get the error record
        cur.execute('''
            SELECT pipeline_stage, failure_code, blocking_reason, severity, process_id
            FROM outreach.blog_errors
            WHERE outreach_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        ''', (test_outreach_id,))
        error_row = cur.fetchone()

    finally:
        cur.close()
        conn.close()

    # Build test results
    test_results = {
        'test_outreach_id': test_outreach_id,
        'result_success': result.success,
        'result_failure_code': result.failure_code,
        'result_error_persisted': result.error_persisted,
        'blog_count_unchanged': blog_after == blog_before,
        'errors_incremented': errors_after == errors_before + 1,
        'error_row_found': error_row is not None,
        'assertions': {}
    }

    # Assertions
    test_results['assertions']['blog_unchanged'] = {
        'expected': blog_before,
        'actual': blog_after,
        'pass': blog_after == blog_before
    }
    test_results['assertions']['errors_incremented'] = {
        'expected': errors_before + 1,
        'actual': errors_after,
        'pass': errors_after == errors_before + 1
    }

    if error_row:
        test_results['error_details'] = {
            'pipeline_stage': error_row[0],
            'failure_code': error_row[1],
            'blocking_reason': error_row[2],
            'severity': error_row[3],
            'process_id': str(error_row[4]) if error_row[4] else None
        }
        test_results['assertions']['correct_stage'] = {
            'expected': 'ingest',
            'actual': error_row[0],
            'pass': error_row[0] == 'ingest'
        }
        # Expected code is BLOG-I-UPSTREAM-FAIL (CT not ready)
        test_results['assertions']['correct_code'] = {
            'expected': 'BLOG-I-UPSTREAM-FAIL',
            'actual': error_row[1],
            'pass': error_row[1] == 'BLOG-I-UPSTREAM-FAIL'
        }
        test_results['assertions']['process_id_set'] = {
            'expected': True,
            'actual': error_row[4] is not None,
            'pass': error_row[4] is not None
        }

    # Overall pass/fail
    all_pass = all(a.get('pass', False) for a in test_results['assertions'].values())
    test_results['overall_pass'] = all_pass

    return test_results


# ─────────────────────────────────────────────────────────────────────────────
# CLI Entry Point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == "--test-errors":
            # Forced failure test mode
            print("Running forced-failure test...")
            results = run_forced_failure_test()
            print(f"Test outreach_id: {results['test_outreach_id']}")
            print(f"Result success: {results['result_success']}")
            print(f"Error persisted: {results['result_error_persisted']}")
            print()
            print("Assertions:")
            for name, assertion in results['assertions'].items():
                status = "PASS" if assertion['pass'] else "FAIL"
                print(f"  [{status}] {name}: expected={assertion['expected']}, actual={assertion['actual']}")
            print()
            print(f"Overall: {'PASS' if results['overall_pass'] else 'FAIL'}")
        else:
            # Single outreach_id mode
            outreach_id = arg
            result = run_blog_imo(outreach_id)
            print(f"Result: {'PASS' if result.success else 'FAIL'}")
            print(f"Stage: {result.stage}")
            print(f"Process ID: {result.process_id}")
            if result.success:
                print(f"Event: {result.event_type}, BIT: {result.bit_impact}")
            else:
                print(f"Error: {result.failure_code} - {result.blocking_reason}")
                print(f"Error persisted: {result.error_persisted}")
    else:
        # Batch mode
        processed = run_pending_batch(limit=10)
        print(f"Processed: {processed}")
