# BIT Doctrine — Buyer Intent Tool
## Barton Doctrine Framework | SVG-PLE Marketing Core

**Document ID**: `01.04.03.04.10000.001`
**Version**: 1.0.0
**Last Updated**: 2025-11-07
**Altitude**: 10,000 ft (Execution Layer)
**Role**: Axle of the Perpetual Lead Engine
**Status**: Active | Production Ready

---

## Section 1: Purpose and Position within PLE

### Overview

The **Buyer Intent Tool (BIT)** serves as the **axle** of the Shenandoah Valley Group Perpetual Lead Engine (SVG-PLE). As the central scoring mechanism, BIT converts discrete business events into quantified buyer intent scores that drive lead prioritization and outreach automation.

### Position in SVG-PLE Architecture

```
┌──────────────────────────────────────────────────┐
│           SVG-PLE Architecture                    │
└──────────────────────────────────────────────────┘

HUB (Core Intelligence)
└─▶ Marketing DB (Neon PostgreSQL)
    ├── company_master
    ├── people_master
    └── company_slot

SPOKES (Data Ingestion)
├─▶ Talent Flow Spoke
│   └── Executive movements, hiring signals
├─▶ Renewal Spoke
│   └── Contract expiration windows
└─▶ Compliance Spoke
    └── DOL violations, regulatory events

AXLE (BIT) ← YOU ARE HERE
└─▶ Converts events → scores → priorities
    ├── Rule engine (configurable weights)
    ├── Event aggregation (multiple signals)
    └── Score calculation (0-100 scale)

WHEEL (Lead Cycles)
└─▶ Outreach automation based on BIT scores
    ├── High intent (80-100): Immediate outreach
    ├── Medium intent (50-79): Nurture campaign
    └── Low intent (0-49): Monitor only
```

### Core Function

BIT transforms **qualitative business events** into **quantitative intent scores**:

- **Input**: Events from spokes (executive_movement, renewal_window_120d, dol_violation)
- **Processing**: Apply weighted rules, aggregate multiple signals
- **Output**: Intent score (0-100) with decay over time
- **Action**: Trigger outreach workflows based on score thresholds

### Business Value

1. **Prioritization**: Focus sales resources on highest-intent accounts
2. **Timing**: Strike when buyer signals are strongest (executive changes, renewals)
3. **Automation**: Reduce manual lead qualification time by 80%
4. **Data-Driven**: Replace gut feeling with quantified scoring
5. **Scalability**: Handle thousands of accounts with consistent logic

---

## Section 2: Logical Flow Diagram

### Event-to-Score Pipeline

```
┌────────────────────────────────────────────────────────────────┐
│  STAGE 1: Event Detection (Spokes)                             │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌──────────────────────────────────┐
        │  Talent Flow Spoke                │
        │  • Executive hired                │
        │  • Executive departed             │
        │  • New CFO/CEO/HR role filled     │
        └──────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│  STAGE 2: Event Logging (marketing.data_enrichment_log)        │
│  • movement_detected = true                                    │
│  • movement_type = 'executive_hire' | 'executive_departure'    │
│  • data_quality_score captured                                 │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│  STAGE 3: BIT Event Creation (bit.events)                      │
│  • event_id = 01.04.03.04.10000.###                           │
│  • event_type = 'executive_movement'                           │
│  • company_unique_id linked                                    │
│  • rule_reference_id linked                                    │
│  • detected_at = NOW()                                         │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│  STAGE 4: Rule Application (bit.rule_reference)                │
│  • Lookup rule weight (e.g., executive_movement = 40 points)   │
│  • Apply decay factor (reduce score over time)                 │
│  • Check is_active flag                                        │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│  STAGE 5: Score Calculation (bit.scores view)                  │
│  • Aggregate all events for company                            │
│  • Apply time decay: score * (1 - days_since/365)              │
│  • Sum weighted scores                                         │
│  • Cap at 100 maximum                                          │
│  • Categorize: Hot (80-100), Warm (50-79), Cold (0-49)         │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│  STAGE 6: Action Trigger (Outreach Layer)                      │
│  • Hot leads → Immediate outreach (24-48 hours)                │
│  • Warm leads → Nurture campaign (7-14 days)                   │
│  • Cold leads → Monitor only (no active outreach)              │
└────────────────────────────────────────────────────────────────┘
```

### Data Flow Example

