<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/nodes
Barton ID: 04.04.22
Unique ID: CTB-AF095AE8
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
-->

# Node 1 — Company + People Database + PLE (TODO)

**Status:** 30k scaffolding only (no DDL/runtime)

## 30k — Scaffolding & Contracts

- [ ] Declare Ingester dependency (external repo link)
- [ ] Define Ingester → DB function contract (signature only)
- [ ] Orchestrator (Garage-MCP, build-only) + sub-agents declared
- [ ] Tools declared (Neon funcs listed, no SQL)
- [ ] PLE sub-node declared (purpose/events only)
- [ ] History policy declared (skip strategy)
- [ ] Seed CSV stub present (headers only)
- [ ] Schema placeholders exist (comment-only)
- [ ] PR template with 30k acceptance
- [ ] Render API dependency declared (external service)
- [ ] API contracts defined (signature/schema only)
- [ ] Service catalog created (external service registry)
- [ ] Migration manifest declared (schema evolution plan)
- [ ] Environment template created (config variables only)

## 20k — External Integration & Validation (placeholder)

- [ ] Ingester submodule integration strategy (design doc)
- [ ] Function contract implementation (actual code)
- [ ] People entity linking logic (design doc)
- [ ] Email validation pipeline (external service integration)
- [ ] History freshness thresholds (implementation design)
- [ ] PLE event handler implementations
- [ ] Data quality rules & validation engine

## 10k — PLE Mechanics & Scraping (placeholder)

- [ ] Contact scraping integration (Apollo API)
- [ ] PLE reconciliation flows (current/forward/reverse)
- [ ] Entity relationship mapping engine
- [ ] Lead scoring algorithm implementation
- [ ] Contact enrichment workflows
- [ ] Movement signal detection logic
- [ ] Performance optimization & caching layer

## 5k — Runtime & Operations (placeholder)

- [ ] Production database deployment with DDL
- [ ] External Ingester CI/CD integration
- [ ] Monitoring & alerting for external dependencies
- [ ] Performance dashboards & metrics
- [ ] Data backup & recovery procedures
- [ ] Security audit for external integrations
- [ ] Load testing with external Ingester
- [ ] Operational runbooks & troubleshooting

## Completion Tracking

### Overall Node Status
- **30k Progress**: 0/14 items complete (scaffolding only)
- **20k Progress**: 0/7 items (external integration design)
- **10k Progress**: 0/7 items (PLE mechanics implementation)
- **5k Progress**: 0/8 items (production runtime)

### Current Altitude: 30k
**Focus**: Contract declarations and external dependency specifications only.

**Key External Dependency**: https://github.com/djb258/ingest-companies-people

**Next Milestone**: Complete all 30k contract declarations before advancing to 20k integration design.

## Dependencies

### External (Primary)
- **Ingester Repository**: https://github.com/djb258/ingest-companies-people
  - Processes Apollo.io data + CSV uploads
- **Render-for-DB Service**: https://github.com/djb258/Render-for-DB.git
  - Database interface layer for Neon operations
- **Neon.tech**: Serverless database platform (contract only at 30k)

### Internal
- **GitHub Workflows**: Contract validation CI
- **ORBT Framework**: Process compliance
- **40k Star Tracking**: Progress rollup integration

## Integration Strategy (30k Declarations)

### Option 1: Git Submodule (Future)
```bash
git submodule add https://github.com/djb258/ingest-companies-people external/ingestor
```

### Option 2: GitHub Actions Artifact (Future)
```yaml
# Workflow dependency - artifact handoff between repos
uses: ./external/ingestor/.github/workflows/process.yml
```

### Option 3: Function Contract Interface (Current 30k)
```typescript
// Direct function interface - declared at 30k
await insertCompanyWithSlots(ingestorOutput)
```

## Notes

- **30k Constraint**: All work is declaration/contract only
- **No Implementation**: No actual database operations at 30k
- **External Dependency**: Input processing handled by separate repo
- **Contract Focus**: Interface specifications and event schemas only
- **Deferred Runtime**: All execution logic postponed to higher altitudes

This TODO feeds into [40k Star](../../docs/40k_star.md) completion tracking.