# Solo Operator Strategy: Scaling to 47K Companies & 150K People

**Context**: You're the only person validating 47,000 companies and ~150,000 people
**Goal**: Maximize data quality while minimizing manual work
**Not client-facing**: Internal data quality improvements

---

## If I Were You: My 10-Point Strategy

### 1. **Automate Duplicate Resolution (Don't Send to Invalid)**

**Current Problem**: 16 duplicates sent to `people_invalid` for manual review

**My Solution**: Programmatic tie-breaking rules instead of manual review

```python
# Enhanced duplicate resolution
def pick_best_executive(candidates):
    """
    When multiple people match same slot, pick best using:
    1. Title exactness (CEO > Co-CEO > Executive Director)
    2. Data completeness (has LinkedIn + verified email > just email)
    3. Data recency (created_at/updated_at newer = better)
    4. Confidence score (only as tiebreaker)
    """

    # Score each candidate
    for person, confidence in candidates:
        score = confidence * 100  # Start with pattern confidence

        # Title exactness bonus
        if person['title'] == 'CEO':
            score += 20
        elif person['title'] == 'Chief Executive Officer':
            score += 15
        elif 'Co-' in person['title']:
            score -= 10  # Co-CEO is shared role

        # Completeness bonus
        if person.get('linkedin_url'):
            score += 10
        if person.get('email_verified'):
            score += 10
        if person.get('phone'):
            score += 5

        # Recency bonus (within last 6 months)
        if person.get('updated_at'):
            days_old = (now() - person['updated_at']).days
            if days_old < 180:
                score += (180 - days_old) / 18  # Max +10 points

        person['_auto_score'] = score

    # Pick highest score
    return max(candidates, key=lambda x: x[0]['_auto_score'])
```

**Impact**: Eliminates 100% of manual duplicate reviews → saves ~160 hours on 150k people (assuming 1% duplicate rate = 1,500 duplicates × 6 min each)

---

### 2. **Batch Processing with Progress Tracking**

**Current Problem**: All-or-nothing processing - if fails at 40k companies, lose all progress

**My Solution**: Process in batches of 1,000 companies, save state

```python
class BatchSlotMapper:
    def __init__(self, batch_size=1000):
        self.batch_size = batch_size
        self.state_file = 'mapping_state.json'

    def process_all(self):
        # Load last checkpoint
        start_batch = self.load_checkpoint()

        # Process in batches
        for batch_num in range(start_batch, 47):  # 47 batches for 47k companies
            print(f"[BATCH {batch_num + 1}/47] Processing companies {batch_num * 1000} - {(batch_num + 1) * 1000}")

            self.process_batch(batch_num)
            self.save_checkpoint(batch_num + 1)

            # Progress report
            pct = ((batch_num + 1) / 47) * 100
            print(f"  Progress: {pct:.1f}% complete")
            print(f"  Total mapped so far: {self.get_total_mapped()}")
            print()
```

**Impact**: Can resume from failures, track progress, process overnight without monitoring

---

### 3. **Quality-Based Prioritization (Don't Waste Time on Junk)**

**Current Problem**: Trying to map people to companies with no website (failed validation)

**My Solution**: Skip low-quality companies entirely

```python
# Before processing people for a company, check quality
def should_process_company(company):
    """Skip companies not worth processing yet"""

    # Must have website (passed validation)
    if not company.get('website_url'):
        return False, "No website - fix company data first"

    # Must not be in invalid table
    if company['company_unique_id'] in invalid_companies:
        return False, "Company failed validation"

    # Optional: Industry filter (focus on target industries)
    if PRIORITY_INDUSTRIES and company.get('industry') not in PRIORITY_INDUSTRIES:
        return False, "Non-priority industry"

    return True, None

# Result: Only process 339 valid companies (not all 453)
# For 47k: Might reduce to ~35k valid companies worth processing
```

**Impact**: 25% reduction in processing time, focus on actionable data

---

### 4. **Confidence Thresholds (Auto-Accept High Quality)**

**Current Problem**: Reviewing every mapping manually

**My Solution**: Auto-accept high confidence, flag only questionable ones

