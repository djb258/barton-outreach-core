# Barton Outreach Core - Obsidian Vault

## Overview

This vault contains documentation for the Barton Outreach Core system, following the IMO-Creator format and CL Parent-Child Doctrine.

**v1.0 Operational Baseline Status**: CERTIFIED + FROZEN (2026-01-20)

## Structure

```
obsidian/
├── 10-PRD/              # Product Requirements Documents
├── 20-ADR/              # Architecture Decision Records
├── 30-DOCS/             # Technical Documentation
│   ├── dol-hub/         # DOL Sub-Hub specific docs
│   ├── sovereign-completion/  # Sovereign Completion docs
│   └── v1-baseline/     # v1.0 Operational Baseline docs
├── 40-CHECKLISTS/       # Compliance Checklists
└── README.md            # This file
```

## Quick Links

### v1.0 Operational Baseline (NEW)
- [[V1 Operational Baseline]] - Certified go-live state
- [[Tier Telemetry]] - Distribution and drift analytics
- [[Marketing Safety Gate]] - HARD_FAIL enforcement
- [[Kill Switch System]] - Manual overrides
- [[Sovereign Completion Overview]] - Hub status tracking

### Hubs
- [[DOL Sub-Hub Overview]]
- [[Company Target Hub]]
- [[People Intelligence Hub]]

### Key Documents
- [[PRD_DOL_SUBHUB|DOL Sub-Hub PRD v3.0]]
- [[ADR-004|DOL Data Import & Read-Only Lock]]
- [[DOL_HUB_COMPLIANCE|DOL Compliance Checklist]]

### Schemas
- [[DOL Schema ERD]]
- [[Column Metadata Guide]]

## Tags

- `#v1` - v1.0 Operational Baseline
- `#frozen` - FROZEN components (DO NOT MODIFY)
- `#hub/dol` - DOL Sub-Hub content
- `#prd` - Product Requirements
- `#adr` - Architecture Decisions
- `#schema` - Database schemas
- `#hardened` - Production-ready artifacts
- `#analytics` - Telemetry and analytics
- `#safety` - Safety gate enforcement

## Last Updated

2026-01-20
