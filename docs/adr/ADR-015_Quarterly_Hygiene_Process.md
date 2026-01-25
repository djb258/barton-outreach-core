# ADR-015: Quarterly Hygiene and Schema Drift Audit Process

## Status
**ACCEPTED**

## Date
2026-01-25

## Context

With the establishment of IMO_CANONICAL_v1.0 as the doctrine freeze point, we need a recurring process to detect and prevent entropy drift. Without active monitoring, schemas diverge, documentation becomes stale, and CTB violations creep back in.

## Decision

Establish a **Quarterly Hygiene Audit** process with the following components:

### 1. SNAP_ON Audit (Quarterly)

Run comprehensive audit every quarter:

```bash
# Q1: January 15
# Q2: April 15
# Q3: July 15
# Q4: October 15

doppler run -- python scripts/ci/verify_schema_drift.py
python scripts/ci/audit_imo_compliance.py
```

### 2. Schema Drift Detection

| Check | Frequency | Gate |
|-------|-----------|------|
| Neon ≠ SCHEMA.md | Every PR | HARD FAIL |
| SCHEMA.md missing Mermaid | Every PR | HARD FAIL |
| SCHEMA.md missing authority | Every PR | HARD FAIL |
| Forbidden folders | Every PR | HARD FAIL |
| IMO template compliance | Every PR | HARD FAIL |

### 3. Drift Resolution Process

When drift is detected:

1. **Immediate**: Block merge until resolved
2. **Assessment**: Determine if drift is intentional or accidental
3. **If Intentional**:
   - Create ADR documenting the change
   - Bump doctrine version (v1.0 → v1.1)
   - Update SCHEMA.md with new Neon verification date
4. **If Accidental**:
   - Fix SCHEMA.md to match Neon
   - No ADR needed
   - Run full audit to verify

### 4. Version Bump Policy

| Change Type | Version Bump | ADR Required |
|-------------|--------------|--------------|
| New table added | MINOR (v1.0 → v1.1) | YES |
| Column added | MINOR | YES |
| Column removed | MAJOR (v1.0 → v2.0) | YES |
| Table removed | MAJOR | YES |
| Documentation only | PATCH (v1.0 → v1.0.1) | NO |
| New hub added | MINOR | YES |

### 5. Quarterly Hygiene Checklist

```markdown
## Quarterly Hygiene Audit Checklist

Date: ___________
Auditor: ___________
Doctrine Version: ___________

### Pre-Audit
- [ ] Pull latest main branch
- [ ] Verify Doppler access
- [ ] Verify Neon READ-ONLY access

### Schema Drift
- [ ] Run: `doppler run -- python scripts/ci/verify_schema_drift.py`
- [ ] Result: PASS / FAIL
- [ ] If FAIL, list drift items:
  - [ ] _________________
  - [ ] _________________

### IMO Compliance
- [ ] Run: `python scripts/ci/audit_imo_compliance.py`
- [ ] Result: PASS / FAIL
- [ ] All hubs have SCHEMA.md: YES / NO
- [ ] All hubs have CHECKLIST.md: YES / NO
- [ ] All hubs have PRD.md: YES / NO

### CTB Compliance
- [ ] No forbidden folders (utils, helpers, etc.): YES / NO
- [ ] All ERDs in Mermaid format: YES / NO
- [ ] All SCHEMA.md have Neon authority: YES / NO

### Resolution Actions
- [ ] ADRs created for any intentional drift: ___________
- [ ] Version bump required: YES / NO → New version: ___________
- [ ] SCHEMA.md files updated with new verification date: YES / NO

### Sign-Off
- [ ] Audit complete
- [ ] Results documented in #doctrine-audit Slack channel
- [ ] Next audit scheduled: ___________
```

## Calendar Integration

### Recurring Events

| Event | Schedule | Owner |
|-------|----------|-------|
| Q1 Hygiene Audit | January 15 | Engineering Lead |
| Q2 Hygiene Audit | April 15 | Engineering Lead |
| Q3 Hygiene Audit | July 15 | Engineering Lead |
| Q4 Hygiene Audit | October 15 | Engineering Lead |

### Notifications

- 1 week before: Reminder to engineering team
- Day of: Audit begins, block non-essential merges
- 1 day after: Results published to #doctrine-audit

## Consequences

### Positive
- Prevents entropy drift
- Maintains documentation accuracy
- Enforces discipline on schema changes
- Clear versioning for audit trail

### Negative
- Quarterly overhead for auditors
- May slow down urgent changes during audit window

### Neutral
- Requires Doppler and Neon access for auditors

## Implementation

1. Add calendar events for Q1-Q4 2026
2. Create #doctrine-audit Slack channel
3. Document audit owner rotation
4. Train team on drift resolution process

## References

- CI Workflow: `.github/workflows/doctrine-audit.yml`
- Schema Drift Script: `scripts/ci/verify_schema_drift.py`
- IMO Audit Script: `scripts/ci/audit_imo_compliance.py`
- Freeze Tag: `IMO_CANONICAL_v1.0`

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-25 |
| Author | Claude Code |
| Status | ACCEPTED |
| Review Frequency | Quarterly |
