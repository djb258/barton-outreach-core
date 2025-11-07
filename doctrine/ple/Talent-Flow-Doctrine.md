# Talent Flow Doctrine — People Movement Detection Spoke
## Barton Doctrine Framework | SVG-PLE Marketing Core

**Document ID**: `01.04.02.04.20000.001`
**Version**: 1.0.0
**Last Updated**: 2025-11-07
**Altitude**: 20,000 ft (Category / Spoke Layer)
**Role**: Movement Detection Spoke feeding BIT Axle
**Status**: Active | Production Ready

---

## Section 1: Purpose and Doctrine Position

### Overview

**Talent Flow** is a critical spoke in the Shenandoah Valley Group Perpetual Lead Engine (SVG-PLE), responsible for detecting, classifying, and tracking people movement events across companies. As a spoke, Talent Flow feeds high-value intelligence to the BIT (Buyer Intent Tool) axle, which converts movement events into actionable buyer intent scores.

### Position in SVG-PLE Architecture

```
┌──────────────────────────────────────────────────┐
│           SVG-PLE Architecture                    │
└──────────────────────────────────────────────────┘

HUB (Core Intelligence)
└─▶ People Database
    ├── people.contact (individual records)
    ├── people.contact_employment (employment history)
    └── marketing.company_master (company records)

SPOKE 1: TALENT FLOW ← YOU ARE HERE
└─▶ People movement detection and classification
    ├── Enrichment agents (LinkedIn, Apify, Abacus)
    ├── Movement classification (hire, departure, promotion, transfer)
    ├── Confidence scoring (0-100)
    └── Event creation for BIT

SPOKE 2: Renewal Intelligence
└─▶ Contract expiration tracking

SPOKE 3: Compliance Monitor
└─▶ Regulatory event detection

AXLE (BIT)
└─▶ Converts Talent Flow events → Intent scores
    ├── executive_movement rule (40 points, 365 day decay)
    └── Triggers outreach workflows

WHEEL (Lead Cycles)
└─▶ Outreach automation based on BIT scores
```

### Core Function

Talent Flow transforms **raw LinkedIn/enrichment data** into **classified movement events**:

- **Input**: LinkedIn profile updates, enrichment agent results, employment changes
- **Processing**: Classify movement type, assign confidence score, determine business impact
- **Output**: Structured movement event (hire/departure/promotion/transfer)
- **Action**: Trigger BIT event creation for high-impact movements (e.g., new CFO)

### Business Value

1. **Early Detection**: Identify executive changes within 24-48 hours of LinkedIn update
2. **Contextual Intelligence**: Know WHY a company is in flux (new CFO = vendor reevaluation)
3. **Competitive Advantage**: Reach out before competitors notice the change
4. **Automated Enrichment**: No manual LinkedIn stalking required
5. **Data Quality**: Confidence scoring ensures only high-quality signals reach BIT

### Key Metrics

- **Detection Speed**: 24-48 hours from LinkedIn update to movement record
- **Confidence Threshold**: Minimum 70/100 for BIT event creation
- **Movement Types**: 4 classifications (hire, departure, promotion, transfer)
- **Target Roles**: CFO, CEO, HR Director, VP HR (high-impact positions)
- **Annual Volume**: ~500-1000 movements tracked per year (based on 200-500 target companies)

---

## Section 2: Logical Flow (Hub → Talent Flow → BIT)

### End-to-End Pipeline

```
┌────────────────────────────────────────────────────────────────┐
│  STAGE 1: LinkedIn Profile Update (External Event)             │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
        Jane Smith's LinkedIn profile updated:
        "Excited to announce I've joined TechStart Inc as CFO!"
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│  STAGE 2: Enrichment Agent Detection                           │
│  (Apify, Abacus, or Firecrawl)                                 │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
        Agent scrapes profile and detects:
        - Previous: CFO at OldCorp (2020-2025)
        - Current: CFO at TechStart Inc (2025-present)
        - Change detected: 2025-11-01
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│  STAGE 3: Enrichment Log Entry                                 │
│  (marketing.data_enrichment_log)                               │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
        INSERT INTO marketing.data_enrichment_log (
          enrichment_id: 'ENRICH-2025-11-001',
          company_unique_id: '04.04.02.04.30000.042',
          agent_name: 'Apify',
          enrichment_type: 'executive',
          status: 'success',
          movement_detected: true,
          movement_type: 'executive_hire',
          data_quality_score: 95,
          result_data: { ... Jane Smith details ... },
          completed_at: '2025-11-01 14:30:00'
        );
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│  STAGE 4: Talent Flow Movement Creation                        │
│  (talent_flow.movements)                                       │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
        INSERT INTO talent_flow.movements (
          movement_id: (auto-generated),
          contact_id: 12345,
          old_company_id: 999 (OldCorp),
          new_company_id: 042 (TechStart),
          movement_type: 'hire',
          old_title: 'CFO',
          new_title: 'Chief Financial Officer',
          detected_source: 'Apify - LinkedIn',
          confidence_score: 95.0,
          detected_at: '2025-11-01 14:30:00',
          processed: false
        );
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│  STAGE 5: Movement Classification & BIT Eligibility            │
│  (talent_flow.classify_movement_impact())                      │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
        Classification Logic:
        - Title: "CFO" → High Impact Role ✅
        - Movement Type: "hire" → New Executive ✅
        - Confidence: 95 → Above 70 threshold ✅
        - Result: ELIGIBLE for BIT event
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│  STAGE 6: BIT Event Creation (Automatic Trigger)               │
│  (bit.events)                                                  │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
        INSERT INTO bit.events (
          event_id: '01.04.03.04.10000.045',
          company_unique_id: '04.04.02.04.30000.042',
          event_type: 'executive_movement',
          rule_reference_id: '01.04.03.04.10000.101',
          event_payload: { ... movement details ... },
          detected_at: '2025-11-01 14:30:00',
          data_quality_score: 95
        );
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│  STAGE 7: Intent Score Calculation                             │
│  (bit.scores view)                                             │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
        Score Calculation:
        - Base Weight: 40 points (executive_movement rule)
        - Decay Factor: 1.0 (0 days since event)
        - Quality Modifier: 0.95 (95% confidence)
        - Final Score: 40 * 1.0 * 0.95 = 38 points
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│  STAGE 8: Outreach Decision                                    │
│  (Wheel Layer - if score triggers threshold)                   │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
        38 points → Cold category (0-49)
        Action: Monitor only (no immediate outreach)

        Note: If additional signals arrive (renewal window,
        tech stack change), cumulative score may reach
        Warm (50-79) or Hot (80-100) thresholds.
```

