# Node 1 — Company + People DB (TODO)

**Status:** 30k scaffolding only (no runtime, no DDL)

## 30k — Scaffolding & Contracts

- [ ] Input declared (Apollo, CSV) in README
- [ ] Ingestor UX pages listed (Control Panel, Upload Form) in README
- [ ] Orchestrator declared (Garage-MCP, build-only) in `orchestration.yaml`
- [ ] Sub-agents declared (CSV_Ingestor, UID_Generator, Slot_Initializer)
- [ ] Tools declared (Neon functions listed, no SQL) in `tools.yaml`
- [ ] PLE sub-node declared (purpose, events) in `ple/` stubs
- [ ] History policy declared (skip strategy) in `history/` stubs
- [ ] Seed CSV stub present (headers only)
- [ ] Schema placeholders exist (comment-only files)
- [ ] ORBT PR template present with node/altitude checklist
- [ ] README explains ID patterns and acceptance gates

## 20k — People Linking & Validation (placeholder)

- [ ] Define people entities & link policy (design doc)
- [ ] Email validation plan (design doc)
- [ ] History freshness thresholds (design doc)
- [ ] Contact enrichment strategy (Apollo integration)
- [ ] Data quality rules & scoring system
- [ ] Duplicate detection algorithms
- [ ] PII handling & compliance framework

## 10k — Scraper & PLE Mechanics (placeholder)

- [ ] Scraper contracts (Apollo, LinkedIn, web sources)
- [ ] PLE reconciliation flows (current/forward/reverse)
- [ ] Contact data normalization engine
- [ ] Lead scoring algorithm implementation
- [ ] Entity relationship mapping
- [ ] Data freshness monitoring
- [ ] Performance optimization & caching

## 5k — Runtime & Operations (placeholder)

- [ ] Production database deployment
- [ ] Monitoring & alerting systems
- [ ] Performance dashboards
- [ ] Data backup & recovery procedures  
- [ ] Security audit & penetration testing
- [ ] Load testing & capacity planning
- [ ] Documentation & training materials
- [ ] SLA definitions & monitoring

## Completion Tracking

### Overall Node Status
- **30k Progress**: 0/11 items complete
- **20k Progress**: 0/7 items (placeholders)
- **10k Progress**: 0/7 items (placeholders)
- **5k Progress**: 0/8 items (placeholders)

### Current Altitude: 30k
**Focus**: Scaffolding contracts and declarations only. No actual implementation.

**Next Milestone**: Complete all 30k items before advancing to 20k design phase.

## Dependencies

### External
- PostgreSQL 14+ for database layer
- Apollo.io API access for company data
- Neon.tech for serverless database functions

### Internal  
- GitHub workflows for CI/CD
- ORBT framework compliance
- 40k Star tracking integration

## Notes

- All 30k work is scaffolding/contracts only
- No actual SQL implementation at 30k level
- Schema files contain comments/placeholders only
- Runtime functionality begins at 20k altitude
- This TODO feeds into [40k Star](../../docs/40k_star.md) completion tracking