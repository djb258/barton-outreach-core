"""
People Node Spoke - Orchestrator for People Processing
======================================================
Manages the complete people pipeline through the wheel.

This is the main spoke class that orchestrates:
1. Hub Gate (company matching)
2. Slot Assignment (seniority competition)
3. Email Verification Sub-Wheel
4. Export to Neon

Wraps existing phase implementations with wheel architecture.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from ...wheel.bicycle_wheel import Spoke, Hub, SubWheel, BicycleWheel
from ...wheel.wheel_result import SpokeResult, FailureResult, ResultStatus, FailureType
from ...hub.bit_engine import BITEngine, SignalType


logger = logging.getLogger(__name__)


@dataclass
class PersonRecord:
    """A person record being processed through the People Node"""
    person_id: str
    full_name: str
    first_name: str
    last_name: str
    job_title: str
    seniority: str
    seniority_rank: int
    company_name_raw: str
    linkedin_url: Optional[str] = None

    # Populated during processing
    matched_company_id: Optional[str] = None
    matched_company_name: Optional[str] = None
    matched_domain: Optional[str] = None
    fuzzy_score: float = 0.0
    slot_assigned: Optional[str] = None
    email_pattern: Optional[str] = None
    generated_email: Optional[str] = None
    email_verified: bool = False
    email_result: Optional[str] = None
    failure_reason: Optional[str] = None

    @property
    def is_complete(self) -> bool:
        """Check if person has all required fields for export"""
        return bool(
            self.matched_company_id and
            self.slot_assigned and
            self.generated_email and
            self.email_verified
        )


class PeopleNodeSpoke(Spoke):
    """
    People Node - Spoke #1 of the Company Hub.

    Processes people through:
    1. Hub Gate - Company matching (fuzzy)
    2. Slot Assignment - Seniority competition
    3. Email Generation - Pattern application
    4. Email Verification - MillionVerifier sub-wheel
    """

    def __init__(self, hub: Hub, bit_engine: Optional[BITEngine] = None):
        super().__init__(name="people_node", hub=hub)
        self.bit_engine = bit_engine or BITEngine()

        # Track processing stats
        self.stats = {
            'total_processed': 0,
            'matched': 0,
            'slots_won': 0,
            'emails_verified': 0,
            'failures': {
                'no_match': 0,
                'low_confidence': 0,
                'lost_slot': 0,
                'no_pattern': 0,
                'email_invalid': 0
            }
        }

    def process(self, data: Any) -> SpokeResult:
        """
        Process a person record through the People Node.

        This method coordinates all sub-spokes and routes failures.
        """
        if not isinstance(data, PersonRecord):
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.VALIDATION_ERROR,
                failure_reason="Expected PersonRecord, got " + type(data).__name__
            )

        person = data
        self.stats['total_processed'] += 1

        # STEP 1: Hub Gate - Company Matching
        # Implemented in existing phases, wrapped here
        if not person.matched_company_id:
            self.stats['failures']['no_match'] += 1
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.NO_MATCH,
                failure_reason=f"No company match for: {person.company_name_raw}",
                data=person
            )

        if person.fuzzy_score < 80:
            if person.fuzzy_score >= 70:
                self.stats['failures']['low_confidence'] += 1
                return SpokeResult(
                    status=ResultStatus.FAILED,
                    failure_type=FailureType.LOW_CONFIDENCE,
                    failure_reason=f"Low confidence match ({person.fuzzy_score}%)",
                    data=person
                )
            else:
                self.stats['failures']['no_match'] += 1
                return SpokeResult(
                    status=ResultStatus.FAILED,
                    failure_type=FailureType.NO_MATCH,
                    failure_reason=f"Fuzzy score too low ({person.fuzzy_score}%)",
                    data=person
                )

        self.stats['matched'] += 1

        # STEP 2: Slot Assignment - Seniority Competition
        if not person.slot_assigned:
            self.stats['failures']['lost_slot'] += 1
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.LOST_SLOT,
                failure_reason=f"Lost slot competition (rank: {person.seniority_rank})",
                data=person
            )

        self.stats['slots_won'] += 1

        # Send signal to BIT Engine
        if self.bit_engine:
            self.bit_engine.create_signal(
                signal_type=SignalType.SLOT_FILLED,
                company_id=person.matched_company_id,
                source_spoke=self.name,
                metadata={'slot_type': person.slot_assigned, 'person_id': person.person_id}
            )

        # STEP 3: Email Generation
        if not person.email_pattern or not person.matched_domain:
            self.stats['failures']['no_pattern'] += 1
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.NO_PATTERN,
                failure_reason=f"No email pattern for domain: {person.matched_domain}",
                data=person
            )

        # STEP 4: Email Verification (sub-wheel)
        if not person.email_verified:
            self.stats['failures']['email_invalid'] += 1
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.EMAIL_INVALID,
                failure_reason=f"Email verification failed: {person.email_result}",
                data=person
            )

        self.stats['emails_verified'] += 1

        # Send email verified signal
        if self.bit_engine:
            self.bit_engine.create_signal(
                signal_type=SignalType.EMAIL_VERIFIED,
                company_id=person.matched_company_id,
                source_spoke=self.name,
                metadata={'email': person.generated_email, 'person_id': person.person_id}
            )

        # SUCCESS - Person is complete
        return SpokeResult(
            status=ResultStatus.SUCCESS,
            data=person,
            hub_signal={
                'signal_type': 'person_processed',
                'impact': 5.0,
                'source': self.name,
                'company_id': person.matched_company_id,
                'person_id': person.person_id
            },
            metrics={
                'fuzzy_score': person.fuzzy_score,
                'slot': person.slot_assigned,
                'email': person.generated_email
            }
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        total = self.stats['total_processed']
        return {
            'total_processed': total,
            'matched': self.stats['matched'],
            'match_rate': f"{self.stats['matched'] / max(total, 1) * 100:.1f}%",
            'slots_won': self.stats['slots_won'],
            'slot_rate': f"{self.stats['slots_won'] / max(total, 1) * 100:.1f}%",
            'emails_verified': self.stats['emails_verified'],
            'verify_rate': f"{self.stats['emails_verified'] / max(total, 1) * 100:.1f}%",
            'failure_breakdown': self.stats['failures']
        }

    def summary(self) -> str:
        """Human-readable summary"""
        stats = self.get_stats()
        return (
            f"People Node Stats:\n"
            f"  Processed: {stats['total_processed']}\n"
            f"  Matched: {stats['matched']} ({stats['match_rate']})\n"
            f"  Slots Won: {stats['slots_won']} ({stats['slot_rate']})\n"
            f"  Emails Verified: {stats['emails_verified']} ({stats['verify_rate']})\n"
            f"  Failures: {sum(stats['failure_breakdown'].values())}"
        )
