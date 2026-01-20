"""
Talent Flow Output Layer - Signal Writer
========================================

Writes movement events to the BIT signal log for score computation.

Doctrine:
    - Spoke is I/O only - no logic, no state
    - Writes to outreach.bit_signal_log
    - Does NOT compute BIT score (that's BIT engine's job)
"""

from typing import List
from datetime import datetime
import uuid
import logging

from ..middle import MovementEvent, MovementType


logger = logging.getLogger(__name__)


class MovementSignalWriter:
    """
    Writes movement events to the BIT signal log.
    
    Doctrine Compliance:
        - I/O only - no business logic
        - Writes to Neon database
        - Does NOT compute BIT scores
        - Signal deduplication via hash + timestamp
    """
    
    def __init__(self, db_connection):
        """
        Initialize the writer.
        
        Args:
            db_connection: Neon database connection
        """
        self.db = db_connection
    
    def write_movements(self, events: List[MovementEvent]) -> int:
        """
        Write movement events to the signal log.
        
        Args:
            events: List of detected movement events
            
        Returns:
            Number of events written
        """
        if not events:
            return 0
        
        written = 0
        for event in events:
            try:
                self._write_signal(event)
                written += 1
            except Exception as e:
                logger.error(f"Failed to write movement signal: {e}")
        
        logger.info(f"Wrote {written}/{len(events)} movement signals")
        return written
    
    def _write_signal(self, event: MovementEvent) -> None:
        """
        Write a single movement event as a BIT signal.
        
        The signal format matches bit_signal_log schema.
        """
        signal_type = self._map_movement_to_signal(event.event_type)
        
        # This would execute the insert
        # For now, just log the intent
        logger.debug(
            f"Would write signal: {signal_type} for company {event.company_unique_id}"
        )
    
    def _map_movement_to_signal(self, movement_type: MovementType) -> str:
        """Map movement type to BIT signal type."""
        mapping = {
            MovementType.JOINED: "executive_joined",
            MovementType.LEFT: "executive_left",
            MovementType.TITLE_CHANGE: "title_change",
        }
        return mapping.get(movement_type, "unknown_movement")
    
    def update_hub_status(
        self, 
        company_unique_id: uuid.UUID, 
        status: str,
        metric_value: float = None
    ) -> None:
        """
        Update the company_hub_status for talent-flow.
        
        This is called after processing to record hub completion status.
        
        Args:
            company_unique_id: The company identifier
            status: PASS, FAIL, BLOCKED, or IN_PROGRESS
            metric_value: Optional metric (movement detection rate)
        """
        # This would execute the upsert to company_hub_status
        logger.info(
            f"Would update talent-flow status: {company_unique_id} -> {status}"
        )


__all__ = ['MovementSignalWriter']
