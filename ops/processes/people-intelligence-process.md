# Process Declaration: People Intelligence Hub

> **Note (2026-02-20)**: Some tables referenced in this document were dropped during database consolidation (all had 0 rows). See `doctrine/DO_NOT_MODIFY_REGISTRY.md` for the complete list of dropped tables and their migration sources. Affected tables: `outreach.bit_signals`.

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
| **Hub ID** | HUB-PEOPLE |
| **Doctrine ID** | 04.04.02 |
| **Process Type** | Sub-Hub Execution |
| **Version** | 1.0.0 |

---

## Process ID Pattern

```
people-intelligence-${PROCESS_TYPE}-${TIMESTAMP}-${RANDOM_HEX}
```

### Process Types

| Type | Description | Example |
|------|-------------|---------|
| `ingest` | Person intake | `people-intelligence-ingest-20260129-a1b2c3d4` |
| `email` | Email generation | `people-intelligence-email-20260129-b2c3d4e5` |
| `slot` | Slot assignment | `people-intelligence-slot-20260129-c3d4e5f6` |
| `verify` | Email verification | `people-intelligence-verify-20260129-d4e5f6a7` |

---

## Constants Consumed

_Reference: `docs/prd/PRD_PEOPLE_SUBHUB.md §3 Constants`_

| Constant | Source | Description |
|----------|--------|-------------|
| `outreach_id` | outreach.outreach | Operational spine identifier |
| `slot_requirements` | Company Target | Required slots (CEO, CFO, HR, etc.) |
| `linkedin_profile_data` | External enrichment | LinkedIn profile information |
| `email_pattern` | Company Target | Verified email pattern |
| `person_intake_data` | Intake CSV | Raw person records |

---

## Variables Produced

_Reference: `docs/prd/PRD_PEOPLE_SUBHUB.md §3 Variables`_

| Variable | Destination | Description |
|----------|-------------|-------------|
| `person_unique_id` | people.people_master | Minted person identifier |
| `generated_email` | people.people_master | Pattern-applied email |
| `email_verified` | people.people_master | Verification status |
| `slot_type` | people.company_slot | Assigned slot |
| `is_filled` | people.company_slot | Slot fill status |
| `SLOT_FILLED_signal` | BIT Engine | Signal emission |
| `EMAIL_VERIFIED_signal` | BIT Engine | Signal emission |

---

## Governing PRD

| Field | Value |
|-------|-------|
| **PRD** | `docs/prd/PRD_PEOPLE_SUBHUB.md` |
| **PRD Version** | 3.0.0 |

---

## Pass Ownership

| Pass | IMO Layer | Description |
|------|-----------|-------------|
| **CAPTURE** | I (Ingress) | Receive slot requirements, LinkedIn data, person intake |
| **COMPUTE** | M (Middle) | Dedup, title normalization, email generation, slot assignment |
| **GOVERN** | O (Egress) | Emit SLOT_FILLED, EMAIL_VERIFIED signals to BIT Engine |

---

## Execution Flow

```
1. CAPTURE: Receive slot_requirements from Company Target
   ↓
2. CAPTURE: Receive person_intake_data from CSV
   ↓
3. COMPUTE: Deduplication against existing people_master
   ↓
4. COMPUTE: Title normalization and seniority ranking
   ↓
5. COMPUTE: Email generation using company email_pattern
   ↓
6. COMPUTE: Slot assignment (one person per slot per company)
   ↓
7. GOVERN: Emit SLOT_FILLED signal to BIT Engine
   ↓
8. GOVERN: Emit EMAIL_VERIFIED signal to BIT Engine
```

---

## Signal Emissions

| Signal | Impact | Dedup Key | Window |
|--------|--------|-----------|--------|
| `SLOT_FILLED` | +10.0 | `(company_id, slot_type, person_id)` | 24 hours |
| `SLOT_VACATED` | -5.0 | `(company_id, slot_type, person_id)` | 24 hours |
| `EMAIL_VERIFIED` | +3.0 | `(person_id, email)` | 24 hours |
| `LINKEDIN_FOUND` | +2.0 | `(person_id, linkedin_url)` | 24 hours |

---

## Error Codes

| Code | Severity | Description |
|------|----------|-------------|
| `PSH-P0-001` | MEDIUM | Person deduplication conflict |
| `PSH-P5-001` | HIGH | Email generation failed (missing pattern) |
| `PSH-P5-002` | MEDIUM | Email generation failed (missing name) |
| `PSH-P6-001` | LOW | Slot assignment conflict (replaced existing) |
| `PSH-P6-002` | MEDIUM | Title classification failed |

---

## Correlation ID Enforcement

- `correlation_id` inherited from Company Hub Pipeline
- Propagated through Phases 0, 5-8
- Included in all signal emissions
- Stored in `outreach.people_errors` for tracing

---

## Structural Bindings

| Binding Type | Reference |
|--------------|-----------|
| **Governing PRD** | `docs/prd/PRD_PEOPLE_SUBHUB.md` |
| **Tables READ** | `outreach.outreach`, `outreach.company_target`, `people.people_master` |
| **Tables WRITTEN** | `people.people_master`, `people.company_slot`, `outreach.people`, `outreach.bit_signals`, `outreach.people_errors` |
| **Pass Participation** | CAPTURE → COMPUTE → GOVERN |
| **ERD Reference** | `docs/ERD_SUMMARY.md §Authoritative Pass Ownership` |

---

**Created**: 2026-01-29
**Version**: 1.0.0
