# CL Authority Registry Doctrine

**Status**: LOCAL EXTENSION
**Authority**: barton-outreach-core (extends IMO-Creator)
**Version**: 1.0.0
**Last Updated**: 2026-02-05

---

## Purpose

This doctrine defines the relationship between Company Lifecycle (CL) as the authority registry and downstream hubs. CL owns identity, downstream hubs own workflow.

---

## The Golden Rule

```
IF outreach_id IS NULL:
    STOP. DO NOT PROCEED.
    1. Mint outreach_id in outreach.outreach (operational spine)
    2. Write outreach_id ONCE to cl.company_identity (authority registry)
    3. If CL write fails (already claimed) → HARD FAIL
```

---

## CL Authority Registry Definition

CL is the **authority registry** for company identity. It stores identity pointers only.

| Column | Purpose | Write Pattern |
|--------|---------|---------------|
| `sovereign_company_id` | Primary identity (minted by CL) | IMMUTABLE |
| `outreach_id` | Pointer to Outreach hub | WRITE-ONCE by Outreach |
| `sales_process_id` | Pointer to Sales hub | WRITE-ONCE by Sales |
| `client_id` | Pointer to Client hub | WRITE-ONCE by Client |

### What CL Stores

- **Identity pointers ONLY** — `outreach_id`, `sales_process_id`, `client_id`
- **Lifecycle state** — which hubs have claimed this company
- **Canonical company data** — `sovereign_company_id`, `company_name`, `company_domain`

### What CL Does NOT Store

- Workflow state (belongs to each hub's operational spine)
- Enrichment data (belongs to downstream hubs)
- Campaign data (belongs to Outreach)
- Pipeline data (belongs to Sales)

---

## Write-Once Pattern

Each downstream hub:
1. **Mints** its own ID in its operational spine
2. **Registers** that ID in CL (WRITE-ONCE)
3. **Never** modifies CL after initial registration

```python
# CORRECT: Write-once pattern
UPDATE cl.company_identity
SET outreach_id = $new_outreach_id
WHERE sovereign_company_id = $sid
  AND outreach_id IS NULL;  # CRITICAL: Only if not already claimed

# MUST verify affected_rows == 1
if affected_rows != 1:
    HARD_FAIL("Outreach ID already claimed or invalid SID")
```

---

## Alignment Rule

```
outreach.outreach count = cl.company_identity (outreach_id NOT NULL) count
```

If these counts diverge:
- **Orphaned outreach_ids** → Archive and cleanup required
- **Missing registrations** → Registration failed, investigate

---

## Prohibited Actions

| Action | Reason |
|--------|--------|
| Mint `sovereign_company_id` | CL owns identity minting |
| Write workflow state to CL | CL stores pointers only |
| Modify `outreach_id` after write | WRITE-ONCE is immutable |
| Bypass affected_rows check | Race condition protection |
| Query CL for workflow decisions | CL is registry, not workflow |

---

## Hub Responsibilities

| Hub | Mints | Registers in CL |
|-----|-------|-----------------|
| **CL** | `sovereign_company_id` | N/A (owns the registry) |
| **Outreach** | `outreach_id` | `outreach_id` (ONCE) |
| **Sales** | `sales_process_id` | `sales_process_id` (ONCE) |
| **Client** | `client_id` | `client_id` (ONCE) |

---

## Enforcement

This doctrine is enforced by:
- `ops/enforcement/authority_gate.py` — CC layer validation
- `ops/enforcement/schema_guard.py` — Cross-hub isolation
- `src/sys/db/guarded_connection.py` — Query-level schema enforcement

---

## Traceability

| Document | Reference |
|----------|-----------|
| Parent Doctrine | CONSTITUTION.md |
| Domain Spec | doctrine/REPO_DOMAIN_SPEC.md |
| Operational Spine | doctrine/OUTREACH_SPINE_DOCTRINE.md |
| CLAUDE.md | §CL Authority Registry |

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-02-05 |
| Type | LOCAL EXTENSION |
| Status | ACTIVE |
| Change Protocol | ADR required |
