"""
People State Initializer
========================
Bridges ingest → movement engine for initial state assignment.

Key Responsibilities:
- Initialize funnel state from ingest classification
- Record initial transition to Movement Engine
- Bypass cooldown for initial ingest (cannot be blocked)
- Force initial state assignment (movement engine cannot veto)
- Emit MOVEMENT_TRANSITION events to logging

This module connects Phase 0 (People Ingest) output to the Movement Engine,
ensuring that newly ingested people are properly initialized in the funnel system.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime

from .movement_engine import (
    MovementEngine,
    LifecycleState,
    EventType,
    ContactState,
    TransitionRecord
)
from .phases.phase0_people_ingest import PeopleIngestResult, IngestEvent
from .utils.logging import PipelineLogger, EventType as LogEventType


@dataclass
class PeopleStateInitializationResult:
    """Result of initializing a person's funnel state."""
    person_id: str
    company_id: Optional[str]
    initial_state: LifecycleState
    initialized_at: datetime
    bypass_cooldown: bool = True  # Initial ingest cannot be blocked
    forced_assignment: bool = True  # Movement engine cannot veto
    transition_recorded: bool = False
    events_emitted: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'person_id': self.person_id,
            'company_id': self.company_id,
            'initial_state': self.initial_state.value,
            'initialized_at': self.initialized_at.isoformat(),
            'bypass_cooldown': self.bypass_cooldown,
            'forced_assignment': self.forced_assignment,
            'transition_recorded': self.transition_recorded,
            'events_emitted': self.events_emitted,
            'metadata': self.metadata
        }


