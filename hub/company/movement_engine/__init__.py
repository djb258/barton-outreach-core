"""
Movement Engine
===============

Core engine for 4-Funnel GTM System state transitions.

This module provides:
- StateMachine: Finite state machine for lifecycle states
- MovementRules: Business rules for engagement classification
- MovementEngine: Main orchestrator for event detection and transitions

Usage:
    from pipeline_engine.movement_engine import (
        MovementEngine,
        StateMachine,
        MovementRules,
        LifecycleState,
        EventType,
        FunnelMembership
    )

    # Create engine
    engine = MovementEngine()

    # Detect an event
    event = engine.detect_event(
        company_id="uuid-123",
        person_id="uuid-456",
        event_type="email_reply",
        metadata={"reply_text": "I'm interested!"}
    )

    # Determine next state
    result = engine.determine_next_state(
        current_state="SUSPECT",
        event_type="EVENT_REPLY"
    )

Doctrine Reference:
    - ctb/sys/doctrine/4_funnel_doctrine.md
    - ctb/sys/doctrine/funnel_state_machine.md
    - ctb/sys/doctrine/funnel_rules.md

Database Schema:
    - neon/migrations/0001-0010 (funnel schema)
"""

from .state_machine import (
    StateMachine,
    LifecycleState,
    EventType,
    FunnelMembership,
    TransitionResult,
    StateProperties
)

from .movement_rules import (
    MovementRules,
    MovementRulesConfig,
    ReplySentiment,
    TalentFlowSignalType,
    ReplyClassification,
    ThresholdResult,
    BITScoreResult,
    TalentFlowValidation,
    ReengagementStatus,
    CooldownStatus
)

from .movement_engine import (
    MovementEngine,
    ContactState,
    DetectedEvent,
    TransitionDecision,
    TransitionRecord
)

__all__ = [
    # State Machine
    "StateMachine",
    "LifecycleState",
    "EventType",
    "FunnelMembership",
    "TransitionResult",
    "StateProperties",

    # Movement Rules
    "MovementRules",
    "MovementRulesConfig",
    "ReplySentiment",
    "TalentFlowSignalType",
    "ReplyClassification",
    "ThresholdResult",
    "BITScoreResult",
    "TalentFlowValidation",
    "ReengagementStatus",
    "CooldownStatus",

    # Movement Engine
    "MovementEngine",
    "ContactState",
    "DetectedEvent",
    "TransitionDecision",
    "TransitionRecord",
]

__version__ = "1.0.0"
