# Quick Wins Checklist: Implement These First

**Goal**: Get from current state (453 companies, 170 people) to production-ready for 47k companies and 150k people

**Time Investment**: ~2-3 days of focused work
**Time Savings**: 2+ years of manual validation work

---

## ✅ Priority 1: Must-Have (Implement Today)

### 1. Enhanced Duplicate Resolution (2 hours)

**Current**: 16 duplicates sent to manual review
**Target**: 0 duplicates sent to manual review

**Implementation**:

```python
# Add to map_people_to_slots.py

def score_candidate(person, confidence):
    """Score candidates for best-match selection"""
    score = confidence * 100

    # Title exactness (exact match = higher score)
    exact_titles = {'CEO': 20, 'Chief Executive Officer': 15, 'CFO': 20, 'Chief Financial Officer': 15}
    score += exact_titles.get(person['title'], 0)

    # Data completeness
    if person.get('linkedin_url'):
        score += 10
    if person.get('email_verified'):
        score += 10
    if person.get('work_phone_e164') or person.get('personal_phone_e164'):
        score += 5

    # Penalize co-roles
    if 'Co-' in person.get('title', ''):
        score -= 10

    return score

# In map_people_to_slots(), replace:
# best_person, best_conf = person_list_sorted[0]

# With:
scored = [(p, c, score_candidate(p, c)) for p, c in person_list]
best = max(scored, key=lambda x: x[2])
best_person, best_conf, best_score = best
```

**Test**:
```bash
python map_people_to_slots.py --skip-create
# Check: Should have 0 duplicates sent to invalid
```

---

### 2. Batch Processing (3 hours)

**Current**: All-or-nothing processing
**Target**: Process 1,000 companies at a time, save progress

**Implementation**:

```python
# Create: batch_slot_mapper.py

import json
import os
from map_people_to_slots import SlotMapper

class BatchSlotMapper:
    def __init__(self, batch_size=1000):
        self.batch_size = batch_size
        self.state_file = 'mapping_state.json'

    def load_checkpoint(self):
        if os.path.exists(self.state_file):
            with open(self.state_file) as f:
                state = json.load(f)
                return state.get('last_batch', 0)
        return 0

    def save_checkpoint(self, batch_num):
        with open(self.state_file, 'w') as f:
            json.dump({
                'last_batch': batch_num,
                'timestamp': datetime.now().isoformat()
            }, f)

    def process_all(self):
        start_batch = self.load_checkpoint()

        cursor = self.get_cursor()
        cursor.execute("SELECT COUNT(*) FROM marketing.company_master")
        total_companies = cursor.fetchone()[0]
        total_batches = (total_companies // self.batch_size) + 1

        for batch_num in range(start_batch, total_batches):
            offset = batch_num * self.batch_size
            limit = self.batch_size

            print(f"\n{'='*70}")
            print(f"BATCH {batch_num + 1}/{total_batches}")
            print(f"Companies: {offset} - {offset + limit}")
            print(f"Progress: {((batch_num + 1) / total_batches) * 100:.1f}%")
            print(f"{'='*70}\n")

            self.process_batch(offset, limit)
            self.save_checkpoint(batch_num + 1)

            # Progress stats
            filled = self.count_filled_slots()
            print(f"\nTotal slots filled: {filled}")

# Usage:
# python batch_slot_mapper.py
```

**Test**:
```bash
python batch_slot_mapper.py --batch-size 100
# Should process in batches, save progress after each
```

---

### 3. Confidence-Based Auto-Accept (1 hour)

**Current**: All mappings treated equally
**Target**: Auto-accept high confidence (>0.85), flag medium (0.5-0.85)

**Implementation**:

```python
# In map_people_to_slots.py, add:

CONFIDENCE_AUTO_ACCEPT = 0.85
CONFIDENCE_NEEDS_REVIEW = 0.50

def map_people_to_slots(self):
    # ... existing code ...

    for (company_id, slot_type), person_list in sorted(candidates.items()):
        # ... pick best person ...

        if confidence >= CONFIDENCE_AUTO_ACCEPT:
            # Auto-accept - high confidence
            self.fill_slot(company_id, slot_type, person, confidence)
            print(f"  [AUTO] {person['full_name'][:30]:30} -> {slot_type:3} (conf: {confidence:.2f})")

        elif confidence >= CONFIDENCE_NEEDS_REVIEW:
            # Flag for review - medium confidence
            self.fill_slot(company_id, slot_type, person, confidence)
            self.flag_for_review(company_id, slot_type, person, confidence, "Medium confidence mapping")
            print(f"  [REVIEW] {person['full_name'][:30]:30} -> {slot_type:3} (conf: {confidence:.2f}) *FLAGGED*")

        else:
            # Skip - low confidence
            print(f"  [SKIP] {person['full_name'][:30]:30} -> {slot_type:3} (conf: {confidence:.2f}) - Too low")

def flag_for_review(self, company_id, slot_type, person, confidence, reason):
    # Insert to review queue table
    cursor.execute("""
        INSERT INTO marketing.slot_review_queue (
            company_unique_id, slot_type, person_unique_id,
            confidence_score, reason, created_at
        ) VALUES (%s, %s, %s, %s, %s, now())
    """, (company_id, slot_type, person['unique_id'], confidence, reason))
```

