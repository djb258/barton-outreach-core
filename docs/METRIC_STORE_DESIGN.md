# Metric Store Design

## Problem Statement

When building personalized outreach messages, we need to:
1. Calculate metrics from DOL filings (PEPM, broker commissions, healthcare spend)
2. Compare those metrics across multiple years (2021 vs 2023)
3. Compare against benchmarks (state median, industry average)
4. Pull specific year values into message templates

**Example message we want to generate:**
> "Liz, your broker costs went from $2,500 PEPM in 2021 to $3,928 in 2023 - a 57% increase. The Maryland median dropped 12% in that same period."

## Why Not Process IDs?

Initially considered tracking each calculation with a unique process ID:
```
proc_001: PEPM calculation → $3,928
proc_002: Blog extract → "expansion"
proc_003: Message build → references 001, 002
```

**Problem:** This adds unnecessary complexity. We don't need to track the *process* of calculating - we need to track the *results* by time period.

## Solution: Metric Store

Store calculated metrics by company + type + year:

```
Company: 3P Health (outreach_id: abc-123)
├── PEPM_2021: $2,500
├── PEPM_2022: $3,100
├── PEPM_2023: $3,928
├── BROKER_COMM_2023: $47,200
└── HEALTHCARE_SPEND_2023: $892,000
```

### Schema Design

```sql
CREATE TABLE outreach.company_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    outreach_id UUID NOT NULL REFERENCES outreach.outreach(outreach_id),

    -- What metric
    metric_type VARCHAR(50) NOT NULL,    -- 'PEPM', 'BROKER_COMM', 'HEALTHCARE_SPEND', etc.
    metric_year INTEGER NOT NULL,        -- Filing year: 2021, 2022, 2023

    -- The values
    metric_value NUMERIC,                -- The calculated number
    comparison_value NUMERIC,            -- Benchmark (state median, industry avg)
    comparison_type VARCHAR(50),         -- 'STATE_MEDIAN', 'INDUSTRY_AVG', etc.

    -- Traceability
    source_table VARCHAR(100),           -- 'dol.schedule_a', 'dol.form_5500'
    source_filing_id UUID,               -- Which filing record it came from
    calculation_formula TEXT,            -- How it was calculated (for audit)

    -- Timestamps
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(outreach_id, metric_type, metric_year)
);

-- Index for common queries
CREATE INDEX idx_company_metrics_lookup ON outreach.company_metrics(outreach_id, metric_type);
CREATE INDEX idx_company_metrics_year ON outreach.company_metrics(metric_year, metric_type);
```

### Metric Types

| Metric Type | Source | Calculation |
|-------------|--------|-------------|
| `PEPM` | schedule_a + form_5500 | (broker_comm / participants) / 12 |
| `BROKER_COMM` | schedule_a | ins_broker_comm_tot_amt |
| `BROKER_FEES` | schedule_a | ins_broker_fees_tot_amt |
| `PARTICIPANT_COUNT` | form_5500 | tot_active_partcp_cnt |
| `HEALTHCARE_SPEND` | schedule_a | Sum of welfare benefit amounts |

### Comparison Types

| Comparison Type | Description |
|-----------------|-------------|
| `STATE_MEDIAN` | Median for companies in same state |
| `STATE_AVG` | Average for companies in same state |
| `INDUSTRY_MEDIAN` | Median for companies in same industry |
| `SIZE_BAND_MEDIAN` | Median for similar-sized companies |

## How It Works

### 1. Batch Calculation (Nightly/Weekly)

Run calculations for all companies with DOL filings:

```sql
INSERT INTO outreach.company_metrics (outreach_id, metric_type, metric_year, metric_value, source_table)
SELECT
    o.outreach_id,
    'PEPM' as metric_type,
    sa.form_year::integer as metric_year,
    (SUM(sa.ins_broker_comm_tot_amt) / NULLIF(MAX(f.tot_active_partcp_cnt), 0)) / 12 as metric_value,
    'dol.schedule_a + dol.form_5500' as source_table
FROM outreach.outreach o
JOIN dol.schedule_a sa ON o.ein = sa.sch_a_ein
JOIN dol.form_5500 f ON sa.sch_a_ein = f.sponsor_dfe_ein AND sa.form_year = f.form_year
WHERE sa.ins_broker_comm_tot_amt > 0
  AND f.tot_active_partcp_cnt > 0
GROUP BY o.outreach_id, sa.form_year
ON CONFLICT (outreach_id, metric_type, metric_year)
DO UPDATE SET metric_value = EXCLUDED.metric_value, updated_at = NOW();
```

