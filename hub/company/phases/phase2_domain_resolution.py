"""
Phase 2: Domain Resolution
==========================
Ensures each matched company has a valid domain:
- Pull domain from matched company record
- Validate domain (DNS/MX check)
- Flag for Tier 0 enrichment if still unresolved

Resolution hierarchy:
1. Use domain from company_master (website_url or domain field)
2. Use domain from input person record
3. Validate domain health (DNS/MX)
4. Queue for enrichment if no valid domain
"""

import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from enum import Enum
import pandas as pd

from ..utils.normalization import normalize_domain
from ..utils.verification import (
    verify_domain_dns,
    verify_domain_health,
    DomainHealthStatus,
    DomainVerificationResult
)
from ..utils.logging import (
    PipelineLogger,
    EventType,
    LogLevel,
    log_phase_start,
    log_phase_complete
)


class DomainSource(Enum):
    """Source of the domain resolution."""
    COMPANY_MASTER = "company_master"      # From matched company record
    INPUT_RECORD = "input_record"          # From input person record
    ENRICHMENT = "enrichment"              # From Tier 0 enrichment
    NONE = "none"                          # No domain found


class DomainStatus(Enum):
    """Status of domain resolution."""
    VALID = "valid"                        # Domain is valid and has MX
    VALID_NO_MX = "valid_no_mx"            # Domain resolves but no MX
    PARKED = "parked"                      # Domain is parked/for sale
    UNREACHABLE = "unreachable"            # Domain doesn't resolve
    MISSING = "missing"                    # No domain available
    NEEDS_ENRICHMENT = "needs_enrichment"  # Queued for Tier 0


@dataclass
class DomainResult:
    """Result of domain resolution for a single company."""
    company_id: str
    person_id: str
    domain: Optional[str] = None
    normalized_domain: Optional[str] = None
    source: DomainSource = DomainSource.NONE
    status: DomainStatus = DomainStatus.MISSING
    has_mx: bool = False
    mx_records: List[str] = field(default_factory=list)
    verification_details: Optional[DomainVerificationResult] = None
    needs_enrichment: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Phase2Stats:
    """Statistics for Phase 2 execution."""
    total_input: int = 0
    already_have_domain: int = 0
    domain_from_company: int = 0
    domain_from_input: int = 0
    valid_domains: int = 0
    invalid_domains: int = 0
    parked_domains: int = 0
    missing_domains: int = 0
    queued_for_enrichment: int = 0
    duration_seconds: float = 0.0


