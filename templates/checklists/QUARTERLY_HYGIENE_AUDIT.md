# Quarterly Hygiene Audit Checklist

**Status**: TEMPLATE
**Authority**: CONSTITUTIONAL
**Version**: 1.1.0

---

## Purpose

This checklist MUST be completed for every quarterly hygiene audit.
**No audit is valid without completing this checklist.**

---

## Audit Metadata

| Field | Value |
|-------|-------|
| **Repository** | |
| **Audit Date** | |
| **Quarter** | Q1 / Q2 / Q3 / Q4 |
| **Year** | |
| **Auditor** | |

---

## Quarterly Schedule

| Quarter | Target Date | Status |
|---------|-------------|--------|
| Q1 | January 15 | |
| Q2 | April 15 | |
| Q3 | July 15 | |
| Q4 | October 15 | |

---

## COMPLIANCE GATE (MANDATORY)

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                      ZERO-TOLERANCE ENFORCEMENT RULE                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  You CANNOT mark an audit as COMPLIANT if:                                    ║
║                                                                               ║
║    1. ANY CRITICAL violations exist                                           ║
║    2. ANY HIGH violations exist                                               ║
║                                                                               ║
║  HIGH violations are NOT "fix later" items.                                   ║
║  HIGH violations BLOCK compliance.                                            ║
║                                                                               ║
║  The ONLY path forward is:                                                    ║
║    → FIX the violation, OR                                                    ║
║    → DOWNGRADE to MEDIUM with documented justification + ADR                  ║
║                                                                               ║
║  NEVER mark COMPLIANT with open HIGH/CRITICAL violations.                     ║
║  This is a HARD RULE. No exceptions.                                          ║
║                                                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Common Mistake (DO NOT DO THIS)

```
❌ WRONG: "5 HIGH violations found. Status: COMPLIANT"
   This is INVALID. HIGH violations block compliance.

✅ RIGHT: "5 HIGH violations found. Status: NON-COMPLIANT"
   Then fix the violations and re-audit.

✅ RIGHT: "0 HIGH/CRITICAL violations. 3 MEDIUM. Status: COMPLIANT WITH NOTES"
   Medium violations are documented but don't block.
```

---

## Pre-Audit Setup

| Check | Status |
|-------|--------|
| [ ] Latest main branch pulled | |
| [ ] Database access verified (READ-ONLY) | |
| [ ] Previous audit reviewed | |
| [ ] ADRs since last audit reviewed | |

---

## 1. Schema Drift Check

| Check | Status | Notes |
|-------|--------|-------|
| [ ] Run schema verification script | | |
| [ ] Compare Neon tables to SCHEMA.md | | |
| [ ] Identify undocumented tables | | |
| [ ] Identify missing tables | | |

**Schema Drift Finding**: [ ] None / [ ] Drift detected (see notes)

---

## 2. IMO Compliance Check

For each hub, verify:

| Hub | IMO Structure | Spokes I/O Only | Tools in M Only | Status |
|-----|---------------|-----------------|-----------------|--------|
| | [ ] YES | [ ] YES | [ ] YES | [ ] PASS / [ ] FAIL |
| | [ ] YES | [ ] YES | [ ] YES | [ ] PASS / [ ] FAIL |
| | [ ] YES | [ ] YES | [ ] YES | [ ] PASS / [ ] FAIL |

---

## 3. CTB Compliance Check

| Check | Status |
|-------|--------|
| [ ] No forbidden folders (utils, helpers, common, shared, lib, misc) | |
| [ ] CTB branches intact (sys, data, app, ai, ui) | |
| [ ] No root-level unauthorized scripts | |

---

## 4. ERD Format Check

| Check | Status |
|-------|--------|
| [ ] All SCHEMA.md files use Mermaid erDiagram | |
| [ ] All SCHEMA.md files declare Neon authority | |
| [ ] All tables have documented purpose | |
| [ ] All FKs are documented | |

---

## 5. ADR Review

| ADR | Date | Summary | Impact |
|-----|------|---------|--------|
| | | | |
| | | | |

---

## 6. Version Assessment

| Check | Status |
|-------|--------|
| [ ] Doctrine versions current | |
| [ ] IMO_CONTROL.json up to date | |
| [ ] Version bump required? | [ ] YES / [ ] NO |

---

## 7. Data Accuracy Verification

**Purpose**: Verify all documented data values in MD files match the Neon database (source of truth).

### Required Queries

Run these queries against Neon and record actual values:

```sql
-- Core alignment (MUST MATCH)
SELECT COUNT(*) FROM outreach.outreach;                                    -- Spine
SELECT COUNT(*) FROM cl.company_identity WHERE outreach_id IS NOT NULL;    -- CL claimed
SELECT COUNT(*) FROM outreach.outreach_excluded;                           -- Excluded

-- Sub-hub counts
SELECT COUNT(*) FROM outreach.company_target;
SELECT COUNT(*) FROM outreach.dol;
SELECT COUNT(*) FROM outreach.blog;
SELECT COUNT(*) FROM outreach.bit_scores;
SELECT COUNT(*) FROM outreach.people;

-- People/CL counts
SELECT COUNT(*) FROM people.company_slot;
SELECT COUNT(*) FROM people.people_master;
SELECT COUNT(*) FROM cl.company_identity;
SELECT COUNT(*) FROM cl.company_domains;
```

