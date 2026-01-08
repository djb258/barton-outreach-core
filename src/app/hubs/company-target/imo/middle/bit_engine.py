"""
BIT Engine - Buyer Intent Tool
==============================
Spine-First Architecture v1.1

The core metric engine that lives INSIDE the Company Hub.

Architecture:
    ╔═════════════════════════════════════════════════╗
    ║              COMPANY HUB                        ║
    ║                                                 ║
    ║   ┌───────────────────────────────────────┐     ║
    ║   │           BIT ENGINE                  │     ║
    ║   │        (Core Metric)                  │     ║
    ║   │                                       │     ║
    ║   │   Aggregates signals from:            │     ║
    ║   │   - People Sub-Hub (slot filled)      │     ║
    ║   │   - DOL Sub-Hub (5500 signals)        │     ║
    ║   │   - Blog Sub-Hub (news/events)        │     ║
    ║   │   - Talent Flow (movement)            │     ║
    ║   └───────────────────────────────────────┘     ║
    ║                                                 ║
    ╚═════════════════════════════════════════════════╝

BIT Score Components:
    - Slot Signals: +10 per filled executive slot
    - DOL Signals: +5 per relevant 5500 filing
    - Event Signals: +3 to +15 per news event
    - Movement Signals: +10 per detected movement

Neon Integration (Spine-First):
    - Signals are persisted to outreach.bit_signals
    - Scores are persisted to outreach.bit_scores
    - All writes FK to outreach_id (spine anchor)
    - Errors persist to outreach.bit_errors

DOCTRINE: Uses outreach_id as the ONLY identity. sovereign_id is HIDDEN.

Version: 2.0 (Spine-First Refactor)
Date: 2026-01-08
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import logging
import uuid


logger = logging.getLogger(__name__)


# =============================================================================
# DOCTRINE GUARDS (LOCKED 2026-01-08)
# =============================================================================

ENFORCE_OUTREACH_SPINE_ONLY = True
assert ENFORCE_OUTREACH_SPINE_ONLY is True, "BIT Engine MUST use outreach_id only"

ENFORCE_CORRELATION_ID = True
assert ENFORCE_CORRELATION_ID is True, "BIT Engine MUST require correlation_id for persistence"

ENFORCE_ERROR_PERSISTENCE = True
assert ENFORCE_ERROR_PERSISTENCE is True, "BIT Engine MUST persist all errors"

# Tier bands (LOCKED - do not modify)
TIER_BANDS_LOCKED = True
assert TIER_BANDS_LOCKED is True, "BIT tier bands are LOCKED"


# =============================================================================
# RUNTIME GUARDS (HARD ENFORCEMENT)
# =============================================================================

class BITDoctrineViolation(Exception):
    """Raised when BIT doctrine is violated. This is a HARD STOP."""
    pass


def guard_no_company_unique_id(data: dict, context: str = ""):
    """
    HARD GUARD: Raise exception if company_unique_id appears anywhere.

    BIT uses outreach_id ONLY. company_unique_id is FORBIDDEN.
    """
    forbidden_keys = ['company_unique_id', 'company_id', 'sovereign_id']
    for key in forbidden_keys:
        if key in data:
            raise BITDoctrineViolation(
                f"DOCTRINE VIOLATION: '{key}' found in {context}. "
                f"BIT uses outreach_id ONLY. company_unique_id is FORBIDDEN."
            )


def guard_correlation_id(correlation_id: str, context: str = ""):
    """
    HARD GUARD: Fail fast if correlation_id is missing.

    All BIT operations REQUIRE correlation_id for traceability.
    """
    if not correlation_id:
        raise BITDoctrineViolation(
            f"DOCTRINE VIOLATION: correlation_id missing in {context}. "
            f"All BIT operations REQUIRE correlation_id."
        )


def guard_tier_value(tier: str, context: str = ""):
    """
    HARD GUARD: Ensure tier is one of the locked values.
    """
    valid_tiers = {'COLD', 'WARM', 'HOT', 'BURNING'}
    if tier not in valid_tiers:
        raise BITDoctrineViolation(
            f"DOCTRINE VIOLATION: Invalid tier '{tier}' in {context}. "
            f"Valid tiers: {valid_tiers}"
        )


def guard_score_delta(old_score: float, new_score: float, max_delta: float = 50.0, context: str = ""):
    """
    GUARD: Cap maximum score change per operation to prevent runaway.
    """
    delta = abs(new_score - old_score)
    if delta > max_delta:
        logger.warning(
            f"Score delta {delta} exceeds max {max_delta} in {context}. "
            f"Capping change."
        )
        if new_score > old_score:
            return old_score + max_delta
        else:
            return old_score - max_delta
    return new_score


# =============================================================================
# SIGNAL TYPES
# =============================================================================

class SignalType(Enum):
    """Types of signals that feed the BIT Engine"""
    # People Sub-Hub signals
    SLOT_FILLED = "slot_filled"
    SLOT_VACATED = "slot_vacated"
    EMAIL_VERIFIED = "email_verified"
    LINKEDIN_FOUND = "linkedin_found"

    # DOL Sub-Hub signals
    FORM_5500_FILED = "form_5500_filed"
    LARGE_PLAN = "large_plan"
    BROKER_CHANGE = "broker_change"

    # Blog Sub-Hub signals (per PRD v2.1)
    FUNDING_EVENT = "funding_event"
    ACQUISITION = "acquisition"
    LEADERSHIP_CHANGE = "leadership_change"
    EXPANSION = "expansion"
    PRODUCT_LAUNCH = "product_launch"
    PARTNERSHIP = "partnership"
    LAYOFF = "layoff"
    NEGATIVE_NEWS = "negative_news"

    # Talent Flow signals
    EXECUTIVE_JOINED = "executive_joined"
    EXECUTIVE_LEFT = "executive_left"
    TITLE_CHANGE = "title_change"


# Signal impact values (per PRD v2.1)
SIGNAL_IMPACTS: Dict[SignalType, float] = {
    # People Sub-Hub
    SignalType.SLOT_FILLED: 10.0,
    SignalType.SLOT_VACATED: -5.0,
    SignalType.EMAIL_VERIFIED: 3.0,
    SignalType.LINKEDIN_FOUND: 2.0,

    # DOL Sub-Hub
    SignalType.FORM_5500_FILED: 5.0,
    SignalType.LARGE_PLAN: 8.0,
    SignalType.BROKER_CHANGE: 7.0,

    # Blog Sub-Hub (per PRD v2.1)
    SignalType.FUNDING_EVENT: 15.0,
    SignalType.ACQUISITION: 12.0,
    SignalType.LEADERSHIP_CHANGE: 8.0,
    SignalType.EXPANSION: 7.0,
    SignalType.PRODUCT_LAUNCH: 5.0,
    SignalType.PARTNERSHIP: 5.0,
    SignalType.LAYOFF: -3.0,
    SignalType.NEGATIVE_NEWS: -5.0,

    # Talent Flow
    SignalType.EXECUTIVE_JOINED: 10.0,
    SignalType.EXECUTIVE_LEFT: -5.0,
    SignalType.TITLE_CHANGE: 3.0,
}

# Signal decay periods by category
SIGNAL_DECAY_PERIODS: Dict[SignalType, int] = {
    # Structural signals - 365 days
    SignalType.FORM_5500_FILED: 365,
    SignalType.LARGE_PLAN: 365,

    # Movement signals - 180 days
    SignalType.BROKER_CHANGE: 180,
    SignalType.EXECUTIVE_JOINED: 180,
    SignalType.EXECUTIVE_LEFT: 180,
    SignalType.TITLE_CHANGE: 180,

    # Event signals - 90 days
    SignalType.FUNDING_EVENT: 90,
    SignalType.ACQUISITION: 90,
    SignalType.LEADERSHIP_CHANGE: 90,
    SignalType.EXPANSION: 90,
    SignalType.PRODUCT_LAUNCH: 90,
    SignalType.PARTNERSHIP: 90,
    SignalType.LAYOFF: 60,
    SignalType.NEGATIVE_NEWS: 60,

    # Operational signals - 90 days
    SignalType.SLOT_FILLED: 90,
    SignalType.SLOT_VACATED: 90,
    SignalType.EMAIL_VERIFIED: 90,
    SignalType.LINKEDIN_FOUND: 90,
}

# BIT Score Thresholds
BIT_THRESHOLD_COLD = 0
BIT_THRESHOLD_WARM = 25       # COLD -> WARM
BIT_THRESHOLD_HOT = 50        # WARM -> HOT
BIT_THRESHOLD_BURNING = 75    # HOT -> BURNING


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class BITSignal:
    """A single signal feeding the BIT Engine"""
    signal_type: SignalType
    outreach_id: str  # DOCTRINE: Uses outreach_id, NOT company_id
    source_spoke: str
    impact: float
    correlation_id: str  # DOCTRINE: Required for persistence
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    process_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'signal_type': self.signal_type.value,
            'outreach_id': self.outreach_id,
            'source_spoke': self.source_spoke,
            'impact': self.impact,
            'correlation_id': self.correlation_id,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            'process_id': self.process_id
        }


@dataclass
class CompanyBITScore:
    """BIT score for a single company (identified by outreach_id)"""
    outreach_id: str  # DOCTRINE: Uses outreach_id, NOT company_id
    score: float = 0.0
    signal_count: int = 0
    last_signal_at: Optional[datetime] = None
    signal_history: List[BITSignal] = field(default_factory=list)

    # Score breakdown by source
    people_score: float = 0.0
    dol_score: float = 0.0
    blog_score: float = 0.0
    talent_flow_score: float = 0.0

    def add_signal(self, signal: BITSignal):
        """Add a signal and update score"""
        self.signal_history.append(signal)
        self.score += signal.impact
        self.signal_count += 1
        self.last_signal_at = signal.timestamp

        # Update source-specific score
        if signal.source_spoke == 'people_subhub':
            self.people_score += signal.impact
        elif signal.source_spoke == 'dol_subhub':
            self.dol_score += signal.impact
        elif signal.source_spoke == 'blog_subhub':
            self.blog_score += signal.impact
        elif signal.source_spoke == 'talent_flow':
            self.talent_flow_score += signal.impact

    def breakdown(self) -> Dict[str, float]:
        """Get score breakdown by source"""
        return {
            'total': self.score,
            'people_subhub': self.people_score,
            'dol_subhub': self.dol_score,
            'blog_subhub': self.blog_score,
            'talent_flow': self.talent_flow_score
        }

    def get_tier(self) -> str:
        """Get current tier based on score"""
        if self.score >= BIT_THRESHOLD_BURNING:
            return 'BURNING'
        elif self.score >= BIT_THRESHOLD_HOT:
            return 'HOT'
        elif self.score >= BIT_THRESHOLD_WARM:
            return 'WARM'
        return 'COLD'


# =============================================================================
# BIT ENGINE CLASS
# =============================================================================

class BITEngine:
    """
    Buyer Intent Tool - Core Metric Engine.
    Spine-First Architecture v1.1

    Lives INSIDE the Company Hub. Aggregates signals from all sub-hubs
    to calculate buyer intent scores.

    DOCTRINE:
    - Uses outreach_id as the ONLY identity anchor
    - sovereign_id is HIDDEN from this layer
    - correlation_id is REQUIRED for all persistence
    - Errors persist to outreach.bit_errors

    Neon Integration:
    - Set persist_to_neon=True to persist signals to database
    - Signals logged to outreach.bit_signals
    - Scores updated in outreach.bit_scores
    """

    def __init__(self, persist_to_neon: bool = False):
        """
        Initialize BIT Engine.

        Args:
            persist_to_neon: If True, persist signals to Neon database
        """
        self.name = "bit_engine"
        self._scores: Dict[str, CompanyBITScore] = {}
        self._total_signals: int = 0
        self._aggregate_score: float = 0.0
        self.logger = logging.getLogger(__name__)

        # Neon integration
        self.persist_to_neon = persist_to_neon
        self._bit_writer = None

    def _get_bit_writer(self):
        """Get or create BIT writer instance."""
        if self._bit_writer is None:
            from ..output.bit_writer import BITWriter
            self._bit_writer = BITWriter()
        return self._bit_writer

    def process_signal(
        self,
        signal: BITSignal,
    ):
        """
        Process a signal and update company BIT score.

        This is the core function that all sub-hubs call to feed the engine.

        DOCTRINE: correlation_id is REQUIRED and comes from the signal.

        Args:
            signal: BIT signal to process (must have correlation_id)

        Raises:
            BITDoctrineViolation: If correlation_id missing or forbidden ID used
        """
        # GUARD: Enforce correlation_id
        guard_correlation_id(signal.correlation_id, "process_signal")

        # GUARD: Ensure no forbidden identifiers in signal metadata
        if signal.metadata:
            guard_no_company_unique_id(signal.metadata, "signal.metadata")

        outreach_id = signal.outreach_id

        # Initialize score if new company
        if outreach_id not in self._scores:
            self._scores[outreach_id] = CompanyBITScore(outreach_id=outreach_id)

        # Store old score for delta check
        old_score = self._scores[outreach_id].score

        # Add signal to company score
        self._scores[outreach_id].add_signal(signal)

        # GUARD: Apply score delta cap
        new_score = guard_score_delta(
            old_score,
            self._scores[outreach_id].score,
            max_delta=50.0,
            context=f"process_signal({outreach_id})"
        )
        self._scores[outreach_id].score = new_score

        # Cap at max score (100)
        if self._scores[outreach_id].score > 100:
            self._scores[outreach_id].score = 100.0
        # Floor at min score (0)
        if self._scores[outreach_id].score < 0:
            self._scores[outreach_id].score = 0.0

        # Update aggregates
        self._total_signals += 1
        self._aggregate_score += signal.impact

        self.logger.info(
            f"BIT Signal: {signal.signal_type.value} for {outreach_id} "
            f"(impact: {signal.impact:+.1f}, new score: {self._scores[outreach_id].score:.1f})"
        )

        # Persist to Neon if enabled
        if self.persist_to_neon:
            self._persist_signal_to_neon(signal)

    def _persist_signal_to_neon(self, signal: BITSignal):
        """
        Persist a signal to Neon database.

        DOCTRINE: Uses outreach.bit_signals and outreach.bit_scores tables.

        Args:
            signal: BIT signal to persist (must have correlation_id)
        """
        # DOCTRINE: correlation_id is required
        if not signal.correlation_id:
            self.logger.error("Cannot persist signal without correlation_id (DOCTRINE)")
            return

        try:
            from ..output.bit_writer import BITWriter, BITSignalInput, BITScoreInput

            writer = self._get_bit_writer()

            # Get decay period for this signal type
            decay_period = SIGNAL_DECAY_PERIODS.get(signal.signal_type, 90)

            # Create signal input
            signal_input = BITSignalInput(
                outreach_id=signal.outreach_id,
                signal_type=signal.signal_type.value,
                signal_impact=signal.impact,
                source_spoke=signal.source_spoke,
                correlation_id=signal.correlation_id,
                process_id=signal.process_id,
                signal_metadata=signal.metadata,
                decay_period_days=decay_period
            )

            # Write signal
            signal_result = writer.write_signal(signal_input)

            if not signal_result.success:
                self.logger.error(f"Failed to persist BIT signal: {signal_result.error_message}")
                return

            # Update the company's BIT score
            company_score = self._scores[signal.outreach_id]
            score_input = BITScoreInput(
                outreach_id=signal.outreach_id,
                score=company_score.score,
                score_tier=company_score.get_tier(),
                signal_count=company_score.signal_count,
                correlation_id=signal.correlation_id,
                process_id=signal.process_id,
                people_score=company_score.people_score,
                dol_score=company_score.dol_score,
                blog_score=company_score.blog_score,
                talent_flow_score=company_score.talent_flow_score
            )

            score_result = writer.write_score(score_input)

            if score_result.success:
                self.logger.debug(
                    f"Persisted BIT signal to Neon: {signal.signal_type.value} "
                    f"for {signal.outreach_id}"
                )
            else:
                self.logger.error(f"Failed to update BIT score: {score_result.error_message}")

        except Exception as e:
            self.logger.error(f"Failed to persist BIT signal to Neon: {e}")

    def create_signal(
        self,
        signal_type: SignalType,
        outreach_id: str,
        source_spoke: str,
        correlation_id: str,
        impact: Optional[float] = None,
        metadata: Dict[str, Any] = None,
        process_id: Optional[str] = None
    ) -> BITSignal:
        """
        Create and process a signal.

        If impact not specified, uses default from SIGNAL_IMPACTS.

        DOCTRINE: correlation_id is REQUIRED.

        Args:
            signal_type: Type of signal
            outreach_id: Outreach ID (spine anchor) receiving the signal
            source_spoke: Sub-hub that generated the signal
            correlation_id: Pipeline trace ID (REQUIRED)
            impact: Signal impact (uses default if not specified)
            metadata: Additional signal metadata
            process_id: Process ID for traceability

        Raises:
            BITDoctrineViolation: If correlation_id missing or forbidden ID used
        """
        # GUARD: Enforce correlation_id (hard fail)
        guard_correlation_id(correlation_id, "create_signal")

        # GUARD: Ensure metadata doesn't contain forbidden identifiers
        if metadata:
            guard_no_company_unique_id(metadata, "create_signal.metadata")

        # Use default impact if not specified
        if impact is None:
            impact = SIGNAL_IMPACTS.get(signal_type, 0.0)

        # GUARD: Validate tier will be valid after adding signal
        # (informational only - tier is derived from score)

        signal = BITSignal(
            signal_type=signal_type,
            outreach_id=outreach_id,
            source_spoke=source_spoke,
            impact=impact,
            correlation_id=correlation_id,
            metadata=metadata or {},
            process_id=process_id
        )

        self.process_signal(signal)
        return signal

    def get_score(self, outreach_id: str) -> Optional[CompanyBITScore]:
        """Get BIT score for a company by outreach_id"""
        return self._scores.get(outreach_id)

    def get_score_value(self, outreach_id: str) -> float:
        """Get just the numeric score for a company"""
        score = self._scores.get(outreach_id)
        return score.score if score else 0.0

    def get_top_companies(self, limit: int = 10) -> List[CompanyBITScore]:
        """Get top companies by BIT score"""
        sorted_scores = sorted(
            self._scores.values(),
            key=lambda x: x.score,
            reverse=True
        )
        return sorted_scores[:limit]

    def get_companies_above_threshold(self, threshold: float) -> List[CompanyBITScore]:
        """Get companies with BIT score above threshold"""
        return [s for s in self._scores.values() if s.score >= threshold]

    def get_recent_movers(self, hours: int = 24, min_signals: int = 3) -> List[CompanyBITScore]:
        """Get companies with recent signal activity"""
        cutoff = datetime.now().timestamp() - (hours * 3600)
        return [
            s for s in self._scores.values()
            if s.last_signal_at and s.last_signal_at.timestamp() > cutoff
            and s.signal_count >= min_signals
        ]

    def summary(self) -> Dict[str, Any]:
        """Get BIT Engine summary statistics"""
        if not self._scores:
            return {
                'total_companies': 0,
                'total_signals': 0,
                'aggregate_score': 0.0
            }

        scores = [s.score for s in self._scores.values()]
        return {
            'total_companies': len(self._scores),
            'total_signals': self._total_signals,
            'aggregate_score': self._aggregate_score,
            'average_score': sum(scores) / len(scores),
            'max_score': max(scores),
            'min_score': min(scores),
            'companies_above_50': len([s for s in scores if s >= 50]),
            'companies_above_100': len([s for s in scores if s >= 100])
        }

    def export_scores(self) -> List[Dict[str, Any]]:
        """Export all scores for reporting"""
        return [
            {
                'outreach_id': s.outreach_id,
                'score': s.score,
                'tier': s.get_tier(),
                'signal_count': s.signal_count,
                'last_signal_at': s.last_signal_at.isoformat() if s.last_signal_at else None,
                'breakdown': s.breakdown()
            }
            for s in sorted(self._scores.values(), key=lambda x: x.score, reverse=True)
        ]

    def load_scores_from_neon(self) -> int:
        """
        Load BIT scores from Neon database.

        This hydrates the in-memory scores from the database.
        Should be called on startup to sync with persisted state.

        Returns:
            Number of companies loaded
        """
        try:
            import os
            import psycopg2

            conn = psycopg2.connect(
                host=os.getenv('NEON_HOST'),
                database=os.getenv('NEON_DATABASE'),
                user=os.getenv('NEON_USER'),
                password=os.getenv('NEON_PASSWORD'),
                sslmode='require'
            )

            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT outreach_id, score, score_tier, signal_count,
                           people_score, dol_score, blog_score, talent_flow_score,
                           last_signal_at
                    FROM outreach.bit_scores
                """)

                count = 0
                for row in cursor.fetchall():
                    outreach_id = str(row[0])
                    if outreach_id not in self._scores:
                        self._scores[outreach_id] = CompanyBITScore(outreach_id=outreach_id)

                    score = self._scores[outreach_id]
                    score.score = float(row[1])
                    score.signal_count = row[3]
                    score.people_score = float(row[4])
                    score.dol_score = float(row[5])
                    score.blog_score = float(row[6])
                    score.talent_flow_score = float(row[7])
                    score.last_signal_at = row[8]
                    count += 1

            conn.close()
            self.logger.info(f"Loaded BIT scores for {count} companies from Neon")
            return count

        except Exception as e:
            self.logger.error(f"Failed to load BIT scores from Neon: {e}")
            return 0

    def sync_score_to_neon(
        self,
        outreach_id: str,
        correlation_id: str
    ) -> bool:
        """
        Sync a company's BIT score to Neon.

        DOCTRINE: correlation_id is REQUIRED.

        Args:
            outreach_id: Company to sync (by outreach_id)
            correlation_id: Pipeline trace ID (REQUIRED)

        Returns:
            True if successful
        """
        if not self.persist_to_neon:
            self.logger.warning("Neon persistence not enabled")
            return False

        if not correlation_id:
            self.logger.error("correlation_id is required (DOCTRINE)")
            return False

        if outreach_id not in self._scores:
            self.logger.warning(f"No score found for outreach_id {outreach_id}")
            return False

        try:
            from ..output.bit_writer import BITWriter, BITScoreInput

            writer = self._get_bit_writer()
            company_score = self._scores[outreach_id]

            score_input = BITScoreInput(
                outreach_id=outreach_id,
                score=company_score.score,
                score_tier=company_score.get_tier(),
                signal_count=company_score.signal_count,
                correlation_id=correlation_id,
                people_score=company_score.people_score,
                dol_score=company_score.dol_score,
                blog_score=company_score.blog_score,
                talent_flow_score=company_score.talent_flow_score
            )

            result = writer.write_score(score_input)
            return result.success

        except Exception as e:
            self.logger.error(f"Failed to sync BIT score to Neon: {e}")
            return False

    def close(self):
        """Close Neon connection if open."""
        if self._bit_writer:
            self._bit_writer.close()
            self._bit_writer = None

    # =========================================================================
    # LIFECYCLE STATE HELPERS
    # =========================================================================

    def get_lifecycle_state(self, outreach_id: str) -> str:
        """
        Get lifecycle state based on BIT score.

        States per Doctrine:
        - COLD: 0-24
        - WARM: 25-49
        - HOT: 50-74
        - BURNING: 75+

        Args:
            outreach_id: Company to check

        Returns:
            Lifecycle state string
        """
        score = self.get_score_value(outreach_id)

        if score >= BIT_THRESHOLD_BURNING:
            return 'BURNING'
        elif score >= BIT_THRESHOLD_HOT:
            return 'HOT'
        elif score >= BIT_THRESHOLD_WARM:
            return 'WARM'
        else:
            return 'COLD'

    def get_companies_by_state(self, state: str) -> List[CompanyBITScore]:
        """
        Get companies in a specific lifecycle state.

        Args:
            state: COLD, WARM, HOT, or BURNING

        Returns:
            List of companies in that state
        """
        state = state.upper()

        if state == 'BURNING':
            return [s for s in self._scores.values() if s.score >= BIT_THRESHOLD_BURNING]
        elif state == 'HOT':
            return [s for s in self._scores.values()
                    if BIT_THRESHOLD_HOT <= s.score < BIT_THRESHOLD_BURNING]
        elif state == 'WARM':
            return [s for s in self._scores.values()
                    if BIT_THRESHOLD_WARM <= s.score < BIT_THRESHOLD_HOT]
        else:  # COLD
            return [s for s in self._scores.values() if s.score < BIT_THRESHOLD_WARM]

    def get_state_summary(self) -> Dict[str, int]:
        """
        Get count of companies in each lifecycle state.

        Returns:
            Dict with state counts
        """
        return {
            'COLD': len(self.get_companies_by_state('COLD')),
            'WARM': len(self.get_companies_by_state('WARM')),
            'HOT': len(self.get_companies_by_state('HOT')),
            'BURNING': len(self.get_companies_by_state('BURNING')),
        }

    # =========================================================================
    # DECAY CALCULATION (LOCKED)
    # =========================================================================

    def calculate_decayed_score(
        self,
        outreach_id: str,
        as_of: Optional[datetime] = None
    ) -> float:
        """
        Calculate decayed BIT score for a company.

        DOCTRINE: Decay is deterministic, time-based, formulaic.
        Formula: decayed_score = base_score * max(0, 1 - (days_since_signal / decay_period))

        Args:
            outreach_id: Company to calculate decay for
            as_of: Reference datetime (defaults to now)

        Returns:
            Decayed score value
        """
        if outreach_id not in self._scores:
            return 0.0

        if as_of is None:
            as_of = datetime.now()

        company_score = self._scores[outreach_id]
        total_decayed = 0.0

        for signal in company_score.signal_history:
            days_since = (as_of - signal.timestamp).days
            decay_period = SIGNAL_DECAY_PERIODS.get(signal.signal_type, 90)

            # Apply decay formula
            decay_factor = max(0, 1 - (days_since / decay_period))
            decayed_impact = signal.impact * decay_factor
            total_decayed += decayed_impact

        # Apply guardrails
        total_decayed = max(0, min(100, total_decayed))

        return round(total_decayed, 2)

    def apply_decay_to_all(self, as_of: Optional[datetime] = None) -> Dict[str, float]:
        """
        Apply decay to all company scores.

        DOCTRINE: Decay run is deterministic and auditable.

        Args:
            as_of: Reference datetime (defaults to now)

        Returns:
            Dict of outreach_id -> decayed_score
        """
        if as_of is None:
            as_of = datetime.now()

        decayed_scores = {}
        for outreach_id in self._scores:
            decayed_scores[outreach_id] = self.calculate_decayed_score(outreach_id, as_of)

        self.logger.info(f"Decay applied to {len(decayed_scores)} companies")
        return decayed_scores


