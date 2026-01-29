# Audit Procedure

**Status**: MANDATORY
**Authority**: CONSTITUTIONAL
**Version**: 1.0.0
**Last Updated**: 2026-01-29

---

## Purpose

This document defines the MANDATORY procedure for conducting audits in the barton-outreach-core repository. **No audit is valid without following this procedure.**

---

## Audit Types

| Type | Trigger | Frequency |
|------|---------|-----------|
| **Quarterly Hygiene** | Calendar | Q1 (Jan 15), Q2 (Apr 15), Q3 (Jul 15), Q4 (Oct 15) |
| **Post-Change** | After significant changes | As needed |
| **Post-Cleanup** | After cascade cleanup | As needed |
| **Initial Certification** | Before v1.0 release | Once |

---

## MANDATORY Checklists

**Every audit MUST fill out and complete these checklists:**

### 1. Quarterly Hygiene Audit Checklist

**Template**: `templates/checklists/QUARTERLY_HYGIENE_AUDIT.md`

**Required For**:
- All scheduled quarterly audits
- Post-cleanup audits
- Post-change audits

**Sections to Complete**:
- [ ] Audit Metadata (date, quarter, auditor)
- [ ] Pre-Audit Setup (verify access)
- [ ] Schema Drift Check (run verification scripts)
- [ ] IMO Compliance Check (all hubs)
- [ ] CTB Compliance Check (forbidden folders)
- [ ] ERD Format Check (Mermaid diagrams)
- [ ] ADR Review (new ADRs since last audit)
- [ ] Version Assessment (bump required?)
- [ ] Resolution Actions (immediate and follow-up)
- [ ] Sign-Off (auditor, reviewer, lead)
- [ ] Next Audit (schedule)

### 2. Hub Compliance Checklist

**Template**: `templates/checklists/HUB_COMPLIANCE.md`

**Required For**:
- New hub creation
- Hub modification
- Constitutional validation

**Sections to Complete**:
- [ ] Part A: Constitutional Validity (CONST → VAR)
- [ ] Part A: PRD Compliance
- [ ] Part A: ERD Compliance
- [ ] Part A: ERD Pressure Test (Q1-Q4 for each table)
- [ ] Part A: ERD Upstream Flow Test
- [ ] Part A: Process Compliance
- [ ] Part B: Operational Compliance (all sections)
- [ ] Compliance Summary (count CRITICAL/HIGH/MEDIUM)

### 3. Constitutional Audit Attestation

**Template**: `templates/audit/CONSTITUTIONAL_AUDIT_ATTESTATION.md`

**Required For**:
- ALL audits (this is the final sign-off document)

**Sections to Complete**:
- [ ] Repo Metadata
- [ ] Doctrine Versions (verify all compliant)
- [ ] Remediation Order Acknowledgment
- [ ] Hub Compliance Roll-Up (one per hub)
- [ ] ERD Compliance Roll-Up (Pressure Test + Flow Test)
- [ ] Process Compliance Roll-Up
- [ ] Kill Switch & Observability
- [ ] Violations Found (list all)
- [ ] Final Constitutional Verdict
- [ ] Attestation signatures

---

## Audit Output Requirements

**Every audit MUST produce these artifacts:**

| Artifact | Location | Naming Convention |
|----------|----------|-------------------|
| Quarterly Hygiene Audit | `docs/audits/` | `QUARTERLY_HYGIENE_AUDIT_YYYY-QN.md` |
| Constitutional Attestation | `docs/audits/` | `CONSTITUTIONAL_AUDIT_ATTESTATION_YYYY-MM-DD.md` |
| Hub Compliance (if needed) | `docs/audits/` | `HUB_COMPLIANCE_[HUB_NAME]_YYYY-MM-DD.md` |

**Example naming**:
- `QUARTERLY_HYGIENE_AUDIT_2026-Q1.md`
- `CONSTITUTIONAL_AUDIT_ATTESTATION_2026-01-29.md`
- `HUB_COMPLIANCE_COMPANY_TARGET_2026-01-29.md`

