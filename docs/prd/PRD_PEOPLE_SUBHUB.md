# PRD: People Sub-Hub v3.0

**Version:** 3.0 (Constitutional Compliance + FREE Extraction Complete)
**Status:** Active
**Constitutional Date:** 2026-01-29
**Last Updated:** 2026-01-30
**Doctrine:** IMO-Creator Constitutional Doctrine
**Barton ID Range:** `04.04.02.04.2XXXX.###`

---

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | IMO-Creator v1.0 |
| **Domain Spec Reference** | `doctrine/REPO_DOMAIN_SPEC.md` |
| **CC Layer** | CC-02 |
| **PRD Constitution** | `templates/doctrine/PRD_CONSTITUTION.md` |

---

## 1. Sovereign Reference (CC-01)

| Field | Value |
|-------|-------|
| **Sovereign ID** | CL-01 (Company Lifecycle) |
| **Sovereign Boundary** | Company identity and lifecycle state |

---

## 2. Hub Identity (CC-02)

| Field | Value |
|-------|-------|
| **Hub Name** | People Intelligence |
| **Hub ID** | HUB-PEOPLE |
| **Doctrine ID** | 04.04.02 |
| **Owner** | Barton Outreach Core |
| **Version** | 3.0 |
| **Waterfall Order** | 3 |

---

## 3. Purpose & Transformation Declaration

### Transformation Statement (REQUIRED)

> **"This hub transforms raw people data and verified email patterns (CONSTANTS) into slotted contact records with generated emails and lifecycle states (VARIABLES) through CAPTURE (people data intake), COMPUTE (email generation, slot assignment, lifecycle classification), and GOVERN (signal emission with idempotency enforcement)."**

| Field | Value |
|-------|-------|
| **Transformation Summary** | Raw people data + email patterns → Slotted contacts with emails and lifecycle states |

### Constants (Inputs)

_Immutable inputs received from outside this hub. Reference: `doctrine/REPO_DOMAIN_SPEC.md §2`_

| Constant | Source | Description |
|----------|--------|-------------|
| `outreach_id` | Outreach Spine | Operational identifier for FK linkage |
| `verified_email_pattern` | Company Target | Verified email pattern for domain |
| `company_domain` | Company Target | Validated company domain |
| `raw_people_data` | Enrichment Providers | Raw executive/contact data |
| `linkedin_profile_data` | External Enrichment | LinkedIn profile information |

### Variables (Outputs)

_Outputs this hub produces. Reference: `doctrine/REPO_DOMAIN_SPEC.md §3`_

| Variable | Destination | Description |
|----------|-------------|-------------|
| `slot_assignments` | Outreach People table | Executive slot assignments (CEO, CFO, HR) |
| `contact_records` | Outreach People table | Enriched contact records |
| `generated_email` | Outreach People table | Generated email address |
| `email_verified_flag` | Outreach People table | Email verification status |
| `lifecycle_state` | People Master | Contact lifecycle state (SUSPECT, WARM, etc.) |
| `slot_filled_signal` | BIT Engine | Slot filled signal |
| `email_verified_signal` | BIT Engine | Email verified signal |

### Pass Structure

_Constitutional pass mapping per `PRD_CONSTITUTION.md §Pass-to-IMO Mapping`_

| Pass | Type | IMO Layer | Description |
|------|------|-----------|-------------|
| People Data Intake | **CAPTURE** | I (Ingress) | Receive raw people data from enrichment sources |
| Email Generation | **COMPUTE** | M (Middle) | Generate emails using verified patterns (Phase 5) |
| Slot Assignment | **COMPUTE** | M (Middle) | Classify titles and assign to slots (Phase 6) |
| Lifecycle Classification | **COMPUTE** | M (Middle) | Determine lifecycle state (Phase 0) |
| Signal Emission | **GOVERN** | O (Egress) | Emit idempotent signals to BIT Engine |

### Scope Boundary

| Scope | Description |
|-------|-------------|
| **IN SCOPE** | People lifecycle state, email generation, slot assignment, talent flow detection, enrichment queue, output writing |
| **OUT OF SCOPE** | Company identity creation (Company Target owns), email pattern discovery (Company Target owns), BIT scoring (BIT Engine owns), DOL data (DOL owns) |

---

## Sub-Hub Ownership Statement

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         PEOPLE SUB-HUB OWNERSHIP                              ║
║                                                                               ║
║   This sub-hub OWNS:                                                          ║
║   ├── People lifecycle state initialization (SUSPECT, WARM, etc.)            ║
║   ├── Email generation for individuals (using Company Hub patterns)          ║
║   ├── Slot assignment (CHRO, HR_MANAGER, BENEFITS_LEAD, etc.)               ║
║   ├── Talent Flow detection (movement events)                                ║
║   ├── Enrichment queue management for people                                 ║
║   └── People output writing (CSV files)                                      ║
║                                                                               ║
║   This sub-hub DOES NOT OWN:                                                  ║
║   ├── Company identity (company_id, company_name, EIN)                       ║
║   ├── Domain resolution or validation                                        ║
║   ├── Email pattern discovery or verification                                ║
║   ├── BIT Engine scoring or decision making                                  ║
║   ├── Outreach decisions (who gets messaged, when, how)                      ║
║   └── DOL filing ingestion or matching                                       ║
║                                                                               ║
║   This sub-hub EMITS SIGNALS to Company Hub. It NEVER makes decisions.       ║
║                                                                               ║
║   PREREQUISITE: company_id MUST exist before any People process runs.        ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 1. Purpose

The People Sub-Hub manages the **person lifecycle** within the Barton Outreach system. It receives company anchors from the Company Hub and processes people attached to those companies.

### Core Functions

1. **People Ingest & Classification** (Phase 0) - Classify incoming people into lifecycle states
2. **Email Generation** (Phase 5) - Generate emails using Company Hub patterns
3. **Slot Assignment** (Phase 6) - Assign people to HR slots
4. **Enrichment Queue** (Phase 7) - Track items needing additional processing
5. **Output Writing** (Phase 8) - Write pipeline results to files
6. **Talent Flow Detection** - Detect executive movement events

