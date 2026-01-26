"""
Company Target Sub-Hub
======================
The Company Target Sub-Hub is the internal anchor of the Hub & Spoke architecture.
All other sub-hubs connect to Company Target for company identity validation.

Core Entities Owned:
    - company_master
    - slot_requirements (requirements only - assignments are in People Hub)
    - bit_scores
    - domain
    - email_pattern

Core Metric: BIT_SCORE

"IF company_id IS NULL OR domain IS NULL OR email_pattern IS NULL:
    STOP. Route to Company Identity Pipeline first."
-- The Golden Rule

Doctrine ID: 04.04.01
"""

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
    # Company Pipeline (main entry point)
    'CompanyPipeline',
    'PipelineRunResult',
    # Company Hub
    'CompanyHub',
    'CompanyHubRecord',
    'Slot',
    # BIT Engine
    'BITEngine',
    'SignalType',
    'SIGNAL_IMPACTS',
    'BIT_THRESHOLD_WARM',
    'BIT_THRESHOLD_HOT',
    'BIT_THRESHOLD_BURNING',
    # Neon Writer
    'CompanyNeonWriter',
    'NeonConfig',
    'CompanyWriterStats',
    'WriteResult',
    'check_company_neon_connection',
    'bootstrap_company_hub',
]
