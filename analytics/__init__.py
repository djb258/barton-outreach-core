"""
Analytics Module
================

Analytics and reporting for Barton Outreach.

This module provides read-only analytics and reporting capabilities.
It does NOT modify tier computation, kill switches, or hub status logic.

Components:
    - tier_telemetry: Tier distribution and drift analysis
    - hub_metrics: Hub performance metrics
"""

from ops.metrics.tier_snapshot import capture_tier_snapshot, get_tier_drift
from ops.metrics.tier_report import generate_markdown_report

__all__ = [
    'capture_tier_snapshot',
    'get_tier_drift',
    'generate_markdown_report',
]
