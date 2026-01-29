# Process Declaration: Talent Flow Hub

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
| **Hub ID** | talent-flow |
| **Doctrine ID** | 04.04.06 |
| **Process Type** | Sub-Hub Execution |
| **Version** | 1.0.0 |
| **Status** | SCAFFOLD (implementation pending) |

---

## Process ID Pattern

```
talent-flow-${PROCESS_TYPE}-${TIMESTAMP}-${RANDOM_HEX}
```

### Process Types

| Type | Description | Example |
|------|-------------|---------|
| `detect` | Movement detection | `talent-flow-detect-20260129-a1b2c3d4` |
| `gate` | Company gate check | `talent-flow-gate-20260129-b2c3d4e5` |
| `signal` | Signal emission | `talent-flow-signal-20260129-c3d4e5f6` |

---

## Constants Consumed

_Reference: `docs/prd/PRD_TALENT_FLOW_SPOKE.md §3 Constants`_

| Constant | Source | Description |
|----------|--------|-------------|
| `person_record` | People Intelligence | Person data with LinkedIn URL |
| `company_unique_id` | CL | Company identity |
| `linkedin_change_data` | External monitoring | LinkedIn profile changes |
| `current_title` | People Hub | Current job title |
| `current_company` | People Hub | Current employer |

---

## Variables Produced

_Reference: `docs/prd/PRD_TALENT_FLOW_SPOKE.md §3 Variables`_

| Variable | Destination | Description |
|----------|-------------|-------------|
| `movement_event` | Movement history | Detected movement record |
| `event_type` | Movement event | joined/left/title_change |
| `from_company` | Movement event | Previous employer |
| `to_company` | Movement event | New employer |
| `confidence` | Movement event | Detection confidence |
| `EXECUTIVE_JOINED_signal` | BIT Engine | Signal emission (+10.0) |
| `EXECUTIVE_LEFT_signal` | BIT Engine | Signal emission (-5.0) |
| `TITLE_CHANGE_signal` | BIT Engine | Signal emission (+3.0) |

---

## Governing PRD

| Field | Value |
|-------|-------|
| **PRD** | `docs/prd/PRD_TALENT_FLOW_SPOKE.md` |
| **PRD Version** | 3.0.0 |

---

## Pass Ownership

| Pass | IMO Layer | Description |
|------|-----------|-------------|
| **CAPTURE** | I (Ingress) | Receive person records from People Hub, LinkedIn changes |
| **COMPUTE** | M (Middle) | Movement detection, company gate check, signal value calculation |
| **GOVERN** | O (Egress) | Emit EXECUTIVE_JOINED, EXECUTIVE_LEFT, TITLE_CHANGE signals |

---

## Execution Flow

```
1. CAPTURE: Receive person record with LinkedIn URL
   ↓
2. CAPTURE: Detect LinkedIn profile changes
   ↓
3. COMPUTE: Company gate check (both companies must exist in CL)
   ↓
4. COMPUTE: Classify movement type (joined/left/title_change)
   ↓
5. COMPUTE: Calculate signal value based on seniority
   ↓
6. GOVERN: Record movement event
   ↓
7. GOVERN: Emit appropriate signal to BIT Engine
```

---

## Signal Emissions

| Signal | Impact | Dedup Key | Window |
|--------|--------|-----------|--------|
| `EXECUTIVE_JOINED` | +10.0 | `(company_id, person_id)` | 24 hours |
| `EXECUTIVE_LEFT` | -5.0 | `(company_id, person_id)` | 24 hours |
| `TITLE_CHANGE` | +3.0 | `(company_id, person_id)` | 24 hours |

---

## Company Gate Rules

| Condition | Action |
|-----------|--------|
| Both companies exist in CL | Proceed with movement detection |
| Old company missing | Flag for identity resolution |
| New company missing | Trigger identity pipeline |
| Neither company exists | Skip (no signal) |

---

## Error Codes

| Code | Severity | Description |
|------|----------|-------------|
| `TF-001` | MEDIUM | LinkedIn profile unavailable |
| `TF-002` | LOW | Movement detection confidence < 0.5 |
| `TF-003` | HIGH | Company gate failed (company not in CL) |
| `TF-004` | LOW | Duplicate movement detected (within dedup window) |

---

## Correlation ID Enforcement

- `correlation_id` inherited from People Hub
- Propagated through movement detection
- Included in all signal emissions

---

## Dependencies

| Direction | Hub | Description |
|-----------|-----|-------------|
| Upstream | People Intelligence | Person data needed for tracking |
| Downstream | Company Target | Movement signals feed BIT engine |

---

## Structural Bindings

| Binding Type | Reference |
|--------------|-----------|
| **Governing PRD** | `docs/prd/PRD_TALENT_FLOW_SPOKE.md` |
| **Tables READ** | `people.people_master`, `cl.company_identity`, `outreach.outreach` |
| **Tables WRITTEN** | `bit.movement_events`, `outreach.bit_signals` |
| **Pass Participation** | CAPTURE → COMPUTE → GOVERN |
| **ERD Reference** | `docs/ERD_SUMMARY.md §Authoritative Pass Ownership` |

---

**Created**: 2026-01-29
**Version**: 1.0.0
