"""
DOL Node Spoke - Department of Labor Data
==========================================
Processes DOL Form 5500, Schedule A, and violation data.

This spoke enriches company records with:
- Benefit plan information (Form 5500)
- Insurance broker data (Schedule A)
- Compliance signals

Sends signals to BIT Engine based on plan characteristics.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from ...wheel.bicycle_wheel import Spoke, Hub
from ...wheel.wheel_result import SpokeResult, ResultStatus, FailureType
from ...hub.bit_engine import BITEngine, SignalType


logger = logging.getLogger(__name__)


@dataclass
class Form5500Record:
    """A Form 5500 filing record"""
    filing_id: str
    ein: str
    plan_name: str
    plan_year_begin: Optional[datetime] = None
    plan_year_end: Optional[datetime] = None
    total_participants: int = 0
    total_assets: float = 0.0
    plan_effective_date: Optional[datetime] = None
    admin_name: Optional[str] = None
    admin_phone: Optional[str] = None
    is_small_plan: bool = False


@dataclass
class ScheduleARecord:
    """A Schedule A insurance record"""
    schedule_id: str
    filing_id: str
    broker_name: Optional[str] = None
    broker_fees: float = 0.0
    carrier_name: Optional[str] = None
    policy_type: Optional[str] = None


class DOLNodeSpoke(Spoke):
    """
    DOL Node - Spoke #2 of the Company Hub.

    Processes Department of Labor data to:
    1. Match Form 5500 filings to companies by EIN
    2. Extract insurance broker data from Schedule A
    3. Send signals to BIT Engine for intent scoring
    """

    def __init__(self, hub: Hub, bit_engine: Optional[BITEngine] = None):
        super().__init__(name="dol_node", hub=hub)
        self.bit_engine = bit_engine or BITEngine()

        # Track stats
        self.stats = {
            'total_processed': 0,
            'matched_by_ein': 0,
            'large_plans': 0,
            'schedule_a_records': 0,
            'signals_sent': 0
        }

    def process(self, data: Any) -> SpokeResult:
        """
        Process a DOL record and send signals to BIT Engine.

        Can process Form5500Record or ScheduleARecord.
        """
        self.stats['total_processed'] += 1

        if isinstance(data, Form5500Record):
            return self._process_form_5500(data)
        elif isinstance(data, ScheduleARecord):
            return self._process_schedule_a(data)
        else:
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.VALIDATION_ERROR,
                failure_reason=f"Unknown data type: {type(data).__name__}"
            )

    def _process_form_5500(self, record: Form5500Record) -> SpokeResult:
        """Process a Form 5500 filing"""
        if not record.ein:
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.NO_MATCH,
                failure_reason="No EIN in Form 5500 record"
            )

        # Look up company by EIN
        company_id = self._lookup_company_by_ein(record.ein)

        if not company_id:
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.NO_MATCH,
                failure_reason=f"No company found for EIN: {record.ein}"
            )

        self.stats['matched_by_ein'] += 1

        # Send base signal for any 5500 filing
        self._send_signal(
            SignalType.FORM_5500_FILED,
            company_id,
            metadata={'filing_id': record.filing_id, 'plan_name': record.plan_name}
        )

        # Additional signal for large plans
        if record.total_participants >= 500:
            self.stats['large_plans'] += 1
            self._send_signal(
                SignalType.LARGE_PLAN,
                company_id,
                metadata={
                    'participants': record.total_participants,
                    'assets': record.total_assets
                }
            )

        return SpokeResult(
            status=ResultStatus.SUCCESS,
            data=record,
            hub_signal={
                'signal_type': 'form_5500_processed',
                'impact': 5.0,
                'source': self.name,
                'company_id': company_id
            },
            metrics={
                'ein': record.ein,
                'participants': record.total_participants,
                'is_large_plan': record.total_participants >= 500
            }
        )

    def _process_schedule_a(self, record: ScheduleARecord) -> SpokeResult:
        """Process a Schedule A insurance record"""
        self.stats['schedule_a_records'] += 1

        # Schedule A links to Form 5500 by filing_id
        # Would need to look up the EIN from the parent filing

        return SpokeResult(
            status=ResultStatus.SUCCESS,
            data=record,
            metrics={
                'broker_name': record.broker_name,
                'broker_fees': record.broker_fees
            }
        )

    def _lookup_company_by_ein(self, ein: str) -> Optional[str]:
        """
        Look up company_id by EIN.

        In real implementation, this queries company_master.
        """
        # This would be a database query in production
        # For now, return None (would be implemented with actual DB connection)
        return None

    def _send_signal(
        self,
        signal_type: SignalType,
        company_id: str,
        metadata: Dict = None
    ):
        """Send a signal to the BIT Engine"""
        if self.bit_engine:
            self.bit_engine.create_signal(
                signal_type=signal_type,
                company_id=company_id,
                source_spoke=self.name,
                metadata=metadata or {}
            )
            self.stats['signals_sent'] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            'total_processed': self.stats['total_processed'],
            'matched_by_ein': self.stats['matched_by_ein'],
            'match_rate': f"{self.stats['matched_by_ein'] / max(self.stats['total_processed'], 1) * 100:.1f}%",
            'large_plans': self.stats['large_plans'],
            'schedule_a_records': self.stats['schedule_a_records'],
            'signals_sent': self.stats['signals_sent']
        }
