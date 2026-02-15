# ERD Drift - Action Checklist

**Date**: 2026-02-02
**Priority**: HIGH
**Assigned**: Architecture Team

## Immediate Actions (48 Hours)

### Priority 1: Critical v1.0 Compliance Issues

- [ ] **Update `cl.company_identity` ERD** (hubs/company-target/SCHEMA.md)
  - [ ] Add `sovereign_company_id` (PRIMARY KEY)
  - [ ] Add `outreach_id` (WRITE-ONCE claim)
  - [ ] Add `sales_process_id` (WRITE-ONCE claim)
  - [ ] Add `client_id` (WRITE-ONCE claim)
  - [ ] Add `canonical_name`
  - [ ] Add `eligibility_status`
  - [ ] Add `lifecycle_run_id`
  - [ ] Add `identity_pass`
  - [ ] Add remaining 18+ columns
  - [ ] Update timestamp fields to `timestamptz`

- [ ] **Document Kill Switch System** (hubs/outreach-execution/SCHEMA.md)
  - [ ] Add `outreach.manual_overrides` table
  - [ ] Add `outreach.override_audit_log` table
  - [ ] Document override types and enforcement
  - [ ] Link to DO_NOT_MODIFY_REGISTRY.md

- [ ] **Document Hub Registry** (hubs/outreach-execution/SCHEMA.md)
  - [ ] Add `outreach.hub_registry` table
  - [ ] Document hub registration workflow
  - [ ] Link to waterfall execution order

### Priority 2: Remove Stale References

- [ ] **Remove/Mark Deprecated Tables**
  - [ ] `bit.bit_company_score` (replaced by?)
  - [ ] `bit.bit_contact_score` (replaced by?)
  - [ ] `bit.bit_signal` (replaced by?)
  - [ ] `blog.pressure_signals` (schema mismatch)
  - [ ] `company.target_vw_all_pressure_signals` (view missing?)
  - [ ] `marketing.company_master` (legacy dropped?)
  - [ ] `marketing.people_master` (legacy dropped?)
  - [ ] `outreach.ctx_context` (deprecated?)
  - [ ] `outreach.ctx_spend_log` (deprecated?)
  - [ ] `talent.flow_movement_history` (schema mismatch)

## Short-Term Actions (2 Weeks)

### Priority 3: Archive Tables Documentation

- [ ] **CL Archive Tables** (hubs/company-target/SCHEMA.md)
  - [ ] `cl.company_domains_archive`
  - [ ] `cl.company_identity_archive`
  - [ ] `cl.company_names_archive`
  - [ ] `cl.domain_hierarchy_archive`
  - [ ] `cl.identity_confidence_archive`

- [ ] **Outreach Archive Tables** (respective SCHEMA.md files)
  - [ ] `outreach.bit_scores_archive`
  - [ ] `outreach.blog_archive`
  - [ ] `outreach.company_target_archive`
  - [ ] `outreach.dol_archive`
  - [ ] `outreach.outreach_archive`
  - [ ] `outreach.people_archive`
  - [ ] `outreach.outreach_orphan_archive`

- [ ] **People Archive Tables** (hubs/people-intelligence/SCHEMA.md)
  - [ ] `people.company_slot_archive`
  - [ ] `people.people_master_archive`

### Priority 4: Error Tables Standardization

Create standard error table template and apply to:

- [ ] **Outreach Error Tables** (respective SCHEMA.md files)
  - [ ] `outreach.bit_errors`
  - [ ] `outreach.blog_errors`
  - [ ] `outreach.company_target_errors`
  - [ ] `outreach.dol_errors`
  - [ ] `outreach.people_errors`
  - [ ] `outreach.outreach_errors`

- [ ] **People Error Tables** (hubs/people-intelligence/SCHEMA.md)
  - [ ] `people.people_errors`

- [ ] **Company Error Tables** (hubs/company-target/SCHEMA.md)
  - [ ] `company.pipeline_errors`
  - [ ] `company.validation_failures_log`

- [ ] **CL Error Tables** (hubs/company-target/SCHEMA.md)
  - [ ] `cl.cl_err_existence`
  - [ ] `cl.cl_errors_archive`

### Priority 5: Exclusion Tables Documentation

- [ ] **CL Exclusion Pattern** (hubs/company-target/SCHEMA.md)
  - [ ] `cl.company_domains_excluded`
  - [ ] `cl.company_identity_excluded`
  - [ ] `cl.company_names_excluded`
  - [ ] `cl.identity_confidence_excluded`
  - [ ] Document exclusion criteria
  - [ ] Link to marketing safety gates

