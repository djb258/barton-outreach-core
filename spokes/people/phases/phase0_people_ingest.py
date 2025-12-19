"""
Phase 0: People Ingest
======================
Classifies newly ingested people before Phases 5-8 run.
Determines initial funnel state based on data characteristics.

Initial State Classification Logic:
- If company_id missing → SUSPECT
- If reply flag exists (historical import) → WARM
- If TalentFlow movement exists → TALENTFLOW_WARM
- If BIT score ≥ 25 → WARM
- If past meeting flag → APPOINTMENT
- Default → SUSPECT

NO DATABASE WRITES - classification only.
All output anchored to company_id (Company-First doctrine).

DOCTRINE ENFORCEMENT:
- correlation_id is MANDATORY (FAIL HARD if missing)
- hub_gate validation for company anchor
"""

import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from enum import Enum
import pandas as pd

# Doctrine enforcement imports
from ops.enforcement.correlation_id import validate_correlation_id, CorrelationIDError
from ops.enforcement.hub_gate import validate_company_anchor, HubGateError, GateLevel

from ..movement_engine import LifecycleState, EventType as MovementEventType


class IngestEventType(Enum):
    """Types of events detected during ingest."""
    HISTORICAL_REPLY = "historical_reply"
    TALENTFLOW_MOVEMENT = "talentflow_movement"
    BIT_THRESHOLD_MET = "bit_threshold_met"
    PAST_MEETING = "past_meeting"
    MISSING_COMPANY_ID = "missing_company_id"
    DEFAULT_INGEST = "default_ingest"


@dataclass
class IngestEvent:
    """An event detected during people ingest."""
    event_type: IngestEventType
    detected_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'event_type': self.event_type.value,
            'detected_at': self.detected_at.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class PeopleIngestResult:
    """Result of classifying a single person during ingest."""
    person_id: str
    company_id: Optional[str]
    initial_funnel_state: LifecycleState
    slot_candidate: Optional[str] = None  # Candidate slot type if applicable
    ingest_events: List[IngestEvent] = field(default_factory=list)
    classification_reason: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'person_id': self.person_id,
            'company_id': self.company_id,
            'initial_funnel_state': self.initial_funnel_state.value,
            'slot_candidate': self.slot_candidate,
            'ingest_events': [e.to_dict() for e in self.ingest_events],
            'classification_reason': self.classification_reason
        }


@dataclass
class Phase0Stats:
    """Statistics for Phase 0 execution."""
    total_input: int = 0
    classified_suspect: int = 0
    classified_warm: int = 0
    classified_talentflow_warm: int = 0
    classified_appointment: int = 0
    missing_company_id: int = 0
    historical_replies_detected: int = 0
    talentflow_movements_detected: int = 0
    bit_thresholds_met: int = 0
    past_meetings_detected: int = 0
    hub_gate_failures: int = 0
    duration_seconds: float = 0.0
    correlation_id: str = ""  # Propagated unchanged


