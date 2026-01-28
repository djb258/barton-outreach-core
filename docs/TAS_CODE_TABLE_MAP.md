# Technical Architecture Specification: Code to Table Map

**Repository**: barton-outreach-core
**Version**: 1.0.0
**Generated**: 2026-01-28
**Purpose**: Which code writes to which tables — No guessing about data sources

---

## Hub Module → Table Mapping

### Company Target (04.04.01)

| Module | Path | Writes To | Read From |
|--------|------|-----------|-----------|
| company_hub.py | `hubs/company-target/imo/middle/` | `outreach.company_target` | `cl.company_identity`, `outreach.outreach` |
| bit_engine.py | `hubs/company-target/imo/middle/` | - | `outreach.bit_scores` |
| company_pipeline.py | `hubs/company-target/imo/middle/` | `outreach.company_target` | `cl.company_identity` |
| Phase1CompanyMatching | `hubs/company-target/imo/middle/phases/` | - | `cl.company_identity` |
| Phase2DomainResolution | `hubs/company-target/imo/middle/phases/` | `outreach.company_target` | `cl.company_identity` |
| Phase3EmailPatternWaterfall | `hubs/company-target/imo/middle/phases/` | `outreach.company_target` | - |
| Phase4PatternVerification | `hubs/company-target/imo/middle/phases/` | `outreach.company_target` | - |
| neon_writer.py | `hubs/company-target/imo/output/` | `outreach.company_target`, `outreach.company_target_errors` | - |

### DOL Filings (04.04.03)

