# Blog Content — Pipeline Definition

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   BLOG CONTENT PIPELINE                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ INGEST: Content Sources                                      │
│ ─────────────────────────────────────────────────────────── │
│ • News feeds                                                │
│ • Funding alerts (Crunchbase, etc.)                         │
│ • Content webhooks                                          │
│ • Manual imports                                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ MATCH: Company Identification                                │
│ ─────────────────────────────────────────────────────────── │
│ • Extract company name from content                         │
│ • Match to existing company_sov_id                          │
│ • NO MINTING — must already exist in Company Lifecycle      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Match Found?   │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
        ┌─────────┐                   ┌─────────┐
        │   YES   │                   │   NO    │
        └────┬────┘                   └────┬────┘
             │                              │
             ▼                              ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│ CLASSIFY: Event Type    │    │ DISCARD: No Authority   │
│ ─────────────────────── │    │ ─────────────────────── │
│ • FUNDING_EVENT         │    │ • Log unmatched event   │
│ • ACQUISITION           │    │ • DO NOT create company │
│ • LEADERSHIP_CHANGE     │    │ • DO NOT trigger enrich │
│ • EXPANSION             │    └─────────────────────────┘
│ • PRODUCT_LAUNCH        │
│ • PARTNERSHIP           │
│ • LAYOFF                │
│ • NEGATIVE_NEWS         │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│ GATE: Lifecycle Check                                        │
│ ─────────────────────────────────────────────────────────── │
│ • Verify lifecycle_state >= ACTIVE                          │
│ • If not active → STOP (do not emit signal)                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ EMIT: BIT Signal                                             │
│ ─────────────────────────────────────────────────────────── │
│ • Emit signal to BIT engine                                 │
│ • Apply impact value:                                       │
│   - FUNDING_EVENT: +15.0                                    │
│   - ACQUISITION: +12.0                                      │
│   - LEADERSHIP_CHANGE: +8.0                                 │
│   - EXPANSION: +7.0                                         │
│   - PRODUCT_LAUNCH: +5.0                                    │
│   - PARTNERSHIP: +5.0                                       │
│   - LAYOFF: -3.0                                            │
│   - NEGATIVE_NEWS: -5.0                                     │
│ • Log to bit_signal_log                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Constraints

| Constraint | Enforcement |
|------------|-------------|
| No company minting | Match existing only |
| No enrichment trigger | Signals only |
| No lifecycle mutation | Read-only |
| Lifecycle gate | >= ACTIVE required |

---

## Key Files

| Component | File |
|-----------|------|
| Hub Manifest | `hub.manifest.yaml` |
| Event Processor | `imo/middle/` (to be implemented) |