```python
CONFIDENCE_THRESHOLDS = {
    'auto_accept': 0.85,   # Auto-fill slot, no review needed
    'needs_review': 0.50,  # Flag for manual review
    'auto_reject': 0.50    # Below this, don't even try
}

def process_mapping(person, slot, confidence):
    if confidence >= 0.85:
        # High confidence - just do it
        fill_slot(person, slot)
        log_action('auto_accepted', confidence)

    elif confidence >= 0.50:
        # Medium confidence - flag for review
        add_to_review_queue(person, slot, confidence)
        log_action('flagged_review', confidence)

    else:
        # Low confidence - skip
        log_action('auto_rejected', confidence)
```

**Impact**:
- ~70% auto-accepted (no review)
- ~20% flagged for review (focus your time here)
- ~10% auto-rejected (saves time)

---

### 5. **Title Normalization Database**

**Current Problem**: "CEO" and "Chief Executive Officer" treated as different patterns (different confidence scores)

**My Solution**: Normalize titles before pattern matching

```sql
-- Create title normalization table
CREATE TABLE public.title_normalization (
    raw_title TEXT PRIMARY KEY,
    normalized_title TEXT NOT NULL,
    slot_type TEXT NOT NULL,  -- CEO, CFO, HR
    confidence DECIMAL(3,2) NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);

-- Seed with known mappings
INSERT INTO public.title_normalization VALUES
    ('CEO', 'Chief Executive Officer', 'CEO', 1.00),
    ('Chief Executive Officer', 'Chief Executive Officer', 'CEO', 1.00),
    ('President & CEO', 'Chief Executive Officer', 'CEO', 0.95),
    ('Co-CEO', 'Chief Executive Officer', 'CEO', 0.85),  -- Lower confidence
    ('Executive Director', 'Chief Executive Officer', 'CEO', 0.70),

    ('CFO', 'Chief Financial Officer', 'CFO', 1.00),
    ('Chief Financial Officer', 'Chief Financial Officer', 'CFO', 1.00),
    ('VP Finance', 'Chief Financial Officer', 'CFO', 0.75),
    ('Controller', 'Chief Financial Officer', 'CFO', 0.65),

    ('CHRO', 'Chief Human Resources Officer', 'HR', 1.00),
    ('VP HR', 'Chief Human Resources Officer', 'HR', 0.80),
    ('HR Director', 'Chief Human Resources Officer', 'HR', 0.70);

-- Use it
SELECT
    pm.unique_id,
    tn.slot_type,
    tn.confidence
FROM marketing.people_master pm
JOIN public.title_normalization tn ON pm.title = tn.raw_title
WHERE tn.confidence >= 0.50;
```

**Impact**:
- Faster lookups (hash table vs regex)
- Easier to update patterns (just INSERT new row)
- Crowdsource patterns (add titles as you see them)

---

### 6. **Smart Defaults for Solo Companies**

**Current Problem**: Company has 1 person, they're "VP Finance", but CFO slot empty

**My Solution**: If only 1 executive in database, promote them intelligently

```python
def smart_fill_slots(company_id):
    """Fill slots intelligently when limited data"""

    # Get all people at this company
    people = get_people_for_company(company_id)

    if len(people) == 1:
        person = people[0]

        # Solo executive gets best-guess slot
        if 'Finance' in person['title'] or 'CFO' in person['title']:
            fill_slot(company_id, 'CFO', person)
        elif 'CEO' in person['title'] or 'Executive' in person['title']:
            fill_slot(company_id, 'CEO', person)
        elif 'HR' in person['title'] or 'People' in person['title']:
            fill_slot(company_id, 'HR', person)
        else:
            # Generic title - fill CEO by default (assume most senior)
            fill_slot(company_id, 'CEO', person)

    elif len(people) == 2:
        # Two executives - try to fill CEO + one other
        titles = [p['title'] for p in people]

        # Strategy: CEO + CFO is most common
        # Find best CEO match
        ceo_match = find_best_match(people, 'CEO')
        if ceo_match:
            fill_slot(company_id, 'CEO', ceo_match)
            remaining = [p for p in people if p != ceo_match]
            # Fill CFO with remaining person if finance-related
            if 'Finance' in remaining[0]['title']:
                fill_slot(company_id, 'CFO', remaining[0])
```

**Impact**: Increases fill rate from 16% → ~40% with smart guessing

---

