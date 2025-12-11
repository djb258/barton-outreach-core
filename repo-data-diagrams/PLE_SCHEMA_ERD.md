# PLE Schema ERD - Marketing Database

## Entity Relationship Diagram

```mermaid
erDiagram
    company_master ||--o{ company_slot : "has slots"
    company_master ||--o{ people_master : "employs"
    company_master ||--o{ company_events : "has events"
    company_master ||--o{ person_movement_history : "source/destination"
    company_master ||--o{ form_5500 : "has 5500 filings"
    company_master ||--o{ dol_violations : "has violations"

    company_slot }o--|| people_master : "filled by"
    company_slot ||--|| company_master : "belongs to"

    people_master ||--|| company_slot : "fills slot"
    people_master ||--|| company_master : "works at"
    people_master ||--o{ person_movement_history : "has movements"
    people_master ||--o| person_scores : "has score"

    person_movement_history }o--|| people_master : "tracks person"
    person_movement_history }o--|| company_master : "from company"
    person_movement_history }o--o| company_master : "to company"

    person_scores }o--|| people_master : "scores person"

    company_events }o--|| company_master : "event for"

    form_5500 }o--o| company_master : "5500 for company"

    dol_violations }o--o| company_master : "violation for company"

    failed_company_match ||--o| company_master : "best match"
    failed_slot_assignment ||--|| company_master : "matched to"
    failed_low_confidence ||--o| company_master : "low conf match"
    failed_no_pattern ||--|| company_master : "has no pattern"
    failed_email_verification ||--|| company_master : "email failed"

    company_master {
        text company_unique_id PK "04.04.01.XX.XXXXX.XXX"
        text company_name
        text website_url
        text industry
        int employee_count "min 50"
        text company_phone
        text address_street
        text address_city
        text address_state "PA,VA,MD,OH,WV,KY"
        text address_zip
        text address_country
        text linkedin_url
        text facebook_url
        text twitter_url
        text sic_codes
        int founded_year "1700-current"
        text_array keywords
        text description
        text source_system
        text source_record_id
        timestamptz promoted_from_intake_at
        int promotion_audit_log_id
        timestamptz created_at
        timestamptz updated_at
        text state_abbrev
        text import_batch_id
        timestamptz validated_at
        text validated_by
        numeric data_quality_score
        varchar ein "Employer ID Number"
        varchar duns "Dun Bradstreet Number"
        varchar cage_code "Govt Entity Code"
        varchar email_pattern "Pattern: {f}{last}@"
        int email_pattern_confidence "0-100"
        varchar email_pattern_source "hunter, manual, enrichment"
        timestamp email_pattern_verified_at
    }

    company_slot {
        text company_slot_unique_id PK "04.04.05.XX.XXXXX.XXX"
        text company_unique_id FK
        text person_unique_id FK "nullable"
        text slot_type "CEO,CFO,HR"
        bool is_filled "default false"
        numeric confidence_score
        timestamptz created_at
        timestamptz filled_at
        timestamptz last_refreshed_at
        text filled_by
        text source_system "default manual"
        int enrichment_attempts "default 0"
        varchar status "default open"
        timestamp vacated_at
        varchar phone "Role phone number"
        varchar phone_extension "Phone extension"
        timestamp phone_verified_at
    }

    people_master {
        text unique_id PK "04.04.02.XX.XXXXX.XXX"
        text company_unique_id FK "04.04.01.XX.XXXXX.XXX"
        text company_slot_unique_id FK "04.04.05.XX.XXXXX.XXX"
        text first_name
        text last_name
        text full_name
        text title
        text seniority
        text department
        text email "validated format"
        text work_phone_e164
        text personal_phone_e164
        text linkedin_url
        text twitter_url
        text facebook_url
        text bio
        text_array skills
        text education
        text_array certifications
        text source_system
        text source_record_id
        timestamptz promoted_from_intake_at
        int promotion_audit_log_id
        timestamptz created_at
        timestamptz updated_at
        bool email_verified "default false"
        text message_key_scheduled
        text email_verification_source
        timestamptz email_verified_at
        varchar validation_status
        timestamp last_verified_at
        timestamp last_enrichment_attempt
    }

    person_movement_history {
        int id PK "auto-increment"
        text person_unique_id FK
        text linkedin_url
        text company_from_id FK
        text company_to_id FK "nullable"
        text title_from
        text title_to "nullable"
        text movement_type "company_change,title_change,contact_lost"
        timestamp detected_at
        jsonb raw_payload
        timestamp created_at
    }

    person_scores {
        int id PK "auto-increment"
        text person_unique_id FK "unique"
        int bit_score "0-100"
        int confidence_score "0-100"
        timestamp calculated_at
        jsonb score_factors
        timestamp created_at
        timestamp updated_at
    }

    company_events {
        int id PK "auto-increment"
        text company_unique_id FK
        text event_type "funding,acquisition,ipo,layoff,leadership_change,product_launch,office_opening,other"
        date event_date
        text source_url
        text summary
        timestamp detected_at
        bool impacts_bit "default true"
        int bit_impact_score "-100 to 100"
        timestamp created_at
    }

    form_5500 {
        int id PK "auto-increment"
        text company_unique_id FK "nullable"
        varchar ack_id "DOL acknowledgment"
        varchar ein "Employer ID - 9 digits"
        varchar plan_number "3 digits"
        varchar plan_name "140 chars"
        varchar sponsor_name "70 chars"
        varchar address "35 chars"
        varchar city "22 chars"
        varchar state "2 chars"
        varchar zip "12 chars"
        date date_received
        varchar plan_codes "59 chars"
        int participant_count
        numeric total_assets "15,2 precision"
        int filing_year
        jsonb raw_payload
        timestamp created_at
        timestamp updated_at
    }

    dol_violations {
        int id PK "auto-increment"
        text company_unique_id FK "nullable"
        varchar ein "9 digits"
        varchar violation_type "100 chars"
        date violation_date
        date resolution_date "nullable"
        numeric penalty_amount "12,2 precision"
        text description
        varchar source_url "500 chars"
        jsonb raw_payload
        timestamp detected_at
    }

    failed_company_match {
        int id PK "auto-increment"
        varchar person_id "PE-XX-XXXXXXXX"
        varchar full_name
        varchar job_title
        varchar title_seniority
        varchar company_name_raw "Raw input company"
        varchar linkedin_url
        varchar best_match_company "Closest fuzzy match"
        decimal best_match_score "0-100"
        text best_match_notes
        varchar resolution_status "pending,resolved"
        varchar resolution "confirmed,rejected,remapped"
        text resolution_notes
        varchar resolved_by
        timestamp resolved_at
        varchar resolved_company_id FK "If added to hub"
        varchar source_file
        timestamp created_at
    }

    failed_slot_assignment {
        int id PK "auto-increment"
        varchar person_id "PE-XX-XXXXXXXX"
        varchar full_name
        varchar job_title
        varchar title_seniority
        varchar company_name_raw
        varchar linkedin_url
        varchar matched_company_id FK
        varchar matched_company_name
        decimal fuzzy_score
        varchar slot_type "hr"
        varchar lost_to_person_id "Winner's ID"
        varchar lost_to_person_name
        varchar lost_to_seniority
        varchar resolution_status "pending"
        varchar source_file
        timestamp created_at
    }

    failed_low_confidence {
        int id PK "auto-increment"
        varchar person_id "PE-XX-XXXXXXXX"
        varchar full_name
        varchar job_title
        varchar title_seniority
        varchar company_name_raw
        varchar linkedin_url
        varchar matched_company_id FK
        varchar matched_company_name
        decimal fuzzy_score "70-79%"
        text match_notes
        varchar resolution_status "pending"
        varchar resolution "confirmed,rejected,remapped"
        varchar confirmed_company_id FK "If confirmed"
        varchar source_file
        timestamp created_at
    }

    failed_no_pattern {
        int id PK "auto-increment"
        varchar person_id "PE-XX-XXXXXXXX"
        varchar full_name
        varchar job_title
        varchar title_seniority
        varchar company_name_raw
        varchar linkedin_url
        varchar company_id FK
        varchar company_name
        varchar company_domain
        varchar slot_type "hr"
        varchar failure_reason "no_domain,pattern_lookup_failed"
        text failure_notes
        varchar resolution_status "pending"
        varchar resolution "pattern_added,manual_email,skipped"
        varchar manual_email "If manually provided"
        varchar source_file
        timestamp created_at
    }

    failed_email_verification {
        int id PK "auto-increment"
        varchar person_id "PE-XX-XXXXXXXX"
        varchar full_name
        varchar job_title
        varchar title_seniority
        varchar company_name_raw
        varchar linkedin_url
        varchar company_id FK
        varchar company_name
        varchar company_domain
        varchar email_pattern
        varchar slot_type "hr"
        varchar generated_email "Email that failed"
        varchar verification_error "invalid,catch_all,etc"
        text verification_notes
        text email_variants "JSON: variants tried"
        varchar resolution_status "pending"
        varchar resolution "alt_email_found,manual_verified,skipped"
        varchar verified_email "If alt found"
        varchar source_file
        timestamp created_at
    }
```

