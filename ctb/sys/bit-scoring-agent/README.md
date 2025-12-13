# BIT Scoring Agent - Signal to Score Engine

**Barton Doctrine ID**: `04.04.02.04.70000.001`
**CTB Layer**: System (Yellow - AI/SHQ nerve)
**Status**: ✅ READY FOR DEPLOYMENT

---

## 🎯 Mission

Convert events (signals) into numeric Buyer Intent Scores that trigger sales actions.

**The question BIT answers**: *"How ready is this person/company to take a meeting?"*

**No vibes. Pure math.**

---

## 📊 Architecture

```
config/                           ← EDIT THESE to fix logic (not code)
├── scoring_config.json           ← Agent settings, safety rules
└── trigger_config.json           ← Action thresholds, trigger rules

core/                             ← Modular components (standalone)
├── neon_connector.py             ← All SQL queries live here
├── score_calculator.py           ← Score calculation logic
└── trigger_evaluator.py          ← Threshold evaluation & actions

agent_bit_scoring.py              ← Main orchestrator (ties modules together)
```

**Key Design Principle**: Configuration over code = easy corrections

---

## 🔄 How It Works

### Step-by-Step Flow

1. **Pull Unscored Signals** (last 7 days)
   - From `bit_signal` table
   - Where `scored = FALSE`
   - Group by person/company

2. **For Each Person/Company**:
   - Get ALL signals (including previously scored ones)
   - Calculate raw score: `Σ(signal_weight × signal_value)`
   - Calculate decayed score: `Σ(signal_weight × signal_value × confidence × decay)`
   - Determine score tier (cold/warm/engaged/hot/burning)
   - Check safety limits (max increase per day)

3. **Evaluate Triggers**:
   - Check if tier changed (only trigger on increase)
   - Validate action requirements (email, phone, etc.)
   - Check deduplication (prevent duplicate actions within 72 hours)
   - Determine action type (ignore/watch/nurture/sdr_escalate/auto_meeting)

4. **Write Results**:
   - Upsert to `bit_score` table
   - Insert to `outreach_log` (if triggered)
   - Insert to `meeting_queue` (if auto_meeting)
   - Log to `shq.audit_log`
   - Auto-mark signals as scored (via database trigger)

---

## 🛡️ Safety Features (Kill Switches)

### ✅ No Double-Scoring (Idempotent Writes)
Database trigger auto-marks signals as `scored = TRUE` after score calculation.

**Config**: `safety.no_double_scoring = true`

**Database Trigger**:
```sql
CREATE TRIGGER trigger_mark_signals_scored
AFTER INSERT OR UPDATE ON marketing.bit_score
FOR EACH ROW
EXECUTE FUNCTION marketing.mark_signal_scored();
```

### ✅ No Runaway Escalations
Caps score increases to max per day (default: 300 points).

**Config**: `safety.max_score_increase_per_day = 300`

### ✅ No Missing Weight Defaults
All signal types have explicit weights. Fallback to default if missing.

**Config**: `scoring.default_signal_weight = 40`

### ✅ Deduplication Window
Won't trigger same action twice within 72 hours.

**Config**: `trigger.deduplication_window_hours = 72`

---

## 📋 Scoring Formula

### Core Formula

```
Raw Score = Σ(weight × signal_value)

Decayed Score = Σ(weight × signal_value × confidence × decay)
```

**Where**:
- `weight` = signal type weight (from `bit_signal_weights` table)
- `signal_value` = 1.0 (default, could be dynamic)
- `confidence` = data source quality multiplier (from `bit_confidence_modifiers`)
- `decay` = time-based decay factor (from `bit_decay_rules`)

### Example Calculation

**Scenario**: Person has 3 signals

1. **Movement: Promotion** (detected 5 days ago, from PeopleDataLabs)
   - Weight: 70
   - Confidence: 1.15 (PDL)
   - Decay: 1.0 (0-7 days)
   - Contribution: 70 × 1 × 1.15 × 1.0 = **80.5**