### Data Flow Summary

| Stage | System Component | Data Format | Timing |
|-------|------------------|-------------|--------|
| 1 | LinkedIn | Profile update | Real-time |
| 2 | Enrichment Agent | API response | 24-48h |
| 3 | Enrichment Log | JSONB record | Immediate |
| 4 | Talent Flow | Movement record | Immediate (trigger) |
| 5 | Classification | Impact assessment | Immediate (function) |
| 6 | BIT Event | Structured event | Immediate (trigger) |
| 7 | Score Calculation | Real-time view | Immediate (query) |
| 8 | Outreach Decision | Workflow trigger | Based on score |

---

## Section 3: Event Classification Table

### Movement Types

Talent Flow classifies all people movements into 4 primary types:

| Movement Type | Definition | Example | BIT Impact |
|---------------|------------|---------|------------|
| **hire** | Person joins new company (from external org) | Jane Smith: OldCorp → TechStart | High (if executive) |
| **departure** | Person leaves company (destination unknown or external) | John Doe: TechStart → Unemployed/Unknown | Medium |
| **promotion** | Person moves up within same company | Sarah Lee: Manager → VP @ TechStart | Low-Medium |
| **transfer** | Person moves between divisions/locations (same company) | Mike Chen: NYC Office → SF Office @ TechStart | Low |

### Impact Scoring Matrix

**When does a movement create a BIT event?**

| Role Level | Movement Type | Confidence Score | BIT Event Created? | BIT Score Impact |
|------------|---------------|------------------|-------------------|------------------|
| C-Suite (CEO, CFO, COO) | hire | ≥ 70 | ✅ Yes | 40 points |
| C-Suite | departure | ≥ 70 | ✅ Yes | 35 points |
| C-Suite | promotion | ≥ 70 | ✅ Yes | 25 points |
| C-Suite | transfer | Any | ❌ No | N/A |
| VP/Director | hire | ≥ 80 | ✅ Yes | 30 points |
| VP/Director | departure | ≥ 80 | ⚠️ Maybe | 20 points |
| VP/Director | promotion | ≥ 80 | ❌ No | N/A |
| Manager/IC | Any | Any | ❌ No | N/A |

**Legend**:
- ✅ Yes: Always creates BIT event (if confidence threshold met)
- ⚠️ Maybe: Creates BIT event only if specific criteria met (e.g., HR Director departure)
- ❌ No: Does not create BIT event

### High-Impact Titles

These titles automatically qualify for BIT event creation (if confidence ≥ 70):

**Tier 1 (C-Suite)**:
- Chief Executive Officer (CEO)
- Chief Financial Officer (CFO)
- Chief Operating Officer (COO)
- Chief Human Resources Officer (CHRO)
- Chief Technology Officer (CTO)

**Tier 2 (VP/Director - HR Focus)**:
- Vice President of Human Resources
- VP of People Operations
- Director of Human Resources
- Head of Talent Acquisition
- VP of Total Rewards

**Tier 3 (Specialized)**:
- VP of Payroll
- Director of Compliance
- Head of Benefits

### Confidence Score Calibration

Confidence scores (0-100) are assigned based on data source quality:

| Score Range | Quality Level | Source Examples |
|-------------|---------------|-----------------|
| 90-100 | **Verified** | Official company announcement, verified LinkedIn update with date |
| 80-89 | **High** | LinkedIn profile change with confirmation from 2+ sources |
| 70-79 | **Medium** | LinkedIn profile change, single source verification |
| 60-69 | **Low** | Unverified profile change, job board posting |
| 0-59 | **Unreliable** | Rumor, speculation (not recorded in Talent Flow) |

**Threshold**: Minimum 70 confidence required for BIT event creation.

### Movement Detection Sources

| Source | Reliability | Typical Confidence | Cost |
|--------|-------------|-------------------|------|
| **Apify (LinkedIn scraper)** | High | 85-95 | Medium |
| **Abacus (executive tracking)** | Very High | 90-100 | High |
| **Firecrawl (web scraping)** | Medium | 70-85 | Low |
| **Manual entry** | Variable | 60-100 | Free |
| **Company announcement (press release)** | Very High | 95-100 | Free |

---

## Section 4: Schema Explanation

### Database Structure

**Schema**: `talent_flow` (dedicated namespace for movement tracking)

**Location**: `doctrine/schemas/talent_flow-schema.sql`

