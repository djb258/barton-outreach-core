"""
Forecast Model
==============

Revenue and lives projection model for 4-Funnel GTM System.

Calculates:
- 12-36 month revenue projections
- Lives (employee) projections
- Compounding impact modeling
- Renewal-driven growth curves
- Scenario analysis (conservative, moderate, aggressive)

All functions are pure math - no database fetches.

Usage:
    from forecast_model import ForecastModel, ForecastConfig

    model = ForecastModel()
    result = model.project_revenue(
        current_clients=100,
        avg_revenue_per_client=50000,
        months=36
    )
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import math as stdlib_math
from datetime import datetime, date


class GrowthScenario(Enum):
    """Growth scenario types for forecasting."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


@dataclass
class ForecastConfig:
    """Configuration for forecast model."""
    # Growth rates (monthly)
    monthly_new_client_rate: float = 0.05       # 5% monthly new client growth
    monthly_churn_rate: float = 0.02            # 2% monthly churn
    monthly_expansion_rate: float = 0.01        # 1% monthly expansion (upsells)

    # Revenue assumptions
    avg_revenue_per_client: float = 50000.0     # Average annual revenue per client
    avg_lives_per_client: float = 150.0         # Average employees per client
    revenue_per_life: float = 333.33            # Revenue per employee ($50k/150)

    # Retention
    annual_retention_rate: float = 0.85         # 85% annual retention
    renewal_uplift: float = 0.03                # 3% price increase on renewal

    # Seasonality (index 0 = January)
    monthly_seasonality: List[float] = field(default_factory=lambda: [
        0.06, 0.07, 0.08,  # Q1: 21%
        0.09, 0.09, 0.10,  # Q2: 28%
        0.08, 0.08, 0.09,  # Q3: 25%
        0.10, 0.10, 0.06   # Q4: 26%
    ])

    # Compounding factors
    referral_rate: float = 0.10                 # 10% of clients refer new business
    cross_sell_rate: float = 0.15               # 15% buy additional products

    def get_seasonality_factor(self, month: int) -> float:
        """Get seasonality factor for a month (1-12)."""
        if 1 <= month <= 12:
            return self.monthly_seasonality[month - 1]
        return 1.0 / 12

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'growth_rates': {
                'monthly_new_client': self.monthly_new_client_rate,
                'monthly_churn': self.monthly_churn_rate,
                'monthly_expansion': self.monthly_expansion_rate
            },
            'revenue': {
                'avg_per_client': self.avg_revenue_per_client,
                'avg_lives_per_client': self.avg_lives_per_client,
                'per_life': self.revenue_per_life
            },
            'retention': {
                'annual_rate': self.annual_retention_rate,
                'renewal_uplift': self.renewal_uplift
            },
            'compounding': {
                'referral_rate': self.referral_rate,
                'cross_sell_rate': self.cross_sell_rate
            }
        }


@dataclass
class MonthlyProjection:
    """Single month projection data."""
    month: int                      # Sequential month (1-36)
    calendar_month: int             # Calendar month (1-12)
    year: int                       # Year

    # Client counts
    starting_clients: int = 0
    new_clients: int = 0
    churned_clients: int = 0
    ending_clients: int = 0

    # Lives (employees)
    starting_lives: int = 0
    new_lives: int = 0
    churned_lives: int = 0
    ending_lives: int = 0

    # Revenue
    recurring_revenue: float = 0.0
    new_revenue: float = 0.0
    churned_revenue: float = 0.0
    expansion_revenue: float = 0.0
    total_revenue: float = 0.0

    # Growth metrics
    client_growth_rate: float = 0.0
    revenue_growth_rate: float = 0.0
    net_revenue_retention: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'period': {
                'month': self.month,
                'calendar_month': self.calendar_month,
                'year': self.year
            },
            'clients': {
                'starting': self.starting_clients,
                'new': self.new_clients,
                'churned': self.churned_clients,
                'ending': self.ending_clients
            },
            'lives': {
                'starting': self.starting_lives,
                'new': self.new_lives,
                'churned': self.churned_lives,
                'ending': self.ending_lives
            },
            'revenue': {
                'recurring': self.recurring_revenue,
                'new': self.new_revenue,
                'churned': self.churned_revenue,
                'expansion': self.expansion_revenue,
                'total': self.total_revenue
            },
            'growth': {
                'client_growth_rate': self.client_growth_rate,
                'revenue_growth_rate': self.revenue_growth_rate,
                'net_revenue_retention': self.net_revenue_retention
            }
        }


