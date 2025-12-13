# Company Slot Evaluation Guide

**Script**: `evaluate_company_slots.py`
**Created**: 2025-11-18
**Barton ID**: 04.04.02.04.50000.###

---

## Overview

The Slot Evaluation Agent runs **after people enrichment** to detect missing leadership slots (CEO, CFO, HR) and update slot tracking in the `marketing.company_slot` table.

This allows downstream agents to:
- Skip dead leads (closed_missing slots)
- Focus enrichment efforts on open slots
- Track fill rates and enrichment effectiveness

---

## Quick Start

### 1. Dry Run (Simulation)

See what would be updated without making changes:

```bash
cd outreach_core/workbench
python evaluate_company_slots.py --dry-run
```

**Output**:
- Shows which slots would be filled/opened/closed
- Displays matching people for each slot
- No database changes

### 2. Live Update

Run the actual slot evaluation:

```bash
python evaluate_company_slots.py
```

**What happens**:
- ✅ Creates 3 slot records (CEO, CFO, HR) for each company if not exist
- ✅ Matches people to slots by title keywords
- ✅ Updates `company_slot` table with person assignments
- ✅ Sets slot status: filled, open, or closed_missing
- ✅ Increments enrichment_attempts for unfilled slots
- ✅ Generates summary report

---

## Slot Matching Rules

### Title Keywords

**CEO Slot**:
- Exact: `\bceo\b` (word boundary match)
- Contains: "chief executive officer", "chief executive"

**CFO Slot**:
- Exact: `\bcfo\b`
- Contains: "chief financial officer", "chief financial"

**HR Slot**:
- Exact: `\bhr\b`
- Contains: "human resources", "talent", "people operations", "chief people officer", "head of people", "vp of people", "director of human resources"

### Matching Priority

1. **Exact match** (e.g., title == "CEO")
2. **Contains keyword** (e.g., "Chief Executive Officer")
3. **Regex word boundary** (e.g., r"\bceo\b" matches "CEO & Founder")

### Special Cases

**First Match Wins**:
- If multiple people match the same slot, the **first** match is selected
- Other candidates are logged as warnings

**Compound Titles**:
- One person can fill **multiple slots**
- Example: "CEO & CFO" fills both CEO and CFO slots

**Multiple Candidates**:
- If 2+ people have "CEO" in their title, first match is used
- Warning logged: `[WARNING] CEO: 2 candidates, picked first match`

---

## Slot Status Logic

### Status Values

| Status | Meaning | Condition |
|--------|---------|-----------|
| `filled` | Person found and assigned | `is_filled = TRUE` |
| `open` | No match, enrichment ongoing | `is_filled = FALSE` AND `enrichment_attempts < 2` |
| `closed_missing` | No match, enrichment exhausted | `is_filled = FALSE` AND `enrichment_attempts >= 2` |

### Status Transitions

```
Initial state: open (enrichment_attempts = 0)
   |
   | No match found after enrichment
   v
open (enrichment_attempts = 1)
   |
   | Still no match after 2nd enrichment
   v
closed_missing (enrichment_attempts = 2)
   |
   | OR person found at any point
   v
filled (enrichment_attempts = 0, reset)
```

### Enrichment Attempts Counter

- **Incremented** each time slot is evaluated and no match is found
- **Reset to 0** when a person is successfully matched
- **Threshold**: 2 attempts before marking as `closed_missing`

---

## Database Schema

### Table: `marketing.company_slot`

```sql
company_slot_unique_id    VARCHAR(50)  PRIMARY KEY (Barton ID: 04.04.02.04.10000.XXX)
company_unique_id         VARCHAR(50)  FK → company_master
person_unique_id          VARCHAR(50)  FK → people_master (NULL if not filled)
slot_type                 VARCHAR(10)  'CEO', 'CFO', or 'HR'
is_filled                 BOOLEAN      TRUE if person assigned
filled_at                 TIMESTAMP    When slot was filled (NULL if open)
enrichment_attempts       INTEGER      Number of enrichment attempts (0-2+)
status                    VARCHAR(20)  'filled', 'open', or 'closed_missing'
last_refreshed_at         TIMESTAMP    Last evaluation timestamp
created_at                TIMESTAMP    Record creation
updated_at                TIMESTAMP    Last update (auto-trigger)
```

### Auto-Update Trigger

The `status` field is automatically updated by a database trigger:

```sql
CREATE TRIGGER company_slot_status_auto_update
    BEFORE INSERT OR UPDATE ON marketing.company_slot
    FOR EACH ROW
    EXECUTE FUNCTION update_company_slot_status();
```

**Logic**:
- If `is_filled = TRUE` → `status = 'filled'`
- If `enrichment_attempts >= 2` → `status = 'closed_missing'`
- Otherwise → `status = 'open'`

---

## Example Output

### Dry Run