### Company-First Doctrine

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   IF company_id IS NULL:                                               │
│       STOP. DO NOT PROCESS.                                            │
│       → Route person to Company Hub for identity resolution first.     │
│                                                                         │
│   People Sub-Hub NEVER creates company identity.                       │
│   People Sub-Hub ONLY processes people with valid company anchors.     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### Correlation ID Doctrine (HARD LAW)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       CORRELATION ID ENFORCEMENT                              ║
║                                                                               ║
║   DOCTRINE: correlation_id MUST be propagated unchanged across ALL phases    ║
║             and into all error logs and emitted signals.                      ║
║                                                                               ║
║   RULES:                                                                      ║
║   1. Every input to Phases 0, 5-8 MUST include correlation_id               ║
║   2. Every output from Phases 0, 5-8 MUST include correlation_id            ║
║   3. Every signal emitted to BIT Engine MUST include correlation_id          ║
║   4. Every error logged MUST include correlation_id                          ║
║   5. correlation_id MUST NOT be modified or regenerated mid-pipeline         ║
║                                                                               ║
║   FORMAT: UUID v4 (e.g., "550e8400-e29b-41d4-a716-446655440000")              ║
║   GENERATED BY: Intake process or upstream hub                               ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

### Signal Idempotency Doctrine (HARD LAW)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       SIGNAL IDEMPOTENCY ENFORCEMENT                          ║
║                                                                               ║
║   DOCTRINE: All signals emitted to BIT Engine MUST be idempotent.            ║
║             Duplicate signals MUST be deduplicated before emission.           ║
║                                                                               ║
║   DEDUPLICATION RULES:                                                        ║
║   ├── Key: (company_id, signal_type, person_id)                              ║
║   ├── Window: 24 hours (same signal within window = duplicate)               ║
║   └── Hash: SHA-256 of key fields for fast lookup                            ║
║                                                                               ║
║   DUPLICATE HANDLING:                                                         ║
║   ├── Increment duplicate_count on existing signal                           ║
║   ├── Do NOT emit new signal to BIT Engine                                   ║
║   └── Log duplicate detection with correlation_id                            ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 2. Owned Processes

### Phase 0: People Ingest

**File:** `ctb/sys/enrichment/pipeline_engine/phases/phase0_people_ingest.py`
**Purpose:** Classify newly ingested people into lifecycle states

#### Classification Priority (First Match Wins)

| Priority | Condition | State Assignment |
|----------|-----------|------------------|
| 1 | `company_id` is NULL | `SUSPECT` (unanchored) |
| 2 | Past meeting flag exists | `APPOINTMENT` |
| 3 | Historical reply detected | `WARM` |
| 4 | TalentFlow movement exists | `TALENTFLOW_WARM` |
| 5 | BIT score >= 25 | `WARM` |
| 6 | Default | `SUSPECT` |

#### Tooling Declaration

| Tool | API | Cost Tier | Rate Limit | Cache |
|------|-----|-----------|------------|-------|
| Classification Engine | Internal | FREE | N/A | None |
| BIT Score Lookup | Internal | FREE | 1000/min | 5 min |
| Calendar Integration | Google API | LOW | 100/min | 1 hour |

#### Input Contract

| Field | Type | Required | Source |
|-------|------|----------|--------|
| `correlation_id` | UUID | **YES** | Upstream process (propagate unchanged) |
| `person_id` | string | Yes | Input data |
| `company_id` | string | **Required** | Company Hub |
| `first_name` | string | Yes | Input data |
| `last_name` | string | Yes | Input data |
| `job_title` | string | No | Input data |
| `has_replied` | bool | No | Historical import |
| `talentflow_movement` | bool | No | TalentFlow Spoke |
| `bit_score` | int | No | BIT Engine |
| `has_meeting` | bool | No | Calendar integration |

#### Output Contract

| Field | Type | Description |
|-------|------|-------------|
| `correlation_id` | UUID | **Propagated unchanged from input** |
| `person_id` | string | Person identifier |
| `company_id` | string | Company anchor |
| `initial_funnel_state` | LifecycleState | SUSPECT, WARM, TALENTFLOW_WARM, APPOINTMENT |
| `slot_candidate` | string | Suggested slot type (CHRO, HR_MANAGER, etc.) |
| `classification_reason` | string | Why this state was assigned |
| `ingest_events` | List[IngestEvent] | Events detected during ingest |

#### Failure Handling

| Failure | Severity | Local Table | Global Emit | Recovery |
|---------|----------|-------------|-------------|----------|
| Missing company_id | HIGH | `people_subhub.failures` | YES (PSH-P0-001) | Route to Company Hub |
| Invalid data format | MEDIUM | `people_subhub.failures` | YES (PSH-P0-002) | Manual review queue |
| BIT lookup timeout | LOW | `people_subhub.failures` | NO | Retry with backoff |
| Classification error | MEDIUM | `people_subhub.failures` | YES (PSH-P0-003) | Default to SUSPECT |

#### Signal Emission

```python
# Phase 0 emits signals to BIT Engine for state classification
# MUST include correlation_id - signals without it WILL BE REJECTED
bit_engine.create_signal(
    correlation_id=correlation_id,  # REQUIRED - propagate unchanged
    signal_type=SignalType.PERSON_CLASSIFIED,
    company_id=company_id,
    source_spoke='people_node',
    emitted_at=datetime.now(),
    metadata={
        'person_id': person_id,
        'initial_state': initial_funnel_state.value
    }
)
```

---

### Phase 5: Email Generation

**File:** `ctb/sys/enrichment/pipeline_engine/phases/phase5_email_generation.py`
**Purpose:** Generate emails using verified patterns from Company Hub

#### Tooling Declaration

| Tool | API | Cost Tier | Rate Limit | Cache | Bypass Condition |
|------|-----|-----------|------------|-------|------------------|
| Pattern Templates | Internal | FREE | N/A | None | Never |
| Waterfall Tier 0 | Firecrawl, ScraperAPI | FREE | 100/hour | 24 hour | If pattern exists |
| Waterfall Tier 1 | Hunter.io, Clearbit | LOW ($0.001-0.01) | 50/hour | 24 hour | If Tier 0 succeeds |
| Waterfall Tier 2 | Prospeo, Snov, Clay | MID ($0.05-0.10) | 20/hour | 24 hour | If Tier 1 succeeds |

#### Input Contract

| Field | Type | Required | Source |
|-------|------|----------|--------|
| `correlation_id` | UUID | **YES** | Upstream process (propagate unchanged) |
| `person_id` | string | Yes | Phase 0 or input |
| `company_id` | string | **Required** | Company Hub |
| `first_name` | string | Yes | Input data |
| `last_name` | string | Yes | Input data |
| `email_pattern` | string | **Required** | Company Hub (Phase 4) |
| `domain` | string | **Required** | Company Hub (Phase 2) |
| `pattern_confidence` | float | No | Company Hub (Phase 4) |

