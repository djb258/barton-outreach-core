"""
Funnel Reports
==============

Reporting and forecasting modules for the 4-Funnel GTM System.

This package provides:
- FunnelMath: Conversion rate calculations and funnel efficiency metrics
- ForecastModel: 12-36 month revenue and lives projections
- 10-3-1 Modern Ratios analysis
- Renewal-driven cyclicity calculations
- Compounding impact modeling

Usage:
    from ctb.sys.reporting.funnel_reports import (
        FunnelMath,
        FunnelMetrics,
        ForecastModel,
        ForecastResult,
        TenThreeOneRatios
    )

    # Calculate funnel metrics
    math = FunnelMath()
    metrics = math.calculate_funnel_metrics(
        suspects=10000,
        warm=1000,
        talentflow_warm=300,
        appointments=100,
        clients=33
    )

    # Generate forecast
    forecast = ForecastModel()
    result = forecast.project_revenue(
        current_clients=100,
        avg_revenue_per_client=50000,
        months=36
    )

Doctrine Reference:
    - ctb/sys/doctrine/4_funnel_doctrine.md
    - ctb/sys/doctrine/funnel_rules.md
"""

from .funnel_math import (
    FunnelMath,
    FunnelMetrics,
    ConversionRates,
    TenThreeOneRatios,
    MonthlyMovement,
    RenewalCyclicity,
    FunnelEfficiency
)

from .forecast_model import (
    ForecastModel,
    ForecastResult,
    RevenueProjection,
    LivesProjection,
    CompoundingImpact,
    ForecastConfig
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
