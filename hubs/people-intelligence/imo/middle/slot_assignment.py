"""
Slot Assignment Spoke - Seniority Competition
=============================================
Assigns people to executive slots based on seniority ranking.

Slot Types:
    - CEO (Chief Executive Officer)
    - CFO (Chief Financial Officer)
    - HR (HR Director/CHRO)

Seniority Ranking (HR slots):
    1. CHRO / Chief Human Resources Officer / Chief People Officer
    2. VP / Vice President / SVP
    3. Director
    4. Manager
    5. HRBP / HR Business Partner
    6. Generalist
    7. Specialist / Coordinator / Administrator
    8. Other

Competition Rules:
    - Lower rank number wins
    - Existing slot holder can be displaced by higher seniority
    - Displaced person goes to FAILED_SLOT_ASSIGNMENT failure spoke
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import logging

# TODO: ctb/ was archived — bicycle_wheel module does not exist. Need to implement in src/sys/wheel/ or remove.
# from ctb.sys.enrichment.pipeline_engine.wheel.bicycle_wheel import Spoke, Hub
# from ctb.sys.enrichment.pipeline_engine.wheel.wheel_result import SpokeResult, ResultStatus, FailureType


logger = logging.getLogger(__name__)


# Seniority rankings (lower number = higher seniority)
SENIORITY_RANK = {
    # C-Level
    'CHRO': 1,
    'Chief Human Resources Officer': 1,
    'Chief People Officer': 1,
    'CPO': 1,

    # VP Level
    'VP': 2,
    'Vice President': 2,
    'SVP': 2,
    'Senior Vice President': 2,
    'VP HR': 2,
    'VP Human Resources': 2,

    # Director Level
    'Director': 3,
    'HR Director': 3,
    'Director of HR': 3,
    'Director Human Resources': 3,
    'Senior Director': 3,

    # Manager Level
    'Manager': 4,
    'HR Manager': 4,
    'Human Resources Manager': 4,
    'Senior Manager': 4,

    # HRBP Level
    'HRBP': 5,
    'HR Business Partner': 5,
    'Senior HRBP': 5,

    # Generalist Level
    'Generalist': 6,
    'HR Generalist': 6,
    'Senior Generalist': 6,

    # Specialist/Coordinator Level
    'Specialist': 7,
    'HR Specialist': 7,
    'Coordinator': 7,
    'HR Coordinator': 7,
    'Administrator': 7,
    'HR Administrator': 7,

    # Other
    'Other': 8
}


@dataclass
class SlotCandidate:
    """A candidate for a slot"""
    person_id: str
    full_name: str
    job_title: str
    seniority: str
    seniority_rank: int
    company_id: str


@dataclass
class SlotState:
    """Current state of a slot"""
    slot_type: str
    company_id: str
    current_holder: Optional[SlotCandidate] = None
    is_filled: bool = False
    last_updated: Optional[datetime] = None
    competition_history: List[Dict] = None

    def __post_init__(self):
        if self.competition_history is None:
            self.competition_history = []


class SlotAssignmentSpoke(Spoke):
    """
    Slot Assignment - Seniority competition for executive slots.

    Processes incoming people and assigns them to slots if they
    have higher seniority than the current holder.
    """

    def __init__(self, hub: Hub):
        super().__init__(name="slot_assignment", hub=hub)
        # company_id -> slot_type -> SlotState
        self._slots: Dict[str, Dict[str, SlotState]] = {}

        # Track stats
        self.stats = {
            'total_candidates': 0,
            'slots_won': 0,
            'slots_defended': 0,
            'displacements': 0
        }

    def process(self, data: Any) -> SpokeResult:
        """
        Process a person for slot assignment.

        The person competes with the current slot holder (if any).
        Higher seniority (lower rank number) wins.
        """
        if not hasattr(data, 'matched_company_id') or not data.matched_company_id:
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.VALIDATION_ERROR,
                failure_reason="No matched_company_id - must pass Hub Gate first"
            )

        self.stats['total_candidates'] += 1

        # Create candidate
        candidate = SlotCandidate(
            person_id=data.person_id,
            full_name=data.full_name,
            job_title=data.job_title,
            seniority=data.seniority,
            seniority_rank=data.seniority_rank,
            company_id=data.matched_company_id
        )

        # Determine slot type (default to HR for this spoke)
        slot_type = self._determine_slot_type(data.job_title)

        # Try to win the slot
        result = self.compete_for_slot(candidate, slot_type)

        if result['won']:
            self.stats['slots_won'] += 1
            data.slot_assigned = slot_type

            if result['displaced']:
                self.stats['displacements'] += 1

            return SpokeResult(
                status=ResultStatus.SUCCESS,
                data=data,
                hub_signal={
                    'signal_type': 'slot_filled',
                    'impact': 10.0,
                    'source': self.name,
                    'company_id': data.matched_company_id,
                    'slot_type': slot_type,
                    'person_id': data.person_id
                },
                metrics={
                    'slot_type': slot_type,
                    'seniority_rank': candidate.seniority_rank,
                    'displaced': result['displaced']
                }
            )
        else:
            self.stats['slots_defended'] += 1
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.LOST_SLOT,
                failure_reason=(
                    f"Lost slot competition for {slot_type}. "
                    f"Rank {candidate.seniority_rank} vs current holder rank {result['defender_rank']}"
                ),
                data=data,
                metrics={
                    'slot_type': slot_type,
                    'candidate_rank': candidate.seniority_rank,
                    'defender_rank': result['defender_rank']
                }
            )

    def compete_for_slot(
        self,
        candidate: SlotCandidate,
        slot_type: str
    ) -> Dict[str, Any]:
        """
        Compete for a slot.

        Returns:
            {
                'won': bool,
                'displaced': bool (if won and someone was already there),
                'defender_rank': int (rank of current holder if lost)
            }
        """
        company_id = candidate.company_id

        # Initialize company slots if needed
        if company_id not in self._slots:
            self._slots[company_id] = {
                'CEO': SlotState(slot_type='CEO', company_id=company_id),
                'CFO': SlotState(slot_type='CFO', company_id=company_id),
                'HR': SlotState(slot_type='HR', company_id=company_id)
            }

        slot = self._slots[company_id].get(slot_type)
        if not slot:
            # Invalid slot type
            return {'won': False, 'displaced': False, 'defender_rank': 0}

        # Empty slot - automatic win
        if not slot.is_filled:
            slot.current_holder = candidate
            slot.is_filled = True
            slot.last_updated = datetime.now()
            slot.competition_history.append({
                'event': 'won_empty',
                'winner': candidate.person_id,
                'timestamp': datetime.now().isoformat()
            })
            return {'won': True, 'displaced': False, 'defender_rank': None}

        # Compete with current holder
        current_holder = slot.current_holder

        if candidate.seniority_rank < current_holder.seniority_rank:
            # Candidate wins - displace current holder
            displaced_holder = current_holder
            slot.current_holder = candidate
            slot.last_updated = datetime.now()
            slot.competition_history.append({
                'event': 'displaced',
                'winner': candidate.person_id,
                'loser': displaced_holder.person_id,
                'winner_rank': candidate.seniority_rank,
                'loser_rank': displaced_holder.seniority_rank,
                'timestamp': datetime.now().isoformat()
            })

            logger.info(
                f"Slot {slot_type} at {company_id}: "
                f"{candidate.full_name} (rank {candidate.seniority_rank}) "
                f"displaced {displaced_holder.full_name} (rank {displaced_holder.seniority_rank})"
            )

            return {'won': True, 'displaced': True, 'defender_rank': displaced_holder.seniority_rank}
        else:
            # Current holder defends
            slot.competition_history.append({
                'event': 'defended',
                'defender': current_holder.person_id,
                'challenger': candidate.person_id,
                'defender_rank': current_holder.seniority_rank,
                'challenger_rank': candidate.seniority_rank,
                'timestamp': datetime.now().isoformat()
            })
            return {'won': False, 'displaced': False, 'defender_rank': current_holder.seniority_rank}

    def _determine_slot_type(self, job_title: str) -> str:
        """Determine slot type from job title"""
        title_lower = job_title.lower() if job_title else ''

        # Check for CEO/CFO keywords
        if any(kw in title_lower for kw in ['ceo', 'chief executive', 'president']):
            return 'CEO'
        if any(kw in title_lower for kw in ['cfo', 'chief financial', 'finance director']):
            return 'CFO'

        # Default to HR for benefits/HR roles
        return 'HR'

    def get_slot_state(self, company_id: str, slot_type: str) -> Optional[SlotState]:
        """Get current state of a specific slot"""
        if company_id in self._slots:
            return self._slots[company_id].get(slot_type)
        return None

    def get_company_slots(self, company_id: str) -> Dict[str, SlotState]:
        """Get all slots for a company"""
        return self._slots.get(company_id, {})

    def get_stats(self) -> Dict[str, Any]:
        """Get slot assignment statistics"""
        total_slots = sum(
            1 for company_slots in self._slots.values()
            for slot in company_slots.values()
            if slot.is_filled
        )
        return {
            'total_candidates': self.stats['total_candidates'],
            'slots_won': self.stats['slots_won'],
            'slots_defended': self.stats['slots_defended'],
            'displacements': self.stats['displacements'],
            'total_filled_slots': total_slots,
            'companies_with_slots': len(self._slots)
        }


def get_seniority_rank(title: str) -> int:
    """
    Get seniority rank for a job title.

    Lower number = higher seniority.
    """
    if not title:
        return SENIORITY_RANK['Other']

    title_lower = title.lower()

    # Check exact matches first
    for key, rank in SENIORITY_RANK.items():
        if key.lower() == title_lower:
            return rank

    # Check partial matches
    for key, rank in SENIORITY_RANK.items():
        if key.lower() in title_lower:
            return rank

    return SENIORITY_RANK['Other']
