# Funnel Reports

## Overview

Reporting and forecasting modules for the 4-Funnel GTM System. Provides pure mathematical functions for:

- Stage-to-stage conversion rates
- Total funnel efficiency
- 10-3-1 Modern Sales Ratios
- Monthly movement percentages
- Renewal-driven cyclicity
- 12-36 month revenue and lives projections
- Compounding impact modeling

**No database fetches** - all functions accept data as parameters.

## Architecture

```
funnel_reports/
├── __init__.py              # Public API exports
├── funnel_math.py           # Conversion rates & metrics
├── forecast_model.py        # Revenue & lives projections
├── funnel_dashboard.json    # Dashboard schema definition
└── README.md               # This file
```

## Components

### FunnelMath

Core mathematical calculations for funnel analytics.

```python
from ctb.sys.reporting.funnel_reports import FunnelMath, FunnelMetrics

math = FunnelMath()

# Calculate complete funnel metrics
metrics = math.calculate_funnel_metrics(
    suspects=10000,
    warm=1000,
    talentflow_warm=300,
    appointments=100,
    clients=33,
    velocity_days=90,
    marketing_spend=165000,
    avg_client_ltv=500000
)

print(f"Total Efficiency: {metrics.efficiency.total_efficiency:.2%}")
print(f"Suspect → Warm: {metrics.conversion_rates.suspect_to_warm:.2%}")
print(f"LTV/CAC Ratio: {metrics.efficiency.ltv_cac_ratio:.1f}x")
```

**Key Metrics:**

| Metric | Description |
|--------|-------------|
| `suspect_to_warm` | % of suspects that become warm |
| `warm_to_talentflow` | % of warm with TalentFlow signal |
| `talentflow_to_appointment` | % of TalentFlow that book meetings |
| `appointment_to_client` | % of appointments that convert |
| `total_efficiency` | End-to-end conversion rate |

### 10-3-1 Modern Ratios

Industry-standard sales efficiency metrics.

```python
ratios = math.calculate_ten_three_one(
    warm=1000,        # Qualified leads
    appointments=100,  # Meetings held
    clients=33        # Closed deals
)

print(f"Leads per Client: {ratios.actual_leads_per_client:.1f}")
print(f"Target: {ratios.leads_per_client}")
print(f"Efficiency: {ratios.leads_efficiency:.0%}")
print(f"Above Target: {ratios.is_above_target}")
```

**The 10-3-1 Model:**
- 10 qualified leads → 3 appointments → 1 client
- Measures sales efficiency against industry standard
- `efficiency > 1.0` = performing better than target

### Monthly Movement

Track stage movements over time.

```python
from ctb.sys.reporting.funnel_reports import MonthlyMovement

movements = [
    MonthlyMovement(
        month=1, year=2025,
        suspects_added=500,
        suspects_to_warm=50,
        warm_to_talentflow=15,
        talentflow_to_appointment=5,
        appointments_to_client=2,
        suspects_churned=100,
        warm_churned=10
    )
]

# Calculate percentages
stage_bases = {
    'suspects': 10000,
    'warm': 1000,
    'talentflow': 300,
    'appointments': 100
}

math.calculate_monthly_movement_pct(movements, stage_bases)

print(f"Suspect→Warm: {movements[0].suspect_warm_pct:.1f}%")
print(f"Churn Rate: {movements[0].churn_rate:.1f}%")
```

### Renewal Cyclicity

Model renewal-driven business patterns.

```python
from ctb.sys.reporting.funnel_reports import RenewalCyclicity

cyclicity = RenewalCyclicity(
    q1_weight=0.15,
    q2_weight=0.20,
    q3_weight=0.25,
    q4_weight=0.40,
    retention_rate=0.85
)

# Get monthly factors
jan_factor = cyclicity.get_month_factor(1)  # 0.08
oct_factor = cyclicity.get_month_factor(10)  # 0.10

# Project renewal cohorts
cohorts = cyclicity.calculate_renewal_cohort(
    initial_clients=100,
    years=5
)

for cohort in cohorts:
    print(f"Year {cohort['year']}: {cohort['retained']:.0f} retained ({cohort['cumulative_retention']:.0%})")
```

### ForecastModel

Revenue and lives projections for 12-36 months.

```python
from ctb.sys.reporting.funnel_reports import (
    ForecastModel,
    ForecastConfig,
    GrowthScenario
)

# Configure forecast
config = ForecastConfig(
    monthly_new_client_rate=0.05,
    monthly_churn_rate=0.02,
    avg_revenue_per_client=50000,
    avg_lives_per_client=150,
    annual_retention_rate=0.85
)

model = ForecastModel(config)

# Generate 36-month forecast
result = model.generate_forecast(
    current_clients=100,
    months=36,
    scenario=GrowthScenario.MODERATE
)

print(f"Starting ARR: ${result.revenue.starting_arr:,.0f}")
print(f"Ending ARR: ${result.revenue.ending_arr:,.0f}")
print(f"CAGR: {result.revenue.cagr:.1f}%")
print(f"Compounding Multiplier: {result.compounding.compounding_multiplier:.2f}x")
```

**Scenario Types:**

