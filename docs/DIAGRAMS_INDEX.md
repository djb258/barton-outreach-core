# Diagrams Index

**Repository**: barton-outreach-core
**Generated**: 2026-02-02
**Source of Truth**: Neon PostgreSQL (live database queries)
**Doctrine**: DOCUMENTATION_ERD_DOCTRINE.md v1.0.0

---

## ⚠️ CRITICAL: Authoritative Table Reference

> **ALL work MUST use `outreach.company_target` as the company source (95,837 companies).**
> **See [AUTHORITATIVE_TABLE_REFERENCE.md](AUTHORITATIVE_TABLE_REFERENCE.md) for complete details.**

---

## Quick Reference

| Category | Diagram | Description |
|----------|---------|-------------|
| **ERD** | [PEOPLE_DATA_FLOW_ERD.md](diagrams/PEOPLE_DATA_FLOW_ERD.md) | ⭐ **START HERE** - People slot/enrichment flow |
| **ERD** | [CORE_SCHEMA.mmd](diagrams/erd/CORE_SCHEMA.mmd) | Complete system entity relationships |
| **ERD** | [CL_AUTHORITY_REGISTRY.mmd](diagrams/erd/CL_AUTHORITY_REGISTRY.mmd) | CL parent hub schema |
| **ERD** | [OUTREACH_SPINE.mmd](diagrams/erd/OUTREACH_SPINE.mmd) | Outreach operational spine |
| **ERD** | [COMPANY_TARGET_SUBHUB.mmd](diagrams/erd/COMPANY_TARGET_SUBHUB.mmd) | Company Target (04.04.01) |
| **ERD** | [DOL_SUBHUB.mmd](diagrams/erd/DOL_SUBHUB.mmd) | DOL Filings (04.04.03) |
| **ERD** | [PEOPLE_INTELLIGENCE_SUBHUB.mmd](diagrams/erd/PEOPLE_INTELLIGENCE_SUBHUB.mmd) | People Intelligence (04.04.02) |
| **ERD** | [BLOG_SUBHUB.mmd](diagrams/erd/BLOG_SUBHUB.mmd) | Blog Content (04.04.05) |
| **ERD** | [BIT_ENGINE.mmd](diagrams/erd/BIT_ENGINE.mmd) | BIT scoring engine |
| **Architecture** | [CTB_TREE.mmd](diagrams/architecture/CTB_TREE.mmd) | Repository structure map |
| **Architecture** | [HUB_SPOKE.mmd](diagrams/architecture/HUB_SPOKE.mmd) | Hub and spoke relationships |
| **Architecture** | [IMO_FLOW.mmd](diagrams/architecture/IMO_FLOW.mmd) | Ingress/Middle/Egress flow |
| **Architecture** | [WATERFALL.mmd](diagrams/architecture/WATERFALL.mmd) | Sub-hub execution order |
| **Architecture** | [DATA_FLOW.mmd](diagrams/architecture/DATA_FLOW.mmd) | Data flow sequence |
| **ERD** | [COMPLETENESS_SYSTEM.mmd](diagrams/erd/COMPLETENESS_SYSTEM.mmd) | Completeness contract schema |
| **Architecture** | [COMPLETENESS_FLOW.mmd](diagrams/architecture/COMPLETENESS_FLOW.mmd) | Completeness evaluation flow |
| **Operations** | [COMPLETENESS_CHECK.md](COMPLETENESS_CHECK.md) | Per-company completeness lookup |
| **Operations** | [SUBHUB_COMPLETENESS_MATRIX.md](SUBHUB_COMPLETENESS_MATRIX.md) | Enrichment progress tracking |

---

## ERD Diagrams

### ⭐ People Data Flow (START HERE)

#### PEOPLE_DATA_FLOW_ERD.md
**Location**: `docs/diagrams/PEOPLE_DATA_FLOW_ERD.md`
**Purpose**: Complete people data flow from company_target through slots to outreach
**Key Tables**:
- `outreach.company_target` → AUTHORITATIVE (95,837)
- `people.company_slot` → Slot assignments (CEO, CFO, HR)
- `people.people_master` → People data
- `outreach.people` → Promoted for outreach

### Overall System

#### CORE_SCHEMA.mmd
**Location**: `docs/diagrams/erd/CORE_SCHEMA.mmd`
**Purpose**: Complete entity relationship diagram showing all major schemas and their relationships
**Scope**: cl, outreach, people, dol, marketing schemas
**Key Relationships**:
- CL → Outreach (WRITE-ONCE registration)
- Outreach spine → All sub-hubs (FK)
- DOL Form 5500 → Schedule A (filing relationship)
- People Master → Company Slot (slot assignment)

### Parent Hub

#### CL_AUTHORITY_REGISTRY.mmd
**Location**: `docs/diagrams/erd/CL_AUTHORITY_REGISTRY.mmd`
**Purpose**: Company Lifecycle authority registry (parent hub)
**Schema**: `cl`
**Tables**: 13 tables
**Key Table**: `cl.company_identity` (52,675 rows)
**Key Concept**: WRITE-ONCE identity pointers (outreach_id, sales_process_id, client_id)

### Operational Spine

#### OUTREACH_SPINE.mmd
**Location**: `docs/diagrams/erd/OUTREACH_SPINE.mmd`
**Purpose**: Outreach operational spine and all sub-hub connections
**Schema**: `outreach`
**Tables**: 45+ tables
**Key Table**: `outreach.outreach` (49,737 rows)
**Key Concept**: All sub-hubs FK to outreach_id

