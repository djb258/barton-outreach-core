# ADR-CT-IMO-001: Company Target as Single-Pass IMO Gate

**Status:** ACCEPTED
**Date:** 2026-01-07
**Deciders:** Architecture Team
**Technical Story:** Company Target Spine-First Refactor

## Context and Problem Statement

Company Target was originally designed as a "Company Hub" that performed:
- Company matching (fuzzy logic)
- Identity minting
- Hold queue management
- Retry/rescue logic

This violated the architectural principle that **identity is owned by Company Lifecycle (CL)**, not by downstream systems. The result was:
- Duplicate matching logic across systems
- Unclear ownership of company identity
- Retry loops that masked data quality issues
- Direct CL table access from Outreach

## Decision Drivers

1. **Identity/Execution Separation**: CL owns identity; Outreach owns execution
2. **Cost Control**: Tier-2 tools are expensive; single-pass prevents cost explosion
3. **Auditability**: Terminal failures create clear audit trail
4. **Simplicity**: One path, no rescue loops, no retry queues

## Considered Options

1. **Keep Company Target as-is** (matching + execution)
2. **Split into two services** (matcher + executor)
3. **Refactor to IMO gate** (execution-only, single-pass)

## Decision Outcome

**Chosen option:** "Refactor to IMO gate"

Company Target is now a **single-pass Input-Middle-Output (IMO) gate** that:
- Accepts `outreach_id` from Outreach Spine
- Derives email methodology (pattern discovery)
- Routes to PASS or terminal FAIL

### Positive Consequences

- Clear ownership: CL = identity, CT = execution prep
- Predictable costs: one Tier-2 call max per record
- Debuggable: failures are permanent work items, not transient states
- CI-enforceable: drift guards prevent resurrection of legacy logic

### Negative Consequences

- Legacy code must be deleted (phase1, phase1b, fuzzy.py)
- Existing pipelines must migrate to new entrypoint
- No automatic retry for transient failures (by design)

## Explicit Rejections

The following concepts are **permanently rejected** for Company Target:

| Concept | Reason |
|---------|--------|
| Phase 1 (Company Matching) | Moved to CL |
| Phase 1b (Unmatched Hold) | Moved to CL |
| Fuzzy matching | CL's responsibility |
| Fuzzy arbitration | CL's responsibility |
| Retry/backoff logic | FAIL is terminal |
| `sovereign_id` access | Hidden by spine |
| CL table reads | Spine provides `outreach_id` only |
| ID minting | Spine mints `outreach_id` |

## Technical Details

### Entrypoint

```python
from hubs.company_target import run_company_target_imo

run_company_target_imo(outreach_id)  # Single-pass execution
```

### IMO Stages

| Stage | Responsibility |
|-------|----------------|
| **I — Input** | Load from spine, validate `outreach_id` + domain |
| **M — Middle** | MX gate, pattern generation, SMTP validation |
| **O — Output** | Write to `outreach.company_target` or `outreach.company_target_errors` |

### Tool Registry (SNAP_ON_TOOLBOX.yaml)

| Tool | Tier | Stage |
|------|------|-------|
| MXLookup (TOOL-004) | 0 (FREE) | M1 |
| SMTPCheck (TOOL-005) | 0 (FREE) | M3 |
| EmailVerifier (TOOL-019) | 2 (GATED) | M5 (optional) |

### Write Targets

- **PASS**: `outreach.company_target` (execution_status = 'ready')
- **FAIL**: `outreach.company_target_errors` (terminal, no retry)

## Links

- **PRD**: `docs/prd/PRD_COMPANY_HUB.md` (v3.0)
- **Code**: `hubs/company-target/imo/middle/company_target_imo.py`
- **CI Guard**: `.github/workflows/company_target_imo_guard.yml`
- **Tool Registry**: `ops/tooling/SNAP_ON_TOOLBOX.yaml`

## Supersedes

This ADR supersedes any previous documentation describing Company Target as:
- "Central Core"
- "Identity Authority"
- "Matching Hub"
- "Company Hub (AXLE)"

The IMO model is the **only valid architecture** as of v3.0.