| Scenario | Growth Multiplier | Description |
|----------|------------------|-------------|
| `CONSERVATIVE` | 0.7x | Risk-adjusted, lower growth |
| `MODERATE` | 1.0x | Baseline projections |
| `AGGRESSIVE` | 1.4x | Optimistic, stretch goals |

### Revenue Projections

```python
# Project revenue only
revenue = model.project_revenue(
    current_clients=100,
    avg_revenue_per_client=50000,
    months=36,
    scenario=GrowthScenario.MODERATE
)

# Monthly breakdown
for month in revenue.monthly_projections:
    print(f"Month {month.month}: {month.ending_clients} clients, ${month.total_revenue:,.0f}")
```

### Lives Projections

```python
# Project employee counts
lives = model.project_lives(
    current_clients=100,
    avg_lives_per_client=150,
    months=36,
    scenario=GrowthScenario.MODERATE
)

print(f"Starting Lives: {lives.starting_lives:,}")
print(f"Ending Lives: {lives.ending_lives:,}")
print(f"Growth: {lives.lives_growth_pct:.1f}%")
```

### Compounding Impact

Model the multiplier effect of referrals, cross-sells, and price uplifts.

```python
impact = model.calculate_compounding_impact(
    current_clients=100,
    months=36,
    scenario=GrowthScenario.MODERATE
)

print(f"Base Revenue: ${impact.base_revenue:,.0f}")
print(f"Compounded Revenue: ${impact.compounded_revenue:,.0f}")
print(f"Multiplier: {impact.compounding_multiplier:.2f}x")

print(f"\nImpact Breakdown:")
print(f"  Referrals: ${impact.referral_revenue:,.0f} ({impact.referral_clients} clients)")
print(f"  Cross-Sell: ${impact.cross_sell_revenue:,.0f}")
print(f"  Price Uplift: ${impact.price_uplift_revenue:,.0f}")
```

### All Scenarios

Generate conservative, moderate, and aggressive forecasts.

```python
scenarios = model.generate_scenarios(
    current_clients=100,
    months=36
)

for name, result in scenarios.items():
    print(f"\n{name.upper()}:")
    print(f"  Ending ARR: ${result.revenue.ending_arr:,.0f}")
    print(f"  Ending Lives: {result.lives.ending_lives:,}")
    print(f"  CAGR: {result.revenue.cagr:.1f}%")
```

## Dashboard Schema

The `funnel_dashboard.json` defines the schema for dashboard data.

**Key Sections:**

| Section | Description |
|---------|-------------|
| `metadata` | Dashboard ID, timestamps, refresh frequency |
| `funnel_overview` | Stage counts and movements |
| `conversion_rates` | Stage-to-stage conversion with benchmarks |
| `ten_three_one` | 10-3-1 ratio analysis |
| `monthly_movements` | Historical movement data |
| `renewal_cyclicity` | Renewal timing and retention |
| `forecast` | Revenue/lives projections |
| `kpis` | Key performance indicators |
| `alerts` | Active warnings and alerts |
| `visualizations` | Chart configuration |

## Utility Functions

### Calculate Required Suspects

```python
# How many suspects to hit 50 clients?
required = math.calculate_required_suspects(
    target_clients=50,
    conversion_rate=0.01  # 1% end-to-end
)
# Returns: 5000
```

### Calculate Stage Targets

```python
# Reverse-engineer funnel targets
targets = math.calculate_stage_targets(
    target_clients=50,
    suspect_to_warm=0.10,
    warm_to_appointment=0.30,
    appointment_to_client=0.33
)
# Returns: {'suspects': 5051, 'warm': 505, 'appointments': 152, 'clients': 50}
```

### Calculate Break-Even

```python
# Months to reach $10M ARR
months = model.calculate_break_even(
    target_revenue=10_000_000,
    current_clients=100,
    scenario=GrowthScenario.MODERATE
)
# Returns: 24 (months)
```

### Calculate LTV

```python
ltv = model.calculate_ltv(
    avg_revenue_per_client=50000,
    retention_years=6.67  # From 85% retention
)
# Returns: $333,500
```

## Benchmarks

Default industry benchmarks (customizable):

| Metric | Benchmark |
|--------|-----------|
| Suspect → Warm | 10% |
| Warm → Appointment | 30% |
| Appointment → Client | 33% |
| Total Efficiency | 1% |
| Funnel Velocity | 90 days |

## Configuration

All modules accept configuration dictionaries.

```python
# Custom FunnelMath benchmarks
math = FunnelMath(benchmarks={
    'suspect_to_warm': 0.15,
    'total_efficiency': 0.02
})

# Custom ForecastConfig
config = ForecastConfig(
    monthly_new_client_rate=0.08,
    monthly_churn_rate=0.015,
    avg_revenue_per_client=75000,
    avg_lives_per_client=200,
    annual_retention_rate=0.90,
    referral_rate=0.15,
    cross_sell_rate=0.20
)
```

## Related Documentation

- **Doctrine:** `ctb/sys/doctrine/4_funnel_doctrine.md`
- **State Machine:** `ctb/sys/doctrine/funnel_state_machine.md`
- **Rules:** `ctb/sys/doctrine/funnel_rules.md`
- **Movement Engine:** `pipeline_engine/movement_engine/README.md`
- **Schema:** `neon/migrations/README.md`

## Version

- **Version:** 1.0.0
- **Created:** 2025-12-05