### Table: talent_flow.movements

**Purpose**: Central repository for all detected people movements across companies

#### Column Breakdown

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| `movement_id` | BIGSERIAL | Auto-incrementing primary key | PRIMARY KEY |
| `contact_id` | BIGINT | Links to people.contact | FK to people.contact, NOT NULL |
| `old_company_id` | VARCHAR(50) | Previous company (Barton ID) | FK to marketing.company_master, nullable |
| `new_company_id` | VARCHAR(50) | New company (Barton ID) | FK to marketing.company_master, nullable |
| `movement_type` | VARCHAR(20) | Type of movement | CHECK IN ('hire','departure','promotion','transfer') |
| `old_title` | TEXT | Previous job title | nullable |
| `new_title` | TEXT | New job title | nullable |
| `detected_source` | TEXT | Where movement was detected | NOT NULL |
| `confidence_score` | NUMERIC(5,2) | Confidence 0-100 | CHECK >= 0 AND <= 100 |
| `detected_at` | TIMESTAMPTZ | When movement detected | DEFAULT NOW() |
| `effective_date` | DATE | Actual movement date (if known) | nullable |
| `processed` | BOOLEAN | Has been sent to BIT? | DEFAULT FALSE |
| `payload` | JSONB | Additional data from source | nullable |
| `created_at` | TIMESTAMPTZ | Record creation timestamp | DEFAULT NOW() |
| `updated_at` | TIMESTAMPTZ | Last update timestamp | DEFAULT NOW() |

#### Indexes

- **Primary Key**: `movement_id`
- **Foreign Keys**: `contact_id`, `old_company_id`, `new_company_id`
- **Search Indexes**:
  - `idx_movements_contact` on `contact_id`
  - `idx_movements_new_company` on `new_company_id`
  - `idx_movements_type` on `movement_type`
  - `idx_movements_detected_at` on `detected_at DESC`
  - `idx_movements_processed` on `processed`
- **JSONB Index**: `idx_movements_payload` (GIN index for payload queries)

### Table: talent_flow.movement_audit

**Purpose**: Historical audit trail for movement record changes

#### Columns

| Column | Type | Description |
|--------|------|-------------|
| `audit_id` | BIGSERIAL | Primary key |
| `movement_id` | BIGINT | Links to movements table |
| `operation` | VARCHAR(10) | INSERT, UPDATE, or DELETE |
| `old_data` | JSONB | Record before change |
| `new_data` | JSONB | Record after change |
| `changed_by` | VARCHAR(100) | User/system that made change |
| `changed_at` | TIMESTAMPTZ | When change occurred |

### View: talent_flow.executive_movements

**Purpose**: Pre-filtered view of high-impact movements (C-Suite + VP/Director)

**Logic**:
```sql
SELECT m.*
FROM talent_flow.movements m
WHERE (
  m.new_title ~* 'chief|ceo|cfo|coo|chro|cto|vp|vice president|director'
  OR m.old_title ~* 'chief|ceo|cfo|coo|chro|cto|vp|vice president|director'
)
AND m.confidence_score >= 70
ORDER BY m.detected_at DESC;
```

### Key Design Decisions

1. **Nullable Company IDs**: Allows tracking "unknown" departures (person left, destination unknown)
2. **Confidence Score**: Enables threshold-based filtering (e.g., only send 70+ to BIT)
3. **Processed Flag**: Prevents duplicate BIT event creation
4. **JSONB Payload**: Stores raw enrichment data for debugging/auditing
5. **Separate Audit Table**: Immutable log of all changes for compliance

---

## Section 5: Trigger Logic → Insert BIT Event

### Automatic BIT Event Creation

When a high-impact movement is detected, Talent Flow automatically creates a BIT event to influence buyer intent scores.

### Trigger Function: talent_flow.create_bit_event_from_movement()

**Purpose**: Automatically create BIT events for executive movements

**Trigger Timing**: AFTER INSERT OR UPDATE on `talent_flow.movements`

**Trigger Conditions** (all must be true):
1. Movement is NEW (processed = FALSE)
2. Confidence score ≥ 70
3. Movement type is 'hire' or 'departure'
4. New or old title contains C-Suite/VP/Director keywords
5. No duplicate BIT event already exists for this movement

### Pseudocode Logic

```
ON INSERT OR UPDATE of talent_flow.movements:
  IF NEW.processed = FALSE THEN
    -- Check if this is a high-impact movement
    IF NEW.confidence_score >= 70 THEN
      IF NEW.movement_type IN ('hire', 'departure') THEN
        IF is_executive_title(NEW.new_title) OR is_executive_title(NEW.old_title) THEN

          -- Determine target company (where intent is created)
          target_company = CASE
            WHEN NEW.movement_type = 'hire' THEN NEW.new_company_id
            WHEN NEW.movement_type = 'departure' THEN NEW.old_company_id
          END;

          -- Create BIT event
          INSERT INTO bit.events (
            company_unique_id = target_company,
            event_type = 'executive_movement',
            rule_reference_id = '01.04.03.04.10000.101',
            event_payload = jsonb_build_object(
              'movement_id', NEW.movement_id,
              'contact_id', NEW.contact_id,
              'movement_type', NEW.movement_type,
              'old_title', NEW.old_title,
              'new_title', NEW.new_title,
              'confidence_score', NEW.confidence_score
            ),
            detected_at = NEW.detected_at,
            data_quality_score = NEW.confidence_score
          );

          -- Mark movement as processed
          UPDATE talent_flow.movements
          SET processed = TRUE
          WHERE movement_id = NEW.movement_id;

        END IF;
      END IF;
    END IF;
  END IF;
```

