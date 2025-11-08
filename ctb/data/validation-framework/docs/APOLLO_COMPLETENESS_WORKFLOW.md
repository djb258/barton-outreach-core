# Apollo Completeness Workflow - Final System Design

**Date**: 2025-11-07
**Purpose**: 100% complete records (all fields + all 3 slots filled)
**Target**: 47,000 companies (50-2000 employees) with 150,000 people

---

## Complete Record Criteria

### ✅ Company is COMPLETE When:
1. **Address**: City + State (minimum)
2. **Website URL**: Company website
3. **LinkedIn**: Company LinkedIn profile
4. **All 3 Slots Filled**: CEO + CFO + HR executives

### ✅ Person is COMPLETE When:
1. **Mapped to Slot**: Assigned to CEO, CFO, or HR slot
2. **Email**: Work or personal email
3. **LinkedIn**: Personal LinkedIn profile
4. **Phone**: Optional (nice to have)

---

## Workflow

```
Apollo.io Import
(47k companies, 150k people)
         ↓
┌────────────────────┐
│ Completeness Check │
│                    │
│ Companies:         │
│ - Address?         │
│ - Website?         │
│ - LinkedIn?        │
│ - 3 slots filled?  │
│                    │
│ People:            │
│ - In a slot?       │
│ - Email?           │
│ - LinkedIn?        │
│ - Phone? (opt)     │
└────────────────────┘
         ↓
    ____/ \____
   /           \
COMPLETE      INCOMPLETE
  ↓             ↓
✅ DONE        enrichment_queue
              ↓
         Enrichment Agents
         (Apify, Clearbit, etc.)
              ↓
         Find Missing Data:
         - Address
         - Website
         - LinkedIn
         - Executives (CEO/CFO/HR)
         - Email/LinkedIn for people
              ↓
         Update Database
              ↓
    Re-validate IMMEDIATELY
              ↓
         COMPLETE? → ✅ DONE
         Still incomplete? → Back to queue
```

---

## Scripts

### 1. Validate Completeness

```bash
# Run completeness validation
cd ctb/data/validation-framework/scripts/python
python validate_completeness.py

# Dry run first
python validate_completeness.py --dry-run

# Only companies
python validate_completeness.py --companies-only

# Only people
python validate_completeness.py --people-only
```

**Output**:
- Complete companies → marked as validated
- Complete people → no action needed
- Incomplete → added to enrichment_queue with specific tasks

### 2. Map People to Slots

```bash
# After Apollo import, map people to slots
python map_people_to_slots.py

# This fills CEO, CFO, HR slots based on titles
# Companies with <3 filled slots = incomplete
```

### 3. Process Enrichment Queue

```bash
# Get pending tasks
psql $DATABASE_URL -c "
    SELECT
        entity_type,
        company_name,
        person_name,
        missing_fields,
        enrichment_tasks,
        priority
    FROM marketing.enrichment_queue
    WHERE status = 'pending'
    ORDER BY priority DESC, created_at
    LIMIT 100;
"

# Agent processes tasks:
# - Find missing address
# - Find missing website
# - Find missing executives
# - Find missing email/LinkedIn for people
```

### 4. Re-validate After Enrichment

```bash
# Immediately after agent enriches a record
python validate_completeness.py

# If now complete → marked as done
# If still incomplete → stays in queue for retry
```

---

## Database Schema

### enrichment_queue Table

```sql
CREATE TABLE marketing.enrichment_queue (
    id BIGSERIAL PRIMARY KEY,
    entity_type TEXT NOT NULL,          -- 'company' or 'person'
    entity_id TEXT NOT NULL,            -- company_unique_id or person unique_id
    company_name TEXT,
    person_name TEXT,

    missing_fields JSONB NOT NULL,      -- ["address", "website", "executives (1/3 filled)"]
    enrichment_tasks JSONB NOT NULL,    -- [{task, priority, agent, details}, ...]

    priority TEXT NOT NULL,             -- low, medium, high, critical
    status TEXT NOT NULL,               -- pending, in_progress, complete, failed

    created_at TIMESTAMP DEFAULT now(),
    completed_at TIMESTAMP,

    UNIQUE (entity_type, entity_id)
);
```