**SQL**:
```sql
-- Create review queue table
CREATE TABLE IF NOT EXISTS marketing.slot_review_queue (
    id BIGSERIAL PRIMARY KEY,
    company_unique_id TEXT NOT NULL,
    slot_type TEXT NOT NULL,
    person_unique_id TEXT NOT NULL,
    confidence_score DECIMAL(3,2),
    reason TEXT,
    reviewed BOOLEAN DEFAULT FALSE,
    reviewed_at TIMESTAMP,
    reviewed_by TEXT,
    action_taken TEXT,
    created_at TIMESTAMP DEFAULT now()
);
```

---

## ✅ Priority 2: High Value (Implement This Week)

### 4. Title Normalization Database (2 hours)

**Benefit**: 10x faster lookups, easier pattern updates

**Implementation**:

```sql
-- Create table
CREATE TABLE public.title_normalization (
    raw_title TEXT PRIMARY KEY,
    normalized_title TEXT NOT NULL,
    slot_type TEXT NOT NULL,
    confidence DECIMAL(3,2) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT now()
);

-- Seed with top 100 titles
INSERT INTO public.title_normalization (raw_title, normalized_title, slot_type, confidence) VALUES
    ('CEO', 'Chief Executive Officer', 'CEO', 1.00),
    ('Chief Executive Officer', 'Chief Executive Officer', 'CEO', 1.00),
    ('President & CEO', 'Chief Executive Officer', 'CEO', 0.95),
    ('CFO', 'Chief Financial Officer', 'CFO', 1.00),
    ('Chief Financial Officer', 'Chief Financial Officer', 'CFO', 1.00),
    -- ... add more as you see them
    ;

-- Index for fast lookups
CREATE INDEX idx_title_norm_raw ON public.title_normalization(raw_title);
CREATE INDEX idx_title_norm_slot ON public.title_normalization(slot_type);
```

**Usage**:
```python
# In map_people_to_slots.py, add lookup method
def detect_slot_type_db(self, title):
    cursor.execute("""
        SELECT slot_type, confidence
        FROM public.title_normalization
        WHERE raw_title = %s
    """, (title,))

    result = cursor.fetchone()
    if result:
        return result[0], result[1]

    # Fall back to regex patterns
    return self.detect_slot_type_regex(title)
```

---

### 5. Smart Company Filtering (1 hour)

**Benefit**: Skip 25% of low-quality companies

**Implementation**:

```python
# In batch_slot_mapper.py

def should_process_company(self, company):
    """Filter out companies not worth processing"""

    # Must have website (passed validation)
    if not company.get('website_url'):
        return False

    # Must not be in company_invalid
    if company['company_unique_id'] in self.invalid_companies:
        return False

    # Optional: minimum employee count
    if company.get('employee_count', 0) < 10:
        return False

    # Optional: target industries only
    PRIORITY_INDUSTRIES = ['Technology', 'Healthcare', 'Finance', 'Manufacturing']
    if company.get('industry') not in PRIORITY_INDUSTRIES:
        return False  # Or True to include all

    return True
```

---

### 6. Incremental Validation (2 hours)

**Benefit**: Only re-process changed data

**Implementation**:

```python
import hashlib

def hash_company_data(company):
    """Create hash of company data to detect changes"""
    data = f"{company.get('company_name')}|{company.get('website_url')}|{company.get('industry')}"
    return hashlib.md5(data.encode()).hexdigest()

def needs_validation(self, company):
    """Check if company data has changed since last validation"""
    current_hash = hash_company_data(company)

    if company.get('validation_hash') == current_hash:
        return False  # No changes

    return True

# After successful validation
cursor.execute("""
    UPDATE marketing.company_master
    SET validation_hash = %s,
        last_validated_at = now()
    WHERE company_unique_id = %s
""", (current_hash, company['company_unique_id']))
```

---

## ✅ Priority 3: Nice to Have (When You Have Time)

### 7. Quick Status Dashboard (30 minutes)

