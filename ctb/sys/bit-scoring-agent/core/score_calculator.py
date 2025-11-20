"""
BIT Score Calculator
Barton Doctrine ID: 04.04.02.04.70000.003

Core scoring logic: Score = Σ(weight × signal_value × confidence × decay)

All score calculation happens here, isolated from database and triggers.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json


class ScoreCalculator:
    """
    Calculate BIT scores from signals

    Formula: Score = Σ(weight × signal_value × confidence × decay)

    Design: Pure calculation logic, no database calls
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration"""
        self.config = config
        self.scoring_config = config['scoring']

        # Cached weight/decay/confidence tables (loaded from DB at start)
        self.signal_weights: Dict[str, int] = {}
        self.confidence_modifiers: Dict[str, float] = {}

    def load_weights(self, signal_weights: Dict[str, int]):
        """Load signal weights from database"""
        self.signal_weights = signal_weights

    def load_confidence_modifiers(self, confidence_modifiers: Dict[str, float]):
        """Load confidence modifiers from database"""
        self.confidence_modifiers = confidence_modifiers

    def calculate_score(
        self,
        signals: List[Dict[str, Any]],
        decay_lookup_fn,  # Function to get decay factor by days
        person_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate BIT score from list of signals

        Args:
            signals: List of signal records
            decay_lookup_fn: Function(days_old: int) -> float (decay factor)
            person_data: Optional person data for bonus calculations

        Returns:
            {
                'raw_score': int,           # Sum without decay
                'decayed_score': int,       # Sum with decay applied
                'signal_count': int,
                'last_signal_at': datetime,
                'score_breakdown': [...]    # Details per signal
            }
        """
        if not signals:
            return {
                'raw_score': 0,
                'decayed_score': 0,
                'signal_count': 0,
                'last_signal_at': None,
                'score_breakdown': []
            }

        raw_score = 0
        decayed_score = 0
        breakdown = []
        last_signal_at = None

        for signal in signals:
            signal_type = signal['signal_type']
            signal_weight = signal.get('signal_weight') or self._get_signal_weight(signal_type)
            detected_at = signal['detected_at']

            # Get signal metadata
            metadata = signal.get('metadata', {})
            source = metadata.get('data_source', 'unknown')

            # Calculate age in days
            age_days = (datetime.now(detected_at.tzinfo) - detected_at).days

            # Get decay factor
            decay_factor = 1.0
            if self.scoring_config['decay_enabled']:
                decay_factor = decay_lookup_fn(age_days)

            # Get confidence modifier
            confidence = 1.0
            if self.scoring_config['confidence_enabled']:
                confidence = self._get_confidence_modifier(source)

            # Calculate contribution
            signal_value = 1.0  # Default signal value (could be dynamic)
            raw_contribution = int(signal_weight * signal_value)
            decayed_contribution = int(signal_weight * signal_value * confidence * decay_factor)

            raw_score += raw_contribution
            decayed_score += decayed_contribution

            # Track breakdown
            breakdown.append({
                'signal_id': signal['signal_id'],
                'signal_type': signal_type,
                'weight': signal_weight,
                'confidence': confidence,
                'decay_factor': decay_factor,
                'age_days': age_days,
                'raw_contribution': raw_contribution,
                'decayed_contribution': decayed_contribution,
                'detected_at': detected_at.isoformat()
            })

            # Track most recent signal
            if last_signal_at is None or detected_at > last_signal_at:
                last_signal_at = detected_at

        # Apply caps
        raw_score = min(raw_score, self.scoring_config['max_score_cap'])
        raw_score = max(raw_score, self.scoring_config['min_score_floor'])

        decayed_score = min(decayed_score, self.scoring_config['max_score_cap'])
        decayed_score = max(decayed_score, self.scoring_config['min_score_floor'])

        return {
            'raw_score': raw_score,
            'decayed_score': decayed_score,
            'signal_count': len(signals),
            'last_signal_at': last_signal_at,
            'score_breakdown': breakdown
        }

    def _get_signal_weight(self, signal_type: str) -> int:
        """Get weight for signal type (with fallback to default)"""
        return self.signal_weights.get(
            signal_type,
            self.scoring_config['default_signal_weight']
        )

    def _get_confidence_modifier(self, source: str) -> float:
        """Get confidence modifier for source (with fallback to neutral 1.0)"""
        return self.confidence_modifiers.get(source, 1.0)

    def get_score_tier(self, decayed_score: int, thresholds: List[Dict[str, Any]]) -> str:
        """
        Determine score tier based on thresholds

        Args:
            decayed_score: Computed score
            thresholds: List of threshold configs from database

        Returns:
            Tier name (cold/warm/engaged/hot/burning)
        """
        for threshold in thresholds:
            min_score = threshold['min_score']
            max_score = threshold['max_score']

            if max_score is None:
                # Top tier (no upper bound)
                if decayed_score >= min_score:
                    return threshold['trigger_level']
            else:
                # Bounded tier
                if min_score <= decayed_score <= max_score:
                    return threshold['trigger_level']

        # Fallback
        return 'cold'

    def should_recalculate(
        self,
        current_score: Optional[Dict[str, Any]],
        recalculation_interval_hours: int
    ) -> bool:
        """
        Determine if score should be recalculated

        Args:
            current_score: Existing score record (or None)
            recalculation_interval_hours: Min hours between recalculations

        Returns:
            True if should recalculate, False if skip
        """
        if not current_score:
            return True  # No existing score, calculate

        computed_at = current_score['computed_at']
        time_since = datetime.now(computed_at.tzinfo) - computed_at

        # Recalculate if past interval
        return time_since >= timedelta(hours=recalculation_interval_hours)

    def validate_score_increase(
        self,
        old_score: Optional[int],
        new_score: int,
        max_increase_per_day: int
    ) -> Dict[str, Any]:
        """
        Safety check: prevent runaway score increases

        Args:
            old_score: Previous score (or None)
            new_score: Newly calculated score
            max_increase_per_day: Max allowed increase

        Returns:
            {
                'valid': bool,
                'capped_score': int,
                'reason': str
            }
        """
        if old_score is None:
            # First score, no validation needed
            return {
                'valid': True,
                'capped_score': new_score,
                'reason': 'Initial score calculation'
            }

        increase = new_score - old_score

        if increase <= max_increase_per_day:
            return {
                'valid': True,
                'capped_score': new_score,
                'reason': f'Increase {increase} within limit {max_increase_per_day}'
            }

        # Cap the increase
        capped_score = old_score + max_increase_per_day

        return {
            'valid': False,
            'capped_score': capped_score,
            'reason': f'Increase {increase} exceeds limit {max_increase_per_day}, capped to {capped_score}'
        }

    def get_score_delta_analysis(
        self,
        old_score: Optional[Dict[str, Any]],
        new_score: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze score change

        Returns details about what changed and why
        """
        if not old_score:
            return {
                'is_new': True,
                'delta': new_score['decayed_score'],
                'percent_change': None,
                'tier_changed': True,
                'old_tier': None,
                'new_tier': new_score.get('score_tier', 'unknown')
            }

        old_decayed = old_score['decayed_score']
        new_decayed = new_score['decayed_score']
        delta = new_decayed - old_decayed

        percent_change = 0.0
        if old_decayed > 0:
            percent_change = (delta / old_decayed) * 100

        old_tier = old_score.get('score_tier', 'unknown')
        new_tier = new_score.get('score_tier', 'unknown')

        return {
            'is_new': False,
            'delta': delta,
            'percent_change': round(percent_change, 2),
            'tier_changed': old_tier != new_tier,
            'old_tier': old_tier,
            'new_tier': new_tier,
            'old_score': old_decayed,
            'new_score': new_decayed
        }
