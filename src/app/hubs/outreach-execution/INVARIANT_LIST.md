# Outreach Hub - Invariant List

## Overview

This document enumerates all **non-negotiable rules** (invariants) that the Outreach
Execution Hub must obey per the Company Lifecycle (CL) Parent-Child Doctrine.

**Doctrine Version**: CL Parent-Child Model v1.1
**Parent Hub**: Company Lifecycle (CL)
**Child Hub**: Outreach Execution

---

## Invariant Categories

| Category | Count | Severity |
|----------|-------|----------|
| Identity Invariants | 6 | CRITICAL |
| Authority Invariants | 5 | CRITICAL |
| Sub-Hub Invariants | 4 | CRITICAL |
| Join Invariants | 5 | HIGH |
| Failure Mode Invariants | 4 | CRITICAL |
| Data Contract Invariants | 4 | HIGH |
| **TOTAL** | **28** | - |

---

## 1. Identity Invariants

### INV-ID-001: CL Mints company_unique_id

```
INVARIANT: company_unique_id is minted ONLY by Company Lifecycle (CL)
SEVERITY:  CRITICAL
VIOLATION: Creating/generating company_unique_id in Outreach code
```

**Correct**:
```python
# Receive from CL via spoke
company_unique_id = data.get("company_unique_id")
```

**Violation**:
```python
# PROHIBITED: Generating ID in Outreach
company_unique_id = str(uuid.uuid4())  # VIOLATION!
```

---

### INV-ID-002: No Identity Inference

```
INVARIANT: Outreach NEVER infers company identity from domain, email, or name
SEVERITY:  CRITICAL
VIOLATION: Deriving company_unique_id from company_name or email domain
```

**Correct**:
```python
# Accept ID as provided by CL
company_id = record["company_unique_id"]
```

**Violation**:
```python
# PROHIBITED: Inferring from domain
domain = email.split("@")[1]
company_id = lookup_company_by_domain(domain)  # VIOLATION!
```

---

### INV-ID-003: No Shadow Identifiers

```
INVARIANT: Outreach NEVER creates alternate, placeholder, or temporary company IDs
SEVERITY:  CRITICAL
VIOLATION: Using local IDs as substitutes for company_unique_id
```

**Violation Examples**:
```python
company_id = "UNKNOWN"           # VIOLATION
company_id = "PENDING-" + seq    # VIOLATION
company_id = local_target_id     # VIOLATION (if used as company identity)
```

---

### INV-ID-004: target_id is Local Only

```
INVARIANT: target_id has no meaning outside Outreach Hub
SEVERITY:  HIGH
VIOLATION: Exposing target_id to other hubs or using it as company identity
```

**Correct**:
```python
# target_id for Outreach-internal use only
target_id = f"TGT-{company_unique_id[:8]}-{seq}"

# Always include company_unique_id for external communication
egress_payload = {
    "company_unique_id": company_unique_id,  # Required
    "target_id": target_id                    # Optional, internal
}
```

---

### INV-ID-005: company_unique_id is Immutable

```
INVARIANT: Outreach NEVER modifies, transforms, or replaces company_unique_id
SEVERITY:  CRITICAL
VIOLATION: Altering the ID after receipt from CL
```

**Violation**:
```python
# PROHIBITED: Transforming the ID
company_id = company_unique_id.upper()     # VIOLATION
company_id = "OUT-" + company_unique_id    # VIOLATION
```

---

### INV-ID-006: Single Source of Truth

```
INVARIANT: CL is the single source of truth for company existence
SEVERITY:  CRITICAL
VIOLATION: Storing company metadata that contradicts CL
```

**Correct**:
```python
# Query CL for company data
company_data = get_company_from_cl(company_unique_id)
```

**Violation**:
```python
# PROHIBITED: Local company storage
outreach_companies = {"ACME": {"id": "local-123"}}  # VIOLATION
```

---

## 2. Authority Invariants

### INV-AUTH-001: Zero Promotion Authority

```
INVARIANT: Outreach CANNOT promote companies through lifecycle states
SEVERITY:  CRITICAL
VIOLATION: Changing lifecycle_state (prospect/sales/client/churned)
```

**Prohibited Actions**:
| Action | Authority |
|--------|-----------|
| Move to Prospect | ❌ NO |
| Move to Sales | ❌ NO |
| Move to Client | ❌ NO |
| Mark as Churned | ❌ NO |
| Any lifecycle transition | ❌ NO |

---

### INV-AUTH-002: Signal Only

```
INVARIANT: Outreach can only SIGNAL intent; CL DECIDES on state changes
SEVERITY:  CRITICAL
VIOLATION: Making lifecycle decisions without CL approval
```

