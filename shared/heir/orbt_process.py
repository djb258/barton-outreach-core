#!/usr/bin/env python3
"""
ORBT Process Tracking — Operate, Repair, Build, Train

DOCTRINE: Every process MUST have a process_id for lifecycle tracking.
The process_id groups related operations under a single execution session.

Format: PRC-<SYSTEM>-<EPOCH_TIMESTAMP>
Example: PRC-OUTREACH-1738772400

Process Lifecycle:
1. OPERATE - Normal execution
2. REPAIR  - Error recovery/remediation
3. BUILD   - Creation/modification
4. TRAIN   - Learning/optimization

Every pipeline run, batch job, or significant operation should:
1. Start a process with start_process()
2. Track operations within that process
3. End with end_process()

The process_id enables:
- Grouping related operations
- Measuring process duration
- Tracking success/failure rates
- Correlating errors to processes
"""

import os
import time
import uuid
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager


# =============================================================================
# CONFIGURATION
# =============================================================================

class OrbtLayer(Enum):
    """ORBT lifecycle layers."""
    OPERATE = "OPERATE"  # Normal execution
    REPAIR = "REPAIR"    # Error recovery
    BUILD = "BUILD"      # Creation/modification
    TRAIN = "TRAIN"      # Learning/optimization


class ProcessStatus(Enum):
    """Process execution status."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Default configuration
DEFAULT_SYSTEM = "OUTREACH"


# =============================================================================
# PROCESS ID
# =============================================================================

@dataclass
class ProcessId:
    """
    ORBT Process identifier.

    Contains the process_id and metadata about the process.
    """
    process_id: str
    system: str
    epoch: int
    started_at: datetime
    orbt_layer: OrbtLayer
    status: ProcessStatus = ProcessStatus.RUNNING
    ended_at: Optional[datetime] = None
    operations: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def __str__(self) -> str:
        return self.process_id

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get process duration in seconds."""
        if self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        return (datetime.now() - self.started_at).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "process_id": self.process_id,
            "system": self.system,
            "epoch": self.epoch,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "orbt_layer": self.orbt_layer.value,
            "status": self.status.value,
            "duration_seconds": self.duration_seconds,
            "operations_count": len(self.operations),
            "metadata": self.metadata,
            "error": self.error,
        }


# =============================================================================
# PROCESS TRACKER
# =============================================================================

