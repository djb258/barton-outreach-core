# Backfill & Historical State Agent

**Barton Doctrine ID**: `04.04.02.04.80000.001`
**CTB Layer**: System (Yellow - AI/SHQ nerve)
**Status**: ✅ READY FOR DEPLOYMENT

---

## 🎯 Mission

Import legacy outreach data (~700 companies), normalize it, match against existing records, and generate initial BIT and Talent Flow baselines without overwriting human-corrected data.

**No magic. Pure deterministic matching.**

---

## 📊 Architecture

```
config/                              ← EDIT THESE to fix logic (not code)
├── backfill_config.json             ← Matching rules, safety settings
└── normalization_rules.json         ← Data cleaning rules

core/                                ← Modular components (standalone)
├── neon_connector.py                ← All SQL queries live here
├── csv_loader.py                    ← CSV parsing & validation
├── normalizer.py                    ← Data cleaning & standardization
├── matcher.py                       ← Perfect & fuzzy matching logic
└── baseline_generator.py            ← BIT & TF baseline creation

agent_backfill.py                    ← Main orchestrator (ties modules together)
```

**Key Design Principle**: Configuration over code = easy corrections

---

## 🔄 How It Works

### Step-by-Step Flow

1. **Load CSV** (~700 companies, ~1,200-1,600 people)
   - Parse CSV with validation
   - Generate row hashes for deduplication
   - Report validation errors/warnings

2. **For Each Row**:
   - Normalize data (casing, domains, titles, emails)
   - Match company (perfect domain match → fuzzy name match)
   - Match person (perfect email/LinkedIn → fuzzy name match)
   - Insert new or update existing (respecting locked fields)

3. **Generate Baselines**:
   - **BIT Baseline**: Convert historical opens/replies/meetings → score
   - **Talent Flow Baseline**: Snapshot current state for future movement detection
   - Insert BIT signals for historical engagement

4. **Log Results**:
   - Log to `backfill_log` (match results, actions taken)
   - Unresolved matches → `garage.missing_parts`
   - All operations → `shq.audit_log`

---

## 🛡️ Safety Features (Kill Switches)

### ✅ No Overwriting Locked Fields
Checks `locked_fields[]` array and specific locked columns before updating.

**Config**: `matching.locked_fields`

**Locked Field List**:
- `locked_fields` (array)
- `manual_overrides`
- `manually_corrected_email`
- `manually_corrected_title`
- `manually_corrected_domain`
- `notes_internal`

### ✅ No Duplicate Entries
Perfect matching by domain/email/LinkedIn prevents duplicate companies and people.

**Config**: `safety.no_duplicate_entries = true`

### ✅ No Tier 3 Enrichment
Backfill does NOT call external enrichment APIs (Apify, Abacus, etc.).

**Config**: `safety.no_tier3_enrichment = true`

### ✅ Fuzzy Matches Require Confidence
All fuzzy matches include confidence scores. Low-confidence matches go to fallout bucket.

**Config**:
- `safety.min_confidence_for_auto_match = 0.90`
- `safety.fallout_bucket_threshold = 0.90`

---

## 📋 Input Format

### CSV Columns (Canonical)

| Column | Required | Description |
|--------|----------|-------------|
| company_name | ✅ | Company name |
| company_domain | | Domain (e.g., acme.com) |
| company_website | | Website URL |
| full_name | ✅ | Person full name |
| first_name | | First name (auto-split if missing) |
| last_name | | Last name (auto-split if missing) |
| title | | Job title |
| email | | Email address |
| phone | | Phone number |
| linkedin_url | | LinkedIn profile URL |
| historical_open_count | | Email opens (count) |
| historical_reply_count | | Email replies (count) |
| historical_meeting_count | | Meetings (count) |
| last_engaged_at | | Last engagement date |
| notes | | Additional notes |

