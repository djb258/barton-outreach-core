# PRD — Company Hub (Central Core) v3.0

**Version:** 3.0 (Constitutional Compliance)
**Constitutional Date:** 2026-01-29
**Changes:** Constitutional transformation declaration, CAPTURE/COMPUTE/GOVERN pass mapping, Constants/Variables sections

---

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | IMO-Creator v1.7.0 |
| **Domain Spec Reference** | `doctrine/REPO_DOMAIN_SPEC.md` |
| **CC Layer** | CC-02 |
| **PRD Constitution** | `templates/doctrine/PRD_CONSTITUTION.md` |

---

## 1. Sovereign Reference (CC-01)

| Field | Value |
|-------|-------|
| **Sovereign ID** | CL-01 (Company Lifecycle) |
| **Sovereign Boundary** | Company identity minting and lifecycle state |

---

## 2. Hub Identity (CC-02)

| Field | Value |
|-------|-------|
| **Hub Name** | Company Target |
| **Hub ID** | HUB-COMPANY-TARGET |
| **Doctrine ID** | 04.04.01 |
| **Owner** | Barton Outreach Core |
| **Version** | 3.0 |
| **Waterfall Order** | 1 |

---

## 3. Purpose & Transformation Declaration

### Transformation Statement (REQUIRED)

> **"This hub transforms sovereign company identities and raw domain data (CONSTANTS) into verified company targeting records with email patterns (VARIABLES) through CAPTURE (identity reception from CL), COMPUTE (domain resolution and pattern discovery), and GOVERN (verification and eligibility gating)."**

| Field | Value |
|-------|-------|
| **Transformation Summary** | Sovereign identity → Verified targeting record with email pattern |

### Constants (Inputs)

_Immutable inputs received from outside this hub. Reference: `doctrine/REPO_DOMAIN_SPEC.md §2`_

| Constant | Source | Description |
|----------|--------|-------------|
| `sovereign_company_id` | CL (Company Lifecycle) | Immutable company identity from CL |
| `company_name` | CL (Company Lifecycle) | Canonical company name |
| `company_domain` | CL (Company Lifecycle) | Primary domain from CL |
| `identity_status` | CL (Company Lifecycle) | Identity verification status (PASS/FAIL) |
| `existence_verified` | CL (Company Lifecycle) | Domain existence verification |

### Variables (Outputs)

_Outputs this hub produces. Reference: `doctrine/REPO_DOMAIN_SPEC.md §3`_

| Variable | Destination | Description |
|----------|-------------|-------------|
| `outreach_id` | Outreach Spine, CL (WRITE-ONCE) | Primary targeting identifier |
| `verified_email_pattern` | People Intelligence | Discovered and verified email pattern |
| `target_status` | Downstream Hubs | Company targeting status (PASS/FAIL/IN_PROGRESS) |
| `domain_resolution_status` | BIT Engine | Domain validation result |
| `pattern_confidence` | People Intelligence | Email pattern confidence score |

### Pass Structure

_Constitutional pass mapping per `PRD_CONSTITUTION.md §Pass-to-IMO Mapping`_

| Pass | Type | IMO Layer | Description |
|------|------|-----------|-------------|
| Identity Reception | **CAPTURE** | I (Ingress) | Receive sovereign_company_id and company data from CL |
| Domain Resolution | **COMPUTE** | M (Middle) | Validate domain, discover email pattern (Phases 1-4) |
| Pattern Verification | **COMPUTE** | M (Middle) | Verify pattern with SMTP and sample emails |
| Eligibility Gate | **GOVERN** | O (Egress) | Gate output based on verification status |

### Scope Boundary

| Scope | Description |
|-------|-------------|
| **IN SCOPE** | Domain resolution, email pattern discovery, pattern verification, company matching, BIT signal aggregation, employee data, domain health tracking |
| **OUT OF SCOPE** | Minting sovereign_company_id (CL owns), slot assignment (People owns), DOL data (DOL owns), people state (People owns) |

---

## CT Sub-Hub Live Metrics (2026-02-13)

> **Standard View**: See `docs/DATABASE_OVERVIEW_TEMPLATE.md` for the complete Database Overview format.

### Company Firmographics

| Metric | Count | % of 94,129 |
|--------|-------|-------------|
| **Has Employee Data** | 70,392 | 74.8% |
| **50+ Employees** | 37,493 | 39.8% |
| **Total Employees (50+)** | **16,205,443** | — |
| Email Method | 80,950 | 86.0% |

