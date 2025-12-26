# CL Admission Gate Doctrine

**Doctrine Version**: 1.0
**Status**: LOCKED
**Authority**: Company Lifecycle (CL) — Sovereign Identity Hub

---

## Foundational Principle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                    IDs ARE EARNED, NOT ASSIGNED.                            │
│                                                                             │
│   CL identities are minted only after admission gating.                     │
│   Junk targets never receive a CL ID.                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Doctrine Summary

| Concept | Definition |
|---------|------------|
| **Company Target** | A candidate record in Outreach. Not an identity. Discardable. |
| **CL Identity** | A sovereign, minted `company_unique_id`. Permanent. Authoritative. |
| **Admission** | The act of evaluating a candidate and minting an identity. |
| **Rejection** | The act of denying admission. Terminal. No ID minted. |

---

## Core Doctrine (Non-Negotiable)

### 1. CL Does Not See Candidates. CL Admits Identities.

CL has no awareness of "targets" or "candidates."

CL receives **admission requests** and returns one of two outcomes:
- **ADMIT** — Mint `company_unique_id`, record identity
- **REJECT** — No ID, no state, no record in CL

There is no third option. There is no "pending." There is no "maybe later."

### 2. A Company Target Must Explicitly Qualify

No automatic promotion. No implicit admission.

A Company Target becomes a CL Identity **only** when:
1. Outreach submits an admission request
2. CL evaluates admission criteria
3. Criteria are met
4. CL mints identity

If any step fails, **no identity exists**.

---

## Admission Rule (Hard Gate)

### Minimum Identity Criteria

CL may mint a `company_unique_id` **only if** the Company Target provides at least **ONE** of the following:

| Criterion | Description | Example |
|-----------|-------------|---------|
| **Canonical Domain** | Verified company website domain | `acme.com` |
| **Website URL** | Full URL to company website | `https://www.acme.com` |
| **LinkedIn Company URL** | Verified LinkedIn company page | `linkedin.com/company/acme` |

### The Name-Only Rule (Absolute)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│           NAME-ONLY RECORDS ARE NEVER SUFFICIENT FOR ADMISSION.             │
│                                                                             │
│   A company name without domain or LinkedIn URL is NOT an identity.         │
│   It is noise. It stays in Outreach. It never enters CL.                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Admission Decision Table

| Has Domain? | Has LinkedIn? | Has Name Only? | Decision |
|-------------|---------------|----------------|----------|
| Yes | Yes | - | **ADMIT** |
| Yes | No | - | **ADMIT** |
| No | Yes | - | **ADMIT** |
| No | No | Yes | **REJECT** |
| No | No | No | **REJECT** |

---

## Rejection Rule

### What Happens on Rejection

When a Company Target **fails** admission criteria:

| Action | Status |
|--------|--------|
| CL identity minted | **NO** |
| Lifecycle state created | **NO** |
| Downstream hubs may attach | **NO** |
| Record remains in Outreach | **YES** |
| Record is discardable | **YES** |

### Rejection Is Terminal

Rejection is not a "try again later" state.

A rejected target:
- Has no CL presence
- Has no `company_unique_id`
- Cannot be referenced by People, DOL, or Outreach Execution hubs
- May be deleted, archived, or ignored by Outreach

### Rejected Targets Must Not Pollute CL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                JUNK DATA MUST DIE IN OUTREACH, NOT CL.                      │
│                                                                             │
│   CL is not a graveyard. CL is not a staging area.                         │
│   CL contains only admitted, sovereign identities.                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## What Is Allowed to Enter CL

### Identity-Grade Attributes Only

Upon successful admission, CL may record **only** the following:

| Attribute | Description | Required? |
|-----------|-------------|-----------|
| `company_unique_id` | CL-minted sovereign ID | Yes (generated) |
| `normalized_company_name` | Cleaned, standardized name | Yes |
| `canonical_domain` | Primary company domain | If available |
| `website_url` | Full company website URL | If available |
| `linkedin_url` | LinkedIn company page URL | If available |
| `source_system` | Origin of admission request | Yes |
| `admitted_at` | Timestamp of admission | Yes (generated) |
| `admission_criteria_met` | Which criterion qualified | Yes |

