# ADR-012: Company Target Utils Folder Refactor

## Status
**ACCEPTED**

## Date
2026-01-25

## Context

The audit identified a **CRITICAL CTB VIOLATION**: a `utils/` folder exists at `hubs/company-target/imo/middle/utils/`.

Per CANONICAL_ARCHITECTURE_DOCTRINE.md §1.3 and the Global Invariants section:
> Forbidden folders (utils, helpers, common, shared, lib, misc) — This doctrine

The `utils/` folder contains 11 files:
- `__init__.py`
- `cl_gate.py` — CL identity gate enforcement
- `config.py` — Configuration management
- `context_manager.py` — Context/session management
- `fuzzy.py` — Fuzzy matching algorithms
- `fuzzy_arbitration.py` — Match arbitration logic
- `logging.py` — Logging utilities
- `normalization.py` — Data normalization
- `patterns.py` — Email pattern utilities
- `providers.py` — External provider integrations
- `verification.py` — Verification utilities

## Decision

Refactor the forbidden `utils/` folder into **domain-specific folders** under `middle/`.

### Option A: Rename to `support/` — REJECTED
- Still generic naming
- Does not address the root issue of unclear ownership

### Option B: Flatten into `middle/` — REJECTED
- Would clutter the middle/ directory
- Loses logical grouping

### Option C: Domain-specific folders — ACCEPTED
- Clear ownership per domain
- Maintains logical grouping
- Doctrine-compliant naming

## New Structure

```
hubs/company-target/imo/middle/
├── gates/
│   └── cl_gate.py              # CL identity enforcement
├── matching/
│   ├── fuzzy.py                # Fuzzy matching
│   ├── fuzzy_arbitration.py    # Match arbitration
│   └── normalization.py        # Data normalization
├── verification/
│   ├── patterns.py             # Email patterns
│   └── verification.py         # Verification logic
├── config.py                   # Configuration (root level)
├── context_manager.py          # Context management (root level)
├── logging_config.py           # Logging (renamed to avoid stdlib conflict)
└── providers.py                # External providers (root level)
```

## Consequences

### Positive
- Removes CTB violation
- Improves code discoverability
- Enforces domain boundaries
- Passes doctrine audit

### Negative
- Requires import path updates across codebase
- One-time migration effort

### Neutral
- No functional changes to code logic

## Implementation

1. Create new folder structure
2. Move files to appropriate locations
3. Update all import statements
4. Run tests to verify
5. Delete empty `utils/` folder
6. Commit with doctrine compliance reference

## References

- CANONICAL_ARCHITECTURE_DOCTRINE.md §1.3 (Forbidden folders)
- Audit Report 2026-01-25 (Phase 2.4 Forbidden Patterns)

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-25 |
| Author | Claude Code |
| Status | ACCEPTED |
| CC Layer | CC-03 |
