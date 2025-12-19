"""
BIT Engine - Buyer Intent Tool
==============================
The core metric that lives INSIDE the Company Hub.

Architecture:
    ╔═════════════════════════════════════════════════╗
    ║              COMPANY HUB                        ║
    ║                                                 ║
    ║   ┌───────────────────────────────────────┐     ║
    ║   │           BIT ENGINE                  │     ║
    ║   │        (Core Metric)                  │     ║
    ║   │                                       │     ║
    ║   │   Aggregates signals from:            │     ║
    ║   │   - People Node (slot filled)         │     ║
    ║   │   - DOL Node (5500 signals)           │     ║
    ║   │   - Blog Node (news/events)           │     ║
    ║   │   - Talent Flow (movement)            │     ║
    ║   └───────────────────────────────────────┘     ║
    ║                                                 ║
    ╚═════════════════════════════════════════════════╝

BIT Score Components:
    - Slot Signals: +10 per filled executive slot
    - DOL Signals: +5 per relevant 5500 filing
    - Event Signals: +3 to +15 per news event
    - Movement Signals: +10 per detected movement

Neon Integration:
    - Signals are persisted to funnel.bit_signal_log
    - Scores are persisted to marketing.company_master.bit_score
    - Signal deduplication via hash + timestamp constraints
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import logging
import uuid


logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Types of signals that feed the BIT Engine"""
    # People Node signals
    SLOT_FILLED = "slot_filled"
    SLOT_VACATED = "slot_vacated"
    EMAIL_VERIFIED = "email_verified"
    LINKEDIN_FOUND = "linkedin_found"

    # DOL Node signals
    FORM_5500_FILED = "form_5500_filed"
    LARGE_PLAN = "large_plan"
    BROKER_CHANGE = "broker_change"

    # Blog Node signals (per PRD v2.1)
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
    # People Node
    SignalType.SLOT_FILLED: 10.0,
    SignalType.SLOT_VACATED: -5.0,
    SignalType.EMAIL_VERIFIED: 3.0,
    SignalType.LINKEDIN_FOUND: 2.0,

    # DOL Node
    SignalType.FORM_5500_FILED: 5.0,
    SignalType.LARGE_PLAN: 8.0,
    SignalType.BROKER_CHANGE: 7.0,

    # Blog Node (per PRD v2.1)
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

# BIT Score Thresholds (per Funnel Doctrine)
# These define when a company moves between lifecycle states
BIT_THRESHOLD_WARM = 25      # SUSPECT -> WARM
BIT_THRESHOLD_HOT = 50       # WARM -> HOT
BIT_THRESHOLD_BURNING = 75   # HOT -> BURNING


@dataclass
class BITSignal:
    """A single signal feeding the BIT Engine"""
    signal_type: SignalType
    company_id: str
    source_spoke: str
    impact: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'signal_type': self.signal_type.value,
            'company_id': self.company_id,
            'source_spoke': self.source_spoke,
            'impact': self.impact,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class CompanyBITScore:
    """BIT score for a single company"""
    company_id: str
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
        if signal.source_spoke == 'people_node':
            self.people_score += signal.impact
        elif signal.source_spoke == 'dol_node':
            self.dol_score += signal.impact
        elif signal.source_spoke == 'blog_node':
            self.blog_score += signal.impact
        elif signal.source_spoke == 'talent_flow':
            self.talent_flow_score += signal.impact

    def breakdown(self) -> Dict[str, float]:
        """Get score breakdown by source"""
        return {
            'total': self.score,
            'people_node': self.people_score,
            'dol_node': self.dol_score,
            'blog_node': self.blog_score,
            'talent_flow': self.talent_flow_score
        }


