#!/usr/bin/env python3
"""
HEIR+ORBT Unified Tracking — Combined Identity and Process Management

DOCTRINE: Every operation MUST have both:
1. unique_id (HEIR) - Identity tracing
2. process_id (ORBT) - Process lifecycle

This module provides a unified interface for tracking operations
with both HEIR and ORBT compliance.

Usage:
    from src.sys.heir import Tracker, track_operation

    # Simple usage
    with track_operation("process_companies") as ctx:
        # ctx.unique_id and ctx.process_id available
        process_companies(unique_id=ctx.unique_id, process_id=ctx.process_id)

    # Full context
    tracker = Tracker()
    with tracker.operation("batch_import", layer=OrbtLayer.BUILD) as ctx:
        for item in items:
            tracker.log("import_item", item_id=item.id)
        tracker.log("complete", count=len(items))

    # Decorator
    @tracked(layer=OrbtLayer.OPERATE)
    def my_pipeline():
        # unique_id and process_id auto-managed
        ctx = get_tracking_context()
        return ctx.unique_id, ctx.process_id
"""

import threading
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager
import functools

from .heir_identity import (
    HeirIdentity,
    HeirId,
    HeirFormat,
    get_heir,
    generate_unique_id,
    get_current_unique_id,
)
from .orbt_process import (
    OrbtProcess,
    ProcessId,
    OrbtLayer,
    ProcessStatus,
    get_orbt,
    generate_process_id,
    get_current_process_id,
)


# =============================================================================
# TRACKING CONTEXT
# =============================================================================

@dataclass
class TrackingContext:
    """
    Combined HEIR+ORBT tracking context.

    Provides both unique_id and process_id for full traceability.
    """
    unique_id: str
    process_id: str
    heir_id: HeirId
    process: ProcessId
    operation_name: str
    started_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"TrackingContext(unique_id={self.unique_id}, process_id={self.process_id})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "unique_id": self.unique_id,
            "process_id": self.process_id,
            "operation_name": self.operation_name,
            "started_at": self.started_at.isoformat(),
            "orbt_layer": self.process.orbt_layer.value,
            "metadata": self.metadata,
        }

    def as_params(self) -> Dict[str, str]:
        """Get unique_id and process_id as dict for passing to functions."""
        return {
            "unique_id": self.unique_id,
            "process_id": self.process_id,
        }


# =============================================================================
# UNIFIED TRACKER
# =============================================================================

class Tracker:
    """
    Unified HEIR+ORBT tracker.

    Manages both unique_id and process_id together for complete
    operation traceability.

    Usage:
        tracker = Tracker()

        # Start tracking
        with tracker.operation("my_pipeline") as ctx:
            # Do work with full context
            result = do_work(
                unique_id=ctx.unique_id,
                process_id=ctx.process_id
            )

            # Log operations
            tracker.log("step_1", records=100)
            tracker.log("step_2", records=200)

        # Check status
        print(tracker.last_context)
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return

        self._heir = get_heir()
        self._orbt = get_orbt()
        self._local = threading.local()
        self._initialized = True

    def current(self) -> Optional[TrackingContext]:
        """Get current tracking context."""
        return getattr(self._local, 'context', None)

    @contextmanager
    def operation(
        self,
        name: str,
        layer: OrbtLayer = OrbtLayer.OPERATE,
        heir_format: HeirFormat = HeirFormat.STANDARD,
        metadata: Dict[str, Any] = None
    ):
        """
        Context manager for tracked operations.

        Args:
            name: Operation name
            layer: ORBT layer
            heir_format: HEIR ID format
            metadata: Optional metadata

        Yields:
            TrackingContext with unique_id and process_id
        """
        # Generate IDs
        heir_id = self._heir.generate(heir_format, metadata)
        process = self._orbt.start_process(layer, metadata)

        # Create context
        ctx = TrackingContext(
            unique_id=heir_id.unique_id,
            process_id=process.process_id,
            heir_id=heir_id,
            process=process,
            operation_name=name,
            metadata=metadata or {},
        )

        # Set as current
        previous = self.current()
        self._local.context = ctx

        try:
            yield ctx
            self._orbt.end_process(success=True)
        except Exception as e:
            self._orbt.end_process(success=False, error=str(e))
            raise
        finally:
            # Restore previous context
            self._local.context = previous

    def log(self, operation: str, success: bool = True, **kwargs) -> None:
        """Log an operation to the current process."""
        ctx = self.current()
        if ctx:
            self._orbt.log_operation(
                operation,
                success=success,
                unique_id=ctx.unique_id,
                **kwargs
            )

    @property
    def unique_id(self) -> Optional[str]:
        """Get current unique_id."""
        ctx = self.current()
        return ctx.unique_id if ctx else None

    @property
    def process_id(self) -> Optional[str]:
        """Get current process_id."""
        ctx = self.current()
        return ctx.process_id if ctx else None


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Global instance
_tracker = None


def get_tracker() -> Tracker:
    """Get or create global tracker."""
    global _tracker
    if _tracker is None:
        _tracker = Tracker()
    return _tracker


def get_tracking_context() -> Optional[TrackingContext]:
    """Get current tracking context."""
    return get_tracker().current()


def require_tracking_context(
    name: str = "anonymous",
    layer: OrbtLayer = OrbtLayer.OPERATE
) -> TrackingContext:
    """
    Get current context or create one.

    Use when you need both IDs but don't want to fail
    if tracking wasn't started upstream.
    """
    ctx = get_tracking_context()
    if ctx:
        return ctx

    # Create minimal context
    tracker = get_tracker()
    heir_id = tracker._heir.generate()
    process = tracker._orbt.start_process(layer)

    return TrackingContext(
        unique_id=heir_id.unique_id,
        process_id=process.process_id,
        heir_id=heir_id,
        process=process,
        operation_name=name,
    )


@contextmanager
def track_operation(
    name: str,
    layer: OrbtLayer = OrbtLayer.OPERATE,
    metadata: Dict[str, Any] = None
):
    """
    Simple context manager for tracked operations.

    Usage:
        with track_operation("process_data") as ctx:
            print(ctx.unique_id, ctx.process_id)
    """
    with get_tracker().operation(name, layer, metadata=metadata) as ctx:
        yield ctx


# =============================================================================
# DECORATOR
# =============================================================================

def tracked(
    name: str = None,
    layer: OrbtLayer = OrbtLayer.OPERATE
):
    """
    Decorator for tracked functions.

    Usage:
        @tracked("my_pipeline")
        def my_function():
            ctx = get_tracking_context()
            # unique_id and process_id available
            return result

        @tracked(layer=OrbtLayer.BUILD)
        def build_function():
            pass
    """
    def decorator(func: Callable):
        op_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with track_operation(op_name, layer):
                return func(*args, **kwargs)

        return wrapper

    return decorator


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Classes
    "Tracker",
    "TrackingContext",
    # Functions
    "get_tracker",
    "get_tracking_context",
    "require_tracking_context",
    "track_operation",
    # Decorator
    "tracked",
    # Re-exports from submodules
    "HeirIdentity",
    "HeirId",
    "HeirFormat",
    "OrbtProcess",
    "ProcessId",
    "OrbtLayer",
    "ProcessStatus",
]
