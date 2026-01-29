# Constitutional Index

**Status**: LOCKED
**Authority**: CONSTITUTIONAL
**Version**: 1.0.0
**Change Protocol**: ADR + HUMAN APPROVAL REQUIRED

---

## Parent Doctrine

| Field | Value |
|-------|-------|
| **Parent Repository** | imo-creator |
| **Parent Version** | v1.5.0 |
| **Relationship** | Child (derives from) |
| **Sync Date** | 2026-01-29 |

---

## Bound Constitutions

| Constitution | Location | Purpose |
|--------------|----------|---------|
| PRD_CONSTITUTION.md | `templates/doctrine/PRD_CONSTITUTION.md` | PRD structural requirements |
| ERD_CONSTITUTION.md | `templates/doctrine/ERD_CONSTITUTION.md` | ERD validation protocols |
| ERD_DOCTRINE.md | `templates/doctrine/ERD_DOCTRINE.md` | ERD structural proof rules |
| PROCESS_DOCTRINE.md | `templates/doctrine/PROCESS_DOCTRINE.md` | Process declaration requirements |

---

## Domain Binding

| Field | Value |
|-------|-------|
| **Domain Specification** | `doctrine/REPO_DOMAIN_SPEC.md` |
| **Domain Version** | 2.0.0 |
| **Domain Scope** | Outreach (Marketing Intelligence & Executive Enrichment) |

---

## Enforcement Scope

### Hubs Governed

| Hub ID | Doctrine ID | Manifest Location |
|--------|-------------|-------------------|
| HUB-COMPANY-TARGET | 04.04.01 | `hubs/company-target/hub.manifest.yaml` |
| HUB-PEOPLE | 04.04.02 | `hubs/people-intelligence/hub.manifest.yaml` |
| HUB-DOL | 04.04.03 | `hubs/dol-filings/hub.manifest.yaml` |
| HUB-OUTREACH | 04.04.04 | `hubs/outreach-execution/hub.manifest.yaml` |
| HUB-BLOG-001 | 04.04.05 | `hubs/blog-content/hub.manifest.yaml` |
| talent-flow | 04.04.06 | `hubs/talent-flow/hub.manifest.yaml` |

### PRDs Governed

| PRD | Version | CC Layer |
|-----|---------|----------|
| PRD_COMPANY_HUB.md | 3.0.0 | CC-02 |
| PRD_PEOPLE_SUBHUB.md | 3.0.0 | CC-02 |
| PRD_DOL_SUBHUB.md | 4.0.0 | CC-02 |
| PRD_BIT_ENGINE.md | 3.0.0 | CC-02 |
| PRD_BLOG_NEWS_SUBHUB.md | 3.0.0 | CC-02 |
| PRD_TALENT_FLOW_SPOKE.md | 3.0.0 | CC-02 |
| PRD_OUTREACH_SPOKE.md | 4.0.0 | CC-02 |
| PRD_SOVEREIGN_COMPLETION.md | 2.0.0 | CC-02 |
| PRD_KILL_SWITCH_SYSTEM.md | 2.0.0 | CC-02 |
| PRD_COMPANY_HUB_PIPELINE.md | 3.0.0 | CC-02 |
| PRD_MASTER_ERROR_LOG.md | 2.0.0 | CC-03 |
| HUB_PROCESS_SIGNAL_MATRIX.md | 3.0.0 | CC-02 |

### Process Declarations Governed

| Process | Location |
|---------|----------|
| company-target-process.md | `ops/processes/` |
| people-intelligence-process.md | `ops/processes/` |
| dol-filings-process.md | `ops/processes/` |
| blog-content-process.md | `ops/processes/` |
| talent-flow-process.md | `ops/processes/` |
| outreach-execution-process.md | `ops/processes/` |
| sovereign-completion-process.md | `ops/processes/` |
| kill-switch-process.md | `ops/processes/` |

### ERD Governed

| ERD | Location |
|-----|----------|
| ERD_SUMMARY.md | `docs/ERD_SUMMARY.md` |
| ERD_DIAGRAM.md | `docs/ERD_DIAGRAM.md` |

---

## Audit Type

| Field | Value |
|-------|-------|
| **Audit Mode** | READ-ONLY |
| **Audit Scope** | CONSTITUTIONAL |
| **Runtime Logic** | NOT REVIEWED |
| **Schema Enforcement** | NOT REVIEWED |

---

## Compliance Chain

```
imo-creator (Parent)
    │
    ├── PRD_CONSTITUTION.md
    ├── ERD_CONSTITUTION.md
    ├── ERD_DOCTRINE.md
    └── PROCESS_DOCTRINE.md
            │
            ▼
barton-outreach-core (Child)
    │
    ├── doctrine/REPO_DOMAIN_SPEC.md (Domain Binding)
    ├── doctrine/CONSTITUTIONAL_INDEX.md (This File)
    ├── docs/prd/*.md (12 PRDs)
    ├── docs/ERD_SUMMARY.md (ERD)
    ├── hubs/*/hub.manifest.yaml (6 Manifests)
    └── ops/processes/*.md (8 Process Declarations)
```

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-29 |
| Last Modified | 2026-01-29 |
| Version | 1.0.0 |
| Status | LOCKED |
| Authority | CONSTITUTIONAL |
