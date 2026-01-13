"""
Outreach Execution Hub - Middle Layer
======================================
Core business logic for Outreach Execution Hub.

Components:
    - outreach_hub.py: Core hub logic for campaign execution
"""

from .outreach_hub import OutreachSpoke as OutreachHub

__all__ = [
    'OutreachHub',
]