```
Executive Movement Detected
        ↓
marketing.data_enrichment_log.movement_detected = true
        ↓
INSERT INTO bit.events (
  event_id: 01.04.03.04.10000.001,
  company_unique_id: 04.04.02.04.30000.042,
  event_type: 'executive_movement',
  rule_reference_id: 01.04.03.04.10000.101
)
        ↓
SELECT FROM bit.rule_reference WHERE rule_id = 101
  → weight = 40
  → decay_days = 365
  → is_active = true
        ↓
Calculate Score:
  base_score = 40
  days_since = 15
  decay_factor = 1 - (15/365) = 0.959
  final_score = 40 * 0.959 = 38.36
        ↓
bit.scores VIEW:
  company_unique_id: 04.04.02.04.30000.042
  total_score: 38.36
  score_category: 'Cold' (0-49)
```

---

## Section 3: Scoring Logic and Weight Table

### Scoring Formula

```
Total Intent Score = SUM(
  event_weight * decay_factor * quality_modifier
)

Where:
  decay_factor = 1 - (days_since_event / decay_days)
  quality_modifier = data_quality_score / 100

Cap: MAX(Total Intent Score, 100)
```

### Standard Rule Weights

| Rule ID | Event Type | Base Weight | Decay Days | Rationale |
|---------|-----------|-------------|------------|-----------|
| `01.04.03.04.10000.101` | executive_movement | 40 | 365 | New exec likely evaluating vendors |
| `01.04.03.04.10000.102` | renewal_window_120d | 35 | 120 | Contract renewal decision window |
| `01.04.03.04.10000.103` | renewal_window_90d | 45 | 90 | Higher urgency, closer to renewal |
| `01.04.03.04.10000.104` | renewal_window_60d | 55 | 60 | Critical decision timeframe |
| `01.04.03.04.10000.105` | renewal_window_30d | 70 | 30 | Urgent, immediate opportunity |
| `01.04.03.04.10000.106` | dol_violation | 30 | 180 | Compliance pain point |
| `01.04.03.04.10000.107` | hiring_surge | 25 | 180 | Growth indicator |
| `01.04.03.04.10000.108` | funding_round | 50 | 270 | Budget availability signal |
| `01.04.03.04.10000.109` | tech_stack_change | 35 | 180 | Infrastructure modernization |
| `01.04.03.04.10000.110` | competitor_switch | 60 | 365 | Actively seeking alternatives |

### Score Categories

| Category | Score Range | Outreach Strategy | Response Time |
|----------|-------------|-------------------|---------------|
| 🔥 **Hot** | 80-100 | Immediate personalized outreach | 24-48 hours |
| 🔶 **Warm** | 50-79 | Nurture campaign, targeted content | 7-14 days |
| 🔵 **Cold** | 0-49 | Monitor only, no active outreach | No immediate action |

### Quality Modifiers

Data quality affects final score:

- **High Quality (90-100)**: 1.0x multiplier (no reduction)
- **Medium Quality (70-89)**: 0.85x multiplier (15% reduction)
- **Low Quality (50-69)**: 0.70x multiplier (30% reduction)
- **Poor Quality (<50)**: Event ignored

### Decay Curve

```
Score Decay Over Time (Example: 40-point event, 365-day decay)

Day 0:   40 pts (100%)
Day 90:  30 pts (75%)
Day 180: 20 pts (50%)
Day 270: 10 pts (25%)
Day 365: 0 pts (0%)

Formula: score = base_weight * (1 - days_since/decay_days)
```

---

## Section 4: Numbering Convention

### Barton Doctrine ID Format

**BIT Prefix**: `01.04.03.04.10000`

Breaking down the prefix:
- `01` = Subhive (Marketing/Sales)
- `04` = Application (SVG-PLE)
- `03` = Layer (Execution - 10,000 ft)
- `04` = Schema (BIT)
- `10000` = Base sequence for BIT entities

### ID Ranges

| Entity Type | ID Pattern | Range | Example |
|-------------|-----------|-------|---------|
| Rule Reference | `01.04.03.04.10000.1##` | 101-199 | `01.04.03.04.10000.101` |
| BIT Events | `01.04.03.04.10000.###` | 001-999 (per company) | `01.04.03.04.10000.001` |
| Score Snapshots | `01.04.03.04.10000.8##` | 801-899 | `01.04.03.04.10000.801` |
| Audit Logs | `01.04.03.04.10000.9##` | 901-999 | `01.04.03.04.10000.901` |

