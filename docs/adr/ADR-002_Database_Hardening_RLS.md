# ADR-002: Database Hardening with Row-Level Security

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | CL Parent-Child Doctrine v1.0 |
| **CC Layer** | CC-03 |

---

## ADR Identity

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-002 |
| **Status** | [x] Accepted |
| **Date** | 2026-01-13 |

---

## Owning Hub (CC-02)

| Field | Value |
|-------|-------|
| **Sovereign ID** | CL (Company Lifecycle) |
| **Hub Name** | Barton Outreach Core |
| **Hub ID** | 04.04.02.04 |

---

## CC Layer Scope

| Layer | Affected | Description |
|-------|----------|-------------|
| CC-01 (Sovereign) | [ ] | N/A |
| CC-02 (Hub) | [x] | All sub-hubs receive RLS enforcement |
| CC-03 (Context) | [x] | RLS policies define access context |
| CC-04 (Process) | [x] | Migrations executed, roles created |

---

## IMO Layer Scope

| Layer | Affected |
|-------|----------|
| I - Ingress | [ ] |
| M - Middle | [x] |
| O - Egress | [x] |

---

## Constant vs Variable

| Classification | Value |
|----------------|-------|
| **This decision defines** | [x] Constant (structure/meaning) |
| **Mutability** | [x] Immutable |

---

## Context

**Problem Statement:**

During the 2026-01-13 lifecycle audit, the following gaps were identified:

1. **DOL Hub had NO database tables** - The DOL Filings Hub (04.04.03) referenced tables that did not exist
2. **Outreach execution incomplete** - Missing campaigns, sequences, send_log tables
3. **No RLS on production tables** - Direct database access bypassed doctrine enforcement
4. **Immutability not enforced** - engagement_events could be modified/deleted

**Urgency:**

People CSV ingestion at scale requires guaranteed:
- FK integrity (no orphan records)
- Lifecycle order enforcement (company anchor first)
- Event log immutability (audit trail preservation)

---

## Decision

**Implement database-level hardening using PostgreSQL Row-Level Security (RLS) with role-based access control.**

### Schema Creation

| Schema | Tables Created | Purpose |
|--------|----------------|---------|
| `dol` | form_5500, form_5500_sf, schedule_a, renewal_calendar | DOL Filings Hub storage |
| `outreach` | campaigns, sequences, send_log | Outreach execution tracking |

### RLS Implementation

| Pattern | Implementation |
|---------|----------------|
| **Default Deny** | RLS enabled on all production tables |
| **Explicit Allow** | Policies grant access per-operation (SELECT, INSERT, UPDATE) |
| **Role-Based** | Three roles control access |
| **Immutability** | DELETE blocked on event logs via trigger |

### Role Definitions

| Role | Permissions | Tables |
|------|-------------|--------|
| `outreach_hub_writer` | SELECT, INSERT, UPDATE | outreach.* |
| `dol_hub_writer` | SELECT, INSERT, UPDATE | dol.* |
| `hub_reader` | SELECT only | All hub tables |

### Immutability Enforcement

```sql
-- engagement_events DELETE blocked at trigger level
CREATE TRIGGER trg_engagement_events_immutability_delete
    BEFORE DELETE ON outreach.engagement_events
    FOR EACH ROW
    EXECUTE FUNCTION outreach.fn_engagement_events_immutability();
```

---

## Alternatives Considered

| Option | Why Not Chosen |
|--------|----------------|
| Application-level access control only | Bypassable via direct DB access |
| PostgreSQL GRANT without RLS | No row-level filtering capability |
| Column-level encryption | Overkill for access control, adds complexity |
| Do Nothing | Unacceptable security posture for production |

---

## Consequences

### Enables

- **Defense in depth**: Database enforces doctrine even if application bypassed
- **Audit compliance**: Immutable event logs for traceability
- **Role separation**: Writers can't delete, readers can't write
- **Lifecycle enforcement**: FK constraints prevent orphan records
- **Production readiness**: Safe for People CSV ingestion at scale

### Prevents

- **Accidental data deletion**: engagement_events immutable
- **Unauthorized writes**: Role-based access control
- **Orphan records**: FK constraints to company_target
- **Doctrine bypass**: RLS enforces rules at database level

---

## PID Impact (if CC-04 affected)

| Field | Value |
|-------|-------|
| **New PID required** | [x] Yes - Migration execution PIDs |
| **PID pattern change** | [ ] No |
| **Audit trail impact** | New migrations recorded in master_error_log |

---

## Guard Rails

| Type | Value | CC Layer |
|------|-------|----------|
| Rate Limit | N/A (database-level) | CC-04 |
| Timeout | 30s per migration | CC-04 |
| Kill Switch | Rollback via SQL | CC-04 |

---

## Rollback

1. Drop RLS policies: `DROP POLICY IF EXISTS ... ON ...`
2. Disable RLS: `ALTER TABLE ... DISABLE ROW LEVEL SECURITY`
3. Drop roles: `DROP ROLE IF EXISTS outreach_hub_writer, dol_hub_writer, hub_reader`
4. Drop triggers: `DROP TRIGGER IF EXISTS trg_engagement_events_immutability_delete ON ...`

Note: Schema/table drops require data backup first.

---

## Traceability

| Artifact | Reference |
|----------|-----------|
| Canonical Doctrine | CANONICAL_ARCHITECTURE_DOCTRINE.md |
| PRD | PRD_OUTREACH_SPOKE.md, PRD_DOL_SUBHUB.md |
| Work Items | Lifecycle Audit 2026-01-13 |
| PR(s) | Database Hardening PR (this commit) |

---

## Migrations Created

| Migration | Purpose | Tables |
|-----------|---------|--------|
| `2026-01-13-dol-schema-creation.sql` | DOL Hub tables | 4 tables, 16 indexes |
| `2026-01-13-outreach-execution-complete.sql` | Outreach execution | 3 tables, 14 indexes |
| `2026-01-13-enable-rls-production-tables.sql` | RLS + roles | 29 policies, 3 roles |

---

## Verification Results

| Check | Status | Details |
|-------|--------|---------|
| FK Existence | PASS | 25 FKs in outreach/dol schemas |
| RLS Policies | PASS | 29 policies active |
| Lifecycle Order | PASS | FK constraints enforce sequence |
| Immutability | PASS | engagement_events DELETE blocked |
| Gate Enforcement | PASS | All phases validate company anchor |

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner (CC-02) | Barton Doctrine | 2026-01-13 |
| Reviewer | Claude Code | 2026-01-13 |
| Implementation | Claude Code | 2026-01-13 |

---

## AI Audit Record

```yaml
audit_id: AUDIT-2026-01-13-001
audit_type: lifecycle_verification
audit_date: 2026-01-13
auditor: claude-opus-4-5-20251101
status: PASS
verdict: GREEN for People CSV ingestion at scale

checks_performed:
  - fk_existence: 25 FKs verified
  - rls_policies: 29 policies active
  - lifecycle_order: FK constraints enforce sequence
  - gate_enforcement: All phases validate company anchor
  - immutability: engagement_events DELETE trigger present

migrations_executed:
  - 2026-01-13-dol-schema-creation.sql
  - 2026-01-13-outreach-execution-complete.sql
  - 2026-01-13-enable-rls-production-tables.sql

tables_hardened:
  outreach:
    - company_target
    - people
    - engagement_events
    - campaigns
    - sequences
    - send_log
  dol:
    - form_5500
    - form_5500_sf
    - schedule_a
    - renewal_calendar

roles_created:
  - outreach_hub_writer
  - dol_hub_writer
  - hub_reader
```
