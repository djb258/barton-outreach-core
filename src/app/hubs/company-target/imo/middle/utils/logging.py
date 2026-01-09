"""
Pipeline Logging Utilities
==========================
Centralized logging for pipeline phases with structured event tracking.

Integrates with:
- ops/master_error_log for error emission
- Correlation ID propagation
- Phase-level statistics
"""

import logging
import time
import json
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
from enum import Enum
from functools import wraps


# =============================================================================
# ENUMS
# =============================================================================

class EventType(Enum):
    """Pipeline event types."""
    PHASE_START = "phase_start"
    PHASE_COMPLETE = "phase_complete"
    PHASE_ERROR = "phase_error"
    RECORD_PROCESSED = "record_processed"
    RECORD_SKIPPED = "record_skipped"
    RECORD_FAILED = "record_failed"
    PROVIDER_CALL = "provider_call"
    PROVIDER_SUCCESS = "provider_success"
    PROVIDER_FAILURE = "provider_failure"
    SIGNAL_EMITTED = "signal_emitted"
    SIGNAL_DEDUPLICATED = "signal_deduplicated"
    HUB_GATE_PASSED = "hub_gate_passed"
    HUB_GATE_FAILED = "hub_gate_failed"
    ENRICHMENT_QUEUED = "enrichment_queued"
    PATTERN_DISCOVERED = "pattern_discovered"
    PATTERN_VERIFIED = "pattern_verified"
    EMAIL_GENERATED = "email_generated"
    SLOT_ASSIGNED = "slot_assigned"
    CORRELATION_ERROR = "correlation_error"


class LogLevel(Enum):
    """Log severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class PipelineEvent:
    """A single pipeline event."""
    event_type: EventType
    phase_name: str
    process_id: str
    correlation_id: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    level: LogLevel = LogLevel.INFO
    message: str = ""
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None  # company, person, etc.
    duration_ms: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage."""
        d = asdict(self)
        d['event_type'] = self.event_type.value
        d['level'] = self.level.value
        return d

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class PhaseMetrics:
    """Metrics for a single phase execution."""
    phase_name: str
    correlation_id: str
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    total_records: int = 0
    processed_records: int = 0
    skipped_records: int = 0
    failed_records: int = 0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def complete(self) -> None:
        """Mark phase as complete."""
        self.end_time = datetime.utcnow()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()

    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_records == 0:
            return 0.0
        return (self.processed_records / self.total_records) * 100


# =============================================================================
# PIPELINE LOGGER
# =============================================================================