### SQL Implementation

```sql
CREATE OR REPLACE FUNCTION talent_flow.create_bit_event_from_movement()
RETURNS TRIGGER AS $$
DECLARE
  target_company VARCHAR(50);
BEGIN
  -- Only process unprocessed movements
  IF NEW.processed = FALSE AND NEW.confidence_score >= 70 THEN

    -- Check if movement type qualifies
    IF NEW.movement_type IN ('hire', 'departure') THEN

      -- Check if title is executive-level
      IF (NEW.new_title ~* 'chief|ceo|cfo|coo|chro|cto|vp|vice president|director|head of') OR
         (NEW.old_title ~* 'chief|ceo|cfo|coo|chro|cto|vp|vice president|director|head of') THEN

        -- Determine target company for BIT event
        target_company := CASE
          WHEN NEW.movement_type = 'hire' THEN NEW.new_company_id
          WHEN NEW.movement_type = 'departure' THEN NEW.old_company_id
        END;

        -- Create BIT event (if not already exists)
        INSERT INTO bit.events (
          company_unique_id,
          event_type,
          rule_reference_id,
          event_payload,
          detected_at,
          data_quality_score
        )
        SELECT
          target_company,
          'executive_movement',
          '01.04.03.04.10000.101',
          jsonb_build_object(
            'movement_id', NEW.movement_id,
            'contact_id', NEW.contact_id,
            'movement_type', NEW.movement_type,
            'old_title', NEW.old_title,
            'new_title', NEW.new_title,
            'old_company_id', NEW.old_company_id,
            'new_company_id', NEW.new_company_id,
            'confidence_score', NEW.confidence_score,
            'detected_source', NEW.detected_source
          ),
          NEW.detected_at,
          NEW.confidence_score::INTEGER
        WHERE target_company IS NOT NULL
          AND NOT EXISTS (
            -- Prevent duplicate BIT events
            SELECT 1 FROM bit.events
            WHERE event_payload->>'movement_id' = NEW.movement_id::TEXT
          );

        -- Mark as processed
        NEW.processed := TRUE;

      END IF;
    END IF;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### Example Execution Flow

**Scenario**: New CFO hired at TechStart Inc

1. **Movement Record Created**:
```sql
INSERT INTO talent_flow.movements (
  contact_id: 12345,
  old_company_id: '04.04.02.04.30000.999',
  new_company_id: '04.04.02.04.30000.042',
  movement_type: 'hire',
  old_title: 'CFO',
  new_title: 'Chief Financial Officer',
  detected_source: 'Apify - LinkedIn',
  confidence_score: 95.0,
  detected_at: '2025-11-01 14:30:00'
);
```

2. **Trigger Evaluates**:
   - ✅ processed = FALSE
   - ✅ confidence_score = 95 (≥ 70)
   - ✅ movement_type = 'hire'
   - ✅ new_title contains "Chief" (executive keyword)
   - ✅ No duplicate BIT event exists

3. **BIT Event Created**:
```sql
INSERT INTO bit.events (
  event_id: '01.04.03.04.10000.045',
  company_unique_id: '04.04.02.04.30000.042',
  event_type: 'executive_movement',
  rule_reference_id: '01.04.03.04.10000.101',
  event_payload: {
    "movement_id": 123,
    "contact_id": 12345,
    "movement_type": "hire",
    "old_title": "CFO",
    "new_title": "Chief Financial Officer",
    "confidence_score": 95.0
  },
  detected_at: '2025-11-01 14:30:00',
  data_quality_score: 95
);
```

4. **Movement Marked Processed**:
```sql
UPDATE talent_flow.movements
SET processed = TRUE
WHERE movement_id = 123;
```

---

## Section 6: Numbering + ID Examples

### Barton Doctrine ID Format

**Talent Flow Prefix**: `01.04.02.04.20000`

Breaking down the prefix:
- `01` = Subhive (Marketing/Sales)
- `04` = Application (SVG-PLE)
- `02` = Layer (Category - 20,000 ft)
- `04` = Schema (Talent Flow spoke)
- `20000` = Base sequence for Talent Flow entities

### ID Ranges (Reserved but Not Used in Current Schema)

**Note**: Current schema uses BIGSERIAL for `movement_id` instead of Barton ID format. Future enhancement may add Barton IDs for cross-system referencing.

| Entity Type | ID Pattern | Range | Example | Usage |
|-------------|-----------|-------|---------|-------|
| Movement Events | `01.04.02.04.20000.###` | 001-999 | `01.04.02.04.20000.001` | Future |
| Audit Logs | `01.04.02.04.20000.8##` | 801-899 | `01.04.02.04.20000.801` | Future |
| Configuration | `01.04.02.04.20000.9##` | 901-999 | `01.04.02.04.20000.901` | Future |

### Current ID Strategy

**movement_id**: Uses PostgreSQL BIGSERIAL (auto-incrementing integer)
- **Rationale**: Simpler for high-volume inserts, easier joins
- **Format**: 1, 2, 3, ..., 999999+
- **Collision Risk**: None (sequence-based)

**Alternative**: Future migration to Barton ID format could use:
```sql
movement_unique_id VARCHAR(50) DEFAULT CONCAT(
  '01.04.02.04.20000.',
  LPAD(NEXTVAL('talent_flow.movement_id_seq')::TEXT, 3, '0')
)
```

### Cross-System ID References

