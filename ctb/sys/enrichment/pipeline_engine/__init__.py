"""
Pipeline Engine
===============
Multi-phase people enrichment pipeline for email generation and slot assignment.

Architecture:
    Phase 1: Company Matching (exact, fuzzy, domain)
    Phase 2: Domain Resolution (database, scraping)
    Phase 3: Email Pattern Waterfall (Tier 0/1/2)
    Phase 4: Pattern Verification (test, SMTP)
    Phase 5: Mass Email Generation
    Phase 6: Slot Assignment (CEO/CFO/HR)
    Phase 7: Enrichment Queue
    Phase 8: Output Writer

Usage:
    from pipeline_engine import PipelineEngine, PipelineConfig

    config = PipelineConfig()
    engine = PipelineEngine(config)
    results = engine.run(input_df)
"""

from .main import PipelineEngine, PipelineRun
from .phases import (
    Phase1CompanyMatching,
    Phase1bUnmatchedHoldExport,
    Phase2DomainResolution,
    Phase3EmailPatternWaterfall,
    Phase4PatternVerification,
    Phase5EmailGeneration,
    Phase6SlotAssignment,
    Phase7EnrichmentQueue,
    Phase8OutputWriter,
)
from .utils import (
    PipelineConfig,
    PipelineLogger,
    load_config,
)

__version__ = "0.1.0"
__all__ = [
    # Main
    "PipelineEngine",
    "PipelineRun",
    # Phases
    "Phase1CompanyMatching",
    "Phase1bUnmatchedHoldExport",
    "Phase2DomainResolution",
    "Phase3EmailPatternWaterfall",
    "Phase4PatternVerification",
    "Phase5EmailGeneration",
    "Phase6SlotAssignment",
    "Phase7EnrichmentQueue",
    "Phase8OutputWriter",
    # Utils
    "PipelineConfig",
    "PipelineLogger",
    "load_config",
]
