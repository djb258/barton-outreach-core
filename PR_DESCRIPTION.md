# Pull Request: DOL EIN Refactor + Fuzzy Filing Discovery

## Summary

Complete refactor of the DOL Subhub to EIN Resolution Only, with the addition of fuzzy filing discovery for Form 5500 matching.

## Changes

### New Files

| File | Description |
|------|-------------|
| `ctb/sys/dol-ein/findCandidateFilings.js` | Fuzzy filing discovery + deterministic validation |
| `ctb/sys/company-target/identity_validator.js` | Company Target EIN resolution with ENRICHMENT routing |
| `ctb/data/infra/migrations/011_5500_projection_views.sql` | 5500 renewal month + insurance facts views |
| `ctb/data/infra/migrations/012_company_target_ein_error_routing.sql` | Error routing indexes |
| `doctrine/ple/COMPANY_TARGET_IDENTITY.md` | Company Target identity doctrine |
| `doctrine/ple/5500_PROJECTION_LAYER.md` | 5500 projection layer doctrine |
| `ctb/docs/prd/PRD-DOL-EIN-FUZZY-FILING-DISCOVERY.md` | Product requirements |
| `ctb/docs/adr/ADR-DOL-FUZZY-BOUNDARY.md` | Architecture decision record |
| `ctb/docs/obsidian-vault/architecture/DOL-EIN-Fuzzy-Discovery.md` | Obsidian documentation |

### Modified Files

| File | Changes |
|------|---------|
| `ctb/sys/dol-ein/ein_validator.js` | Added `DOL_FILING_NOT_CONFIRMED`, `validateEINResolutionGate`, `failHardFilingNotConfirmed` |
| `doctrine/ple/DOL_EIN_RESOLUTION.md` | Added Section 9: Fuzzy Matching Boundary |
| `doctrine/README.md` | Updated index with Company Target + DOL execution gate |
| `ctb/docs/tasks/hub_tasks.md` | Updated task completion status |
| `ctb/docs/obsidian-vault/README.md` | Updated structure |

## Execution Flow

```
Company Target (PASS, EIN locked)
        ↓
DOL Subhub
  ├─ fuzzy → candidate filings
  ├─ deterministic validation
        ├─ PASS → append-only write
        └─ FAIL → DOL_FILING_NOT_CONFIRMED
```

## Error Codes Added

| Code | Layer | Trigger |
|------|-------|---------|
| `EIN_NOT_RESOLVED` | Company Target | Fuzzy EIN resolution failed |
| `DOL_FILING_NOT_CONFIRMED` | DOL | Deterministic validation rejected all candidates |

## Doctrine Compliance

- [x] DOL Subhub is EIN Resolution ONLY
- [x] Fuzzy matching for filing discovery only (not EIN resolution)
- [x] Deterministic EIN validation before any write
- [x] All failures dual-write to AIR + `shq.error_master`
- [x] No fuzzy logic in analytics views
- [x] No changes to Company Target execution boundary

## Testing Checklist

- [ ] Deploy schema migrations to Neon
- [ ] Test identity gate validation
- [ ] Test fuzzy filing discovery with sample data
- [ ] Verify deterministic validation rejects mismatched EINs
- [ ] Confirm error routing to `shq.error_master`
- [ ] Verify AIR logging

## Related Documents

- PRD: `ctb/docs/prd/PRD-DOL-EIN-FUZZY-FILING-DISCOVERY.md`
- ADR: `ctb/docs/adr/ADR-DOL-FUZZY-BOUNDARY.md`
- Doctrine: `doctrine/ple/DOL_EIN_RESOLUTION.md`
