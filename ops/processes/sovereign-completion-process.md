# Process Declaration: Sovereign Completion System

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
| **Hub ID** | HUB-SOVEREIGN-COMPLETION |
| **Process Type** | Governance Process |
| **Version** | 1.0.0 |

---

## Process ID Pattern

```
sovereign-completion-${PROCESS_TYPE}-${TIMESTAMP}-${RANDOM_HEX}
```

### Process Types

| Type | Description | Example |
|------|-------------|---------|
| `compute` | Tier computation | `sovereign-completion-compute-20260129-a1b2c3d4` |
| `override` | Override application | `sovereign-completion-override-20260129-b2c3d4e5` |
| `audit` | Audit evaluation | `sovereign-completion-audit-20260129-c3d4e5f6` |

---

## Constants Consumed

_Reference: `docs/prd/PRD_SOVEREIGN_COMPLETION.md §3 Constants`_

| Constant | Source | Description |
|----------|--------|-------------|
| `company_target_status` | Company Target | Hub completion status (PASS/FAIL/IN_PROGRESS) |
| `dol_status` | DOL Filings | Hub completion status |
| `people_status` | People Intelligence | Hub completion status |
| `talent_flow_status` | Talent Flow | Hub completion status |
| `blog_status` | Blog Content | Hub completion status (optional) |
| `bit_score` | BIT Engine | Buyer intent score |

---

## Variables Produced

_Reference: `docs/prd/PRD_SOVEREIGN_COMPLETION.md §3 Variables`_

| Variable | Destination | Description |
|----------|-------------|-------------|
| `marketing_tier` | Eligibility views | Computed tier (-1 to 3) |
| `overall_status` | vw_sovereign_completion | Aggregated hub status |
| `effective_tier` | vw_marketing_eligibility_with_overrides | Tier after kill-switch |

---

## Governing PRD

| Field | Value |
|-------|-------|
| **PRD** | `docs/prd/PRD_SOVEREIGN_COMPLETION.md` |
| **PRD Version** | 2.0.0 |

---

## Pass Ownership

| Pass | IMO Layer | Description |
|------|-----------|-------------|
| **CAPTURE** | I (Ingress) | Receive status changes from sub-hubs |
| **COMPUTE** | M (Middle) | Compute marketing tier from hub statuses |
| **GOVERN** | O (Egress) | Expose computed eligibility to consumers |

---

## Marketing Tier Logic

| Tier | Name | Requirement |
|------|------|-------------|
| -1 | INELIGIBLE | overall_status = BLOCKED |
| 0 | Cold | company_target = PASS |
| 1 | Persona | people = PASS |
| 2 | Trigger | talent_flow = PASS |
| 3 | Aggressive | ALL PASS + BIT >= 50 |

---

## Hub Registry (Waterfall Order)

| Order | Hub | Classification | Gates Completion |
|-------|-----|----------------|------------------|
| 1 | company-target | required | TRUE |
| 2 | dol-filings | required | TRUE |
| 3 | people-intelligence | required | TRUE |
| 4 | talent-flow | required | TRUE |
| 5 | blog-content | optional | FALSE |
| 6 | bit-enrichment | optional | FALSE |

---

## Tools (Deterministic)

| Tool | Type | IMO Layer |
|------|------|-----------|
| vw_sovereign_completion | View | M |
| vw_marketing_eligibility | View | O |
| vw_marketing_eligibility_with_overrides | View | O |
| fn_get_completion | Function | O |

---

## Error Codes

| Code | Severity | Description |
|------|----------|-------------|
| `SC-001` | HIGH | View query timeout |
| `SC-002` | CRITICAL | Kill switch bypass detected |
| `SC-003` | HIGH | Ghost PASS state (invalid) |
| `SC-004` | MEDIUM | Missing hub status (defaulted to IN_PROGRESS) |

---

## Guard Rails

| Guard Rail | Type | Threshold |
|------------|------|-----------|
| Kill Switch | Override | manual_overrides table |
| BIT Gate | Threshold | >= 25 for PASS |
| Tier 3 Gate | Threshold | BIT >= 50 + all hubs PASS |

---

## Correlation ID Enforcement

- `correlation_id` from status update event
- Propagated through tier computation
- Included in audit log entries

---

## Frozen Components (v1.0)

**DO NOT MODIFY without formal change request:**
- `vw_marketing_eligibility_with_overrides` (authoritative view)
- `vw_sovereign_completion` (sovereign view)
- Marketing tier computation logic
- Kill switch system
- Hub registry and waterfall order

---

## Structural Bindings

| Binding Type | Reference |
|--------------|-----------|
| **Governing PRD** | `docs/prd/PRD_SOVEREIGN_COMPLETION.md` |
| **Tables READ** | `outreach.company_target`, `outreach.dol`, `outreach.people`, `outreach.blog`, `outreach.bit_scores`, `outreach.manual_overrides` |
| **Tables WRITTEN** | None (views only) |
| **Views OWNED** | `vw_sovereign_completion`, `vw_marketing_eligibility`, `vw_marketing_eligibility_with_overrides` |
| **Pass Participation** | CAPTURE → COMPUTE → GOVERN |
| **ERD Reference** | `docs/ERD_SUMMARY.md §Authoritative Pass Ownership` |

---

**Created**: 2026-01-29
**Version**: 1.0.0
