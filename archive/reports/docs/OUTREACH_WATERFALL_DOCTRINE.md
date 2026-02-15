# Outreach Waterfall Doctrine

**Version**: 1.3
**Last Updated**: 2026-02-02
**Status**: AUTHORITATIVE
**Changes**:
- v1.1: Added Bridge Paths & Blog → People Enrichment Flow
- v1.2: Added Reverse Flow: Verified Email → Company Target Promotion
- v1.3: Added Verification Gate (GUESS → FACT state flip) + Agent Chain

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
**URL Source**: `company.company_source_urls` (bridge via domain → `company.company_master`)

**What happens**:
- Blog extracts **About Us** content from the company website
- Blog extracts **Blog/News** content for signals
- Blog extracts **Leadership/Team** pages for people discovery
- Blog identifies hiring signals, growth indicators, and timing cues

**URL Types Available**:
| Type | Count | Purpose |
|------|-------|---------|
| `about_page` | 24,099 | Company narrative |
| `press_page` | 14,377 | Timing signals |
| `leadership_page` | 9,214 | CEO/CFO discovery |
| `team_page` | 7,959 | HR discovery |

**Outcome**:
- Company narrative context is captured
- Content signals inform campaign personalization
- **Leadership/Team pages feed directly into People slot filling**
- Blog DONE = content successfully extracted and stored

**Key Rule**: Blog depends on CL for URLs. If CL failed, Blog cannot proceed.

**Bridge Path**: See "Bridge Paths & Cross-Schema Joins" section for query patterns.

---

### Step 7 — People Slot Filling

**Owner**: People Intelligence Sub-Hub
**Inputs**: Company identity, Domain, Email pattern, **Blog content (leadership/team pages)**

**What happens**:
- People hub identifies executives for each slot type:
  - **CEO** — Chief Executive Officer (from `leadership_page`)
  - **CFO** — Chief Financial Officer (from `leadership_page`)
  - **HR/Benefits** — Human Resources / Benefits Decision Maker (from `team_page`)
- People hub generates email addresses using CT's email pattern
- People hub verifies emails using MillionVerifier (when gated)

**Tables Involved**:
| Table | Purpose |
|-------|---------|
| `company.company_source_urls` | Leadership/team page URLs |
| `people.people_master` | Person records |
| `people.company_slot` | Slot assignments (CEO/CFO/HR × company) |

**Outcome**:
- Company becomes **fully actionable** for outreach campaigns
- Each slot contains a verified contact
- Campaign sequences can begin

**Key Rule**: People depends on CT for email pattern. If CT is not DONE, People cannot generate valid emails.

**Data Flow**:
```
company.company_source_urls (leadership_page, team_page)
    ↓ Extract names, titles
people.people_master (person records)
    ↓ Assign to company
people.company_slot (CEO/CFO/HR slots)
    ↓ Generate email via CT pattern
outreach.company_target (email_method)
```

---

## Hub Ownership Matrix

| Hub | Owns | Consumes | Feeds Into |
|-----|------|----------|------------|
| **CL** | Domain, LinkedIn, Sovereign ID | Raw company name | CT, Blog, DOL |
| **Outreach Spine** | Outreach ID | Sovereign ID | All sub-hubs |
| **CT** | Email pattern, BIT score, **canonical_verified_email** | Domain from CL, **verified email from People** | People (email pattern) |
| **DOL** | EIN linkage | Company identity | (non-blocking) |
| **Blog** | Content signals, URLs | URLs from CL | **People** (leadership/team pages) |
| **People** | Slot assignments, Emails | Email pattern from CT, **URLs from Blog** | Campaigns, **CT** (verified email promotion) |

> **Note**: People → CT is a **reverse flow** (fact promotion). See "Reverse Flow: Verified Email → Company Target Promotion" section.

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

## Bridge Paths & Cross-Schema Joins

This section documents how to navigate between schemas when data lives in different ownership domains.

### Blog Sub-Hub → Company URLs Bridge

