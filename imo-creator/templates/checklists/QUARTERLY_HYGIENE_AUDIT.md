# Quarterly Hygiene Audit Checklist

> **Doctrine**: IMO_CANONICAL_v1.0
> **Schedule**: Q1 (Jan 15), Q2 (Apr 15), Q3 (Jul 15), Q4 (Oct 15)

---

## Audit Metadata

| Field | Value |
|-------|-------|
| **Date** | _________________ |
| **Quarter** | Q__ 20__ |
| **Auditor** | _________________ |
| **Current Doctrine Version** | _________________ |
| **Previous Audit Date** | _________________ |

---

## 1. Pre-Audit Setup

- [ ] Pull latest `main` branch
- [ ] Verify Doppler access: `doppler whoami`
- [ ] Verify Neon READ-ONLY access: `doppler run -- python -c "import psycopg2; print('OK')"`
- [ ] Review ADRs created since last audit

---

## 2. Schema Drift Check

```bash
doppler run -- python scripts/ci/verify_schema_drift.py
```

| Check | Result |
|-------|--------|
| **Overall Result** | PASS / FAIL |
| company-target schema | PASS / FAIL |
| dol-filings schema | PASS / FAIL |
| people-intelligence schema | PASS / FAIL |
| outreach-execution schema | PASS / FAIL |
| talent-flow schema | PASS / FAIL |

### Drift Items (if any)

| Table | Expected | Actual | Resolution |
|-------|----------|--------|------------|
| | | | |
| | | | |

---

## 3. IMO Compliance Check

```bash
python scripts/ci/audit_imo_compliance.py
```

| Check | Result |
|-------|--------|
| **Overall Result** | PASS / FAIL |
| All hubs have SCHEMA.md | YES / NO |
| All hubs have CHECKLIST.md | YES / NO |
| All hubs have PRD.md | YES / NO |
| All hubs have hub.manifest.yaml | YES / NO |
| All hubs have IMO structure | YES / NO |

### Compliance Issues (if any)

| Hub | Issue | Resolution |
|-----|-------|------------|
| | | |
| | | |

---

## 4. CTB Compliance Check

| Check | Result |
|-------|--------|
| No `utils/` folders | YES / NO |
| No `helpers/` folders | YES / NO |
| No `common/` folders | YES / NO |
| No `shared/` folders | YES / NO |
| No `lib/` folders | YES / NO |
| No `misc/` folders | YES / NO |

### Violations Found (if any)

| Path | Action Taken |
|------|--------------|
| | |

---

## 5. ERD Format Check

| Check | Result |
|-------|--------|
| All SCHEMA.md use Mermaid erDiagram | YES / NO |
| No ASCII art diagrams in ERD sections | YES / NO |
| All SCHEMA.md have Neon authority declaration | YES / NO |
| All SCHEMA.md have verification date | YES / NO |

---

## 6. ADR Review

### ADRs Created Since Last Audit

| ADR | Title | Impact |
|-----|-------|--------|
| ADR-___ | | |
| ADR-___ | | |

### ADRs Requiring This Audit

| ADR | Action Required | Completed |
|-----|-----------------|-----------|
| | | [ ] |
| | | [ ] |

---

## 7. Version Assessment

| Question | Answer |
|----------|--------|
| Were new tables added to Neon? | YES / NO |
| Were columns added to existing tables? | YES / NO |
| Were columns removed from existing tables? | YES / NO |
| Were tables removed from Neon? | YES / NO |
| Were new hubs added? | YES / NO |

### Version Bump Required?

- [ ] NO - No structural changes
- [ ] PATCH (v1.0.x) - Documentation only
- [ ] MINOR (v1.x.0) - Additions (new tables/columns/hubs)
- [ ] MAJOR (vX.0.0) - Breaking changes (removals)

**New Version**: _________________

---

## 8. Resolution Actions

### Immediate Actions

| Action | Owner | Deadline | Status |
|--------|-------|----------|--------|
| | | | [ ] |
| | | | [ ] |

### Follow-Up Actions

| Action | Owner | Deadline | Status |
|--------|-------|----------|--------|
| | | | [ ] |
| | | | [ ] |

---

## 9. Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| **Auditor** | | | |
| **Reviewer** | | | |
| **Engineering Lead** | | | |

---

## 10. Next Audit

| Field | Value |
|-------|-------|
| **Next Audit Date** | _________________ |
| **Assigned Auditor** | _________________ |
| **Blockers to Address** | _________________ |

---

## Appendix: Audit Commands

```bash
# Full audit suite
doppler run -- python scripts/ci/verify_schema_drift.py && \
python scripts/ci/audit_imo_compliance.py

# Check for forbidden folders
find hubs -type d \( -name "utils" -o -name "helpers" -o -name "common" -o -name "shared" -o -name "lib" -o -name "misc" \) 2>/dev/null

# Verify Mermaid ERDs
grep -l "erDiagram" hubs/*/SCHEMA.md

# Check Neon authority
grep -l "AUTHORITY.*Neon" hubs/*/SCHEMA.md

# List all ADRs
ls -la docs/adr/

# Show current tag
git tag -l "IMO_CANONICAL*" | tail -1
```

---

*Template Version: 1.0*
*Last Updated: 2026-01-25*
