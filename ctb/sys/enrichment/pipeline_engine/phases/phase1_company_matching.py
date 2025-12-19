"""
Phase 1: Company Matching
=========================
Matches input people to companies using doctrine-compliant matching hierarchy:
- GOLD: Domain match (score=1.0)
- SILVER: Exact name match (score=0.95)
- BRONZE: Fuzzy match with city guardrail (score>=0.85)

Per doctrine: collision threshold = 0.03
City guardrail: Required for scores 0.85-0.92, not required for >=0.92

Neon Integration:
- Can load company_master directly from Neon database
- Supports real-time lookups against production data
- Caches company data in-memory for batch processing
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import pandas as pd

from ..utils.normalization import (
    normalize_company_name,
    normalize_domain,
    normalize_city,
    normalize_state
)
from ..utils.fuzzy import (
    MatchTier,
    MatchCandidate,
    MatchResult as FuzzyMatchResult,
    jaro_winkler_similarity,
    apply_city_guardrail,
    resolve_multi_candidate,
    check_ambiguous_collision
)
from ..utils.logging import (
    PipelineLogger,
    EventType,
    log_phase_start,
    log_phase_complete
)
from ..utils.config import MatchingConfig


logger = logging.getLogger(__name__)


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
    # Neon integration stats
    neon_companies_loaded: int = 0
    neon_lookup_time_seconds: float = 0.0
    used_neon: bool = False


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

    Neon Integration:
    - Set use_neon=True to load companies directly from Neon database
    - Falls back to passed company_df if Neon connection fails
    - Caches loaded companies for batch processing
    """

    def __init__(
        self,
        config: Dict[str, Any] = None,
        logger: PipelineLogger = None,
        use_neon: bool = False
    ):
        """
        Initialize Phase 1.

        Args:
            config: Configuration dictionary with thresholds and settings
            logger: Pipeline logger instance
            use_neon: If True, load companies from Neon database
        """
        self.config = config or {}
        self.logger = logger or PipelineLogger()
        self.use_neon = use_neon

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

        # Neon integration
        self._neon_writer = None
        self._neon_companies_cache: Optional[pd.DataFrame] = None

    def run(
        self,
        people_df: pd.DataFrame,
        company_df: pd.DataFrame = None
    ) -> Tuple[pd.DataFrame, Phase1Stats]:
        """
        Run company matching phase.

        Args:
            people_df: Input people DataFrame with columns:
                - person_id, first_name, last_name, company_name, company_domain, city, state
            company_df: Company master DataFrame with columns:
                - company_unique_id, company_name, website_url, address_city, address_state
                (Optional if use_neon=True, will load from Neon)

        Returns:
            Tuple of (result_df with match results, Phase1Stats)
        """
        start_time = time.time()
        stats = Phase1Stats(total_input=len(people_df))

        log_phase_start(self.logger, 1, "Company Matching", len(people_df))

        # Load companies from Neon if enabled and no company_df provided
        if self.use_neon and (company_df is None or len(company_df) == 0):
            neon_start = time.time()
            company_df = self._load_companies_from_neon()
            stats.neon_lookup_time_seconds = time.time() - neon_start
            stats.neon_companies_loaded = len(company_df) if company_df is not None else 0
            stats.used_neon = True

            if company_df is None or len(company_df) == 0:
                logger.warning("No companies loaded from Neon, matching will fail")
                company_df = pd.DataFrame(columns=[
                    'company_unique_id', 'company_name', 'website_url',
                    'address_city', 'address_state'
                ])

        # Ensure we have a company_df
        if company_df is None:
            raise ValueError("company_df is required when use_neon=False")

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

    def _load_companies_from_neon(self) -> Optional[pd.DataFrame]:
        """
        Load company_master from Neon database.

        Returns:
            DataFrame with company data, or None if connection fails
        """
        # Return cached data if available
        if self._neon_companies_cache is not None:
            logger.debug("Using cached Neon companies data")
            return self._neon_companies_cache

        try:
            # Lazy import to avoid circular dependencies
            from hub.company.neon_writer import CompanyNeonWriter

            logger.info("Loading companies from Neon database...")
            self._neon_writer = CompanyNeonWriter()

            companies = self._neon_writer.load_all_companies()

            if not companies:
                logger.warning("No companies found in Neon database")
                return None

            # Convert to DataFrame
            df = pd.DataFrame(companies)

            # Map Neon column names to expected Phase 1 column names
            column_mapping = {
                'domain': 'website_url',
                'address_state': 'address_state',
                'address_city': 'address_city',
            }
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns and new_col not in df.columns:
                    df[new_col] = df[old_col]

            # Ensure required columns exist
            required_cols = ['company_unique_id', 'company_name', 'website_url',
                             'address_city', 'address_state']
            for col in required_cols:
                if col not in df.columns:
                    df[col] = None

            # Cache for subsequent calls
            self._neon_companies_cache = df

            logger.info(f"Loaded {len(df)} companies from Neon")
            return df

        except Exception as e:
            logger.error(f"Failed to load companies from Neon: {e}")
            return None

    def _get_neon_writer(self):
        """Get or create Neon writer instance."""
        if self._neon_writer is None:
            from hub.company.neon_writer import CompanyNeonWriter
            self._neon_writer = CompanyNeonWriter()
        return self._neon_writer

    def lookup_company_by_domain_neon(self, domain: str) -> Optional[Dict[str, Any]]:
        """
        Direct Neon lookup by domain (GOLD match - Tool 1).

        This bypasses the in-memory index and queries Neon directly.
        Useful for real-time lookups against the production database.

        Args:
            domain: Domain to lookup

        Returns:
            Company dict or None
        """
        if not self.use_neon:
            logger.warning("Neon not enabled, use _domain_match instead")
            return None

        try:
            writer = self._get_neon_writer()
            return writer.find_company_by_domain(domain)
        except Exception as e:
            logger.error(f"Neon domain lookup failed: {e}")
            return None

    def lookup_company_by_ein_neon(self, ein: str) -> Optional[Dict[str, Any]]:
        """
        Direct Neon lookup by EIN (Tool 18: Exact EIN Match).

        DOCTRINE: Exact match only. No fuzzy. Fail closed.

        Args:
            ein: EIN to lookup

        Returns:
            Company dict or None
        """
        if not self.use_neon:
            logger.warning("Neon not enabled")
            return None

        try:
            writer = self._get_neon_writer()
            return writer.find_company_by_ein(ein)
        except Exception as e:
            logger.error(f"Neon EIN lookup failed: {e}")
            return None

    def close(self):
        """Close Neon connection if open."""
        if self._neon_writer:
            self._neon_writer.close()
            self._neon_writer = None

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
            # Collision detected
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
                'collision_reason': resolution.ambiguous_reason
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


