"""
People Intelligence Error Handling Module
==========================================

Doctrine-locked error capture for all People Intelligence failures.
This module ensures:
  - No data loss
  - No auto-guessing
  - Deterministic re-entry after correction

Error rows are APPEND-ONLY. Status-driven lifecycle only.
"""

import os
import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from enum import Enum

import psycopg2
from psycopg2.extras import RealDictCursor, Json

logger = logging.getLogger(__name__)


# =============================================================================
# KILL SWITCHES
# =============================================================================

class KillSwitches:
    """Feature flags that halt on disable (never skip)."""
    
    @staticmethod
    def slot_autofill_enabled() -> bool:
        return os.environ.get('PEOPLE_SLOT_AUTOFILL_ENABLED', 'true').lower() == 'true'
    
    @staticmethod
    def movement_detect_enabled() -> bool:
        return os.environ.get('PEOPLE_MOVEMENT_DETECT_ENABLED', 'true').lower() == 'true'
    
    @staticmethod
    def auto_replay_enabled() -> bool:
        return os.environ.get('PEOPLE_AUTO_REPLAY_ENABLED', 'true').lower() == 'true'
    
    @classmethod
    def check_or_error(cls, switch_name: str) -> None:
        """Check switch; raise error if disabled (never skip)."""
        switches = {
            'slot_autofill': cls.slot_autofill_enabled,
            'movement_detect': cls.movement_detect_enabled,
            'auto_replay': cls.auto_replay_enabled,
        }
        if switch_name not in switches:
            raise ValueError(f"Unknown kill switch: {switch_name}")
        
        if not switches[switch_name]():
            raise KillSwitchDisabledError(
                f"Kill switch disabled: {switch_name}. "
                "Operations halt on disable, not skip."
            )


class KillSwitchDisabledError(Exception):
    """Raised when a kill switch is disabled."""
    pass


# =============================================================================
# ERROR ENUMS
# =============================================================================

class ErrorStage(str, Enum):
    """Pipeline stage where error occurred."""
    SLOT_CREATION = 'slot_creation'
    SLOT_FILL = 'slot_fill'
    MOVEMENT_DETECT = 'movement_detect'
    ENRICHMENT = 'enrichment'
    PROMOTION = 'promotion'


class ErrorType(str, Enum):
    """Category of error."""
    VALIDATION = 'validation'
    AMBIGUITY = 'ambiguity'
    CONFLICT = 'conflict'
    MISSING_DATA = 'missing_data'
    STALE_DATA = 'stale_data'
    EXTERNAL_FAIL = 'external_fail'


class RetryStrategy(str, Enum):
    """Recovery path for error."""
    MANUAL_FIX = 'manual_fix'
    AUTO_RETRY = 'auto_retry'
    DISCARD = 'discard'


class ErrorStatus(str, Enum):
    """Lifecycle state of error."""
    OPEN = 'open'
    FIXED = 'fixed'
    REPLAYED = 'replayed'
    ABANDONED = 'abandoned'


# =============================================================================
# ERROR CODES — STABLE MACHINE KEYS
# =============================================================================

@dataclass
class ErrorCodeDef:
    """Definition of a stable error code."""
    code: str
    stage: ErrorStage
    error_type: ErrorType
    message_template: str
    retry_strategy: RetryStrategy
    retry_delay_minutes: Optional[int] = None