**Correct**:
```python
# Send engagement signal to CL
signal = {
    "company_unique_id": company_id,
    "signal_type": "high_engagement",
    "engagement_score": 0.85
}
send_to_cl_spoke(signal)  # CL decides what to do
```

**Violation**:
```python
# PROHIBITED: Making the decision ourselves
update_company_status(company_id, "sales_ready")  # VIOLATION
```

---

### INV-AUTH-003: No Client Eligibility Decisions

```
INVARIANT: Outreach CANNOT determine if a company is eligible to be a client
SEVERITY:  CRITICAL
VIOLATION: Setting client_eligible flags or similar
```

---

### INV-AUTH-004: No Sales Readiness Decisions

```
INVARIANT: Outreach CANNOT determine if a company is sales-ready
SEVERITY:  CRITICAL
VIOLATION: Setting sales_ready flags or triggering sales handoff
```

---

### INV-AUTH-005: Read-Only Lifecycle Access

```
INVARIANT: Outreach can READ lifecycle_state but NEVER WRITE it
SEVERITY:  CRITICAL
VIOLATION: Any UPDATE to lifecycle_state
```

**Correct**:
```sql
-- READ is allowed
SELECT lifecycle_state FROM marketing.company_master
WHERE company_unique_id = $1;
```

**Violation**:
```sql
-- WRITE is prohibited
UPDATE marketing.company_master
SET lifecycle_state = 'sales'  -- VIOLATION!
WHERE company_unique_id = $1;
```

---

## 3. Sub-Hub Invariants

### INV-SUB-001: Four Sub-Hubs Only

```
INVARIANT: Outreach contains exactly 4 internal sub-hubs
SEVERITY:  HIGH
VIOLATION: Adding/removing sub-hubs without doctrine update
```

| # | Sub-Hub | Purpose |
|---|---------|---------|
| 1 | Company Target | Internal anchor, CL join point |
| 2 | People | Contacts, slot assignments |
| 3 | DOL | Filing data, renewal signals |
| 4 | Blog / Content | News signals, content engagement |

---

### INV-SUB-002: Sub-Hubs Attach to Company Target

```
INVARIANT: People, DOL, Blog MUST attach to Company Target, NOT to CL
SEVERITY:  CRITICAL
VIOLATION: Direct FK from sub-hub table to CL
```

**Correct**:
```sql
-- People attaches to Company Target
CREATE TABLE outreach.people (
    target_id TEXT REFERENCES outreach.company_target(target_id)  -- Correct
);
```

**Violation**:
```sql
-- PROHIBITED: Direct CL attachment
CREATE TABLE outreach.people (
    company_unique_id TEXT REFERENCES marketing.company_master(company_unique_id)  -- VIOLATION
);
```

---

### INV-SUB-003: Company Target is Sole CL Join Point

```
INVARIANT: Only Company Target may join directly to CL
SEVERITY:  CRITICAL
VIOLATION: Any other Outreach table joining directly to marketing.company_master
```

**The ONLY allowed direct join**:
```sql
SELECT * FROM outreach.company_target ct
INNER JOIN marketing.company_master cm  -- ALLOWED (Company Target only)
    ON ct.company_unique_id = cm.company_unique_id;
```

---

### INV-SUB-004: Cascade Through Company Target

```
INVARIANT: Sub-hub records cascade delete through Company Target
SEVERITY:  HIGH
VIOLATION: Sub-hub records orphaned when target deleted
```

**Required constraint**:
```sql
CONSTRAINT fk_target
    FOREIGN KEY (target_id)
    REFERENCES outreach.company_target(target_id)
    ON DELETE CASCADE  -- Required
```

---

## 4. Join Invariants

### INV-JOIN-001: Full Chain Required

```
INVARIANT: Queries from sub-hub to CL must chain through Company Target
SEVERITY:  HIGH
VIOLATION: Skipping Company Target in join chain
```

**Correct**:
```sql
-- Full chain: People → Company Target → CL
SELECT p.*, cm.company_name
FROM outreach.people p
INNER JOIN outreach.company_target ct ON p.target_id = ct.target_id
INNER JOIN marketing.company_master cm ON ct.company_unique_id = cm.company_unique_id;
```

**Violation**:
```sql
-- PROHIBITED: Skipping Company Target
SELECT p.*, cm.company_name
FROM outreach.people p
INNER JOIN marketing.company_master cm ON p.company_unique_id = cm.company_unique_id;
```

---

### INV-JOIN-002: target_id Required for Sub-Hubs

