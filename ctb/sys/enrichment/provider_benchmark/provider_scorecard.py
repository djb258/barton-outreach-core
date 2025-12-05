"""
Provider Scorecard
==================
Calculates ROI and quality scores for enrichment providers.

Uses metrics from ProviderMetrics and cost data from provider_cost_profile.json
to produce actionable tier recommendations.

Scoring Formula:
    provider_score = (quality_score * 0.4) + (cost_efficiency * 0.3) + (latency_score * 0.2) + (reliability * 0.1)

Where:
    quality_score = verified_hits / patterns_found (0-1)
    cost_efficiency = 1 - (cost_per_success / max_cost_per_success)
    latency_score = 1 - (latency_mean / max_latency)
    reliability = 1 - (errors / calls_made)

Tier Recommendations:
    - promote: score >= 0.8 and in lower tier
    - demote: score < 0.4
    - remove: score < 0.2 or reliability < 0.5
    - keep: all others

Architecture:
- System-level component (Hub-and-Spoke doctrine)
- Read-only analysis of metrics
- Deterministic, non-networked
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class TierRecommendation(Enum):
    """Tier recommendation outcomes."""
    PROMOTE = "promote"
    DEMOTE = "demote"
    REMOVE = "remove"
    KEEP = "keep"


@dataclass
class ProviderScore:
    """Score breakdown for a single provider."""
    provider_name: str
    overall_score: float
    quality_score: float
    cost_efficiency: float
    latency_score: float
    reliability_score: float
    tier_recommendation: TierRecommendation
    current_tier: int
    recommended_tier: Optional[int] = None
    cost_per_success: float = 0.0
    latency_mean_ms: float = 0.0
    total_calls: int = 0
    success_count: int = 0
    failure_count: int = 0
    calculated_at: datetime = None

    def __post_init__(self):
        if self.calculated_at is None:
            self.calculated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'provider_name': self.provider_name,
            'overall_score': round(self.overall_score, 4),
            'quality_score': round(self.quality_score, 4),
            'cost_efficiency': round(self.cost_efficiency, 4),
            'latency_score': round(self.latency_score, 4),
            'reliability_score': round(self.reliability_score, 4),
            'tier_recommendation': self.tier_recommendation.value,
            'current_tier': self.current_tier,
            'recommended_tier': self.recommended_tier,
            'cost_per_success': round(self.cost_per_success, 6),
            'latency_mean_ms': round(self.latency_mean_ms, 2),
            'total_calls': self.total_calls,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'calculated_at': self.calculated_at.isoformat() if self.calculated_at else None
        }


class ProviderScorecard:
    """
    Calculates provider performance using:

      cost_per_success
      quality_score (verified_hits / patterns_found)
      latency_mean

    Produces:
      provider_score
      tier_recommendation

    Scoring weights (configurable):
      quality: 40%
      cost_efficiency: 30%
      latency: 20%
      reliability: 10%

    Usage:
        scorecard = ProviderScorecard()
        scores = scorecard.calculate(metrics.export_metrics(), cost_profile)

        for provider, score in scores.items():
            print(f"{provider}: {score['overall_score']} - {score['tier_recommendation']}")
    """

    # Scoring weights
    WEIGHT_QUALITY = 0.4
    WEIGHT_COST = 0.3
    WEIGHT_LATENCY = 0.2
    WEIGHT_RELIABILITY = 0.1

    # Thresholds for recommendations
    THRESHOLD_PROMOTE = 0.8
    THRESHOLD_DEMOTE = 0.4
    THRESHOLD_REMOVE = 0.2
    THRESHOLD_RELIABILITY_MIN = 0.5

    # Normalization caps
    MAX_LATENCY_MS = 5000.0  # 5 seconds considered worst case
    MAX_COST_PER_SUCCESS = 0.50  # $0.50 per success considered worst case

    def __init__(
        self,
        weight_quality: float = None,
        weight_cost: float = None,
        weight_latency: float = None,
        weight_reliability: float = None
    ):
        """
        Initialize scorecard with optional custom weights.

        Args:
            weight_quality: Weight for quality score (default: 0.4)
            weight_cost: Weight for cost efficiency (default: 0.3)
            weight_latency: Weight for latency score (default: 0.2)
            weight_reliability: Weight for reliability (default: 0.1)
        """
        self._weight_quality = weight_quality or self.WEIGHT_QUALITY
        self._weight_cost = weight_cost or self.WEIGHT_COST
        self._weight_latency = weight_latency or self.WEIGHT_LATENCY
        self._weight_reliability = weight_reliability or self.WEIGHT_RELIABILITY

        # Normalize weights to sum to 1.0
        total = self._weight_quality + self._weight_cost + self._weight_latency + self._weight_reliability
        if total != 1.0:
            self._weight_quality /= total
            self._weight_cost /= total
            self._weight_latency /= total
            self._weight_reliability /= total

        self._last_calculation: Optional[datetime] = None
        self._scores: Dict[str, ProviderScore] = {}

    def calculate(
        self,
        metrics: Dict[str, Any],
        cost_profile: Dict[str, Any],
        registry: Dict[str, Any] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate scores for all providers with metrics.

        Args:
            metrics: Output from ProviderMetrics.export_metrics()
            cost_profile: Provider cost configuration (from JSON)
            registry: Optional provider registry with tier info

        Returns:
            Dict of provider_name → {score, tier_recommendation, ...}
        """
        self._scores = {}
        self._last_calculation = datetime.now()

        providers_data = metrics.get('providers', {})

        for provider_name, provider_metrics in providers_data.items():
            score = self._calculate_provider_score(
                provider_name,
                provider_metrics,
                cost_profile.get(provider_name, {}),
                registry.get(provider_name, {}) if registry else {}
            )
            self._scores[provider_name] = score

        return {name: score.to_dict() for name, score in self._scores.items()}

    def _calculate_provider_score(
        self,
        provider_name: str,
        metrics: Dict[str, Any],
        cost_info: Dict[str, Any],
        registry_info: Dict[str, Any]
    ) -> ProviderScore:
        """
        Calculate score for a single provider.

        Args:
            provider_name: Name of the provider
            metrics: Metrics for this provider
            cost_info: Cost profile for this provider
            registry_info: Registry info with tier

        Returns:
            ProviderScore with all calculated values
        """
        # Extract metrics
        calls_made = metrics.get('calls_made', 0)
        patterns_found = metrics.get('patterns_found', 0)
        verified_hits = metrics.get('verified_hits', 0)
        errors = metrics.get('errors', 0) + metrics.get('timeouts', 0)
        latency_mean = metrics.get('latency_mean_ms', 0.0)
        cost_accumulated = metrics.get('cost_accumulated', 0.0)

        # Current tier from registry
        current_tier = int(registry_info.get('tier', 1))

        # Calculate quality score (verified_hits / patterns_found)
        quality_score = 0.0
        if patterns_found > 0:
            quality_score = verified_hits / patterns_found

        # Calculate cost per success
        cost_per_success = 0.0
        if verified_hits > 0:
            cost_per_success = cost_accumulated / verified_hits
        elif patterns_found > 0:
            cost_per_success = cost_accumulated / patterns_found
        elif calls_made > 0:
            cost_per_success = cost_accumulated / calls_made

        # Calculate cost efficiency (inverse normalized)
        cost_efficiency = 1.0
        if cost_per_success > 0:
            cost_efficiency = max(0.0, 1.0 - (cost_per_success / self.MAX_COST_PER_SUCCESS))

        # Calculate latency score (inverse normalized)
        latency_score = 1.0
        if latency_mean > 0:
            latency_score = max(0.0, 1.0 - (latency_mean / self.MAX_LATENCY_MS))

        # Calculate reliability score
        reliability_score = 1.0
        if calls_made > 0:
            reliability_score = max(0.0, 1.0 - (errors / calls_made))

        # Calculate overall score
        overall_score = (
            (quality_score * self._weight_quality) +
            (cost_efficiency * self._weight_cost) +
            (latency_score * self._weight_latency) +
            (reliability_score * self._weight_reliability)
        )

        # Determine tier recommendation
        tier_recommendation = self._get_tier_recommendation(
            overall_score,
            reliability_score,
            current_tier
        )

        # Calculate recommended tier
        recommended_tier = self._calculate_recommended_tier(
            tier_recommendation,
            current_tier
        )

        return ProviderScore(
            provider_name=provider_name,
            overall_score=overall_score,
            quality_score=quality_score,
            cost_efficiency=cost_efficiency,
            latency_score=latency_score,
            reliability_score=reliability_score,
            tier_recommendation=tier_recommendation,
            current_tier=current_tier,
            recommended_tier=recommended_tier,
            cost_per_success=cost_per_success,
            latency_mean_ms=latency_mean,
            total_calls=calls_made,
            success_count=verified_hits,
            failure_count=errors
        )

    def _get_tier_recommendation(
        self,
        overall_score: float,
        reliability_score: float,
        current_tier: int
    ) -> TierRecommendation:
        """
        Determine tier recommendation based on scores.

        Args:
            overall_score: Overall provider score
            reliability_score: Reliability component
            current_tier: Current tier assignment

        Returns:
            TierRecommendation enum value
        """
        # Remove if very low score or unreliable
        if overall_score < self.THRESHOLD_REMOVE:
            return TierRecommendation.REMOVE

        if reliability_score < self.THRESHOLD_RELIABILITY_MIN:
            return TierRecommendation.REMOVE

        # Demote if below threshold
        if overall_score < self.THRESHOLD_DEMOTE:
            return TierRecommendation.DEMOTE

        # Promote if high performer in lower tier
        if overall_score >= self.THRESHOLD_PROMOTE and current_tier > 0:
            return TierRecommendation.PROMOTE

        return TierRecommendation.KEEP

    def _calculate_recommended_tier(
        self,
        recommendation: TierRecommendation,
        current_tier: int
    ) -> Optional[int]:
        """
        Calculate the recommended tier based on recommendation.

        Args:
            recommendation: Tier recommendation
            current_tier: Current tier

        Returns:
            Recommended tier number or None if no change
        """
        if recommendation == TierRecommendation.PROMOTE:
            return max(0, current_tier - 1)
        elif recommendation == TierRecommendation.DEMOTE:
            return current_tier + 1
        elif recommendation == TierRecommendation.REMOVE:
            return None  # Indicates removal
        return current_tier  # KEEP

    def get_scores(self) -> Dict[str, ProviderScore]:
        """Get all calculated scores as ProviderScore objects."""
        return self._scores.copy()

    def get_recommendations(self) -> Dict[str, TierRecommendation]:
        """Get recommendations for all providers."""
        return {
            name: score.tier_recommendation
            for name, score in self._scores.items()
        }

    def get_providers_by_recommendation(
        self,
        recommendation: TierRecommendation
    ) -> List[str]:
        """
        Get providers with a specific recommendation.

        Args:
            recommendation: TierRecommendation to filter by

        Returns:
            List of provider names
        """
        return [
            name for name, score in self._scores.items()
            if score.tier_recommendation == recommendation
        ]

    def get_top_performers(self, n: int = 5) -> List[ProviderScore]:
        """
        Get top N performing providers.

        Args:
            n: Number of providers to return

        Returns:
            List of ProviderScore sorted by overall_score descending
        """
        sorted_scores = sorted(
            self._scores.values(),
            key=lambda x: x.overall_score,
            reverse=True
        )
        return sorted_scores[:n]

    def get_underperformers(self, threshold: float = None) -> List[ProviderScore]:
        """
        Get providers performing below threshold.

        Args:
            threshold: Score threshold (default: THRESHOLD_DEMOTE)

        Returns:
            List of ProviderScore below threshold
        """
        threshold = threshold or self.THRESHOLD_DEMOTE
        return [
            score for score in self._scores.values()
            if score.overall_score < threshold
        ]

    def export_scorecard(self) -> Dict[str, Any]:
        """
        Export full scorecard data.

        Returns:
            Dict with all scores and metadata
        """
        return {
            'calculated_at': self._last_calculation.isoformat() if self._last_calculation else None,
            'weights': {
                'quality': self._weight_quality,
                'cost': self._weight_cost,
                'latency': self._weight_latency,
                'reliability': self._weight_reliability
            },
            'thresholds': {
                'promote': self.THRESHOLD_PROMOTE,
                'demote': self.THRESHOLD_DEMOTE,
                'remove': self.THRESHOLD_REMOVE,
                'reliability_min': self.THRESHOLD_RELIABILITY_MIN
            },
            'provider_count': len(self._scores),
            'recommendations_summary': {
                'promote': len(self.get_providers_by_recommendation(TierRecommendation.PROMOTE)),
                'demote': len(self.get_providers_by_recommendation(TierRecommendation.DEMOTE)),
                'remove': len(self.get_providers_by_recommendation(TierRecommendation.REMOVE)),
                'keep': len(self.get_providers_by_recommendation(TierRecommendation.KEEP))
            },
            'scores': {name: score.to_dict() for name, score in self._scores.items()}
        }

    def get_tier_optimization_plan(self) -> Dict[str, Any]:
        """
        Generate a tier optimization plan based on scores.

        Returns:
            Dict with recommended changes and expected impact
        """
        plan = {
            'generated_at': datetime.now().isoformat(),
            'actions': [],
            'summary': {
                'total_providers': len(self._scores),
                'changes_recommended': 0,
                'promotions': 0,
                'demotions': 0,
                'removals': 0
            }
        }

        for name, score in self._scores.items():
            if score.tier_recommendation != TierRecommendation.KEEP:
                action = {
                    'provider': name,
                    'action': score.tier_recommendation.value,
                    'current_tier': score.current_tier,
                    'recommended_tier': score.recommended_tier,
                    'overall_score': round(score.overall_score, 4),
                    'rationale': self._get_action_rationale(score)
                }
                plan['actions'].append(action)
                plan['summary']['changes_recommended'] += 1

                if score.tier_recommendation == TierRecommendation.PROMOTE:
                    plan['summary']['promotions'] += 1
                elif score.tier_recommendation == TierRecommendation.DEMOTE:
                    plan['summary']['demotions'] += 1
                elif score.tier_recommendation == TierRecommendation.REMOVE:
                    plan['summary']['removals'] += 1

        return plan

    def _get_action_rationale(self, score: ProviderScore) -> str:
        """Generate human-readable rationale for a recommendation."""
        reasons = []

        if score.overall_score < self.THRESHOLD_REMOVE:
            reasons.append(f"Very low overall score ({score.overall_score:.2f})")

        if score.reliability_score < self.THRESHOLD_RELIABILITY_MIN:
            reasons.append(f"Unreliable ({score.failure_count} failures)")

        if score.quality_score < 0.3:
            reasons.append(f"Low verification rate ({score.quality_score:.1%})")

        if score.cost_per_success > 0.10:
            reasons.append(f"High cost per success (${score.cost_per_success:.4f})")

        if score.overall_score >= self.THRESHOLD_PROMOTE:
            reasons.append(f"High performer ({score.overall_score:.2f}) in lower tier")

        return "; ".join(reasons) if reasons else "Performance within acceptable range"
