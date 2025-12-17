"""
Master Error Log Emitter

This module provides the interface for emitting errors to the global
shq_master_error_log table per PRD_MASTER_ERROR_LOG.md.

DOCTRINE (ENFORCED - FAIL HARD):
- Local First: Write to local sub-hub table BEFORE calling this emitter
- Correlation Required: All errors MUST have a valid correlation_id (UUID v4)
- Process ID Required: All errors MUST have a valid process_id (hub.subhub.pipeline.phase)
- Append-Only: No updates or deletes allowed
- Immutable History: Error history is immutable. Corrections are new records, never edits.

ENFORCEMENT:
- Missing correlation_id → ValidationError (FAIL HARD)
- Missing process_id → ValidationError (FAIL HARD)
- Malformed process_id → ValidationError (FAIL HARD)
- Empty/whitespace values → ValidationError (FAIL HARD)

Usage:
    from utils.master_error_emitter import MasterErrorEmitter, Hub, Severity

    # Initialize emitter
    emitter = MasterErrorEmitter(db_connection, operating_mode=OperatingMode.STEADY_STATE)

    # First, write to local sub-hub table (LOCAL FIRST)
    local_table.insert(error_record)

    # Then emit to master error log
    error_id = emitter.emit(
        correlation_id="550e8400-e29b-41d4-a716-446655440000",
        hub=Hub.PEOPLE,
        sub_hub="lifecycle",
        process_id="people.lifecycle.email.phase5",  # REQUIRED - FAIL HARD IF MISSING
        pipeline_phase="phase5",
        entity_type=EntityType.PERSON,
        entity_id="04.04.02.04.20000.042",
        severity=Severity.MEDIUM,
        error_code="PSH-P5-001",
        error_message="Cannot generate email - missing first_name",
        source_tool="pattern_template",
        retryable=False
    )
"""

import uuid
import json
import re
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class Hub(Enum):
    """Valid hub values per PRD_MASTER_ERROR_LOG.md"""
    COMPANY = "company"
    PEOPLE = "people"
    DOL = "dol"
    BLOG_NEWS = "blog_news"
    OUTREACH = "outreach"
    PLATFORM = "platform"