2. **Email Open** (detected 10 days ago, from email tracking)
   - Weight: 10
   - Confidence: 1.0 (email tracking)
   - Decay: 0.85 (8-30 days)
   - Contribution: 10 × 1 × 1.0 × 0.85 = **8.5**

3. **Demo Request** (detected 2 days ago, manual entry)
   - Weight: 100
   - Confidence: 1.2 (manual)
   - Decay: 1.0 (0-7 days)
   - Contribution: 100 × 1 × 1.2 × 1.0 = **120**

**Total Decayed Score**: 80.5 + 8.5 + 120 = **209 points**

**Score Tier**: **hot** (200-299 range)

**Action Triggered**: **sdr_escalate**

---

## 🎚️ Score Tiers & Actions

| Tier | Score Range | Action | Description |
|------|-------------|--------|-------------|
| **cold** | 0-49 | ignore | No engagement detected |
| **warm** | 50-99 | watch | Monitor for additional signals |
| **engaged** | 100-199 | nurture | Send targeted nurture content |
| **hot** | 200-299 | sdr_escalate | Escalate to SDR for outreach |
| **burning** | 300+ | auto_meeting | Auto-schedule meeting or urgent follow-up |

**Trigger Rules**:
- Only trigger on **tier increase** (not every score change)
- Validate contact info before triggering (email/phone required)
- Deduplicate within 72-hour window
- Auto-execute enabled for engaged/hot/burning tiers

---

## 📊 Signal Weights

### Movement Signals (from Talent Flow Agent)

| Signal Type | Weight | Description |
|-------------|--------|-------------|
| movement_hire | 50 | Person hired at new company |
| movement_exit | 30 | Person left company |
| movement_promotion | 70 | Person promoted within company |
| movement_transfer | 40 | Person transferred roles |

### Email Engagement

| Signal Type | Weight | Description |
|-------------|--------|-------------|
| email_open | 10 | Email opened |
| email_click | 25 | Email link clicked |
| email_reply | 60 | Email replied to |

### Website Activity

| Signal Type | Weight | Description |
|-------------|--------|-------------|
| website_visit | 15 | Company website visited |
| content_download | 35 | Whitepaper/content downloaded |
| demo_request | 100 | Demo request submitted |
| pricing_page_view | 45 | Pricing page viewed |

### Social Engagement

| Signal Type | Weight | Description |
|-------------|--------|-------------|
| linkedin_engage | 20 | LinkedIn post engagement |

### Profile Attributes

| Signal Type | Weight | Description |
|-------------|--------|-------------|
| enrichment_update | 5 | Profile enriched with new data |
| role_executive | 30 | Executive-level role (CEO/CFO/CTO) |
| role_director | 20 | Director-level role |
| role_manager | 10 | Manager-level role |
| company_size_large | 25 | Company size 500+ employees |
| company_size_medium | 15 | Company size 50-500 employees |
| industry_target | 20 | Company in target industry |

**Total**: 19 signal types

---

## ⏱️ Time Decay Rules

| Rule Name | Age (Days) | Decay Factor | Weight % |
|-----------|------------|--------------|----------|
| fresh_0_7 | 0-7 | 1.000 | 100% |
| recent_8_30 | 8-30 | 0.850 | 85% |
| moderate_31_90 | 31-90 | 0.650 | 65% |
| aged_91_180 | 91-180 | 0.400 | 40% |
| stale_181_365 | 181-365 | 0.200 | 20% |
| expired_365_plus | 365+ | 0.050 | 5% |

**Purpose**: Recent signals are more valuable than old ones.

---

## 🎯 Confidence Modifiers (Data Source Quality)

