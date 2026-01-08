# DOL Filings Hub — CC-02

CC_VERSION: v1.1.0
LAST_VERIFIED: 2026-01-05

**CC Layer**: CC-02 (Hub)
**Doctrine ID**: 04.04.03
**Doctrine**: Canonical Architecture Doctrine v1.1.0

---

## Authority Boundary

DOL Filings owns:
- EIN resolution and matching
- Form 5500 data processing
- Schedule A analysis

## Identity Rules

| Identity | Owner | This Hub |
|----------|-------|----------|
| company_unique_id | CL via CT | CONSUME ONLY |
| filing_id | This Hub | MINT |
| ein_match_id | This Hub | MINT |

## IMO Structure

```
dol-filings/
├── CC.md
├── hub.manifest.yaml
├── __init__.py
└── imo/
    ├── input/            # CT signal ingress
    ├── middle/           # EIN matching, filing processing
    │   ├── processors/
    │   └── importers/    # 5500, 5500-SF imports
    └── output/           # EIN signals egress
```

## Upstream Dependencies

| Upstream | Signal Consumed | Required |
|----------|-----------------|----------|
| Company Target | company_unique_id, domain | YES |

## Waterfall Position

Executes BEFORE People Intelligence.
Emits: ein, filing_signals → consumed by People.
