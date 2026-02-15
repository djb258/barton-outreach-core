# Barton Outreach: System Overview

**Version**: 1.0 | **Date**: 2026-02-09 | **Status**: Operational

---

## What It Is

An evidence-based marketing intelligence platform that transforms fragmented public data — DOL filings, executive records, domain signals — into authorized, timing-aware outreach. Every message above Band 2 requires a **proof line**: a traceable citation of detected organizational pressure. The system intercepts companies in motion. It does not persuade static targets.

---

## By The Numbers

| Metric | Count |
|--------|-------|
| Companies tracked (CL) | 102,922 |
| Outreach-ready pipeline | 95,837 |
| Executive slots (CEO/CFO/HR) | 285,012 |
| Slots filled with verified contacts | 178,043 (62.5%) |
| People records | 182,946 |
| Companies with email patterns | 82,074 (85.6%) |
| DOL benefits intelligence | 70,150 companies (73.2%) |
| Renewal timing known | 70,142 companies |
| Company domains verified alive | 85,521 (90%) |
| Blog/About/Press URLs indexed | 114,736 across 40,381 companies |

---

## Hub-and-Spoke Architecture

```
                         ┌──────────────────────────────────┐
                         │    CL AUTHORITY REGISTRY          │
                         │    (PARENT HUB)                   │
                         │                                   │
                         │    102,922 companies tracked      │
                         │    95,837 outreach_id minted      │
                         │    5,327 excluded                 │
                         │                                   │
                         │    YOU GET:                        │
                         │    - Immutable sovereign ID        │
                         │    - Write-once identity pointers  │
                         │    - Lifecycle state tracking      │
                         └───────────────┬──────────────────┘
                                         │
                                         │ outreach_id (universal FK)
                                         │
                         ┌───────────────┴──────────────────┐
                         │    OUTREACH SPINE                  │
                         │    95,837 records                  │
                         │    (95,004 cold + 833 partners)    │
                         └───────────────┬──────────────────┘
                                         │
              ┌──────────────┬───────────┼───────────┬──────────────┐
              │              │           │           │              │
              ▼              ▼           ▼           ▼              ▼
┌─────────────────┐ ┌──────────────┐ ┌─────────────────┐ ┌──────────────┐ ┌──────────────┐
│ COMPANY TARGET  │ │ DOL FILINGS  │ │ PEOPLE          │ │ BLOG CONTENT │ │ CLS ENGINE   │
│ (04.04.01)      │ │ (04.04.03)   │ │ (04.04.02)      │ │ (04.04.05)   │ │              │
│ GATE: #1        │ │ GATE: #2     │ │ GATE: #3        │ │ GATE: #4     │ │ POST-GATES   │
├─────────────────┤ ├──────────────┤ ├─────────────────┤ ├──────────────┤ ├──────────────┤
│                 │ │              │ │                 │ │              │ │              │
│ 95,837 records  │ │ 70,150       │ │ 182,946 people  │ │ 95,004       │ │ 13,226       │
│ 100% coverage   │ │ 73.2%        │ │ 285,012 slots   │ │ 100%         │ │ 13.8%        │
│                 │ │ coverage     │ │ 178,043 filled  │ │ coverage     │ │ coverage     │
│                 │ │              │ │ (62.5%)         │ │              │ │              │
│ YOU GET:        │ │ YOU GET:     │ │ YOU GET:        │ │ YOU GET:     │ │ YOU GET:     │
│                 │ │              │ │                 │ │              │ │              │
│ - Domain        │ │ - EIN        │ │ - CEO name      │ │ - About page │ │ - Auth band  │
│   resolution    │ │   (70,150)   │ │   + email       │ │   (29,483)   │ │   (0-5)      │
│ - Email pattern │ │ - Filing     │ │   (62,404)      │ │ - Press/news │ │ - Proof      │
│   (82,074)      │ │   status     │ │ - CFO name      │ │   (16,603)   │ │   lines      │
│ - Pattern type  │ │   (64,975)   │ │   + email       │ │ - Leadership │ │ - Pressure   │
│   (GUESS/FACT)  │ │ - Carrier    │ │   (57,399)      │ │   pages      │ │   class      │
│ - MX validation │ │   (10,233)   │ │ - HR name       │ │   (12,829)   │ │ - Convergence│
│ - Domain status │ │ - Broker     │ │   + email       │ │ - Careers    │ │   score      │
│   (alive/dead)  │ │   (6,995)    │ │   (58,240)      │ │   (17,659)   │ │ - Recommended│
│                 │ │ - Funding    │ │ - LinkedIn      │ │ - Team pages │ │   channel    │
│                 │ │   type       │ │   (143,825)     │ │   (9,287)    │ │              │
│                 │ │   (70,150)   │ │ - Phone (680)   │ │ - Contact    │ │              │
│                 │ │ - Renewal    │ │ - Barton ID     │ │   (27,662)   │ │              │
│                 │ │   month      │ │                 │ │              │ │              │
│                 │ │   (70,142)   │ │                 │ │ 114,736 URLs │ │              │
│                 │ │ - Outreach   │ │ 99.1% have      │ │ across       │ │              │
│                 │ │   start      │ │ email           │ │ 40,381       │ │              │
│                 │ │   month      │ │ 80.8% have      │ │ companies    │ │              │
│                 │ │              │ │ LinkedIn        │ │              │ │              │
│                 │ │ 432,582      │ │                 │ │              │ │              │
│                 │ │ Form 5500    │ │                 │ │              │ │              │
│                 │ │ 625,520      │ │                 │ │              │ │              │
│                 │ │ Schedule A   │ │                 │ │              │ │              │
└─────────────────┘ └──────────────┘ └─────────────────┘ └──────────────┘ └──────────────┘

WATERFALL ORDER: CT must PASS → DOL must PASS → People must PASS → Blog → CLS scores
```

