# Hub-Process-Signal Ownership Matrix v3.0

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | IMO-Creator v1.0 |
| **Domain Spec Reference** | `doctrine/REPO_DOMAIN_SPEC.md` |
| **CC Layer** | CC-02 (Hub Governance) |
| **PRD Constitution** | `templates/doctrine/PRD_CONSTITUTION.md` |
| **CTB Governance** | `docs/CTB_GOVERNANCE.md` |
| **Document Type** | Governance Reference (NOT a Hub PRD) |

---

## 1. Sovereign Reference (CC-01)

| Field | Value |
|-------|-------|
| **Sovereign ID** | CL-01 (Company Lifecycle) |
| **Sovereign Boundary** | Company identity and lifecycle state |

---

## 2. Document Identity

| Field | Value |
|-------|-------|
| **Document Name** | Hub-Process-Signal Ownership Matrix |
| **Document ID** | DOC-HUB-SIGNAL-MATRIX |
| **Owner** | Barton Outreach Core |
| **Version** | 3.0.0 |
| **Type** | Governance Reference Document |

---

## 3. Purpose

This document serves as the **authoritative reference** for:
- Hub and sub-hub ownership boundaries
- Process-to-hub assignments
- Signal emission and routing
- Decision authority matrix
- Correlation ID and idempotency governance

**This is NOT a hub PRD** — it documents how hubs interact and enforce boundaries.

---

## 4. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-17 | Initial Hub-Process-Signal Matrix |
| 2.1 | 2025-12-17 | Hardened: Correlation ID enforcement, Signal idempotency matrix, PRD v2.1 alignment |
| 3.0 | 2026-01-29 | Constitutional compliance: Conformance sections, doctrine references |

---