#### Output Contract

| Field | Type | Description |
|-------|------|-------------|
| `correlation_id` | UUID | **Propagated unchanged from input** |
| `person_id` | string | Person identifier |
| `company_id` | string | Company anchor |
| `generated_email` | string | Generated email address |
| `email_confidence` | EmailConfidence | VERIFIED, DERIVED, LOW_CONFIDENCE, WATERFALL |
| `pattern_used` | string | Pattern template used |
| `email_domain` | string | Domain used |
| `email_candidates` | string | Top 3 alternative formats |

#### Failure Handling

| Failure | Severity | Local Table | Global Emit | Recovery |
|---------|----------|-------------|-------------|----------|
| No pattern for company | HIGH | `people_subhub.failures` | YES (PSH-P5-001) | Queue for waterfall |
| Missing name fields | MEDIUM | `people_subhub.failures` | YES (PSH-P5-002) | Queue for enrichment |
| Pattern generation error | HIGH | `people_subhub.failures` | YES (PSH-P5-003) | Manual review |
| Waterfall exhausted | MEDIUM | `people_subhub.failures` | YES (PSH-P5-004) | Use suggested pattern |
| API rate limited | LOW | `people_subhub.failures` | NO | Exponential backoff |

#### Email Confidence Levels

| Level | Description | When Used |
|-------|-------------|-----------|
| `VERIFIED` | Pattern verified in Phase 4 | Pattern status = 'verified' |
| `DERIVED` | Pattern derived from known emails | Pattern status = 'derived' |
| `LOW_CONFIDENCE` | Fallback pattern, unverified | No verification status |
| `WATERFALL` | Pattern discovered via on-demand waterfall | Waterfall enabled, pattern found |

#### Signal Emission

```python
# Phase 5 emits EMAIL_VERIFIED signal to BIT Engine
# MUST include correlation_id - signals without it WILL BE REJECTED
if confidence in [EmailConfidence.VERIFIED, EmailConfidence.WATERFALL]:
    # Check deduplication before emitting
    dedup_key = f"{company_id}:EMAIL_VERIFIED:{person_id}"
    if not signal_cache.exists(dedup_key, window_hours=24):
        bit_engine.create_signal(
            correlation_id=correlation_id,  # REQUIRED - propagate unchanged
            signal_type=SignalType.EMAIL_VERIFIED,
            company_id=company_id,
            source_spoke='people_node',
            emitted_at=datetime.now(),
            impact=3.0,
            metadata={
                'person_id': person_id,
                'email': generated_email,
                'confidence': confidence.value
            }
        )
        signal_cache.set(dedup_key, ttl_hours=24)
```

---

### Phase 6: Slot Assignment

**File:** `ctb/sys/enrichment/pipeline_engine/phases/phase6_slot_assignment.py`
**Purpose:** Assign people to company HR slots based on title classification

#### Tooling Declaration

| Tool | API | Cost Tier | Rate Limit | Cache |
|------|-----|-----------|------------|-------|
| Title Classifier | Internal | FREE | N/A | None |
| Seniority Scorer | Internal | FREE | N/A | None |
| Slot Conflict Resolver | Internal | FREE | N/A | None |

#### Slot Types (Seniority Order)

| Slot Type | Seniority Rank | Title Keywords |
|-----------|----------------|----------------|
| `CHRO` | 100 | Chief Human Resources, Chief People, CPO, VP HR, SVP HR |
| `HR_MANAGER` | 80 | HR Director, HR Manager, HR Lead, Head of HR |
| `BENEFITS_LEAD` | 60 | Benefits Director, Benefits Manager, Total Rewards |
| `PAYROLL_ADMIN` | 50 | Payroll Director, Payroll Manager, Payroll Admin |
| `HR_SUPPORT` | 30 | HR Coordinator, HR Specialist, HR Generalist, HRBP |
| `UNSLOTTED` | 0 | Cannot classify |

#### Slot Rules

1. **One person per slot per company** - Enforced strictly
2. **Conflict resolution** - Higher seniority wins (min diff: 10 points)
3. **Empty slots** - Recorded in enrichment queue for future filling
4. **Company anchor required** - No slot assignment without `company_id`

#### Input Contract

| Field | Type | Required | Source |
|-------|------|----------|--------|
| `correlation_id` | UUID | **YES** | Upstream process (propagate unchanged) |
| `person_id` | string | Yes | Phase 5 |
| `company_id` | string | **Required** | Company Hub |
| `job_title` | string | Yes | Input data |
| `generated_email` | string | Yes | Phase 5 |

#### Output Contract

| Field | Type | Description |
|-------|------|-------------|
| `correlation_id` | UUID | **Propagated unchanged from input** |
| `person_id` | string | Person identifier |
| `company_id` | string | Company anchor |
| `slot_type` | SlotType | Assigned slot (CHRO, HR_MANAGER, etc.) |
| `seniority_score` | int | 0-100 seniority score |
| `slot_reason` | string | assigned, higher_seniority_by_X, slot_occupied |
| `replaced_person_id` | string | ID of displaced person (if any) |
| `title_normalized` | string | Normalized job title |

#### Failure Handling

| Failure | Severity | Local Table | Global Emit | Recovery |
|---------|----------|-------------|-------------|----------|
| Missing company_id | HIGH | `people_subhub.failures` | YES (PSH-P6-001) | Route to Company Hub |
| Missing title | MEDIUM | `people_subhub.failures` | YES (PSH-P6-002) | Classify as UNSLOTTED |
| Title not recognized | LOW | `people_subhub.failures` | NO | Classify as UNSLOTTED |
| Slot conflict | INFO | `people_subhub.slot_conflicts` | NO | Normal seniority resolution |

#### Slot Summary Output

| Field | Type | Description |
|-------|------|-------------|
| `company_id` | string | Company anchor |
| `has_chro` | bool | CHRO slot filled |
| `has_hr_manager` | bool | HR Manager slot filled |
| `has_benefits_lead` | bool | Benefits Lead slot filled |
| `has_payroll_admin` | bool | Payroll Admin slot filled |
| `has_hr_support` | bool | HR Support slot filled |
| `total_slots_filled` | int | Count of filled slots |
| `missing_slots` | string | Comma-separated missing slot types |

#### Signal Emission

