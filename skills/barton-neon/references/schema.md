# barton-outreach-core -- Neon Schema Reference

Source: `archive/data-files/neon_schema_snapshot.json`

---

## outreach (39 tables)

The largest schema. Serves as the canonical egress layer and contains cross-domain
summary tables, campaign execution, and governance registries.

| Table | Purpose |
|-------|---------|
| `bit_errors` | BIT scoring error log |
| `bit_input_history` | BIT score input audit trail |
| `bit_scores` | Current BIT scores |
| `bit_scores_archive` | Historical BIT scores |
| `bit_signals` | BIT signal data |
| `blog` | Blog content (canonical) |
| `blog_archive` | Blog content history |
| `blog_errors` | Blog pipeline errors |
| `blog_ingress_control` | Blog ingestion gating |
| `blog_source_history` | Blog source tracking |
| `campaigns` | Outreach campaign definitions |
| `column_registry` | Doctrine column registry |
| `company_hub_status` | Company processing status across hubs |
| `company_target` | Target companies (canonical) |
| `company_target_archive` | Target company history |
| `company_target_errors` | Company target pipeline errors |
| `dol` | DOL summary (egress mirror) |
| `dol_archive` | DOL summary history |
| `dol_audit_log` | DOL mutation audit trail |
| `dol_errors` | DOL pipeline errors |
| `dol_url_enrichment` | DOL URL enrichment tracking |
| `engagement_events` | Outreach engagement tracking |
| `entity_resolution_queue` | Cross-entity resolution queue |
| `hub_registry` | Sub-hub registry (doctrine) |
| `manual_overrides` | Manual data overrides |
| `mv_credit_usage` | Enrichment credit usage tracking |
| `outreach` | Outreach records (canonical) |
| `outreach_archive` | Outreach history |
| `outreach_errors` | Outreach pipeline errors |
| `outreach_excluded` | Excluded outreach records |
| `outreach_legacy_quarantine` | Legacy data quarantine |
| `outreach_orphan_archive` | Orphaned outreach records |
| `override_audit_log` | Override mutation audit trail |
| `people` | People summary (egress mirror) |
| `people_archive` | People summary history |
| `people_errors` | People pipeline errors |
| `pipeline_audit_log` | Pipeline execution audit trail |
| `send_log` | Email/message send log |
| `sequences` | Outreach sequence definitions |

---

## people (22 tables)

People enrichment, staging, resolution, and slot assignment.

| Table | Purpose |
|-------|---------|
| `company_resolution_log` | Company-to-person resolution audit |
| `company_slot` | Company slot assignments (current) |
| `company_slot_archive` | Company slot history |
| `paid_enrichment_queue` | Queue for paid enrichment (Hunter, etc.) |
| `people_candidate` | People candidates (pre-promotion) |
| `people_errors` | People pipeline errors |
| `people_invalid` | Invalid people records |
| `people_master` | People master records (canonical) |
| `people_master_archive` | People master history |
| `people_promotion_audit` | Candidate-to-master promotion audit |
| `people_resolution_history` | Entity resolution history |
| `people_resolution_queue` | Entity resolution queue |
| `people_sidecar` | People sidecar (enrichment metadata) |
| `people_staging` | People ingress staging |
| `person_movement_history` | Job change / movement tracking |
| `person_scores` | Person-level scores |
| `pressure_signals` | People pressure signals |
| `slot_assignment_history` | Slot assignment audit trail |
| `slot_ingress_control` | Slot ingestion gating |
| `slot_orphan_snapshot_r0_002` | Orphan slot snapshot (repair batch) |
| `slot_quarantine_r0_002` | Quarantined slots (repair batch) |
| `title_slot_mapping` | Title-to-slot mapping rules |

---

## company (12 tables)

Company master data, enrichment, and pipeline governance.

| Table | Purpose |
|-------|---------|
| `company_events` | Company lifecycle events |
| `company_master` | Company master records (canonical) |
| `company_sidecar` | Company sidecar (enrichment metadata) |
| `company_slots` | Company slot definitions |
| `company_source_urls` | Source URLs for company data |
| `contact_enrichment` | Contact enrichment results |
| `email_verification` | Email verification results |
| `message_key_reference` | Message key lookup |
| `pipeline_errors` | Company pipeline errors |
| `pipeline_events` | Company pipeline events |
| `url_discovery_failures` | Failed URL discovery attempts |
| `validation_failures_log` | Validation failure audit |

---

## cl (18 tables)

Company-lifecycle identity resolution. Cross-hub schema for entity deduplication
and confidence scoring.

| Table | Purpose |
|-------|---------|
| `cl_err_existence` | CL existence error log |
| `cl_errors_archive` | CL error history |
| `company_candidate` | Company identity candidates |
| `company_domains` | Company domain mappings (current) |
| `company_domains_archive` | Domain mapping history |
| `company_domains_excluded` | Excluded domain mappings |
| `company_identity` | Resolved company identities (canonical) |
| `company_identity_archive` | Identity history |
| `company_identity_bridge` | Identity bridge (cross-reference) |
| `company_identity_excluded` | Excluded identities |
| `company_names` | Company name variants (current) |
| `company_names_archive` | Name variant history |
| `company_names_excluded` | Excluded name variants |
| `domain_hierarchy` | Domain parent-child hierarchy |
| `domain_hierarchy_archive` | Domain hierarchy history |
| `identity_confidence` | Identity confidence scores (current) |
| `identity_confidence_archive` | Confidence score history |
| `identity_confidence_excluded` | Excluded confidence records |

---

## dol (8 tables)

Department of Labor Form 5500 filings and derived signals.

| Table | Purpose |
|-------|---------|
| `column_metadata` | DOL column metadata |
| `ein_urls` | EIN-to-URL mappings |
| `form_5500` | Raw Form 5500 filings |
| `form_5500_icp_filtered` | ICP-filtered Form 5500 subset |
| `form_5500_sf` | Form 5500 (Salesforce format) |
| `pressure_signals` | DOL-derived pressure signals |
| `renewal_calendar` | Plan renewal calendar |
| `schedule_a` | Schedule A filings |

---

## bit (6 tables)

Governance and authorization tracking (BIT = Barton Intelligence Tracker).

| Table | Purpose |
|-------|---------|
| `authorization_log` | Authorization event log |
| `movement_events` | Movement event tracking |
| `phase_state` | Pipeline phase state machine |
| `proof_lines` | Proof line audit trail |
