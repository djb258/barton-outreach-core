# CTB Guardrail Status Report

**Generated**: 2026-02-06T10:35:57.005478

---

## 1. CTB Registry Status

| Metric | Value |
|--------|-------|
| Total Registered | 246 |
| Frozen (Immutable) | 9 |

### Leaf Type Distribution

| Leaf Type | Count |
|-----------|-------|
| ARCHIVE | 112 |
| CANONICAL | 50 |
| SYSTEM | 23 |
| DEPRECATED | 21 |
| ERROR | 14 |
| STAGING | 12 |
| MV | 8 |
| REGISTRY | 6 |

## 2. NOT NULL Constraint Status

| Table | Column | NOT NULL |
|-------|--------|----------|
| outreach.dol_errors | error_type | YES |
| outreach.blog_errors | error_type | YES |
| cl.cl_errors_archive | error_type | YES |
| people.people_errors | error_type | YES |

## 3. Frozen Core Tables

| Schema | Table |
|--------|-------|
| cl | company_identity |
| outreach | bit_scores |
| outreach | blog |
| outreach | company_target |
| outreach | dol |
| outreach | outreach |
| outreach | people |
| people | company_slot |
| people | people_master |

## 4. Event Trigger Status

*No CTB event triggers installed (optional enforcement)*

## 5. Violation Log Status

| Metric | Value |
|--------|-------|
| Total Violations | 0 |

---

## Document Control

| Field | Value |
|-------|-------|
| Generated | 2026-02-06T10:35:57.405041 |
| Phase | CTB Phase 3 |
| Type | GUARDRAIL STATUS |