### 7. **Enrichment Prioritization (Fill Gaps Strategically)**

**Current Problem**: 1,205 empty slots (88.7%) - can't manually fill all

**My Solution**: Prioritize enrichment by business value

```python
# Rank companies for enrichment
def calculate_enrichment_priority(company):
    priority_score = 0

    # High value companies first
    if company.get('employee_count', 0) > 500:
        priority_score += 50
    elif company.get('employee_count', 0) > 100:
        priority_score += 30

    # Target industries
    if company.get('industry') in ['Technology', 'Healthcare', 'Finance']:
        priority_score += 20

    # Already have some data
    filled_slots = count_filled_slots(company['company_unique_id'])
    if filled_slots == 2:  # Close to complete
        priority_score += 40
    elif filled_slots == 1:
        priority_score += 20

    # Geographic focus
    if company.get('state') in ['CA', 'NY', 'TX']:
        priority_score += 10

    return priority_score

# Process highest priority first
companies_ranked = sorted(companies, key=calculate_enrichment_priority, reverse=True)

for company in companies_ranked[:5000]:  # Top 5k companies
    enrich_executives(company)
```

**Impact**: Fill most valuable slots first, maximize ROI on enrichment budget

---

### 8. **Validation Rules as Configuration (Not Code)**

**Current Problem**: Have to edit Python code to add new title patterns

**My Solution**: YAML configuration file

```yaml
# title_patterns.yaml
ceo:
  exact_matches:
    - CEO
    - Chief Executive Officer
  patterns:
    - pattern: '\bCEO\b'
      confidence: 1.0
      industry: all
    - pattern: '\bPresident\b'
      confidence: 0.8
      industry: all
    - pattern: '\bSuperintendent\b'
      confidence: 0.9
      industry: education
    - pattern: '\bHospital Director\b'
      confidence: 0.85
      industry: healthcare

cfo:
  exact_matches:
    - CFO
    - Chief Financial Officer
  patterns:
    - pattern: '\bCFO\b'
      confidence: 1.0
    - pattern: '\bVP.*Finance\b'
      confidence: 0.75
    - pattern: '\bController\b'
      confidence: 0.65

# Then in code:
patterns = yaml.load('title_patterns.yaml')
```

**Impact**: Non-technical users can update patterns, version control on pattern changes

---

### 9. **Incremental Validation (Don't Re-Process Everything)**

**Current Problem**: Re-running validation processes all 47k companies every time

**My Solution**: Track what's been validated, only process new/changed

```sql
-- Add tracking columns
ALTER TABLE marketing.company_master
ADD COLUMN last_validated_at TIMESTAMP,
ADD COLUMN validation_hash TEXT;  -- Hash of company data

-- Only validate if data changed
def needs_validation(company):
    current_hash = hash_company_data(company)

    if company['validation_hash'] == current_hash:
        # Data hasn't changed, skip
        return False

    return True

# Result: First run = 47k companies
#         Second run = only changed companies (~1-5% per day)
```

**Impact**: 95% reduction in re-processing time

---

### 10. **Statistical Reporting (Know When to Stop)**

**Current Problem**: Don't know if 90% validated is good enough or need 100%

**My Solution**: Track diminishing returns

```python
def generate_validation_report():
    return {
        'companies': {
            'total': 47000,
            'validated': 42000,
            'validation_rate': '89.4%',

            'with_all_3_slots': 5000,  # 10.6% fully complete
            'with_2_slots': 8000,      # 17.0%
            'with_1_slot': 12000,      # 25.5%
            'with_0_slots': 22000,     # 46.8%
        },

        'people': {
            'total': 150000,
            'mapped': 135000,
            'mapping_rate': '90.0%',
            'duplicates_resolved': 15000,
            'unmapped': 15000,
        },

        'efficiency': {
            'avg_time_per_company': '0.5 seconds',
            'total_processing_time': '6.5 hours',
            'manual_review_needed': '2,000 records (1.3%)',
            'estimated_manual_hours': '200 hours',
        },

        'recommendations': [
            'Stop at 90% - diminishing returns beyond this',
            'Focus enrichment on 22k companies with 0 slots',
            'Accept that 10% will remain incomplete (cost/benefit)',
        ]
    }
```

