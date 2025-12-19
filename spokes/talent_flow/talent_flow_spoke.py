"""
Talent Flow Node - Spoke #4
===========================
Detects executive movement between companies.

Tool 16: Movement Detection Engine

Per Doctrine:
- Detects hires, exits, promotions, transfers
- Emits signals to BIT Engine
- Requires company anchor (both old and new for transfers)
- 365-day deduplication window for structural signals

Signals emitted:
- EXECUTIVE_JOINED: +10.0
- EXECUTIVE_LEFT: -5.0
- TITLE_CHANGE: +3.0

Barton ID Range: 04.04.02.04.60000.###
"""

import os
import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

# Wheel imports
from ctb.sys.enrichment.pipeline_engine.wheel.bicycle_wheel import Spoke, Hub
from ctb.sys.enrichment.pipeline_engine.wheel.wheel_result import SpokeResult, ResultStatus, FailureType

# BIT Engine
from hub.company.bit_engine import BITEngine, SignalType

# Doctrine enforcement
from ops.enforcement.correlation_id import validate_correlation_id, CorrelationIDError
from ops.enforcement.hub_gate import validate_company_anchor, HubGateError, GateLevel
from ops.enforcement.signal_dedup import should_emit_signal, get_deduplicator


logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class MovementType(Enum):
    """Types of executive movement"""
    HIRE = "hire"              # New person at company
    EXIT = "exit"              # Person left company
    PROMOTION = "promotion"    # Title change (upward)
    DEMOTION = "demotion"      # Title change (downward)
    TRANSFER = "transfer"      # Moved to different company
    LATERAL = "lateral"        # Same level, different role


class TitleLevel(Enum):
    """Executive title levels for seniority comparison"""
    C_SUITE = "c_suite"                    # CEO, CFO, CTO, COO, CHRO
    VP = "vp"                              # Vice President
    DIRECTOR = "director"                  # Director
    SENIOR_MANAGER = "senior_manager"      # Senior Manager
    MANAGER = "manager"                    # Manager
    INDIVIDUAL = "individual_contributor"  # IC


# =============================================================================
# TITLE LEVEL KEYWORDS
# =============================================================================

TITLE_LEVEL_KEYWORDS: Dict[TitleLevel, List[str]] = {
    TitleLevel.C_SUITE: [
        'ceo', 'chief executive', 'cfo', 'chief financial',
        'cto', 'chief technology', 'coo', 'chief operating',
        'chro', 'chief human resources', 'cio', 'chief information',
        'cpo', 'chief people', 'president', 'founder', 'co-founder'
    ],
    TitleLevel.VP: [
        'vp', 'vice president', 'svp', 'senior vice president',
        'evp', 'executive vice president', 'avp', 'assistant vice president'
    ],
    TitleLevel.DIRECTOR: [
        'director', 'head of', 'principal'
    ],
    TitleLevel.SENIOR_MANAGER: [
        'senior manager', 'sr. manager', 'sr manager',
        'senior lead', 'team lead', 'lead'
    ],
    TitleLevel.MANAGER: [
        'manager', 'supervisor', 'coordinator'
    ],
    TitleLevel.INDIVIDUAL: []  # Default
}


# =============================================================================
# MOVEMENT IMPACT VALUES
# =============================================================================

MOVEMENT_IMPACTS: Dict[MovementType, float] = {
    MovementType.HIRE: 10.0,
    MovementType.EXIT: -5.0,
    MovementType.PROMOTION: 5.0,
    MovementType.DEMOTION: -3.0,
    MovementType.TRANSFER: 10.0,  # Transfer in (positive for new company)
    MovementType.LATERAL: 3.0,
}