**Known Data Quality Issues** (automatically handled):
- Mixed casing
- Inconsistent domains
- Titles not standardized (VP HR, HR VP, HR Lead)
- Multiple emails per person in one cell
- Hybrid personal + work emails
- Missing last names
- Company name variants (Inc, LLC, Group)
- Blank `last_engaged_at`

---

## 🎯 Matching Rules

### Perfect Match Rules (100% confidence)

**Company**:
- Domain exact match → `company.com` = `company.com`

**Person**:
- LinkedIn URL exact match (strongest signal)
- Email exact match
- Email domain + first/last name exact match

### Fuzzy Match Thresholds

| Match Type | Threshold | Description |
|------------|-----------|-------------|
| Company name | ≥ 0.90 | Safe auto-match |
| Person name | ≥ 0.88 | + same company domain |
| Title | N/A | Support signal only, never primary |

**Algorithm**: Levenshtein-like (SequenceMatcher)

**Examples**:
- "Acme Corporation" vs "Acme Corp" → 0.92 confidence ✅
- "John Smith" vs "Jon Smith" → 0.95 confidence ✅
- "Acme Inc" vs "ABC Inc" → 0.45 confidence ❌ (fallout bucket)

---

## 📊 Normalization Rules

### Company Name
- Remove suffixes: Inc, LLC, Ltd, Corp, Corporation, Company, Group
- Title case
- Dedupe spaces

**Example**: `ACME CORPORATION, INC.` → `Acme`

### Company Domain
- Extract from email if missing
- Extract from website if missing
- Lowercase
- Remove `www.`, protocols, paths

**Example**: `https://www.Acme.com/about` → `acme.com`

### Person Name
- Title case
- Remove prefixes: Mr., Mrs., Ms., Dr., Prof.
- Remove suffixes: Jr., Sr., III, IV
- Split full name if first/last missing

**Example**: `Mr. JOHN SMITH, Jr.` → `John Smith` (first: `John`, last: `Smith`)

### Title
- Standardize abbreviations:
  - `V.P.`, `Vice President`, `VP of` → `VP`
  - `Chief Executive Officer`, `C.E.O.` → `CEO`
  - `Dir.`, `Dir of` → `Director`
- Title case

**Example**: `v.p. of hr operations` → `VP of HR Operations`

### Email
- Lowercase
- Split multiple emails (`,`, `;`, `|`)
- Prefer work email over personal (gmail, yahoo, etc.)
- Validate format

**Example**: `John.Smith@acme.com; jsmith@gmail.com` → `john.smith@acme.com`

### Phone
- Remove non-digits
- Add +1 country code for 10-digit numbers
- Validate length (10-15 digits)

**Example**: `(555) 123-4567` → `+15551234567`

---

## 🎚️ Baseline Generation

### BIT Baseline Formula

```
Baseline Score = (opens × 5) + (replies × 30) + (meetings × 50)
```

**Example**:
- 20 opens, 3 replies, 1 meeting
- Score = (20 × 5) + (3 × 30) + (1 × 50) = **240 points**
- Tier = **hot** (200-299 range)

**Signal Weights**:
- `historical_open`: 5 points each
- `historical_reply`: 30 points each
- `historical_meeting`: 50 points each

**BIT Signals Generated**:
- Creates aggregated signals in `bit_signal` table
- Marked as `scored = FALSE` for BIT Scoring Agent to process
- Source type: `backfill_baseline`

### Talent Flow Baseline

- Computes MD5 hash of current state (name, title, company, LinkedIn)
- Saves snapshot to `talent_flow_baseline` table
- Used by Talent Flow Agent for future movement detection

**Purpose**: Establish "starting point" so monthly sweeps can detect changes.

---

## 🗄️ Database Schema

