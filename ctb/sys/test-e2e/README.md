# End-to-End Agent Flow Test

**Barton Doctrine ID**: `04.04.02.04.90000.001`
**Purpose**: Verify all three agents work together correctly

---

## Test Coverage

### 1. Database Connectivity Test
- ✅ Verify Neon PostgreSQL connection
- ✅ Test basic query execution

### 2. Schema Validation Test
- ✅ Verify all 17 tables exist:
  - **Backfill**: backfill_log, bit_baseline_snapshot, talent_flow_baseline, garage.missing_parts
  - **Talent Flow**: talent_flow_snapshots, talent_flow_movements, bit_signal
  - **BIT Scoring**: bit_signal_weights, bit_decay_rules, bit_confidence_modifiers, bit_trigger_thresholds, bit_score, outreach_log, meeting_queue

### 3. Backfill Agent Flow Test
- ✅ CSV Loader initialization
- ✅ Normalizer functionality:
  - Company name: `ACME CORPORATION, INC.` → `Acme`
  - Domain: `https://www.Acme.com/about` → `acme.com`
  - Name: `Mr. JOHN SMITH, Jr.` → `John Smith`
  - Email: `John.Smith@acme.com; jsmith@gmail.com` → `john.smith@acme.com`
  - Phone: `(555) 123-4567` → `+15551234567`
  - Title: `v.p. of hr operations` → `VP of HR Operations`
- ✅ Matcher initialization
- ✅ Baseline Generator:
  - BIT score calculation: (20 × 5) + (3 × 30) + (1 × 50) = 240 pts
  - Tier determination: 240 pts = hot tier

### 4. Talent Flow Agent Flow Test
- ✅ Diff Engine:
  - Hash computation (MD5)
  - Change detection
- ✅ Movement Classifier:
  - Promotion detection: "Sales Manager" → "VP Sales"
  - Movement type classification
  - Confidence scoring

### 5. BIT Scoring Agent Flow Test
- ✅ Score Calculator:
  - Raw score: 70 + 60 + 10 = 140 pts
  - Signal counting
  - Decay application
- ✅ Trigger Evaluator:
  - Tier change detection: engaged → hot
  - Action determination: sdr_escalate
  - Validation logic

### 6. Integration Validation Test
- ✅ Complete data flow simulation:
  1. Backfill imports John Smith (20 opens, 3 replies, 1 meeting)
  2. BIT baseline: 240 pts (hot tier)
  3. TF baseline: Snapshot saved
  4. [30 days pass]
  5. TF detects promotion: Sales Manager → VP Sales
  6. BIT signal generated: movement_promotion (weight: 70)
  7. BIT Scoring: 240 + 70 = 310 pts (burning tier)
  8. Trigger fires: auto_meeting
  9. Outreach log created
  10. Meeting queue: Priority URGENT

---

## Running Tests

### Prerequisites

1. **Database tables created**:
```bash
psql $NEON_DATABASE_URL -f ../talent-flow-agent/schema/create_talent_flow_tables.sql
psql $NEON_DATABASE_URL -f ../bit-scoring-agent/schema/create_bit_scoring_tables.sql
psql $NEON_DATABASE_URL -f ../backfill-agent/schema/create_backfill_tables.sql
```

2. **Environment variables set**:
```bash
export NEON_DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require"
```

3. **Dependencies installed**:
```bash
pip install asyncpg python-dotenv
```

### Run Tests

```bash
cd ctb/sys/test-e2e
python test_agent_flow.py
```

### Expected Output

```
================================================================================
🧪 END-TO-END AGENT FLOW TEST
================================================================================

📊 Test 1: Database Connectivity
   ✅ Database connected: 2024-11-20 10:30:00+00:00

📊 Test 2: Schema Validation
   ✅ Table exists: marketing.backfill_log
   ✅ Table exists: marketing.bit_baseline_snapshot
   ✅ Table exists: marketing.talent_flow_baseline
   [... all 17 tables ...]
   ✅ All required tables exist

📊 Test 3: Backfill Agent Flow
   Testing CSV Loader...
   ✅ CSV Loader initialized
   Testing Normalizer...
   ✅ Normalizer working correctly
   Testing Matcher...
   ✅ Matcher initialized
   Testing Baseline Generator...
   ✅ Baseline Generator working correctly (240 pts = hot tier)

📊 Test 4: Talent Flow Agent Flow
   Testing Diff Engine...
   ✅ Diff Engine working correctly (hash detection)
   Testing Movement Classifier...
   ✅ Movement Classifier working correctly (detected promotion)

📊 Test 5: BIT Scoring Agent Flow
   Testing Score Calculator...
   ✅ Score Calculator working correctly (140 pts)
   Testing Trigger Evaluator...
   ✅ Trigger Evaluator working correctly (sdr_escalate triggered)

📊 Test 6: Integration Validation
   Testing data flow:
   1. Backfill → BIT baseline (historical engagement)
   2. Backfill → TF baseline (snapshot)
   3. TF → BIT signal (movement detected)
   4. BIT Scoring → Score calculation
   5. BIT Scoring → Trigger evaluation
   6. Trigger → Outreach log

   Simulating complete flow:
   📥 Backfill imports: John Smith (20 opens, 3 replies, 1 meeting)
   📊 BIT baseline created: 240 pts (hot tier)
   📸 TF baseline snapshot: Sales Manager @ Acme Corp
   ⏱️  [30 days pass]
   🔄 TF detects movement: Sales Manager → VP Sales (promotion)
   📊 BIT signal generated: movement_promotion (weight: 70)
   🔢 BIT Scoring calculates: 240 + 70 = 310 pts (burning tier)
   🔔 Trigger fires: auto_meeting (tier: engaged → burning)
   📝 Outreach log created
   📅 Meeting queue: Priority URGENT

   ✅ Integration flow validated

================================================================================
📊 TEST SUMMARY
================================================================================
✅ BACKFILL: passed
   - db_connection: success
   - modules: all working
✅ TALENT_FLOW: passed
   - modules: all working
✅ BIT_SCORING: passed
   - modules: all working
✅ INTEGRATION: passed
   - schema_validation: success
   - flow: validated
================================================================================
🎉 ALL TESTS PASSED - System ready for deployment!
```