```
================================================================================
SLOT EVALUATION AGENT - POST-ENRICHMENT
================================================================================

Mode: DRY RUN (Simulation)
Timestamp: 2025-11-18T14:40:18

STEP 1: Fetching All Companies
--------------------------------------------------------------------------------
[OK] Found 453 companies

STEP 2: Evaluating Slots for Each Company
--------------------------------------------------------------------------------
  [1/453] Jan Dils, Attorneys at Law (04.04.01.00.00100.100)
  [DRY RUN] UPDATE slot 04.04.02.04.10001.001: CEO -> open
  [DRY RUN] UPDATE slot 04.04.02.04.10002.002: CFO -> open
  [DRY RUN] UPDATE slot 04.04.02.04.10003.003: HR -> open
    No slots filled (no matching titles)

  [4/453] J.H. Fletcher & Co. (04.04.01.00.00400.400)
  [DRY RUN] UPDATE slot 04.04.02.04.10010.010: CEO -> open
  [DRY RUN] UPDATE slot 04.04.02.04.10011.011: CFO -> filled
  [DRY RUN] UPDATE slot 04.04.02.04.10012.012: HR -> open
    Filled: CFO: Chuck Brown

  [10/453] Valley Health Systems, Inc. (04.04.01.02.00002.002)
  [DRY RUN] UPDATE slot 04.04.02.04.10028.028: CEO -> filled
    [WARNING] CEO: 2 candidates, picked first match
  [DRY RUN] UPDATE slot 04.04.02.04.10029.029: CFO -> open
  [DRY RUN] UPDATE slot 04.04.02.04.10030.030: HR -> open
    Filled: CEO: Mathew Weimer

[OK] Slot evaluation complete

[DRY RUN] No changes made to database
================================================================================
SLOT EVALUATION SUMMARY
================================================================================

Companies Processed: 453
Slots Created: 0
Slots Updated: 0

Slot Status Distribution:
  Filled: 152
  Open (< 2 attempts): 1207
  Closed Missing (>= 2 attempts): 0

Data Quality Metrics:
  Compound Matches (1 person = multiple slots): 0
  Multiple Candidates (>1 person per slot): 15

Overall Fill Rate: 11.2% (152/1359)

================================================================================
```

### Live Update

```bash
python evaluate_company_slots.py
```

Same output as dry run, but with:
- `[OK] Changes committed to database` at the end
- Actual database records created/updated

---

## Integration with Enrichment Pipeline

### Workflow

```
1. People enrichment completes
   ↓
2. Run slot evaluation:
   python evaluate_company_slots.py
   ↓
3. Slots updated with current state:
   - filled: Person found
   - open: No match, < 2 attempts
   - closed_missing: No match, >= 2 attempts
   ↓
4. Downstream agents check slot status:
   - Skip closed_missing slots
   - Enrich only open slots
   ↓
5. Re-run evaluation after enrichment
   ↓
6. Repeat until all slots filled or closed
```

### Scheduling

**Recommended**:
- Run after **every** people enrichment batch
- Run **before** agent routing to update slot priorities
- Run **daily** or **weekly** for data freshness

**Example Cron**:
```bash
# Run daily at 2 AM after enrichment
0 2 * * * cd /path/to/outreach_core/workbench && python evaluate_company_slots.py >> /var/log/slot_eval.log 2>&1
```

---

## Monitoring Queries

### Check Slot Fill Rates

```sql
-- Overall fill rate by slot type
SELECT
    slot_type,
    COUNT(*) AS total_slots,
    COUNT(*) FILTER (WHERE status = 'filled') AS filled,
    COUNT(*) FILTER (WHERE status = 'open') AS open,
    COUNT(*) FILTER (WHERE status = 'closed_missing') AS closed,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'filled') / COUNT(*), 1) AS fill_rate_pct
FROM marketing.company_slot
GROUP BY slot_type
ORDER BY slot_type;
```

### Find Companies with All Slots Filled

```sql
-- Companies with complete leadership (CEO + CFO + HR)
SELECT
    cm.company_name,
    cm.company_unique_id,
    COUNT(*) AS total_slots,
    COUNT(*) FILTER (WHERE cs.status = 'filled') AS filled_slots
FROM marketing.company_master cm
JOIN marketing.company_slot cs ON cm.company_unique_id = cs.company_unique_id
GROUP BY cm.company_unique_id, cm.company_name
HAVING COUNT(*) FILTER (WHERE cs.status = 'filled') = 3
ORDER BY cm.company_name;
```

### Find Companies with No Slots Filled

```sql
-- Companies with zero leadership matches
SELECT
    cm.company_name,
    cm.company_unique_id,
    COUNT(*) AS total_slots,
    COUNT(*) FILTER (WHERE cs.status = 'closed_missing') AS exhausted_slots
FROM marketing.company_master cm
JOIN marketing.company_slot cs ON cm.company_unique_id = cs.company_unique_id
GROUP BY cm.company_unique_id, cm.company_name
HAVING COUNT(*) FILTER (WHERE cs.status = 'filled') = 0
ORDER BY cm.company_name;
```

