# Slot Mapping Complete Guide

**Purpose**: Map people to company executive slots (CEO, CFO, HR) using title pattern matching

**Last Updated**: 2025-11-07
**Status**: Production Ready - Tested on 453 companies, 170 people

---

## Overview

This system maps people from `people_master` to executive slots in `company_slot` table based on their job titles.

### Architecture

```
company_master (453 companies)
    ↓
company_slot (1,359 slots: 3 per company)
    ↓
people_master (170 people) → Pattern Matching → Fill Slots
                                    ↓
                            Handle Duplicates
```

### Current Results

- **154 people mapped** (90.6% of 170)
- **75 CEO slots filled** (16.6% of companies)
- **66 CFO slots filled** (14.6% of companies)
- **13 HR slots filled** (2.9% of companies)
- **16 duplicates resolved** automatically

---

## Scripts & Files

### Core Scripts

1. **`create_company_slot.sql`** - Creates slot table
   - Location: `ctb/data/validation-framework/sql/`
   - Creates 3 slots (CEO, CFO, HR) per company
   - Barton ID format: `04.04.02.04.10000.XXX`

2. **`map_people_to_slots.py`** - Main mapping engine
   - Location: `ctb/data/validation-framework/scripts/python/`
   - Pattern matching for CEO/CFO/HR titles
   - Duplicate resolution (picks highest confidence)
   - Supports dry-run mode

3. **`move_unmapped_to_invalid.py`** - Moves unmapped people
   - Identifies people who don't match patterns
   - Moves to `people_invalid` for manual review

### Usage

```bash
# Create slots (only needed once per company batch)
python -c "exec(open('scripts/python/map_people_to_slots.py').read())"

# Map people to slots (re-run after adding new people)
cd ctb/data/validation-framework/scripts/python
python map_people_to_slots.py

# Dry run first
python map_people_to_slots.py --dry-run

# Skip slot creation if slots already exist
python map_people_to_slots.py --skip-create

# Move unmapped to invalid
python move_unmapped_to_invalid.py
```

---

## Title Patterns (Current)

### CEO Patterns (Confidence: 1.0 → 0.5)

```python
patterns = [
    r'\bCEO\b',                           # 1.0 confidence
    r'\bChief Executive Officer\b',       # 0.9
    r'\bChief Executive\b',               # 0.8
    r'\bPresident\s*[/&,]?\s*CEO\b',      # 0.7
    r'\bCEO\s*[/&,]?\s*President\b',      # 0.6
    r'\bCo-?Founder\s*[/&,]?\s*CEO\b',    # 0.5
    r'\bCEO\s*[/&,]?\s*Co-?Founder\b',
    r'\bFounder\s*[/&,]?\s*President\b',
    r'\bPresident\s*[/&,]?\s*Founder\b',
    r'\bExecutive Director\b',
    r'\bManaging Director\b',
]
```

### CFO Patterns

```python
patterns = [
    r'\bCFO\b',                                      # 1.0
    r'\bChief Financial Officer\b',                  # 0.9
    r'\bChief.*Financial\b',                         # 0.8
    r'\bVice President\s*[/&,]?\s*CFO\b',           # 0.7
    r'\bVP\s*[,]?\s*Finance\b',                     # 0.6
    r'\bVice President.*Financial\b',               # 0.5
    r'\bVP.*CFO\b',
    r'\bController\b',
    r'\bTreasurer\b',
    r'\bChief School Business Official\b',  # Education sector
]
```

### HR Patterns

```python
patterns = [
    r'\bCHRO\b',                                   # 1.0
    r'\bChief Human Resources Officer\b',          # 0.9
    r'\bVP\s*[,]?\s*Human Resources\b',           # 0.8
    r'\bVice President.*Human Resources\b',        # 0.7
    r'\bHR\s+Director\b',                         # 0.6
    r'\bHuman Resources Director\b',              # 0.5
    r'\bHR\s+Manager\b',
    r'\bHuman Resources Manager\b',
    r'\bHuman Resources.*Manager\b',      # Catches "HR Payroll Manager"
    r'\bHuman Resources.*Coordinator\b',  # Catches "HR Benefits Coordinator"
    r'\bHuman Resources.*Specialist\b',   # Catches "Senior HR Specialist"
    r'\bBenefits.*Manager\b',             # "VP & Benefits Manager"
    r'\bPeople\s+Officer\b',
]
```

---

## Duplicate Resolution Logic

When multiple people match same slot at same company:

### Current Algorithm

```python
1. Group all candidates by (company_id, slot_type)
2. For each group with >1 person:
   - Sort by confidence score (highest first)
   - Pick the person with highest confidence
   - Log skipped candidates
3. If tied confidence:
   - First person alphabetically wins (deterministic)
```

### Examples

