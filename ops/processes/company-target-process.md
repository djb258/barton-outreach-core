# Process Declaration: Company Target Hub

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
| **Hub ID** | HUB-COMPANY-TARGET |
| **Doctrine ID** | 04.04.01 |
| **Process Type** | Sub-Hub Execution |
| **Version** | 1.0.0 |

---

## Process ID Pattern

```
company-target-${PROCESS_TYPE}-${TIMESTAMP}-${RANDOM_HEX}
```

### Process Types

| Type | Description | Example |
|------|-------------|---------|
| `pattern` | Email pattern discovery | `company-target-pattern-20260129-a1b2c3d4` |
| `domain` | Domain resolution | `company-target-domain-20260129-b2c3d4e5` |
| `verify` | Pattern verification | `company-target-verify-20260129-c3d4e5f6` |

---

## Constants Consumed

_Reference: `docs/prd/PRD_COMPANY_HUB.md §3 Constants`_

| Constant | Source | Description |
|----------|--------|-------------|
| `outreach_id` | outreach.outreach | Operational spine identifier |
| `sovereign_company_id` | CL | Company identity from authority registry |
| `domain` | CL/DNS | Company domain |
| `dns_mx_records` | DNS infrastructure | MX record validation results |
| `external_pattern_data` | Tier 0/1/2 providers | Pattern discovery API responses |

---

## Variables Produced

_Reference: `docs/prd/PRD_COMPANY_HUB.md §3 Variables`_

| Variable | Destination | Description |
|----------|-------------|-------------|
| `email_method` | outreach.company_target | Verified email pattern |
| `method_type` | outreach.company_target | Pattern source (verified/hunter/clearbit) |
| `confidence_score` | outreach.company_target | Pattern confidence (0.00-1.00) |
| `outreach_status` | outreach.company_target | Processing status |
| `imo_completed_at` | outreach.company_target | IMO completion timestamp |

---

## Governing PRD

| Field | Value |
|-------|-------|
| **PRD** | `docs/prd/PRD_COMPANY_HUB.md` |
| **PRD Version** | 3.0.0 |

---

## Pass Ownership

| Pass | IMO Layer | Description |
|------|-----------|-------------|
| **CAPTURE** | I (Ingress) | Receive identity from CL, pattern discovery responses |
| **COMPUTE** | M (Middle) | Domain resolution, pattern discovery, pattern verification |
| **GOVERN** | O (Egress) | Write verified patterns to company_target |

---

## Execution Flow

```
1. CAPTURE: Receive outreach_id + domain from outreach.outreach
   ↓
2. COMPUTE: Resolve domain via DNS/MX check
   ↓
3. COMPUTE: Discover pattern via Tier 0 → 1 → 2 waterfall
   ↓
4. COMPUTE: Verify pattern via sample email match
   ↓
5. GOVERN: Write email_method to outreach.company_target
   ↓
6. GOVERN: Update outreach_status to 'completed'
```

---

## Error Codes

| Code | Severity | Description |
|------|----------|-------------|
| `CT-001` | HIGH | Domain resolution failed |
| `CT-002` | MEDIUM | Pattern discovery failed (all tiers exhausted) |
| `CT-003` | LOW | Pattern verification confidence < 0.7 |
| `CT-004` | CRITICAL | Missing outreach_id |

---

## Correlation ID Enforcement

- `correlation_id` REQUIRED from batch intake
- Propagated to all error logs
- Included in all pattern discovery API calls
- Stored in `outreach.company_target_errors` for tracing

---

## Structural Bindings

| Binding Type | Reference |
|--------------|-----------|
| **Governing PRD** | `docs/prd/PRD_COMPANY_HUB.md` |
| **Tables READ** | `cl.company_identity`, `outreach.outreach` |
| **Tables WRITTEN** | `outreach.company_target`, `outreach.company_target_errors` |
| **Pass Participation** | CAPTURE → COMPUTE → GOVERN |
| **ERD Reference** | `docs/ERD_SUMMARY.md §Authoritative Pass Ownership` |

---

**Created**: 2026-01-29
**Version**: 1.0.0
