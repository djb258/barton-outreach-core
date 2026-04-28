# Agent Outreach Pages — Territory Views + CSV Export

## Status: OPERATE
## Medium: worker
## Business: svg-agency

---

# IDENTITY (Thing — what this IS)

## 1. IDENTITY

| Field | Value |
|-------|-------|
| ID | WKR-AGENT-PAGES |
| Name | Agent Outreach Pages |
| Medium | CF Worker (Hono + TypeScript) |
| Business Silo | svg-agency |
| CTB Position | leaf / workers / agent-pages |
| ORBT | OPERATE |
| Strikes | 0 |
| Authority | sovereign — Dave Barton |
| Last Modified | 2026-04-15 |
| BAR Reference | none |

### HEIR

| Field | Value |
|-------|-------|
| sovereign_ref | svg-agency |
| hub_id | agent-pages |
| ctb_placement | leaf |
| imo_topology | output |
| cc_layer | CC-03 leaf |
| services | Cloudflare Workers, D1 (outreach-ops + spine) |
| secrets_provider | none (no auth — obscure URLs) |
| acceptance_criteria | Each agent sees their companies, contacts, and can export CSV |

---

## 2. PURPOSE

Service agents need to see which companies are being marketed in their territory and hand lists to callers. Without this, agents have no visibility into outreach activity and can't coordinate phone follow-ups with email campaigns.

---

# CONTRACT (Flow — what flows through this)

## 3. RESOURCES

### Dependencies

| Dependency | Type | What It Provides | Status |
|-----------|------|-----------------|--------|
| D1 outreach-ops (73a285b8) | database | slot_workbench — all company/contact data | ACTIVE |
| D1 spine (641a9a1e) | database | coverage_service_agent — agent lookup | ACTIVE |
| slot_workbench.service_agents | column | Agent assignment per company | ACTIVE |

### Downstream Consumers

| Consumer | What It Needs |
|----------|--------------|
| Dave Allan (SA-001) | His territory companies + CSV export |
| Jeff Mussolino (SA-002) | His territory companies + CSV export |
| David Vang (SA-003) | His territory companies + CSV export |
| Phone callers | CSV lists from agents for outbound calls |

---

## 4. IMO — Input, Middle, Output

### Two-Question Intake
1. **"What triggers this?"** — Agent opens their URL to see current outreach targets
2. **"How do we get it?"** — Live D1 query on slot_workbench filtered by service_agents

### Input
HTTP GET request to `/agent/{sa-001|sa-002|sa-003}`

### Middle
Query slot_workbench WHERE service_agents LIKE '%SA-00x%' AND has_name = 1 AND has_email = 1. Group by company. Render HTML table with search + CSV export.

### Output
HTML page with company list, contacts, search bar, two export buttons (all / verified only).

---

## 5. DATA SCHEMA

### URLs

| URL | What |
|-----|------|
| https://agent-pages.svg-outreach.workers.dev/ | Landing — all 3 agents |
| https://agent-pages.svg-outreach.workers.dev/agent/sa-001 | Dave Allan's territory |
| https://agent-pages.svg-outreach.workers.dev/agent/sa-002 | Jeff Mussolino's territory |
| https://agent-pages.svg-outreach.workers.dev/agent/sa-003 | David Vang's territory |
| https://agent-pages.svg-outreach.workers.dev/health | Health check |

### Agent Registry (D1: spine — coverage_service_agent)

| Agent Number | Name | Status |
|-------------|------|--------|
| SA-001 | Dave Allan | active |
| SA-002 | Jeff Mussolino | active |
| SA-003 | David Vang | active |

### Territory Distribution (slot_workbench, sendable only)

| Agent | Companies | Slots |
|-------|----------:|------:|
| SA-002 (Jeff) | 22,469 | 67,407 |
| SA-001 (Dave A.) | 3,940 | 11,820 |
| SA-003 (David V.) | 3,331 | 9,993 |
| SA-001 + SA-002 (shared) | 2,921 | 8,763 |

