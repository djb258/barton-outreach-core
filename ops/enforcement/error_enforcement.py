"""
Error Zero-Tolerance Enforcement
================================

DOCTRINE: Every error MUST have an explicit, PRD-compliant code.
No silent failures. No generic exceptions. No swallowed errors.

This module provides:
1. Error wrapping to ensure all exceptions have codes
2. Error logging with structured output
3. Error propagation that preserves context
4. Error metrics for observability
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Callable
from functools import wraps
from datetime import datetime
import traceback
import logging
import json
import uuid

from .error_codes import (
    ErrorDefinition,
    ErrorSeverity,
    get_error_definition,
    format_error,
    is_critical,
    ERROR_REGISTRY
)


logger = logging.getLogger(__name__)


# ============================================================================
# ERROR EXCEPTIONS
# ============================================================================

class DoctrineError(Exception):
    """
    Base exception for all doctrine-compliant errors.
    
    All errors in the system MUST inherit from this or be wrapped by it.
    """
    
    def __init__(
        self,
        code: str,
        message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        self.code = code
        self.error_def = get_error_definition(code)
        self.context = context or {}
        self.cause = cause
        self.timestamp = datetime.utcnow()
        self.trace_id = str(uuid.uuid4())
        
        # Build message
        if message:
            self.message = message
        elif self.error_def:
            self.message = self.error_def.message
        else:
            self.message = f"Unknown error: {code}"
        
        super().__init__(self.full_message)
    
    @property
    def full_message(self) -> str:
        """Get full formatted message with code and context."""
        return format_error(self.code, **self.context)
    
    @property
    def severity(self) -> ErrorSeverity:
        """Get error severity."""
        if self.error_def:
            return self.error_def.severity
        return ErrorSeverity.ERROR
    
    @property
    def is_critical(self) -> bool:
        """Check if error is critical (should halt processing)."""
        return self.severity == ErrorSeverity.CRITICAL
    
    @property
    def is_recoverable(self) -> bool:
        """Check if error is recoverable."""
        if self.error_def:
            return self.error_def.recoverable
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "trace_id": self.trace_id,
            "is_critical": self.is_critical,
            "is_recoverable": self.is_recoverable,
            "cause": str(self.cause) if self.cause else None,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class CLGateError(DoctrineError):
    """Error raised when CL gate validation fails."""
    
    def __init__(
        self,
        message: str = "company_unique_id is required",
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            code="ENF-CID-001",
            message=message,
            context=context
        )


class HubGateError(DoctrineError):
    """Error raised when hub gate validation fails."""
    
    def __init__(
        self,
        missing_field: str,
        context: Optional[Dict[str, Any]] = None
    ):
        code_map = {
            "company_id": "ENF-HUB-001",
            "domain": "ENF-HUB-002",
            "email_pattern": "ENF-HUB-003",
        }
        code = code_map.get(missing_field, "ENF-HUB-001")
        
        ctx = context or {}
        ctx["missing_field"] = missing_field
        
        super().__init__(code=code, context=ctx)


# ============================================================================
# ERROR WRAPPING
# ============================================================================

def wrap_error(
    error: Exception,
    default_code: str = "ENF-GEN-001",
    context: Optional[Dict[str, Any]] = None
) -> DoctrineError:
    """
    Wrap any exception in a DoctrineError.
    
    If the exception is already a DoctrineError, returns it unchanged.
    Otherwise, wraps it with a default code.
    
    Args:
        error: The exception to wrap
        default_code: Code to use if not already a DoctrineError
        context: Additional context to include
        
    Returns:
        DoctrineError instance
    """
    if isinstance(error, DoctrineError):
        # Merge context if provided
        if context:
            error.context.update(context)
        return error
    
    return DoctrineError(
        code=default_code,
        message=str(error),
        context=context,
        cause=error
    )


# ============================================================================
# ERROR DECORATOR
# ============================================================================

def doctrine_error_handler(
    default_code: str = "ENF-GEN-001",
    reraise_critical: bool = True,
    log_errors: bool = True
):
    """
    Decorator to enforce error handling doctrine.
    
    Wraps function to catch all exceptions and convert them to DoctrineErrors.
    
    Args:
        default_code: Default error code for unhandled exceptions
        reraise_critical: Whether to reraise critical errors
        log_errors: Whether to log errors
        
    Usage:
        @doctrine_error_handler(default_code="PSH-P0-001")
        def my_function():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except DoctrineError as e:
                if log_errors:
                    _log_error(e)
                if reraise_critical and e.is_critical:
                    raise
                return _error_result(e)
            except Exception as e:
                doctrine_error = wrap_error(
                    e,
                    default_code=default_code,
                    context={
                        "function": func.__name__,
                        "traceback": traceback.format_exc()
                    }
                )
                if log_errors:
                    _log_error(doctrine_error)
                if reraise_critical and doctrine_error.is_critical:
                    raise doctrine_error
                return _error_result(doctrine_error)
        return wrapper
    return decorator


