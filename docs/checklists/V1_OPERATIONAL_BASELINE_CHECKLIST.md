# v1.0 Operational Baseline Deployment Checklist

## Document Info

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Date** | 2026-01-20 |
| **Author** | IMO-Creator |
| **Status** | CERTIFIED |

---

## Pre-Deployment Validation

### Infrastructure

- [x] `outreach.hub_registry` table exists with 6 hubs
- [x] `outreach.company_hub_status` table exists and has data (135,684 rows)
- [x] `outreach.manual_overrides` table exists with RLS enabled
- [x] `outreach.vw_sovereign_completion` view exists and returns data
- [x] `outreach.vw_marketing_eligibility` view exists
- [x] `outreach.vw_marketing_eligibility_with_overrides` view exists (authoritative)

### Hub Registry

- [x] company-target registered (waterfall order 1, gates_completion=true)
- [x] dol-filings registered (waterfall order 2, gates_completion=true)
- [x] people-intelligence registered (waterfall order 3, gates_completion=true)
- [x] talent-flow registered (waterfall order 4, gates_completion=true)
- [x] blog-content registered (waterfall order 5, gates_completion=false)
- [x] outreach-execution registered (waterfall order 6, gates_completion=false)

### Doctrine Compliance

- [x] Required hubs in correct waterfall order
- [x] No false COMPLETE status entries
- [x] BIT is gate, not hub (BIT hub entries: 0)
- [x] Tier 3 requires COMPLETE + BIT >= 50
- [x] BLOCKED companies are Tier -1

### Data Integrity

- [x] company_target count matches vw_sovereign_completion
- [x] No NULL company_unique_id in hub status
- [x] All hub_ids reference valid hubs
- [x] Tier distribution is reasonable
- [x] No ghost PASS entries

### Operational Safety

- [x] Kill switch table has required columns
- [x] Override view has effective_tier and computed_tier
- [x] Error tables exist for failure routing (4/4)
- [x] RLS enabled on manual_overrides
- [x] Override audit log exists

---

## Migration Checklist

### SQL Migrations

- [x] 2026-01-19-kill-switches.sql - Kill switch system
- [x] 2026-01-20-tier-telemetry-views.sql - Tier telemetry views
- [x] 2026-01-20-send-attempt-audit.sql - Append-only audit table

### Python Components

- [x] `hubs/outreach-execution/imo/middle/marketing_safety_gate.py` - Safety gate
- [x] `hubs/people-intelligence/imo/middle/hub_status.py` - People hub status
- [x] `hubs/blog-content/imo/middle/hub_status.py` - Blog hub status
- [x] `hubs/talent-flow/imo/middle/hub_status.py` - Talent flow hub status
- [x] `ops/metrics/tier_snapshot.py` - Daily snapshot job
- [x] `ops/metrics/tier_report.py` - Markdown report generator
- [x] Analytics module (consolidated into `ops/metrics/`)

---

## Documentation Checklist

### ADRs

- [x] ADR-006: Sovereign Completion Infrastructure
- [x] ADR-007: Kill Switch System
- [x] ADR-008: v1.0 Operational Baseline
- [x] ADR-009: Tier Telemetry Analytics
- [x] ADR-010: Marketing Safety Gate

### PRDs

- [x] PRD_SOVEREIGN_COMPLETION.md updated with v1.0 status
- [x] PRD_KILL_SWITCH_SYSTEM.md exists

### GO-LIVE Documentation

- [x] docs/GO-LIVE_STATE_v1.0.md created
- [x] doctrine/DO_NOT_MODIFY_REGISTRY.md created
- [x] CLAUDE.md updated with v1.0 baseline info
- [x] doctrine/README.md updated with v1.0 status

### DO NOT MODIFY Banners

- [x] Banner added to 2026-01-19-kill-switches.sql
- [x] Banner added to 2026-01-20-tier-telemetry-views.sql
- [x] Banner added to 2026-01-20-send-attempt-audit.sql
- [x] Banner added to marketing_safety_gate.py

---

## Post-Deployment Verification

### Smoke Tests

- [ ] Query vw_marketing_eligibility_with_overrides returns data
- [ ] Query vw_tier_distribution returns tier counts
- [ ] Kill switch insert creates audit log entry
- [ ] Safety gate blocks tier -1 company

### Operational Readiness

- [ ] Daily snapshot job scheduled (00:00 UTC)
- [ ] Tier report generation tested
- [ ] Kill switch activation tested
- [ ] Audit trail verified

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Data Validation Agent | Agent A | 2026-01-19 | PASS |
| Infrastructure Migration Agent | Agent B | 2026-01-19 | PASS |
| Final Certification Agent | Agent C | 2026-01-19 | PASS |
| Sub-Hub Hardening Agent | - | 2026-01-20 | PASS |
| Safety Auditor Agent | - | 2026-01-20 | PASS |
| Tier Telemetry Agent | - | 2026-01-20 | PASS |
| Doctrine Freeze Agent | - | 2026-01-20 | PASS |

---

## Certification

**FINAL STATUS**: CERTIFIED

**Safe to Enable Live Marketing**: YES

**Baseline Freeze Date**: 2026-01-20

---

## References

- docs/reports/FINAL_CERTIFICATION_REPORT_2026-01-19.md
- docs/GO-LIVE_STATE_v1.0.md
- doctrine/DO_NOT_MODIFY_REGISTRY.md
