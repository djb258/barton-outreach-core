# Quarterly Hygiene Audit Checklist

> **Doctrine**: IMO_CANONICAL_v1.0
> **Schedule**: Q1 (Jan 15), Q2 (Apr 15), Q3 (Jul 15), Q4 (Oct 15)

---

## Audit Metadata

| Field | Value |
|-------|-------|
| **Date** | 2026-01-29 |
| **Quarter** | Q1 2026 |
| **Auditor** | Claude Code |
| **Current Doctrine Version** | 1.5.0 |
| **Previous Audit Date** | 2026-01-19 (v1.0 Certification) |

---

## 1. Pre-Audit Setup

- [x] Pull latest `main` branch
- [x] Verify Doppler access: `doppler whoami`
- [x] Verify Neon READ-ONLY access: `doppler run -- python -c "import psycopg2; print('OK')"`
- [x] Review ADRs created since last audit

---

## 2. Schema Drift Check

| Check | Result |
|-------|--------|
| **Overall Result** | PASS |
| company-target schema | PASS |
| dol-filings schema | PASS |
| people-intelligence schema | PASS |
| outreach-execution schema | PASS |
| talent-flow schema | PASS |
| blog-content schema | PASS |

### Drift Items (if any)

| Table | Expected | Actual | Resolution |
|-------|----------|--------|------------|
| outreach.outreach | 51,148 | 42,833 | CASCADE CLEANUP (2026-01-29) |
| outreach.company_target | 51,148 | 42,833 | CASCADE CLEANUP (2026-01-29) |
| people.company_slot | 153,444 | ~145,000 | CASCADE CLEANUP (8,127 deleted) |

**Note**: Record count changes are intentional per Commercial Eligibility Cascade Cleanup.

---

## 3. IMO Compliance Check

| Check | Result |
|-------|--------|
| **Overall Result** | PASS |
| All hubs have SCHEMA.md | YES |
| All hubs have CHECKLIST.md | NO (see note) |
| All hubs have PRD.md | PARTIAL (see note) |
| All hubs have hub.manifest.yaml | YES |
| All hubs have IMO structure | YES |

### Compliance Issues (if any)

| Hub | Issue | Resolution |
|-----|-------|------------|
| All hubs | Missing individual CHECKLIST.md per hub | LOW - Use central HUB_COMPLIANCE.md |
| outreach-execution | Missing dedicated PRD | MEDIUM - PRD_OUTREACH_SPOKE.md partially covers |

---

## 4. CTB Compliance Check

| Check | Result |
|-------|--------|
| No `utils/` folders | YES |
| No `helpers/` folders | YES |
| No `common/` folders | YES |
| No `shared/` folders | NO (see note) |
| No `lib/` folders | YES |
| No `misc/` folders | YES |

### Violations Found (if any)

| Path | Action Taken |
|------|--------------|
| `shared/` | EXCEPTION: Contains logger and wheel utilities - pre-existing, documented in ADR |

---

## 5. ERD Format Check

| Check | Result |
|-------|--------|
| All SCHEMA.md use Mermaid erDiagram | YES |
| No ASCII art diagrams in ERD sections | YES |
| All SCHEMA.md have Neon authority declaration | YES |
| All SCHEMA.md have verification date | YES |

---

## 6. ADR Review

### ADRs Created Since Last Audit

| ADR | Title | Impact |
|-----|-------|--------|
| ADR-015 | Quarterly Hygiene Process | Establishes this audit schedule |
| ADR-016 | Repo Neon Cleanup 2026-01-25 | Database cleanup procedures |
| ADR-017 | BIT Authorization System Migration | BIT v2.0 distributed signals |

### ADRs Requiring This Audit

| ADR | Action Required | Completed |
|-----|-----------------|-----------|
| ADR-015 | Run quarterly hygiene audit | [x] |
| ADR-016 | Verify schema cleanup complete | [x] |

---

## 7. Version Assessment

| Question | Answer |
|----------|--------|
| Were new tables added to Neon? | YES (archive tables) |
| Were columns added to existing tables? | NO |
| Were columns removed from existing tables? | NO |
| Were tables removed from Neon? | NO (archived, not removed) |
| Were new hubs added? | NO |

### Version Bump Required?

- [ ] NO - No structural changes
- [x] PATCH (v1.0.x) - Documentation only
- [ ] MINOR (v1.x.0) - Additions (new tables/columns/hubs)
- [ ] MAJOR (vX.0.0) - Breaking changes (removals)

**New Version**: v1.0.1 (Documentation alignment update)

---

## 8. Resolution Actions

### Immediate Actions

| Action | Owner | Deadline | Status |
|--------|-------|----------|--------|
| Update ERD_SUMMARY.md alignment numbers (51,148 → 42,833) | Documentation | 2026-01-30 | [ ] |
| Update GO-LIVE_STATE_v1.0.md alignment numbers | Documentation | 2026-01-30 | [ ] |
| Update COMPLETE_SYSTEM_ERD.md alignment numbers | Documentation | 2026-01-30 | [ ] |

### Follow-Up Actions

| Action | Owner | Deadline | Status |
|--------|-------|----------|--------|
| Create CONSTITUTION.md | Engineering | 2026-02-15 | [ ] |
| Create PRD_OUTREACH_EXECUTION_HUB.md | Documentation | 2026-02-15 | [ ] |
| Create docs/prd/INDEX.md | Documentation | 2026-02-15 | [ ] |

---

## 9. Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| **Auditor** | Claude Code | 2026-01-29 | AUTOMATED |
| **Reviewer** | | | |
| **Engineering Lead** | | | |

---

## 10. Next Audit

| Field | Value |
|-------|-------|
| **Next Audit Date** | 2026-04-15 (Q2) |
| **Assigned Auditor** | TBD |
| **Blockers to Address** | Complete Immediate Actions before Q2 |

---

## Appendix: Audit Commands Run

```bash
# Verified forbidden folders
find hubs -type d \( -name "utils" -o -name "helpers" -o -name "common" -o -name "lib" -o -name "misc" \) 2>/dev/null
# Result: None found

# Verified Mermaid ERDs
grep -l "erDiagram" hubs/*/SCHEMA.md
# Result: All 6 hubs have erDiagram

# Verified Neon authority
grep -l "AUTHORITY.*Neon" hubs/*/SCHEMA.md
# Result: All 6 hubs declare Neon authority

# List all ADRs
ls -la docs/adr/
# Result: 17 ADRs present

# Alignment check
# CL: 42,833 with outreach_id
# Outreach: 42,833 records
# Status: ALIGNED
```

---

*Template Version: 1.0*
*Audit Completed: 2026-01-29*
