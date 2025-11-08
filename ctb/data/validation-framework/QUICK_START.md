# Quick Start: Apollo → Completeness Validation

**Goal**: Validate 47k companies and 150k people for 100% completeness

---

## What "Complete" Means

### Company ✅
- City + State
- Website URL
- Company LinkedIn
- **ALL 3 slots filled** (CEO + CFO + HR)

### Person ✅
- Mapped to slot (CEO, CFO, or HR)
- Email
- LinkedIn
- Phone (optional)

---

## 3-Step Workflow

### Step 1: Import Apollo Data
```bash
# (Your Apollo import process here)
# Results in: company_master + people_master tables
```

### Step 2: Map People to Slots
```bash
cd ctb/data/validation-framework/scripts/python

# Map people to CEO/CFO/HR slots
python map_people_to_slots.py
```

### Step 3: Validate Completeness
```bash
# Check if companies/people are complete
python validate_completeness.py

# Incomplete records → enrichment_queue
# Complete records → marked as done ✅
```

---

## Agent Enrichment Loop

```bash
# View enrichment queue
psql $DATABASE_URL -c "
    SELECT entity_type, company_name, missing_fields, priority
    FROM marketing.enrichment_queue
    WHERE status = 'pending'
    ORDER BY priority DESC
    LIMIT 20;
"

# Agents find missing data:
# - Address (Google Maps)
# - Website (Clearbit/Google)
# - LinkedIn (LinkedIn API)
# - Executives (ALWAYS all 3: CEO + CFO + HR)
# - Email/LinkedIn for people

# After agent enrichment:
python validate_completeness.py  # Re-validate IMMEDIATELY

# If complete → done ✅
# If still incomplete → back to queue
```

---

## Key Rules

1. **ALWAYS find all 3 executives** (CEO + CFO + HR)
2. **Re-validate IMMEDIATELY** after agent work
3. **Phone is optional** for people (nice to have)
4. **50-2000 employees** = should have all 3 execs

---

## Files You Need

```
scripts/python/
├── validate_completeness.py     ← Main validation script
├── map_people_to_slots.py        ← Map people to CEO/CFO/HR
└── [supporting scripts]

sql/
├── create_enrichment_queue.sql   ← Agent work queue
└── create_company_slot.sql       ← Executive slots

docs/
├── APOLLO_COMPLETENESS_WORKFLOW.md  ← Full workflow guide
└── SLOT_MAPPING_COMPLETE_GUIDE.md   ← Title patterns reference
```

---

## Expected Results

**Initial** (Apollo data):
- ~70% companies complete
- ~85% people complete
- ~40% have all 3 slots

**After Agents**:
- 95%+ companies complete
- 98%+ people complete
- 90%+ have all 3 slots

**Time**: 1-2 weeks for 47k companies (mostly agent work, minimal manual effort)

---

## Quick Checks

```sql
-- How many companies complete?
SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE completeness_validated = TRUE) as complete,
    ROUND(100.0 * COUNT(*) FILTER (WHERE completeness_validated = TRUE) / COUNT(*), 1) || '%' as complete_pct
FROM marketing.company_master;

-- How many have all 3 slots?
SELECT COUNT(DISTINCT company_unique_id)
FROM marketing.company_slot
WHERE is_filled = TRUE
GROUP BY company_unique_id
HAVING COUNT(*) = 3;

-- Enrichment queue size?
SELECT status, COUNT(*)
FROM marketing.enrichment_queue
GROUP BY status;
```

---

**You're all set! Import Apollo data and run the scripts.** 🚀