- [ ] **Outreach Exclusion** (hubs/outreach-execution/SCHEMA.md)
  - [ ] `outreach.outreach_excluded`
  - [ ] `outreach.outreach_legacy_quarantine`

### Priority 6: DOL Tables Complete Documentation

- [ ] **DOL Form 5500** (hubs/dol-filings/SCHEMA.md)
  - [ ] Add all 100+ sponsor fields
  - [ ] Add all administrator fields
  - [ ] Add all preparer fields
  - [ ] Add all plan metadata fields
  - [ ] Add signature validation fields

- [ ] **DOL Form 5500-SF** (hubs/dol-filings/SCHEMA.md)
  - [ ] Add all 200+ short form fields
  - [ ] Document SF-specific requirements

- [ ] **DOL Supporting Tables** (hubs/dol-filings/SCHEMA.md)
  - [ ] `dol.ein_urls` (currently missing from ERD)
  - [ ] `dol.form_5500_icp_filtered` (currently missing from ERD)

### Priority 7: People Hub Gaps

- [ ] **Enrichment Pipeline** (hubs/people-intelligence/SCHEMA.md)
  - [ ] `people.paid_enrichment_queue`
  - [ ] Document enrichment workflow

- [ ] **Resolution Pipeline** (hubs/people-intelligence/SCHEMA.md)
  - [ ] `people.company_resolution_log`
  - [ ] `people.people_resolution_history`
  - [ ] `people.people_resolution_queue`

- [ ] **Staging and Validation** (hubs/people-intelligence/SCHEMA.md)
  - [ ] `people.people_staging`
  - [ ] `people.people_invalid`
  - [ ] `people.title_slot_mapping`

- [ ] **Quarantine Tables** (hubs/people-intelligence/SCHEMA.md)
  - [ ] `people.slot_orphan_snapshot_r0_002`
  - [ ] `people.slot_quarantine_r0_002`

- [ ] **Audit and Scoring** (hubs/people-intelligence/SCHEMA.md)
  - [ ] `people.people_promotion_audit`
  - [ ] `people.person_scores`

### Priority 8: Blog Content Hub

- [ ] **Blog Tables** (hubs/blog-content/SCHEMA.md)
  - [ ] `outreach.blog` (currently undocumented)
  - [ ] `outreach.blog_ingress_control`
  - [ ] `outreach.blog_source_history`
  - [ ] Update `company.company_source_urls` with 12 missing columns

### Priority 9: Company Target Hub Gaps

