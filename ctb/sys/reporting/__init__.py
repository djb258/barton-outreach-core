"""
Reporting Package
=================

Reporting and analytics modules for the Barton Outreach Core system.

Subpackages:
- funnel_reports: 4-Funnel GTM System analytics and forecasting
"""

from .funnel_reports import (
    FunnelMath,
    FunnelMetrics,
    ConversionRates,
    TenThreeOneRatios,
    MonthlyMovement,
    RenewalCyclicity,
    FunnelEfficiency,
    ForecastModel,
    ForecastResult,
    RevenueProjection,
    LivesProjection,
    CompoundingImpact,
    ForecastConfig,
)

__all__ = [
    # Funnel Math
    "FunnelMath",
    "FunnelMetrics",
    "ConversionRates",
    "TenThreeOneRatios",
    "MonthlyMovement",
    "RenewalCyclicity",
    "FunnelEfficiency",

    # Forecast Model
    "ForecastModel",
    "ForecastResult",
    "RevenueProjection",
    "LivesProjection",
    "CompoundingImpact",
    "ForecastConfig",
]

__version__ = "1.0.0"
