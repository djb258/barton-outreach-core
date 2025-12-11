# Pipeline Engine Architecture

## Core Principle: Hub-and-Spoke Design

**THE COMPANY HUB IS THE MASTER NODE.**

Everything in this system is gravity-bound to the Company Hub. There is no valid pipeline that does not first anchor to a company record.

---

## Hub-and-Spoke Model

```
                                    SPOKE NODES
                                    (Satellites)
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         │                               │                               │
         ▼                               ▼                               ▼
┌─────────────────┐            ┌─────────────────┐            ┌─────────────────┐
│                 │            │                 │            │                 │
│   PEOPLE NODE   │            │    DOL NODE     │            │   BLOG NODE     │
│   (Spoke #1)    │            │   (Spoke #2)    │            │   (Spoke #3)    │
│                 │            │                 │            │   [PLANNED]     │
│  Status: ACTIVE │            │  Status: ACTIVE │            │                 │
└────────┬────────┘            └────────┬────────┘            └────────┬────────┘
         │                               │                               │
         │                               │                               │
         └───────────────────────────────┼───────────────────────────────┘
                                         │
                                         ▼
                           ┌─────────────────────────────┐
                           │                             │
                           │       COMPANY HUB           │
                           │      (Master Node)          │
                           │                             │
                           │  • company_id               │
                           │  • company_name             │
                           │  • domain                   │
                           │  • email_pattern            │
                           │  • industry_class           │
                           │  • slots                    │
                           │                             │
                           │      Status: ACTIVE         │
                           └─────────────────────────────┘
                                         │
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         │                               │                               │
         ▼                               ▼                               ▼
┌─────────────────┐            ┌─────────────────┐            ┌─────────────────┐
│                 │            │                 │            │                 │
│  TALENT FLOW    │            │   BIT ENGINE    │            │    OUTREACH     │
│    NODE         │            │     NODE        │            │      NODE       │
│  (Spoke #4)     │            │   (Spoke #5)    │            │   (Spoke #6)    │
│                 │            │                 │            │                 │
│  Status: SHELL  │            │  Status: PLANNED│            │  Status: PLANNED│
└─────────────────┘            └─────────────────┘            └─────────────────┘
```

---

## Node Registry

| Node | Type | Status | Description | Pipeline Location |
|------|------|--------|-------------|-------------------|
| **Company** | HUB | ACTIVE | Master node - all data anchors here | `phases/phase1-4` |
| **People** | SPOKE | ACTIVE | Titles, emails, slot assignments | `phases/phase5-8` |
| **DOL** | SPOKE | ACTIVE | Form 5500 filings, renewal dates | `ctb/sys/enrichment/dol/` |
| **Blog** | SPOKE | PLANNED | News, sentiment, competitor intel | TBD |
| **Talent Flow** | SPOKE | SHELL | Movement detection, job changes | `phases/talentflow_phase0` |
| **BIT Engine** | SPOKE | PLANNED | Buyer intent scoring | TBD |
| **Outreach** | SPOKE | PLANNED | Campaign targeting, sequences | TBD |

---

