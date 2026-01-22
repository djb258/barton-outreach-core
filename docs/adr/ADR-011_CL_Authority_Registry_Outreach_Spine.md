# ADR-011: CL Authority Registry + Outreach Operational Spine

## Status

**ACCEPTED**

## Date

2026-01-22

## Context

The Barton system operates across multiple hubs (Outreach, Sales, Client) that all reference companies from the Company Lifecycle (CL) system. We needed to clarify:

1. What CL stores vs what Outreach stores
2. Who mints which IDs
3. How handoffs between hubs work
4. Where workflow state lives

Previous documentation conflated CL as both an authority registry AND a workflow state store, leading to confusion.

## Decision

### CL = Authority Registry (Identity Pointers Only)

CL's `company_identity` table stores **identity pointers only**:

```sql
cl.company_identity
├── sovereign_company_id   PK, IMMUTABLE (minted by CL)
├── outreach_id            WRITE-ONCE (minted by Outreach)
├── sales_process_id       WRITE-ONCE (minted by Sales)
└── client_id              WRITE-ONCE (minted by Client)
```

**CL does NOT store**:
- Workflow state
- Timestamps beyond creation
- Status fields
- Operational data

### Outreach = Operational Spine (Workflow State)

Outreach maintains its own operational spine:

```sql
outreach.outreach
├── outreach_id            PK (minted here, registered in CL)
├── sovereign_company_id   FK → cl.company_identity
├── status                 WORKFLOW STATE
├── created_at             OPERATIONAL TIMESTAMP
└── updated_at             OPERATIONAL TIMESTAMP
```

All Outreach sub-hubs (company_target, dol, people, blog) FK to `outreach_id`.

### ID Minting Rules

| ID | Minted By | Stored In CL | Operational Spine |
|----|-----------|--------------|-------------------|
| sovereign_company_id | CL | PK | — |
| outreach_id | Outreach | WRITE-ONCE | outreach.outreach |
| sales_process_id | Sales | WRITE-ONCE | sales.sales_process |
| client_id | Client | WRITE-ONCE | client.client |

### Outreach Init Pattern

```python
# 1. Verify company exists in CL and outreach_id is NULL
SELECT sovereign_company_id FROM cl.company_identity
WHERE sovereign_company_id = $sid
  AND outreach_id IS NULL;

# 2. Mint outreach_id in operational spine
INSERT INTO outreach.outreach (outreach_id, sovereign_company_id, status)
VALUES ($new_outreach_id, $sid, 'INIT');

# 3. Register in CL authority registry (WRITE-ONCE guard)
UPDATE cl.company_identity
SET outreach_id = $new_outreach_id
WHERE sovereign_company_id = $sid
  AND outreach_id IS NULL;

# 4. Verify write succeeded
if affected_rows != 1:
    ROLLBACK()
    HARD_FAIL("Outreach ID already claimed or invalid SID")
```

### Handoff Pattern (Outreach → Sales)

Outreach does NOT invoke Sales directly. Handoff occurs via:

1. Outreach generates signed calendar link (sid + oid + sig + TTL)
2. Meeting booking triggers webhook
3. Webhook fires Sales Init worker
4. Sales snapshots Outreach data at that moment
5. Sales mints `sales_process_id` and writes to CL

## Consequences

### Positive

- **Clear ownership**: Each hub owns its operational data
- **CL stays simple**: Identity pointers only, no workflow bloat
- **Decoupled hubs**: Handoff via webhook, not direct invocation
- **WRITE-ONCE guards**: Prevent duplicate claims
- **Audit trail**: Each spine tracks its own lifecycle

### Negative

- **Two writes for init**: Outreach must write to both spine and CL
- **Snapshot at handoff**: Sales gets point-in-time data, not live sync

### Neutral

- **No architectural refactor needed**: This clarifies existing design
- **Runtime behavior unchanged**: Only documentation updated

## Compliance

| Requirement | Status |
|-------------|--------|
| CL Parent-Child Doctrine v1.1 | COMPLIANT |
| WRITE-ONCE enforcement | COMPLIANT |
| Webhook handoff | COMPLIANT |
| Operational spine separation | COMPLIANT |

## Related Documents

- `CLAUDE.md` - Updated with CL registry + Outreach spine model
- `docs/COMPLETE_SYSTEM_ERD.md` - ERD with authority vs operational tables
- `docs/prd/PRD_OUTREACH_SPOKE.md` - Outreach responsibilities

## Tags

#adr #cl #outreach #identity #spine #authority-registry