```python
# Phase 6 emits SLOT_FILLED signal to BIT Engine
# MUST include correlation_id - signals without it WILL BE REJECTED
# Check deduplication before emitting
dedup_key = f"{company_id}:SLOT_FILLED:{slot_type.value}"
if not signal_cache.exists(dedup_key, window_hours=24):
    bit_engine.create_signal(
        correlation_id=correlation_id,  # REQUIRED - propagate unchanged
        signal_type=SignalType.SLOT_FILLED,
        company_id=company_id,
        source_spoke='people_node',
        emitted_at=datetime.now(),
        impact=10.0,
        metadata={
            'person_id': person_id,
            'slot_type': slot_type.value,
            'seniority_score': seniority_score
        }
    )
    signal_cache.set(dedup_key, ttl_hours=24)

# If slot is vacated (replacement), emit SLOT_VACATED
if replaced_person_id:
    vacate_key = f"{company_id}:SLOT_VACATED:{replaced_person_id}"
    if not signal_cache.exists(vacate_key, window_hours=24):
        bit_engine.create_signal(
            correlation_id=correlation_id,  # REQUIRED - propagate unchanged
            signal_type=SignalType.SLOT_VACATED,
            company_id=company_id,
            source_spoke='people_node',
            emitted_at=datetime.now(),
            impact=-5.0,
            metadata={
                'person_id': replaced_person_id,
                'slot_type': slot_type.value,
                'replaced_by': person_id
            }
        )
        signal_cache.set(vacate_key, ttl_hours=24)
```

---

### Phase 7: Enrichment Queue

**File:** `ctb/sys/enrichment/pipeline_engine/phases/phase7_enrichment_queue.py`
**Purpose:** Build unified queue for items needing additional processing

#### Tooling Declaration

| Tool | API | Cost Tier | Rate Limit | Cache |
|------|-----|-----------|------------|-------|
| Queue Manager | Internal | FREE | N/A | None |
| Waterfall Invoker | External | VARIABLE | See Phase 5 | 24 hour |
| Priority Calculator | Internal | FREE | N/A | None |

#### Queue TTL Policy (HARD LAW)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       ENRICHMENT QUEUE TTL ENFORCEMENT                        ║
║                                                                               ║
║   DOCTRINE: Queue items MUST have TTL. Stale items MUST be resolved or       ║
║             escalated. No indefinite queue retention.                         ║
║                                                                               ║
║   TTL BY PRIORITY:                                                            ║
║   ├── HIGH:   7 days  (auto-escalate at Day 3, Day 5)                        ║
║   ├── MEDIUM: 14 days (auto-escalate at Day 7, Day 12)                       ║
║   └── LOW:    30 days (auto-escalate at Day 14, Day 25)                      ║
║                                                                               ║
║   EXPIRY BEHAVIOR:                                                            ║
║   ├── Log to people_subhub.expired_queue with correlation_id                 ║
║   ├── Emit error event to master error log (PSH-P7-TTL)                      ║
║   └── Mark original record as 'enrichment_abandoned'                         ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

#### Queue Sources

| Source | Phase | Reason |
|--------|-------|--------|
| Missing patterns | 5 | No email pattern for company |
| Empty slots | 6 | Company missing HR slots |
| Slot conflicts | 6 | Multiple candidates for same slot |
| Email issues | 5 | Email generation failed |
| Data quality | 5,6 | Missing company_id, name, title |

#### Queue Priorities

| Priority | Reasons | Impact | TTL |
|----------|---------|--------|-----|
| `HIGH` | Pattern missing, CHRO empty, Benefits empty | Blocks multiple records | 7 days |
| `MEDIUM` | HR Manager empty, Payroll empty, slot collision | Important but not blocking | 14 days |
| `LOW` | HR Support empty, individual emails | Single-record impact | 30 days |

#### Input Contract

| Field | Type | Required | Source |
|-------|------|----------|--------|
| `correlation_id` | UUID | **YES** | Upstream process (propagate unchanged) |
| `people_missing_pattern_df` | DataFrame | Yes | Phase 5 |
| `unslotted_people_df` | DataFrame | Yes | Phase 6 |
| `slot_summary_df` | DataFrame | Yes | Phase 6 |

#### Output Contract

| Field | Type | Description |
|-------|------|-------------|
| `correlation_id` | UUID | **Propagated unchanged from input** |
| `queue_id` | string | Unique queue item ID (Q-XXXX) |
| `entity_type` | EntityType | COMPANY or PERSON |
| `entity_id` | string | Entity identifier |
| `company_id` | string | Company anchor |
| `reason` | QueueReason | Why item was queued |
| `priority` | QueuePriority | HIGH, MEDIUM, LOW |
| `source_phase` | int | Phase that triggered queueing |
| `status` | string | pending, processing, completed, failed |
| `ttl_days` | int | Days until expiry |
| `expires_at` | datetime | Calculated expiration timestamp |
| `escalation_status` | string | none, warning, escalated |

#### Failure Handling

| Failure | Severity | Local Table | Global Emit | Recovery |
|---------|----------|-------------|-------------|----------|
| Waterfall exhausted | MEDIUM | `people_subhub.failures` | YES (PSH-P7-001) | Mark exhausted, manual |
| Budget exceeded | LOW | `people_subhub.failures` | NO | Next run |
| API rate limit | LOW | `people_subhub.failures` | NO | Exponential backoff |
| Queue TTL expired | MEDIUM | `people_subhub.expired_queue` | YES (PSH-P7-TTL) | Archive and close |

#### Waterfall Integration

When `enable_waterfall=True`:
1. PATTERN_MISSING items are processed via waterfall
2. Tier 0 (FREE) → Tier 1 (Low Cost) → Tier 2 (Premium)
3. Resolved patterns returned for immediate email generation
4. Respects budget and batch limits

---

### Phase 8: Output Writer

**File:** `ctb/sys/enrichment/pipeline_engine/phases/phase8_output_writer.py`
**Purpose:** Write pipeline results to CSV files

#### Tooling Declaration

| Tool | API | Cost Tier | Rate Limit | Cache |
|------|-----|-----------|------------|-------|
| CSV Writer | Internal | FREE | N/A | None |
| Summary Generator | Internal | FREE | N/A | None |
| Audit Logger | Internal | FREE | N/A | None |

#### Output Files

| File | Description |
|------|-------------|
| `people_final.csv` | All people with emails and slot assignments |
| `slot_assignments.csv` | Slot summary by company |
| `enrichment_queue.csv` | Items needing additional enrichment |
| `pipeline_summary.txt` | Human-readable run summary |
| `audit_log.json` | Complete event log with correlation_ids |

#### Input Contract