**Problem**: Blog content URLs (About Us, Press, etc.) live in `company.company_source_urls` using `company_unique_id` (format: `04.04.01.xx`), but Outreach uses `outreach_id` (UUID).

**Solution**: Bridge via domain matching through `company.company_master`:

```
outreach.outreach (42,192)
    │
    │ JOIN ON: domain → website_url (normalized)
    ▼
company.company_master (74,641)
    │
    │ JOIN ON: company_unique_id
    ▼
company.company_source_urls (97,124)
```

**Bridge Query**:

```sql
SELECT 
    o.outreach_id,
    o.domain,
    csu.source_type,
    csu.source_url,
    csu.page_title
FROM outreach.outreach o
JOIN company.company_master cm ON LOWER(o.domain) = LOWER(
    REPLACE(REPLACE(REPLACE(cm.website_url, 'http://', ''), 'https://', ''), 'www.', '')
)
JOIN company.company_source_urls csu ON csu.company_unique_id = cm.company_unique_id
WHERE csu.source_type IN ('about_page', 'press_page');
```

**Coverage**: 19,996 outreach companies (47.6%) have discoverable URLs via this bridge.

### Blog → People Slot Enrichment Flow

When Blog extracts content, it feeds **context** for People slot filling:

```
┌─────────────────────────────────────────────────────────────────┐
│                BLOG → PEOPLE ENRICHMENT FLOW                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   SOURCE: company.company_source_urls                           │
│           ├── leadership_page (9,214)  ──┐                      │
│           └── team_page (7,959)        ──┤                      │
│                                          ▼                      │
│   PROCESS: People Discovery                                     │
│           ├── Scrape executive bios                             │
│           ├── Match names to LinkedIn                           │
│           └── Extract titles/roles                              │
│                                          │                      │
│                                          ▼                      │
│   TARGET: people.company_slot                                   │
│           ├── CEO slot (person_unique_id)                       │
│           ├── CFO slot (person_unique_id)                       │
│           └── HR slot (person_unique_id)                        │
│                                          │                      │
│                                          ▼                      │
│   ENRICHMENT: Email Generation                                  │
│           ├── Use CT email pattern                              │
│           └── Validate via MillionVerifier                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Join**: People slots connect via `outreach_id`:

```sql
-- Full path: Blog URLs → People Slots
SELECT 
    o.outreach_id,
    o.domain,
    csu.source_type,
    csu.source_url,
    cs.slot_type,
    pm.first_name,
    pm.last_name,
    pm.email