## Relationship Summary

| Source Table | Source Column | Target Table | Target Column | Relationship Type | Constraint Name |
|--------------|---------------|--------------|---------------|-------------------|-----------------|
| company_slot | company_unique_id | company_master | company_unique_id | Many-to-One | fk_company |
| company_slot | person_unique_id | people_master | unique_id | Many-to-One (Optional) | fk_person |
| people_master | company_unique_id | company_master | company_unique_id | Many-to-One | people_master_company_barton_id_format |
| people_master | company_slot_unique_id | company_slot | company_slot_unique_id | One-to-One | people_master_slot_barton_id_format |
| person_movement_history | person_unique_id | people_master | unique_id | Many-to-One | person_movement_history_person_unique_id_fkey |
| person_movement_history | company_from_id | company_master | company_unique_id | Many-to-One | person_movement_history_company_from_id_fkey |
| person_movement_history | company_to_id | company_master | company_unique_id | Many-to-One (Optional) | person_movement_history_company_to_id_fkey |
| person_scores | person_unique_id | people_master | unique_id | One-to-One | person_scores_person_unique_id_fkey |
| company_events | company_unique_id | company_master | company_unique_id | Many-to-One | company_events_company_unique_id_fkey |
| form_5500 | company_unique_id | company_master | company_unique_id | Many-to-One (Optional) | form_5500_company_unique_id_fkey |
| dol_violations | company_unique_id | company_master | company_unique_id | Many-to-One (Optional) | dol_violations_company_unique_id_fkey |
| failed_company_match | resolved_company_id | company_master | company_unique_id | Many-to-One (Optional) | fk_failed_company_match_resolved |
| failed_slot_assignment | matched_company_id | company_master | company_unique_id | Many-to-One | fk_failed_slot_assignment_company |
| failed_low_confidence | matched_company_id | company_master | company_unique_id | Many-to-One (Optional) | fk_failed_low_confidence_matched |
| failed_low_confidence | confirmed_company_id | company_master | company_unique_id | Many-to-One (Optional) | fk_failed_low_confidence_confirmed |
| failed_no_pattern | company_id | company_master | company_unique_id | Many-to-One | fk_failed_no_pattern_company |
| failed_email_verification | company_id | company_master | company_unique_id | Many-to-One | fk_failed_email_verification_company |

