# Talent Flow Agent - Movement Detection Engine

**Barton Doctrine ID**: `04.04.02.04.60000.001`
**CTB Layer**: System (Yellow - AI/SHQ nerve)
**Status**: ✅ READY FOR DEPLOYMENT

---

## 🎯 Mission

Detect human movement (hires, exits, promotions, transfers) monthly and convert to BIT signals that steer outreach intelligently.

**No magic. Pure deterministic rules.**

---

## 📊 Architecture

```
config/                    ← EDIT THESE to fix logic (not code)
├── movement_rules.json    ← Rules for detecting movements
├── confidence_weights.json ← Confidence calculation weights
└── agent_config.json      ← DB connection, safety rules

core/                      ← Modular components (standalone)
├── neon_connector.py      ← All SQL queries live here
├── diff_engine.py         ← Hash comparison logic
├── movement_classifier.py ← Movement detection rules
└── confidence_scorer.py   ← Confidence calculation

agent_talent_flow.py       ← Main orchestrator (ties modules together)
```

**Key Design Principle**: Configuration over code = easy corrections

---

## 🔄 How It Works

### Step-by-Step Flow

1. **Pull Active People** (last 30 days)
   - From `people_master`
   - Who have been updated recently OR have no snapshot yet

2. **For Each Person**:
   - Compute hash of current state (name, title, company, dates, linkedin)
   - Get last snapshot hash
   - **If hash unchanged** → Skip (no movement)
   - **If hash changed** → Analyze delta

3. **Detect Movement**:
   - Compare old state vs new state
   - Check against 4 movement types: hire, exit, promotion, transfer
   - Match rules from `movement_rules.json`
   - Calculate base confidence

4. **Calculate Final Confidence**:
   - Apply data source weight (PDL > Abacus > Firecrawl)
   - Apply recency multiplier (recent = higher confidence)
   - Add field completeness bonus
   - Add movement-specific modifiers
   - Cap at min/max thresholds

5. **Write Results**:
   - Insert to `talent_flow_movements`
   - Generate BIT signal → `bit_signal`
   - Save new snapshot → `talent_flow_snapshots`
   - Log to `shq.audit_log`

---

## 🛡️ Safety Features (Kill Switches)

### ✅ No Reprocessing Same Hash
If hash hasn't changed, skip processing entirely.

**Config**: `safety.require_hash_change = true`

### ✅ Cooldown Period
Won't reprocess same person within 168 hours (7 days) of last movement.

**Config**: `safety.cooldown_hours = 168`

### ✅ Max Movements Per Person Per Month
Limit: 2 movements per person per month. Prevents runaway detection.

**Config**: `safety.max_movements_per_person_per_month = 2`

### ✅ Contradiction Detection
Detects suspicious patterns (e.g., company name changed but company_unique_id stayed same) and logs to `garage.contradictions`.

**Config**: `safety.no_multipass_contradictions = true`

---

## 📋 Movement Types

### 1. **Hire** (Signal Weight: 50)
**Rules**:
- Company name changed AND title exists
- Start date recent AND company changed
- Previous company was null AND current company exists

**Example**: Person moved from "Acme Corp" to "NewCo Inc"

---

### 2. **Exit** (Signal Weight: 30)
**Rules**:
- End date exists AND company unchanged
- Title is null AND previously had title
- Company is null AND previously had company

**Example**: Person left "Acme Corp", end_date populated

---

### 3. **Promotion** (Signal Weight: 70)
**Rules**:
- Title changed AND company unchanged AND title level increased
- Title keywords match promotion (VP, SVP, Director, etc.) AND company unchanged
- Org layer increased AND company unchanged

**Example**: "Engineer" → "Senior Engineer" at same company

---

### 4. **Transfer** (Signal Weight: 40)
**Rules**:
- Title changed AND company unchanged AND title level same
- Department changed AND company unchanged

**Example**: "Sales Manager" → "Operations Manager" at same company

---

## 🎛️ Configuration

### Movement Rules (`config/movement_rules.json`)

**What you can edit**:
- ✅ Movement type rules and conditions
- ✅ Minimum confidence thresholds
- ✅ Title level classifications
- ✅ Hash fields to compare
- ✅ Promotion keywords

**Example**:
```json
{
  "movement_types": {
    "promotion": {
      "rules": [
        {
          "condition": "title_changed AND company_name_unchanged AND title_level_increased",
          "weight": 1.0
        }
      ],
      "min_confidence": 0.7
    }
  }
}
```

### Confidence Weights (`config/confidence_weights.json`)

**What you can edit**:
- ✅ Data source weights (PDL vs Abacus vs Firecrawl)
- ✅ Recency multipliers (7 days vs 90 days vs 365 days)
- ✅ Field completeness bonuses
- ✅ Movement-specific modifiers
- ✅ Min/max confidence caps

**Example**:
```json
{
  "data_source_weights": {
    "peopledatalabs": 1.0,
    "clearbit": 0.9,
    "abacus": 0.85,
    "firecrawl": 0.7
  }
}
```

### Agent Config (`config/agent_config.json`)