### Example IDs in Context

**Rule Reference**:
```sql
rule_reference_id: 01.04.03.04.10000.101
rule_name: 'executive_movement'
weight: 40
```

**BIT Event**:
```sql
event_id: 01.04.03.04.10000.042
company_unique_id: 04.04.02.04.30000.015
event_type: 'executive_movement'
rule_reference_id: 01.04.03.04.10000.101
detected_at: 2025-11-07 14:30:00
```

**Score Snapshot**:
```sql
snapshot_id: 01.04.03.04.10000.801
company_unique_id: 04.04.02.04.30000.015
snapshot_date: 2025-11-07
total_score: 72.5
score_category: 'Warm'
```

### Auto-Generation

Event IDs are auto-generated using:
```sql
DEFAULT CONCAT(
  '01.04.03.04.10000.',
  LPAD(NEXTVAL('bit.event_id_seq')::TEXT, 3, '0')
)
```

---

## Section 5: Schema Summary

### Database: `bit` schema

Location: `doctrine/schemas/bit-schema.sql`

### Tables

#### 1. `bit.rule_reference`

**Purpose**: Defines scoring rules with weights and decay parameters

**Columns**:
- `rule_reference_id` (VARCHAR, PK) - Barton ID: `01.04.03.04.10000.1##`
- `rule_name` (VARCHAR) - Human-readable name (e.g., 'executive_movement')
- `event_type` (VARCHAR) - Event type identifier
- `weight` (INTEGER) - Base score points (0-100)
- `decay_days` (INTEGER) - Days until score reaches zero
- `description` (TEXT) - Rule explanation
- `is_active` (BOOLEAN) - Enable/disable rule
- `created_at`, `updated_at` (TIMESTAMPTZ)

**Indexes**:
- PK on `rule_reference_id`
- Index on `event_type`
- Index on `is_active`

#### 2. `bit.events`

**Purpose**: Logs individual buyer intent events for companies

**Columns**:
- `event_id` (VARCHAR, PK) - Barton ID: `01.04.03.04.10000.###`
- `company_unique_id` (VARCHAR, FK) - Links to `marketing.company_master`
- `event_type` (VARCHAR) - Type of event (links to rule_reference)
- `rule_reference_id` (VARCHAR, FK) - Links to `bit.rule_reference`
- `event_payload` (JSONB) - Additional event data
- `detected_at` (TIMESTAMPTZ) - When event occurred
- `data_quality_score` (INTEGER) - Quality of data (0-100)
- `created_at` (TIMESTAMPTZ)

**Indexes**:
- PK on `event_id`
- Index on `company_unique_id`
- Index on `event_type`
- Index on `detected_at`
- GIN index on `event_payload`

#### 3. `bit.scores` (VIEW)

**Purpose**: Calculates real-time intent scores for all companies

**Columns**:
- `company_unique_id` - Company identifier
- `company_name` - Company name (from company_master)
- `total_score` - Aggregated intent score (0-100)
- `score_category` - Hot/Warm/Cold classification
- `event_count` - Number of active events
- `latest_event_date` - Most recent event timestamp
- `score_breakdown` - JSONB with per-event contributions

**Logic**:
```sql
total_score = SUM(
  rule.weight *
  (1 - EXTRACT(DAY FROM NOW() - event.detected_at) / rule.decay_days) *
  (event.data_quality_score / 100.0)
)
WHERE detected_at >= NOW() - INTERVAL '1 year'
  AND rule.is_active = true
```

### Seed Data

Default rules are inserted on schema creation:
- Executive Movement (40 pts, 365 day decay)
- Renewal Window 120d (35 pts, 120 day decay)
- DOL Violation (30 pts, 180 day decay)

See `bit-schema.sql` for complete DDL.

---

## Section 6: Example Trigger - Executive Movement Detection

### Scenario

An enrichment agent detects that **Example Corp** has hired a new CFO. This triggers a chain reaction through the BIT system.

### Step-by-Step Flow

#### 1. Enrichment Agent Detects Movement