class PipelineLogger:
    """
    Centralized logger for pipeline operations.

    Features:
    - Structured event logging
    - Phase-level metrics tracking
    - Correlation ID propagation
    - Integration with master error log
    """

    def __init__(
        self,
        name: str,
        correlation_id: str,
        log_level: LogLevel = LogLevel.INFO
    ):
        """
        Initialize pipeline logger.

        Args:
            name: Logger name (usually phase name)
            correlation_id: Correlation ID for tracing
            log_level: Minimum log level
        """
        self.name = name
        self.correlation_id = correlation_id
        self.log_level = log_level
        self._logger = logging.getLogger(f"pipeline.{name}")
        self._events: List[PipelineEvent] = []
        self._metrics: Optional[PhaseMetrics] = None
        self._start_time: Optional[float] = None

    def start_phase(self, total_records: int = 0) -> None:
        """
        Mark phase start.

        Args:
            total_records: Total records to process
        """
        self._start_time = time.time()
        self._metrics = PhaseMetrics(
            phase_name=self.name,
            correlation_id=self.correlation_id,
            total_records=total_records
        )

        self._log_event(
            EventType.PHASE_START,
            LogLevel.INFO,
            f"Phase {self.name} started with {total_records} records",
            metadata={"total_records": total_records}
        )

    def complete_phase(self) -> PhaseMetrics:
        """
        Mark phase complete and return metrics.

        Returns:
            PhaseMetrics with execution statistics
        """
        if self._metrics:
            self._metrics.complete()

        duration_ms = int((time.time() - (self._start_time or time.time())) * 1000)

        self._log_event(
            EventType.PHASE_COMPLETE,
            LogLevel.INFO,
            f"Phase {self.name} completed in {duration_ms}ms",
            duration_ms=duration_ms,
            metadata={
                "processed": self._metrics.processed_records if self._metrics else 0,
                "skipped": self._metrics.skipped_records if self._metrics else 0,
                "failed": self._metrics.failed_records if self._metrics else 0,
            }
        )

        return self._metrics

    def record_processed(
        self,
        entity_id: str,
        entity_type: str = "record",
        metadata: Dict[str, Any] = None
    ) -> None:
        """Log successful record processing."""
        if self._metrics:
            self._metrics.processed_records += 1

        self._log_event(
            EventType.RECORD_PROCESSED,
            LogLevel.DEBUG,
            f"Processed {entity_type} {entity_id}",
            entity_id=entity_id,
            entity_type=entity_type,
            metadata=metadata or {}
        )

    def record_skipped(
        self,
        entity_id: str,
        reason: str,
        entity_type: str = "record"
    ) -> None:
        """Log skipped record."""
        if self._metrics:
            self._metrics.skipped_records += 1

        self._log_event(
            EventType.RECORD_SKIPPED,
            LogLevel.DEBUG,
            f"Skipped {entity_type} {entity_id}: {reason}",
            entity_id=entity_id,
            entity_type=entity_type,
            metadata={"reason": reason}
        )

    def record_failed(
        self,
        entity_id: str,
        error: str,
        entity_type: str = "record"
    ) -> None:
        """Log failed record."""
        if self._metrics:
            self._metrics.failed_records += 1
            self._metrics.errors.append(f"{entity_id}: {error}")

        self._log_event(
            EventType.RECORD_FAILED,
            LogLevel.WARNING,
            f"Failed {entity_type} {entity_id}: {error}",
            entity_id=entity_id,
            entity_type=entity_type,
            metadata={"error": error}
        )

    def log_provider_call(
        self,
        provider_name: str,
        domain: str,
        success: bool,
        duration_ms: int,
        pattern: str = None,
        error: str = None
    ) -> None:
        """Log provider API call."""
        event_type = EventType.PROVIDER_SUCCESS if success else EventType.PROVIDER_FAILURE
        level = LogLevel.DEBUG if success else LogLevel.WARNING

        self._log_event(
            event_type,
            level,
            f"Provider {provider_name} {'succeeded' if success else 'failed'} for {domain}",
            duration_ms=duration_ms,
            metadata={
                "provider": provider_name,
                "domain": domain,
                "pattern": pattern,
                "error": error
            }
        )

    def log_signal(
        self,
        signal_type: str,
        entity_id: str,
        deduplicated: bool = False
    ) -> None:
        """Log signal emission or deduplication."""
        event_type = EventType.SIGNAL_DEDUPLICATED if deduplicated else EventType.SIGNAL_EMITTED
        level = LogLevel.DEBUG if deduplicated else LogLevel.INFO

        self._log_event(
            event_type,
            level,
            f"Signal {signal_type} {'deduplicated' if deduplicated else 'emitted'} for {entity_id}",
            entity_id=entity_id,
            metadata={"signal_type": signal_type}
        )

    def log_hub_gate(
        self,
        entity_id: str,
        passed: bool,
        missing_fields: List[str] = None
    ) -> None:
        """Log hub gate validation result."""
        event_type = EventType.HUB_GATE_PASSED if passed else EventType.HUB_GATE_FAILED
        level = LogLevel.DEBUG if passed else LogLevel.WARNING

        self._log_event(
            event_type,
            level,
            f"Hub gate {'passed' if passed else 'failed'} for {entity_id}",
            entity_id=entity_id,
            metadata={"missing_fields": missing_fields or []}
        )

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self._log_event(EventType.RECORD_PROCESSED, LogLevel.INFO, message, metadata=kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self._log_event(EventType.RECORD_PROCESSED, LogLevel.WARNING, message, metadata=kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self._log_event(EventType.PHASE_ERROR, LogLevel.ERROR, message, metadata=kwargs)

    def _log_event(
        self,
        event_type: EventType,
        level: LogLevel,
        message: str,
        entity_id: str = None,
        entity_type: str = None,
        duration_ms: int = None,
        metadata: Dict[str, Any] = None
    ) -> None:
        """Internal event logging."""
        event = PipelineEvent(
            event_type=event_type,
            phase_name=self.name,
            process_id=f"pipeline.{self.name}",
            correlation_id=self.correlation_id,
            level=level,
            message=message,
            entity_id=entity_id,
            entity_type=entity_type,
            duration_ms=duration_ms,
            metadata=metadata or {}
        )

        self._events.append(event)

        # Log to standard logger
        log_method = getattr(self._logger, level.value)
        log_method(f"[{self.correlation_id[:8]}] {message}")

    def get_events(self) -> List[PipelineEvent]:
        """Get all logged events."""
        return self._events.copy()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def log_phase_start(
    phase_name: str,
    correlation_id: str,
    total_records: int = 0,
    **kwargs
) -> PipelineLogger:
    """
    Convenience function to start logging a phase.

    Args:
        phase_name: Name of the phase
        correlation_id: Correlation ID
        total_records: Total records to process

    Returns:
        PipelineLogger instance
    """
    logger = PipelineLogger(phase_name, correlation_id)
    logger.start_phase(total_records)
    return logger


def log_phase_complete(logger: PipelineLogger) -> PhaseMetrics:
    """
    Convenience function to complete phase logging.

    Args:
        logger: PipelineLogger instance

    Returns:
        PhaseMetrics with execution statistics
    """
    return logger.complete_phase()


def log_error(
    phase_name: str,
    correlation_id: str,
    error_code: str,
    message: str,
    entity_id: str = None,
    **kwargs
) -> None:
    """
    Log an error to the pipeline logger.

    Also emits to master error log if available.

    Args:
        phase_name: Name of the phase
        correlation_id: Correlation ID
        error_code: Error code (e.g., "HUB-P1-001")
        message: Error message
        entity_id: Optional entity ID
        **kwargs: Additional metadata
    """
    logger = logging.getLogger(f"pipeline.{phase_name}")
    logger.error(f"[{correlation_id[:8]}] [{error_code}] {message}")

    # Try to emit to master error log
    try:
        from ops.master_error_log.master_error_emitter import emit_error
        emit_error(
            error_code=error_code,
            message=message,
            correlation_id=correlation_id,
            process_id=f"pipeline.{phase_name}",
            entity_id=entity_id,
            metadata=kwargs
        )
    except ImportError:
        pass  # Master error log not available


# =============================================================================
# DECORATOR
# =============================================================================

def logged_phase(phase_name: str):
    """
    Decorator to automatically log phase execution.

    Usage:
        @logged_phase("phase1")
        def run(self, correlation_id: str, ...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to get correlation_id from kwargs or args
            correlation_id = kwargs.get('correlation_id', 'unknown')

            logger = PipelineLogger(phase_name, correlation_id)
            logger.start_phase()

            try:
                result = func(*args, **kwargs)
                logger.complete_phase()
                return result
            except Exception as e:
                logger.error(f"Phase failed: {str(e)}")
                raise

        return wrapper
    return decorator


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "EventType",
    "LogLevel",
    # Data classes
    "PipelineEvent",
    "PhaseMetrics",
    # Logger class
    "PipelineLogger",
    # Convenience functions
    "log_phase_start",
    "log_phase_complete",
    "log_error",
    # Decorator
    "logged_phase",
]
