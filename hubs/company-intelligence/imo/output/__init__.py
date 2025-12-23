"""
Company Intelligence Hub - Output Layer
========================================
Handles outgoing data to spokes:
    - EIN lookup requests to DOL Spoke (CONTRACT-CO-DOL)
    - Target selection to Outreach Spoke (CONTRACT-CO-OUTREACH)
    - Slot requirements to People Spoke (CONTRACT-CO-PEOPLE)

Also includes:
    - neon_writer.py: Persistence to Neon PostgreSQL
"""

from .neon_writer import (
    CompanyNeonWriter,
    NeonConfig,
    CompanyWriterStats,
    WriteResult,
    check_company_neon_connection,
    bootstrap_company_hub,
)

__all__ = [
    'CompanyNeonWriter',
    'NeonConfig',
    'CompanyWriterStats',
    'WriteResult',
    'check_company_neon_connection',
    'bootstrap_company_hub',
]
