# Deployment Checklist: Sovereign Completion Infrastructure

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | CL Parent-Child Doctrine v1.1 |
| **CC Layer** | CC-04 |

---

## Hub Identity (CC-02)

| Field | Value |
|-------|-------|
| **Sovereign ID** | barton-enterprises |
| **Hub Name** | Sovereign Completion |
| **Hub ID** | 04.04.02.04.SC |

---

## Pre-Deployment Checklist

### Documentation Verification
- [x] ADR approved and merged (ADR-006, ADR-007)
- [x] PRDs created (PRD_SOVEREIGN_COMPLETION, PRD_KILL_SWITCH_SYSTEM)
- [x] ERD updated (SOVEREIGN_COMPLETION_ERD.md)
- [x] Obsidian documentation created

### Migration Preparation
- [x] Migration files present in infra/migrations/
- [x] Migration order verified
- [x] Rollback plan documented

### Environment Verification
- [x] Doppler secrets configured
- [x] Database connection verified
- [x] Sufficient permissions confirmed

---

## Migration Execution Order

Execute migrations in this exact order:

### Phase 1: Hub Registry
```bash
doppler run -- psql -f infra/migrations/2026-01-19-hub-registry.sql
```

Verify:
```sql
SELECT COUNT(*) FROM outreach.hub_registry;  -- Should be 6
SELECT COUNT(*) FROM outreach.company_hub_status;  -- Should be 0 initially
```

### Phase 2: Sovereign Completion Views
```bash
doppler run -- psql -f infra/migrations/2026-01-19-sovereign-completion-view.sql
```

Verify:
```sql
SELECT COUNT(*) FROM outreach.vw_sovereign_completion;
SELECT COUNT(*) FROM outreach.vw_marketing_eligibility;
```

### Phase 3: Kill Switches
```bash
doppler run -- psql -f infra/migrations/2026-01-19-kill-switches.sql
```

Verify:
```sql
SELECT COUNT(*) FROM outreach.manual_overrides;  -- Should be 0
SELECT rowsecurity FROM pg_tables WHERE tablename = 'manual_overrides';  -- Should be true
```

### Phase 4: Backfill Hub Status
```sql
-- Backfill company-target
INSERT INTO outreach.company_hub_status (company_unique_id, hub_id, status, status_reason, backfill_source)
SELECT company_unique_id, 'company-target', 'PASS'::outreach.hub_status_enum,
       'Backfilled: Record exists in company_target', 'initial_migration'
FROM outreach.company_target WHERE company_unique_id IS NOT NULL
ON CONFLICT (company_unique_id, hub_id) DO NOTHING;

-- Backfill other required hubs as IN_PROGRESS
INSERT INTO outreach.company_hub_status (company_unique_id, hub_id, status, status_reason, backfill_source)
SELECT ct.company_unique_id, hr.hub_id, 'IN_PROGRESS'::outreach.hub_status_enum,
       'Backfilled: Awaiting hub processing', 'initial_migration'
FROM outreach.company_target ct
CROSS JOIN outreach.hub_registry hr
WHERE hr.classification = 'required' AND hr.hub_id != 'company-target'
AND ct.company_unique_id IS NOT NULL
ON CONFLICT (company_unique_id, hub_id) DO NOTHING;
```

---

## Post-Deployment Verification

### Infrastructure Checks
- [x] hub_registry exists with 6 rows
- [x] company_hub_status exists with data
- [x] manual_overrides exists
- [x] override_audit_log exists
- [x] vw_sovereign_completion returns data
- [x] vw_marketing_eligibility returns data
- [x] vw_marketing_eligibility_with_overrides returns data

### Doctrine Compliance Checks
- [x] Required hubs in correct waterfall order
- [x] No false COMPLETE status
- [x] BIT is gate, not hub
- [x] Tier 3 requires COMPLETE + BIT >= 50
- [x] BLOCKED companies are Tier -1

### Data Integrity Checks
- [x] company_target count matches vw_sovereign_completion
- [x] No NULL company_unique_id in hub status
- [x] All hub_ids reference valid hubs
- [x] No ghost PASS entries

### Operational Safety Checks
- [x] Kill switch table has required columns
- [x] Override view has effective_tier and computed_tier
- [x] Error tables exist for failure routing
- [x] RLS enabled on manual_overrides
- [x] Override audit log exists

---

## Verification Queries

```sql
-- Check tier distribution
SELECT effective_tier, COUNT(*) as cnt
FROM outreach.vw_marketing_eligibility_with_overrides
GROUP BY effective_tier
ORDER BY effective_tier;

-- Check for ghost PASS
SELECT COUNT(*) FROM outreach.company_hub_status chs
WHERE chs.hub_id = 'company-target' AND chs.status = 'PASS'
AND NOT EXISTS (
    SELECT 1 FROM outreach.company_target ct
    WHERE ct.company_unique_id = chs.company_unique_id
);

-- Check RLS
SELECT tablename, rowsecurity FROM pg_tables
WHERE schemaname = 'outreach'
AND tablename IN ('manual_overrides', 'override_audit_log');

-- Check policies
SELECT tablename, policyname, cmd, roles
FROM pg_policies
WHERE schemaname = 'outreach';
```

---

## Final Certification

Run Final Certification Agent (Agent C) to verify:

```bash
doppler run -- python temp_final_certification.py
```

Expected result: **SAFE TO ENABLE LIVE MARKETING: YES**

---

## Rollback Procedure

If deployment fails:

```sql
-- 1. Drop views
DROP VIEW IF EXISTS outreach.vw_marketing_eligibility_with_overrides;
DROP VIEW IF EXISTS outreach.vw_marketing_eligibility;
DROP VIEW IF EXISTS outreach.vw_sovereign_completion;

-- 2. Disable RLS
ALTER TABLE outreach.manual_overrides DISABLE ROW LEVEL SECURITY;
ALTER TABLE outreach.override_audit_log DISABLE ROW LEVEL SECURITY;

-- 3. Drop policies
DROP POLICY IF EXISTS manual_overrides_owner_policy ON outreach.manual_overrides;
DROP POLICY IF EXISTS override_audit_owner_policy ON outreach.override_audit_log;
DROP POLICY IF EXISTS override_audit_read_policy ON outreach.override_audit_log;

-- 4. Drop tables
DROP TABLE IF EXISTS outreach.override_audit_log;
DROP TABLE IF EXISTS outreach.manual_overrides;
DROP TABLE IF EXISTS outreach.company_hub_status;
DROP TABLE IF EXISTS outreach.hub_registry;

-- 5. Drop enums
DROP TYPE IF EXISTS outreach.override_type_enum;
DROP TYPE IF EXISTS outreach.hub_status_enum;
```

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Deployer | Claude Code | 2026-01-19 | Deployed |
| Verifier | Final Certification Agent | 2026-01-19 | PASS |
| Hub Owner | | | |

---

## Traceability

| Artifact | Reference |
|----------|-----------|
| Canonical Doctrine | CANONICAL_ARCHITECTURE_DOCTRINE.md |
| ADR | docs/adr/ADR-006_Sovereign_Completion_Infrastructure.md |
| ADR | docs/adr/ADR-007_Kill_Switch_System.md |
| PRD | docs/prd/PRD_SOVEREIGN_COMPLETION.md |
| PRD | docs/prd/PRD_KILL_SWITCH_SYSTEM.md |
| ERD | docs/SOVEREIGN_COMPLETION_ERD.md |
| Certification | docs/reports/FINAL_CERTIFICATION_REPORT_2026-01-19.md |