When Talent Flow creates BIT events, it uses:

| System | ID Field | Format | Example |
|--------|----------|--------|---------|
| **Talent Flow** | movement_id | BIGSERIAL | 12345 |
| **People Hub** | contact_id | BIGINT | 67890 |
| **Company Hub** | company_unique_id | Barton ID | `04.04.02.04.30000.042` |
| **BIT Events** | event_id | Barton ID | `01.04.03.04.10000.045` |

**Link**: BIT event payload contains `movement_id` for traceability:
```json
{
  "movement_id": 12345,
  "contact_id": 67890,
  "new_company_id": "04.04.02.04.30000.042"
}
```

### Document ID Example

**This Doctrine Document**: `01.04.02.04.20000.001`
- Represents: Talent Flow Doctrine v1.0.0
- Altitude: 20,000 ft (Category layer)
- Schema: 04 (Talent Flow spoke)

---

## Section 7: Relationship to PLE and Outreach

### SVG-PLE Ecosystem Integration

```
┌─────────────────────────────────────────────────────────┐
│                     HUB (Core Data)                      │
│  • people.contact (individual records)                  │
│  • people.contact_employment (job history)              │
│  • marketing.company_master (companies)                 │
└─────────────────────────────────────────────────────────┘
                            ▲
                            │ (People data flows FROM hub)
                            │
┌─────────────────────────────────────────────────────────┐
│              TALENT FLOW SPOKE (You Are Here)            │
│  • talent_flow.movements (movement detection)           │
│  • Enrichment agents (Apify, Abacus, Firecrawl)        │
│  • Classification logic (hire/departure/promotion)      │
│  • Confidence scoring (0-100)                           │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼ (Movement events flow TO axle)
┌─────────────────────────────────────────────────────────┐
│                   BIT AXLE (Intent Scoring)              │
│  • bit.events (receives movement events)                │
│  • bit.scores (calculates intent scores)                │
│  • executive_movement rule (40 points)                  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼ (Scores flow TO wheel)
┌─────────────────────────────────────────────────────────┐
│                  OUTREACH LAYER (Wheel)                  │
│  • Hot leads (80-100): Immediate outreach               │
│  • Warm leads (50-79): Nurture campaign                 │
│  • Cold leads (0-49): Monitor only                      │
└─────────────────────────────────────────────────────────┘
```

### Data Flow Patterns

#### Pattern 1: New Hire Detection (Most Common)

1. **Hub → Enrichment**: Apify scrapes LinkedIn for target companies
2. **Enrichment → Log**: `marketing.data_enrichment_log.movement_detected = TRUE`
3. **Log → Talent Flow**: Trigger creates `talent_flow.movements` record
4. **Talent Flow → BIT**: Trigger creates `bit.events` record (if executive-level)
5. **BIT → Scores**: View calculates real-time intent score
6. **Scores → Outreach**: If score ≥ 50, enroll in campaign

#### Pattern 2: Departure Detection

1. **LinkedIn Update**: Jane Smith's profile shows "Former CFO at TechStart"
2. **Enrichment Agent**: Detects title change (CFO → Unemployed/Unknown)
3. **Talent Flow**: Creates movement record (type: 'departure')
4. **BIT Event**: Created for TechStart (company losing CFO)
5. **Intent Score**: TechStart gets 35 points (departure rule)
6. **Outreach Logic**: Lower priority than hire, but still tracked

#### Pattern 3: Promotion (Lower Priority)

1. **LinkedIn Update**: "Excited to announce my promotion to VP!"
2. **Enrichment Agent**: Detects title change within same company
3. **Talent Flow**: Creates movement record (type: 'promotion')
4. **BIT Event**: Created only if C-Suite promotion (rare)
5. **Intent Score**: Lower impact (25 points)

### Integration with Other Spokes

| Spoke | Integration Type | Data Exchange |
|-------|------------------|---------------|
| **Renewal Intelligence** | Complementary | Combined signals (new CFO + renewal window) create high intent |
| **Compliance Monitor** | Parallel | DOL violation + executive departure = double signal |
| **Enrichment Tracking** | Source | Talent Flow reads from `marketing.data_enrichment_log` |

### Outreach Workflow Example

**Scenario**: TechStart Inc hires new CFO (Jane Smith)

1. **Day 0**: Movement detected, BIT score = 38 points (Cold)
2. **Day 30**: Renewal window opens (90d), BIT score = 79 points (Warm)
3. **Day 60**: Tech stack change detected, BIT score = 89 points (Hot)
4. **Day 61**: Sales rep receives alert: "TechStart Inc - Hot Lead (89 pts)"
5. **Outreach Email**:
   ```
   Subject: Congrats on your new role, Jane - Quick question about Feb renewal

   Hi Jane,

   Congratulations on joining TechStart as CFO! I saw the announcement last month...
   ```

**Result**: Perfect timing, personalized context, high conversion likelihood

---

## Section 8: Audit + Data Lineage Rules

### Barton Doctrine Compliance

#### Data Quality Standards

✅ **Requirement**: All movements must have confidence score ≥ 60 to be recorded
✅ **Enforcement**: Application-level validation (not database constraint to allow low-confidence logging for debugging)
✅ **BIT Threshold**: Only movements with confidence ≥ 70 create BIT events

```sql
-- Validation check (monthly audit)
SELECT COUNT(*) AS low_confidence_movements
FROM talent_flow.movements
WHERE confidence_score < 60;
-- Expected: 0 in production (may have test data)
```

#### Audit Trail Requirements