## 5. Quick Reference: Who Owns What

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    HUB-AND-SPOKE OWNERSHIP SUMMARY                            ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   COMPANY HUB (Master Node)                                                   ║
║   ├── OWNS: Identity, Domain, Pattern, BIT Engine, Outreach Decisions        ║
║   ├── Phases 1-4 (Company Identity Pipeline)                                 ║
║   └── Signal Type: DECISION                                                   ║
║                                                                               ║
║   PEOPLE SUB-HUB (Spoke #1)                                                   ║
║   ├── OWNS: People Lifecycle, Email Generation, Slots, Talent Flow           ║
║   ├── Phases 0, 5-8 (People Pipeline)                                        ║
║   └── Signal Type: EMISSION (to BIT Engine)                                  ║
║                                                                               ║
║   DOL SUB-HUB (Spoke #2)                                                      ║
║   ├── OWNS: Form 5500, Schedule A, EIN Matching, Broker Change               ║
║   ├── DOL Node Spoke                                                          ║
║   └── Signal Type: EMISSION (to BIT Engine)                                  ║
║                                                                               ║
║   BLOG/NEWS SUB-HUB (Spoke #3) - PLANNED                                      ║
║   ├── OWNS: News Ingestion, Event Detection, Sentiment Analysis              ║
║   ├── Blog Node Spoke                                                         ║
║   └── Signal Type: EMISSION (to BIT Engine)                                  ║
║                                                                               ║
║   OUTREACH NODE (Execution)                                                   ║
║   ├── OWNS: Campaign Execution ONLY                                          ║
║   ├── BIT-Gated (requires score >= 50)                                       ║
║   └── Signal Type: NONE (executes decisions only)                            ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## Correlation ID Enforcement (Global)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                   GLOBAL CORRELATION ID DOCTRINE                              ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   EVERY hub and sub-hub MUST enforce correlation_id (UUID v4):               ║
║                                                                               ║
║   1. Company Hub Pipeline:                                                    ║
║      └── Generated ONCE at batch intake                                      ║
║      └── Propagated through Phases 1-4 and into People Pipeline             ║
║                                                                               ║
║   2. People Sub-Hub:                                                          ║
║      └── Inherits correlation_id from Company Hub Pipeline                   ║
║      └── Propagates through Phases 0, 5-8                                    ║
║      └── Includes in ALL signals emitted to BIT Engine                       ║
║                                                                               ║
║   3. DOL Sub-Hub:                                                             ║
║      └── Generated at filing ingest (one per Form 5500)                      ║
║      └── Includes in ALL signals emitted to BIT Engine                       ║
║                                                                               ║
║   4. Blog/News Sub-Hub:                                                       ║
║      └── Generated at article ingest (one per article)                       ║
║      └── Includes in ALL signals emitted to BIT Engine                       ║
║                                                                               ║
║   RULES:                                                                      ║
║   • Every signal MUST include correlation_id                                  ║
║   • Every error log MUST include correlation_id                              ║
║   • correlation_id MUST NOT be modified after generation                      ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## Signal Idempotency Matrix

| Source Hub | Signal Type | Dedup Key | Window |
|------------|-------------|-----------|--------|
| People Sub-Hub | SLOT_FILLED | `(company_id, slot_type, person_id)` | 24 hours |
| People Sub-Hub | SLOT_VACATED | `(company_id, slot_type, person_id)` | 24 hours |
| People Sub-Hub | EMAIL_VERIFIED | `(person_id, email)` | 24 hours |
| People Sub-Hub | EXECUTIVE_JOINED | `(company_id, person_id)` | 24 hours |
| People Sub-Hub | EXECUTIVE_LEFT | `(company_id, person_id)` | 24 hours |
| DOL Sub-Hub | FORM_5500_FILED | `(company_id, filing_id)` | 365 days |
| DOL Sub-Hub | LARGE_PLAN | `(company_id, filing_id)` | 365 days |
| DOL Sub-Hub | BROKER_CHANGE | `(company_id, filing_id)` | 365 days |
| Blog Sub-Hub | FUNDING_EVENT | `(company_id, article_id)` | 30 days |
| Blog Sub-Hub | ACQUISITION | `(company_id, article_id)` | 30 days |
| Blog Sub-Hub | LEADERSHIP_CHANGE | `(company_id, article_id)` | 30 days |
| Blog Sub-Hub | LAYOFF | `(company_id, article_id)` | 30 days |

---

## 1. Process Ownership by Hub

### Company Hub (Master) — Phases 1-4

| Process ID | Process Name | File | Signal Type |
|------------|--------------|------|-------------|
| Phase 1 | Company Matching | `phases/phase1_company_matching.py` | Identity |
| Phase 1b | Unmatched Hold Export | `phases/phase1b_unmatched_hold.py` | Identity |
| Phase 2 | Domain Resolution | `phases/phase2_domain_resolution.py` | Identity |
| Phase 3 | Email Pattern Waterfall | `phases/phase3_email_pattern_waterfall.py` | Identity |
| Phase 4 | Pattern Verification | `phases/phase4_pattern_verification.py` | Identity |
| BIT Engine | Signal Aggregation | `hub/bit_engine.py` | Decision |
| Movement | State Machine | `movement_engine/state_machine.py` | Decision |
| Movement | Movement Rules | `movement_engine/movement_rules.py` | Decision |

### People Sub-Hub — Phases 0, 5-8

| Process ID | Process Name | File | Signal Type |
|------------|--------------|------|-------------|
| Phase 0 | People Ingest | `phases/phase0_people_ingest.py` | Signal |
| Phase 5 | Email Generation | `phases/phase5_email_generation.py` | Signal |
| Phase 6 | Slot Assignment | `phases/phase6_slot_assignment.py` | Signal |
| Phase 7 | Enrichment Queue | `phases/phase7_enrichment_queue.py` | Signal |
| Phase 8 | Output Writer | `phases/phase8_output_writer.py` | Signal |
| Talent Flow | Company Gate | `phases/talentflow_phase0_company_gate.py` | Signal |

### DOL Sub-Hub — DOL Node

| Process ID | Process Name | File | Signal Type |
|------------|--------------|------|-------------|
| DOL-Match | EIN Matching | `spokes/dol_node/dol_node_spoke.py` | Signal |
| DOL-5500 | Form 5500 Processing | `spokes/dol_node/dol_node_spoke.py` | Signal |
| DOL-SchA | Schedule A Processing | `spokes/dol_node/dol_node_spoke.py` | Signal |

### Blog/News Sub-Hub (PLANNED) — Blog Node

| Process ID | Process Name | File | Signal Type |
|------------|--------------|------|-------------|
| BLOG-Ingest | News Ingestion | `spokes/blog_node/blog_node_spoke.py` | Signal |
| BLOG-Detect | Event Detection | `spokes/blog_node/blog_node_spoke.py` | Signal |
| BLOG-Match | Entity Matching | `spokes/blog_node/blog_node_spoke.py` | Signal |

### Outreach Node (Execution Only)

| Process ID | Process Name | File | Signal Type |
|------------|--------------|------|-------------|
| OUT-Promote | Promotion to Log | `toolbox-hub/backend/outreach/promote_to_log.py` | Execution |

---

## 2. Signal Emission Matrix

### Signals Emitted by Source

| Signal Type | Enum | Impact | Source Hub | Target |
|-------------|------|--------|------------|--------|
| `SLOT_FILLED` | `SignalType.SLOT_FILLED` | +10.0 | People Sub-Hub | BIT Engine |
| `SLOT_VACATED` | `SignalType.SLOT_VACATED` | -5.0 | People Sub-Hub | BIT Engine |
| `EMAIL_VERIFIED` | `SignalType.EMAIL_VERIFIED` | +3.0 | People Sub-Hub | BIT Engine |
| `LINKEDIN_FOUND` | `SignalType.LINKEDIN_FOUND` | +2.0 | People Sub-Hub | BIT Engine |
| `EXECUTIVE_JOINED` | `SignalType.EXECUTIVE_JOINED` | +10.0 | People Sub-Hub | BIT Engine |
| `EXECUTIVE_LEFT` | `SignalType.EXECUTIVE_LEFT` | -5.0 | People Sub-Hub | BIT Engine |
| `TITLE_CHANGE` | `SignalType.TITLE_CHANGE` | +3.0 | People Sub-Hub | BIT Engine |
| `FORM_5500_FILED` | `SignalType.FORM_5500_FILED` | +5.0 | DOL Sub-Hub | BIT Engine |
| `LARGE_PLAN` | `SignalType.LARGE_PLAN` | +8.0 | DOL Sub-Hub | BIT Engine |
| `BROKER_CHANGE` | `SignalType.BROKER_CHANGE` | +7.0 | DOL Sub-Hub | BIT Engine |
| `FUNDING_EVENT` | `SignalType.FUNDING_EVENT` | +15.0 | Blog Sub-Hub | BIT Engine |
| `ACQUISITION` | `SignalType.ACQUISITION` | +12.0 | Blog Sub-Hub | BIT Engine |
| `LEADERSHIP_CHANGE` | `SignalType.LEADERSHIP_CHANGE` | +8.0 | Blog Sub-Hub | BIT Engine |
| `LAYOFF` | `SignalType.LAYOFF` | -3.0 | Blog Sub-Hub | BIT Engine |

### Signal Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SIGNAL AGGREGATION FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

    PEOPLE SUB-HUB              DOL SUB-HUB              BLOG SUB-HUB
    (Phases 0, 5-8)             (DOL Node)               (PLANNED)

    ┌───────────────┐        ┌───────────────┐        ┌───────────────┐
    │ Signals:      │        │ Signals:      │        │ Signals:      │
    │ +10 SLOT_FILL │        │ +5 5500_FILED │        │ +15 FUNDING   │
    │ -5 SLOT_VAC   │        │ +8 LARGE_PLAN │        │ +12 ACQUISITION│
    │ +3 EMAIL_VER  │        │ +7 BROKER_CHG │        │ +8 LEADERSHIP │
    │ +10 EXEC_JOIN │        │               │        │ -3 LAYOFF     │
    │ -5 EXEC_LEFT  │        │               │        │               │
    │ +3 TITLE_CHG  │        │               │        │               │
    └───────┬───────┘        └───────┬───────┘        └───────┬───────┘
            │                        │                        │
            └────────────────────────┼────────────────────────┘
                                     │
                                     ▼
                    ╔═══════════════════════════════════════╗
                    ║           COMPANY HUB                  ║
                    ║                                        ║
                    ║  ┌──────────────────────────────────┐ ║
                    ║  │         BIT ENGINE               │ ║
                    ║  │                                  │ ║
                    ║  │  Aggregate → Score → Decide      │ ║
                    ║  │                                  │ ║
                    ║  │  Hot >= 75:  Immediate Outreach  │ ║
                    ║  │  Warm 50-74: Nurture Sequence    │ ║
                    ║  │  Cold < 50:  No Outreach         │ ║
                    ║  └──────────────────────────────────┘ ║
                    ╚═══════════════════════════════════════╝
                                     │
                                     │ (BIT Decision: score >= 50)
                                     │
                                     ▼
                    ┌───────────────────────────────────────┐
                    │          OUTREACH NODE                │
                    │         (Execution Only)              │
                    │                                       │
                    │  • Campaign enrollment                │
                    │  • Sequence assignment                │
                    │  • Send scheduling                    │
                    └───────────────────────────────────────┘
```

---

## 3. Decision Authority Matrix

| Decision Type | Authority | Rationale |
|---------------|-----------|-----------|
| Who gets messaged | BIT Engine (Company Hub) | Only BIT aggregates all signals |
| When they get messaged | BIT Engine (Company Hub) | Timing based on score thresholds |
| What campaign they enter | BIT Engine (Company Hub) | Campaign selection by score/signals |
| Company identity creation | Company Hub | Central identity authority |
| Email pattern discovery | Company Hub | Pattern applies to company, not person |
| Domain validation | Company Hub | Domain is company attribute |
| Person state initialization | People Sub-Hub | Lifecycle is person attribute |
| Slot assignment | People Sub-Hub | Slots are person-to-company links |
| Form 5500 matching | DOL Sub-Hub | EIN matching is DOL domain |
| News event detection | Blog Sub-Hub | Event detection is news domain |

---

## 4. What Each Hub CANNOT Do

### Company Hub CANNOT:

- Initialize people lifecycle states (People Sub-Hub)
- Generate emails for individuals (People Sub-Hub)
- Assign slots (People Sub-Hub)
- Process Form 5500 filings (DOL Sub-Hub)
- Detect news events (Blog Sub-Hub)

### People Sub-Hub CANNOT:

- Create company identity (Company Hub)
- Discover email patterns (Company Hub)
- Validate domains (Company Hub)
- Make outreach decisions (BIT Engine in Company Hub)
- Execute campaigns (Outreach Node)

### DOL Sub-Hub CANNOT:

- Create company identity (Company Hub)
- Match without EIN (must use Company Hub)
- Make outreach decisions (BIT Engine)
- Process people lifecycle (People Sub-Hub)

### Blog/News Sub-Hub CANNOT:

- Create company identity (Company Hub)
- Make outreach decisions (BIT Engine)
- Process people lifecycle (People Sub-Hub)
- Process DOL filings (DOL Sub-Hub)

### Outreach Node CANNOT:

- Execute without BIT approval (must have score >= 50)
- Make targeting decisions (BIT Engine decides)
- Create signals (spokes create signals)
- Bypass BIT score check

---

## 5. PRD Cross-Reference

| Hub/Sub-Hub | PRD Document | Version | Status |
|-------------|--------------|---------|--------|
| Company Hub | `docs/prd/PRD_COMPANY_HUB.md` | v2.1 | Active |
| People Sub-Hub | `docs/prd/PRD_PEOPLE_SUBHUB.md` | v2.1 | Active |
| DOL Sub-Hub | `docs/prd/PRD_DOL_SUBHUB.md` | v2.1 | Active |
| Blog/News Sub-Hub | `docs/prd/PRD_BLOG_NEWS_SUBHUB.md` | v2.1 | Planned |
| Pipeline Overview | `docs/prd/PRD_COMPANY_HUB_PIPELINE.md` | v2.1 | Active |

### Cross-Cutting Processes

| Process | PRD Document | Version | Status |
|---------|--------------|---------|--------|
| Master Error Log | `docs/prd/PRD_MASTER_ERROR_LOG.md` | v1.0 | Active |

### PRD v2.1 Hardening Features (All PRDs)

| Feature | Description |
|---------|-------------|
| Correlation ID | UUID v4 propagated through all phases, signals, errors |
| Signal Idempotency | Deduplication windows per sub-hub (24h/30d/365d) |
| Two-Layer Errors | Local remediation + Global visibility (shq_master_error_log) |
| Tooling Declarations | Tools, cost tiers, rate limits, cache policies |
| Promotion States | Burn-in → Steady-state with explicit gates |
| Error Code Standards | Hub-specific prefixes (PSH-, DOL-, BLOG-, PIPE-) |
| Process ID Standard | Format: `hub.subhub.pipeline.phase` (per PRD_MASTER_ERROR_LOG) |

---

## 6. Phase Execution Order

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PIPELINE EXECUTION ORDER                               │
└─────────────────────────────────────────────────────────────────────────────┘

    COMPANY HUB FIRST (Phases 1-4)
    ════════════════════════════════════════════════════════════════════
    Phase 1:  Company Matching (GOLD/SILVER/BRONZE)
              ↓
    Phase 1b: Unmatched Hold Export
              ↓
    Phase 2:  Domain Resolution
              ↓
    Phase 3:  Email Pattern Waterfall (Tier 0 → 1 → 2)
              ↓
    Phase 4:  Pattern Verification
              ↓
              ↓ company_id, domain, email_pattern
              ↓
    ════════════════════════════════════════════════════════════════════

    PEOPLE SUB-HUB SECOND (Phases 0, 5-8)
    ════════════════════════════════════════════════════════════════════
    Phase 0:  People Ingest (Classification)
              ↓
    Phase 5:  Email Generation (Uses patterns from Phase 4)
              ↓
    Phase 6:  Slot Assignment
              ↓
    Phase 7:  Enrichment Queue
              ↓
    Phase 8:  Output Writer
              ↓
              ↓ SIGNALS → BIT ENGINE
              ↓
    ════════════════════════════════════════════════════════════════════

    BIT ENGINE (Aggregation)
    ════════════════════════════════════════════════════════════════════
    Aggregate:  All signals from all sub-hubs
                ↓
    Calculate:  BIT Score (0-100)
                ↓
    Decide:     Hot/Warm/Cold classification
                ↓
                ↓ Score >= 50
                ↓
    ════════════════════════════════════════════════════════════════════

    OUTREACH NODE (Execution)
    ════════════════════════════════════════════════════════════════════
    Execute:    Campaign enrollment
                Sequence assignment
                Send scheduling
    ════════════════════════════════════════════════════════════════════
```

---

## 7. Enforcement Checklist (v2.1)

### For Any New Process

- [ ] Does it have a clear hub owner?
- [ ] Is the hub owner documented in the file header?
- [ ] Does it require company_id as a prerequisite?
- [ ] Does it emit signals (not decisions) if it's a sub-hub?
- [ ] Does it respect the Company-First doctrine?
- [ ] Does it have kill switches?
- [ ] Does it log to standard observability?
- [ ] **v2.1:** Does it propagate correlation_id (UUID v4)?
- [ ] **v2.1:** Does it log errors to BOTH local table AND shq_error_log?
- [ ] **v2.1:** Does it have defined error codes (HUB-XXX format)?

### For Sub-Hub Processes (v2.1 Requirements)

- [ ] Does it ONLY emit signals to BIT Engine?
- [ ] Does it NEVER make outreach decisions?
- [ ] Does it NEVER create company identity?
- [ ] Does it request identity from Company Hub when needed?
- [ ] **v2.1:** Does every signal include correlation_id?
- [ ] **v2.1:** Does it implement signal idempotency with dedup window?
- [ ] **v2.1:** Does it declare tools, cost tiers, and rate limits?
- [ ] **v2.1:** Does it define promotion gates (burn-in → steady-state)?

### For Company Hub Processes (v2.1 Requirements)

- [ ] Is it related to identity, domain, pattern, or BIT scoring?
- [ ] Does it NOT process people lifecycle?
- [ ] Does it NOT process DOL filings directly?
- [ ] Does it NOT process news events directly?
- [ ] **v2.1:** Does it generate correlation_id at batch intake?
- [ ] **v2.1:** Does it pass correlation_id to People Pipeline?

### Signal Emission Checklist (v2.1)

- [ ] Signal includes `correlation_id` (UUID v4)
- [ ] Signal includes `company_id` (required anchor)
- [ ] Signal includes `source_spoke` identifier
- [ ] Signal uses correct dedup key for idempotency
- [ ] Signal respects dedup window (24h/30d/365d per hub)
- [ ] Duplicate detection skips silently (no error)

---

## 8. Summary Statistics

| Metric | Count |
|--------|-------|
| **Total Hubs/Sub-Hubs** | 4 (1 master + 3 spokes) |
| **Total Processes** | 21 |
| **Total Signal Types** | 14 |
| **Decision Points** | 1 (BIT Engine only) |
| **Active PRDs** | 4 |
| **Planned PRDs** | 1 |

---

## 9. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-17 | Initial Hub-Process-Signal Matrix |
| 2.1 | 2025-12-17 | Hardened: Correlation ID enforcement, Signal idempotency matrix, PRD v2.1 alignment |

---

*Document Version: 2.1*
*Last Updated: 2025-12-17*
*Doctrine: Bicycle Wheel v1.1 / Barton Doctrine*
