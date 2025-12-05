"""
Optimization Plan
=================
Data container for a single waterfall optimization pass.

This class holds the results of a WaterfallOptimizer.generate_optimized_order() call,
including the new tier ordering, provider movements, and rationale.

Option C - Hybrid Model:
- global_order: Baseline waterfall order
- company_pipeline_order: Company Pipeline specific order
- people_pipeline_order: People Pipeline specific order (prioritizes quality)
- talent_flow_pipeline_order: Talent Flow specific order (prioritizes speed)

Architecture:
- Pure data container (no business logic)
- Immutable after creation
- JSON-serializable for persistence/debugging

Usage:
    plan = OptimizationPlan(
        ordered_providers={'tier0': [...], 'tier1': [...]},
        promoted=['hunter'],
        demoted=['clearbit'],
        removed=[],
        rationale="Hunter promoted due to high ROI score",
        global_order={'tier0': [...], ...},
        company_pipeline_order={'tier0': [...], ...},
        people_pipeline_order={'tier0': [...], ...},
        talent_flow_pipeline_order={'tier0': [...], ...}
    )

    # Access plan data
    print(plan.global_order)
    print(plan.company_pipeline_order)
    print(plan.people_pipeline_order)
    print(plan.talent_flow_pipeline_order)
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


class OptimizationPlan:
    """
    Data container for a single optimization pass.

    Option C - Hybrid Model Attributes:
        global_order: Global waterfall order (baseline)
        company_pipeline_order: Company Pipeline specific order
        people_pipeline_order: People Pipeline order (quality-focused)
        talent_flow_pipeline_order: Talent Flow order (speed-focused)

    Movement Tracking:
        promoted: List of provider names that were promoted (moved up a tier)
        demoted: List of provider names that were demoted (moved down a tier)
        removed: List of provider names that were removed from waterfall

    Metadata:
        rationale: Text summary explaining the optimization decisions
        timestamp: When this plan was generated
        metadata: Optional additional data for debugging/analysis
    """

    def __init__(
        self,
        ordered_providers: Dict[str, List[str]],
        promoted: List[str],
        demoted: List[str],
        removed: List[str],
        rationale: str,
        metadata: Optional[Dict[str, Any]] = None,
        # Pipeline-specific orders (Option C - Hybrid Model)
        global_order: Optional[Dict[str, List[str]]] = None,
        company_pipeline_order: Optional[Dict[str, List[str]]] = None,
        people_pipeline_order: Optional[Dict[str, List[str]]] = None,
        talent_flow_pipeline_order: Optional[Dict[str, List[str]]] = None
    ):
        """
        Initialize an OptimizationPlan.

        Args:
            ordered_providers: Dict mapping tier name to list of provider names (legacy)
            promoted: List of provider names promoted to higher tier
            demoted: List of provider names demoted to lower tier
            removed: List of provider names removed from waterfall
            rationale: Human-readable explanation of optimization decisions
            metadata: Optional additional context data
            global_order: Global waterfall order (Option C)
            company_pipeline_order: Company Pipeline specific order
            people_pipeline_order: People Pipeline specific order
            talent_flow_pipeline_order: Talent Flow specific order
        """
        # Legacy compatibility
        self.ordered_providers = ordered_providers

        # Movement tracking
        self.promoted = promoted
        self.demoted = demoted
        self.removed = removed

        # Rationale and metadata
        self.rationale = rationale
        self.timestamp = datetime.now()
        self.metadata = metadata or {}

        # Pipeline-specific orders (Option C - Hybrid Model)
        # Default to ordered_providers if not provided
        self.global_order = global_order or ordered_providers
        self.company_pipeline_order = company_pipeline_order or self.global_order
        self.people_pipeline_order = people_pipeline_order or self.global_order
        self.talent_flow_pipeline_order = talent_flow_pipeline_order or self.global_order

    @property
    def has_changes(self) -> bool:
        """Check if this plan contains any changes from previous order."""
        return bool(self.promoted or self.demoted or self.removed)

    @property
    def total_providers(self) -> int:
        """Count total providers across all tiers in global order."""
        return sum(len(providers) for providers in self.global_order.values())

    @property
    def tier_count(self) -> int:
        """Count number of tiers in the plan."""
        return len(self.global_order)

    @property
    def has_pipeline_overrides(self) -> bool:
        """Check if pipeline-specific orders differ from global."""
        return (
            self.company_pipeline_order != self.global_order or
            self.people_pipeline_order != self.global_order or
            self.talent_flow_pipeline_order != self.global_order
        )

    def get_tier_providers(self, tier_name: str, pipeline: str = 'global') -> List[str]:
        """
        Get providers for a specific tier in a specific pipeline.

        Args:
            tier_name: Name of tier (e.g., 'tier0', 'tier1')
            pipeline: Pipeline name ('global', 'company', 'people', 'talent_flow')

        Returns:
            List of provider names in that tier, or empty list if tier not found
        """
        order = self._get_pipeline_order(pipeline)
        return order.get(tier_name, [])

    def get_provider_tier(self, provider_name: str, pipeline: str = 'global') -> Optional[str]:
        """
        Find which tier a provider belongs to in a specific pipeline.

        Args:
            provider_name: Name of the provider
            pipeline: Pipeline name ('global', 'company', 'people', 'talent_flow')

        Returns:
            Tier name or None if provider not in any tier
        """
        order = self._get_pipeline_order(pipeline)
        for tier_name, providers in order.items():
            if provider_name in providers:
                return tier_name
        return None

    def _get_pipeline_order(self, pipeline: str) -> Dict[str, List[str]]:
        """
        Get the order for a specific pipeline.

        Args:
            pipeline: Pipeline name

        Returns:
            Order dict for that pipeline
        """
        pipeline_map = {
            'global': self.global_order,
            'company': self.company_pipeline_order,
            'company_pipeline': self.company_pipeline_order,
            'people': self.people_pipeline_order,
            'people_pipeline': self.people_pipeline_order,
            'talent_flow': self.talent_flow_pipeline_order,
            'talent_flow_pipeline': self.talent_flow_pipeline_order
        }
        return pipeline_map.get(pipeline, self.global_order)

    def get_pipeline_differences(self) -> Dict[str, Dict[str, Any]]:
        """
        Get differences between global and pipeline-specific orders.

        Returns:
            Dict with differences for each pipeline
        """
        differences = {}

        for pipeline_name, pipeline_order in [
            ('company', self.company_pipeline_order),
            ('people', self.people_pipeline_order),
            ('talent_flow', self.talent_flow_pipeline_order)
        ]:
            diff = {'tier_diffs': {}}

            for tier_name in self.global_order.keys():
                global_providers = self.global_order.get(tier_name, [])
                pipeline_providers = pipeline_order.get(tier_name, [])

                if global_providers != pipeline_providers:
                    diff['tier_diffs'][tier_name] = {
                        'global': global_providers,
                        'pipeline': pipeline_providers
                    }

            if diff['tier_diffs']:
                differences[pipeline_name] = diff

        return differences

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert plan to dictionary for serialization.

        Returns:
            Dict representation of the plan
        """
        return {
            # Legacy field
            'ordered_providers': self.ordered_providers,

            # Movement tracking
            'promoted': self.promoted,
            'demoted': self.demoted,
            'removed': self.removed,

            # Metadata
            'rationale': self.rationale,
            'timestamp': self.timestamp.isoformat(),
            'has_changes': self.has_changes,
            'total_providers': self.total_providers,
            'tier_count': self.tier_count,
            'metadata': self.metadata,

            # Pipeline-specific orders (Option C)
            'global_order': self.global_order,
            'company_pipeline_order': self.company_pipeline_order,
            'people_pipeline_order': self.people_pipeline_order,
            'talent_flow_pipeline_order': self.talent_flow_pipeline_order,
            'has_pipeline_overrides': self.has_pipeline_overrides
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OptimizationPlan':
        """
        Create an OptimizationPlan from a dictionary.

        Args:
            data: Dict with plan data

        Returns:
            OptimizationPlan instance
        """
        plan = cls(
            ordered_providers=data.get('ordered_providers', {}),
            promoted=data.get('promoted', []),
            demoted=data.get('demoted', []),
            removed=data.get('removed', []),
            rationale=data.get('rationale', ''),
            metadata=data.get('metadata', {}),
            global_order=data.get('global_order'),
            company_pipeline_order=data.get('company_pipeline_order'),
            people_pipeline_order=data.get('people_pipeline_order'),
            talent_flow_pipeline_order=data.get('talent_flow_pipeline_order')
        )
        # Restore timestamp if provided
        if 'timestamp' in data:
            try:
                plan.timestamp = datetime.fromisoformat(data['timestamp'])
            except (ValueError, TypeError):
                pass
        return plan

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"OptimizationPlan("
            f"tiers={self.tier_count}, "
            f"providers={self.total_providers}, "
            f"promoted={len(self.promoted)}, "
            f"demoted={len(self.demoted)}, "
            f"removed={len(self.removed)}, "
            f"has_overrides={self.has_pipeline_overrides})"
        )

    def __str__(self) -> str:
        """Human-readable string representation."""
        lines = [
            f"Optimization Plan ({self.timestamp.strftime('%Y-%m-%d %H:%M:%S')})",
            f"  Tiers: {self.tier_count}",
            f"  Total Providers: {self.total_providers}",
        ]
        if self.promoted:
            lines.append(f"  Promoted: {', '.join(self.promoted)}")
        if self.demoted:
            lines.append(f"  Demoted: {', '.join(self.demoted)}")
        if self.removed:
            lines.append(f"  Removed: {', '.join(self.removed)}")
        if self.has_pipeline_overrides:
            lines.append("  Pipeline Overrides: Yes")
        lines.append(f"  Rationale: {self.rationale}")
        return '\n'.join(lines)

    def get_waterfall_profiles(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Get all waterfall profiles in a single dict.

        Returns:
            Dict with keys 'global', 'company_pipeline', 'people_pipeline', 'talent_flow_pipeline'
        """
        return {
            'global': self.global_order,
            'company_pipeline': self.company_pipeline_order,
            'people_pipeline': self.people_pipeline_order,
            'talent_flow_pipeline': self.talent_flow_pipeline_order
        }