class OrbtProcess:
    """
    ORBT Process tracker.

    Manages process lifecycle and tracks operations within processes.

    Usage:
        orbt = OrbtProcess()

        # Start a process
        process = orbt.start_process(OrbtLayer.OPERATE)
        print(process.process_id)  # PRC-OUTREACH-1738772400

        # Track operations
        orbt.log_operation("fetch_companies", count=100)
        orbt.log_operation("process_slots", count=300)

        # End process
        orbt.end_process(success=True)

        # Or use context manager
        with orbt.process(OrbtLayer.BUILD) as proc:
            # Operations automatically tracked
            do_work()
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Singleton pattern for global process tracker."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, system: str = None):
        """
        Initialize ORBT process tracker.

        Args:
            system: System name for process IDs (default: OUTREACH)
        """
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.system = system or os.getenv("BARTON_SYSTEM", DEFAULT_SYSTEM)

        # Thread-local storage for current process
        self._local = threading.local()

        # Process history (limited to last 100)
        self._history: List[ProcessId] = []
        self._history_lock = threading.Lock()
        self._max_history = 100

        self._initialized = True

    def start_process(
        self,
        layer: OrbtLayer = OrbtLayer.OPERATE,
        metadata: Dict[str, Any] = None
    ) -> ProcessId:
        """
        Start a new process.

        Args:
            layer: ORBT layer (OPERATE, REPAIR, BUILD, TRAIN)
            metadata: Optional metadata

        Returns:
            ProcessId for the new process
        """
        epoch = int(time.time())
        process_id = f"PRC-{self.system}-{epoch}"

        proc = ProcessId(
            process_id=process_id,
            system=self.system,
            epoch=epoch,
            started_at=datetime.now(),
            orbt_layer=layer,
            metadata=metadata or {},
        )

        # Set as current process
        self._local.current = proc

        return proc

    def current(self) -> Optional[ProcessId]:
        """Get the current process in this context."""
        return getattr(self._local, 'current', None)

    def log_operation(
        self,
        operation: str,
        success: bool = True,
        **kwargs
    ) -> None:
        """
        Log an operation within the current process.

        Args:
            operation: Operation name/description
            success: Whether operation succeeded
            **kwargs: Additional operation data
        """
        proc = self.current()
        if proc:
            proc.operations.append({
                "operation": operation,
                "timestamp": datetime.now().isoformat(),
                "success": success,
                **kwargs
            })

    def end_process(
        self,
        success: bool = True,
        error: str = None
    ) -> Optional[ProcessId]:
        """
        End the current process.

        Args:
            success: Whether process completed successfully
            error: Error message if failed

        Returns:
            The completed ProcessId
        """
        proc = self.current()
        if proc:
            proc.ended_at = datetime.now()
            proc.status = ProcessStatus.COMPLETED if success else ProcessStatus.FAILED
            proc.error = error

            # Add to history
            with self._history_lock:
                self._history.append(proc)
                if len(self._history) > self._max_history:
                    self._history = self._history[-self._max_history:]

            # Clear current
            self._local.current = None

        return proc

    def cancel_process(self, reason: str = None) -> Optional[ProcessId]:
        """Cancel the current process."""
        proc = self.current()
        if proc:
            proc.ended_at = datetime.now()
            proc.status = ProcessStatus.CANCELLED
            proc.error = reason or "Process cancelled"
            self._local.current = None
        return proc

    def get_or_start(
        self,
        layer: OrbtLayer = OrbtLayer.OPERATE,
        metadata: Dict[str, Any] = None
    ) -> ProcessId:
        """Get current process or start a new one."""
        current = self.current()
        if current is None:
            return self.start_process(layer, metadata)
        return current

    @contextmanager
    def process(
        self,
        layer: OrbtLayer = OrbtLayer.OPERATE,
        metadata: Dict[str, Any] = None
    ):
        """
        Context manager for process lifecycle.

        Usage:
            with orbt.process(OrbtLayer.BUILD) as proc:
                do_work()
            # Process automatically ended

            # On exception, process marked as failed
            with orbt.process() as proc:
                raise Exception("Oops")
            # proc.status == ProcessStatus.FAILED
        """
        proc = self.start_process(layer, metadata)
        try:
            yield proc
            self.end_process(success=True)
        except Exception as e:
            self.end_process(success=False, error=str(e))
            raise

    def history(self, limit: int = 10) -> List[ProcessId]:
        """Get recent process history."""
        with self._history_lock:
            return list(self._history[-limit:])


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Global instance
_orbt = None


def get_orbt() -> OrbtProcess:
    """Get or create the global ORBT process tracker."""
    global _orbt
    if _orbt is None:
        _orbt = OrbtProcess()
    return _orbt


def generate_process_id(
    layer: OrbtLayer = OrbtLayer.OPERATE,
    metadata: Dict[str, Any] = None
) -> str:
    """
    Generate a new process_id and start tracking.

    Args:
        layer: ORBT layer
        metadata: Optional metadata

    Returns:
        The process_id string

    Example:
        process_id = generate_process_id(OrbtLayer.BUILD)
        # PRC-OUTREACH-1738772400
    """
    return get_orbt().start_process(layer, metadata).process_id


def get_current_process_id() -> Optional[str]:
    """Get the current process_id if one exists."""
    proc = get_orbt().current()
    return proc.process_id if proc else None


def require_process_id(layer: OrbtLayer = OrbtLayer.OPERATE) -> str:
    """
    Get current process_id or start a new process.

    Use this when you need a process_id but don't want to fail
    if one wasn't started upstream.
    """
    return get_orbt().get_or_start(layer).process_id


def log_operation(operation: str, success: bool = True, **kwargs) -> None:
    """Log an operation to the current process."""
    get_orbt().log_operation(operation, success, **kwargs)


def end_current_process(success: bool = True, error: str = None) -> None:
    """End the current process."""
    get_orbt().end_process(success, error)


# =============================================================================
# DECORATOR
# =============================================================================

def with_process(layer: OrbtLayer = OrbtLayer.OPERATE):
    """
    Decorator to automatically manage process lifecycle.

    Usage:
        @with_process(OrbtLayer.BUILD)
        def my_pipeline():
            # Process automatically started and ended
            do_work()
    """
    import functools

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with get_orbt().process(layer):
                return func(*args, **kwargs)
        return wrapper

    return decorator


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Classes
    "OrbtProcess",
    "ProcessId",
    "OrbtLayer",
    "ProcessStatus",
    # Functions
    "get_orbt",
    "generate_process_id",
    "get_current_process_id",
    "require_process_id",
    "log_operation",
    "end_current_process",
    # Decorator
    "with_process",
]
