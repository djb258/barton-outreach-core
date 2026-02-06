# Enforcement Module - Barton Doctrine Compliance
# FAIL HARD on all violations

from .correlation_id import validate_correlation_id, CorrelationIDError
from .hub_gate import validate_company_anchor, HubGateError
from .signal_dedup import SignalDeduplicator, DuplicateSignalError
from .error_codes import (
    HubErrorCodes,
    PeopleErrorCodes,
    DOLErrorCodes,
    EnforcementErrorCodes,
    get_error_definition,
    format_error,
    is_critical,
    ErrorSeverity,
    ErrorDefinition,
)
from .error_enforcement import (
    DoctrineError,
    CLGateError,
    HubGateError as EnforcedHubGateError,
    wrap_error,
    doctrine_error_handler,
    record_error,
    require_company_id,
    require_hub_gate,
    error_metrics,
    ErrorMetrics,
)
from .schema_guard import (
    SchemaGuard,
    SchemaGuardError,
    ForbiddenSchemaAccessError,
    ReadOnlySchemaWriteError,
    RepoContext,
    validate_query,
    guarded_query,
    schema_guard_context,
    get_guard,
    SCHEMA_ACCESS_RULES,
)

__all__ = [
    # Correlation ID
    "validate_correlation_id",
    "CorrelationIDError",
    # Hub Gate
    "validate_company_anchor",
    "HubGateError",
    # Signal Deduplication
    "SignalDeduplicator",
    "DuplicateSignalError",
    # Error Codes
    "HubErrorCodes",
    "PeopleErrorCodes",
    "DOLErrorCodes",
    "EnforcementErrorCodes",
    "get_error_definition",
    "format_error",
    "is_critical",
    "ErrorSeverity",
    "ErrorDefinition",
    # Error Enforcement (Zero-Tolerance)
    "DoctrineError",
    "CLGateError",
    "EnforcedHubGateError",
    "wrap_error",
    "doctrine_error_handler",
    "record_error",
    "require_company_id",
    "require_hub_gate",
    "error_metrics",
    "ErrorMetrics",
    # Schema Guard (Cross-Repo Protection)
    "SchemaGuard",
    "SchemaGuardError",
    "ForbiddenSchemaAccessError",
    "ReadOnlySchemaWriteError",
    "RepoContext",
    "validate_query",
    "guarded_query",
    "schema_guard_context",
    "get_guard",
    "SCHEMA_ACCESS_RULES",
]