@dataclass
class RevenueProjection:
    """Revenue projection summary."""
    months: int
    starting_arr: float = 0.0       # Starting Annual Recurring Revenue
    ending_arr: float = 0.0         # Ending ARR
    total_revenue: float = 0.0      # Total revenue over period

    # Growth
    arr_growth_pct: float = 0.0
    cagr: float = 0.0               # Compound Annual Growth Rate

    # Components
    new_arr: float = 0.0
    churned_arr: float = 0.0
    expansion_arr: float = 0.0
    net_new_arr: float = 0.0

    # Monthly breakdown
    monthly_projections: List[MonthlyProjection] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'summary': {
                'months': self.months,
                'starting_arr': self.starting_arr,
                'ending_arr': self.ending_arr,
                'total_revenue': self.total_revenue,
                'arr_growth_pct': self.arr_growth_pct,
                'cagr': self.cagr
            },
            'components': {
                'new_arr': self.new_arr,
                'churned_arr': self.churned_arr,
                'expansion_arr': self.expansion_arr,
                'net_new_arr': self.net_new_arr
            },
            'monthly': [m.to_dict() for m in self.monthly_projections]
        }


@dataclass
class LivesProjection:
    """Lives (employee count) projection summary."""
    months: int
    starting_lives: int = 0
    ending_lives: int = 0

    # Growth
    total_new_lives: int = 0
    total_churned_lives: int = 0
    net_lives_growth: int = 0
    lives_growth_pct: float = 0.0

    # Monthly breakdown
    monthly_lives: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'summary': {
                'months': self.months,
                'starting_lives': self.starting_lives,
                'ending_lives': self.ending_lives,
                'net_growth': self.net_lives_growth,
                'growth_pct': self.lives_growth_pct
            },
            'monthly_lives': self.monthly_lives
        }


@dataclass
class CompoundingImpact:
    """Compounding impact analysis."""
    # Base projection without compounding
    base_revenue: float = 0.0
    base_clients: int = 0

    # With compounding effects
    compounded_revenue: float = 0.0
    compounded_clients: int = 0

    # Impact breakdown
    referral_revenue: float = 0.0
    referral_clients: int = 0
    cross_sell_revenue: float = 0.0
    price_uplift_revenue: float = 0.0

    # Multiplier
    compounding_multiplier: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'base': {
                'revenue': self.base_revenue,
                'clients': self.base_clients
            },
            'compounded': {
                'revenue': self.compounded_revenue,
                'clients': self.compounded_clients
            },
            'impact': {
                'referral_revenue': self.referral_revenue,
                'referral_clients': self.referral_clients,
                'cross_sell_revenue': self.cross_sell_revenue,
                'price_uplift_revenue': self.price_uplift_revenue
            },
            'multiplier': self.compounding_multiplier
        }


@dataclass
class ForecastResult:
    """Complete forecast result package."""
    scenario: GrowthScenario
    config: ForecastConfig
    revenue: RevenueProjection
    lives: LivesProjection
    compounding: CompoundingImpact

    # Metadata
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    forecast_start: Optional[str] = None
    forecast_end: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'metadata': {
                'scenario': self.scenario.value,
                'generated_at': self.generated_at,
                'forecast_start': self.forecast_start,
                'forecast_end': self.forecast_end
            },
            'config': self.config.to_dict(),
            'revenue': self.revenue.to_dict(),
            'lives': self.lives.to_dict(),
            'compounding': self.compounding.to_dict()
        }