```sql
-- marketing.data_enrichment_log entry
INSERT INTO marketing.data_enrichment_log (
  enrichment_id,
  company_unique_id,
  agent_name,
  enrichment_type,
  status,
  movement_detected,
  movement_type,
  data_quality_score,
  result_data,
  completed_at
) VALUES (
  'ENRICH-2025-11-001',
  '04.04.02.04.30000.042',
  'Apify',
  'executive',
  'success',
  true,
  'executive_hire',
  95,
  '{
    "executive_name": "Jane Smith",
    "title": "Chief Financial Officer",
    "start_date": "2025-11-01",
    "previous_company": "Tech Giant Inc"
  }'::jsonb,
  NOW()
);
```

#### 2. BIT Event Trigger (Automatic)

```sql
-- Triggered by movement_detected = true
-- Function: bit.create_event_from_enrichment()

INSERT INTO bit.events (
  event_id,
  company_unique_id,
  event_type,
  rule_reference_id,
  event_payload,
  detected_at,
  data_quality_score
)
SELECT
  CONCAT('01.04.03.04.10000.', LPAD(NEXTVAL('bit.event_id_seq')::TEXT, 3, '0')),
  '04.04.02.04.30000.042',
  'executive_movement',
  '01.04.03.04.10000.101', -- executive_movement rule
  del.result_data,
  NOW(),
  del.data_quality_score
FROM marketing.data_enrichment_log del
WHERE del.movement_detected = true
  AND del.enrichment_id = 'ENRICH-2025-11-001';
```

Result:
```sql
event_id: 01.04.03.04.10000.042
company_unique_id: 04.04.02.04.30000.042
event_type: executive_movement
rule_reference_id: 01.04.03.04.10000.101
detected_at: 2025-11-07 14:30:00
data_quality_score: 95
```

#### 3. Score Calculation (Automatic via VIEW)

```sql
-- Query bit.scores view
SELECT * FROM bit.scores
WHERE company_unique_id = '04.04.02.04.30000.042';
```

Result:
```
company_unique_id: 04.04.02.04.30000.042
company_name: Example Corp
total_score: 38.0
score_category: Cold
event_count: 1
latest_event_date: 2025-11-07 14:30:00
score_breakdown: {
  "executive_movement": {
    "base_weight": 40,
    "decay_factor": 1.0,
    "quality_modifier": 0.95,
    "final_contribution": 38.0
  }
}
```

#### 4. Outreach Trigger Decision

```sql
-- Check if score warrants immediate outreach
SELECT
  company_name,
  total_score,
  score_category,
  CASE
    WHEN total_score >= 80 THEN 'Immediate outreach (24-48h)'
    WHEN total_score >= 50 THEN 'Nurture campaign (7-14d)'
    ELSE 'Monitor only'
  END AS recommended_action
FROM bit.scores
WHERE company_unique_id = '04.04.02.04.30000.042';
```

Result:
```
company_name: Example Corp
total_score: 38.0
score_category: Cold
recommended_action: Monitor only
```

**Note**: Score is below threshold for immediate action. However, if additional events occur (e.g., renewal window approaching), the cumulative score may trigger outreach.

---

## Section 7: Doctrine Relationships (Hub/Spoke/Axle/Wheel)

### SVG-PLE Architecture Mapping