### backfill_log
Audit trail for all backfill operations.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| source_row_hash | TEXT | MD5 hash of CSV row |
| source_data | JSONB | Original CSV data |
| match_type | TEXT | perfect/fuzzy/no_match |
| match_confidence | NUMERIC(5,3) | 0.0 - 1.0 |
| matched_company_id | TEXT | Matched company ID |
| matched_person_id | TEXT | Matched person ID |
| resolution_status | TEXT | initialized/unresolved/duplicate/error/skipped_locked |
| actions_taken | JSONB | Actions performed |
| error_message | TEXT | Error details (if any) |
| notes | TEXT | Additional notes |
| created_at | TIMESTAMPTZ | Creation timestamp |
| worker_id | TEXT | Worker ID |
| process_id | TEXT | Process ID |

### backfill_staging (Optional)
Temporary holding table for pre-normalization rows.

### bit_baseline_snapshot
Initial BIT state from historical engagement data.

| Column | Type | Description |
|--------|------|-------------|
| baseline_id | BIGSERIAL | Primary key |
| person_unique_id | TEXT | FK to people_master |
| company_unique_id | TEXT | FK to company_master |
| historical_open_count | INTEGER | Opens count |
| historical_reply_count | INTEGER | Replies count |
| historical_meeting_count | INTEGER | Meetings count |
| last_engaged_at | TIMESTAMPTZ | Last engagement date |
| baseline_score | INTEGER | Computed BIT score |
| baseline_tier | TEXT | Tier (cold/warm/engaged/hot/burning) |
| signals_generated | INTEGER | # of BIT signals created |
| created_at | TIMESTAMPTZ | Creation timestamp |
| source | TEXT | backfill_agent |
| metadata | JSONB | Additional details |

### talent_flow_baseline
Initial Talent Flow snapshot.

| Column | Type | Description |
|--------|------|-------------|
| baseline_id | BIGSERIAL | Primary key |
| person_unique_id | TEXT | FK to people_master (unique) |
| enrichment_hash | TEXT | MD5 hash for change detection |
| snapshot_data | JSONB | Complete person record |
| baseline_date | DATE | Snapshot date |
| source | TEXT | backfill_agent |
| created_at | TIMESTAMPTZ | Creation timestamp |
| metadata | JSONB | Additional details |

### garage.missing_parts
Unresolved matches and low-confidence fallout.

| Column | Type | Description |
|--------|------|-------------|
| missing_id | BIGSERIAL | Primary key |
| source | TEXT | backfill_agent |
| issue_type | TEXT | low_confidence_match, etc. |
| source_data | JSONB | Original CSV data |
| match_attempts | JSONB | Match attempt details |
| confidence_score | NUMERIC(5,3) | Highest confidence achieved |
| resolved | BOOLEAN | Resolution status |
| resolved_at | TIMESTAMPTZ | Resolution timestamp |
| created_at | TIMESTAMPTZ | Creation timestamp |

---

## 🚀 Usage

### 1. Install Dependencies

```bash
cd ctb/sys/backfill-agent
pip install -r requirements.txt
```

### 2. Create Database Tables

```bash
psql $NEON_DATABASE_URL -f schema/create_backfill_tables.sql
```

### 3. Configure Environment

```bash
# Add to .env
NEON_DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

### 4. Prepare CSV File

Ensure CSV has required columns:
- `company_name`
- `full_name`

Optional but recommended:
- `company_domain`
- `email`
- `linkedin_url`
- `historical_open_count`
- `historical_reply_count`
- `historical_meeting_count`

### 5. Run Agent

```bash
python agent_backfill.py /path/to/legacy_data.csv
```

**Expected Output**:
```
🚀 Backfill Agent Starting
   Worker ID: backfill-abc12345
   Process ID: PRC-BF-20251119143000
   CSV Path: /path/to/legacy_data.csv

✅ Connected to Neon database
📥 Loading CSV...
✅ Loaded 1,500 rows
   Valid: 1,450, Errors: 20, Warnings: 30

📊 Loading existing companies...
✅ Loaded 500 existing companies

