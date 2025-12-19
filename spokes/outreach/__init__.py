"""
Outreach Spoke - Spoke #6
=========================
Campaign targeting and outreach sequencing based on BIT scores.

Barton ID Range: 04.04.02.04.70000.###
"""

from .outreach_spoke import (
    OutreachSpoke,
    OutreachConfig,
    load_outreach_config,
    OutreachCandidate,
    CampaignTarget,
)

__all__ = [
    "OutreachSpoke",
    "OutreachConfig",
    "load_outreach_config",
    "OutreachCandidate",
    "CampaignTarget",
]