| Company | Slot | Candidates | Winner | Reason |
|---------|------|------------|--------|--------|
| Eastridge Health | CFO | Gary White (0.90)<br>Walt Dewalt (0.90)<br>Kathleen Salmons (0.90) | Gary White | Tied confidence, first alphabetically |
| Bayer Heritage | CFO | James Coulter (1.00)<br>Ryan Rotilio (0.90) | James Coulter | Higher confidence (1.00 > 0.90) |
| Oktana | CEO | Adrian (1.00)<br>Jaime (1.00) | Adrian Armijos Kruger | Tied, first alphabetically |

---

## Database Schema

### company_slot Table

```sql
CREATE TABLE marketing.company_slot (
    company_slot_unique_id TEXT PRIMARY KEY,  -- 04.04.02.04.10000.XXX
    company_unique_id TEXT NOT NULL,          -- FK to company_master
    person_unique_id TEXT,                    -- FK to people_master (nullable)
    slot_type TEXT NOT NULL,                  -- CEO, CFO, or HR
    is_filled BOOLEAN DEFAULT FALSE,
    confidence_score DECIMAL(3,2),            -- 0.00-1.00
    created_at TIMESTAMP WITH TIME ZONE,
    filled_at TIMESTAMP WITH TIME ZONE,
    last_refreshed_at TIMESTAMP WITH TIME ZONE,
    filled_by TEXT,                           -- 'slot_mapper_v2'
    source_system TEXT,                       -- 'slot_mapper'

    CONSTRAINT unique_company_slot UNIQUE (company_unique_id, slot_type)
);
```

### Key Indexes

```sql
idx_company_slot_company     -- On company_unique_id
idx_company_slot_person      -- On person_unique_id
idx_company_slot_type        -- On slot_type
idx_company_slot_filled      -- On is_filled
idx_company_slot_unfilled    -- On (company_unique_id, slot_type) WHERE is_filled = FALSE
```

---

## Verification Queries

### Check Mapping Results

```sql
-- Slots filled by type
SELECT
    slot_type,
    COUNT(*) as total,
    COUNT(person_unique_id) as filled,
    COUNT(*) - COUNT(person_unique_id) as unfilled,
    ROUND(100.0 * COUNT(person_unique_id) / COUNT(*), 1) as fill_rate
FROM marketing.company_slot
GROUP BY slot_type
ORDER BY slot_type;

-- Companies with all 3 slots filled
SELECT
    cm.company_unique_id,
    cm.company_name,
    COUNT(cs.person_unique_id) as filled_slots
FROM marketing.company_master cm
JOIN marketing.company_slot cs ON cm.company_unique_id = cs.company_unique_id
WHERE cs.is_filled = TRUE
GROUP BY cm.company_unique_id, cm.company_name
HAVING COUNT(cs.person_unique_id) = 3
ORDER BY cm.company_name;

-- Unmapped people (have title but no slot)
SELECT
    pm.unique_id,
    pm.full_name,
    pm.title,
    cm.company_name
FROM marketing.people_master pm
JOIN marketing.company_master cm ON pm.company_unique_id = cm.company_unique_id
WHERE pm.unique_id NOT IN (
    SELECT person_unique_id FROM marketing.company_slot WHERE is_filled = TRUE
)
AND pm.title IS NOT NULL
ORDER BY pm.title;
```

### Data Quality Checks

```sql
-- Companies with duplicate executives in slots (should be 0)
SELECT
    company_unique_id,
    slot_type,
    COUNT(*) as duplicate_count
FROM marketing.company_slot
WHERE is_filled = TRUE
GROUP BY company_unique_id, slot_type
HAVING COUNT(*) > 1;

-- People mapped to multiple slots (should be 0)
SELECT
    person_unique_id,
    COUNT(*) as slot_count
FROM marketing.company_slot
WHERE is_filled = TRUE
GROUP BY person_unique_id
HAVING COUNT(*) > 1;

-- Slots with invalid confidence scores
SELECT *
FROM marketing.company_slot
WHERE is_filled = TRUE
AND (confidence_score IS NULL OR confidence_score < 0 OR confidence_score > 1);
```

---

## Common Issues & Solutions

### Issue 1: Pattern Doesn't Match Expected Titles

**Symptoms**: People with "VP Finance" title not filling CFO slot

**Solution**: Add pattern to `cfo_patterns` list in `map_people_to_slots.py`:
```python
self.cfo_patterns = [
    # ... existing patterns
    r'\bVP\s+Finance\b',  # Add this
]
```

### Issue 2: Multiple People at Same Company, Same Role

**Symptoms**: 2 CEOs at same company, one gets skipped

**Solutions**:
1. **Accept it**: Current logic picks highest confidence, logs the skipped one
2. **Manual review**: Check `people_invalid` table for duplicates
3. **Expand slots**: Allow 2 people per slot type (requires schema change)