MOVEMENT_TO_SIGNAL: Dict[MovementType, SignalType] = {
    MovementType.HIRE: SignalType.EXECUTIVE_JOINED,
    MovementType.EXIT: SignalType.EXECUTIVE_LEFT,
    MovementType.PROMOTION: SignalType.TITLE_CHANGE,
    MovementType.DEMOTION: SignalType.TITLE_CHANGE,
    MovementType.TRANSFER: SignalType.EXECUTIVE_JOINED,
    MovementType.LATERAL: SignalType.TITLE_CHANGE,
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class PersonSnapshot:
    """Snapshot of a person's state at a point in time"""
    person_id: str
    full_name: str
    company_id: Optional[str] = None
    company_name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    snapshot_at: datetime = field(default_factory=datetime.utcnow)
    data_source: str = "unknown"

    def compute_hash(self) -> str:
        """Compute hash for change detection"""
        hash_fields = [
            self.company_id or "",
            self.company_name or "",
            self.title or "",
        ]
        combined = "|".join(hash_fields).lower()
        return hashlib.sha256(combined.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'person_id': self.person_id,
            'full_name': self.full_name,
            'company_id': self.company_id,
            'company_name': self.company_name,
            'title': self.title,
            'email': self.email,
            'linkedin_url': self.linkedin_url,
            'snapshot_at': self.snapshot_at.isoformat(),
            'data_source': self.data_source,
        }


@dataclass
class DetectedMovement:
    """A detected movement event"""
    movement_type: MovementType
    person_id: str
    person_name: str
    confidence: float

    # Company context
    old_company_id: Optional[str] = None
    old_company_name: Optional[str] = None
    new_company_id: Optional[str] = None
    new_company_name: Optional[str] = None

    # Title context
    old_title: Optional[str] = None
    new_title: Optional[str] = None

    # Metadata
    detected_at: datetime = field(default_factory=datetime.utcnow)
    matched_rules: List[str] = field(default_factory=list)

    @property
    def impact(self) -> float:
        """Get BIT impact for this movement"""
        return MOVEMENT_IMPACTS.get(self.movement_type, 0.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'movement_type': self.movement_type.value,
            'person_id': self.person_id,
            'person_name': self.person_name,
            'confidence': self.confidence,
            'impact': self.impact,
            'old_company_id': self.old_company_id,
            'old_company_name': self.old_company_name,
            'new_company_id': self.new_company_id,
            'new_company_name': self.new_company_name,
            'old_title': self.old_title,
            'new_title': self.new_title,
            'detected_at': self.detected_at.isoformat(),
            'matched_rules': self.matched_rules,
        }


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class TalentFlowConfig:
    """Configuration for Talent Flow Spoke"""
    enabled: bool = True
    min_confidence: float = 0.70
    dedup_window_days: int = 365  # Structural signals: 365 days
    cooldown_hours: int = 24
    max_movements_per_person_per_month: int = 3
    target_titles: List[str] = field(default_factory=lambda: [
        'chro', 'chief human resources', 'hr director', 'vp hr',
        'benefits', 'compensation', 'payroll', 'ceo', 'cfo'
    ])


def load_talent_flow_config() -> TalentFlowConfig:
    """Load Talent Flow configuration from environment"""
    return TalentFlowConfig(
        enabled=os.getenv("TALENT_FLOW_ENABLED", "true").lower() == "true",
        min_confidence=float(os.getenv("TALENT_FLOW_MIN_CONFIDENCE", "0.70")),
        dedup_window_days=int(os.getenv("TALENT_FLOW_DEDUP_WINDOW", "365")),
        cooldown_hours=int(os.getenv("TALENT_FLOW_COOLDOWN_HOURS", "24")),
        max_movements_per_person_per_month=int(os.getenv("TALENT_FLOW_MAX_MOVEMENTS", "3")),
    )


# =============================================================================
# MOVEMENT DETECTOR (TOOL 16)
# =============================================================================

class MovementDetector:
    """
    Tool 16: Movement Detection Engine

    Detects executive movements by comparing person snapshots.
    """

    def __init__(self, config: TalentFlowConfig = None):
        self.config = config or load_talent_flow_config()
        self._stats = {
            'comparisons': 0,
            'hires': 0,
            'exits': 0,
            'promotions': 0,
            'demotions': 0,
            'transfers': 0,
            'laterals': 0,
            'no_change': 0,
        }

    def detect_movement(
        self,
        old_snapshot: Optional[PersonSnapshot],
        new_snapshot: PersonSnapshot
    ) -> Optional[DetectedMovement]:
        """
        Detect movement between two snapshots.

        Args:
            old_snapshot: Previous state (None for new person)
            new_snapshot: Current state

        Returns:
            DetectedMovement if detected, None otherwise
        """
        self._stats['comparisons'] += 1

        # New person (no previous snapshot)
        if old_snapshot is None:
            if new_snapshot.company_id:
                self._stats['hires'] += 1
                return DetectedMovement(
                    movement_type=MovementType.HIRE,
                    person_id=new_snapshot.person_id,
                    person_name=new_snapshot.full_name,
                    confidence=0.90,
                    new_company_id=new_snapshot.company_id,
                    new_company_name=new_snapshot.company_name,
                    new_title=new_snapshot.title,
                    matched_rules=['new_person_with_company']
                )
            return None

        # Check for changes
        old_hash = old_snapshot.compute_hash()
        new_hash = new_snapshot.compute_hash()

        if old_hash == new_hash:
            self._stats['no_change'] += 1
            return None

        # Company changed
        company_changed = (old_snapshot.company_id != new_snapshot.company_id)

        # Title changed
        title_changed = (
            (old_snapshot.title or "").lower().strip() !=
            (new_snapshot.title or "").lower().strip()
        )

        # Detect movement type
        if company_changed:
            if old_snapshot.company_id and new_snapshot.company_id:
                # Transfer to new company
                self._stats['transfers'] += 1
                return DetectedMovement(
                    movement_type=MovementType.TRANSFER,
                    person_id=new_snapshot.person_id,
                    person_name=new_snapshot.full_name,
                    confidence=0.85,
                    old_company_id=old_snapshot.company_id,
                    old_company_name=old_snapshot.company_name,
                    new_company_id=new_snapshot.company_id,
                    new_company_name=new_snapshot.company_name,
                    old_title=old_snapshot.title,
                    new_title=new_snapshot.title,
                    matched_rules=['company_changed', 'both_companies_exist']
                )
            elif old_snapshot.company_id and not new_snapshot.company_id:
                # Exit
                self._stats['exits'] += 1
                return DetectedMovement(
                    movement_type=MovementType.EXIT,
                    person_id=new_snapshot.person_id,
                    person_name=new_snapshot.full_name,
                    confidence=0.80,
                    old_company_id=old_snapshot.company_id,
                    old_company_name=old_snapshot.company_name,
                    old_title=old_snapshot.title,
                    matched_rules=['company_removed']
                )
            elif not old_snapshot.company_id and new_snapshot.company_id:
                # Hire (was unaffiliated, now has company)
                self._stats['hires'] += 1
                return DetectedMovement(
                    movement_type=MovementType.HIRE,
                    person_id=new_snapshot.person_id,
                    person_name=new_snapshot.full_name,
                    confidence=0.85,
                    new_company_id=new_snapshot.company_id,
                    new_company_name=new_snapshot.company_name,
                    new_title=new_snapshot.title,
                    matched_rules=['company_added']
                )

        # Title changed but same company
        if title_changed and not company_changed:
            old_level = self._get_title_level(old_snapshot.title)
            new_level = self._get_title_level(new_snapshot.title)

            level_change = self._compare_levels(old_level, new_level)

            if level_change > 0:
                self._stats['promotions'] += 1
                return DetectedMovement(
                    movement_type=MovementType.PROMOTION,
                    person_id=new_snapshot.person_id,
                    person_name=new_snapshot.full_name,
                    confidence=0.80,
                    old_company_id=old_snapshot.company_id,
                    old_company_name=old_snapshot.company_name,
                    new_company_id=new_snapshot.company_id,
                    new_company_name=new_snapshot.company_name,
                    old_title=old_snapshot.title,
                    new_title=new_snapshot.title,
                    matched_rules=['title_changed', 'level_increased']
                )
            elif level_change < 0:
                self._stats['demotions'] += 1
                return DetectedMovement(
                    movement_type=MovementType.DEMOTION,
                    person_id=new_snapshot.person_id,
                    person_name=new_snapshot.full_name,
                    confidence=0.75,
                    old_company_id=old_snapshot.company_id,
                    old_company_name=old_snapshot.company_name,
                    new_company_id=new_snapshot.company_id,
                    new_company_name=new_snapshot.company_name,
                    old_title=old_snapshot.title,
                    new_title=new_snapshot.title,
                    matched_rules=['title_changed', 'level_decreased']
                )
            else:
                # Lateral move (same level, different title)
                self._stats['laterals'] += 1
                return DetectedMovement(
                    movement_type=MovementType.LATERAL,
                    person_id=new_snapshot.person_id,
                    person_name=new_snapshot.full_name,
                    confidence=0.70,
                    old_company_id=old_snapshot.company_id,
                    old_company_name=old_snapshot.company_name,
                    new_company_id=new_snapshot.company_id,
                    new_company_name=new_snapshot.company_name,
                    old_title=old_snapshot.title,
                    new_title=new_snapshot.title,
                    matched_rules=['title_changed', 'level_same']
                )

        return None

    def _get_title_level(self, title: Optional[str]) -> TitleLevel:
        """Determine title seniority level"""
        if not title:
            return TitleLevel.INDIVIDUAL

        title_lower = title.lower()

        for level, keywords in TITLE_LEVEL_KEYWORDS.items():
            if any(kw in title_lower for kw in keywords):
                return level

        return TitleLevel.INDIVIDUAL

    def _compare_levels(self, old_level: TitleLevel, new_level: TitleLevel) -> int:
        """
        Compare title levels.

        Returns:
            1 if promoted (new is higher)
            -1 if demoted (new is lower)
            0 if same level
        """
        level_order = [
            TitleLevel.INDIVIDUAL,
            TitleLevel.MANAGER,
            TitleLevel.SENIOR_MANAGER,
            TitleLevel.DIRECTOR,
            TitleLevel.VP,
            TitleLevel.C_SUITE,
        ]

        try:
            old_idx = level_order.index(old_level)
            new_idx = level_order.index(new_level)

            if new_idx > old_idx:
                return 1
            elif new_idx < old_idx:
                return -1
            return 0
        except ValueError:
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get detector statistics"""
        return self._stats.copy()


# =============================================================================
# TALENT FLOW SPOKE
# =============================================================================

class TalentFlowSpoke(Spoke):
    """
    Talent Flow Node - Spoke #4 of the Company Hub.

    Detects executive movements and emits signals to BIT Engine.

    DOCTRINE:
    - Both old and new company must have valid company_id for transfers
    - 365-day deduplication window for structural signals
    - Cooldown period between movement detections for same person

    Company Hub Integration:
    - Uses CompanyPipeline for company validation
    - Signals persisted to Neon via BIT Engine
    """

    def __init__(
        self,
        hub: Hub,
        bit_engine: Optional[BITEngine] = None,
        config: TalentFlowConfig = None,
        company_pipeline=None
    ):
        """
        Initialize Talent Flow Spoke.

        Args:
            hub: Parent hub instance
            bit_engine: BIT Engine for signals
            config: Talent Flow configuration
            company_pipeline: CompanyPipeline for company validation
        """
        super().__init__(name="talent_flow", hub=hub)
        self.bit_engine = bit_engine or BITEngine()
        self.config = config or load_talent_flow_config()
        self.detector = MovementDetector(config=self.config)
        self._company_pipeline = company_pipeline

        # Snapshot cache for comparison
        self._snapshot_cache: Dict[str, PersonSnapshot] = {}

        # Movement history for cooldown
        self._movement_history: Dict[str, List[datetime]] = {}

        # Stats
        self.stats = {
            'total_processed': 0,
            'movements_detected': 0,
            'signals_emitted': 0,
            'signals_deduped': 0,
            'skipped_cooldown': 0,
            'skipped_max_movements': 0,
            'errors': 0,
        }

    def set_company_pipeline(self, pipeline) -> None:
        """Set company pipeline for company validation."""
        self._company_pipeline = pipeline

    def process(self, data: Any, correlation_id: str = None) -> SpokeResult:
        """
        Process a person snapshot for movement detection.

        DOCTRINE: correlation_id is MANDATORY. FAIL HARD if missing.

        Args:
            data: PersonSnapshot or list of PersonSnapshot
            correlation_id: MANDATORY - End-to-end trace ID (UUID v4)

        Returns:
            SpokeResult with processing outcome
        """
        # Kill switch
        if not self.config.enabled or os.getenv('KILL_TALENT_FLOW', '').lower() == 'true':
            return SpokeResult(
                status=ResultStatus.SKIPPED,
                failure_reason='killed_by_config'
            )

        # Handle batch
        if isinstance(data, list):
            return self._process_batch(data, correlation_id)

        if not isinstance(data, PersonSnapshot):
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.VALIDATION_ERROR,
                failure_reason=f"Expected PersonSnapshot, got {type(data).__name__}"
            )

        return self._process_snapshot(data, correlation_id)

    def _process_snapshot(
        self,
        snapshot: PersonSnapshot,
        correlation_id: str
    ) -> SpokeResult:
        """Process a single person snapshot"""
        # DOCTRINE: Validate correlation_id
        process_id = "talent_flow.spoke.process"
        try:
            correlation_id = validate_correlation_id(correlation_id, process_id, "Talent Flow")
        except CorrelationIDError as e:
            self.stats['errors'] += 1
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.VALIDATION_ERROR,
                failure_reason=str(e)
            )

        self.stats['total_processed'] += 1

        # Safety: Cooldown check
        if self._in_cooldown(snapshot.person_id):
            self.stats['skipped_cooldown'] += 1
            return SpokeResult(
                status=ResultStatus.SKIPPED,
                failure_reason='cooldown_active'
            )

        # Safety: Max movements check
        if self._exceeds_max_movements(snapshot.person_id):
            self.stats['skipped_max_movements'] += 1
            return SpokeResult(
                status=ResultStatus.SKIPPED,
                failure_reason='max_movements_exceeded'
            )

        # Get previous snapshot
        old_snapshot = self._snapshot_cache.get(snapshot.person_id)

        # Detect movement
        movement = self.detector.detect_movement(old_snapshot, snapshot)

        # Update snapshot cache
        self._snapshot_cache[snapshot.person_id] = snapshot

        if not movement:
            return SpokeResult(
                status=ResultStatus.SUCCESS,
                data=None,
                metrics={'movement_detected': False}
            )

        self.stats['movements_detected'] += 1

        # Check confidence threshold
        if movement.confidence < self.config.min_confidence:
            return SpokeResult(
                status=ResultStatus.SUCCESS,
                data=movement,
                metrics={'movement_detected': True, 'below_threshold': True}
            )

        # Record movement for cooldown
        self._record_movement(snapshot.person_id)

        # Emit signal
        signal_emitted = self._emit_signal(correlation_id, movement)

        return SpokeResult(
            status=ResultStatus.SUCCESS,
            data=movement,
            hub_signal={
                'signal_type': movement.movement_type.value,
                'impact': movement.impact,
                'source': self.name,
                'company_id': movement.new_company_id or movement.old_company_id
            } if signal_emitted else None,
            metrics={
                'movement_detected': True,
                'movement_type': movement.movement_type.value,
                'signal_emitted': signal_emitted
            }
        )

    def _process_batch(
        self,
        snapshots: List[PersonSnapshot],
        correlation_id: str
    ) -> SpokeResult:
        """Process a batch of snapshots"""
        results = []
        for snapshot in snapshots:
            result = self._process_snapshot(snapshot, correlation_id)
            results.append(result)

        successful = sum(1 for r in results if r.success)
        movements = sum(1 for r in results if r.data is not None)

        return SpokeResult(
            status=ResultStatus.SUCCESS,
            data=results,
            metrics={
                'total': len(snapshots),
                'successful': successful,
                'movements_detected': movements
            }
        )

    def _in_cooldown(self, person_id: str) -> bool:
        """Check if person is in cooldown period"""
        if person_id not in self._movement_history:
            return False

        history = self._movement_history[person_id]
        if not history:
            return False

        last_movement = max(history)
        hours_since = (datetime.utcnow() - last_movement).total_seconds() / 3600

        return hours_since < self.config.cooldown_hours

    def _exceeds_max_movements(self, person_id: str) -> bool:
        """Check if person exceeds max movements this month"""
        if person_id not in self._movement_history:
            return False

        # Count movements in last 30 days
        cutoff = datetime.utcnow().replace(day=1)  # Start of month
        history = self._movement_history[person_id]
        recent_count = sum(1 for dt in history if dt >= cutoff)

        return recent_count >= self.config.max_movements_per_person_per_month

    def _record_movement(self, person_id: str):
        """Record a movement for cooldown tracking"""
        if person_id not in self._movement_history:
            self._movement_history[person_id] = []
        self._movement_history[person_id].append(datetime.utcnow())

        # Clean old entries (keep last 12 months)
        cutoff = datetime.utcnow().replace(month=1) if datetime.utcnow().month == 12 else datetime.utcnow()
        self._movement_history[person_id] = [
            dt for dt in self._movement_history[person_id]
            if (datetime.utcnow() - dt).days < 365
        ]

    def _emit_signal(
        self,
        correlation_id: str,
        movement: DetectedMovement
    ) -> bool:
        """Emit signal to BIT Engine with deduplication"""
        if not self.bit_engine:
            return False

        # Determine target company
        company_id = movement.new_company_id or movement.old_company_id
        if not company_id:
            logger.warning(f"Cannot emit signal without company_id: {movement.person_id}")
            return False

        # Map to SignalType
        signal_type = MOVEMENT_TO_SIGNAL.get(movement.movement_type)
        if not signal_type:
            return False

        # Check deduplication (365-day window for structural signals)
        dedup_key = f"{company_id}:{signal_type.value}:{movement.person_id}"
        if not should_emit_signal(signal_type.value, company_id, correlation_id):
            self.stats['signals_deduped'] += 1
            return False

        # Emit (with Neon persistence)
        try:
            self.bit_engine.create_signal(
                signal_type=signal_type,
                company_id=company_id,
                source_spoke=self.name,
                impact=movement.impact,
                metadata={
                    'person_id': movement.person_id,
                    'person_name': movement.person_name,
                    'movement_type': movement.movement_type.value,
                    'confidence': movement.confidence,
                    'old_title': movement.old_title,
                    'new_title': movement.new_title,
                    'old_company': movement.old_company_name,
                    'new_company': movement.new_company_name,
                    'detected_at': movement.detected_at.isoformat(),
                },
                correlation_id=correlation_id  # For Neon persistence
            )

            self.stats['signals_emitted'] += 1
            logger.info(
                f"Talent Flow signal: {signal_type.value} for {movement.person_name} "
                f"({movement.movement_type.value}, impact: {movement.impact:+.1f})"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to emit talent flow signal: {e}")
            self.stats['errors'] += 1
            return False

    def load_snapshots(self, snapshots: List[Dict[str, Any]]):
        """Pre-load snapshot cache from database"""
        for snap_data in snapshots:
            snapshot = PersonSnapshot(
                person_id=snap_data['person_unique_id'],
                full_name=snap_data.get('full_name', ''),
                company_id=snap_data.get('company_unique_id'),
                company_name=snap_data.get('company_name'),
                title=snap_data.get('title'),
                email=snap_data.get('email'),
                linkedin_url=snap_data.get('linkedin_url'),
            )
            self._snapshot_cache[snapshot.person_id] = snapshot

        logger.info(f"Loaded {len(snapshots)} snapshots into cache")

    def get_stats(self) -> Dict[str, Any]:
        """Get spoke statistics"""
        return {
            **self.stats,
            'detector_stats': self.detector.get_stats(),
            'snapshot_cache_size': len(self._snapshot_cache),
            'config': {
                'enabled': self.config.enabled,
                'min_confidence': self.config.min_confidence,
                'cooldown_hours': self.config.cooldown_hours,
            }
        }


# =============================================================================
# EXPORTS
# =============================================================================

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
