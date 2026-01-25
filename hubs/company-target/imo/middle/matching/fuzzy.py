"""
Fuzzy Matching Utilities
========================
String similarity and fuzzy matching functions.
Implements Jaro-Winkler with doctrine-compliant thresholds and guardrails.
"""

from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum


class MatchTier(Enum):
    """Match confidence tiers per doctrine."""
    GOLD = "gold"       # Domain match (1.0)
    SILVER = "silver"   # Exact name match (0.95)
    BRONZE = "bronze"   # Fuzzy match (>= 0.85 with guardrails)
    NONE = "none"       # No match


@dataclass
class MatchCandidate:
    """A potential match candidate with scoring."""
    candidate_id: str
    candidate_name: str
    score: float
    tier: MatchTier
    match_method: str  # 'domain', 'exact', 'fuzzy'
    city_match: bool = False
    state_match: bool = False


@dataclass
class MatchResult:
    """Result of a matching operation."""
    matched: bool
    candidate: Optional[MatchCandidate]
    all_candidates: List[MatchCandidate]
    is_ambiguous: bool = False
    ambiguous_reason: Optional[str] = None


def jaro_similarity(s1: str, s2: str) -> float:
    """
    Calculate Jaro similarity between two strings.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Jaro similarity score 0.0-1.0
    """
    if not s1 or not s2:
        return 0.0

    if s1 == s2:
        return 1.0

    len1, len2 = len(s1), len(s2)

    # Calculate match window
    match_distance = max(len1, len2) // 2 - 1
    if match_distance < 0:
        match_distance = 0

    s1_matches = [False] * len1
    s2_matches = [False] * len2

    matches = 0
    transpositions = 0

    # Find matching characters
    for i in range(len1):
        start = max(0, i - match_distance)
        end = min(i + match_distance + 1, len2)

        for j in range(start, end):
            if s2_matches[j] or s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    # Count transpositions
    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    transpositions //= 2

    return (
        matches / len1 +
        matches / len2 +
        (matches - transpositions) / matches
    ) / 3.0


