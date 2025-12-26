# Hub & Spoke Architecture Enforcement

This document describes the automated enforcement mechanisms that protect the Hub & Spoke architecture.

---

## Overview

The repository uses three layers of enforcement to prevent architectural drift:

| Layer | Tool | When | Blocks |
|-------|------|------|--------|
| **Local** | Pre-commit hook | Before every commit | Yes |
| **CI** | GitHub Actions | On every PR | Yes (merge blocked) |
| **Lint** | Spoke Purity Linter | CI + manual | Yes |

---

## 1. Pre-Commit Hook (Repo Shape Guard)

**Location**: `tooling/git-hooks/pre-commit`

### Installation

```bash
# One-time setup
./tooling/git-hooks/install.sh

# Or manually
cp tooling/git-hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### What It Checks

| Check | Rule | Rationale |
|-------|------|-----------|
| **Root Python Files** | No `*.py` at repo root | All Python must be in hubs/, spokes/, or tooling/ |
| **Directory Allowlist** | Only approved top-level dirs | Prevents architectural sprawl |
| **Large Files** | Max 5MB outside data/ | Keeps repo lean |

### Allowed Top-Level Directories

```
.github/        hubs/           shared/
.vscode/        infra/          spokes/
contracts/      integrations/   templates/
docs/           neon/           tests/
doctrine/       ops/            tooling/
global-config/
```

### Bypassing (Emergency Only)

```bash
# Skip hook for a single commit (requires approval)
git commit --no-verify -m "EMERGENCY: <reason>"
```

**WARNING**: All `--no-verify` commits are flagged in CI and require justification.

---

## 2. GitHub Actions CI (hub-spoke-guard.yml)

**Location**: `.github/workflows/hub-spoke-guard.yml`

### Triggers

- All pull requests to `main`
- All pushes to `main`

### Checks Performed

| Check | Description | Exit on Failure |
|-------|-------------|-----------------|
| **Repo Shape Guard** | Same as pre-commit hook | Yes |
| **Hub Manifest Validation** | All hubs have valid YAML manifests | Yes |
| **Spoke Contract Validation** | All contracts have required fields | Yes |
| **Spoke Purity Linter** | No forbidden imports/patterns | Yes |
| **Hub IMO Structure** | All hubs have input/middle/output | Yes |
| **Hub Isolation** | No sideways hub-to-hub imports | Yes |

### Required Hub Manifests

Each hub must have `hub.manifest.yaml` with:

```yaml
hub_id: HUB-COMPANY-TARGET
doctrine_id: "04.04.01"
type: sub-hub
parent:
  hub_id: HUB-COMPANY-LIFECYCLE
  relationship: child
core_metric: BIT_SCORE
entities_owned:
  - outreach.company_target
imo_structure:
  input: receivers/
  middle: processors/
  output: emitters/
```

### Required Contract Fields

Each spoke contract must have:

```yaml
contract_id: CONTRACT-CO-PEOPLE
source_hub: company-target
target_hub: people-intelligence
direction: bidirectional  # or ingress, egress
```

---

## 3. Spoke Purity Linter

**Location**: `tooling/spoke_linter.py`

### Running Manually

```bash
python tooling/spoke_linter.py
```

### Rules

#### Forbidden Imports (BLOCKS)

These imports are NEVER allowed in spokes:

```python
# Data Processing
pandas, numpy, scipy, sklearn

# Database
sqlalchemy, psycopg2, psycopg, asyncpg, redis, pymongo

# HTTP/Network
requests, httpx, aiohttp, urllib3, boto3

# Other
firebase_admin, neon
```

#### Forbidden Patterns (BLOCKS)

These patterns indicate spoke impurity:

```python
sqlite3
psycopg2.connect
create_engine
Session(
redis.Redis
MongoClient
requests.get/post/put/delete
httpx.get/post
aiohttp.ClientSession
boto3.client
firebase.initialize
```

#### Business Logic (BLOCKS)

- If/else chains with more than 3 branches
- Nested loops (data processing)

#### LOC Warning (WARNS)

Files with more than 50 lines of code get a warning.

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All checks passed |
| 1 | Violations found (blocks PR) |

---

## Architecture Rules Summary

### The Golden Rule

```
IF company_id IS NULL OR domain IS NULL OR email_pattern IS NULL:
    STOP. DO NOT PROCEED.
    → Route to Company Identity Pipeline first.
```

### Hub Rules

1. **Hubs own entities** - All business logic lives in hub middle layers
2. **Hubs have IMO structure** - input/, middle/, output/ subdirectories
3. **No sideways imports** - Hubs communicate through spokes only
4. **Company Target is internal anchor** - Receives identity from CL parent hub

### Spoke Rules

1. **I/O only** - No business logic, no state, no transformation
2. **Pass-through** - Receive payload, route to target, done
3. **Contracts define interface** - All spokes have YAML contracts
4. **Minimal code** - Should be under 50 LOC

### What Goes Where

| Code Type | Location |
|-----------|----------|
| Business logic | `hubs/<name>/imo/middle/` |
| Data transformation | `hubs/<name>/imo/middle/` |
| API receivers | `hubs/<name>/imo/input/` |
| Event emitters | `hubs/<name>/imo/output/` |
| Hub-to-hub routing | `spokes/<name>/` |
| Contracts | `contracts/*.contract.yaml` |
| Shared utilities | `shared/` |
| Tests | `tests/` |

---

## Troubleshooting

### "Forbidden import" error

**Problem**: You imported pandas/numpy/etc in a spoke.

**Solution**: Move the code to a hub middle layer. Spokes only route data.

```python
# BAD - in spokes/
import pandas as pd
df = pd.DataFrame(data)

# GOOD - move to hubs/<name>/imo/middle/
# Spokes just pass the payload through
```

### "Complex conditional" error

**Problem**: Your spoke has too much if/else logic.

**Solution**: Decision logic belongs in hubs. Spokes should have at most:

```python
# Acceptable in spoke
def route(self, payload):
    if payload.is_priority:
        self._urgent_handler(payload)
    else:
        self._normal_handler(payload)
```

### "Unauthorized directory" error

**Problem**: You created a new top-level directory.

**Solution**: Either:
1. Put your code in an existing approved directory
2. Add your directory to the allowlist in `tooling/git-hooks/pre-commit`

---

## Adding New Enforcement Rules

1. Update `tooling/git-hooks/pre-commit` for local checks
2. Update `.github/workflows/hub-spoke-guard.yml` for CI checks
3. Update `tooling/spoke_linter.py` for spoke-specific rules
4. Document the new rule in this file

---

## Related Documentation

- [Hub & Spoke Architecture](./HUB_AND_SPOKE_ARCHITECTURE_AUDIT.md)
- [ADR-001: Hub Spoke Architecture](./adr/ADR-001_Hub_Spoke_Architecture.md)
- [Complete System ERD](./COMPLETE_SYSTEM_ERD.md)
- [Migration Complete](../MIGRATION_COMPLETE.md)

---

*Last updated: 2025-12-23*