def _log_error(error: DoctrineError) -> None:
    """Log a DoctrineError with appropriate level."""
    log_func = {
        ErrorSeverity.DEBUG: logger.debug,
        ErrorSeverity.INFO: logger.info,
        ErrorSeverity.WARNING: logger.warning,
        ErrorSeverity.ERROR: logger.error,
        ErrorSeverity.CRITICAL: logger.critical,
    }.get(error.severity, logger.error)
    
    log_func(
        f"{error.code}: {error.message}",
        extra={
            "error_code": error.code,
            "error_context": error.context,
            "trace_id": error.trace_id
        }
    )


def _error_result(error: DoctrineError) -> Dict[str, Any]:
    """Create a standard error result."""
    return {
        "success": False,
        "error": error.to_dict()
    }


# ============================================================================
# ERROR METRICS
# ============================================================================

@dataclass
class ErrorMetrics:
    """Tracks error metrics for observability."""
    
    counts: Dict[str, int] = field(default_factory=dict)
    last_errors: Dict[str, DoctrineError] = field(default_factory=dict)
    
    def record(self, error: DoctrineError) -> None:
        """Record an error occurrence."""
        self.counts[error.code] = self.counts.get(error.code, 0) + 1
        self.last_errors[error.code] = error
    
    def get_summary(self) -> Dict[str, Any]:
        """Get error metrics summary."""
        return {
            "total_errors": sum(self.counts.values()),
            "error_counts": self.counts,
            "unique_errors": len(self.counts),
            "critical_count": sum(
                count for code, count in self.counts.items()
                if is_critical(code)
            )
        }


# Global error metrics instance
error_metrics = ErrorMetrics()


def record_error(error: DoctrineError) -> None:
    """Record an error in global metrics."""
    error_metrics.record(error)


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def require_company_id(company_unique_id: Optional[str]) -> None:
    """
    Validate that company_unique_id is present.
    
    Raises CLGateError if missing.
    """
    if not company_unique_id:
        raise CLGateError(
            message="company_unique_id is NULL - STOP. DO NOT PROCEED.",
            context={"received": company_unique_id}
        )


def require_hub_gate(
    company_id: Optional[str] = None,
    domain: Optional[str] = None,
    email_pattern: Optional[str] = None
) -> None:
    """
    Validate hub gate fields.
    
    Raises HubGateError if any required field is missing.
    """
    if not company_id:
        raise HubGateError("company_id")
    if not domain:
        raise HubGateError("domain")
    # email_pattern may be optional depending on hub


__all__ = [
    # Exceptions
    'DoctrineError',
    'CLGateError',
    'HubGateError',
    
    # Functions
    'wrap_error',
    'doctrine_error_handler',
    'record_error',
    'require_company_id',
    'require_hub_gate',
    
    # Metrics
    'error_metrics',
    'ErrorMetrics',
]
