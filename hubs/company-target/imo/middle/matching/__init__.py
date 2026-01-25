"""
Matching Module
===============
Fuzzy matching, normalization, and arbitration utilities.
"""

from .fuzzy import (
    MatchTier,
    MatchCandidate,
    MatchResult,
    jaro_similarity,
    jaro_winkler_similarity,
    levenshtein_distance,
    levenshtein_similarity,
    fuzzy_match_score,
    find_best_match,
    find_all_matches,
    token_sort_ratio,
    token_set_ratio,
    check_ambiguous_collision,
    apply_city_guardrail,
    resolve_multi_candidate,
    rank_candidates_by_score,
)

from .fuzzy_arbitration import (
    ArbitrationResult,
    CollisionCandidate,
    ArbitrationResponse,
    AbacusFuzzyArbitrator,
    create_arbitrator,
    arbitrate_collision,
)

from .normalization import (
    normalize_company_name,
    normalize_domain,
    normalize_email,
    normalize_city,
    normalize_state,
    extract_domain_from_email,
    extract_domain_from_url,
    is_personal_email,
    clean_company_name,
    remove_company_suffix,
)

__all__ = [
    # fuzzy
    "MatchTier",
    "MatchCandidate",
    "MatchResult",
    "jaro_similarity",
    "jaro_winkler_similarity",
    "levenshtein_distance",
    "levenshtein_similarity",
    "fuzzy_match_score",
    "find_best_match",
    "find_all_matches",
    "token_sort_ratio",
    "token_set_ratio",
    "check_ambiguous_collision",
    "apply_city_guardrail",
    "resolve_multi_candidate",
    "rank_candidates_by_score",
    # fuzzy_arbitration
    "ArbitrationResult",
    "CollisionCandidate",
    "ArbitrationResponse",
    "AbacusFuzzyArbitrator",
    "create_arbitrator",
    "arbitrate_collision",
    # normalization
    "normalize_company_name",
    "normalize_domain",
    "normalize_email",
    "normalize_city",
    "normalize_state",
    "extract_domain_from_email",
    "extract_domain_from_url",
    "is_personal_email",
    "clean_company_name",
    "remove_company_suffix",
]
