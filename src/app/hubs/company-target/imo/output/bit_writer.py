"""
BIT Writer - Spine-First Architecture v1.1
==========================================

Writes BIT signals and scores to outreach.bit_* tables.

DOCTRINE LOCK:
- All writes FK to outreach_id (spine anchor)
- sovereign_id is HIDDEN from this layer
- correlation_id is REQUIRED for all writes
- Errors persist to outreach.bit_errors

Target Tables:
- outreach.bit_signals: Individual BIT signals
- outreach.bit_scores: Company-level scores
- outreach.bit_errors: Error persistence

Created: 2026-01-08
Doctrine: Spine-First Architecture v1.1
"""

import os
import uuid
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

# =============================================================================
# DOCTRINE GUARDS (LOCKED)
# =============================================================================

ENFORCE_OUTREACH_SPINE_ONLY = True
assert ENFORCE_OUTREACH_SPINE_ONLY is True, "BIT Writer MUST use outreach_id only"

ENFORCE_CORRELATION_ID = True
assert ENFORCE_CORRELATION_ID is True, "BIT Writer MUST require correlation_id"

ENFORCE_ERROR_PERSISTENCE = True
assert ENFORCE_ERROR_PERSISTENCE is True, "BIT Writer MUST persist all errors"

# =============================================================================
# CONSTANTS
# =============================================================================

# BIT Score Thresholds
BIT_THRESHOLD_COLD = 0
BIT_THRESHOLD_WARM = 25
BIT_THRESHOLD_HOT = 50
BIT_THRESHOLD_BURNING = 75

# Decay periods by signal category
DECAY_PERIODS = {
    'structural': 365,   # Form 5500, etc.
    'movement': 180,     # Hire/depart
    'event': 90,         # Funding, news
    'operational': 90,   # Email verified
}

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

class PipelineStage(Enum):
    """BIT pipeline stages for error tracking"""
    INGEST = "ingest"
    VALIDATE = "validate"
    CALCULATE = "calculate"
    PERSIST = "persist"


class ErrorSeverity(Enum):
    """Error severity levels"""
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"


@dataclass
class BITWriteResult:
    """Result of a BIT write operation"""
    success: bool
    outreach_id: str
    operation: str  # 'signal', 'score', 'error'
    table_name: str
    rows_affected: int = 0
    error_message: Optional[str] = None
    error_persisted: bool = False
    process_id: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class BITSignalInput:
    """Input for recording a BIT signal"""
    outreach_id: str
    signal_type: str
    signal_impact: float
    source_spoke: str
    correlation_id: str
    process_id: Optional[str] = None
    signal_metadata: Optional[Dict[str, Any]] = None
    decay_period_days: int = 90


@dataclass
class BITScoreInput:
    """Input for updating a BIT score"""
    outreach_id: str
    score: float
    score_tier: str
    signal_count: int
    correlation_id: str
    process_id: Optional[str] = None
    people_score: float = 0.0
    dol_score: float = 0.0
    blog_score: float = 0.0
    talent_flow_score: float = 0.0


# =============================================================================
# BIT WRITER CLASS
# =============================================================================