## Constraints Summary

### Primary Keys

| Table | Column | Type |
|-------|--------|------|
| company_master | company_unique_id | Barton ID (04.04.01.XX.XXXXX.XXX) |
| company_slot | company_slot_unique_id | Barton ID (04.04.05.XX.XXXXX.XXX) |
| people_master | unique_id | Barton ID (04.04.02.XX.XXXXX.XXX) |
| person_movement_history | id | Auto-increment Integer |
| person_scores | id | Auto-increment Integer |
| company_events | id | Auto-increment Integer |
| form_5500 | id | Auto-increment Integer |
| dol_violations | id | Auto-increment Integer |
| failed_company_match | id | Auto-increment Integer |
| failed_slot_assignment | id | Auto-increment Integer |
| failed_low_confidence | id | Auto-increment Integer |
| failed_no_pattern | id | Auto-increment Integer |
| failed_email_verification | id | Auto-increment Integer |

### Unique Constraints

| Table | Columns | Constraint Name | Purpose |
|-------|---------|-----------------|---------|
| company_slot | (company_unique_id, slot_type) | unique_company_slot, uq_company_slot_type | Ensures one slot per role per company |
| person_scores | person_unique_id | person_scores_person_unique_id_key | One score record per person |

### Check Constraints

#### company_master

| Constraint | Rule | Description |
|------------|------|-------------|
| company_master_barton_id_format | `^04\.04\.01\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$` | Validates Barton ID format |
| company_master_employee_count_positive | `employee_count >= 0` | Ensures non-negative employee count |
| company_master_founded_year_reasonable | `1700 <= founded_year <= CURRENT_YEAR` | Validates founding year |
| chk_employee_minimum | `employee_count >= 50` | Minimum 50 employees required |
| chk_state_valid | State in (PA, VA, MD, OH, WV, KY) | Restricts to specific states |

