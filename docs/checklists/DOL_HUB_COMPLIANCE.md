# DOL Sub-Hub Compliance Checklist

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | 1.1.0 |
| **CC Layer** | CC-02 |
| **Hub ID** | HUB-DOL-FILINGS |
| **Doctrine ID** | 04.04.03 |
| **Checklist Date** | 2026-01-15 |

---

## Instructions

All items must be checked (✓) before the hub can be promoted to production. This is a **binary gate** - partial completion is not acceptable.

---

## 1. CC Compliance

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1.1 | Hub has valid CC-02 PRD | ✓ | `docs/prd/PRD_DOL_SUBHUB.md` v3.0 |
| 1.2 | Hub has approved ADRs for major decisions | ✓ | `docs/adr/ADR-004_*.md` |
| 1.3 | Hub does not violate CC layer boundaries | ✓ | No direct writes to other hub tables |
| 1.4 | Hub respects parent-child doctrine | ✓ | Consumes company_unique_id, does not mint |

---

## 2. Hub Identity

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 2.1 | Hub manifest exists | ✓ | `hubs/dol-filings/hub.manifest.yaml` |
| 2.2 | Hub has unique doctrine ID | ✓ | 04.04.03 |
| 2.3 | Hub ownership statement is clear | ✓ | PRD Section: Sub-Hub Ownership Statement |
| 2.4 | Hub has defined core metric | ✓ | FILING_MATCH_RATE |

---

## 3. CTB Placement

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 3.1 | Hub files in correct directory structure | ✓ | `hubs/dol-filings/` |
| 3.2 | IMO structure follows convention | ✓ | `imo/input/`, `imo/middle/`, `imo/output/` |
| 3.3 | No files outside designated paths | ✓ | All code in hubs/dol-filings/ |

---

## 4. IMO Structure Compliance

### 4.1 Ingress Layer (I)

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 4.1.1 | Ingress only handles input validation | ✓ | CSV parsing, column normalization |
| 4.1.2 | Ingress does not contain business logic | ✓ | Logic in middle layer |
| 4.1.3 | Ingress does not make decisions | ✓ | Pass-through to middle |

### 4.2 Middle Layer (M)

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 4.2.1 | All business logic in middle layer | ✓ | `import_dol_full.py`, `build_column_metadata.py` |
| 4.2.2 | Transformations contained in middle | ✓ | EIN matching, signal emission |
| 4.2.3 | Tools registered and scoped | ✓ | PRD Section 10: Tooling Declaration |

### 4.3 Egress Layer (O)

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 4.3.1 | Egress is read-only view | ✓ | `dol.search_columns()`, `dol.get_table_schema()` |
| 4.3.2 | Egress does not mutate state | ✓ | Query functions only |
| 4.3.3 | Output contracts defined | ✓ | BIT signal emission |

---

## 5. Spoke Compliance

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 5.1 | Spokes contain no logic | ✓ | Signal emission is I/O only |
| 5.2 | Spokes contain no state | ✓ | Stateless pass-through |
| 5.3 | Spoke contracts documented | ✓ | PRD Section 9: Signal Emission |
| 5.4 | Spoke direction is unidirectional | ✓ | DOL → BIT Engine signals |

---

## 6. Database Compliance

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 6.1 | Schema follows naming convention | ✓ | `dol.*` schema |
| 6.2 | RLS policies enabled | ✓ | All tables have RLS |
| 6.3 | Tables have audit columns | ✓ | `created_at`, `updated_at` |
| 6.4 | Migrations documented | ✓ | `migrations/2026-01-15-*.sql` |
| 6.5 | **Read-only lock enforced** | ✓ | Trigger-based protection |

---

## 7. Data Integrity

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 7.1 | Source data is authoritative (DOL) | ✓ | U.S. Department of Labor EFAST2 |
| 7.2 | Data import is idempotent | ✓ | Year-based replacement |
| 7.3 | Column metadata is complete | ✓ | 441 columns documented |
| 7.4 | Search functions tested | ✓ | `dol.search_columns()` verified |

---

## 8. Guard Rails

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 8.1 | Kill switches documented | ✓ | PRD Section 11: Kill Switches |
| 8.2 | Kill switches tested | ✓ | `KILL_DOL_SUBHUB` verified |
| 8.3 | Rate limits defined | N/A | Annual bulk import, no API calls |
| 8.4 | Timeouts configured | N/A | Batch processing, no real-time |

---

## 9. Error Handling

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 9.1 | Error codes defined | ✓ | DOL-001 through DOL-005 |
| 9.2 | Correlation ID propagated | ✓ | PRD Section 8 |
| 9.3 | Local failure table exists | ✓ | `dol_subhub.failures` |
| 9.4 | Global emit rules defined | ✓ | HIGH severity → shq_error_log |

---

## 10. Observability

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 10.1 | Metrics defined | ✓ | `dol.processed.total`, etc. |
| 10.2 | Logging format standardized | ✓ | Structured logging with sub_hub field |
| 10.3 | Processing stats available | ✓ | `get_stats()` method |

---

## 11. Documentation

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 11.1 | PRD complete and current | ✓ | v3.0, 2026-01-15 |
| 11.2 | ADR(s) approved | ✓ | ADR-004 accepted |
| 11.3 | ERD created | ✓ | `doctrine/diagrams/DOL_Schema_ERD.mmd` |
| 11.4 | API reference documented | ✓ | PRD Section 5: Search Functions |

---

## 12. Data Statistics (2023 Import)

| Table | Rows | Columns | Verified |
|-------|------|---------|----------|
| form_5500 | 230,482 | 147 | ✓ |
| form_5500_sf | 760,839 | 196 | ✓ |
| schedule_a | 337,476 | 98 | ✓ |
| column_metadata | 441 | 12 | ✓ |

---

## 13. Promotion Gates

| Gate | Requirement | Status |
|------|-------------|--------|
| G1 | PRD approved | ✓ PASS |
| G2 | ADRs documented | ✓ PASS |
| G3 | Data imported | ✓ PASS |
| G4 | Read-only lock | ✓ PASS |
| G5 | Metadata complete | ✓ PASS |
| G6 | RLS policies active | ✓ PASS |
| G7 | Compliance checklist complete | ✓ PASS |

---

## Final Approval

| Role | Approver | Date | Signature |
|------|----------|------|-----------|
| Hub Owner | DOL Sub-Hub | 2026-01-15 | ✓ |
| Reviewer | Claude Code | 2026-01-15 | ✓ |

---

## Notes

- All DOL data tables are **READ-ONLY** except during annual import
- Import bypass requires: `SET session dol.import_mode = 'active'`
- Form 5500-SF does NOT have Schedule A attachments (by DOL design)
- 70% of plans have January renewal month

---

*Checklist Version: 1.0*
*Last Updated: 2026-01-15*
*CC Layer: CC-02*