```
                           ┌─────────────────────────────────┐
                           │                                 │
                           │      COMPANY NODE (MASTER)      │
                           │                                 │
                           │  • company_id                   │
                           │  • company_name (normalized)    │
                           │  • domain                       │
                           │  • industry_class               │
                           │  • email_pattern                │
                           │  • slots (CHRO/HR/Benefits/     │
                           │          Payroll)               │
                           │                                 │
                           └─────────────────────────────────┘
                                          │
            ┌─────────────────────────────┼─────────────────────────────┐
            │                             │                             │
            ▼                             ▼                             ▼
   ┌─────────────────┐          ┌─────────────────┐          ┌─────────────────┐
   │  PEOPLE NODE    │          │   DOL NODE      │          │   BLOG NODE     │
   │                 │          │                 │          │                 │
   │  • Titles       │          │  • 5500 filings │          │  • Sentiment    │
   │  • Slots        │          │  • Renewal dates│          │  • Events       │
   │  • Emails       │          │  • Participants │          │  • Competitor   │
   │  • LinkedIn     │          │  • Assets       │          │    intel        │
   └─────────────────┘          └─────────────────┘          └─────────────────┘
            │                             │                             │
            │                             │                             │
            ▼                             │                             ▼
   ┌─────────────────┐                    │                  ┌─────────────────┐
   │  TALENT FLOW    │◄───────────────────┘                  │   BIT ENGINE    │
   │                 │                                       │                 │
   │  • Movement logs│                                       │  • Intent score │
   │  • Job changes  │                                       │  • Triggers     │
   │  • Promotions   │                                       │  • Signals      │
   └─────────────────┘                                       └─────────────────┘
            │                                                         │
            │                                                         │
            └────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
                           ┌─────────────────────────────────┐
                           │         OUTREACH NODE           │
                           │                                 │
                           │  • Campaign targeting           │
                           │  • Sequence triggers            │
                           │  • Engagement tracking          │
                           └─────────────────────────────────┘
```

---

## Why Company-First?

### Nothing Exists Without a Company Anchor

| Node | Why It Needs Company First |
|------|---------------------------|
| **People** | People do not stand alone — they attach to a company. A person without a company_id is unroutable. |
| **Talent Flow** | Movement events pivot around a company change. "John left X for Y" requires both X and Y to be valid companies. |
| **DOL Data** | Form 5500 filings must map into a company. EIN matching, plan data — all meaningless without company anchor. |
| **Blog/News** | Signals feed into company intelligence. Sentiment analysis requires knowing WHICH company. |
| **BIT Scoring** | Intent scoring is impossible without a company anchor. Scores attach to companies, not floating entities. |
| **Outreach** | You cannot email a person who isn't linked to a company with a valid domain and pattern. |

---

## The Company Identity Pipeline (Phases 1-4)

This is **THE FOUNDATION**. Before any spoke can function, the company must be:
1. Matched/created in company_master
2. Enriched with domain
3. Enriched with email pattern
4. Verified

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    COMPANY IDENTITY PIPELINE                              │
│                    (Must Complete Before Any Spoke)                       │
└──────────────────────────────────────────────────────────────────────────┘

    INPUT: Raw company name, optional domain
           │
           ▼
    ┌──────────────────────────────────────────────────────────────┐
    │ PHASE 1: Company Matching                                     │
    │ • Domain match (GOLD = 1.0)                                  │
    │ • Exact name match (SILVER = 0.95)                           │
    │ • Fuzzy match with city guardrail (BRONZE = 0.85-0.92)      │
    │ OUTPUT: company_id linkage OR → HOLD queue                   │
    └──────────────────────────────────────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────────────────────────────────────┐
    │ PHASE 1b: Unmatched Hold Export                              │
    │ • No premature enrichment of unanchored records              │
    │ • Export to HOLD CSV for later processing                    │
    │ OUTPUT: people_unmatched_hold.csv                            │
    └──────────────────────────────────────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────────────────────────────────────┐
    │ PHASE 2: Domain Resolution                                    │
    │ • Pull domain from company_master                            │
    │ • Validate DNS/MX records                                    │
    │ • Flag for Tier 0 enrichment if missing                      │
    │ OUTPUT: company_id + validated domain                        │
    └──────────────────────────────────────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────────────────────────────────────┐
    │ PHASE 3: Email Pattern Waterfall                              │
    │ • Tier 0 (Free): Firecrawl, WebScraper, Google Places       │
    │ • Tier 1 (Low Cost): Hunter.io, Clearbit, Apollo            │
    │ • Tier 2 (Premium): Prospeo, Snov, Clay                     │
    │ OUTPUT: domain + email_pattern                               │
    └──────────────────────────────────────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────────────────────────────────────┐
    │ PHASE 4: Pattern Verification                                 │
    │ • Test pattern against known emails                          │
    │ • MX record verification                                     │
    │ • Confidence scoring                                         │
    │ OUTPUT: verified_pattern + confidence_score                  │
    └──────────────────────────────────────────────────────────────┘
           │
           ▼
    COMPANY IS NOW READY TO ANCHOR SPOKES
