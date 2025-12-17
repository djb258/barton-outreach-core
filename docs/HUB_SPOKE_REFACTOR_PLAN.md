# Hub-and-Spoke Repository Refactor Plan

**Status:** DRAFT
**Version:** 1.0
**Date:** 2025-12-17
**Doctrine:** Barton Doctrine / Bicycle Wheel v1.1

---

## Executive Summary

This document defines the target directory structure, code ownership mapping, branch cleanup plan, and file deletion list for refactoring barton-outreach-core to a clean Hub-and-Spoke architecture.

**Principle:** PRDs are law. Code conforms. If a file doesn't belong to a hub/spoke, it doesn't belong.

---

## 1. Target Directory Structure

```
barton-outreach-core/
│
├── hub/
│   └── company/                           # COMPANY HUB (Master Node)
│       ├── README.md                      # Hub documentation
│       ├── __init__.py
│       ├── company_hub.py                 # Core hub implementation
│       ├── bit_engine.py                  # BIT scoring engine
│       ├── phases/
│       │   ├── __init__.py
│       │   ├── phase1_company_matching.py
│       │   ├── phase1b_unmatched_hold.py
│       │   ├── phase2_domain_resolution.py
│       │   ├── phase3_email_pattern_waterfall.py
│       │   └── phase4_pattern_verification.py
│       ├── email/
│       │   ├── __init__.py
│       │   ├── pattern_discovery_pipeline.py
│       │   ├── pattern_guesser.py
│       │   └── bulk_verifier.py
│       ├── movement_engine/
│       │   ├── __init__.py
│       │   ├── state_machine.py
│       │   └── movement_rules.py
│       └── utils/
│           ├── __init__.py
│           ├── fuzzy.py
│           ├── normalization.py
│           └── patterns.py
│
├── spokes/
│   ├── people/                            # PEOPLE SPOKE (Spoke #1)
│   │   ├── README.md
│   │   ├── __init__.py
│   │   ├── people_spoke.py                # Main spoke implementation
│   │   ├── hub_gate.py                    # Company anchor validation
│   │   ├── slot_assignment.py             # CEO/CFO/HR slot logic
│   │   ├── phases/
│   │   │   ├── __init__.py
│   │   │   ├── phase0_people_ingest.py
│   │   │   ├── phase5_email_generation.py
│   │   │   ├── phase6_slot_assignment.py
│   │   │   ├── phase7_enrichment_queue.py
│   │   │   └── phase8_output_writer.py
│   │   └── sub_wheels/
│   │       └── email_verification/
│   │           ├── __init__.py
│   │           ├── bulk_verifier_spoke.py
│   │           └── pattern_guesser_spoke.py
│   │
│   ├── dol/                               # DOL SPOKE (Spoke #2)
│   │   ├── README.md
│   │   ├── __init__.py
│   │   ├── dol_spoke.py                   # Main spoke implementation
│   │   ├── form5500_processor.py
│   │   ├── schedule_a_processor.py
│   │   ├── ein_matcher.py
│   │   └── importers/
│   │       ├── __init__.py
│   │       ├── import_5500.py
│   │       ├── import_5500_sf.py
│   │       └── import_schedule_a.py
│   │
│   ├── blog_news/                         # BLOG/NEWS SPOKE (Spoke #3) - PLANNED
│   │   ├── README.md
│   │   ├── __init__.py
│   │   └── .gitkeep
│   │
│   ├── talent_flow/                       # TALENT FLOW SPOKE (Spoke #4) - SHELL
│   │   ├── README.md
│   │   ├── __init__.py
│   │   ├── talent_flow_spoke.py
│   │   └── company_gate.py
│   │
│   └── outreach/                          # OUTREACH SPOKE (Spoke #5) - PLANNED
│       ├── README.md
│       ├── __init__.py
│       ├── outreach_spoke.py
│       └── promote_to_log.py
│
├── ops/
│   ├── master_error_log/                  # CROSS-CUTTING: Error Observability
│   │   ├── README.md
│   │   ├── __init__.py
│   │   ├── master_error_emitter.py
│   │   └── migrations/
│   │       ├── 002_create_master_error_log.sql
│   │       └── 003_enforce_immutability.sql
│   │
│   ├── phase_registry/                    # Phase execution framework
│   │   ├── __init__.py
│   │   ├── outreach_phase_registry.py
│   │   └── phase_executor.py
│   │
│   ├── validation/                        # Validation framework
│   │   ├── __init__.py
│   │   ├── validation_rules.py
│   │   └── db_utils.py
│   │
│   ├── providers/                         # External provider integrations
│   │   ├── __init__.py
│   │   ├── providers.py                   # Tier 0/1/2/3 waterfall
│   │   └── rate_limiter.py
│   │
│   └── reporting/                         # Funnel reports
│       ├── __init__.py
│       ├── funnel_math.py
│       └── forecast_model.py
│
├── infra/                                 # Infrastructure (unchanged)
│   ├── migrations/
│   ├── scripts/
│   └── docs/
│
├── docs/                                  # Documentation
│   ├── prd/                               # PRD documents (SOURCE OF TRUTH)
│   │   ├── PRD_COMPANY_HUB.md
│   │   ├── PRD_PEOPLE_SUBHUB.md
│   │   ├── PRD_DOL_SUBHUB.md
│   │   ├── PRD_BLOG_NEWS_SUBHUB.md
│   │   ├── PRD_MASTER_ERROR_LOG.md
│   │   └── HUB_PROCESS_SIGNAL_MATRIX.md
│   └── architecture/
│       ├── BICYCLE_WHEEL_DOCTRINE.md
│       └── HUB_AND_SPOKE_ARCHITECTURE.md
│
├── services/                              # External service integrations
│   ├── apollo-scraper/
│   ├── csv-data-ingestor/
│   ├── heyreach-integration/
│   └── instantly-integration/
│
├── ui/                                    # Frontend (consolidated)
│   └── [existing ctb/ui structure]
│
├── tests/                                 # Test suite
│   ├── hub/
│   ├── spokes/
│   └── ops/
│
├── .archive/                              # Archived legacy code
│   ├── HEIR-AGENT-SYSTEM/
│   ├── enrichment-hub/
│   ├── outreach_core/
│   └── legacy_ctb_sys/
│
├── CLAUDE.md
├── README.md
└── package.json
```

