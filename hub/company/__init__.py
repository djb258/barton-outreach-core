"""
Hub - Central Axle
==================
The Company Hub is the master node. All data anchors here.

"IF company_id IS NULL OR domain IS NULL OR email_pattern IS NULL:
    STOP. Route to Company Identity Pipeline first."
-- The Golden Rule

Usage:
    from hub.company import CompanyPipeline, SignalType

    # Initialize pipeline with Neon persistence
    pipeline = CompanyPipeline(persist_to_neon=True)
    pipeline.bootstrap()

    # Emit BIT signals
    pipeline.emit_bit_signal(
        company_id="04.04.01.XX.XXXXX.XXX",
        signal_type=SignalType.SLOT_FILLED,
        source_spoke="people_node"
    )
"""

from .company_hub import CompanyHub, CompanyHubRecord, Slot
from .bit_engine import BITEngine, SignalType, SIGNAL_IMPACTS
from .bit_engine import BIT_THRESHOLD_WARM, BIT_THRESHOLD_HOT, BIT_THRESHOLD_BURNING
from .neon_writer import (
    CompanyNeonWriter,
    NeonConfig,
    CompanyWriterStats,
    WriteResult,
    check_company_neon_connection,
    bootstrap_company_hub,
)
from .company_pipeline import CompanyPipeline, PipelineRunResult

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
