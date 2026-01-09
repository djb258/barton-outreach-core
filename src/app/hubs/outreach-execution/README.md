# Outreach Execution Hub

## Authoritative Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        COMPANY LIFECYCLE (CL)                                │
│                            PARENT HUB                                        │
│                                                                             │
│   Sovereign owner of:                                                       │
│   • company_unique_id (THE identity)                                       │
│   • Lifecycle state (prospect → sales → client → churned)                  │
│   • Promotion authority                                                     │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     │ company_unique_id (READ-ONLY)
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           OUTREACH EXECUTION                                 │
│                             CHILD HUB                                        │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      COMPANY TARGET                                  │   │
│   │                    (Formerly "Company")                              │   │
│   │                                                                     │   │
│   │   • Receives company_unique_id from CL                              │   │
│   │   • Internal anchor for all Outreach sub-hubs                       │   │
│   │   • May generate local target_id                                    │   │
│   │   • Manages targeting context, NOT identity                         │   │
│   └────────────────────────────┬────────────────────────────────────────┘   │
│                                │                                            │
│         ┌──────────────────────┼──────────────────────┐                     │
│         │                      │                      │                     │
│         ▼                      ▼                      ▼                     │
│   ┌───────────┐          ┌───────────┐          ┌───────────┐              │
│   │  PEOPLE   │          │    DOL    │          │   BLOG    │              │
│   │           │          │           │          │ / Content │              │
│   │ Attaches  │          │ Attaches  │          │ Attaches  │              │
│   │ to Target │          │ to Target │          │ to Target │              │
│   └───────────┘          └───────────┘          └───────────┘              │
│                                                                             │
│   ⚠️  NO sub-hub may attach directly to CL                                  │
│   ⚠️  All sub-hubs route through Company Target                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Nomenclature Change

| Old Name | New Name | Rationale |
|----------|----------|-----------|
| Company | **Company Target** | Outreach works on TARGETS, not sovereign companies |

**Why "Company Target"?**

- CL owns "Companies" (sovereign identity)
- Outreach works on "Targets" (campaign context)
- A Target references a Company but does not own it
- This distinction prevents identity confusion

---

## Four Internal Sub-Hubs

Outreach Execution contains exactly **four** internal sub-hubs:

| # | Sub-Hub | Purpose | Attaches To |
|---|---------|---------|-------------|
| 1 | **Company Target** | Internal anchor, targeting context | CL (via company_unique_id) |
| 2 | **People** | Contact records, slot assignments | Company Target |
| 3 | **DOL** | Filing data, renewal signals | Company Target |
| 4 | **Blog / Content** | News signals, content engagement | Company Target |

### Sub-Hub Hierarchy

```
CL (Parent)
   │
   └─► Outreach (Child Hub)
          │
          └─► Company Target (Internal Anchor)
                 ├─► People
                 ├─► DOL
                 └─► Blog / Content
```

**Critical Rule**: No sub-hub may attach directly to CL. All must route through Company Target.

---

## Company Target Specification

### What Company Target IS

| Responsibility | Description |
|----------------|-------------|
| **Targeting Context** | Outreach-specific company context (queued, active, exhausted) |
| **Enrichment Coordination** | Coordinating enrichment across People, DOL, Blog |
| **Sub-Hub Linking** | Connecting People, DOL, Blog records to a target |
| **Local Target ID** | May generate `target_id` for internal Outreach use |
| **BIT Score Consumption** | Receives and uses BIT scores from CL |

### What Company Target IS NOT

| Non-Responsibility | Owner | Why Not Company Target |
|--------------------|-------|------------------------|
| **Lifecycle State** | CL | prospect/sales/client is CL's decision |
| **Sales Readiness** | CL | Outreach informs, CL decides |
| **Client Eligibility** | CL | Promotion authority is CL's |
| **Identity Resolution** | CL | company_unique_id is CL's to mint |
| **Identity Merge/Retire** | CL | Deduplication is CL's domain |

---

## Identity & Authority Rules

### 1. company_unique_id Flows from CL

```
CL (mints) ──► company_unique_id ──► Company Target (receives)
```

- CL **mints** company_unique_id
- Company Target **receives** company_unique_id
- Company Target **NEVER** mints, infers, merges, or retires identity

### 2. Zero Promotion Authority

| Action | Outreach Authority |
|--------|-------------------|
| Move company to Sales | ❌ NO |
| Move company to Client | ❌ NO |
| Mark company as Churned | ❌ NO |
| Change lifecycle state | ❌ NO |

**Outreach has ZERO promotion authority. It can only signal; CL decides.**

### 3. Local Target Identifier

Company Target MAY generate a local `target_id`:

```python
# Allowed: Local target ID for Outreach-internal use
target_id = f"TGT-{company_unique_id[:8]}-{sequence_num}"
```