### What CL Must NEVER Ingest

| Forbidden Data | Reason |
|----------------|--------|
| Campaign data | Belongs to Outreach Execution |
| People data | Belongs to People Intelligence |
| DOL filings | Belongs to DOL Filings Hub |
| Enrichment artifacts | Ephemeral, not identity |
| Confidence scores | Uncertainty is not truth |
| BIT scores | Belongs to Company Target |
| Email patterns | Belongs to People Intelligence |
| Employee counts | Enrichment, not identity |
| Revenue data | Enrichment, not identity |
| Industry codes | Enrichment, not identity |

### The Enrichment Rule

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│            CL RECORDS IDENTITY. CL DOES NOT STORE ENRICHMENT.              │
│                                                                             │
│   Enrichment data lives in child hubs.                                     │
│   CL knows WHO a company is, not WHAT a company does.                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Separation of Responsibility

### Outreach Responsibility

Outreach (Company Target sub-hub) is responsible for:

| Task | Description |
|------|-------------|
| Receive raw inputs | From Clay, CSV, API, etc. |
| Clean data | Normalize, dedupe, validate |
| Enrich data | Add domain, LinkedIn, etc. |
| Evaluate readiness | Check if admission criteria can be met |
| Submit admission request | Send qualified candidates to CL |
| Handle rejections | Archive, delete, or retry enrichment |

Outreach is the **sandbox**. Garbage lives here. Experiments happen here.

### CL Responsibility

CL is responsible for:

| Task | Description |
|------|-------------|
| Receive admission request | From Outreach only |
| Evaluate admission criteria | Domain OR LinkedIn present? |
| Decide | ADMIT or REJECT |
| Mint identity (if admitted) | Generate `company_unique_id` |
| Record admission | Log the event with timestamp |
| Record rejection | Log the denial with reason |

CL performs **no cleanup, no enrichment, no remediation**.

### The Separation Rule

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   OUTREACH: Cleans, enriches, evaluates, submits                           │
│   CL: Evaluates, admits or rejects, records                                │
│                                                                             │
│   If data is insufficient, CL REJECTS. CL does not repair.                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Invariants (Absolute Rules)

The following invariants MUST always be true:

### INV-ADM-001: CL Identity Is Scarce and Intentional

```yaml
invariant: CL-ADM-001
rule: "CL identity is scarce and intentional"
meaning: |
  Every company_unique_id represents a verified, qualified entity.
  CL does not mint IDs speculatively or optimistically.
  Scarcity ensures trust.
enforcement: Admission gate rejects unqualified candidates
```

### INV-ADM-002: Junk Data Dies in Outreach

```yaml
invariant: CL-ADM-002
rule: "Junk data must die in Outreach, not CL"
meaning: |
  Clay imports, CSV noise, and unqualified records never reach CL.
  Outreach is the firewall. CL is the vault.
enforcement: Admission gate rejects name-only records
```

### INV-ADM-003: No Name-Only Identities

```yaml
invariant: CL-ADM-003
rule: "CL never mints identity from name-only records"
meaning: |
  A company name without domain or LinkedIn is not an identity.
  Names are ambiguous. Domains and LinkedIn URLs are canonical.
enforcement: Admission gate requires domain OR LinkedIn
```

### INV-ADM-004: Admission Decisions Are Auditable

```yaml
invariant: CL-ADM-004
rule: "Admission decisions are auditable"
meaning: |
  Every ADMIT and REJECT is logged with timestamp, criteria, and outcome.
  No silent admissions. No invisible rejections.
enforcement: CL records all admission events
```

### INV-ADM-005: Rejection Is Terminal

```yaml
invariant: CL-ADM-005
rule: "Rejection is a valid, terminal outcome"
meaning: |
  A rejected candidate has no CL presence.
  Rejection is not failure. Rejection is protection.
  CL quality depends on saying NO.
enforcement: Rejected targets cannot reference CL schema
```

---

## Absolute Prohibitions

