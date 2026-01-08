"""
Company Target Sub-Hub (Execution Prep)
=======================================
PRD: Company Target (Execution Prep Sub-Hub) v3.0
Doctrine: Spine-First Architecture

PURPOSE:
Company Target is the execution-readiness sub-hub for Outreach.
It prepares records for downstream spokes (DOL, People, Blog).
It does NOT create identity - that's CL + Spine's job.

WHAT IT DOES:
- Accept outreach_id from Outreach Spine
- Derive email methodology (pattern discovery)
- Mark records as execution-ready or route to error table

WHAT IT DOES NOT DO (HARD LAW):
- Reference sovereign_id (hidden by spine)
- Mint any IDs (spine mints outreach_id)
- Perform company matching (CL's job)
- Use fuzzy logic (CL's job)
- Retry failures (FAIL is forever)

ENTRYPOINT:
    run_company_target_imo(outreach_id) -> None

Doctrine ID: 04.04.01
"""

# =============================================================================
# PRIMARY ENTRYPOINT (v3.0 - Spine-First)
# =============================================================================
from .imo.middle.company_target_imo import (
    run_company_target_imo,
    run_pending_batch,
    IMOResult,
    IMOStage,
    ErrorCode,
    MethodType,
    ENFORCE_OUTREACH_SPINE_ONLY,
)

# =============================================================================
# LEGACY EXPORTS (DEPRECATED - Use run_company_target_imo instead)
# =============================================================================
from .imo.middle.company_hub import CompanyHub, CompanyHubRecord, Slot
from .imo.middle.bit_engine import BITEngine, SignalType, SIGNAL_IMPACTS
from .imo.middle.bit_engine import BIT_THRESHOLD_WARM, BIT_THRESHOLD_HOT, BIT_THRESHOLD_BURNING
from .imo.output.neon_writer import (
    CompanyNeonWriter,
    NeonConfig,
    CompanyWriterStats,
    WriteResult,
    check_company_neon_connection,
    bootstrap_company_hub,
)
from .imo.middle.company_pipeline import CompanyPipeline, PipelineRunResult

__all__ = [
    # ==========================================================================
    # PRIMARY ENTRYPOINT (v3.0)
    # ==========================================================================
    'run_company_target_imo',  # THE entrypoint - single-pass IMO gate
    'run_pending_batch',       # Batch processor for queue
    'IMOResult',
    'IMOStage',
    'ErrorCode',
    'MethodType',
    'ENFORCE_OUTREACH_SPINE_ONLY',

    # ==========================================================================
    # LEGACY (DEPRECATED - will be removed)
    # ==========================================================================
    'CompanyPipeline',         # DEPRECATED: Use run_company_target_imo
    'PipelineRunResult',       # DEPRECATED
    'CompanyHub',              # DEPRECATED
    'CompanyHubRecord',        # DEPRECATED
    'Slot',
    'BITEngine',
    'SignalType',
    'SIGNAL_IMPACTS',
    'BIT_THRESHOLD_WARM',
    'BIT_THRESHOLD_HOT',
    'BIT_THRESHOLD_BURNING',
    'CompanyNeonWriter',       # DEPRECATED: IMO handles writes
    'NeonConfig',
    'CompanyWriterStats',
    'WriteResult',
    'check_company_neon_connection',
    'bootstrap_company_hub',
]
