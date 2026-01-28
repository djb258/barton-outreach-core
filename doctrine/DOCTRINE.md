# Doctrine Reference

This repository is governed by **IMO-Creator**.

---

## Conformance Declaration

| Field | Value |
|-------|-------|
| **Parent** | imo-creator |
| **Sovereignty** | INHERITED |
| **Doctrine Version** | 1.5.0 |
| **CTB Version** | 1.0.0 |

---

## Child Declaration

> This repository (barton-outreach-core) inherits doctrine from IMO-Creator and operates under INHERITED sovereignty. All parent doctrine rules apply without modification. Domain-specific bindings are declared in `doctrine/REPO_DOMAIN_SPEC.md`.

---

## Binding Documents

This repository conforms to the following doctrine files from IMO-Creator:

| Document | Purpose | Location |
|----------|---------|----------|
| CANONICAL_ARCHITECTURE_DOCTRINE.md | Operating physics | imo-creator/templates/doctrine/ |
| ALTITUDE_DESCENT_MODEL.md | CC descent sequence | imo-creator/templates/doctrine/ |
| TEMPLATE_IMMUTABILITY.md | AI modification prohibition | imo-creator/templates/doctrine/ |
| SNAP_ON_TOOLBOX.yaml | Tool registry | imo-creator/templates/ |
| IMO_SYSTEM_SPEC.md | System index | imo-creator/templates/ |
| AI_EMPLOYEE_OPERATING_CONTRACT.md | Agent constraints | imo-creator/templates/ |

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
| CL_ADMISSION_GATE_DOCTRINE.md | CL authority registry admission rules | ACTIVE |
| CL_ADMISSION_GATE_WIRING.md | CL wiring implementation guidance | ACTIVE |
| CL_NON_OPERATIONAL_LOCK.md | CL non-operational lock rules | ACTIVE |
| SALES_CLIENT_NON_OPERATIONAL_LOCK.md | Sales/Client hub lock rules | ACTIVE |
| DO_NOT_MODIFY_REGISTRY.md | v1.0 frozen components | ACTIVE |
| BIT_AUTHORIZATION_INLINE.md | BIT scoring authorization rules | ACTIVE |
| DOCTRINE_DASHBOARD.md | Doctrine status overview | ACTIVE |

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-28 |
| Last Modified | 2026-01-28 |
| Status | ACTIVE |