The following are **FORBIDDEN** in the admission process:

### No Fuzzy Matching

```
PROHIBITED: Using fuzzy string matching to "find" an existing CL identity
REASON: CL is the source of identity, not a search index
CORRECT: Exact match on domain or LinkedIn URL only
```

### No Confidence-Based Auto-Admission

```
PROHIBITED: Admitting records based on confidence scores
REASON: Confidence is uncertainty. CL requires certainty.
CORRECT: Hard gate on domain OR LinkedIn presence
```

### No Remediation Logic Inside CL

```
PROHIBITED: CL attempting to "fix" or "clean" incoming data
REASON: CL evaluates, it does not transform
CORRECT: Outreach cleans data before submission
```

### No Temporary Identities

```
PROHIBITED: Creating "provisional" or "pending" CL identities
REASON: A company_unique_id is permanent and sovereign
CORRECT: ADMIT fully or REJECT fully. No middle state.
```

### No Execution Logic

```
PROHIBITED: CL containing workers, pipelines, or workflows
REASON: CL decides and records, it does not execute
CORRECT: All execution lives in child hubs
```

### The Repair Prohibition

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│          IF DATA IS INSUFFICIENT, CL REJECTS. CL DOES NOT REPAIR.          │
│                                                                             │
│   CL is not a hospital. CL is a courthouse.                                │
│   Bring qualified evidence or be denied.                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Admission Request Format

When Outreach submits an admission request to CL, it must include:

| Field | Required | Description |
|-------|----------|-------------|
| `company_name` | Yes | Normalized company name |
| `canonical_domain` | Conditional | Required if no LinkedIn |
| `linkedin_url` | Conditional | Required if no domain |
| `source_system` | Yes | Where the record originated |
| `outreach_target_id` | Yes | Reference back to Outreach |

### Admission Response Format

CL returns one of:

**On ADMIT:**
```yaml
decision: ADMIT
company_unique_id: "CL-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
admitted_at: "2025-12-26T12:00:00Z"
criteria_met: "canonical_domain"
```

**On REJECT:**
```yaml
decision: REJECT
reason: "name_only_insufficient"
rejected_at: "2025-12-26T12:00:00Z"
guidance: "Enrich with domain or LinkedIn before resubmission"
```

---

## Downstream Impact

### On Admission

When CL admits a Company Target:

| Hub | May Now... |
|-----|------------|
| Company Target | Reference `company_unique_id` as FK |
| People Intelligence | Attach people to company |
| DOL Filings | Match filings to company |
| Outreach Execution | Include company in campaigns |

### On Rejection

When CL rejects a Company Target:

| Hub | Status |
|-----|--------|
| Company Target | Record remains orphaned |
| People Intelligence | Cannot attach people |
| DOL Filings | Cannot match filings |
| Outreach Execution | Cannot include in campaigns |

The rejected target is **invisible** to the ecosystem.

---

## Validation Checklist

Before this doctrine is considered implemented, confirm:

- [ ] CL admission gate exists and enforces criteria
- [ ] Name-only records are rejected
- [ ] Domain OR LinkedIn is required for admission
- [ ] Rejection is logged with reason
- [ ] No fuzzy matching in admission logic
- [ ] No confidence-based admission
- [ ] No remediation logic in CL
- [ ] No temporary identities possible
- [ ] All admission events are auditable

---

## Doctrine Lock Statement

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   CONFIRMATION:                                                             │
│                                                                             │
│   "CL identities are minted only after admission gating.                   │
│    Junk targets never receive a CL ID."                                    │
│                                                                             │
│   This doctrine is LOCKED.                                                  │
│                                                                             │
│   CL cannot be polluted by Clay junk.                                      │
│   Company identities are trustworthy by construction.                       │
│   Outreach remains the sandbox.                                             │
│   CL remains the constitution.                                              │
│                                                                             │
│   IDs are earned, not assigned.                                             │
│                                                                             │
│   Locked By: Doctrine Enforcement Author                                    │
│   Locked On: 2025-12-26                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

**END OF ADMISSION GATE DOCTRINE**
