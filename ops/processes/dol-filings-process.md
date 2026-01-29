# Process Declaration: DOL Filings Hub

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | IMO-Creator v1.0 |
| **Domain Spec Reference** | `doctrine/REPO_DOMAIN_SPEC.md` |
| **CC Layer** | CC-04 (Process) |
| **Process Doctrine** | `templates/doctrine/PROCESS_DOCTRINE.md` |

---

## Process Identity

| Field | Value |
|-------|-------|
| **Hub ID** | HUB-DOL |
| **Doctrine ID** | 04.04.03 |
| **Process Type** | Sub-Hub Execution |
| **Version** | 1.0.0 |

---

## Process ID Pattern

```
dol-filings-${PROCESS_TYPE}-${TIMESTAMP}-${RANDOM_HEX}
```

### Process Types

| Type | Description | Example |
|------|-------------|---------|
| `ingest` | Form 5500 ingestion | `dol-filings-ingest-20260129-a1b2c3d4` |
| `match` | EIN matching | `dol-filings-match-20260129-b2c3d4e5` |
| `extract` | Schedule A extraction | `dol-filings-extract-20260129-c3d4e5f6` |

---

## Constants Consumed

_Reference: `docs/prd/PRD_DOL_SUBHUB.md §3 Constants`_

| Constant | Source | Description |
|----------|--------|-------------|
| `outreach_id` | outreach.outreach | Operational spine identifier |
| `dol_form_5500_filings` | Federal DOL | Raw Form 5500 filing data |
| `dol_schedule_a_data` | Federal DOL | Schedule A insurance data |
| `ein_lookup_request` | Company Target | EIN resolution request |

---

## Variables Produced

_Reference: `docs/prd/PRD_DOL_SUBHUB.md §3 Variables`_

| Variable | Destination | Description |
|----------|-------------|-------------|
| `filing_id` | dol.form_5500 | Parsed filing identifier |
| `ein_match_result` | outreach.dol | EIN → company match |
| `form_5500_matched` | outreach.dol | Match success flag |
| `schedule_a_matched` | outreach.dol | Schedule A match flag |
| `match_confidence` | outreach.dol | Match confidence score |
| `FORM_5500_FILED_signal` | BIT Engine | Signal emission |
| `LARGE_PLAN_signal` | BIT Engine | Signal emission |
| `BROKER_CHANGE_signal` | BIT Engine | Signal emission |

---

## Governing PRD

| Field | Value |
|-------|-------|
| **PRD** | `docs/prd/PRD_DOL_SUBHUB.md` |
| **PRD Version** | 4.0.0 |

---

## Pass Ownership

| Pass | IMO Layer | Description |
|------|-----------|-------------|
| **CAPTURE** | I (Ingress) | Receive federal DOL data downloads, EIN lookup requests |
| **COMPUTE** | M (Middle) | Filing parsing, Schedule A extraction, EIN matching |
| **GOVERN** | O (Egress) | Emit FORM_5500_FILED, LARGE_PLAN, BROKER_CHANGE signals |

---

## Execution Flow

```
1. CAPTURE: Ingest federal DOL Form 5500 bulk files
   ↓
2. COMPUTE: Parse filings into structured records
   ↓
3. COMPUTE: Extract Schedule A insurance data
   ↓
4. COMPUTE: Match EIN to outreach_id via ein_urls lookup
   ↓
5. GOVERN: Write match results to outreach.dol
   ↓
6. GOVERN: Emit FORM_5500_FILED signal (if new filing)
   ↓
7. GOVERN: Emit LARGE_PLAN signal (if participants > 1000)
   ↓
8. GOVERN: Emit BROKER_CHANGE signal (if broker changed)
```

---

## Signal Emissions

| Signal | Impact | Dedup Key | Window |
|--------|--------|-----------|--------|
| `FORM_5500_FILED` | +5.0 | `(company_id, filing_id)` | 365 days |
| `LARGE_PLAN` | +8.0 | `(company_id, filing_id)` | 365 days |
| `BROKER_CHANGE` | +7.0 | `(company_id, filing_id)` | 365 days |

---

## Error Codes

| Code | Severity | Description |
|------|----------|-------------|
| `DOL-001` | CRITICAL | Federal data download failed |
| `DOL-002` | MEDIUM | Filing parse error (invalid XML/format) |
| `DOL-003` | HIGH | EIN match failed (no company found) |
| `DOL-004` | LOW | Schedule A extraction incomplete |
| `DOL-007` | MEDIUM | Multiple EIN candidates (collision) |

---

## Correlation ID Enforcement

- `correlation_id` generated at filing ingest (one per Form 5500)
- Included in all signal emissions
- Stored in `outreach.dol_errors` for tracing

---

## Structural Bindings

| Binding Type | Reference |
|--------------|-----------|
| **Governing PRD** | `docs/prd/PRD_DOL_SUBHUB.md` |
| **Tables READ** | `dol.form_5500`, `dol.schedule_a`, `dol.ein_urls`, `outreach.outreach` |
| **Tables WRITTEN** | `dol.form_5500`, `dol.schedule_a`, `dol.renewal_calendar`, `outreach.dol`, `outreach.bit_signals`, `outreach.dol_errors` |
| **Pass Participation** | CAPTURE → COMPUTE → GOVERN |
| **ERD Reference** | `docs/ERD_SUMMARY.md §Authoritative Pass Ownership` |

---

**Created**: 2026-01-29
**Version**: 1.0.0