| Module | Path | Writes To | Read From |
|--------|------|-----------|-----------|
| dol_hub.py | `hubs/dol-filings/imo/middle/` | `outreach.dol` | `outreach.outreach`, `dol.form_5500` |
| ein_matcher.py | `hubs/dol-filings/imo/middle/` | `outreach.dol` | `dol.form_5500`, `dol.ein_urls` |
| processors/*.py | `hubs/dol-filings/imo/middle/processors/` | `outreach.dol`, `outreach.dol_errors` | `dol.*` |
| importers/*.py | `hubs/dol-filings/imo/middle/importers/` | `dol.form_5500`, `dol.schedule_a` | External DOL data |

### People Intelligence (04.04.02)

| Module | Path | Writes To | Read From |
|--------|------|-----------|-----------|
| people_hub.py | `hubs/people-intelligence/imo/middle/` | `outreach.people` | `people.people_master` |
| slot_assignment.py | `hubs/people-intelligence/imo/middle/` | `people.company_slot` | `people.people_master` |
| Phase5EmailGeneration | `hubs/people-intelligence/imo/middle/phases/` | `outreach.people` | `outreach.company_target` |
| Phase6SlotAssignment | `hubs/people-intelligence/imo/middle/phases/` | `people.company_slot` | `people.people_master` |
| Phase7EnrichmentQueue | `hubs/people-intelligence/imo/middle/phases/` | `people.paid_enrichment_queue` | `people.people_master` |
| Phase8OutputWriter | `hubs/people-intelligence/imo/middle/phases/` | `outreach.people` | `people.company_slot` |
| ceo_email_pipeline.py | `hubs/people-intelligence/imo/middle/phases/` | `outreach.people`, `people.company_slot` | `people.people_master` |
| movement_engine/*.py | `hubs/people-intelligence/imo/middle/movement_engine/` | `people.person_movement_history` | `people.people_master` |

### Outreach Execution (04.04.04)

| Module | Path | Writes To | Read From |
|--------|------|-----------|-----------|
| outreach_hub.py | `hubs/outreach-execution/imo/middle/` | `outreach.campaigns`, `outreach.sequences` | `outreach.company_target` |
| campaign_manager.py | `hubs/outreach-execution/imo/middle/` | `outreach.campaigns` | - |
| sequence_manager.py | `hubs/outreach-execution/imo/middle/` | `outreach.sequences` | - |
| send_executor.py | `hubs/outreach-execution/imo/middle/` | `outreach.send_log` | `outreach.sequences` |

---

## Spoke → Table Mapping

| Spoke | Path | Direction | Tables Touched |
|-------|------|-----------|----------------|
| cl-identity | `spokes/signal-company/` | Ingress | READ: `cl.company_identity` |
| target-people | `spokes/company-people/` | Bidirectional | READ: `outreach.company_target`, `people.company_slot` |
| target-dol | `spokes/company-dol/` | Bidirectional | READ: `outreach.company_target`, `outreach.dol` |
| target-outreach | `spokes/company-outreach/` | Bidirectional | READ: `outreach.company_target` |
| people-outreach | `spokes/people-outreach/` | Bidirectional | READ: `outreach.people`, `people.people_master` |

**NOTE**: Spokes are I/O only — they READ but do NOT WRITE

---

## Ops/Enforcement → Table Mapping

| Module | Path | Writes To | Read From |
|--------|------|-----------|-----------|
| correlation_id.py | `ops/enforcement/` | - | - (UUID propagation) |
| hub_gate.py | `ops/enforcement/` | - | `outreach.company_target` |
| signal_dedup.py | `ops/enforcement/` | - | `outreach.bit_signals` |
| error_codes.py | `ops/enforcement/` | - | - (error definitions) |
| authority_gate.py | `ops/enforcement/` | - | `cl.company_identity` |

---

## Function → Table Quick Lookup

### "What writes to this table?"

| Table | Written By |
|-------|------------|
| `cl.company_identity` | External intake (NOT Outreach code) |
| `outreach.outreach` | Outreach init process |
| `outreach.company_target` | company_hub.py, company_pipeline.py, neon_writer.py |
| `outreach.dol` | dol_hub.py, ein_matcher.py |
| `outreach.people` | people_hub.py, ceo_email_pipeline.py |
| `outreach.blog` | blog_hub.py (if exists) |
| `outreach.bit_scores` | BIT calculation process |
| `outreach.bit_signals` | Signal detection processes |
| `outreach.manual_overrides` | Admin/manual processes only |
| `outreach.campaigns` | outreach_hub.py, campaign_manager.py |
| `outreach.sequences` | sequence_manager.py |
| `outreach.send_log` | send_executor.py |
| `people.people_master` | Enrichment imports |
| `people.company_slot` | slot_assignment.py, ceo_email_pipeline.py |
| `dol.form_5500` | DOL importers |
| `dol.schedule_a` | DOL importers |

### "What reads from this table?"

| Table | Read By |
|-------|---------|
| `cl.company_identity` | All hubs (for company lookup) |
| `outreach.outreach` | All sub-hubs (for outreach_id verification) |
| `outreach.company_target` | DOL hub, People hub, BIT engine |
| `outreach.dol` | People hub, BIT engine |
| `outreach.people` | Outreach execution |
| `outreach.bit_scores` | Campaign selection, marketing eligibility |
| `people.people_master` | People hub, Outreach people |
| `people.company_slot` | People hub, Outreach people |
| `dol.form_5500` | DOL hub, BIT engine |
| `dol.schedule_a` | DOL hub |

---

## Entry Points

### Pipeline Entry Points

| Entry Point | Script | First Table Written |
|-------------|--------|---------------------|
| Company intake | External | `cl.company_identity` |
| Outreach init | `outreach_init.py` | `outreach.outreach` |
| Company Target phase | `company_pipeline.py` | `outreach.company_target` |
| DOL matching | `dol_hub.py` | `outreach.dol` |
| People pipeline | `ceo_email_pipeline.py` | `outreach.people` |
| BIT calculation | BIT engine | `outreach.bit_scores` |
| Campaign execution | `outreach_hub.py` | `outreach.campaigns` |

### CLI Entry Points

| Command | Script | Tables Affected |
|---------|--------|-----------------|
| `python ceo_email_pipeline.py <csv>` | ceo_email_pipeline.py | `outreach.people`, `people.company_slot` |
| `python company_pipeline.py` | company_pipeline.py | `outreach.company_target` |

---

## Error Table Writers

| Error Table | Written By |
|-------------|------------|
| `outreach.company_target_errors` | neon_writer.py, company_hub.py |
| `outreach.dol_errors` | dol_hub.py, processors/*.py |
| `outreach.people_errors` | people_hub.py, ceo_email_pipeline.py |
| `outreach.blog_errors` | blog_hub.py |
| `outreach.bit_errors` | BIT engine |
| `outreach.outreach_errors` | Various (general errors) |

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-28 |
| Version | 1.0.0 |
| Author | Claude Code (AI Employee) |
