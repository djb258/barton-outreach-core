"""
Logging Utilities
=================
Structured pipeline logging and event tracking.
Per doctrine: every match decision, confidence, domain source,
enrichment source, slot fills, collisions, errors with full stacktraces.
"""

import json
import logging
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pathlib import Path
import uuid


class LogLevel(Enum):
    """Log severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventType(Enum):
    """Pipeline event types for structured logging."""
    # Phase events
    PHASE_START = "phase_start"
    PHASE_COMPLETE = "phase_complete"
    PHASE_ERROR = "phase_error"

    # Match events
    MATCH_DOMAIN = "match_domain"
    MATCH_EXACT = "match_exact"
    MATCH_FUZZY = "match_fuzzy"
    MATCH_AMBIGUOUS = "match_ambiguous"
    MATCH_NONE = "match_none"

    # Domain events
    DOMAIN_RESOLVED = "domain_resolved"
    DOMAIN_SCRAPED = "domain_scraped"
    DOMAIN_DNS_LOOKUP = "domain_dns_lookup"
    DOMAIN_PARKED = "domain_parked"
    DOMAIN_FAILED = "domain_failed"

    # Pattern events
    PATTERN_DISCOVERED = "pattern_discovered"
    PATTERN_VERIFIED = "pattern_verified"
    PATTERN_FAILED = "pattern_failed"

    # Email events
    EMAIL_GENERATED = "email_generated"
    EMAIL_DUPLICATE = "email_duplicate"

    # Slot events
    SLOT_ASSIGNED = "slot_assigned"
    SLOT_COLLISION = "slot_collision"
    SLOT_EMPTY = "slot_empty"

    # Queue events
    QUEUE_ADD = "queue_add"
    QUEUE_RETRY = "queue_retry"
    QUEUE_COMPLETE = "queue_complete"

    # General events
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class PipelineEvent:
    """A structured pipeline event for audit logging."""
    event_id: str
    timestamp: str
    pipeline_run_id: str
    phase: Optional[int]
    event_type: str
    message: str
    level: str
    entity_type: Optional[str] = None  # 'company', 'person', 'domain', 'pattern'
    entity_id: Optional[str] = None
    confidence: Optional[float] = None
    source: Optional[str] = None  # Provider or method that produced result
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    stacktrace: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class PipelineLogger:
    """
    Structured logger for pipeline events per doctrine.

    Features:
    - Phase-aware logging
    - Entity tracking
    - Event aggregation
    - File and database persistence
    - Full audit trail
    """

    def __init__(self, run_id: str = None, config: Dict[str, Any] = None):
        """
        Initialize pipeline logger.

        Args:
            run_id: Unique identifier for this pipeline run
            config: Logging configuration
        """
        self.run_id = run_id or str(uuid.uuid4())[:8]
        self.config = config or {}
        self.events: List[PipelineEvent] = []
        self.current_phase: Optional[int] = None
        self._event_counts: Dict[str, int] = {}

        # Set up Python logger
        self.logger = logging.getLogger(f"pipeline.{self.run_id}")
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up logging handlers."""
        log_level = getattr(logging, self.config.get('log_level', 'INFO').upper())
        self.logger.setLevel(log_level)

        # Console handler
        if not self.logger.handlers:
            console = logging.StreamHandler()
            console.setLevel(log_level)
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console.setFormatter(formatter)
            self.logger.addHandler(console)

        # File handler (if configured)
        if self.config.get('log_to_file'):
            log_dir = Path(self.config.get('log_directory', './logs'))
            log_dir.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(
                log_dir / f"pipeline_{self.run_id}.log"
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s'
            ))
            self.logger.addHandler(file_handler)

    def set_phase(self, phase: int) -> None:
        """Set current pipeline phase for context."""
        self.current_phase = phase

    def _create_event(self, event_type: EventType, message: str,
                      level: LogLevel = LogLevel.INFO, **kwargs) -> PipelineEvent:
        """Create a structured event."""
        event = PipelineEvent(
            event_id=str(uuid.uuid4())[:12],
            timestamp=datetime.utcnow().isoformat(),
            pipeline_run_id=self.run_id,
            phase=self.current_phase,
            event_type=event_type.value,
            message=message,
            level=level.value,
            **kwargs
        )

        # Track event counts
        self._event_counts[event_type.value] = self._event_counts.get(event_type.value, 0) + 1

        return event

    def log_event(self, event_type: EventType, message: str,
                  level: LogLevel = LogLevel.INFO, **kwargs) -> PipelineEvent:
        """
        Log a structured pipeline event.

        Args:
            event_type: Type of event
            message: Human-readable message
            level: Log severity
            **kwargs: Additional event data (entity_type, entity_id, confidence, etc.)

        Returns:
            Created PipelineEvent
        """
        event = self._create_event(event_type, message, level, **kwargs)
        self.events.append(event)

        # Also log to Python logger
        log_func = getattr(self.logger, level.value)
        log_func(f"[{event_type.value}] {message}")

        return event

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.log_event(EventType.INFO, message, LogLevel.DEBUG, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.log_event(EventType.INFO, message, LogLevel.INFO, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.log_event(EventType.WARNING, message, LogLevel.WARNING, **kwargs)

    def error(self, message: str, error: Exception = None, **kwargs) -> None:
        """Log error with optional exception."""
        error_str = str(error) if error else None
        stacktrace = traceback.format_exc() if error else None

        self.log_event(
            EventType.ERROR, message, LogLevel.ERROR,
            error=error_str, stacktrace=stacktrace, **kwargs
        )

    def critical(self, message: str, error: Exception = None, **kwargs) -> None:
        """Log critical error."""
        error_str = str(error) if error else None
        stacktrace = traceback.format_exc() if error else None

        self.log_event(
            EventType.ERROR, message, LogLevel.CRITICAL,
            error=error_str, stacktrace=stacktrace, **kwargs
        )

    # Match logging methods
    def log_match_domain(self, raw_id: str, canonical_id: str, domain: str) -> None:
        """Log GOLD domain match."""
        self.log_event(
            EventType.MATCH_DOMAIN,
            f"Domain match: {domain}",
            entity_type="company",
            entity_id=raw_id,
            confidence=1.0,
            source="domain",
            metadata={"canonical_id": canonical_id, "domain": domain}
        )

    def log_match_exact(self, raw_id: str, canonical_id: str, name: str) -> None:
        """Log SILVER exact name match."""
        self.log_event(
            EventType.MATCH_EXACT,
            f"Exact name match: {name}",
            entity_type="company",
            entity_id=raw_id,
            confidence=0.95,
            source="exact_name",
            metadata={"canonical_id": canonical_id, "name": name}
        )

    def log_match_fuzzy(self, raw_id: str, canonical_id: str,
                        score: float, method: str) -> None:
        """Log BRONZE fuzzy match."""
        self.log_event(
            EventType.MATCH_FUZZY,
            f"Fuzzy match (score={score:.3f}, method={method})",
            entity_type="company",
            entity_id=raw_id,
            confidence=score,
            source=method,
            metadata={"canonical_id": canonical_id}
        )

    def log_match_ambiguous(self, raw_id: str, candidates: List[Dict]) -> None:
        """Log ambiguous match collision."""
        self.log_event(
            EventType.MATCH_AMBIGUOUS,
            f"Ambiguous match: {len(candidates)} candidates within threshold",
            LogLevel.WARNING,
            entity_type="company",
            entity_id=raw_id,
            metadata={"candidates": candidates}
        )

    def log_match_none(self, raw_id: str, reason: str) -> None:
        """Log no match found."""
        self.log_event(
            EventType.MATCH_NONE,
            f"No match: {reason}",
            entity_type="company",
            entity_id=raw_id,
            metadata={"reason": reason}
        )

    # Domain logging methods
    def log_domain_resolved(self, company_id: str, domain: str, source: str) -> None:
        """Log domain resolution."""
        self.log_event(
            EventType.DOMAIN_RESOLVED,
            f"Domain resolved: {domain} (source={source})",
            entity_type="domain",
            entity_id=company_id,
            source=source,
            metadata={"domain": domain}
        )

    def log_domain_failed(self, company_id: str, reason: str) -> None:
        """Log domain resolution failure."""
        self.log_event(
            EventType.DOMAIN_FAILED,
            f"Domain resolution failed: {reason}",
            LogLevel.WARNING,
            entity_type="domain",
            entity_id=company_id,
            metadata={"reason": reason}
        )

    # Slot logging methods
    def log_slot_assigned(self, company_id: str, slot_type: str,
                          person_id: str, title: str) -> None:
        """Log slot assignment."""
        self.log_event(
            EventType.SLOT_ASSIGNED,
            f"Slot assigned: {slot_type} <- {title}",
            entity_type="slot",
            entity_id=company_id,
            metadata={"slot_type": slot_type, "person_id": person_id, "title": title}
        )

    def log_slot_collision(self, company_id: str, slot_type: str,
                           existing_id: str, new_id: str) -> None:
        """Log slot collision."""
        self.log_event(
            EventType.SLOT_COLLISION,
            f"Slot collision: {slot_type} (existing={existing_id}, new={new_id})",
            LogLevel.WARNING,
            entity_type="slot",
            entity_id=company_id,
            metadata={"slot_type": slot_type, "existing_id": existing_id, "new_id": new_id}
        )

    def get_events(self, phase: int = None, event_type: str = None,
                   level: str = None) -> List[PipelineEvent]:
        """Get events with optional filters."""
        results = self.events

        if phase is not None:
            results = [e for e in results if e.phase == phase]

        if event_type:
            results = [e for e in results if e.event_type == event_type]

        if level:
            results = [e for e in results if e.level == level]

        return results

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of logged events."""
        return {
            "pipeline_run_id": self.run_id,
            "total_events": len(self.events),
            "events_by_type": dict(self._event_counts),
            "errors": len([e for e in self.events if e.level in ['error', 'critical']]),
            "warnings": len([e for e in self.events if e.level == 'warning']),
        }

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Get full audit log as list of dicts."""
        return [e.to_dict() for e in self.events]

    def save_audit_log(self, file_path: str) -> None:
        """Save audit log to JSON file."""
        with open(file_path, 'w') as f:
            json.dump({
                "summary": self.get_summary(),
                "events": self.get_audit_log()
            }, f, indent=2)

    def save_events_jsonl(self, file_path: str) -> None:
        """Save events to JSONL file (one event per line)."""
        with open(file_path, 'w') as f:
            for event in self.events:
                f.write(event.to_json() + '\n')


# Helper functions for common logging patterns

def log_phase_start(logger: PipelineLogger, phase: int,
                    phase_name: str, input_count: int) -> None:
    """Log the start of a pipeline phase."""
    logger.set_phase(phase)
    logger.log_event(
        EventType.PHASE_START,
        f"Phase {phase} ({phase_name}) started with {input_count} records",
        metadata={"phase_name": phase_name, "input_count": input_count}
    )


def log_phase_complete(logger: PipelineLogger, phase: int,
                       phase_name: str, output_count: int,
                       duration_seconds: float, stats: Dict = None) -> None:
    """Log the completion of a pipeline phase."""
    logger.log_event(
        EventType.PHASE_COMPLETE,
        f"Phase {phase} ({phase_name}) completed: {output_count} records in {duration_seconds:.2f}s",
        metadata={
            "phase_name": phase_name,
            "output_count": output_count,
            "duration_seconds": duration_seconds,
            "stats": stats or {}
        }
    )


def log_error(logger: PipelineLogger, error: Exception,
              entity_type: str = None, entity_id: str = None,
              context: Dict[str, Any] = None) -> None:
    """Log an error with context."""
    logger.error(
        str(error),
        error=error,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata=context or {}
    )


def setup_file_logging(log_path: str, level: str = "INFO") -> logging.Logger:
    """Set up file-based logging and return logger."""
    logger = logging.getLogger("pipeline")
    logger.setLevel(getattr(logging, level.upper()))

    handler = logging.FileHandler(log_path)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s'
    ))
    logger.addHandler(handler)

    return logger