class BITEngine:
    """
    Buyer Intent Tool - Core Metric Engine.

    Lives INSIDE the Company Hub. Aggregates signals from all spokes
    to calculate buyer intent scores.

    Neon Integration:
    - Set persist_to_neon=True to persist signals to database
    - Signals logged to funnel.bit_signal_log
    - Scores updated in marketing.company_master.bit_score
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
        self._neon_writer = None

    def _get_neon_writer(self):
        """Get or create Neon writer instance."""
        if self._neon_writer is None:
            from .neon_writer import CompanyNeonWriter
            self._neon_writer = CompanyNeonWriter()
        return self._neon_writer

    def process_signal(
        self,
        signal: BITSignal,
        correlation_id: str = None
    ):
        """
        Process a signal and update company BIT score.

        This is the core function that all spokes call to feed the hub.

        Args:
            signal: BIT signal to process
            correlation_id: Pipeline trace ID for Neon persistence
        """
        company_id = signal.company_id

        # Initialize score if new company
        if company_id not in self._scores:
            self._scores[company_id] = CompanyBITScore(company_id=company_id)

        # Add signal to company score
        self._scores[company_id].add_signal(signal)

        # Update aggregates
        self._total_signals += 1
        self._aggregate_score += signal.impact

        self.logger.info(
            f"BIT Signal: {signal.signal_type.value} for {company_id} "
            f"(impact: {signal.impact:+.1f}, new score: {self._scores[company_id].score:.1f})"
        )

        # Persist to Neon if enabled
        if self.persist_to_neon:
            self._persist_signal_to_neon(signal, correlation_id)

    def _persist_signal_to_neon(
        self,
        signal: BITSignal,
        correlation_id: str = None
    ):
        """
        Persist a signal to Neon database.

        Args:
            signal: BIT signal to persist
            correlation_id: Pipeline trace ID
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        try:
            writer = self._get_neon_writer()

            # Log the signal
            writer.log_bit_signal(
                company_id=signal.company_id,
                signal_type=signal.signal_type.value,
                signal_impact=signal.impact,
                source_spoke=signal.source_spoke,
                correlation_id=correlation_id
            )

            # Update the company's BIT score
            new_score = self._scores[signal.company_id].score
            writer.update_bit_score(
                company_id=signal.company_id,
                bit_score=new_score,
                correlation_id=correlation_id
            )

            self.logger.debug(
                f"Persisted BIT signal to Neon: {signal.signal_type.value} "
                f"for {signal.company_id}"
            )

        except Exception as e:
            self.logger.error(f"Failed to persist BIT signal to Neon: {e}")

    def create_signal(
        self,
        signal_type: SignalType,
        company_id: str,
        source_spoke: str,
        impact: Optional[float] = None,
        metadata: Dict[str, Any] = None,
        correlation_id: str = None
    ) -> BITSignal:
        """
        Create and process a signal.

        If impact not specified, uses default from SIGNAL_IMPACTS.

        Args:
            signal_type: Type of signal
            company_id: Company receiving the signal
            source_spoke: Spoke that generated the signal
            impact: Signal impact (uses default if not specified)
            metadata: Additional signal metadata
            correlation_id: Pipeline trace ID for Neon persistence
        """
        if impact is None:
            impact = SIGNAL_IMPACTS.get(signal_type, 0.0)

        signal = BITSignal(
            signal_type=signal_type,
            company_id=company_id,
            source_spoke=source_spoke,
            impact=impact,
            metadata=metadata or {}
        )

        self.process_signal(signal, correlation_id)
        return signal

    def get_score(self, company_id: str) -> Optional[CompanyBITScore]:
        """Get BIT score for a company"""
        return self._scores.get(company_id)

    def get_score_value(self, company_id: str) -> float:
        """Get just the numeric score for a company"""
        score = self._scores.get(company_id)
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
                'company_id': s.company_id,
                'score': s.score,
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
            writer = self._get_neon_writer()
            companies = writer.load_all_companies()

            count = 0
            for company in companies:
                company_id = company.get('company_unique_id')
                bit_score = company.get('bit_score', 0.0)

                if company_id and bit_score:
                    if company_id not in self._scores:
                        self._scores[company_id] = CompanyBITScore(company_id=company_id)
                    self._scores[company_id].score = bit_score
                    count += 1

            self.logger.info(f"Loaded BIT scores for {count} companies from Neon")
            return count

        except Exception as e:
            self.logger.error(f"Failed to load BIT scores from Neon: {e}")
            return 0

    def sync_score_to_neon(
        self,
        company_id: str,
        correlation_id: str = None
    ) -> bool:
        """
        Sync a company's BIT score to Neon.

        Args:
            company_id: Company to sync
            correlation_id: Pipeline trace ID

        Returns:
            True if successful
        """
        if not self.persist_to_neon:
            self.logger.warning("Neon persistence not enabled")
            return False

        if company_id not in self._scores:
            self.logger.warning(f"No score found for company {company_id}")
            return False

        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        try:
            writer = self._get_neon_writer()
            writer.update_bit_score(
                company_id=company_id,
                bit_score=self._scores[company_id].score,
                correlation_id=correlation_id
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to sync BIT score to Neon: {e}")
            return False

    def close(self):
        """Close Neon connection if open."""
        if self._neon_writer:
            self._neon_writer.close()
            self._neon_writer = None

    # =========================================================================
    # LIFECYCLE STATE HELPERS
    # =========================================================================

    def get_lifecycle_state(self, company_id: str) -> str:
        """
        Get lifecycle state based on BIT score.

        States per Funnel Doctrine:
        - SUSPECT: 0-24
        - WARM: 25-49
        - HOT: 50-74
        - BURNING: 75+

        Args:
            company_id: Company to check

        Returns:
            Lifecycle state string
        """
        score = self.get_score_value(company_id)

        if score >= BIT_THRESHOLD_BURNING:
            return 'BURNING'
        elif score >= BIT_THRESHOLD_HOT:
            return 'HOT'
        elif score >= BIT_THRESHOLD_WARM:
            return 'WARM'
        else:
            return 'SUSPECT'

    def get_companies_by_state(self, state: str) -> List[CompanyBITScore]:
        """
        Get companies in a specific lifecycle state.

        Args:
            state: SUSPECT, WARM, HOT, or BURNING

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
        else:  # SUSPECT
            return [s for s in self._scores.values() if s.score < BIT_THRESHOLD_WARM]

    def get_state_summary(self) -> Dict[str, int]:
        """
        Get count of companies in each lifecycle state.

        Returns:
            Dict with state counts
        """
        return {
            'SUSPECT': len(self.get_companies_by_state('SUSPECT')),
            'WARM': len(self.get_companies_by_state('WARM')),
            'HOT': len(self.get_companies_by_state('HOT')),
            'BURNING': len(self.get_companies_by_state('BURNING')),
        }
