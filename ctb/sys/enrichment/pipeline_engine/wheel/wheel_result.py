"""
Wheel Result Classes
====================
Standardized result objects for wheel processing.

Every spoke returns a WheelResult that indicates:
- Success/failure status
- Data to pass to next spoke
- Failure routing information
- Hub feedback signals
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum


class ResultStatus(Enum):
    """Status of a spoke/wheel operation"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    PENDING = "pending"


class FailureType(Enum):
    """Standard failure types that route to failure spokes"""
    NO_MATCH = "no_match"
    LOW_CONFIDENCE = "low_confidence"
    LOST_SLOT = "lost_slot"
    NO_PATTERN = "no_pattern"
    EMAIL_INVALID = "email_invalid"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    VALIDATION_ERROR = "validation_error"


@dataclass
class SpokeResult:
    """
    Result from a single spoke operation.

    Attributes:
        status: SUCCESS, FAILED, SKIPPED, PENDING
        data: Processed data to pass forward
        failure_type: If failed, which failure spoke to route to
        failure_reason: Human-readable failure description
        metrics: Stats for this spoke (processing time, counts, etc.)
        hub_signal: Optional signal to feed back to hub (e.g., +10 BIT score)
    """
    status: ResultStatus
    data: Any = None
    failure_type: Optional[FailureType] = None
    failure_reason: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    hub_signal: Optional[Dict[str, Any]] = None

    @property
    def success(self) -> bool:
        return self.status == ResultStatus.SUCCESS

    @property
    def failed(self) -> bool:
        return self.status == ResultStatus.FAILED

    def to_dict(self) -> Dict[str, Any]:
        return {
            'status': self.status.value,
            'data': self.data,
            'failure_type': self.failure_type.value if self.failure_type else None,
            'failure_reason': self.failure_reason,
            'metrics': self.metrics,
            'hub_signal': self.hub_signal
        }


@dataclass
class FailureResult:
    """
    Result from a failure spoke.

    Failure spokes are first-class citizens - they process failed records
    and determine resolution paths.
    """
    failure_type: FailureType
    record_id: str
    original_data: Any
    failure_reason: str
    resolution_path: str  # e.g., "manual_review", "auto_retry", "discard"
    retry_eligible: bool = False
    retry_after: Optional[datetime] = None
    severity: str = "error"  # info, warning, error, critical

    def to_dict(self) -> Dict[str, Any]:
        return {
            'failure_type': self.failure_type.value,
            'record_id': self.record_id,
            'failure_reason': self.failure_reason,
            'resolution_path': self.resolution_path,
            'retry_eligible': self.retry_eligible,
            'retry_after': self.retry_after.isoformat() if self.retry_after else None,
            'severity': self.severity
        }


@dataclass
class WheelResult:
    """
    Aggregate result from a complete wheel rotation.

    A wheel processes data through all its spokes, collecting results
    and routing failures to appropriate failure spokes.
    """
    wheel_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None

    # Counts
    total_processed: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0

    # Detailed results
    spoke_results: List[SpokeResult] = field(default_factory=list)
    failure_results: List[FailureResult] = field(default_factory=list)

    # Hub feedback
    hub_signals: List[Dict[str, Any]] = field(default_factory=list)

    # Output data
    output_data: List[Any] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_processed == 0:
            return 0.0
        return (self.successful / self.total_processed) * 100

    @property
    def duration_seconds(self) -> float:
        if not self.completed_at:
            return 0.0
        return (self.completed_at - self.started_at).total_seconds()

    def add_success(self, result: SpokeResult):
        """Add a successful spoke result"""
        self.spoke_results.append(result)
        self.successful += 1
        self.total_processed += 1
        if result.hub_signal:
            self.hub_signals.append(result.hub_signal)
        if result.data:
            self.output_data.append(result.data)

    def add_failure(self, result: FailureResult):
        """Add a failure result"""
        self.failure_results.append(result)
        self.failed += 1
        self.total_processed += 1

    def add_skip(self):
        """Record a skipped item"""
        self.skipped += 1
        self.total_processed += 1

    def complete(self):
        """Mark wheel rotation as complete"""
        self.completed_at = datetime.now()

    def summary(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        failure_breakdown = {}
        for fr in self.failure_results:
            ft = fr.failure_type.value
            failure_breakdown[ft] = failure_breakdown.get(ft, 0) + 1

        return {
            'wheel_name': self.wheel_name,
            'duration_seconds': self.duration_seconds,
            'total_processed': self.total_processed,
            'successful': self.successful,
            'failed': self.failed,
            'skipped': self.skipped,
            'success_rate': f"{self.success_rate:.1f}%",
            'failure_breakdown': failure_breakdown,
            'hub_signals_sent': len(self.hub_signals)
        }

    def __str__(self) -> str:
        return (
            f"WheelResult({self.wheel_name}): "
            f"{self.successful}/{self.total_processed} success ({self.success_rate:.1f}%), "
            f"{self.failed} failed, {self.skipped} skipped"
        )
