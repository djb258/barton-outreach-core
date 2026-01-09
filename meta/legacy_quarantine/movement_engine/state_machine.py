"""
State Machine
=============
Finite State Machine implementation for the 4-Funnel GTM System.

This module defines the valid lifecycle states and transitions per the
doctrine defined in ctb/sys/doctrine/funnel_state_machine.md.

Architecture:
- Pure logic implementation (no database access)
- Immutable state definitions
- Deterministic transition logic

Usage:
    from movement_engine.state_machine import StateMachine, LifecycleState, EventType

    sm = StateMachine()

    # Check if transition is valid
    is_valid = sm.is_valid_transition(
        from_state=LifecycleState.SUSPECT,
        to_state=LifecycleState.WARM,
        event_type=EventType.EVENT_REPLY
    )

    # Get next state for an event
    next_state = sm.get_next_state(
        current_state=LifecycleState.SUSPECT,
        event_type=EventType.EVENT_REPLY
    )
"""

from enum import Enum
from typing import Optional, Dict, List, Set, Tuple
from dataclasses import dataclass


# =============================================================================
# ENUMS
# =============================================================================

class LifecycleState(Enum):
    """
    Lifecycle states for contacts in the 4-Funnel system.

    States map to funnels as follows:
    - SUSPECT -> Funnel 1: Cold Universe
    - WARM -> Funnel 3: Warm Universe
    - TALENTFLOW_WARM -> Funnel 2: TalentFlow Universe
    - REENGAGEMENT -> Funnel 4: Re-Engagement Universe
    - APPOINTMENT -> Sales Pipeline (no funnel)
    - CLIENT -> Customer (terminal state)
    - DISQUALIFIED -> Removed (terminal state)
    - UNSUBSCRIBED -> Opted out (terminal state)
    """
    SUSPECT = "SUSPECT"
    WARM = "WARM"
    TALENTFLOW_WARM = "TALENTFLOW_WARM"
    REENGAGEMENT = "REENGAGEMENT"
    APPOINTMENT = "APPOINTMENT"
    CLIENT = "CLIENT"
    DISQUALIFIED = "DISQUALIFIED"
    UNSUBSCRIBED = "UNSUBSCRIBED"


class EventType(Enum):
    """
    Events that trigger state transitions.

    These events are detected by the MovementEngine and processed
    to determine if a state transition should occur.
    """
    EVENT_REPLY = "EVENT_REPLY"
    EVENT_CLICKS_X2 = "EVENT_CLICKS_X2"
    EVENT_OPENS_X3 = "EVENT_OPENS_X3"
    EVENT_TALENTFLOW_MOVE = "EVENT_TALENTFLOW_MOVE"
    EVENT_BIT_THRESHOLD = "EVENT_BIT_THRESHOLD"
    EVENT_REENGAGEMENT_TRIGGER = "EVENT_REENGAGEMENT_TRIGGER"
    EVENT_APPOINTMENT = "EVENT_APPOINTMENT"
    EVENT_CLIENT_SIGNED = "EVENT_CLIENT_SIGNED"
    EVENT_INACTIVITY_30D = "EVENT_INACTIVITY_30D"
    EVENT_REENGAGEMENT_EXHAUSTED = "EVENT_REENGAGEMENT_EXHAUSTED"
    EVENT_UNSUBSCRIBE = "EVENT_UNSUBSCRIBE"
    EVENT_HARD_BOUNCE = "EVENT_HARD_BOUNCE"
    EVENT_MANUAL_OVERRIDE = "EVENT_MANUAL_OVERRIDE"