### Issue 3: Low HR Fill Rate (2.9%)

**Root Cause**: Not enough HR executives in data (only 170 people total, HR is rarest)

**Solutions**:
1. Lower HR pattern threshold (accept "HR Coordinator" not just "HR Director")
2. Enrich companies to find HR contacts
3. Accept that most companies won't have HR exec in database

### Issue 4: Slow Performance at Scale

**Symptoms**: Script takes >10 minutes for 10k+ people

**Optimizations**:
1. Batch processing (1,000 companies at a time)
2. Pre-filter people by title (skip those with NULL title)
3. Use database-side pattern matching (PostgreSQL regex)
4. Index on people_master.title column

---

## Extending the System

### Adding New Slot Types

To add CTO, COO, etc.:

1. Update `company_slot` table constraint:
```sql
ALTER TABLE marketing.company_slot
DROP CONSTRAINT company_slot_slot_type_check;

ALTER TABLE marketing.company_slot
ADD CONSTRAINT company_slot_slot_type_check
CHECK (slot_type IN ('CEO', 'CFO', 'HR', 'CTO', 'COO'));
```

2. Add patterns in `map_people_to_slots.py`:
```python
self.cto_patterns = [
    r'\bCTO\b',
    r'\bChief Technology Officer\b',
    r'\bChief Technical Officer\b',
    r'\bVP.*Technology\b',
    r'\bVP.*Engineering\b',
]
```

3. Update `create_slots_for_companies()` to create 5 slots instead of 3

### Industry-Specific Patterns

For healthcare, education, non-profit sectors:

```python
# Healthcare
self.ceo_patterns_healthcare = [
    r'\bHospital Director\b',
    r'\bMedical Director\b',
    r'\bChief Medical Officer\b',
]

# Education
self.ceo_patterns_education = [
    r'\bSuperintendent\b',
    r'\bPresident\b',  # University president
    r'\bChancellor\b',
]

# Non-profit
self.ceo_patterns_nonprofit = [
    r'\bExecutive Director\b',
    r'\bChief Executive\b',
]
```

Then detect company industry and use appropriate patterns.

---

## Performance Benchmarks

**Tested on**:
- 453 companies
- 170 people
- Windows 11, Python 3.11.9
- Neon PostgreSQL

**Results**:
- Slot creation: ~2 seconds (1,359 slots)
- People mapping: ~8 seconds (170 people, 16 duplicates)
- Total time: ~10 seconds

**Projected for 47k companies**:
- Slot creation: ~4 minutes (141,000 slots)
- People mapping (150k people): ~15 minutes
- Total time: ~20 minutes per batch

---

## Future Improvements

### 1. Machine Learning Title Classification

Instead of regex patterns, train ML model on:
- Input: Job title string
- Output: CEO / CFO / HR / Other (with confidence)
- Training data: 10,000+ labeled titles

### 2. Smart Duplicate Resolution

Improve beyond "highest confidence wins":
- Use data recency (prefer newer records)
- Use profile completeness (prefer verified emails, LinkedIn)
- Use explicit hierarchy markers in titles

### 3. Bulk Operations

```bash
# Process in batches
python map_people_to_slots.py --batch-size 1000 --start 0 --end 47000

# Resume from failure
python map_people_to_slots.py --resume-from 15000
```

### 4. Configuration Files

Move patterns to YAML:

```yaml
# title_patterns.yaml
ceo:
  - pattern: '\bCEO\b'
    confidence: 1.0
  - pattern: '\bChief Executive Officer\b'
    confidence: 0.9
  - pattern: '\bExecutive Director\b'
    confidence: 0.7
```

### 5. Monitoring & Alerts

```python
# After mapping
if fill_rate < 10%:
    alert("Low fill rate - check patterns")

if duplicate_count > 100:
    alert("High duplicate count - review data quality")
```

---

## Troubleshooting

### Script Fails with "No module named 'psycopg2'"

```bash
pip install psycopg2-binary
```

### "Permission denied" on .env file

```bash
# Make sure DATABASE_URL is set
cat .env | grep DATABASE_URL
```

### Barton ID conflicts

```sql
-- Find conflicting IDs
SELECT company_slot_unique_id, COUNT(*)
FROM marketing.company_slot
GROUP BY company_slot_unique_id
HAVING COUNT(*) > 1;
```

---

## Contact & Support

- **Script Location**: `ctb/data/validation-framework/scripts/python/`
- **Documentation**: `ctb/data/validation-framework/docs/`
- **Database**: Neon PostgreSQL (Marketing DB)
- **Last Tested**: 2025-11-07

---

**Next Steps**:
1. Review unmapped people in `people_invalid` table
2. Validate and move back to `people_master`
3. Re-run mapping
4. Check which companies have all 3 slots filled
5. Use enrichment agents to fill remaining slots
