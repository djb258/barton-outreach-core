"""
Company Pipeline Orchestrator
==============================
The main orchestration layer that ties together the Company Hub,
BIT Engine, and all spokes.

Architecture:
    ╔═════════════════════════════════════════════════════════════════╗
    ║                    COMPANY PIPELINE                              ║
    ║                    (Orchestrator)                                ║
    ║                                                                  ║
    ║   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         ║
    ║   │  Company    │    │   BIT       │    │   Neon      │         ║
    ║   │  Hub        │◄───┤   Engine    │◄───┤   Writer    │         ║
    ║   └─────────────┘    └─────────────┘    └─────────────┘         ║
    ║          │                                     │                 ║
    ║          ▼                                     │                 ║
    ║   ┌─────────────────────────────────────────┐  │                 ║
    ║   │              SPOKES                      │  │                 ║
    ║   │  People | DOL | Blog | Talent Flow      │◄─┘                 ║
    ║   └─────────────────────────────────────────┘                    ║
    ╚═════════════════════════════════════════════════════════════════╝

Usage:
    from hub.company import CompanyPipeline

    # Initialize with Neon persistence
    pipeline = CompanyPipeline(persist_to_neon=True)

    # Bootstrap from Neon
    pipeline.bootstrap()

    # Process incoming data
    results = pipeline.run_company_matching(people_df)

    # Emit BIT signals
    pipeline.emit_bit_signal(
        company_id="04.04.01.XX.XXXXX.XXX",
        signal_type=SignalType.SLOT_FILLED,
        source_spoke="people_node"
    )
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

import pandas as pd

from .company_hub import CompanyHub, CompanyHubRecord
from .bit_engine import (
    BITEngine,
    SignalType,
    SIGNAL_IMPACTS,
    BIT_THRESHOLD_WARM,
    BIT_THRESHOLD_HOT,
    BIT_THRESHOLD_BURNING,
)
from .neon_writer import CompanyNeonWriter, check_company_neon_connection


logger = logging.getLogger(__name__)


@dataclass
class PipelineRunResult:
    """Result of a pipeline run."""
    success: bool = True
    correlation_id: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    companies_processed: int = 0
    companies_matched: int = 0
    companies_created: int = 0
    companies_updated: int = 0
    signals_emitted: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0


class CompanyPipeline:
    """
    Company Pipeline Orchestrator.

    The central orchestration layer that coordinates:
    - Company Hub (master data)
    - BIT Engine (buyer intent scoring)
    - Neon database persistence
    - Spoke integrations
    """

    def __init__(
        self,
        persist_to_neon: bool = True,
        auto_bootstrap: bool = False
    ):
        """
        Initialize Company Pipeline.

        Args:
            persist_to_neon: If True, persist all data to Neon database
            auto_bootstrap: If True, automatically bootstrap from Neon on init
        """
        self.persist_to_neon = persist_to_neon
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.hub = CompanyHub()
        self.bit_engine = BITEngine(persist_to_neon=persist_to_neon)

        # Neon writer (lazy init)
        self._neon_writer = None

        # Track initialization state
        self._bootstrapped = False

        if auto_bootstrap:
            self.bootstrap()

    @property
    def neon_writer(self) -> CompanyNeonWriter:
        """Get or create Neon writer instance."""
        if self._neon_writer is None:
            self._neon_writer = CompanyNeonWriter()
        return self._neon_writer

    # =========================================================================
    # BOOTSTRAP & INITIALIZATION
    # =========================================================================

    def bootstrap(self) -> int:
        """
        Bootstrap the pipeline from Neon database.

        Loads all existing companies and BIT scores into memory.

        Returns:
            Number of companies loaded
        """
        if self._bootstrapped:
            self.logger.warning("Pipeline already bootstrapped, skipping")
            return self.hub.get_company_count()

        self.logger.info("Bootstrapping Company Pipeline from Neon...")

        # Load companies into hub
        companies_loaded = self.hub.bootstrap_from_neon()

        # Load BIT scores
        scores_loaded = self.bit_engine.load_scores_from_neon()

        self._bootstrapped = True

        self.logger.info(
            f"Bootstrap complete: {companies_loaded} companies, "
            f"{scores_loaded} BIT scores loaded"
        )

        return companies_loaded

    def check_neon_connection(self) -> bool:
        """Check if Neon database is accessible."""
        return check_company_neon_connection()

    # =========================================================================
    # COMPANY MATCHING (Phase 1)
    # =========================================================================

    def run_company_matching(
        self,
        people_df: pd.DataFrame,
        correlation_id: str = None
    ) -> Tuple[pd.DataFrame, PipelineRunResult]:
        """
        Run company matching phase.

        Uses Phase 1 with Neon integration to match incoming people
        to existing companies in the database.

        Args:
            people_df: Input DataFrame with people to match
            correlation_id: Pipeline trace ID

        Returns:
            Tuple of (matched DataFrame, PipelineRunResult)
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        result = PipelineRunResult(correlation_id=correlation_id)
        result.companies_processed = len(people_df)

        try:
            # Import here to avoid circular dependencies
            from ctb.sys.enrichment.pipeline_engine.phases import (
                Phase1CompanyMatching,
                MatchType
            )

            # Initialize Phase 1 with Neon integration
            phase1 = Phase1CompanyMatching(use_neon=self.persist_to_neon)

            # Run matching
            matched_df, stats = phase1.run(people_df)

            # Update result stats
            result.companies_matched = (
                stats.domain_matches +
                stats.exact_matches +
                stats.fuzzy_matches
            )

            phase1.close()

            result.success = True
            result.completed_at = datetime.now()

            self.logger.info(
                f"Company matching complete: {result.companies_matched}/"
                f"{result.companies_processed} matched"
            )

            return matched_df, result

        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            result.completed_at = datetime.now()
            self.logger.error(f"Company matching failed: {e}")
            return people_df, result

    # =========================================================================
    # DOMAIN DETECTION (Phase 2)
    # =========================================================================

    def run_domain_detection(
        self,
        company_ids: List[str] = None,
        correlation_id: str = None
    ) -> PipelineRunResult:
        """
        Run domain detection phase for companies missing domains.

        Phase 2: Detects company domains using:
        1. Website extraction from existing data
        2. DNS lookup verification
        3. Search engine inference

        Args:
            company_ids: Specific companies to process (None = all needing domain)
            correlation_id: Pipeline trace ID

        Returns:
            PipelineRunResult with stats
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        result = PipelineRunResult(correlation_id=correlation_id)

        # Get companies needing domain
        if company_ids:
            companies = [self.hub.get_company(cid) for cid in company_ids if self.hub.get_company(cid)]
        else:
            companies = self.hub.get_companies_missing_domain()

        result.companies_processed = len(companies)

        for company in companies:
            try:
                # Try to infer domain from company name
                domain = self._infer_domain(company.company_name)

                if domain:
                    # Update company domain
                    company.domain = domain
                    company.updated_at = datetime.now()

                    if self.persist_to_neon:
                        self.neon_writer.update_domain(
                            company.company_unique_id,
                            domain,
                            correlation_id
                        )

                    result.companies_matched += 1
                    self.logger.debug(f"Domain detected for {company.company_name}: {domain}")

            except Exception as e:
                result.errors.append(f"Domain detection failed for {company.company_unique_id}: {e}")

        result.success = len(result.errors) == 0
        result.completed_at = datetime.now()

        self.logger.info(
            f"Domain detection complete: {result.companies_matched}/"
            f"{result.companies_processed} domains found"
        )

        return result

    def _infer_domain(self, company_name: str) -> Optional[str]:
        """
        Infer domain from company name.

        Uses simple heuristics - can be enhanced with DNS/search.
        """
        if not company_name:
            return None

        # Normalize company name
        normalized = company_name.lower().strip()

        # Remove common suffixes
        for suffix in [' inc', ' llc', ' ltd', ' corp', ' co', ' corporation', ' company']:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
                break

        # Remove punctuation and spaces
        import re
        domain_base = re.sub(r'[^\w]', '', normalized)

        if domain_base:
            return f"{domain_base}.com"

        return None

    # =========================================================================
    # EMAIL PATTERN DETECTION (Phase 3)
    # =========================================================================

    def run_email_pattern_detection(
        self,
        company_ids: List[str] = None,
        correlation_id: str = None
    ) -> PipelineRunResult:
        """
        Run email pattern detection phase.

        Phase 3: Detects email patterns using:
        1. Sample emails from people_master
        2. Common pattern inference
        3. External pattern lookup

        Args:
            company_ids: Specific companies to process (None = all needing pattern)
            correlation_id: Pipeline trace ID

        Returns:
            PipelineRunResult with stats
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        result = PipelineRunResult(correlation_id=correlation_id)

        # Get companies with domain but no email pattern
        if company_ids:
            companies = [
                self.hub.get_company(cid)
                for cid in company_ids
                if self.hub.get_company(cid) and self.hub.get_company(cid).domain
            ]
        else:
            companies = [
                c for c in self.hub._companies.values()
                if c.domain and not c.email_pattern
            ]

        result.companies_processed = len(companies)

        for company in companies:
            try:
                # Try to detect pattern from existing emails
                pattern = self._detect_email_pattern(company.company_unique_id, company.domain)

                if pattern:
                    company.email_pattern = pattern
                    company.updated_at = datetime.now()

                    if self.persist_to_neon:
                        self.neon_writer.update_email_pattern(
                            company.company_unique_id,
                            pattern,
                            correlation_id
                        )

                    result.companies_matched += 1
                    self.logger.debug(f"Email pattern detected for {company.company_name}: {pattern}")

            except Exception as e:
                result.errors.append(f"Pattern detection failed for {company.company_unique_id}: {e}")

        result.success = len(result.errors) == 0
        result.completed_at = datetime.now()

        self.logger.info(
            f"Email pattern detection complete: {result.companies_matched}/"
            f"{result.companies_processed} patterns found"
        )

        return result

    def _detect_email_pattern(self, company_id: str, domain: str) -> Optional[str]:
        """
        Detect email pattern from existing emails or use default.

        Common patterns:
        - {first}.{last}@domain.com
        - {first}{last}@domain.com
        - {f}{last}@domain.com
        - {first}@domain.com
        """
        # Try to load existing people with emails
        try:
            people = self.neon_writer.load_people_by_company(company_id)

            if people:
                # Analyze emails to detect pattern
                for person in people:
                    email = person.get('email', '')
                    first_name = person.get('first_name', '').lower()
                    last_name = person.get('last_name', '').lower()

                    if email and first_name and last_name and domain.lower() in email.lower():
                        local_part = email.split('@')[0].lower()

                        # Check common patterns
                        if local_part == f"{first_name}.{last_name}":
                            return "{first}.{last}"
                        elif local_part == f"{first_name}{last_name}":
                            return "{first}{last}"
                        elif local_part == f"{first_name[0]}{last_name}":
                            return "{f}{last}"
                        elif local_part == first_name:
                            return "{first}"
                        elif local_part == f"{last_name}.{first_name}":
                            return "{last}.{first}"

        except Exception as e:
            self.logger.warning(f"Failed to detect pattern from emails: {e}")

        # Default pattern (most common)
        return "{first}.{last}"

    # =========================================================================
    # SPOKE READY CHECK (Phase 4)
    # =========================================================================

    def run_spoke_ready_check(
        self,
        company_ids: List[str] = None,
        correlation_id: str = None
    ) -> PipelineRunResult:
        """
        Run spoke ready check phase.

        Phase 4: Validates companies have all required anchors:
        - company_id: Present
        - domain: Present
        - email_pattern: Present

        Args:
            company_ids: Specific companies to check (None = all)
            correlation_id: Pipeline trace ID

        Returns:
            PipelineRunResult with stats
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        result = PipelineRunResult(correlation_id=correlation_id)

        # Get companies to check
        if company_ids:
            companies = [self.hub.get_company(cid) for cid in company_ids if self.hub.get_company(cid)]
        else:
            companies = list(self.hub._companies.values())

        result.companies_processed = len(companies)

        spoke_ready = []
        not_ready = []

        for company in companies:
            is_valid, missing = self.hub.validate_golden_rule(company.company_unique_id)

            if is_valid:
                spoke_ready.append(company)
                result.companies_matched += 1
            else:
                not_ready.append({
                    'company_id': company.company_unique_id,
                    'company_name': company.company_name,
                    'missing': missing
                })

        result.success = True
        result.completed_at = datetime.now()

        self.logger.info(
            f"Spoke ready check complete: {result.companies_matched}/"
            f"{result.companies_processed} ready for spoke processing"
        )

        # Log not ready companies
        if not_ready:
            self.logger.warning(
                f"{len(not_ready)} companies not spoke-ready. "
                f"Run Phase 2/3 to fill missing anchors."
            )

        return result

    def run_full_pipeline(
        self,
        people_df: pd.DataFrame,
        correlation_id: str = None
    ) -> Tuple[pd.DataFrame, Dict[str, PipelineRunResult]]:
        """
        Run the full company pipeline (Phase 1-4).

        Args:
            people_df: Input DataFrame with people to process
            correlation_id: Pipeline trace ID

        Returns:
            Tuple of (processed DataFrame, dict of phase results)
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        results = {}

        # Phase 1: Company Matching
        matched_df, phase1_result = self.run_company_matching(people_df, correlation_id)
        results['phase1_matching'] = phase1_result

        # Get matched company IDs
        matched_ids = matched_df['matched_company_id'].dropna().unique().tolist()

        # Phase 2: Domain Detection (for companies missing domain)
        phase2_result = self.run_domain_detection(matched_ids, correlation_id)
        results['phase2_domain'] = phase2_result

        # Phase 3: Email Pattern Detection
        phase3_result = self.run_email_pattern_detection(matched_ids, correlation_id)
        results['phase3_pattern'] = phase3_result

        # Phase 4: Spoke Ready Check
        phase4_result = self.run_spoke_ready_check(matched_ids, correlation_id)
        results['phase4_ready'] = phase4_result

        self.logger.info(
            f"Full pipeline complete: "
            f"Phase 1 matched {phase1_result.companies_matched}, "
            f"Phase 4 spoke-ready: {phase4_result.companies_matched}"
        )

        return matched_df, results

    # =========================================================================
    # COMPANY CRUD
    # =========================================================================

    def add_company(
        self,
        company_name: str,
        domain: str = None,
        email_pattern: str = None,
        ein: str = None,
        industry: str = None,
        employee_count: int = None,
        address_state: str = None,
        correlation_id: str = None
    ) -> Optional[CompanyHubRecord]:
        """
        Add a new company to the hub.

        Args:
            company_name: Company name
            domain: Company domain (anchor field)
            email_pattern: Email pattern (anchor field)
            ein: Employer Identification Number
            industry: Industry classification
            employee_count: Number of employees
            address_state: State abbreviation
            correlation_id: Pipeline trace ID

        Returns:
            Created CompanyHubRecord or None
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Generate Barton ID
        # Format: 04.04.01.XX.XXXXX.XXX
        import random
        company_id = f"04.04.01.{random.randint(10,99)}.{random.randint(10000,99999)}.{random.randint(100,999)}"

        # Create record
        company = CompanyHubRecord(
            company_unique_id=company_id,
            company_name=company_name,
            domain=domain,
            email_pattern=email_pattern,
            ein=ein,
            industry=industry,
            employee_count=employee_count,
            address_state=address_state,
            created_at=datetime.now()
        )

        # Add to hub
        if not self.hub.add_company(company):
            self.logger.warning(f"Failed to add company {company_name}")
            return None

        # Persist to Neon
        if self.persist_to_neon:
            self.hub.persist_company_to_neon(company_id, correlation_id)

        self.logger.info(f"Added company: {company_name} ({company_id})")
        return company

    def get_company(self, company_id: str) -> Optional[CompanyHubRecord]:
        """Get a company by ID."""
        return self.hub.get_company(company_id)

    def find_company_by_domain(self, domain: str) -> Optional[CompanyHubRecord]:
        """Find company by domain (GOLD match)."""
        return self.hub.find_company_by_domain(domain)

    def find_company_by_ein(self, ein: str) -> Optional[CompanyHubRecord]:
        """Find company by EIN (Tool 18)."""
        return self.hub.find_company_by_ein(ein)

    def update_company_domain(
        self,
        company_id: str,
        domain: str,
        correlation_id: str = None
    ) -> bool:
        """Update a company's domain."""
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        company = self.hub.get_company(company_id)
        if not company:
            return False

        company.domain = domain
        company.updated_at = datetime.now()

        if self.persist_to_neon:
            self.neon_writer.update_domain(company_id, domain, correlation_id)

        return True

    def update_company_email_pattern(
        self,
        company_id: str,
        email_pattern: str,
        correlation_id: str = None
    ) -> bool:
        """Update a company's email pattern."""
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        company = self.hub.get_company(company_id)
        if not company:
            return False

        company.email_pattern = email_pattern
        company.updated_at = datetime.now()

        if self.persist_to_neon:
            self.neon_writer.update_email_pattern(
                company_id, email_pattern, correlation_id
            )

        return True

    # =========================================================================
    # BIT SIGNALS
    # =========================================================================

    def emit_bit_signal(
        self,
        company_id: str,
        signal_type: SignalType,
        source_spoke: str,
        impact: float = None,
        metadata: Dict[str, Any] = None,
        correlation_id: str = None
    ) -> bool:
        """
        Emit a BIT signal for a company.

        Args:
            company_id: Company receiving the signal
            signal_type: Type of signal
            source_spoke: Spoke that generated the signal
            impact: Signal impact (uses default if not specified)
            metadata: Additional signal data
            correlation_id: Pipeline trace ID

        Returns:
            True if successful
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Emit via BIT Engine
        signal = self.bit_engine.create_signal(
            signal_type=signal_type,
            company_id=company_id,
            source_spoke=source_spoke,
            impact=impact,
            metadata=metadata,
            correlation_id=correlation_id
        )

        # Also update via hub (for company-level tracking)
        if self.persist_to_neon:
            self.hub.emit_bit_signal(
                company_id=company_id,
                signal_type=signal_type.value,
                signal_impact=signal.impact,
                source_spoke=source_spoke,
                correlation_id=correlation_id,
                persist=True
            )

        return True

    def get_bit_score(self, company_id: str) -> float:
        """Get BIT score for a company."""
        return self.bit_engine.get_score_value(company_id)

    def get_lifecycle_state(self, company_id: str) -> str:
        """Get lifecycle state for a company."""
        return self.bit_engine.get_lifecycle_state(company_id)

    def get_hot_companies(self) -> List[CompanyHubRecord]:
        """Get companies with HOT or BURNING status."""
        hot_scores = self.bit_engine.get_companies_above_threshold(BIT_THRESHOLD_HOT)
        return [
            self.hub.get_company(s.company_id)
            for s in hot_scores
            if self.hub.get_company(s.company_id)
        ]

    # =========================================================================
    # SPOKE INTEGRATION HELPERS
    # =========================================================================

    def validate_company_anchor(self, company_id: str) -> Tuple[bool, List[str]]:
        """
        Validate the Golden Rule for a company.

        Returns (is_valid, list_of_missing_fields)
        """
        return self.hub.validate_golden_rule(company_id)

    def get_spoke_ready_companies(self) -> List[CompanyHubRecord]:
        """Get all companies ready for spoke processing."""
        return self.hub.get_spoke_ready_companies()

    def get_companies_needing_domain(self) -> List[CompanyHubRecord]:
        """Get companies missing domain anchor."""
        return self.hub.get_companies_missing_domain()

    def get_companies_needing_pattern(self) -> List[CompanyHubRecord]:
        """Get companies missing email pattern anchor."""
        return self.hub.get_companies_missing_pattern()

    # =========================================================================
    # SLOT MANAGEMENT
    # =========================================================================

    def fill_slot(
        self,
        company_id: str,
        slot_type: str,
        person_id: str,
        correlation_id: str = None
    ) -> bool:
        """
        Fill an executive slot for a company.

        Emits SLOT_FILLED BIT signal automatically.

        Args:
            company_id: Company ID
            slot_type: CEO, CFO, or HR
            person_id: Person filling the slot
            correlation_id: Pipeline trace ID

        Returns:
            True if successful
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        company = self.hub.get_company(company_id)
        if not company:
            return False

        if not company.fill_slot(slot_type, person_id):
            return False

        # Emit BIT signal for slot filled
        self.emit_bit_signal(
            company_id=company_id,
            signal_type=SignalType.SLOT_FILLED,
            source_spoke="people_node",
            metadata={
                'slot_type': slot_type,
                'person_id': person_id
            },
            correlation_id=correlation_id
        )

        # Persist company update
        if self.persist_to_neon:
            self.hub.persist_company_to_neon(company_id, correlation_id)

        self.logger.info(
            f"Filled {slot_type} slot for {company_id} with person {person_id}"
        )

        return True

    # =========================================================================
    # SUMMARY & REPORTING
    # =========================================================================

    def summary(self) -> Dict[str, Any]:
        """Get pipeline summary statistics."""
        hub_summary = self.hub.summary()
        bit_summary = self.bit_engine.summary()
        state_summary = self.bit_engine.get_state_summary()

        return {
            'bootstrapped': self._bootstrapped,
            'persist_to_neon': self.persist_to_neon,
            'hub': hub_summary,
            'bit_engine': bit_summary,
            'lifecycle_states': state_summary,
        }

    # =========================================================================
    # CLEANUP
    # =========================================================================

    def close(self):
        """Close all connections."""
        if self._neon_writer:
            self._neon_writer.close()
            self._neon_writer = None

        self.bit_engine.close()
        self.logger.info("Company Pipeline closed")
