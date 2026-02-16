# Barton Outreach Core

Marketing intelligence and executive enrichment platform built on hub-and-spoke architecture with Neon PostgreSQL.

## What This Is

Barton Outreach Core is a data pipeline system that manages company targeting, executive slot filling, DOL filing analysis, and outreach execution for B2B marketing. It processes ~95,000 companies through a waterfall of enrichment sub-hubs, each building on the previous one's output.

## Architecture

**Hub-and-Spoke** with strict doctrine enforcement inherited from [IMO-Creator](https://github.com/djb258/imo-creator).

- **CL (Company Lifecycle)** — Authority registry. Mints `sovereign_company_id`, stores identity pointers only.
- **Outreach Spine** (`outreach.outreach`) — Operational backbone. All sub-hubs FK via `outreach_id`.
- **Sub-Hubs** execute in waterfall order: Company Target → DOL Filings → People Intelligence → Blog Content.
- **Spokes** are I/O connectors only — no logic, no state.

### Sub-Hubs

| Order | Hub | Doctrine ID | Purpose |
|-------|-----|-------------|---------|
| 1 | Company Target | 04.04.01 | Domain resolution, email pattern discovery |
| 2 | DOL Filings | 04.04.03 | EIN resolution, Form 5500 + Schedule A |
| 3 | People Intelligence | 04.04.02 | Slot assignment, email generation |
| 4 | Blog Content | 04.04.05 | URL discovery, content signals |
| 5 | Coverage | 04.04.06 | Market coverage analysis + gap routing |
| 6 | Outreach Execution | 04.04.04 | Campaign execution, sequences |
| 7 | Talent Flow | — | Executive movement detection |

## Tech Stack

- **Database**: Neon PostgreSQL (serverless), 18 schemas, 249 registered tables
- **Backend**: Python 3.11+ (hub logic, pipelines, scripts)
- **Secrets**: Doppler (`doppler run -- python ...`)
- **HTTP**: httpx (async) — `requests` is banned per Snap-on Toolbox
- **Templates**: Inherited from IMO-Creator parent repo

## Repository Structure

```
barton-outreach-core/
├── hubs/                    # Hub business logic (IMO pattern)
│   ├── company-target/      # Internal anchor (04.04.01)
│   ├── dol-filings/         # DOL filing analysis (04.04.03)
│   ├── people-intelligence/ # Slot assignment + enrichment (04.04.02)
│   ├── blog-content/        # URL discovery (04.04.05)
│   ├── coverage/            # Market coverage (04.04.06)
│   ├── outreach-execution/  # Campaign execution (04.04.04)
│   └── talent-flow/         # Executive movement detection
├── spokes/                  # I/O connectors (no logic)
├── contracts/               # Spoke interface contracts (YAML)
├── ops/                     # Enforcement, validation, scheduling
├── src/                     # Source code (HEIR identity, codegen)
├── scripts/                 # Operational scripts (hooks, codegen, staleness)
├── migrations/              # Database migrations (SQL)
├── docs/                    # OSAM, ADRs, PRDs, ERDs, schema
├── doctrine/                # Governance doctrine files
├── templates/               # IMO-Creator inherited templates
├── tests/                   # Hub, spoke, and ops tests
└── archive/                 # Archived reports, one-off scripts
```

## Quick Start

```bash
# Prerequisites: Python 3.11+, Doppler CLI, Neon database access

# Install hooks
bash scripts/install-hooks.sh

# Run coverage for a market
doppler run -- python hubs/coverage/imo/middle/run_coverage.py \
    --anchor-zip 26739 --radius-miles 100

# Fill executive slots from Hunter CSV
doppler run -- python hubs/people-intelligence/imo/middle/phases/fill_slots_from_hunter.py data.csv

# Discover blog/about URLs
doppler run -- python hubs/blog-content/imo/middle/discover_blog_urls.py --dry-run --limit 20
```

## Key Doctrine Rules

1. **Universal join key**: `outreach_id` — never use domain as FK
2. **CL is authority registry** — identity pointers only, never workflow state
3. **Write-once to CL** — each hub mints its ID and registers once
4. **Spokes are I/O only** — no logic, no state, no transformation
5. **No processing without valid `outreach_id`**

## Key Documentation

| Document | Purpose |
|----------|---------|
| `CLAUDE.md` | AI bootstrap guide (start here) |
| `docs/OSAM.md` | Query routing — which table for which question |
| `DOCTRINE.md` | Doctrine reference (v2.8.0) |
| `REGISTRY.yaml` | Hub identity declaration |
| `doctrine/DO_NOT_MODIFY_REGISTRY.md` | Frozen components list |

## Status

- **v1.0 Baseline**: Certified and frozen (2026-01-20)
- **Outreach Spine**: 95,837 companies
- **Slot Fill Rate**: 62.4% (177,757 / 285,012)
- **People Records**: 182,946
- **CTB Registry**: 249 tables, 9 frozen core, 9 leaf types

## License

See [LICENSE](LICENSE).