---

## Test Data

Sample CSV included: `sample_data.csv`

**5 test companies**:
1. ACME CORPORATION INC - High engagement (20 opens, 3 replies, 1 meeting)
2. TechCorp LLC - Medium engagement (15 opens, 2 replies, demo request)
3. Global Industries - Low engagement (5 opens, 1 reply)
4. Innovate Solutions - Very high engagement (30 opens, 5 replies, 2 meetings)
5. DataTech Group - Cold lead (10 opens, no replies)

**Expected Results**:
- ACME: 240 pts (hot tier) → nurture/sdr_escalate
- TechCorp: 130 pts (engaged tier) → nurture
- Global Industries: 55 pts (warm tier) → watch
- Innovate Solutions: 350 pts (burning tier) → auto_meeting
- DataTech: 50 pts (warm tier) → watch

---

## Manual Testing with Sample Data

### 1. Run Backfill with Sample Data

```bash
cd ctb/sys/backfill-agent
python agent_backfill.py ../test-e2e/sample_data.csv
```

**Expected**:
- 5 companies created
- 5 people created
- 5 BIT baselines created (scores: 240, 130, 55, 350, 50)
- 5 TF baselines created

### 2. Verify Baselines Created

```sql
-- Check BIT baselines
SELECT
    p.full_name,
    c.company_name,
    b.baseline_score,
    b.baseline_tier,
    b.historical_open_count,
    b.historical_reply_count,
    b.historical_meeting_count
FROM marketing.bit_baseline_snapshot b
JOIN marketing.people_master p ON b.person_unique_id = p.unique_id
JOIN marketing.company_master c ON b.company_unique_id = c.company_unique_id
ORDER BY b.baseline_score DESC;

-- Expected results:
-- Sarah Williams | Innovate Solutions | 350 | burning | 30 | 5 | 2
-- John Smith     | ACME CORPORATION   | 240 | hot     | 20 | 3 | 1
-- Jane Doe       | TechCorp           | 130 | engaged | 15 | 2 | 0
-- Robert Johnson | Global Industries  |  55 | warm    |  5 | 1 | 0
-- Michael Brown  | DataTech Group     |  50 | warm    | 10 | 0 | 0
```

### 3. Run BIT Scoring Agent

```bash
cd ctb/sys/bit-scoring-agent
python agent_bit_scoring.py
```

**Expected**:
- 5 unscored signals picked up
- 5 scores calculated
- 2-3 triggers fired (engaged, hot, burning tiers)

### 4. Verify Scores & Triggers

```sql
-- Check BIT scores
SELECT
    p.full_name,
    c.company_name,
    s.raw_score,
    s.decayed_score,
    s.score_tier,
    s.signal_count
FROM marketing.bit_score s
JOIN marketing.people_master p ON s.person_unique_id = p.unique_id
JOIN marketing.company_master c ON s.company_unique_id = c.company_unique_id
ORDER BY s.decayed_score DESC;

-- Check triggered actions
SELECT
    p.full_name,
    c.company_name,
    o.action_type,
    o.bit_score,
    o.score_tier,
    o.trigger_reason,
    o.created_at
FROM marketing.outreach_log o
JOIN marketing.people_master p ON o.person_unique_id = p.unique_id
JOIN marketing.company_master c ON o.company_unique_id = c.company_unique_id
ORDER BY o.created_at DESC;
```

### 5. Simulate Movement & Re-score

```sql
-- Update John Smith's title (simulate promotion)
UPDATE marketing.people_master
SET title = 'SVP Sales',
    updated_at = NOW()
WHERE full_name = 'John Smith';
```

```bash
# Run Talent Flow Agent
cd ctb/sys/talent-flow-agent
python agent_talent_flow.py
```

**Expected**:
- 1 movement detected (promotion)
- 1 BIT signal generated (movement_promotion, weight: 70)

```bash
# Run BIT Scoring Agent again
cd ctb/sys/bit-scoring-agent
python agent_bit_scoring.py
```

**Expected**:
- John Smith's score: 240 → 310 (hot → burning)
- Trigger fires: auto_meeting
- Meeting queue entry created

---

## Troubleshooting

### Tests Fail: Missing Tables

**Fix**: Run schema creation scripts:
```bash
psql $NEON_DATABASE_URL -f ../talent-flow-agent/schema/create_talent_flow_tables.sql
psql $NEON_DATABASE_URL -f ../bit-scoring-agent/schema/create_bit_scoring_tables.sql
psql $NEON_DATABASE_URL -f ../backfill-agent/schema/create_backfill_tables.sql
```

### Tests Fail: Module Import Errors

**Fix**: Ensure you're running from test-e2e directory:
```bash
cd ctb/sys/test-e2e
python test_agent_flow.py
```

### Tests Fail: Database Connection

**Fix**: Set NEON_DATABASE_URL:
```bash
export NEON_DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require"
```

---

## Success Criteria

✅ All 6 tests pass
✅ All 17 tables exist in database
✅ Normalization working correctly
✅ Matching logic functional
✅ Score calculation accurate
✅ Trigger evaluation correct
✅ Data flows between agents

🎉 **System ready for production deployment!**