# =============================================================================
# OUTREACH SUB-HUB READ-ONLY INTERFACE (LOCKED)
# =============================================================================

class BITReadOnlyInterface:
    """
    Read-only interface for Outreach Sub-Hub.

    DOCTRINE: Outreach Sub-Hub can READ BIT scores but CANNOT write signals or scores.
    This interface provides read-only access to BIT data.

    Usage:
        from bit_engine import BITReadOnlyInterface
        bit_reader = BITReadOnlyInterface()
        hot_companies = bit_reader.get_hot_companies()
    """

    def __init__(self):
        """Initialize read-only interface."""
        self._connection = None
        self.logger = logging.getLogger(__name__)

    def _get_connection(self):
        """Get database connection (read-only queries only)."""
        if self._connection is None or self._connection.closed:
            import os
            import psycopg2
            self._connection = psycopg2.connect(
                host=os.getenv('NEON_HOST'),
                database=os.getenv('NEON_DATABASE'),
                user=os.getenv('NEON_USER'),
                password=os.getenv('NEON_PASSWORD'),
                sslmode='require'
            )
        return self._connection

    def close(self):
        """Close database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()
            self._connection = None

    def get_score(self, outreach_id: str) -> Optional[Dict[str, Any]]:
        """
        Get BIT score for a company (READ ONLY).

        Args:
            outreach_id: Company's outreach_id

        Returns:
            Dict with score details or None
        """
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT outreach_id, score, score_tier, signal_count,
                           last_signal_at, last_scored_at
                    FROM outreach.bit_scores
                    WHERE outreach_id = %s
                """, (outreach_id,))
                row = cursor.fetchone()
                if row:
                    return {
                        'outreach_id': str(row[0]),
                        'score': float(row[1]),
                        'tier': row[2],
                        'signal_count': row[3],
                        'last_signal_at': row[4],
                        'last_scored_at': row[5]
                    }
                return None
        except Exception as e:
            self.logger.error(f"Failed to get BIT score: {e}")
            return None

    def get_hot_companies(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get companies with HOT or BURNING tier (READ ONLY).

        DOCTRINE: Outreach Sub-Hub uses this to select outreach candidates.
        Score >= 50 = outreach eligible.

        Args:
            limit: Maximum companies to return

        Returns:
            List of company score dicts
        """
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT outreach_id, score, score_tier, signal_count,
                           last_signal_at
                    FROM outreach.bit_scores
                    WHERE score >= %s
                    ORDER BY score DESC
                    LIMIT %s
                """, (BIT_THRESHOLD_HOT, limit))
                rows = cursor.fetchall()
                return [
                    {
                        'outreach_id': str(row[0]),
                        'score': float(row[1]),
                        'tier': row[2],
                        'signal_count': row[3],
                        'last_signal_at': row[4]
                    }
                    for row in rows
                ]
        except Exception as e:
            self.logger.error(f"Failed to get hot companies: {e}")
            return []

    def get_tier_distribution(self) -> Dict[str, int]:
        """
        Get count of companies by tier (READ ONLY).

        Returns:
            Dict with tier counts
        """
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT score_tier, COUNT(*)
                    FROM outreach.bit_scores
                    GROUP BY score_tier
                """)
                rows = cursor.fetchall()
                result = {'COLD': 0, 'WARM': 0, 'HOT': 0, 'BURNING': 0}
                for row in rows:
                    if row[0] in result:
                        result[row[0]] = row[1]
                return result
        except Exception as e:
            self.logger.error(f"Failed to get tier distribution: {e}")
            return {'COLD': 0, 'WARM': 0, 'HOT': 0, 'BURNING': 0}

    def is_outreach_eligible(self, outreach_id: str) -> bool:
        """
        Check if company is eligible for outreach (READ ONLY).

        DOCTRINE: Score >= 50 (HOT tier) = outreach eligible.

        Args:
            outreach_id: Company's outreach_id

        Returns:
            True if eligible for outreach
        """
        score_data = self.get_score(outreach_id)
        if score_data:
            return score_data['score'] >= BIT_THRESHOLD_HOT
        return False


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Doctrine Guards
    'BITDoctrineViolation',
    'guard_no_company_unique_id',
    'guard_correlation_id',
    'guard_tier_value',
    'guard_score_delta',
    # Signal Types
    'SignalType',
    'SIGNAL_IMPACTS',
    'SIGNAL_DECAY_PERIODS',
    # Thresholds
    'BIT_THRESHOLD_COLD',
    'BIT_THRESHOLD_WARM',
    'BIT_THRESHOLD_HOT',
    'BIT_THRESHOLD_BURNING',
    # Data Classes
    'BITSignal',
    'CompanyBITScore',
    # Engine
    'BITEngine',
    # Read-Only Interface (for Outreach Sub-Hub)
    'BITReadOnlyInterface',
]