class Severity(Enum):
    """Error severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EntityType(Enum):
    """Entity types involved in errors"""
    COMPANY = "company"
    PERSON = "person"
    FILING = "filing"
    ARTICLE = "article"
    BATCH = "batch"
    UNKNOWN = "unknown"


class OperatingMode(Enum):
    """Operating mode affects alerting thresholds"""
    BURN_IN = "BURN_IN"
    STEADY_STATE = "STEADY_STATE"


# ============================================================================
# ERROR EVENT DATA CLASS
# ============================================================================

@dataclass
class MasterErrorEvent:
    """
    Represents a normalized error event for the master error log.

    All fields match the shq_master_error_log table schema.
    """
    correlation_id: str  # REQUIRED
    hub: Hub
    process_id: str
    pipeline_phase: str
    entity_type: EntityType
    severity: Severity
    error_code: str
    error_message: str
    operating_mode: OperatingMode
    retryable: bool
    sub_hub: Optional[str] = None
    entity_id: Optional[str] = None
    source_tool: Optional[str] = None
    cost_impact_usd: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "correlation_id": self.correlation_id,
            "hub": self.hub.value,
            "sub_hub": self.sub_hub,
            "process_id": self.process_id,
            "pipeline_phase": self.pipeline_phase,
            "entity_type": self.entity_type.value,
            "entity_id": self.entity_id,
            "severity": self.severity.value,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "source_tool": self.source_tool,
            "operating_mode": self.operating_mode.value,
            "retryable": self.retryable,
            "cost_impact_usd": self.cost_impact_usd,
            "metadata": self.metadata
        }


# ============================================================================
# VALIDATION
# ============================================================================

class ValidationError(Exception):
    """Raised when error event validation fails"""
    pass


def validate_correlation_id(correlation_id: Optional[str]) -> None:
    """
    Validate correlation_id is present and valid UUID.

    DOCTRINE: Correlation is REQUIRED per Barton Doctrine.
    """
    if not correlation_id:
        raise ValidationError("correlation_id is REQUIRED per Barton Doctrine")

    try:
        uuid.UUID(correlation_id)
    except ValueError:
        raise ValidationError(f"correlation_id must be valid UUID: {correlation_id}")


def validate_process_id(process_id: Optional[str]) -> None:
    """
    Validate process_id format: hub.subhub.pipeline.phase

    DOCTRINE: process_id is MANDATORY. FAIL HARD if missing or malformed.

    Examples:
    - company.identity.matching.phase1
    - people.lifecycle.email.phase5
    - dol.form5500.ingest.parse

    Raises:
        ValidationError: If process_id is missing, empty, whitespace, or malformed.
                        This is a FAIL HARD condition - no error can be emitted without
                        a valid process_id.
    """
    # FAIL HARD: process_id is MANDATORY
    if process_id is None:
        raise ValidationError(
            "process_id is MANDATORY per Barton Doctrine. "
            "FAIL HARD: Cannot emit error without process_id."
        )

    # FAIL HARD: Empty or whitespace-only
    if not process_id or not process_id.strip():
        raise ValidationError(
            "process_id cannot be empty or whitespace. "
            "FAIL HARD: Cannot emit error without valid process_id."
        )

    # Normalize (strip whitespace)
    process_id = process_id.strip()

    # FAIL HARD: Must be exactly 4 dot-separated components
    parts = process_id.split('.')
    if len(parts) != 4:
        raise ValidationError(
            f"process_id must have exactly 4 components (hub.subhub.pipeline.phase). "
            f"Got {len(parts)} components: {process_id}. "
            f"FAIL HARD: Malformed process_id."
        )

    # FAIL HARD: Each component must be non-empty
    for i, part in enumerate(parts):
        if not part:
            raise ValidationError(
                f"process_id component {i+1} is empty: {process_id}. "
                f"FAIL HARD: All 4 components must be non-empty."
            )

    # FAIL HARD: Must match strict pattern
    pattern = r'^[a-z_]+\.[a-z_]+\.[a-z_]+\.[a-z0-9_]+$'
    if not re.match(pattern, process_id):
        raise ValidationError(
            f"Invalid process_id format: {process_id}. "
            f"Expected format: hub.subhub.pipeline.phase (all lowercase, underscores allowed). "
            f"FAIL HARD: Malformed process_id."
        )

    # FAIL HARD: Max length exceeded
    if len(process_id) > 100:
        raise ValidationError(
            f"process_id exceeds max length of 100: {len(process_id)}. "
            f"FAIL HARD: process_id too long."
        )

    # WARN: Validate hub component against known hubs
    valid_hubs = {'company', 'people', 'dol', 'blog_news', 'outreach', 'platform'}
    hub = parts[0]
    if hub not in valid_hubs:
        logger.warning(
            f"process_id hub '{hub}' not in known hubs: {valid_hubs}. "
            f"Proceeding but this may indicate a configuration issue."
        )


def validate_error_code(error_code: str) -> None:
    """
    Validate error_code format: PREFIX-CATEGORY-NUMBER

    Examples:
    - PSH-P5-001
    - DOL-002
    - PIPE-301
    - BLOG-101
    """
    if not error_code:
        raise ValidationError("error_code is REQUIRED")

    # Flexible pattern: PREFIX-CODE (where code can be alphanumeric)
    pattern = r'^[A-Z]+-[A-Z0-9]+-?[0-9]*$'
    if not re.match(pattern, error_code):
        raise ValidationError(
            f"Invalid error_code format: {error_code}. "
            f"Expected format: PREFIX-CATEGORY-NUMBER (e.g., PSH-P5-001)"
        )


# ============================================================================
# MASTER ERROR EMITTER
# ============================================================================

class MasterErrorEmitter:
    """
    Emits normalized error events to shq_master_error_log.

    DOCTRINE (ENFORCED - FAIL HARD):
    - Local First: Write to local sub-hub table BEFORE calling this emitter
    - Correlation Required: All errors MUST have correlation_id (UUID v4)
    - Process ID Required: All errors MUST have process_id (hub.subhub.pipeline.phase)
    - Append-Only: No updates or deletes allowed
    - Immutable History: Error history is immutable. Corrections are new records, never edits.

    ENFORCEMENT BEHAVIOR:
    - Missing correlation_id → ValidationError raised (FAIL HARD)
    - Missing process_id → ValidationError raised (FAIL HARD)
    - Malformed process_id → ValidationError raised (FAIL HARD)
    - Empty/whitespace values → ValidationError raised (FAIL HARD)

    This class will NEVER emit an error without valid correlation_id AND process_id.
    If ambiguity exists, FAIL CLOSED.

    Example:
        emitter = MasterErrorEmitter(db_conn, OperatingMode.STEADY_STATE)
        error_id = emitter.emit(
            correlation_id="550e8400-e29b-41d4-a716-446655440000",  # REQUIRED
            hub=Hub.PEOPLE,
            process_id="people.lifecycle.email.phase5",  # REQUIRED
            ...
        )
    """

    def __init__(self, db_connection, operating_mode: OperatingMode):
        """
        Initialize the error emitter.

        Args:
            db_connection: Database connection object with execute() method
            operating_mode: BURN_IN or STEADY_STATE (affects alerting)
        """
        self.db = db_connection
        self.operating_mode = operating_mode

    def emit(
        self,
        correlation_id: str,  # REQUIRED - FAIL HARD IF MISSING
        hub: Hub,
        process_id: str,  # REQUIRED - FAIL HARD IF MISSING
        pipeline_phase: str,
        entity_type: EntityType,
        severity: Severity,
        error_code: str,
        error_message: str,
        sub_hub: Optional[str] = None,
        entity_id: Optional[str] = None,
        source_tool: Optional[str] = None,
        retryable: bool = False,
        cost_impact_usd: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Emit error event to master error log.

        DOCTRINE (ENFORCED - FAIL HARD):
        - correlation_id is MANDATORY → ValidationError if missing/invalid
        - process_id is MANDATORY → ValidationError if missing/malformed
        - Error history is immutable. Corrections are new records, never edits.

        IMPORTANT: Write to local sub-hub table FIRST before calling this.

        Args:
            correlation_id: End-to-end trace ID (REQUIRED - FAIL HARD)
            hub: Source hub (company, people, dol, blog_news, outreach, platform)
            process_id: Canonical process identifier (REQUIRED - FAIL HARD)
                       Format: hub.subhub.pipeline.phase
            pipeline_phase: Phase name or number
            entity_type: Type of entity involved
            severity: LOW, MEDIUM, HIGH, CRITICAL
            error_code: Machine-readable error code
            error_message: Human-readable description
            sub_hub: Specific sub-hub (optional)
            entity_id: ID of affected entity (optional)
            source_tool: Tool/service that failed (optional)
            retryable: Can system retry automatically?
            cost_impact_usd: Estimated cost impact (optional)
            metadata: Additional context as dict (optional)

        Returns:
            error_id: UUID of inserted record

        Raises:
            ValidationError: If correlation_id or process_id is missing/invalid.
                            This is FAIL HARD - no error can be emitted without
                            valid correlation_id AND process_id.
        """
        # ============================================================
        # MANDATORY VALIDATION - FAIL HARD
        # ============================================================
        # These validations will raise ValidationError if fields are
        # missing, empty, or malformed. This is intentional - we FAIL
        # CLOSED rather than allowing incomplete error records.
        # ============================================================

        # FAIL HARD: correlation_id is MANDATORY
        validate_correlation_id(correlation_id)

        # FAIL HARD: process_id is MANDATORY
        validate_process_id(process_id)

        # FAIL HARD: error_code is MANDATORY
        validate_error_code(error_code)

        logger.debug(
            f"Validation passed for error emission",
            extra={
                "correlation_id": correlation_id,
                "process_id": process_id,
                "error_code": error_code
            }
        )

        # Generate error_id
        error_id = str(uuid.uuid4())

        # Build insert query
        query = """
            INSERT INTO public.shq_master_error_log (
                error_id, timestamp_utc, correlation_id,
                hub, sub_hub, process_id, pipeline_phase,
                entity_type, entity_id,
                severity, error_code, error_message,
                source_tool, operating_mode, retryable,
                cost_impact_usd, metadata
            ) VALUES (
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s
            )
        """

        params = (
            error_id,
            datetime.utcnow(),
            correlation_id,
            hub.value,
            sub_hub,
            process_id,
            pipeline_phase,
            entity_type.value,
            entity_id,
            severity.value,
            error_code,
            error_message,
            source_tool,
            self.operating_mode.value,
            retryable,
            cost_impact_usd,
            json.dumps(metadata) if metadata else None
        )

        try:
            self.db.execute(query, params)
            logger.info(
                f"Master error emitted: {error_id}",
                extra={
                    "error_id": error_id,
                    "correlation_id": correlation_id,
                    "hub": hub.value,
                    "process_id": process_id,
                    "severity": severity.value,
                    "error_code": error_code
                }
            )
            return error_id

        except Exception as e:
            logger.error(
                f"Failed to emit master error: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "hub": hub.value,
                    "error_code": error_code
                }
            )
            raise

    def emit_from_event(self, event: MasterErrorEvent) -> str:
        """
        Emit error from MasterErrorEvent dataclass.

        Args:
            event: MasterErrorEvent instance

        Returns:
            error_id: UUID of inserted record
        """
        return self.emit(
            correlation_id=event.correlation_id,
            hub=event.hub,
            process_id=event.process_id,
            pipeline_phase=event.pipeline_phase,
            entity_type=event.entity_type,
            severity=event.severity,
            error_code=event.error_code,
            error_message=event.error_message,
            sub_hub=event.sub_hub,
            entity_id=event.entity_id,
            source_tool=event.source_tool,
            retryable=event.retryable,
            cost_impact_usd=event.cost_impact_usd,
            metadata=event.metadata
        )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_process_id(hub: str, sub_hub: str, pipeline: str, phase: str) -> str:
    """
    Create a properly formatted process_id.

    Args:
        hub: Hub name (company, people, dol, blog_news, outreach)
        sub_hub: Sub-hub name (identity, lifecycle, form5500, news, etc.)
        pipeline: Pipeline name (matching, email, ingest, etc.)
        phase: Phase identifier (phase1, phase5, parse, etc.)

    Returns:
        Formatted process_id: hub.subhub.pipeline.phase

    Example:
        process_id = create_process_id("people", "lifecycle", "email", "phase5")
        # Returns: "people.lifecycle.email.phase5"
    """
    process_id = f"{hub}.{sub_hub}.{pipeline}.{phase}".lower()
    validate_process_id(process_id)
    return process_id


