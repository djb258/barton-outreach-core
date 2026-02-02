# Outreach Waterfall Doctrine

**Version**: 1.0
**Last Updated**: 2026-02-02
**Status**: AUTHORITATIVE

---

## Purpose

This document explains how data flows through the Outreach system from raw company input to fully actionable people slots. It is the single source of truth for understanding hub ownership, execution order, and enforcement boundaries.

---

## The Golden Rule

```
No hub may act on data it does not own.
No hub may invent data another hub is responsible for.
No hub may bypass the waterfall order.
```

---

## Waterfall Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         OUTREACH WATERFALL                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   STEP 1: Company Lifecycle (CL)                                        │
│           ├── Verify company identity                                   │
│           ├── Confirm official URL                                      │
│           └── Confirm LinkedIn company page                             │
│                          │                                              │
│                          ▼                                              │
│   STEP 2: Sovereign ID Issuance                                         │
│           └── Mint sovereign_company_id (CL DONE contract)              │
│                          │                                              │
│                          ▼                                              │
│   STEP 3: Outreach ID Creation                                          │
│           └── Assign outreach_id linked to sovereign_company_id         │
│                          │                                              │
│                          ▼                                              │
│   STEP 4: Company Target (CT)                                           │
│           ├── Discover email pattern                                    │
│           └── Compute BIT score                                         │
│                          │                                              │
│                          ▼                                              │
│   STEP 5: DOL Matching                                                  │
│           └── Attempt EIN linkage (best-effort, non-blocking)           │
│                          │                                              │
│                          ▼                                              │
│   STEP 6: Content Expansion (Blog / About Us)                           │
│           ├── Extract About Us content                                  │
│           └── Extract Blog/News content                                 │
│                          │                                              │
│                          ▼                                              │
│   STEP 7: People Slot Filling                                           │
│           ├── CEO slot                                                  │
│           ├── CFO slot                                                  │
│           └── HR/Benefits slot                                          │
│                          │                                              │
│                          ▼                                              │
│   OUTCOME: Company is FULLY ACTIONABLE for campaigns                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Explanation

### Step 1 — Company Lifecycle (CL): Authority Verification

**Owner**: CL Hub
**Input**: Company name (raw)

**What happens**:
- CL receives a company name and attempts to verify it as a real, operating business entity
- CL confirms the **official company URL** (website domain)
- CL confirms the **LinkedIn company page** URL
- CL validates identity through domain resolution and existence checks

**Outcome**:
- Company is verified as a real operating entity
- Domain and LinkedIn are now **authoritative** (owned by CL)
- If verification fails, the record is marked with a failure reason and does not proceed

**Key Rule**: CL is the ONLY hub that discovers domains. No other hub may discover, infer, or fabricate a domain.

---

### Step 2 — Sovereign ID Issuance

**Owner**: CL Hub
**Condition**: CL verification successful

**What happens**:
- CL mints a **Sovereign Company ID** (`sovereign_company_id`)
- This ID is registered in `cl.company_identity` as the authoritative company record
- The Sovereign ID is immutable once issued

**Outcome**:
- Sovereign ID represents the **CL DONE contract**
- The company is now eligible for all downstream hubs
- Any hub seeing a Sovereign ID can trust that CL has completed its work

**Key Rule**: Sovereign ID = CL DONE. If `sovereign_company_id IS NULL`, CL is not complete and downstream hubs must not act.

---

### Step 3 — Outreach ID Creation

**Owner**: Outreach Spine
**Condition**: Sovereign ID exists

**What happens**:
- An **Outreach ID** (`outreach_id`) is minted in `outreach.outreach`
- The Outreach ID is linked to the Sovereign Company ID
- The Outreach ID is written ONCE to `cl.company_identity` (write-once registration)

**Outcome**:
- Outreach ID becomes the **tracking key** across all downstream sub-hubs
- All sub-hub tables use `outreach_id` as their foreign key
- The company is now in the Outreach operational spine

**Key Rule**: Outreach ID is minted by Outreach, not CL. CL only stores the pointer.

---

### Step 4 — Company Target (CT): Targeting Readiness

