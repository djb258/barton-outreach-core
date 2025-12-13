# PLE Schema Reference - Marketing Database

Complete table-by-table documentation for the Pipeline Lifecycle Engine (PLE) marketing schema.

---

## Table of Contents

1. [company_master](#company_master)
2. [company_slot](#company_slot)
3. [people_master](#people_master)
4. [person_movement_history](#person_movement_history)
5. [person_scores](#person_scores)
6. [company_events](#company_events)
7. [Quick Reference](#quick-reference)

---

## company_master

**Purpose:** Master record for validated companies in the outreach pipeline.

**Barton ID Format:** `04.04.01.XX.XXXXX.XXX`

**Primary Key:** `company_unique_id`

### Columns

| Column | Type | Required | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| company_unique_id | text | YES | - | PK, Barton ID format | Unique company identifier |
| company_name | text | YES | - | - | Legal or DBA company name |
| website_url | text | YES | - | - | Primary company website |
| industry | text | NO | - | - | Industry classification |
| employee_count | integer | YES | - | >= 50 | Number of employees |
| company_phone | text | NO | - | - | Main company phone |
| address_street | text | NO | - | - | Street address |
| address_city | text | NO | - | - | City |
| address_state | text | YES | - | PA, VA, MD, OH, WV, KY | State (full name) |
| address_zip | text | NO | - | - | ZIP code |
| address_country | text | NO | - | - | Country |
| linkedin_url | text | NO | - | - | LinkedIn company page |
| facebook_url | text | NO | - | - | Facebook page |
| twitter_url | text | NO | - | - | Twitter/X handle |
| sic_codes | text | NO | - | - | SIC classification codes |
| founded_year | integer | NO | - | 1700-current year | Year founded |
| keywords | text[] | NO | - | - | Search/classification keywords |
| description | text | NO | - | - | Company description |
| source_system | text | YES | - | - | Source system name |
| source_record_id | text | NO | - | - | Source system record ID |
| promoted_from_intake_at | timestamptz | YES | now() | - | Promotion timestamp |
| promotion_audit_log_id | integer | NO | - | - | Audit log reference |
| created_at | timestamptz | NO | now() | - | Record creation time |
| updated_at | timestamptz | NO | now() | - | Last update time |
| state_abbrev | text | NO | - | - | State abbreviation (e.g., PA) |
| import_batch_id | text | NO | - | - | Batch import identifier |
| validated_at | timestamptz | NO | - | - | Validation timestamp |
| validated_by | text | NO | - | - | Validator identifier |
| data_quality_score | numeric | NO | - | - | Data quality score (0-100) |

### Foreign Keys
None (root entity)

### Indexes
- Primary key on `company_unique_id`
- Unique constraint on Barton ID format

### Example Insert

```sql
INSERT INTO marketing.company_master (
    company_unique_id,
    company_name,
    website_url,
    industry,
    employee_count,
    address_state,
    source_system,
    promoted_from_intake_at
) VALUES (
    '04.04.01.04.30001.001',
    'Acme Corporation',
    'https://www.acmecorp.com',
    'Technology',
    250,
    'PA',
    'csv_import',
    NOW()
);
```

---

## company_slot

**Purpose:** Tracks executive positions (CEO, CFO, HR) per company. Links companies to people.

**Barton ID Format:** `04.04.05.XX.XXXXX.XXX`

**Primary Key:** `company_slot_unique_id`

**Unique Constraint:** One slot per (company_unique_id, slot_type) combination

### Columns

| Column | Type | Required | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| company_slot_unique_id | text | YES | - | PK, Barton ID format | Unique slot identifier |
| company_unique_id | text | YES | - | FK → company_master | Company reference |
| person_unique_id | text | NO | - | FK → people_master | Person filling slot (nullable) |
| slot_type | text | YES | - | CEO, CFO, HR | Executive role type |
| is_filled | boolean | NO | false | - | Whether slot is filled |
| confidence_score | numeric | NO | - | 0-100 | Confidence in assignment |
| created_at | timestamptz | NO | now() | - | Slot creation time |
| filled_at | timestamptz | NO | - | - | When slot was filled |
| last_refreshed_at | timestamptz | NO | - | - | Last enrichment refresh |
| filled_by | text | NO | - | - | Source that filled slot |
| source_system | text | NO | 'manual' | - | Source system |
| enrichment_attempts | integer | NO | 0 | - | Number of enrichment attempts |
| status | varchar(20) | NO | 'open' | - | Slot status (open, filled, vacated) |
| vacated_at | timestamp | NO | - | - | When person left role |

### Foreign Keys
- `company_unique_id` → `company_master.company_unique_id`
- `person_unique_id` → `people_master.unique_id`

### Indexes
- Primary key on `company_slot_unique_id`
- Unique constraint on `(company_unique_id, slot_type)`
- Foreign key indexes on both FKs

### Example Insert

```sql
-- Create empty slot for CEO position
INSERT INTO marketing.company_slot (
    company_slot_unique_id,
    company_unique_id,
    slot_type,
    is_filled,
    source_system
) VALUES (
    '04.04.05.04.10001.001',
    '04.04.01.04.30001.001',
    'CEO',
    false,
    'auto_slot_creation'
);

-- Fill slot after enrichment
UPDATE marketing.company_slot
SET
    person_unique_id = '04.04.02.04.20001.001',
    is_filled = true,
    filled_at = NOW(),
    filled_by = 'apify_enrichment',
    confidence_score = 95.5
WHERE company_slot_unique_id = '04.04.05.04.10001.001';
```

---

## people_master

**Purpose:** Master record for executive contacts in the pipeline.

**Barton ID Format:** `04.04.02.XX.XXXXX.XXX`

**Primary Key:** `unique_id`

### Columns

| Column | Type | Required | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| unique_id | text | YES | - | PK, Barton ID format | Unique person identifier |
| company_unique_id | text | YES | - | FK → company_master | Current company |
| company_slot_unique_id | text | YES | - | FK → company_slot | Slot being filled |
| first_name | text | YES | - | - | First name |
| last_name | text | YES | - | - | Last name |
| full_name | text | NO | - | - | Full name (computed) |
| title | text | NO | - | - | Job title |
| seniority | text | NO | - | - | Seniority level |
| department | text | NO | - | - | Department |
| email | text | NO | - | Valid email format | Email address |
| work_phone_e164 | text | NO | - | - | Work phone (E.164 format) |
| personal_phone_e164 | text | NO | - | - | Personal phone (E.164) |
| linkedin_url | text | NO | - | - | LinkedIn profile URL |
| twitter_url | text | NO | - | - | Twitter/X profile |
| facebook_url | text | NO | - | - | Facebook profile |
| bio | text | NO | - | - | Professional bio |
| skills | text[] | NO | - | - | Skills array |
| education | text | NO | - | - | Education history |
| certifications | text[] | NO | - | - | Certifications array |
| source_system | text | YES | - | - | Source system |
| source_record_id | text | NO | - | - | Source record ID |
| promoted_from_intake_at | timestamptz | YES | now() | - | Promotion timestamp |
| promotion_audit_log_id | integer | NO | - | - | Audit log reference |
| created_at | timestamptz | NO | now() | - | Record creation |
| updated_at | timestamptz | NO | now() | - | Last update |
| email_verified | boolean | NO | false | - | Email verification status |
| message_key_scheduled | text | NO | - | - | Scheduled message key |
| email_verification_source | text | NO | - | - | Verification source |
| email_verified_at | timestamptz | NO | - | - | Verification timestamp |
| validation_status | varchar | NO | - | - | Validation status |
| last_verified_at | timestamp | YES | now() | - | Last verification check |
| last_enrichment_attempt | timestamp | NO | - | - | Last enrichment attempt |

### Foreign Keys
- `company_unique_id` → `company_master.company_unique_id`
- `company_slot_unique_id` → `company_slot.company_slot_unique_id`

### Check Constraints
- At least one of `linkedin_url` OR `email` must be non-null
- Email must match valid email regex

### Example Insert

```sql
INSERT INTO marketing.people_master (
    unique_id,
    company_unique_id,
    company_slot_unique_id,
    first_name,
    last_name,
    full_name,
    title,
    email,
    linkedin_url,
    source_system
) VALUES (
    '04.04.02.04.20001.001',
    '04.04.01.04.30001.001',
    '04.04.05.04.10001.001',
    'Jane',
    'Smith',
    'Jane Smith',
    'Chief Executive Officer',
    'jane.smith@acmecorp.com',
    'https://linkedin.com/in/janesmith',
    'apify_linkedin'
);
```

---

## person_movement_history

**Purpose:** Tracks executive job changes, promotions, and contact loss.

**Primary Key:** `id` (auto-increment)

### Columns

| Column | Type | Required | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| id | integer | YES | auto | PK, sequence | Auto-increment ID |
| person_unique_id | text | YES | - | FK → people_master | Person being tracked |
| linkedin_url | text | NO | - | - | LinkedIn URL at detection |
| company_from_id | text | YES | - | FK → company_master | Source company |
| company_to_id | text | NO | - | FK → company_master | Destination company (null if lost) |
| title_from | text | YES | - | - | Previous title |
| title_to | text | NO | - | - | New title (null if lost contact) |
| movement_type | text | YES | - | company_change, title_change, contact_lost | Type of movement |
| detected_at | timestamp | YES | now() | - | Detection timestamp |
| raw_payload | jsonb | NO | - | - | Raw enrichment payload |
| created_at | timestamp | NO | now() | - | Record creation |

### Foreign Keys
- `person_unique_id` → `people_master.unique_id`
- `company_from_id` → `company_master.company_unique_id`
- `company_to_id` → `company_master.company_unique_id`

### Movement Types
- **company_change:** Person moved to new company
- **title_change:** Person promoted/changed title at same company
- **contact_lost:** Person no longer at company, destination unknown

### Example Insert

```sql
-- Track company change
INSERT INTO marketing.person_movement_history (
    person_unique_id,
    linkedin_url,
    company_from_id,
    company_to_id,
    title_from,
    title_to,
    movement_type,
    detected_at,
    raw_payload
) VALUES (
    '04.04.02.04.20001.001',
    'https://linkedin.com/in/janesmith',
    '04.04.01.04.30001.001',
    '04.04.01.04.30002.001',
    'Chief Executive Officer',
    'Chief Operating Officer',
    'company_change',
    NOW(),
    '{"source": "linkedin_scrape", "confidence": 0.95}'::jsonb
);
```

---

## person_scores

**Purpose:** Stores BIT (Buyer Intent Trigger) and confidence scores for contacts.

**Primary Key:** `id` (auto-increment)

**Unique Constraint:** One score record per `person_unique_id`

### Columns

| Column | Type | Required | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| id | integer | YES | auto | PK, sequence | Auto-increment ID |
| person_unique_id | text | YES | - | FK → people_master, UNIQUE | Person being scored |
| bit_score | integer | NO | - | 0-100 | Buyer Intent Trigger score |
| confidence_score | integer | NO | - | 0-100 | Confidence in data quality |
| calculated_at | timestamp | YES | now() | - | Score calculation time |
| score_factors | jsonb | NO | - | - | Factors contributing to score |
| created_at | timestamp | NO | now() | - | Record creation |
| updated_at | timestamp | NO | now() | - | Last update |

### Foreign Keys
- `person_unique_id` → `people_master.unique_id`

### Score Ranges
- **bit_score:** 0-100 (higher = more likely to buy)
- **confidence_score:** 0-100 (higher = better data quality)

### Example Insert

```sql
INSERT INTO marketing.person_scores (
    person_unique_id,
    bit_score,
    confidence_score,
    calculated_at,
    score_factors
) VALUES (
    '04.04.02.04.20001.001',
    75,
    92,
    NOW(),
    '{
        "company_growth": 20,
        "recent_funding": 15,
        "job_posting_activity": 10,
        "leadership_change": 30
    }'::jsonb
)
ON CONFLICT (person_unique_id)
DO UPDATE SET
    bit_score = EXCLUDED.bit_score,
    confidence_score = EXCLUDED.confidence_score,
    calculated_at = EXCLUDED.calculated_at,
    score_factors = EXCLUDED.score_factors,
    updated_at = NOW();
```

---

## company_events

**Purpose:** Tracks significant company events that impact BIT scores.

**Primary Key:** `id` (auto-increment)

### Columns

| Column | Type | Required | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| id | integer | YES | auto | PK, sequence | Auto-increment ID |
| company_unique_id | text | YES | - | FK → company_master | Company reference |
| event_type | text | NO | - | Valid event types | Type of event |
| event_date | date | NO | - | - | When event occurred |
| source_url | text | NO | - | - | Source URL for event |
| summary | text | NO | - | - | Event summary |
| detected_at | timestamp | YES | now() | - | When event was detected |
| impacts_bit | boolean | NO | true | - | Whether event affects BIT |
| bit_impact_score | integer | NO | - | -100 to 100 | Impact on BIT score |
| created_at | timestamp | NO | now() | - | Record creation |

### Foreign Keys
- `company_unique_id` → `company_master.company_unique_id`

### Event Types
- **funding:** Funding round received
- **acquisition:** Company acquired or acquiring
- **ipo:** Initial public offering
- **layoff:** Layoffs announced
- **leadership_change:** C-suite change
- **product_launch:** Major product launch
- **office_opening:** New office/expansion
- **other:** Other significant event

### BIT Impact Scores
- **Positive (1-100):** Funding, acquisition, product launch, office opening
- **Negative (-100 to -1):** Layoffs, leadership departures
- **Neutral (0):** Informational events

### Example Insert

```sql
INSERT INTO marketing.company_events (
    company_unique_id,
    event_type,
    event_date,
    source_url,
    summary,
    detected_at,
    impacts_bit,
    bit_impact_score
) VALUES (
    '04.04.01.04.30001.001',
    'funding',
    '2025-11-15',
    'https://techcrunch.com/acme-series-b',
    'Acme Corporation raises $50M Series B led by Sequoia Capital',
    NOW(),
    true,
    25
);
```

---

## Quick Reference

### Common Joins

#### Get all filled slots with person details
```sql
SELECT
    cs.company_slot_unique_id,
    cs.slot_type,
    cm.company_name,
    pm.full_name,
    pm.title,
    pm.email,
    cs.filled_at,
    cs.confidence_score
FROM marketing.company_slot cs
JOIN marketing.company_master cm ON cs.company_unique_id = cm.company_unique_id
JOIN marketing.people_master pm ON cs.person_unique_id = pm.unique_id
WHERE cs.is_filled = true;
```

#### Get company with all slots and current scores
```sql
SELECT
    cm.company_name,
    cs.slot_type,
    pm.full_name,
    pm.email,
    ps.bit_score,
    ps.confidence_score,
    cs.last_refreshed_at
FROM marketing.company_master cm
JOIN marketing.company_slot cs ON cm.company_unique_id = cs.company_unique_id
LEFT JOIN marketing.people_master pm ON cs.person_unique_id = pm.unique_id
LEFT JOIN marketing.person_scores ps ON pm.unique_id = ps.person_unique_id
WHERE cm.company_unique_id = '04.04.01.04.30001.001'
ORDER BY cs.slot_type;
```

#### Track person movement history
```sql
SELECT
    pm.full_name,
    pmh.movement_type,
    cm_from.company_name AS from_company,
    cm_to.company_name AS to_company,
    pmh.title_from,
    pmh.title_to,
    pmh.detected_at
FROM marketing.person_movement_history pmh
JOIN marketing.people_master pm ON pmh.person_unique_id = pm.unique_id
JOIN marketing.company_master cm_from ON pmh.company_from_id = cm_from.company_unique_id
LEFT JOIN marketing.company_master cm_to ON pmh.company_to_id = cm_to.company_unique_id
WHERE pm.unique_id = '04.04.02.04.20001.001'
ORDER BY pmh.detected_at DESC;
```

#### Get companies with recent high-impact events
```sql
SELECT
    cm.company_name,
    ce.event_type,
    ce.summary,
    ce.bit_impact_score,
    ce.event_date
FROM marketing.company_events ce
JOIN marketing.company_master cm ON ce.company_unique_id = cm.company_unique_id
WHERE ce.impacts_bit = true
  AND ce.bit_impact_score > 20
  AND ce.detected_at >= NOW() - INTERVAL '30 days'
ORDER BY ce.bit_impact_score DESC, ce.detected_at DESC;
```

### Typical Insert Order

1. **company_master** - Insert validated company
2. **company_slot** - Create executive slots (CEO, CFO, HR)
3. **people_master** - Insert discovered executive
4. **company_slot** - Update slot with person_unique_id
5. **person_scores** - Calculate initial scores
6. **company_events** - Track any relevant events
7. **person_movement_history** - Track future changes

### Barton ID Allocation

| Entity | Schema ID | Format | Example |
|--------|-----------|--------|---------|
| Company | 01 | 04.04.01.XX.XXXXX.XXX | 04.04.01.04.30001.001 |
| Person | 02 | 04.04.02.XX.XXXXX.XXX | 04.04.02.04.20001.001 |
| Slot | 05 | 04.04.05.XX.XXXXX.XXX | 04.04.05.04.10001.001 |

### State Codes

Valid states for company_master.address_state:
- PA (Pennsylvania)
- VA (Virginia)
- MD (Maryland)
- OH (Ohio)
- WV (West Virginia)
- KY (Kentucky)

### Slot Types

Valid slot_type values:
- CEO
- CFO
- HR

### Movement Types

Valid movement_type values:
- company_change
- title_change
- contact_lost

### Event Types

Valid event_type values:
- funding
- acquisition
- ipo
- layoff
- leadership_change
- product_launch
- office_opening
- other