```

---

## Spoke Pipelines (All Require Company Anchor)

### People Pipeline (Phases 5-8)
**Prerequisite**: Company must have `company_id`, `domain`, `email_pattern`

```
Company Anchor Required
        │
        ▼
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│ Phase 5: Email    │────▶│ Phase 6: Slot     │────▶│ Phase 7: Queue    │
│ Generation        │     │ Assignment        │     │ Management        │
│                   │     │                   │     │                   │
│ Apply pattern to  │     │ CHRO/HR/Benefits  │     │ Failed records    │
│ first.last        │     │ Payroll slots     │     │ for retry         │
└───────────────────┘     └───────────────────┘     └───────────────────┘
                                    │
                                    ▼
                          ┌───────────────────┐
                          │ Phase 8: Output   │
                          │ Writer            │
                          │                   │
                          │ Final CSV/DB      │
                          └───────────────────┘
```

### Talent Flow Pipeline (Phase 0)
**Prerequisite**: Both OLD and NEW company must be valid anchors

```
Movement Event Detected
"John moved from Company A to Company B"
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ PHASE 0: Talent Flow Company Gate                              │
│                                                                │
│ 1. Is Company B in company_master?                            │
│    YES → Use existing company_id                              │
│    NO  → Trigger Company Identity Pipeline (Phases 1-4)       │
│                                                                │
│ 2. Once Company B is valid anchor:                            │
│    → Run People Pipeline (Phases 5-8) for John                │
│    → Update slot assignments                                   │
│    → Update BIT signals                                        │
└───────────────────────────────────────────────────────────────┘
```

### DOL Spoke
**Prerequisite**: Company must exist to receive DOL enrichment

```
Form 5500 Data (EIN, plan info, participants)
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ DOL Matching Pipeline                                          │
│                                                                │
│ 1. Match EIN/Company Name to company_master                   │
│ 2. Attach DOL fields to company record:                       │
│    • plan_year_end (renewal timing)                           │
│    • tot_partcp_boy_cnt (company size validation)             │
│    • total_assets (financial health)                          │
│ 3. Flag for BIT scoring updates                               │
└───────────────────────────────────────────────────────────────┘
```

### Blog/News Spoke
**Prerequisite**: Company must exist to receive intelligence

```
News/Blog Signal Detected
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ Blog Intelligence Pipeline                                     │
│                                                                │
│ 1. Extract company mentions                                   │
│ 2. Match to company_master                                    │
│ 3. Attach signals:                                            │
│    • Sentiment (positive/negative/neutral)                    │
│    • Event type (funding, layoff, expansion, etc.)           │
│    • Competitor mentions                                       │
│ 4. Feed into BIT Engine                                       │
└───────────────────────────────────────────────────────────────┘
```

### BIT Engine Spoke
**Prerequisite**: Company must exist with complete profile

```
All Signals Converge
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ BIT (Buyer Intent Tool) Engine                                 │
│                                                                │
│ Inputs (all anchored to company_id):                          │
│ • People signals (slot changes, new hires)                    │
│ • DOL signals (renewal timing, plan changes)                  │
│ • Blog signals (sentiment, events)                            │
│ • Talent Flow signals (executive movement)                    │
│                                                                │
│ Output:                                                        │
│ • BIT Score (0-100)                                           │
│ • Trigger flags (ready_for_outreach, needs_nurture, etc.)    │
│ • Recommended action                                           │
└───────────────────────────────────────────────────────────────┘
```

---

## The Golden Rule

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   IF company_id IS NULL OR domain IS NULL OR email_pattern IS NULL:    │
│       STOP. DO NOT PROCEED.                                            │
│       → Route to Company Identity Pipeline first.                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**No spoke pipeline should EVER process a record that lacks a valid company anchor.**

---

## Company Master Schema (The Anchor)

```sql
company.company_master
├── company_unique_id (PK)     -- The anchor ID
├── company_name               -- Normalized name
├── company_name_normalized    -- Cleaned for matching
├── website_url                -- Primary domain source
├── domain                     -- Validated domain
├── email_pattern              -- Verified pattern (e.g., "{first}.{last}")
├── industry_class             -- Industry classification
├── employee_count             -- Size indicator
├── address_city               -- Location (for guardrail)
├── address_state              -- Location (for guardrail)
├── dol_ein                    -- Linked EIN from DOL
├── dol_plan_year_end          -- Renewal timing from DOL
├── bit_score                  -- Current BIT score
├── bit_last_updated           -- When BIT was calculated
├── created_at                 -- Record creation
└── updated_at                 -- Last modification
```

---

## Company Slots (The People Anchors)

Each company has slots that people fill:

```sql
company.company_slot
├── slot_id (PK)
├── company_unique_id (FK)     -- Links to company_master
├── slot_type                  -- CHRO, HR, Benefits, Payroll
├── person_unique_id (FK)      -- Current person in slot (nullable)
├── is_filled                  -- Boolean
├── filled_at                  -- When slot was filled
├── previous_person_id         -- Who held it before (for Talent Flow)
└── last_refreshed_at          -- Enrichment timestamp
```

---

## Pipeline Execution Order

### For New Data Intake:
1. **Company Identity Pipeline (Phases 1-4)** — ALWAYS FIRST
2. People Pipeline (Phases 5-8) — Only after company anchor exists
3. BIT Scoring — Only after people are slotted

### For Talent Flow Events:
1. **Phase 0: Company Gate** — Ensure new company exists
2. If missing: Run Company Identity Pipeline (Phases 1-4)
3. Then: People Pipeline (Phases 5-8)
4. Then: BIT Score update

### For DOL/Blog/News:
1. Match to existing company_master
2. If no match: Queue for Company Identity Pipeline
3. Attach enrichment to company record
4. Trigger BIT recalculation

---

## Summary

```
                    ╔═══════════════════════════════════════╗
                    ║                                       ║
                    ║   COMPANY = THE CENTER OF GRAVITY     ║
                    ║                                       ║
                    ║   All pipelines orbit around it.      ║
                    ║   All data anchors to it.             ║
                    ║   All scoring depends on it.          ║
                    ║                                       ║
                    ╚═══════════════════════════════════════╝
