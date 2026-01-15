# ADR: DOL 2023 Data Import with Read-Only Lock and AI-Ready Metadata

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | 1.1.0 |
| **CC Layer** | CC-03 |

---

## ADR Identity

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-004 |
| **Status** | [x] Accepted |
| **Date** | 2026-01-15 |

---

## Owning Hub (CC-02)

| Field | Value |
|-------|-------|
| **Sovereign ID** | BARTON-OUTREACH |
| **Hub Name** | DOL Sub-Hub |
| **Hub ID** | HUB-DOL-FILINGS |

---

## CC Layer Scope

| Layer | Affected | Description |
|-------|----------|-------------|
| CC-01 (Sovereign) | [ ] | No sovereign-level changes |
| CC-02 (Hub) | [x] | PRD updated with new data schema and metadata |
| CC-03 (Context) | [x] | Data import process, read-only enforcement, search functions |
| CC-04 (Process) | [x] | Import scripts, metadata builder, SQL migrations |

---

## IMO Layer Scope

| Layer | Affected |
|-------|----------|
| I — Ingress | [x] DOL EFAST2 bulk data import |
| M — Middle | [x] Data processing, metadata generation |
| O — Egress | [x] Query interface, search functions |

---

## Constant vs Variable

| Classification | Value |
|----------------|-------|
| **This decision defines** | [x] Constant (structure/meaning) |
| **Mutability** | [x] Immutable (DOL data is authoritative, annual refresh only) |

---

## Context

The DOL Sub-Hub required complete 2023 EFAST2 data to enable:

1. **EIN Matching** - Link DOL filings to Company Hub records
2. **Broker Intelligence** - Track insurance brokers, carriers, and commissions
3. **Renewal Detection** - Identify plan renewal months for outreach timing
4. **BIT Signals** - Emit buyer intent signals based on filing characteristics

Previous state:
- DOL schema tables existed but were empty (0 rows)
- Column definitions were incomplete (missing broker/carrier fields)
- No metadata documentation for AI/human consumption
- No protection against accidental data modification

---

## Decision

### 1. Import Full DOL 2023 Dataset

Import all columns from the U.S. Department of Labor EFAST2 system:

| Table | Rows | Columns | Source |
|-------|------|---------|--------|
| form_5500 | 230,482 | 147 | f_5500_2023_latest.csv |
| form_5500_sf | 760,839 | 196 | f_5500_sf_2023_latest.csv |
| schedule_a | 337,476 | 98 | F_SCH_A_2023_latest.csv |

### 2. Implement Read-Only Lock

Enforce read-only access on DOL tables using PostgreSQL BEFORE triggers:

```sql
-- Blocks INSERT, UPDATE, DELETE unless import_mode is active
CREATE TRIGGER dol_form_5500_readonly_insert
    BEFORE INSERT ON dol.form_5500
    FOR EACH ROW EXECUTE FUNCTION dol.form_5500_readonly_guard();
```

Bypass mechanism for annual imports:
```sql
SET session dol.import_mode = 'active';
-- import operations --
RESET dol.import_mode;
```

### 3. Create AI-Ready Column Metadata

Document all 441 columns with:
- Unique column IDs (e.g., `DOL_F5500_SPONSOR_DFE_NAME`)
- Human-readable descriptions
- Data format patterns (CURRENCY, DATE, FLAG, EIN)
- Search keywords for natural language queries
- Category classification (Sponsor, Insurance, Welfare, Pension)

Provide search functions:
```sql
SELECT * FROM dol.search_columns('broker');
SELECT * FROM dol.get_table_schema('schedule_a');
```

---

## Alternatives Considered

| Option | Why Not Chosen |
|--------|----------------|
| Import only key columns | Would miss broker fees, welfare indicators, renewal dates needed for BIT signals |
| Use database permissions instead of triggers | Permissions are role-based; triggers provide operation-level granularity and clear error messages |
| Manual documentation in markdown only | Not searchable; metadata table enables programmatic access and AI consumption |
| Do Nothing | DOL data essential for EIN matching and outreach timing |

---

## Consequences

### Enables

