# PRD — Blog Content Sub-Hub

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | 1.1.0 |
| **CTB Version** | 1.0.0 |
| **CC Layer** | CC-03 (Context within CC-02 Hub) |

---

## 1. Sovereign Reference (CC-01)

| Field | Value |
|-------|-------|
| **Sovereign ID** | barton-enterprises |
| **Sovereign Boundary** | Marketing intelligence and executive enrichment operations |

---

## 2. Hub Identity (CC-02)

| Field | Value |
|-------|-------|
| **Parent Hub** | outreach-core |
| **Parent Hub ID** | outreach-core-001 |
| **Hub Name** | Blog Content |
| **Hub ID** | HUB-BC-001 |
| **Doctrine ID** | 04.04.05 |
| **Owner** | Outreach Team |
| **Version** | 1.0.0 |

---

## 3. Process Identity (CC-04)

| Field | Value |
|-------|-------|
| **PID Pattern** | `HUB-BC-001-${TIMESTAMP}-${RANDOM_HEX}` |
| **Session Pattern** | `HUB-BC-001-session-${SESSION_ID}` |
| **Context Binding** | outreach_context_id |

---

## 4. Purpose

Provide **timing signals** from news, funding events, and content sources.
BIT modulation only — cannot mint, revive, or trigger enrichment.

---

## 3.1 Waterfall Position

**Position**: 5th (LAST) in canonical waterfall

```
1. CL ──────────► PASS ──┐  (EXTERNAL)
                         │ company_unique_id
                         ▼
2. COMPANY TARGET ► PASS ──┐
                           │ verified_pattern, domain
                           ▼
3. DOL FILINGS ───► PASS ──┐
                           │ ein, filing_signals
                           ▼
4. PEOPLE ────────► PASS ──┐
                           │ slot_assignments
                           ▼
5. BLOG ──────────► PASS    ◄── YOU ARE HERE (FINAL)
```

### Upstream Dependencies

| Upstream | Required Signal | Gate |
|----------|-----------------|------|
| Company Target | company_unique_id, domain | MUST have PASS |
| DOL Filings | regulatory_signals | MUST have PASS |
| People Intelligence | slot_assignments | MUST have PASS |

### Downstream Consumers

| Downstream | Signals Emitted | Binding |
|------------|-----------------|---------|
| BIT Engine | timing_signals | outreach_context_id |
| Context Finalization | final_state | outreach_context_id |

### Waterfall Rules (LOCKED)

- People Intelligence must PASS before this hub executes
- This is the FINAL hub — context is finalized after this hub
- No retry/rescue from this hub (nothing downstream)
- Failures stay local — context finalized as FAIL

---

## 3.2 External Dependencies & Program Scope

### CL is EXTERNAL to Outreach

| Boundary | System | Ownership |
|----------|--------|-----------|
| **External** | Company Lifecycle (CL) | Mints company_unique_id, shared across all programs |
| **Program** | Outreach Orchestration | Mints outreach_context_id, program-scoped |
| **Sub-Hub** | Blog Content (this hub) | FINAL sub-hub in waterfall |

### Key Doctrine

- **CL is external** — Outreach CONSUMES company_unique_id, does NOT invoke CL
- **Timing Only** — This hub provides TIMING signals, NOT enrichment
- **Run identity** — All operations bound by outreach_context_id from Orchestration
- **Context table** — outreach.outreach_context is the root audit record

### Consumer-Only Compliance (CRITICAL)

This hub is a **CONSUMER** of upstream data, not a **PRODUCER**:

| Data | Source | This Hub |
|------|--------|----------|
| Company identity | Company Target | CONSUME (not mint) |
| Domain resolution | Company Target | CONSUME (not resolve) |
| Email patterns | People Intelligence | CONSUME (not generate) |
| Slot assignments | People Intelligence | CONSUME (not assign) |

### Explicit Prohibitions

- [ ] Does NOT invoke Company Lifecycle (CL is external)
- [ ] Does NOT mint company_unique_id (CL does)
- [ ] Does NOT trigger enrichment (timing only)
- [ ] Does NOT trigger spend (free signals only)
- [ ] Does NOT create outreach_context_id (Orchestration does)

---

## 4. Lifecycle Gate

| Minimum Lifecycle State | Gate Condition |
|-------------------------|----------------|
| ACTIVE | Requires lifecycle >= ACTIVE |

---

## 5. Signals Emitted

