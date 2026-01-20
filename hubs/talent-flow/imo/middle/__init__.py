"""
Talent Flow Middle Layer - Movement Detection
=============================================

Core business logic for detecting executive movements.

Movement Types:
    - JOINED: Person joined the target company
    - LEFT: Person left the target company
    - TITLE_CHANGE: Person changed titles at the company
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid
import logging

from ..input import PersonRecord


logger = logging.getLogger(__name__)


class MovementType(Enum):
    """Types of detected movements."""
    JOINED = "joined"
    LEFT = "left"
    TITLE_CHANGE = "title_change"


# Signal impacts per movement type (per BIT engine spec)
MOVEMENT_IMPACTS: Dict[MovementType, int] = {
    MovementType.JOINED: 10,
    MovementType.LEFT: -5,
    MovementType.TITLE_CHANGE: 3,
}


@dataclass
class MovementEvent:
    """
    Detected movement event.
    
    This is the primary output of the movement detection engine.
    """
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    company_unique_id: uuid.UUID = None
    person_id: uuid.UUID = None
    event_type: MovementType = None
    from_company: Optional[str] = None
    to_company: Optional[str] = None
    from_title: Optional[str] = None
    to_title: Optional[str] = None
    detected_at: datetime = field(default_factory=datetime.now)
    confidence: float = 0.0
    signal_value: int = 0
    
    def __post_init__(self):
        """Calculate signal value based on movement type."""
        if self.event_type and self.signal_value == 0:
            self.signal_value = MOVEMENT_IMPACTS.get(self.event_type, 0)


class MovementDetector:
    """
    Movement detection engine.
    
    Compares current person records against historical data to detect:
    - New executives joining the company
    - Executives leaving the company
    - Title changes (promotions, lateral moves)
    
    Doctrine Compliance:
        - Business logic lives in middle layer only
        - Takes clean input from input layer
        - Produces clean events for output layer
        - Does NOT access database directly
    """
    
    def __init__(self, confidence_threshold: float = 0.7):
        """
        Initialize the detector.
        
        Args:
            confidence_threshold: Minimum confidence to emit an event
        """
        self.confidence_threshold = confidence_threshold
        self._historical_cache: Dict[uuid.UUID, Dict[str, Any]] = {}
    
    def detect_movements(
        self, 
        current_records: List[PersonRecord],
        historical_records: List[PersonRecord]
    ) -> List[MovementEvent]:
        """
        Detect movements by comparing current vs historical records.
        
        Args:
            current_records: Current person records from People Intelligence
            historical_records: Previous snapshot for comparison
            
        Returns:
            List of detected MovementEvent objects
        """
        events = []
        
        # Build lookup maps
        current_by_person = {r.person_id: r for r in current_records}
        historical_by_person = {r.person_id: r for r in historical_records}
        
        # Detect JOIN and TITLE_CHANGE
        for person_id, current in current_by_person.items():
            historical = historical_by_person.get(person_id)
            
            if historical is None:
                # New person - JOINED
                event = self._detect_join(current)
                if event and event.confidence >= self.confidence_threshold:
                    events.append(event)
            else:
                # Existing person - check for title change
                event = self._detect_title_change(current, historical)
                if event and event.confidence >= self.confidence_threshold:
                    events.append(event)
        
        # Detect LEFT
        for person_id, historical in historical_by_person.items():
            if person_id not in current_by_person:
                event = self._detect_departure(historical)
                if event and event.confidence >= self.confidence_threshold:
                    events.append(event)
        
        logger.info(f"Detected {len(events)} movements")
        return events
    
    def _detect_join(self, record: PersonRecord) -> Optional[MovementEvent]:
        """Detect a join event."""
        return MovementEvent(
            company_unique_id=record.company_unique_id,
            person_id=record.person_id,
            event_type=MovementType.JOINED,
            from_company=record.previous_company,
            to_company=record.current_company,
            to_title=record.current_title,
            confidence=0.85 if record.linkedin_url else 0.60
        )
    
    def _detect_departure(self, record: PersonRecord) -> Optional[MovementEvent]:
        """Detect a departure event."""
        return MovementEvent(
            company_unique_id=record.company_unique_id,
            person_id=record.person_id,
            event_type=MovementType.LEFT,
            from_company=record.current_company,
            from_title=record.current_title,
            confidence=0.80  # High confidence if person disappeared
        )
    
    def _detect_title_change(
        self, 
        current: PersonRecord, 
        historical: PersonRecord
    ) -> Optional[MovementEvent]:
        """Detect a title change event."""
        if current.current_title == historical.current_title:
            return None
        
        return MovementEvent(
            company_unique_id=current.company_unique_id,
            person_id=current.person_id,
            event_type=MovementType.TITLE_CHANGE,
            from_title=historical.current_title,
            to_title=current.current_title,
            confidence=0.90  # High confidence if title changed
        )


from .hub_status import (
    TalentFlowHubStatusResult,
    compute_talent_flow_hub_status,
    backfill_talent_flow_hub_status,
    generate_movement_signal_hash,
    FRESHNESS_DAYS,
    MIN_MOVEMENTS,
    CONFIDENCE_THRESHOLD,
)


__all__ = [
    'MovementType',
    'MovementEvent',
    'MovementDetector',
    'MOVEMENT_IMPACTS',
    # Hub status computation
    'TalentFlowHubStatusResult',
    'compute_talent_flow_hub_status',
    'backfill_talent_flow_hub_status',
    'generate_movement_signal_hash',
    'FRESHNESS_DAYS',
    'MIN_MOVEMENTS',
    'CONFIDENCE_THRESHOLD',
]