```
INVARIANT: People, DOL, Blog records MUST have target_id
SEVERITY:  CRITICAL
VIOLATION: NULL target_id in sub-hub table
```

**Required**:
```sql
target_id TEXT NOT NULL  -- Required for all sub-hub tables
```

---

### INV-JOIN-003: Denormalized company_unique_id Must Match

```
INVARIANT: If sub-hub stores company_unique_id, it MUST match target's
SEVERITY:  HIGH
VIOLATION: Mismatch between sub-hub.company_unique_id and target.company_unique_id
```

**Integrity check**:
```sql
-- Must return 0 rows
SELECT p.person_id
FROM outreach.people p
INNER JOIN outreach.company_target ct ON p.target_id = ct.target_id
WHERE p.company_unique_id != ct.company_unique_id;
```

---

### INV-JOIN-004: One Target Per Company

```
INVARIANT: Only one Company Target record per company_unique_id
SEVERITY:  HIGH
VIOLATION: Multiple targets for same company
```

**Required**:
```sql
CREATE UNIQUE INDEX idx_target_company
ON outreach.company_target(company_unique_id);
```

---

### INV-JOIN-005: No Cross-Hub Direct Access

```
INVARIANT: Outreach sub-hubs cannot directly access other hubs
SEVERITY:  HIGH
VIOLATION: Direct queries to People Hub, DOL Hub, etc.
```

**Correct**:
```python
# Access via spoke contract
people_data = receive_from_people_spoke(company_unique_id)
```

**Violation**:
```python
# PROHIBITED: Direct hub access
people_data = query_people_hub_directly(company_unique_id)  # VIOLATION
```

---

## 5. Failure Mode Invariants

### INV-FAIL-001: Hard Fail on NULL company_unique_id

```
INVARIANT: Processing MUST STOP if company_unique_id is NULL
SEVERITY:  CRITICAL
VIOLATION: Continuing processing with NULL ID
```

**Required**:
```python
def process(data):
    company_id = data.get("company_unique_id")
    if not company_id:
        return {"status": "HARD_FAIL", "reason": "Missing company_unique_id"}
    # Continue only if ID present
```

---

### INV-FAIL-002: Hard Fail on Invalid company_unique_id

```
INVARIANT: Processing MUST STOP if company_unique_id not found in CL
SEVERITY:  CRITICAL
VIOLATION: Creating records for non-existent company
```

**Required**:
```python
def validate_company(company_id):
    exists = check_company_in_cl(company_id)
    if not exists:
        return {"status": "HARD_FAIL", "reason": "Company not found in CL"}
```

---

### INV-FAIL-003: No Silent Fallbacks

```
INVARIANT: Outreach NEVER silently substitutes a default/placeholder company
SEVERITY:  CRITICAL
VIOLATION: Using "UNKNOWN" or similar when company_unique_id missing
```

**Prohibited patterns**:
```python
# All VIOLATIONS:
company_id = company_id or "UNKNOWN"
company_id = company_id or generate_placeholder()
company_id = company_id or DEFAULT_COMPANY_ID
```

---

### INV-FAIL-004: No Skip-and-Continue

```
INVARIANT: Outreach NEVER skips records with missing company_unique_id
SEVERITY:  CRITICAL
VIOLATION: Logging warning and proceeding without company anchor
```

**Violation**:
```python
# PROHIBITED: Skip and continue
for record in records:
    if not record.get("company_unique_id"):
        logger.warning("Missing company ID, skipping")  # VIOLATION
        continue
    process(record)
```

**Correct**:
```python
# Required: Hard fail
for record in records:
    if not record.get("company_unique_id"):
        raise ValueError("Missing company_unique_id - HARD FAIL")
    process(record)
```

---

## 6. Data Contract Invariants

### INV-DATA-001: company_unique_id NOT NULL

```
INVARIANT: company_unique_id column MUST be NOT NULL in all Outreach tables
SEVERITY:  CRITICAL
VIOLATION: Nullable company_unique_id column
```

**Required**:
```sql
company_unique_id TEXT NOT NULL
```

---

### INV-DATA-002: FK to CL Required for Company Target

```
INVARIANT: Company Target MUST have FK constraint to CL
SEVERITY:  CRITICAL
VIOLATION: Missing FK constraint to marketing.company_master
```

**Required**:
```sql
CONSTRAINT fk_company_lifecycle
    FOREIGN KEY (company_unique_id)
    REFERENCES marketing.company_master(company_unique_id)
    ON DELETE RESTRICT
```

---

### INV-DATA-003: FK to Company Target Required for Sub-Hubs

