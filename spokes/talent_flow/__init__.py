"""
Talent Flow Node - Spoke #4
===========================
Executive movement detection and tracking.

Signals to BIT Engine:
    - EXECUTIVE_JOINED: +10 per new hire/transfer in
    - EXECUTIVE_LEFT: -5 per departure
    - TITLE_CHANGE: +3 per promotion/lateral move

Tools:
    - Tool 16: Movement Detection Engine

Barton ID Range: 04.04.02.04.60000.###
"""

from .talent_flow_spoke import (
    # Main spoke
    TalentFlowSpoke,
    TalentFlowConfig,
    load_talent_flow_config,
    # Detector (Tool 16)
    MovementDetector,
    # Enums
    MovementType,
    TitleLevel,
    # Data classes
    PersonSnapshot,
    DetectedMovement,
    # Constants
    MOVEMENT_IMPACTS,
    MOVEMENT_TO_SIGNAL,
    TITLE_LEVEL_KEYWORDS,
)


__all__ = [
    # Main spoke
    "TalentFlowSpoke",
    "TalentFlowConfig",
    "load_talent_flow_config",
    # Detector (Tool 16)
    "MovementDetector",
    # Enums
    "MovementType",
    "TitleLevel",
    # Data classes
    "PersonSnapshot",
    "DetectedMovement",
    # Constants
    "MOVEMENT_IMPACTS",
    "MOVEMENT_TO_SIGNAL",
    "TITLE_LEVEL_KEYWORDS",
]
