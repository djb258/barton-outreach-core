"""
Phase 1: Company Matching
=========================
Matches input people to companies using doctrine-compliant matching hierarchy:
- GOLD: Domain match (score=1.0)
- SILVER: Exact name match (score=0.95)
- BRONZE: Fuzzy match with city guardrail (score>=0.85)

Per doctrine: collision threshold = 0.03
City guardrail: Required for scores 0.85-0.92, not required for >=0.92

DOCTRINE ENFORCEMENT:
- correlation_id is MANDATORY (FAIL HARD if missing)
- All downstream calls must propagate correlation_id unchanged
"""

import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import pandas as pd

# Doctrine enforcement imports
from ops.enforcement.correlation_id import validate_correlation_id, CorrelationIDError

from ..matching import (
    normalize_company_name,
    normalize_domain,
    normalize_city,
    normalize_state,
    MatchTier,
    MatchCandidate,
    MatchResult as FuzzyMatchResult,
    jaro_winkler_similarity,
    apply_city_guardrail,
    resolve_multi_candidate,
    check_ambiguous_collision,
    AbacusFuzzyArbitrator,
    CollisionCandidate,
    ArbitrationResult,
    create_arbitrator,
)
from ..logging_config import (
    PipelineLogger,
    EventType,
    log_phase_start,
    log_phase_complete
)
from ..config import get_config


class MatchType(Enum):
    """Type of company match achieved."""
    DOMAIN = "domain"       # GOLD - matched by domain
    EXACT = "exact"         # SILVER - exact name match
    FUZZY = "fuzzy"         # BRONZE - fuzzy name match
    NONE = "none"           # No match found


@dataclass
class CompanyMatchResult:
    """Result of a company match attempt."""
    person_id: str
    input_company_name: str
    input_domain: Optional[str] = None
    matched_company_id: Optional[str] = None
    matched_company_name: Optional[str] = None
    match_type: MatchType = MatchType.NONE
    match_tier: MatchTier = MatchTier.NONE
    match_score: float = 0.0
    confidence: float = 0.0
    is_collision: bool = False
    collision_candidates: List[Dict] = field(default_factory=list)
    collision_reason: Optional[str] = None
    city_match: bool = False
    state_match: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Phase1Stats:
    """Statistics for Phase 1 execution."""
    total_input: int = 0
    domain_matches: int = 0
    exact_matches: int = 0
    fuzzy_matches: int = 0
    collisions: int = 0
    unmatched: int = 0
    duration_seconds: float = 0.0
    correlation_id: str = ""  # Propagated unchanged


