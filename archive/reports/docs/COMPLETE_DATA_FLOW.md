# Barton Outreach Core - Complete Data Flow

**Version**: 2.2.0
**Last Updated**: 2026-01-30
**Architecture**: Bicycle Wheel Doctrine v1.1

---

## Master Architecture

```
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                                    RAW INPUT                                           ║
║                         (CSV Upload, API, Manual Entry)                               ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝
                                         │
                                         │ People records, company data, DOL filings
                                         │
                                         ▼
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                        ║
║                              ██████╗ ██████╗ ███╗   ███╗██████╗  █████╗ ███╗   ██╗██╗   ██╗ ║
║                             ██╔════╝██╔═══██╗████╗ ████║██╔══██╗██╔══██╗████╗  ██║╚██╗ ██╔╝ ║
║                             ██║     ██║   ██║██╔████╔██║██████╔╝███████║██╔██╗ ██║ ╚████╔╝  ║
║                             ██║     ██║   ██║██║╚██╔╝██║██╔═══╝ ██╔══██║██║╚██╗██║  ╚██╔╝   ║
║                             ╚██████╗╚██████╔╝██║ ╚═╝ ██║██║     ██║  ██║██║ ╚████║   ██║    ║
║                              ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ║
║                                           HUB                                          ║
║                                      (MASTER NODE)                                     ║
║                                                                                        ║
║  ┌──────────────────────────────────────────────────────────────────────────────────┐  ║
║  │                            COMPANY IDENTITY PIPELINE                              │  ║
║  │                                                                                   │  ║
║  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │  ║
║  │   │  PHASE 1    │    │  PHASE 2    │    │  PHASE 3    │    │  PHASE 4    │       │  ║
║  │   │             │    │             │    │             │    │             │       │  ║
║  │   │  Company    │───▶│   Domain    │───▶│   Email     │───▶│  Pattern    │       │  ║
║  │   │  Matching   │    │ Resolution  │    │  Pattern    │    │ Verification│       │  ║
║  │   │             │    │             │    │  Waterfall  │    │             │       │  ║
║  │   └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘       │  ║
║  │         │                  │                  │                  │                │  ║
║  │         ▼                  ▼                  ▼                  ▼                │  ║
║  │   ┌───────────┐      ┌───────────┐      ┌───────────┐      ┌───────────┐         │  ║
║  │   │GOLD/SILVER│      │ DNS Check │      │ Tier 0→3  │      │ MX/SMTP   │         │  ║
║  │   │/BRONZE    │      │ MX Check  │      │ Providers │      │ Million   │         │  ║
║  │   │ Matching  │      │ Validate  │      │ Waterfall │      │ Verifier  │         │  ║
║  │   └───────────┘      └───────────┘      └───────────┘      └───────────┘         │  ║
║  └──────────────────────────────────────────────────────────────────────────────────┘  ║
║                                           │                                            ║
║                                           ▼                                            ║
║  ┌──────────────────────────────────────────────────────────────────────────────────┐  ║
║  │                           BIT ENGINE (Sub-Hub)                                    │  ║
║  │                                                                                   │  ║
║  │   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐              │  ║
║  │   │ Signal Intake   │───▶│  Score Calc     │───▶│ Threshold Check │              │  ║
║  │   │                 │    │                 │    │                 │              │  ║
║  │   │ • DOL signals   │    │ Σ(impact ×      │    │ Score ≥ 25?     │              │  ║
║  │   │ • People signals│    │   decay ×       │    │ → WARM status   │              │  ║
║  │   │ • Talent signals│    │   weight)       │    │ → Priority flag │              │  ║
║  │   └─────────────────┘    └─────────────────┘    └─────────────────┘              │  ║
║  └──────────────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                        ║
╚════════════════════════════════════════╤═══════════════════════════════════════════════╝
                                         │
                                         │ OUTPUT: company_id + domain + email_pattern
                                         │ (REQUIRED FOR ALL SPOKES)
                                         │
          ┌──────────────────────────────┼──────────────────────────────┐
          │                              │                              │
          ▼                              ▼                              ▼
╔═════════════════════════════╗ ╔═════════════════════════════╗ ╔═════════════════════════════╗
║      PEOPLE SPOKE           ║ ║       DOL SPOKE             ║ ║      BLOG SPOKE             ║
║      (Spoke #1)             ║ ║       (Spoke #2)            ║ ║      (Spoke #3)             ║
║       [ACTIVE]              ║ ║        [ACTIVE]             ║ ║      [PLANNED]              ║
╠═════════════════════════════╣ ╠═════════════════════════════╣ ╠═════════════════════════════╣
║ See detailed flow below     ║ ║ See detailed flow below     ║ ║ • News monitoring           ║
║                             ║ ║                             ║ ║ • Sentiment analysis        ║
║                             ║ ║                             ║ ║ • Competitor intel          ║
╚═════════════════════════════╝ ╚═════════════════════════════╝ ╚═════════════════════════════╝
```

---

## Company Hub - Detailed Phase Flow