| Source | Multiplier | Quality |
|--------|------------|---------|
| manual | 1.200 | Highest trust |
| peopledatalabs | 1.150 | Verified data |
| talent_flow_movement | 1.100 | Movement detection |
| rocketreach | 1.100 | High quality |
| clearbit | 1.050 | Good quality |
| email_tracking | 1.000 | Neutral (baseline) |
| abacus | 0.950 | Good |
| clay | 0.900 | Enrichment platform |
| apify | 0.900 | Scraping |
| firecrawl | 0.850 | Web scraping |
| zenrows | 0.800 | Scraping API |
| scraperapi | 0.800 | Scraping API |
| scrapingbee | 0.750 | Scraping API |
| serpapi | 0.750 | Search API |
| unknown | 0.700 | Lowest trust |

**Purpose**: Weight signals based on data source reliability.

---

## 🎛️ Configuration

### Scoring Config (`config/scoring_config.json`)

**What you can edit**:
- ✅ Database connection settings
- ✅ Batch size and concurrency
- ✅ Lookback period (default: 7 days)
- ✅ Default signal weight (fallback)
- ✅ Score caps (min/max)
- ✅ Decay and confidence toggles
- ✅ Safety rules (max increase per day)
- ✅ Logging configuration

**Example**:
```json
{
  "scoring": {
    "default_signal_weight": 40,
    "max_score_cap": 1000,
    "min_score_floor": 0,
    "decay_enabled": true,
    "confidence_enabled": true
  },
  "safety": {
    "no_double_scoring": true,
    "max_score_increase_per_day": 300
  }
}
```

### Trigger Config (`config/trigger_config.json`)

**What you can edit**:
- ✅ Trigger levels (score ranges)
- ✅ Action types (ignore/watch/nurture/sdr_escalate/auto_meeting)
- ✅ Auto-execute toggles
- ✅ Action requirements (email, phone)
- ✅ Deduplication window
- ✅ Notification settings

**Example**:
```json
{
  "trigger_levels": {
    "burning": {
      "min_score": 300,
      "max_score": null,
      "action": "auto_meeting",
      "enabled": true,
      "auto_execute": true,
      "priority": "urgent"
    }
  },
  "deduplication": {
    "enabled": true,
    "window_hours": 72
  }
}
```

---

## 🚀 Usage

### 1. Install Dependencies

```bash
cd ctb/sys/bit-scoring-agent
pip install -r requirements.txt
```

### 2. Create Database Tables

```bash
psql $NEON_DATABASE_URL -f schema/create_bit_scoring_tables.sql
```

### 3. Configure Environment

```bash
# Add to .env
NEON_DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

### 4. Run Agent

```bash
python agent_bit_scoring.py
```

**Expected Output**:
```
🚀 BIT Scoring Agent Starting
   Worker ID: bit-scoring-abc12345
   Process ID: PRC-BIT-20251119143000

✅ Connected to Neon database
📥 Loading weight tables...
   ✅ Loaded 19 signal weights
   ✅ Weight tables loaded

📊 Found 45 unscored signals (last 7 days)
👥 Processing 12 person/company combinations

🔢 John Smith: Calculating BIT score...
   Raw: 180, Decayed: 155, Tier: engaged
   🔔 TRIGGER: nurture (priority: medium)
      → Outreach log created (ID: 123)

🔢 Jane Doe: Calculating BIT score...
   Raw: 350, Decayed: 320, Tier: burning
   🔔 TRIGGER: auto_meeting (priority: urgent)
      → Outreach log created (ID: 124)
      → Meeting queued (ID: 45, priority: urgent)

...

📊 BIT SCORING AGENT - EXECUTION SUMMARY
Signals Processed: 45
Scores Calculated: 8
Scores Updated: 4
Triggers Fired: 6
  - Meetings Queued: 2
