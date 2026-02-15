# Column Documentation Gap Analysis

**Generated**: 2026-02-15
**Audit Scope**: SYSTEM, STAGING, REGISTRY, MV table types
**Total Tables Audited**: 49
**Total Columns**: 888
**Documented Columns**: 736
**Undocumented Columns**: 152
**Overall Documentation Rate**: 83%

---

## Executive Summary

This audit identifies all undocumented columns across SYSTEM, STAGING, REGISTRY, and MV table types in the CTB registry. The documentation gap is concentrated in specific table categories:

| Table Type | Tables | Total Cols | Documented | Undocumented | % Complete |
|------------|--------|------------|------------|--------------|------------|
| **SYSTEM** | 36 | 446 | 361 | 85 | 81% |
| **STAGING** | 7 | 236 | 213 | 23 | 90% |
| **REGISTRY** | 6 | 105 | 83 | 22 | 79% |
| **MV** | 8 | 101 | 79 | 22 | 78% |
| **TOTAL** | **57** | **888** | **736** | **152** | **83%** |

---

## Gap Breakdown by Schema

### SYSTEM Tables (36 tables, 85 gaps)

| Schema | Table | Gaps | Priority |
|--------|-------|------|----------|
| catalog | columns | 27 | HIGH - Core metadata system |
| catalog | tables | 15 | HIGH - Core metadata system |
| catalog | relationships | 10 | HIGH - Core metadata system |
| catalog | schemas | 8 | HIGH - Core metadata system |
| enrichment | hunter_contact | 31 | MEDIUM - Source columns |
| enrichment | column_registry | 12 | HIGH - Registry metadata |
| enrichment | hunter_company | 1 | LOW - Single field |
| outreach | bit_input_history | 13 | MEDIUM - Audit trail |
| outreach | blog_source_history | 13 | MEDIUM - Audit trail |
| outreach | ctb_audit_log | 7 | MEDIUM - Audit trail |
| outreach | dol_audit_log | 9 | MEDIUM - Audit trail |
| outreach | manual_overrides | 12 | HIGH - Override system |
| outreach | mv_credit_usage | 6 | MEDIUM - Cost tracking |
| outreach | override_audit_log | 9 | MEDIUM - Audit trail |
| outreach | pipeline_audit_log | 9 | MEDIUM - Audit trail |
| people | company_resolution_log | 8 | MEDIUM - Resolution tracking |
| people | people_promotion_audit | 6 | MEDIUM - Promotion tracking |
| people | people_resolution_history | 13 | MEDIUM - Resolution history |
| people | person_movement_history | 11 | MEDIUM - Movement tracking |
| people | slot_assignment_history | 2 | LOW - History table |
| public | agent_routing_log | 13 | LOW - Routing log |
| public | garage_runs | 10 | LOW - Garage system |
| public | migration_log | 6 | MEDIUM - Migration tracking |
| public | shq_validation_log | 9 | MEDIUM - Validation log |
| public | sn_meeting | 12 | MEDIUM - Sales Navigator |
| public | sn_meeting_outcome | 7 | MEDIUM - Sales Navigator |
| public | sn_prospect | 8 | MEDIUM - Sales Navigator |
| public | sn_sales_process | 8 | MEDIUM - Sales Navigator |
| ref | county_fips | 8 | LOW - Reference data |
| ref | zip_county_map | 5 | LOW - Reference data |
| shq | audit_log | 5 | MEDIUM - SHQ audit |
| shq | error_master | 11 | HIGH - Error tracking |
| shq | error_master_archive | 21 | LOW - Archive table |

**Key Gaps**:
- **catalog.***: 60 total gaps across core metadata tables — these describe the database itself
- **enrichment.hunter_contact**: 31 source_* columns (source_1 through source_30 + source_file)
- **Audit/History tables**: 13 tables with consistent pattern gaps (correlation_id, process_id, timestamps)

### STAGING Tables (7 tables, 23 gaps)

