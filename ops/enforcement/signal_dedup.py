"""
Signal Idempotency Enforcement Module
=====================================
DOCTRINE: Signals must be deduplicated within time windows.
- 24h window for operational signals (People Spoke)
- 365d window for structural signals (DOL, executive changes)

Mechanism:
- Deterministic hash: (signal_type + entity_id + window_start)
- Lookup table for deduplication
- Duplicate signal → ignored, no score impact

No probabilistic logic. No ML. No guessing.
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock

logger = logging.getLogger(__name__)


class DuplicateSignalError(Exception):
    """
    Raised when a duplicate signal is detected.

    This is NOT a fail-hard condition - duplicates are silently dropped.
    This exception is only raised if explicitly requested for debugging.
    """

    def __init__(self, message: str, dedup_key: str, original_timestamp: datetime):
        self.message = message
        self.dedup_key = dedup_key
        self.original_timestamp = original_timestamp
        super().__init__(self.message)


class SignalWindow(Enum):
    """Signal deduplication window types."""
    OPERATIONAL = "operational"   # 24-hour window
    STRUCTURAL = "structural"     # 365-day window


# Signal type to window mapping per PRD
SIGNAL_WINDOWS: Dict[str, SignalWindow] = {
    # Operational signals (24h)
    "SLOT_FILLED": SignalWindow.OPERATIONAL,
    "SLOT_VACATED": SignalWindow.OPERATIONAL,
    "EMAIL_VERIFIED": SignalWindow.OPERATIONAL,
    "EMAIL_GENERATED": SignalWindow.OPERATIONAL,
    "LINKEDIN_FOUND": SignalWindow.OPERATIONAL,
    "PERSON_CLASSIFIED": SignalWindow.OPERATIONAL,

    # Structural signals (365d)
    "FORM_5500_FILED": SignalWindow.STRUCTURAL,
    "LARGE_PLAN": SignalWindow.STRUCTURAL,
    "BROKER_CHANGE": SignalWindow.STRUCTURAL,
    "EXECUTIVE_JOINED": SignalWindow.STRUCTURAL,
    "EXECUTIVE_LEFT": SignalWindow.STRUCTURAL,
    "COMPANY_MATCHED": SignalWindow.STRUCTURAL,
}

# Window durations in hours
WINDOW_HOURS: Dict[SignalWindow, int] = {
    SignalWindow.OPERATIONAL: 24,
    SignalWindow.STRUCTURAL: 365 * 24,  # 365 days
}


@dataclass
class DedupEntry:
    """Entry in the deduplication cache."""
    dedup_key: str
    signal_type: str
    entity_id: str
    first_seen: datetime
    window_end: datetime
    count: int = 1


class SignalDeduplicator:
    """
    Signal deduplication service.

    Provides deterministic deduplication based on signal type, entity ID,
    and time window. Thread-safe for concurrent access.

    Usage:
        dedup = SignalDeduplicator()

        # Check before emitting signal
        if dedup.should_emit("SLOT_FILLED", "C001:P001"):
            bit_engine.emit_signal(...)
            dedup.record_emission("SLOT_FILLED", "C001:P001")
        else:
            logger.debug("Duplicate signal dropped")
    """

    def __init__(self, use_persistence: bool = False, db_connection=None):
        """
        Initialize deduplicator.

        Args:
            use_persistence: If True, use database for persistence (production)
                           If False, use in-memory cache (testing/development)
            db_connection: Database connection for persistent mode
        """
        self._cache: Dict[str, DedupEntry] = {}
        self._lock = Lock()
        self._use_persistence = use_persistence
        self._db = db_connection
        self._stats = {
            'signals_checked': 0,
            'signals_allowed': 0,
            'signals_blocked': 0,
        }

    def should_emit(
        self,
        signal_type: str,
        entity_id: str,
        correlation_id: Optional[str] = None,
        check_only: bool = False
    ) -> bool:
        """
        Check if a signal should be emitted (not a duplicate).

        DETERMINISTIC LOGIC:
        1. Get window type for signal_type (24h or 365d)
        2. Calculate window_start = floor(now / window_size)
        3. Generate dedup_key = hash(signal_type + entity_id + window_start)
        4. Check if dedup_key exists in cache/db
        5. If exists → return False (duplicate)
        6. If not exists → return True (allow emission)

        Args:
            signal_type: Type of signal (e.g., "SLOT_FILLED", "FORM_5500_FILED")
            entity_id: Entity identifier (e.g., "C001:P001" for company:person)
            correlation_id: Optional correlation ID for logging
            check_only: If True, don't record the emission (dry run)

        Returns:
            True if signal should be emitted, False if duplicate
        """
        self._stats['signals_checked'] += 1

        # Get window type
        window = SIGNAL_WINDOWS.get(signal_type, SignalWindow.OPERATIONAL)
        window_hours = WINDOW_HOURS[window]

        # Calculate deterministic window start
        now = datetime.utcnow()
        window_start = self._calculate_window_start(now, window_hours)

        # Generate deterministic dedup key
        dedup_key = self._generate_dedup_key(signal_type, entity_id, window_start)

        with self._lock:
            # Check cache
            if self._use_persistence and self._db:
                exists = self._check_db(dedup_key)
            else:
                exists = dedup_key in self._cache

            if exists:
                self._stats['signals_blocked'] += 1
                logger.debug(
                    f"Duplicate signal blocked: {signal_type} for {entity_id} "
                    f"(dedup_key: {dedup_key[:16]}..., correlation: {correlation_id})"
                )
                return False

            # Record emission if not check_only
            if not check_only:
                self._record_internal(
                    dedup_key=dedup_key,
                    signal_type=signal_type,
                    entity_id=entity_id,
                    window_start=window_start,
                    window_hours=window_hours
                )

            self._stats['signals_allowed'] += 1
            return True

    def record_emission(
        self,
        signal_type: str,
        entity_id: str,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Record a signal emission for deduplication.

        Call this AFTER successfully emitting a signal if you used
        should_emit() with check_only=True.

        Args:
            signal_type: Type of signal
            entity_id: Entity identifier
            correlation_id: Optional correlation ID for logging

        Returns:
            The dedup_key used
        """
        window = SIGNAL_WINDOWS.get(signal_type, SignalWindow.OPERATIONAL)
        window_hours = WINDOW_HOURS[window]

        now = datetime.utcnow()
        window_start = self._calculate_window_start(now, window_hours)
        dedup_key = self._generate_dedup_key(signal_type, entity_id, window_start)

        with self._lock:
            self._record_internal(
                dedup_key=dedup_key,
                signal_type=signal_type,
                entity_id=entity_id,
                window_start=window_start,
                window_hours=window_hours
            )

        return dedup_key

    def _calculate_window_start(self, timestamp: datetime, window_hours: int) -> datetime:
        """
        Calculate deterministic window start time.

        Windows are aligned to fixed time boundaries, not rolling.
        This ensures consistent dedup_keys regardless of when checked.

        Args:
            timestamp: Current timestamp
            window_hours: Window size in hours

        Returns:
            Window start timestamp (floored to window boundary)
        """
        # For 24h windows, align to midnight UTC
        if window_hours == 24:
            return datetime(timestamp.year, timestamp.month, timestamp.day)

        # For 365d windows, align to year start
        if window_hours >= 365 * 24:
            return datetime(timestamp.year, 1, 1)

        # For other windows, floor to nearest window boundary
        epoch = datetime(2020, 1, 1)  # Fixed reference point
        hours_since_epoch = (timestamp - epoch).total_seconds() / 3600
        window_number = int(hours_since_epoch // window_hours)
        return epoch + timedelta(hours=window_number * window_hours)

    def _generate_dedup_key(
        self,
        signal_type: str,
        entity_id: str,
        window_start: datetime
    ) -> str:
        """
        Generate deterministic dedup key.

        Key = SHA256(signal_type + entity_id + window_start_iso)

        Args:
            signal_type: Type of signal
            entity_id: Entity identifier
            window_start: Window start timestamp

        Returns:
            Hex digest of hash
        """
        key_material = f"{signal_type}:{entity_id}:{window_start.isoformat()}"
        return hashlib.sha256(key_material.encode()).hexdigest()

    def _record_internal(
        self,
        dedup_key: str,
        signal_type: str,
        entity_id: str,
        window_start: datetime,
        window_hours: int
    ) -> None:
        """
        Internal method to record emission (must be called with lock held).
        """
        window_end = window_start + timedelta(hours=window_hours)

        entry = DedupEntry(
            dedup_key=dedup_key,
            signal_type=signal_type,
            entity_id=entity_id,
            first_seen=datetime.utcnow(),
            window_end=window_end
        )

        if self._use_persistence and self._db:
            self._insert_db(entry)
        else:
            self._cache[dedup_key] = entry

    def _check_db(self, dedup_key: str) -> bool:
        """Check if dedup_key exists in database."""
        # Placeholder for database implementation
        # In production, this would query:
        # SELECT 1 FROM signal_dedup WHERE dedup_key = ? AND window_end > NOW()
        return False

    def _insert_db(self, entry: DedupEntry) -> None:
        """Insert dedup entry into database."""
        # Placeholder for database implementation
        # In production, this would insert:
        # INSERT INTO signal_dedup (dedup_key, signal_type, entity_id, first_seen, window_end)
        pass

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.

        Call this periodically to prevent memory growth.

        Returns:
            Number of entries removed
        """
        now = datetime.utcnow()
        removed = 0

        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.window_end < now
            ]

            for key in expired_keys:
                del self._cache[key]
                removed += 1

        return removed

    def get_stats(self) -> Dict[str, int]:
        """Get deduplication statistics."""
        return {
            **self._stats,
            'cache_size': len(self._cache),
            'block_rate': (
                self._stats['signals_blocked'] / max(self._stats['signals_checked'], 1)
            )
        }

    def reset(self) -> None:
        """Reset deduplicator state (for testing)."""
        with self._lock:
            self._cache.clear()
            self._stats = {
                'signals_checked': 0,
                'signals_allowed': 0,
                'signals_blocked': 0,
            }


# Global singleton instance
_default_deduplicator: Optional[SignalDeduplicator] = None


def get_deduplicator() -> SignalDeduplicator:
    """Get the global deduplicator instance."""
    global _default_deduplicator
    if _default_deduplicator is None:
        _default_deduplicator = SignalDeduplicator()
    return _default_deduplicator


def should_emit_signal(
    signal_type: str,
    entity_id: str,
    correlation_id: Optional[str] = None
) -> bool:
    """
    Convenience function to check if signal should be emitted.

    Uses the global deduplicator instance.

    Args:
        signal_type: Type of signal
        entity_id: Entity identifier
        correlation_id: Optional correlation ID

    Returns:
        True if signal should be emitted, False if duplicate
    """
    return get_deduplicator().should_emit(
        signal_type=signal_type,
        entity_id=entity_id,
        correlation_id=correlation_id
    )
