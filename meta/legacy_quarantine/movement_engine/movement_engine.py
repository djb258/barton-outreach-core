"""
Movement Engine
===============
Core engine for detecting events and orchestrating funnel state transitions.

This module provides the main MovementEngine class that:
- Detects engagement events from various sources
- Evaluates events against movement rules
- Determines if state transitions should occur
- Records transition decisions (placeholder - no DB writes yet)

Architecture:
- Orchestrates StateMachine and MovementRules
- Pure logic implementation (no database access in this version)
- Event-driven processing model
- Supports batch event processing with priority resolution

Usage:
    from movement_engine import MovementEngine

    engine = MovementEngine()

    # Detect and process an event
    result = engine.detect_event(
        company_id="uuid-123",
        person_id="uuid-456",
        event_type="email_reply",
        metadata={"reply_text": "I'm interested!"}
    )

    # Determine next state
    transition = engine.determine_next_state(
        current_state="SUSPECT",
        event_type="EVENT_REPLY"
    )
"""

from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import uuid

from .state_machine import (
    StateMachine,
    LifecycleState,
    EventType,
    FunnelMembership,
    TransitionResult
)
from .movement_rules import (
    MovementRules,
    MovementRulesConfig,
    ReplyClassification,
    ReplySentiment,
    ThresholdResult,
    BITScoreResult,
    TalentFlowValidation,
    ReengagementStatus,
    CooldownStatus
)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ContactState:
    """
    Current state of a contact in the funnel system.

    This is a placeholder data structure - in production,
    this would be loaded from the database.
    """
    company_id: str
    person_id: str
    email: str
    current_state: LifecycleState
    funnel_membership: FunnelMembership
    last_event_ts: Optional[datetime] = None
    last_state_change_ts: Optional[datetime] = None
    email_open_count: int = 0
    email_click_count: int = 0
    email_reply_count: int = 0
    current_bit_score: int = 0
    reengagement_cycle: int = 0
    is_locked: bool = False
    cooldown_until: Optional[datetime] = None


@dataclass
class DetectedEvent:
    """
    An event detected by the Movement Engine.
    """
    event_id: str
    company_id: str
    person_id: str
    event_type: EventType
    raw_event_type: str  # Original event type string
    event_ts: datetime
    metadata: Dict[str, Any]
    source_system: Optional[str] = None
    is_duplicate: bool = False
    event_hash: Optional[str] = None


@dataclass
class TransitionDecision:
    """
    Decision about whether a transition should occur.
    """
    should_transition: bool
    from_state: LifecycleState
    to_state: Optional[LifecycleState]
    event_type: EventType
    event_id: str
    company_id: str
    person_id: str
    reason: str
    validation_checks: List[Dict[str, Any]] = field(default_factory=list)
    blocked_by_cooldown: bool = False
    blocked_by_lock: bool = False
    priority: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TransitionRecord:
    """
    Record of a transition (placeholder - no DB writes yet).
    """
    transition_id: str
    company_id: str
    person_id: str
    from_state: LifecycleState
    to_state: LifecycleState
    event_type: EventType
    event_id: str
    event_ts: datetime
    transition_ts: datetime
    validation_checks: List[Dict[str, Any]]
    metadata: Dict[str, Any]


# =============================================================================
# EVENT TYPE MAPPING
# =============================================================================