```bash
#!/bin/bash
# status.sh - Quick validation status

echo "=== VALIDATION STATUS ==="
psql $DATABASE_URL -c "
    WITH stats AS (
        SELECT
            (SELECT COUNT(*) FROM marketing.company_master) as total_companies,
            (SELECT COUNT(*) FROM marketing.company_master WHERE website_url IS NOT NULL) as valid_companies,
            (SELECT COUNT(*) FROM marketing.company_slot WHERE is_filled = TRUE) as filled_slots,
            (SELECT COUNT(*) FROM marketing.company_slot) as total_slots,
            (SELECT COUNT(DISTINCT person_unique_id) FROM marketing.company_slot WHERE is_filled = TRUE) as mapped_people,
            (SELECT COUNT(*) FROM marketing.people_master) as total_people
    )
    SELECT
        'Companies Validated' as metric,
        valid_companies || ' / ' || total_companies as count,
        ROUND(100.0 * valid_companies / NULLIF(total_companies, 0), 1) || '%' as percentage
    FROM stats
    UNION ALL
    SELECT
        'Slots Filled',
        filled_slots || ' / ' || total_slots,
        ROUND(100.0 * filled_slots / NULLIF(total_slots, 0), 1) || '%'
    FROM stats
    UNION ALL
    SELECT
        'People Mapped',
        mapped_people || ' / ' || total_people,
        ROUND(100.0 * mapped_people / NULLIF(total_people, 0), 1) || '%'
    FROM stats;
"
```

---

### 8. Pattern Configuration File (1 hour)

```yaml
# title_patterns.yaml
ceo:
  exact_matches:
    - CEO
    - Chief Executive Officer
  patterns:
    - pattern: '\bCEO\b'
      confidence: 1.0
    - pattern: '\bPresident.*CEO\b'
      confidence: 0.9
    - pattern: '\bExecutive Director\b'
      confidence: 0.7

cfo:
  exact_matches:
    - CFO
    - Chief Financial Officer
  patterns:
    - pattern: '\bCFO\b'
      confidence: 1.0
    - pattern: '\bVP.*Finance\b'
      confidence: 0.75

hr:
  exact_matches:
    - CHRO
    - Chief Human Resources Officer
  patterns:
    - pattern: '\bCHRO\b'
      confidence: 1.0
    - pattern: '\bVP.*HR\b'
      confidence: 0.8
```

---

## Testing Checklist

After each implementation:

```bash
# Test 1: Small batch
python batch_slot_mapper.py --batch-size 10 --dry-run

# Test 2: Check duplicate resolution
python -c "
import psycopg2, os
from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM marketing.people_invalid WHERE batch_id LIKE %s', ('UNMAPPED-%',))
print(f'Unmapped people in invalid: {cursor.fetchone()[0]}')
print('Target: 0')
"

# Test 3: Check auto-accept rate
python -c "
import psycopg2, os
from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM marketing.company_slot WHERE is_filled = TRUE AND confidence_score >= 0.85')
auto = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM marketing.company_slot WHERE is_filled = TRUE')
total = cursor.fetchone()[0]
print(f'Auto-accepted: {auto}/{total} ({auto/total*100:.1f}%)')
print('Target: >70%')
"

# Test 4: Run status dashboard
bash status.sh
```

---

## Success Metrics

**Before improvements**:
- Manual review needed: 16 duplicates (100%)
- Processing time: All or nothing
- Review burden: Every mapping

**After improvements**:
- Manual review needed: <10% of mappings
- Processing time: Resumable batches
- Review burden: Only medium-confidence cases

**For 47k companies / 150k people**:
- Estimated time: 3 months (vs 2.5 years)
- Manual review: ~15,000 records (vs 150,000)
- Processing: Overnight batches (vs months of runtime)

---

## Order of Implementation

**Day 1**: Priority 1 items (5-6 hours)
- Enhanced duplicate resolution
- Batch processing
- Confidence thresholds

**Day 2**: Priority 2 items (5-6 hours)
- Title normalization
- Company filtering
- Incremental validation

**Day 3**: Testing & refinement
- Run on full dataset
- Fix edge cases
- Document learnings

**Result**: Production-ready system for 47k+ companies

---

## When You're Ready to Scale

```bash
# Process all 47k companies in batches
python batch_slot_mapper.py --batch-size 1000

# Review flagged items
SELECT * FROM marketing.slot_review_queue WHERE reviewed = FALSE ORDER BY confidence_score ASC;

# Check progress
bash status.sh

# Resume if interrupted
python batch_slot_mapper.py --batch-size 1000  # Will resume from last checkpoint
```

---

**Bottom Line**: Implement these 6 items in 2-3 days, save 2+ years of manual work.

Start with Priority 1, test thoroughly, then move to Priority 2. You got this! 💪