✅ **Requirement**: All changes to movement records must be logged
✅ **Implementation**: Audit trigger on `talent_flow.movements`
✅ **Storage**: `talent_flow.movement_audit` (immutable append-only log)

```sql
-- Audit trail query
SELECT * FROM talent_flow.movement_audit
WHERE movement_id = 12345
ORDER BY changed_at DESC;
```

### Data Lineage Tracking

Every movement record must be traceable back to its source:

**Required Fields**:
1. `detected_source`: Where was this movement found? (e.g., "Apify - LinkedIn")
2. `payload`: Raw data from source (JSONB) for verification
3. `created_at`: When record was created
4. `detected_at`: When movement actually occurred (if known)

**Lineage Chain**:
```
LinkedIn Profile Update
  └─▶ Apify Scrape (2025-11-01 14:30:00)
      └─▶ marketing.data_enrichment_log (enrichment_id: ENRICH-2025-11-001)
          └─▶ talent_flow.movements (movement_id: 12345)
              └─▶ bit.events (event_id: 01.04.03.04.10000.045)
                  └─▶ bit.scores (company score: 38 → 79 → 89)
                      └─▶ Outreach campaign enrollment
```

### Audit Rules

#### Monthly Audit Checklist

Run these queries monthly to verify Talent Flow data quality:

**1. Orphaned Movements (no contact)**
```sql
SELECT COUNT(*) AS orphaned_movements
FROM talent_flow.movements m
LEFT JOIN people.contact c ON m.contact_id = c.contact_id
WHERE c.contact_id IS NULL;
-- Expected: 0
```

**2. Duplicate Detection (same person, same movement, same day)**
```sql
SELECT contact_id, movement_type, DATE(detected_at), COUNT(*)
FROM talent_flow.movements
GROUP BY contact_id, movement_type, DATE(detected_at)
HAVING COUNT(*) > 1;
-- Expected: 0 rows
```

**3. Confidence Distribution**
```sql
SELECT
  CASE
    WHEN confidence_score >= 90 THEN '90-100 (Verified)'
    WHEN confidence_score >= 80 THEN '80-89 (High)'
    WHEN confidence_score >= 70 THEN '70-79 (Medium)'
    ELSE '0-69 (Low)'
  END AS confidence_tier,
  COUNT(*) AS movement_count
FROM talent_flow.movements
WHERE detected_at >= NOW() - INTERVAL '30 days'
GROUP BY confidence_tier
ORDER BY confidence_tier DESC;
-- Expected: Majority in 80+ range
```

**4. Unprocessed Executive Movements**
```sql
SELECT COUNT(*) AS unprocessed_executives
FROM talent_flow.movements
WHERE processed = FALSE
  AND confidence_score >= 70
  AND (new_title ~* 'chief|ceo|cfo|coo|chro|cto|vp|vice president|director'
       OR old_title ~* 'chief|ceo|cfo|coo|chro|cto|vp|vice president|director');
-- Expected: 0 (all should auto-process via trigger)
```

**5. BIT Event Creation Success Rate**
```sql
SELECT
  COUNT(*) AS eligible_movements,
  SUM(CASE WHEN processed = TRUE THEN 1 ELSE 0 END) AS processed_count,
  ROUND(100.0 * SUM(CASE WHEN processed = TRUE THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate
FROM talent_flow.movements
WHERE confidence_score >= 70
  AND movement_type IN ('hire', 'departure')
  AND (new_title ~* 'chief|ceo|cfo|coo|chro|cto|vp|vice president|director'
       OR old_title ~* 'chief|ceo|cfo|coo|chro|cto|vp|vice president|director');
-- Expected: success_rate = 100%
```

### Alert Thresholds

Configure alerts for these conditions:

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Orphaned movements | > 0 | Investigate contact_id references |
| Duplicate movements | > 5 in 7 days | Review enrichment agent logic |
| Low confidence movements | > 30% of total | Review data sources |
| Unprocessed executives | > 10 | Check trigger function |
| BIT creation success rate | < 95% | Debug trigger/BIT schema |

### Compliance Automation

**Auto-Compliance Script**: `infra/scripts/compliance:complete`

Runs all compliance checks and generates report:
```bash
npm run compliance:complete -- --module=talent_flow
```

Output: `audit_results/talent_flow-compliance-YYYY-MM-DD.json`

---

## Section 9: Example Scenario - HR Director Transfer

### Real-World Scenario

**Person**: Sarah Martinez
**Title**: Director of Human Resources
**Event**: Transfer from ABC Corporation (old client) to XYZ Industries (target prospect)
**Detection**: November 1, 2025
**Source**: Apify LinkedIn scraper
**Confidence**: 92/100

### Timeline Walkthrough

#### Day 0: LinkedIn Update (Nov 1, 2025, 9:00 AM)

**Sarah's LinkedIn Post**:
```
Excited to announce that I'm joining XYZ Industries as Director of HR!
After 4 amazing years at ABC Corporation, I'm ready for a new challenge.
Looking forward to building a world-class people team at XYZ!

#NewJob #HumanResources #PeopleOps
```

---

#### Day 0: Enrichment Agent Scrape (Nov 1, 2025, 2:00 PM)

**Apify LinkedIn Scraper** detects profile change:

**Previous State** (cached Oct 30, 2025):
```json
{
  "name": "Sarah Martinez",
  "current_position": {
    "title": "Director of Human Resources",
    "company": "ABC Corporation",
    "start_date": "2021-01-01",
    "location": "Boston, MA"
  }
}
```