# ============================================================================
# PROCESS ID REGISTRY
# ============================================================================

# Pre-defined process IDs for common operations
PROCESS_IDS = {
    # Company Hub Pipeline
    "company.identity.matching.phase1": "Phase 1: Company Matching",
    "company.identity.matching.phase1b": "Phase 1b: Unmatched Hold Export",
    "company.identity.domain.phase2": "Phase 2: Domain Resolution",
    "company.identity.pattern.phase3": "Phase 3: Email Pattern Waterfall",
    "company.identity.verification.phase4": "Phase 4: Pattern Verification",
    "company.bit.aggregation.score": "BIT Engine: Signal Aggregation",
    "company.bit.decision.threshold": "BIT Engine: Decision Threshold",

    # People Sub-Hub
    "people.lifecycle.ingest.phase0": "Phase 0: People Ingest",
    "people.lifecycle.email.phase5": "Phase 5: Email Generation",
    "people.lifecycle.slot.phase6": "Phase 6: Slot Assignment",
    "people.lifecycle.queue.phase7": "Phase 7: Enrichment Queue",
    "people.lifecycle.output.phase8": "Phase 8: Output Writer",
    "people.talentflow.gate.company": "Talent Flow: Company Gate",

    # DOL Sub-Hub
    "dol.form5500.ingest.parse": "Form 5500: File Parsing",
    "dol.form5500.match.ein": "Form 5500: EIN Matching",
    "dol.form5500.extract.schedule_a": "Form 5500: Schedule A Extraction",
    "dol.form5500.signal.emit": "Form 5500: Signal Emission",

    # Blog/News Sub-Hub
    "blog_news.news.ingest.crawl": "News: Article Crawl",
    "blog_news.news.extract.entity": "News: Entity Extraction",
    "blog_news.news.match.company": "News: Company Matching",
    "blog_news.news.classify.event": "News: Event Classification",
    "blog_news.news.signal.emit": "News: Signal Emission",

    # Outreach Node
    "outreach.campaign.promote.log": "Campaign: Promote to Log",
    "outreach.campaign.enroll.sequence": "Campaign: Sequence Enrollment",
}


def get_process_description(process_id: str) -> Optional[str]:
    """Get human-readable description for a process_id"""
    return PROCESS_IDS.get(process_id)


def list_process_ids_for_hub(hub: str) -> Dict[str, str]:
    """Get all process_ids for a specific hub"""
    return {
        pid: desc
        for pid, desc in PROCESS_IDS.items()
        if pid.startswith(f"{hub}.")
    }