class BITWriter:
    """
    BIT Writer for Spine-First Architecture.

    Handles all BIT-related writes to Neon:
    - Signal recording (outreach.bit_signals)
    - Score updates (outreach.bit_scores)
    - Error persistence (outreach.bit_errors)

    DOCTRINE: Uses outreach_id as the ONLY identity anchor.
    """

    # SQL Statements
    INSERT_SIGNAL_SQL = """
        INSERT INTO outreach.bit_signals (
            outreach_id,
            signal_type,
            signal_impact,
            source_spoke,
            correlation_id,
            process_id,
            signal_metadata,
            decay_period_days,
            signal_timestamp,
            created_at
        ) VALUES (
            %(outreach_id)s,
            %(signal_type)s,
            %(signal_impact)s,
            %(source_spoke)s,
            %(correlation_id)s,
            %(process_id)s,
            %(signal_metadata)s,
            %(decay_period_days)s,
            %(signal_timestamp)s,
            %(created_at)s
        )
        RETURNING signal_id
    """

    UPSERT_SCORE_SQL = """
        INSERT INTO outreach.bit_scores (
            outreach_id,
            score,
            score_tier,
            signal_count,
            people_score,
            dol_score,
            blog_score,
            talent_flow_score,
            last_signal_at,
            last_scored_at,
            created_at,
            updated_at
        ) VALUES (
            %(outreach_id)s,
            %(score)s,
            %(score_tier)s,
            %(signal_count)s,
            %(people_score)s,
            %(dol_score)s,
            %(blog_score)s,
            %(talent_flow_score)s,
            %(last_signal_at)s,
            %(last_scored_at)s,
            %(created_at)s,
            %(updated_at)s
        )
        ON CONFLICT (outreach_id) DO UPDATE SET
            score = EXCLUDED.score,
            score_tier = EXCLUDED.score_tier,
            signal_count = EXCLUDED.signal_count,
            people_score = EXCLUDED.people_score,
            dol_score = EXCLUDED.dol_score,
            blog_score = EXCLUDED.blog_score,
            talent_flow_score = EXCLUDED.talent_flow_score,
            last_signal_at = EXCLUDED.last_signal_at,
            last_scored_at = EXCLUDED.last_scored_at,
            updated_at = EXCLUDED.updated_at
    """

    INSERT_ERROR_SQL = """
        INSERT INTO outreach.bit_errors (
            outreach_id,
            pipeline_stage,
            failure_code,
            blocking_reason,
            severity,
            retry_allowed,
            correlation_id,
            process_id,
            raw_input,
            stack_trace,
            created_at
        ) VALUES (
            %(outreach_id)s,
            %(pipeline_stage)s,
            %(failure_code)s,
            %(blocking_reason)s,
            %(severity)s,
            %(retry_allowed)s,
            %(correlation_id)s,
            %(process_id)s,
            %(raw_input)s,
            %(stack_trace)s,
            %(created_at)s
        )
        RETURNING error_id
    """

    VALIDATE_SPINE_SQL = """
        SELECT outreach_id, domain
        FROM outreach.outreach
        WHERE outreach_id = %(outreach_id)s
    """

    def __init__(self):
        """Initialize BIT Writer."""
        self._connection = None
        self.logger = logging.getLogger(__name__)

    def _get_connection(self):
        """Get or create database connection."""
        if self._connection is None or self._connection.closed:
            import psycopg2
            self._connection = psycopg2.connect(
                host=os.getenv('NEON_HOST'),
                database=os.getenv('NEON_DATABASE'),
                user=os.getenv('NEON_USER'),
                password=os.getenv('NEON_PASSWORD'),
                sslmode='require'
            )
        return self._connection

    def close(self):
        """Close database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()
            self._connection = None

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def validate_spine_exists(self, outreach_id: str) -> bool:
        """
        Validate that outreach_id exists in spine.

        DOCTRINE: All writes require valid spine anchor.
        """
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(self.VALIDATE_SPINE_SQL, {'outreach_id': outreach_id})
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            self.logger.error(f"Spine validation failed: {e}")
            return False

    @staticmethod
    def calculate_tier(score: float) -> str:
        """Calculate BIT tier from score."""
        if score >= BIT_THRESHOLD_BURNING:
            return 'BURNING'
        elif score >= BIT_THRESHOLD_HOT:
            return 'HOT'
        elif score >= BIT_THRESHOLD_WARM:
            return 'WARM'
        return 'COLD'

    # =========================================================================
    # SIGNAL WRITING
    # =========================================================================

    def write_signal(self, signal: BITSignalInput) -> BITWriteResult:
        """
        Write a BIT signal to outreach.bit_signals.

        Args:
            signal: BITSignalInput with signal details

        Returns:
            BITWriteResult indicating success/failure
        """
        import time
        start_time = time.time()

        result = BITWriteResult(
            success=False,
            outreach_id=signal.outreach_id,
            operation='signal',
            table_name='outreach.bit_signals',
            process_id=signal.process_id
        )

        # Validate correlation_id (DOCTRINE)
        if not signal.correlation_id:
            result.error_message = "correlation_id is required (DOCTRINE)"
            self._persist_error(
                outreach_id=signal.outreach_id,
                stage=PipelineStage.VALIDATE,
                code='BIT-V-NO-CORRELATION',
                reason='correlation_id is required for all BIT writes',
                correlation_id=None,
                process_id=signal.process_id
            )
            result.error_persisted = True
            return result

        # Validate spine exists
        if not self.validate_spine_exists(signal.outreach_id):
            result.error_message = f"outreach_id {signal.outreach_id} not in spine"
            self._persist_error(
                outreach_id=signal.outreach_id,
                stage=PipelineStage.VALIDATE,
                code='BIT-V-NOT-IN-SPINE',
                reason=f'outreach_id not found in outreach.outreach',
                correlation_id=signal.correlation_id,
                process_id=signal.process_id
            )
            result.error_persisted = True
            return result

        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                import json
                now = datetime.now()
                cursor.execute(self.INSERT_SIGNAL_SQL, {
                    'outreach_id': signal.outreach_id,
                    'signal_type': signal.signal_type,
                    'signal_impact': signal.signal_impact,
                    'source_spoke': signal.source_spoke,
                    'correlation_id': signal.correlation_id,
                    'process_id': signal.process_id,
                    'signal_metadata': json.dumps(signal.signal_metadata) if signal.signal_metadata else None,
                    'decay_period_days': signal.decay_period_days,
                    'signal_timestamp': now,
                    'created_at': now
                })
                conn.commit()
                result.success = True
                result.rows_affected = 1

                self.logger.info(
                    f"BIT Signal recorded: {signal.signal_type} for {signal.outreach_id} "
                    f"(impact: {signal.signal_impact:+.1f})"
                )

        except Exception as e:
            result.error_message = str(e)
            self.logger.error(f"Failed to write BIT signal: {e}")
            self._persist_error(
                outreach_id=signal.outreach_id,
                stage=PipelineStage.PERSIST,
                code='BIT-P-SIGNAL-FAIL',
                reason=f'Failed to write signal: {e}',
                correlation_id=signal.correlation_id,
                process_id=signal.process_id,
                stack_trace=traceback.format_exc()
            )
            result.error_persisted = True
            if self._connection:
                self._connection.rollback()

        result.duration_seconds = time.time() - start_time
        return result

    # =========================================================================
    # SCORE WRITING
    # =========================================================================

    def write_score(self, score_input: BITScoreInput) -> BITWriteResult:
        """
        Write/update a BIT score to outreach.bit_scores.

        Uses UPSERT - creates if not exists, updates if exists.

        Args:
            score_input: BITScoreInput with score details

        Returns:
            BITWriteResult indicating success/failure
        """
        import time
        start_time = time.time()

        result = BITWriteResult(
            success=False,
            outreach_id=score_input.outreach_id,
            operation='score',
            table_name='outreach.bit_scores',
            process_id=score_input.process_id
        )

        # Validate correlation_id (DOCTRINE)
        if not score_input.correlation_id:
            result.error_message = "correlation_id is required (DOCTRINE)"
            self._persist_error(
                outreach_id=score_input.outreach_id,
                stage=PipelineStage.VALIDATE,
                code='BIT-V-NO-CORRELATION',
                reason='correlation_id is required for all BIT writes',
                correlation_id=None,
                process_id=score_input.process_id
            )
            result.error_persisted = True
            return result

        # Validate spine exists
        if not self.validate_spine_exists(score_input.outreach_id):
            result.error_message = f"outreach_id {score_input.outreach_id} not in spine"
            self._persist_error(
                outreach_id=score_input.outreach_id,
                stage=PipelineStage.VALIDATE,
                code='BIT-V-NOT-IN-SPINE',
                reason=f'outreach_id not found in outreach.outreach',
                correlation_id=score_input.correlation_id,
                process_id=score_input.process_id
            )
            result.error_persisted = True
            return result

        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                now = datetime.now()
                cursor.execute(self.UPSERT_SCORE_SQL, {
                    'outreach_id': score_input.outreach_id,
                    'score': score_input.score,
                    'score_tier': score_input.score_tier,
                    'signal_count': score_input.signal_count,
                    'people_score': score_input.people_score,
                    'dol_score': score_input.dol_score,
                    'blog_score': score_input.blog_score,
                    'talent_flow_score': score_input.talent_flow_score,
                    'last_signal_at': now,
                    'last_scored_at': now,
                    'created_at': now,
                    'updated_at': now
                })
                conn.commit()
                result.success = True
                result.rows_affected = 1

                self.logger.info(
                    f"BIT Score updated: {score_input.outreach_id} = {score_input.score:.1f} ({score_input.score_tier})"
                )

        except Exception as e:
            result.error_message = str(e)
            self.logger.error(f"Failed to write BIT score: {e}")
            self._persist_error(
                outreach_id=score_input.outreach_id,
                stage=PipelineStage.PERSIST,
                code='BIT-P-SCORE-FAIL',
                reason=f'Failed to write score: {e}',
                correlation_id=score_input.correlation_id,
                process_id=score_input.process_id,
                stack_trace=traceback.format_exc()
            )
            result.error_persisted = True
            if self._connection:
                self._connection.rollback()

        result.duration_seconds = time.time() - start_time
        return result

    # =========================================================================
    # ERROR PERSISTENCE
    # =========================================================================

    def _persist_error(
        self,
        outreach_id: str,
        stage: PipelineStage,
        code: str,
        reason: str,
        correlation_id: Optional[str] = None,
        process_id: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        raw_input: Optional[Dict[str, Any]] = None,
        stack_trace: Optional[str] = None
    ) -> bool:
        """
        Persist error to outreach.bit_errors.

        DOCTRINE: Errors are first-class outputs, not hidden logging.
        """
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                import json
                cursor.execute(self.INSERT_ERROR_SQL, {
                    'outreach_id': outreach_id if outreach_id else None,
                    'pipeline_stage': stage.value,
                    'failure_code': code,
                    'blocking_reason': reason,
                    'severity': severity.value,
                    'retry_allowed': False,  # DOCTRINE: Terminal failures
                    'correlation_id': correlation_id,
                    'process_id': process_id,
                    'raw_input': json.dumps(raw_input) if raw_input else None,
                    'stack_trace': stack_trace,
                    'created_at': datetime.now()
                })
                conn.commit()
                self.logger.warning(f"BIT Error persisted: {code} - {reason}")
                return True
        except Exception as e:
            self.logger.error(f"CRITICAL: Failed to persist BIT error: {e}")
            return False

    # =========================================================================
    # BULK OPERATIONS
    # =========================================================================

    def write_signals_batch(self, signals: List[BITSignalInput]) -> List[BITWriteResult]:
        """
        Write multiple signals in a batch.

        Args:
            signals: List of BITSignalInput

        Returns:
            List of BITWriteResult for each signal
        """
        results = []
        for signal in signals:
            result = self.write_signal(signal)
            results.append(result)
        return results

    # =========================================================================
    # QUERY HELPERS
    # =========================================================================

    def get_score(self, outreach_id: str) -> Optional[Dict[str, Any]]:
        """Get current BIT score for an outreach_id."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT outreach_id, score, score_tier, signal_count,
                           people_score, dol_score, blog_score, talent_flow_score,
                           last_signal_at, last_scored_at
                    FROM outreach.bit_scores
                    WHERE outreach_id = %s
                """, (outreach_id,))
                row = cursor.fetchone()
                if row:
                    return {
                        'outreach_id': row[0],
                        'score': float(row[1]),
                        'score_tier': row[2],
                        'signal_count': row[3],
                        'people_score': float(row[4]),
                        'dol_score': float(row[5]),
                        'blog_score': float(row[6]),
                        'talent_flow_score': float(row[7]),
                        'last_signal_at': row[8],
                        'last_scored_at': row[9]
                    }
                return None
        except Exception as e:
            self.logger.error(f"Failed to get BIT score: {e}")
            return None

    def get_signals_for_company(
        self,
        outreach_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent signals for an outreach_id."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT signal_id, signal_type, signal_impact, source_spoke,
                           decay_period_days, signal_timestamp, correlation_id
                    FROM outreach.bit_signals
                    WHERE outreach_id = %s
                    ORDER BY signal_timestamp DESC
                    LIMIT %s
                """, (outreach_id, limit))
                rows = cursor.fetchall()
                return [
                    {
                        'signal_id': str(row[0]),
                        'signal_type': row[1],
                        'signal_impact': float(row[2]),
                        'source_spoke': row[3],
                        'decay_period_days': row[4],
                        'signal_timestamp': row[5],
                        'correlation_id': str(row[6]) if row[6] else None
                    }
                    for row in rows
                ]
        except Exception as e:
            self.logger.error(f"Failed to get BIT signals: {e}")
            return []
