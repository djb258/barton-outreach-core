# Company Target Hub — CC-02

CC_VERSION: v1.1.0
LAST_VERIFIED: 2026-01-05

**CC Layer**: CC-02 (Hub)
**Doctrine ID**: 04.04.01
**Doctrine**: Canonical Architecture Doctrine v1.1.0

---

## Authority Boundary

Company Target is the **internal anchor** for the Outreach program.
It receives `company_unique_id` from CL (CC-01) and owns:
- Domain resolution
- Email pattern discovery
- BIT scoring

## Identity Rules

| Identity | Owner | This Hub |
|----------|-------|----------|
| company_unique_id | CL (CC-01) | RECEIVE ONLY |
| outreach_context_id | This Hub | MINT (program-scoped) |
| target_id | This Hub | MINT (internal) |

## IMO Structure

```
company-target/
├── CC.md                 # This file
├── hub.manifest.yaml     # Hub declaration
├── __init__.py
└── imo/
    ├── input/            # CL identity ingress
    ├── middle/           # Domain, pattern, BIT logic
    │   ├── phases/       # CC-04 phase execution
    │   ├── email/        # Pattern discovery
    │   └── utils/        # cl_gate.py enforces CC-01 boundary
    └── output/           # Downstream egress
```

## Upstream Gate

`imo/middle/utils/cl_gate.py` enforces the CC-01 boundary:
- **MUST** verify company exists in CL before proceeding
- **MUST NOT** mint, modify, or infer company_unique_id
- **MUST** HARD FAIL on missing identity

## Write Permissions

| Target | Permitted? | Via |
|--------|------------|-----|
| CC-01 (CL) | DENIED | Never |
| CC-02 (other hubs) | Via spoke | contracts/ |
| CC-03 (context) | PERMITTED | outreach_context |
| CC-04 (process) | PERMITTED | phases/ |
