# DRY RUN SUMMARY REPORT
**Run ID**: 7aed0b56-b274-44cb-973f-f9e4b3eecad3
**Timestamp**: 2025-12-19T14:25:41.177738
**Duration**: 0.09 seconds

## Volume Metrics
- Companies Processed: 1,000
- People Processed: 5,000
- Emails Generated: 4,419
- Total Signals Emitted: 6,926

### Signals by Type
- EMAIL_VERIFIED: 3,753
- SLOT_FILLED: 2,670
- FORM_5500_FILED: 241
- LARGE_PLAN: 78
- EXECUTIVE_HIRE: 30
- LATERAL_MOVE: 28
- EXECUTIVE_DEPARTURE: 27
- PROMOTION: 24
- BROKER_CHANGE: 19
- LAYOFFS: 16
- FUNDING_ROUND: 12
- EXPANSION: 12
- ACQUISITION: 9
- EXECUTIVE_CHANGE: 7

## Cost Metrics
- **Total Estimated Cost**: $215.98
- **Cost per 1k Records**: $35.9966

### Cost by Phase
- company_p1_p4: $0.2074
- people_spoke: $53.8647
- dol_spoke: $53.9485
- blog_spoke: $53.9741
- talent_flow_spoke: $53.9850
- outreach_spoke: $0.0000

### Top 3 Most Expensive Tools
- linkedin_enrichment: $30.9200
- email_verification: $22.0950
- bit_signal: $0.6926

## Quality Metrics

### Fuzzy Match Distribution
- 90-100%: 596
- 80-89%: 276
- 70-79%: 49
- <70%: 79

### Email Verification
- Pass: 3,753
- Fail: 666
- Pass Rate: 84.9%

### Slot Fill Rates
- CEO: 43.2%
- CFO: 43.4%
- CHRO: 47.9%
- HR: 132.5%

### BIT Score Distribution
- 0-24: 336
- 25-49: 392
- 50-74: 176
- 75+: 96

## Risk Metrics
- Email Rejection Rate: 15.1%
- Companies with BIT >= 50: 44.8%
- Max Signals (Single Company): 22
- Enrichment Queue Size: 1,546

## Kill Switch Status
- **Triggered**: 2
- **Passed**: 2

### Triggered Switches
- **signal_flood_per_source**: Source people_spoke exceeded signal limit
- **daily_cost_ceiling**: Daily cost $215.98 exceeds ceiling