FROM outreach.outreach o
-- Bridge to URLs
JOIN company.company_master cm ON LOWER(o.domain) = LOWER(
    REPLACE(REPLACE(REPLACE(cm.website_url, 'http://', ''), 'https://', ''), 'www.', '')
)
JOIN company.company_source_urls csu ON csu.company_unique_id = cm.company_unique_id
-- Connect to People
LEFT JOIN people.company_slot cs ON o.outreach_id = cs.outreach_id
LEFT JOIN people.people_master pm ON cs.person_unique_id = pm.unique_id
WHERE csu.source_type IN ('leadership_page', 'team_page')
ORDER BY o.outreach_id, cs.slot_type;
```

### Cross-Schema Join Reference

| From | To | Join Strategy |
|------|-----|---------------|
| `outreach.outreach` | `company.company_source_urls` | Domain bridge via `company.company_master` |
| `outreach.outreach` | `people.company_slot` | Direct FK: `outreach_id` |
| `outreach.outreach` | `outreach.company_target` | Direct FK: `outreach_id` |
| `outreach.outreach` | `outreach.blog` | Direct FK: `outreach_id` |
| `people.company_slot` | `people.people_master` | `person_unique_id = unique_id` |
| `outreach.company_target` | `people.company_slot` | Shared `outreach_id` |

### URL Type → Enrichment Use

| URL Type | Source Type | Enrichment Purpose |
|----------|-------------|-------------------|
| About Us | `about_page` | Company narrative, values, personalization |
| News/Press | `press_page` | Timing signals, recent events |
| Leadership | `leadership_page` | **CEO/CFO discovery** |
| Team | `team_page` | **HR/Benefits discovery** |
| Careers | `careers_page` | Expansion signals, hiring context |
| Contact | `contact_page` | Address verification |

---

## Reverse Flow: Verified Email → Company Target Promotion

> **CRITICAL**: This is the **hinge** between People and Company Target that makes downstream Outreach deterministic and cheap.

### Purpose

When **one person's email is VERIFIED**, promote the **full verified email** to **Company Target**, derive the email pattern from that verified fact, and lock it for downstream use.

### Data Flow Diagram

```
┌───────────────────────────────────────────────────────────────────────────┐
│               VERIFIED EMAIL → COMPANY TARGET PROMOTION                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  TRIGGER: Person record with email_verification_status = VERIFIED         │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ people.people_master                                                │  │
│  │   • email_address = jane.doe@acme.com                              │  │
│  │   • email_verification_status = VERIFIED                           │  │
│  │   • company_id = <outreach_id>                                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                      │
│                                    ▼ PROMOTE (fact, not enrichment)       │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ outreach.company_target                                             │  │
│  │   • canonical_verified_email = jane.doe@acme.com                   │  │
│  │   • verified_source = MillionVerifier                              │  │
│  │   • verified_at = 2026-02-02T...                                   │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                      │
│                                    ▼ DERIVE (mechanically, no guessing)   │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ outreach.company_target                                             │  │
│  │   • derived_email_pattern = first.last@domain                      │  │
│  │   • pattern_confidence = HIGH                                       │  │
│  │   • pattern_source = canonical_verified_email                       │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                      │
│                                    ▼ LOCK (authoritative for slots)       │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ Pattern locked for downstream People slot filling                   │  │
│  │ Overwrite blocked unless:                                           │  │
│  │   • bounce detected, OR                                             │  │
│  │   • explicit override flag present                                  │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

### Trigger Conditions

| Condition | Required |
|-----------|----------|
| `email_verification_status = VERIFIED` | ✅ |
| `email_address` present | ✅ |
| `company_id` resolvable | ✅ |
| Execute once per company (unless override) | ✅ |

### Execution Steps (ORDERED, NO SKIPS)

| Step | Action | Target Table |
|------|--------|--------------|
| 1 | Select first VERIFIED person (prefer exec/HR) | `people.people_master` |
| 2 | Abort if CT already has HIGH-confidence pattern | `outreach.company_target` |
| 3 | Promote verified email upstream | `outreach.company_target.canonical_verified_email` |
| 4 | Derive pattern mechanically (e.g., `jane.doe@acme.com` → `first.last@domain`) | `outreach.company_target.derived_email_pattern` |
| 5 | Lock pattern as authoritative | `outreach.company_target.pattern_confidence = HIGH` |
| 6 | Audit log the event | Audit table |

### Pattern Derivation Examples

| Verified Email | Derived Pattern |
|----------------|-----------------|
| `jane.doe@acme.com` | `first.last@domain` |
| `jdoe@acme.com` | `f_initial+last@domain` |
| `jane_doe@acme.com` | `first_last@domain` |
| `jane@acme.com` | `first@domain` |

### Hard Rules

| Rule | Consequence |
|------|-------------|
| Do NOT derive patterns without a verified email | Pattern would be speculation |
| Do NOT update People records in this flow | This is upstream promotion only |
| Do NOT re-verify additional people | One verified = enough for pattern |
| Do NOT overwrite CT without downgrade reason | Preserve HIGH confidence patterns |

### Failure Handling

| Condition | Action |
|-----------|--------|
| Verification status ≠ VERIFIED | Exit silently |
| Pattern already HIGH confidence | No-op + log skip |
| Email malformed | Log error + do not promote |

### Completion Criteria

```
✅ Company Target contains:
   • canonical_verified_email
   • derived_email_pattern  
   • pattern_confidence = HIGH
   
✅ Audit record exists with:
   • company_id
   • person_id
   • verified_email
   • derived_pattern
   • source_tool
   • timestamp
   
✅ Agent exits cleanly
```