But this ID:
- Has no meaning outside Outreach
- Does not replace company_unique_id
- Must always trace back to company_unique_id

---

## Sub-Hub Attachment Rules

### People Sub-Hub

```sql
-- People records MUST attach to Company Target
CREATE TABLE outreach.people (
    person_id TEXT PRIMARY KEY,
    target_id TEXT NOT NULL,              -- Links to Company Target
    company_unique_id TEXT NOT NULL,      -- CL identity (via Target)
    ...
);
```

### DOL Sub-Hub

```sql
-- DOL records MUST attach to Company Target
CREATE TABLE outreach.dol_filings (
    filing_id TEXT PRIMARY KEY,
    target_id TEXT NOT NULL,              -- Links to Company Target
    company_unique_id TEXT NOT NULL,      -- CL identity (via Target)
    ...
);
```

### Blog / Content Sub-Hub

```sql
-- Blog records MUST attach to Company Target
CREATE TABLE outreach.blog_signals (
    signal_id TEXT PRIMARY KEY,
    target_id TEXT NOT NULL,              -- Links to Company Target
    company_unique_id TEXT NOT NULL,      -- CL identity (via Target)
    ...
);
```

**No sub-hub may attach directly to CL. All must route through Company Target.**

---

## Outreach-Specific Status

Company Target owns outreach-specific status (not lifecycle state):

| Status | Meaning | CL Equivalent |
|--------|---------|---------------|
| `queued` | In outreach queue | N/A (Outreach-only) |
| `active` | Currently being targeted | N/A (Outreach-only) |
| `exhausted` | All sequences completed | N/A (Outreach-only) |
| `paused` | Temporarily held | N/A (Outreach-only) |
| `opted_out` | Contact requested stop | N/A (Outreach-only) |

**These are Outreach states, not lifecycle states. CL does not see these.**

---

## Failure Modes

### Hard Failure Conditions

| Condition | Behavior |
|-----------|----------|
| `company_unique_id` is NULL | **HARD FAIL** - No target without CL identity |
| `company_unique_id` not in CL | **HARD FAIL** - Cannot fabricate identity |
| Sub-hub record missing target_id | **HARD FAIL** - Must attach to Company Target |
| Direct CL attachment attempted | **HARD FAIL** - Must route through Company Target |

### Prohibited Behaviors

| Behavior | Why Prohibited |
|----------|----------------|
| Silent fallback to default company | Creates shadow identity |
| Infer company from email domain | CL owns identity resolution |
| Create placeholder company | Shadow identity violation |
| Skip missing company_unique_id | Data integrity violation |

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                               DATA FLOW                                      │
└─────────────────────────────────────────────────────────────────────────────┘

    CL                           OUTREACH
    ──                           ────────
     │
     │ company_unique_id
     │ domain
     │ BIT score
     │
     ▼
┌─────────────────┐
│ Company Target  │◄──── Targeting context
│                 │◄──── Local target_id
│                 │◄──── Outreach status
└────────┬────────┘
         │
    ┌────┴────┬────────────┐
    │         │            │
    ▼         ▼            ▼
┌───────┐ ┌───────┐ ┌───────────┐
│People │ │  DOL  │ │Blog/Content│
│       │ │       │ │           │
│Contacts│ │Filings│ │ Signals  │
│Slots  │ │Renewals│ │ News    │
└───────┘ └───────┘ └───────────┘
    │         │            │
    └────┬────┴────────────┘
         │
         ▼
┌─────────────────┐
│   Campaigns     │
│   Sequences     │
│   Send Log      │
│   Engagement    │
└─────────────────┘
         │
         │ engagement_signal
         │
         ▼
    CL (receives signals, makes decisions)
```

---

## Schema Summary

| Table | Parent | company_unique_id | target_id |
|-------|--------|-------------------|-----------|
| company_target | CL | REQUIRED | GENERATED |
| people | Company Target | REQUIRED | REQUIRED |
| dol_filings | Company Target | REQUIRED | REQUIRED |
| blog_signals | Company Target | REQUIRED | REQUIRED |
| campaigns | Company Target | REQUIRED | OPTIONAL |
| send_log | Company Target | REQUIRED | REQUIRED |
| engagement_events | Company Target | REQUIRED | REQUIRED |

---

## Doctrine ID

**04.04.04** - Outreach Execution Hub

Internal sub-hub doctrine IDs:
- 04.04.04.01 - Company Target
- 04.04.04.02 - People (Outreach context)
- 04.04.04.03 - DOL (Outreach context)
- 04.04.04.04 - Blog / Content

---

*Last Updated: 2025-12-26*
*Doctrine Version: CL Parent-Child Model v1.1*
*Parent Hub: Company Lifecycle (CL)*
*Internal Sub-Hubs: Company Target, People, DOL, Blog/Content*