---

## 2. Code Ownership Mapping

### 2.1 COMPANY HUB (hub/company/)

| Current Location | Target Location | PRD Reference |
|------------------|-----------------|---------------|
| `ctb/sys/enrichment/pipeline_engine/hub/company_hub.py` | `hub/company/company_hub.py` | PRD_COMPANY_HUB.md |
| `ctb/sys/enrichment/pipeline_engine/hub/bit_engine.py` | `hub/company/bit_engine.py` | PRD_COMPANY_HUB.md |
| `ctb/sys/enrichment/pipeline_engine/phases/phase1_company_matching.py` | `hub/company/phases/phase1_company_matching.py` | PRD_COMPANY_HUB_PIPELINE.md |
| `ctb/sys/enrichment/pipeline_engine/phases/phase1b_unmatched_hold_export.py` | `hub/company/phases/phase1b_unmatched_hold.py` | PRD_COMPANY_HUB_PIPELINE.md |
| `ctb/sys/enrichment/pipeline_engine/phases/phase2_domain_resolution.py` | `hub/company/phases/phase2_domain_resolution.py` | PRD_COMPANY_HUB_PIPELINE.md |
| `ctb/sys/enrichment/pipeline_engine/phases/phase3_email_pattern_waterfall.py` | `hub/company/phases/phase3_email_pattern_waterfall.py` | PRD_COMPANY_HUB_PIPELINE.md |
| `ctb/sys/enrichment/pipeline_engine/phases/phase4_pattern_verification.py` | `hub/company/phases/phase4_pattern_verification.py` | PRD_COMPANY_HUB_PIPELINE.md |
| `ctb/sys/enrichment/pipeline_engine/email/pattern_discovery_pipeline.py` | `hub/company/email/pattern_discovery_pipeline.py` | PRD_COMPANY_HUB.md |
| `ctb/sys/enrichment/pipeline_engine/email/pattern_guesser.py` | `hub/company/email/pattern_guesser.py` | PRD_COMPANY_HUB.md |
| `ctb/sys/enrichment/pipeline_engine/email/bulk_verifier.py` | `hub/company/email/bulk_verifier.py` | PRD_COMPANY_HUB.md |
| `ctb/sys/enrichment/pipeline_engine/movement_engine/` | `hub/company/movement_engine/` | PRD_COMPANY_HUB.md |
| `ctb/sys/enrichment/pipeline_engine/utils/fuzzy.py` | `hub/company/utils/fuzzy.py` | PRD_COMPANY_HUB.md |
| `ctb/sys/enrichment/pipeline_engine/utils/normalization.py` | `hub/company/utils/normalization.py` | PRD_COMPANY_HUB.md |
| `ctb/sys/enrichment/pipeline_engine/utils/patterns.py` | `hub/company/utils/patterns.py` | PRD_COMPANY_HUB.md |