class FunnelMembership(Enum):
    """
    Funnel universe membership categories.
    """
    COLD_UNIVERSE = "COLD_UNIVERSE"
    TALENTFLOW_UNIVERSE = "TALENTFLOW_UNIVERSE"
    WARM_UNIVERSE = "WARM_UNIVERSE"
    REENGAGEMENT_UNIVERSE = "REENGAGEMENT_UNIVERSE"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class TransitionResult:
    """
    Result of a state transition evaluation.

    Attributes:
        is_valid: Whether the transition is allowed
        from_state: Starting state
        to_state: Target state (if valid)
        event_type: Event that triggered the evaluation
        reason: Explanation of the result
        priority: Priority of this transition (for conflict resolution)
    """
    is_valid: bool
    from_state: LifecycleState
    to_state: Optional[LifecycleState]
    event_type: EventType
    reason: str
    priority: int = 0


@dataclass
class StateProperties:
    """
    Properties of a lifecycle state.

    Attributes:
        state: The lifecycle state
        funnel: Which funnel this state belongs to
        is_terminal: Whether this state has no outgoing transitions
        allowed_events: Events that can trigger transitions from this state
        priority: Priority for simultaneous event resolution
    """
    state: LifecycleState
    funnel: Optional[FunnelMembership]
    is_terminal: bool
    allowed_events: Set[EventType]
    priority: int


# =============================================================================
# STATE MACHINE
# =============================================================================