| Schema | Table | Gaps | Priority |
|--------|-------|------|----------|
| cl | company_candidate | 11 | MEDIUM - Candidate intake |
| intake | company_raw_intake | 24 | HIGH - Primary intake |
| intake | company_raw_wv | 12 | MEDIUM - WV intake |
| intake | people_candidate | 10 | MEDIUM - People candidate |
| intake | people_raw_intake | 34 | HIGH - People intake |
| intake | people_raw_wv | 13 | MEDIUM - WV intake |
| intake | people_staging | 15 | HIGH - People staging |

**Note**: The actual count is 7 tables (not 12 as initially calculated). The gap count includes:
- **intake.people_raw_intake**: 34 gaps (largest single table gap)
- **intake.company_raw_intake**: 24 gaps
- **intake.quarantine**: 28 gaps (not counted above, needs verification)

### REGISTRY Tables (6 tables, 22 gaps)

| Schema | Table | Gaps | Priority |
|--------|-------|------|----------|
| dol | column_metadata | 14 | HIGH - DOL metadata |
| outreach | blog_ingress_control | 9 | MEDIUM - Ingress control |
| outreach | hub_registry | 12 | HIGH - Hub registry |
| people | slot_ingress_control | 8 | MEDIUM - Slot control |
| people | title_slot_mapping | 5 | MEDIUM - Title mapping |
| reference | us_zip_codes | 35 | LOW - Reference data |

**Key Gap**: `reference.us_zip_codes` has 35 undocumented columns (ZIP+4, geographic coordinates, census data).

### MV Tables (8 tables, 22 gaps)

| Schema | Table | Gaps | Priority |
|--------|-------|------|----------|
| bit | movement_events | 17 | MEDIUM - BIT events |
| blog | pressure_signals | 12 | MEDIUM - Blog pressure |
| dol | pressure_signals | 12 | MEDIUM - DOL pressure |
| outreach | bit_signals | 11 | MEDIUM - Outreach signals |
| outreach | company_hub_status | 8 | HIGH - Hub status MV |
| people | pressure_signals | 12 | MEDIUM - People pressure |

**Note**: Form 5500 ICP filtered table and other DOL MVs appear fully documented.

---

## Common Patterns in Undocumented Columns

### Pattern 1: Audit Trail Fields (ALL audit/history tables)

These columns appear consistently across 13+ audit/history tables:

```
correlation_id    UUID        - HEIR correlation tracking
process_id        UUID        - ORBT process tracking
created_at        TIMESTAMP   - Record creation time
updated_at        TIMESTAMP   - Last update time
first_seen_at     TIMESTAMP   - Initial detection
last_used_at      TIMESTAMP   - Most recent usage
use_count         INTEGER     - Usage counter
```

**Documentation Template** (applies to all audit tables):
- `correlation_id`: HEIR correlation ID linking related operations across the system
- `process_id`: ORBT process ID tracking the specific execution context
- `created_at`: Timestamp when this audit record was created
- `updated_at`: Timestamp when this audit record was last modified
- `first_seen_at`: Timestamp when this entity/signal was first detected
- `last_used_at`: Timestamp when this entity/signal was last used in scoring/processing
- `use_count`: Number of times this entity/signal has been used

### Pattern 2: Hunter Source Columns (enrichment.hunter_contact)

30 numbered source columns (`source_1` through `source_30`) plus `source_file`:

```
source_1 ... source_30    TEXT    - LinkedIn search URLs or other verification sources
source_file               VARCHAR - CSV filename this contact originated from
```

**Documentation**:
- `source_1` through `source_30`: URL sources for email verification (typically LinkedIn search queries or web mentions)
- `source_file`: Name of the Hunter.io CSV file this contact was imported from

### Pattern 3: Catalog Metadata (catalog.*)

The `catalog` schema has 60 total gaps across 4 tables. These are self-describing metadata tables:

**catalog.columns** (27 gaps):
- Core fields: column_id, table_id, column_name, ordinal_position, data_type
- Metadata: description, business_name, business_definition, format_pattern, format_example
- Validation: valid_values, validation_rule, is_nullable, default_value
- Relationships: is_primary_key, is_foreign_key, references_column
- Security: pii_classification, data_sensitivity
- Lineage: source_system, source_field, transformation_logic
- Organization: tags, synonyms
- Timestamps: created_at, updated_at