# Canonical error code registry
ERROR_CODES: Dict[str, ErrorCodeDef] = {
    # Slot Creation Errors (PI-E1xx)
    'PI-E101': ErrorCodeDef(
        code='PI-E101',
        stage=ErrorStage.SLOT_CREATION,
        error_type=ErrorType.VALIDATION,
        message_template="Invalid slot type: {slot_type}. Must be CEO|CFO|HR|BEN.",
        retry_strategy=RetryStrategy.MANUAL_FIX,
    ),
    'PI-E102': ErrorCodeDef(
        code='PI-E102',
        stage=ErrorStage.SLOT_CREATION,
        error_type=ErrorType.VALIDATION,
        message_template="Outreach ID {outreach_id} already has slots created. Duplicate creation blocked.",
        retry_strategy=RetryStrategy.DISCARD,
    ),
    'PI-E103': ErrorCodeDef(
        code='PI-E103',
        stage=ErrorStage.SLOT_CREATION,
        error_type=ErrorType.MISSING_DATA,
        message_template="Cannot create slots: company_unique_id missing for outreach {outreach_id}.",
        retry_strategy=RetryStrategy.MANUAL_FIX,
    ),
    
    # Slot Fill Errors (PI-E2xx)
    'PI-E201': ErrorCodeDef(
        code='PI-E201',
        stage=ErrorStage.SLOT_FILL,
        error_type=ErrorType.AMBIGUITY,
        message_template="Multiple candidates for slot {slot_id}: confidence gap {gap}% < 15% threshold.",
        retry_strategy=RetryStrategy.MANUAL_FIX,
    ),
    'PI-E202': ErrorCodeDef(
        code='PI-E202',
        stage=ErrorStage.SLOT_FILL,
        error_type=ErrorType.CONFLICT,
        message_template="LinkedIn title '{linkedin_title}' conflicts with slot type {slot_type}.",
        retry_strategy=RetryStrategy.MANUAL_FIX,
    ),
    'PI-E203': ErrorCodeDef(
        code='PI-E203',
        stage=ErrorStage.SLOT_FILL,
        error_type=ErrorType.MISSING_DATA,
        message_template="LinkedIn URL missing for candidate. Cannot verify identity.",
        retry_strategy=RetryStrategy.MANUAL_FIX,
    ),
    'PI-E204': ErrorCodeDef(
        code='PI-E204',
        stage=ErrorStage.SLOT_FILL,
        error_type=ErrorType.VALIDATION,
        message_template="Slot {slot_id} already filled. Cannot overwrite.",
        retry_strategy=RetryStrategy.DISCARD,
    ),
    
    # Movement Detection Errors (PI-E3xx)
    'PI-E301': ErrorCodeDef(
        code='PI-E301',
        stage=ErrorStage.MOVEMENT_DETECT,
        error_type=ErrorType.AMBIGUITY,
        message_template="Movement type ambiguous for person {person_id}: {context}.",
        retry_strategy=RetryStrategy.MANUAL_FIX,
    ),
    'PI-E302': ErrorCodeDef(
        code='PI-E302',
        stage=ErrorStage.MOVEMENT_DETECT,
        error_type=ErrorType.STALE_DATA,
        message_template="LinkedIn data stale for person {person_id}. Last update: {last_update}.",
        retry_strategy=RetryStrategy.AUTO_RETRY,
        retry_delay_minutes=1440,  # 24 hours
    ),
    'PI-E303': ErrorCodeDef(
        code='PI-E303',
        stage=ErrorStage.MOVEMENT_DETECT,
        error_type=ErrorType.CONFLICT,
        message_template="Blog hint says '{blog_hint}' but LinkedIn shows '{linkedin_status}'.",
        retry_strategy=RetryStrategy.MANUAL_FIX,
    ),
    
    # Enrichment Errors (PI-E4xx)
    'PI-E401': ErrorCodeDef(
        code='PI-E401',
        stage=ErrorStage.ENRICHMENT,
        error_type=ErrorType.EXTERNAL_FAIL,
        message_template="Clay API timeout after {timeout_seconds}s for person {person_id}.",
        retry_strategy=RetryStrategy.AUTO_RETRY,
        retry_delay_minutes=15,
    ),
    'PI-E402': ErrorCodeDef(
        code='PI-E402',
        stage=ErrorStage.ENRICHMENT,
        error_type=ErrorType.EXTERNAL_FAIL,
        message_template="Clay API blocked: rate limit exceeded. Cool-off required.",
        retry_strategy=RetryStrategy.AUTO_RETRY,
        retry_delay_minutes=60,
    ),
    'PI-E403': ErrorCodeDef(
        code='PI-E403',
        stage=ErrorStage.ENRICHMENT,
        error_type=ErrorType.EXTERNAL_FAIL,
        message_template="Cost guardrail triggered: enrichment budget exhausted.",
        retry_strategy=RetryStrategy.MANUAL_FIX,
    ),
    'PI-E404': ErrorCodeDef(
        code='PI-E404',
        stage=ErrorStage.ENRICHMENT,
        error_type=ErrorType.MISSING_DATA,
        message_template="No email found for person {person_id} after enrichment.",
        retry_strategy=RetryStrategy.MANUAL_FIX,
    ),
    
    # Promotion Errors (PI-E5xx)
    'PI-E501': ErrorCodeDef(
        code='PI-E501',
        stage=ErrorStage.PROMOTION,
        error_type=ErrorType.VALIDATION,
        message_template="Cannot promote slot {slot_id}: email not verified.",
        retry_strategy=RetryStrategy.MANUAL_FIX,
    ),
    'PI-E502': ErrorCodeDef(
        code='PI-E502',
        stage=ErrorStage.PROMOTION,
        error_type=ErrorType.VALIDATION,
        message_template="Cannot promote slot {slot_id}: person_status is '{status}', expected 'active'.",
        retry_strategy=RetryStrategy.MANUAL_FIX,
    ),
    'PI-E503': ErrorCodeDef(
        code='PI-E503',
        stage=ErrorStage.PROMOTION,
        error_type=ErrorType.EXTERNAL_FAIL,
        message_template="Database error promoting to outreach.people: {db_error}.",
        retry_strategy=RetryStrategy.AUTO_RETRY,
        retry_delay_minutes=5,
    ),
    
    # Kill Switch Errors (PI-E9xx)
    'PI-E901': ErrorCodeDef(
        code='PI-E901',
        stage=ErrorStage.SLOT_FILL,
        error_type=ErrorType.VALIDATION,
        message_template="Kill switch PEOPLE_SLOT_AUTOFILL_ENABLED is disabled. Operations halted.",
        retry_strategy=RetryStrategy.MANUAL_FIX,
    ),
    'PI-E902': ErrorCodeDef(
        code='PI-E902',
        stage=ErrorStage.MOVEMENT_DETECT,
        error_type=ErrorType.VALIDATION,
        message_template="Kill switch PEOPLE_MOVEMENT_DETECT_ENABLED is disabled. Operations halted.",
        retry_strategy=RetryStrategy.MANUAL_FIX,
    ),
    'PI-E903': ErrorCodeDef(
        code='PI-E903',
        stage=ErrorStage.SLOT_FILL,
        error_type=ErrorType.VALIDATION,
        message_template="Kill switch PEOPLE_AUTO_REPLAY_ENABLED is disabled. Replay halted.",
        retry_strategy=RetryStrategy.MANUAL_FIX,
    ),
}