```
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                              COMPANY HUB - PHASE DETAILS                               ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: COMPANY MATCHING                                                               │
│ File: hub/company/phases/phase1_company_matching.py                                     │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   INPUT                           PROCESS                           OUTPUT              │
│   ─────                           ───────                           ──────              │
│                                                                                         │
│   ┌─────────────┐                                               ┌─────────────┐        │
│   │ People DF   │                                               │ Matched     │        │
│   │ • person_id │     ┌─────────────────────────────────┐       │ Companies   │        │
│   │ • company   │────▶│      MATCHING WATERFALL         │──────▶│ • company_id│        │
│   │   _name     │     │                                 │       │ • match_type│        │
│   │ • domain    │     │  1. 🥇 DOMAIN MATCH (1.00)      │       │ • match_    │        │
│   │ • city      │     │     Exact domain lookup         │       │   score     │        │
│   │ • state     │     │              ↓ (if no match)    │       │ • is_       │        │
│   └─────────────┘     │  2. 🥈 EXACT NAME (0.95)        │       │   collision │        │
│                       │     Normalized name match       │       └─────────────┘        │
│   ┌─────────────┐     │              ↓ (if no match)    │                              │
│   │ Company     │     │  3. 🥉 FUZZY NAME (0.85-0.92)   │       ┌─────────────┐        │
│   │ Master DF   │────▶│     Jaro-Winkler + city guard   │──────▶│ Unmatched   │        │
│   │ • company_id│     │              ↓ (if no match)    │       │ → Phase 1b  │        │
│   │ • name      │     │  4. ❌ NO MATCH                  │       │ → HOLD queue│        │
│   │ • domain    │     │     Route to HOLD queue         │       └─────────────┘        │
│   └─────────────┘     └─────────────────────────────────┘                              │
│                                                                                         │
│   TOOLS: normalize_company_name(), normalize_domain(), jaro_winkler_similarity(),       │
│          apply_city_guardrail()                                                         │
│                                                                                         │
│   COLLISION: If top 2 candidates within 0.03 score → flag for manual review            │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: DOMAIN RESOLUTION                                                              │
│ File: hub/company/phases/phase2_domain_resolution.py                                    │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   INPUT                           PROCESS                           OUTPUT              │
│   ─────                           ───────                           ──────              │
│                                                                                         │
│   ┌─────────────┐     ┌─────────────────────────────────┐       ┌─────────────┐        │
│   │ Matched     │     │      RESOLUTION WATERFALL       │       │ Resolved    │        │
│   │ Companies   │────▶│                                 │──────▶│ Domains     │        │
│   │ from        │     │  1. Company Master Lookup       │       │ • domain    │        │
│   │ Phase 1     │     │     Try website_url, then domain│       │ • domain_   │        │
│   └─────────────┘     │              ↓ (if not found)   │       │   status    │        │
│                       │  2. Input Record Fallback       │       │ • has_mx    │        │
│                       │     Use input company_domain    │       └─────────────┘        │
│                       │              ↓ (if found)       │                              │
│                       │  3. DNS Validation              │       ┌─────────────┐        │
│                       │     A-record lookup             │       │ Needs       │        │
│                       │              ↓                  │──────▶│ Enrichment  │        │
│                       │  4. MX Record Check             │       │ → Phase 3   │        │
│                       │     Can receive email?          │       └─────────────┘        │
│                       └─────────────────────────────────┘                              │
│                                                                                         │
│   TOOLS: verify_domain_dns(), verify_mx_records(), DNS cache layer                      │
│                                                                                         │
│   STATUS: VALID, VALID_NO_MX, PARKED, UNREACHABLE, MISSING                              │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: EMAIL PATTERN WATERFALL                                                        │
│ File: hub/company/phases/phase3_email_pattern_waterfall.py                              │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   INPUT                           PROCESS                           OUTPUT              │
│   ─────                           ───────                           ──────              │
│                                                                                         │
│   ┌─────────────┐     ┌─────────────────────────────────┐       ┌─────────────┐        │
│   │ Companies   │     │   PROVIDER WATERFALL            │       │ Patterns    │        │
│   │ with        │────▶│   (STOPS ON FIRST MATCH)        │──────▶│ Discovered  │        │
│   │ Domains     │     │                                 │       │ • pattern   │        │
│   └─────────────┘     │ ┌─────────────────────────────┐ │       │ • source    │        │
│                       │ │ TIER 0 - FREE               │ │       │ • confidence│        │
│                       │ │ • Direct Scraper    $0.00   │ │       │ • provider  │        │
│                       │ │ • Firecrawl         $0.0001 │ │       └─────────────┘        │
│                       │ │ • Google CSE        $0.005  │ │                              │
│                       │ │ • Google Places     $0.003  │ │                              │
│                       │ └────────────┬────────────────┘ │                              │
│                       │              ↓ (if no pattern)  │                              │
│                       │ ┌─────────────────────────────┐ │                              │
│                       │ │ TIER 1 - LOW COST           │ │                              │
│                       │ │ • Hunter.io         $0.008  │ │                              │
│                       │ │ • Apollo.io         $0.005  │ │                              │
│                       │ │ • Clay              $0.01   │ │                              │
│                       │ └────────────┬────────────────┘ │                              │
│                       │              ↓ (if no pattern)  │                              │
│                       │ ┌─────────────────────────────┐ │                              │
│                       │ │ TIER 1.5 - MID COST         │ │                              │
│                       │ │ • Prospeo           $0.003  │ │                              │
│                       │ │ • Snov.io           $0.004  │ │                              │
│                       │ └────────────┬────────────────┘ │                              │
│                       │              ↓ (if no pattern)  │                              │
│                       │ ┌─────────────────────────────┐ │       ┌─────────────┐        │
│                       │ │ TIER 2 - PREMIUM            │ │       │ Suggested   │        │
│                       │ │ • Clearbit          $0.02   │ │──────▶│ Patterns    │        │
│                       │ │ • PDL               $0.03   │ │       │ (fallback)  │        │
│                       │ │ • ZenRows           $0.005  │ │       └─────────────┘        │
│                       │ └─────────────────────────────┘ │                              │
│                       └─────────────────────────────────┘                              │
│                                                                                         │
│   FALLBACK PATTERNS: {first}.{last}, {first}{last}, {f}{last}, {first}_{last}           │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: PATTERN VERIFICATION                                                           │
│ File: hub/company/phases/phase4_pattern_verification.py                                 │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   INPUT                           PROCESS                           OUTPUT              │
│   ─────                           ───────                           ──────              │
│                                                                                         │
│   ┌─────────────┐     ┌─────────────────────────────────┐       ┌─────────────┐        │
│   │ Patterns    │     │   VERIFICATION WATERFALL        │       │ Verified    │        │
│   │ from        │────▶│                                 │──────▶│ Patterns    │        │
│   │ Phase 3     │     │  1. Known Emails Test           │       │ • verified  │        │
│   └─────────────┘     │     Generate → Compare          │       │ • confidence│        │
│                       │              ↓                  │       │ • method    │        │
│                       │  2. MX Record Check             │       └─────────────┘        │
│                       │     Domain can receive email?   │                              │
│                       │              ↓                  │                              │
│                       │  3. SMTP Verification (opt)     │                              │
│                       │     Test actual delivery        │                              │
│                       │              ↓                  │                              │
│                       │  4. MillionVerifier API         │                              │
│                       │     $0.001-$0.004/email         │                              │
│                       │              ↓                  │       ┌─────────────┐        │
│                       │  5. Confidence Scoring          │       │ Fallback    │        │
│                       │     Calculate final score       │──────▶│ Required    │        │
│                       └─────────────────────────────────┘       │ (if failed) │        │
│                                                                 └─────────────┘        │
│   TOOLS: _test_pattern_against_known_emails(), _check_mx_records(), _smtp_verify()      │
│                                                                                         │
│   STATUS: VERIFIED, LIKELY_VALID, UNVERIFIED, FAILED, SKIPPED                           │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
                    ┌────────────────────────────────────────┐
                    │           SPOKE-READY OUTPUT           │
                    │                                        │
                    │   • company_id      (Barton ID)        │
                    │   • domain          (validated)        │
                    │   • email_pattern   (verified)         │
                    │                                        │
                    │   → Ready for People, DOL, Blog spokes │
                    └────────────────────────────────────────┘
```