class PeopleStateInitializer:
    """
    Bridge between People Ingest (Phase 0) and Movement Engine.

    Handles initial state assignment for newly ingested people:
    - Determines current_state from ingest classification
    - Records transition placeholder to Movement Engine
    - Bypasses cooldown (initial ingest cannot be blocked)
    - Forces state assignment (movement engine cannot veto initial state)
    - Emits MOVEMENT_TRANSITION events to logging system

    Usage:
        from pipeline_engine.people_state_initializer import PeopleStateInitializer
        from pipeline_engine.movement_engine import MovementEngine

        engine = MovementEngine()
        initializer = PeopleStateInitializer(movement_engine=engine)

        # Initialize state from ingest result
        init_result = initializer.initialize_state(ingest_result)
    """

    def __init__(
        self,
        movement_engine: MovementEngine,
        logger: PipelineLogger = None,
        config: Dict[str, Any] = None
    ):
        """
        Initialize the People State Initializer.

        Args:
            movement_engine: Movement Engine instance for state transitions
            logger: Optional pipeline logger for event tracking
            config: Configuration dictionary
        """
        self.movement_engine = movement_engine
        self.logger = logger
        self.config = config or {}

    def initialize_state(
        self,
        ingest_result: PeopleIngestResult
    ) -> PeopleStateInitializationResult:
        """
        Initialize funnel state from ingest classification.

        This method:
        1. Determines current_state from ingest result
        2. Records transition placeholder to Movement Engine
        3. Bypasses cooldown (initial ingest cannot be blocked)
        4. Forces state assignment
        5. Emits MOVEMENT_TRANSITION event

        Args:
            ingest_result: Classification result from Phase 0

        Returns:
            PeopleStateInitializationResult
        """
        now = datetime.now()
        events_emitted = []

        # Get initial state from ingest classification
        initial_state = ingest_result.initial_funnel_state

        # Build result
        result = PeopleStateInitializationResult(
            person_id=ingest_result.person_id,
            company_id=ingest_result.company_id,
            initial_state=initial_state,
            initialized_at=now,
            bypass_cooldown=True,
            forced_assignment=True,
            metadata={
                'classification_reason': ingest_result.classification_reason,
                'slot_candidate': ingest_result.slot_candidate,
                'ingest_events': [e.to_dict() for e in ingest_result.ingest_events]
            }
        )

        # Record transition placeholder (no actual DB write yet)
        # Movement Engine stores this in memory
        try:
            self._record_initial_transition(
                person_id=ingest_result.person_id,
                company_id=ingest_result.company_id,
                initial_state=initial_state,
                ingest_events=ingest_result.ingest_events,
                classification_reason=ingest_result.classification_reason
            )
            result.transition_recorded = True
            events_emitted.append('TRANSITION_RECORDED')
        except Exception as e:
            result.metadata['transition_error'] = str(e)

        # Emit MOVEMENT_TRANSITION event to logging
        if self.logger:
            self._emit_movement_transition_event(
                person_id=ingest_result.person_id,
                company_id=ingest_result.company_id,
                initial_state=initial_state,
                classification_reason=ingest_result.classification_reason
            )
            events_emitted.append('MOVEMENT_TRANSITION_LOGGED')

        result.events_emitted = events_emitted
        return result

    def initialize_batch(
        self,
        ingest_results: List[PeopleIngestResult]
    ) -> List[PeopleStateInitializationResult]:
        """
        Initialize state for multiple people.

        Args:
            ingest_results: List of ingest classification results

        Returns:
            List of initialization results
        """
        results = []
        for ingest_result in ingest_results:
            result = self.initialize_state(ingest_result)
            results.append(result)
        return results

    def _record_initial_transition(
        self,
        person_id: str,
        company_id: Optional[str],
        initial_state: LifecycleState,
        ingest_events: List[IngestEvent],
        classification_reason: str
    ) -> None:
        """
        Record initial transition to Movement Engine.

        This is a placeholder call - Movement Engine stores in memory.
        No actual database writes occur in this implementation.

        Args:
            person_id: Person unique ID
            company_id: Company anchor ID
            initial_state: Initial funnel state
            ingest_events: Events detected during ingest
            classification_reason: Reason for classification
        """
        # Determine event type based on initial state
        event_type = self._map_state_to_event_type(initial_state)

        # Detect event in Movement Engine (records to pending events)
        if company_id:
            self.movement_engine.detect_event(
                company_id=company_id,
                person_id=person_id,
                event_type=event_type,
                metadata={
                    'is_initial_ingest': True,
                    'classification_reason': classification_reason,
                    'bypass_cooldown': True,
                    'forced_assignment': True,
                    'ingest_events': [e.event_type.value for e in ingest_events]
                }
            )

    def _map_state_to_event_type(self, state: LifecycleState) -> str:
        """
        Map initial state to corresponding event type for Movement Engine.

        Args:
            state: Initial lifecycle state

        Returns:
            Event type string for Movement Engine
        """
        state_to_event = {
            LifecycleState.SUSPECT: 'initial_ingest',
            LifecycleState.WARM: 'reply',  # Historical reply detected
            LifecycleState.TALENTFLOW_WARM: 'talentflow_move',
            LifecycleState.APPOINTMENT: 'appointment',
            LifecycleState.REENGAGEMENT: 'inactivity'
        }
        return state_to_event.get(state, 'initial_ingest')

    def _emit_movement_transition_event(
        self,
        person_id: str,
        company_id: Optional[str],
        initial_state: LifecycleState,
        classification_reason: str
    ) -> None:
        """
        Emit MOVEMENT_TRANSITION event to logging system.

        Args:
            person_id: Person unique ID
            company_id: Company anchor ID
            initial_state: Initial funnel state
            classification_reason: Reason for classification
        """
        if self.logger:
            # Use the logging system's movement_transition method
            self.logger.log_movement_transition(
                company_id=company_id or 'UNANCHORED',
                person_id=person_id,
                from_state='NONE',  # No prior state for initial ingest
                to_state=initial_state.value,
                event_type='INITIAL_INGEST',
                reason=classification_reason
            )

    def get_initial_contact_state(
        self,
        ingest_result: PeopleIngestResult
    ) -> ContactState:
        """
        Build a ContactState object for a newly ingested person.

        Useful for immediate processing through Movement Engine
        after initial ingest.

        Args:
            ingest_result: Classification result from Phase 0

        Returns:
            ContactState ready for Movement Engine processing
        """
        # Get BIT score if available
        bit_score = 0
        for event in ingest_result.ingest_events:
            if event.event_type.value == 'bit_threshold_met':
                bit_score = event.metadata.get('bit_score', 0)
                break

        return ContactState(
            company_id=ingest_result.company_id or 'UNANCHORED',
            person_id=ingest_result.person_id,
            email='',  # Not yet generated (Phase 5)
            current_state=ingest_result.initial_funnel_state,
            funnel_membership=self.movement_engine.state_machine.get_funnel_membership(
                ingest_result.initial_funnel_state
            ),
            last_event_ts=datetime.now(),
            last_state_change_ts=datetime.now(),
            current_bit_score=bit_score,
            is_locked=False,
            cooldown_until=None  # No cooldown for initial ingest
        )


def initialize_people_state(
    ingest_results: List[PeopleIngestResult],
    movement_engine: MovementEngine,
    logger: PipelineLogger = None,
    config: Dict[str, Any] = None
) -> List[PeopleStateInitializationResult]:
    """
    Convenience function to initialize state for multiple people.

    Args:
        ingest_results: List of ingest classification results
        movement_engine: Movement Engine instance
        logger: Optional pipeline logger
        config: Optional configuration

    Returns:
        List of initialization results
    """
    initializer = PeopleStateInitializer(
        movement_engine=movement_engine,
        logger=logger,
        config=config
    )
    return initializer.initialize_batch(ingest_results)