### company_master Updates

```sql
ALTER TABLE marketing.company_master
ADD COLUMN completeness_validated BOOLEAN DEFAULT FALSE,
ADD COLUMN needs_enrichment BOOLEAN DEFAULT FALSE,
ADD COLUMN enrichment_queued_at TIMESTAMP;
```

---

## Enrichment Tasks

### Company Tasks

| Missing Field | Agent Task | Agent |
|---------------|------------|-------|
| Address | `find_address` | Google Maps API, Clearbit |
| Website URL | `find_website` | Google Search, Clearbit |
| Company LinkedIn | `find_company_linkedin` | LinkedIn API |
| Executives (0/3) | `find_executives` | **ALWAYS find all 3** (Apollo, LinkedIn, Apify) |
| Executives (1/3) | `find_executives` | **Find missing 2** (CFO + HR, or CEO + HR, etc.) |
| Executives (2/3) | `find_executives` | **Find missing 1** (CEO, CFO, or HR) |

### Person Tasks

| Missing Field | Agent Task | Agent |
|---------------|------------|-------|
| Not in slot | `determine_role` | Title classifier → assign to CEO/CFO/HR |
| Email | `find_email` | Apollo, Hunter.io |
| LinkedIn | `find_linkedin_profile` | LinkedIn API, Apollo |
| Phone (optional) | `find_phone` | Apollo, ZoomInfo |

---

## Agent Behavior

### Rule: ALWAYS Try to Find All 3 Executives

Even if Apollo only gave you 1 or 2 executives, **agents MUST search for all 3**:

```python
# For companies with 50-2000 employees
# ALWAYS have CEO + CFO + HR

if filled_slots < 3:
    missing_roles = get_missing_slot_types(company)  # e.g., ['CFO', 'HR']

    for role in missing_roles:
        # Agent searches:
        # 1. Apollo.io (search by company + title)
        # 2. LinkedIn (company page → People → filter by title)
        # 3. Company website (About/Team page scraping)

        executive = agent_find_executive(company, role)

        if executive:
            insert_to_people_master(executive)
            fill_slot(company, role, executive)
        else:
            log_failure(company, role, "Executive not found after 3 attempts")
```

### Re-validation: IMMEDIATE After Enrichment

```python
# Agent workflow:
1. Pick task from enrichment_queue (status = 'pending')
2. Mark as 'in_progress'
3. Perform enrichment (find missing data)
4. Update database with found data
5. Mark task as 'complete'
6. **IMMEDIATELY re-validate** the record
7. If now complete → done
8. If still incomplete → back to queue (with incremented attempts)
```

---

## Expected Results

### From Apollo Import

**Likely scenario** (based on typical Apollo quality):
- Companies: ~70% complete (have address + website + LinkedIn)
- People: ~85% complete (have email + LinkedIn)
- Executives: ~40% have all 3 slots filled

**Initial state**:
- ~33,000 companies complete (70%)
- ~14,000 companies need enrichment (30%)
- ~127,500 people complete (85%)
- ~22,500 people need enrichment (15%)

### After Agent Enrichment

**Target** (with agents working):
- Companies: 95%+ complete
- People: 98%+ complete
- Executives: 90%+ have all 3 slots filled

**Remaining incomplete** (accept as edge cases):
- ~2,350 companies (5%)
- ~3,000 people (2%)
- These may be:
  - Defunct companies
  - Stealth startups
  - Companies that truly don't have HR executive
  - People who left the company

---

## Queries

### Check Completeness Status

