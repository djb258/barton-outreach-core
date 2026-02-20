"""
Outreach Execution Hub
=======================
Campaign execution and engagement tracking.

NOTE: Core tables (campaigns, sequences, send_log, engagement_events) were
DROPPED 2026-02-20 during table consolidation Phase 1 (all had 0 rows).
This hub is scaffolded but not yet operational.

Core Metric: ENGAGEMENT_RATE

Doctrine ID: 04.04.04
"""

from .imo.middle.outreach_hub import OutreachSpoke as OutreachHub

__all__ = [
    'OutreachHub',
]
