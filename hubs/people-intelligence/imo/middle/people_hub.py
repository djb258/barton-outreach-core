"""
People Node Spoke - Orchestrator for People Processing
======================================================
Manages the complete people pipeline through the wheel.

This is the main spoke class that orchestrates:
1. Company Hub Anchor Validation (THE GOLDEN RULE)
2. Hub Gate (company matching)
3. Slot Assignment (seniority competition)
4. Email Verification Sub-Wheel
5. Export to Neon

THE GOLDEN RULE:
    IF company_id IS NULL OR domain IS NULL OR email_pattern IS NULL:
        STOP. Route to Company Identity Pipeline first.

Wraps existing phase implementations with wheel architecture.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import logging
import uuid

# PHANTOM IMPORTS - ctb.* module does not exist (commented out per doctrine)
# from ctb.sys.enrichment.pipeline_engine.wheel.bicycle_wheel import Spoke, Hub, SubWheel, BicycleWheel
# from ctb.sys.enrichment.pipeline_engine.wheel.wheel_result import SpokeResult, FailureResult, ResultStatus, FailureType

# PHANTOM IMPORT - hub.company path does not exist (hubs use hyphens, not valid Python)
# from hub.company.bit_engine import BITEngine, SignalType

# Stub placeholders to prevent NameError (minimal fix per doctrine)
Spoke = Hub = SubWheel = BicycleWheel = object
SpokeResult = FailureResult = object
class ResultStatus: SUCCEEDED = "SUCCEEDED"; FAILED = "FAILED"
class FailureType: VALIDATION_ERROR = "VALIDATION_ERROR"; NO_MATCH = "NO_MATCH"
BITEngine = SignalType = None  # Not available

# Doctrine enforcement
from ops.enforcement.correlation_id import validate_correlation_id, CorrelationIDError
from ops.enforcement.signal_dedup import should_emit_signal


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
    0. Company Hub Anchor Validation (THE GOLDEN RULE) ← NEW
    1. Hub Gate - Company matching (fuzzy)
    2. Slot Assignment - Seniority competition
    3. Email Generation - Pattern application
    4. Email Verification - MillionVerifier sub-wheel

    THE GOLDEN RULE:
        Before processing ANY person, the associated company MUST have:
        - company_id (valid Barton ID)
        - domain (website URL)
        - email_pattern (e.g., {first}.{last}@domain.com)

        If ANY anchor is missing, STOP and route to Company Identity Pipeline.
    """

    def __init__(
        self,
        hub: Hub,
        bit_engine: Optional[BITEngine] = None,
        company_pipeline=None
    ):
        """
        Initialize People Node Spoke.

        Args:
            hub: Parent hub instance
            bit_engine: BIT Engine for signals
            company_pipeline: CompanyPipeline for anchor validation
        """
        super().__init__(name="people_node", hub=hub)
        self.bit_engine = bit_engine or BITEngine()
        self._company_pipeline = company_pipeline

        # Track processing stats
        self.stats = {
            'total_processed': 0,
            'anchor_validated': 0,
            'anchor_failed': 0,
            'matched': 0,
            'slots_won': 0,
            'emails_verified': 0,
            'failures': {
                'missing_anchor': 0,  # NEW - company missing required anchors
                'no_match': 0,
                'low_confidence': 0,
                'lost_slot': 0,
                'no_pattern': 0,
                'email_invalid': 0
            }
        }

    def set_company_pipeline(self, pipeline) -> None:
        """Set company pipeline for anchor validation."""
        self._company_pipeline = pipeline

    def validate_company_anchors(
        self,
        company_id: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate the Golden Rule for a company.

        THE GOLDEN RULE:
            IF company_id IS NULL OR domain IS NULL OR email_pattern IS NULL:
                STOP. Route to Company Identity Pipeline first.

        Args:
            company_id: Company ID to validate

        Returns:
            Tuple of (is_valid, list_of_missing_anchors)
        """
        if not company_id:
            return False, ['company_id']

        # Use company pipeline if available
        if self._company_pipeline:
            return self._company_pipeline.validate_company_anchor(company_id)

        # Fallback: Try to get company from hub
        try:
            from hubs.company_target.imo.middle.company_hub import CompanyHub
            company_hub = CompanyHub()
            company = company_hub.get_company(company_id)

            if not company:
                return False, ['company_not_found']

            missing = []
            if not company.company_unique_id:
                missing.append('company_id')
            if not company.domain:
                missing.append('domain')
            if not company.email_pattern:
                missing.append('email_pattern')

            return len(missing) == 0, missing

        except Exception as e:
            logger.error(f"Failed to validate company anchors: {e}")
            return False, ['validation_error']

    def process(self, data: Any, correlation_id: str = None) -> SpokeResult:
        """
        Process a person record through the People Node.

        DOCTRINE: correlation_id is MANDATORY. FAIL HARD if missing.

        This method coordinates all sub-spokes and routes failures.

        Processing Order:
        0. THE GOLDEN RULE - Validate company anchors
        1. Hub Gate - Company matching (fuzzy)
        2. Slot Assignment - Seniority competition
        3. Email Generation - Pattern application
        4. Email Verification - MillionVerifier sub-wheel

        Args:
            data: PersonRecord to process
            correlation_id: MANDATORY - End-to-end trace ID (UUID v4)

        Returns:
            SpokeResult with processing outcome

        Raises:
            CorrelationIDError: If correlation_id is missing or invalid (FAIL HARD)
        """
        # DOCTRINE ENFORCEMENT: Validate correlation_id (FAIL HARD)
        process_id = "people.spoke.process"
        try:
            correlation_id = validate_correlation_id(correlation_id, process_id, "People Spoke")
        except CorrelationIDError as e:
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.VALIDATION_ERROR,
                failure_reason=str(e)
            )

        if not isinstance(data, PersonRecord):
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.VALIDATION_ERROR,
                failure_reason="Expected PersonRecord, got " + type(data).__name__
            )

        person = data
        self.stats['total_processed'] += 1

        # =====================================================================
        # STEP 0: THE GOLDEN RULE - Company Anchor Validation
        # =====================================================================
        # IF company_id IS NULL OR domain IS NULL OR email_pattern IS NULL:
        #     STOP. Route to Company Identity Pipeline first.
        # =====================================================================

        if person.matched_company_id:
            is_valid, missing_anchors = self.validate_company_anchors(
                person.matched_company_id
            )

            if not is_valid:
                self.stats['anchor_failed'] += 1
                self.stats['failures']['missing_anchor'] += 1

                logger.warning(
                    f"Golden Rule violation for person {person.person_id}: "
                    f"Company {person.matched_company_id} missing anchors: {missing_anchors}"
                )

                return SpokeResult(
                    status=ResultStatus.FAILED,
                    failure_type=FailureType.VALIDATION_ERROR,
                    failure_reason=(
                        f"Golden Rule violation: Company {person.matched_company_id} "
                        f"missing required anchors: {', '.join(missing_anchors)}. "
                        f"Route to Company Identity Pipeline first."
                    ),
                    data=person,
                    metrics={'missing_anchors': missing_anchors}
                )

            self.stats['anchor_validated'] += 1

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

        # Send signal to BIT Engine (with deduplication and Neon persistence)
        if self.bit_engine:
            # Check deduplication before emitting (24h window for operational signals)
            signal_key = f"slot_filled:{person.matched_company_id}:{person.slot_assigned}"
            if should_emit_signal(SignalType.SLOT_FILLED.value, person.matched_company_id, correlation_id):
                self.bit_engine.create_signal(
                    signal_type=SignalType.SLOT_FILLED,
                    company_id=person.matched_company_id,
                    source_spoke=self.name,
                    metadata={'slot_type': person.slot_assigned, 'person_id': person.person_id},
                    correlation_id=correlation_id  # For Neon persistence
                )
            else:
                logger.debug(f"Duplicate SLOT_FILLED signal dropped for {person.matched_company_id}")

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

        # Send email verified signal (with deduplication and Neon persistence)
        if self.bit_engine:
            if should_emit_signal(SignalType.EMAIL_VERIFIED.value, person.matched_company_id, correlation_id):
                self.bit_engine.create_signal(
                    signal_type=SignalType.EMAIL_VERIFIED,
                    company_id=person.matched_company_id,
                    source_spoke=self.name,
                    metadata={'email': person.generated_email, 'person_id': person.person_id},
                    correlation_id=correlation_id  # For Neon persistence
                )
            else:
                logger.debug(f"Duplicate EMAIL_VERIFIED signal dropped for {person.matched_company_id}")

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