- EIN-to-company matching for 991,321 total filings
- Broker intelligence queries (235K+ records with commission data)
- Renewal month detection (70% of plans renew in January)
- State-based filtering for targeted outreach
- AI/LLM consumption of column metadata via search functions
- Annual data refresh without schema changes

### Prevents

- Accidental modification of authoritative DOL data
- Schema drift between annual imports
- Ambiguous column naming (standardized IDs)
- Manual lookup of column definitions (searchable metadata)

---

## PID Impact (if CC-04 affected)

| Field | Value |
|-------|-------|
| **New PID required** | [x] Yes - DOL import PIDs |
| **PID pattern change** | [ ] No |
| **Audit trail impact** | Import operations logged with timestamp |

---

## Guard Rails

| Type | Value | CC Layer |
|------|-------|----------|
| Read-Only Lock | Trigger-based, blocks INSERT/UPDATE/DELETE | CC-04 |
| Import Bypass | Session variable `dol.import_mode` | CC-04 |
| Annual Refresh | Data replaced per-year, not appended | CC-03 |
| Error Code | DOL-005 for read-only violations | CC-03 |

---

## Rollback

If this decision fails:

1. Disable read-only triggers:
   ```sql
   DROP TRIGGER dol_form_5500_readonly_insert ON dol.form_5500;
   -- repeat for all triggers
   ```

2. Data can be re-imported from source CSV files stored in `data/dol_2023/`

3. Metadata table can be dropped and regenerated:
   ```sql
   DROP TABLE dol.column_metadata CASCADE;
   ```

---

## Traceability

| Artifact | Reference |
|----------|-----------|
| Canonical Doctrine | CANONICAL_ARCHITECTURE_DOCTRINE.md |
| PRD | docs/prd/PRD_DOL_SUBHUB.md (v3.0) |
| Work Items | DOL-2023-IMPORT |
| PR(s) | (To be created) |

### Files Created/Modified

| File | Purpose |
|------|---------|
| `infra/migrations/2026-01-15-dol-readonly-lock.sql` | Read-only trigger migration |
| `infra/migrations/2026-01-15-dol-column-metadata.sql` | Metadata table schema |
| `hubs/dol-filings/imo/middle/importers/import_dol_full.py` | Full-column data import |
| `hubs/dol-filings/imo/middle/importers/build_column_metadata.py` | Metadata generator |
| `docs/prd/PRD_DOL_SUBHUB.md` | Updated to v3.0 |

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner (CC-02) | DOL Sub-Hub | 2026-01-15 |
| Reviewer | Claude Code | 2026-01-15 |

---

## Technical Details

### Data Statistics

```
Form 5500:     230,482 rows × 147 columns = 33.9M cells
Form 5500-SF:  760,839 rows × 196 columns = 149.1M cells
Schedule A:    337,476 rows × 98 columns  = 33.1M cells
─────────────────────────────────────────────────────────
Total:         1,328,797 rows × 441 unique columns
```

### Key Query Patterns

```sql
-- Find companies with broker data in Texas
SELECT sponsor_name, ins_carrier_name, ins_broker_comm_tot_amt
FROM dol.schedule_a
WHERE sponsor_state = 'TX'
  AND ins_broker_comm_tot_amt > 0;

-- Get renewal month distribution
SELECT SUBSTRING(sch_a_plan_year_begin_date, 6, 2) as month, COUNT(*)
FROM dol.schedule_a
GROUP BY 1 ORDER BY 2 DESC;

-- Search for health benefit columns
SELECT column_id, description
FROM dol.column_metadata
WHERE 'health' = ANY(search_keywords);
```

### Import Trigger Protection

```
Normal Operation:
  INSERT → DOL_READONLY_VIOLATION (blocked)
  UPDATE → DOL_READONLY_VIOLATION (blocked)
  DELETE → DOL_READONLY_VIOLATION (blocked)
  SELECT → Allowed

Import Mode (dol.import_mode = 'active'):
  INSERT → Allowed
  UPDATE → Allowed
  DELETE → Allowed
  SELECT → Allowed
```

---

*ADR Version: 1.0*
*Created: 2026-01-15*
*CC Layer: CC-03*
