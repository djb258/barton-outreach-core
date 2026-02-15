# Documentation Requirements

**Repository**: barton-outreach-core
**Status**: MANDATORY
**Version**: 1.0.0

---

## Purpose

This document defines **mandatory documentation updates** that MUST be performed whenever schema, data flow, or table changes are made. This ensures Claude Code and human operators always have accurate, unambiguous references.

---

## Mandatory Documentation Updates

### When Schema Changes Occur

Any change to database tables, columns, or relationships MUST trigger:

| Document | Action Required |
|----------|-----------------|
| `docs/TAS_DATA_OPERATIONS.md` | Update join paths, lookup guide, flow sequences |
| `docs/diagrams/erd/*.mmd` | Update affected ERD diagram(s) |
| `docs/DATABASE_QUERY_RESULTS.md` | Re-run schema export queries |
| `docs/database_erd_export.json` | Regenerate JSON export |

### When Data Flow Changes Occur

Any change to how data moves between tables or sub-hubs MUST trigger:

| Document | Action Required |
|----------|-----------------|
| `docs/TAS_DATA_OPERATIONS.md` | Update Data Flow Sequences section |
| `docs/diagrams/architecture/DATA_FLOW.mmd` | Update sequence diagram |
| `docs/diagrams/architecture/WATERFALL.mmd` | Update if sub-hub order changes |

### When New Tables Are Added

Adding a new table MUST trigger:

| Document | Action Required |
|----------|-----------------|
| `docs/TAS_DATA_OPERATIONS.md` | Add to Primary Key Reference, Join Path Reference, Lookup Guide |
| `docs/diagrams/erd/*.mmd` | Add to relevant ERD diagram |
| `docs/DIAGRAMS_INDEX.md` | Update if new diagram created |

### When Sub-Hub Changes Occur

Changes to sub-hub logic or ownership MUST trigger:

| Document | Action Required |
|----------|-----------------|
| `docs/TAS_DATA_OPERATIONS.md` | Update Sub-Hub Table Ownership section |
| `docs/diagrams/erd/*_SUBHUB.mmd` | Update sub-hub ERD |
| `docs/diagrams/architecture/HUB_SPOKE.mmd` | Update if spoke contracts change |

---

## Documentation Checklist

Before any PR that changes schema or data flow is merged:

- [ ] `docs/TAS_DATA_OPERATIONS.md` is updated
- [ ] Relevant ERD diagrams in `docs/diagrams/erd/` are updated
- [ ] Relevant architecture diagrams in `docs/diagrams/architecture/` are updated
- [ ] `docs/DIAGRAMS_INDEX.md` references any new diagrams
- [ ] Join paths are verified against live Neon database
- [ ] Use case query patterns are tested

---

## Core Documentation Files

### Operational Guide (MUST be kept current)

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `docs/TAS_DATA_OPERATIONS.md` | **PRIMARY** - Join paths, lookups, flows | Every schema/flow change |
| `docs/DIAGRAMS_INDEX.md` | Master index of all diagrams | When diagrams added/removed |
| `CLAUDE.md` | Bootstrap guide for Claude Code | Major architecture changes |

### ERD Diagrams (MUST reflect Neon)

| File | Scope |
|------|-------|
| `docs/diagrams/erd/CORE_SCHEMA.mmd` | Overall system |
| `docs/diagrams/erd/CL_AUTHORITY_REGISTRY.mmd` | CL parent hub |
| `docs/diagrams/erd/OUTREACH_SPINE.mmd` | Outreach operational spine |
| `docs/diagrams/erd/COMPANY_TARGET_SUBHUB.mmd` | Company Target (04.04.01) |
| `docs/diagrams/erd/DOL_SUBHUB.mmd` | DOL Filings (04.04.03) |
| `docs/diagrams/erd/PEOPLE_INTELLIGENCE_SUBHUB.mmd` | People Intelligence (04.04.02) |
| `docs/diagrams/erd/BLOG_SUBHUB.mmd` | Blog Content (04.04.05) |
| `docs/diagrams/erd/BIT_ENGINE.mmd` | BIT scoring engine |

### Architecture Diagrams

| File | Purpose |
|------|---------|
| `docs/diagrams/architecture/CTB_TREE.mmd` | Repository structure |
| `docs/diagrams/architecture/HUB_SPOKE.mmd` | Hub and spoke relationships |
| `docs/diagrams/architecture/IMO_FLOW.mmd` | Ingress/Middle/Egress flow |
| `docs/diagrams/architecture/WATERFALL.mmd` | Sub-hub execution order |
| `docs/diagrams/architecture/DATA_FLOW.mmd` | Data flow sequence |

### Database Exports

| File | Purpose |
|------|---------|
| `docs/database_erd_export.json` | Full JSON schema export |
| `docs/DATABASE_QUERY_RESULTS.md` | Tabular query results |
| `docs/ERD_SUMMARY.md` | Human-readable summary |

---

## TAS Document Structure

The `docs/TAS_DATA_OPERATIONS.md` MUST contain:

### 1. Primary Key Reference
- Every table with its PK column and type
- Notes on FK relationships

### 2. Join Path Reference
- SQL examples for every common join
- CL → Outreach path
- Outreach → Sub-hub paths
- Sub-hub → Source table paths
- Complete profile joins

### 3. Data Lookup Guide
- "I need to find X by Y" tables
- Company lookups
- Person lookups
- DOL lookups
- Status lookups

### 4. Data Flow Sequences
- Step-by-step flows with SQL
- Outreach init flow
- Each sub-hub flow
- BIT scoring flow

### 5. Use Case Query Patterns
- Common queries with full SQL
- Marketing eligibility
- Contact retrieval
- DOL renewal pipeline
- Slot coverage
- Full company profile

### 6. Sub-Hub Table Ownership
- Which sub-hub owns which tables
- Read vs write permissions
- Critical constraints

---

## Verification Process

### After Documentation Update

1. **Syntax Check**: Verify all Mermaid diagrams render
2. **Query Test**: Run sample queries from TAS against Neon
3. **Cross-Reference**: Ensure ERDs match TAS join paths
4. **Index Check**: Verify DIAGRAMS_INDEX.md is complete

### Quarterly Audit

Run `templates/claude/HYGIENE_AUDITOR.prompt.md` to verify:
- All tables in Neon are documented
- All FKs are in ERD diagrams
- All join paths are in TAS
- No stale documentation

---

## Non-Compliance

If documentation is not updated with schema changes:

| Violation | Action |
|-----------|--------|
| Missing TAS update | PR blocked |
| Missing ERD update | PR blocked |
| Stale documentation | Quarterly audit flags |
| Undocumented table | HALT condition |

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-28 |
| Version | 1.0.0 |
| Status | MANDATORY |
| Author | Claude Code (AI Employee) |