| Field | Type | Required | Source |
|-------|------|----------|--------|
| `correlation_id` | UUID | **YES** | Upstream process (propagate unchanged) |
| `people_with_emails_df` | DataFrame | Yes | Phase 5 |
| `slotted_people_df` | DataFrame | Yes | Phase 6 |
| `unslotted_people_df` | DataFrame | Yes | Phase 6 |
| `slot_summary_df` | DataFrame | Yes | Phase 6 |
| `enrichment_queue_df` | DataFrame | Yes | Phase 7 |
| `phase_stats` | Dict | No | All phases |

#### Failure Handling

| Failure | Severity | Local Table | Global Emit | Recovery |
|---------|----------|-------------|-------------|----------|
| Disk full | CRITICAL | `people_subhub.failures` | YES (PSH-P8-001) | Alert, halt |
| Write permission | HIGH | `people_subhub.failures` | YES (PSH-P8-002) | Fix permissions |
| Invalid data | MEDIUM | `people_subhub.failures` | YES (PSH-P8-003) | Skip record, log |
| Audit log failure | HIGH | N/A | YES (PSH-P8-004) | Retry, then alert |

#### People Final Output Schema

| Column | Type | Description |
|--------|------|-------------|
| `person_id` | string | Person identifier |
| `company_id` | string | Company anchor |
| `first_name` | string | First name |
| `last_name` | string | Last name |
| `job_title` | string | Job title |
| `generated_email` | string | Generated email |
| `email_confidence` | string | Confidence level |
| `slot_type` | string | Assigned slot |
| `slot_reason` | string | Assignment reason |
| `seniority_score` | int | Seniority score |
| `pattern_used` | string | Email pattern |
| `email_domain` | string | Email domain |

---

## 3. Talent Flow Integration

### Purpose

Talent Flow detects executive movement events (people joining/leaving companies) and emits signals to the BIT Engine.

### Signal Types

| Signal | Impact | When Emitted |
|--------|--------|--------------|
| `EXECUTIVE_JOINED` | +10.0 | New executive detected at company |
| `EXECUTIVE_LEFT` | -5.0 | Executive departed company |
| `TITLE_CHANGE` | +3.0 | Executive title/role changed |

### Talent Flow Gate

**File:** `ctb/sys/enrichment/pipeline_engine/phases/talentflow_phase0_company_gate.py`

Before processing any Talent Flow event:
1. Validate `company_id` exists in Company Hub
2. If missing, emit `COMPANY_IDENTITY_NEEDED` signal
3. Do NOT create company identity (Company Hub responsibility)

```python
def process_talent_flow_event(event: TalentFlowEvent):
    """Process talent flow event - MUST validate company first."""

    # Gate: Validate company exists
    if not company_hub.company_exists(event.company_id):
        # Request identity creation from Company Hub
        company_hub.request_identity_creation(
            company_name=event.company_name,
            domain=event.domain,
            source='talent_flow'
        )
        return {'status': 'queued', 'reason': 'awaiting_company_identity'}

    # Emit signal to BIT Engine
    bit_engine.create_signal(
        signal_type=SignalType.EXECUTIVE_JOINED,
        company_id=event.company_id,
        source_spoke='talent_flow',
        metadata={'person_name': event.person_name, 'title': event.title}
    )
```

---

## 4. Movement Engine Integration

The People Sub-Hub integrates with the Movement Engine for lifecycle state transitions.

### State Transitions

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    PEOPLE LIFECYCLE STATES                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   SUSPECT ──────────────► WARM ──────────────► TALENTFLOW_WARM          │
│      │                      │                         │                  │
│      │                      │                         │                  │
│      └──────────────────────┴─────────────────────────┴──────────────►  │
│                                                                          │
│                                                             APPOINTMENT  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Transition Triggers

| From | To | Trigger |
|------|-----|---------|
| SUSPECT | WARM | BIT score >= 25 |
| SUSPECT | WARM | Historical reply detected |
| SUSPECT | TALENTFLOW_WARM | TalentFlow movement detected |
| WARM | TALENTFLOW_WARM | TalentFlow movement detected |
| Any | APPOINTMENT | Meeting scheduled |

---

## 5. Signal Emission Summary

All signals emitted by People Sub-Hub to Company Hub BIT Engine:

| Signal Type | Enum | Impact | Source Phase |
|-------------|------|--------|--------------|
| `SLOT_FILLED` | `SignalType.SLOT_FILLED` | +10.0 | Phase 6 |
| `SLOT_VACATED` | `SignalType.SLOT_VACATED` | -5.0 | Phase 6 |
| `EMAIL_VERIFIED` | `SignalType.EMAIL_VERIFIED` | +3.0 | Phase 5 |
| `LINKEDIN_FOUND` | `SignalType.LINKEDIN_FOUND` | +2.0 | Enrichment |
| `EXECUTIVE_JOINED` | `SignalType.EXECUTIVE_JOINED` | +10.0 | Talent Flow |
| `EXECUTIVE_LEFT` | `SignalType.EXECUTIVE_LEFT` | -5.0 | Talent Flow |
| `TITLE_CHANGE` | `SignalType.TITLE_CHANGE` | +3.0 | Talent Flow |

---

## 6. Error Log Integration (HARD LAW)

### Local Failure Table Schema

All failures from Phases 0, 5-8 MUST be logged to `people_subhub.failures` with correlation_id.

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       TWO-LAYER ERROR MODEL                                   ║
║                                                                               ║
║   LAYER 1 - LOCAL: people_subhub.failures                                    ║
║   ├── Owned by People Sub-Hub                                                ║
║   ├── Used for execution & remediation                                       ║
║   └── Contains full context for retry/resolution                             ║
║                                                                               ║
║   LAYER 2 - GLOBAL: public.shq_error_log                                     ║
║   ├── Owned by System                                                        ║
║   ├── Used for visibility & trend detection                                  ║
║   └── Receives normalized error events from sub-hubs                         ║
║                                                                               ║
║   RULE: Sub-hubs write locally FIRST, then emit normalized event upward.    ║
║   RULE: No sub-hub writes directly to another hub's tables.                  ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

#### Required Local Failure Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `failure_id` | UUID | YES | Auto-generated |
| `correlation_id` | UUID | **YES** | Pipeline trace ID |
| `error_code` | string | YES | Standardized error code |
| `error_message` | string | YES | Human-readable message |
| `severity` | enum | YES | `info`, `warning`, `error`, `critical` |
| `phase` | string | YES | `phase_0`, `phase_5`, `phase_6`, `phase_7`, `phase_8` |
| `person_id` | string | NO | If available |
| `company_id` | string | NO | If available |
| `stack_trace` | text | NO | For debugging |
| `created_at` | datetime | YES | Auto-generated |