**Current State** (scraped Nov 1, 2025):
```json
{
  "name": "Sarah Martinez",
  "current_position": {
    "title": "Director of HR",
    "company": "XYZ Industries",
    "start_date": "2025-11-01",
    "location": "Boston, MA"
  },
  "previous_positions": [
    {
      "title": "Director of Human Resources",
      "company": "ABC Corporation",
      "start_date": "2021-01-01",
      "end_date": "2025-10-31"
    }
  ]
}
```

**Change Detected**:
- ✅ Company changed: ABC Corporation → XYZ Industries
- ✅ Title updated: Director of Human Resources → Director of HR
- ✅ Movement type: **HIRE** (external company transfer)
- ✅ Confidence: 92/100 (verified via LinkedIn official update + post confirmation)

---

#### Day 0: Enrichment Log Entry (Nov 1, 2025, 2:05 PM)

```sql
INSERT INTO marketing.data_enrichment_log (
  enrichment_id,
  company_unique_id,
  agent_name,
  enrichment_type,
  status,
  movement_detected,
  movement_type,
  data_quality_score,
  result_data,
  started_at,
  completed_at
) VALUES (
  'ENRICH-2025-11-001',
  '04.04.02.04.30000.150', -- XYZ Industries
  'Apify',
  'executive',
  'success',
  TRUE,
  'executive_hire',
  92,
  '{
    "contact_id": 45678,
    "person_name": "Sarah Martinez",
    "old_company": "ABC Corporation",
    "new_company": "XYZ Industries",
    "old_title": "Director of Human Resources",
    "new_title": "Director of HR",
    "linkedin_url": "https://linkedin.com/in/sarah-martinez-hr",
    "start_date": "2025-11-01",
    "detection_method": "profile_comparison",
    "verification_sources": ["linkedin_post", "profile_update"],
    "confidence_breakdown": {
      "profile_verified": 95,
      "post_confirmation": 100,
      "date_accuracy": 90,
      "title_match": 85
    }
  }'::jsonb,
  '2025-11-01 14:00:00',
  '2025-11-01 14:05:00'
);
```

---

#### Day 0: Talent Flow Movement Record (Nov 1, 2025, 2:05:01 PM)

**Automatic Creation** (via enrichment → Talent Flow integration):

```sql
INSERT INTO talent_flow.movements (
  contact_id,
  old_company_id,
  new_company_id,
  movement_type,
  old_title,
  new_title,
  detected_source,
  confidence_score,
  detected_at,
  effective_date,
  processed,
  payload
) VALUES (
  45678, -- Sarah Martinez
  '04.04.02.04.30000.085', -- ABC Corporation
  '04.04.02.04.30000.150', -- XYZ Industries
  'hire',
  'Director of Human Resources',
  'Director of HR',
  'Apify - LinkedIn',
  92.0,
  '2025-11-01 14:05:00',
  '2025-11-01', -- Effective date from LinkedIn
  FALSE, -- Will be set to TRUE after BIT event creation
  '{
    "enrichment_id": "ENRICH-2025-11-001",
    "linkedin_url": "https://linkedin.com/in/sarah-martinez-hr",
    "verification_method": "linkedin_post",
    "post_text": "Excited to announce that I am joining XYZ Industries...",
    "previous_tenure_years": 4
  }'::jsonb
);

-- Returns movement_id: 12345
```

---

#### Day 0: Trigger Evaluation (Nov 1, 2025, 2:05:02 PM)

**Trigger**: `talent_flow.create_bit_event_from_movement()`

**Evaluation**:
1. ✅ `processed = FALSE`
2. ✅ `confidence_score = 92` (≥ 70 threshold)
3. ✅ `movement_type = 'hire'`
4. ✅ `new_title = 'Director of HR'` contains "Director" (executive keyword)
5. ✅ `target_company = new_company_id = '04.04.02.04.30000.150'` (XYZ Industries)
6. ✅ No duplicate BIT event exists

**Result**: ✅ CREATE BIT EVENT

---

#### Day 0: BIT Event Creation (Nov 1, 2025, 2:05:03 PM)

```sql
INSERT INTO bit.events (
  event_id,
  company_unique_id,
  event_type,
  rule_reference_id,
  event_payload,
  detected_at,
  data_quality_score
) VALUES (
  '01.04.03.04.10000.087', -- Auto-generated
  '04.04.02.04.30000.150', -- XYZ Industries (NEW company)
  'executive_movement',
  '01.04.03.04.10000.101', -- executive_movement rule (40 points, 365 day decay)
  '{
    "movement_id": 12345,
    "contact_id": 45678,
    "person_name": "Sarah Martinez",
    "movement_type": "hire",
    "old_title": "Director of Human Resources",
    "new_title": "Director of HR",
    "old_company_id": "04.04.02.04.30000.085",
    "old_company_name": "ABC Corporation",
    "new_company_id": "04.04.02.04.30000.150",
    "new_company_name": "XYZ Industries",
    "confidence_score": 92.0,
    "detected_source": "Apify - LinkedIn"
  }'::jsonb,
  '2025-11-01 14:05:00',
  92 -- Confidence score as data quality
);
```

**Movement Marked as Processed**:
```sql
UPDATE talent_flow.movements
SET processed = TRUE, updated_at = NOW()
WHERE movement_id = 12345;
```

---

#### Day 0: Intent Score Calculation (Nov 1, 2025, 2:05:04 PM)

**Query**: `SELECT * FROM bit.scores WHERE company_unique_id = '04.04.02.04.30000.150';`

