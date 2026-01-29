# Process Declarations

**Status**: CONSTITUTIONAL
**Doctrine Version**: IMO-Creator v1.0
**Domain Spec Reference**: `doctrine/REPO_DOMAIN_SPEC.md`
**CC Layer**: CC-04 (Process)

---

## Purpose

This directory contains formal **PROCESS DECLARATIONS** per IMO-Creator Process Doctrine.

A process declaration is required when a hub executes logic that:
1. Consumes constants from outside the system
2. Produces variables that are consumed by other systems
3. Requires a trackable process_id for audit and correlation

---

## Process Declaration Structure

Each process declaration MUST contain:

| Section | Description |
|---------|-------------|
| **process_id** | UUID pattern for this process type |
| **constants_consumed** | Reference to PRD constants table |
| **variables_produced** | Reference to PRD variables table |
| **governing_prd** | PRD that defines this process |
| **governing_pass** | Which pass (CAPTURE/COMPUTE/GOVERN) owns this process |
| **imo_layer** | I (Ingress), M (Middle), or O (Egress) |

---

## Process Files

| File | Hub | Governing PRD |
|------|-----|---------------|
| `company-target-process.md` | Company Target (04.04.01) | PRD_COMPANY_HUB.md |
| `people-intelligence-process.md` | People Intelligence (04.04.02) | PRD_PEOPLE_SUBHUB.md |
| `dol-filings-process.md` | DOL Filings (04.04.03) | PRD_DOL_SUBHUB.md |
| `blog-content-process.md` | Blog Content (04.04.05) | PRD_BLOG_NEWS_SUBHUB.md |
| `talent-flow-process.md` | Talent Flow (04.04.06) | PRD_TALENT_FLOW_SPOKE.md |
| `outreach-execution-process.md` | Outreach Execution (04.04.04) | PRD_OUTREACH_SPOKE.md |
| `sovereign-completion-process.md` | Sovereign Completion | PRD_SOVEREIGN_COMPLETION.md |
| `kill-switch-process.md` | Kill Switch System | PRD_KILL_SWITCH_SYSTEM.md |

---

## Process ID Patterns

All process IDs follow the pattern:
```
{hub_id}-{process_type}-{timestamp}-{random_hex}
```

Example: `company-target-pattern-20260129-a1b2c3d4`

---

## Correlation ID Doctrine

Every process execution MUST:
1. Generate or receive a `correlation_id` (UUID v4)
2. Propagate `correlation_id` to all downstream processes
3. Include `correlation_id` in all error logs
4. Include `correlation_id` in all signal emissions

---

**Created**: 2026-01-29
**Last Modified**: 2026-01-29
**Version**: 1.0.0