### 2.2 PEOPLE SPOKE (spokes/people/)

| Current Location | Target Location | PRD Reference |
|------------------|-----------------|---------------|
| `ctb/sys/enrichment/pipeline_engine/spokes/people_node/people_node_spoke.py` | `spokes/people/people_spoke.py` | PRD_PEOPLE_SUBHUB.md |
| `ctb/sys/enrichment/pipeline_engine/spokes/people_node/hub_gate_spoke.py` | `spokes/people/hub_gate.py` | PRD_PEOPLE_SUBHUB.md |
| `ctb/sys/enrichment/pipeline_engine/spokes/people_node/slot_assignment_spoke.py` | `spokes/people/slot_assignment.py` | PRD_PEOPLE_SUBHUB.md |
| `ctb/sys/enrichment/pipeline_engine/phases/phase0_people_ingest.py` | `spokes/people/phases/phase0_people_ingest.py` | PRD_PEOPLE_SUBHUB.md |
| `ctb/sys/enrichment/pipeline_engine/phases/phase5_email_generation.py` | `spokes/people/phases/phase5_email_generation.py` | PRD_PEOPLE_SUBHUB.md |
| `ctb/sys/enrichment/pipeline_engine/phases/phase6_slot_assignment.py` | `spokes/people/phases/phase6_slot_assignment.py` | PRD_PEOPLE_SUBHUB.md |
| `ctb/sys/enrichment/pipeline_engine/phases/phase7_enrichment_queue.py` | `spokes/people/phases/phase7_enrichment_queue.py` | PRD_PEOPLE_SUBHUB.md |
| `ctb/sys/enrichment/pipeline_engine/phases/phase8_output_writer.py` | `spokes/people/phases/phase8_output_writer.py` | PRD_PEOPLE_SUBHUB.md |
| `ctb/sys/enrichment/pipeline_engine/spokes/people_node/sub_wheels/` | `spokes/people/sub_wheels/` | PRD_PEOPLE_SUBHUB.md |

### 2.3 DOL SPOKE (spokes/dol/)

| Current Location | Target Location | PRD Reference |
|------------------|-----------------|---------------|
| `ctb/sys/enrichment/pipeline_engine/spokes/dol_node/dol_node_spoke.py` | `spokes/dol/dol_spoke.py` | PRD_DOL_SUBHUB.md |
| `ctb/sys/enrichment/import_5500.py` | `spokes/dol/importers/import_5500.py` | PRD_DOL_SUBHUB.md |
| `ctb/sys/enrichment/import_5500_sf.py` | `spokes/dol/importers/import_5500_sf.py` | PRD_DOL_SUBHUB.md |
| `ctb/sys/enrichment/import_schedule_a.py` | `spokes/dol/importers/import_schedule_a.py` | PRD_DOL_SUBHUB.md |
| `ctb/sys/enrichment/extract_schedule_a_renewals.py` | `spokes/dol/schedule_a_processor.py` | PRD_DOL_SUBHUB.md |
| `ctb/sys/enrichment/join_form5500_schedule_a.py` | `spokes/dol/form5500_processor.py` | PRD_DOL_SUBHUB.md |
| `ctb/sys/enrichment/backfill_ein_from_dol.py` | `spokes/dol/ein_matcher.py` | PRD_DOL_SUBHUB.md |

