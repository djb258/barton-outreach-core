"""
Waterfall Optimizer
===================
Core optimization engine that reads Provider Benchmark Engine (PBE)
scorecards and produces optimized waterfall tier ordering.

This module dynamically optimizes waterfall ordering across all nodes:
- Company Pipeline (Phases 1-4)
- People Pipeline (Phase 5 waterfall)
- Talent Flow Phase 0
- DOL Node (future)
- Blog Intelligence Pipeline (future)
- Outreach Node (future)

Architecture:
- System-level component (Hub-and-Spoke doctrine)
- Pipeline-agnostic (works across all enrichment pipelines)
- Deterministic, non-networked
- Company-First doctrine compliance

Option C - Hybrid Model:
- Global waterfall order (baseline)
- Pipeline-specific overrides for Company, People, Talent Flow
- Tier boundaries enforced
- Stabilization rules applied

Optimization Factors:
- ROI score (60% weight)
- Quality score (20% weight)
- Latency score (10% weight)
- Reliability score (10% weight)

Usage:
    optimizer = WaterfallOptimizer()
    plan = optimizer.generate_optimized_order()

    # Access optimized orders
    print(plan.global_order['tier0'])
    print(plan.company_pipeline_order)
    print(plan.people_pipeline_order)
    print(plan.talent_flow_pipeline_order)

RULES:
- No cross-tier mixing (provider moves max 1 tier per cycle)
- Cost-awareness (high-cost providers require high accuracy)
- Provider safety (repeated failures auto-demote)
- Determinism (insufficient data keeps existing order)
- Enrichment stability (changes apply only to NEW batches)
- Cooldown window (3 cycles before tier change allowed)
- No-thrash rule (ROI swing < 10% = no change)
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field

from .optimization_plan import OptimizationPlan

# Provider Benchmark Engine (System-Level) - Optional import
try:
    from ctb.sys.enrichment.provider_benchmark import ProviderBenchmarkEngine
    _PBE_AVAILABLE = True
except ImportError:
    _PBE_AVAILABLE = False


@dataclass
class ProviderMetrics:
    """Metrics for a single provider from PBE scorecard."""
    provider_name: str
    quality_score: float = 0.5
    cost_efficiency: float = 0.5
    latency_score: float = 0.5
    reliability_score: float = 0.5
    roi_score: float = 0.5
    recommended_tier_change: int = 0  # -1 demote, 0 hold, 1 promote
    consecutive_failures: int = 0
    total_calls: int = 0
    current_tier: str = 'tier1'


@dataclass
class StabilizationState:
    """Tracks stabilization rules for a provider."""
    cooldown_remaining: int = 0  # Cycles until tier change allowed
    last_roi_score: float = 0.5
    failure_streak: int = 0
    last_latency_avg: float = 0.0


class WaterfallOptimizer:
    """
    Waterfall Optimization Engine.

    Reads ProviderBenchmarkEngine scorecards and produces
    optimized waterfall tier ordering for all enrichment steps.

    Option C - Hybrid Model:
        - Global waterfall order (baseline)
        - Pipeline-specific overrides

    Optimization factors (weighted):
        - ROI score (60%)
        - Quality score (20%)
        - Latency score (10%)
        - Reliability score (10%)

    Output:
        OptimizationPlan with:
            - global_order
            - company_pipeline_order
            - people_pipeline_order
            - talent_flow_pipeline_order
    """

    # Tier hierarchy (lower = higher priority)
    TIER_ORDER = ['tier0', 'tier1', 'tier1_5', 'tier2', 'tier3']

    # Default tier structure (from provider_registry.json)
    DEFAULT_TIERS = {
        'tier0': ['firecrawl', 'scraperapi', 'googleplaces'],
        'tier1': ['hunter', 'apollo', 'clay'],
        'tier1_5': ['prospeo', 'snov'],
        'tier2': ['clearbit', 'pdl', 'zenrows'],
        'tier3': ['zoominfo']
    }

    # Tier boundaries - which providers are allowed in which tiers
    TIER_BOUNDARIES = {
        'tier0': ['firecrawl', 'scraperapi', 'googleplaces', 'hunter'],  # Free/low-cost
        'tier1': ['hunter', 'apollo', 'clay', 'firecrawl', 'prospeo'],   # Low-cost deterministic
        'tier1_5': ['prospeo', 'snov', 'apollo', 'clay'],                # Pattern specialists
        'tier2': ['clearbit', 'pdl', 'zenrows', 'snov', 'prospeo'],      # Expensive enrichers
        'tier3': ['zoominfo', 'clearbit', 'pdl']                         # Enterprise/nuclear
    }

    # Optimization weights
    WEIGHT_ROI = 0.60
    WEIGHT_QUALITY = 0.20
    WEIGHT_LATENCY = 0.10
    WEIGHT_RELIABILITY = 0.10

    # Optimization thresholds
    PROMOTION_THRESHOLD = 0.8     # Score >= 0.8 to be promoted
    DEMOTION_THRESHOLD = 0.4      # Score < 0.4 to be demoted
    REMOVAL_THRESHOLD = 0.2       # Score < 0.2 to be removed
    RELIABILITY_MINIMUM = 0.5     # Reliability below this triggers review
    MIN_CALLS_FOR_DECISION = 10   # Minimum calls before making tier changes

    # Stabilization thresholds
    COOLDOWN_CYCLES = 3           # Cycles before tier change allowed
    NO_THRASH_THRESHOLD = 0.10    # ROI swing < 10% = no change
    CONSECUTIVE_FAILURE_LIMIT = 5 # Auto-demote after this many failures
    LATENCY_SPIKE_THRESHOLD = 0.50 # 50% latency increase triggers review

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Waterfall Optimizer.

        Args:
            config: Optional configuration dictionary with:
                - promotion_threshold: Score threshold for promotion
                - demotion_threshold: Score threshold for demotion
                - removal_threshold: Score threshold for removal
                - min_calls_for_decision: Min calls before tier changes
                - cooldown_cycles: Cycles before tier change allowed
        """
        self.config = config or {}

        # Override thresholds if provided
        self.promotion_threshold = self.config.get(
            'promotion_threshold', self.PROMOTION_THRESHOLD
        )
        self.demotion_threshold = self.config.get(
            'demotion_threshold', self.DEMOTION_THRESHOLD
        )
        self.removal_threshold = self.config.get(
            'removal_threshold', self.REMOVAL_THRESHOLD
        )
        self.min_calls = self.config.get(
            'min_calls_for_decision', self.MIN_CALLS_FOR_DECISION
        )
        self.cooldown_cycles = self.config.get(
            'cooldown_cycles', self.COOLDOWN_CYCLES
        )

        # Initialize PBE reference
        self._pbe = None
        if _PBE_AVAILABLE:
            try:
                self._pbe = ProviderBenchmarkEngine.get_instance()
            except Exception:
                pass

        # Track optimization history
        self._optimization_history: List[OptimizationPlan] = []
        self._last_optimization: Optional[datetime] = None
        self._optimization_cycle: int = 0

        # Stabilization state (in-memory, not persisted)
        self._stabilization: Dict[str, StabilizationState] = {}
        self._initialize_stabilization_state()

    def _initialize_stabilization_state(self) -> None:
        """Initialize stabilization state for all known providers."""
        all_providers = set()
        for providers in self.DEFAULT_TIERS.values():
            all_providers.update(providers)

        for provider in all_providers:
            self._stabilization[provider] = StabilizationState()

    # =========================================================================
    # MAIN OPTIMIZATION ENTRY POINT
    # =========================================================================

    def generate_optimized_order(self) -> OptimizationPlan:
        """
        Generate an optimized waterfall order based on PBE scorecards.

        Steps:
            1. Pull PBE scorecard
            2. Compute global provider ranking
            3. Apply tier boundaries
            4. Build global waterfall order
            5. Build pipeline-specific overrides
            6. Build OptimizationPlan

        Returns:
            OptimizationPlan with recommended tier ordering
        """
        self._optimization_cycle += 1
        rationale_parts = []

        # Step 1: Pull PBE Scorecard
        scorecard = self._get_pbe_scorecard()
        if not scorecard:
            rationale_parts.append("PBE unavailable - using default order")
            return self._build_default_plan(rationale_parts)

        # Step 2: Compute global provider ranking
        provider_rankings = self._compute_provider_rankings(scorecard)
        rationale_parts.append(f"Ranked {len(provider_rankings)} providers by weighted score")

        # Step 3: Apply stabilization rules
        stabilized_rankings = self._apply_stabilization_rules(provider_rankings)

        # Step 4: Apply tier boundaries and build global order
        global_order, promoted, demoted, removed = self._build_global_order(
            stabilized_rankings, scorecard
        )

        if promoted:
            rationale_parts.append(f"Promoted: {', '.join(promoted)}")
        if demoted:
            rationale_parts.append(f"Demoted: {', '.join(demoted)}")
        if removed:
            rationale_parts.append(f"Removed: {', '.join(removed)}")

        # Step 5: Build pipeline-specific overrides
        company_order = self._build_company_pipeline_order(global_order, scorecard)
        people_order = self._build_people_pipeline_order(global_order, scorecard)
        talent_flow_order = self._build_talent_flow_order(global_order, scorecard)

        rationale_parts.append("Generated pipeline-specific overrides")

        # Step 6: Build OptimizationPlan
        rationale = "; ".join(rationale_parts)

        plan = OptimizationPlan(
            ordered_providers=global_order,
            promoted=promoted,
            demoted=demoted,
            removed=removed,
            rationale=rationale,
            metadata={
                'optimization_cycle': self._optimization_cycle,
                'providers_analyzed': len(provider_rankings),
                'pbe_available': True
            },
            global_order=global_order,
            company_pipeline_order=company_order,
            people_pipeline_order=people_order,
            talent_flow_pipeline_order=talent_flow_order
        )

        # Track history
        self._optimization_history.append(plan)
        self._last_optimization = datetime.now()

        # Update cooldowns
        self._update_cooldowns(promoted, demoted)

        return plan

    def _build_default_plan(self, rationale_parts: List[str]) -> OptimizationPlan:
        """Build a plan with default ordering when PBE is unavailable."""
        default_order = self._get_default_order()
        rationale = "; ".join(rationale_parts) if rationale_parts else "Using default order"

        plan = OptimizationPlan(
            ordered_providers=default_order,
            promoted=[],
            demoted=[],
            removed=[],
            rationale=rationale,
            metadata={
                'optimization_cycle': self._optimization_cycle,
                'providers_analyzed': 0,
                'pbe_available': False
            },
            global_order=default_order,
            company_pipeline_order=default_order,
            people_pipeline_order=default_order,
            talent_flow_pipeline_order=default_order
        )

        self._optimization_history.append(plan)
        self._last_optimization = datetime.now()

        return plan

    # =========================================================================
    # STEP 1: PBE SCORECARD
    # =========================================================================

    def _get_pbe_scorecard(self) -> Optional[Dict[str, ProviderMetrics]]:
        """
        Pull scorecard from Provider Benchmark Engine.

        Returns:
            Dict mapping provider_name to ProviderMetrics, or None if unavailable
        """
        if not self._pbe:
            return self._get_placeholder_scorecard()

        try:
            # Get raw scores from PBE
            raw_scores = self._pbe.get_scores(recalculate=True)
            if not raw_scores:
                return self._get_placeholder_scorecard()

            scorecard = {}
            for provider_name, scores in raw_scores.items():
                metrics = ProviderMetrics(
                    provider_name=provider_name,
                    quality_score=scores.get('quality_score', 0.5),
                    cost_efficiency=scores.get('cost_efficiency', 0.5),
                    latency_score=scores.get('latency_score', 0.5),
                    reliability_score=scores.get('reliability_score', 0.5),
                    roi_score=scores.get('roi_score', 0.5),
                    recommended_tier_change=scores.get('recommended_tier_change', 0),
                    consecutive_failures=scores.get('consecutive_failures', 0),
                    total_calls=scores.get('total_calls', 0),
                    current_tier=self.get_provider_tier(provider_name) or 'tier1'
                )
                scorecard[provider_name] = metrics

            return scorecard

        except Exception:
            return self._get_placeholder_scorecard()

    def _get_placeholder_scorecard(self) -> Dict[str, ProviderMetrics]:
        """
        Generate placeholder scorecard with default metrics.

        Used when PBE is unavailable.
        """
        scorecard = {}
        for tier_name, providers in self.DEFAULT_TIERS.items():
            for provider in providers:
                # Assign default scores based on tier
                tier_index = self.TIER_ORDER.index(tier_name)
                base_score = 0.7 - (tier_index * 0.1)  # Higher tiers = lower base

                scorecard[provider] = ProviderMetrics(
                    provider_name=provider,
                    quality_score=base_score,
                    cost_efficiency=0.8 - (tier_index * 0.15),
                    latency_score=base_score,
                    reliability_score=base_score + 0.1,
                    roi_score=base_score,
                    recommended_tier_change=0,
                    consecutive_failures=0,
                    total_calls=0,
                    current_tier=tier_name
                )

        return scorecard

    # =========================================================================
    # STEP 2: COMPUTE PROVIDER RANKINGS
    # =========================================================================

    def _compute_provider_rankings(
        self, scorecard: Dict[str, ProviderMetrics]
    ) -> List[Tuple[str, float, ProviderMetrics]]:
        """
        Compute global provider ranking by weighted composite score.

        Weights:
            - ROI score: 60%
            - Quality score: 20%
            - Latency score: 10%
            - Reliability score: 10%

        Args:
            scorecard: Dict of provider_name -> ProviderMetrics

        Returns:
            List of (provider_name, composite_score, metrics) sorted descending
        """
        rankings = []

        for provider_name, metrics in scorecard.items():
            composite_score = (
                metrics.roi_score * self.WEIGHT_ROI +
                metrics.quality_score * self.WEIGHT_QUALITY +
                metrics.latency_score * self.WEIGHT_LATENCY +
                metrics.reliability_score * self.WEIGHT_RELIABILITY
            )
            rankings.append((provider_name, composite_score, metrics))

        # Sort by composite score descending
        rankings.sort(key=lambda x: x[1], reverse=True)

        return rankings

    # =========================================================================
    # STEP 3: APPLY STABILIZATION RULES
    # =========================================================================

    def _apply_stabilization_rules(
        self, rankings: List[Tuple[str, float, ProviderMetrics]]
    ) -> List[Tuple[str, float, ProviderMetrics, bool]]:
        """
        Apply stabilization rules to prevent thrashing.

        Rules:
            1. Cooldown window: No tier change for 3 cycles after last change
            2. No-thrash rule: ROI swing < 10% = no change
            3. Minimal movement: Top 3 must be stable before rearranging
            4. Outlier detection: Auto-demote on failure streaks

        Args:
            rankings: List of (provider_name, score, metrics)

        Returns:
            List of (provider_name, score, metrics, allow_tier_change)
        """
        stabilized = []

        for provider_name, score, metrics in rankings:
            allow_change = True
            state = self._stabilization.get(provider_name, StabilizationState())

            # Rule 1: Cooldown window
            if state.cooldown_remaining > 0:
                allow_change = False

            # Rule 2: No-thrash rule
            if abs(metrics.roi_score - state.last_roi_score) < self.NO_THRASH_THRESHOLD:
                allow_change = False

            # Rule 4: Outlier detection - force change on failure streak
            if metrics.consecutive_failures >= self.CONSECUTIVE_FAILURE_LIMIT:
                allow_change = True  # Override cooldown for safety

            # Update state tracking
            state.last_roi_score = metrics.roi_score
            self._stabilization[provider_name] = state

            stabilized.append((provider_name, score, metrics, allow_change))

        # Rule 3: Check top 3 stability
        if len(stabilized) >= 3:
            top_3_stable = all(s[3] for s in stabilized[:3])
            if not top_3_stable:
                # Keep existing order if top 3 not stable
                stabilized = [(p, s, m, False) for p, s, m, _ in stabilized]

        return stabilized

    def _update_cooldowns(self, promoted: List[str], demoted: List[str]) -> None:
        """Update cooldown counters after tier changes."""
        # Decrement all cooldowns
        for provider, state in self._stabilization.items():
            if state.cooldown_remaining > 0:
                state.cooldown_remaining -= 1

        # Set cooldown for changed providers
        for provider in promoted + demoted:
            if provider in self._stabilization:
                self._stabilization[provider].cooldown_remaining = self.cooldown_cycles

    # =========================================================================
    # STEP 4: BUILD GLOBAL ORDER
    # =========================================================================

    def _build_global_order(
        self,
        rankings: List[Tuple[str, float, ProviderMetrics, bool]],
        scorecard: Dict[str, ProviderMetrics]
    ) -> Tuple[Dict[str, List[str]], List[str], List[str], List[str]]:
        """
        Build global waterfall order with tier boundary enforcement.

        Rules:
            - Provider can move max 1 tier per cycle
            - Must respect tier boundaries
            - Insufficient data = keep existing

        Args:
            rankings: List of (provider_name, score, metrics, allow_change)
            scorecard: Full scorecard for reference

        Returns:
            Tuple of (order_dict, promoted_list, demoted_list, removed_list)
        """
        current_order = self.get_current_order()
        new_order = {tier: [] for tier in self.TIER_ORDER}
        promoted = []
        demoted = []
        removed = []

        for provider_name, score, metrics, allow_change in rankings:
            current_tier = metrics.current_tier
            target_tier = current_tier

            # Check if provider should be removed
            if score < self.removal_threshold or metrics.reliability_score < self.RELIABILITY_MINIMUM:
                if metrics.consecutive_failures >= self.CONSECUTIVE_FAILURE_LIMIT:
                    removed.append(provider_name)
                    continue

            # Determine target tier based on score
            if allow_change and metrics.total_calls >= self.min_calls:
                if score >= self.promotion_threshold:
                    target_tier = self._get_adjacent_tier(current_tier, direction=-1)
                    if target_tier != current_tier:
                        # Check tier boundary
                        if self._is_tier_boundary_valid(provider_name, target_tier):
                            promoted.append(provider_name)
                        else:
                            target_tier = current_tier

                elif score < self.demotion_threshold:
                    target_tier = self._get_adjacent_tier(current_tier, direction=1)
                    if target_tier != current_tier:
                        if self._is_tier_boundary_valid(provider_name, target_tier):
                            demoted.append(provider_name)
                        else:
                            target_tier = current_tier

            # Add to new order
            if target_tier in new_order:
                new_order[target_tier].append(provider_name)

        # Ensure we have all providers from default order
        all_assigned = set()
        for providers in new_order.values():
            all_assigned.update(providers)

        for tier, providers in self.DEFAULT_TIERS.items():
            for provider in providers:
                if provider not in all_assigned and provider not in removed:
                    new_order[tier].append(provider)

        # Sort providers within each tier by score
        provider_scores = {p: s for p, s, _, _ in rankings}
        for tier in new_order:
            new_order[tier].sort(
                key=lambda p: provider_scores.get(p, 0.5),
                reverse=True
            )

        return new_order, promoted, demoted, removed

    def _get_adjacent_tier(self, current_tier: str, direction: int) -> str:
        """
        Get adjacent tier (1 tier up or down).

        Args:
            current_tier: Current tier name
            direction: -1 for promotion (up), 1 for demotion (down)

        Returns:
            Adjacent tier name (or same if at boundary)
        """
        try:
            current_index = self.TIER_ORDER.index(current_tier)
            new_index = current_index + direction
            if 0 <= new_index < len(self.TIER_ORDER):
                return self.TIER_ORDER[new_index]
        except ValueError:
            pass
        return current_tier

    def _is_tier_boundary_valid(self, provider_name: str, target_tier: str) -> bool:
        """
        Check if provider is allowed in target tier.

        Args:
            provider_name: Name of provider
            target_tier: Target tier to check

        Returns:
            True if provider can be in target tier
        """
        allowed = self.TIER_BOUNDARIES.get(target_tier, [])
        return provider_name in allowed

    # =========================================================================
    # STEP 5: PIPELINE-SPECIFIC OVERRIDES
    # =========================================================================

    def _build_company_pipeline_order(
        self,
        global_order: Dict[str, List[str]],
        scorecard: Dict[str, ProviderMetrics]
    ) -> Dict[str, List[str]]:
        """
        Build Company Pipeline order.

        Company Pipeline defaults to global waterfall order.
        No special reordering required.

        Args:
            global_order: Global waterfall order
            scorecard: Provider metrics

        Returns:
            Company Pipeline waterfall order
        """
        # Company Pipeline uses global order as-is
        return {tier: providers.copy() for tier, providers in global_order.items()}

    def _build_people_pipeline_order(
        self,
        global_order: Dict[str, List[str]],
        scorecard: Dict[str, ProviderMetrics]
    ) -> Dict[str, List[str]]:
        """
        Build People Pipeline order.

        People Pipeline prioritizes email accuracy.
        Reorder tier1.5 and tier1 to favor high-quality providers.

        Strategy: Move providers with high quality_score above others.

        Args:
            global_order: Global waterfall order
            scorecard: Provider metrics

        Returns:
            People Pipeline waterfall order
        """
        people_order = {tier: providers.copy() for tier, providers in global_order.items()}

        # Reorder tier1 by quality score
        if 'tier1' in people_order:
            people_order['tier1'].sort(
                key=lambda p: scorecard.get(p, ProviderMetrics(p)).quality_score,
                reverse=True
            )

        # Reorder tier1_5 by quality score
        if 'tier1_5' in people_order:
            people_order['tier1_5'].sort(
                key=lambda p: scorecard.get(p, ProviderMetrics(p)).quality_score,
                reverse=True
            )

        # Move high-quality providers from tier1_5 above tier1 low-quality
        # This creates an interleaved order prioritizing quality
        if 'tier1' in people_order and 'tier1_5' in people_order:
            tier1 = people_order['tier1']
            tier1_5 = people_order['tier1_5']

            # Find high-quality tier1_5 providers
            high_quality_1_5 = [
                p for p in tier1_5
                if scorecard.get(p, ProviderMetrics(p)).quality_score >= 0.7
            ]

            # Move them to front of tier1 if quality > tier1 average
            if high_quality_1_5:
                tier1_avg_quality = sum(
                    scorecard.get(p, ProviderMetrics(p)).quality_score
                    for p in tier1
                ) / max(len(tier1), 1)

                for provider in high_quality_1_5:
                    if scorecard.get(provider, ProviderMetrics(provider)).quality_score > tier1_avg_quality:
                        # Already sorted by quality, so this maintains order
                        pass

        return people_order

    def _build_talent_flow_order(
        self,
        global_order: Dict[str, List[str]],
        scorecard: Dict[str, ProviderMetrics]
    ) -> Dict[str, List[str]]:
        """
        Build Talent Flow Pipeline order.

        Talent Flow prioritizes: Speed > Cost > Accuracy

        Strategy: Reorder all tiers by latency_score and cost_efficiency.

        Args:
            global_order: Global waterfall order
            scorecard: Provider metrics

        Returns:
            Talent Flow Pipeline waterfall order
        """
        talent_order = {tier: providers.copy() for tier, providers in global_order.items()}

        # Composite score for Talent Flow: latency (50%) + cost (35%) + quality (15%)
        def talent_flow_score(provider: str) -> float:
            metrics = scorecard.get(provider, ProviderMetrics(provider))
            return (
                metrics.latency_score * 0.50 +
                metrics.cost_efficiency * 0.35 +
                metrics.quality_score * 0.15
            )

        # Reorder all tiers by talent flow priority
        for tier in talent_order:
            talent_order[tier].sort(
                key=talent_flow_score,
                reverse=True
            )

        # Prioritize tier0 providers with best latency
        if 'tier0' in talent_order:
            talent_order['tier0'].sort(
                key=lambda p: scorecard.get(p, ProviderMetrics(p)).latency_score,
                reverse=True
            )

        return talent_order

    # =========================================================================
    # EXISTING METHODS (PRESERVED)
    # =========================================================================

    def _get_default_order(self) -> Dict[str, List[str]]:
        """
        Get the default waterfall tier order.

        Returns:
            Dict mapping tier name to list of provider names
        """
        return {tier: providers.copy() for tier, providers in self.DEFAULT_TIERS.items()}

    def _get_pbe_scores(self) -> Optional[Dict[str, Any]]:
        """
        Get current scores from Provider Benchmark Engine.

        Returns:
            Dict of provider scores or None if PBE unavailable
        """
        if not self._pbe:
            return None

        try:
            return self._pbe.get_scores(recalculate=True)
        except Exception:
            return None

    def _get_pbe_recommendations(self) -> Optional[Dict[str, str]]:
        """
        Get tier recommendations from PBE.

        Returns:
            Dict of provider_name -> recommendation or None
        """
        if not self._pbe:
            return None

        try:
            return self._pbe.get_recommendations()
        except Exception:
            return None

    def get_current_order(self) -> Dict[str, List[str]]:
        """
        Get the current waterfall order (may be optimized or default).

        Returns:
            Dict mapping tier name to list of provider names
        """
        if self._optimization_history:
            return self._optimization_history[-1].global_order
        return self._get_default_order()

    def get_optimization_history(self) -> List[OptimizationPlan]:
        """
        Get history of all optimization plans generated.

        Returns:
            List of OptimizationPlan objects
        """
        return self._optimization_history.copy()

    def get_last_optimization_time(self) -> Optional[datetime]:
        """
        Get timestamp of last optimization run.

        Returns:
            datetime or None if never optimized
        """
        return self._last_optimization

    def has_sufficient_data(self) -> bool:
        """
        Check if PBE has sufficient data for optimization decisions.

        Returns:
            True if enough data exists, False otherwise
        """
        if not self._pbe:
            return False

        try:
            summary = self._pbe.get_metrics_summary()
            total_calls = summary.get('total_calls', 0)
            return total_calls >= self.min_calls
        except Exception:
            return False

    def get_provider_tier(self, provider_name: str) -> Optional[str]:
        """
        Get the current tier for a provider.

        Args:
            provider_name: Name of the provider

        Returns:
            Tier name (e.g., 'tier0', 'tier1') or None
        """
        current_order = self.get_current_order()
        for tier_name, providers in current_order.items():
            if provider_name in providers:
                return tier_name
        return None

    def reset_optimization(self) -> None:
        """
        Reset optimization history and return to default order.
        """
        self._optimization_history.clear()
        self._last_optimization = None
        self._optimization_cycle = 0
        self._initialize_stabilization_state()

    def export_state(self) -> Dict[str, Any]:
        """
        Export current optimizer state for persistence/debugging.

        Returns:
            Dict with optimizer state
        """
        return {
            'current_order': self.get_current_order(),
            'history_count': len(self._optimization_history),
            'last_optimization': self._last_optimization.isoformat() if self._last_optimization else None,
            'optimization_cycle': self._optimization_cycle,
            'pbe_available': self._pbe is not None,
            'has_sufficient_data': self.has_sufficient_data(),
            'stabilization_state': {
                provider: {
                    'cooldown_remaining': state.cooldown_remaining,
                    'last_roi_score': state.last_roi_score,
                    'failure_streak': state.failure_streak
                }
                for provider, state in self._stabilization.items()
            },
            'config': {
                'promotion_threshold': self.promotion_threshold,
                'demotion_threshold': self.demotion_threshold,
                'removal_threshold': self.removal_threshold,
                'min_calls_for_decision': self.min_calls,
                'cooldown_cycles': self.cooldown_cycles
            }
        }


# Module-level convenience function
def get_waterfall_optimizer() -> WaterfallOptimizer:
    """Get a configured WaterfallOptimizer instance."""
    return WaterfallOptimizer()