### Sub-Hub ERDs

#### COMPANY_TARGET_SUBHUB.mmd
**Location**: `docs/diagrams/erd/COMPANY_TARGET_SUBHUB.mmd`
**Purpose**: Company Target sub-hub (04.04.01)
**Waterfall Position**: #1 (PASS REQUIRED)
**Key Table**: `outreach.company_target` (45,816 rows, 91.4% have email_method)
**Responsibilities**: Domain resolution, email pattern discovery

#### DOL_SUBHUB.mmd
**Location**: `docs/diagrams/erd/DOL_SUBHUB.mmd`
**Purpose**: DOL Filings sub-hub (04.04.03)
**Waterfall Position**: #2 (PASS REQUIRED)
**Key Tables**:
- `outreach.dol` (18,575 rows, 27% coverage)
- `dol.form_5500` (230,482 filings)
- `dol.schedule_a` (337,476 records)
**Responsibilities**: EIN resolution, Form 5500 + Schedule A matching

#### PEOPLE_INTELLIGENCE_SUBHUB.mmd
**Location**: `docs/diagrams/erd/PEOPLE_INTELLIGENCE_SUBHUB.mmd`
**Purpose**: People Intelligence sub-hub (04.04.02)
**Waterfall Position**: #3 (PASS REQUIRED, executes after DOL)
**Key Tables**:
- `outreach.people` (379 rows)
- `people.people_master` (71,237 rows)
- `people.company_slot` (149,172 slots)
**Responsibilities**: Slot assignment, email generation, movement detection

#### BLOG_SUBHUB.mmd
**Location**: `docs/diagrams/erd/BLOG_SUBHUB.mmd`
**Purpose**: Blog Content sub-hub (04.04.05)
**Waterfall Position**: #4 (PASS)
**Key Table**: `outreach.blog` (46,468 rows, 100% coverage)
**Responsibilities**: Content signals, news monitoring, pressure detection

#### BIT_ENGINE.mmd
**Location**: `docs/diagrams/erd/BIT_ENGINE.mmd`
**Purpose**: Buyer Intent Tracking scoring engine
**Waterfall Position**: After all sub-hubs
**Key Table**: `outreach.bit_scores` (15,032 rows)
**Responsibilities**: Signal aggregation, tier assignment, intent scoring

---

## Architecture Diagrams

#### CTB_TREE.mmd
**Location**: `docs/diagrams/architecture/CTB_TREE.mmd`
**Purpose**: Christmas Tree Backbone repository structure map
**Shows**: Directory structure, hub organization, IMO layers

#### HUB_SPOKE.mmd
**Location**: `docs/diagrams/architecture/HUB_SPOKE.mmd`
**Purpose**: Hub and spoke relationships
**Shows**: CL parent, Outreach child, sub-hubs, spoke contracts

#### IMO_FLOW.mmd
**Location**: `docs/diagrams/architecture/IMO_FLOW.mmd`
**Purpose**: Ingress/Middle/Egress data flow pattern
**Shows**: Data flow through I, M, O layers with rules

#### WATERFALL.mmd
**Location**: `docs/diagrams/architecture/WATERFALL.mmd`
**Purpose**: Sub-hub waterfall execution order
**Shows**: Gate validation, PASS requirements, failure handling

#### DATA_FLOW.mmd
**Location**: `docs/diagrams/architecture/DATA_FLOW.mmd`
**Purpose**: Complete data flow sequence diagram
**Shows**: Intake → CL → Outreach → Sub-hubs → Neon

---

## Rendering Instructions

### GitHub / GitLab
Mermaid diagrams render natively. Simply view the `.mmd` files in the browser.

### VS Code
Install the "Mermaid" extension:
1. Open Extensions (Ctrl+Shift+X)
2. Search "Mermaid"
3. Install "Markdown Preview Mermaid Support"

### Online
Use https://mermaid.live/ to paste diagram content and render.

### Export to PNG/SVG
1. Go to https://mermaid.live/
2. Paste diagram content
3. Use export options in the UI

---

## Database Statistics

| Schema | Tables | Key Table | Rows |
|--------|--------|-----------|------|
| cl | 13 | company_identity | 52,675 |
| outreach | 45+ | outreach | 49,737 |
| people | 20+ | people_master | 71,237 |
| dol | 8 | form_5500 | 230,482 |
| marketing | 12 | company_master | - |

**Total Tables**: 172
**Total Views**: 56
**Total Foreign Keys**: 62
**Total Indexes**: 677

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| [DATABASE_QUERY_RESULTS.md](DATABASE_QUERY_RESULTS.md) | Complete schema export with all tables/columns |
| [ERD_DIAGRAM.md](ERD_DIAGRAM.md) | Inline Mermaid diagrams (legacy) |
| [ERD_SUMMARY.md](ERD_SUMMARY.md) | Human-readable ERD summary |
| [database_erd_export.json](database_erd_export.json) | Full JSON schema export |

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-28 |
| Last Modified | 2026-01-28 |
| Author | Claude Code (AI Employee) |
| Source | Neon PostgreSQL (live queries) |
| Doctrine | DOCUMENTATION_ERD_DOCTRINE.md v1.0.0 |