### Verification Table

| Metric | Neon Value | CLAUDE.md | DATA_REGISTRY.md | SCHEMA.md | Status |
|--------|------------|-----------|------------------|-----------|--------|
| outreach.outreach | | | | | [ ] MATCH / [ ] STALE |
| CL with outreach_id | | | | | [ ] MATCH / [ ] STALE |
| outreach_excluded | | | | | [ ] MATCH / [ ] STALE |
| company_target | | | | | [ ] MATCH / [ ] STALE |
| outreach.dol | | | | | [ ] MATCH / [ ] STALE |
| outreach.blog | | | | | [ ] MATCH / [ ] STALE |
| bit_scores | | | | | [ ] MATCH / [ ] STALE |
| outreach.people | | | | | [ ] MATCH / [ ] STALE |
| company_slot | | | | | [ ] MATCH / [ ] STALE |
| people_master | | | | | [ ] MATCH / [ ] STALE |
| cl.company_identity | | | | | [ ] MATCH / [ ] STALE |
| cl.company_domains | | | | | [ ] MATCH / [ ] STALE |

### Alignment Rule Verification

```
CL-Outreach Golden Rule:
outreach.outreach count = cl.company_identity (outreach_id NOT NULL) count

Actual: _______ = _______ [ ] ALIGNED / [ ] MISALIGNED
```

### Files to Check

| File | Contains Data Values | Checked |
|------|---------------------|---------|
| `CLAUDE.md` | Post-Cleanup State table | [ ] |
| `docs/DATA_REGISTRY.md` | All table counts | [ ] |
| `hubs/*/SCHEMA.md` | Hub-specific counts | [ ] |
| `docs/MASTER_ERD.md` | Table counts section | [ ] |
| `docs/COMPLETE_SYSTEM_ERD.md` | Architecture diagrams | [ ] |
| `docs/ERD_SUMMARY.md` | Summary counts | [ ] |

### Data Accuracy Result

| Check | Status |
|-------|--------|
| [ ] All documented values match Neon | |
| [ ] CL-Outreach alignment verified | |
| [ ] Stale values updated (if any) | |

**Data Accuracy Finding**: [ ] All values current / [ ] Updates applied (list files below)

Files updated:
-
-

---

## Violations Found

| # | Violation | Severity | Category | Status |
|---|-----------|----------|----------|--------|
| 1 | | CRITICAL / HIGH / MEDIUM / LOW | | [ ] Fixed / [ ] Open |
| 2 | | CRITICAL / HIGH / MEDIUM / LOW | | [ ] Fixed / [ ] Open |
| 3 | | CRITICAL / HIGH / MEDIUM / LOW | | [ ] Fixed / [ ] Open |

---

## Compliance Gate Verification

| Severity | Count | Gate Status |
|----------|-------|-------------|
| CRITICAL | | [ ] 0 = PASS / [ ] >0 = BLOCKED |
| HIGH | | [ ] 0 = PASS / [ ] >0 = BLOCKED |
| MEDIUM | | [ ] Documented |
| LOW | | [ ] N/A |

**Gate Result**: [ ] PASS / [ ] BLOCKED

---

## Resolution Actions

### Immediate (Before Marking Compliant)

| Action | Owner | Status |
|--------|-------|--------|
| | | [ ] Done |
| | | [ ] Done |

### Follow-Up (Within Quarter)

| Action | Owner | Deadline | Status |
|--------|-------|----------|--------|
| | | | [ ] Pending |
| | | | [ ] Pending |

---

## Audit Verdict

```
[ ] COMPLIANT (CLEAN PASS)
    → 0 CRITICAL, 0 HIGH, 0 MEDIUM violations
    → All checks passed

[ ] COMPLIANT WITH NOTES
    → 0 CRITICAL, 0 HIGH violations
    → MEDIUM violations documented with owners + deadlines

[ ] NON-COMPLIANT
    → CRITICAL or HIGH violations exist
    → MUST fix before marking compliant
    → Re-audit required after remediation
```

---

## Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Auditor | | | |
| Reviewer | | | |
| Engineering Lead (if required) | | | |

---

## Next Audit

| Field | Value |
|-------|-------|
| Next Audit Date | |
| Assigned Auditor | |
| Quarter | |

---

## Traceability

| Document | Reference |
|----------|-----------|
| Constitutional Attestation | templates/audit/CONSTITUTIONAL_AUDIT_ATTESTATION.md |
| Hub Compliance | templates/checklists/HUB_COMPLIANCE.md |
| Hygiene Auditor | templates/claude/HYGIENE_AUDITOR.prompt.md |
| Data Accuracy Report | docs/reports/DATA_ACCURACY_CHECK_{DATE}.md |

---

## Document Control

| Field | Value |
|-------|-------|
| Template Version | 1.1.0 |
| Authority | CONSTITUTIONAL |
| Change Protocol | ADR + HUMAN APPROVAL REQUIRED |