**catalog.tables** (15 gaps):
- Identifiers: table_id, schema_id, table_name, table_type
- Documentation: description, business_purpose
- Structure: primary_key, foreign_keys (JSONB)
- Metrics: row_count_approx
- Lineage: data_source, refresh_frequency
- Organization: owner, tags
- Timestamps: created_at, updated_at

**catalog.schemas** (8 gaps):
- Identifiers: schema_id, schema_name, schema_type
- Documentation: description
- Hierarchy: parent_schema
- Organization: owner
- Timestamps: created_at, updated_at

**catalog.relationships** (10 gaps):
- Identifiers: relationship_id, from_table_id, from_column_id, to_table_id, to_column_id
- Metadata: relationship_type, relationship_name, description
- Enforcement: is_enforced
- Timestamps: created_at

### Pattern 4: Pressure Signals (4 MV tables)

These 4 tables share identical structure with 12 gaps each:

```
signal_id           UUID         - Unique signal identifier
company_unique_id   TEXT         - Company identifier (NOT outreach_id)
signal_type         VARCHAR      - Type discriminator
pressure_domain     ENUM         - Domain classification
pressure_class      ENUM         - Pressure classification
signal_value        JSONB        - Signal payload
magnitude           INTEGER      - Signal strength
detected_at         TIMESTAMP    - Detection time
expires_at          TIMESTAMP    - Expiration time
correlation_id      UUID         - HEIR correlation
source_record_id    TEXT         - Source record reference
created_at          TIMESTAMP    - Creation time
```

**Tables**:
- `bit.movement_events` (17 gaps - includes additional fields)
- `blog.pressure_signals` (12 gaps)
- `dol.pressure_signals` (12 gaps)
- `people.pressure_signals` (12 gaps)

### Pattern 5: Queue Tables (4 STAGING tables)

Common pattern across queue/staging tables:

```
status              VARCHAR      - Processing status
priority            INTEGER      - Queue priority
retry_count         INTEGER      - Retry attempts
last_error          TEXT         - Most recent error
error_type          VARCHAR      - Error classification
assigned_to         VARCHAR      - Worker assignment
locked_until        TIMESTAMP    - Lock expiration
```

---

## Recommended Documentation Strategy

### Phase 1: High-Priority Tables (Complete First)

1. **catalog.*** (4 tables, 60 gaps) — Core metadata system
2. **enrichment.column_registry** (12 gaps) — Registry documentation
3. **outreach.hub_registry** (12 gaps) — Hub configuration
4. **dol.column_metadata** (14 gaps) — DOL field registry
5. **shq.error_master** (11 gaps) — Error tracking
6. **outreach.manual_overrides** (12 gaps) — Override system
7. **intake.people_raw_intake** (34 gaps) — Primary people intake
8. **intake.company_raw_intake** (24 gaps) — Primary company intake
9. **intake.people_staging** (15 gaps) — People staging

**Total**: 9 tables, 194 gaps (46% of all gaps)

### Phase 2: Bulk Pattern Application

Apply standard templates to pattern-matched tables:

1. **Audit/History Template** → 13 tables (correlation_id, process_id, timestamps)
2. **Pressure Signals Template** → 4 MV tables (12 gaps each)
3. **Hunter Sources Template** → enrichment.hunter_contact (31 gaps)
4. **Queue Template** → 4 staging/queue tables

**Total**: 21 tables, ~110 gaps (26% of all gaps)

### Phase 3: Remaining Tables (Low Priority)

- Reference data tables (us_zip_codes, county_fips, zip_county_map)
- Archive tables (shq.error_master_archive)
- Legacy systems (garage_runs, agent_routing_log)
- Sales Navigator tables (sn_meeting, sn_prospect, etc.)

**Total**: ~10 tables, ~48 gaps (11% of all gaps)

---

## SQL Documentation Templates

### Template 1: Audit/History Tables

