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

from ..wheel.bicycle_wheel import Hub


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