```sql
-- Company completeness
SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE completeness_validated = TRUE) as complete,
    COUNT(*) FILTER (WHERE needs_enrichment = TRUE) as needs_enrichment,
    ROUND(100.0 * COUNT(*) FILTER (WHERE completeness_validated = TRUE) / COUNT(*), 1) as complete_pct
FROM marketing.company_master;

-- Companies with all 3 slots filled
SELECT
    cm.company_unique_id,
    cm.company_name,
    COUNT(cs.person_unique_id) as filled_slots
FROM marketing.company_master cm
LEFT JOIN marketing.company_slot cs ON cm.company_unique_id = cs.company_unique_id
    AND cs.is_filled = TRUE
GROUP BY cm.company_unique_id, cm.company_name
HAVING COUNT(cs.person_unique_id) = 3;
```

### View Enrichment Queue

```sql
-- Pending enrichment tasks (prioritized)
SELECT
    entity_type,
    company_name,
    person_name,
    missing_fields,
    priority,
    created_at
FROM marketing.enrichment_queue
WHERE status = 'pending'
ORDER BY
    CASE priority
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
    END,
    created_at
LIMIT 100;

-- Companies needing executives
SELECT
    company_name,
    enrichment_tasks
FROM marketing.enrichment_queue
WHERE entity_type = 'company'
AND status = 'pending'
AND enrichment_tasks::text LIKE '%find_executives%'
ORDER BY priority DESC;
```

### Monitor Progress

```sql
-- Enrichment queue stats
SELECT
    status,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) as percentage
FROM marketing.enrichment_queue
GROUP BY status
ORDER BY count DESC;

-- Completion rate over time
SELECT
    DATE(completeness_validated_at) as date,
    COUNT(*) as companies_completed
FROM marketing.company_master
WHERE completeness_validated = TRUE
AND completeness_validated_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(completeness_validated_at)
ORDER BY date;
```

---

## Implementation Checklist

### Day 1: Setup

- [x] Create enrichment_queue table
- [x] Create validate_completeness.py script
- [x] Add completeness columns to company_master
- [ ] Test on small batch (100 companies)

### Day 2: Apollo Import

- [ ] Import Apollo data (companies + people)
- [ ] Run slot mapping
- [ ] Run completeness validation
- [ ] Review enrichment queue

### Day 3: Agent Integration

- [ ] Set up agent workflows:
  - [ ] Address finder (Google Maps API)
  - [ ] Website finder (Clearbit/Google)
  - [ ] LinkedIn finder (LinkedIn API)
  - [ ] Executive finder (Apollo + LinkedIn + Apify)
  - [ ] Email finder (Hunter.io)
  - [ ] Phone finder (Apollo/ZoomInfo)
- [ ] Test agent enrichment on 10 records
- [ ] Verify immediate re-validation works

### Week 2: Scale

- [ ] Process enrichment queue (batch 1,000 at a time)
- [ ] Monitor completion rates
- [ ] Handle failed enrichments (max 3 attempts)
- [ ] Accept 90-95% completion as "done"

---

## Key Principles

1. **Completeness = 100% of required fields**
   - Not "good enough" data
   - ALL fields must be present

2. **Agents do the work**
   - You don't manually review
   - Agents find missing data
   - You monitor agent progress

3. **Immediate re-validation**
   - After agent enrichment → re-check right away
   - Don't batch re-validations

4. **ALWAYS find all 3 executives**
   - 50-2000 employee companies have CEO, CFO, HR
   - Agents must search for all 3
   - If not found after 3 attempts → flag as exception

5. **Phone is optional**
   - Nice to have for people
   - Don't fail validation without it
   - Log as warning only

---

## Success Metrics

**Target after enrichment**:
- 95%+ companies complete
- 98%+ people complete
- 90%+ companies with all 3 slots filled

**Acceptable edge cases** (5% incomplete):
- Defunct companies
- Stealth startups
- Companies without dedicated HR exec
- People who left the company

**Efficiency**:
- Initial completeness: 70-85%
- Agent enrichment: +10-15%
- Total time: ~1-2 weeks for 47k companies
- Your manual time: ~2-3 days setup + monitoring

---

**This is the final system design. All scripts are in place. Ready to process Apollo data!** 🚀