#### Error Code Standards (People Sub-Hub)

| Code | Phase | Description |
|------|-------|-------------|
| `PSH-P0-001` | Phase 0 | Missing company_id |
| `PSH-P0-002` | Phase 0 | Invalid data format |
| `PSH-P0-003` | Phase 0 | Classification error |
| `PSH-P5-001` | Phase 5 | No pattern for company |
| `PSH-P5-002` | Phase 5 | Missing name fields |
| `PSH-P5-003` | Phase 5 | Pattern generation error |
| `PSH-P5-004` | Phase 5 | Waterfall exhausted |
| `PSH-P6-001` | Phase 6 | Missing company_id |
| `PSH-P6-002` | Phase 6 | Missing title |
| `PSH-P7-001` | Phase 7 | Waterfall exhausted |
| `PSH-P7-TTL` | Phase 7 | Queue TTL expired |
| `PSH-P8-001` | Phase 8 | Disk full |
| `PSH-P8-002` | Phase 8 | Write permission error |
| `PSH-P8-003` | Phase 8 | Invalid data |
| `PSH-P8-004` | Phase 8 | Audit log failure |

---

## 7. Failure Modes Summary

### By Phase

| Phase | Critical Failures | High Failures | Medium Failures | Low Failures |
|-------|-------------------|---------------|-----------------|--------------|
| Phase 0 | 0 | 1 | 2 | 1 |
| Phase 5 | 0 | 2 | 2 | 1 |
| Phase 6 | 0 | 1 | 1 | 2 |
| Phase 7 | 0 | 0 | 2 | 2 |
| Phase 8 | 1 | 2 | 1 | 0 |

### Global Emit Rules

Only failures marked "Global Emit: YES" are propagated to `public.shq_error_log`:
- All HIGH and CRITICAL severity failures
- MEDIUM failures that affect data integrity
- TTL expirations (for trend detection)
- LOW failures are retained locally only

---

## 8. Kill Switches

### Phase-Level Kill Switches

```python
# Phase 5 Kill Switch
if config.get('kill_phase5', False):
    logger.warning("Phase 5 killed by configuration")
    return pd.DataFrame(), pd.DataFrame(), Phase5Stats()

# Phase 6 Kill Switch
if config.get('kill_phase6', False):
    logger.warning("Phase 6 killed by configuration")
    return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), Phase6Stats()
```

### Global Kill Switches

| Switch | Scope | Effect |
|--------|-------|--------|
| `KILL_PEOPLE_PIPELINE` | All phases | Stops entire People Pipeline |
| `KILL_TALENT_FLOW` | Talent Flow | Stops movement detection |
| `KILL_WATERFALL` | Phase 5, 7 | Disables pattern waterfall |
| `KILL_SIGNALS` | All phases | Stops signal emission to BIT |

### Runtime Termination

```python
# Check kill switch before each phase
def check_kill_switch(phase_name: str) -> bool:
    """Check if phase should be killed."""
    global_kill = os.environ.get('KILL_PEOPLE_PIPELINE', 'false').lower() == 'true'
    phase_kill = os.environ.get(f'KILL_{phase_name.upper()}', 'false').lower() == 'true'
    return global_kill or phase_kill
```

---

## 9. Observability

### Metrics

| Metric | Type | Phase |
|--------|------|-------|
| `people.classified.total` | Counter | 0 |
| `people.classified.state.{state}` | Counter | 0 |
| `emails.generated.total` | Counter | 5 |
| `emails.generated.confidence.{level}` | Counter | 5 |
| `slots.assigned.total` | Counter | 6 |
| `slots.assigned.type.{type}` | Counter | 6 |
| `queue.items.total` | Gauge | 7 |
| `queue.items.priority.{level}` | Gauge | 7 |
| `signals.emitted.total` | Counter | All |
| `signals.emitted.type.{type}` | Counter | All |

### Logging

```python
# Standard log format for People Sub-Hub
logger.info(
    "Phase completed",
    extra={
        'phase': 6,
        'sub_hub': 'people',
        'company_id': company_id,
        'records_processed': 150,
        'duration_seconds': 2.5
    }
)
```

### Tracing

```python
# Trace context for cross-phase correlation
trace_context = {
    'run_id': 'PPL-20251217-ABC123',
    'company_id': company_id,
    'person_id': person_id,
    'phase': 6
}
```

---

## 10. Integration with Company Hub

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA FLOW                                          │
└─────────────────────────────────────────────────────────────────────────────┘

    COMPANY HUB                              PEOPLE SUB-HUB
    (Identity + Patterns)                    (Lifecycle + Slots)

    ┌───────────────────┐                    ┌───────────────────┐
    │ Phase 1-4         │                    │ Phase 0           │
    │ Company Identity  │                    │ People Ingest     │
    │ Pipeline          │                    │                   │
    │                   │    company_id      │                   │
    │ • company_id   ───┼──────────────────► │ • Classify        │
    │ • domain       ───┼──────────────────► │ • Assign State    │
    │ • email_pattern───┼──────────────────► │                   │
    └───────────────────┘                    └─────────┬─────────┘
                                                       │
                                                       ▼
                                             ┌───────────────────┐
                                             │ Phase 5           │
                                             │ Email Generation  │
                                             │                   │
                                             │ • Generate emails │
                                             │ • Track confidence│
                                             └─────────┬─────────┘
                                                       │
                                                       ▼
                                             ┌───────────────────┐
                                             │ Phase 6           │
                                             │ Slot Assignment   │
                                             │                   │
                                             │ • Assign slots    │
                                             │ • Resolve conflicts│
                                             └─────────┬─────────┘
                                                       │
                         SIGNALS                       │ SIGNALS
                         ┌─────────────────────────────┤
                         │                             │
                         ▼                             ▼
    ┌───────────────────┐                    ┌───────────────────┐
    │ BIT ENGINE        │◄───────────────────│ Phase 7           │
    │ (Company Hub)     │    SLOT_FILLED     │ Enrichment Queue  │
    │                   │    EMAIL_VERIFIED  │                   │
    │ • Aggregate       │    EXEC_JOINED     │ • Queue items     │
    │ • Calculate score │                    │ • Process waterfall│
    │ • Make decisions  │                    └─────────┬─────────┘
    └───────────────────┘                              │
                                                       ▼
                                             ┌───────────────────┐
                                             │ Phase 8           │
                                             │ Output Writer     │
                                             │                   │
                                             │ • Write CSVs      │
                                             │ • Generate summary│
                                             └───────────────────┘