**Owner**: CT Sub-Hub
**Inputs**: Sovereign ID, Company domain (from CL)

**What happens**:
- CT **consumes** the domain that CL discovered (CT does not discover domains)
- CT discovers the **email pattern** for the domain (e.g., `{first}.{last}@domain.com`)
- CT computes the **BIT score** (Buyer Intent Targeting score)
- CT determines execution readiness

**Outcome**:
- Company becomes **targetable**
- Email pattern enables email generation for people
- BIT score enables prioritization for campaigns
- CT DONE = `execution_status = 'ready'` + `email_method IS NOT NULL`

**Key Rule**: CT consumes data from CL. CT never discovers domains, scrapes websites for identity, or invents upstream data.

---

### Step 5 — DOL Matching

**Owner**: DOL Sub-Hub
**Inputs**: Outreach ID, Company identity

**What happens**:
- DOL attempts to match the company to an **EIN** (Employer Identification Number)
- DOL validates against Department of Labor filings (Form 5500, Schedule A)
- DOL establishes regulatory linkage when possible

**Outcome**:
- Companies with EIN matches have regulatory context for outreach
- Companies without matches are **parked** (structural failure, not fixable)
- DOL failures do NOT block upstream work

**Key Rule**: DOL is best-effort and non-blocking. A DOL failure (NO_MATCH, NO_STATE) does not prevent CT, Blog, or People from completing.

---

### Step 6 — Content Expansion (Blog / About Us)

**Owner**: Blog Sub-Hub
**Inputs**: Verified company URLs (from CL)

**What happens**:
- Blog extracts **About Us** content from the company website
- Blog extracts **Blog/News** content for signals
- Blog identifies hiring signals, growth indicators, and timing cues

**Outcome**:
- Company narrative context is captured
- Content signals inform campaign personalization
- Blog DONE = content successfully extracted and stored

**Key Rule**: Blog depends on CL for URLs. If CL failed, Blog cannot proceed.

---

### Step 7 — People Slot Filling

**Owner**: People Intelligence Sub-Hub
**Inputs**: Company identity, Domain, Email pattern, Content context

**What happens**:
- People hub identifies executives for each slot type:
  - **CEO** — Chief Executive Officer
  - **CFO** — Chief Financial Officer
  - **HR/Benefits** — Human Resources / Benefits Decision Maker
- People hub generates email addresses using CT's email pattern
- People hub verifies emails using MillionVerifier (when gated)

**Outcome**:
- Company becomes **fully actionable** for outreach campaigns
- Each slot contains a verified contact
- Campaign sequences can begin

**Key Rule**: People depends on CT for email pattern. If CT is not DONE, People cannot generate valid emails.

---

## Hub Ownership Matrix

| Hub | Owns | Consumes | Never Does |
|-----|------|----------|------------|
| **CL** | Domain, LinkedIn, Sovereign ID | Raw company name | — |
| **Outreach Spine** | Outreach ID | Sovereign ID | Mint Sovereign ID |
| **CT** | Email pattern, BIT score | Domain from CL | Discover domains |
| **DOL** | EIN linkage | Company identity | Block upstream |
| **Blog** | Content signals | URLs from CL | Discover URLs |
| **People** | Slot assignments, Emails | Email pattern from CT | Generate emails without pattern |

---

## Enforcement Boundaries

### What Each Hub CAN Do

| Hub | Allowed Actions |
|-----|-----------------|
| CL | Verify identity, discover domain, mint Sovereign ID |
| CT | Consume domain, discover email pattern, compute BIT score |
| DOL | Match EIN, park structural failures |
| Blog | Extract content from verified URLs |
| People | Fill slots, generate emails using pattern |

### What Each Hub CANNOT Do

| Hub | Forbidden Actions |
|-----|-------------------|
| CL | Mint Outreach ID, fill people slots |
| CT | Discover domains, scrape for identity, bypass CL |
| DOL | Block upstream hubs, force EIN matches |
| Blog | Discover URLs, operate without CL URLs |
| People | Generate emails without pattern, bypass CT |

---

## Error Handling by Hub