### Employee Size Bands (50+ only)

| Band | Companies | Total Employees | % |
|------|-----------|-----------------|---|
| 50-100 | 24,179 | 1,233,129 | 64.5% |
| 101-250 | 6,795 | 1,365,795 | 18.1% |
| 501-1,000 | 2,696 | 1,350,696 | 7.2% |
| 1,001-5,000 | 2,657 | 2,659,657 | 7.1% |
| 5,001+ | 1,166 | 9,596,166 | 3.1% |
| **Total** | **37,493** | **16,205,443** | **100%** |

**Note**: Employee counts are Hunter enrichment band minimums (floor estimates). Real totals are higher.

### Domain Health

| Metric | Count | % |
|--------|-------|---|
| Domain Reachable | 52,870 | 85.4% of checked |
| Domain Unreachable | 9,047 | 14.6% of checked |

### Data Sources

| Metric | Source Table |
|--------|-------------|
| Employee Count | `outreach.company_target.employees` |
| Email Method | `outreach.company_target.email_method` |
| Domain Health | `outreach.sitemap_discovery.domain_reachable` |

---

## Hub Ownership Statement

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         COMPANY HUB OWNERSHIP                                 ║
║                                                                               ║
║   This hub OWNS:                                                              ║
║   ├── Company identity (company_id, company_name, EIN)                       ║
║   ├── Domain resolution and validation                                        ║
║   ├── Email pattern discovery and verification                               ║
║   ├── BIT Engine (signal aggregation + decision making)                      ║
║   └── Outreach decisioning (who gets messaged, when, how)                    ║
║                                                                               ║
║   This hub DOES NOT OWN:                                                      ║
║   ├── People lifecycle state initialization                                   ║
║   ├── Email generation for individuals                                        ║
║   ├── Slot assignment                                                         ║
║   ├── DOL filing ingestion                                                    ║
║   ├── Talent Flow detection                                                   ║
║   └── Blog/News signal collection                                             ║
║                                                                               ║
║   Sub-hubs EMIT SIGNALS to this hub. This hub MAKES DECISIONS.               ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 1. Overview

| Attribute | Value |
|-----------|-------|
| **System Name** | Barton Outreach Core |
| **Hub Name** | Company Hub |
| **Hub Type** | Central Core (Master Node) |
| **Owner** | [ASSIGN: Hub Owner] |
| **Version** | 2.1 (Hardened per Barton Doctrine) |
| **Doctrine ID** | 04.04.02.04.00001.001 |

---

## 2. Purpose

The Company Hub is the **central identity authority** and **decision-making core** for the Barton Outreach platform.

### Owns

1. **Company Identity** — The authoritative record of `company_id`, `company_name`, `domain`, `email_pattern`
2. **Domain Resolution** — Validation and verification of company domains
3. **Email Pattern Discovery** — Waterfall-based pattern discovery
4. **BIT Engine** — Signal aggregation and buyer intent scoring
5. **Outreach Decisioning** — Determines who gets messaged based on BIT score

### Does NOT Own

1. **People State** — Managed by People Sub-Hub
2. **Slot Assignment** — Managed by People Sub-Hub
3. **DOL Data** — Managed by DOL Sub-Hub
4. **Talent Flow** — Managed by People Sub-Hub
5. **Blog/News** — Managed by Blog/News Sub-Hub

---

## 3. Owned Processes (Company Identity Pipeline)

### Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 COMPANY IDENTITY PIPELINE (Phases 1-4)                      │
│                      OWNED BY: Company Hub                                   │
└─────────────────────────────────────────────────────────────────────────────┘

    INPUT: Raw company names, domains from ANY sub-hub
           ↓
    ┌──────────────────────────────────────────────────────────────┐
    │ PHASE 1: Company Matching                                     │
    │ - Match input to company_master                               │
    │ - OUTPUT: company_id linkage                                  │
    └──────────────────────────────────────────────────────────────┘
           ↓
    ┌──────────────────────────────────────────────────────────────┐
    │ PHASE 1b: Unmatched Hold Export                              │
    │ - Quarantine no_match, collision, low_confidence             │
    │ - OUTPUT: hold queue for manual review                       │
    └──────────────────────────────────────────────────────────────┘
           ↓
    ┌──────────────────────────────────────────────────────────────┐
    │ PHASE 2: Domain Resolution                                    │
    │ - Resolve and validate company domain                        │
    │ - OUTPUT: company_id + validated domain                      │
    └──────────────────────────────────────────────────────────────┘
           ↓
    ┌──────────────────────────────────────────────────────────────┐
    │ PHASE 3: Email Pattern Waterfall                              │
    │ - Discover email pattern via tiered providers                │
    │ - OUTPUT: company_id + domain + email_pattern                │
    └──────────────────────────────────────────────────────────────┘
           ↓
    ┌──────────────────────────────────────────────────────────────┐
    │ PHASE 4: Pattern Verification                                 │
    │ - Verify pattern with known emails and SMTP                  │
    │ - OUTPUT: verified company identity record                   │
    └──────────────────────────────────────────────────────────────┘
           ↓
    OUTPUT: Company Identity Record (company_id, domain, email_pattern, confidence)
            → Consumed by Sub-Hubs