⚙️  Processing rows...
   ➕ Created company: Acme Corp (ID: 04.04.02.04.30000.701)
   ➕ Created person: John Smith at Acme Corp
   📊 BIT baseline: 240 pts (hot)
   📸 TF baseline: Snapshot created

   ✓ Company: Perfect match | ✓ Person: Fuzzy match (0.95)
   🔄 Updated person: Jane Doe (fields: title, phone)
   📊 BIT baseline: 150 pts (engaged)

...

📊 BACKFILL AGENT - EXECUTION SUMMARY
Rows Loaded: 1,500
Rows Processed: 1,500

Companies:
  - Matched: 450
  - Created: 250

People:
  - Matched: 800
  - Created: 600
  - Updated: 100

Baselines:
  - BIT Baselines: 1,200
  - TF Baselines: 1,400

Issues:
  - Unresolved: 50
  - Locked Field Skips: 10
  - Errors: 20
```

---

## 🔧 Troubleshooting

### Low Match Rate

**Check**:
1. Are domains normalized? Check `company_domain` column
2. Are emails present? Email is strongest person match signal
3. Are fuzzy thresholds too strict? Lower to 0.85-0.88

**Fix**: Edit `config/backfill_config.json` matching thresholds

### Too Many Unresolved Matches

**Check**:
1. Query `garage.missing_parts` for low-confidence matches
2. Review `match_attempts` JSONB field for details
3. Are company names too variant? ("Acme Corp" vs "ABC Company")

**Fix**: Manually resolve in database, add to `company_master`

### Locked Field Warnings

**Check**:
1. Query `marketing.people_master` for `locked_fields` column
2. Which fields are locked? Email? Title?
3. Is this expected (human corrections)?

**Fix**: This is intentional behavior. Locked fields are preserved.

### BIT Baselines Not Created

**Check**:
1. Does CSV have `historical_open_count`, `historical_reply_count`, or `historical_meeting_count`?
2. Are all counts = 0? (No engagement history)

**Fix**: Add historical engagement data to CSV

---

## 📊 Cost Estimate

**One-Time Execution**:
- 700 companies × ~2 people/company = 1,400 people
- 1,400 rows processed
- Processing time: ~10-15 minutes
- Database queries: ~8,400 queries (6 per person: select, match, insert/update, baselines)
- **Cost**: Negligible (Neon free tier supports this easily)

**No Recurring Cost**: Backfill is one-time operation.

---

## 🎯 Integration with Other Agents

**Data Flow**:
```
Backfill Agent runs ONCE
    ↓
Creates initial records in company_master & people_master
    ↓
Generates BIT baselines → bit_baseline_snapshot + bit_signal (unscored)
    ↓
Generates TF baselines → talent_flow_baseline
    ↓
BIT Scoring Agent picks up unscored signals → calculates scores
    ↓
Talent Flow Agent detects future movements from baseline snapshots
```

**Example**:
1. Backfill imports "John Smith" with 3 historical replies (90 points)
2. BIT baseline created: 90 points (warm tier)
3. TF baseline snapshot saved with current title: "Sales Manager"
4. **Next month**: Talent Flow detects title changed to "VP Sales" → generates movement signal (promotion)
5. BIT Scoring adds 70 points (promotion weight) → total now 160 (engaged tier)
6. Trigger fires: nurture campaign

---

## 🎯 Next Steps

1. ✅ **Deploy Backfill Agent** (DONE)
2. 🔜 **Run backfill once** with production CSV
3. 🔜 **Review `garage.missing_parts`** for unresolved matches
4. 🔜 **Verify baselines created** (query `bit_baseline_snapshot`, `talent_flow_baseline`)
5. 🔜 **Test end-to-end** (backfill → BIT scoring → movement detection → trigger)

---

**Backfill Agent is THE FOUNDATION for the entire outreach system.**
**Without backfill → no historical state → no movement detection → no intelligent scoring.**