```

**This is not just a design choice. It is THE architecture.**

---

## File Reference

| File | Purpose |
|------|---------|
| `phases/phase1_company_matching.py` | Match input to company_master |
| `phases/phase1b_unmatched_hold_export.py` | Export unanchored records |
| `phases/phase2_domain_resolution.py` | Resolve/validate domain |
| `phases/phase3_email_pattern_waterfall.py` | Discover email pattern |
| `phases/phase4_pattern_verification.py` | Verify pattern works |
| `phases/talentflow_phase0_company_gate.py` | Talent Flow company check |
| `phases/phase5_email_generation.py` | Generate emails (People Pipeline) |
| `phases/phase6_slot_assignment.py` | Assign to slots (People Pipeline) |
| `phases/phase7_enrichment_queue.py` | Queue failures (People Pipeline) |
| `phases/phase8_output_writer.py` | Final output (People Pipeline) |
| `main.py` | Pipeline orchestrator |
| `email/pattern_guesser.py` | Local email pattern generation (FREE) |
| `email/bulk_verifier.py` | MillionVerifier async integration |
| `email/pattern_discovery_pipeline.py` | Pattern discovery orchestration |
| `intake/wv_hr_full_pipeline.py` | Full WV HR pipeline with verification |

---

## Email Verification Module

### Cost-Optimized Email Strategy

The email module uses a **Pattern Guessing + Bulk Verification** approach to minimize costs:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    EMAIL VERIFICATION COST COMPARISON                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Hunter.io:        $6,700+ for 67K companies ($0.10/lookup)            │
│  Pattern + MV:     ~$500-1000 for 67K companies                        │
│                                                                         │
│  SAVINGS:          ~90% cost reduction                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Pattern Guesser (FREE - Local Processing)

The `email/pattern_guesser.py` module generates email variants locally without any API calls:

```
Pattern Priority (most common first):
1. first.last@domain.com     (40% of companies)
2. flast@domain.com          (25% of companies)
3. f.last@domain.com         (10% of companies)
4. firstl@domain.com         (8% of companies)
5. first@domain.com          (5% of companies)
6. last.first@domain.com     (5% of companies)
7. lastf@domain.com          (4% of companies)
8. first_last@domain.com     (3% of companies)
```

### MillionVerifier Integration (~$37/10,000 verifications)

The `email/bulk_verifier.py` module provides async verification:

```
┌───────────────────────────────────────────────────────────────┐
│                    VERIFICATION FLOW                           │
│                                                                │
│  1. Generate all pattern variants locally (FREE)              │
│  2. Sort by priority (most likely patterns first)             │
│  3. Verify with MillionVerifier ($0.0037/email)               │
│  4. STOP on first valid email for each company                │
│  5. Save discovered pattern to company_master                 │
│                                                                │
│  Average verifications per company: 2-3                        │
│  Cost per company: ~$0.01                                      │
└───────────────────────────────────────────────────────────────┘
```

### Pattern Discovery Pipeline

```python
# Pattern discovery for companies without known patterns
async def discover_patterns_for_companies(people, companies):
    # 1. Generate guesses (FREE)
    guesses = generate_verification_batch(people, companies)

    # 2. Sort by priority
    guesses = sort_guesses_by_priority(guesses)

    # 3. Verify (CHEAP)
    results, discovered = await verify_batch(guesses, api_key, {})

    # 4. Return discovered patterns
    return discovered  # {company_id: PatternDiscovery}