Skipped (Duplicate): 1
Errors: 0
```

---

## 🗄️ Database Schema

### bit_signal_weights
Defines weight for each signal type.

| Column | Type | Description |
|--------|------|-------------|
| weight_id | SERIAL | Primary key |
| signal_type | TEXT | Signal type (unique) |
| weight | INTEGER | Numeric weight |
| description | TEXT | Human-readable description |
| active | BOOLEAN | Enable/disable weight |

### bit_decay_rules
Time-based decay factors for signal aging.

| Column | Type | Description |
|--------|------|-------------|
| decay_id | SERIAL | Primary key |
| rule_name | TEXT | Rule name (unique) |
| days_threshold | INTEGER | Age threshold in days |
| decay_factor | NUMERIC(4,3) | Multiplier (0.0 - 1.0) |
| applies_to | TEXT[] | Signal types (NULL = all) |
| active | BOOLEAN | Enable/disable rule |

### bit_confidence_modifiers
Data source quality multipliers.

| Column | Type | Description |
|--------|------|-------------|
| modifier_id | SERIAL | Primary key |
| source | TEXT | Data source (unique) |
| confidence_multiplier | NUMERIC(4,3) | Multiplier (0.0 - 2.0) |
| description | TEXT | Human-readable description |
| active | BOOLEAN | Enable/disable modifier |

### bit_trigger_thresholds
Score thresholds that trigger actions.

| Column | Type | Description |
|--------|------|-------------|
| threshold_id | SERIAL | Primary key |
| trigger_level | TEXT | Tier name (cold/warm/engaged/hot/burning) |
| min_score | INTEGER | Minimum score |
| max_score | INTEGER | Maximum score (NULL = no upper bound) |
| action_type | TEXT | Action (ignore/watch/nurture/sdr_escalate/auto_meeting) |
| description | TEXT | Human-readable description |
| active | BOOLEAN | Enable/disable threshold |

### bit_score
Computed BIT scores per person/company.

| Column | Type | Description |
|--------|------|-------------|
| score_id | BIGSERIAL | Primary key |
| person_unique_id | TEXT | FK to people_master |
| company_unique_id | TEXT | FK to company_master |
| raw_score | INTEGER | Sum of all signal weights (no decay) |
| decayed_score | INTEGER | Score after applying time decay |
| score_tier | TEXT | Tier (cold/warm/engaged/hot/burning) |
| last_signal_at | TIMESTAMPTZ | Most recent signal timestamp |
| signal_count | INTEGER | Number of signals contributing to score |
| computed_at | TIMESTAMPTZ | When score was calculated |
| metadata | JSONB | Score breakdown, worker ID, etc. |

**Unique constraint**: `(person_unique_id, company_unique_id)`

### outreach_log
Actions triggered by BIT scores.

| Column | Type | Description |
|--------|------|-------------|
| outreach_id | BIGSERIAL | Primary key |
| person_unique_id | TEXT | FK to people_master |
| company_unique_id | TEXT | FK to company_master |
| action_type | TEXT | Action triggered |
| bit_score | INTEGER | Score at time of trigger |
| score_tier | TEXT | Tier at time of trigger |
| trigger_reason | TEXT | Human-readable reason |
| metadata | JSONB | Additional details |
| created_at | TIMESTAMPTZ | When triggered |
| processed | BOOLEAN | Whether action was executed |
| processed_at | TIMESTAMPTZ | When action was executed |

### meeting_queue
High-score contacts requiring meetings.

| Column | Type | Description |
|--------|------|-------------|
| meeting_id | BIGSERIAL | Primary key |
| person_unique_id | TEXT | FK to people_master |
| company_unique_id | TEXT | FK to company_master |
| bit_score | INTEGER | Score at time of queueing |
| priority | TEXT | Priority (low/medium/high/urgent) |
| status | TEXT | Status (pending/scheduled/completed/cancelled) |
| scheduled_at | TIMESTAMPTZ | When meeting was scheduled |
| completed_at | TIMESTAMPTZ | When meeting was completed |
| metadata | JSONB | Additional details |
| created_at | TIMESTAMPTZ | When queued |

---

## 🧪 Testing

### Test with Small Batch

Edit `config/scoring_config.json`:
```json
{
  "processing": {
    "batch_size": 10,
    "lookback_days": 3
  }
}
```

Then run:
```bash
python agent_bit_scoring.py
```

### Test Specific Person

```python
from core.neon_connector import NeonConnector
from core.score_calculator import ScoreCalculator
import asyncio
import json