### Why This Matters

This reverse flow makes the rest of Outreach **deterministic and cheap**:

1. **One verified email** → pattern for entire company
2. **No speculation** → patterns derived from facts only
3. **Locked patterns** → downstream People slots use authoritative source
4. **Bounce protection** → pattern can be downgraded if bounces detected

### Related Agent: Bounce-Based Downgrade

When a verified pattern produces bounces, a separate **Bounce Downgrade Agent** can:
- Detect bounce signals from `outreach.send_log`
- Downgrade `pattern_confidence` from HIGH to MEDIUM/LOW
- Unlock pattern for re-derivation
- (Implementation: future work)

---

## Verification Gate: Pattern State Flip

> **CRITICAL**: This agent **asserts and locks** verification state. It's the line between GUESS and FACT.

### Purpose

Confirm that a Company Target email pattern is no longer inferred/guessed and **mark it as VERIFIED** only when backed by a promoted, verified email.

### State Transition

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PATTERN STATE FLIP                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   BEFORE (pattern = GUESS):                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ outreach.company_target                                             │   │
│   │   • email_method = first.last@domain (from Hunter/guessed)         │   │
│   │   • email_pattern_status = GUESS                                   │   │
│   │   • pattern_confidence = LOW/MEDIUM                                │   │
│   │   • pattern_locked = false                                         │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼ VERIFICATION GATE RUNS                 │
│                                                                             │
│   AFTER (pattern = FACT):                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ outreach.company_target                                             │   │
│   │   • canonical_verified_email = jane.doe@acme.com                   │   │
│   │   • derived_email_pattern = first.last@domain                      │   │
│   │   • email_pattern_status = VERIFIED                                │   │
│   │   • pattern_confidence = HIGH                                      │   │
│   │   • pattern_locked = true                                          │   │
│   │   • pattern_verified_at = 2026-02-02T...                          │   │
│   │   • pattern_verification_method = single_person_verified          │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Trigger Conditions

| Condition | Required |
|-----------|----------|
| `canonical_verified_email` populated | ✅ |
| `derived_email_pattern` populated | ✅ |
| Pattern not yet marked VERIFIED | ✅ |

### Execution Steps (NO REORDERING)

| Step | Action | Validation |
|------|--------|------------|
| 1 | **Verify Preconditions** | `canonical_verified_email` exists, `email_verification_source` exists |
| 2 | **Validate Consistency** | Re-derive pattern from email, compare to stored pattern |
| 3 | **Flip Verification State** | Set `email_pattern_status = VERIFIED` |
| 4 | **Lock Pattern** | Set `pattern_locked = true` |
| 5 | **Audit Log** | Record company_id, email, pattern, method, timestamp |

### Step 2 Detail: Consistency Validation

```
canonical_verified_email = jane.doe@acme.com
                              ↓ DERIVE
expected_pattern = first.last@domain
                              ↓ COMPARE
stored_pattern = first.last@domain
                              ↓ 
MATCH → proceed to Step 3
MISMATCH → BLOCKED, log error, exit
```

**Mismatch Example**:
```
canonical_verified_email = jdoe@acme.com
expected_pattern = f_initial+last@domain
stored_pattern = first.last@domain  ← WRONG
                              ↓
BLOCKED: Pattern derived from wrong source
```

### Fields Updated

| Field | Before | After |
|-------|--------|-------|
| `email_pattern_status` | GUESS | **VERIFIED** |
| `pattern_confidence` | LOW/MEDIUM | **HIGH** |
| `pattern_locked` | false | **true** |
| `pattern_verified_at` | NULL | timestamp |
| `pattern_verification_method` | NULL | `single_person_verified` |

### Failure Handling

| Condition | Action | Result |
|-----------|--------|--------|
| Preconditions fail (missing email) | No-op | Pattern remains GUESS |
| Pattern mismatch | BLOCKED + error_code | Pattern remains GUESS |
| Already VERIFIED | No-op + audit skip | No change |

