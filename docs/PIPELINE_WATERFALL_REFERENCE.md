# Barton Outreach Core - Complete Pipeline & Waterfall Reference

**Version**: 2.1.0
**Last Updated**: 2025-12-19
**Architecture**: Bicycle Wheel Doctrine v1.1

---

## Architecture Overview

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                     COMPANY HUB                         │
                    │                    (Master Node)                        │
                    │               Phases 1 → 2 → 3 → 4                      │
                    │                                                         │
                    │   ┌─────────────────────────────────────────────────┐   │
                    │   │              BIT ENGINE (Sub-Hub)               │   │
                    │   │         Buyer Intent Scoring & Signals          │   │
                    │   └─────────────────────────────────────────────────┘   │
                    └───────────────────────────┬─────────────────────────────┘
                                                │
              ┌─────────────────────────────────┼─────────────────────────────┐
              │                                 │                             │
              ▼                                 ▼                             ▼
┌─────────────────────────────────┐   ┌─────────────────┐          ┌─────────────────┐
│         PEOPLE SPOKE            │   │    DOL SPOKE    │          │   BLOG SPOKE    │
│        (Spoke #1)               │   │   (Spoke #2)    │          │   (Spoke #3)    │
│   Phases 0, 5, 6, 7, 8          │   │  EIN → Signal   │          │   [PLANNED]     │
│                                 │   │                 │          │                 │
│ ┌─────────────────────────────┐ │   └─────────────────┘          └─────────────────┘
│ │    TALENT FLOW (Sub-Hub)    │ │
│ │   Movement Detection &      │ │
│ │   Job Change Tracking       │ │
│ └─────────────────────────────┘ │
│                                 │
│ ┌─────────────────────────────┐ │
│ │  EMAIL VERIFICATION         │ │
│ │     (Sub-Wheel)             │ │
│ │   MillionVerifier API       │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

**Golden Rule**: No spoke can process without `company_id` + `domain` + `email_pattern` from Company Hub.

---

## 1. COMPANY HUB (Master Node)

**Purpose**: Resolve company identity. ALL data anchors here first.

**Phases**: 1 → 2 → 3 → 4 (sequential, must complete in order)

---

### Phase 1: Company Matching

| Attribute | Details |
|-----------|---------|
| **File** | `hub/company/phases/phase1_company_matching.py` |
| **Input** | People DataFrame + Company Master |
| **Output** | Matched companies with confidence scores |

#### Matching Waterfall (Priority Order)

| Tier | Match Type | Score | Logic | Tools |
|------|-----------|-------|-------|-------|
| 🥇 GOLD | Domain | 1.00 | Exact domain lookup | `normalize_domain()` |
| 🥈 SILVER | Exact Name | 0.95 | Normalized name match | `normalize_company_name()` |
| 🥉 BRONZE | Fuzzy Name | 0.85-0.92 | Jaro-Winkler + city guardrail | `jaro_winkler_similarity()`, `apply_city_guardrail()` |

**Collision Detection**: Top 2 candidates within 0.03 score → flag for manual review

---

### Phase 2: Domain Resolution

| Attribute | Details |
|-----------|---------|
| **File** | `hub/company/phases/phase2_domain_resolution.py` |
| **Input** | Matched companies from Phase 1 |
| **Output** | Companies with validated domains |

#### Resolution Waterfall

| Step | Source | Action | Tools |
|------|--------|--------|-------|
| 1 | Company Master | Try `website_url`, then `domain` | Database lookup |
| 2 | Input Record | Fallback to `company_domain` | Field extraction |
| 3 | Validation | DNS + MX record check | `verify_domain_dns()`, `verify_mx_records()` |
| 4 | Queue | Mark for enrichment if missing | Queue manager |

**Domain Status**: VALID, VALID_NO_MX, PARKED, UNREACHABLE, MISSING

---

### Phase 3: Email Pattern Waterfall

| Attribute | Details |
|-----------|---------|
| **File** | `hub/company/phases/phase3_email_pattern_waterfall.py` |
| **Input** | Companies with domains from Phase 2 |
| **Output** | Companies with discovered email patterns |

#### Provider Waterfall (Stops on First Pattern Found)

##### TIER 0 - FREE ($0.00 - $0.005/call)

| Provider | Cost | Purpose | Rate Limit | API |
|----------|------|---------|------------|-----|
| **Direct Scraper** | $0.00 | HTTP scrape /contact, /about, /team | 5/sec | None (HTTP) |
| **Firecrawl** | $0.0001 | Website → markdown conversion | 5/min | `api.firecrawl.dev` |
| **Google CSE** | $0.005 | Find company website via search | 10/sec | `googleapis.com/customsearch` |
| **Google Places** | $0.003 | Business verification | 5/sec | `maps.googleapis.com` |
| **ScraperAPI** | $0.002 | Proxy-based scraping | 2/sec | `scraperapi.com` |

##### TIER 1 - LOW COST ($0.005 - $0.01/call)

| Provider | Cost | Purpose | Rate Limit | API |
|----------|------|---------|------------|-----|
| **Hunter.io** | $0.008 | Domain → email pattern + samples | 1/sec | `api.hunter.io/v2/domain-search` |
| **Apollo.io** | $0.005 | People search + emails | 2/sec | `api.apollo.io/v1/mixed_people/search` |
| **Clay** | $0.01 | Multi-source enrichment | 1/sec | `api.clay.com/v1/enrich` |

##### TIER 1.5 - MID COST ($0.003 - $0.004/call)

| Provider | Cost | Purpose | Rate Limit | API |
|----------|------|---------|------------|-----|
| **Prospeo** | $0.003 | Pattern discovery + verification | Conservative | `api.prospeo.io/v1/domain-search` |
| **Snov.io** | $0.004 | Email finder (2-step API) | Strict | `api.snov.io/v1/get-domain-emails` |

##### TIER 2 - PREMIUM ($0.02 - $0.03/call)

| Provider | Cost | Purpose | Rate Limit | API |
|----------|------|---------|------------|-----|
| **Clearbit** | $0.02 | Company enrichment | 5/sec | `company.clearbit.com/v2` |
| **PDL** | $0.03 | Enterprise people data | 0.5/sec | `api.peopledatalabs.com` |
| **ZenRows** | $0.005 | JS rendering + anti-bot | 2/sec | `api.zenrows.com` |

##### TIER 3 - ENTERPRISE ($0.15+/call)

| Provider | Cost | Purpose | Rate Limit | API |
|----------|------|---------|------------|-----|
| **ZoomInfo** | $0.15 | Org charts, intent data | Negotiated | Enterprise API |

#### Fallback Patterns (if all providers fail)

| Pattern | Format | Likelihood |
|---------|--------|------------|
| `{first}.{last}` | john.smith@domain.com | 95% |
| `{first}{last}` | johnsmith@domain.com | 85% |
| `{f}{last}` | jsmith@domain.com | 80% |
| `{first}_{last}` | john_smith@domain.com | 75% |
| `{f}.{last}` | j.smith@domain.com | 70% |

---

### Phase 4: Pattern Verification

| Attribute | Details |
|-----------|---------|
| **File** | `hub/company/phases/phase4_pattern_verification.py` |
| **Input** | Companies with patterns from Phase 3 |
| **Output** | Verified patterns ready for spokes |

#### Verification Waterfall

| Step | Method | Purpose | Tools |
|------|--------|---------|-------|
| 1 | Known Emails Test | Generate from pattern → compare | `_test_pattern_against_known_emails()` |
| 2 | MX Record Check | Verify domain can receive email | `_check_mx_records()` (cached) |
| 3 | SMTP Verification | Test actual delivery (optional) | `_smtp_verify()` |
| 4 | MillionVerifier | Email validation API | `$0.001-$0.004/email` |

**Verification Status**: VERIFIED, LIKELY_VALID, UNVERIFIED, FAILED, SKIPPED

---

### BIT ENGINE (Sub-Hub of Company Hub)

| Attribute | Details |
|-----------|---------|
| **Location** | `hub/company/bit_engine.py` |
| **Purpose** | Calculate Buyer Intent Tool score from signals |
| **Status** | PLANNED |

#### Signal Sources

| Source | Signal Type | Impact | Dedup Window |
|--------|-------------|--------|--------------|
| DOL Spoke | FORM_5500_FILED | +5.0 | 365 days |
| DOL Spoke | LARGE_PLAN (≥500 participants) | +8.0 | 365 days |
| DOL Spoke | BROKER_CHANGE | +7.0 | 365 days |
| People Spoke | SLOT_FILLED | +3.0 | 24 hours |
| People Spoke | EMAIL_VERIFIED | +2.0 | 24 hours |
| Talent Flow | EXECUTIVE_JOINED | +10.0 | 365 days |
| Talent Flow | EXECUTIVE_LEFT | +6.0 | 365 days |
| Blog Spoke | NEWS_MENTION | +1.0 | 24 hours |

#### BIT Score Calculation

```
BIT_SCORE = Σ(signal_impact × recency_decay × source_weight)

Where:
- recency_decay = 1.0 for <7 days, 0.8 for 7-30 days, 0.5 for 30-90 days
- source_weight = 1.0 for DOL, 0.8 for TalentFlow, 0.6 for People
```

---

## 2. PEOPLE SPOKE (Phases 0, 5, 6, 7, 8)

**Purpose**: Process people after company anchor exists. Generate emails, assign to slots, track movement.

**Anchor Requirement**: Must have valid `company_id` from Company Hub

---

### Phase 0: People Ingest

| Attribute | Details |
|-----------|---------|
| **File** | `spokes/people/phases/phase0_people_ingest.py` |
| **Input** | Raw people records |
| **Output** | Classified people records |

#### Classification Waterfall (First Match Wins)

| Priority | Condition | Classification | Action |
|----------|-----------|----------------|--------|
| 1 | Missing company_id | SUSPECT | Route to matching |
| 2 | Past meeting flag | APPOINTMENT | Priority processing |
| 3 | Historical reply | WARM | Track engagement |
| 4 | TalentFlow movement | TALENTFLOW_WARM | Monitor changes |
| 5 | BIT score ≥ 25 | WARM | Prioritize outreach |
| 6 | Default | SUSPECT | Standard processing |

---

### Phase 5: Email Generation

| Attribute | Details |
|-----------|---------|
| **File** | `spokes/people/phases/phase5_email_generation.py` |
| **Input** | Matched people + Pattern DataFrame |
| **Output** | People with generated emails |

#### Email Generation Waterfall

| Step | Source | Confidence Level | Tools |
|------|--------|------------------|-------|
| 1 | Verified pattern (Phase 4) | VERIFIED | `apply_pattern()` |
| 2 | Derived from known emails | DERIVED | Pattern extraction |
| 3 | On-demand waterfall | WATERFALL | Provider APIs |
| 4 | Fallback pattern | LOW_CONFIDENCE | Common patterns |

---

### Phase 6: Slot Assignment

| Attribute | Details |
|-----------|---------|
| **File** | `spokes/people/phases/phase6_slot_assignment.py` |
| **Input** | People with emails |
| **Output** | Slotted + unslotted people |

#### Slot Hierarchy (HR-Focused)

| Slot | Seniority Score | Keywords |
|------|-----------------|----------|
| **CHRO** | 100 | chief hr, chief people, chro, cpo, vp hr, svp hr, evp hr |
| **HR_MANAGER** | 80 | hr director, hr manager, head of hr, hr lead |
| **BENEFITS_LEAD** | 60 | benefits director, total rewards, compensation |
| **PAYROLL_ADMIN** | 50 | payroll director, payroll manager |
| **HR_SUPPORT** | 30 | hr coordinator, hr specialist, hrbp, hr generalist |

#### Assignment Rules

1. **One person per slot per company**
2. **Higher seniority wins conflicts** (score difference ≥ 10 to replace)
3. **Displaced people → enrichment queue**

---

### Phase 7: Enrichment Queue

| Attribute | Details |
|-----------|---------|
| **File** | `spokes/people/phases/phase7_enrichment_queue.py` |
| **Input** | Missing patterns + unslotted people |
| **Output** | Prioritized enrichment queue |

#### Queue Priority

| Priority | Reasons |
|----------|---------|
| **HIGH (1)** | PATTERN_MISSING, SLOT_EMPTY_CHRO, SLOT_EMPTY_BENEFITS, MISSING_COMPANY_ID |
| **MEDIUM (2)** | PATTERN_LOW_CONFIDENCE, SLOT_EMPTY_HR_MANAGER, SLOT_COLLISION |
| **LOW (3)** | SLOT_EMPTY_HR_SUPPORT, EMAIL_LOW_CONFIDENCE, MISSING_NAME |

#### Retry Logic

- **Max retries**: 3
- **Backoff**: `base_delay × 2^retry_count`
- **Base delay**: 1 hour
- **Max delay**: 24 hours

---

### Phase 8: Output Writer

| Attribute | Details |
|-----------|---------|
| **File** | `spokes/people/phases/phase8_output_writer.py` |
| **Input** | All phase outputs |
| **Output** | CSV files + summary |

#### Output Files

```
output/
├── people_final.csv        # All people with emails + slots
├── slot_assignments.csv    # Slot assignments by company
├── enrichment_queue.csv    # Items needing enrichment
└── pipeline_summary.txt    # Human-readable summary
```

---

### TALENT FLOW (Sub-Hub of People Spoke)

| Attribute | Details |
|-----------|---------|
| **Location** | `spokes/people/talent_flow/` |
| **Purpose** | Detect job changes, executive movement |
| **Status** | SHELL (structure exists, logic pending) |

#### Movement Detection

| Movement Type | Signal | Impact | Detection Method |
|---------------|--------|--------|------------------|
| Executive Joined | EXECUTIVE_JOINED | +10.0 | LinkedIn monitoring |
| Executive Left | EXECUTIVE_LEFT | +6.0 | LinkedIn monitoring |
| Title Change | TITLE_PROMOTED | +4.0 | Title comparison |
| Company Change | COMPANY_CHANGED | +8.0 | Company ID change |

#### Integration Points

- **Input**: LinkedIn profile updates, Apollo alerts
- **Output**: Signals to BIT Engine, WARM classification in Phase 0

---

### EMAIL VERIFICATION (Sub-Wheel of People Spoke)

| Attribute | Details |
|-----------|---------|
| **Location** | `spokes/people/sub_wheels/email_verification/` |
| **Purpose** | Verify generated emails work |

#### Components

| Component | Purpose | Tool |
|-----------|---------|------|
| Pattern Guesser | Generate email from pattern | Internal |
| Bulk Verifier | Verify with API | MillionVerifier |

#### MillionVerifier Results

| Code | Meaning | Action |
|------|---------|--------|
| `ok` | Valid email | Accept |
| `catch_all` | Risky but deliverable | Accept |
| `invalid` | Bad format | Reject |
| `disposable` | Temporary email | Reject |
| `role` | info@, support@ | Accept |
| `risky` | Deliverable but risky | Accept |
| `unknown` | Cannot verify | Reject |

---

## 3. DOL SPOKE (Department of Labor)

**Purpose**: Process Form 5500 filings, match to companies via EIN, send signals to BIT Engine.

| Attribute | Details |
|-----------|---------|
| **File** | `spokes/dol/dol_spoke.py` |
| **Input** | Form5500Record or ScheduleARecord |
| **Output** | Signals to BIT Engine |

---

### Data Sources

| Form | Scope | Records | Key Fields |
|------|-------|---------|------------|
| **Form 5500** | Large plans (≥100) | ~800K | EIN, plan_name, participants, assets |
| **Form 5500-SF** | Small plans (<100) | ~600K | EIN, plan_name, participants |
| **Schedule A** | Insurance | ~336K | broker, carrier, renewal dates |

---

### Processing Waterfall

| Step | Action | Tools |
|------|--------|-------|
| 1 | Validate correlation_id | `validate_correlation_id()` (FAIL HARD) |
| 2 | Normalize EIN | Remove hyphens, validate 9 digits |
| 3 | Lookup company | `_lookup_company_by_ein()` (exact match only) |
| 4 | Hub Gate validation | `validate_company_anchor()` |
| 5 | Emit signals | `_send_signal()` with 365-day dedup |

---

### EIN Matching Strategy

| Principle | Implementation |
|-----------|----------------|
| **FAIL CLOSED** | Exact match only, no fuzzy |
| **Deterministic** | No ML/heuristics |
| **Reproducible** | Same input → same output |

#### Backfill Algorithm (Initial Population)

| Step | Match On | Threshold |
|------|----------|-----------|
| 1 | State | Exact match |
| 2 | City | Exact (case-insensitive) |
| 3 | Name | Trigram similarity > 0.8 |

---

### Signal Emission

| Signal | Impact | Condition | Dedup |
|--------|--------|-----------|-------|
| FORM_5500_FILED | +5.0 | Any valid filing | 365 days |
| LARGE_PLAN | +8.0 | ≥500 participants | 365 days |
| BROKER_CHANGE | +7.0 | Broker changed | 365 days |

**Dedup Key Format**: `{signal_name}:{company_id}:{filing_year}`

---

### Import Pipeline

```
DOL CSV Files (Annual FOIA Release)
│
├── F_5500_2023_latest.csv
│   └─→ spokes/dol/importers/import_5500.py
│       └─→ output/form_5500_staging.csv
│           └─→ marketing.form_5500_staging (Neon table)
│               └─→ CALL process_5500_staging()
│
├── F_5500_SF_2023_latest.csv
│   └─→ spokes/dol/importers/import_5500_sf.py
│       └─→ output/form_5500_sf_staging.csv
│
└── F_SCH_A_2023_latest.csv
    └─→ spokes/dol/importers/import_schedule_a.py
        └─→ output/schedule_a_staging.csv (13 columns, ~336K rows)
```

---

## 4. COMPLETE DATA FLOW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              RAW INPUT                                       │
│                    (CSV, API, Manual Upload)                                │
└─────────────────────────────────────────────┬───────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            COMPANY HUB                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  PHASE 1    │  │  PHASE 2    │  │  PHASE 3    │  │  PHASE 4    │        │
│  │  Matching   │─▶│  Domain     │─▶│  Pattern    │─▶│  Verify     │        │
│  │             │  │  Resolution │  │  Waterfall  │  │             │        │
│  │ GOLD/SILVER │  │ DNS/MX      │  │ Tier 0→1→2  │  │ MX/SMTP/    │        │
│  │ /BRONZE     │  │ Check       │  │ Providers   │  │ MillionVerif│        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         BIT ENGINE (Sub-Hub)                          │  │
│  │   Collects signals from all spokes → Calculates BIT Score            │  │
│  │   Signal Types: FORM_5500_FILED, LARGE_PLAN, SLOT_FILLED, etc.       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────┬────────────────────────────────────┘
                                         │
                                         │ company_id + domain + email_pattern
                                         │ (REQUIRED FOR ALL SPOKES)
                                         │
         ┌───────────────────────────────┴───────────────────────────────┐
         │                                                               │
         ▼                                                               ▼
┌────────────────────────────────────────┐      ┌────────────────────────────┐
│            PEOPLE SPOKE                │      │         DOL SPOKE          │
│  ┌──────────────────────────────────┐  │      │  ┌──────────────────────┐  │
│  │ Phase 0: Ingest & Classify       │  │      │  │ EIN Normalization    │  │
│  │ Phase 5: Email Generation        │  │      │  │ Company Lookup       │  │
│  │ Phase 6: Slot Assignment         │  │      │  │ Hub Gate Validation  │  │
│  │ Phase 7: Enrichment Queue        │  │      │  │ Signal Emission      │  │
│  │ Phase 8: Output Writer           │  │      │  │ (365-day dedup)      │  │
│  └──────────────────────────────────┘  │      │  └──────────────────────┘  │
│                                        │      │                            │
│  ┌──────────────────────────────────┐  │      │  Signals to BIT Engine:    │
│  │     TALENT FLOW (Sub-Hub)        │  │      │  • FORM_5500_FILED (+5)    │
│  │  Movement detection, job changes │  │      │  • LARGE_PLAN (+8)         │
│  │  LinkedIn monitoring             │  │      │  • BROKER_CHANGE (+7)      │
│  │  Signals: EXEC_JOINED/LEFT       │  │      │                            │
│  └──────────────────────────────────┘  │      └────────────────────────────┘
│                                        │
│  ┌──────────────────────────────────┐  │
│  │  EMAIL VERIFICATION (Sub-Wheel)  │  │
│  │  MillionVerifier API             │  │
│  │  Bulk + Real-time verification   │  │
│  └──────────────────────────────────┘  │
└────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│              OUTPUT FILES              │
│  • people_final.csv                    │
│  • slot_assignments.csv                │
│  • enrichment_queue.csv                │
│  • pipeline_summary.txt                │
└────────────────────────────────────────┘
```

---

## 5. PROVIDER COST REFERENCE

### Waterfall Order (Cost-Optimized)

```
TIER 0 (FREE) ────────────────────────────────────────────────
  Direct Scraper    $0.00       HTTP to /contact, /about
  Firecrawl         $0.0001     Website → markdown
  Google CSE        $0.005      Find company website
  Google Places     $0.003      Business verification
  [STOP if pattern found]

TIER 1 (LOW COST) ────────────────────────────────────────────
  Hunter.io         $0.008      Domain → email pattern
  Apollo.io         $0.005      People + email search
  Clay              $0.01       Multi-source enrichment
  [STOP if pattern found]

TIER 1.5 (MID COST) ──────────────────────────────────────────
  Prospeo           $0.003      Pattern + verification
  Snov.io           $0.004      Email finder (2-step)
  [STOP if pattern found]

TIER 2 (PREMIUM) ─────────────────────────────────────────────
  Clearbit          $0.02       Company enrichment
  PDL               $0.03       Enterprise people data
  ZenRows           $0.005      JS rendering
  [STOP if pattern found]

TIER 3 (ENTERPRISE) ──────────────────────────────────────────
  ZoomInfo          $0.15       Org charts, intent data
```

### Rate Limits

| Provider | Limit | Notes |
|----------|-------|-------|
| Direct Scraper | 5/sec | Be nice to servers |
| Firecrawl | 5/min | Strict |
| Google CSE | 10/sec | Within quota |
| Hunter | 1/sec | Very strict |
| Apollo | 2/sec | Moderate |
| Clearbit | 5/sec | Generous |
| PDL | 0.5/sec | Enterprise |
| **GLOBAL** | 5/sec | Across ALL providers |

---

## 6. DOCTRINE ENFORCEMENT

### Correlation ID (MANDATORY)

Every phase `run()` method requires `correlation_id`:

```python
from ops.enforcement.correlation_id import validate_correlation_id

correlation_id = validate_correlation_id(
    correlation_id,
    "company.identity.matching.phase1",
    "Phase 1"
)
# Raises CorrelationIDError if invalid (FAIL HARD)
```

### Hub Gate (Company Anchor)

All spokes must validate company anchor:

```python
from ops.enforcement.hub_gate import validate_company_anchor, GateLevel

result = validate_company_anchor(
    record=record,
    level=GateLevel.COMPANY_ID_ONLY,  # or FULL for domain+pattern
    process_id="people.lifecycle.email.phase5",
    correlation_id=correlation_id,
    fail_hard=True  # or False for soft validation
)
```

### Signal Deduplication

Prevent duplicate signals:

```python
from ops.enforcement.signal_dedup import should_emit_signal

if should_emit_signal("FORM_5500_FILED", company_id, correlation_id):
    bit_engine.create_signal(...)
# Dedup windows: 24h (operational), 365d (structural)
```

---

## 7. ERROR CODES

| Code | Meaning | Severity |
|------|---------|----------|
| HUB-P1-001 | Company matching - no correlation_id | CRITICAL |
| HUB-P2-001 | Domain resolution - no correlation_id | CRITICAL |
| HUB-P3-002 | Pattern waterfall - no provider available | ERROR |
| PSH-P0-001 | People ingest - no correlation_id | CRITICAL |
| PSH-P0-002 | People ingest - hub gate failed | WARNING |
| PSH-P6-003 | Slot assignment - title not recognized | WARNING |
| DOL-GEN-001 | DOL processing - no correlation_id | CRITICAL |
| DOL-EIN-003 | EIN lookup - no company found | WARNING |
| ENF-CID-001 | Correlation ID missing | CRITICAL |
| ENF-HUB-001 | Hub gate - missing company_id | ERROR |

---

## 8. KEY FILES REFERENCE

### Company Hub
- `hub/company/phases/phase1_company_matching.py`
- `hub/company/phases/phase2_domain_resolution.py`
- `hub/company/phases/phase3_email_pattern_waterfall.py`
- `hub/company/phases/phase4_pattern_verification.py`
- `hub/company/bit_engine.py`

### People Spoke
- `spokes/people/phases/phase0_people_ingest.py`
- `spokes/people/phases/phase5_email_generation.py`
- `spokes/people/phases/phase6_slot_assignment.py`
- `spokes/people/phases/phase7_enrichment_queue.py`
- `spokes/people/phases/phase8_output_writer.py`
- `spokes/people/sub_wheels/email_verification/`

### DOL Spoke
- `spokes/dol/dol_spoke.py`
- `spokes/dol/ein_matcher.py`
- `spokes/dol/importers/import_5500.py`
- `spokes/dol/importers/import_schedule_a.py`

### Enrichment
- `ctb/sys/enrichment/agents/tier0/` (free providers)
- `ctb/sys/enrichment/provider_benchmark/` (cost tracking)
- `ops/providers/providers.py` (provider registry)

### Enforcement
- `ops/enforcement/correlation_id.py`
- `ops/enforcement/hub_gate.py`
- `ops/enforcement/signal_dedup.py`
- `ops/enforcement/error_codes.py`

---

*Document generated from codebase analysis - 2025-12-19*