def jaro_winkler_similarity(s1: str, s2: str, prefix_weight: float = 0.1) -> float:
    """
    Calculate Jaro-Winkler similarity between two strings.

    Higher weight given to strings that match from the beginning.
    This is the primary fuzzy matching algorithm per doctrine.

    Args:
        s1: First string
        s2: Second string
        prefix_weight: Weight for common prefix (default 0.1, max 0.25)

    Returns:
        Similarity score 0.0-1.0
    """
    if not s1 or not s2:
        return 0.0

    if s1 == s2:
        return 1.0

    # Calculate base Jaro similarity
    jaro = jaro_similarity(s1, s2)

    # Find common prefix length (max 4 characters)
    prefix_len = 0
    max_prefix = min(4, min(len(s1), len(s2)))

    for i in range(max_prefix):
        if s1[i] == s2[i]:
            prefix_len += 1
        else:
            break

    # Ensure prefix_weight doesn't exceed 0.25
    prefix_weight = min(prefix_weight, 0.25)

    # Calculate Jaro-Winkler score
    return jaro + (prefix_len * prefix_weight * (1 - jaro))


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein (edit) distance between two strings.

    Number of single-character edits (insertions, deletions, substitutions)
    required to change one string into the other.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Edit distance (0 = identical)
    """
    if not s1:
        return len(s2) if s2 else 0
    if not s2:
        return len(s1)

    # Create distance matrix
    rows = len(s1) + 1
    cols = len(s2) + 1
    dist = [[0] * cols for _ in range(rows)]

    # Initialize first row and column
    for i in range(rows):
        dist[i][0] = i
    for j in range(cols):
        dist[0][j] = j

    # Fill in the rest of the matrix
    for i in range(1, rows):
        for j in range(1, cols):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            dist[i][j] = min(
                dist[i-1][j] + 1,      # deletion
                dist[i][j-1] + 1,      # insertion
                dist[i-1][j-1] + cost  # substitution
            )

    return dist[rows-1][cols-1]


def levenshtein_similarity(s1: str, s2: str) -> float:
    """
    Calculate Levenshtein similarity (normalized edit distance).

    Args:
        s1: First string
        s2: Second string

    Returns:
        Similarity score 0.0-1.0
    """
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))

    return 1.0 - (distance / max_len)


def fuzzy_match_score(s1: str, s2: str, method: str = "jaro_winkler") -> float:
    """
    Calculate fuzzy match score using specified method.

    Methods:
    - jaro_winkler: Best for short strings (names) - DEFAULT per doctrine
    - levenshtein: Best for longer strings
    - token_sort: Good for reordered words
    - token_set: Good for partial matches

    Args:
        s1: First string
        s2: Second string
        method: Matching method to use

    Returns:
        Similarity score 0.0-1.0
    """
    if not s1 or not s2:
        return 0.0

    if method == "jaro_winkler":
        return jaro_winkler_similarity(s1, s2)
    elif method == "levenshtein":
        return levenshtein_similarity(s1, s2)
    elif method == "token_sort":
        return token_sort_ratio(s1, s2)
    elif method == "token_set":
        return token_set_ratio(s1, s2)
    else:
        return jaro_winkler_similarity(s1, s2)


def find_best_match(query: str, candidates: List[str],
                    threshold: float = 0.85,
                    method: str = "jaro_winkler") -> Optional[Tuple[str, float]]:
    """
    Find best matching string from candidates.

    Args:
        query: String to match
        candidates: List of potential matches
        threshold: Minimum score to consider a match
        method: Matching method to use

    Returns:
        Tuple of (best_match, score) or None if no match above threshold
    """
    if not query or not candidates:
        return None

    best_match = None
    best_score = 0.0

    for candidate in candidates:
        score = fuzzy_match_score(query, candidate, method)
        if score > best_score:
            best_score = score
            best_match = candidate

    if best_score >= threshold:
        return (best_match, best_score)

    return None


def find_all_matches(query: str, candidates: List[str],
                     threshold: float = 0.85,
                     method: str = "jaro_winkler",
                     limit: int = 10) -> List[Tuple[str, float]]:
    """
    Find all matching strings above threshold.

    Args:
        query: String to match
        candidates: List of potential matches
        threshold: Minimum score to consider a match
        method: Matching method to use
        limit: Maximum matches to return

    Returns:
        List of (match, score) tuples, sorted by score descending
    """
    if not query or not candidates:
        return []

    matches = []

    for candidate in candidates:
        score = fuzzy_match_score(query, candidate, method)
        if score >= threshold:
            matches.append((candidate, score))

    # Sort by score descending
    matches.sort(key=lambda x: x[1], reverse=True)

    return matches[:limit]


def token_sort_ratio(s1: str, s2: str) -> float:
    """
    Calculate similarity after sorting tokens alphabetically.

    Good for matching strings with reordered words:
    "John Smith Inc" vs "Smith Inc John"

    Args:
        s1: First string
        s2: Second string

    Returns:
        Similarity score 0.0-1.0
    """
    if not s1 or not s2:
        return 0.0

    # Tokenize and sort
    tokens1 = sorted(s1.lower().split())
    tokens2 = sorted(s2.lower().split())

    # Join back and compare
    sorted1 = ' '.join(tokens1)
    sorted2 = ' '.join(tokens2)

    return jaro_winkler_similarity(sorted1, sorted2)


def token_set_ratio(s1: str, s2: str) -> float:
    """
    Calculate similarity based on common tokens.

    Good for partial matches:
    "John Smith Inc" vs "John Smith Corporation Inc"

    Args:
        s1: First string
        s2: Second string

    Returns:
        Similarity score 0.0-1.0
    """
    if not s1 or not s2:
        return 0.0

    # Tokenize
    tokens1 = set(s1.lower().split())
    tokens2 = set(s2.lower().split())

    # Find intersection and differences
    intersection = tokens1 & tokens2
    diff1 = tokens1 - tokens2
    diff2 = tokens2 - tokens1

    if not intersection:
        return 0.0

    # Create sorted strings for comparison
    sorted_intersection = ' '.join(sorted(intersection))
    combined1 = ' '.join(sorted(intersection | diff1))
    combined2 = ' '.join(sorted(intersection | diff2))

    # Return max of different comparisons
    scores = [
        jaro_winkler_similarity(sorted_intersection, combined1),
        jaro_winkler_similarity(sorted_intersection, combined2),
        jaro_winkler_similarity(combined1, combined2)
    ]

    return max(scores)


def check_ambiguous_collision(candidates: List[MatchCandidate],
                              threshold: float = 0.03) -> Tuple[bool, Optional[str]]:
    """
    Check if top candidates are within collision threshold.

    Per doctrine: If two candidates are within 0.03 Jaro-Winkler score,
    mark as ambiguous and send to review queue.

    Args:
        candidates: List of match candidates sorted by score
        threshold: Score difference threshold for collision (default 0.03)

    Returns:
        Tuple of (is_ambiguous, reason)
    """
    if len(candidates) < 2:
        return (False, None)

    # Check if top two are within threshold
    score_diff = abs(candidates[0].score - candidates[1].score)

    if score_diff <= threshold:
        return (True, f"Top candidates within {threshold} score threshold: "
                      f"{candidates[0].candidate_name} ({candidates[0].score:.3f}) vs "
                      f"{candidates[1].candidate_name} ({candidates[1].score:.3f})")

    return (False, None)


def apply_city_guardrail(query_name: str, query_city: str, query_state: str,
                         candidates: List[Dict[str, Any]],
                         name_threshold: float = 0.85,
                         high_threshold: float = 0.92) -> List[MatchCandidate]:
    """
    Apply doctrine-compliant fuzzy matching with city/state guardrail.

    Matching rules per doctrine:
    - If JW >= 0.92: Match regardless of location
    - If 0.85 <= JW < 0.92: Match only if same city
    - If JW < 0.85: No match

    Args:
        query_name: Company name to match (should be normalized)
        query_city: City for guardrail (should be normalized)
        query_state: State for guardrail (should be normalized)
        candidates: List of candidate records with name, city, state, id fields
        name_threshold: Minimum name similarity (default 0.85)
        high_threshold: High confidence threshold (default 0.92)

    Returns:
        List of MatchCandidate objects that pass guardrails
    """
    results = []

    for candidate in candidates:
        cand_name = candidate.get('name', candidate.get('company_name', ''))
        cand_city = candidate.get('city', candidate.get('address_city', ''))
        cand_state = candidate.get('state', candidate.get('address_state', ''))
        cand_id = candidate.get('id', candidate.get('company_unique_id', ''))

        # Calculate similarity
        score = jaro_winkler_similarity(query_name, cand_name)

        # Check city/state match
        city_match = (query_city and cand_city and
                      query_city.lower() == cand_city.lower())
        state_match = (query_state and cand_state and
                       query_state.upper() == cand_state.upper())

        # Apply guardrail rules per doctrine
        if score >= high_threshold:
            # High confidence - match regardless of location
            tier = MatchTier.BRONZE
            results.append(MatchCandidate(
                candidate_id=str(cand_id),
                candidate_name=cand_name,
                score=score,
                tier=tier,
                match_method='fuzzy_high',
                city_match=city_match,
                state_match=state_match
            ))
        elif score >= name_threshold and city_match:
            # Medium confidence - require city match
            tier = MatchTier.BRONZE
            results.append(MatchCandidate(
                candidate_id=str(cand_id),
                candidate_name=cand_name,
                score=score,
                tier=tier,
                match_method='fuzzy_city_guardrail',
                city_match=city_match,
                state_match=state_match
            ))
        # Else: Below threshold or missing city match - no match

    # Sort by score descending
    results.sort(key=lambda x: x.score, reverse=True)

    return results


def resolve_multi_candidate(candidates: List[MatchCandidate],
                            collision_threshold: float = 0.03) -> MatchResult:
    """
    Resolve matching when multiple candidates found.

    Per doctrine:
    - Single candidate: Return as match
    - Multiple candidates within collision_threshold: Mark ambiguous
    - Multiple candidates outside threshold: Return best

    Args:
        candidates: List of match candidates
        collision_threshold: Score difference for collision detection

    Returns:
        MatchResult with resolution
    """
    if not candidates:
        return MatchResult(
            matched=False,
            candidate=None,
            all_candidates=[],
            is_ambiguous=False
        )

    if len(candidates) == 1:
        return MatchResult(
            matched=True,
            candidate=candidates[0],
            all_candidates=candidates,
            is_ambiguous=False
        )

    # Check for ambiguous collision
    is_ambiguous, reason = check_ambiguous_collision(candidates, collision_threshold)

    if is_ambiguous:
        return MatchResult(
            matched=False,
            candidate=None,
            all_candidates=candidates,
            is_ambiguous=True,
            ambiguous_reason=reason
        )

    # Return best match
    return MatchResult(
        matched=True,
        candidate=candidates[0],
        all_candidates=candidates,
        is_ambiguous=False
    )


def rank_candidates_by_score(candidates: List[MatchCandidate],
                             prefer_location_match: bool = True) -> List[MatchCandidate]:
    """
    Rank candidates by score with optional location preference.

    Args:
        candidates: List of candidates to rank
        prefer_location_match: Whether to boost location matches

    Returns:
        Sorted list of candidates
    """
    def sort_key(c: MatchCandidate) -> Tuple[float, int, int]:
        location_boost = 0
        if prefer_location_match:
            if c.city_match:
                location_boost += 2
            if c.state_match:
                location_boost += 1
        return (c.score, location_boost, 0 if c.tier == MatchTier.GOLD else
                1 if c.tier == MatchTier.SILVER else 2)

    return sorted(candidates, key=sort_key, reverse=True)
