# Doctrine Reference

This repository is governed by **IMO-Creator**.

---

## Conformance Declaration

| Field | Value |
|-------|-------|
| **Parent** | imo-creator |
| **Sovereignty** | INHERITED |
| **Doctrine Version** | 2.8.0 |
| **CTB Version** | 1.0.0 |
| **Template Sync Date** | 2026-02-15 |

---

## Child Declaration

> This repository (barton-outreach-core) inherits doctrine from IMO-Creator and operates under INHERITED sovereignty. All parent doctrine rules apply without modification. Domain-specific bindings are declared in `doctrine/REPO_DOMAIN_SPEC.md`.

---

## Binding Documents

This repository conforms to the following doctrine files from IMO-Creator:

| Document | Purpose | Location |
|----------|---------|----------|
| ARCHITECTURE.md | Primary architecture doctrine (CTB, CC, Hub-Spoke, IMO, Descent) | imo-creator/templates/doctrine/ |
| CANONICAL_ARCHITECTURE_DOCTRINE.md | REDIRECT → ARCHITECTURE.md | imo-creator/templates/doctrine/ |
| ALTITUDE_DESCENT_MODEL.md | REDIRECT → ARCHITECTURE.md Part VI | imo-creator/templates/doctrine/ |
| TEMPLATE_IMMUTABILITY.md | AI modification prohibition | imo-creator/templates/doctrine/ |
| ROLLBACK_PROTOCOL.md | Doctrine sync rollback procedure | imo-creator/templates/doctrine/ |
| TOOLS.md | Tool doctrine and LLM containment | imo-creator/templates/integrations/ |
| SNAP_ON_TOOLBOX.yaml | Tool registry | imo-creator/templates/ |
| OSAM.md (template) | Query routing contract | imo-creator/templates/semantic/ |
| IMO_SYSTEM_SPEC.md | System index | imo-creator/templates/ |
| AI_EMPLOYEE_OPERATING_CONTRACT.md | Agent constraints | imo-creator/templates/ |
| GUARDSPEC.md | CI enforcement rules | imo-creator/templates/ |

---

## Loading Tiers (v2.3.0+)

| Tier | Name | Rule | Files |
|------|------|------|-------|
| 1 | MANDATORY | Load ALL before any work | IMO_CONTROL.json, CC_OPERATIONAL_DIGEST.md, CLAUDE.md |
| 2 | DOMAIN | Load on-demand when working in that domain | REGISTRY.yaml, column_registry.yml, PRD, OSAM, SNAP_ON_TOOLBOX.yaml |
| 3 | AUDIT | Never auto-loaded; human-requested or audit-triggered only | Full parent ARCHITECTURE.md, individual doctrine files, claude prompts |

---

## Session Startup (MANDATORY — v2.6.0+)

Every session, before any work. See `STARTUP_PROTOCOL.md` for full sequence.

1. **Doctrine version check** — compare DOCTRINE.md version vs parent manifest
2. **Load Tier 1** — 3 files only (IMO_CONTROL.json, CC_OPERATIONAL_DIGEST.md, CLAUDE.md)
3. **Verify checkpoint** — read DOCTRINE_CHECKPOINT.yaml, fill if stale
4. **Ready** — begin work, load Tier 2 on-demand

---

## Doctrine Checkpoint Protocol (v2.4.0+)

Before writing ANY code: fill `DOCTRINE_CHECKPOINT.yaml` with your plan.
Pre-commit hook (CHECK 11) rejects commits with missing or stale checkpoints.
See `DOCTRINE_CHECKPOINT.yaml` at repo root.

---

## Rollback Protocol (v2.8.0+)

If a doctrine sync breaks the child repo, follow `doctrine/ROLLBACK_PROTOCOL.md`:
1. STOP — isolate the problem
2. IDENTIFY — find the sync commit
3. REVERT — `git revert <sync-commit>`
4. PIN — update DOCTRINE.md to last working version
5. REPORT — file ADR in imo-creator
6. RE-SYNC — after parent fixes the issue

---

## Domain-Specific Bindings

This repository's domain-specific bindings are declared in:

```
doctrine/REPO_DOMAIN_SPEC.md
```

This file maps generic roles to domain-specific tables and concepts.

---

## Authority Rule

> Parent doctrine is READ-ONLY.
> Domain specifics live in REPO_DOMAIN_SPEC.md.
> If rules conflict, parent wins.

---

## Local Doctrine Extensions

This repository has the following local doctrine documents that extend (not override) parent doctrine:

| Document | Purpose | Status |
|----------|---------|--------|
| OSAM.md | Query routing contract (domain-specific) | ACTIVE |
| CL_ADMISSION_GATE_DOCTRINE.md | CL authority registry admission rules | ACTIVE |
| CL_ADMISSION_GATE_WIRING.md | CL wiring implementation guidance | ACTIVE |
| CL_NON_OPERATIONAL_LOCK.md | CL non-operational lock rules | ACTIVE |
| SALES_CLIENT_NON_OPERATIONAL_LOCK.md | Sales/Client hub lock rules | ACTIVE |
| DO_NOT_MODIFY_REGISTRY.md | v1.0 frozen components | ACTIVE |
| BIT_AUTHORIZATION_INLINE.md | BIT scoring authorization rules | ACTIVE |
| DOCTRINE_DASHBOARD.md | Doctrine status overview | ACTIVE |
| CL_COMMERCIAL_ELIGIBILITY_DOCTRINE.md | Commercial eligibility rules | ACTIVE |

---

## HEIR/ORBT Tracking System

This repository implements the HEIR/ORBT tracking system:

| Component | Location | Purpose |
|-----------|----------|---------|
| heir.doctrine.yaml | repo root | HEIR configuration |
| heir_identity.py | src/sys/heir/ | unique_id generation |
| orbt_process.py | src/sys/heir/ | process_id lifecycle |
| tracking.py | src/sys/heir/ | Unified tracking context |
| schema_guard.py | ops/enforcement/ | Cross-repo isolation |

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-28 |
| Last Modified | 2026-02-15 |
| Status | ACTIVE |
| Template Sync | v2.8.0 (2026-02-15) |
| Manifest Version | 2.8.0 |