---

## Company Hub - BIT Engine Sub-Hub

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ BIT ENGINE (Sub-Hub of Company Hub)                                                     │
│ File: hub/company/bit_engine.py                                                         │
│ Status: PLANNED                                                                         │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   SIGNAL SOURCES                      PROCESSING                    OUTPUT              │
│   ──────────────                      ──────────                    ──────              │
│                                                                                         │
│   ┌─────────────────────┐                                                              │
│   │ DOL SPOKE SIGNALS   │                                                              │
│   │ • FORM_5500_FILED   │──┐                                                           │
│   │   (+5.0 impact)     │  │                                                           │
│   │ • LARGE_PLAN        │  │                                                           │
│   │   (+8.0 impact)     │  │     ┌─────────────────────────────┐                       │
│   │ • BROKER_CHANGE     │  │     │                             │                       │
│   │   (+7.0 impact)     │  │     │    SIGNAL AGGREGATOR        │                       │
│   └─────────────────────┘  │     │                             │                       │
│                            ├────▶│  • Deduplicate (24h/365d)   │                       │
│   ┌─────────────────────┐  │     │  • Apply recency decay      │                       │
│   │ PEOPLE SPOKE SIGNALS│  │     │  • Weight by source         │     ┌───────────┐     │
│   │ • SLOT_FILLED       │──┤     │                             │     │           │     │
│   │   (+3.0 impact)     │  │     └──────────────┬──────────────┘     │ BIT SCORE │     │
│   │ • EMAIL_VERIFIED    │  │                    │                    │           │     │
│   │   (+2.0 impact)     │  │                    ▼                    │ 0-100     │     │
│   └─────────────────────┘  │     ┌─────────────────────────────┐     │           │     │
│                            │     │                             │     │ ≥25 = WARM│     │
│   ┌─────────────────────┐  │     │    SCORE CALCULATOR         │────▶│           │     │
│   │ TALENT FLOW SIGNALS │  │     │                             │     └───────────┘     │
│   │ • EXECUTIVE_JOINED  │──┤     │  BIT = Σ(impact × decay     │                       │
│   │   (+10.0 impact)    │  │     │          × weight)          │                       │
│   │ • EXECUTIVE_LEFT    │  │     │                             │                       │
│   │   (+6.0 impact)     │  │     │  Decay:                     │                       │
│   └─────────────────────┘  │     │  • <7 days:   1.0           │                       │
│                            │     │  • 7-30 days: 0.8           │                       │
│   ┌─────────────────────┐  │     │  • 30-90 days: 0.5          │                       │
│   │ BLOG SPOKE SIGNALS  │  │     │                             │                       │
│   │ • NEWS_MENTION      │──┘     │  Weight:                    │                       │
│   │   (+1.0 impact)     │        │  • DOL: 1.0                 │                       │
│   │ [PLANNED]           │        │  • TalentFlow: 0.8          │                       │
│   └─────────────────────┘        │  • People: 0.6              │                       │
│                                  └─────────────────────────────┘                       │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## People Spoke - Detailed Phase Flow