| Hub | Error Type | Disposition | Impact |
|-----|------------|-------------|--------|
| **CL** | DOMAIN_FAIL, COLLISION | ARCHIVE | Record cannot proceed |
| **CT** | NO_MX, PATTERN_FAIL | RETRY or PARK | Blocks People |
| **DOL** | NO_MATCH, NO_STATE | PARK | Non-blocking |
| **Blog** | UPSTREAM_FAIL | AUTO-RESOLVE | Waits for CT |
| **People** | ENRICHMENT_FAIL | RETRY | Blocks campaign |

---

## Readiness Tiers

| Tier | Meaning | Requirements |
|------|---------|--------------|
| **NOT_READY** | Cannot be used for campaigns | Missing CT DONE or other blockers |
| **TIER_0_ANCHOR_DONE** | CT complete, targeting possible | CT DONE = true |
| **TIER_2_ENRICHMENT_COMPLETE** | Full enrichment done | CT + DOL + Blog complete |
| **TIER_3_CAMPAIGN_READY** | Ready for active campaigns | All slots filled, emails verified |

---

## Frequently Asked Questions

### Q: Why can't CT discover domains?

**A**: CL is the authority on company identity. If CT could discover domains, there would be two sources of truth, leading to conflicts, duplicate records, and audit failures. CL owns identity; CT consumes it.

### Q: What happens if DOL fails?

**A**: DOL failures are **parked**, not retried. DOL matching is best-effort — many companies don't file Form 5500 or are in states without coverage. DOL failure does NOT block CT, Blog, or People.

### Q: When can People fill slots?

**A**: People can only fill slots when:
1. Sovereign ID exists (CL DONE)
2. Email pattern exists (CT DONE)
3. Company is targetable

### Q: What is the Sovereign ID?

**A**: The Sovereign ID is the **CL DONE contract**. It means:
- Company identity is verified
- Domain is authoritative
- LinkedIn is confirmed
- All downstream hubs may proceed

### Q: Can I bypass the waterfall for speed?

**A**: No. The waterfall is enforced by database constraints and runtime gates. Attempting to bypass will result in HARD_FAIL errors.

---

## Visual Summary

```
                    ┌─────────────────────┐
                    │   COMPANY NAME      │
                    │   (Raw Input)       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   COMPANY LIFECYCLE │
                    │   (CL Hub)          │
                    │                     │
                    │   Verify Identity   │
                    │   Discover Domain   │
                    │   Confirm LinkedIn  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   SOVEREIGN ID      │
                    │   (CL DONE)         │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   OUTREACH ID       │
                    │   (Tracking Key)    │
                    └──────────┬──────────┘
                               │
               ┌───────────────┼───────────────┐
               │               │               │
               ▼               ▼               ▼
        ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
        │     CT      │ │    DOL      │ │    BLOG     │
        │             │ │             │ │             │
        │ Email       │ │ EIN Match   │ │ Content     │
        │ Pattern     │ │ (optional)  │ │ Signals     │
        │ BIT Score   │ │             │ │             │
        └──────┬──────┘ └─────────────┘ └─────────────┘
               │
               ▼
        ┌─────────────┐
        │   PEOPLE    │
        │             │
        │ CEO Slot    │
        │ CFO Slot    │
        │ HR Slot     │
        └──────┬──────┘
               │
               ▼
        ┌─────────────────────┐
        │   CAMPAIGN READY    │
        │   (Fully Actionable)│
        └─────────────────────┘
```

---

## Document Control

| Field | Value |
|-------|-------|
| **Author** | Doctrine Explainer Agent |
| **Approved By** | System Owner |
| **Effective Date** | 2026-02-02 |
| **Review Cycle** | Quarterly |
| **Change Control** | DO_NOT_MODIFY_REGISTRY.md |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `CLAUDE.md` | Bootstrap guide for agents |
| `doctrine/DO_NOT_MODIFY_REGISTRY.md` | Frozen components list |
| `docs/GO-LIVE_STATE_v1.0.md` | Production baseline state |
| `TOOL_CANON_ENFORCEMENT.md` | Approved tools and gates |

---

**END OF DOCUMENT**