```

### Full Pipeline Integration

The `intake/wv_hr_full_pipeline.py` integrates all components:

```
CSV Input (720 people)
        │
        ▼
[Load Companies from Neon] ← company_master with domains
        │
        ▼
[Fuzzy Match People to Companies] ← 80% threshold
        │
        ├──→ <80% → failed_company_match table
        │
        ▼
[Slot Assignment] ← Seniority competition
        │
        ├──→ Lost slot → failed_slot_assignment table
        ├──→ 70-79% → failed_low_confidence table
        │
        ▼
[Email Pattern Lookup] ← From company_master.email_pattern
        │
        ├──→ No pattern → Pattern Discovery Pipeline
        │                  │
        │                  ▼
        │              [Generate Guesses (FREE)]
        │                  │
        │                  ▼
        │              [MillionVerifier (CHEAP)]
        │                  │
        │                  ▼
        │              [Save Pattern to company_master]
        │
        ▼
[Email Generation] ← Apply pattern to first.last
        │
        ▼
[Email Verification] ← MillionVerifier
        │
        ├──→ Invalid → failed_email_verification table
        │
        ▼
[Export to Neon] ← ONLY verified emails
        │
        ▼
people_master + company_slot (is_filled=true, email_verified=true)
```

---

## Stage-Specific Failure Tables

The pipeline routes failures to stage-specific tables for manual review:

| Table | Stage | Trigger | Resolution Options |
|-------|-------|---------|-------------------|
| `failed_company_match` | Phase 2 | Fuzzy score <80% | Confirm, Reject, Remap |
| `failed_slot_assignment` | Phase 3 | Lost to higher seniority | Manual override |
| `failed_low_confidence` | Phase 3 | Fuzzy score 70-79% | Confirm, Reject, Remap |
| `failed_no_pattern` | Phase 4 | No domain/pattern | Add pattern manually |
| `failed_email_verification` | Phase 5 | MV returned invalid | Try alternate email |

---

*Last Updated: 2024-12-11*
*Architecture Version: 1.1 - Added Email Verification Module*
