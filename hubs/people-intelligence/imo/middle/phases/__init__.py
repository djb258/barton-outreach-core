"""
People Intelligence Hub - Phases (5-8)
=======================================
People-owned phases of the enrichment pipeline.

Phase 5: Email Generation - Generate emails using Company's pattern
Phase 6: Slot Assignment - Assign people to company slots
Phase 7: Enrichment Queue - Queue for external enrichment
Phase 8: Output Writer - Write enriched data to output

NOTE: Phases 1-4 belong to Company Intelligence Hub.

CEO Email Pipeline (Hardened):
- Phases 5-8 with MillionVerifier as HARD GATE
- Only VALID emails promoted to Neon
- Deterministic, no enrichment, no retries
"""

from .phase5_email_generation import Phase5EmailGeneration
from .phase6_slot_assignment import Phase6SlotAssignment
from .phase7_enrichment_queue import Phase7EnrichmentQueue
from .phase8_output_writer import Phase8OutputWriter
from .ceo_email_pipeline import (
    CEOCandidate,
    PipelineStats,
    PipelineGuard,
    VerificationStatus,
    SlotResolutionReason,
    run_pipeline,
    load_candidates_from_csv,
    load_candidates_from_neon,
)

__all__ = [
    'Phase5EmailGeneration',
    'Phase6SlotAssignment',
    'Phase7EnrichmentQueue',
    'Phase8OutputWriter',
    # Hardened CEO Pipeline
    'CEOCandidate',
    'PipelineStats',
    'PipelineGuard',
    'VerificationStatus',
    'SlotResolutionReason',
    'run_pipeline',
    'load_candidates_from_csv',
    'load_candidates_from_neon',
]