```
┌─────────────────────────────────────────────────────────┐
│                     HUB (Core Data)                      │
│  • marketing.company_master                             │
│  • marketing.people_master                              │
│  • marketing.company_slot                               │
│  • Barton IDs: 04.04.02.04.#####.###                    │
└─────────────────────────────────────────────────────────┘
                            ▲
                            │ (Data flows UP to hub)
                            │
┌─────────────────────────────────────────────────────────┐
│                  SPOKES (Data Ingestion)                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Spoke 1: Talent Flow                            │   │
│  │  • Enrichment agents (Apify, Abacus, Firecrawl)  │   │
│  │  • marketing.data_enrichment_log                 │   │
│  │  • Detects: executive movements, hiring signals  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Spoke 2: Renewal Intelligence                   │   │
│  │  • Contract tracking system                      │   │
│  │  • Renewal window calculations                   │   │
│  │  • Alerts: 120d, 90d, 60d, 30d before expiry     │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Spoke 3: Compliance Monitor                     │   │
│  │  • DOL violation tracking                        │   │
│  │  • Regulatory event detection                    │   │
│  │  • Compliance pain point identification          │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼ (Events flow INTO axle)
┌─────────────────────────────────────────────────────────┐
│                   AXLE (BIT - You Are Here)              │
│  • bit.rule_reference (scoring rules)                   │
│  • bit.events (discrete intent signals)                 │
│  • bit.scores (aggregated intent scores)                │
│  • Converts events → scores → priorities                │
│  • Barton IDs: 01.04.03.04.10000.###                    │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼ (Scores flow TO wheel)
┌─────────────────────────────────────────────────────────┐
│                  WHEEL (Lead Cycles)                     │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Cycle 1: Hot Leads (80-100 score)               │   │
│  │  • Immediate personalized outreach               │   │
│  │  • 24-48 hour response time                      │   │
│  │  • Direct sales engagement                       │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Cycle 2: Warm Leads (50-79 score)               │   │
│  │  • Nurture campaign enrollment                   │   │
│  │  • 7-14 day follow-up cadence                    │   │
│  │  • Targeted content delivery                     │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Cycle 3: Cold Leads (0-49 score)                │   │
│  │  • Monitor only (no active outreach)             │   │
│  │  • Wait for additional signals                   │   │
│  │  • Re-evaluate when score increases              │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Data Flow Through Architecture

1. **Hub → Spoke**: Core company/contact data used by enrichment agents
2. **Spoke → Axle**: Events detected by spokes create BIT events
3. **Axle → Wheel**: Intent scores determine which cycle activates
4. **Wheel → Hub**: Outreach activities update company/contact records
5. **Hub → Spoke**: Updated records inform future enrichment

### Integration Points

| System | Integration Type | Data Exchange |
|--------|------------------|---------------|
| Hub (Marketing DB) | Bidirectional | Company/contact data ↔ BIT scores |
| Talent Flow Spoke | Event-driven | Enrichment events → BIT events |
| Renewal Spoke | Scheduled | Renewal windows → BIT events |
| Compliance Spoke | Event-driven | Violations → BIT events |
| Outreach Layer | Score-triggered | BIT scores → Campaign enrollment |
| Grafana | Read-only | BIT scores/events → Dashboards |

---

## Section 8: Cross-References

### Related Infrastructure

#### Barton Outreach Core Documentation

- **OUTREACH_DOCTRINE_A_Z_v1.3.2.md** - Complete system documentation
- **FINAL_AUDIT_SUMMARY.md** - 100% compliance audit (BIT included)
- **CLAUDE.md** - Bootstrap guide (BIT integration points)
- **global-config.yaml** - BIT configuration settings

#### Database Schema

- **docs/schema_map.json** - Complete schema reference (includes BIT)
- **infra/migrations/** - Database migrations (BIT schema changes)
- **ctb/data/migrations/README.md** - Migration guidelines

#### Grafana Dashboards

**Dashboard**: SVG-PLE Dashboard
**Location**: `infra/grafana/svg-ple-dashboard.json`
**URL**: https://dbarton.grafana.net/d/svg-ple-dashboard

**Panels**:
1. **BIT Heatmap** - Company intent scores (color-coded by category)
2. **Score Distribution** - Histogram of Hot/Warm/Cold companies
3. **Hot Companies** - Table of 80-100 score accounts
4. **Signal Types** - Breakdown of event types (last 30 days)

**Queries** (SQL):
- All queries in `infra/docs/ENRICHMENT_TRACKING_QUERIES.sql`
- BIT-specific queries in `doctrine/schemas/bit-queries.sql`

#### Related Doctrine Documents

- **Barton Doctrine ID System** - `OUTREACH_DOCTRINE_A_Z_v1.3.2.md` Section 3
- **Marketing Schema** - `OUTREACH_DOCTRINE_A_Z_v1.3.2.md` Section 5
- **Enrichment System** - `infra/docs/ENRICHMENT_TRACKING_DASHBOARD.md`

#### API Integration

**Enrichment Trigger Endpoint**:
```bash
POST /api/v1/enrichment/trigger
{
  "company_unique_id": "04.04.02.04.30000.042",
  "slot_type": "CEO"
}
```

**BIT Score Query Endpoint**:
```bash
GET /api/v1/bit/scores/{company_unique_id}
Response: {
  "company_unique_id": "04.04.02.04.30000.042",
  "total_score": 72.5,
  "score_category": "Warm",
  "event_count": 3,
  "latest_event_date": "2025-11-07T14:30:00Z"
}
```

#### Configuration Files

- **global-config.yaml** - BIT system enabled, tracking configured
- **ctb/ai/README.md** - Enrichment agents that feed BIT
- **.env** - Database connection for BIT schema access

---

## Section 9: Audit & Compliance Rules

### Barton Doctrine Compliance

#### ID Format Compliance

✅ **Requirement**: All BIT entities must use Barton Doctrine ID format
✅ **Format**: `01.04.03.04.10000.###`
✅ **Validation**: Enforced by database constraints and triggers

