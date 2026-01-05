# CC Purification Report

**Date**: 2026-01-05
**Doctrine Version**: v1.1.0
**Status**: COMPLETE

---

## Executive Summary

The `barton-outreach-core` repository has been purified to enforce **Canonical Chain (CC) exclusivity**. Every file and directory now maps cleanly to a single CC layer.

---

## Root Directory Structure (AFTER)

```
barton-outreach-core/
├── .github/          # CI/visibility (allowed)
├── contexts/         # CC-03 Context
├── contracts/        # CC-03 Context
├── docs/             # Visibility only
├── hubs/             # CC-02 Hub
├── meta/             # Quarantine/dev tooling
├── ops/              # CC-04 Process
├── spokes/           # Interface (no CC layer)
├── doppler.yaml      # ALLOWED (Doppler exception)
├── .env.example      # ALLOWED
└── [config files]    # package.json, requirements.txt, etc.
```

---

## Directories Moved to `meta/legacy_quarantine/`

| Original Location | Reason | Action |
|-------------------|--------|--------|
| `.archive/` | Legacy archive | Quarantined |
| `api/` | Unclassified executable | Quarantined |
| `barton-outreach-core/` | Nested repo | Quarantined |
| `ctb/` | Legacy CTB structure | Quarantined |
| `data/` | Runtime data, not CC | Quarantined |
| `delegations/` | Empty, deprecated | Deleted |
| `enrichment-hub/` | Legacy hub structure | Quarantined |
| `HEIR-AGENT-SYSTEM/` | Legacy system | Quarantined |
| `integrations/` | Unclassified | Quarantined |
| `nodes/` | Unclassified | Quarantined |
| `orbt/` | Legacy ORBT | Quarantined |
| `output/` | Runtime output | Quarantined |
| `outreach_core/` | Legacy core | Quarantined |
| `public/` | Unclassified | Quarantined |
| `services/` | Unclassified | Quarantined |
| `shared/` | Unclassified | Quarantined |
| `src/` | Unclassified | Quarantined |
| `sync/` | Unclassified | Quarantined |

---

## Directories Moved to `meta/dev_tooling/`

| Original Location | Reason |
|-------------------|--------|
| `.devcontainer/` | VS Code dev container |
| `.vscode/` | VS Code settings |

---

## Directories Moved to `ops/` (CC-04)

| Original Location | New Location | Reason |
|-------------------|--------------|--------|
| `diagnostics/` | `ops/diagnostics/` | Runtime diagnostics |
| `grafana/` | `ops/monitoring/grafana/` | Monitoring config |
| `infra/` | `ops/infra/` | Infrastructure |
| `migrations/` | `ops/migrations/` | DB migrations |
| `neon/` | `ops/neon/` | Neon operations |
| `scripts/` | `ops/scripts/` | Operational scripts |
| `tests/` | `ops/tests/` | Test execution |
| `tooling/` | `ops/tooling/` | Operational tooling |
| `tools/` | `ops/tools/` | CLI tools |
| `setup_*.py` | `ops/scripts/` | Setup scripts |

---

## Directories Moved to `contexts/` (CC-03)

| Original Location | New Location | Reason |
|-------------------|--------------|--------|
| `config/` | `contexts/config/` | Configuration |
| `global-config/` | `contexts/global-config/` | Global config |

---

## Directories Moved to `contracts/` (CC-03)

| Original Location | New Location | Reason |
|-------------------|--------------|--------|
| `schemas/` | `contracts/schemas/` | Schema definitions |

---

## Directories Moved to `docs/`

| Original Location | New Location | Reason |
|-------------------|--------------|--------|
| `doctrine/` | `docs/doctrine_ref/` | Doctrine reference |
| `repo-data-diagrams/` | `docs/repo-data-diagrams/` | Diagrams |
| `templates/` | `docs/templates/` | Document templates |

---

## External Repositories Removed

| Repository | Reason |
|------------|--------|
| `company-lifecycle-cl/` | External CC-01 sovereign - should be separate repo |
| `site-scout-pro/` | External project - should be separate repo |

---

## CC.md Files Created/Updated

| File | CC Layer |
|------|----------|
| `meta/CC.md` | N/A (Visibility) |
| `meta/legacy_quarantine/CC.md` | QUARANTINE |
| `meta/dev_tooling/CC.md` | N/A (Local) |
| `docs/CC.md` | N/A (Visibility) |
| `ops/CC.md` | CC-04 (updated) |

---

## CI Guardrails Added

| Job | Purpose | Fail Condition |
|-----|---------|----------------|
| `cc-root-lockdown` | Enforce allowed directories | New unauthorized directory |
| `cc-executable-check` | Executables in ops/ only | Shell scripts outside ops/ |

---

## Doppler Exception

The following files are explicitly allowed per the Doppler exception:
- `.doppler/` (if exists)
- `.doppler.yaml` (if exists)
- `doppler.yaml`
- `.env.example`

These are for **local developer runtime access only** and are never promoted into CC logic.

---

## Quarantine Protocol

Items in `meta/legacy_quarantine/` have **90 days** to be:
1. Migrated to proper CC location
2. Deleted permanently

After 90 days (2026-04-05), remaining items should be deleted.

---

## Verification Checklist

- [x] Root directory contains only allowed directories
- [x] All directories have CC.md annotations
- [x] No executable code outside ops/
- [x] Contexts and contracts properly separated
- [x] CI guardrails updated for root lockdown
- [x] Doppler files explicitly allowed

---

## Post-Purification Structure

```
CC-01 SOVEREIGN (External)
└── company-lifecycle-cl (REMOVED - separate repo)

CC-02 HUB
└── hubs/
    ├── company-target/
    ├── dol-filings/
    ├── people-intelligence/
    ├── blog-content/
    └── outreach-execution/

CC-03 CONTEXT
├── contexts/
│   ├── config/
│   └── global-config/
└── contracts/
    └── schemas/

CC-04 PROCESS
└── ops/
    ├── cc_enforcement/
    ├── diagnostics/
    ├── infra/
    ├── migrations/
    ├── monitoring/
    ├── neon/
    ├── scripts/
    ├── tests/
    ├── tooling/
    └── tools/

INTERFACE (No CC Layer)
└── spokes/

VISIBILITY ONLY
├── .github/
├── docs/
└── meta/
```

---

**Signed**: Claude Code
**Date**: 2026-01-05
**Doctrine Version**: v1.1.0
