# DOL Subhub Refactor — Confirmation Checklist
## Scope Correction: EIN Resolution Only

**Date**: 2025-01-01
**Refactor Version**: 2.0.0
**Previous Version**: 1.0.0 (Compliance Monitor - DEPRECATED)

---

## ✅ Scope Corrections Applied

### Removed from DOL Subhub

| Item | Previous State | Current State | Confirmation |
|------|---------------|---------------|--------------|
| Buyer Intent Language | Present in docs | **REMOVED** | ✅ |
| BIT Scoring Logic | Planned integration | **REMOVED** | ✅ |
| BIT Event Creation | `dol_violation` → BIT events | **REMOVED** | ✅ |
| OSHA Citations | Planned tracking | **REMOVED** | ✅ |
| EEOC Complaints | Planned tracking | **REMOVED** | ✅ |
| Slack Integration | Planned alerts | **REMOVED** | ✅ |
| Salesforce Sync | Planned CRM sync | **REMOVED** | ✅ |
| Grafana Dashboards | Planned monitoring | **REMOVED** | ✅ |
| Outreach Triggers | Planned automation | **REMOVED** | ✅ |
| People Enrichment | Planned contact data | **REMOVED** | ✅ |

### Added to DOL Subhub

| Item | Description | Confirmation |
|------|-------------|--------------|
| EIN ↔ company_unique_id linkage | Core function | ✅ |
| Identity Gate Validation | FAIL HARD requirements | ✅ |
| Append-Only Storage | No updates, no overwrites | ✅ |
| AIR Event Logging | Audit trail for all events | ✅ |
| Hash Fingerprint | Document integrity | ✅ |
| Source Verification | DOL/EBSA filing validation | ✅ |

---

## ✅ Documentation Updates

| Document | Update Type | Confirmation |
|----------|-------------|--------------|
| `DOL_EIN_RESOLUTION.md` | **CREATED** - New doctrine | ✅ |
| `dol_ein_linkage-schema.sql` | **CREATED** - New schema | ✅ |
| `PLE-Doctrine.md` | Updated Spoke 3 definition | ✅ |
| `PLE-Hub-Spoke-Axle.mmd` | Isolated DOL from BIT | ✅ |
| `hub_tasks.md` | Corrected DOL scope | ✅ |
| `doctrine/README.md` | Updated index | ✅ |
| `ein_validator.js` | **CREATED** - Validation module | ✅ |

---

## ✅ Diagram Updates

### PLE-Hub-Spoke-Axle.mmd Changes

| Change | Before | After |
|--------|--------|-------|
| Spoke 3 Label | "Compliance Monitor" | "DOL EIN Resolution" |
| Spoke 3 Content | "DOL Violations, OSHA, EEOC" | "EIN Linkage ONLY" |
| Spoke 3 Style | `futureStyle` | `isolatedStyle` |
| BIT Connection | `SPOKE3 → EVENTS` | **REMOVED** (commented out) |
| Hub Connection | `compliance.violations` | `dol.ein_linkage (ISOLATED)` |

---

## ✅ Schema Changes

### New Table: `dol.ein_linkage`

| Feature | Implementation |
|---------|---------------|
| Append-Only | Triggers block UPDATE/DELETE |
| EIN Format | CHECK constraint `^\d{2}-\d{7}$` |
| Source Validation | ENUM constraint |
| Hash Fingerprint | SHA-256 format validation |
| Foreign Key | `company_unique_id` → `company_master` |
| Unique Constraint | One EIN per company |

### New Table: `dol.air_log`

| Feature | Implementation |
|---------|---------------|
| Event Types | 9 defined types (kill switches + success) |
| Status Tracking | SUCCESS / FAILED / ABORTED |
| Identity Gate | Boolean + JSON anchors snapshot |
| Context ID | Required per HEIR doctrine |

---

## ✅ Kill Switches Implemented (DUAL-WRITE)

**Failure Routing Doctrine**:
All DOL Subhub failures are dual-written to:
1. **AIR event log** (`dol.air_log`) — authoritative / audit
2. **Canonical error table** (`shq.error_master`) — operational / triage

AIR is authoritative; `shq.error_master` is operational.