**Calculation**:
```
Event: executive_movement
  - Base Weight: 40 points (from bit.rule_reference)
  - Days Since Event: 0
  - Decay Factor: 1.0 - (0 / 365) = 1.0
  - Quality Modifier: 92 / 100 = 0.92
  - Final Contribution: 40 * 1.0 * 0.92 = 36.8 points

Total Score: 36.8 points
Category: COLD (0-49)
```

**Result**:
```json
{
  "company_unique_id": "04.04.02.04.30000.150",
  "company_name": "XYZ Industries",
  "total_score": 36.8,
  "score_category": "Cold",
  "event_count": 1,
  "latest_event_date": "2025-11-01 14:05:00",
  "score_breakdown": {
    "executive_movement": {
      "event_id": "01.04.03.04.10000.087",
      "base_weight": 40,
      "decay_factor": 1.0,
      "quality_modifier": 0.92,
      "final_contribution": 36.8
    }
  }
}
```

**Outreach Decision**: ❌ No immediate action (score below 50 threshold)

---

#### Day 30: Additional Signal (Renewal Window Opens)

**Scenario**: XYZ Industries has a contract expiring in 90 days

**New BIT Event**:
```sql
INSERT INTO bit.events (
  event_id: '01.04.03.04.10000.088',
  company_unique_id: '04.04.02.04.30000.150',
  event_type: 'renewal_window_90d',
  rule_reference_id: '01.04.03.04.10000.103', -- renewal_window_90d (45 points)
  detected_at: '2025-12-01 00:00:00',
  data_quality_score: 100
);
```

**New Score Calculation**:
```
Event 1: executive_movement
  - Base: 40, Days: 30, Decay: 0.918, Quality: 0.92
  - Contribution: 40 * 0.918 * 0.92 = 33.74 points

Event 2: renewal_window_90d
  - Base: 45, Days: 0, Decay: 1.0, Quality: 1.0
  - Contribution: 45 * 1.0 * 1.0 = 45 points

Total Score: 33.74 + 45 = 78.74 points
Category: WARM (50-79)
```

**Outreach Decision**: ✅ Enroll in nurture campaign
- **Target**: Sarah Martinez (new HR Director)
- **Message**: "Congrats on your new role! We noticed your contract renewal is coming up..."
- **Timing**: 7-day cadence

---

#### Day 60: Outreach Results

**Campaign Performance**:
- ✅ Email opened within 2 hours
- ✅ Response received same day
- ✅ Meeting scheduled for next week
- ✅ Pipeline opportunity: $80,000/year

**Why It Worked**:
1. **Perfect Timing**: New HR Director evaluating all vendors
2. **Personalization**: Referenced her LinkedIn post and previous role
3. **Relevance**: Renewal window created urgency
4. **Data Quality**: 92% confidence = accurate, trustworthy data

---

### Outcome Summary

| Metric | Result |
|--------|--------|
| Detection Speed | 5 hours (LinkedIn update → Talent Flow record) |
| BIT Event Creation | Immediate (trigger-based) |
| Initial Score | 36.8 points (Cold) |
| Score After 30 Days | 78.74 points (Warm) |
| Outreach Timing | Day 30 (optimal) |
| Response Rate | 100% (1/1 opened, replied) |
| Meeting Booked | Yes (within 1 week) |
| Pipeline Value | $80,000/year |
| Sales Cycle Impact | Reduced by ~30 days (early engagement) |

**ROI of Talent Flow**:
- ✅ Detected movement within hours (vs. weeks manually)
- ✅ Automatic BIT event creation (no manual entry)
- ✅ Perfect outreach timing (new hire + renewal window)
- ✅ High-quality data (92% confidence)
- ✅ Personalized context for sales rep

---

## Appendix A: Quick Reference

### Key Concepts

| Term | Definition |
|------|------------|
| **Talent Flow** | Spoke that detects and classifies people movement events |
| **Movement** | Change in employment (hire, departure, promotion, transfer) |
| **Confidence Score** | Data quality metric (0-100) for movement accuracy |
| **BIT Event** | Intent signal created from high-impact movements |
| **Processed Flag** | Indicates movement has been sent to BIT |

### Movement Types

- **hire**: External person joins company (highest BIT impact)
- **departure**: Person leaves company (medium BIT impact)
- **promotion**: Internal upward move (low BIT impact)
- **transfer**: Internal lateral move (usually no BIT impact)

### Confidence Thresholds

- **70+**: Minimum for BIT event creation
- **80+**: High quality (preferred)
- **90+**: Verified (highest trust)

### Barton ID Prefix

`01.04.02.04.20000` - Talent Flow spoke identifier (reserved for future use)

### Key Tables

- `talent_flow.movements` - Movement records
- `talent_flow.movement_audit` - Change audit trail
- `talent_flow.executive_movements` - Pre-filtered view

### Schema Location

`doctrine/schemas/talent_flow-schema.sql`

### Related Systems

- **BIT Axle**: `bit.events` receives movements
- **People Hub**: `people.contact` source data
- **Enrichment Log**: `marketing.data_enrichment_log` detection source

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-07 | Barton Outreach Team | Initial Talent Flow Doctrine creation |

---

**End of Talent Flow Doctrine**

*For technical implementation details, see `doctrine/schemas/talent_flow-schema.sql`*
*For BIT integration, see `doctrine/ple/BIT-Doctrine.md`*
*For operational queries, see `infra/docs/ENRICHMENT_TRACKING_QUERIES.sql`*