**Impact**: Data-driven decisions on when validation is "good enough"

---

## My Priority Stack (What I'd Do First)

### Week 1: Foundation
1. ✅ Implement batch processing with checkpoints
2. ✅ Add quality-based filtering (skip invalid companies)
3. ✅ Set up confidence thresholds (auto-accept high, flag medium)

### Week 2: Automation
4. ✅ Enhanced duplicate resolution (no manual review)
5. ✅ Title normalization database
6. ✅ Incremental validation (only process changes)

### Week 3: Optimization
7. ✅ Smart defaults for small companies
8. ✅ Enrichment prioritization scoring
9. ✅ Configuration-based patterns (YAML)

### Week 4: Reporting
10. ✅ Statistical reporting dashboard
11. Track diminishing returns
12. Set "good enough" thresholds

---

## Key Principle: **Automate the 90%, Review the 10%**

### The Math

**Without automation**:
- 150,000 people × 2 minutes each = 5,000 hours of manual work
- That's 625 8-hour days = **2.5 years of full-time work**

**With automation**:
- 135,000 auto-processed (90%) = 0 manual hours
- 15,000 flagged for review (10%) × 2 minutes = 500 hours
- That's 62.5 8-hour days = **~3 months of work**

**Savings**: 2.25 years → 3 months (90% reduction)

---

## What NOT to Do

❌ **Don't try to manually review all 150k people** - it's not scalable

❌ **Don't aim for 100% perfection** - 90% is usually good enough for internal data

❌ **Don't process everything in one run** - batch processing prevents disaster

❌ **Don't build complex UI** - command-line scripts are fine for solo work

❌ **Don't ignore data quality at source** - fix bad company data first

❌ **Don't process companies with no enrichment value** - prioritize high-value targets

---

## Tools to Build

### 1. Quick Status Dashboard (10 minutes to build)

```bash
# status.sh
#!/bin/bash
echo "=== Validation Status ==="
psql $DATABASE_URL -c "
    SELECT
        'Companies Validated' as metric,
        COUNT(*) FILTER (WHERE validated = TRUE) as count,
        ROUND(100.0 * COUNT(*) FILTER (WHERE validated = TRUE) / COUNT(*), 1) || '%' as percentage
    FROM marketing.company_master
    UNION ALL
    SELECT
        'Slots Filled',
        COUNT(*) FILTER (WHERE is_filled = TRUE),
        ROUND(100.0 * COUNT(*) FILTER (WHERE is_filled = TRUE) / COUNT(*), 1) || '%'
    FROM marketing.company_slot
    UNION ALL
    SELECT
        'People Mapped',
        COUNT(DISTINCT person_unique_id),
        ROUND(100.0 * COUNT(DISTINCT person_unique_id) / (SELECT COUNT(*) FROM marketing.people_master), 1) || '%'
    FROM marketing.company_slot WHERE is_filled = TRUE;
"
```

### 2. Batch Progress Tracker

```python
# progress.py
import json
from datetime import datetime

def log_progress(batch_num, companies_processed, people_mapped):
    with open('progress.jsonl', 'a') as f:
        f.write(json.dumps({
            'timestamp': datetime.now().isoformat(),
            'batch': batch_num,
            'companies': companies_processed,
            'people': people_mapped,
        }) + '\n')

# Then visualize with:
# tail -f progress.jsonl | jq
```

### 3. Error Aggregator

```sql
-- See most common errors
SELECT
    reason_code,
    COUNT(*) as frequency,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) as percentage
FROM marketing.company_invalid
GROUP BY reason_code
ORDER BY frequency DESC
LIMIT 10;
```

---

## Final Recommendation

**Focus on the 20% that gives you 80% of value:**

1. **Auto-accept high-confidence mappings** (saves 70% of time)
2. **Skip low-quality companies** (saves 25% of processing)
3. **Batch process with checkpoints** (prevents lost work)
4. **Review only flagged items** (focus your expertise)
5. **Accept 90% completion** (diminishing returns after this)

With these improvements:
- **Before**: 2.5 years of manual work
- **After**: 3 months of semi-automated work
- **Your time**: Focus on the 15,000 "review needed" cases, not all 150,000

That's my honest advice as a solo operator. Ship the 90% solution fast, iterate on the edge cases.