# Maps raw event strings to EventType enum
RAW_EVENT_TYPE_MAP: Dict[str, EventType] = {
    # Email events
    "email_open": EventType.EVENT_OPENS_X3,  # Requires threshold check
    "email_click": EventType.EVENT_CLICKS_X2,  # Requires threshold check
    "email_reply": EventType.EVENT_REPLY,
    "reply": EventType.EVENT_REPLY,
    "unsubscribe": EventType.EVENT_UNSUBSCRIBE,
    "hard_bounce": EventType.EVENT_HARD_BOUNCE,
    "bounce": EventType.EVENT_HARD_BOUNCE,

    # TalentFlow events
    "talentflow_move": EventType.EVENT_TALENTFLOW_MOVE,
    "job_change": EventType.EVENT_TALENTFLOW_MOVE,
    "promotion": EventType.EVENT_TALENTFLOW_MOVE,

    # BIT events
    "bit_threshold": EventType.EVENT_BIT_THRESHOLD,
    "bit_score_update": EventType.EVENT_BIT_THRESHOLD,

    # Lifecycle events
    "appointment": EventType.EVENT_APPOINTMENT,
    "meeting_booked": EventType.EVENT_APPOINTMENT,
    "client_signed": EventType.EVENT_CLIENT_SIGNED,
    "contract_signed": EventType.EVENT_CLIENT_SIGNED,

    # System events
    "inactivity": EventType.EVENT_INACTIVITY_30D,
    "inactivity_30d": EventType.EVENT_INACTIVITY_30D,
    "reengagement_trigger": EventType.EVENT_REENGAGEMENT_TRIGGER,
    "reengagement_exhausted": EventType.EVENT_REENGAGEMENT_EXHAUSTED,
    "manual_override": EventType.EVENT_MANUAL_OVERRIDE,
}


# =============================================================================
# MOVEMENT ENGINE
# =============================================================================