### Hard Rules

| Rule | Why |
|------|-----|
| Never mark VERIFIED without promoted verified email | Would be speculation |
| Never infer verification from guesses or heuristics | Only facts allowed |
| Never unlock without explicit downgrade agent | Prevents accidental overwrite |

### Completion Criteria

```
✅ Company Target shows:
   • email_pattern_status = VERIFIED
   • pattern_locked = true
   • pattern_verified_at = <timestamp>
   
✅ Audit record exists with:
   • company_id
   • canonical_verified_email
   • verified_pattern
   • verification_method
   • timestamp
   
✅ Agent exits cleanly
```

### Net Effect

| State | Meaning | Downstream Behavior |
|-------|---------|---------------------|
| **GUESS** | Pattern inferred, not proven | People emails may bounce, verify each |
| **FACT** | Pattern backed by verified email | People emails trusted, skip verification |

**This is the line that keeps Outreach sane.**

---

## Agent Sequence Summary

The complete verification flow involves three agents in sequence:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     VERIFICATION AGENT CHAIN                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  AGENT 1: People → CT Promotion                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ TRIGGER: Person email verified by MillionVerifier                   │    │
│  │ ACTION:  Promote email + derive pattern to Company Target           │    │
│  │ OUTPUT:  canonical_verified_email, derived_email_pattern            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│  AGENT 2: Verification Gate (STATE FLIP)                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ TRIGGER: CT has canonical_verified_email + derived_email_pattern    │    │
│  │ ACTION:  Validate consistency, flip status, lock pattern            │    │
│  │ OUTPUT:  email_pattern_status = VERIFIED, pattern_locked = true     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│  AGENT 3: Bounce Downgrade (FUTURE)                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ TRIGGER: Bounce detected in outreach.send_log                       │    │
│  │ ACTION:  Downgrade confidence, unlock pattern, allow re-derivation  │    │
│  │ OUTPUT:  pattern_confidence = LOW, pattern_locked = false           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  LOOP: If Agent 3 fires → Agent 1 can re-run with new verified email       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Agent Responsibilities

| Agent | Responsibility | Never Does |
|-------|---------------|------------|
| **Promotion Agent** | Move verified email upstream, derive pattern | Mark VERIFIED, lock pattern |
| **Verification Gate** | Validate + flip state + lock | Derive patterns, verify emails |
| **Bounce Downgrade** | Unlock + downgrade confidence | Re-verify, promote new email |

### Why Three Separate Agents?

1. **Single Responsibility** — Each agent does exactly one thing
2. **Audit Trail** — Clear separation of who changed what
3. **Failure Isolation** — One failure doesn't corrupt the chain
4. **Testability** — Each agent can be tested independently

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

### Q: How does Blog enrichment feed into People slots?

**A**: Blog extracts URLs from `company.company_source_urls` (especially `leadership_page` and `team_page` types), scrapes executive information, and writes discovered people to `people.people_master`. The People hub then assigns them to slots in `people.company_slot` via `outreach_id`. Finally, CT's email pattern is used to generate emails for each person.

### Q: Why is there a domain bridge instead of a direct join?

**A**: The `company.company_source_urls` table uses `company_unique_id` in `04.04.01.xx` format (from company schema), while `outreach.outreach` uses UUID-format `outreach_id`. These IDs don't match directly. The bridge goes: `outreach.outreach.domain` → `company.company_master.website_url` → `company.company_source_urls.company_unique_id`. This covers 47.6% of outreach companies.

### Q: What is the Verified Email → CT Promotion flow?

**A**: When People verifies one email (via MillionVerifier), that **verified fact** is promoted upstream to Company Target. The email pattern is derived mechanically (e.g., `jane.doe@acme.com` → `first.last@domain`) and locked as HIGH confidence. This makes all future People emails for that company deterministic—no more guessing.

### Q: Why promote verified emails upstream instead of just using them downstream?