```

---

### Correlation ID Doctrine (HARD LAW)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       CORRELATION ID ENFORCEMENT                              ║
║                                                                               ║
║   DOCTRINE: correlation_id MUST be propagated unchanged across ALL phases    ║
║             and into the master error log (public.shq_error_log).            ║
║                                                                               ║
║   RULES:                                                                      ║
║   1. Every input to Phases 1-4 MUST include correlation_id                   ║
║   2. Every output from Phases 1-4 MUST include correlation_id                ║
║   3. Every BIT Engine signal MUST include correlation_id                     ║
║   4. Every error logged MUST include correlation_id                          ║
║   5. correlation_id MUST NOT be modified or regenerated mid-pipeline         ║
║                                                                               ║
║   FORMAT: UUID v4 (e.g., "550e8400-e29b-41d4-a716-446655440000")              ║
║   GENERATED BY: Initiating sub-hub or intake process                         ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

### Phase 1: Company Matching

**Owner:** Company Hub
**Purpose:** Match input company references to authoritative `company_master` records.

#### Input Contract

| Field | Type | Required | Source |
|-------|------|----------|--------|
| `correlation_id` | UUID | **YES** | Initiating process (propagate unchanged) |
| `input_company_name` | string | YES | Any Sub-Hub |
| `input_domain` | string | NO | Any Sub-Hub |
| `input_city` | string | NO | Any Sub-Hub |
| `input_state` | string | NO | Any Sub-Hub |
| `requesting_hub` | string | YES | System |

#### Process

1. Normalize company name (strip Inc, LLC, Corp)
2. Try GOLD match (domain lookup)
3. Try SILVER match (exact name)
4. Try BRONZE match (fuzzy with city guardrail)
5. Detect collisions (score_diff < 0.03)

#### Matching Hierarchy

| Tier | Name | Score | Condition |
|------|------|-------|-----------|
| GOLD | Domain Match | 1.0 | Domain matches `company_master.website_url` |
| SILVER | Exact Name | 0.95 | Normalized names match exactly |
| BRONZE | Fuzzy Match | 0.85-0.92 | Jaro-Winkler with city guardrail |

#### Output Contract (Signal)

| Field | Type | Description |
|-------|------|-------------|
| `correlation_id` | UUID | **Propagated unchanged from input** |
| `company_id` | string | Matched company ID or NULL |
| `match_type` | enum | `domain`, `exact`, `fuzzy`, `none` |
| `match_score` | float | 0.0 - 1.0 |
| `is_collision` | bool | True if ambiguous match |

#### Failure Handling

| Failure | Severity | Routes To |
|---------|----------|-----------|
| No match found | MEDIUM | Phase 1b Hold Queue |
| Collision detected | HIGH | Phase 1b Hold Queue |
| Score below 0.85 | LOW | Phase 1b Hold Queue |

---

### Phase 1b: Unmatched Hold Export

**Owner:** Company Hub
**Purpose:** Quarantine unmatched records to prevent invalid processing downstream.

#### Hold Queue TTL Policy (HARD LAW)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       HOLD QUEUE TTL ENFORCEMENT                              ║
║                                                                               ║
║   DOCTRINE: Records in hold queue MUST expire and be purged per TTL policy.  ║
║             Expired records are PERMANENTLY removed - no silent retention.    ║
║                                                                               ║
║   TTL TIERS:                                                                  ║
║   ├── Default:     30 days (auto-purge if unresolved)                        ║
║   ├── Extended-1:  60 days (requires manual extension request)               ║
║   └── Extended-2:  90 days (maximum, requires director approval)             ║
║                                                                               ║
║   AUTO-ESCALATION:                                                            ║
║   ├── Day 7:   Alert to data steward (warning)                               ║
║   ├── Day 21:  Alert to team lead (escalation)                               ║
║   └── Day 28:  Final warning before purge                                     ║
║                                                                               ║
║   PURGE BEHAVIOR:                                                             ║
║   ├── Record moved to purge_archive table (90-day cold storage)              ║
║   ├── Error logged with correlation_id to shq_error_log                      ║
║   └── Metrics updated (hold_queue.purged counter)                            ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

#### Input Contract

| Field | Type | Required |
|-------|------|----------|
| `correlation_id` | UUID | **YES** (propagate unchanged) |
| `unmatched_records` | DataFrame | YES |
| `collision_records` | DataFrame | YES |

#### Output Contract

| Field | Type | Description |
|-------|------|-------------|
| `correlation_id` | UUID | **Propagated unchanged from input** |
| `hold_id` | string | Unique hold queue entry ID |
| `hold_reason` | enum | `no_match`, `collision`, `low_confidence` |
| `collision_candidates` | List[Dict] | If collision, top candidates |
| `queued_at` | datetime | Timestamp |
| `ttl_tier` | enum | `default_30d`, `extended_60d`, `extended_90d` |
| `expires_at` | datetime | Calculated expiration timestamp |
| `escalation_status` | enum | `none`, `warned`, `escalated`, `final_warning` |

#### Hold Queue State Machine

| Current State | Trigger | Next State | Action |
|---------------|---------|------------|--------|
| `queued` | Day 7 | `warned` | Send warning alert |
| `warned` | Day 21 | `escalated` | Send escalation alert |
| `escalated` | Day 28 | `final_warning` | Send final warning |
| `final_warning` | Day 30 | `purged` | Archive and purge |
| Any | Manual extend | `extended` | Reset TTL to new tier |
| Any | Manual resolve | `resolved` | Remove from queue |

---

### Phase 2: Domain Resolution

**Owner:** Company Hub
**Purpose:** Ensure every matched company has a validated domain.

#### Input Contract

| Field | Type | Required |
|-------|------|----------|
| `correlation_id` | UUID | **YES** (propagate unchanged) |
| `company_id` | string | YES |
| `input_domain` | string | NO |

#### Process

1. Check `company_master.website_url`
2. Fall back to input domain if master missing
3. Validate DNS resolution
4. Check MX records
5. Detect parked domains

#### Output Contract (Signal)

| Field | Type | Description |
|-------|------|-------------|
| `correlation_id` | UUID | **Propagated unchanged from input** |
| `company_id` | string | Company ID |
| `resolved_domain` | string | Validated domain |
| `domain_status` | enum | `valid`, `valid_no_mx`, `parked`, `unreachable`, `missing` |
| `has_mx` | bool | Has mail exchange records |

---

### Phase 3: Email Pattern Waterfall

**Owner:** Company Hub
**Purpose:** Discover the email pattern for each company domain.

#### Input Contract

| Field | Type | Required |
|-------|------|----------|
| `correlation_id` | UUID | **YES** (propagate unchanged) |
| `company_id` | string | YES |
| `domain` | string | YES |

#### Waterfall Tiers

| Tier | Cost | Providers | Stop Condition |
|------|------|-----------|----------------|
| 0 | FREE | Firecrawl, ScraperAPI, Google Places | Pattern found (confidence >= 0.7) |
| 1 | $0.001-0.01 | Hunter.io, Clearbit, Apollo | Pattern found (confidence >= 0.7) |
| 2 | $0.05-0.10 | Prospeo, Snov, Clay | Pattern found or exhausted |

#### Output Contract (Signal)

| Field | Type | Description |
|-------|------|-------------|
| `correlation_id` | UUID | **Propagated unchanged from input** |
| `company_id` | string | Company ID |
| `domain` | string | Company domain |
| `email_pattern` | string | Pattern (e.g., `{first}.{last}`) |
| `pattern_source` | enum | `tier_0`, `tier_1`, `tier_2`, `suggested` |
| `confidence` | float | 0.0 - 1.0 |
| `tier_used` | int | 0, 1, or 2 |
| `cost_credits` | float | API cost incurred |

---

### Phase 4: Pattern Verification

**Owner:** Company Hub
**Purpose:** Verify discovered patterns before allowing email generation.

#### Input Contract

| Field | Type | Required |
|-------|------|----------|
| `correlation_id` | UUID | **YES** (propagate unchanged) |
| `company_id` | string | YES |
| `domain` | string | YES |
| `email_pattern` | string | YES |
| `sample_emails` | List[str] | NO |

#### Verification Methods

| Method | Cost | Confidence Boost |
|--------|------|------------------|
| Sample Email Match | FREE | +0.3 |
| MX Record Check | FREE | +0.1 |
| SMTP Verification | $0.003/email | +0.2 |

#### Output Contract (Signal)

| Field | Type | Description |
|-------|------|-------------|
| `correlation_id` | UUID | **Propagated unchanged from input** |
| `company_id` | string | Company ID |
| `email_pattern` | string | Verified pattern |
| `verification_status` | enum | `verified`, `partial`, `failed` |
| `pattern_confidence` | float | 0.0 - 1.0 |

---

## 4. BIT Engine (Signal Aggregation)

**Owner:** Company Hub
**Purpose:** Aggregate signals from all sub-hubs and make outreach decisions.

### BIT Engine Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BIT ENGINE                                     │
│                         OWNED BY: Company Hub                               │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                      SIGNAL AGGREGATION                              │  │
│   │                                                                      │  │
│   │   People Sub-Hub Signals:        DOL Sub-Hub Signals:               │  │
│   │   ├── SLOT_FILLED (+10)          ├── FORM_5500_FILED (+5)           │  │
│   │   ├── SLOT_VACATED (-5)          ├── LARGE_PLAN (+8)                │  │
│   │   ├── EMAIL_VERIFIED (+3)        └── BROKER_CHANGE (+7)             │  │
│   │   └── LINKEDIN_FOUND (+2)                                            │  │
│   │                                   Blog Sub-Hub Signals:              │  │
│   │   Talent Flow Signals:           ├── FUNDING_EVENT (+15)            │  │
│   │   ├── EXECUTIVE_JOINED (+10)     ├── ACQUISITION (+12)              │  │
│   │   ├── EXECUTIVE_LEFT (-5)        ├── LAYOFF (-3)                    │  │
│   │   └── TITLE_CHANGE (+3)          └── LEADERSHIP_CHANGE (+8)         │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                      SCORE CALCULATION                               │  │
│   │                                                                      │  │
│   │   BIT_Score = Σ (signal_impact for all signals)                     │  │
│   │                                                                      │  │
│   │   Score Thresholds:                                                  │  │
│   │   ├── HOT (>= 75): Immediate outreach                               │  │
│   │   ├── WARM (50-74): Nurture sequence                                │  │
│   │   └── COLD (< 50): No outreach                                       │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                      OUTREACH DECISION                               │  │
│   │                                                                      │  │
│   │   ONLY BIT ENGINE MAY DECIDE:                                       │  │
│   │   ├── WHO gets messaged                                             │  │
│   │   ├── WHEN they get messaged                                        │  │
│   │   └── WHAT campaign they enter                                       │  │
│   │                                                                      │  │
│   │   Output: OUTREACH_DECISION signal to Outreach Node                 │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### BIT Engine Input Contract

#### Signal Correlation ID Enforcement (HARD LAW)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║   DOCTRINE: Every signal to BIT Engine MUST include correlation_id.          ║
║             Signals without correlation_id MUST be rejected.                  ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

#### Required Signal Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `correlation_id` | UUID | **YES** | Trace ID for full pipeline lineage |
| `signal_type` | enum | YES | Signal type (see table below) |
| `company_id` | string | YES | Company anchor |
| `source_spoke` | string | YES | Originating sub-hub |
| `emitted_at` | datetime | YES | Signal emission timestamp |
| `metadata` | Dict | NO | Additional signal context |

#### Signal Impact Values

| Signal | Source | Impact |
|--------|--------|--------|
| `SLOT_FILLED` | People Sub-Hub | +10.0 |
| `SLOT_VACATED` | People Sub-Hub | -5.0 |
| `EMAIL_VERIFIED` | People Sub-Hub | +3.0 |
| `LINKEDIN_FOUND` | People Sub-Hub | +2.0 |
| `EXECUTIVE_JOINED` | People Sub-Hub (Talent Flow) | +10.0 |
| `EXECUTIVE_LEFT` | People Sub-Hub (Talent Flow) | -5.0 |
| `FORM_5500_FILED` | DOL Sub-Hub | +5.0 |
| `LARGE_PLAN` | DOL Sub-Hub | +8.0 |
| `BROKER_CHANGE` | DOL Sub-Hub | +7.0 |
| `FUNDING_EVENT` | Blog/News Sub-Hub | +15.0 |
| `ACQUISITION` | Blog/News Sub-Hub | +12.0 |
| `LAYOFF` | Blog/News Sub-Hub | -3.0 |

### BIT Engine Output Contract

| Field | Type | Description |
|-------|------|-------------|
| `correlation_id` | UUID | **Propagated from input signal** |
| `company_id` | string | Company ID |
| `bit_score` | float | Calculated score |
| `category` | enum | `hot`, `warm`, `cold` |
| `outreach_eligible` | bool | True if score >= 50 |
| `campaign_id` | string | Assigned campaign (if eligible) |
| `decision_timestamp` | datetime | When decision was made |

---

## 5. Sub-Hub Registry

| Sub-Hub | Status | Signals Emitted | Parent |
|---------|--------|-----------------|--------|
| **People Sub-Hub** | ACTIVE | `SLOT_FILLED`, `SLOT_VACATED`, `EMAIL_VERIFIED`, `LINKEDIN_FOUND`, `EXECUTIVE_JOINED`, `EXECUTIVE_LEFT` | Company Hub |
| **DOL Sub-Hub** | ACTIVE | `FORM_5500_FILED`, `LARGE_PLAN`, `BROKER_CHANGE` | Company Hub |
| **Blog/News Sub-Hub** | PLANNED | `FUNDING_EVENT`, `ACQUISITION`, `LAYOFF`, `LEADERSHIP_CHANGE` | Company Hub |

---

## 6. Signal Contract Enforcement

### Hard Rules

1. **BIT Engine consumes SIGNALS ONLY** — Never reads raw sub-hub tables
2. **All inter-hub communication is event-based** — No direct database queries across hubs
3. **Sub-hubs may REQUEST company identity creation** — But NEVER create it themselves
4. **Sub-hubs EMIT signals, never DECISIONS** — Only Company Hub (BIT) decides outreach

### Signal Flow Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   People    │     │     DOL     │     │  Blog/News  │
│  Sub-Hub    │     │  Sub-Hub    │     │  Sub-Hub    │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       │ SLOT_FILLED       │ FORM_5500_FILED   │ FUNDING_EVENT
       │ EMAIL_VERIFIED    │ LARGE_PLAN        │ ACQUISITION
       │ EXEC_JOINED       │ BROKER_CHANGE     │ LEADERSHIP_CHG
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
              ╔════════════════════════════╗
              ║       COMPANY HUB          ║
              ║                            ║
              ║   ┌────────────────────┐   ║
              ║   │    BIT ENGINE      │   ║
              ║   │  (Signal → Score)  │   ║
              ║   └─────────┬──────────┘   ║
              ║             │              ║
              ║             ▼              ║
              ║   OUTREACH_DECISION        ║
              ╚════════════╪═══════════════╝
                           │
                           ▼
                  ┌────────────────┐
                  │  Outreach Node │
                  │  (Execution)   │
                  └────────────────┘
```

