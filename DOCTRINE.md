# Doctrine Reference

**Repository:** barton-outreach-cc
**Governed By:** IMO-Creator
**Status:** DOWNSTREAM
**Last Audit:** 2026-01-08

---

## Constitutional Authority

This repository is governed by **IMO-Creator** as the upstream constitutional authority.

| Field | Value |
|-------|-------|
| Upstream Repository | imo-creator |
| Upstream Commit | bf1de681b |
| Upstream Location | C:/Users/CUSTOMER PC/Cursor Repo/imo-creator |
| Control File | IMO_CONTROL.json |

---

## Binding Doctrine Files

The following doctrine files from IMO-Creator are binding on this repository:

| File | Purpose | Version |
|------|---------|---------|
| CANONICAL_ARCHITECTURE_DOCTRINE.md | Operating physics - CC layers, hub-spoke, CTB branches | 1.2.0 |
| HUB_SPOKE_ARCHITECTURE.md | Geometry law - hub owns logic, spokes are interfaces | 1.2.0 |
| ALTITUDE_DESCENT_MODEL.md | Descent law - CC-01→02→03→04 sequence | 1.1.0 |

---

## Local Policy (This Repository)

This repository uses the **IMO_HUBS** structural variant:

| Element | Location | Description |
|---------|----------|-------------|
| **Hubs** | `hubs/` | Major functional boundaries with IMO substructure |
| **Spokes** | `spokes/` | Interface contracts between hubs (data only) |
| **Ops** | `ops/` | Operational infrastructure |
| **Docs** | `docs/` | Documentation (PRDs, ADRs, diagrams) |
| **Contexts** | `contexts/` | Configuration and context files |
| **Contracts** | `contracts/` | Data contracts between hubs |

### IMO Substructure

Each hub follows Input-Middle-Output (IMO) pattern:

```
hubs/{hub-name}/
├── imo/
│   ├── input/    # Data ingestion, validation
│   ├── middle/   # Business logic, processing
│   └── output/   # Data emission, exports
├── CHECKLIST.md
├── PRD.md
└── ADR.md
```

---

## Active Certifications

| ID | System | Status | Date |
|----|--------|--------|------|
| **TF-001** | Talent Flow | 🚀 PRODUCTION-READY | 2026-01-08 |

---

## Known Technical Debt

| Location | Violation | Status | Remediation |
|----------|-----------|--------|-------------|
| `hubs/company-target/imo/middle/utils/` | CTB_VIOLATION | DOCUMENTED | Requires ADR-approved refactor |

---

## Governance Rules

1. **Modification requires ADR + human approval**
2. **Structure changes require doctrine review**
3. **New certifications require formal process**
4. **Forbidden folders may not be created**

---

## How to Verify Compliance

1. Read `IMO_CONTROL.json` at repository root
2. Check `known_violations` section for documented debt
3. Run audit to detect new violations
4. Report findings before proceeding

---

**Document Control**

| Field | Value |
|-------|-------|
| Created | 2026-01-08 |
| Authority | IMO-Creator (Constitutional) |
| Status | ACTIVE |
| Author | Claude Code (IMO-Creator) |