class StateMachine:
    """
    Finite State Machine for 4-Funnel lifecycle management.

    This class implements the state machine defined in the doctrine,
    providing methods to validate and execute state transitions.

    Key principles:
    1. A contact can only be in ONE state at a time
    2. Only defined transitions are allowed
    3. Terminal states have no outgoing transitions
    4. Event priority determines which transition wins when multiple events occur
    """

    # =========================================================================
    # TRANSITION TABLE
    # Maps (from_state, event_type) -> to_state
    # =========================================================================

    ALLOWED_TRANSITIONS: Dict[Tuple[LifecycleState, EventType], LifecycleState] = {
        # From SUSPECT
        (LifecycleState.SUSPECT, EventType.EVENT_REPLY): LifecycleState.WARM,
        (LifecycleState.SUSPECT, EventType.EVENT_OPENS_X3): LifecycleState.WARM,
        (LifecycleState.SUSPECT, EventType.EVENT_CLICKS_X2): LifecycleState.WARM,
        (LifecycleState.SUSPECT, EventType.EVENT_BIT_THRESHOLD): LifecycleState.WARM,
        (LifecycleState.SUSPECT, EventType.EVENT_TALENTFLOW_MOVE): LifecycleState.TALENTFLOW_WARM,
        (LifecycleState.SUSPECT, EventType.EVENT_UNSUBSCRIBE): LifecycleState.UNSUBSCRIBED,
        (LifecycleState.SUSPECT, EventType.EVENT_HARD_BOUNCE): LifecycleState.DISQUALIFIED,

        # From WARM
        (LifecycleState.WARM, EventType.EVENT_APPOINTMENT): LifecycleState.APPOINTMENT,
        (LifecycleState.WARM, EventType.EVENT_TALENTFLOW_MOVE): LifecycleState.TALENTFLOW_WARM,
        (LifecycleState.WARM, EventType.EVENT_INACTIVITY_30D): LifecycleState.REENGAGEMENT,
        (LifecycleState.WARM, EventType.EVENT_UNSUBSCRIBE): LifecycleState.UNSUBSCRIBED,
        (LifecycleState.WARM, EventType.EVENT_HARD_BOUNCE): LifecycleState.DISQUALIFIED,

        # From TALENTFLOW_WARM
        (LifecycleState.TALENTFLOW_WARM, EventType.EVENT_APPOINTMENT): LifecycleState.APPOINTMENT,
        (LifecycleState.TALENTFLOW_WARM, EventType.EVENT_INACTIVITY_30D): LifecycleState.REENGAGEMENT,
        (LifecycleState.TALENTFLOW_WARM, EventType.EVENT_UNSUBSCRIBE): LifecycleState.UNSUBSCRIBED,
        (LifecycleState.TALENTFLOW_WARM, EventType.EVENT_HARD_BOUNCE): LifecycleState.DISQUALIFIED,

        # From REENGAGEMENT
        (LifecycleState.REENGAGEMENT, EventType.EVENT_REPLY): LifecycleState.WARM,
        (LifecycleState.REENGAGEMENT, EventType.EVENT_TALENTFLOW_MOVE): LifecycleState.TALENTFLOW_WARM,
        (LifecycleState.REENGAGEMENT, EventType.EVENT_APPOINTMENT): LifecycleState.APPOINTMENT,
        (LifecycleState.REENGAGEMENT, EventType.EVENT_REENGAGEMENT_EXHAUSTED): LifecycleState.SUSPECT,
        (LifecycleState.REENGAGEMENT, EventType.EVENT_UNSUBSCRIBE): LifecycleState.UNSUBSCRIBED,
        (LifecycleState.REENGAGEMENT, EventType.EVENT_HARD_BOUNCE): LifecycleState.DISQUALIFIED,

        # From APPOINTMENT
        (LifecycleState.APPOINTMENT, EventType.EVENT_CLIENT_SIGNED): LifecycleState.CLIENT,
        (LifecycleState.APPOINTMENT, EventType.EVENT_INACTIVITY_30D): LifecycleState.REENGAGEMENT,
        (LifecycleState.APPOINTMENT, EventType.EVENT_UNSUBSCRIBE): LifecycleState.UNSUBSCRIBED,

        # CLIENT, DISQUALIFIED, UNSUBSCRIBED are terminal - no outgoing transitions
    }

    # =========================================================================
    # EVENT PRIORITIES (higher = more important)
    # Used for conflict resolution when multiple events occur simultaneously
    # =========================================================================

    EVENT_PRIORITIES: Dict[EventType, int] = {
        EventType.EVENT_CLIENT_SIGNED: 100,
        EventType.EVENT_APPOINTMENT: 90,
        EventType.EVENT_TALENTFLOW_MOVE: 80,
        EventType.EVENT_REPLY: 70,
        EventType.EVENT_BIT_THRESHOLD: 60,
        EventType.EVENT_CLICKS_X2: 50,
        EventType.EVENT_OPENS_X3: 40,
        EventType.EVENT_REENGAGEMENT_TRIGGER: 30,
        EventType.EVENT_INACTIVITY_30D: 20,
        EventType.EVENT_REENGAGEMENT_EXHAUSTED: 10,
        EventType.EVENT_UNSUBSCRIBE: 95,  # High priority for compliance
        EventType.EVENT_HARD_BOUNCE: 95,  # High priority for deliverability
        EventType.EVENT_MANUAL_OVERRIDE: 100,  # Admin override always wins
    }

    # =========================================================================
    # STATE PROPERTIES
    # =========================================================================

    STATE_PROPERTIES: Dict[LifecycleState, StateProperties] = {
        LifecycleState.SUSPECT: StateProperties(
            state=LifecycleState.SUSPECT,
            funnel=FunnelMembership.COLD_UNIVERSE,
            is_terminal=False,
            allowed_events={
                EventType.EVENT_REPLY,
                EventType.EVENT_OPENS_X3,
                EventType.EVENT_CLICKS_X2,
                EventType.EVENT_BIT_THRESHOLD,
                EventType.EVENT_TALENTFLOW_MOVE,
                EventType.EVENT_UNSUBSCRIBE,
                EventType.EVENT_HARD_BOUNCE,
            },
            priority=10
        ),
        LifecycleState.WARM: StateProperties(
            state=LifecycleState.WARM,
            funnel=FunnelMembership.WARM_UNIVERSE,
            is_terminal=False,
            allowed_events={
                EventType.EVENT_APPOINTMENT,
                EventType.EVENT_TALENTFLOW_MOVE,
                EventType.EVENT_INACTIVITY_30D,
                EventType.EVENT_UNSUBSCRIBE,
                EventType.EVENT_HARD_BOUNCE,
            },
            priority=30
        ),
        LifecycleState.TALENTFLOW_WARM: StateProperties(
            state=LifecycleState.TALENTFLOW_WARM,
            funnel=FunnelMembership.TALENTFLOW_UNIVERSE,
            is_terminal=False,
            allowed_events={
                EventType.EVENT_APPOINTMENT,
                EventType.EVENT_INACTIVITY_30D,
                EventType.EVENT_UNSUBSCRIBE,
                EventType.EVENT_HARD_BOUNCE,
            },
            priority=40
        ),
        LifecycleState.REENGAGEMENT: StateProperties(
            state=LifecycleState.REENGAGEMENT,
            funnel=FunnelMembership.REENGAGEMENT_UNIVERSE,
            is_terminal=False,
            allowed_events={
                EventType.EVENT_REPLY,
                EventType.EVENT_TALENTFLOW_MOVE,
                EventType.EVENT_APPOINTMENT,
                EventType.EVENT_REENGAGEMENT_EXHAUSTED,
                EventType.EVENT_UNSUBSCRIBE,
                EventType.EVENT_HARD_BOUNCE,
            },
            priority=20
        ),
        LifecycleState.APPOINTMENT: StateProperties(
            state=LifecycleState.APPOINTMENT,
            funnel=None,  # Sales pipeline, not a funnel
            is_terminal=False,
            allowed_events={
                EventType.EVENT_CLIENT_SIGNED,
                EventType.EVENT_INACTIVITY_30D,
                EventType.EVENT_UNSUBSCRIBE,
            },
            priority=50
        ),
        LifecycleState.CLIENT: StateProperties(
            state=LifecycleState.CLIENT,
            funnel=None,  # Customer, not a funnel
            is_terminal=True,
            allowed_events=set(),  # No events allowed - terminal state
            priority=100
        ),
        LifecycleState.DISQUALIFIED: StateProperties(
            state=LifecycleState.DISQUALIFIED,
            funnel=None,
            is_terminal=True,
            allowed_events=set(),
            priority=0
        ),
        LifecycleState.UNSUBSCRIBED: StateProperties(
            state=LifecycleState.UNSUBSCRIBED,
            funnel=None,
            is_terminal=True,
            allowed_events=set(),
            priority=0
        ),
    }

    def __init__(self):
        """Initialize the state machine."""
        pass

    # =========================================================================
    # PUBLIC METHODS
    # =========================================================================

    def get_next_state(
        self,
        current_state: LifecycleState,
        event_type: EventType
    ) -> Optional[LifecycleState]:
        """
        Determine the next state for a given event.

        Args:
            current_state: Current lifecycle state
            event_type: Event that occurred

        Returns:
            Next state if transition is valid, None otherwise
        """
        # Manual override can transition to any state - handled separately
        if event_type == EventType.EVENT_MANUAL_OVERRIDE:
            return None  # Caller must specify target state

        key = (current_state, event_type)
        return self.ALLOWED_TRANSITIONS.get(key)

    def is_valid_transition(
        self,
        from_state: LifecycleState,
        to_state: LifecycleState,
        event_type: EventType
    ) -> bool:
        """
        Check if a transition is valid.

        Args:
            from_state: Starting state
            to_state: Target state
            event_type: Event triggering the transition

        Returns:
            True if transition is allowed, False otherwise
        """
        # Manual override allows any transition (except from terminal states)
        if event_type == EventType.EVENT_MANUAL_OVERRIDE:
            return not self.is_terminal_state(from_state)

        # Check transition table
        key = (from_state, event_type)
        expected_to_state = self.ALLOWED_TRANSITIONS.get(key)

        return expected_to_state == to_state

    def evaluate_transition(
        self,
        current_state: LifecycleState,
        event_type: EventType
    ) -> TransitionResult:
        """
        Evaluate a potential transition and return detailed result.

        Args:
            current_state: Current lifecycle state
            event_type: Event that occurred

        Returns:
            TransitionResult with validation details
        """
        # Check if current state is terminal
        if self.is_terminal_state(current_state):
            return TransitionResult(
                is_valid=False,
                from_state=current_state,
                to_state=None,
                event_type=event_type,
                reason=f"Cannot transition from terminal state {current_state.value}",
                priority=0
            )

        # Check if event is allowed for this state
        state_props = self.STATE_PROPERTIES.get(current_state)
        if state_props and event_type not in state_props.allowed_events:
            return TransitionResult(
                is_valid=False,
                from_state=current_state,
                to_state=None,
                event_type=event_type,
                reason=f"Event {event_type.value} not allowed in state {current_state.value}",
                priority=0
            )

        # Get the target state
        next_state = self.get_next_state(current_state, event_type)

        if next_state is None:
            return TransitionResult(
                is_valid=False,
                from_state=current_state,
                to_state=None,
                event_type=event_type,
                reason=f"No transition defined for {current_state.value} + {event_type.value}",
                priority=0
            )

        return TransitionResult(
            is_valid=True,
            from_state=current_state,
            to_state=next_state,
            event_type=event_type,
            reason=f"Valid transition: {current_state.value} -> {next_state.value}",
            priority=self.EVENT_PRIORITIES.get(event_type, 0)
        )

    def get_allowed_events(self, state: LifecycleState) -> Set[EventType]:
        """
        Get all events that can trigger transitions from a state.

        Args:
            state: The lifecycle state

        Returns:
            Set of allowed event types
        """
        state_props = self.STATE_PROPERTIES.get(state)
        if state_props:
            return state_props.allowed_events.copy()
        return set()

    def get_funnel_membership(self, state: LifecycleState) -> Optional[FunnelMembership]:
        """
        Get the funnel membership for a state.

        Args:
            state: The lifecycle state

        Returns:
            Funnel membership or None if not in a funnel
        """
        state_props = self.STATE_PROPERTIES.get(state)
        if state_props:
            return state_props.funnel
        return None

    def is_terminal_state(self, state: LifecycleState) -> bool:
        """
        Check if a state is terminal (no outgoing transitions).

        Args:
            state: The lifecycle state

        Returns:
            True if terminal, False otherwise
        """
        state_props = self.STATE_PROPERTIES.get(state)
        if state_props:
            return state_props.is_terminal
        return False

    def get_event_priority(self, event_type: EventType) -> int:
        """
        Get the priority of an event type.

        Args:
            event_type: The event type

        Returns:
            Priority value (higher = more important)
        """
        return self.EVENT_PRIORITIES.get(event_type, 0)

    def resolve_event_priority(self, events: List[EventType]) -> EventType:
        """
        Resolve which event should take priority when multiple occur.

        Args:
            events: List of events that occurred simultaneously

        Returns:
            The highest-priority event
        """
        if not events:
            raise ValueError("No events provided")

        return max(events, key=lambda e: self.EVENT_PRIORITIES.get(e, 0))

    def get_all_transitions_from(self, state: LifecycleState) -> Dict[EventType, LifecycleState]:
        """
        Get all possible transitions from a state.

        Args:
            state: The starting state

        Returns:
            Dict mapping event types to target states
        """
        transitions = {}
        for (from_state, event_type), to_state in self.ALLOWED_TRANSITIONS.items():
            if from_state == state:
                transitions[event_type] = to_state
        return transitions

    def get_all_transitions_to(self, state: LifecycleState) -> Dict[Tuple[LifecycleState, EventType], LifecycleState]:
        """
        Get all transitions that lead to a state.

        Args:
            state: The target state

        Returns:
            Dict mapping (from_state, event_type) to the target state
        """
        transitions = {}
        for (from_state, event_type), to_state in self.ALLOWED_TRANSITIONS.items():
            if to_state == state:
                transitions[(from_state, event_type)] = to_state
        return transitions

    def get_state_priority(self, state: LifecycleState) -> int:
        """
        Get the priority of a state (for funnel membership resolution).

        Args:
            state: The lifecycle state

        Returns:
            Priority value
        """
        state_props = self.STATE_PROPERTIES.get(state)
        if state_props:
            return state_props.priority
        return 0