- [ ] **Company Tables** (hubs/company-target/SCHEMA.md)
  - [ ] Add 23 missing columns to `company.company_master`
  - [ ] Fix `company.company_sidecar` (6 columns documented but don't exist)
  - [ ] Fix `company.company_slots` (5 columns documented but don't exist)
  - [ ] Fix `company.contact_enrichment` (5 columns documented but don't exist)
  - [ ] Fix `company.email_verification` (6 columns documented but don't exist)

- [ ] **Company Operational** (hubs/company-target/SCHEMA.md)
  - [ ] `company.company_events`
  - [ ] `company.message_key_reference`
  - [ ] `company.pipeline_events`

### Priority 10: BIT Scoring Hub

- [ ] **BIT Tables** (hubs/company-target/SCHEMA.md or create separate BIT SCHEMA.md)
  - [ ] `bit.authorization_log`
  - [ ] `bit.movement_events`
  - [ ] `bit.phase_state`
  - [ ] `bit.proof_lines`

### Priority 11: CL Supporting Tables

- [ ] **CL Identity Resolution** (hubs/company-target/SCHEMA.md)
  - [ ] `cl.company_candidate`
  - [ ] `cl.company_identity_bridge`
  - [ ] `cl.company_names` (name variants)
  - [ ] `cl.domain_hierarchy`
  - [ ] `cl.identity_confidence`

### Priority 12: Outreach Operational Tables

- [ ] **Outreach Control** (hubs/outreach-execution/SCHEMA.md)
  - [ ] `outreach.column_registry`
  - [ ] `outreach.entity_resolution_queue`
  - [ ] `outreach.pipeline_audit_log`

- [ ] **Outreach BIT Integration** (hubs/outreach-execution/SCHEMA.md)
  - [ ] `outreach.bit_input_history`

- [ ] **Outreach DOL Integration** (hubs/dol-filings/SCHEMA.md)
  - [ ] `outreach.dol_url_enrichment`

- [ ] **Outreach Metrics** (hubs/outreach-execution/SCHEMA.md)
  - [ ] `outreach.mv_credit_usage`

### Priority 13: Fix Data Type Mismatches

- [ ] **Timestamp Standardization**
  - [ ] `cl.company_domains.checked_at` (timestamp → timestamptz)
  - [ ] `cl.company_identity.created_at` (timestamp → timestamptz)
  - [ ] `outreach.outreach.created_at` (timestamp → timestamptz)
  - [ ] `outreach.people.email_verified_at` (timestamp → timestamptz)
  - [ ] `outreach.people.last_event_ts` (timestamp → timestamptz)
  - [ ] `outreach.bit_scores.last_signal_at` (timestamp → timestamptz)
  - [ ] `outreach.bit_scores.last_scored_at` (timestamp → timestamptz)
  - [ ] `people.company_slot.filled_at` (timestamp → timestamptz)

- [ ] **Enum Type Documentation**
  - [ ] `outreach.people.lifecycle_state` (enum → USER-DEFINED)
  - [ ] `outreach.people.funnel_membership` (enum → USER-DEFINED)
  - [ ] Document enum values for each

### Priority 14: Fix Column Mismatches in Existing Tables

Tables with correct name but wrong columns:

- [ ] **Company Target** (hubs/people-intelligence/SCHEMA.md)
  - [ ] Add 13 missing columns to `outreach.company_target`

- [ ] **Outreach Spine** (hubs/talent-flow/SCHEMA.md)
  - [ ] Add `updated_at` to `outreach.outreach`

- [ ] **People Master** (hubs/talent-flow/SCHEMA.md)
  - [ ] Add 23 missing columns to `people.people_master`

- [ ] **People Operational** (hubs/people-intelligence/SCHEMA.md)
  - [ ] Add 4 missing columns to `outreach.people`
  - [ ] Add 2 missing columns to `people.company_slot`

- [ ] **BIT Scores** (hubs/outreach-execution/SCHEMA.md)
  - [ ] Add `created_at` and `updated_at` to `outreach.bit_scores`

- [ ] **DOL Operational** (hubs/dol-filings/SCHEMA.md)
  - [ ] Add `created_at` and `updated_at` to `outreach.dol`

## Long-Term Actions (1 Month)

### Priority 15: Missing Views Documentation

- [ ] **Verify and Document Views**
  - [ ] `cl.v_company_lifecycle_status` (documented in CLAUDE.md)
  - [ ] `outreach.vw_marketing_eligibility_with_overrides` (v1.0 FROZEN)
  - [ ] `outreach.vw_sovereign_completion` (v1.0 FROZEN)
  - [ ] `company_target.vw_all_pressure_signals` (BIT v2.0)
  - [ ] `company_target.vw_company_authorization` (BIT v2.0)

### Priority 16: Schema Governance

- [ ] **Process Improvements**
  - [ ] Add ERD update requirement to PR template
  - [ ] Add schema drift checker to CI/CD
  - [ ] Create weekly drift report automation
  - [ ] Document schema change ADR requirement

- [ ] **Tooling**
  - [ ] Version control `neon_schema_snapshot.json`
  - [ ] Create schema diff report for PRs
  - [ ] Automate Mermaid ERD generation from Neon

### Priority 17: Cross-Reference Documentation

- [ ] **Create Reference Guides**
  - [ ] Map spoke contracts to actual tables
  - [ ] Document all FK relationships
  - [ ] Create data flow diagrams
  - [ ] Document RLS policies per table

## Tracking

**Progress**: 0 / 17 priorities
**Completion Target**: 2026-03-02 (1 month)

### Completed

- [ ] P1: Critical v1.0 Compliance
- [ ] P2: Stale References
- [ ] P3: Archive Tables
- [ ] P4: Error Tables
- [ ] P5: Exclusion Tables
- [ ] P6: DOL Complete
- [ ] P7: People Hub
- [ ] P8: Blog Content
- [ ] P9: Company Target
- [ ] P10: BIT Scoring
- [ ] P11: CL Supporting
- [ ] P12: Outreach Operational
- [ ] P13: Data Types
- [ ] P14: Column Mismatches
- [ ] P15: Views
- [ ] P16: Governance
- [ ] P17: Cross-Reference

---

**Created**: 2026-02-02
**Owner**: Architecture Team
**Reviewer**: Database Lead
**Status**: ACTIVE