#### people_master

| Constraint | Rule | Description |
|------------|------|-------------|
| people_master_barton_id_format | `^04\.04\.02\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$` | Validates person Barton ID |
| people_master_company_barton_id_format | `^04\.04\.01\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$` | Validates company reference |
| people_master_slot_barton_id_format | `^04\.04\.05\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$` | Validates slot reference |
| people_master_email_format | Valid email regex | Ensures proper email format |
| chk_contact_required | `linkedin_url IS NOT NULL OR email IS NOT NULL` | At least one contact method required |

#### company_slot

| Constraint | Rule | Description |
|------------|------|-------------|
| company_slot_slot_type_check | Type in (CEO, CFO, HR) | Restricts slot types to exec roles |

#### person_movement_history

| Constraint | Rule | Description |
|------------|------|-------------|
| person_movement_history_movement_type_check | Type in (company_change, title_change, contact_lost) | Valid movement types |

#### person_scores

| Constraint | Rule | Description |
|------------|------|-------------|
| person_scores_bit_score_check | `0 <= bit_score <= 100` | BIT score range |
| person_scores_confidence_score_check | `0 <= confidence_score <= 100` | Confidence score range |

#### company_events

| Constraint | Rule | Description |
|------------|------|-------------|
| company_events_event_type_check | Type in (funding, acquisition, ipo, layoff, leadership_change, product_launch, office_opening, other) | Valid event types |
| company_events_bit_impact_score_check | `-100 <= bit_impact_score <= 100` | BIT impact range |

## Data Flow

### Typical Insert Sequence

1. **company_master** - Insert validated company (from intake)
2. **company_slot** - Auto-create slots (CEO, CFO, HR) for company
3. **people_master** - Insert person and link to company + slot
4. **company_slot** - Update with person_unique_id, set is_filled=true
5. **person_scores** - Calculate and insert BIT/confidence scores
6. **company_events** - Track significant company events
7. **person_movement_history** - Track role/company changes

### Enrichment Flow

1. Slot created empty (is_filled=false)
2. Enrichment agent discovers executive
3. Person inserted into people_master
4. Slot updated with person_unique_id
5. person_scores calculated
6. company_slot.last_refreshed_at updated

### Pipeline Failure Flow (Stage-Specific Routing)

The pipeline routes failures to stage-specific tables for manual review:

```
CSV Input (720 people)
        |
        v
[Phase 2: Fuzzy Match to Company Hub]
        |
        +---> <80% match --> failed_company_match (manual review)
        |
        v
[Phase 3: Slot Assignment (Seniority Competition)]
        |
        +---> Lost to higher seniority --> failed_slot_assignment
        |
        +---> 70-79% confidence --> failed_low_confidence (manual review)
        |
        v
[Phase 4: Email Pattern Lookup]
        |
        +---> No domain/pattern --> failed_no_pattern
        |
        v
[Phase 5: Email Generation + Verification]
        |
        +---> MillionVerifier: invalid --> failed_email_verification
        |
        v
[SUCCESS: Export to Neon]
        |
        v
people_master + company_slot (is_filled=true)
```

**Failure Table Purposes:**

| Table | Stage | Trigger | Resolution Options |
|-------|-------|---------|-------------------|
| failed_company_match | Phase 2 | Fuzzy score <80% | Confirm match, Reject, Remap to different company |
| failed_slot_assignment | Phase 3 | Higher seniority person won slot | Manual override, Wait for vacancy |
| failed_low_confidence | Phase 3 | Fuzzy score 70-79% | Confirm match, Reject, Remap |
| failed_no_pattern | Phase 4 | Company has no domain or email pattern | Add pattern manually, Provide manual email |
| failed_email_verification | Phase 5 | MillionVerifier returned invalid | Try alternate email, Manual verification |

## Notes

- All Barton IDs follow format: `04.04.XX.YY.ZZZZZ.NNN`
  - 04.04 = SubHive.App
  - XX = Schema (01=company, 02=person, 05=slot)
  - YY = Layer
  - ZZZZZ = Sequence
  - NNN = Counter
- Timestamps use `timestamptz` for timezone awareness (created_at, updated_at, etc.)
- Event tracking uses `timestamp without time zone` for detected_at
- JSONB fields store flexible metadata (raw_payload, score_factors)
- Arrays store multi-value fields (keywords, skills, certifications)
