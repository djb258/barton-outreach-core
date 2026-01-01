"""
Blog Content Sub-Hub (04.04.05)
================================

PURPOSE:
    Provide timing signals from news, funding events, and content sources.
    BIT modulation only - cannot mint, revive, or trigger enrichment.

LIFECYCLE GATE:
    Requires lifecycle >= ACTIVE

RULES:
    - Cannot mint or revive companies
    - Cannot trigger enrichment
    - BIT modulation only
    - Requires company_sov_id
    - Lifecycle read-only

SIGNALS EMITTED:
    - FUNDING_EVENT: +15.0
    - ACQUISITION: +12.0
    - LEADERSHIP_CHANGE: +8.0
    - EXPANSION: +7.0
    - PRODUCT_LAUNCH: +5.0
    - PARTNERSHIP: +5.0
    - LAYOFF: -3.0
    - NEGATIVE_NEWS: -5.0
"""

__version__ = "1.0.0"
__doctrine_id__ = "04.04.05"