---

## Audit Workflow

```
1. PREPARE
   ├── Pull latest main branch
   ├── Verify Doppler access
   ├── Verify Neon READ-ONLY access
   └── Review ADRs since last audit

2. EXECUTE
   ├── Fill out QUARTERLY_HYGIENE_AUDIT.md checklist
   ├── Fill out HUB_COMPLIANCE.md for each hub (if full audit)
   ├── Run verification scripts
   └── Document all findings

3. DOCUMENT
   ├── Create audit artifacts in docs/audits/
   ├── Fill out CONSTITUTIONAL_AUDIT_ATTESTATION.md
   └── List all violations with severity

4. REMEDIATE
   ├── Create immediate action items
   ├── Create follow-up action items
   └── Assign owners and deadlines

5. SIGN-OFF
   ├── Auditor signature
   ├── Reviewer signature
   └── Engineering Lead signature (if required)

6. SCHEDULE
   └── Document next audit date and assigned auditor
```

---

## Violation Severity Levels

| Severity | Ship Without? | Action Required |
|----------|---------------|-----------------|
| **CRITICAL** | NO | Must fix before production |
| **HIGH** | Only with ADR exception | Fix within sprint |
| **MEDIUM** | Yes, but document why | Fix within quarter |
| **LOW** | Yes | Fix when convenient |

---

## Non-Compliant Audits

**An audit is NON-COMPLIANT if:**

1. Quarterly Hygiene Checklist not filled out
2. Constitutional Attestation not produced
3. CRITICAL violations not addressed
4. Sign-off section incomplete
5. Next audit not scheduled

**Non-compliant audits are NON-AUTHORITATIVE** and must be re-done.

---

## Historical Audits

| Date | Type | Attestation | Result |
|------|------|-------------|--------|
| 2026-01-19 | Initial Certification | docs/reports/FINAL_CERTIFICATION_REPORT_2026-01-19.md | PASS |
| 2026-01-29 | Post-Change (Cascade Cleanup) | docs/audits/CONSTITUTIONAL_AUDIT_ATTESTATION_2026-01-29.md | PASS |

---

## Commands Reference

```bash
# Schema drift check
doppler run -- python scripts/ci/verify_schema_drift.py

# IMO compliance check
python scripts/ci/audit_imo_compliance.py

# Check for forbidden folders
find hubs -type d \( -name "utils" -o -name "helpers" -o -name "common" -o -name "shared" -o -name "lib" -o -name "misc" \) 2>/dev/null

# Verify Mermaid ERDs
grep -l "erDiagram" hubs/*/SCHEMA.md

# Check Neon authority declarations
grep -l "AUTHORITY.*Neon" hubs/*/SCHEMA.md

# List all ADRs
ls -la docs/adr/

# Alignment check
SELECT COUNT(*) FROM cl.company_identity WHERE outreach_id IS NOT NULL;
SELECT COUNT(*) FROM outreach.outreach;
```

---

## Traceability

| Document | Purpose |
|----------|---------|
| `templates/checklists/QUARTERLY_HYGIENE_AUDIT.md` | Quarterly audit checklist template |
| `templates/checklists/HUB_COMPLIANCE.md` | Hub compliance checklist template |
| `templates/audit/CONSTITUTIONAL_AUDIT_ATTESTATION.md` | Final attestation template |
| `doctrine/DO_NOT_MODIFY_REGISTRY.md` | Frozen components list |
| `docs/adr/ADR-015-quarterly-hygiene-process.md` | Quarterly audit ADR |

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-29 |
| Last Modified | 2026-01-29 |
| Version | 1.0.0 |
| Status | MANDATORY |
| Authority | CONSTITUTIONAL |
| Change Protocol | ADR + HUMAN APPROVAL REQUIRED |