### Per-Slot Breakdown

| Slot Type | Total Slots | Filled | Fill Rate | With Email | With LinkedIn |
|-----------|-------------|--------|-----------|------------|---------------|
| **CEO** | 95,004 | 62,404 | 65.7% | 61,840+ | 50,400+ |
| **CFO** | 95,004 | 57,399 | 60.4% | 56,900+ | 46,300+ |
| **HR** | 95,004 | 58,240 | 61.3% | 57,600+ | 47,100+ |
| **Total** | **285,012** | **178,043** | **62.5%** | **176,366** | **143,825** |

### DOL Intelligence Breakdown

| Data Point | Count | Coverage | Source |
|------------|-------|----------|--------|
| EIN (company ID) | 70,150 | 100% of DOL | Form 5500 |
| Filing present | 64,975 | 92.6% | Form 5500 |
| Funding type | 70,150 | 100% | Form 5500 |
| Renewal month | 70,142 | 100% | Plan year begin |
| Outreach start month | 70,142 | 100% | Renewal - 5 months |
| Insurance carrier | 10,233 | 14.6% | Schedule A |
| Broker/advisor | 6,995 | 10.0% | Schedule C |
| Form 5500 filings | 432,582 | 3 years | DOL EFAST2 |
| Schedule A records | 625,520 | 3 years | DOL EFAST2 |

---

## Three Messaging Lanes

| Lane | Purpose | Records | Schema |
|------|---------|---------|--------|
| **Cold Outreach** | New prospect engagement via CLS scoring | 95,837 | `outreach.*` |
| **Appointments Already Had** | Re-engage stalled/ghosted meetings | 771 | `sales.*` |
| **Fractional CFO Partners** | Build partner referral network | 833 | `partners.*` |

Each lane is isolated. No cross-lane data flow. No shared state.

---

## The Pipeline

```
COMPANY IDENTITY (CL)          What: Write-once authority registry
  102,922 companies             Why:  One sovereign ID per company, forever
         |
         v
COMPANY TARGET (04.04.01)      What: Domain + email pattern discovery
  95,837 targeting-ready        Why:  Know HOW to reach them
  86.4% with email patterns     How:  Hunter -> Domain analysis -> Verified promotion
         |
         v
DOL FILINGS (04.04.03)         What: Benefits intelligence from federal data
  70,150 with EIN bridge        Why:  Know WHEN to reach them (renewal timing)
  1.06M filing rows             How:  Form 5500 + Schedule A + Schedule C
         |
         v
PEOPLE INTELLIGENCE (04.04.02) What: Executive slot discovery + email generation
  178,043 slots filled          Why:  Know WHO to reach
  182,946 people records        How:  Hunter + Clay + leadership page scraping
         |
         v
BLOG / CONTENT (04.04.05)      What: Narrative signals from company websites
  114,736 URLs indexed          Why:  Know what's HAPPENING (timing amplifier)
  40,381 companies covered      How:  Sitemap-first discovery, 8 URL types
         |
         v
CLS AUTHORIZATION ENGINE       What: Movement-derived authorization scoring
  6 bands (0-5)                 Why:  Only contact when evidence justifies it
  5 pressure classes            How:  Three-domain convergence + proof lines
```