class MovementEngine:
    """
    Core engine for funnel state transitions.

    The MovementEngine orchestrates the detection and evaluation of
    engagement events, determines if state transitions should occur,
    and records transition decisions.

    Key responsibilities:
    1. Event detection and classification
    2. Threshold evaluation (opens, clicks, BIT score)
    3. Transition validation against state machine
    4. Cooldown and lock enforcement
    5. Transition recording (placeholder)
    """

    def __init__(
        self,
        rules_config: Optional[MovementRulesConfig] = None
    ):
        """
        Initialize the Movement Engine.

        Args:
            rules_config: Optional configuration for movement rules
        """
        self.state_machine = StateMachine()
        self.rules = MovementRules(config=rules_config)

        # In-memory storage (placeholder for database)
        self._pending_events: List[DetectedEvent] = []
        self._transition_records: List[TransitionRecord] = []

    # =========================================================================
    # EVENT DETECTION
    # =========================================================================

    def detect_event(
        self,
        company_id: str,
        person_id: str,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        source_system: Optional[str] = None,
        event_ts: Optional[datetime] = None
    ) -> DetectedEvent:
        """
        Detect and classify an engagement event.

        Args:
            company_id: Company identifier
            person_id: Person identifier
            event_type: Raw event type string
            metadata: Event metadata (reply text, click URL, etc.)
            source_system: Source system that generated the event
            event_ts: Event timestamp (uses now if not provided)

        Returns:
            DetectedEvent with classified event type
        """
        metadata = metadata or {}
        event_ts = event_ts or datetime.now()

        # Map raw event type to enum
        mapped_type = self._map_event_type(event_type, metadata)

        # Generate event ID and hash
        event_id = str(uuid.uuid4())
        event_hash = self._generate_event_hash(
            person_id=person_id,
            event_type=mapped_type.value,
            source_system=source_system,
            event_ts=event_ts
        )

        event = DetectedEvent(
            event_id=event_id,
            company_id=company_id,
            person_id=person_id,
            event_type=mapped_type,
            raw_event_type=event_type,
            event_ts=event_ts,
            metadata=metadata,
            source_system=source_system,
            is_duplicate=False,  # Dedup check would happen against DB
            event_hash=event_hash
        )

        # Add to pending events queue
        self._pending_events.append(event)

        return event

    def _map_event_type(
        self,
        raw_type: str,
        metadata: Dict[str, Any]
    ) -> EventType:
        """
        Map raw event type string to EventType enum.

        Args:
            raw_type: Raw event type string
            metadata: Event metadata for context

        Returns:
            Mapped EventType
        """
        normalized = raw_type.lower().strip().replace(" ", "_")

        if normalized in RAW_EVENT_TYPE_MAP:
            return RAW_EVENT_TYPE_MAP[normalized]

        # Fallback mappings based on metadata
        if "reply" in normalized or metadata.get("reply_text"):
            return EventType.EVENT_REPLY

        if "click" in normalized:
            return EventType.EVENT_CLICKS_X2

        if "open" in normalized:
            return EventType.EVENT_OPENS_X3

        # Default to manual override for unknown types
        return EventType.EVENT_MANUAL_OVERRIDE

    def _generate_event_hash(
        self,
        person_id: str,
        event_type: str,
        source_system: Optional[str],
        event_ts: datetime
    ) -> str:
        """
        Generate deduplication hash for an event.

        Args:
            person_id: Person identifier
            event_type: Event type
            source_system: Source system
            event_ts: Event timestamp (truncated to hour)

        Returns:
            SHA256 hash string
        """
        hash_input = (
            f"{person_id}|"
            f"{event_type}|"
            f"{source_system or ''}|"
            f"{event_ts.strftime('%Y-%m-%d %H')}"
        )
        return hashlib.sha256(hash_input.encode()).hexdigest()

    # =========================================================================
    # STATE TRANSITION DETERMINATION
    # =========================================================================

    def determine_next_state(
        self,
        current_state: str,
        event_type: str,
        contact_data: Optional[Dict[str, Any]] = None
    ) -> TransitionResult:
        """
        Determine the next state for a given event.

        Args:
            current_state: Current state as string
            event_type: Event type as string
            contact_data: Optional contact data for context

        Returns:
            TransitionResult with next state information
        """
        # Parse state and event type
        try:
            state = LifecycleState(current_state)
        except ValueError:
            return TransitionResult(
                is_valid=False,
                from_state=None,
                to_state=None,
                event_type=None,
                reason=f"Invalid current state: {current_state}",
                priority=0
            )

        try:
            event = EventType(event_type)
        except ValueError:
            # Try mapping from raw type
            event = self._map_event_type(event_type, contact_data or {})

        # Use state machine to evaluate
        return self.state_machine.evaluate_transition(state, event)

    def evaluate_transition(
        self,
        contact: ContactState,
        event: DetectedEvent
    ) -> TransitionDecision:
        """
        Fully evaluate whether a transition should occur.

        This method performs all validation checks including:
        - State machine validity
        - Threshold checks (opens, clicks, BIT)
        - Cooldown enforcement
        - Lock status

        Args:
            contact: Current contact state
            event: Detected event

        Returns:
            TransitionDecision with full evaluation result
        """
        validation_checks = []

        # Check if contact is locked
        if contact.is_locked:
            return TransitionDecision(
                should_transition=False,
                from_state=contact.current_state,
                to_state=None,
                event_type=event.event_type,
                event_id=event.event_id,
                company_id=event.company_id,
                person_id=event.person_id,
                reason="Contact is locked",
                validation_checks=[{"check": "lock_status", "passed": False}],
                blocked_by_lock=True
            )

        # Check cooldown
        cooldown_status = self.rules.check_cooldown(contact.last_state_change_ts)
        validation_checks.append({
            "check": "cooldown",
            "passed": not cooldown_status.is_in_cooldown,
            "details": cooldown_status.reason
        })

        # Allow bypass for high-priority events
        can_bypass_cooldown = event.event_type in [
            EventType.EVENT_APPOINTMENT,
            EventType.EVENT_CLIENT_SIGNED,
            EventType.EVENT_UNSUBSCRIBE,
            EventType.EVENT_HARD_BOUNCE
        ]

        if cooldown_status.is_in_cooldown and not can_bypass_cooldown:
            return TransitionDecision(
                should_transition=False,
                from_state=contact.current_state,
                to_state=None,
                event_type=event.event_type,
                event_id=event.event_id,
                company_id=event.company_id,
                person_id=event.person_id,
                reason=cooldown_status.reason,
                validation_checks=validation_checks,
                blocked_by_cooldown=True
            )

        # Event-specific validation
        event_validation = self._validate_event_thresholds(contact, event)
        validation_checks.extend(event_validation["checks"])

        if not event_validation["passed"]:
            return TransitionDecision(
                should_transition=False,
                from_state=contact.current_state,
                to_state=None,
                event_type=event.event_type,
                event_id=event.event_id,
                company_id=event.company_id,
                person_id=event.person_id,
                reason=event_validation["reason"],
                validation_checks=validation_checks
            )

        # Evaluate state machine transition
        transition_result = self.state_machine.evaluate_transition(
            contact.current_state,
            event.event_type
        )
        validation_checks.append({
            "check": "state_machine",
            "passed": transition_result.is_valid,
            "details": transition_result.reason
        })

        if not transition_result.is_valid:
            return TransitionDecision(
                should_transition=False,
                from_state=contact.current_state,
                to_state=None,
                event_type=event.event_type,
                event_id=event.event_id,
                company_id=event.company_id,
                person_id=event.person_id,
                reason=transition_result.reason,
                validation_checks=validation_checks
            )

        # Transition approved
        return TransitionDecision(
            should_transition=True,
            from_state=contact.current_state,
            to_state=transition_result.to_state,
            event_type=event.event_type,
            event_id=event.event_id,
            company_id=event.company_id,
            person_id=event.person_id,
            reason=transition_result.reason,
            validation_checks=validation_checks,
            priority=transition_result.priority
        )

    def _validate_event_thresholds(
        self,
        contact: ContactState,
        event: DetectedEvent
    ) -> Dict[str, Any]:
        """
        Validate event-specific thresholds.

        Args:
            contact: Current contact state
            event: Detected event

        Returns:
            Dict with passed status, reason, and checks
        """
        checks = []

        # Opens threshold check
        if event.event_type == EventType.EVENT_OPENS_X3:
            result = self.rules.check_open_threshold(contact.email_open_count + 1)
            checks.append({
                "check": "opens_threshold",
                "passed": result.threshold_met,
                "details": result.reason
            })
            if not result.threshold_met:
                return {
                    "passed": False,
                    "reason": result.reason,
                    "checks": checks
                }

        # Clicks threshold check
        elif event.event_type == EventType.EVENT_CLICKS_X2:
            result = self.rules.check_click_threshold(contact.email_click_count + 1)
            checks.append({
                "check": "clicks_threshold",
                "passed": result.threshold_met,
                "details": result.reason
            })
            if not result.threshold_met:
                return {
                    "passed": False,
                    "reason": result.reason,
                    "checks": checks
                }

        # BIT threshold check
        elif event.event_type == EventType.EVENT_BIT_THRESHOLD:
            new_score = event.metadata.get("bit_score", contact.current_bit_score)
            result = self.rules.check_bit_threshold(new_score, "warm")
            checks.append({
                "check": "bit_threshold",
                "passed": result.threshold_met,
                "details": result.reason
            })
            if not result.threshold_met:
                return {
                    "passed": False,
                    "reason": result.reason,
                    "checks": checks
                }

        # Reply sentiment check
        elif event.event_type == EventType.EVENT_REPLY:
            reply_text = event.metadata.get("reply_text", "")
            classification = self.rules.classify_reply(reply_text)
            checks.append({
                "check": "reply_sentiment",
                "passed": classification.should_promote,
                "details": classification.reason,
                "sentiment": classification.sentiment.value
            })
            if not classification.should_promote:
                return {
                    "passed": False,
                    "reason": f"Reply not promotable: {classification.reason}",
                    "checks": checks
                }

        # TalentFlow validation
        elif event.event_type == EventType.EVENT_TALENTFLOW_MOVE:
            signal_date = event.metadata.get("signal_date", event.event_ts)
            signal_type = event.metadata.get("signal_type", "job_change")
            validation = self.rules.validate_talentflow_signal(
                signal_type=signal_type,
                signal_date=signal_date
            )
            checks.append({
                "check": "talentflow_validity",
                "passed": validation.is_valid,
                "details": validation.reason
            })
            if not validation.is_valid:
                return {
                    "passed": False,
                    "reason": validation.reason,
                    "checks": checks
                }

        # Re-engagement exhaustion check
        elif event.event_type == EventType.EVENT_REENGAGEMENT_EXHAUSTED:
            status = self.rules.evaluate_reengagement_status(
                current_cycle=contact.reengagement_cycle,
                days_since_last_engagement=event.metadata.get("days_inactive", 0)
            )
            checks.append({
                "check": "reengagement_status",
                "passed": status.is_exhausted,
                "details": status.reason
            })
            if not status.is_exhausted:
                return {
                    "passed": False,
                    "reason": "Re-engagement not exhausted yet",
                    "checks": checks
                }

        # Default: no specific threshold check needed
        return {
            "passed": True,
            "reason": "Event validated",
            "checks": checks
        }

    # =========================================================================
    # TRANSITION RECORDING (PLACEHOLDER)
    # =========================================================================

    def record_transition(
        self,
        decision: TransitionDecision,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TransitionRecord:
        """
        Record a transition decision.

        NOTE: This is a placeholder implementation. In production,
        this would write to the database.

        Args:
            decision: The transition decision
            metadata: Optional additional metadata

        Returns:
            TransitionRecord
        """
        if not decision.should_transition:
            raise ValueError("Cannot record transition for failed decision")

        record = TransitionRecord(
            transition_id=str(uuid.uuid4()),
            company_id=decision.company_id,
            person_id=decision.person_id,
            from_state=decision.from_state,
            to_state=decision.to_state,
            event_type=decision.event_type,
            event_id=decision.event_id,
            event_ts=decision.timestamp,
            transition_ts=datetime.now(),
            validation_checks=decision.validation_checks,
            metadata=metadata or {}
        )

        # Store in memory (placeholder)
        self._transition_records.append(record)

        return record

    # =========================================================================
    # BATCH PROCESSING
    # =========================================================================

    def process_pending_events(
        self,
        contact: ContactState
    ) -> List[TransitionDecision]:
        """
        Process all pending events for a contact.

        Resolves priority conflicts when multiple events would
        trigger transitions.

        Args:
            contact: Contact state

        Returns:
            List of TransitionDecisions (only the winning transition is marked as should_transition)
        """
        person_events = [
            e for e in self._pending_events
            if e.person_id == contact.person_id
        ]

        if not person_events:
            return []

        # Evaluate all events
        decisions = []
        for event in person_events:
            decision = self.evaluate_transition(contact, event)
            decisions.append(decision)

        # Find winning transition
        valid_decisions = [d for d in decisions if d.should_transition]

        if len(valid_decisions) > 1:
            # Resolve priority - highest priority wins
            winning_decision = max(valid_decisions, key=lambda d: d.priority)

            # Mark others as not transitioning
            for d in valid_decisions:
                if d.event_id != winning_decision.event_id:
                    d.should_transition = False
                    d.reason = f"Superseded by higher priority event: {winning_decision.event_type.value}"

        # Clear processed events
        self._pending_events = [
            e for e in self._pending_events
            if e.person_id != contact.person_id
        ]

        return decisions

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def get_allowed_transitions(
        self,
        current_state: str
    ) -> Dict[str, str]:
        """
        Get all allowed transitions from a state.

        Args:
            current_state: Current state as string

        Returns:
            Dict mapping event types to target states
        """
        try:
            state = LifecycleState(current_state)
        except ValueError:
            return {}

        transitions = self.state_machine.get_all_transitions_from(state)
        return {
            event.value: target.value
            for event, target in transitions.items()
        }

    def get_funnel_for_state(self, state: str) -> Optional[str]:
        """
        Get funnel membership for a state.

        Args:
            state: State as string

        Returns:
            Funnel name or None
        """
        try:
            lifecycle_state = LifecycleState(state)
        except ValueError:
            return None

        funnel = self.state_machine.get_funnel_membership(lifecycle_state)
        return funnel.value if funnel else None

    def get_transition_records(self) -> List[TransitionRecord]:
        """
        Get all recorded transitions (placeholder).

        Returns:
            List of TransitionRecords
        """
        return self._transition_records.copy()

    def clear_transition_records(self):
        """Clear recorded transitions (placeholder)."""
        self._transition_records.clear()

    def clear_pending_events(self):
        """Clear pending events queue."""
        self._pending_events.clear()
