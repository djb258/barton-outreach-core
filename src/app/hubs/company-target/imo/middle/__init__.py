"""
Company Intelligence Hub - Middle Layer
========================================
Core business logic for Company Intelligence Hub.

Phases (Company-owned):
    - Phase 1: Company Matching
    - Phase 1b: Unmatched Hold Export
    - Phase 2: Domain Resolution
    - Phase 3: Email Pattern Waterfall
    - Phase 4: Pattern Verification

Components:
    - company_hub.py: Core hub logic
    - bit_engine.py: Buyer Intent Tool scoring
    - company_pipeline.py: Pipeline orchestration
"""

from .company_hub import CompanyHub, CompanyHubRecord, Slot
from .bit_engine import BITEngine, SignalType, SIGNAL_IMPACTS
from .company_pipeline import CompanyPipeline, PipelineRunResult

__all__ = [
    'CompanyHub',
    'CompanyHubRecord',
    'Slot',
    'BITEngine',
    'SignalType',
    'SIGNAL_IMPACTS',
    'CompanyPipeline',
    'PipelineRunResult',
]