```sql
-- Validation check
SELECT event_id
FROM bit.events
WHERE event_id !~ '^01\.04\.03\.04\.10000\.\d{3}$';
-- Expected: 0 rows (all IDs compliant)
```

#### Data Quality Standards

✅ **Requirement**: All events must have data_quality_score >= 50
✅ **Enforcement**: CHECK constraint on `bit.events.data_quality_score`
✅ **Impact**: Low-quality events (< 50) are rejected at insert

```sql
ALTER TABLE bit.events
ADD CONSTRAINT chk_data_quality
CHECK (data_quality_score >= 50 AND data_quality_score <= 100);
```

#### Audit Trail Requirements

✅ **Requirement**: All changes to rules must be logged
✅ **Implementation**: Audit trigger on `bit.rule_reference`
✅ **Storage**: `public.shq_error_log` (severity: 'audit')

```sql
-- Audit trail query
SELECT * FROM public.shq_error_log
WHERE component = 'bit.rule_reference'
  AND severity = 'audit'
ORDER BY created_at DESC;
```

### Compliance Checks

#### Monthly Audit Checklist

Run these queries monthly to verify BIT system health:

**1. ID Format Compliance**
```sql
SELECT COUNT(*) AS non_compliant_ids
FROM bit.events
WHERE event_id !~ '^01\.04\.03\.04\.10000\.\d{3}$';
-- Expected: 0
```

**2. Active Rules Count**
```sql
SELECT COUNT(*) AS active_rules
FROM bit.rule_reference
WHERE is_active = true;
-- Expected: >= 10 (standard rule set)
```

**3. Orphaned Events**
```sql
SELECT COUNT(*) AS orphaned_events
FROM bit.events e
LEFT JOIN bit.rule_reference r ON e.rule_reference_id = r.rule_reference_id
WHERE r.rule_reference_id IS NULL;
-- Expected: 0
```

**4. Score Calculation Accuracy**
```sql
-- Verify bit.scores view produces valid results
SELECT COUNT(*) AS invalid_scores
FROM bit.scores
WHERE total_score < 0 OR total_score > 100;
-- Expected: 0
```

**5. Data Quality Distribution**
```sql
SELECT
  CASE
    WHEN data_quality_score >= 90 THEN 'High'
    WHEN data_quality_score >= 70 THEN 'Medium'
    ELSE 'Low'
  END AS quality_tier,
  COUNT(*) AS event_count
FROM bit.events
WHERE detected_at >= NOW() - INTERVAL '30 days'
GROUP BY quality_tier;
-- Expected: Majority in 'High' tier
```

#### Alert Thresholds

Configure alerts for these conditions:

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Orphaned events | > 0 | Immediate investigation |
| Non-compliant IDs | > 0 | Block new inserts until fixed |
| Inactive rules | > 50% | Review rule configuration |
| Low quality events | > 30% | Review enrichment agent performance |
| Score calculation errors | > 0 | Check VIEW definition |

### Compliance Automation

**Auto-Compliance Script**: `infra/scripts/compliance:complete`

Runs all compliance checks and generates report:
```bash
npm run compliance:complete -- --module=bit
```

Output: `audit_results/bit-compliance-YYYY-MM-DD.json`

---

## Section 10: Example Scenario - Executive Movement

### Real-World Scenario

**Company**: TechStart Inc (500 employees, SaaS industry)
**Event**: New CFO hired after previous CFO departure
**Timeline**: November 2025
**Additional Context**: Company is 90 days from contract renewal

### Scenario Walkthrough

#### Day 0: Executive Movement Detected

**Talent Flow Spoke** (Enrichment Agent: Apify)
```
LinkedIn Profile Scan Detects:
- Previous CFO: John Doe (departed Oct 30, 2025)
- New CFO: Jane Smith (started Nov 1, 2025)
- Source: LinkedIn profile update + company announcement
- Data Quality: 95/100 (verified via multiple sources)
```