class ForecastModel:
    """
    Revenue and lives forecasting model.

    Provides pure math functions for projecting business growth.
    No database access - all data is passed in.
    """

    # Scenario multipliers
    SCENARIO_MULTIPLIERS = {
        GrowthScenario.CONSERVATIVE: 0.7,
        GrowthScenario.MODERATE: 1.0,
        GrowthScenario.AGGRESSIVE: 1.4
    }

    def __init__(self, config: ForecastConfig = None):
        """
        Initialize ForecastModel.

        Args:
            config: Optional ForecastConfig (uses defaults if not provided)
        """
        self.config = config or ForecastConfig()

    # ==========================================
    # CORE PROJECTION FUNCTIONS
    # ==========================================

    def project_month(self, starting_clients: int, starting_revenue: float,
                      month: int, year: int,
                      scenario: GrowthScenario = GrowthScenario.MODERATE) -> MonthlyProjection:
        """
        Project a single month.

        Args:
            starting_clients: Client count at month start
            starting_revenue: MRR at month start
            month: Calendar month (1-12)
            year: Year
            scenario: Growth scenario

        Returns:
            MonthlyProjection for the month
        """
        multiplier = self.SCENARIO_MULTIPLIERS[scenario]
        seasonality = self.config.get_seasonality_factor(month)

        # Calculate new clients (with seasonality)
        base_new = starting_clients * self.config.monthly_new_client_rate * multiplier
        new_clients = int(base_new * (seasonality * 12))  # Normalize seasonality

        # Calculate churn
        churned_clients = int(starting_clients * self.config.monthly_churn_rate / multiplier)

        # Ending clients
        ending_clients = starting_clients + new_clients - churned_clients

        # Lives calculation
        starting_lives = int(starting_clients * self.config.avg_lives_per_client)
        new_lives = int(new_clients * self.config.avg_lives_per_client)
        churned_lives = int(churned_clients * self.config.avg_lives_per_client)
        ending_lives = starting_lives + new_lives - churned_lives

        # Revenue calculation (monthly)
        monthly_avg_revenue = self.config.avg_revenue_per_client / 12
        recurring_revenue = starting_clients * monthly_avg_revenue
        new_revenue = new_clients * monthly_avg_revenue
        churned_revenue = churned_clients * monthly_avg_revenue
        expansion_revenue = starting_clients * monthly_avg_revenue * self.config.monthly_expansion_rate * multiplier
        total_revenue = recurring_revenue + new_revenue - churned_revenue + expansion_revenue

        # Growth rates
        client_growth = ((ending_clients - starting_clients) / starting_clients * 100
                         if starting_clients > 0 else 0.0)
        revenue_growth = ((total_revenue - recurring_revenue) / recurring_revenue * 100
                          if recurring_revenue > 0 else 0.0)

        # Net Revenue Retention (NRR)
        base_revenue = starting_clients * monthly_avg_revenue
        retained_revenue = (starting_clients - churned_clients) * monthly_avg_revenue + expansion_revenue
        nrr = (retained_revenue / base_revenue * 100) if base_revenue > 0 else 100.0

        return MonthlyProjection(
            month=1,  # Will be set by caller
            calendar_month=month,
            year=year,
            starting_clients=starting_clients,
            new_clients=new_clients,
            churned_clients=churned_clients,
            ending_clients=ending_clients,
            starting_lives=starting_lives,
            new_lives=new_lives,
            churned_lives=churned_lives,
            ending_lives=ending_lives,
            recurring_revenue=recurring_revenue,
            new_revenue=new_revenue,
            churned_revenue=churned_revenue,
            expansion_revenue=expansion_revenue,
            total_revenue=total_revenue,
            client_growth_rate=client_growth,
            revenue_growth_rate=revenue_growth,
            net_revenue_retention=nrr
        )

    def project_revenue(self, current_clients: int,
                        avg_revenue_per_client: float = None,
                        months: int = 36,
                        start_month: int = None,
                        start_year: int = None,
                        scenario: GrowthScenario = GrowthScenario.MODERATE) -> RevenueProjection:
        """
        Project revenue over time.

        Args:
            current_clients: Starting client count
            avg_revenue_per_client: Annual revenue per client (uses config default if None)
            months: Number of months to project (12, 24, or 36)
            start_month: Starting calendar month (1-12, default: current month)
            start_year: Starting year (default: current year)
            scenario: Growth scenario

        Returns:
            RevenueProjection with monthly breakdown
        """
        if avg_revenue_per_client:
            self.config.avg_revenue_per_client = avg_revenue_per_client

        # Default start date
        now = datetime.now()
        start_month = start_month or now.month
        start_year = start_year or now.year

        # Initialize projection
        projection = RevenueProjection(months=months)
        projection.starting_arr = current_clients * self.config.avg_revenue_per_client

        # Track running totals
        clients = current_clients
        running_revenue = projection.starting_arr / 12  # Monthly

        calendar_month = start_month
        calendar_year = start_year

        for m in range(1, months + 1):
            # Project this month
            monthly = self.project_month(
                starting_clients=clients,
                starting_revenue=running_revenue,
                month=calendar_month,
                year=calendar_year,
                scenario=scenario
            )
            monthly.month = m

            # Track totals
            projection.new_arr += monthly.new_revenue * 12
            projection.churned_arr += monthly.churned_revenue * 12
            projection.expansion_arr += monthly.expansion_revenue * 12
            projection.total_revenue += monthly.total_revenue

            projection.monthly_projections.append(monthly)

            # Update running state
            clients = monthly.ending_clients
            running_revenue = monthly.total_revenue

            # Advance calendar
            calendar_month += 1
            if calendar_month > 12:
                calendar_month = 1
                calendar_year += 1

        # Calculate final metrics
        projection.ending_arr = clients * self.config.avg_revenue_per_client
        projection.net_new_arr = projection.ending_arr - projection.starting_arr
        projection.arr_growth_pct = (
            (projection.ending_arr - projection.starting_arr) / projection.starting_arr * 100
            if projection.starting_arr > 0 else 0.0
        )

        # CAGR calculation
        years = months / 12
        if projection.starting_arr > 0 and years > 0:
            projection.cagr = (
                (projection.ending_arr / projection.starting_arr) ** (1 / years) - 1
            ) * 100

        return projection

    def project_lives(self, current_clients: int,
                      avg_lives_per_client: float = None,
                      months: int = 36,
                      scenario: GrowthScenario = GrowthScenario.MODERATE) -> LivesProjection:
        """
        Project lives (employee count) over time.

        Args:
            current_clients: Starting client count
            avg_lives_per_client: Average employees per client (uses config default if None)
            months: Number of months to project
            scenario: Growth scenario

        Returns:
            LivesProjection with monthly breakdown
        """
        if avg_lives_per_client:
            self.config.avg_lives_per_client = avg_lives_per_client

        # Use revenue projection for client growth
        revenue_proj = self.project_revenue(
            current_clients=current_clients,
            months=months,
            scenario=scenario
        )

        projection = LivesProjection(months=months)
        projection.starting_lives = int(current_clients * self.config.avg_lives_per_client)

        for monthly in revenue_proj.monthly_projections:
            projection.monthly_lives.append(monthly.ending_lives)
            projection.total_new_lives += monthly.new_lives
            projection.total_churned_lives += monthly.churned_lives

        projection.ending_lives = projection.monthly_lives[-1] if projection.monthly_lives else projection.starting_lives
        projection.net_lives_growth = projection.ending_lives - projection.starting_lives
        projection.lives_growth_pct = (
            projection.net_lives_growth / projection.starting_lives * 100
            if projection.starting_lives > 0 else 0.0
        )

        return projection

    # ==========================================
    # COMPOUNDING IMPACT
    # ==========================================

    def calculate_compounding_impact(self, current_clients: int,
                                      months: int = 36,
                                      scenario: GrowthScenario = GrowthScenario.MODERATE) -> CompoundingImpact:
        """
        Calculate compounding impact (referrals, cross-sells, price uplifts).

        Args:
            current_clients: Starting client count
            months: Projection period
            scenario: Growth scenario

        Returns:
            CompoundingImpact analysis
        """
        multiplier = self.SCENARIO_MULTIPLIERS[scenario]

        # Base projection (without compounding)
        base_proj = self.project_revenue(
            current_clients=current_clients,
            months=months,
            scenario=scenario
        )

        impact = CompoundingImpact()
        impact.base_revenue = base_proj.total_revenue
        impact.base_clients = base_proj.monthly_projections[-1].ending_clients if base_proj.monthly_projections else current_clients

        # Calculate compounding effects

        # Referral revenue: % of clients refer new business
        referral_clients = int(impact.base_clients * self.config.referral_rate * (months / 12) * multiplier)
        referral_revenue = referral_clients * self.config.avg_revenue_per_client * (months / 24)  # Partial year

        # Cross-sell revenue: % of clients buy additional products
        cross_sell_revenue = (impact.base_clients * self.config.cross_sell_rate *
                               self.config.avg_revenue_per_client * 0.3 * multiplier)  # 30% uplift

        # Price uplift: Annual increases on renewals
        years = months / 12
        price_uplift_revenue = 0.0
        for year in range(1, int(years) + 1):
            # Each year, renewal uplift applies to retained base
            retained = impact.base_clients * (self.config.annual_retention_rate ** year)
            price_uplift_revenue += retained * self.config.avg_revenue_per_client * self.config.renewal_uplift

        impact.referral_clients = referral_clients
        impact.referral_revenue = referral_revenue
        impact.cross_sell_revenue = cross_sell_revenue
        impact.price_uplift_revenue = price_uplift_revenue

        # Totals
        impact.compounded_clients = impact.base_clients + referral_clients
        impact.compounded_revenue = (impact.base_revenue + referral_revenue +
                                      cross_sell_revenue + price_uplift_revenue)

        impact.compounding_multiplier = (
            impact.compounded_revenue / impact.base_revenue
            if impact.base_revenue > 0 else 1.0
        )

        return impact

    # ==========================================
    # SCENARIO ANALYSIS
    # ==========================================

    def generate_scenarios(self, current_clients: int,
                            months: int = 36) -> Dict[str, ForecastResult]:
        """
        Generate all three scenarios (conservative, moderate, aggressive).

        Args:
            current_clients: Starting client count
            months: Projection period

        Returns:
            Dict with scenario name -> ForecastResult
        """
        results = {}

        for scenario in GrowthScenario:
            revenue = self.project_revenue(current_clients, months=months, scenario=scenario)
            lives = self.project_lives(current_clients, months=months, scenario=scenario)
            compounding = self.calculate_compounding_impact(current_clients, months, scenario)

            results[scenario.value] = ForecastResult(
                scenario=scenario,
                config=self.config,
                revenue=revenue,
                lives=lives,
                compounding=compounding
            )

        return results

    def generate_forecast(self, current_clients: int,
                           avg_revenue_per_client: float = None,
                           avg_lives_per_client: float = None,
                           months: int = 36,
                           scenario: GrowthScenario = GrowthScenario.MODERATE) -> ForecastResult:
        """
        Generate complete forecast for a single scenario.

        Args:
            current_clients: Starting client count
            avg_revenue_per_client: Annual revenue per client (optional)
            avg_lives_per_client: Employees per client (optional)
            months: Projection period (12, 24, or 36)
            scenario: Growth scenario

        Returns:
            ForecastResult with all projections
        """
        # Update config if custom values provided
        if avg_revenue_per_client:
            self.config.avg_revenue_per_client = avg_revenue_per_client
        if avg_lives_per_client:
            self.config.avg_lives_per_client = avg_lives_per_client

        revenue = self.project_revenue(current_clients, months=months, scenario=scenario)
        lives = self.project_lives(current_clients, months=months, scenario=scenario)
        compounding = self.calculate_compounding_impact(current_clients, months, scenario)

        now = datetime.now()
        end_date = datetime(now.year + (months // 12), now.month, 1)

        return ForecastResult(
            scenario=scenario,
            config=self.config,
            revenue=revenue,
            lives=lives,
            compounding=compounding,
            forecast_start=now.strftime('%Y-%m'),
            forecast_end=end_date.strftime('%Y-%m')
        )

    # ==========================================
    # UTILITY FUNCTIONS
    # ==========================================

    def calculate_break_even(self, target_revenue: float,
                              current_clients: int,
                              scenario: GrowthScenario = GrowthScenario.MODERATE) -> int:
        """
        Calculate months to reach target revenue.

        Args:
            target_revenue: Target ARR
            current_clients: Starting client count
            scenario: Growth scenario

        Returns:
            Months to break even (max 60)
        """
        for months in range(1, 61):
            proj = self.project_revenue(current_clients, months=months, scenario=scenario)
            if proj.ending_arr >= target_revenue:
                return months
        return 60  # Max projection period

    def calculate_client_target(self, target_revenue: float,
                                 avg_revenue_per_client: float = None) -> int:
        """
        Calculate clients needed to hit revenue target.

        Args:
            target_revenue: Target ARR
            avg_revenue_per_client: Revenue per client (uses config default if None)

        Returns:
            Required client count
        """
        avg_rev = avg_revenue_per_client or self.config.avg_revenue_per_client
        if avg_rev <= 0:
            return 0
        return stdlib_math.ceil(target_revenue / avg_rev)

    def calculate_cagr(self, starting_value: float, ending_value: float,
                        years: float) -> float:
        """
        Calculate Compound Annual Growth Rate.

        Args:
            starting_value: Initial value
            ending_value: Final value
            years: Number of years

        Returns:
            CAGR as percentage
        """
        if starting_value <= 0 or years <= 0:
            return 0.0
        return ((ending_value / starting_value) ** (1 / years) - 1) * 100

    def calculate_payback_months(self, cac: float, monthly_revenue: float) -> float:
        """
        Calculate customer acquisition cost payback period.

        Args:
            cac: Customer acquisition cost
            monthly_revenue: Monthly revenue per customer

        Returns:
            Months to payback CAC
        """
        if monthly_revenue <= 0:
            return float('inf')
        return cac / monthly_revenue

    def calculate_ltv(self, avg_revenue_per_client: float = None,
                       retention_years: float = None) -> float:
        """
        Calculate customer lifetime value.

        Args:
            avg_revenue_per_client: Annual revenue (uses config default if None)
            retention_years: Average retention in years (default: calculated from rate)

        Returns:
            Lifetime value
        """
        avg_rev = avg_revenue_per_client or self.config.avg_revenue_per_client

        if retention_years is None:
            # Calculate from retention rate: 1 / (1 - retention_rate)
            churn_rate = 1 - self.config.annual_retention_rate
            retention_years = 1 / churn_rate if churn_rate > 0 else 10

        return avg_rev * retention_years
