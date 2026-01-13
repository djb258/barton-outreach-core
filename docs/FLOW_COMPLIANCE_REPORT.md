# DOL Sub-Hub Data Flow Compliance Report

**Audit Date**: 2025-01-07  
**Scope**: DOL Sub-Hub Data Flow Enforcement  
**Mode**: Structural Audit (Read-Only Inspection)

---

## Authoritative Flow Verification

### 1. Company Lifecycle (CL) — Sovereign ID Production

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Produces `company_unique_id` (sovereign) | ✅ PASS | [CC.md#L23](hubs/dol-filings/CC.md#L23): `company_unique_id | CL via CT | CONSUME ONLY` |
| No DOL access without CL ID existing | ✅ PASS | DOL reads via FK to `marketing.company_master` |

**Result**: ✅ **PASS**

---

### 2. Outreach Orchestration — Context Mapping

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Maps `company_unique_id → outreach_context_id` | ✅ PASS | [dol_ein_linkage-schema.sql#L100](docs/doctrine_ref/schemas/dol_ein_linkage-schema.sql#L100): `outreach_context_id VARCHAR(100) NOT NULL` |
| outreach_context_id is campaign-scoped | ✅ PASS | [VIOLATION_DISCOVERY_FLOW.md#L54-L66](docs/doctrine_ref/ple/VIOLATION_DISCOVERY_FLOW.md#L54-L66): Context minted by Outreach Orchestration |

**Result**: ✅ **PASS**

---

### 3. Company Target — Gate Enforcement

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Produces `company_target_status = PASS\|FAIL` | ✅ PASS | [PRD.md#L93](hubs/dol-filings/PRD.md#L93): `Company Target PASS | Validation | MUST have upstream PASS` |
| May perform fuzzy logic | ✅ PASS | Fuzzy exists in Company Target (not DOL) |
| Emits resolved EIN OR routes to `shq.error_master` | ⚠️ PARTIAL | Doctrine mandates dual-write; Python implementation missing (see Stage 7) |

**Result**: ⚠️ **PARTIAL** — Error routing not fully implemented in code

---

### 4. DOL Sub-Hub — Read-Only Inputs

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Receives `company_unique_id` | ✅ PASS | [dol_hub.py#L343-L356](hubs/dol-filings/imo/middle/dol_hub.py#L343-L356): Reads `company_unique_id` from Company Hub |
| Receives `outreach_context_id` | ✅ PASS | Required in `dol.ein_linkage` schema |
| Receives normalized company attributes | ✅ PASS | Name, state, domain from Company Target |
| **MUST NOT mint identity** | ⚠️ VIOLATION | See Violation V-001 below |
| **MUST NOT alter CL data** | ❌ VIOLATION | See Violation V-002 below |
| **MUST NOT emit outreach triggers** | ❌ VIOLATION | See Violation V-003 below |

**Result**: ❌ **FAIL** — 3 violations detected

---

### 5. DOL EIN Resolution — Fuzzy Discovery + Deterministic Confirmation

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Fuzzy discovery ONLY to locate EIN candidates | ✅ PASS | [ein_matcher.py#L99-L110](hubs/dol-filings/imo/middle/ein_matcher.py#L99-L110): Trigram similarity for candidate discovery |
| Uses upstream truth as constraints | ✅ PASS | State + city exact match required before fuzzy name |
| Deterministic EIN confirmation REQUIRED | ✅ PASS | [dol_hub.py#L313-L340](hubs/dol-filings/imo/middle/dol_hub.py#L313-L340): Exact EIN match only |
| Writes append-only to `dol.ein_linkage` | ✅ PASS | [dol_ein_linkage-schema.sql#L221-L253](docs/doctrine_ref/schemas/dol_ein_linkage-schema.sql#L221-L253): Triggers block UPDATE/DELETE |

**Result**: ✅ **PASS**

---

### 6. Violation Discovery — Join Discipline

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Joins ONLY via EIN → ein_linkage | ✅ PASS | [dol_violations-schema.sql#L242](docs/doctrine_ref/schemas/dol_violations-schema.sql#L242): `JOIN dol.violations v ON el.ein = v.ein` |
| Populates `ein` | ✅ PASS | [dol_violations-schema.sql#L56](docs/doctrine_ref/schemas/dol_violations-schema.sql#L56): `ein VARCHAR(10) NOT NULL` |
| Populates `outreach_context_id` | ✅ PASS | [dol_violations-schema.sql#L98](docs/doctrine_ref/schemas/dol_violations-schema.sql#L98): `outreach_context_id VARCHAR(100)` |
| Populates `company_unique_id` | ✅ PASS | [dol_violations-schema.sql#L59](docs/doctrine_ref/schemas/dol_violations-schema.sql#L59): `company_unique_id VARCHAR(50)` |
| Writes facts only to `dol.violations` | ✅ PASS | Append-only triggers enforced |

**Result**: ✅ **PASS**

---

### 7. Failure Discipline — Dual-Write Enforcement

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Write AIR event on failure | ✅ PASS | [dol_ein_linkage-schema.sql#L327-L496](docs/doctrine_ref/schemas/dol_ein_linkage-schema.sql#L327-L496): All failure paths insert to `dol.air_log` |
| Write to `shq.error_master` on failure | ⚠️ DOCTRINE ONLY | Mandated in [DOL_EIN_RESOLUTION.md#L351-L355](docs/doctrine_ref/ple/DOL_EIN_RESOLUTION.md#L351-L355), but **no implementation found** in Python code |
| NO silent drops | ⚠️ PARTIAL | AIR captures failures, but `shq.error_master` not written |

**Result**: ⚠️ **PARTIAL** — `shq.error_master` dual-write not implemented in code

---

## Violations Detected

### V-001: DOL Updates `company_master.ein` (Identity Alteration)

| Field | Value |
|-------|-------|
| **Severity** | HIGH |
| **File** | [hubs/dol-filings/imo/middle/ein_matcher.py#L159](hubs/dol-filings/imo/middle/ein_matcher.py#L159) |
| **Code** | `UPDATE company.company_master SET ein = %s ...` |
| **Violation** | DOL Sub-Hub writes to `company_master`, altering CL-owned data |
| **Doctrine** | DOL MUST NOT alter CL data — identity is sovereign |

**Required Action**: Remove UPDATE to `company_master`. EIN should be written to `dol.ein_linkage` only; Company Hub should consume EIN from linkage table.

---

### V-002: DOL Queries `company_master` Directly (Join Discipline Violation)

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Files** | [ein_matcher.py#L69-L103](hubs/dol-filings/imo/middle/ein_matcher.py#L69-L103), [dol_hub.py#L367](hubs/dol-filings/imo/middle/dol_hub.py#L367) |
| **Code** | `FROM company.company_master`, `SELECT company_unique_id FROM company.company_master` |
| **Violation** | DOL joins directly to `company_master` instead of via `dol.ein_linkage` |
| **Doctrine** | DOL should receive `company_unique_id` from Company Target, not query CL directly |

**Required Action**: DOL should receive `company_unique_id` via spoke contract, not query `company_master`.

---

### V-003: DOL Emits BIT Signals (Boundary Violation)

| Field | Value |
|-------|-------|
| **Severity** | HIGH |
| **File** | [hubs/dol-filings/imo/middle/dol_hub.py#L21](hubs/dol-filings/imo/middle/dol_hub.py#L21), [#L190](hubs/dol-filings/imo/middle/dol_hub.py#L190), [#L200](hubs/dol-filings/imo/middle/dol_hub.py#L200), [#L279](hubs/dol-filings/imo/middle/dol_hub.py#L279) |
| **Code** | `from hub.company.bit_engine import BITEngine, SignalType`; `SignalType.FORM_5500_FILED`, `SignalType.LARGE_PLAN`, `SignalType.BROKER_CHANGE` |
| **Violation** | DOL emits BIT signals directly, violating doctrine isolation |
| **Doctrine** | DOL has NO CONNECTION to BIT Axle — emits facts only |

**Required Action**: Remove BITEngine integration from DOL Hub. BIT should consume DOL facts via views (`dol.ein_linkage`, `analytics.v_5500_*`).

---

### V-004: Pipeline Documentation Shows BIT Integration

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **File** | [hubs/dol-filings/pipeline.md#L61](hubs/dol-filings/pipeline.md#L61) |
| **Code** | `EMIT: BIT Signals ... FORM_5500_FILED (+5.0) ... LARGE_PLAN (+8.0)` |
| **Violation** | Pipeline documentation describes BIT signal emission |
| **Doctrine** | DOL is isolated from BIT — pipeline doc must be updated |

**Required Action**: Update pipeline.md to remove BIT signal emission references.

---

### V-005: Missing `shq.error_master` Dual-Write in Python

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Files** | All files in `hubs/dol-filings/**` |
| **Evidence** | Grep for `shq.error_master` returns 0 matches |
| **Violation** | Doctrine mandates dual-write (AIR + error_master); only AIR is implemented |
| **Doctrine** | All failures MUST write to both `dol.air_log` AND `shq.error_master` |

**Required Action**: Implement `shq.error_master` writes on all FAIL HARD paths in DOL Python code.

---

## Summary

| Stage | Status |
|-------|--------|
| 1. Company Lifecycle (CL) | ✅ PASS |
| 2. Outreach Orchestration | ✅ PASS |
| 3. Company Target Gate | ⚠️ PARTIAL |
| 4. DOL Sub-Hub Read-Only Inputs | ❌ FAIL (3 violations) |
| 5. DOL EIN Resolution | ✅ PASS |
| 6. Violation Discovery | ✅ PASS |
| 7. Failure Discipline | ⚠️ PARTIAL |

---

## Overall Compliance Status

### ❌ **FAIL** — Flow Contract NOT Locked

**Blocking Issues (Must Fix)**:

1. **V-001**: DOL updates `company_master.ein` — violates CL sovereignty
2. **V-003**: DOL emits BIT signals — violates isolation boundary

**Non-Blocking Issues (Should Fix)**:

3. **V-002**: DOL queries `company_master` directly — should use spoke contract
4. **V-004**: Pipeline.md documents BIT integration — needs update
5. **V-005**: Missing `shq.error_master` dual-write — operational gap

---

## Recommended Guard Additions

### Guard 1: Block EIN Writes to company_master from DOL

Add assertion in `ein_matcher.py` before any UPDATE:

```python
# DOCTRINE GUARD: DOL MUST NOT update company_master
raise DoctrineViolation(
    "DOL Sub-Hub cannot update company_master. "
    "EIN should be written to dol.ein_linkage only."
)
```

### Guard 2: Remove BITEngine Import from DOL Hub

Remove from `dol_hub.py`:

```python
# REMOVE: DOL has NO CONNECTION to BIT
# from hub.company.bit_engine import BITEngine, SignalType
```

### Guard 3: Add Error Master Write Function

Add to DOL failure paths:

```python
def write_error_master(error_code: str, context: dict) -> None:
    """DOCTRINE: Dual-write to shq.error_master on all failures."""
    # Implementation required
    pass
```

---

## Sign-Off Criteria

Before DOL Sub-Hub can be locked as `v1.0 (Barton-Locked)`:

- [ ] V-001 resolved: No writes to `company_master` from DOL
- [ ] V-003 resolved: No BIT signal emission from DOL
- [ ] V-005 resolved: `shq.error_master` dual-write implemented
- [ ] Pipeline.md updated to remove BIT references
- [ ] Re-audit confirms all stages PASS

---

**End of Flow Compliance Report**

*This report enforces doctrine — it does not invent it.*