class Phase2DomainResolution:
    """
    Phase 2: Resolve domains for matched companies.

    Resolution hierarchy:
    1. Use domain from company_master (website_url or domain field)
    2. Use domain from input person record
    3. Validate domain health (DNS/MX)
    4. Queue for enrichment if no valid domain

    This phase does NOT perform web scraping or API calls.
    It only resolves from existing data and validates.
    Companies without domains are flagged for Phase 3 enrichment.
    """

    def __init__(self, config: Dict[str, Any] = None, logger: PipelineLogger = None):
        """
        Initialize Phase 2.

        Args:
            config: Configuration dictionary with:
                - validate_dns: Whether to perform DNS validation (default: True)
                - validate_mx: Whether to check MX records (default: True)
                - dns_timeout: DNS lookup timeout in seconds (default: 5.0)
                - skip_validation_if_known: Skip validation for known-good domains
            logger: Pipeline logger instance
        """
        self.config = config or {}
        self.logger = logger or PipelineLogger()

        # Configuration
        self.validate_dns = self.config.get('validate_dns', True)
        self.validate_mx = self.config.get('validate_mx', True)
        self.dns_timeout = self.config.get('dns_timeout', 5.0)
        self.skip_validation_if_known = self.config.get('skip_validation_if_known', False)

        # Cache for validated domains (to avoid repeated lookups)
        self._domain_cache: Dict[str, DomainVerificationResult] = {}

    def run(self, matched_df: pd.DataFrame,
            company_df: pd.DataFrame = None) -> Tuple[pd.DataFrame, Phase2Stats]:
        """
        Run domain resolution phase.

        Args:
            matched_df: DataFrame with matched companies from Phase 1
                Expected columns: person_id, matched_company_id, company_domain (optional)
            company_df: Optional company master DataFrame for domain lookup
                Expected columns: company_unique_id, website_url, domain

        Returns:
            Tuple of (result_df with domain info, Phase2Stats)
        """
        start_time = time.time()
        stats = Phase2Stats(total_input=len(matched_df))

        log_phase_start(self.logger, 2, "Domain Resolution", len(matched_df))

        # Build company domain lookup if company_df provided
        company_domains = {}
        if company_df is not None:
            company_domains = self._build_company_domain_index(company_df)

        # Process each matched person
        results = []
        for idx, row in matched_df.iterrows():
            result = self._resolve_domain(row, company_domains)
            results.append(result)

            # Update stats
            if result.status == DomainStatus.VALID:
                stats.valid_domains += 1
                if result.source == DomainSource.COMPANY_MASTER:
                    stats.domain_from_company += 1
                elif result.source == DomainSource.INPUT_RECORD:
                    stats.domain_from_input += 1
            elif result.status == DomainStatus.VALID_NO_MX:
                stats.valid_domains += 1  # Still count as valid
            elif result.status == DomainStatus.PARKED:
                stats.parked_domains += 1
            elif result.status == DomainStatus.UNREACHABLE:
                stats.invalid_domains += 1
            elif result.status == DomainStatus.MISSING:
                stats.missing_domains += 1

            if result.needs_enrichment:
                stats.queued_for_enrichment += 1

        # Build output DataFrame
        result_df = self._build_result_dataframe(matched_df, results)

        stats.duration_seconds = time.time() - start_time

        log_phase_complete(
            self.logger, 2, "Domain Resolution",
            output_count=len(result_df),
            duration_seconds=stats.duration_seconds,
            stats={
                'valid_domains': stats.valid_domains,
                'invalid_domains': stats.invalid_domains,
                'parked_domains': stats.parked_domains,
                'missing_domains': stats.missing_domains,
                'queued_for_enrichment': stats.queued_for_enrichment
            }
        )

        return result_df, stats

    def _build_company_domain_index(self, company_df: pd.DataFrame) -> Dict[str, str]:
        """
        Build lookup index of company_id -> domain.

        Args:
            company_df: Company master DataFrame

        Returns:
            Dict mapping company_id to normalized domain
        """
        index = {}

        for idx, row in company_df.iterrows():
            company_id = row.get('company_unique_id', '')
            if not company_id:
                continue

            # Try website_url first, then domain field
            domain = row.get('website_url', '') or row.get('domain', '')
            if domain:
                normalized = normalize_domain(domain)
                if normalized:
                    index[company_id] = normalized

        self.logger.debug(
            f"Built company domain index with {len(index)} entries",
            metadata={'index_size': len(index)}
        )

        return index

    def _resolve_domain(self, row: pd.Series,
                        company_domains: Dict[str, str]) -> DomainResult:
        """
        Resolve domain for a single matched person/company.

        Resolution order:
        1. Check company_master via lookup
        2. Check input record company_domain field
        3. Validate the found domain
        4. Flag for enrichment if no valid domain

        Args:
            row: DataFrame row with match results
            company_domains: Company ID -> domain lookup

        Returns:
            DomainResult
        """
        person_id = str(row.get('person_id', row.name))
        company_id = str(row.get('matched_company_id', '') or '')

        result = DomainResult(
            company_id=company_id,
            person_id=person_id
        )

        domain = None
        source = DomainSource.NONE

        # 1. Try company_master lookup
        if company_id and company_id in company_domains:
            domain = company_domains[company_id]
            source = DomainSource.COMPANY_MASTER
            self.logger.log_event(
                EventType.DOMAIN_RESOLVED,
                f"Domain from company_master: {domain}",
                entity_type="domain",
                entity_id=person_id,
                source="company_master",
                metadata={'domain': domain, 'company_id': company_id}
            )

        # 2. Try input record
        if not domain:
            input_domain = row.get('company_domain', '') or row.get('domain', '') or row.get('input_domain', '')
            if input_domain:
                domain = normalize_domain(str(input_domain))
                if domain:
                    source = DomainSource.INPUT_RECORD
                    self.logger.log_event(
                        EventType.DOMAIN_RESOLVED,
                        f"Domain from input record: {domain}",
                        entity_type="domain",
                        entity_id=person_id,
                        source="input_record",
                        metadata={'domain': domain}
                    )

        # 3. Validate domain if found
        if domain:
            result.domain = domain
            result.normalized_domain = domain
            result.source = source

            # Validate domain
            validation = self._validate_domain(domain)
            result.verification_details = validation

            if validation:
                result.has_mx = validation.has_mx
                result.mx_records = validation.mx_records

                if validation.status == DomainHealthStatus.HEALTHY:
                    result.status = DomainStatus.VALID
                elif validation.status == DomainHealthStatus.NO_MX:
                    result.status = DomainStatus.VALID_NO_MX
                elif validation.status == DomainHealthStatus.PARKED:
                    result.status = DomainStatus.PARKED
                    result.needs_enrichment = True
                else:
                    result.status = DomainStatus.UNREACHABLE
                    result.needs_enrichment = True
            else:
                # Validation failed or skipped
                result.status = DomainStatus.VALID  # Assume valid if not validated

        else:
            # No domain found
            result.status = DomainStatus.MISSING
            result.needs_enrichment = True
            self.logger.log_domain_failed(
                person_id, "No domain available from any source"
            )

        return result

    def _validate_domain(self, domain: str) -> Optional[DomainVerificationResult]:
        """
        Validate domain via DNS/MX lookup.

        Args:
            domain: Domain to validate

        Returns:
            DomainVerificationResult or None if validation skipped
        """
        if not self.validate_dns:
            return None

        # Check cache first
        if domain in self._domain_cache:
            return self._domain_cache[domain]

        # Perform validation
        try:
            verification = verify_domain_health(domain, timeout=self.dns_timeout)
            self._domain_cache[domain] = verification

            # Log result
            if verification.status == DomainHealthStatus.HEALTHY:
                self.logger.log_event(
                    EventType.DOMAIN_DNS_LOOKUP,
                    f"Domain healthy: {domain} (MX: {verification.has_mx})",
                    entity_type="domain",
                    metadata={'domain': domain, 'has_mx': verification.has_mx}
                )
            elif verification.status == DomainHealthStatus.PARKED:
                self.logger.log_event(
                    EventType.DOMAIN_PARKED,
                    f"Domain parked: {domain}",
                    LogLevel.WARNING,
                    entity_type="domain",
                    metadata={'domain': domain}
                )

            return verification

        except Exception as e:
            self.logger.error(
                f"Domain validation failed for {domain}",
                error=e,
                entity_type="domain",
                metadata={'domain': domain}
            )
            return None

    def _build_result_dataframe(self, matched_df: pd.DataFrame,
                                results: List[DomainResult]) -> pd.DataFrame:
        """Build output DataFrame with domain results appended."""
        # Create result columns
        result_data = []
        for result in results:
            result_data.append({
                'person_id': result.person_id,
                'resolved_domain': result.domain,
                'domain_source': result.source.value if result.source else None,
                'domain_status': result.status.value if result.status else None,
                'domain_has_mx': result.has_mx,
                'domain_needs_enrichment': result.needs_enrichment
            })

        result_df = pd.DataFrame(result_data)

        # Ensure person_id column exists in matched_df
        if 'person_id' not in matched_df.columns:
            matched_df = matched_df.reset_index()
            matched_df = matched_df.rename(columns={'index': 'person_id'})
            matched_df['person_id'] = matched_df['person_id'].astype(str)

        # Merge with original matched_df
        output_df = matched_df.merge(
            result_df,
            on='person_id',
            how='left'
        )

        return output_df

    def get_enrichment_queue(self, result_df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract records that need domain enrichment.

        Args:
            result_df: Output from run()

        Returns:
            DataFrame of records needing domain enrichment
        """
        if 'domain_needs_enrichment' not in result_df.columns:
            return pd.DataFrame()

        queue_df = result_df[result_df['domain_needs_enrichment'] == True].copy()

        # Add queue metadata
        queue_df['enrichment_type'] = 'domain'
        queue_df['enrichment_tier'] = 0  # Start with Tier 0
        queue_df['queued_at'] = datetime.now().isoformat()

        return queue_df

    def validate_domain_batch(self, domains: List[str]) -> Dict[str, DomainVerificationResult]:
        """
        Validate multiple domains.

        Args:
            domains: List of domains to validate

        Returns:
            Dict mapping domain to verification result
        """
        results = {}
        for domain in domains:
            if domain:
                normalized = normalize_domain(domain)
                if normalized:
                    results[normalized] = self._validate_domain(normalized)

        return results

    def get_domain_statistics(self, result_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get statistics about domain resolution results.

        Args:
            result_df: Output from run()

        Returns:
            Dict with domain statistics
        """
        stats = {
            'total': len(result_df),
            'by_status': {},
            'by_source': {},
            'has_mx': 0,
            'needs_enrichment': 0,
            'unique_domains': 0
        }

        if 'domain_status' in result_df.columns:
            stats['by_status'] = result_df['domain_status'].value_counts().to_dict()

        if 'domain_source' in result_df.columns:
            stats['by_source'] = result_df['domain_source'].value_counts().to_dict()

        if 'domain_has_mx' in result_df.columns:
            stats['has_mx'] = result_df['domain_has_mx'].sum()

        if 'domain_needs_enrichment' in result_df.columns:
            stats['needs_enrichment'] = result_df['domain_needs_enrichment'].sum()

        if 'resolved_domain' in result_df.columns:
            stats['unique_domains'] = result_df['resolved_domain'].nunique()

        return stats


def resolve_domains(matched_df: pd.DataFrame,
                    company_df: pd.DataFrame = None,
                    config: Dict[str, Any] = None) -> Tuple[pd.DataFrame, Phase2Stats]:
    """
    Convenience function to run domain resolution.

    Args:
        matched_df: DataFrame with matched companies from Phase 1
        company_df: Optional company master DataFrame
        config: Optional configuration

    Returns:
        Tuple of (result_df, Phase2Stats)
    """
    phase2 = Phase2DomainResolution(config=config)
    return phase2.run(matched_df, company_df)


def validate_single_domain(domain: str, timeout: float = 5.0) -> DomainVerificationResult:
    """
    Validate a single domain.

    Args:
        domain: Domain to validate
        timeout: DNS timeout

    Returns:
        DomainVerificationResult
    """
    normalized = normalize_domain(domain)
    if normalized:
        return verify_domain_health(normalized, timeout=timeout)
    return None
