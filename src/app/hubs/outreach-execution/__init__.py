"""
Outreach Execution Hub
=======================
Owns campaign execution, sequences, and engagement tracking.

Core Entities Owned:
    - campaigns
    - sequences
    - send_log
    - engagement_events

Core Metric: ENGAGEMENT_RATE

Doctrine ID: 04.04.04
"""

from .imo.middle.outreach_hub import OutreachSpoke as OutreachHub

__all__ = [
    'OutreachHub',
]
