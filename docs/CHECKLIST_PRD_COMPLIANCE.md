# PRD Compliance Checklist

**Version:** 3.0 (Spine-First Architecture)
**Last Updated:** 2026-01-07

---

## PRD Inventory

### Hub PRDs

| PRD | File | Status | Last Updated |
|-----|------|--------|--------------|
| Company Target (IMO) | `docs/prd/PRD_COMPANY_HUB.md` | ✅ Current (v3.0) | 2026-01-07 |
| ~~Company Pipeline~~ | ~~`docs/prd/PRD_COMPANY_HUB_PIPELINE.md`~~ | **DEPRECATED** | See v3.0 |
| BIT Engine | `docs/prd/PRD_BIT_ENGINE.md` | ✅ Current | 2025-12-19 |
| Master Error Log | `docs/prd/PRD_MASTER_ERROR_LOG.md` | ✅ Current | 2025-12-17 |

> **v3.0 Note:** Company Target is now a single-pass IMO gate. Phase 1/1b removed (moved to CL).

### Spoke PRDs

| PRD | File | Status | Last Updated |
|-----|------|--------|--------------|
| People Sub-Hub | `docs/prd/PRD_PEOPLE_SUBHUB.md` | ✅ Current | 2025-12-17 |
| DOL Sub-Hub | `docs/prd/PRD_DOL_SUBHUB.md` | ✅ Current | 2025-12-17 |
| Blog/News Sub-Hub | `docs/prd/PRD_BLOG_NEWS_SUBHUB.md` | ✅ Current | 2025-12-17 |
| Talent Flow Spoke | `docs/prd/PRD_TALENT_FLOW_SPOKE.md` | ✅ Current | 2025-12-19 |
| Outreach Spoke | `docs/prd/PRD_OUTREACH_SPOKE.md` | ✅ Current | 2025-12-19 |

---

## PRD Standards Compliance

### Every PRD Must Include:

- [ ] **Version Number** - v2.1 format
- [ ] **Status** - Active/Draft/Deprecated
- [ ] **Hardening Date** - When doctrine-aligned
- [ ] **Last Updated** - Date of last modification
- [ ] **Doctrine Reference** - Bicycle Wheel v1.1 / Barton Doctrine
- [ ] **Barton ID Range** - `04.04.02.04.XXXXX.###`

### Ownership Statement

- [ ] **OWNS** section - What this component is responsible for
- [ ] **DOES NOT OWN** section - What belongs to other components
- [ ] **PREREQUISITE** statement - What must exist before processing

### Technical Sections

- [ ] **Purpose** - Core functions and goals
- [ ] **Data Flow** - ASCII diagram of data movement
- [ ] **Correlation ID Doctrine** - Hard law for tracing
- [ ] **Signal Idempotency** - Deduplication rules
- [ ] **Kill Switches** - Safety thresholds
- [ ] **Implementation Status** - Component completion table
- [ ] **Dependencies** - What this component needs
- [ ] **Metrics & KPIs** - Success measurements

---

## Doctrine Enforcement Checklist

### Correlation ID (HARD LAW)

For each PRD, verify:

- [ ] correlation_id is REQUIRED parameter in main process()
- [ ] correlation_id is propagated to ALL downstream calls
- [ ] correlation_id is included in ALL error logs
- [ ] correlation_id is included in ALL emitted signals
- [ ] correlation_id is NEVER modified mid-processing

### Hub Gate (HARD LAW) — v3.0 Spine-First

For each PRD, verify:

- [ ] `outreach_id` validation before processing (NOT `company_id`)
- [ ] Domain loaded from spine (NOT from CL directly)
- [ ] `sovereign_id` NEVER referenced in sub-hubs
- [ ] Clear STOP conditions documented (terminal failure = no retry)

### Signal Deduplication

For each PRD, verify:

- [ ] Deduplication window defined (24h operational, 365d structural)
- [ ] Dedup key components listed
- [ ] should_emit_signal() check before emission

---

## PRD Review Schedule

| PRD | Next Review | Reviewer |
|-----|-------------|----------|
| PRD_COMPANY_HUB | 2026-01-17 | TBD |
| PRD_COMPANY_HUB_PIPELINE | 2026-01-17 | TBD |
| PRD_BIT_ENGINE | 2026-01-19 | TBD |
| PRD_PEOPLE_SUBHUB | 2026-01-17 | TBD |
| PRD_DOL_SUBHUB | 2026-01-17 | TBD |
| PRD_BLOG_NEWS_SUBHUB | 2026-01-17 | TBD |
| PRD_TALENT_FLOW_SPOKE | 2026-01-19 | TBD |
| PRD_OUTREACH_SPOKE | 2026-01-19 | TBD |
| PRD_MASTER_ERROR_LOG | 2026-01-17 | TBD |

---

## Missing PRDs

| Component | Status | Priority |
|-----------|--------|----------|
| N8N Integration | Not Created | Low |
| External API Integrations | Not Created | Medium |
| Campaign Templates | Not Created | Medium |

---

## ADR Inventory

| ADR | File | Status |
|-----|------|--------|
| ADR-001: Hub-Spoke Architecture | `docs/adr/ADR-001_Hub_Spoke_Architecture.md` | ✅ Accepted (updated v3.0) |
| ADR-CT-IMO-001: Company Target as IMO Gate | `docs/adr/ADR-CT-IMO-001.md` | ✅ Accepted |

### Pending ADRs

| Decision | Status | Priority |
|----------|--------|----------|
| Signal Weighting Strategy | Pending | Medium |
| Cache Invalidation Policy | Pending | Low |
| ~~External API Selection~~ | **RESOLVED** | See SNAP_ON_TOOLBOX.yaml |

---

## Checklist Inventory

| Checklist | File | Status |
|-----------|------|--------|
| Deployment | `docs/CHECKLIST_DEPLOYMENT.md` | ✅ Current |
| PRD Compliance | `docs/CHECKLIST_PRD_COMPLIANCE.md` | ✅ Current |

---

## Sign-Off

| Role | Name | Date |
|------|------|------|
| Documentation Owner | Claude Code | 2025-12-19 |
| Reviewer | | |

---

**Last Updated:** 2025-12-19
**Author:** Claude Code