### D1 Databases

| Binding | Database | ID |
|---------|----------|----|
| D1_OUTREACH | svg-d1-outreach-ops | 73a285b8-770a-4370-abbe-ce9607be0b34 |
| D1_SPINE | svg-d1-spine | 641a9a1e-0882-41a7-82af-ea700e7cfbb3 |

### CSV Export Columns

Company, City, State, Employees, Role, First Name, Last Name, Email, Verified, Phone

---

## 6. DMJ — Define, Map, Join

### 6a. DEFINE

| Element | ID | Format | C or V |
|---------|-----|--------|--------|
| Agent number | SA-00x | text | C |
| Agent name | string | text | V (people change) |
| Territory assignment | service_agents column | CSV list of SA-00x | C (ZIP-based) |
| Company data | slot_workbench row | 80+ columns | V |
| CSV export format | 10 columns | standard | C |

### 6b. MAP

| Source | Target |
|--------|--------|
| slot_workbench.service_agents | URL path /agent/sa-00x |
| slot_workbench contact fields | HTML table + CSV export |
| coverage_service_agent | Agent name display |

### 6c. JOIN

| Join Path | Type |
|-----------|------|
| URL param → AGENTS lookup → D1 query | Direct |
| slot_workbench → coverage_service_agent via SA-00x | Direct |

---

## 7. CONSTANTS & VARIABLES

### Constants
- Three agent slots (SA-001, SA-002, SA-003)
- Territory assignment by ZIP code radius
- CSV export format (10 columns)
- Page layout and search functionality

### Variables
- Agent names (people change)
- Company data (updates with enrichment pipeline)
- Contact details (updates with MV runs, people worker)
- Which companies were emailed (updates with each send batch)

---

## 8. STOP CONDITIONS

| Condition | Action |
|-----------|--------|
| Agent not found in URL | Return 404 |
| D1 query fails | Worker returns 500 — check D1 binding |
| Agent added/removed | Update AGENTS constant in index.ts + coverage_service_agent table |

---

# GOVERNANCE (Change — how this is controlled)

## 9. VERIFICATION

```
1. curl https://agent-pages.svg-outreach.workers.dev/health → {"status":"ok"}
2. Open /agent/sa-001 → shows Dave Allan's companies with search + CSV
3. Click "Export CSV" → downloads file with correct columns
4. Click "Export Verified Only" → downloads subset with has_verified_email = 1
5. Search bar filters companies in real time
```

---

## 10. ANALYTICS

| Metric | Unit | Baseline | Target |
|--------|------|----------|--------|
| Page load time | ms | — | < 3000 |
| Companies per agent | count | SA-001: 3,940 / SA-002: 22,469 / SA-003: 3,331 | grows with pipeline |
| CSV downloads | count/week | 0 | track usage |

---

## 11. EXECUTION TRACE

| Date | What | Result |
|------|------|--------|
| 2026-04-15 | Initial deploy | Live at agent-pages.svg-outreach.workers.dev |
| 2026-04-15 | Populated coverage_service_agent in D1 | 3 agents from Neon |

---

## 12. LOGBOOK

No logbook during BUILD. Created on first certification.

---

## 13. FLEET FAILURE REGISTRY

| Pattern ID | Location | Error Code | First Seen | Status |
|-----------|----------|-----------|-----------|--------|
| — | — | — | — | No failures registered |

---

## 14. SESSION LOG

| Date | What Was Done | LBB Record |
|------|---------------|-----------|
| 2026-04-15 | Built and deployed agent-pages worker | pending |

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-04-15 |
| Last Modified | 2026-04-15 |
| Version | 1.0.0 |
| Template Version | UNIFIED_TEMPLATE 1.0.0 |
| Medium | worker |
| Governing Engine | law/doctrine/FOUNDATIONAL_BEDROCK.md |