---

## What Makes It Different

### 1. Authorization, Not Scoring
Traditional systems score "intent" and blast emails. This system scores **authorization** — it determines what you're *permitted* to do, not what you *want* to do. Band 3+ requires a proof line tracing back to a real organizational movement.

### 2. Renewal Calendar Intelligence
70,142 companies have known renewal months from DOL filings. The system calculates outreach start (5 months before renewal) automatically. You're not guessing timing — you're reading it from federal records.

### 3. Three-Domain Convergence
Outreach requires pressure from multiple independent sources:

| Domain | Source | Trust | Role |
|--------|--------|-------|------|
| Structural Pressure | DOL filings | Highest | Gravity (required for authority) |
| Decision Surface | People/Exec changes | High | Direction (who can act) |
| Narrative Volatility | Blog/News | Lowest | Amplifier only |

One domain moving = noise. Two = watch. Three aligned = act. **Blog alone never justifies contact.**

### 4. Verified Email -> Free Pattern Derivation
When one person's email is verified (jane.doe@acme.com), the system derives the company pattern (first.last), locks it as FACT, and generates all future emails deterministically. One verification makes every subsequent contact at that company free.

### 5. Slot-First Architecture
The system tracks 285,012 structural slots (CEO/CFO/HR per company), not just people. When an executive leaves, the slot empties — it doesn't vanish. The company's structure persists through people churn.

### 6. System-Failure Framing
Messages lead with what's broken in the prospect's organization, never with product:

> *"Your employer contribution rose 18% last year while headcount stayed flat — that's a cost visibility gap we can close."*

> *"You've changed brokers twice in three years. That pattern usually means the underlying data infrastructure isn't transferring. We fix that layer."*

---

## Proof Line System

Every Band 3+ message must include a proof line — a traceable evidence chain:

**Band 3** (Single-source):
```
COST_PRESSURE detected via DOL: employer contribution +18% YoY, renewal in 75 days
```

**Band 4** (Multi-source):
```
VENDOR_DISSATISFACTION convergence: broker changed YoY (DOL) + new HR leader 90 days (People)
```

**Band 5** (Full-chain):
```
PHASE TRANSITION: DEADLINE_PROXIMITY — renewal in 45 days (DOL) + new CHRO 60 days
(People) + funding announced (Blog) — Decision window: 45 days
```

Proofs expire when movements expire. They cannot be refreshed — they must regenerate from current state.

---

## Safety Mechanisms

| Mechanism | What It Does |
|-----------|-------------|
| **Write-Once CL** | Company IDs minted once, never modified downstream |
| **Waterfall Gates** | Each sub-hub must PASS before the next executes |
| **Kill Switch** | Immediate halt per company or globally, no grace period |
| **Pattern Lock** | Verified email patterns locked against overwrite |
| **Proof Expiration** | Stale evidence auto-expires, can't justify contact |
| **CTB Registry** | 249 tables governed, 9 frozen core tables, 0 violations |
| **Band Caps** | No DOL = max Band 2. Blog alone = max Band 1 |

---

## Pressure Classes

| Class | What's Broken | Primary Source |
|-------|---------------|----------------|
| **Cost Pressure** | No cost visibility, silent drift, blind renewal decisions | DOL |
| **Vendor Dissatisfaction** | Broker churn, manual processes, lost institutional knowledge | DOL + People |
| **Deadline Proximity** | Renewal treated as event not process, compressed decisions | DOL |
| **Organizational Reconfiguration** | New executives inherit no context, no continuity layer | People |
| **Operational Chaos** | Filing irregularities, compliance gaps, missed deadlines | DOL |

---

## Data Sources

| Source | What It Provides | Records |
|--------|-----------------|---------|
| **DOL Form 5500** | Benefits filings, EIN, plan year, funding type | 432,582 filings |
| **DOL Schedule A** | Insurance carriers, brokers, commissions | 625,520 records |
| **Hunter.io** | Email contacts, company patterns, LinkedIn | 583,433 contacts |
| **Clay** | People profiles, LinkedIn URLs, company data | 120,045 intake records |
| **Company Websites** | About/Press/Leadership/Careers pages | 114,736 URLs |
| **Domain Verification** | MX records, alive/dead status | 95,004 domains checked |

---

*Barton Outreach Core v1.0 — Certified 2026-01-19 — Three Messaging Lanes Active 2026-02-09*