**Database Insert**:
```sql
INSERT INTO marketing.data_enrichment_log (
  enrichment_id: 'ENRICH-2025-11-001',
  company_unique_id: '04.04.02.04.30000.123',
  agent_name: 'Apify',
  enrichment_type: 'executive',
  status: 'success',
  movement_detected: true,
  movement_type: 'executive_hire',
  data_quality_score: 95,
  result_data: {
    "new_executive": {
      "name": "Jane Smith",
      "title": "Chief Financial Officer",
      "start_date": "2025-11-01",
      "previous_company": "Fortune 500 Tech Co",
      "linkedin_url": "https://linkedin.com/in/janesmith"
    },
    "previous_executive": {
      "name": "John Doe",
      "departure_date": "2025-10-30",
      "tenure_years": 3
    }
  },
  completed_at: '2025-11-01 14:30:00'
);
```

#### Day 0: BIT Event Created (Automatic)

**Trigger Fires**: `bit.create_event_from_enrichment()`

```sql
INSERT INTO bit.events (
  event_id: '01.04.03.04.10000.045',
  company_unique_id: '04.04.02.04.30000.123',
  event_type: 'executive_movement',
  rule_reference_id: '01.04.03.04.10000.101',
  event_payload: { ... }, -- Copied from enrichment log
  detected_at: '2025-11-01 14:30:00',
  data_quality_score: 95
);
```

**Score Calculation**:
```
Rule: executive_movement (weight: 40, decay: 365 days)
Days Since: 0
Decay Factor: 1.0
Quality Modifier: 0.95
Score Contribution: 40 * 1.0 * 0.95 = 38 points
```

**Current Total Score**: 38 points → **Category: Cold** (0-49)

**Action**: No immediate outreach (score below 50 threshold)

---

#### Day 30: Renewal Window Opens (90 days before expiry)

**Renewal Spoke** detects contract approaching:

```sql
INSERT INTO bit.events (
  event_id: '01.04.03.04.10000.046',
  company_unique_id: '04.04.02.04.30000.123',
  event_type: 'renewal_window_90d',
  rule_reference_id: '01.04.03.04.10000.103',
  event_payload: {
    "contract_end_date": "2026-01-30",
    "current_vendor": "Competitor X",
    "contract_value": "$120,000/year"
  },
  detected_at: '2025-12-01 00:00:00',
  data_quality_score: 100
);
```

**Score Calculation**:
```
Event 1: executive_movement
  Base: 40, Days: 30, Decay: 0.918, Quality: 0.95
  Contribution: 40 * 0.918 * 0.95 = 34.88 points

Event 2: renewal_window_90d
  Base: 45, Days: 0, Decay: 1.0, Quality: 1.0
  Contribution: 45 * 1.0 * 1.0 = 45 points

Total Score: 34.88 + 45 = 79.88 points
```

**Current Total Score**: 79.88 points → **Category: Warm** (50-79)

**Action**: Enroll in nurture campaign
- Send targeted content about CFO challenges
- 7-day follow-up cadence
- Focus on contract renewal messaging

---

#### Day 60: Additional Signal (Tech Stack Change Detected)

**Enrichment agent** detects company adopted new HR software:

```sql
INSERT INTO bit.events (
  event_id: '01.04.03.04.10000.047',
  company_unique_id: '04.04.02.04.30000.123',
  event_type: 'tech_stack_change',
  rule_reference_id: '01.04.03.04.10000.109',
  event_payload: {
    "change_type": "new_hr_software",
    "vendor": "Modern HR Platform",
    "detected_source": "job_postings"
  },
  detected_at: '2025-12-31 10:00:00',
  data_quality_score: 80
);
```

**Score Calculation**:
```
Event 1: executive_movement
  Base: 40, Days: 60, Decay: 0.836, Quality: 0.95
  Contribution: 40 * 0.836 * 0.95 = 31.77 points

Event 2: renewal_window_90d
  Base: 45, Days: 30, Decay: 0.667, Quality: 1.0
  Contribution: 45 * 0.667 * 1.0 = 30.02 points

Event 3: tech_stack_change
  Base: 35, Days: 0, Decay: 1.0, Quality: 0.80
  Contribution: 35 * 1.0 * 0.80 = 28 points

Total Score: 31.77 + 30.02 + 28 = 89.79 points
```