### 2. Calculate Comparisons

After metrics are stored, calculate benchmarks:

```sql
-- Calculate state medians
WITH state_medians AS (
    SELECT
        ct.state,
        cm.metric_type,
        cm.metric_year,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cm.metric_value) as median_value
    FROM outreach.company_metrics cm
    JOIN outreach.company_target ct ON ct.outreach_id = cm.outreach_id
    GROUP BY ct.state, cm.metric_type, cm.metric_year
)
UPDATE outreach.company_metrics cm
SET
    comparison_value = sm.median_value,
    comparison_type = 'STATE_MEDIAN'
FROM outreach.company_target ct
JOIN state_medians sm ON ct.state = sm.state
    AND cm.metric_type = sm.metric_type
    AND cm.metric_year = sm.metric_year
WHERE cm.outreach_id = ct.outreach_id;
```

### 3. Query for Message Building

Pull all metrics for a company to build personalized message:

```sql
SELECT
    cm.metric_type,
    cm.metric_year,
    cm.metric_value,
    cm.comparison_value,
    cm.comparison_type,
    (cm.metric_value / NULLIF(cm.comparison_value, 0)) as vs_benchmark
FROM outreach.company_metrics cm
WHERE cm.outreach_id = 'your-outreach-id'
ORDER BY cm.metric_type, cm.metric_year;
```

### 4. Calculate Year-over-Year Changes

```sql
SELECT
    curr.outreach_id,
    curr.metric_type,
    curr.metric_year as current_year,
    curr.metric_value as current_value,
    prev.metric_year as previous_year,
    prev.metric_value as previous_value,
    ((curr.metric_value - prev.metric_value) / NULLIF(prev.metric_value, 0)) * 100 as pct_change
FROM outreach.company_metrics curr
JOIN outreach.company_metrics prev
    ON curr.outreach_id = prev.outreach_id
    AND curr.metric_type = prev.metric_type
    AND curr.metric_year = prev.metric_year + 2  -- Compare 2023 to 2021
WHERE curr.metric_year = 2023;
```

## Message Template Variables

Once metrics are stored, pull into message templates:

| Variable | Query | Example |
|----------|-------|---------|
| `{{pepm_2023}}` | metric_value WHERE type='PEPM' AND year=2023 | "$3,928" |
| `{{pepm_2021}}` | metric_value WHERE type='PEPM' AND year=2021 | "$2,500" |
| `{{pepm_change_pct}}` | ((2023 - 2021) / 2021) * 100 | "57%" |
| `{{state_median}}` | comparison_value WHERE comparison_type='STATE_MEDIAN' | "$1.44" |
| `{{vs_median}}` | metric_value / comparison_value | "2,729x" |

## Integration with OSAM

This becomes a new queryable source in the OSAM:

```
METRIC STORE: outreach.company_metrics
├── PK: metric_id (uuid)
├── FK: outreach_id → outreach.outreach
├── Owns: calculated metrics by year
└── Ask: "What's the PEPM trend for this company?"
```

## Benefits

1. **Multi-year comparison**: "Your PEPM increased 57% since 2021"
2. **Benchmark comparison**: "You're 2,729x above the state median"
3. **Trend analysis**: Identify companies with increasing costs
4. **Audit trail**: Know exactly where each number came from
5. **Message personalization**: Pull specific year values into templates
6. **Targeting**: Find companies with biggest YoY increases

## Next Steps

1. Create the `outreach.company_metrics` table
2. Write batch calculation jobs for each metric type
3. Calculate state/industry benchmarks
4. Add to OSAM as queryable source
5. Build message template variable resolver

---

*Created: 2026-02-05*
*Status: DESIGN - Not yet implemented*