```
INVARIANT: People, DOL, Blog MUST have FK constraint to Company Target
SEVERITY:  CRITICAL
VIOLATION: Missing FK constraint to outreach.company_target
```

**Required**:
```sql
CONSTRAINT fk_target
    FOREIGN KEY (target_id)
    REFERENCES outreach.company_target(target_id)
    ON DELETE CASCADE
```

---

### INV-DATA-004: Local IDs Are Outreach-Only

```
INVARIANT: target_id, campaign_id, sequence_id have no meaning outside Outreach
SEVERITY:  HIGH
VIOLATION: Exposing local IDs as cross-hub identifiers
```

**Local IDs** (Outreach-only):
- `target_id`
- `campaign_id`
- `sequence_id`
- `message_id`
- `engagement_id`

**Cross-Hub ID** (from CL):
- `company_unique_id`

---

## Enforcement Matrix

| Invariant | Enforced By | Enforcement Method |
|-----------|-------------|-------------------|
| INV-ID-001 | Code Review | No uuid.uuid4() for company |
| INV-ID-002 | Code Review | No domain/email parsing |
| INV-ID-003 | Code Review | No placeholder patterns |
| INV-ID-004 | Schema | target_id not in spoke contracts |
| INV-ID-005 | Code Review | ID passed through unchanged |
| INV-ID-006 | Architecture | No local company tables |
| INV-AUTH-001 | Code Review | No lifecycle mutations |
| INV-AUTH-002 | Architecture | Signals via spoke only |
| INV-AUTH-003 | Code Review | No eligibility flags |
| INV-AUTH-004 | Code Review | No readiness flags |
| INV-AUTH-005 | Schema + RLS | No UPDATE grants on CL |
| INV-SUB-001 | Manifest | hub.manifest.yaml |
| INV-SUB-002 | Schema | FK constraints |
| INV-SUB-003 | Schema | Only company_target joins CL |
| INV-SUB-004 | Schema | ON DELETE CASCADE |
| INV-JOIN-001 | Code Review | Query patterns |
| INV-JOIN-002 | Schema | NOT NULL constraint |
| INV-JOIN-003 | Trigger/Check | Integrity check query |
| INV-JOIN-004 | Schema | UNIQUE INDEX |
| INV-JOIN-005 | Architecture | Spoke contracts |
| INV-FAIL-001 | Code | Validation check |
| INV-FAIL-002 | Code | CL existence check |
| INV-FAIL-003 | Code Review | No default substitution |
| INV-FAIL-004 | Code | Exception on missing ID |
| INV-DATA-001 | Schema | NOT NULL |
| INV-DATA-002 | Schema | FK CONSTRAINT |
| INV-DATA-003 | Schema | FK CONSTRAINT |
| INV-DATA-004 | Manifest | Local ID declarations |

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        OUTREACH INVARIANTS - QUICK REFERENCE                │
└─────────────────────────────────────────────────────────────────────────────┘

IDENTITY (6 rules):
  ✗ Do NOT mint company_unique_id
  ✗ Do NOT infer from domain/email/name
  ✗ Do NOT create shadow IDs
  ✗ Do NOT modify company_unique_id
  ✓ Do receive company_unique_id from CL only
  ✓ Do treat CL as single source of truth

AUTHORITY (5 rules):
  ✗ Do NOT change lifecycle_state
  ✗ Do NOT promote to Sales/Client
  ✗ Do NOT decide eligibility/readiness
  ✓ Do signal engagement to CL
  ✓ Do let CL make all decisions

SUB-HUBS (4 rules):
  ✓ Exactly 4 sub-hubs: Company Target, People, DOL, Blog
  ✓ Sub-hubs attach to Company Target only
  ✓ Only Company Target joins to CL
  ✓ Cascade deletes through Company Target

JOINS (5 rules):
  ✓ Full chain: Sub-hub → Company Target → CL
  ✓ target_id required for sub-hubs
  ✓ company_unique_id must match via target
  ✓ One target per company
  ✗ Do NOT access other hubs directly

FAILURES (4 rules):
  ✓ HARD FAIL on NULL company_unique_id
  ✓ HARD FAIL on invalid company_unique_id
  ✗ Do NOT use silent fallbacks
  ✗ Do NOT skip-and-continue

DATA (4 rules):
  ✓ company_unique_id NOT NULL always
  ✓ FK to CL on company_target
  ✓ FK to company_target on sub-hubs
  ✓ Local IDs stay local
```

---

*Last Updated: 2025-12-26*
*Doctrine Version: CL Parent-Child Model v1.1*
*Total Invariants: 28*
