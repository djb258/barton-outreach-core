"""
Base Failure Spoke - Abstract class for all failure spokes
==========================================================
Provides common functionality for failure handling.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from ..wheel.bicycle_wheel import FailureSpoke
from ..wheel.wheel_result import FailureResult, FailureType


logger = logging.getLogger(__name__)


@dataclass
class FailureRecord:
    """A record in a failure table"""
    failure_id: str
    record_id: str
    failure_type: FailureType
    failure_reason: str
    original_data: Dict[str, Any]
    resolution_path: str
    severity: str = "error"
    retry_eligible: bool = False
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    resolution_status: str = "open"  # open, investigating, resolved, wont_fix


class BaseFailureSpoke(FailureSpoke):
    """
    Base class for all failure spokes.

    Provides:
    - Standard failure routing
    - Master Failure Hub reporting
    - Retry logic
    - Resolution tracking
    """

    def __init__(
        self,
        name: str,
        failure_type: FailureType,
        table_name: str,
        resolution_path: str,
        severity: str = "error",
        retry_eligible: bool = False,
        max_retries: int = 3
    ):
        super().__init__(name, failure_type, table_name)
        self.resolution_path = resolution_path
        self.default_severity = severity
        self.retry_eligible = retry_eligible
        self.max_retries = max_retries

        # In-memory storage (would be DB in production)
        self._records: List[FailureRecord] = []

        # Stats
        self.stats = {
            'total_failures': 0,
            'resolved': 0,
            'retried': 0,
            'escalated': 0
        }

    def route(self, data: Any, reason: str) -> FailureResult:
        """
        Route a failed record to this failure spoke.

        Creates a FailureRecord and returns a FailureResult.
        """
        self.stats['total_failures'] += 1

        # Create failure record
        record = FailureRecord(
            failure_id=f"{self.name}_{self.stats['total_failures']}",
            record_id=str(getattr(data, 'person_id', None) or id(data)),
            failure_type=self.failure_type,
            failure_reason=reason,
            original_data=self._serialize_data(data),
            resolution_path=self.resolution_path,
            severity=self.default_severity,
            retry_eligible=self.retry_eligible,
            max_retries=self.max_retries
        )

        # Store record
        self._records.append(record)

        # Log to Master Failure Hub
        self._report_to_master_hub(record)

        # Return FailureResult
        return FailureResult(
            failure_type=self.failure_type,
            record_id=record.record_id,
            original_data=data,
            failure_reason=reason,
            resolution_path=self.resolution_path,
            retry_eligible=self.retry_eligible,
            severity=self.default_severity
        )

    def _serialize_data(self, data: Any) -> Dict[str, Any]:
        """Serialize data for storage"""
        if hasattr(data, '__dict__'):
            return {k: str(v) for k, v in data.__dict__.items()}
        elif isinstance(data, dict):
            return {k: str(v) for k, v in data.items()}
        else:
            return {'raw': str(data)}

    def _report_to_master_hub(self, record: FailureRecord):
        """Report failure to Master Failure Hub (shq_error_log)"""
        master_record = {
            'source_hub': 'pipeline_engine',
            'sub_hub': self.name,
            'error_code': self.failure_type.value,
            'error_message': record.failure_reason,
            'severity': record.severity,
            'component': f'failure_spoke.{self.name}',
            'resolution_status': record.resolution_status,
            'created_at': record.created_at.isoformat()
        }
        logger.info(f"Reported to Master Failure Hub: {master_record}")
        # In production, this would insert into shq_error_log

    def resolve(self, failure_id: str, resolution_notes: str = "") -> bool:
        """Mark a failure as resolved"""
        for record in self._records:
            if record.failure_id == failure_id:
                record.resolution_status = "resolved"
                record.resolved_at = datetime.now()
                record.updated_at = datetime.now()
                self.stats['resolved'] += 1
                return True
        return False

    def retry(self, failure_id: str) -> Optional[Any]:
        """
        Attempt to retry a failed record.

        Returns the original data if retry is eligible and within limits.
        """
        for record in self._records:
            if record.failure_id == failure_id:
                if not record.retry_eligible:
                    logger.warning(f"Failure {failure_id} is not retry eligible")
                    return None
                if record.retry_count >= record.max_retries:
                    logger.warning(f"Failure {failure_id} has exceeded max retries")
                    return None

                record.retry_count += 1
                record.updated_at = datetime.now()
                self.stats['retried'] += 1
                return record.original_data
        return None

    def get_open_failures(self) -> List[FailureRecord]:
        """Get all open (unresolved) failures"""
        return [r for r in self._records if r.resolution_status == "open"]

    def get_retry_eligible(self) -> List[FailureRecord]:
        """Get failures eligible for retry"""
        return [
            r for r in self._records
            if r.retry_eligible and r.retry_count < r.max_retries
            and r.resolution_status == "open"
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get failure spoke statistics"""
        return {
            'spoke_name': self.name,
            'failure_type': self.failure_type.value,
            'table_name': self.table_name,
            'total_failures': self.stats['total_failures'],
            'open': len(self.get_open_failures()),
            'resolved': self.stats['resolved'],
            'retried': self.stats['retried'],
            'retry_eligible': len(self.get_retry_eligible())
        }