def match_single_company(
    company_name: str,
    domain: str,
    city: str,
    state: str,
    company_df: pd.DataFrame = None,
    config: Dict[str, Any] = None,
    use_neon: bool = False
) -> CompanyMatchResult:
    """
    Convenience function to match a single company.

    Args:
        company_name: Company name to match
        domain: Company domain (optional)
        city: Company city (optional)
        state: Company state (optional)
        company_df: Company master DataFrame (optional if use_neon=True)
        config: Optional configuration
        use_neon: If True, load companies from Neon database

    Returns:
        CompanyMatchResult
    """
    phase1 = Phase1CompanyMatching(config=config, use_neon=use_neon)

    # Load from Neon if enabled
    if use_neon:
        company_df = phase1._load_companies_from_neon()
        if company_df is None:
            company_df = pd.DataFrame(columns=[
                'company_unique_id', 'company_name', 'website_url',
                'address_city', 'address_state'
            ])

    if company_df is None:
        raise ValueError("company_df is required when use_neon=False")

    phase1._build_indices(company_df)

    person_row = pd.Series({
        'person_id': 'single_lookup',
        'company_name': company_name,
        'company_domain': domain,
        'city': city,
        'state': state
    })

    result = phase1._match_person(person_row, company_df)
    phase1.close()
    return result


def match_company_from_neon(
    company_name: str = None,
    domain: str = None,
    ein: str = None,
    city: str = None,
    state: str = None,
    config: Dict[str, Any] = None
) -> CompanyMatchResult:
    """
    Match a company against Neon database (production lookup).

    Priority order per doctrine:
    1. Domain match (GOLD - Tool 1)
    2. EIN match (Tool 18)
    3. Name match (SILVER/BRONZE)

    Args:
        company_name: Company name to match
        domain: Company domain (highest priority)
        ein: Company EIN (second priority)
        city: Company city (for fuzzy guardrail)
        state: Company state (for fuzzy guardrail)
        config: Optional configuration

    Returns:
        CompanyMatchResult
    """
    phase1 = Phase1CompanyMatching(config=config, use_neon=True)

    # Priority 1: Domain lookup (GOLD)
    if domain:
        company = phase1.lookup_company_by_domain_neon(domain)
        if company:
            phase1.close()
            return CompanyMatchResult(
                person_id='neon_lookup',
                input_company_name=company_name or '',
                input_domain=domain,
                matched_company_id=company['company_unique_id'],
                matched_company_name=company.get('company_name', ''),
                match_type=MatchType.DOMAIN,
                match_tier=MatchTier.GOLD,
                match_score=1.0,
                confidence=1.0,
                metadata={'match_method': 'neon_domain_lookup'}
            )

    # Priority 2: EIN lookup (Tool 18)
    if ein:
        company = phase1.lookup_company_by_ein_neon(ein)
        if company:
            phase1.close()
            return CompanyMatchResult(
                person_id='neon_lookup',
                input_company_name=company_name or '',
                input_domain=domain,
                matched_company_id=company['company_unique_id'],
                matched_company_name=company.get('company_name', ''),
                match_type=MatchType.EXACT,
                match_tier=MatchTier.SILVER,
                match_score=0.98,  # EIN is very high confidence
                confidence=0.98,
                metadata={'match_method': 'neon_ein_lookup'}
            )

    # Priority 3: Name-based matching
    if company_name:
        result = match_single_company(
            company_name=company_name,
            domain=domain or '',
            city=city or '',
            state=state or '',
            use_neon=True,
            config=config
        )
        return result

    phase1.close()
    return CompanyMatchResult(
        person_id='neon_lookup',
        input_company_name=company_name or '',
        input_domain=domain,
        match_type=MatchType.NONE,
        match_tier=MatchTier.NONE,
        metadata={'error': 'No search criteria provided'}
    )