### 2.4 MASTER ERROR LOG (ops/master_error_log/)

| Current Location | Target Location | PRD Reference |
|------------------|-----------------|---------------|
| `ctb/sys/enrichment/pipeline_engine/utils/master_error_emitter.py` | `ops/master_error_log/master_error_emitter.py` | PRD_MASTER_ERROR_LOG.md |
| `infra/migrations/002_create_master_error_log.sql` | `ops/master_error_log/migrations/002_create_master_error_log.sql` | PRD_MASTER_ERROR_LOG.md |
| `infra/migrations/003_enforce_master_error_immutability.sql` | `ops/master_error_log/migrations/003_enforce_immutability.sql` | PRD_MASTER_ERROR_LOG.md |

### 2.5 OPS (ops/)

| Current Location | Target Location | PRD Reference |
|------------------|-----------------|---------------|
| `ctb/sys/toolbox-hub/backend/outreach_phase_registry.py` | `ops/phase_registry/outreach_phase_registry.py` | HUB_PROCESS_SIGNAL_MATRIX.md |
| `ctb/sys/toolbox-hub/backend/validator/validation_rules.py` | `ops/validation/validation_rules.py` | All PRDs |
| `ctb/sys/toolbox-hub/backend/validator/db_utils.py` | `ops/validation/db_utils.py` | All PRDs |
| `ctb/sys/enrichment/pipeline_engine/utils/providers.py` | `ops/providers/providers.py` | PRD_COMPANY_HUB_PIPELINE.md |
| `ctb/sys/enrichment/rate_limiter.py` | `ops/providers/rate_limiter.py` | PRD_COMPANY_HUB_PIPELINE.md |
| `ctb/sys/reporting/funnel_reports/` | `ops/reporting/` | All PRDs |

---

## 3. Branch Cleanup Plan

### 3.1 Branch Inventory (50 branches total)

```
LOCAL BRANCHES (23):
├── main                              # PRIMARY - KEEP
├── feature/node1-enrichment-queue    # ACTIVE - KEEP (current work)
├── feature/ctb-full-implementation   # REVIEW - likely merge to main
├── doctrine/get-ingest               # KEEP - doctrine branch
├── imo/input                         # KEEP - IMO integration
├── imo/middle                        # KEEP - IMO integration
├── imo/output                        # KEEP - IMO integration
├── ops/automation-scripts            # KEEP - operational
├── ops/report-builder                # KEEP - operational
├── sys/activepieces                  # DELETE - not referenced by PRD
├── sys/agent-fleet-deploy            # DELETE - not referenced by PRD
├── sys/bigquery-warehouse            # DELETE - not referenced by PRD
├── sys/builder-bridge                # DELETE - not referenced by PRD
├── sys/chartdb                       # DELETE - not referenced by PRD
├── sys/claude-skills                 # REVIEW - may be useful
├── sys/composio-mcp                  # KEEP - MCP integration
├── sys/enrichment-garage-2.0         # DELETE - superseded
├── sys/firebase-workbench            # DELETE - not referenced by PRD
├── sys/github-factory                # DELETE - not referenced by PRD
├── sys/neon-vault                    # KEEP - database config
├── sys/outreach-tools-backend        # REVIEW - may merge to outreach spoke
├── sys/security-audit                # DELETE - not referenced by PRD
├── sys/windmill                      # DELETE - not referenced by PRD
└── ui                                # KEEP - UI branch

REMOTE-ONLY BRANCHES (additional):
├── feature/apollo-scraper-api        # MERGE to services/ then DELETE
├── feature/csv-data-ingestor         # MERGE to services/ then DELETE
├── feature/instantly-heyreach-integrations  # MERGE to services/ then DELETE
├── feature/message-agent-outreach    # REVIEW - may merge to outreach spoke
├── feature/ui-development            # MERGE to ui then DELETE
├── gitingest                         # DELETE - utility branch
├── node-1-company-db                 # MERGE to hub/company then DELETE
├── node-1-company-people-ple         # MERGE to spokes/people then DELETE
├── node-2-messaging-prep             # MERGE to spokes/outreach then DELETE
├── node-3-campaign-exec              # MERGE to spokes/outreach then DELETE
└── claude/pull-repository-*          # DELETE - temporary
```