class Phase0PeopleIngest:
    """
    Phase 0: Classify newly ingested people.

    Determines initial funnel state for each person based on
    data characteristics. NO database writes - classification only.

    Classification Priority (first match wins):
    1. Missing company_id → SUSPECT (unanchored)
    2. Past meeting flag → APPOINTMENT
    3. Historical reply → WARM
    4. TalentFlow movement → TALENTFLOW_WARM
    5. BIT score ≥ 25 → WARM
    6. Default → SUSPECT

    REQUIRES: company_id anchor (Company-First doctrine)
    """

    # BIT score threshold for WARM classification
    BIT_WARM_THRESHOLD = 25

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Phase 0.

        Args:
            config: Configuration dictionary with:
                - bit_warm_threshold: BIT score threshold for WARM (default: 25)
        """
        self.config = config or {}
        self.bit_threshold = self.config.get('bit_warm_threshold', self.BIT_WARM_THRESHOLD)

    def run(self, people_df: pd.DataFrame,
            correlation_id: str) -> Tuple[List[PeopleIngestResult], Phase0Stats]:
        """
        Run people ingest classification phase.

        DOCTRINE: correlation_id is MANDATORY. FAIL HARD if missing.

        Note: Phase 0 does NOT fail hard on missing company_id - it classifies
        unanchored records as SUSPECT per PRD. Hub gate is validated but failure
        results in SUSPECT classification, not hard failure.

        Args:
            people_df: DataFrame with people to classify
                Expected columns: person_id, company_id, first_name, last_name
                Optional columns: has_replied, talentflow_movement, bit_score,
                                 has_meeting, job_title, title
            correlation_id: MANDATORY - End-to-end trace ID (UUID v4)

        Returns:
            Tuple of (List[PeopleIngestResult], Phase0Stats)

        Raises:
            CorrelationIDError: If correlation_id is missing or invalid (FAIL HARD)
        """
        # DOCTRINE ENFORCEMENT: Validate correlation_id (FAIL HARD)
        process_id = "people.lifecycle.ingest.phase0"
        correlation_id = validate_correlation_id(correlation_id, process_id, "Phase 0")

        start_time = time.time()
        stats = Phase0Stats(total_input=len(people_df), correlation_id=correlation_id)
        results = []

        for idx, row in people_df.iterrows():
            person_id = str(row.get('person_id', idx))
            company_id = str(row.get('company_id', '') or row.get('matched_company_id', '')).strip()

            # Hub gate validation (soft - classify as SUSPECT if fails)
            gate_result = validate_company_anchor(
                record=row.to_dict(),
                level=GateLevel.COMPANY_ID_ONLY,
                process_id=process_id,
                correlation_id=correlation_id,
                fail_hard=False  # Phase 0 classifies failures as SUSPECT
            )
            if not gate_result.passed:
                stats.hub_gate_failures += 1

            # Classify this person
            result = self._classify_person(person_id, company_id, row.to_dict(), stats)
            results.append(result)

        stats.duration_seconds = time.time() - start_time
        return results, stats

    def _classify_person(
        self,
        person_id: str,
        company_id: str,
        row_data: Dict[str, Any],
        stats: Phase0Stats
    ) -> PeopleIngestResult:
        """
        Classify a single person's initial funnel state.

        Args:
            person_id: Person unique ID
            company_id: Company anchor ID (may be empty)
            row_data: Full row data dictionary
            stats: Stats object to update

        Returns:
            PeopleIngestResult with classification
        """
        events = []
        now = datetime.now()

        # Extract classification signals
        has_replied = self._check_reply_flag(row_data)
        has_talentflow = self._check_talentflow_flag(row_data)
        bit_score = self._get_bit_score(row_data)
        has_meeting = self._check_meeting_flag(row_data)

        # Default values
        initial_state = LifecycleState.SUSPECT
        reason = "default_classification"
        slot_candidate = self._determine_slot_candidate(row_data)

        # Classification Priority (first match wins)

        # 1. Missing company_id → SUSPECT (unanchored)
        if not company_id:
            stats.missing_company_id += 1
            events.append(IngestEvent(
                event_type=IngestEventType.MISSING_COMPANY_ID,
                detected_at=now,
                metadata={'person_id': person_id}
            ))
            initial_state = LifecycleState.SUSPECT
            reason = "missing_company_id_unanchored"
            stats.classified_suspect += 1

        # 2. Past meeting flag → APPOINTMENT
        elif has_meeting:
            stats.past_meetings_detected += 1
            events.append(IngestEvent(
                event_type=IngestEventType.PAST_MEETING,
                detected_at=now,
                metadata={'person_id': person_id, 'company_id': company_id}
            ))
            initial_state = LifecycleState.APPOINTMENT
            reason = "past_meeting_detected"
            stats.classified_appointment += 1

        # 3. Historical reply → WARM
        elif has_replied:
            stats.historical_replies_detected += 1
            events.append(IngestEvent(
                event_type=IngestEventType.HISTORICAL_REPLY,
                detected_at=now,
                metadata={'person_id': person_id, 'company_id': company_id}
            ))
            initial_state = LifecycleState.WARM
            reason = "historical_reply_detected"
            stats.classified_warm += 1

        # 4. TalentFlow movement → TALENTFLOW_WARM
        elif has_talentflow:
            stats.talentflow_movements_detected += 1
            events.append(IngestEvent(
                event_type=IngestEventType.TALENTFLOW_MOVEMENT,
                detected_at=now,
                metadata={'person_id': person_id, 'company_id': company_id}
            ))
            initial_state = LifecycleState.TALENTFLOW_WARM
            reason = "talentflow_movement_detected"
            stats.classified_talentflow_warm += 1

        # 5. BIT score ≥ threshold → WARM
        elif bit_score >= self.bit_threshold:
            stats.bit_thresholds_met += 1
            events.append(IngestEvent(
                event_type=IngestEventType.BIT_THRESHOLD_MET,
                detected_at=now,
                metadata={
                    'person_id': person_id,
                    'company_id': company_id,
                    'bit_score': bit_score,
                    'threshold': self.bit_threshold
                }
            ))
            initial_state = LifecycleState.WARM
            reason = f"bit_score_{bit_score}_meets_threshold"
            stats.classified_warm += 1

        # 6. Default → SUSPECT
        else:
            events.append(IngestEvent(
                event_type=IngestEventType.DEFAULT_INGEST,
                detected_at=now,
                metadata={'person_id': person_id, 'company_id': company_id}
            ))
            initial_state = LifecycleState.SUSPECT
            reason = "default_cold_ingest"
            stats.classified_suspect += 1

        return PeopleIngestResult(
            person_id=person_id,
            company_id=company_id if company_id else None,
            initial_funnel_state=initial_state,
            slot_candidate=slot_candidate,
            ingest_events=events,
            classification_reason=reason,
            raw_data=row_data
        )

    def _check_reply_flag(self, row_data: Dict[str, Any]) -> bool:
        """
        Check if person has historical reply flag.

        Args:
            row_data: Row data dictionary

        Returns:
            True if reply flag exists
        """
        # Check various possible column names
        reply_fields = ['has_replied', 'replied', 'reply_received',
                       'historical_reply', 'email_replied']

        for field in reply_fields:
            value = row_data.get(field)
            if value is not None and self._is_truthy(value):
                return True

        return False

    def _check_talentflow_flag(self, row_data: Dict[str, Any]) -> bool:
        """
        Check if person has TalentFlow movement flag.

        Args:
            row_data: Row data dictionary

        Returns:
            True if TalentFlow movement detected
        """
        # Check various possible column names
        tf_fields = ['talentflow_movement', 'talentflow', 'job_change',
                    'employer_change', 'movement_detected']

        for field in tf_fields:
            value = row_data.get(field)
            if value is not None and self._is_truthy(value):
                return True

        return False

    def _get_bit_score(self, row_data: Dict[str, Any]) -> int:
        """
        Get BIT score from row data.

        Args:
            row_data: Row data dictionary

        Returns:
            BIT score (0 if not found)
        """
        # Check various possible column names
        bit_fields = ['bit_score', 'buyer_intent_score', 'intent_score',
                     'engagement_score', 'bit']

        for field in bit_fields:
            value = row_data.get(field)
            if value is not None:
                try:
                    return int(float(value))
                except (ValueError, TypeError):
                    continue

        return 0

    def _check_meeting_flag(self, row_data: Dict[str, Any]) -> bool:
        """
        Check if person has past meeting flag.

        Args:
            row_data: Row data dictionary

        Returns:
            True if past meeting detected
        """
        # Check various possible column names
        meeting_fields = ['has_meeting', 'meeting_scheduled', 'appointment',
                         'meeting_booked', 'calendar_meeting', 'past_meeting']

        for field in meeting_fields:
            value = row_data.get(field)
            if value is not None and self._is_truthy(value):
                return True

        return False

    def _determine_slot_candidate(self, row_data: Dict[str, Any]) -> Optional[str]:
        """
        Determine potential slot candidate based on title.

        Args:
            row_data: Row data dictionary

        Returns:
            Slot type string or None
        """
        title = str(row_data.get('job_title', '') or row_data.get('title', '')).lower()

        if not title:
            return None

        # Quick slot detection (full classification happens in Phase 6)
        if any(kw in title for kw in ['chro', 'chief hr', 'chief human', 'chief people']):
            return 'CHRO'
        elif any(kw in title for kw in ['hr director', 'hr manager', 'hr lead']):
            return 'HR_MANAGER'
        elif any(kw in title for kw in ['benefit', 'total rewards']):
            return 'BENEFITS_LEAD'
        elif any(kw in title for kw in ['payroll']):
            return 'PAYROLL_ADMIN'
        elif any(kw in title for kw in ['hr coord', 'hr spec', 'hr general', 'hrbp']):
            return 'HR_SUPPORT'

        return None

    def _is_truthy(self, value: Any) -> bool:
        """
        Check if value is truthy (handles strings, bools, ints).

        Args:
            value: Value to check

        Returns:
            True if truthy
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value > 0
        if isinstance(value, str):
            return value.lower() in ('true', 'yes', '1', 'y')
        return bool(value)

    def classify_single(self, person_data: Dict[str, Any]) -> PeopleIngestResult:
        """
        Classify a single person (convenience method).

        Args:
            person_data: Dictionary with person data

        Returns:
            PeopleIngestResult
        """
        stats = Phase0Stats(total_input=1)
        person_id = str(person_data.get('person_id', 'unknown'))
        company_id = str(person_data.get('company_id', '') or '').strip()

        return self._classify_person(person_id, company_id, person_data, stats)


def classify_people_ingest(
    people_df: pd.DataFrame,
    config: Dict[str, Any] = None
) -> Tuple[List[PeopleIngestResult], Phase0Stats]:
    """
    Convenience function to run people ingest classification.

    Args:
        people_df: DataFrame with people to classify
        config: Optional configuration

    Returns:
        Tuple of (List[PeopleIngestResult], Phase0Stats)
    """
    phase0 = Phase0PeopleIngest(config=config)
    return phase0.run(people_df)