```
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                              PEOPLE SPOKE - PHASE DETAILS                              ║
║                                    (Spoke #1)                                          ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝

                    ┌────────────────────────────────────────┐
                    │         ANCHOR REQUIREMENT             │
                    │                                        │
                    │   Must have from Company Hub:          │
                    │   • company_id ✓                       │
                    │   • domain ✓                           │
                    │   • email_pattern ✓                    │
                    └────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 0: PEOPLE INGEST                                                                  │
│ File: spokes/people/phases/phase0_people_ingest.py                                      │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   INPUT                           PROCESS                           OUTPUT              │
│   ─────                           ───────                           ──────              │
│                                                                                         │
│   ┌─────────────┐     ┌─────────────────────────────────┐       ┌─────────────┐        │
│   │ Raw People  │     │   CLASSIFICATION WATERFALL      │       │ Classified  │        │
│   │ Records     │────▶│   (FIRST MATCH WINS)            │──────▶│ People      │        │
│   │ • person_id │     │                                 │       │             │        │
│   │ • company_id│     │  1. Missing company_id?         │       │ SUSPECT     │        │
│   │ • job_title │     │     → SUSPECT (unanchored)      │       │ WARM        │        │
│   │ • has_reply │     │              ↓                  │       │ TALENTFLOW  │        │
│   │ • bit_score │     │  2. Past meeting flag?          │       │ APPOINTMENT │        │
│   │ • meeting   │     │     → APPOINTMENT               │       │             │        │
│   └─────────────┘     │              ↓                  │       └─────────────┘        │
│                       │  3. Historical reply?           │                              │
│                       │     → WARM                      │       ┌─────────────┐        │
│                       │              ↓                  │       │ Slot        │        │
│                       │  4. TalentFlow movement?        │──────▶│ Candidates  │        │
│                       │     → TALENTFLOW_WARM           │       │ Detected    │        │
│                       │              ↓                  │       │ (by title)  │        │
│                       │  5. BIT score ≥ 25?             │       └─────────────┘        │
│                       │     → WARM                      │                              │
│                       │              ↓                  │                              │
│                       │  6. Default → SUSPECT           │                              │
│                       └─────────────────────────────────┘                              │
│                                                                                         │
│   HUB GATE: Soft validation (classifies failures as SUSPECT, not hard failure)          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 5: EMAIL GENERATION                                                               │
│ File: spokes/people/phases/phase5_email_generation.py                                   │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   INPUT                           PROCESS                           OUTPUT              │
│   ─────                           ───────                           ──────              │
│                                                                                         │
│   ┌─────────────┐                                               ┌─────────────┐        │
│   │ Matched     │                                               │ People with │        │
│   │ People      │     ┌─────────────────────────────────┐       │ Emails      │        │
│   │ • person_id │────▶│   EMAIL GENERATION WATERFALL    │──────▶│             │        │
│   │ • first_name│     │                                 │       │ • email     │        │
│   │ • last_name │     │  1. Use verified pattern        │       │ • confidence│        │
│   │ • company_id│     │     (from Phase 4)              │       │             │        │
│   └─────────────┘     │     Confidence: VERIFIED        │       └─────────────┘        │
│                       │              ↓                  │                              │
│   ┌─────────────┐     │  2. Derive from known emails    │                              │
│   │ Pattern DF  │     │     Confidence: DERIVED         │                              │
│   │ • company_id│────▶│              ↓                  │                              │
│   │ • pattern   │     │  3. On-demand waterfall         │       ┌─────────────┐        │
│   │ • domain    │     │     (if enabled)                │       │ Missing     │        │
│   │ • confidence│     │     Confidence: WATERFALL       │──────▶│ Pattern     │        │
│   └─────────────┘     │              ↓                  │       │ → Phase 7   │        │
│                       │  4. Fallback pattern            │       └─────────────┘        │
│                       │     Confidence: LOW_CONFIDENCE  │                              │
│                       └─────────────────────────────────┘                              │
│                                                                                         │
│   PATTERN APPLICATION:                                                                  │
│   Pattern: {first}.{last} + Name: John Smith + Domain: acme.com                         │
│   Result: john.smith@acme.com                                                           │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 6: SLOT ASSIGNMENT                                                                │
│ File: spokes/people/phases/phase6_slot_assignment.py                                    │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   INPUT                           PROCESS                           OUTPUT              │
│   ─────                           ───────                           ──────              │
│                                                                                         │
│   ┌─────────────┐     ┌─────────────────────────────────┐       ┌─────────────┐        │
│   │ People with │     │   SLOT ASSIGNMENT LOGIC         │       │ Slotted     │        │
│   │ Emails      │────▶│                                 │──────▶│ People      │        │
│   │ • job_title │     │   SLOT HIERARCHY:               │       │ • slot_type │        │
│   │ • company_id│     │   ┌─────────────────────────┐   │       │ • seniority │        │
│   └─────────────┘     │   │ CHRO           (100)    │   │       │   _score    │        │
│                       │   │ chief hr, vp hr, cpo    │   │       └─────────────┘        │
│                       │   ├─────────────────────────┤   │                              │
│                       │   │ HR_MANAGER     (80)     │   │                              │
│                       │   │ hr director, hr manager │   │                              │
│                       │   ├─────────────────────────┤   │                              │
│                       │   │ BENEFITS_LEAD  (60)     │   │       ┌─────────────┐        │
│                       │   │ benefits dir, rewards   │   │       │ Unslotted   │        │
│                       │   ├─────────────────────────┤   │──────▶│ People      │        │
│                       │   │ PAYROLL_ADMIN  (50)     │   │       │ → Phase 7   │        │
│                       │   │ payroll director/mgr    │   │       └─────────────┘        │
│                       │   ├─────────────────────────┤   │                              │
│                       │   │ HR_SUPPORT     (30)     │   │       ┌─────────────┐        │
│                       │   │ hr coord, hrbp, spec    │   │       │ Slot        │        │
│                       │   └─────────────────────────┘   │──────▶│ Summary     │        │
│                       │                                 │       │ by Company  │        │
│                       │   RULES:                        │       └─────────────┘        │
│                       │   • 1 person per slot/company   │                              │
│                       │   • Higher seniority wins       │                              │
│                       │   • Min 10pt diff to replace    │                              │
│                       └─────────────────────────────────┘                              │
│                                                                                         │
│   SIGNALS: SLOT_FILLED (+3.0) → BIT Engine                                              │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 7: ENRICHMENT QUEUE                                                               │
│ File: spokes/people/phases/phase7_enrichment_queue.py                                   │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   INPUT                           PROCESS                           OUTPUT              │
│   ─────                           ───────                           ──────              │
│                                                                                         │
│   ┌─────────────┐     ┌─────────────────────────────────┐       ┌─────────────┐        │
│   │ Missing     │     │   QUEUE PRIORITY ASSIGNMENT     │       │ Enrichment  │        │
│   │ Patterns    │────▶│                                 │──────▶│ Queue       │        │
│   └─────────────┘     │   HIGH (1):                     │       │ • entity_id │        │
│                       │   • PATTERN_MISSING             │       │ • reason    │        │
│   ┌─────────────┐     │   • SLOT_EMPTY_CHRO             │       │ • priority  │        │
│   │ Unslotted   │────▶│   • SLOT_EMPTY_BENEFITS         │       │ • retry_cnt │        │
│   │ People      │     │   • MISSING_COMPANY_ID          │       └─────────────┘        │
│   └─────────────┘     │                                 │                              │
│                       │   MEDIUM (2):                   │                              │
│   ┌─────────────┐     │   • PATTERN_LOW_CONFIDENCE      │       ┌─────────────┐        │
│   │ Slot        │────▶│   • SLOT_EMPTY_HR_MANAGER       │       │ Resolved    │        │
│   │ Summary     │     │   • SLOT_COLLISION              │──────▶│ Patterns    │        │
│   └─────────────┘     │                                 │       │ (if waterfall│       │
│                       │   LOW (3):                      │       │  enabled)   │        │
│                       │   • SLOT_EMPTY_HR_SUPPORT       │       └─────────────┘        │
│                       │   • EMAIL_LOW_CONFIDENCE        │                              │
│                       │   • MISSING_NAME                │                              │
│                       └─────────────────────────────────┘                              │
│                                                                                         │
│   RETRY: Max 3, backoff = base_delay × 2^retry (1h base, 24h max)                       │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 8: OUTPUT WRITER                                                                  │
│ File: spokes/people/phases/phase8_output_writer.py                                      │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   INPUT                           PROCESS                           OUTPUT              │
│   ─────                           ───────                           ──────              │
│                                                                                         │
│   ┌─────────────┐                                               ┌─────────────────────┐│
│   │ All Phase   │     ┌─────────────────────────────────┐       │ OUTPUT FILES        ││
│   │ Outputs     │────▶│   FILE GENERATION               │──────▶│                     ││
│   │             │     │                                 │       │ output/             ││
│   │ • Emails    │     │  1. Compile all records         │       │ ├─ people_final.csv ││
│   │ • Slots     │     │  2. Format columns              │       │ ├─ slot_assign.csv  ││
│   │ • Queue     │     │  3. Write CSV files             │       │ ├─ enrich_queue.csv ││
│   │ • Stats     │     │  4. Generate summary            │       │ └─ summary.txt      ││
│   └─────────────┘     └─────────────────────────────────┘       └─────────────────────┘│
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## People Spoke - Sub-Hubs

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ TALENT FLOW (Sub-Hub of People Spoke)                                                   │
│ Location: spokes/people/talent_flow/                                                    │
│ Status: SHELL                                                                           │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   DATA SOURCES                        DETECTION                     SIGNALS             │
│   ────────────                        ─────────                     ───────             │
│                                                                                         │
│   ┌─────────────┐     ┌─────────────────────────────────┐       ┌─────────────┐        │
│   │ LinkedIn    │     │   MOVEMENT DETECTION            │       │ To BIT      │        │
│   │ Profiles    │────▶│                                 │──────▶│ Engine      │        │
│   └─────────────┘     │   Compare current vs previous:  │       │             │        │
│                       │                                 │       │ EXECUTIVE   │        │
│   ┌─────────────┐     │   • Company change detected?    │       │ _JOINED     │        │
│   │ Apollo      │────▶│     → COMPANY_CHANGED (+8.0)    │       │ (+10.0)     │        │
│   │ Alerts      │     │                                 │       │             │        │
│   └─────────────┘     │   • Title promotion detected?   │       │ EXECUTIVE   │        │
│                       │     → TITLE_PROMOTED (+4.0)     │       │ _LEFT       │        │
│   ┌─────────────┐     │                                 │       │ (+6.0)      │        │
│   │ Historical  │────▶│   • Executive joined company?   │       │             │        │
│   │ Records     │     │     → EXECUTIVE_JOINED (+10.0)  │       └─────────────┘        │
│   └─────────────┘     │                                 │                              │
│                       │   • Executive left company?     │       ┌─────────────┐        │
│                       │     → EXECUTIVE_LEFT (+6.0)     │       │ To Phase 0  │        │
│                       │                                 │──────▶│ TALENTFLOW  │        │
│                       │   Dedup window: 365 days        │       │ _WARM class │        │
│                       └─────────────────────────────────┘       └─────────────┘        │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ EMAIL VERIFICATION (Sub-Wheel of People Spoke)                                          │
│ Location: spokes/people/sub_wheels/email_verification/                                  │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   INPUT                           VERIFICATION                      OUTPUT              │
│   ─────                           ────────────                      ──────              │
│                                                                                         │
│   ┌─────────────┐     ┌─────────────────────────────────┐       ┌─────────────┐        │
│   │ Generated   │     │   PATTERN GUESSER SPOKE         │       │ Verified    │        │
│   │ Email       │────▶│   Generate email from pattern   │       │ Email       │        │
│   │             │     │   + first/last + domain         │       │             │        │
│   └─────────────┘     └────────────────┬────────────────┘       │ • status    │        │
│                                        │                        │ • code      │        │
│                                        ▼                        │ • valid     │        │
│                       ┌─────────────────────────────────┐       └─────────────┘        │
│                       │   BULK VERIFIER SPOKE           │                              │
│                       │   MillionVerifier API           │                              │
│                       │   $0.001-$0.004/email           │       ┌─────────────┐        │
│                       │                                 │       │ Rejected    │        │
│                       │   RESULT CODES:                 │──────▶│ Email       │        │
│                       │   ✅ ok        → Accept         │       │ → Queue     │        │
│                       │   ⚠️ catch_all → Accept (risky) │       └─────────────┘        │
│                       │   ⚠️ role      → Accept         │                              │
│                       │   ⚠️ risky     → Accept         │                              │
│                       │   ❌ invalid   → Reject         │                              │
│                       │   ❌ disposable→ Reject         │                              │
│                       │   ❌ unknown   → Reject         │                              │
│                       └─────────────────────────────────┘                              │
│                                                                                         │
│   SIGNAL: EMAIL_VERIFIED (+2.0) → BIT Engine                                            │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## DOL Spoke - Detailed Flow

```
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                               DOL SPOKE - DETAILED FLOW                                ║
║                                    (Spoke #2)                                          ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ DATA IMPORT PIPELINE                                                                    │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   DOL FOIA DATA                       IMPORT SCRIPTS                STAGING TABLES      │
│   ─────────────                       ──────────────                ──────────────      │
│                                                                                         │
│   ┌─────────────────┐     ┌───────────────────────┐     ┌─────────────────────┐        │
│   │ F_5500_2023     │     │ import_5500.py        │     │ form_5500_staging   │        │
│   │ _latest.csv     │────▶│ • 56+ columns mapped  │────▶│ • ~800K records     │        │
│   │ (Large Plans)   │     │ • EIN normalization   │     │ • Large plans ≥100  │        │
│   │ ≥100 participants│    └───────────────────────┘     └─────────────────────┘        │
│   └─────────────────┘                                                                  │
│                                                                                         │
│   ┌─────────────────┐     ┌───────────────────────┐     ┌─────────────────────┐        │
│   │ F_5500_SF_2023  │     │ import_5500_sf.py     │     │ form_5500_sf_staging│        │
│   │ _latest.csv     │────▶│ • SF column prefix    │────▶│ • ~600K records     │        │
│   │ (Small Plans)   │     │ • Different fields    │     │ • Small plans <100  │        │
│   │ <100 participants│    └───────────────────────┘     └─────────────────────┘        │
│   └─────────────────┘                                                                  │
│                                                                                         │
│   ┌─────────────────┐     ┌───────────────────────┐     ┌─────────────────────┐        │
│   │ F_SCH_A_2023    │     │ import_schedule_a.py  │     │ schedule_a_staging  │        │
│   │ _latest.csv     │────▶│ • 13 key columns      │────▶│ • ~336K records     │        │
│   │ (Insurance)     │     │ • Renewal date extract│     │ • Links to 5500     │        │
│   └─────────────────┘     └───────────────────────┘     └─────────────────────┘        │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ DOL SPOKE PROCESSING                                                                    │
│ File: spokes/dol/dol_spoke.py                                                           │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   INPUT                           PROCESS                           OUTPUT              │
│   ─────                           ───────                           ──────              │
│                                                                                         │
│   ┌─────────────┐     ┌─────────────────────────────────┐                              │
│   │ Form5500    │     │   PROCESSING WATERFALL          │                              │
│   │ Record      │────▶│                                 │                              │
│   │ • ein       │     │  1. Validate correlation_id     │                              │
│   │ • plan_name │     │     FAIL HARD if missing        │                              │
│   │ • partici-  │     │              ↓                  │                              │
│   │   pants     │     │  2. Normalize EIN               │                              │
│   │ • assets    │     │     Remove hyphens, validate 9  │                              │
│   └─────────────┘     │              ↓                  │       ┌─────────────┐        │
│                       │  3. Lookup company by EIN       │       │ NO MATCH    │        │
│                       │     _lookup_company_by_ein()    │──────▶│ (EIN not    │        │
│                       │     EXACT MATCH ONLY            │       │  found)     │        │
│                       │              ↓ (if found)       │       └─────────────┘        │
│                       │  4. Hub Gate Validation         │                              │
│                       │     validate_company_anchor()   │                              │
│                       │              ↓ (if valid)       │       ┌─────────────┐        │
│                       │  5. Send signals to BIT Engine  │       │ SIGNALS     │        │
│                       │     with 365-day dedup          │──────▶│ EMITTED     │        │
│                       └─────────────────────────────────┘       └─────────────┘        │
│                                                                                         │
│   EIN MATCHING STRATEGY: FAIL CLOSED                                                    │
│   • Exact match only (no fuzzy)                                                         │
│   • Deterministic (no ML/heuristics)                                                    │
│   • Reproducible                                                                        │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ SIGNAL EMISSION                                                                         │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   CONDITION                           SIGNAL                        DEDUP               │
│   ─────────                           ──────                        ─────               │
│                                                                                         │
│   ┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐      │
│   │ Any valid filing    │────▶│ FORM_5500_FILED     │────▶│ 365-day window      │      │
│   │ with EIN match      │     │ Impact: +5.0        │     │ Key: signal:company │      │
│   └─────────────────────┘     └─────────────────────┘     │     :filing_year    │      │
│                                                           └─────────────────────┘      │
│   ┌─────────────────────┐     ┌─────────────────────┐                                  │
│   │ Participants ≥ 500  │────▶│ LARGE_PLAN          │────▶│ 365-day window      │      │
│   │                     │     │ Impact: +8.0        │     │                     │      │
│   └─────────────────────┘     └─────────────────────┘     └─────────────────────┘      │
│                                                                                         │
│   ┌─────────────────────┐     ┌─────────────────────┐                                  │
│   │ Broker changed      │────▶│ BROKER_CHANGE       │────▶│ 365-day window      │      │
│   │ (detected)          │     │ Impact: +7.0        │     │                     │      │
│   └─────────────────────┘     └─────────────────────┘     └─────────────────────┘      │
│                                                                                         │
│                                         │                                               │
│                                         ▼                                               │
│                               ┌─────────────────────┐                                  │
│                               │ BIT ENGINE          │                                  │
│                               │ (Company Hub)       │                                  │
│                               │ Aggregates signals  │                                  │
│                               │ Calculates BIT score│                                  │
│                               └─────────────────────┘                                  │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ EIN BACKFILL (Initial Population)                                                       │
│ File: spokes/dol/ein_matcher.py                                                         │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   MATCHING WATERFALL (State → City → Name)                                              │
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐  │
│   │                                                                                 │  │
│   │   company_master                      form_5500                                 │  │
│   │   ──────────────                      ─────────                                 │  │
│   │                                                                                 │  │
│   │   company_name      ◄──SIMILARITY──►  sponsor_dfe_name                          │  │
│   │   address_state     ◄───EXACT────►    spons_dfe_mail_us_state                   │  │
│   │   address_city      ◄───EXACT────►    spons_dfe_mail_us_city                    │  │
│   │                                                                                 │  │
│   │   WHERE:                                                                        │  │
│   │   • State matches exactly                                                       │  │
│   │   • City matches (case-insensitive)                                             │  │
│   │   • Name trigram similarity > 0.8                                               │  │
│   │                                                                                 │  │
│   │   RESULT: UPDATE company_master SET ein = dol_ein                               │  │
│   │                                                                                 │  │
│   └─────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Complete End-to-End Flow

```
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                            COMPLETE END-TO-END DATA FLOW                               ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    RAW INPUT                                            │
│                                                                                         │
│    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │
│    │ CSV Upload   │    │ API Import   │    │ Manual Entry │    │ DOL FOIA     │        │
│    │ (People)     │    │ (Companies)  │    │ (Leads)      │    │ (Form 5500)  │        │
│    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘        │
│           └───────────────────┴───────────────────┴───────────────────┘                │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                                   COMPANY HUB                                          ║
╠═══════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                        ║
║   PHASE 1              PHASE 2              PHASE 3              PHASE 4               ║
║   Company              Domain               Email Pattern        Pattern               ║
║   Matching             Resolution           Waterfall            Verification          ║
║   ──────────           ──────────           ──────────           ──────────            ║
║                                                                                        ║
║   ┌─────────┐          ┌─────────┐          ┌─────────┐          ┌─────────┐          ║
║   │ GOLD    │          │ Master  │          │ Tier 0  │          │ Known   │          ║
║   │ Domain  │          │ Lookup  │          │ Free    │          │ Emails  │          ║
║   │ Match   │          │         │          │         │          │ Test    │          ║
║   ├─────────┤          ├─────────┤          ├─────────┤          ├─────────┤          ║
║   │ SILVER  │    ───▶  │ Input   │    ───▶  │ Tier 1  │    ───▶  │ MX      │          ║
║   │ Exact   │          │ Fallback│          │ Low Cost│          │ Check   │          ║
║   │ Name    │          │         │          │         │          │         │          ║
║   ├─────────┤          ├─────────┤          ├─────────┤          ├─────────┤          ║
║   │ BRONZE  │          │ DNS/MX  │          │ Tier 1.5│          │ SMTP    │          ║
║   │ Fuzzy   │          │ Validate│          │ Mid Cost│          │ Verify  │          ║
║   │ + City  │          │         │          │         │          │         │          ║
║   └─────────┘          └─────────┘          ├─────────┤          ├─────────┤          ║
║                                             │ Tier 2  │          │ Million │          ║
║                                             │ Premium │          │ Verifier│          ║
║                                             └─────────┘          └─────────┘          ║
║                                                                                        ║
║   ┌────────────────────────────────────────────────────────────────────────────────┐  ║
║   │                           BIT ENGINE (Sub-Hub)                                  │  ║
║   │                                                                                 │  ║
║   │   Signal Intake ──▶ Deduplicate ──▶ Score Calc ──▶ BIT Score (0-100)           │  ║
║   │   (DOL, People,      (24h/365d)     (impact ×       ≥25 = WARM                 │  ║
║   │    TalentFlow)                       decay)                                     │  ║
║   └────────────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                        ║
╚════════════════════════════════════════╤═══════════════════════════════════════════════╝
                                         │
                                         │ company_id + domain + email_pattern
                                         │
          ┌──────────────────────────────┴──────────────────────────────┐
          │                                                             │
          ▼                                                             ▼
╔═══════════════════════════════════════════════╗    ╔════════════════════════════════════╗
║              PEOPLE SPOKE                      ║    ║           DOL SPOKE                ║
╠═══════════════════════════════════════════════╣    ╠════════════════════════════════════╣
║                                               ║    ║                                    ║
║   Phase 0: Ingest & Classify                  ║    ║   Import: Load Form 5500 data      ║
║   ──────────────────────────                  ║    ║   ──────────────────────────       ║
║   SUSPECT → WARM → APPOINTMENT                ║    ║   CSV → Staging → Tables           ║
║              │                                ║    ║              │                     ║
║              ▼                                ║    ║              ▼                     ║
║   Phase 5: Email Generation                   ║    ║   Process: EIN Matching            ║
║   ─────────────────────────                   ║    ║   ─────────────────────            ║
║   Pattern + Name → Email                      ║    ║   EIN → Company (exact match)      ║
║              │                                ║    ║              │                     ║
║              ▼                                ║    ║              ▼                     ║
║   Phase 6: Slot Assignment                    ║    ║   Validate: Hub Gate Check         ║
║   ────────────────────────                    ║    ║   ─────────────────────            ║
║   CHRO > HR_MGR > BENEFITS > PAYROLL          ║    ║   Company anchor valid?            ║
║              │                                ║    ║              │                     ║
║              ▼                                ║    ║              ▼                     ║
║   Phase 7: Enrichment Queue                   ║    ║   Signal: Emit to BIT Engine       ║
║   ─────────────────────────                   ║    ║   ───────────────────────          ║
║   HIGH → MEDIUM → LOW priority                ║    ║   FORM_5500_FILED (+5)             ║
║              │                                ║    ║   LARGE_PLAN (+8)                  ║
║              ▼                                ║    ║   BROKER_CHANGE (+7)               ║
║   Phase 8: Output Writer                      ║    ║              │                     ║
║   ──────────────────────                      ║    ║              │                     ║
║   CSV files + Summary                         ║    ║              │                     ║
║                                               ║    ║              │                     ║
║   ┌─────────────────────────────────────┐    ║    ║              │                     ║
║   │      TALENT FLOW (Sub-Hub)          │    ║    ║              │                     ║
║   │                                     │    ║    ║              │                     ║
║   │   LinkedIn ──▶ Movement Detection   │    ║    ║              │                     ║
║   │                     │               │    ║    ║              │                     ║
║   │   EXEC_JOINED (+10) │ EXEC_LEFT (+6)│    ║    ║              │                     ║
║   │                     ▼               │    ║    ║              │                     ║
║   │   Signals ──────────────────────────┼────╬────╬──────────────┘                     ║
║   └─────────────────────────────────────┘    ║    ║                                    ║
║                                               ║    ║                                    ║
║   ┌─────────────────────────────────────┐    ║    ╚════════════════════════════════════╝
║   │   EMAIL VERIFICATION (Sub-Wheel)    │    ║
║   │                                     │    ║
║   │   Generated Email                   │    ║
║   │        │                            │    ║
║   │        ▼                            │    ║
║   │   MillionVerifier API               │    ║
║   │   $0.001-$0.004/email               │    ║
║   │        │                            │    ║
║   │        ▼                            │    ║
║   │   ok/catch_all → Accept             │    ║
║   │   invalid/disp → Reject             │    ║
║   │        │                            │    ║
║   │        ▼                            │    ║
║   │   EMAIL_VERIFIED (+2) → BIT Engine  │    ║
║   └─────────────────────────────────────┘    ║
║                                               ║
╚═══════════════════════════════════════════════╝
          │
          ▼
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                                    OUTPUT FILES                                        ║
╠═══════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                        ║
║   output/                                                                              ║
║   ├── people_final.csv          All people with emails and slot assignments            ║
║   │   └── person_id, company_id, email, slot_type, seniority_score, confidence        ║
║   │                                                                                    ║
║   ├── slot_assignments.csv      Slot assignments grouped by company                    ║
║   │   └── company_id, chro_id, hr_manager_id, benefits_id, payroll_id                 ║
║   │                                                                                    ║
║   ├── enrichment_queue.csv      Items needing additional processing                    ║
║   │   └── entity_id, reason, priority, retry_count, status                            ║
║   │                                                                                    ║
║   └── pipeline_summary.txt      Human-readable execution summary                       ║
║       └── Phase stats, timing, error counts, completion rates                         ║
║                                                                                        ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝
          │
          ▼
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                                  OUTREACH (PLANNED)                                    ║
╠═══════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                        ║
║   ┌─────────────────────────────────────────────────────────────────────────────────┐ ║
║   │                                                                                 │ ║
║   │   BIT Score ≥ 25 (WARM)                                                         │ ║
║   │        │                                                                        │ ║
║   │        ▼                                                                        │ ║
║   │   Campaign Assignment ──▶ Sequence Selection ──▶ Email Send ──▶ Track Response │ ║
║   │                                                                                 │ ║
║   └─────────────────────────────────────────────────────────────────────────────────┘ ║
║                                                                                        ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝
```

---

## Quick Reference: All Components

| Component | Type | Location | Status | Phases/Steps |
|-----------|------|----------|--------|--------------|
| **Company Hub** | Master Node | `hub/company/` | ACTIVE | P1→P2→P3→P4 |
| ├─ Phase 1 | Pipeline | `phases/phase1_company_matching.py` | ACTIVE | GOLD→SILVER→BRONZE matching |
| ├─ Phase 2 | Pipeline | `phases/phase2_domain_resolution.py` | ACTIVE | Master→Input→DNS→MX |
| ├─ Phase 3 | Pipeline | `phases/phase3_email_pattern_waterfall.py` | ACTIVE | Tier 0→1→1.5→2→3 |
| ├─ Phase 4 | Pipeline | `phases/phase4_pattern_verification.py` | ACTIVE | Known→MX→SMTP→MillionVerify |
| └─ **BIT Engine** | Sub-Hub | `hub/company/bit_engine.py` | PLANNED | Signal→Dedup→Score→Threshold |
| **People Spoke** | Spoke #1 | `spokes/people/` | ACTIVE | P0→P5→P6→P7→P8 |
| ├─ Phase 0 | Pipeline | `phases/phase0_people_ingest.py` | ACTIVE | Classify (SUSPECT/WARM/etc) |
| ├─ Phase 5 | Pipeline | `phases/phase5_email_generation.py` | ACTIVE | Pattern→Name→Email |
| ├─ Phase 6 | Pipeline | `phases/phase6_slot_assignment.py` | ACTIVE | Title→Slot (CHRO/HR/etc) |
| ├─ Phase 7 | Pipeline | `phases/phase7_enrichment_queue.py` | ACTIVE | Priority queue (H/M/L) |
| ├─ Phase 8 | Pipeline | `phases/phase8_output_writer.py` | ACTIVE | CSV output |
| ├─ **Talent Flow** | Sub-Hub | `spokes/people/talent_flow/` | SHELL | LinkedIn→Movement→Signals |
| ├─ **Email Verify** | Sub-Wheel | `sub_wheels/email_verification/` | ACTIVE | Pattern→MillionVerify |
| └─ **FREE Extract** | Pipeline | `scripts/state_extraction_pipeline.py` | ✅ COMPLETE | 7-stage state extraction |
| **DOL Spoke** | Spoke #2 | `spokes/dol/` | ACTIVE | Import→Match→Validate→Signal |
| ├─ Import | Pipeline | `importers/import_5500.py` | ACTIVE | CSV→Staging→Tables |
| ├─ Process | Pipeline | `dol_spoke.py` | ACTIVE | EIN→Company→HubGate |
| └─ Signal | Pipeline | `dol_spoke.py:_send_signal()` | ACTIVE | 365-day dedup→BIT |
| **Blog Spoke** | Spoke #3 | `spokes/blog/` | PLANNED | News→Sentiment→Signal |
| **Outreach** | Output | - | PLANNED | BIT≥25→Campaign→Send |

### FREE State Extraction Pipeline (✅ COMPLETE - 2026-01-30)

```
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                          FREE STATE EXTRACTION PIPELINE                                ║
║                        scripts/state_extraction_pipeline.py                            ║
║                              Status: ✅ ALL 9 STATES COMPLETE                          ║
╠═══════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                        ║
║   APPROVED SOURCE TYPES (4 only - COMPLIANCE CRITICAL):                               ║
║   ├── leadership_page    (Executive team pages)                                        ║
║   ├── team_page          (Staff directories)                                           ║
║   ├── about_page         (About us with personnel)                                     ║
║   └── blog               (Blog author bios)                                            ║
║                                                                                        ║
║   7-STAGE PIPELINE:                                                                    ║
║   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐                 ║
║   │ Stage 1 │──▶│ Stage 2 │──▶│ Stage 3 │──▶│ Stage 4 │──▶│ Stage 5 │                 ║
║   │Baseline │   │  Mint   │   │  Init   │   │  FREE   │   │ Assign  │                 ║
║   │ Check   │   │ Orphans │   │  Slots  │   │ Extract │   │  Slots  │                 ║
║   └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘                 ║
║                                                    │             │                     ║
║                                                    ▼             ▼                     ║
║                                              ┌─────────┐   ┌─────────┐                 ║
║                                              │ Stage 6 │──▶│ Stage 7 │                 ║
║                                              │Generate │   │  Final  │                 ║
║                                              │ Emails  │   │ Report  │                 ║
║                                              └─────────┘   └─────────┘                 ║
║                                                                                        ║
║   RESULTS:                                                                             ║
║   ├── States Processed: PA, OH, VA, MD, NC, KY, OK, DE, WV                            ║
║   ├── Total People: 77,256+                                                            ║
║   ├── CEO Slots: ~37.2%                                                                ║
║   ├── CFO Slots: ~11.7%                                                                ║
║   ├── HR Slots: ~15.7%                                                                 ║
║   └── Paid Queue: ~27,338 URLs remaining for Clay API                                  ║
║                                                                                        ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝
```

---

*Document generated from codebase analysis - 2026-01-30*