---

## 7. Guard Rails

| Guard Rail | Type | Threshold | Action |
|------------|------|-----------|--------|
| Company-First | Validation | `company_id = NULL` | STOP processing |
| Collision Detection | Validation | score_diff < 0.03 | Flag for review |
| Fuzzy Match Floor | Validation | score < 0.85 | No match |
| City Guardrail | Validation | score 0.85-0.92 | Require city match |
| API Rate Limit | Rate Limit | Provider-specific | Queue and retry |
| Pattern Confidence | Validation | confidence < 0.5 | Queue for re-discovery |
| BIT Score Threshold | Validation | score < 50 | No outreach |

---

## 8. Kill Switch

| Attribute | Value |
|-----------|-------|
| **Endpoint** | `POST /api/company-hub/kill` |
| **Environment Variable** | `COMPANY_HUB_ENABLED=false` |
| **Activation Criteria** | Error rate > 10% in 5 min, API cost > $100, DB failure |
| **Emergency Contact** | [ASSIGN: On-Call Engineer] |
| **Scope** | Halts Phases 1-4 + BIT Engine |

---

## 9. Error Log Integration (HARD LAW)

### Master Error Log Schema

All errors from Phases 1-4 and BIT Engine MUST be logged to `public.shq_error_log` with correlation_id.

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       ERROR LOGGING ENFORCEMENT                               ║
║                                                                               ║
║   DOCTRINE: Every error MUST include correlation_id for trace lineage.       ║
║             Errors without correlation_id are INVALID and will be rejected.  ║
║                                                                               ║
║   TARGET TABLE: public.shq_error_log                                         ║
║   RETENTION: 90 days (auto-purge after)                                      ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

