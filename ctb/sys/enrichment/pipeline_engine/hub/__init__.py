"""
Hub - Central Axle
==================
The Company Hub is the master node. All data anchors here.

"IF company_id IS NULL OR domain IS NULL OR email_pattern IS NULL:
    STOP. Route to Company Identity Pipeline first."
-- The Golden Rule
"""

from .company_hub import CompanyHub
from .bit_engine import BITEngine

__all__ = ['CompanyHub', 'BITEngine']