### 3.2 Branch Actions

| Branch | Action | Justification |
|--------|--------|---------------|
| `main` | **KEEP** | Primary branch |
| `feature/node1-enrichment-queue` | **KEEP** | Active development |
| `feature/ctb-full-implementation` | **MERGE → main** | Contains valuable CTB work |
| `doctrine/get-ingest` | **KEEP** | Doctrine reference |
| `imo/*` (3 branches) | **KEEP** | IMO integration pattern |
| `ops/*` (2 branches) | **KEEP** | Operational branches |
| `ui` | **KEEP** | UI development |
| `sys/composio-mcp` | **KEEP** | MCP integration |
| `sys/neon-vault` | **KEEP** | Database config |
| `sys/activepieces` | **DELETE** | No PRD reference |
| `sys/agent-fleet-deploy` | **DELETE** | No PRD reference |
| `sys/bigquery-warehouse` | **DELETE** | No PRD reference |
| `sys/builder-bridge` | **DELETE** | No PRD reference |
| `sys/chartdb` | **DELETE** | No PRD reference |
| `sys/enrichment-garage-2.0` | **DELETE** | Superseded by pipeline_engine |
| `sys/firebase-workbench` | **DELETE** | No PRD reference |
| `sys/github-factory` | **DELETE** | No PRD reference |
| `sys/security-audit` | **DELETE** | No PRD reference |
| `sys/windmill` | **DELETE** | No PRD reference |
| `node-1-company-db` | **SQUASH → hub/company** | Node 1 content |
| `node-1-company-people-ple` | **SQUASH → spokes/people** | PLE content |
| `node-2-messaging-prep` | **SQUASH → spokes/outreach** | Messaging prep |
| `node-3-campaign-exec` | **SQUASH → spokes/outreach** | Campaign execution |
| `feature/apollo-scraper-api` | **SQUASH → services/** | Service content |
| `feature/csv-data-ingestor` | **SQUASH → services/** | Service content |
| `feature/instantly-heyreach-integrations` | **SQUASH → services/** | Service content |
| `feature/ui-development` | **SQUASH → ui** | UI content |
| `gitingest` | **DELETE** | Utility branch |
| `claude/pull-repository-*` | **DELETE** | Temporary |

### 3.3 Branch Cleanup Commands

```bash
# DELETE obsolete local branches
git branch -D sys/activepieces
git branch -D sys/agent-fleet-deploy
git branch -D sys/bigquery-warehouse
git branch -D sys/builder-bridge
git branch -D sys/chartdb
git branch -D sys/enrichment-garage-2.0
git branch -D sys/firebase-workbench
git branch -D sys/github-factory
git branch -D sys/security-audit
git branch -D sys/windmill

# DELETE obsolete remote branches
git push origin --delete sys/activepieces
git push origin --delete sys/agent-fleet-deploy
git push origin --delete sys/bigquery-warehouse
git push origin --delete sys/builder-bridge
git push origin --delete sys/chartdb
git push origin --delete sys/enrichment-garage-2.0
git push origin --delete sys/firebase-workbench
git push origin --delete sys/github-factory
git push origin --delete sys/security-audit
git push origin --delete sys/windmill
git push origin --delete gitingest
git push origin --delete claude/pull-repository-0174f72zxJqC6hz3SSgz7LeL
```

---

## 4. Files Marked for Deletion

### 4.1 Legacy Directories (ARCHIVE)

| Directory | Justification | Action |
|-----------|---------------|--------|
| `HEIR-AGENT-SYSTEM/` | Replaced by MCP-based garage-bay | ARCHIVE |
| `enrichment-hub/` | Parallel implementation, superseded | ARCHIVE |
| `outreach_core/` | Incomplete stub, no PRD reference | ARCHIVE |
| `ctb/sys/activepieces/` | No PRD reference | DELETE |
| `ctb/sys/bigquery-warehouse/` | No PRD reference | DELETE |
| `ctb/sys/builder-bridge/` | No PRD reference | DELETE |
| `ctb/sys/chartdb/` | No PRD reference | DELETE |
| `ctb/sys/deepwiki/` | No PRD reference | DELETE |
| `ctb/sys/firebase-workbench/` | No PRD reference, legacy | DELETE |
| `ctb/sys/github-factory/` | No PRD reference | DELETE |
| `ctb/sys/global-factory/` | Empty, no PRD reference | DELETE |
| `ctb/sys/mechanic/` | No PRD reference | DELETE |
| `ctb/sys/security-audit/` | No PRD reference | DELETE |
| `ctb/sys/cli/` | Legacy CLI, not in PRD | DELETE |
| `ctb/sys/factory/` | Legacy factory, not in PRD | DELETE |
| `ctb/sys/firebase/` | Duplicate of firebase-workbench | DELETE |
| `ctb/sys/deployment/` | Legacy deployment scripts | DELETE |

### 4.2 Duplicate/Legacy Files

| File | Justification | Action |
|------|---------------|--------|
| `ctb/sys/enrichment/enrichment_waterfall.py` | Superseded by pipeline_engine phases | ARCHIVE |
| `ctb/sys/enrichment/stage2_enrichment_pipeline.py` | Superseded by phase system | ARCHIVE |
| `ctb/sys/enrichment/stage2_firecrawl_pipeline.py` | Superseded by phase system | ARCHIVE |
| `ctb/sys/enrichment/stage3_company_vessels_initializer.py` | Superseded | ARCHIVE |
| `ctb/sys/enrichment/stage4_people_hub_initializer.py` | Superseded | ARCHIVE |
| `ctb/sys/enrichment/stage5_*` | Superseded by phase system | ARCHIVE |
| `ctb/sys/enrichment/stage6a_*` | Superseded by phase system | ARCHIVE |
| Multiple `create_*.js` files in enrichment/ | JavaScript superseded by Python | DELETE |
| Multiple `test_*.js` files in enrichment/ | Legacy tests | DELETE |
| `ctb/meta/vercel.json` | Not used | DELETE |

### 4.3 Root-Level Cleanup

| File | Justification | Action |
|------|---------------|--------|
| `setup_claude_global.py` | One-time setup, archive | ARCHIVE |
| `setup_codex_global.py` | One-time setup, archive | ARCHIVE |
| `setup_gemini_global.py` | One-time setup, archive | ARCHIVE |
| `setup_obsidian*.py` | One-time setup, archive | ARCHIVE |
| `sync_neon_to_supabase.py` | Migration utility, archive | ARCHIVE |
| `sync_supabase_to_neon.py` | Migration utility, archive | ARCHIVE |
| `test_claude.py` | One-time test, archive | ARCHIVE |
| `test_codex.py` | One-time test, archive | ARCHIVE |
| `test_gemini.py` | One-time test, archive | ARCHIVE |
| `nul` | Empty/error file | DELETE |

---

## 5. Migration Execution Plan

### Phase 1: Archive Legacy Code (Day 1)

```bash
# Create archive directory
mkdir -p .archive

# Move legacy directories
mv HEIR-AGENT-SYSTEM .archive/
mv enrichment-hub .archive/
mv outreach_core .archive/

# Move legacy ctb/sys directories
mv ctb/sys/activepieces .archive/legacy_ctb_sys/
mv ctb/sys/bigquery-warehouse .archive/legacy_ctb_sys/
mv ctb/sys/builder-bridge .archive/legacy_ctb_sys/
mv ctb/sys/chartdb .archive/legacy_ctb_sys/
mv ctb/sys/deepwiki .archive/legacy_ctb_sys/
mv ctb/sys/firebase-workbench .archive/legacy_ctb_sys/
mv ctb/sys/github-factory .archive/legacy_ctb_sys/
mv ctb/sys/global-factory .archive/legacy_ctb_sys/
mv ctb/sys/mechanic .archive/legacy_ctb_sys/
mv ctb/sys/security-audit .archive/legacy_ctb_sys/
mv ctb/sys/cli .archive/legacy_ctb_sys/
mv ctb/sys/factory .archive/legacy_ctb_sys/
mv ctb/sys/firebase .archive/legacy_ctb_sys/
mv ctb/sys/deployment .archive/legacy_ctb_sys/
```

### Phase 2: Create Hub-Spoke Structure (Day 2)

```bash
# Create hub structure
mkdir -p hub/company/{phases,email,movement_engine,utils}

# Create spoke structures
mkdir -p spokes/people/{phases,sub_wheels/email_verification}
mkdir -p spokes/dol/importers
mkdir -p spokes/blog_news
mkdir -p spokes/talent_flow
mkdir -p spokes/outreach

# Create ops structure
mkdir -p ops/{master_error_log/migrations,phase_registry,validation,providers,reporting}
```

### Phase 3: Move Code to New Structure (Day 3-4)

```bash
# Move Company Hub code
cp ctb/sys/enrichment/pipeline_engine/hub/company_hub.py hub/company/
cp ctb/sys/enrichment/pipeline_engine/hub/bit_engine.py hub/company/
cp ctb/sys/enrichment/pipeline_engine/phases/phase1*.py hub/company/phases/
cp ctb/sys/enrichment/pipeline_engine/phases/phase2*.py hub/company/phases/
cp ctb/sys/enrichment/pipeline_engine/phases/phase3*.py hub/company/phases/
cp ctb/sys/enrichment/pipeline_engine/phases/phase4*.py hub/company/phases/
# ... continue for all mappings
```

### Phase 4: Update Imports (Day 5)

Update all import statements in moved files to reflect new paths:

```python
# Old
from ctb.sys.enrichment.pipeline_engine.hub.company_hub import CompanyHub

# New
from hub.company.company_hub import CompanyHub
```

### Phase 5: Delete Obsolete Branches (Day 6)

Execute branch cleanup commands from Section 3.3.

### Phase 6: Verify and Test (Day 7)

1. Run all tests
2. Verify imports resolve
3. Validate PRD compliance
4. Update CLAUDE.md with new structure

---

## 6. PRD Compliance Checklist

After refactor, verify:

- [ ] Every file in `hub/company/` is referenced by PRD_COMPANY_HUB.md or PRD_COMPANY_HUB_PIPELINE.md
- [ ] Every file in `spokes/people/` is referenced by PRD_PEOPLE_SUBHUB.md
- [ ] Every file in `spokes/dol/` is referenced by PRD_DOL_SUBHUB.md
- [ ] Every file in `ops/master_error_log/` is referenced by PRD_MASTER_ERROR_LOG.md
- [ ] No orphan code exists (code without PRD reference)
- [ ] All branch names follow pattern: `{type}/{hub-or-spoke}-{feature}`

---

## 7. Summary Statistics

| Metric | Before | After |
|--------|--------|-------|
| Top-level directories | 20+ | 8 |
| Legacy directories | 17 | 0 (archived) |
| Branches | 50 | 18 |
| Files without PRD reference | ~100+ | 0 |
| Hub/Spoke clarity | Low | High |

---

## 8. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Import breakage | HIGH | Update imports systematically, test each phase |
| Lost functionality | MEDIUM | Archive rather than delete, review before purge |
| CI/CD breakage | MEDIUM | Update workflows in Phase 5 |
| Team confusion | LOW | Document changes in CLAUDE.md |

---

## 9. Approval Required

Before execution:

- [ ] Review by repository owner
- [ ] Confirm archive vs delete decisions
- [ ] Validate branch ownership for `sys/claude-skills`, `sys/outreach-tools-backend`
- [ ] Confirm feature branches can be squashed

---

*Document Version: 1.0*
*Created: 2025-12-17*
*Status: AWAITING APPROVAL*