```

---

## 11. API Reference

### Phase 0: People Ingest

```python
from pipeline_engine.phases.phase0_people_ingest import Phase0PeopleIngest, classify_people_ingest

# Full class usage
phase0 = Phase0PeopleIngest(config={'bit_warm_threshold': 25})
results, stats = phase0.run(people_df)

# Convenience function
results, stats = classify_people_ingest(people_df, config=None)

# Single person classification
result = phase0.classify_single(person_data)
```

### Phase 5: Email Generation

```python
from pipeline_engine.phases.phase5_email_generation import Phase5EmailGeneration, generate_emails

# Full class usage
phase5 = Phase5EmailGeneration(config={
    'enable_waterfall': True,
    'waterfall_mode': 2
})
people_df, missing_df, stats = phase5.run(matched_people_df, pattern_df)

# Convenience function
people_df, missing_df, stats = generate_emails(matched_people_df, pattern_df)

# Direct email generation
email = phase5.generate_email('john', 'doe', '{first}.{last}', 'example.com')
```

### Phase 6: Slot Assignment

```python
from pipeline_engine.phases.phase6_slot_assignment import Phase6SlotAssignment, assign_slots

# Full class usage
phase6 = Phase6SlotAssignment(config={
    'allow_slot_replacement': True,
    'min_seniority_diff': 10
})
slotted_df, unslotted_df, summary_df, stats = phase6.run(people_with_emails_df)

# Convenience function
slotted_df, unslotted_df, summary_df, stats = assign_slots(people_with_emails_df)

# Title classification
slot_type, score, normalized = phase6.classify_title('VP of Human Resources')
```

### Phase 7: Enrichment Queue

```python
from pipeline_engine.phases.phase7_enrichment_queue import Phase7EnrichmentQueue, build_enrichment_queue

# Full class usage
phase7 = Phase7EnrichmentQueue(config={
    'enable_waterfall': True,
    'waterfall_budget': 100.0,
    'waterfall_batch_limit': 100
})
queue_df, resolved_df, stats = phase7.run(missing_pattern_df, unslotted_df, slot_summary_df)

# Convenience function
queue_df, resolved_df, stats = build_enrichment_queue(missing_df, unslotted_df, summary_df)

# Manual queue addition
queue_id = phase7.add_to_queue('company', company_id, company_id, 'pattern_missing')
```

### Phase 8: Output Writer

```python
from pipeline_engine.phases.phase8_output_writer import Phase8OutputWriter, write_pipeline_output

# Full class usage
phase8 = Phase8OutputWriter(config={
    'output_dir': './output',
    'include_timestamp': True
})
summary, stats = phase8.run(
    people_with_emails_df,
    slotted_df,
    unslotted_df,
    slot_summary_df,
    queue_df,
    phase_stats
)

# Convenience function
summary, stats = write_pipeline_output(
    people_with_emails_df, slotted_df, unslotted_df,
    slot_summary_df, queue_df, phase_stats
)
```

---

## 12. Configuration

### Phase 0 Configuration

```python
{
    'bit_warm_threshold': 25  # BIT score threshold for WARM classification
}
```

### Phase 5 Configuration

```python
{
    'enable_waterfall': True,    # Enable on-demand waterfall for missing patterns
    'waterfall_mode': 2,         # 0=Tier0 only, 1=Tier0+1, 2=Full
    'waterfall_config': {}       # Additional waterfall config
}
```

### Phase 6 Configuration

```python
{
    'allow_slot_replacement': True,  # Allow higher seniority to replace
    'min_seniority_diff': 10         # Min score difference to replace
}
```

### Phase 7 Configuration

```python
{
    'max_retries': 3,              # Max retry attempts per item
    'base_retry_delay': 3600,      # Base delay in seconds (1 hour)
    'enable_waterfall': True,      # Enable waterfall processing
    'waterfall_mode': 2,           # 0=Tier0 only, 1=Tier0+1, 2=Full
    'waterfall_budget': None,      # Max budget for waterfall
    'waterfall_batch_limit': 100   # Max items to process per run
}
```

### Phase 8 Configuration

```python
{
    'output_dir': './output',      # Output directory path
    'run_id': None,                # Custom run ID (auto-generated if not provided)
    'include_timestamp': True      # Add timestamp to file names
}
```

---

## 13. Promotion States (HARD LAW)

### Burn-In vs Steady-State

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       PROMOTION STATE ENFORCEMENT                             ║
║                                                                               ║
║   BURN-IN MODE:                                                               ║
║   ├── Duration: First 14 days or 10,000 records (whichever first)            ║
║   ├── Failure tolerance: 10% error rate allowed                              ║
║   ├── Alert severity: All failures logged as WARNING                         ║
║   └── Purpose: Calibration and pattern learning                              ║
║                                                                               ║
║   STEADY-STATE MODE:                                                          ║
║   ├── After promotion gates pass                                              ║
║   ├── Failure tolerance: 2% error rate maximum                               ║
║   ├── Alert severity: Failures > threshold are HIGH/CRITICAL                 ║
║   └── Purpose: Production operation                                           ║
║                                                                               ║
║   RULE: Unexpected errors in steady-state MUST be HIGH severity.             ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### Promotion Gates

| Gate | Requirement | Metric |
|------|-------------|--------|
| G1 | All phase unit tests pass | 100% pass rate |
| G2 | Integration tests pass | 100% pass rate |
| G3 | Burn-in volume achieved | >= 10,000 records processed |
| G4 | Error rate below threshold | < 5% during burn-in |
| G5 | Kill switch tested | Successfully halts pipeline |
| G6 | Correlation ID propagation verified | 100% of records |
| G7 | Signal deduplication tested | No duplicates in 24h window |
| G8 | Local failure table populated correctly | All errors logged |
| G9 | Global error emission verified | HIGH/CRITICAL errors reach shq_error_log |
| G10 | Queue TTL escalation tested | Alerts fire at correct intervals |

### Alert Severity Escalation (Steady-State)

| Error Rate | Duration | Severity | Action |
|------------|----------|----------|--------|
| > 2% | 5 min | WARNING | Monitor |
| > 5% | 5 min | HIGH | Alert on-call |
| > 10% | 5 min | CRITICAL | Auto-halt pipeline |

---

## 14. Production Implementation

### CEO Email Pipeline (Phases 5-8)

**Implementation File:** `hubs/people-intelligence/imo/middle/phases/ceo_email_pipeline.py`

**ADR:** [ADR-003: CEO Email Pipeline Implementation](../adr/ADR-003_CEO_Email_Pipeline_Implementation.md)

#### Supported Slot Types

| Slot | Seniority | Title Keywords |
|------|-----------|----------------|
| CEO | 100 | Chief Executive, President, CEO, Managing Director |
| CFO | 95 | Chief Financial, CFO, VP Finance, Finance Director |
| CTO | 90 | Chief Technology, CTO, VP Engineering |
| CMO | 85 | Chief Marketing, CMO, VP Marketing |
| COO | 85 | Chief Operating, COO, VP Operations |
| HR | 80 | Chief Human Resources, CHRO, HR Director, VP HR |

#### CLI Usage

```bash
# Basic usage (with verification)
doppler run -- python hubs/people-intelligence/imo/middle/phases/ceo_email_pipeline.py <csv_path>