#### Required Error Log Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `error_id` | UUID | YES | Auto-generated |
| `correlation_id` | UUID | **YES** | Pipeline trace ID |
| `error_code` | string | YES | Standardized error code |
| `error_message` | string | YES | Human-readable message |
| `severity` | enum | YES | `info`, `warning`, `error`, `critical` |
| `component` | string | YES | `phase_1`, `phase_1b`, `phase_2`, `phase_3`, `phase_4`, `bit_engine` |
| `company_id` | string | NO | If available |
| `stack_trace` | text | NO | For debugging |
| `created_at` | datetime | YES | Auto-generated |

#### Error Code Standards

| Code | Component | Description |
|------|-----------|-------------|
| `CH-P1-001` | Phase 1 | No match found |
| `CH-P1-002` | Phase 1 | Collision detected |
| `CH-P1B-001` | Phase 1b | Hold queue full |
| `CH-P1B-002` | Phase 1b | TTL expired (purged) |
| `CH-P2-001` | Phase 2 | Domain unreachable |
| `CH-P2-002` | Phase 2 | Parked domain detected |
| `CH-P3-001` | Phase 3 | All tiers exhausted |
| `CH-P3-002` | Phase 3 | API rate limited |
| `CH-P4-001` | Phase 4 | Verification failed |
| `CH-BIT-001` | BIT Engine | Signal missing correlation_id |
| `CH-BIT-002` | BIT Engine | Invalid company_id |

