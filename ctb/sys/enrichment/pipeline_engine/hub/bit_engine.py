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
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import logging


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

    # Blog Node signals
    FUNDING_EVENT = "funding_event"
    ACQUISITION = "acquisition"
    LAYOFF = "layoff"
    LEADERSHIP_CHANGE = "leadership_change"

    # Talent Flow signals
    EXECUTIVE_JOINED = "executive_joined"
    EXECUTIVE_LEFT = "executive_left"
    TITLE_CHANGE = "title_change"


# Signal impact values
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

    # Blog Node
    SignalType.FUNDING_EVENT: 15.0,
    SignalType.ACQUISITION: 12.0,
    SignalType.LAYOFF: -3.0,
    SignalType.LEADERSHIP_CHANGE: 8.0,

    # Talent Flow
    SignalType.EXECUTIVE_JOINED: 10.0,
    SignalType.EXECUTIVE_LEFT: -5.0,
    SignalType.TITLE_CHANGE: 3.0,
}


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
    """

    def __init__(self):
        self.name = "bit_engine"
        self._scores: Dict[str, CompanyBITScore] = {}
        self._total_signals: int = 0
        self._aggregate_score: float = 0.0
        self.logger = logging.getLogger(__name__)

    def process_signal(self, signal: BITSignal):
        """
        Process a signal and update company BIT score.

        This is the core function that all spokes call to feed the hub.
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

    def create_signal(
        self,
        signal_type: SignalType,
        company_id: str,
        source_spoke: str,
        impact: Optional[float] = None,
        metadata: Dict[str, Any] = None
    ) -> BITSignal:
        """
        Create and process a signal.

        If impact not specified, uses default from SIGNAL_IMPACTS.
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

        self.process_signal(signal)
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
