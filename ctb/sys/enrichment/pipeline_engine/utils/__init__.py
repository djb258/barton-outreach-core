"""
Pipeline Engine Utilities
=========================
Shared utility modules for the enrichment pipeline.
"""

from .normalization import (
    normalize_company_name,
    normalize_name,
    normalize_domain,
    normalize_email,
    clean_text
)

from .fuzzy import (
    jaro_winkler_similarity,
    levenshtein_distance,
    fuzzy_match_score,
    find_best_match
)

from .providers import (
    ProviderBase,
    FirecrawlProvider,
    WebScraperProvider,
    GooglePlacesProvider,
    HunterProvider,
    ClearbitProvider,
    ApolloProvider,
    ProspeoProvider,
    SnovProvider,
    ClayProvider
)

from .patterns import (
    COMMON_PATTERNS,
    extract_pattern_from_email,
    apply_pattern,
    validate_pattern_format
)

from .verification import (
    verify_email_format,
    verify_domain_dns,
    smtp_check,
    bulk_verify
)

from .logging import (
    PipelineLogger,
    log_phase_start,
    log_phase_complete,
    log_error
)

from .config import (
    PipelineConfig,
    load_config,
    get_provider_config,
    get_database_config
)

__all__ = [
    # Normalization
    "normalize_company_name",
    "normalize_name",
    "normalize_domain",
    "normalize_email",
    "clean_text",
    # Fuzzy matching
    "jaro_winkler_similarity",
    "levenshtein_distance",
    "fuzzy_match_score",
    "find_best_match",
    # Providers
    "ProviderBase",
    "FirecrawlProvider",
    "WebScraperProvider",
    "GooglePlacesProvider",
    "HunterProvider",
    "ClearbitProvider",
    "ApolloProvider",
    "ProspeoProvider",
    "SnovProvider",
    "ClayProvider",
    # Patterns
    "COMMON_PATTERNS",
    "extract_pattern_from_email",
    "apply_pattern",
    "validate_pattern_format",
    # Verification
    "verify_email_format",
    "verify_domain_dns",
    "smtp_check",
    "bulk_verify",
    # Logging
    "PipelineLogger",
    "log_phase_start",
    "log_phase_complete",
    "log_error",
    # Config
    "PipelineConfig",
    "load_config",
    "get_provider_config",
    "get_database_config",
]
