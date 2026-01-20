# Hubs Directory — CC-02

CC_VERSION: v1.1.0
LAST_VERIFIED: 2026-01-05

**CC Layer**: CC-02 (Hub)
**Doctrine**: Canonical Architecture Doctrine v1.1.0

---

## Definition

Hubs own authority within their declared boundary. Each hub:
- Owns all logic, state, and decisions within its domain
- Mints program-scoped identities (NOT sovereign identity)
- Operates at CC-02 level

## Contained Hubs

| Hub | Doctrine ID | Purpose | IMO Structure |
|-----|-------------|---------|---------------|
| company-target | 04.04.01 | Internal anchor, domain/pattern | imo/{input,middle,output} |
| dol-filings | 04.04.03 | EIN resolution, Form 5500 | imo/{input,middle,output} |
| people-intelligence | 04.04.02 | People discovery, slots | imo/{input,middle,output} |
| blog-content | 04.04.05 | Content signals, BIT | imo/{input,middle,output} |
| outreach-execution | 04.04.04 | Campaign execution | imo/{input,middle,output} |

## Rules

1. **No lateral hub-to-hub calls** — Use spokes
2. **No identity minting** — CL (CC-01) owns company_unique_id
3. **IMO pattern required** — Input/Middle/Output structure
4. **Write authorization** — May write to CC-03 (contexts), CC-04 (processes)

## IMO Pattern

```
hub/
├── hub.manifest.yaml     # Hub declaration
├── __init__.py           # Hub exports
└── imo/
    ├── input/            # Ingress handlers
    │   └── __init__.py
    ├── middle/           # Business logic
    │   ├── phases/       # Pipeline phases (CC-04)
    │   └── utils/        # Hub utilities
    └── output/           # Egress handlers
        └── __init__.py
```