**Current Total Score**: 89.79 points → **Category: Hot** (80-100) 🔥

**Action**: Immediate personalized outreach
- Assign to senior sales rep
- 24-hour response time
- Personalized email referencing:
  - New CFO (Jane Smith)
  - Upcoming renewal window (30 days out)
  - Recent tech modernization efforts

---

#### Day 61: Outreach Executed

**Email Template (Personalized)**:

```
Subject: Congrats on your new role, Jane - Quick question about Feb renewal

Hi Jane,

Congratulations on joining TechStart as CFO! I saw the announcement last
month and wanted to reach out.

With your contract renewal coming up in 30 days (Jan 30), and knowing you're
modernizing your tech stack (saw you recently adopted Modern HR Platform),
I thought it'd be worth connecting.

We help companies like TechStart with [our solution]. Would you have 15
minutes this week to discuss how we might support your goals as you evaluate
vendors for the upcoming renewal?

Best,
[Sales Rep Name]
```

**Expected Outcome**: High response rate due to:
- ✅ Perfect timing (renewal decision window)
- ✅ Personalized to new CFO role
- ✅ References recent company changes
- ✅ Non-pushy, value-focused approach

---

### Scoring Timeline Visualization

```
BIT Score Over Time for TechStart Inc

100 ├─────────────────────────────────────────────────────────
    │                                                    🔥 89.79
 90 ├────────────────────────────────────────────────────●
    │                                              ◆ 79.88
 80 ├──────────────────────────────────────────────●
    │
 70 ├───────────────────────────────────────────────
    │
 60 ├───────────────────────────────────────────────
    │
 50 ├──────────────────────────────────🔶 Warm───────
    │                              ◆ 38
 40 ├───────────────────────────────●
    │
 30 ├─────────🔵 Cold────────────────────────────────
    │
 20 ├───────────────────────────────────────────────
    │
 10 ├───────────────────────────────────────────────
    │
  0 └─────────────────────────────────────────────────
    Day 0        Day 30       Day 60        Day 90
    (CFO Hire)   (Renewal     (Tech Stack   (Outreach
                  Window)      Change)       Executed)

Legend:
● = executive_movement event
◆ = renewal_window_90d event
◆ = tech_stack_change event
```

### Outcome

**Result**: Company responds positively to outreach
- **Response Time**: 8 hours (well within 24-48h target)
- **Meeting Scheduled**: 2 days later
- **Pipeline Value**: $150,000/year opportunity
- **Win Probability**: 40% (high due to perfect timing)

**BIT System ROI**:
- Identified high-intent account automatically
- Prioritized over 200+ other accounts in database
- Triggered outreach at optimal moment (89.79 score)
- Sales rep had perfect context for personalization
- No manual lead qualification required

---

## Appendix A: Quick Reference

### Key Concepts

| Term | Definition |
|------|------------|
| **BIT** | Buyer Intent Tool - Scoring engine that converts events into intent scores |
| **Event** | Discrete business signal (executive hire, renewal window, etc.) |
| **Rule** | Scoring logic with weight and decay parameters |
| **Score** | Aggregated intent metric (0-100 scale) |
| **Decay** | Time-based reduction of score relevance |
| **Quality Modifier** | Adjustment based on data quality (50-100) |

### Score Categories

- **Hot** (80-100): Immediate outreach, 24-48h response
- **Warm** (50-79): Nurture campaign, 7-14d follow-up
- **Cold** (0-49): Monitor only, no active outreach

### Barton ID Prefix

`01.04.03.04.10000` - BIT system identifier

### Key Tables

- `bit.rule_reference` - Scoring rules
- `bit.events` - Event log
- `bit.scores` - Real-time scores (VIEW)

### Schema Location

`doctrine/schemas/bit-schema.sql`

### Related Dashboards

- SVG-PLE Dashboard: https://dbarton.grafana.net/d/svg-ple-dashboard
- Executive Enrichment: https://dbarton.grafana.net/d/executive-enrichment-monitoring

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-07 | Barton Outreach Team | Initial BIT Doctrine creation |

---

**End of BIT Doctrine**

*For technical implementation details, see `doctrine/schemas/bit-schema.sql`*
*For operational queries, see `doctrine/schemas/bit-queries.sql`*
*For integration examples, see `infra/docs/ENRICHMENT_TRACKING_DASHBOARD.md`*
