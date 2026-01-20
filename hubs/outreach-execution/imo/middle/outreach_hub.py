"""
Outreach Spoke - Spoke #6
=========================
Campaign targeting and outreach sequencing based on BIT scores.

This spoke is the OUTPUT spoke - it consumes signals from all other spokes
and Company Hub to determine outreach readiness.

THE GOLDEN RULE:
    IF company_id IS NULL OR domain IS NULL OR email_pattern IS NULL:
        STOP. Cannot do outreach without company anchor.

BIT Score Thresholds:
    - SUSPECT (0-24): Not ready for outreach
    - WARM (25-49): Light touch (newsletter, content)
    - HOT (50-74): Direct outreach (personalized email)
    - BURNING (75+): Priority outreach (phone + email)

Barton ID Range: 04.04.02.04.70000.###
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum

# PHANTOM IMPORTS - ctb.* module does not exist (commented out per doctrine)
# from ctb.sys.enrichment.pipeline_engine.wheel.bicycle_wheel import Spoke, Hub
# from ctb.sys.enrichment.pipeline_engine.wheel.wheel_result import SpokeResult, ResultStatus, FailureType

# PHANTOM IMPORT - hub.company path does not exist
# from hub.company.bit_engine import BITEngine, BIT_THRESHOLD_WARM, BIT_THRESHOLD_HOT, BIT_THRESHOLD_BURNING

# Stub placeholders to prevent NameError
Spoke = Hub = object
SpokeResult = object
class ResultStatus: SUCCEEDED = "SUCCEEDED"; FAILED = "FAILED"
class FailureType: VALIDATION_ERROR = "VALIDATION_ERROR"; NO_MATCH = "NO_MATCH"
BITEngine = None
BIT_THRESHOLD_WARM = 25
BIT_THRESHOLD_HOT = 50
BIT_THRESHOLD_BURNING = 75

# Doctrine enforcement
from ops.enforcement.correlation_id import validate_correlation_id, CorrelationIDError
from ops.enforcement.hub_gate import validate_company_anchor, HubGateError, GateLevel

# =============================================================================
# ENFORCEMENT POINT: Marketing Safety Gate (MANDATORY)
# =============================================================================
from .marketing_safety_gate import (
    MarketingSafetyGate,
    MarketingEligibilityResult,
    IneligibleTierError,
    ActiveOverrideError,
    EligibilityCheckError,
    SendAttemptStatus,
)


logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class OutreachState(Enum):
    """Outreach lifecycle state based on BIT score."""
    SUSPECT = "suspect"      # BIT < 25: Not ready
    WARM = "warm"            # BIT 25-49: Light touch
    HOT = "hot"              # BIT 50-74: Direct outreach
    BURNING = "burning"      # BIT 75+: Priority outreach


class OutreachAction(Enum):
    """Recommended outreach action."""
    DO_NOT_CONTACT = "do_not_contact"  # Not enough intent
    NEWSLETTER = "newsletter"           # Light touch
    CONTENT = "content"                 # Educational content
    PERSONALIZED_EMAIL = "personalized_email"  # Direct outreach
    PHONE_AND_EMAIL = "phone_and_email"  # Priority outreach


# State to action mapping
STATE_TO_ACTION: Dict[OutreachState, OutreachAction] = {
    OutreachState.SUSPECT: OutreachAction.DO_NOT_CONTACT,
    OutreachState.WARM: OutreachAction.CONTENT,
    OutreachState.HOT: OutreachAction.PERSONALIZED_EMAIL,
    OutreachState.BURNING: OutreachAction.PHONE_AND_EMAIL,
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class OutreachCandidate:
    """A candidate for outreach."""
    company_id: str
    company_name: str
    bit_score: float
    outreach_state: OutreachState
    recommended_action: OutreachAction

    # Contact information
    primary_contact_id: Optional[str] = None
    primary_contact_name: Optional[str] = None
    primary_contact_email: Optional[str] = None
    primary_contact_title: Optional[str] = None

    # Company anchors (validated)
    domain: Optional[str] = None
    email_pattern: Optional[str] = None

    # Slots filled
    ceo_slot_filled: bool = False
    cfo_slot_filled: bool = False
    hr_slot_filled: bool = False

    # Metadata
    last_signal_at: Optional[datetime] = None
    signal_count: int = 0
    evaluated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'company_id': self.company_id,
            'company_name': self.company_name,
            'bit_score': self.bit_score,
            'outreach_state': self.outreach_state.value,
            'recommended_action': self.recommended_action.value,
            'primary_contact': {
                'id': self.primary_contact_id,
                'name': self.primary_contact_name,
                'email': self.primary_contact_email,
                'title': self.primary_contact_title,
            } if self.primary_contact_id else None,
            'domain': self.domain,
            'email_pattern': self.email_pattern,
            'slots': {
                'ceo': self.ceo_slot_filled,
                'cfo': self.cfo_slot_filled,
                'hr': self.hr_slot_filled,
            },
            'last_signal_at': self.last_signal_at.isoformat() if self.last_signal_at else None,
            'signal_count': self.signal_count,
            'evaluated_at': self.evaluated_at.isoformat(),
        }


@dataclass
class CampaignTarget:
    """A target for a specific campaign."""
    candidate: OutreachCandidate
    campaign_id: str
    sequence_step: int = 1
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    status: str = "pending"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'candidate': self.candidate.to_dict(),
            'campaign_id': self.campaign_id,
            'sequence_step': self.sequence_step,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'status': self.status,
        }


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class OutreachConfig:
    """Configuration for Outreach Spoke."""
    enabled: bool = True
    min_bit_score: float = 25.0  # Minimum to consider for outreach
    require_filled_slot: bool = True  # Require at least one slot filled
    require_verified_email: bool = True  # Require verified email
    max_outreach_per_day: int = 100  # Rate limit
    cooling_off_days: int = 30  # Don't re-contact within this period


def load_outreach_config() -> OutreachConfig:
    """Load Outreach configuration from environment."""
    return OutreachConfig(
        enabled=os.getenv("OUTREACH_ENABLED", "true").lower() == "true",
        min_bit_score=float(os.getenv("OUTREACH_MIN_BIT_SCORE", "25.0")),
        require_filled_slot=os.getenv("OUTREACH_REQUIRE_SLOT", "true").lower() == "true",
        require_verified_email=os.getenv("OUTREACH_REQUIRE_VERIFIED", "true").lower() == "true",
        max_outreach_per_day=int(os.getenv("OUTREACH_MAX_PER_DAY", "100")),
        cooling_off_days=int(os.getenv("OUTREACH_COOLING_OFF_DAYS", "30")),
    )


# =============================================================================
# OUTREACH SPOKE
# =============================================================================

class OutreachSpoke(Spoke):
    """
    Outreach Node - Spoke #6 of the Company Hub.

    The OUTPUT spoke that determines outreach readiness based on:
    1. BIT score (from all spokes)
    2. Company anchor validation (THE GOLDEN RULE)
    3. Slot fill status (CEO/CFO/HR)
    4. Email verification status

    DOCTRINE:
    - NEVER initiates outreach without company_id, domain, AND email_pattern
    - Uses BIT thresholds to determine outreach intensity
    - Respects cooling off periods
    - Rate limited per day
    """

    def __init__(
        self,
        hub: Hub,
        bit_engine: Optional[BITEngine] = None,
        config: OutreachConfig = None,
        company_pipeline=None,
        db_connection=None
    ):
        """
        Initialize Outreach Spoke.

        Args:
            hub: Parent hub instance
            bit_engine: BIT Engine for score lookups
            config: Outreach configuration
            company_pipeline: CompanyPipeline for anchor validation
            db_connection: Database connection for safety gate
        """
        super().__init__(name="outreach", hub=hub)
        self.bit_engine = bit_engine or BITEngine()
        self.config = config or load_outreach_config()
        self._company_pipeline = company_pipeline
        self._db_connection = db_connection

        # =====================================================================
        # ENFORCEMENT POINT: Initialize Marketing Safety Gate (MANDATORY)
        # =====================================================================
        self._safety_gate = MarketingSafetyGate(db_connection)

        # Tracking
        self._outreach_history: Dict[str, datetime] = {}  # company_id -> last_contact
        self._daily_count: int = 0
        self._daily_reset_date: Optional[datetime] = None

        # Stats
        self.stats = {
            'total_evaluated': 0,
            'passed_validation': 0,
            'failed_anchor': 0,
            'failed_bit_score': 0,
            'failed_cooling_off': 0,
            'failed_rate_limit': 0,
            'failed_safety_gate': 0,  # ADDED: Safety gate failures
            'candidates_generated': 0,
            'campaigns_created': 0,
        }

    def set_company_pipeline(self, pipeline) -> None:
        """Set company pipeline for anchor validation."""
        self._company_pipeline = pipeline

    def set_db_connection(self, conn) -> None:
        """Set database connection for safety gate."""
        self._db_connection = conn
        self._safety_gate.set_connection(conn)

    def process(self, data: Any, correlation_id: str = None) -> SpokeResult:
        """
        Evaluate companies for outreach readiness.

        Args:
            data: Company ID, list of Company IDs, or None to evaluate all
            correlation_id: MANDATORY - End-to-end trace ID

        Returns:
            SpokeResult with OutreachCandidate(s)
        """
        # Kill switch
        if not self.config.enabled or os.getenv('KILL_OUTREACH', '').lower() == 'true':
            return SpokeResult(
                status=ResultStatus.SKIPPED,
                failure_reason='killed_by_config'
            )

        # DOCTRINE: Validate correlation_id
        process_id = "outreach.spoke.process"
        try:
            correlation_id = validate_correlation_id(correlation_id, process_id, "Outreach Spoke")
        except CorrelationIDError as e:
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.VALIDATION_ERROR,
                failure_reason=str(e)
            )

        # Reset daily counter if needed
        self._check_daily_reset()

        # Handle different input types
        if isinstance(data, str):
            # Single company ID
            candidate = self._evaluate_company(data, correlation_id)
            if candidate:
                return SpokeResult(
                    status=ResultStatus.SUCCESS,
                    data=candidate,
                    metrics={'candidates': 1}
                )
            return SpokeResult(
                status=ResultStatus.SUCCESS,
                data=None,
                metrics={'candidates': 0}
            )

        elif isinstance(data, list):
            # List of company IDs
            candidates = []
            for company_id in data:
                candidate = self._evaluate_company(company_id, correlation_id)
                if candidate:
                    candidates.append(candidate)

            return SpokeResult(
                status=ResultStatus.SUCCESS,
                data=candidates,
                metrics={'candidates': len(candidates)}
            )

        elif data is None:
            # Evaluate all hot/burning companies
            return self._evaluate_all_hot_companies(correlation_id)

        else:
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.VALIDATION_ERROR,
                failure_reason=f"Unknown data type: {type(data).__name__}"
            )

    def _evaluate_company(
        self,
        company_id: str,
        correlation_id: str,
        campaign_id: str = "evaluation"
    ) -> Optional[OutreachCandidate]:
        """
        Evaluate a single company for outreach readiness.

        Returns OutreachCandidate if ready, None otherwise.

        ENFORCEMENT POINT: Safety Gate check happens FIRST before any other
        processing. If company is ineligible, we HARD_FAIL and return None.
        """
        self.stats['total_evaluated'] += 1

        # =====================================================================
        # ENFORCEMENT POINT: MARKETING SAFETY GATE (MUST BE FIRST)
        # Reads from vw_marketing_eligibility_with_overrides
        # HARD_FAIL if effective_tier = -1 or marketing_disabled = true
        # =====================================================================
        try:
            eligibility = self._safety_gate.check_eligibility_or_fail(
                company_unique_id=company_id,
                campaign_id=campaign_id,
                correlation_id=correlation_id
            )
            logger.debug(
                f"Safety gate PASS for {company_id}: "
                f"effective_tier={eligibility.effective_tier}"
            )
        except (IneligibleTierError, ActiveOverrideError, EligibilityCheckError) as e:
            # HARD_FAIL: Company is ineligible - DO NOT PROCEED
            self.stats['failed_safety_gate'] += 1
            logger.warning(
                f"SAFETY_GATE_BLOCK: {company_id} blocked by safety gate: "
                f"{e.error_code} - {str(e)}"
            )
            return None

        # Check rate limit
        if self._daily_count >= self.config.max_outreach_per_day:
            self.stats['failed_rate_limit'] += 1
            logger.debug(f"Rate limit reached, skipping {company_id}")
            return None

        # Check cooling off period
        if self._in_cooling_off(company_id):
            self.stats['failed_cooling_off'] += 1
            logger.debug(f"Company {company_id} in cooling off period")
            return None

        # =====================================================================
        # THE GOLDEN RULE - Company Anchor Validation
        # =====================================================================
        is_valid, missing_anchors = self._validate_company_anchors(company_id)

        if not is_valid:
            self.stats['failed_anchor'] += 1
            logger.debug(
                f"Golden Rule violation for {company_id}: "
                f"missing anchors: {missing_anchors}"
            )
            return None

        # =====================================================================
        # BIT Score Check (use eligibility data if available)
        # =====================================================================
        bit_score = eligibility.bit_score if eligibility else self.bit_engine.get_score_value(company_id)

        if bit_score < self.config.min_bit_score:
            self.stats['failed_bit_score'] += 1
            logger.debug(f"Company {company_id} BIT score too low: {bit_score}")
            return None

        self.stats['passed_validation'] += 1

        # Determine state and action
        outreach_state = self._get_outreach_state(bit_score)
        recommended_action = STATE_TO_ACTION[outreach_state]

        # Get company details
        company_data = self._get_company_data(company_id)

        # Build candidate
        candidate = OutreachCandidate(
            company_id=company_id,
            company_name=self._get_company_name(company_id),
            bit_score=bit_score,
            outreach_state=outreach_state,
            recommended_action=recommended_action,
        )

        # Add company details
        if company_data:
            candidate.domain = company_data.get('domain')
            candidate.email_pattern = company_data.get('email_pattern')
            candidate.ceo_slot_filled = company_data.get('ceo_slot_filled', False)
            candidate.cfo_slot_filled = company_data.get('cfo_slot_filled', False)
            candidate.hr_slot_filled = company_data.get('hr_slot_filled', False)

            # Get primary contact (HR > CEO > CFO priority)
            primary_contact = self._get_primary_contact(company_id, company_data)
            if primary_contact:
                candidate.primary_contact_id = primary_contact.get('id')
                candidate.primary_contact_name = primary_contact.get('name')
                candidate.primary_contact_email = primary_contact.get('email')
                candidate.primary_contact_title = primary_contact.get('title')

        # Get BIT details
        bit_details = self.bit_engine.get_score(company_id)
        if bit_details:
            candidate.last_signal_at = bit_details.last_signal_at
            candidate.signal_count = bit_details.signal_count

        self.stats['candidates_generated'] += 1
        self._daily_count += 1

        return candidate

    def _evaluate_all_hot_companies(
        self,
        correlation_id: str
    ) -> SpokeResult:
        """Evaluate all companies with HOT or BURNING status."""
        hot_companies = self.bit_engine.get_companies_above_threshold(BIT_THRESHOLD_HOT)

        candidates = []
        for score in hot_companies:
            candidate = self._evaluate_company(score.company_id, correlation_id)
            if candidate:
                candidates.append(candidate)

        return SpokeResult(
            status=ResultStatus.SUCCESS,
            data=candidates,
            metrics={
                'hot_companies_found': len(hot_companies),
                'candidates_generated': len(candidates)
            }
        )

    def _validate_company_anchors(
        self,
        company_id: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate the Golden Rule for a company.

        THE GOLDEN RULE:
            IF company_id IS NULL OR domain IS NULL OR email_pattern IS NULL:
                STOP. Cannot do outreach.

        ENFORCEMENT POINT: NO FALLBACK LOGIC
            If company_pipeline is not available, we FAIL CLOSED.
            We do NOT attempt alternate validation paths.

        Returns:
            Tuple of (is_valid, list_of_missing_anchors)
        """
        if not company_id:
            return False, ['company_id']

        # Use Company Pipeline if available
        if self._company_pipeline:
            return self._company_pipeline.validate_company_anchor(company_id)

        # =====================================================================
        # ENFORCEMENT POINT: NO FALLBACK - FAIL CLOSED
        # If company_pipeline is not set, we cannot validate anchors.
        # We MUST fail closed rather than attempt alternate paths.
        # =====================================================================
        logger.error(
            f"ANCHOR_VALIDATION_FAIL_CLOSED: No company_pipeline available for {company_id}. "
            f"Cannot validate anchors without company_pipeline. NO FALLBACK."
        )
        return False, ['no_company_pipeline_fail_closed']

    def _get_outreach_state(self, bit_score: float) -> OutreachState:
        """Determine outreach state from BIT score."""
        if bit_score >= BIT_THRESHOLD_BURNING:
            return OutreachState.BURNING
        elif bit_score >= BIT_THRESHOLD_HOT:
            return OutreachState.HOT
        elif bit_score >= BIT_THRESHOLD_WARM:
            return OutreachState.WARM
        else:
            return OutreachState.SUSPECT

    def _get_company_name(self, company_id: str) -> str:
        """Get company name from Company Pipeline."""
        if self._company_pipeline:
            company = self._company_pipeline.get_company(company_id)
            if company:
                return company.company_name
        return ""

    def _get_company_data(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get company data from Company Pipeline."""
        if self._company_pipeline:
            company = self._company_pipeline.get_company(company_id)
            if company:
                # Get slot fill status
                ceo_slot = company.slots.get('CEO') if hasattr(company, 'slots') else None
                cfo_slot = company.slots.get('CFO') if hasattr(company, 'slots') else None
                hr_slot = company.slots.get('HR') if hasattr(company, 'slots') else None

                return {
                    'domain': company.domain,
                    'email_pattern': company.email_pattern,
                    'ceo_slot_filled': ceo_slot.is_filled if ceo_slot else False,
                    'cfo_slot_filled': cfo_slot.is_filled if cfo_slot else False,
                    'hr_slot_filled': hr_slot.is_filled if hr_slot else False,
                    'ceo_person_id': ceo_slot.person_id if ceo_slot and ceo_slot.is_filled else None,
                    'cfo_person_id': cfo_slot.person_id if cfo_slot and cfo_slot.is_filled else None,
                    'hr_person_id': hr_slot.person_id if hr_slot and hr_slot.is_filled else None,
                }
        return None

    def _get_primary_contact(
        self,
        company_id: str,
        company_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Select primary contact for outreach.

        Priority order:
        1. HR slot (benefits decision maker)
        2. CEO slot (for smaller companies)
        3. CFO slot (budget authority)

        Args:
            company_id: Company ID
            company_data: Company data from _get_company_data()

        Returns:
            Dict with contact info or None
        """
        if not company_data:
            return None

        # Priority order for contact selection
        slot_priority = [
            ('hr', 'HR'),
            ('ceo', 'CEO'),
            ('cfo', 'CFO'),
        ]

        for slot_key, slot_type in slot_priority:
            person_id = company_data.get(f'{slot_key}_person_id')
            if person_id:
                # Try to get person details from People Hub
                person_data = self._get_person_data(person_id)
                if person_data:
                    return {
                        'id': person_id,
                        'name': person_data.get('full_name'),
                        'email': person_data.get('email'),
                        'title': person_data.get('title') or slot_type,
                        'slot_type': slot_type,
                    }

        return None

    def _get_person_data(self, person_id: str) -> Optional[Dict[str, Any]]:
        """
        Get person data from People Hub or Neon.

        Args:
            person_id: Person unique ID

        Returns:
            Dict with person data or None
        """
        # Try Company Pipeline's hub if available
        if self._company_pipeline and hasattr(self._company_pipeline, 'hub'):
            # Check if hub has people data cached
            try:
                from hubs.company_target.imo.output.neon_writer import CompanyNeonWriter
                writer = CompanyNeonWriter()

                # Query people_master for this person
                conn = writer._get_connection()
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT
                            person_unique_id,
                            full_name,
                            email,
                            title,
                            linkedin_url
                        FROM marketing.people_master
                        WHERE person_unique_id = %(person_id)s
                        LIMIT 1
                        """,
                        {'person_id': person_id}
                    )
                    row = cursor.fetchone()
                    if row:
                        columns = [desc[0] for desc in cursor.description]
                        return dict(zip(columns, row))

                writer.close()
            except Exception as e:
                logger.error(f"Failed to get person data for {person_id}: {e}")

        return None

    def _in_cooling_off(self, company_id: str) -> bool:
        """Check if company is in cooling off period."""
        if company_id not in self._outreach_history:
            return False

        last_contact = self._outreach_history[company_id]
        days_since = (datetime.utcnow() - last_contact).days

        return days_since < self.config.cooling_off_days

    def record_outreach(
        self,
        company_id: str,
        campaign_id: str = "unknown",
        success: bool = True,
        error_message: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """
        Record that outreach was sent to a company.

        ENFORCEMENT POINT: Records send result in audit log.

        Args:
            company_id: Company ID
            campaign_id: Campaign ID
            success: Whether send succeeded
            error_message: Error message if failed
            correlation_id: Trace ID
        """
        self._outreach_history[company_id] = datetime.utcnow()

        # Record in safety gate audit log
        self._safety_gate.record_send_result(
            company_unique_id=company_id,
            campaign_id=campaign_id,
            success=success,
            error_message=error_message,
            correlation_id=correlation_id
        )

    def _check_daily_reset(self):
        """Reset daily counter if new day."""
        today = datetime.utcnow().date()
        if self._daily_reset_date != today:
            self._daily_count = 0
            self._daily_reset_date = today

    # =========================================================================
    # CAMPAIGN GENERATION
    # =========================================================================

    def create_campaign_targets(
        self,
        campaign_id: str,
        candidates: List[OutreachCandidate],
        schedule_start: datetime = None,
        correlation_id: str = None
    ) -> List[CampaignTarget]:
        """
        Create campaign targets from candidates.

        ENFORCEMENT POINT: Re-validates eligibility for each candidate
        before creating campaign targets. This is a safety net in case
        eligibility changed between evaluation and target creation.

        Args:
            campaign_id: Campaign identifier
            candidates: List of outreach candidates
            schedule_start: When to start the campaign
            correlation_id: Trace ID

        Returns:
            List of CampaignTarget objects (only for eligible companies)
        """
        targets = []
        schedule = schedule_start or datetime.utcnow()
        blocked_count = 0

        for candidate in candidates:
            # =================================================================
            # ENFORCEMENT POINT: Re-check eligibility before target creation
            # Eligibility may have changed since evaluation
            # =================================================================
            try:
                self._safety_gate.check_eligibility_or_fail(
                    company_unique_id=candidate.company_id,
                    campaign_id=campaign_id,
                    correlation_id=correlation_id
                )
            except (IneligibleTierError, ActiveOverrideError, EligibilityCheckError) as e:
                # Company became ineligible - skip
                logger.warning(
                    f"CAMPAIGN_TARGET_BLOCKED: {candidate.company_id} blocked during "
                    f"target creation: {e.error_code}"
                )
                blocked_count += 1
                continue

            target = CampaignTarget(
                candidate=candidate,
                campaign_id=campaign_id,
                sequence_step=1,
                scheduled_at=schedule,
                status="scheduled"
            )
            targets.append(target)

        self.stats['campaigns_created'] += 1
        logger.info(
            f"Created {len(targets)} targets for campaign {campaign_id} "
            f"(blocked: {blocked_count})"
        )

        return targets

    def get_priority_candidates(
        self,
        limit: int = 10,
        correlation_id: str = None
    ) -> List[OutreachCandidate]:
        """
        Get top priority candidates for outreach.

        Priority is determined by:
        1. BIT score (higher is better)
        2. Outreach state (BURNING > HOT > WARM)

        Args:
            limit: Maximum candidates to return
            correlation_id: Trace ID

        Returns:
            List of priority OutreachCandidate objects
        """
        if not correlation_id:
            import uuid
            correlation_id = str(uuid.uuid4())

        # Get all burning companies first, then hot
        burning = self.bit_engine.get_companies_above_threshold(BIT_THRESHOLD_BURNING)
        hot = [
            c for c in self.bit_engine.get_companies_above_threshold(BIT_THRESHOLD_HOT)
            if c.score < BIT_THRESHOLD_BURNING
        ]

        # Combine and sort by score
        all_hot = burning + hot
        all_hot.sort(key=lambda x: x.score, reverse=True)

        # Evaluate each
        candidates = []
        for score in all_hot[:limit * 2]:  # Get extra in case some fail validation
            candidate = self._evaluate_company(score.company_id, correlation_id)
            if candidate:
                candidates.append(candidate)
            if len(candidates) >= limit:
                break

        return candidates

    # =========================================================================
    # STATS & REPORTING
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get spoke statistics."""
        return {
            **self.stats,
            'daily_count': self._daily_count,
            'daily_limit': self.config.max_outreach_per_day,
            'companies_in_cooling_off': len(self._outreach_history),
            'config': {
                'enabled': self.config.enabled,
                'min_bit_score': self.config.min_bit_score,
                'require_filled_slot': self.config.require_filled_slot,
                'cooling_off_days': self.config.cooling_off_days,
            }
        }

    def get_state_summary(self) -> Dict[str, int]:
        """Get count of companies in each outreach state."""
        return self.bit_engine.get_state_summary()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "OutreachSpoke",
    "OutreachConfig",
    "load_outreach_config",
    "OutreachCandidate",
    "CampaignTarget",
    "OutreachState",
    "OutreachAction",
    # Safety Gate (ENFORCEMENT)
    "MarketingSafetyGate",
    "MarketingEligibilityResult",
    "IneligibleTierError",
    "ActiveOverrideError",
    "EligibilityCheckError",
]