**A**: Because one verified email proves the email pattern for the entire company. Instead of verifying 3 emails (CEO, CFO, HR) at \$0.01 each, we verify 1 and derive the pattern. All future slots use that pattern for \$0.00. This is the **hinge** that makes Outreach cheap.

### Q: What's the difference between GUESS and FACT patterns?

**A**: A **GUESS** pattern is inferred from heuristics (Hunter, domain analysis) and may be wrong. A **FACT** pattern is derived from a verified email—it's proven. The Verification Gate agent flips the state from GUESS to FACT only when backed by a real verified email. This is the line that keeps Outreach honest.

### Q: Why are there three separate agents for verification?

**A**: Single responsibility. The **Promotion Agent** moves data upstream. The **Verification Gate** flips state and locks. The **Bounce Downgrade Agent** unlocks on failure. Each does exactly one thing, creating a clear audit trail and isolating failures. If one breaks, the others still work.

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
        └──────┬──────┘ └─────────────┘ └──────┬──────┘
               │                               │
               │    ┌──────────────────────────┘
               │    │  (leadership/team pages)
               ▼    ▼
        ┌─────────────────┐
        │     PEOPLE      │
        │                 │
        │ CEO Slot ◄──────── leadership_page
        │ CFO Slot ◄──────── leadership_page  
        │ HR Slot  ◄──────── team_page
        │                 │
        │ Email = CT pattern
        └──────┬──────────┘
               │
               ▼
        ┌─────────────────────┐
        │   CAMPAIGN READY    │
        │   (Fully Actionable)│
        └─────────────────────┘
```

### Reverse Flow: Verified Email Promotion

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     REVERSE FLOW: PEOPLE → CT                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   NORMAL WATERFALL (forward):                                               │
│                                                                             │
│   CL → CT (email pattern) → People (generate email) → Verify               │
│                                                                             │
│   REVERSE PROMOTION (after verification):                                   │
│                                                                             │
│   People (VERIFIED email) ──────────────────────────────► CT                │
│         │                                                    │              │
│         │  jane.doe@acme.com                                 │              │
│         │  (verified by MillionVerifier)                     │              │
│         │                                                    ▼              │
│         │                                         ┌──────────────────┐      │
│         │                                         │ canonical_email  │      │
│         │                                         │ derived_pattern  │      │
│         │                                         │ confidence=HIGH  │      │
│         │                                         └────────┬─────────┘      │
│         │                                                  │                │
│         │◄─────────────────────────────────────────────────┘                │
│         │  (locked pattern feeds future People slots)                       │
│         ▼                                                                   │
│   CEO Slot → email from HIGH-confidence pattern                             │
│   CFO Slot → email from HIGH-confidence pattern                             │
│   HR Slot  → email from HIGH-confidence pattern                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Insight**: One verified email makes all future emails for that company **deterministic and cheap**.

### Blog → People Data Flow Detail

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        BLOG → PEOPLE ENRICHMENT                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  STEP 1: Get URLs via Bridge                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ outreach.outreach → company.company_master → company.source_urls   │  │
│  │              (domain)        (website_url)      (company_unique_id) │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                      │
│                                    ▼                                      │
│  STEP 2: Filter by source_type                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ leadership_page (9,214) → CEO, CFO discovery                        │  │
│  │ team_page (7,959)       → HR/Benefits discovery                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                      │
│                                    ▼                                      │
│  STEP 3: Scrape & Extract                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ - Extract names, titles from page content                           │  │
│  │ - Match to LinkedIn profiles                                        │  │
│  │ - Validate role (CEO/CFO/HR)                                        │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                      │
│                                    ▼                                      │
│  STEP 4: Write to People Tables                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ people.people_master → person record (unique_id)                    │  │
│  │ people.company_slot  → slot assignment (outreach_id + slot_type)    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                      │
│                                    ▼                                      │
│  STEP 5: Generate Email                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ Use CT email_method pattern: {first}.{last}@domain.com              │  │
│  │ Write to people.people_master.email                                 │  │
│  │ Verify via MillionVerifier (gated)                                  │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
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