# =============================================================================
# ERROR DATA CLASS
# =============================================================================

@dataclass
class PeopleError:
    """Represents an error to be written to people.people_errors."""
    
    outreach_id: str
    error_code: str
    raw_payload: Dict[str, Any]
    
    # Optional context
    slot_id: Optional[str] = None
    person_id: Optional[str] = None
    source_hints_used: Optional[Dict[str, Any]] = None
    
    # Auto-populated from error code
    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    error_stage: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    retry_strategy: Optional[str] = None
    retry_after: Optional[datetime] = None
    status: str = 'open'
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Populate fields from error code definition."""
        if self.error_code not in ERROR_CODES:
            raise ValueError(f"Unknown error code: {self.error_code}")
        
        code_def = ERROR_CODES[self.error_code]
        self.error_stage = code_def.stage.value
        self.error_type = code_def.error_type.value
        self.retry_strategy = code_def.retry_strategy.value
        
        # Format message with payload
        try:
            self.error_message = code_def.message_template.format(**self.raw_payload)
        except KeyError:
            self.error_message = code_def.message_template
        
        # Set retry_after if auto-retry
        if code_def.retry_strategy == RetryStrategy.AUTO_RETRY and code_def.retry_delay_minutes:
            self.retry_after = datetime.now() + timedelta(minutes=code_def.retry_delay_minutes)


# =============================================================================
# ERROR WRITER
# =============================================================================

class PeopleErrorWriter:
    """Writes errors to people.people_errors table."""
    
    def __init__(self, conn=None):
        """Initialize with database connection."""
        self._conn = conn
        self._own_conn = False
    
    def _get_connection(self):
        """Get or create database connection."""
        if self._conn is None:
            self._conn = psycopg2.connect(os.environ['DATABASE_URL'])
            self._own_conn = True
        return self._conn
    
    def close(self):
        """Close connection if we own it."""
        if self._own_conn and self._conn:
            self._conn.close()
            self._conn = None
    
    def write_error(self, error: PeopleError) -> str:
        """
        Write error to database immediately.
        Returns error_id.
        
        ⚠️ Never retry inline. Errors exit the worker immediately.
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO people.people_errors (
                    error_id, outreach_id, slot_id, person_id,
                    error_stage, error_type, error_code, error_message,
                    source_hints_used, raw_payload, retry_strategy,
                    retry_after, status, created_at, last_updated_at
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s
                )
            """, (
                error.error_id,
                error.outreach_id,
                error.slot_id,
                error.person_id,
                error.error_stage,
                error.error_type,
                error.error_code,
                error.error_message,
                Json(error.source_hints_used) if error.source_hints_used else None,
                Json(error.raw_payload),
                error.retry_strategy,
                error.retry_after,
                error.status,
                error.created_at,
                error.created_at,  # last_updated_at = created_at initially
            ))
            conn.commit()
            
            logger.warning(
                f"[PI-ERROR] {error.error_code}: {error.error_message} | "
                f"outreach_id={error.outreach_id} | error_id={error.error_id}"
            )
            
            return error.error_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to write error to database: {e}")
            raise
        finally:
            cur.close()
    
    def write_errors(self, errors: List[PeopleError]) -> List[str]:
        """Write multiple errors in a batch."""
        error_ids = []
        for error in errors:
            error_id = self.write_error(error)
            error_ids.append(error_id)
        return error_ids
    
    def mark_fixed(self, error_id: str) -> bool:
        """Mark error as fixed (ready for replay)."""
        return self._update_status(error_id, ErrorStatus.FIXED)
    
    def mark_replayed(self, error_id: str) -> bool:
        """Mark error as replayed (replay completed)."""
        return self._update_status(error_id, ErrorStatus.REPLAYED)
    
    def mark_abandoned(self, error_id: str) -> bool:
        """Mark error as abandoned (will not be fixed)."""
        return self._update_status(error_id, ErrorStatus.ABANDONED)
    
    def _update_status(self, error_id: str, status: ErrorStatus) -> bool:
        """Update error status."""
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                UPDATE people.people_errors
                SET status = %s, last_updated_at = now()
                WHERE error_id = %s
            """, (status.value, error_id))
            conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to update error status: {e}")
            raise
        finally:
            cur.close()
    
    def get_open_errors(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get open errors for review."""
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute("""
                SELECT *
                FROM people.people_errors
                WHERE status = 'open'
                ORDER BY created_at ASC
                LIMIT %s
            """, (limit,))
            return [dict(row) for row in cur.fetchall()]
        finally:
            cur.close()
    
    def get_fixed_errors(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get fixed errors ready for replay."""
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute("""
                SELECT *
                FROM people.people_errors
                WHERE status = 'fixed'
                ORDER BY last_updated_at ASC
                LIMIT %s
            """, (limit,))
            return [dict(row) for row in cur.fetchall()]
        finally:
            cur.close()
    
    def get_errors_for_outreach(self, outreach_id: str) -> List[Dict[str, Any]]:
        """Get all errors for a specific outreach_id."""
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute("""
                SELECT *
                FROM people.people_errors
                WHERE outreach_id = %s
                ORDER BY created_at ASC
            """, (outreach_id,))
            return [dict(row) for row in cur.fetchall()]
        finally:
            cur.close()


# =============================================================================
# RUN SUMMARY — AUDIT & OBSERVABILITY
# =============================================================================

@dataclass
class WorkerRunSummary:
    """Summary of a People Intelligence worker run."""
    
    process_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    
    slots_attempted: int = 0
    slots_created: int = 0
    fills_attempted: int = 0
    fills_succeeded: int = 0
    errors_emitted: int = 0
    error_ids: List[str] = field(default_factory=list)
    
    def record_error(self, error_id: str):
        """Record an emitted error."""
        self.error_ids.append(error_id)
        self.errors_emitted += 1
    
    def finalize(self):
        """Mark run as complete."""
        self.ended_at = datetime.now()
    
    def log_summary(self):
        """Log run summary (no silent failures)."""
        self.finalize()
        
        duration = (self.ended_at - self.started_at).total_seconds()
        
        logger.info(
            f"[PI-RUN-SUMMARY] process_id={self.process_id} | "
            f"duration={duration:.2f}s | "
            f"slots_attempted={self.slots_attempted} | "
            f"slots_created={self.slots_created} | "
            f"fills_attempted={self.fills_attempted} | "
            f"fills_succeeded={self.fills_succeeded} | "
            f"errors_emitted={self.errors_emitted}"
        )
        
        if self.error_ids:
            logger.warning(
                f"[PI-RUN-ERRORS] process_id={self.process_id} | "
                f"error_ids={','.join(self.error_ids)}"
            )
        
        return asdict(self)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def emit_error(
    outreach_id: str,
    error_code: str,
    raw_payload: Dict[str, Any],
    slot_id: Optional[str] = None,
    person_id: Optional[str] = None,
    source_hints_used: Optional[Dict[str, Any]] = None,
    writer: Optional[PeopleErrorWriter] = None,
) -> str:
    """
    Emit an error immediately. Never retry inline.
    
    Returns error_id.
    """
    error = PeopleError(
        outreach_id=outreach_id,
        error_code=error_code,
        raw_payload=raw_payload,
        slot_id=slot_id,
        person_id=person_id,
        source_hints_used=source_hints_used,
    )
    
    if writer is None:
        writer = PeopleErrorWriter()
        try:
            return writer.write_error(error)
        finally:
            writer.close()
    else:
        return writer.write_error(error)


def check_kill_switch_or_emit_error(
    switch_name: str,
    outreach_id: str,
    raw_payload: Dict[str, Any],
    writer: Optional[PeopleErrorWriter] = None,
) -> bool:
    """
    Check kill switch. If disabled, emit error and return False.
    If enabled, return True.
    """
    try:
        KillSwitches.check_or_error(switch_name)
        return True
    except KillSwitchDisabledError:
        error_codes_map = {
            'slot_autofill': 'PI-E901',
            'movement_detect': 'PI-E902',
            'auto_replay': 'PI-E903',
        }
        error_code = error_codes_map.get(switch_name, 'PI-E901')
        emit_error(
            outreach_id=outreach_id,
            error_code=error_code,
            raw_payload={**raw_payload, 'switch_name': switch_name},
            writer=writer,
        )
        return False


# =============================================================================
# MODULE TEST
# =============================================================================

if __name__ == "__main__":
    # Test error code registry
    print("People Intelligence Error Codes:")
    print("=" * 60)
    for code, defn in sorted(ERROR_CODES.items()):
        print(f"{code}: [{defn.stage.value}] {defn.error_type.value}")
        print(f"       {defn.message_template[:60]}...")
        print(f"       Strategy: {defn.retry_strategy.value}")
        print()