**What you can edit**:
- ✅ Database connection settings
- ✅ Batch size and concurrency
- ✅ Lookback period (default: 30 days)
- ✅ Safety rules (cooldown, max movements)
- ✅ BIT integration settings
- ✅ Logging configuration

---

## 🚀 Usage

### 1. Install Dependencies

```bash
cd ctb/sys/talent-flow-agent
pip install -r requirements.txt
```

### 2. Create Database Tables

```bash
psql $NEON_DATABASE_URL -f schema/create_talent_flow_tables.sql
```

### 3. Configure Environment

```bash
# Add to .env
NEON_DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

### 4. Run Agent

```bash
python agent_talent_flow.py
```

**Expected Output**:
```
🚀 Talent Flow Agent Starting
   Worker ID: talent-flow-abc12345
   Process ID: PRC-TF-20251119143000

✅ Connected to Neon database
📊 Found 150 people to process (last 30 days)

📦 Processing batch 1 (100 people)
🔄 John Smith: Hash changed, analyzing...
   Changed fields: ['title', 'company_name']
   ✅ HIRE: 0.87 (high)
      Rules matched: ['company_name_changed AND title_exists']
      → BIT signal generated (weight: 43)

...

📊 TALENT FLOW AGENT - EXECUTION SUMMARY
Processed: 150
Movements Detected: 12
  - Hires: 5
  - Exits: 2
  - Promotions: 4
  - Transfers: 1
BIT Signals Generated: 12
Snapshots Saved: 150
Contradictions Detected: 1
```

---

## 🗄️ Database Schema

### talent_flow_snapshots
Stores monthly snapshots for hash comparison.

| Column | Type | Description |
|--------|------|-------------|
| snapshot_id | BIGSERIAL | Primary key |
| person_unique_id | TEXT | FK to people_master |
| enrichment_hash | TEXT | MD5 hash for change detection |
| snapshot_data | JSONB | Full person record at time |
| snapshot_date | DATE | Date of snapshot |
| created_at | TIMESTAMPTZ | Creation timestamp |

**Unique**: `(person_unique_id, snapshot_date)`

### talent_flow_movements
Stores detected movements.

| Column | Type | Description |
|--------|------|-------------|
| movement_id | BIGSERIAL | Primary key |
| person_unique_id | TEXT | FK to people_master |
| movement_type | TEXT | hire/exit/promotion/transfer |
| confidence | NUMERIC(5,3) | 0.0 - 1.0 |
| old_state | JSONB | State before movement |
| new_state | JSONB | State after movement |
| data_source | TEXT | Source of data |
| metadata | JSONB | Movement-specific details |
| detected_at | TIMESTAMPTZ | When detected |

### bit_signal
Stores BIT signals generated from movements.

| Column | Type | Description |
|--------|------|-------------|
| signal_id | BIGSERIAL | Primary key |
| person_unique_id | TEXT | FK to people_master |
| company_unique_id | TEXT | FK to company_master |
| signal_type | TEXT | movement_hire, movement_exit, etc. |
| signal_weight | INTEGER | Numeric weight for scoring |
| source_id | BIGINT | movement_id |
| source_type | TEXT | talent_flow_movement |
| metadata | JSONB | Additional details |
| detected_at | TIMESTAMPTZ | When detected |

---

## 🧪 Testing

### Test with Small Batch

Edit `config/agent_config.json`:
```json
{
  "processing": {
    "batch_size": 10,
    "lookback_days": 7
  }
}
```

Then run:
```bash
python agent_talent_flow.py
```

### Test Specific Person

```python
from core.neon_connector import NeonConnector
from core.diff_engine import DiffEngine
from core.movement_classifier import MovementClassifier

# Load person data
# Compute hash
# Classify movement
# Print results
```

---

## 🔧 Troubleshooting

### No Movements Detected

**Check**:
1. Are people's records updated in last 30 days?
2. Has hash actually changed?
3. Do movement rules match the delta?
4. Is confidence above min threshold?

**Fix**: Edit `movement_rules.json` to adjust thresholds

### Too Many Movements Detected

**Check**:
1. Are confidence thresholds too low?
2. Is cooldown period too short?
3. Are rules too broad?

**Fix**: Edit `movement_rules.json` min_confidence or `agent_config.json` cooldown_hours

### Database Connection Issues

**Check**:
1. Is `NEON_DATABASE_URL` set correctly?
2. Do tables exist? Run `schema/create_talent_flow_tables.sql`
3. Does user have permissions?

---

## 📊 Cost Estimate

**Monthly Execution**:
- 700 companies × ~2 employees/company = 1,400 people
- 1 run per month = 1,400 records processed
- Processing time: ~5-10 minutes
- Database queries: ~5,600 queries (4 per person)
- **Cost**: Negligible (Neon free tier supports this easily)

---

## 🎯 Next Steps

1. ✅ **Deploy Talent Flow Agent** (DONE)
2. 🔜 **Build BIT Scoring Agent** (use movements to calculate scores)
3. 🔜 **Build Backfill Agent** (700 companies baseline)
4. 🔜 **Test end-to-end** (movement → BIT → outreach trigger)

---

**Talent Flow Agent is THE SPINE of the outreach system.**
**Without movement detection → no BIT signals → no outreach progression.**
