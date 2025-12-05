"""
Funnel Math
===========

Mathematical functions for 4-Funnel GTM System analytics.

Calculates:
- Stage-to-stage conversion rates
- Total funnel efficiency
- 10-3-1 Modern Ratios
- Monthly movement percentages
- Renewal-driven cyclicity

All functions are pure math - no database fetches.

Usage:
    from funnel_math import FunnelMath, FunnelMetrics

    math = FunnelMath()
    metrics = math.calculate_funnel_metrics(
        suspects=10000,
        warm=1000,
        talentflow_warm=300,
        appointments=100,
        clients=33
    )
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import math as stdlib_math


class FunnelStage(Enum):
    """Funnel stages in the 4-Funnel GTM System."""
    SUSPECT = "suspect"
    WARM = "warm"
    TALENTFLOW_WARM = "talentflow_warm"
    APPOINTMENT = "appointment"
    CLIENT = "client"


@dataclass
class ConversionRates:
    """Stage-to-stage conversion rates."""
    suspect_to_warm: float = 0.0
    warm_to_talentflow: float = 0.0
    talentflow_to_appointment: float = 0.0
    appointment_to_client: float = 0.0

    # Alternative paths
    suspect_to_talentflow: float = 0.0  # Direct TalentFlow signal
    warm_to_appointment: float = 0.0     # Skip TalentFlow

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            'suspect_to_warm': self.suspect_to_warm,
            'warm_to_talentflow': self.warm_to_talentflow,
            'talentflow_to_appointment': self.talentflow_to_appointment,
            'appointment_to_client': self.appointment_to_client,
            'suspect_to_talentflow': self.suspect_to_talentflow,
            'warm_to_appointment': self.warm_to_appointment
        }


@dataclass
class TenThreeOneRatios:
    """
    10-3-1 Modern Sales Ratios.

    Industry standard metrics:
    - 10 qualified leads -> 3 appointments -> 1 client
    - Updated for modern B2B SaaS/services
    """
    leads_per_client: float = 10.0      # Qualified leads needed per client
    appointments_per_client: float = 3.0  # Appointments needed per client
    client_rate: float = 1.0             # Base client (1)

    # Actual performance vs target
    actual_leads_per_client: float = 0.0
    actual_appointments_per_client: float = 0.0

    # Performance indicators
    leads_efficiency: float = 0.0   # < 1.0 = better than target
    appointment_efficiency: float = 0.0

    @property
    def is_above_target(self) -> bool:
        """Check if performance exceeds 10-3-1 targets."""
        return (self.actual_leads_per_client <= self.leads_per_client and
                self.actual_appointments_per_client <= self.appointments_per_client)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'target': {
                'leads_per_client': self.leads_per_client,
                'appointments_per_client': self.appointments_per_client,
                'client_rate': self.client_rate
            },
            'actual': {
                'leads_per_client': self.actual_leads_per_client,
                'appointments_per_client': self.actual_appointments_per_client
            },
            'efficiency': {
                'leads': self.leads_efficiency,
                'appointments': self.appointment_efficiency
            },
            'is_above_target': self.is_above_target
        }


@dataclass
class MonthlyMovement:
    """Monthly movement percentages between funnel stages."""
    month: int  # 1-12 or sequential month number
    year: Optional[int] = None

    # Movement counts
    suspects_added: int = 0
    suspects_to_warm: int = 0
    warm_to_talentflow: int = 0
    talentflow_to_appointment: int = 0
    appointments_to_client: int = 0

    # Churn/exits
    suspects_churned: int = 0
    warm_churned: int = 0
    unsubscribes: int = 0
    disqualified: int = 0

    # Movement percentages (calculated)
    suspect_warm_pct: float = 0.0
    warm_talentflow_pct: float = 0.0
    talentflow_appointment_pct: float = 0.0
    appointment_client_pct: float = 0.0
    churn_rate: float = 0.0

    def calculate_percentages(self, suspect_base: int, warm_base: int,
                              talentflow_base: int, appointment_base: int) -> None:
        """Calculate movement percentages from base counts."""
        self.suspect_warm_pct = (self.suspects_to_warm / suspect_base * 100
                                  if suspect_base > 0 else 0.0)
        self.warm_talentflow_pct = (self.warm_to_talentflow / warm_base * 100
                                     if warm_base > 0 else 0.0)
        self.talentflow_appointment_pct = (self.talentflow_to_appointment / talentflow_base * 100
                                            if talentflow_base > 0 else 0.0)
        self.appointment_client_pct = (self.appointments_to_client / appointment_base * 100
                                        if appointment_base > 0 else 0.0)

        total_exits = self.suspects_churned + self.warm_churned + self.unsubscribes + self.disqualified
        total_base = suspect_base + warm_base + talentflow_base + appointment_base
        self.churn_rate = (total_exits / total_base * 100) if total_base > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'period': {'month': self.month, 'year': self.year},
            'movements': {
                'suspects_added': self.suspects_added,
                'suspects_to_warm': self.suspects_to_warm,
                'warm_to_talentflow': self.warm_to_talentflow,
                'talentflow_to_appointment': self.talentflow_to_appointment,
                'appointments_to_client': self.appointments_to_client
            },
            'exits': {
                'suspects_churned': self.suspects_churned,
                'warm_churned': self.warm_churned,
                'unsubscribes': self.unsubscribes,
                'disqualified': self.disqualified
            },
            'percentages': {
                'suspect_warm_pct': self.suspect_warm_pct,
                'warm_talentflow_pct': self.warm_talentflow_pct,
                'talentflow_appointment_pct': self.talentflow_appointment_pct,
                'appointment_client_pct': self.appointment_client_pct,
                'churn_rate': self.churn_rate
            }
        }


@dataclass
class RenewalCyclicity:
    """
    Renewal-driven cyclicity calculations.

    Models the natural rhythm of B2B renewals:
    - Annual renewal cycles (Q4 heavy)
    - Multi-year contract patterns
    - Seasonal variation factors
    """
    # Renewal timing weights (sum = 1.0)
    q1_weight: float = 0.15  # Jan-Mar
    q2_weight: float = 0.20  # Apr-Jun
    q3_weight: float = 0.25  # Jul-Sep
    q4_weight: float = 0.40  # Oct-Dec (heaviest)

    # Contract length distribution
    one_year_pct: float = 0.60    # 60% annual contracts
    two_year_pct: float = 0.25   # 25% 2-year contracts
    three_year_pct: float = 0.15  # 15% 3-year contracts

    # Average retention rate
    retention_rate: float = 0.85  # 85% retain year-over-year

    # Monthly factors (index 0 = January)
    monthly_factors: List[float] = field(default_factory=lambda: [
        0.08, 0.07, 0.07,  # Q1: 22%
        0.08, 0.08, 0.09,  # Q2: 25%
        0.08, 0.09, 0.09,  # Q3: 26%
        0.10, 0.11, 0.06   # Q4: 27% (Dec drop for holidays)
    ])

    def get_month_factor(self, month: int) -> float:
        """Get renewal factor for a specific month (1-12)."""
        if 1 <= month <= 12:
            return self.monthly_factors[month - 1]
        return 0.0833  # Default equal distribution

    def get_quarter_factor(self, quarter: int) -> float:
        """Get renewal factor for a quarter (1-4)."""
        weights = [self.q1_weight, self.q2_weight, self.q3_weight, self.q4_weight]
        if 1 <= quarter <= 4:
            return weights[quarter - 1]
        return 0.25

    def calculate_renewal_cohort(self, initial_clients: int, years: int) -> List[Dict[str, Any]]:
        """
        Calculate renewal cohort over multiple years.

        Args:
            initial_clients: Starting client count
            years: Number of years to project

        Returns:
            List of yearly cohort states
        """
        cohorts = []
        remaining = float(initial_clients)

        for year in range(1, years + 1):
            retained = remaining * self.retention_rate
            churned = remaining - retained

            cohorts.append({
                'year': year,
                'start_of_year': remaining,
                'retained': retained,
                'churned': churned,
                'retention_rate': self.retention_rate,
                'cumulative_retention': retained / initial_clients if initial_clients > 0 else 0
            })

            remaining = retained

        return cohorts

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'quarterly_weights': {
                'q1': self.q1_weight,
                'q2': self.q2_weight,
                'q3': self.q3_weight,
                'q4': self.q4_weight
            },
            'contract_distribution': {
                'one_year': self.one_year_pct,
                'two_year': self.two_year_pct,
                'three_year': self.three_year_pct
            },
            'retention_rate': self.retention_rate,
            'monthly_factors': self.monthly_factors
        }


@dataclass
class FunnelEfficiency:
    """Overall funnel efficiency metrics."""
    total_efficiency: float = 0.0  # End-to-end conversion rate
    velocity_days: float = 0.0     # Average days through funnel
    cost_per_client: float = 0.0   # Marketing cost per acquired client
    ltv_cac_ratio: float = 0.0     # Lifetime value / customer acquisition cost

    # Stage-specific velocity
    suspect_to_warm_days: float = 0.0
    warm_to_appointment_days: float = 0.0
    appointment_to_client_days: float = 0.0

    # Benchmark comparisons
    efficiency_vs_benchmark: float = 0.0  # % above/below industry
    velocity_vs_benchmark: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_efficiency': self.total_efficiency,
            'velocity_days': self.velocity_days,
            'cost_per_client': self.cost_per_client,
            'ltv_cac_ratio': self.ltv_cac_ratio,
            'stage_velocity': {
                'suspect_to_warm': self.suspect_to_warm_days,
                'warm_to_appointment': self.warm_to_appointment_days,
                'appointment_to_client': self.appointment_to_client_days
            },
            'benchmarks': {
                'efficiency_vs_benchmark': self.efficiency_vs_benchmark,
                'velocity_vs_benchmark': self.velocity_vs_benchmark
            }
        }


@dataclass
class FunnelMetrics:
    """Complete funnel metrics package."""
    # Stage counts
    suspects: int = 0
    warm: int = 0
    talentflow_warm: int = 0
    appointments: int = 0
    clients: int = 0

    # Calculated metrics
    conversion_rates: ConversionRates = field(default_factory=ConversionRates)
    ten_three_one: TenThreeOneRatios = field(default_factory=TenThreeOneRatios)
    efficiency: FunnelEfficiency = field(default_factory=FunnelEfficiency)
    cyclicity: RenewalCyclicity = field(default_factory=RenewalCyclicity)

    # Monthly movements (if provided)
    monthly_movements: List[MonthlyMovement] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'stage_counts': {
                'suspects': self.suspects,
                'warm': self.warm,
                'talentflow_warm': self.talentflow_warm,
                'appointments': self.appointments,
                'clients': self.clients
            },
            'conversion_rates': self.conversion_rates.to_dict(),
            'ten_three_one': self.ten_three_one.to_dict(),
            'efficiency': self.efficiency.to_dict(),
            'cyclicity': self.cyclicity.to_dict(),
            'monthly_movements': [m.to_dict() for m in self.monthly_movements]
        }


class FunnelMath:
    """
    Funnel mathematics calculator.

    Provides pure math functions for funnel analytics.
    No database access - all data is passed in.
    """

    # Industry benchmarks
    BENCHMARK_SUSPECT_TO_WARM = 0.10        # 10% of suspects become warm
    BENCHMARK_WARM_TO_APPOINTMENT = 0.30    # 30% of warm get appointments
    BENCHMARK_APPOINTMENT_TO_CLIENT = 0.33  # 33% of appointments convert
    BENCHMARK_TOTAL_EFFICIENCY = 0.01       # 1% end-to-end conversion
    BENCHMARK_VELOCITY_DAYS = 90            # 90 days average cycle

    def __init__(self, benchmarks: Dict[str, float] = None):
        """
        Initialize FunnelMath with optional custom benchmarks.

        Args:
            benchmarks: Optional dict of custom benchmark values
        """
        self.benchmarks = benchmarks or {}

    def calculate_conversion_rate(self, from_count: int, to_count: int) -> float:
        """
        Calculate conversion rate between two stages.

        Args:
            from_count: Count at source stage
            to_count: Count at destination stage

        Returns:
            Conversion rate as decimal (0.0 - 1.0)
        """
        if from_count <= 0:
            return 0.0
        return min(to_count / from_count, 1.0)

    def calculate_conversion_rates(self, suspects: int, warm: int,
                                    talentflow_warm: int, appointments: int,
                                    clients: int) -> ConversionRates:
        """
        Calculate all stage-to-stage conversion rates.

        Args:
            suspects: Count of suspects
            warm: Count of warm contacts
            talentflow_warm: Count of TalentFlow warm contacts
            appointments: Count of appointments
            clients: Count of clients

        Returns:
            ConversionRates dataclass
        """
        return ConversionRates(
            suspect_to_warm=self.calculate_conversion_rate(suspects, warm),
            warm_to_talentflow=self.calculate_conversion_rate(warm, talentflow_warm),
            talentflow_to_appointment=self.calculate_conversion_rate(talentflow_warm, appointments),
            appointment_to_client=self.calculate_conversion_rate(appointments, clients),
            suspect_to_talentflow=self.calculate_conversion_rate(suspects, talentflow_warm),
            warm_to_appointment=self.calculate_conversion_rate(warm, appointments)
        )

    def calculate_total_efficiency(self, suspects: int, clients: int) -> float:
        """
        Calculate total funnel efficiency (end-to-end conversion).

        Args:
            suspects: Starting suspect count
            clients: Ending client count

        Returns:
            Total efficiency as decimal
        """
        return self.calculate_conversion_rate(suspects, clients)

    def calculate_ten_three_one(self, warm: int, appointments: int,
                                 clients: int) -> TenThreeOneRatios:
        """
        Calculate 10-3-1 modern ratios.

        The 10-3-1 model:
        - 10 qualified leads (warm) -> 3 appointments -> 1 client
        - Measures sales efficiency against industry standard

        Args:
            warm: Count of warm/qualified leads
            appointments: Count of appointments
            clients: Count of clients

        Returns:
            TenThreeOneRatios dataclass
        """
        ratios = TenThreeOneRatios()

        if clients > 0:
            ratios.actual_leads_per_client = warm / clients
            ratios.actual_appointments_per_client = appointments / clients

            # Efficiency = target / actual (< 1.0 means we need more than target)
            ratios.leads_efficiency = (ratios.leads_per_client /
                                        ratios.actual_leads_per_client
                                        if ratios.actual_leads_per_client > 0 else 0.0)
            ratios.appointment_efficiency = (ratios.appointments_per_client /
                                              ratios.actual_appointments_per_client
                                              if ratios.actual_appointments_per_client > 0 else 0.0)

        return ratios

    def calculate_monthly_movement_pct(self, movements: List[MonthlyMovement],
                                        stage_bases: Dict[str, int]) -> List[MonthlyMovement]:
        """
        Calculate movement percentages for a list of monthly movements.

        Args:
            movements: List of MonthlyMovement objects
            stage_bases: Dict with keys 'suspects', 'warm', 'talentflow', 'appointments'

        Returns:
            Updated list of MonthlyMovement with percentages calculated
        """
        for movement in movements:
            movement.calculate_percentages(
                suspect_base=stage_bases.get('suspects', 0),
                warm_base=stage_bases.get('warm', 0),
                talentflow_base=stage_bases.get('talentflow', 0),
                appointment_base=stage_bases.get('appointments', 0)
            )
        return movements

    def calculate_funnel_efficiency(self, suspects: int, clients: int,
                                     velocity_days: float = None,
                                     marketing_spend: float = None,
                                     avg_client_ltv: float = None) -> FunnelEfficiency:
        """
        Calculate overall funnel efficiency metrics.

        Args:
            suspects: Starting suspect count
            clients: Client count
            velocity_days: Average days through funnel (optional)
            marketing_spend: Total marketing spend (optional)
            avg_client_ltv: Average client lifetime value (optional)

        Returns:
            FunnelEfficiency dataclass
        """
        efficiency = FunnelEfficiency()

        # Total efficiency
        efficiency.total_efficiency = self.calculate_total_efficiency(suspects, clients)

        # Velocity
        if velocity_days is not None:
            efficiency.velocity_days = velocity_days
            efficiency.velocity_vs_benchmark = (
                (self.BENCHMARK_VELOCITY_DAYS - velocity_days) /
                self.BENCHMARK_VELOCITY_DAYS * 100
            )

        # Cost metrics
        if marketing_spend is not None and clients > 0:
            efficiency.cost_per_client = marketing_spend / clients

            if avg_client_ltv is not None:
                efficiency.ltv_cac_ratio = avg_client_ltv / efficiency.cost_per_client

        # Benchmark comparison
        if self.BENCHMARK_TOTAL_EFFICIENCY > 0:
            efficiency.efficiency_vs_benchmark = (
                (efficiency.total_efficiency - self.BENCHMARK_TOTAL_EFFICIENCY) /
                self.BENCHMARK_TOTAL_EFFICIENCY * 100
            )

        return efficiency

    def calculate_funnel_metrics(self, suspects: int, warm: int,
                                  talentflow_warm: int, appointments: int,
                                  clients: int,
                                  velocity_days: float = None,
                                  marketing_spend: float = None,
                                  avg_client_ltv: float = None,
                                  monthly_movements: List[MonthlyMovement] = None) -> FunnelMetrics:
        """
        Calculate complete funnel metrics package.

        Args:
            suspects: Count of suspects
            warm: Count of warm contacts
            talentflow_warm: Count of TalentFlow warm contacts
            appointments: Count of appointments
            clients: Count of clients
            velocity_days: Optional average days through funnel
            marketing_spend: Optional total marketing spend
            avg_client_ltv: Optional average client lifetime value
            monthly_movements: Optional list of monthly movements

        Returns:
            FunnelMetrics dataclass with all calculations
        """
        metrics = FunnelMetrics(
            suspects=suspects,
            warm=warm,
            talentflow_warm=talentflow_warm,
            appointments=appointments,
            clients=clients
        )

        # Calculate all metrics
        metrics.conversion_rates = self.calculate_conversion_rates(
            suspects, warm, talentflow_warm, appointments, clients
        )

        metrics.ten_three_one = self.calculate_ten_three_one(
            warm, appointments, clients
        )

        metrics.efficiency = self.calculate_funnel_efficiency(
            suspects, clients, velocity_days, marketing_spend, avg_client_ltv
        )

        # Process monthly movements if provided
        if monthly_movements:
            stage_bases = {
                'suspects': suspects,
                'warm': warm,
                'talentflow': talentflow_warm,
                'appointments': appointments
            }
            metrics.monthly_movements = self.calculate_monthly_movement_pct(
                monthly_movements, stage_bases
            )

        return metrics

    # ==========================================
    # UTILITY FUNCTIONS
    # ==========================================

    def calculate_required_suspects(self, target_clients: int,
                                     conversion_rate: float = None) -> int:
        """
        Calculate required suspects to hit client target.

        Args:
            target_clients: Desired number of clients
            conversion_rate: End-to-end conversion rate (default: benchmark)

        Returns:
            Required suspect count
        """
        rate = conversion_rate or self.BENCHMARK_TOTAL_EFFICIENCY
        if rate <= 0:
            return 0
        return stdlib_math.ceil(target_clients / rate)

    def calculate_stage_targets(self, target_clients: int,
                                 suspect_to_warm: float = None,
                                 warm_to_appointment: float = None,
                                 appointment_to_client: float = None) -> Dict[str, int]:
        """
        Calculate required counts at each funnel stage.

        Args:
            target_clients: Desired number of clients
            suspect_to_warm: Conversion rate (default: benchmark)
            warm_to_appointment: Conversion rate (default: benchmark)
            appointment_to_client: Conversion rate (default: benchmark)

        Returns:
            Dict with required counts at each stage
        """
        s2w = suspect_to_warm or self.BENCHMARK_SUSPECT_TO_WARM
        w2a = warm_to_appointment or self.BENCHMARK_WARM_TO_APPOINTMENT
        a2c = appointment_to_client or self.BENCHMARK_APPOINTMENT_TO_CLIENT

        appointments = stdlib_math.ceil(target_clients / a2c) if a2c > 0 else 0
        warm = stdlib_math.ceil(appointments / w2a) if w2a > 0 else 0
        suspects = stdlib_math.ceil(warm / s2w) if s2w > 0 else 0

        return {
            'suspects': suspects,
            'warm': warm,
            'appointments': appointments,
            'clients': target_clients
        }

    def calculate_funnel_gap(self, current: Dict[str, int],
                              target: Dict[str, int]) -> Dict[str, int]:
        """
        Calculate gap between current and target funnel state.

        Args:
            current: Dict with current stage counts
            target: Dict with target stage counts

        Returns:
            Dict with gap at each stage (negative = deficit)
        """
        return {
            stage: current.get(stage, 0) - target.get(stage, 0)
            for stage in ['suspects', 'warm', 'appointments', 'clients']
        }

    def calculate_velocity(self, stage_durations: Dict[str, float]) -> float:
        """
        Calculate total funnel velocity from stage durations.

        Args:
            stage_durations: Dict with days spent in each stage

        Returns:
            Total velocity in days
        """
        return sum(stage_durations.values())

    def calculate_weighted_conversion(self, conversions: List[Tuple[int, int, float]]) -> float:
        """
        Calculate weighted average conversion rate.

        Args:
            conversions: List of (from_count, to_count, weight) tuples

        Returns:
            Weighted average conversion rate
        """
        total_weight = sum(w for _, _, w in conversions)
        if total_weight <= 0:
            return 0.0

        weighted_sum = sum(
            self.calculate_conversion_rate(f, t) * w
            for f, t, w in conversions
        )
        return weighted_sum / total_weight