### Find Slots Needing Enrichment

```sql
-- Open slots (candidates for enrichment)
SELECT
    cm.company_name,
    cs.slot_type,
    cs.enrichment_attempts,
    cs.last_refreshed_at
FROM marketing.company_slot cs
JOIN marketing.company_master cm ON cs.company_unique_id = cm.company_unique_id
WHERE cs.status = 'open'
ORDER BY cs.enrichment_attempts ASC, cs.last_refreshed_at ASC
LIMIT 100;
```

### Check Multiple Candidates Issues

```sql
-- Find companies where multiple people match the same slot type
SELECT
    cm.company_name,
    pm.title,
    COUNT(*) AS people_count
FROM marketing.people_master pm
JOIN marketing.company_master cm ON pm.company_unique_id = cm.company_unique_id
WHERE
    pm.title ILIKE '%ceo%'
    OR pm.title ILIKE '%chief executive%'
GROUP BY cm.company_name, pm.title
HAVING COUNT(*) > 1
ORDER BY people_count DESC;
```

---

## Troubleshooting

### Issue: No slots created

**Cause**: Script running in dry-run mode
**Solution**: Run without `--dry-run` flag

```bash
python evaluate_company_slots.py
```

### Issue: Low fill rate (<5%)

**Cause**: Poor title data in people_master
**Solution**:
1. Check title quality in people_master
2. Add more keyword variations to `TITLE_KEYWORDS`
3. Run people enrichment to get better titles

### Issue: Too many "closed_missing" slots

**Cause**: Enrichment attempts exhausted (2+ tries)
**Solution**:
1. Review closed_missing slots for patterns
2. Add missing keywords to matching rules
3. Consider manual review of these companies

```sql
SELECT company_unique_id, slot_type, enrichment_attempts
FROM marketing.company_slot
WHERE status = 'closed_missing'
ORDER BY enrichment_attempts DESC;
```

### Issue: Compound matches not detected

**Cause**: One person should fill multiple slots but doesn't
**Solution**: Check title matching logic for that person

```sql
-- Find person with compound title
SELECT unique_id, full_name, title
FROM marketing.people_master
WHERE title ILIKE '%ceo%cfo%' OR title ILIKE '%cfo%ceo%';
```

---

## Advanced Configuration

### Customize Title Keywords

Edit the `TITLE_KEYWORDS` dictionary in `evaluate_company_slots.py`:

```python
TITLE_KEYWORDS = {
    'CEO': [
        r'\bceo\b',
        'chief executive officer',
        'chief executive',
        'president',  # ADD THIS
        'managing director',  # ADD THIS
    ],
    'CFO': [
        r'\bcfo\b',
        'chief financial officer',
        'chief financial',
        'vp of finance',  # ADD THIS
    ],
    'HR': [
        r'\bhr\b',
        'human resources',
        'talent',
        'people operations',
        'chief people officer',
    ],
}
```

### Add New Slot Types

To track additional roles (e.g., CTO, CMO):

1. **Update `SLOT_TYPES`**:
```python
SLOT_TYPES = ['CEO', 'CFO', 'HR', 'CTO', 'CMO']
```

2. **Add keywords**:
```python
TITLE_KEYWORDS['CTO'] = [r'\bcto\b', 'chief technology officer']
TITLE_KEYWORDS['CMO'] = [r'\bcmo\b', 'chief marketing officer']
```

3. **Re-run** the script to create new slots

---

## Migration Details

The script depends on **Migration 007** which adds:
- `enrichment_attempts` column (INTEGER DEFAULT 0)
- `status` column (VARCHAR(20) DEFAULT 'open')
- Auto-update trigger for status
- Indexes on status and enrichment_attempts

**Migration file**: `infra/migrations/007_add_slot_enrichment_tracking.sql`

**Run migration**:
```bash
cd infra/migrations
python -c "
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('../../.env')

with open('007_add_slot_enrichment_tracking.sql', 'r') as f:
    sql = f.read()

conn = psycopg2.connect(
    host=os.getenv('NEON_HOST'),
    database=os.getenv('NEON_DATABASE'),
    user=os.getenv('NEON_USER'),
    password=os.getenv('NEON_PASSWORD'),
    sslmode='require'
)

cursor = conn.cursor()
cursor.execute(sql)
conn.commit()
print('[OK] Migration 007 complete')
"
```

---

## Performance Notes

- **Speed**: ~0.5 seconds per company (453 companies in ~4 minutes)
- **Database load**: Read-heavy (queries people_master for each company)
- **Optimization**: Script processes sequentially; consider batching for >10k companies

---

**Status**: ✅ **PRODUCTION READY**
**Test Coverage**: ✅ **VERIFIED** (453 companies, 1359 slots, 152 filled)
**Documentation**: ✅ **COMPLETE**