async def test_person():
    with open('config/scoring_config.json', 'r') as f:
        config = json.load(f)

    db = NeonConnector(config)
    calculator = ScoreCalculator(config)

    await db.connect()

    # Get signals for specific person
    person_id = "04.04.02.04.20000.001"
    company_id = "04.04.02.04.30000.001"

    signals = await db.get_person_signals(person_id, company_id, include_scored=True)

    # Calculate score
    score_result = calculator.calculate_score(
        signals=signals,
        decay_lookup_fn=db.get_decay_factor
    )

    print(f"Raw Score: {score_result['raw_score']}")
    print(f"Decayed Score: {score_result['decayed_score']}")
    print(f"Signal Count: {score_result['signal_count']}")
    print(f"Breakdown: {score_result['score_breakdown']}")

    await db.close()

asyncio.run(test_person())
```

---

## 🔧 Troubleshooting

### No Triggers Firing

**Check**:
1. Are there unscored signals? Query: `SELECT COUNT(*) FROM marketing.bit_signal WHERE scored = FALSE;`
2. Is score high enough for trigger tier? Check thresholds in database
3. Has tier changed? Triggers only fire on tier increase
4. Is deduplication blocking? Check `outreach_log` for recent actions

**Fix**: Edit `trigger_config.json` to lower thresholds or disable deduplication

### Scores Too High/Low

**Check**:
1. Are signal weights correct? Query: `SELECT * FROM marketing.bit_signal_weights;`
2. Is decay enabled? Check `scoring_config.json`
3. Are confidence modifiers too high/low? Query: `SELECT * FROM marketing.bit_confidence_modifiers;`

**Fix**: Edit weight values in database or adjust config settings

### Database Connection Issues

**Check**:
1. Is `NEON_DATABASE_URL` set correctly in `.env`?
2. Do tables exist? Run `schema/create_bit_scoring_tables.sql`
3. Does user have permissions?

---

## 📊 Cost Estimate

**Monthly Execution**:
- 700 companies × ~2 employees/company = 1,400 people
- Assume 10 signals per person per month = 14,000 signals
- 1 run per day = ~467 signals per run
- Processing time: ~3-5 minutes per run
- Database queries: ~5,600 queries per run
- **Cost**: Negligible (Neon free tier supports this easily)

---

## 🎯 Integration with Talent Flow Agent

**Data Flow**:
```
Talent Flow Agent detects movement
    ↓
Inserts to bit_signal table (scored = FALSE)
    ↓
BIT Scoring Agent picks up unscored signal
    ↓
Calculates score with decay + confidence
    ↓
Determines tier and triggers action
    ↓
Writes to outreach_log and meeting_queue
    ↓
SDR/Sales executes action
```

**Example**:
1. Talent Flow detects promotion: "John Smith promoted to VP of Sales at Acme Corp"
2. Talent Flow inserts BIT signal: `signal_type='movement_promotion', weight=70, scored=FALSE`
3. BIT Scoring runs and sees unscored signal
4. BIT Scoring calculates: 70 (weight) × 1.15 (PDL confidence) × 1.0 (fresh decay) = 80 points
5. John's total score increases from 150 → 230 (tier: engaged → hot)
6. Tier change triggers: `action_type='sdr_escalate'`
7. Outreach log created, SDR receives notification

---

## 🎯 Next Steps

1. ✅ **Deploy BIT Scoring Agent** (DONE)
2. 🔜 **Build Backfill Agent** (700 companies baseline)
3. 🔜 **Test end-to-end** (enrichment → movement → BIT → outreach trigger)
4. 🔜 **Connect to CRM** (push outreach_log actions to Salesforce/HubSpot)

---

**BIT Scoring Agent is THE ENGINE that powers intelligent outreach.**
**Without BIT scores → no prioritization → no targeted actions.**