class Phase1CompanyMatching:
    """
    Phase 1: Match input people to companies in company_master.

    Matching hierarchy per doctrine:
    1. Domain match (GOLD) - score = 1.0
    2. Exact name match (SILVER) - score = 0.95
    3. Fuzzy match with city guardrail (BRONZE):
       - Score >= 0.92: Match regardless of location
       - Score 0.85-0.92: Match only if same city
       - Score < 0.85: No match
    4. Collision handling if top candidates within 0.03 score
    """

    def __init__(self, config: Dict[str, Any] = None, logger: PipelineLogger = None):
        """
        Initialize Phase 1.

        Args:
            config: Configuration dictionary with thresholds and settings
            logger: Pipeline logger instance
        """
        self.config = config or {}
        self.logger = logger or PipelineLogger()

        # Load matching configuration
        matching_config = self.config.get('matching', {})
        self.domain_match_score = matching_config.get('domain_match_score', 1.0)
        self.exact_match_score = matching_config.get('exact_match_score', 0.95)
        self.fuzzy_high_threshold = matching_config.get('fuzzy_high_threshold', 0.92)
        self.fuzzy_low_threshold = matching_config.get('fuzzy_low_threshold', 0.85)
        self.collision_threshold = matching_config.get('collision_threshold', 0.03)

        # Build lookup indices (populated in run())
        self._domain_index: Dict[str, str] = {}  # domain -> company_id
        self._name_index: Dict[str, List[str]] = {}  # normalized_name -> [company_ids]

        # Tool 3: Abacus.ai Fuzzy Arbitrator for collision resolution
        # Per doctrine: LLM is ONLY allowed for collision resolution when
        # top 2 candidates are within 0.03 score threshold
        self._arbitrator = create_arbitrator()

    def run(self, people_df: pd.DataFrame,
            company_df: pd.DataFrame,
            correlation_id: str) -> Tuple[pd.DataFrame, Phase1Stats]:
        """
        Run company matching phase.

        DOCTRINE: correlation_id is MANDATORY. FAIL HARD if missing.

        Args:
            people_df: Input people DataFrame with columns:
                - person_id, first_name, last_name, company_name, company_domain, city, state
            company_df: Company master DataFrame with columns:
                - company_unique_id, company_name, website_url, address_city, address_state
            correlation_id: MANDATORY - End-to-end trace ID (UUID v4)

        Returns:
            Tuple of (result_df with match results, Phase1Stats)

        Raises:
            CorrelationIDError: If correlation_id is missing or invalid (FAIL HARD)
        """
        # DOCTRINE ENFORCEMENT: Validate correlation_id (FAIL HARD)
        process_id = "company.identity.matching.phase1"
        correlation_id = validate_correlation_id(correlation_id, process_id, "Phase 1")

        start_time = time.time()
        stats = Phase1Stats(total_input=len(people_df), correlation_id=correlation_id)

        log_phase_start(self.logger, 1, "Company Matching", len(people_df))

        # Build lookup indices
        self._build_indices(company_df)

        # Process each person
        results = []
        for idx, row in people_df.iterrows():
            result = self._match_person(row, company_df)
            results.append(result)

            # Update stats
            if result.match_type == MatchType.DOMAIN:
                stats.domain_matches += 1
            elif result.match_type == MatchType.EXACT:
                stats.exact_matches += 1
            elif result.match_type == MatchType.FUZZY:
                stats.fuzzy_matches += 1
            else:
                stats.unmatched += 1

            if result.is_collision:
                stats.collisions += 1

        # Build output DataFrame
        result_df = self._build_result_dataframe(people_df, results)

        stats.duration_seconds = time.time() - start_time

        log_phase_complete(
            self.logger, 1, "Company Matching",
            output_count=len(result_df),
            duration_seconds=stats.duration_seconds,
            stats={
                'domain_matches': stats.domain_matches,
                'exact_matches': stats.exact_matches,
                'fuzzy_matches': stats.fuzzy_matches,
                'collisions': stats.collisions,
                'unmatched': stats.unmatched
            }
        )

        return result_df, stats

    def _build_indices(self, company_df: pd.DataFrame) -> None:
        """Build lookup indices for fast matching."""
        self._domain_index = {}
        self._name_index = {}

        for idx, row in company_df.iterrows():
            company_id = row.get('company_unique_id', '')

            # Domain index
            domain = row.get('website_url', '') or row.get('domain', '')
            if domain:
                normalized_domain = normalize_domain(domain)
                if normalized_domain:
                    self._domain_index[normalized_domain] = company_id

            # Name index
            name = row.get('company_name', '')
            if name:
                normalized_name = normalize_company_name(name)
                if normalized_name:
                    if normalized_name not in self._name_index:
                        self._name_index[normalized_name] = []
                    self._name_index[normalized_name].append(company_id)

    def _match_person(self, person_row: pd.Series,
                      company_df: pd.DataFrame) -> CompanyMatchResult:
        """
        Match a single person to company master.

        Follows doctrine matching hierarchy:
        1. Domain match (GOLD)
        2. Exact name match (SILVER)
        3. Fuzzy match with guardrails (BRONZE)
        """
        person_id = str(person_row.get('person_id', person_row.name))
        input_company_name = str(person_row.get('company_name', '') or '')
        input_domain = str(person_row.get('company_domain', '') or person_row.get('domain', '') or '')
        input_city = str(person_row.get('city', '') or person_row.get('address_city', '') or '')
        input_state = str(person_row.get('state', '') or person_row.get('address_state', '') or '')

        result = CompanyMatchResult(
            person_id=person_id,
            input_company_name=input_company_name,
            input_domain=input_domain
        )

        # Normalize inputs
        normalized_name = normalize_company_name(input_company_name)
        normalized_domain = normalize_domain(input_domain) if input_domain else None
        normalized_city = normalize_city(input_city) if input_city else None
        normalized_state = normalize_state(input_state) if input_state else None

        # 1. Try domain match (GOLD)
        if normalized_domain:
            domain_result = self._domain_match(normalized_domain, company_df)
            if domain_result:
                result.matched_company_id = domain_result['company_id']
                result.matched_company_name = domain_result['company_name']
                result.match_type = MatchType.DOMAIN
                result.match_tier = MatchTier.GOLD
                result.match_score = self.domain_match_score
                result.confidence = self.domain_match_score
                result.metadata['match_method'] = 'domain'

                self.logger.log_match_domain(
                    person_id, result.matched_company_id, normalized_domain
                )
                return result

        # 2. Try exact name match (SILVER)
        if normalized_name:
            exact_result = self._exact_match(normalized_name, company_df)
            if exact_result:
                result.matched_company_id = exact_result['company_id']
                result.matched_company_name = exact_result['company_name']
                result.match_type = MatchType.EXACT
                result.match_tier = MatchTier.SILVER
                result.match_score = self.exact_match_score
                result.confidence = self.exact_match_score
                result.metadata['match_method'] = 'exact_name'

                self.logger.log_match_exact(
                    person_id, result.matched_company_id, result.matched_company_name
                )
                return result

        # 3. Try fuzzy match with city guardrail (BRONZE)
        if normalized_name:
            fuzzy_result = self._fuzzy_match(
                normalized_name, normalized_city, normalized_state, company_df
            )
            if fuzzy_result:
                if fuzzy_result['is_collision']:
                    # Collision detected - mark for review
                    result.is_collision = True
                    result.collision_candidates = fuzzy_result['candidates']
                    result.collision_reason = fuzzy_result['collision_reason']
                    result.metadata['match_method'] = 'fuzzy_collision'

                    self.logger.log_match_ambiguous(
                        person_id, fuzzy_result['candidates']
                    )
                else:
                    # Valid fuzzy match
                    result.matched_company_id = fuzzy_result['company_id']
                    result.matched_company_name = fuzzy_result['company_name']
                    result.match_type = MatchType.FUZZY
                    result.match_tier = MatchTier.BRONZE
                    result.match_score = fuzzy_result['score']
                    result.confidence = fuzzy_result['score']
                    result.city_match = fuzzy_result.get('city_match', False)
                    result.state_match = fuzzy_result.get('state_match', False)
                    result.metadata['match_method'] = fuzzy_result.get('method', 'fuzzy')

                    self.logger.log_match_fuzzy(
                        person_id, result.matched_company_id,
                        result.match_score, result.metadata['match_method']
                    )
                return result

        # No match found
        self.logger.log_match_none(person_id, "No match found above threshold")
        return result

    def _domain_match(self, domain: str,
                      company_df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Attempt domain-based match (GOLD tier).

        Args:
            domain: Normalized domain to match
            company_df: Company master DataFrame

        Returns:
            Match dict with company_id and company_name, or None
        """
        if not domain:
            return None

        # Use index for fast lookup
        if domain in self._domain_index:
            company_id = self._domain_index[domain]
            # Get company name from dataframe
            company_row = company_df[
                company_df['company_unique_id'] == company_id
            ]
            if len(company_row) > 0:
                return {
                    'company_id': company_id,
                    'company_name': company_row.iloc[0].get('company_name', ''),
                    'score': self.domain_match_score,
                    'method': 'domain'
                }

        return None

    def _exact_match(self, normalized_name: str,
                     company_df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Attempt exact name match (SILVER tier).

        Args:
            normalized_name: Normalized company name to match
            company_df: Company master DataFrame

        Returns:
            Match dict with company_id and company_name, or None
        """
        if not normalized_name:
            return None

        # Use index for fast lookup
        if normalized_name in self._name_index:
            company_ids = self._name_index[normalized_name]

            # If multiple companies with same normalized name, check for collision
            if len(company_ids) == 1:
                company_id = company_ids[0]
                company_row = company_df[
                    company_df['company_unique_id'] == company_id
                ]
                if len(company_row) > 0:
                    return {
                        'company_id': company_id,
                        'company_name': company_row.iloc[0].get('company_name', ''),
                        'score': self.exact_match_score,
                        'method': 'exact_name'
                    }

            # Multiple matches - this becomes a collision scenario
            # Fall through to fuzzy matching which handles collisions

        return None

    def _fuzzy_match(self, normalized_name: str, city: str, state: str,
                     company_df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Attempt fuzzy match with city/state guardrail (BRONZE tier).

        Per doctrine:
        - Score >= 0.92: Match regardless of location
        - Score 0.85-0.92: Match only if same city
        - Score < 0.85: No match
        - Collision if top candidates within 0.03 score

        Args:
            normalized_name: Normalized company name to match
            city: Normalized city for guardrail
            state: Normalized state for guardrail
            company_df: Company master DataFrame

        Returns:
            Match dict or collision dict, or None
        """
        if not normalized_name:
            return None

        # Build candidates list from company_df
        candidates = []
        for idx, row in company_df.iterrows():
            candidates.append({
                'id': row.get('company_unique_id', ''),
                'name': row.get('company_name', ''),
                'city': row.get('address_city', ''),
                'state': row.get('address_state', '')
            })

        # Apply city guardrail logic
        match_candidates = apply_city_guardrail(
            query_name=normalized_name,
            query_city=city or '',
            query_state=state or '',
            candidates=candidates,
            name_threshold=self.fuzzy_low_threshold,
            high_threshold=self.fuzzy_high_threshold
        )

        if not match_candidates:
            return None

        # Resolve multi-candidate (handles collision detection)
        resolution = resolve_multi_candidate(
            match_candidates,
            collision_threshold=self.collision_threshold
        )

        if resolution.is_ambiguous:
            # Collision detected - invoke Tool 3: Abacus.ai Fuzzy Arbitration
            # Per doctrine: LLM is ONLY allowed here for collision resolution
            collision_candidates = [
                CollisionCandidate(
                    company_id=c.candidate_id,
                    company_name=c.candidate_name,
                    score=c.score,
                    city=c.city if hasattr(c, 'city') else None,
                    state=c.state if hasattr(c, 'state') else None
                )
                for c in resolution.all_candidates[:5]
            ]

            # Attempt LLM arbitration
            arbitration_result = self._arbitrator.arbitrate(
                input_company_name=normalized_name,
                candidates=collision_candidates,
                input_city=city,
                input_state=state
            )

            if arbitration_result.result == ArbitrationResult.SELECTED:
                # LLM resolved the collision
                return {
                    'is_collision': False,
                    'company_id': arbitration_result.selected_company_id,
                    'company_name': arbitration_result.selected_company_name,
                    'score': arbitration_result.confidence,
                    'city_match': False,  # Unknown from arbitration
                    'state_match': False,
                    'method': 'llm_arbitration'
                }

            # LLM could not resolve or rejected - still a collision
            return {
                'is_collision': True,
                'candidates': [
                    {
                        'company_id': c.candidate_id,
                        'company_name': c.candidate_name,
                        'score': c.score,
                        'city_match': c.city_match,
                        'state_match': c.state_match
                    }
                    for c in resolution.all_candidates[:5]
                ],
                'collision_reason': arbitration_result.reasoning or resolution.ambiguous_reason,
                'arbitration_attempted': True,
                'arbitration_result': arbitration_result.result.value
            }

        if resolution.matched and resolution.candidate:
            # Valid match
            return {
                'is_collision': False,
                'company_id': resolution.candidate.candidate_id,
                'company_name': resolution.candidate.candidate_name,
                'score': resolution.candidate.score,
                'city_match': resolution.candidate.city_match,
                'state_match': resolution.candidate.state_match,
                'method': resolution.candidate.match_method
            }

        return None

    def _build_result_dataframe(self, people_df: pd.DataFrame,
                                results: List[CompanyMatchResult]) -> pd.DataFrame:
        """Build output DataFrame with match results appended."""
        # Create result columns
        result_data = []
        for result in results:
            result_data.append({
                'person_id': result.person_id,
                'matched_company_id': result.matched_company_id,
                'matched_company_name': result.matched_company_name,
                'match_type': result.match_type.value if result.match_type else None,
                'match_tier': result.match_tier.value if result.match_tier else None,
                'match_score': result.match_score,
                'confidence': result.confidence,
                'is_collision': result.is_collision,
                'collision_reason': result.collision_reason,
                'city_match': result.city_match,
                'state_match': result.state_match
            })

        result_df = pd.DataFrame(result_data)

        # Merge with original people_df
        # Ensure person_id column exists in people_df
        if 'person_id' not in people_df.columns:
            people_df = people_df.reset_index()
            people_df = people_df.rename(columns={'index': 'person_id'})
            people_df['person_id'] = people_df['person_id'].astype(str)

        output_df = people_df.merge(
            result_df,
            on='person_id',
            how='left'
        )

        return output_df


def match_single_company(company_name: str, domain: str,
                         city: str, state: str,
                         company_df: pd.DataFrame,
                         config: Dict[str, Any] = None) -> CompanyMatchResult:
    """
    Convenience function to match a single company.

    Args:
        company_name: Company name to match
        domain: Company domain (optional)
        city: Company city (optional)
        state: Company state (optional)
        company_df: Company master DataFrame
        config: Optional configuration

    Returns:
        CompanyMatchResult
    """
    phase1 = Phase1CompanyMatching(config=config)
    phase1._build_indices(company_df)

    person_row = pd.Series({
        'person_id': 'single_lookup',
        'company_name': company_name,
        'company_domain': domain,
        'city': city,
        'state': state
    })

    return phase1._match_person(person_row, company_df)
