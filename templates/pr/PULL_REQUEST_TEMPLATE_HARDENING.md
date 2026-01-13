# Database Hardening Change

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | CL Parent-Child Doctrine v1.0 |
| **CC Layer** | CC-04 |

---

## Hub Identity (CC-02)

| Field | Value |
|-------|-------|
| **Sovereign ID** | CL (Company Lifecycle) |
| **Hub Name** | Barton Outreach Core |
| **Hub ID** | 04.04.02.04 |
| **PID Pattern** | MIGRATION-{DATE}-{SEQ} |

---

## Change Type

- [ ] New Schema Creation
- [ ] Table Creation
- [ ] RLS Policy Addition
- [ ] Role Creation
- [ ] Index Creation
- [ ] Trigger Creation
- [ ] Migration Order Update

---

## Scope Declaration

### Schemas Affected

| Schema | Tables | RLS Policies | Roles |
|--------|--------|--------------|-------|
| outreach | | | |
| dol | | | |
| funnel | | | |
| bit | | | |

### IMO Layers Affected

| Layer | Modified |
|-------|----------|
| I - Ingress | [ ] |
| M - Middle | [x] |
| O - Egress | [x] |

---

## Summary

_What changed and why? Reference the approved ADR - do not define architecture here._

---

## Migrations Included

| Migration File | Purpose |
|----------------|---------|
| | |
| | |

---

## Verification Queries

```sql
-- Check schemas exist
SELECT schema_name FROM information_schema.schemata
WHERE schema_name IN ('outreach', 'dol', 'funnel', 'bit');

-- Check table counts
SELECT table_schema, COUNT(*) as table_count
FROM information_schema.tables
WHERE table_schema IN ('outreach', 'dol')
GROUP BY table_schema;

-- Check RLS enabled
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname IN ('outreach', 'dol')
ORDER BY schemaname, tablename;

-- Check roles created
SELECT rolname FROM pg_roles
WHERE rolname IN ('outreach_hub_writer', 'dol_hub_writer', 'hub_reader', 'error_log_writer');
```

---

## Traceability

| Artifact | Reference |
|----------|-----------|
| Canonical Doctrine | CANONICAL_ARCHITECTURE_DOCTRINE.md |
| ADR | ADR-002_Database_Hardening_RLS.md |
| Migration Order | infra/MIGRATION_ORDER.md |
| Work Item | |

---

## CC Layer Scope

| CC Layer | Affected | Description |
|----------|----------|-------------|
| CC-01 (Sovereign) | [ ] | |
| CC-02 (Hub) | [x] | All sub-hubs receive hardening |
| CC-03 (Context) | [x] | RLS policies define access context |
| CC-04 (Process) | [x] | Migrations executed |

---

## Compliance Checklist

### Doctrine Compliance
- [ ] Doctrine version declared
- [ ] Sovereign reference present (CC-01)
- [ ] Authorization matrix honored (no upward writes)

### Database Compliance
- [ ] RLS enabled on all production tables
- [ ] Roles created with least-privilege
- [ ] FK constraints validate lifecycle order
- [ ] Immutability triggers on event logs
- [ ] Migration order documented

### Audit Compliance
- [ ] AI audit record created
- [ ] Human-readable audit note created
- [ ] ADR approved and merged
- [ ] PRD updated with schema changes

---

## Promotion Gates

| Gate | Requirement | Passed |
|------|-------------|--------|
| G1 | ADR approved | [ ] |
| G2 | Migration order documented | [ ] |
| G3 | Verification queries pass | [ ] |
| G4 | RLS policies active | [ ] |
| G5 | Lifecycle audit PASS | [ ] |

---

## Rollback

1. Drop RLS policies: `DROP POLICY IF EXISTS ... ON ...`
2. Disable RLS: `ALTER TABLE ... DISABLE ROW LEVEL SECURITY`
3. Drop roles: `DROP ROLE IF EXISTS ...`
4. Drop triggers: `DROP TRIGGER IF EXISTS ... ON ...`

Note: Schema/table drops require data backup first.

---

## Post-Merge Verification

```bash
# Run verification queries against production
doppler run -- psql -f infra/scripts/verify_hardening.sql

# Check migration order
cat infra/MIGRATION_ORDER.md
```