**NOTE**: `shq_error_log` is DEPRECATED and must not be referenced.

| Kill Switch | Event Type | Behavior |
|-------------|------------|----------|
| Company Target Not PASS | `COMPANY_TARGET_NOT_PASS` | ABORT + AIR + error_master |
| Multiple EINs | `MULTI_EIN_FOUND` | ABORT + AIR + error_master |
| EIN Mismatch | `EIN_MISMATCH` | ABORT + AIR + error_master |
| Filing TTL Exceeded | `FILING_TTL_EXCEEDED` | ABORT + AIR + error_master |
| Source Unavailable | `SOURCE_UNAVAILABLE` | ABORT + AIR + error_master |
| Cross-Context Contamination | `CROSS_CONTEXT_CONTAMINATION` | ABORT + AIR + error_master |
| Identity Gate Failed | `IDENTITY_GATE_FAILED` | ABORT + AIR + error_master |
| EIN Format Invalid | `EIN_FORMAT_INVALID` | ABORT + AIR + error_master |
| Hash Verification Failed | `HASH_VERIFICATION_FAILED` | ABORT + AIR + error_master |

### Execution Order (CANONICAL)

```
Company Target (PASS)
        ↓
DOL Subhub — EIN Resolution
```

DOL **MUST NOT run** unless Company Target has completed with status `PASS`.

### Error Write Contract (CANONICAL)

```
process_id  = '01.04.02.04.22000'
agent_id    = 'DOL_EIN_SUBHUB'
severity    = 'HARD_FAIL'
```

### No Silent Failures

Every FAIL HARD path:
1. Checks Company Target gate (FIRST)
2. Emits AIR event
3. Writes to shq.error_master
4. Terminates execution

No retries. No swallowing errors. No fallback logic.

---

## ✅ Explicit Non-Goals Enforced

The following are **explicitly prohibited** in DOL Subhub:

```
❌ Assign scores
❌ Trigger outreach
❌ Detect intent
❌ Enrich people
❌ Infer anything beyond EIN linkage
❌ Create BIT events
❌ Integrate with Slack/Salesforce/Grafana
❌ Track OSHA/EEOC
❌ Generate alerts
❌ Influence downstream systems
```

---

## ✅ Files Changed Summary

### Created (New)

```
doctrine/ple/DOL_EIN_RESOLUTION.md
doctrine/schemas/dol_ein_linkage-schema.sql
doctrine/ple/DOL_REFACTOR_CONFIRMATION.md
ctb/sys/dol-ein/ein_validator.js
ctb/data/infra/migrations/010_dol_ein_error_index.sql
```

### Modified

```
doctrine/ple/PLE-Doctrine.md
doctrine/diagrams/PLE-Hub-Spoke-Axle.mmd
doctrine/README.md
ctb/docs/tasks/hub_tasks.md
doctrine/schemas/bit-schema.sql (dol_violation rule commented out)
```

### Deprecated (Previous Version)

```
(None created - Compliance-Doctrine.md was planned but never implemented)
```

---

## ✅ Deployment Checklist

### Pre-Deployment

- [ ] Review all documentation changes
- [ ] Verify schema SQL syntax
- [ ] Test `ein_validator.js` module
- [ ] Confirm identity gate validation logic

### Schema Deployment

```bash
# Deploy DOL EIN schema to Neon
psql $DATABASE_URL -f doctrine/schemas/dol_ein_linkage-schema.sql

# Verify tables created
psql $DATABASE_URL -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'dol';"
# Expected: ein_linkage, air_log

# Verify triggers created
psql $DATABASE_URL -c "SELECT trigger_name FROM information_schema.triggers WHERE event_object_schema = 'dol';"
# Expected: trg_block_ein_linkage_update, trg_block_ein_linkage_delete
```

### Post-Deployment Verification

- [ ] Test identity gate validation function
- [ ] Test EIN linkage insert function
- [ ] Verify append-only enforcement
- [ ] Confirm AIR logging works

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Architect | Barton Outreach Team | 2025-01-01 | ✅ |
| Doctrine Owner | | | |
| QA Review | | | |

---

**End of DOL Subhub Refactor Confirmation**

*This document confirms all scope corrections have been applied per the refactor directive.*