---

## 10. Observability

### Logs

- `public.shq_error_log` (database) — **MUST include correlation_id**

### Metrics

| Metric | Description |
|--------|-------------|
| `company_hub.phase1_match_rate` | % of inputs matched |
| `company_hub.phase1b_hold_queue_size` | Current hold queue depth |
| `company_hub.phase1b_ttl_expired` | Records purged due to TTL |
| `company_hub.phase3_pattern_found_rate` | % of domains with patterns |
| `company_hub.bit_signals_processed` | Total signals processed |
| `company_hub.bit_signals_rejected` | Signals rejected (missing correlation_id) |
| `company_hub.outreach_decisions` | Decisions made (hot/warm/cold) |

### Alerts

| Alert | Condition |
|-------|-----------|
| High Error Rate | Error rate > 5% |
| Low Match Rate | Phase 1 match rate < 50% |
| API Cost Spike | Cost > $50 in 1 hour |
| BIT Engine Stalled | No signals processed in 10 min |
| Hold Queue Backlog | > 1000 records in hold queue |
| TTL Expiring Soon | > 100 records within 3 days of TTL |

---

## 11. Failure Modes

| Failure | Severity | Remediation |
|---------|----------|-------------|
| Database connection lost | CRITICAL | Halt hub, alert |
| All API providers down | HIGH | Use suggested patterns |
| BIT Engine backlog | MEDIUM | Scale processing |
| Pattern confidence low | LOW | Accept partial |
| Hold queue TTL mass expiry | HIGH | Alert data steward, review batch |
| Signal missing correlation_id | MEDIUM | Reject signal, log error |

---

## 12. Promotion Gates

| Gate | Requirement |
|------|-------------|
| G1 | All unit tests pass |
| G2 | Phase 1-4 integration tests pass |
| G3 | BIT Engine signal processing test pass |
| G4 | Kill switch tested |
| G5 | Rollback procedure verified |
| G6 | Correlation ID propagation verified across all phases |
| G7 | Hold queue TTL escalation tested |
| G8 | Error log integration verified (correlation_id present) |

---

## 13. Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner | | |
| Tech Lead | | |
| Reviewer | | |

---

*Document Version: 3.1*
*Last Updated: 2026-02-13*
*Template: PRD_HUB.md*
*Doctrine: Barton Doctrine v2.0 (Refactored Boundaries)*