# Skip verification (bulk processing)
doppler run -- python hubs/people-intelligence/imo/middle/phases/ceo_email_pipeline.py <csv_path> --skip-verification

# Specify slot type
doppler run -- python hubs/people-intelligence/imo/middle/phases/ceo_email_pipeline.py <csv_path> --slot-type HR --skip-verification
```

#### Email Verification Providers

| Provider | API | Default | Notes |
|----------|-----|---------|-------|
| EmailVerify.io | REST | Yes | Default provider |
| MillionVerifier | REST | No | Alternative |
| Prospeo | REST | No | Single email mode |

#### Key Features

1. **Multi-slot support** - Single pipeline handles CEO, CFO, HR, CTO, CMO, COO
2. **Skip-verification mode** - Bulk processing without API rate limits
3. **Transaction rollback** - Individual failures don't abort entire batch
4. **ASCII normalization** - Handles accented characters (é→e, ñ→n)
5. **Audit trail** - Full CSV exports for transparency

#### Output Files

| File | Description |
|------|-------------|
| `{slot}_pipeline_audit_{timestamp}.csv` | Complete processing log |
| `{slot}_valid_emails_{timestamp}.csv` | Emails promoted to Neon |
| `{slot}_flagged_emails_{timestamp}.csv` | Verification failures |

---

## 15. FREE State Extraction Pipeline

**Implementation File:** `scripts/state_extraction_pipeline.py`
**ADR:** [ADR-019: FREE Extraction Pipeline Complete](../adr/ADR-019_FREE_Extraction_Pipeline_Complete.md)
**Status:** ✅ COMPLETE (2026-01-30)

### Overview

The FREE State Extraction Pipeline is a 7-stage automated process that extracts executive contact information from company website URLs without any API costs (beyond Neon database).

### Pipeline Stages

| Stage | Name | Function |
|-------|------|----------|
| 1 | Baseline | Count companies, URLs, existing people, slot coverage |
| 2 | Mint Orphans | Create records for companies found in `web_pages_combined` but missing from `company_target` |
| 3 | Initialize Slots | Create empty slot records (CEO, CFO, HR) for companies |
| 4 | **FREE Extraction** | Parse HTML from `web_pages_combined` for executive names/titles |
| 5 | Assign Slots | Match extracted people to appropriate C-suite slots |
| 6 | Generate Emails | Create email addresses using verified company patterns |
| 7 | Final Report | Output stats and remaining paid queue count |

### Source Type Constraints (COMPLIANCE CRITICAL)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    APPROVED SOURCE TYPES - HARD LAW                           ║
║                                                                               ║
║   The FREE extraction pipeline ONLY processes these 4 source types:          ║
║                                                                               ║
║   ✅ leadership_page  - Executive team pages                                  ║
║   ✅ team_page        - Staff/team directories                                ║
║   ✅ about_page       - About us pages with personnel                         ║
║   ✅ blog             - Blog author bios                                      ║
║                                                                               ║
║   EXCLUDED (NOT PROCESSED):                                                   ║
║   ❌ contact_page     - No people data, just addresses                        ║
║   ❌ careers_page     - Job listings, not current executives                  ║
║   ❌ press_page       - Press releases, not reliable people data              ║
║                                                                               ║
║   WARNING: Status checks MUST use same 4 source types or counts are WRONG    ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### Target States

| State | Companies | URLs | Status |
|-------|-----------|------|--------|
| PA | 21,098 | - | ✅ COMPLETE |
| OH | 14,330 | - | ✅ COMPLETE |
| VA | 8,143 | - | ✅ COMPLETE |
| MD | 7,117 | - | ✅ COMPLETE |
| NC | 10,794 | - | ✅ COMPLETE |
| KY | 4,428 | - | ✅ COMPLETE |
| OK | 3,523 | - | ✅ COMPLETE |
| DE | 1,456 | - | ✅ COMPLETE |
| WV | 1,194 | - | ✅ COMPLETE |
| **TOTAL** | **72,083** | - | ✅ ALL COMPLETE |

### Results Summary

| Metric | Value |
|--------|-------|
| **Total People Extracted** | 77,256+ |
| **CEO Slots Filled** | ~37.2% |
| **CFO Slots Filled** | ~11.7% |
| **HR Slots Filled** | ~15.7% |
| **Paid Queue Remaining** | ~27,338 URLs |

### CLI Usage

```bash
# Run extraction for a state
doppler run -- python scripts/state_extraction_pipeline.py --state PA --batch-size 500

# Check status with CORRECT source types
doppler run -- python scripts/correct_status.py
```

### Key Tables

| Table | Purpose |
|-------|---------|
| `web_pages_combined` | Source HTML content (source_type filtered) |
| `company_target` | Company anchor records |
| `company_slot` | Slot assignments (CEO, CFO, HR per company) |
| `people_master` | Extracted person records |
| `email_queue` | Generated email addresses |

---

## 16. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-17 | Initial People Sub-Hub PRD with clean boundaries |
| 2.1 | 2025-12-17 | Hardened: Correlation ID, Signal idempotency, TTL policies, Two-layer errors, Promotion states |
| 2.2 | 2026-01-14 | Added: Production implementation details (CEO Email Pipeline, multi-slot support) |
| 3.0 | 2026-01-30 | Added: FREE State Extraction Pipeline (§15) - 77,256 people extracted across 9 states |

---

*Document Version: 3.0*
*Last Updated: 2026-01-30*
*Owner: People Sub-Hub*
*Doctrine: Bicycle Wheel v1.1 / Barton Doctrine*