| Signal | BIT Impact | Description |
|--------|-----------|-------------|
| FUNDING_EVENT | +15.0 | Company received funding |
| ACQUISITION | +12.0 | Company acquired or acquiring |
| LEADERSHIP_CHANGE | +8.0 | Executive change detected |
| EXPANSION | +7.0 | Office/market expansion |
| PRODUCT_LAUNCH | +5.0 | New product announced |
| PARTNERSHIP | +5.0 | Partnership announced |
| LAYOFF | -3.0 | Layoffs announced |
| NEGATIVE_NEWS | -5.0 | Negative press coverage |

---

## 6. Constraints

- [ ] Cannot mint or revive companies
- [ ] Cannot trigger enrichment
- [ ] BIT modulation only
- [ ] Requires company_sov_id (must already exist)
- [ ] Lifecycle read-only

---

## 7. Inputs

| Input | Source | Required |
|-------|--------|----------|
| company_sov_id | Company Lifecycle (external) | YES |
| news_feeds | External feeds | NO |
| funding_alerts | Crunchbase, etc. | NO |
| content_webhooks | Custom integrations | NO |

---

## 8. Tools

No paid enrichment tools. Signal processing only.

---

## 9. Core Metric

**SIGNAL_COVERAGE** — Percentage of active companies with recent signals

---

## 10. Upstream Dependencies, Signal Validity, and Downstream Effects

### Execution Position

**Last in canonical order** — After Company Target, DOL Filings, and People Intelligence.

### Required Upstream PASS Conditions

| Upstream | Condition |
|----------|-----------|
| Company Target | PASS (company exists, domain resolved) |
| DOL Filings | PASS (or no filings) |
| People Intelligence | PASS (slots populated) |

### Signals Consumed (Origin-Bound)

| Signal | Origin | Validity |
|--------|--------|----------|
| company_sov_id | Company Lifecycle (via CT) | Run-bound to outreach_context_id |
| domain | Company Target | Run-bound to outreach_context_id |
| BIT_SCORE | Company Target | Run-bound to outreach_context_id |
| regulatory_signals | DOL Filings | Run-bound to outreach_context_id |
| slot_assignments | People Intelligence | Run-bound to outreach_context_id |

### Signals Emitted

| Signal | Consumers | Validity |
|--------|-----------|----------|
| FUNDING_EVENT | BIT Engine | Run-bound to outreach_context_id |
| ACQUISITION | BIT Engine | Run-bound to outreach_context_id |
| LEADERSHIP_CHANGE | BIT Engine | Run-bound to outreach_context_id |
| All timing signals | BIT Engine only | Run-bound to outreach_context_id |

### Downstream Effects

| If This Hub | Then |
|-------------|------|
| PASS | Context finalized as PASS |
| FAIL | Context finalized as FAIL |

### Explicit Prohibitions

- [ ] May NOT trigger enrichment (no paid tools)
- [ ] May NOT trigger spend (timing signals only)
- [ ] May NOT mint or revive companies
- [ ] May NOT fix upstream errors
- [ ] May NOT refresh signals from prior contexts
- [ ] May NOT use signal age to justify action

---

## Approval

| Role | Name | Date |
|------|------|------|
| Owner | | |
| Reviewer | | |

---

---

## 11. URL Discovery System (ADR-005)

### Purpose

Catalog company web pages for future executive extraction and signal monitoring.

### Tables

| Table | Schema | Purpose |
|-------|--------|---------|
| `company_source_urls` | company | Discovered URLs linked to company_unique_id |
| `url_discovery_failures` | company | Failed discovery attempts for retry |

### Source Types

| Type | Purpose | Extraction Target |
|------|---------|-------------------|
| leadership_page | Executive bios | People slots |
| about_page | Company overview | Context |
| team_page | Staff listings | People discovery |
| press_page | News/announcements | Timing signals |
| careers_page | Job postings | Expansion signals |
| contact_page | Contact info | Verification |

### Discovery Results (2026-01-18)

| Metric | Value |
|--------|-------|
| Companies Processed | 73,119 |
| URLs Discovered | 97,124 |
| Success Rate | 42.1% |
| Failed (for retry) | 42,348 |

### Scripts

| Script | Purpose |
|--------|---------|
| `discover_urls_batch.py` | Parallel batch discovery |
| `discovery_status.py` | Progress monitoring |

---

**Last Updated**: 2026-01-18
**Hub**: Blog Content (04.04.05)
**Doctrine**: External CL + Outreach Program v1.0
