# DOL Subhub — Task Checklist
## Barton Outreach Core | SVG-PLE Marketing

**Last Updated**: 2025-01-02
**Status**: Active

---

## EIN Resolution Spoke (Core)

### Schema & Data Model
- [x] Create `dol_ein_linkage-schema.sql` (append-only)
- [x] Deploy schema to Neon PostgreSQL
- [x] Add indexes for common queries
- [x] Add triggers for append-only enforcement

### Identity Gating
- [x] Implement hard identity gate validation
- [x] Require `company_unique_id`, `outreach_context_id`, `state`
- [x] Require identity anchor (domain OR linkedin)
- [x] Implement `FAIL HARD` on missing fields

### EIN Linkage Pipeline
- [x] Create `ein_validator.js` module
- [x] Implement EIN format validation
- [x] Implement hash fingerprint generation
- [x] Implement centralized `failHard()` function
- [x] Dual-write to AIR + `shq.error_master`
- [x] Integrate Apify/Firecrawl for Form 5500 retrieval

### Error Handling
- [x] Implement all 8 FAIL HARD error codes
- [x] Create error indexes for `shq.error_master`
- [x] Verify AIR logging for all events

### Company Target Gate
- [x] Hard gate on `company_target_status = PASS`
- [x] Hard gate on `ein IS NOT NULL`
- [x] Create `EIN_NOT_RESOLVED` error code

---

## Fuzzy Filing Discovery

### Implementation
- [x] Create `findCandidateFilings.js` module
- [x] Implement fuzzy matching (string-similarity)
- [x] Return ranked candidates with scores
- [x] Enforce deterministic EIN checks post-fuzzy
- [x] Implement `DOL_FILING_NOT_CONFIRMED` error code

### Documentation
- [x] Update `DOL_EIN_RESOLUTION.md` with fuzzy boundary section
- [x] Create PRD for fuzzy filing discovery
- [x] Create ADR for fuzzy boundary decision
- [x] Update Obsidian vault

---

## Violation Discovery (NEW)

### Schema & Data Model
- [x] Create `dol_violations-schema.sql` (append-only)
- [x] Define violation categories table
- [ ] Deploy violation schema to Neon PostgreSQL
- [ ] Test violation insert/deduplication

### Implementation
- [x] Create `findViolations.js` module
- [x] Implement violation normalization
- [x] Implement EIN matching for violations
- [x] Implement violation-specific AIR events
- [ ] Integrate OSHA API (enforcedata.dol.gov)
- [ ] Integrate EBSA violation data
- [ ] Integrate WHD violation data

### Views for Outreach
- [x] Create `dol.v_companies_with_violations`
- [x] Create `dol.v_violation_summary`
- [x] Create `dol.v_recent_violations`

### Documentation
- [x] Update `DOL_EIN_RESOLUTION.md` with violations section
- [x] Update PRD with violation requirements
- [x] Update ADR with violation architecture
- [x] Update Obsidian vault

---

## 5500 Projection Layer

### Views
- [x] Create `analytics.v_5500_renewal_month`
- [x] Create `analytics.v_5500_insurance_facts`
- [x] Implement confidence flags (DECLARED, INFERRED, AMBIGUOUS)

### Documentation
- [x] Create `5500_PROJECTION_LAYER.md` doctrine

---

## Pending Deployment

### Database Migrations
- [ ] Deploy `dol_ein_linkage` schema
- [ ] Deploy `dol_violations` schema
- [ ] Deploy `011_5500_projection_views.sql`
- [ ] Deploy `012_company_target_ein_error_routing.sql`
- [ ] Verify all indexes created

### Integration
- [ ] Connect to Apify for Form 5500 scraping
- [ ] Connect to Firecrawl for DOL sources
- [ ] Connect to OSHA Enforcement API
- [ ] Test full pipeline: Company Target → DOL EIN → Violations

---

## Non-Goals (ENFORCE)

The DOL Subhub must NOT:
- ❌ Assign scores
- ❌ Trigger outreach
- ❌ Detect intent
- ❌ Enrich people
- ❌ Infer beyond EIN linkage + violation facts

---

## Document References

| Document | Purpose |
|----------|---------|
| `doctrine/ple/DOL_EIN_RESOLUTION.md` | Core doctrine |
| `doctrine/ple/COMPANY_TARGET_IDENTITY.md` | Upstream doctrine |
| `doctrine/schemas/dol_ein_linkage-schema.sql` | EIN linkage schema |
| `doctrine/schemas/dol_violations-schema.sql` | Violations schema |
| `ctb/docs/prd/PRD-DOL-EIN-FUZZY-FILING-DISCOVERY.md` | PRD |
| `ctb/docs/adr/ADR-DOL-FUZZY-BOUNDARY.md` | ADR |

---

**End of DOL Subhub Task Checklist**
