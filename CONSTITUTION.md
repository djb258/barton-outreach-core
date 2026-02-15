# Constitution

**Status**: INHERITED
**Authority**: IMO-Creator (Parent Sovereign)
**Version**: 1.1.0
**Last Updated**: 2026-02-15

---

## Constitutional Inheritance

This repository inherits its constitution from **IMO-Creator**.

| Field | Value |
|-------|-------|
| **Parent Sovereign** | IMO-Creator |
| **Upstream Repo** | imo-creator |
| **Upstream Commit** | ddf45bb |
| **Conformance Version** | Architecture 2.1.0 |
| **Conformance Direction** | DOWNSTREAM (we conform to parent) |

**Governance Rule**: Doctrine flows DOWN, never UP. This repository CONFORMS to imo-creator. It does not CONTRIBUTE to it.

---

## What This Constitution Governs

- **Repo structure** — CTB branches define physical placement
- **Descent order** — CC layers define authority hierarchy
- **Flow ownership** — IMO defines ingress/middle/egress within hubs
- **Hub/Spoke geometry** — Hubs own logic, spokes carry data
- **Enforcement mechanisms** — Pre-commit, CI, Claude Code

---

## What This Constitution Does NOT Govern

- Programming languages
- Frameworks or libraries
- Test strategies or coverage targets
- Logging implementations
- Deployment mechanics
- Internal folder structure within CTB branches
- Naming conventions

These are **local policy**, delegated to this repository.

---

## The Transformation Law (CONST → VAR)

**This is the supreme governing principle.**

> Nothing may exist unless it transforms declared constants into declared variables.

| Proof Type | Purpose | Authority |
|------------|---------|-----------|
| **PRD** | Explains WHY and HOW the transformation occurs | Behavioral proof |
| **ERD** | Proves WHAT structural artifacts are allowed to exist | Structural proof |
| **Process** | Executes constitutionally approved transformations | Execution declaration |

**Constitutional rule**: No hub, table, schema, or identifier may be instantiated without both proofs.

---

## Repository-Specific Transformation

This repository transforms:

```
CONSTANTS (Inputs)                    VARIABLES (Outputs)
─────────────────                     ──────────────────
sovereign_company_id (from CL)   →    outreach_id (minted here)
company_domain (from CL)         →    verified_email_pattern
identity_status (from CL)        →    target_status (PASS/FAIL)
raw_filings (from DOL)           →    filing_signals
raw_people (from LinkedIn)       →    slot_assignments
```

**Transformation Statement**: This repository transforms sovereign company identities from CL into marketing-ready targeting records with verified email patterns, filing signals, and slot assignments.

---

## Canonical Invariants (Inherited)

- **Transformation law**: Constants → Variables (requires PRD + ERD proof)
- **CTB branches**: `sys` / `data` / `app` / `ai` / `ui`
- **CC descent gates**: PRD before code, ADR before code
- **Hub owns logic**: Spokes carry data only, no logic
- **Sub-hub table cardinality**: Exactly 1 CANONICAL + 1 ERROR table per sub-hub (ADR-001)
- **Forbidden folders**: `utils`, `helpers`, `common`, `shared`, `lib`, `misc`
- **Doctrine-first**: Structure before code, gates before artifacts

---

## Local Extensions

This repository extends the parent constitution with:

| Extension | Document |
|-----------|----------|
| CL Authority Registry | `doctrine/CL_AUTHORITY_DOCTRINE.md` |
| Outreach Operational Spine | `doctrine/OUTREACH_SPINE_DOCTRINE.md` |
| Commercial Eligibility | `doctrine/CL_COMMERCIAL_ELIGIBILITY_DOCTRINE.md` |
| Hub Waterfall Order | `doctrine/REPO_DOMAIN_SPEC.md` |
| Frozen Components | `doctrine/DO_NOT_MODIFY_REGISTRY.md` |

---

## Enforcement

| Layer | Mechanism |
|-------|-----------|
| Claude Code | Reads doctrine, audits structure, blocks violations |
| Audit | `docs/audits/AUDIT_PROCEDURE.md` — produces attestation |
| Checklists | `templates/checklists/` — mandatory for compliance |

---

## Audit Requirements

**Every audit MUST produce:**

1. `QUARTERLY_HYGIENE_AUDIT_YYYY-QN.md` — Filled checklist
2. `CONSTITUTIONAL_AUDIT_ATTESTATION_YYYY-MM-DD.md` — Sign-off document

**Audits without attestation are NON-AUTHORITATIVE.**

See: `docs/audits/AUDIT_PROCEDURE.md`

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-29 |
| Last Modified | 2026-02-15 |
| Version | 1.1.0 |
| Status | INHERITED |
| Authority | IMO-Creator (Parent Sovereign) |
| Change Protocol | ADR + HUMAN APPROVAL REQUIRED |

---

## Traceability

| Document | Location |
|----------|----------|
| Parent Constitution | imo-creator/CONSTITUTION.md |
| IMO Control | ./IMO_CONTROL.json |
| Registry | ./REGISTRY.yaml |
| Doctrine | ./doctrine/DOCTRINE.md |
| Domain Spec | ./doctrine/REPO_DOMAIN_SPEC.md |
