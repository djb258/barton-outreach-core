---
name: barton-neon
description: >
  Neon Serverless PostgreSQL configuration, schemas, and operational patterns for
  barton-outreach-core — endpoint ep-ancient-waterfall-a42vy0du on us-east-1, database
  "Marketing DB", six production schemas (outreach, people, dol, company, cl, bit) plus
  vendor layer. Use this skill whenever querying, migrating, debugging, or making data
  architecture decisions in this repo. Trigger on: Neon, PostgreSQL, Postgres, database,
  schema, table, migration, connection string, pooler, outreach schema, people schema,
  dol schema, company schema, cl schema, bit schema, vendor_claude, enrichment pipeline,
  company-target hub, people-intelligence hub, dol-filings hub, blog-content hub,
  outreach-execution hub, coverage hub, talent-flow hub, or any reference to the
  relational data layer in barton-outreach-core. Also trigger on: column_registry,
  pipeline_errors, hub_registry, batch, or sub-hub architecture questions.
---

# barton-neon -- Car-Level Neon Skill

This skill contains the repo-specific Neon configuration, schema inventory, and
operational patterns for barton-outreach-core. For platform-level Neon capabilities,
connection pooling rules, branching, pricing, and driver selection, see the master skill.

**Master skill reference:** `IMO-Creator/skills/neon/SKILL.md`

## What This Repo Uses

| Component | Value |
|-----------|-------|
| Neon Endpoint | `ep-ancient-waterfall-a42vy0du` |
| Region | `us-east-1` (AWS) |
| Database Name | `Marketing DB` (URL-encoded: `Marketing%20DB`) |
| Pooler Host | `ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech` |
| SSL | Required (`sslmode=require`) |
| RLS | Enabled (`RLS_ENABLED=true`) |
| DB Client | `pg` (node-postgres) v8.17.2 |
| Neon Serverless Driver | Not used (no `@neondatabase/serverless` in package.json) |

## Connection Configuration

All connection details are sourced from environment variables. See `.env.example` for
the canonical list.

| Env Var | Purpose |
|---------|---------|
| `NEON_HOST` | Pooler hostname |
| `NEON_DATABASE` | Database name (contains space -- must URL-encode in connection strings) |
| `NEON_USER` | Database user |
| `NEON_PASSWORD` | Database password |
| `NEON_ENDPOINT_ID` | Neon endpoint identifier |
| `NEON_DATABASE_URL` | Full pooled connection string (application traffic) |
| `DATABASE_URL` | Alias for `NEON_DATABASE_URL` (used by ORMs and migration tools) |

**Important:** The database name `Marketing DB` contains a space. Any programmatic
connection string construction must URL-encode it as `Marketing%20DB`. The `.env.example`
already shows this correctly.

**Connection pattern:** This repo uses the `pg` (node-postgres) driver over the pooled
endpoint. It does NOT use the Neon serverless driver (`@neondatabase/serverless`). There
is no Cloudflare Hyperdrive in this stack.

## Schema / Data Model

Six production schemas plus a company-lifecycle (`cl`) schema:

| Schema | Tables | Primary Purpose | Hub |
|--------|--------|-----------------|-----|
| `outreach` | 39 | Campaign execution, sequences, send log, company targets, blog, DOL summaries, BIT scores, hub/column registry | outreach-execution |
| `people` | 22 | People master, candidate staging, enrichment queues, slot assignment, title mapping, movement history | people-intelligence |
| `company` | 12 | Company master, sidecar, slots, contact enrichment, email verification, pipeline events | company-target |
| `dol` | 8 | DOL Form 5500 filings, Schedule A, EIN URLs, renewal calendar, pressure signals | dol-filings |
| `cl` | 18 | Company-lifecycle identity resolution -- candidates, domains, hierarchy, confidence scoring | (cross-hub) |
| `bit` | 6 | Authorization log, movement events, phase state, proof lines | (governance) |

The `outreach` schema is the largest (39 tables) and serves as the canonical egress
layer with archive tables, error tables, and audit logs for each data domain.

For detailed table listings per schema, see `references/schema.md`.

## Operational Patterns

### Sub-Hub Architecture

barton-outreach-core uses a hub-of-hubs (sub-hub) pattern. Each sub-hub owns a slice
of the data pipeline:

| Sub-Hub | Directory | Data Flow |
|---------|-----------|-----------|
| company-target | `hubs/company-target/` | Company discovery and enrichment -> `company.*` tables |
| people-intelligence | `hubs/people-intelligence/` | People enrichment and slot assignment -> `people.*` tables |
| dol-filings | `hubs/dol-filings/` | DOL Form 5500 ingestion -> `dol.*` tables |
| blog-content | `hubs/blog-content/` | Blog content pipeline -> `outreach.blog*` tables |
| outreach-execution | `hubs/outreach-execution/` | Campaign execution and send log -> `outreach.*` tables |
| coverage | `hubs/coverage/` | Coverage analysis |
| talent-flow | `hubs/talent-flow/` | Talent movement tracking |

Each sub-hub has its own `imo/output/neon_writer.py` for writing to the database.

### Enrichment Pipelines

Data flows through a staged pipeline:
1. **Ingress** -- raw data lands in `*_staging` or `*_candidate` tables with schema validation only
2. **Middle** -- enrichment agents (Apify, Firecrawl, Abacus) process and resolve entities
3. **Egress** -- promoted records land in `*_master` tables; rejected records go to `*_excluded` or `*_errors`

Archive tables (`*_archive`) preserve previous states. Error tables (`*_errors`) capture
pipeline failures with fault codes. Audit log tables (`*_audit_log`) track all mutations.

### Doctrine Integration

| Component | Table/Column |
|-----------|-------------|
| Hub Registry | `outreach.hub_registry` |
| Column Registry | `outreach.column_registry` |
| Pipeline Audit | `outreach.pipeline_audit_log` |
| Override Tracking | `outreach.manual_overrides` + `outreach.override_audit_log` |

## Known Issues

- **Database name contains a space.** The name `Marketing DB` requires URL-encoding
  (`Marketing%20DB`) in all connection strings. Forgetting this causes silent connection
  failures
- **No Neon serverless driver.** The repo uses `pg` directly. If migrating to edge
  functions, the serverless driver would need to be added
- **Large outreach schema.** 39 tables in `outreach` -- some are canonical egress views
  of data owned by other schemas (e.g., `outreach.dol` mirrors `dol.*` tables)

## Cost Profile

| Metric | Estimate |
|--------|----------|
| Plan | Launch (based on data volume and schema count) |
| Schemas | 6 production schemas |
| Total Tables | ~105 tables |
| Compute | Pooled endpoint, scale-to-zero enabled |
| Storage Driver | Space-named DB requires careful connection string handling |
| Primary Cost Factor | Compute CU-hours during enrichment pipeline runs |
