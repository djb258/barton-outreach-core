"""
Company Hub - Central Axle of the Barton System
================================================
The master node that all spokes connect to.

Architecture:
    ╔═════════════════════════════════════════════════╗
    ║              COMPANY HUB                        ║
    ║             (Central Axle)                      ║
    ║                                                 ║
    ║   ┌───────────────────────────────────────┐     ║
    ║   │           BIT ENGINE                  │     ║
    ║   │        (Core Metric)                  │     ║
    ║   └───────────────────────────────────────┘     ║
    ║                                                 ║
    ║   company_unique_id (PK)                        ║
    ║   company_name                                  ║
    ║   domain (REQUIRED)                             ║
    ║   email_pattern (REQUIRED)                      ║
    ║   slots[] (CEO, CFO, HR)                        ║
    ║                                                 ║
    ╚═════════════════════════════════════════════════╝

Barton ID Format: 04.04.01.XX.XXXXX.XXX
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from ctb.sys.enrichment.pipeline_engine.wheel.bicycle_wheel import Hub


logger = logging.getLogger(__name__)


@dataclass
class Slot:
    """Executive slot in the Company Hub"""
    slot_type: str  # CEO, CFO, HR
    person_id: Optional[str] = None
    is_filled: bool = False
    filled_at: Optional[datetime] = None
    last_refreshed_at: Optional[datetime] = None


@dataclass
class CompanyHubRecord:
    """
    A single company record in the hub.

    This is the central entity that all spokes anchor to.
    """
    company_unique_id: str  # Barton ID: 04.04.01.XX.XXXXX.XXX
    company_name: str

    # REQUIRED anchor fields for spokes
    domain: Optional[str] = None
    email_pattern: Optional[str] = None

    # Additional fields
    ein: Optional[str] = None
    industry: Optional[str] = None
    employee_count: Optional[int] = None
    address_state: Optional[str] = None

    # Slots sub-wheel
    slots: Dict[str, Slot] = field(default_factory=lambda: {
        'CEO': Slot(slot_type='CEO'),
        'CFO': Slot(slot_type='CFO'),
        'HR': Slot(slot_type='HR')
    })

    # Core metric (BIT Engine)
    bit_score: float = 0.0

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    data_quality_score: float = 0.0

    @property
    def is_spoke_ready(self) -> bool:
        """
        Check if company is ready for spoke processing.

        The Golden Rule: Must have company_id, domain, AND email_pattern.
        """
        return bool(
            self.company_unique_id and
            self.domain and
            self.email_pattern
        )

    @property
    def missing_anchors(self) -> List[str]:
        """List of missing anchor fields"""
        missing = []
        if not self.company_unique_id:
            missing.append('company_unique_id')
        if not self.domain:
            missing.append('domain')
        if not self.email_pattern:
            missing.append('email_pattern')
        return missing

    def fill_slot(self, slot_type: str, person_id: str) -> bool:
        """Fill a slot with a person"""
        if slot_type not in self.slots:
            return False
        self.slots[slot_type].person_id = person_id
        self.slots[slot_type].is_filled = True
        self.slots[slot_type].filled_at = datetime.now()
        return True

    def get_slot(self, slot_type: str) -> Optional[Slot]:
        """Get a slot by type"""
        return self.slots.get(slot_type)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'company_unique_id': self.company_unique_id,
            'company_name': self.company_name,
            'domain': self.domain,
            'email_pattern': self.email_pattern,
            'ein': self.ein,
            'industry': self.industry,
            'employee_count': self.employee_count,
            'address_state': self.address_state,
            'bit_score': self.bit_score,
            'data_quality_score': self.data_quality_score,
            'slots': {
                st: {
                    'person_id': slot.person_id,
                    'is_filled': slot.is_filled,
                    'filled_at': slot.filled_at.isoformat() if slot.filled_at else None
                }
                for st, slot in self.slots.items()
            },
            'is_spoke_ready': self.is_spoke_ready
        }


class CompanyHub:
    """
    The Company Hub - Central Axle of the Barton Bicycle Wheel.

    All spoke nodes connect to this hub:
    - People Node (Spoke #1)
    - DOL Node (Spoke #2)
    - Blog Node (Spoke #3)
    - Talent Flow (Spoke #4)
    - BIT Engine (Spoke #5)
    - Outreach (Spoke #6)
    """

    def __init__(self):
        self.name = "company_hub"
        self.entity_type = "company"
        self._companies: Dict[str, CompanyHubRecord] = {}
        self._hub = Hub(
            name="company_hub",
            entity_type="company",
            core_metric_name="aggregate_bit_score",
            core_metric_value=0.0,
            anchor_fields={
                'company_count': 0,
                'spoke_ready_count': 0,
                'total_slots': 0,
                'filled_slots': 0
            }
        )
        self.logger = logging.getLogger(__name__)

    def add_company(self, company: CompanyHubRecord) -> bool:
        """Add a company to the hub"""
        if company.company_unique_id in self._companies:
            self.logger.warning(f"Company {company.company_unique_id} already exists in hub")
            return False

        self._companies[company.company_unique_id] = company
        self._update_hub_metrics()
        return True

    def get_company(self, company_id: str) -> Optional[CompanyHubRecord]:
        """Get a company by ID"""
        return self._companies.get(company_id)

    def update_company(self, company: CompanyHubRecord) -> bool:
        """Update a company in the hub"""
        if company.company_unique_id not in self._companies:
            return False
        company.updated_at = datetime.now()
        self._companies[company.company_unique_id] = company
        self._update_hub_metrics()
        return True

    def get_spoke_ready_companies(self) -> List[CompanyHubRecord]:
        """Get all companies ready for spoke processing"""
        return [c for c in self._companies.values() if c.is_spoke_ready]

    def get_companies_missing_domain(self) -> List[CompanyHubRecord]:
        """Get companies missing domain anchor"""
        return [c for c in self._companies.values() if not c.domain]

    def get_companies_missing_pattern(self) -> List[CompanyHubRecord]:
        """Get companies missing email pattern anchor"""
        return [c for c in self._companies.values() if not c.email_pattern]

    def receive_signal(self, signal: Dict[str, Any]):
        """
        Receive a signal from a spoke.

        Signals update the hub's aggregate metrics.
        """
        self._hub.receive_signal(signal)

        # Update company-specific metrics if company_id provided
        if 'company_id' in signal:
            company = self.get_company(signal['company_id'])
            if company and 'impact' in signal:
                company.bit_score += signal['impact']
                self.logger.debug(
                    f"Company {signal['company_id']} BIT score updated: "
                    f"{company.bit_score}"
                )

    def _update_hub_metrics(self):
        """Update hub anchor fields with aggregate metrics"""
        total_companies = len(self._companies)
        spoke_ready = len(self.get_spoke_ready_companies())
        total_slots = total_companies * 3  # CEO, CFO, HR per company
        filled_slots = sum(
            1 for c in self._companies.values()
            for slot in c.slots.values()
            if slot.is_filled
        )

        self._hub.set_anchor('company_count', total_companies)
        self._hub.set_anchor('spoke_ready_count', spoke_ready)
        self._hub.set_anchor('total_slots', total_slots)
        self._hub.set_anchor('filled_slots', filled_slots)

    def summary(self) -> Dict[str, Any]:
        """Get hub summary statistics"""
        return {
            'hub_name': self.name,
            'company_count': len(self._companies),
            'spoke_ready_count': len(self.get_spoke_ready_companies()),
            'missing_domain': len(self.get_companies_missing_domain()),
            'missing_pattern': len(self.get_companies_missing_pattern()),
            'core_metric': {
                'name': self._hub.core_metric_name,
                'value': self._hub.core_metric_value
            },
            'slot_stats': {
                'total': self._hub.get_anchor('total_slots'),
                'filled': self._hub.get_anchor('filled_slots'),
                'fill_rate': (
                    self._hub.get_anchor('filled_slots') /
                    max(self._hub.get_anchor('total_slots'), 1) * 100
                )
            }
        }

    def validate_golden_rule(self, company_id: str) -> tuple[bool, List[str]]:
        """
        Validate the Golden Rule for a company.

        Returns (is_valid, list_of_missing_fields)
        """
        company = self.get_company(company_id)
        if not company:
            return False, ['company_not_found']
        return company.is_spoke_ready, company.missing_anchors

    # =========================================================================
    # NEON DATABASE INTEGRATION
    # =========================================================================

    def bootstrap_from_neon(self) -> int:
        """
        Load all companies from Neon database into the hub.

        This should be called on startup to hydrate the hub with existing data.

        Returns:
            Number of companies loaded
        """
        from .neon_writer import bootstrap_company_hub
        return bootstrap_company_hub(self)

    def persist_company_to_neon(
        self,
        company_id: str,
        correlation_id: str
    ) -> bool:
        """
        Persist a company to Neon database.

        Args:
            company_id: Company to persist
            correlation_id: Pipeline trace ID

        Returns:
            True if successful
        """
        from .neon_writer import CompanyNeonWriter

        company = self.get_company(company_id)
        if not company:
            self.logger.warning(f"Company {company_id} not found in hub")
            return False

        writer = CompanyNeonWriter()
        result = writer.write_company(company.to_dict(), correlation_id)
        writer.close()

        return result.success

    def persist_all_to_neon(self, correlation_id: str) -> Dict[str, int]:
        """
        Persist all companies to Neon database.

        Args:
            correlation_id: Pipeline trace ID

        Returns:
            Dict with write statistics
        """
        from .neon_writer import CompanyNeonWriter

        companies = [c.to_dict() for c in self._companies.values()]

        writer = CompanyNeonWriter()
        result = writer.write_companies_batch(companies, correlation_id)
        writer.close()

        return {
            'written': result.records_written,
            'failed': result.records_failed,
            'success': result.success
        }

    def emit_bit_signal(
        self,
        company_id: str,
        signal_type: str,
        signal_impact: float,
        source_spoke: str,
        correlation_id: str,
        persist: bool = True
    ) -> bool:
        """
        Emit a BIT signal for a company.

        Updates in-memory BIT score and optionally persists to Neon.

        Args:
            company_id: Company receiving the signal
            signal_type: Type of signal (e.g., 'SLOT_FILLED')
            signal_impact: Impact value (e.g., +10.0)
            source_spoke: Source spoke name
            correlation_id: Pipeline trace ID
            persist: Whether to persist to Neon

        Returns:
            True if successful
        """
        # Update in-memory
        company = self.get_company(company_id)
        if not company:
            self.logger.warning(f"Company {company_id} not found for signal")
            return False

        company.bit_score += signal_impact
        company.updated_at = datetime.now()

        self.logger.info(
            f"BIT signal: {signal_type} ({signal_impact:+.1f}) "
            f"for company {company_id}, new score: {company.bit_score:.1f}"
        )

        # Optionally persist to Neon
        if persist:
            from .neon_writer import CompanyNeonWriter
            writer = CompanyNeonWriter()

            # Log the signal
            writer.log_bit_signal(
                company_id=company_id,
                signal_type=signal_type,
                signal_impact=signal_impact,
                source_spoke=source_spoke,
                correlation_id=correlation_id
            )

            # Update the score
            writer.update_bit_score(
                company_id=company_id,
                bit_score=company.bit_score,
                correlation_id=correlation_id
            )
            writer.close()

        return True

    def find_company_by_domain(self, domain: str) -> Optional[CompanyHubRecord]:
        """
        Find company by domain (GOLD match - Tool 1).

        Checks in-memory first, then Neon if not found.
        """
        # Check in-memory
        for company in self._companies.values():
            if company.domain and company.domain.lower() == domain.lower():
                return company

        # Check Neon
        from .neon_writer import CompanyNeonWriter
        writer = CompanyNeonWriter()
        result = writer.find_company_by_domain(domain)
        writer.close()

        if result:
            # Add to in-memory cache
            record = CompanyHubRecord(
                company_unique_id=result['company_unique_id'],
                company_name=result['company_name'],
                domain=result.get('domain'),
                email_pattern=result.get('email_pattern'),
            )
            self._companies[record.company_unique_id] = record
            return record

        return None

    def find_company_by_ein(self, ein: str) -> Optional[CompanyHubRecord]:
        """
        Find company by EIN (Tool 18: Exact EIN Match).

        DOCTRINE: Exact match only. No fuzzy. Fail closed.
        """
        # Normalize EIN
        normalized = ''.join(c for c in ein if c.isdigit())

        # Check in-memory
        for company in self._companies.values():
            if company.ein and company.ein == normalized:
                return company

        # Check Neon
        from .neon_writer import CompanyNeonWriter
        writer = CompanyNeonWriter()
        result = writer.find_company_by_ein(normalized)
        writer.close()

        if result:
            record = CompanyHubRecord(
                company_unique_id=result['company_unique_id'],
                company_name=result['company_name'],
                domain=result.get('domain'),
                email_pattern=result.get('email_pattern'),
                ein=result.get('ein'),
            )
            self._companies[record.company_unique_id] = record
            return record

        return None

    def find_company_by_name(
        self,
        company_name: str,
        fuzzy_threshold: float = 0.85
    ) -> Optional[CompanyHubRecord]:
        """
        Find company by name (with fuzzy matching).

        Uses multiple matching strategies:
        1. Exact match (case-insensitive)
        2. Normalized match (remove LLC, Inc, etc.)
        3. Fuzzy match (rapidfuzz) if threshold met

        Args:
            company_name: Company name to search for
            fuzzy_threshold: Minimum similarity ratio (0.0 to 1.0)

        Returns:
            CompanyHubRecord if found, None otherwise
        """
        if not company_name:
            return None

        # Normalize input
        normalized_input = self._normalize_company_name(company_name)

        # Strategy 1: Exact match (case-insensitive)
        for company in self._companies.values():
            if company.company_name.lower() == company_name.lower():
                return company

        # Strategy 2: Normalized match
        for company in self._companies.values():
            normalized_company = self._normalize_company_name(company.company_name)
            if normalized_company == normalized_input:
                return company

        # Strategy 3: Fuzzy match
        try:
            from rapidfuzz import fuzz, process

            # Build list of (company_id, normalized_name)
            candidates = [
                (cid, self._normalize_company_name(c.company_name))
                for cid, c in self._companies.items()
            ]

            if candidates:
                names = [c[1] for c in candidates]
                result = process.extractOne(
                    normalized_input,
                    names,
                    scorer=fuzz.ratio
                )

                if result and result[1] >= fuzzy_threshold * 100:
                    # Find the matching company
                    matched_name = result[0]
                    for cid, normalized in candidates:
                        if normalized == matched_name:
                            return self._companies[cid]

        except ImportError:
            logger.warning("rapidfuzz not installed - fuzzy matching disabled")

        # Strategy 4: Check Neon
        from .neon_writer import CompanyNeonWriter
        writer = CompanyNeonWriter()
        results = writer.find_companies_by_name(company_name)
        writer.close()

        if results:
            # Return first exact match
            for result in results:
                if result['company_name'].lower() == company_name.lower():
                    record = CompanyHubRecord(
                        company_unique_id=result['company_unique_id'],
                        company_name=result['company_name'],
                        domain=result.get('domain'),
                        email_pattern=result.get('email_pattern'),
                    )
                    self._companies[record.company_unique_id] = record
                    return record

        return None

    def _normalize_company_name(self, name: str) -> str:
        """
        Normalize company name for matching.

        Removes common suffixes, punctuation, and converts to lowercase.
        """
        if not name:
            return ""

        normalized = name.lower().strip()

        # Remove common suffixes
        suffixes = [
            ', inc.', ' inc.', ' inc', ', inc',
            ', llc', ' llc', ', l.l.c.', ' l.l.c.',
            ', ltd.', ' ltd.', ' ltd', ', ltd',
            ', corp.', ' corp.', ' corp', ', corp',
            ', co.', ' co.', ' co', ', co',
            ', corporation', ' corporation',
            ', company', ' company',
            ', incorporated', ' incorporated',
            ', limited', ' limited',
        ]

        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
                break

        # Remove punctuation
        import re
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized

    def get_company_count(self) -> int:
        """Get total number of companies in hub."""
        return len(self._companies)

    def get_spoke_ready_count(self) -> int:
        """Get count of companies ready for spoke processing."""
        return len(self.get_spoke_ready_companies())