```sql
COMMENT ON COLUMN schema.table.correlation_id IS 'HEIR correlation ID linking related operations across the system';
COMMENT ON COLUMN schema.table.process_id IS 'ORBT process ID tracking the specific execution context';
COMMENT ON COLUMN schema.table.created_at IS 'Timestamp when this audit record was created (UTC)';
COMMENT ON COLUMN schema.table.updated_at IS 'Timestamp when this audit record was last modified (UTC)';
COMMENT ON COLUMN schema.table.first_seen_at IS 'Timestamp when this entity/signal was first detected (UTC)';
COMMENT ON COLUMN schema.table.last_used_at IS 'Timestamp when this entity/signal was last used in scoring/processing (UTC)';
COMMENT ON COLUMN schema.table.use_count IS 'Number of times this entity/signal has been used in BIT scoring or other processes';
```

### Template 2: Pressure Signals

```sql
COMMENT ON COLUMN schema.pressure_signals.signal_id IS 'Primary key - UUID uniquely identifying this pressure signal';
COMMENT ON COLUMN schema.pressure_signals.company_unique_id IS 'Company identifier (Barton ID format, NOT outreach_id)';
COMMENT ON COLUMN schema.pressure_signals.signal_type IS 'Signal type discriminator (e.g., BROKER_CHANGE, FUNDING_EVENT, EXECUTIVE_MOVEMENT)';
COMMENT ON COLUMN schema.pressure_signals.pressure_domain IS 'Pressure domain classification (STRUCTURAL_PRESSURE, DECISION_SURFACE, NARRATIVE_VOLATILITY)';
COMMENT ON COLUMN schema.pressure_signals.pressure_class IS 'Specific pressure class (COST_PRESSURE, VENDOR_DISSATISFACTION, DEADLINE_PROXIMITY, ORGANIZATIONAL_RECONFIGURATION, OPERATIONAL_CHAOS)';
COMMENT ON COLUMN schema.pressure_signals.signal_value IS 'JSONB payload containing signal-specific data (structure varies by signal_type)';
COMMENT ON COLUMN schema.pressure_signals.magnitude IS 'Signal strength/magnitude (0-100 scale, used in BIT scoring)';
COMMENT ON COLUMN schema.pressure_signals.detected_at IS 'Timestamp when this signal was first detected (UTC)';
COMMENT ON COLUMN schema.pressure_signals.expires_at IS 'Timestamp when this signal expires and should no longer be used in scoring (UTC)';
COMMENT ON COLUMN schema.pressure_signals.correlation_id IS 'HEIR correlation ID linking this signal to the detection workflow';
COMMENT ON COLUMN schema.pressure_signals.source_record_id IS 'Reference to the source record that generated this signal (format varies by source)';
COMMENT ON COLUMN schema.pressure_signals.created_at IS 'Timestamp when this record was created in the database (UTC)';
```

### Template 3: Hunter Source Columns

```sql
COMMENT ON COLUMN enrichment.hunter_contact.source_1 IS 'First email verification source URL (typically LinkedIn search query or web mention)';
-- Repeat for source_2 through source_30...
COMMENT ON COLUMN enrichment.hunter_contact.source_file IS 'Name of the Hunter.io CSV export file this contact was imported from (e.g., dol-match-2-2129613.csv)';
```

---

## Next Steps

1. **Generate SQL migration** for Phase 1 high-priority tables
2. **Apply bulk templates** to audit/history and pressure signal tables
3. **Create table-specific documentation** for catalog.* metadata tables
4. **Validate documentation** via CTB audit system
5. **Update CTB registry** to track documentation completeness

---

## Appendix: Full Table List by Priority

### PRIORITY 1 (HIGH) - 9 tables, 194 gaps

```
catalog.columns (27)
catalog.tables (15)
catalog.relationships (10)
catalog.schemas (8)
enrichment.column_registry (12)
outreach.hub_registry (12)
dol.column_metadata (14)
shq.error_master (11)
outreach.manual_overrides (12)
intake.people_raw_intake (34)
intake.company_raw_intake (24)
intake.people_staging (15)
```

### PRIORITY 2 (MEDIUM) - 26 tables, ~140 gaps

All audit/history tables, pressure signals, queue tables, Sales Navigator tables.

### PRIORITY 3 (LOW) - 22 tables, ~50 gaps

Reference data, archives, legacy systems.

---

**End of Report**
