# COMPLETE COLUMN REGISTRY

> **Source**: Neon PostgreSQL + dol.column_metadata + outreach.column_registry + enrichment.column_registry + column_registry.yml + pattern inference
> **Generated**: 2026-02-20
> **Scope**: All non-archive tables (archive tables mirror source table schemas)
> **Regenerate**: `doppler run -- python scripts/build_column_registry.py`

**Every column has**: `column_unique_id` | `description` | `semantic_role` | `format`

---

## `CL` CL Authority Registry (PARENT)

**Tables**: 20 | **Total rows**: 625,804

### `cl.cl_err_existence` -- ERROR -- 9,328 rows

**Hub**: `CL` CL Authority Registry

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `error_id` | `cl.cl_err_existence.error_id` | uuid | N | Primary key for this error record | identifier | UUID | inferred |
| 2 | `company_unique_id` | `cl.cl_err_existence.company_unique_id` | uuid | N | FK to cl.company_identity or Barton company ID | foreign_key | UUID | inferred |
| 3 | `company_name` | `cl.cl_err_existence.company_name` | text | Y | Company legal or common name | attribute | STRING | inferred |
| 4 | `company_domain` | `cl.cl_err_existence.company_domain` | text | Y | Company Domain | attribute | STRING | inferred |
| 5 | `linkedin_company_url` | `cl.cl_err_existence.linkedin_company_url` | text | Y | LinkedIn company page URL | attribute | URL | inferred |
| 6 | `reason_code` | `cl.cl_err_existence.reason_code` | text | N | Reason Code | attribute | STRING | inferred |
| 7 | `domain_status_code` | `cl.cl_err_existence.domain_status_code` | integer | Y | Domain Status Code | attribute | INTEGER | inferred |
| 8 | `domain_redirect_chain` | `cl.cl_err_existence.domain_redirect_chain` | ARRAY | Y | Domain Redirect Chain | attribute | ARRAY | inferred |
| 9 | `domain_final_url` | `cl.cl_err_existence.domain_final_url` | text | Y | Domain Final URL | attribute | URL | inferred |
| 10 | `domain_error` | `cl.cl_err_existence.domain_error` | text | Y | Domain Error | attribute | STRING | inferred |
| 11 | `extracted_name` | `cl.cl_err_existence.extracted_name` | text | Y | Extracted Name | attribute | STRING | inferred |
| 12 | `name_match_score` | `cl.cl_err_existence.name_match_score` | integer | Y | Name Match score | metric | INTEGER | inferred |
| 13 | `extracted_state` | `cl.cl_err_existence.extracted_state` | text | Y | Extracted State | attribute | STRING | inferred |
| 14 | `state_match_result` | `cl.cl_err_existence.state_match_result` | text | Y | State Match Result | attribute | STRING | inferred |
| 15 | `evidence` | `cl.cl_err_existence.evidence` | jsonb | Y | Evidence | attribute | JSONB | inferred |
| 16 | `verification_run_id` | `cl.cl_err_existence.verification_run_id` | text | N | Run identifier for verification batch | identifier | STRING | inferred |
| 17 | `created_at` | `cl.cl_err_existence.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 18 | `error_type` | `cl.cl_err_existence.error_type` | character varying(100) | Y | Discriminator column classifying the error type | attribute | ENUM | inferred |

### `cl.cl_errors_archive` -- ERROR -- 16,103 rows

**Hub**: `CL` CL Authority Registry

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `error_id` | `cl.cl_errors_archive.error_id` | uuid | N | Primary key for this error record | identifier | UUID | inferred |
| 2 | `company_unique_id` | `cl.cl_errors_archive.company_unique_id` | uuid | Y | FK to cl.company_identity or Barton company ID | foreign_key | UUID | inferred |
| 3 | `lifecycle_run_id` | `cl.cl_errors_archive.lifecycle_run_id` | text | N | Run identifier for lifecycle batch | identifier | STRING | inferred |
| 4 | `pass_name` | `cl.cl_errors_archive.pass_name` | text | N | Pass Name | attribute | STRING | inferred |
| 5 | `failure_reason_code` | `cl.cl_errors_archive.failure_reason_code` | text | N | Failure Reason Code | attribute | STRING | inferred |
| 6 | `inputs_snapshot` | `cl.cl_errors_archive.inputs_snapshot` | jsonb | Y | Inputs Snapshot | attribute | JSONB | inferred |
| 7 | `created_at` | `cl.cl_errors_archive.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 8 | `resolved_at` | `cl.cl_errors_archive.resolved_at` | timestamp with time zone | Y | When this error/issue was resolved | attribute | ISO-8601 | inferred |
| 9 | `retry_count` | `cl.cl_errors_archive.retry_count` | integer | Y | Number of retry attempts so far | metric | INTEGER | inferred |
| 10 | `retry_ceiling` | `cl.cl_errors_archive.retry_ceiling` | integer | Y | Maximum number of retries allowed | attribute | INTEGER | inferred |
| 11 | `retry_after` | `cl.cl_errors_archive.retry_after` | timestamp with time zone | Y | Earliest time to retry | attribute | ISO-8601 | inferred |
| 12 | `tool_used` | `cl.cl_errors_archive.tool_used` | text | Y | Tool Used | attribute | STRING | inferred |
| 13 | `tool_tier` | `cl.cl_errors_archive.tool_tier` | integer | Y | Tool Tier | attribute | INTEGER | inferred |
| 14 | `expires_at` | `cl.cl_errors_archive.expires_at` | timestamp with time zone | Y | When this record expires | attribute | ISO-8601 | inferred |
| 15 | `archived_at` | `cl.cl_errors_archive.archived_at` | timestamp with time zone | Y | When this record was archived | attribute | ISO-8601 | inferred |
| 16 | `archive_reason` | `cl.cl_errors_archive.archive_reason` | text | Y | Reason this record was archived | attribute | STRING | inferred |
| 17 | `final_outcome` | `cl.cl_errors_archive.final_outcome` | text | Y | Final outcome after processing | attribute | STRING | inferred |
| 18 | `final_reason` | `cl.cl_errors_archive.final_reason` | text | Y | Reason for final outcome | attribute | STRING | inferred |
| 19 | `error_type` | `cl.cl_errors_archive.error_type` | character varying(100) | N | Discriminator column classifying the error type | attribute | ENUM | inferred |

### `cl.company_candidate` -- STAGING -- 76,215 rows

**Hub**: `CL` CL Authority Registry

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `candidate_id` | `cl.company_candidate.candidate_id` | uuid | N | Primary key for this candidate record | identifier | UUID | inferred |
| 2 | `source_system` | `cl.company_candidate.source_system` | text | N | System that originated this record | attribute | STRING | inferred |
| 3 | `source_record_id` | `cl.company_candidate.source_record_id` | text | N | Source Record Id | identifier | STRING | inferred |
| 4 | `state_code` | `cl.company_candidate.state_code` | character(2) | N | US state code (2-letter) | attribute | STRING | inferred |
| 5 | `raw_payload` | `cl.company_candidate.raw_payload` | jsonb | N | Raw Payload | attribute | JSONB | inferred |
| 6 | `ingestion_run_id` | `cl.company_candidate.ingestion_run_id` | text | Y | Run identifier for ingestion batch | identifier | STRING | inferred |
| 7 | `verification_status` | `cl.company_candidate.verification_status` | text | N | Current verification status | attribute | ENUM | inferred |
| 8 | `verification_error` | `cl.company_candidate.verification_error` | text | Y | Error message from verification attempt | attribute | STRING | inferred |
| 9 | `verified_at` | `cl.company_candidate.verified_at` | timestamp with time zone | Y | When verification was completed | attribute | ISO-8601 | inferred |
| 10 | `company_unique_id` | `cl.company_candidate.company_unique_id` | uuid | Y | FK to cl.company_identity or Barton company ID | foreign_key | UUID | inferred |
| 11 | `created_at` | `cl.company_candidate.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |

### `cl.company_domains` -- CANONICAL -- 46,583 rows

**Hub**: `CL` CL Authority Registry

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `domain_id` | `cl.company_domains.domain_id` | uuid | N | Primary key for this domain record | identifier | UUID | inferred |
| 2 | `company_unique_id` | `cl.company_domains.company_unique_id` | uuid | N | FK to cl.company_identity or Barton company ID | foreign_key | UUID | inferred |
| 3 | `domain` | `cl.company_domains.domain` | text | N | Company website domain (lowercase, no protocol) | attribute | STRING | inferred |
| 4 | `domain_health` | `cl.company_domains.domain_health` | text | Y | Domain Health | attribute | ENUM | inferred |
| 5 | `mx_present` | `cl.company_domains.mx_present` | boolean | Y | MX record status | attribute | BOOLEAN | inferred |
| 6 | `domain_name_confidence` | `cl.company_domains.domain_name_confidence` | integer | Y | Domain Name Confidence | metric | INTEGER | inferred |
| 7 | `checked_at` | `cl.company_domains.checked_at` | timestamp with time zone | Y | When this record was last checked/verified | attribute | ISO-8601 | inferred |

### `cl.company_domains_archive` -- ARCHIVE -- 18,328 rows

**Hub**: `CL` CL Authority Registry

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `domain_id` | `cl.company_domains_archive.domain_id` | uuid | N | Primary key for this domain record | identifier | UUID | inferred |
| 2 | `company_unique_id` | `cl.company_domains_archive.company_unique_id` | uuid | N | FK to cl.company_identity or Barton company ID | foreign_key | UUID | inferred |
| 3 | `domain` | `cl.company_domains_archive.domain` | text | N | Company website domain (lowercase, no protocol) | attribute | STRING | inferred |
| 4 | `domain_health` | `cl.company_domains_archive.domain_health` | text | Y | Domain Health | attribute | ENUM | inferred |
| 5 | `mx_present` | `cl.company_domains_archive.mx_present` | boolean | Y | MX record status | attribute | BOOLEAN | inferred |
| 6 | `domain_name_confidence` | `cl.company_domains_archive.domain_name_confidence` | integer | Y | Domain Name Confidence | metric | INTEGER | inferred |
| 7 | `checked_at` | `cl.company_domains_archive.checked_at` | timestamp with time zone | Y | When this record was last checked/verified | attribute | ISO-8601 | inferred |
| 8 | `archived_at` | `cl.company_domains_archive.archived_at` | timestamp with time zone | Y | When this record was archived | attribute | ISO-8601 | inferred |
| 9 | `archive_reason` | `cl.company_domains_archive.archive_reason` | text | Y | Reason this record was archived | attribute | STRING | inferred |

### `cl.company_domains_excluded` -- CANONICAL -- 5,327 rows

**Hub**: `CL` CL Authority Registry

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `domain_id` | `cl.company_domains_excluded.domain_id` | uuid | N | Primary key for this domain record | identifier | UUID | inferred |
| 2 | `company_unique_id` | `cl.company_domains_excluded.company_unique_id` | uuid | N | FK to cl.company_identity or Barton company ID | foreign_key | UUID | inferred |
| 3 | `domain` | `cl.company_domains_excluded.domain` | text | N | Company website domain (lowercase, no protocol) | attribute | STRING | inferred |
| 4 | `domain_health` | `cl.company_domains_excluded.domain_health` | text | Y | Domain Health | attribute | ENUM | inferred |
| 5 | `mx_present` | `cl.company_domains_excluded.mx_present` | boolean | Y | MX record status | attribute | BOOLEAN | inferred |
| 6 | `domain_name_confidence` | `cl.company_domains_excluded.domain_name_confidence` | integer | Y | Domain Name Confidence | metric | INTEGER | inferred |
| 7 | `checked_at` | `cl.company_domains_excluded.checked_at` | timestamp with time zone | Y | When this record was last checked/verified | attribute | ISO-8601 | inferred |

### `cl.company_identity` -- CANONICAL FROZEN -- 117,151 rows

**Hub**: `CL` CL Authority Registry

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `company_unique_id` | `cl.company_identity.company_unique_id` | uuid | N | FK to cl.company_identity or Barton company ID | foreign_key | UUID | inferred |
| 2 | `company_name` | `cl.company_identity.company_name` | text | N | Company legal or common name | attribute | STRING | inferred |
| 3 | `company_domain` | `cl.company_identity.company_domain` | text | Y | Company Domain | attribute | STRING | inferred |
| 4 | `linkedin_company_url` | `cl.company_identity.linkedin_company_url` | text | Y | LinkedIn company page URL | attribute | URL | inferred |
| 5 | `source_system` | `cl.company_identity.source_system` | text | N | System that originated this record | attribute | STRING | inferred |
| 6 | `created_at` | `cl.company_identity.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 7 | `company_fingerprint` | `cl.company_identity.company_fingerprint` | text | Y | Company Fingerprint | attribute | STRING | inferred |
| 8 | `lifecycle_run_id` | `cl.company_identity.lifecycle_run_id` | text | Y | Run identifier for lifecycle batch | identifier | STRING | inferred |
| 9 | `existence_verified` | `cl.company_identity.existence_verified` | boolean | Y | Existence Verified | attribute | BOOLEAN | inferred |
| 10 | `verification_run_id` | `cl.company_identity.verification_run_id` | text | Y | Run identifier for verification batch | identifier | STRING | inferred |
| 11 | `verified_at` | `cl.company_identity.verified_at` | timestamp with time zone | Y | When verification was completed | attribute | ISO-8601 | inferred |
| 12 | `domain_status_code` | `cl.company_identity.domain_status_code` | integer | Y | Domain Status Code | attribute | INTEGER | inferred |
| 13 | `name_match_score` | `cl.company_identity.name_match_score` | integer | Y | Name Match score | metric | INTEGER | inferred |
| 14 | `state_match_result` | `cl.company_identity.state_match_result` | text | Y | State Match Result | attribute | STRING | inferred |
| 15 | `canonical_name` | `cl.company_identity.canonical_name` | text | Y | Canonical Name | attribute | STRING | inferred |
| 16 | `state_verified` | `cl.company_identity.state_verified` | text | Y | State Verified | attribute | STRING | inferred |
| 17 | `employee_count_band` | `cl.company_identity.employee_count_band` | text | Y | Employee Count Band | attribute | STRING | inferred |
| 18 | `identity_pass` | `cl.company_identity.identity_pass` | integer | Y | Identity Pass | attribute | INTEGER | inferred |
| 19 | `identity_status` | `cl.company_identity.identity_status` | text | Y | Identity Status | attribute | STRING | inferred |
| 20 | `last_pass_at` | `cl.company_identity.last_pass_at` | timestamp with time zone | Y | Timestamp for last pass event | attribute | ISO-8601 | inferred |
| 21 | `eligibility_status` | `cl.company_identity.eligibility_status` | text | Y | Eligibility Status | attribute | STRING | inferred |
| 22 | `exclusion_reason` | `cl.company_identity.exclusion_reason` | text | Y | Exclusion Reason | attribute | STRING | inferred |
| 23 | `entity_role` | `cl.company_identity.entity_role` | text | Y | Entity Role | attribute | STRING | inferred |
| 24 | `sovereign_company_id` | `cl.company_identity.sovereign_company_id` | uuid | Y | FK to cl.company_identity (sovereign company identifier) | foreign_key | UUID | inferred |
| 25 | `final_outcome` | `cl.company_identity.final_outcome` | text | Y | Final outcome after processing | attribute | STRING | inferred |
| 26 | `final_reason` | `cl.company_identity.final_reason` | text | Y | Reason for final outcome | attribute | STRING | inferred |
| 27 | `outreach_id` | `cl.company_identity.outreach_id` | uuid | Y | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 28 | `sales_process_id` | `cl.company_identity.sales_process_id` | uuid | Y | Sales Process Id | identifier | UUID | inferred |
| 29 | `client_id` | `cl.company_identity.client_id` | uuid | Y | Client Id | identifier | UUID | inferred |
| 30 | `outreach_attached_at` | `cl.company_identity.outreach_attached_at` | timestamp with time zone | Y | Timestamp for outreachtached event | attribute | ISO-8601 | inferred |
| 31 | `sales_opened_at` | `cl.company_identity.sales_opened_at` | timestamp with time zone | Y | Timestamp for sales opened event | attribute | ISO-8601 | inferred |
| 32 | `client_promoted_at` | `cl.company_identity.client_promoted_at` | timestamp with time zone | Y | Timestamp for client promoted event | attribute | ISO-8601 | inferred |
| 33 | `normalized_domain` | `cl.company_identity.normalized_domain` | text | Y | Normalized Domain | attribute | STRING | inferred |
| 34 | `updated_at` | `cl.company_identity.updated_at` | timestamp with time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |
| 35 | `state_code` | `cl.company_identity.state_code` | character(2) | Y | US state code (2-letter) | attribute | STRING | inferred |

### `cl.company_identity_archive` -- ARCHIVE -- 22,263 rows

**Hub**: `CL` CL Authority Registry

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `company_unique_id` | `cl.company_identity_archive.company_unique_id` | uuid | N | FK to cl.company_identity or Barton company ID | foreign_key | UUID | inferred |
| 2 | `company_name` | `cl.company_identity_archive.company_name` | text | N | Company legal or common name | attribute | STRING | inferred |
| 3 | `company_domain` | `cl.company_identity_archive.company_domain` | text | Y | Company Domain | attribute | STRING | inferred |
| 4 | `linkedin_company_url` | `cl.company_identity_archive.linkedin_company_url` | text | Y | LinkedIn company page URL | attribute | URL | inferred |
| 5 | `source_system` | `cl.company_identity_archive.source_system` | text | N | System that originated this record | attribute | STRING | inferred |
| 6 | `created_at` | `cl.company_identity_archive.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 7 | `company_fingerprint` | `cl.company_identity_archive.company_fingerprint` | text | Y | Company Fingerprint | attribute | STRING | inferred |
| 8 | `lifecycle_run_id` | `cl.company_identity_archive.lifecycle_run_id` | text | Y | Run identifier for lifecycle batch | identifier | STRING | inferred |
| 9 | `existence_verified` | `cl.company_identity_archive.existence_verified` | boolean | Y | Existence Verified | attribute | BOOLEAN | inferred |
| 10 | `verification_run_id` | `cl.company_identity_archive.verification_run_id` | text | Y | Run identifier for verification batch | identifier | STRING | inferred |
| 11 | `verified_at` | `cl.company_identity_archive.verified_at` | timestamp with time zone | Y | When verification was completed | attribute | ISO-8601 | inferred |
| 12 | `domain_status_code` | `cl.company_identity_archive.domain_status_code` | integer | Y | Domain Status Code | attribute | INTEGER | inferred |
| 13 | `name_match_score` | `cl.company_identity_archive.name_match_score` | integer | Y | Name Match score | metric | INTEGER | inferred |
| 14 | `state_match_result` | `cl.company_identity_archive.state_match_result` | text | Y | State Match Result | attribute | STRING | inferred |
| 15 | `canonical_name` | `cl.company_identity_archive.canonical_name` | text | Y | Canonical Name | attribute | STRING | inferred |
| 16 | `state_verified` | `cl.company_identity_archive.state_verified` | text | Y | State Verified | attribute | STRING | inferred |
| 17 | `employee_count_band` | `cl.company_identity_archive.employee_count_band` | text | Y | Employee Count Band | attribute | STRING | inferred |
| 18 | `identity_pass` | `cl.company_identity_archive.identity_pass` | integer | Y | Identity Pass | attribute | INTEGER | inferred |
| 19 | `identity_status` | `cl.company_identity_archive.identity_status` | text | Y | Identity Status | attribute | STRING | inferred |
| 20 | `last_pass_at` | `cl.company_identity_archive.last_pass_at` | timestamp with time zone | Y | Timestamp for last pass event | attribute | ISO-8601 | inferred |
| 21 | `eligibility_status` | `cl.company_identity_archive.eligibility_status` | text | Y | Eligibility Status | attribute | STRING | inferred |
| 22 | `exclusion_reason` | `cl.company_identity_archive.exclusion_reason` | text | Y | Exclusion Reason | attribute | STRING | inferred |
| 23 | `entity_role` | `cl.company_identity_archive.entity_role` | text | Y | Entity Role | attribute | STRING | inferred |
| 24 | `sovereign_company_id` | `cl.company_identity_archive.sovereign_company_id` | uuid | Y | FK to cl.company_identity (sovereign company identifier) | foreign_key | UUID | inferred |
| 25 | `final_outcome` | `cl.company_identity_archive.final_outcome` | text | Y | Final outcome after processing | attribute | STRING | inferred |
| 26 | `final_reason` | `cl.company_identity_archive.final_reason` | text | Y | Reason for final outcome | attribute | STRING | inferred |
| 27 | `archived_at` | `cl.company_identity_archive.archived_at` | timestamp with time zone | Y | When this record was archived | attribute | ISO-8601 | inferred |
| 28 | `archive_reason` | `cl.company_identity_archive.archive_reason` | text | Y | Reason this record was archived | attribute | STRING | inferred |

### `cl.company_identity_bridge` -- CANONICAL -- 74,641 rows

**Hub**: `CL` CL Authority Registry

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `bridge_id` | `cl.company_identity_bridge.bridge_id` | uuid | N | Bridge Id | identifier | UUID | inferred |
| 2 | `source_company_id` | `cl.company_identity_bridge.source_company_id` | text | N | Source Company Id | identifier | STRING | inferred |
| 3 | `company_sov_id` | `cl.company_identity_bridge.company_sov_id` | uuid | N | Company Sov Id | identifier | UUID | inferred |
| 4 | `source_system` | `cl.company_identity_bridge.source_system` | text | N | System that originated this record | attribute | STRING | inferred |
| 5 | `minted_at` | `cl.company_identity_bridge.minted_at` | timestamp with time zone | N | Timestamp for minted event | attribute | ISO-8601 | inferred |
| 6 | `minted_by` | `cl.company_identity_bridge.minted_by` | text | N | Minted By | attribute | STRING | inferred |
| 7 | `lifecycle_run_id` | `cl.company_identity_bridge.lifecycle_run_id` | text | Y | Run identifier for lifecycle batch | identifier | STRING | inferred |

### `cl.company_identity_excluded` -- CANONICAL -- 5,327 rows

**Hub**: `CL` CL Authority Registry

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `company_unique_id` | `cl.company_identity_excluded.company_unique_id` | uuid | N | FK to cl.company_identity or Barton company ID | foreign_key | UUID | inferred |
| 2 | `company_name` | `cl.company_identity_excluded.company_name` | text | N | Company legal or common name | attribute | STRING | inferred |
| 3 | `company_domain` | `cl.company_identity_excluded.company_domain` | text | Y | Company Domain | attribute | STRING | inferred |
| 4 | `linkedin_company_url` | `cl.company_identity_excluded.linkedin_company_url` | text | Y | LinkedIn company page URL | attribute | URL | inferred |
| 5 | `source_system` | `cl.company_identity_excluded.source_system` | text | N | System that originated this record | attribute | STRING | inferred |
| 6 | `created_at` | `cl.company_identity_excluded.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 7 | `company_fingerprint` | `cl.company_identity_excluded.company_fingerprint` | text | Y | Company Fingerprint | attribute | STRING | inferred |
| 8 | `lifecycle_run_id` | `cl.company_identity_excluded.lifecycle_run_id` | text | Y | Run identifier for lifecycle batch | identifier | STRING | inferred |
| 9 | `existence_verified` | `cl.company_identity_excluded.existence_verified` | boolean | Y | Existence Verified | attribute | BOOLEAN | inferred |
| 10 | `verification_run_id` | `cl.company_identity_excluded.verification_run_id` | text | Y | Run identifier for verification batch | identifier | STRING | inferred |
| 11 | `verified_at` | `cl.company_identity_excluded.verified_at` | timestamp with time zone | Y | When verification was completed | attribute | ISO-8601 | inferred |
| 12 | `domain_status_code` | `cl.company_identity_excluded.domain_status_code` | integer | Y | Domain Status Code | attribute | INTEGER | inferred |
| 13 | `name_match_score` | `cl.company_identity_excluded.name_match_score` | integer | Y | Name Match score | metric | INTEGER | inferred |
| 14 | `state_match_result` | `cl.company_identity_excluded.state_match_result` | text | Y | State Match Result | attribute | STRING | inferred |
| 15 | `canonical_name` | `cl.company_identity_excluded.canonical_name` | text | Y | Canonical Name | attribute | STRING | inferred |
| 16 | `state_verified` | `cl.company_identity_excluded.state_verified` | text | Y | State Verified | attribute | STRING | inferred |
| 17 | `employee_count_band` | `cl.company_identity_excluded.employee_count_band` | text | Y | Employee Count Band | attribute | STRING | inferred |
| 18 | `identity_pass` | `cl.company_identity_excluded.identity_pass` | integer | Y | Identity Pass | attribute | INTEGER | inferred |
| 19 | `identity_status` | `cl.company_identity_excluded.identity_status` | text | Y | Identity Status | attribute | STRING | inferred |
| 20 | `last_pass_at` | `cl.company_identity_excluded.last_pass_at` | timestamp with time zone | Y | Timestamp for last pass event | attribute | ISO-8601 | inferred |
| 21 | `eligibility_status` | `cl.company_identity_excluded.eligibility_status` | text | Y | Eligibility Status | attribute | STRING | inferred |
| 22 | `exclusion_reason` | `cl.company_identity_excluded.exclusion_reason` | text | Y | Exclusion Reason | attribute | STRING | inferred |
| 23 | `entity_role` | `cl.company_identity_excluded.entity_role` | text | Y | Entity Role | attribute | STRING | inferred |
| 24 | `sovereign_company_id` | `cl.company_identity_excluded.sovereign_company_id` | uuid | Y | FK to cl.company_identity (sovereign company identifier) | foreign_key | UUID | inferred |
| 25 | `final_outcome` | `cl.company_identity_excluded.final_outcome` | text | Y | Final outcome after processing | attribute | STRING | inferred |
| 26 | `final_reason` | `cl.company_identity_excluded.final_reason` | text | Y | Reason for final outcome | attribute | STRING | inferred |
| 27 | `outreach_id` | `cl.company_identity_excluded.outreach_id` | uuid | Y | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 28 | `sales_process_id` | `cl.company_identity_excluded.sales_process_id` | uuid | Y | Sales Process Id | identifier | UUID | inferred |
| 29 | `client_id` | `cl.company_identity_excluded.client_id` | uuid | Y | Client Id | identifier | UUID | inferred |
| 30 | `outreach_attached_at` | `cl.company_identity_excluded.outreach_attached_at` | timestamp with time zone | Y | Timestamp for outreachtached event | attribute | ISO-8601 | inferred |
| 31 | `sales_opened_at` | `cl.company_identity_excluded.sales_opened_at` | timestamp with time zone | Y | Timestamp for sales opened event | attribute | ISO-8601 | inferred |
| 32 | `client_promoted_at` | `cl.company_identity_excluded.client_promoted_at` | timestamp with time zone | Y | Timestamp for client promoted event | attribute | ISO-8601 | inferred |
| 33 | `normalized_domain` | `cl.company_identity_excluded.normalized_domain` | text | Y | Normalized Domain | attribute | STRING | inferred |

### `cl.company_names` -- CANONICAL -- 70,843 rows

**Hub**: `CL` CL Authority Registry

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `name_id` | `cl.company_names.name_id` | uuid | N | Name Id | identifier | UUID | inferred |
| 2 | `company_unique_id` | `cl.company_names.company_unique_id` | uuid | N | FK to cl.company_identity or Barton company ID | foreign_key | UUID | inferred |
| 3 | `name_value` | `cl.company_names.name_value` | text | N | Name Value | attribute | STRING | inferred |
| 4 | `name_type` | `cl.company_names.name_type` | text | N | Name Type | attribute | STRING | inferred |
| 5 | `created_at` | `cl.company_names.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

### `cl.company_names_archive` -- ARCHIVE -- 17,764 rows

**Hub**: `CL` CL Authority Registry

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `name_id` | `cl.company_names_archive.name_id` | uuid | N | Name Id | identifier | UUID | inferred |
| 2 | `company_unique_id` | `cl.company_names_archive.company_unique_id` | uuid | N | FK to cl.company_identity or Barton company ID | foreign_key | UUID | inferred |
| 3 | `name_value` | `cl.company_names_archive.name_value` | text | N | Name Value | attribute | STRING | inferred |
| 4 | `name_type` | `cl.company_names_archive.name_type` | text | N | Name Type | attribute | STRING | inferred |
| 5 | `created_at` | `cl.company_names_archive.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 6 | `archived_at` | `cl.company_names_archive.archived_at` | timestamp with time zone | Y | When this record was archived | attribute | ISO-8601 | inferred |
| 7 | `archive_reason` | `cl.company_names_archive.archive_reason` | text | Y | Reason this record was archived | attribute | STRING | inferred |

### `cl.company_names_excluded` -- CANONICAL -- 7,361 rows

**Hub**: `CL` CL Authority Registry

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `name_id` | `cl.company_names_excluded.name_id` | uuid | N | Name Id | identifier | UUID | inferred |
| 2 | `company_unique_id` | `cl.company_names_excluded.company_unique_id` | uuid | N | FK to cl.company_identity or Barton company ID | foreign_key | UUID | inferred |
| 3 | `name_value` | `cl.company_names_excluded.name_value` | text | N | Name Value | attribute | STRING | inferred |
| 4 | `name_type` | `cl.company_names_excluded.name_type` | text | N | Name Type | attribute | STRING | inferred |
| 5 | `created_at` | `cl.company_names_excluded.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

### `cl.domain_hierarchy` -- CANONICAL -- 4,705 rows

**Hub**: `CL` CL Authority Registry

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `hierarchy_id` | `cl.domain_hierarchy.hierarchy_id` | uuid | N | Hierarchy Id | identifier | UUID | inferred |
| 2 | `domain` | `cl.domain_hierarchy.domain` | text | N | Company website domain (lowercase, no protocol) | attribute | STRING | inferred |
| 3 | `parent_company_id` | `cl.domain_hierarchy.parent_company_id` | uuid | Y | Parent Company Id | foreign_key | UUID | inferred |
| 4 | `child_company_id` | `cl.domain_hierarchy.child_company_id` | uuid | Y | Child Company Id | identifier | UUID | inferred |
| 5 | `relationship_type` | `cl.domain_hierarchy.relationship_type` | text | N | Relationship Type | attribute | STRING | inferred |
| 6 | `confidence_score` | `cl.domain_hierarchy.confidence_score` | integer | Y | Confidence score (0-100) | metric | INTEGER | inferred |
| 7 | `resolution_method` | `cl.domain_hierarchy.resolution_method` | text | Y | Resolution Method | attribute | STRING | inferred |
| 8 | `created_at` | `cl.domain_hierarchy.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

### `cl.domain_hierarchy_archive` -- ARCHIVE -- 1,878 rows

**Hub**: `CL` CL Authority Registry

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `hierarchy_id` | `cl.domain_hierarchy_archive.hierarchy_id` | uuid | N | Hierarchy Id | identifier | UUID | inferred |
| 2 | `domain` | `cl.domain_hierarchy_archive.domain` | text | N | Company website domain (lowercase, no protocol) | attribute | STRING | inferred |
| 3 | `parent_company_id` | `cl.domain_hierarchy_archive.parent_company_id` | uuid | Y | Parent Company Id | foreign_key | UUID | inferred |
| 4 | `child_company_id` | `cl.domain_hierarchy_archive.child_company_id` | uuid | Y | Child Company Id | identifier | UUID | inferred |
| 5 | `relationship_type` | `cl.domain_hierarchy_archive.relationship_type` | text | N | Relationship Type | attribute | STRING | inferred |
| 6 | `confidence_score` | `cl.domain_hierarchy_archive.confidence_score` | integer | Y | Confidence score (0-100) | metric | INTEGER | inferred |
| 7 | `resolution_method` | `cl.domain_hierarchy_archive.resolution_method` | text | Y | Resolution Method | attribute | STRING | inferred |
| 8 | `created_at` | `cl.domain_hierarchy_archive.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 9 | `archived_at` | `cl.domain_hierarchy_archive.archived_at` | timestamp with time zone | Y | When this record was archived | attribute | ISO-8601 | inferred |
| 10 | `archive_reason` | `cl.domain_hierarchy_archive.archive_reason` | text | Y | Reason this record was archived | attribute | STRING | inferred |

### `cl.identity_confidence` -- CANONICAL -- 46,583 rows

**Hub**: `CL` CL Authority Registry

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `company_unique_id` | `cl.identity_confidence.company_unique_id` | uuid | N | FK to cl.company_identity or Barton company ID | foreign_key | UUID | inferred |
| 2 | `confidence_score` | `cl.identity_confidence.confidence_score` | integer | N | Confidence score (0-100) | metric | INTEGER | inferred |
| 3 | `confidence_bucket` | `cl.identity_confidence.confidence_bucket` | text | N | Confidence Bucket | attribute | STRING | inferred |
| 4 | `computed_at` | `cl.identity_confidence.computed_at` | timestamp with time zone | Y | Timestamp for computed event | attribute | ISO-8601 | inferred |

### `cl.identity_confidence_archive` -- ARCHIVE -- 19,850 rows

**Hub**: `CL` CL Authority Registry

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `company_unique_id` | `cl.identity_confidence_archive.company_unique_id` | uuid | N | FK to cl.company_identity or Barton company ID | foreign_key | UUID | inferred |
| 2 | `confidence_score` | `cl.identity_confidence_archive.confidence_score` | integer | N | Confidence score (0-100) | metric | INTEGER | inferred |
| 3 | `confidence_bucket` | `cl.identity_confidence_archive.confidence_bucket` | text | N | Confidence Bucket | attribute | STRING | inferred |
| 4 | `computed_at` | `cl.identity_confidence_archive.computed_at` | timestamp with time zone | Y | Timestamp for computed event | attribute | ISO-8601 | inferred |
| 5 | `archived_at` | `cl.identity_confidence_archive.archived_at` | timestamp with time zone | Y | When this record was archived | attribute | ISO-8601 | inferred |
| 6 | `archive_reason` | `cl.identity_confidence_archive.archive_reason` | text | Y | Reason this record was archived | attribute | STRING | inferred |

### `cl.identity_confidence_excluded` -- CANONICAL -- 5,327 rows

**Hub**: `CL` CL Authority Registry

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `company_unique_id` | `cl.identity_confidence_excluded.company_unique_id` | uuid | N | FK to cl.company_identity or Barton company ID | foreign_key | UUID | inferred |
| 2 | `confidence_score` | `cl.identity_confidence_excluded.confidence_score` | integer | N | Confidence score (0-100) | metric | INTEGER | inferred |
| 3 | `confidence_bucket` | `cl.identity_confidence_excluded.confidence_bucket` | text | N | Confidence Bucket | attribute | STRING | inferred |
| 4 | `computed_at` | `cl.identity_confidence_excluded.computed_at` | timestamp with time zone | Y | Timestamp for computed event | attribute | ISO-8601 | inferred |

### `cl.movement_code_registry` -- UNREGISTERED -- 15 rows

**Hub**: `CL` CL Authority Registry

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `subhub` | `cl.movement_code_registry.subhub` | character varying | N | Subhub | attribute | STRING | inferred |
| 2 | `code` | `cl.movement_code_registry.code` | integer | N | Code | attribute | INTEGER | inferred |
| 3 | `description` | `cl.movement_code_registry.description` | text | N | Description | attribute | STRING | inferred |
| 4 | `active` | `cl.movement_code_registry.active` | boolean | N | Active | attribute | BOOLEAN | inferred |
| 5 | `created_at` | `cl.movement_code_registry.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |

### `cl.sovereign_mint_backup_20260218` -- UNREGISTERED -- 60,212 rows

**Hub**: `CL` CL Authority Registry

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `company_unique_id` | `cl.sovereign_mint_backup_20260218.company_unique_id` | uuid | Y | FK to cl.company_identity or Barton company ID | foreign_key | UUID | inferred |
| 2 | `source_system` | `cl.sovereign_mint_backup_20260218.source_system` | text | Y | System that originated this record | attribute | STRING | inferred |
| 3 | `company_name` | `cl.sovereign_mint_backup_20260218.company_name` | text | Y | Company legal or common name | attribute | STRING | inferred |
| 4 | `old_sovereign_id` | `cl.sovereign_mint_backup_20260218.old_sovereign_id` | uuid | Y | Old Sovereign Id | identifier | UUID | inferred |

---

## `04.04` Outreach Spine

**Tables**: 16 | **Total rows**: 186,252

### `outreach.column_registry` -- REGISTRY -- 48 rows

**Hub**: `04.04` Outreach Spine

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `registry_id` | `outreach.column_registry.registry_id` | integer | N | Registry Id | identifier | INTEGER | inferred |
| 2 | `schema_name` | `outreach.column_registry.schema_name` | character varying(50) | N | Schema Name | attribute | STRING | inferred |
| 3 | `table_name` | `outreach.column_registry.table_name` | character varying(100) | N | Table Name | attribute | STRING | inferred |
| 4 | `column_name` | `outreach.column_registry.column_name` | character varying(100) | N | Column Name | attribute | STRING | inferred |
| 5 | `column_unique_id` | `outreach.column_registry.column_unique_id` | character varying(50) | N | Column Unique Id | identifier | STRING | inferred |
| 6 | `column_description` | `outreach.column_registry.column_description` | text | N | Column Description | attribute | STRING | inferred |
| 7 | `column_format` | `outreach.column_registry.column_format` | character varying(200) | N | Column Format | attribute | STRING | inferred |
| 8 | `is_nullable` | `outreach.column_registry.is_nullable` | boolean | N | Whether this record nullable | attribute | BOOLEAN | inferred |
| 9 | `default_value` | `outreach.column_registry.default_value` | text | Y | Default Value | attribute | STRING | inferred |
| 10 | `fk_reference` | `outreach.column_registry.fk_reference` | text | Y | Fk Reference | attribute | STRING | inferred |
| 11 | `created_at` | `outreach.column_registry.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 12 | `updated_at` | `outreach.column_registry.updated_at` | timestamp with time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |

### `outreach.ctb_audit_log` -- SYSTEM -- 1,534 rows

**Hub**: `04.04` Outreach Spine

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `audit_id` | `outreach.ctb_audit_log.audit_id` | integer | N | Audit Id | identifier | INTEGER | inferred |
| 2 | `source_hub` | `outreach.ctb_audit_log.source_hub` | character varying(50) | N | Source Hub | attribute | STRING | inferred |
| 3 | `source_table` | `outreach.ctb_audit_log.source_table` | character varying(100) | N | Source Table | attribute | STRING | inferred |
| 4 | `log_data` | `outreach.ctb_audit_log.log_data` | jsonb | N | Log Data | attribute | JSONB | inferred |
| 5 | `original_id` | `outreach.ctb_audit_log.original_id` | text | Y | Original Id | identifier | STRING | inferred |
| 6 | `original_created_at` | `outreach.ctb_audit_log.original_created_at` | timestamp with time zone | Y | Timestamp for original created event | attribute | ISO-8601 | inferred |
| 7 | `ctb_merged_at` | `outreach.ctb_audit_log.ctb_merged_at` | timestamp with time zone | Y | Timestamp for ctb merged event | attribute | ISO-8601 | inferred |

### `outreach.ctb_queue` -- STAGING -- 33,217 rows

**Hub**: `04.04` Outreach Spine

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `queue_id` | `outreach.ctb_queue.queue_id` | integer | N | Queue Id | identifier | INTEGER | inferred |
| 2 | `queue_type` | `outreach.ctb_queue.queue_type` | character varying(50) | N | Queue Type | attribute | STRING | inferred |
| 3 | `source_table` | `outreach.ctb_queue.source_table` | character varying(100) | N | Source Table | attribute | STRING | inferred |
| 4 | `queue_data` | `outreach.ctb_queue.queue_data` | jsonb | N | Queue Data | attribute | JSONB | inferred |
| 5 | `company_unique_id` | `outreach.ctb_queue.company_unique_id` | text | Y | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 6 | `status` | `outreach.ctb_queue.status` | character varying(50) | Y | Current status of this record | attribute | ENUM | inferred |
| 7 | `priority` | `outreach.ctb_queue.priority` | integer | Y | Priority | attribute | INTEGER | inferred |
| 8 | `original_created_at` | `outreach.ctb_queue.original_created_at` | timestamp with time zone | Y | Timestamp for original created event | attribute | ISO-8601 | inferred |
| 9 | `ctb_merged_at` | `outreach.ctb_queue.ctb_merged_at` | timestamp with time zone | Y | Timestamp for ctb merged event | attribute | ISO-8601 | inferred |

### `outreach.engagement_events` -- MV -- 0 rows

**Hub**: `04.04` Outreach Spine

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `event_id` | `outreach.engagement_events.event_id` | uuid | N | UUID primary key | identifier | UUID | outreach.column_registry |
| 2 | `person_id` | `outreach.engagement_events.person_id` | uuid | N | FK to outreach.people | foreign_key | UUID | outreach.column_registry |
| 3 | `target_id` | `outreach.engagement_events.target_id` | uuid | N | FK to outreach.company_target | foreign_key | UUID | outreach.column_registry |
| 4 | `company_unique_id` | `outreach.engagement_events.company_unique_id` | text | N | Denormalized FK to cl | foreign_key | TEXT | outreach.column_registry |
| 5 | `event_type` | `outreach.engagement_events.event_type` | USER-DEFINED | N | Event type enum | attribute | outreach.event_type | outreach.column_registry |
| 6 | `event_subtype` | `outreach.engagement_events.event_subtype` | text | Y | Event subtype | attribute | TEXT | outreach.column_registry |
| 7 | `event_ts` | `outreach.engagement_events.event_ts` | timestamp with time zone | N | Event timestamp | attribute | TIMESTAMPTZ | outreach.column_registry |
| 8 | `source_system` | `outreach.engagement_events.source_system` | text | Y | Source system | attribute | TEXT | outreach.column_registry |
| 9 | `source_campaign_id` | `outreach.engagement_events.source_campaign_id` | text | Y | Source campaign ID | identifier | TEXT | outreach.column_registry |
| 10 | `source_email_id` | `outreach.engagement_events.source_email_id` | text | Y | Source email ID | identifier | TEXT | outreach.column_registry |
| 11 | `metadata` | `outreach.engagement_events.metadata` | jsonb | N | Event metadata | attribute | JSONB | outreach.column_registry |
| 12 | `is_processed` | `outreach.engagement_events.is_processed` | boolean | N | Processing flag | attribute | BOOLEAN | outreach.column_registry |
| 13 | `processed_at` | `outreach.engagement_events.processed_at` | timestamp with time zone | Y | Processing timestamp | attribute | TIMESTAMPTZ | outreach.column_registry |
| 14 | `triggered_transition` | `outreach.engagement_events.triggered_transition` | boolean | N | Transition flag | attribute | BOOLEAN | outreach.column_registry |
| 15 | `transition_to_state` | `outreach.engagement_events.transition_to_state` | USER-DEFINED | Y | New lifecycle state | attribute | outreach.lifecycle_state | outreach.column_registry |
| 16 | `event_hash` | `outreach.engagement_events.event_hash` | character varying(64) | Y | Deduplication hash | attribute | VARCHAR(64) | outreach.column_registry |
| 17 | `is_duplicate` | `outreach.engagement_events.is_duplicate` | boolean | N | Duplicate flag | attribute | BOOLEAN | outreach.column_registry |
| 18 | `created_at` | `outreach.engagement_events.created_at` | timestamp with time zone | N | Creation timestamp | attribute | TIMESTAMPTZ | outreach.column_registry |
| 19 | `outreach_id` | `outreach.engagement_events.outreach_id` | uuid | Y | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |

### `outreach.entity_resolution_queue` -- STAGING -- 2 rows

**Hub**: `04.04` Outreach Spine

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `outreach.entity_resolution_queue.id` | uuid | N | Id | identifier | UUID | inferred |
| 2 | `company_unique_id` | `outreach.entity_resolution_queue.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 3 | `candidate_ein` | `outreach.entity_resolution_queue.candidate_ein` | character varying(9) | Y | Candidate Ein | attribute | STRING | inferred |
| 4 | `candidate_name` | `outreach.entity_resolution_queue.candidate_name` | text | Y | Candidate Name | attribute | STRING | inferred |
| 5 | `candidate_city` | `outreach.entity_resolution_queue.candidate_city` | text | Y | Candidate City | attribute | STRING | inferred |
| 6 | `candidate_state` | `outreach.entity_resolution_queue.candidate_state` | character varying(2) | Y | Candidate State | attribute | STRING | inferred |
| 7 | `candidate_zip` | `outreach.entity_resolution_queue.candidate_zip` | character varying(10) | Y | Candidate Zip | attribute | STRING | inferred |
| 8 | `clay_domain` | `outreach.entity_resolution_queue.clay_domain` | text | Y | Clay Domain | attribute | STRING | inferred |
| 9 | `match_score` | `outreach.entity_resolution_queue.match_score` | numeric | Y | Match score | metric | NUMERIC | inferred |
| 10 | `match_tier` | `outreach.entity_resolution_queue.match_tier` | character varying(10) | Y | Match Tier | attribute | STRING | inferred |
| 11 | `resolution_status` | `outreach.entity_resolution_queue.resolution_status` | character varying(20) | Y | Resolution Status | attribute | STRING | inferred |
| 12 | `resolution_method` | `outreach.entity_resolution_queue.resolution_method` | text | Y | Resolution Method | attribute | STRING | inferred |
| 13 | `resolved_at` | `outreach.entity_resolution_queue.resolved_at` | timestamp with time zone | Y | When this error/issue was resolved | attribute | ISO-8601 | inferred |
| 14 | `created_at` | `outreach.entity_resolution_queue.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 15 | `queue_type` | `outreach.entity_resolution_queue.queue_type` | character varying(50) | Y | Queue Type | attribute | STRING | inferred |

### `outreach.hub_registry` -- REGISTRY -- 6 rows

**Hub**: `04.04` Outreach Spine

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `hub_id` | `outreach.hub_registry.hub_id` | character varying(50) | N | Hub Id | identifier | STRING | inferred |
| 2 | `hub_name` | `outreach.hub_registry.hub_name` | character varying(100) | N | Hub Name | attribute | STRING | inferred |
| 3 | `doctrine_id` | `outreach.hub_registry.doctrine_id` | character varying(20) | N | Doctrine Id | identifier | STRING | inferred |
| 4 | `classification` | `outreach.hub_registry.classification` | character varying(20) | N | Classification | attribute | STRING | inferred |
| 5 | `gates_completion` | `outreach.hub_registry.gates_completion` | boolean | N | Gates Completion | attribute | BOOLEAN | inferred |
| 6 | `waterfall_order` | `outreach.hub_registry.waterfall_order` | integer | N | Waterfall Order | attribute | INTEGER | inferred |
| 7 | `core_metric` | `outreach.hub_registry.core_metric` | character varying(50) | N | Core Metric | attribute | STRING | inferred |
| 8 | `metric_healthy_threshold` | `outreach.hub_registry.metric_healthy_threshold` | numeric | Y | Metric Healthy Threshold | attribute | NUMERIC | inferred |
| 9 | `metric_critical_threshold` | `outreach.hub_registry.metric_critical_threshold` | numeric | Y | Metric Critical Threshold | attribute | NUMERIC | inferred |
| 10 | `description` | `outreach.hub_registry.description` | text | Y | Description | attribute | STRING | inferred |
| 11 | `created_at` | `outreach.hub_registry.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 12 | `updated_at` | `outreach.hub_registry.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |

### `outreach.manual_overrides` -- SYSTEM -- 0 rows

**Hub**: `04.04` Outreach Spine

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `override_id` | `outreach.manual_overrides.override_id` | uuid | N | Override Id | identifier | UUID | inferred |
| 2 | `company_unique_id` | `outreach.manual_overrides.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 3 | `override_type` | `outreach.manual_overrides.override_type` | USER-DEFINED | N | Override Type | attribute | STRING | inferred |
| 4 | `reason` | `outreach.manual_overrides.reason` | text | N | Reason | attribute | STRING | inferred |
| 5 | `metadata` | `outreach.manual_overrides.metadata` | jsonb | Y | Metadata | attribute | JSONB | inferred |
| 6 | `created_at` | `outreach.manual_overrides.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 7 | `created_by` | `outreach.manual_overrides.created_by` | text | N | Created By | attribute | STRING | inferred |
| 8 | `expires_at` | `outreach.manual_overrides.expires_at` | timestamp with time zone | Y | When this record expires | attribute | ISO-8601 | inferred |
| 9 | `is_active` | `outreach.manual_overrides.is_active` | boolean | N | Whether this record active | attribute | BOOLEAN | inferred |
| 10 | `deactivated_at` | `outreach.manual_overrides.deactivated_at` | timestamp with time zone | Y | Timestamp for deactivated event | attribute | ISO-8601 | inferred |
| 11 | `deactivated_by` | `outreach.manual_overrides.deactivated_by` | text | Y | Deactivated By | attribute | STRING | inferred |
| 12 | `deactivation_reason` | `outreach.manual_overrides.deactivation_reason` | text | Y | Deactivation Reason | attribute | STRING | inferred |

### `outreach.mv_credit_usage` -- SYSTEM -- 2 rows

**Hub**: `04.04` Outreach Spine

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `outreach.mv_credit_usage.id` | integer | N | Id | identifier | INTEGER | inferred |
| 2 | `usage_date` | `outreach.mv_credit_usage.usage_date` | date | N | Usage Date | attribute | DATE | inferred |
| 3 | `credits_used` | `outreach.mv_credit_usage.credits_used` | integer | N | Credits Used | attribute | INTEGER | inferred |
| 4 | `cost_estimate` | `outreach.mv_credit_usage.cost_estimate` | numeric | Y | Cost Estimate | attribute | NUMERIC | inferred |
| 5 | `created_at` | `outreach.mv_credit_usage.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 6 | `updated_at` | `outreach.mv_credit_usage.updated_at` | timestamp with time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |

### `outreach.outreach` -- CANONICAL FROZEN -- 114,137 rows

**Hub**: `04.04` Outreach Spine

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `outreach_id` | `outreach.outreach.outreach_id` | uuid | N | Universal join key — minted here, propagated to all sub-hub tables | identifier | UUID | column_registry.yml |
| 2 | `sovereign_id` | `outreach.outreach.sovereign_id` | uuid | N | FK to cl.company_identity (sovereign company identifier) | foreign_key | UUID | inferred |
| 3 | `created_at` | `outreach.outreach.created_at` | timestamp with time zone | N | When the outreach record was created | attribute | ISO-8601 | column_registry.yml |
| 4 | `updated_at` | `outreach.outreach.updated_at` | timestamp with time zone | N | When the outreach record was last updated | attribute | ISO-8601 | column_registry.yml |
| 5 | `domain` | `outreach.outreach.domain` | character varying(255) | Y | Company website domain (lowercase, no protocol) | attribute | STRING | inferred |
| 6 | `ein` | `outreach.outreach.ein` | character varying(20) | Y | Employer Identification Number (9-digit, no dashes) | attribute | STRING | inferred |
| 7 | `has_appointment` | `outreach.outreach.has_appointment` | boolean | Y | Whether this record appointment | attribute | BOOLEAN | inferred |

### `outreach.outreach_archive` -- ARCHIVE -- 27,416 rows

**Hub**: `04.04` Outreach Spine

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `outreach_id` | `outreach.outreach_archive.outreach_id` | uuid | N | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 2 | `sovereign_id` | `outreach.outreach_archive.sovereign_id` | uuid | N | FK to cl.company_identity (sovereign company identifier) | foreign_key | UUID | inferred |
| 3 | `created_at` | `outreach.outreach_archive.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 4 | `updated_at` | `outreach.outreach_archive.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |
| 5 | `domain` | `outreach.outreach_archive.domain` | character varying(255) | Y | Company website domain (lowercase, no protocol) | attribute | STRING | inferred |
| 6 | `archived_at` | `outreach.outreach_archive.archived_at` | timestamp with time zone | Y | When this record was archived | attribute | ISO-8601 | inferred |
| 7 | `archive_reason` | `outreach.outreach_archive.archive_reason` | text | Y | Reason this record was archived | attribute | STRING | inferred |

### `outreach.outreach_errors` -- ERROR -- 0 rows

**Hub**: `04.04` Outreach Spine

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `error_id` | `outreach.outreach_errors.error_id` | uuid | N | Primary key for this error record | identifier | UUID | inferred |
| 2 | `company_unique_id` | `outreach.outreach_errors.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 3 | `outreach_id` | `outreach.outreach_errors.outreach_id` | text | Y | FK to outreach.outreach spine table (universal join key) | foreign_key | STRING | inferred |
| 4 | `pipeline_stage` | `outreach.outreach_errors.pipeline_stage` | text | N | Pipeline Stage | attribute | STRING | inferred |
| 5 | `failure_code` | `outreach.outreach_errors.failure_code` | text | N | Failure Code | attribute | STRING | inferred |
| 6 | `details` | `outreach.outreach_errors.details` | text | Y | Event details (JSON) | attribute | STRING | inferred |
| 7 | `run_id` | `outreach.outreach_errors.run_id` | text | N | Run Id | identifier | STRING | inferred |
| 8 | `created_at` | `outreach.outreach_errors.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 9 | `error_type` | `outreach.outreach_errors.error_type` | character varying(100) | Y | Discriminator column classifying the error type | attribute | ENUM | inferred |

### `outreach.outreach_excluded` -- ARCHIVE -- 5,483 rows

**Hub**: `04.04` Outreach Spine

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `outreach_id` | `outreach.outreach_excluded.outreach_id` | uuid | N | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 2 | `company_name` | `outreach.outreach_excluded.company_name` | text | Y | Company legal or common name | attribute | STRING | inferred |
| 3 | `domain` | `outreach.outreach_excluded.domain` | text | Y | Company website domain (lowercase, no protocol) | attribute | STRING | inferred |
| 4 | `exclusion_reason` | `outreach.outreach_excluded.exclusion_reason` | text | Y | Exclusion Reason | attribute | STRING | inferred |
| 5 | `excluded_at` | `outreach.outreach_excluded.excluded_at` | timestamp with time zone | Y | Timestamp for excluded event | attribute | ISO-8601 | inferred |
| 6 | `created_at` | `outreach.outreach_excluded.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 7 | `updated_at` | `outreach.outreach_excluded.updated_at` | timestamp with time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |
| 8 | `sovereign_id` | `outreach.outreach_excluded.sovereign_id` | uuid | Y | FK to cl.company_identity (sovereign company identifier) | foreign_key | UUID | inferred |
| 9 | `cl_status` | `outreach.outreach_excluded.cl_status` | text | Y | Cl Status | attribute | STRING | inferred |
| 10 | `excluded_by` | `outreach.outreach_excluded.excluded_by` | text | Y | Excluded By | attribute | STRING | inferred |

### `outreach.outreach_legacy_quarantine` -- ARCHIVE -- 1,698 rows

**Hub**: `04.04` Outreach Spine

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `outreach_id` | `outreach.outreach_legacy_quarantine.outreach_id` | uuid | N | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 2 | `sovereign_id` | `outreach.outreach_legacy_quarantine.sovereign_id` | uuid | Y | FK to cl.company_identity (sovereign company identifier) | foreign_key | UUID | inferred |
| 3 | `quarantine_reason` | `outreach.outreach_legacy_quarantine.quarantine_reason` | text | N | Quarantine Reason | attribute | STRING | inferred |
| 4 | `original_created_at` | `outreach.outreach_legacy_quarantine.original_created_at` | timestamp with time zone | Y | Timestamp for original created event | attribute | ISO-8601 | inferred |
| 5 | `quarantined_at` | `outreach.outreach_legacy_quarantine.quarantined_at` | timestamp with time zone | Y | Timestamp for quarantined event | attribute | ISO-8601 | inferred |

### `outreach.outreach_orphan_archive` -- ARCHIVE -- 2,709 rows

**Hub**: `04.04` Outreach Spine

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `outreach_id` | `outreach.outreach_orphan_archive.outreach_id` | uuid | N | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 2 | `sovereign_id` | `outreach.outreach_orphan_archive.sovereign_id` | uuid | N | FK to cl.company_identity (sovereign company identifier) | foreign_key | UUID | inferred |
| 3 | `created_at` | `outreach.outreach_orphan_archive.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 4 | `updated_at` | `outreach.outreach_orphan_archive.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |
| 5 | `domain` | `outreach.outreach_orphan_archive.domain` | character varying | Y | Company website domain (lowercase, no protocol) | attribute | STRING | inferred |
| 6 | `archived_at` | `outreach.outreach_orphan_archive.archived_at` | timestamp with time zone | Y | When this record was archived | attribute | ISO-8601 | inferred |
| 7 | `archive_reason` | `outreach.outreach_orphan_archive.archive_reason` | character varying | Y | Reason this record was archived | attribute | STRING | inferred |

### `outreach.override_audit_log` -- SYSTEM -- 0 rows

**Hub**: `04.04` Outreach Spine

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `audit_id` | `outreach.override_audit_log.audit_id` | uuid | N | Audit Id | identifier | UUID | inferred |
| 2 | `company_unique_id` | `outreach.override_audit_log.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 3 | `override_id` | `outreach.override_audit_log.override_id` | uuid | Y | Override Id | identifier | UUID | inferred |
| 4 | `action` | `outreach.override_audit_log.action` | text | N | Action | attribute | STRING | inferred |
| 5 | `override_type` | `outreach.override_audit_log.override_type` | USER-DEFINED | Y | Override Type | attribute | STRING | inferred |
| 6 | `old_value` | `outreach.override_audit_log.old_value` | jsonb | Y | Old Value | attribute | JSONB | inferred |
| 7 | `new_value` | `outreach.override_audit_log.new_value` | jsonb | Y | New Value | attribute | JSONB | inferred |
| 8 | `performed_by` | `outreach.override_audit_log.performed_by` | text | N | Performed By | attribute | STRING | inferred |
| 9 | `performed_at` | `outreach.override_audit_log.performed_at` | timestamp with time zone | N | Timestamp for performed event | attribute | ISO-8601 | inferred |

### `outreach.pipeline_audit_log` -- SYSTEM -- 0 rows

**Hub**: `04.04` Outreach Spine

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `log_id` | `outreach.pipeline_audit_log.log_id` | integer | N | Primary key for this log entry | identifier | INTEGER | inferred |
| 2 | `company_unique_id` | `outreach.pipeline_audit_log.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 3 | `outreach_id` | `outreach.pipeline_audit_log.outreach_id` | text | Y | FK to outreach.outreach spine table (universal join key) | foreign_key | STRING | inferred |
| 4 | `hub` | `outreach.pipeline_audit_log.hub` | text | N | Hub | attribute | STRING | inferred |
| 5 | `outcome` | `outreach.pipeline_audit_log.outcome` | text | N | Outcome | attribute | STRING | inferred |
| 6 | `failure_code` | `outreach.pipeline_audit_log.failure_code` | text | Y | Failure Code | attribute | STRING | inferred |
| 7 | `run_id` | `outreach.pipeline_audit_log.run_id` | text | N | Run Id | identifier | STRING | inferred |
| 8 | `created_at` | `outreach.pipeline_audit_log.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 9 | `source_hub` | `outreach.pipeline_audit_log.source_hub` | character varying(50) | Y | Source Hub | attribute | STRING | inferred |

---

## `04.04.01` Company Target

**Tables**: 9 | **Total rows**: 368,493

### `outreach.company_hub_status` -- MV -- 68,908 rows

**Hub**: `04.04.01` Company Target

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `company_unique_id` | `outreach.company_hub_status.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 2 | `hub_id` | `outreach.company_hub_status.hub_id` | character varying(50) | N | Hub Id | identifier | STRING | inferred |
| 3 | `status` | `outreach.company_hub_status.status` | USER-DEFINED | N | Current status of this record | attribute | ENUM | inferred |
| 4 | `status_reason` | `outreach.company_hub_status.status_reason` | text | Y | Status Reason | attribute | STRING | inferred |
| 5 | `metric_value` | `outreach.company_hub_status.metric_value` | numeric | Y | Metric Value | attribute | NUMERIC | inferred |
| 6 | `last_processed_at` | `outreach.company_hub_status.last_processed_at` | timestamp with time zone | Y | Timestamp for last processed event | attribute | ISO-8601 | inferred |
| 7 | `created_at` | `outreach.company_hub_status.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 8 | `updated_at` | `outreach.company_hub_status.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |

### `outreach.company_target` -- CANONICAL FROZEN -- 114,137 rows

**Hub**: `04.04.01` Company Target

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `target_id` | `outreach.company_target.target_id` | uuid | N | UUID primary key for outreach company target record | identifier | UUID | outreach.column_registry |
| 2 | `company_unique_id` | `outreach.company_target.company_unique_id` | text | Y | FK to cl.company_identity - parent hub identity | foreign_key | TEXT | outreach.column_registry |
| 3 | `outreach_status` | `outreach.company_target.outreach_status` | text | N | Current outreach status | attribute | TEXT | outreach.column_registry |
| 4 | `bit_score_snapshot` | `outreach.company_target.bit_score_snapshot` | integer | Y | Cached BIT score at targeting (0-100) | attribute | INTEGER | outreach.column_registry |
| 5 | `first_targeted_at` | `outreach.company_target.first_targeted_at` | timestamp with time zone | Y | First targeting timestamp | attribute | TIMESTAMPTZ | outreach.column_registry |
| 6 | `last_targeted_at` | `outreach.company_target.last_targeted_at` | timestamp with time zone | Y | Most recent outreach timestamp | attribute | TIMESTAMPTZ | outreach.column_registry |
| 7 | `sequence_count` | `outreach.company_target.sequence_count` | integer | N | Number of sequences completed | attribute | INTEGER | outreach.column_registry |
| 8 | `active_sequence_id` | `outreach.company_target.active_sequence_id` | text | Y | Current sequence ID | identifier | TEXT | outreach.column_registry |
| 9 | `source` | `outreach.company_target.source` | text | Y | Record origin | attribute | TEXT | outreach.column_registry |
| 10 | `created_at` | `outreach.company_target.created_at` | timestamp with time zone | N | Creation timestamp | attribute | TIMESTAMPTZ | outreach.column_registry |
| 11 | `updated_at` | `outreach.company_target.updated_at` | timestamp with time zone | N | Last update timestamp | attribute | TIMESTAMPTZ | outreach.column_registry |
| 12 | `outreach_id` | `outreach.company_target.outreach_id` | uuid | Y | FK to outreach.outreach spine table | foreign_key | UUID | column_registry.yml |
| 13 | `email_method` | `outreach.company_target.email_method` | character varying(100) | Y | Email Method | attribute | EMAIL | inferred |
| 14 | `method_type` | `outreach.company_target.method_type` | character varying(50) | Y | Method Type | attribute | STRING | inferred |
| 15 | `confidence_score` | `outreach.company_target.confidence_score` | numeric | Y | Confidence score (0-100) | metric | NUMERIC | inferred |
| 16 | `execution_status` | `outreach.company_target.execution_status` | character varying(50) | Y | Execution Status | attribute | STRING | inferred |
| 17 | `imo_completed_at` | `outreach.company_target.imo_completed_at` | timestamp with time zone | Y | Timestamp for imo completed event | attribute | ISO-8601 | inferred |
| 18 | `is_catchall` | `outreach.company_target.is_catchall` | boolean | Y | Whether this record catchall | attribute | BOOLEAN | inferred |
| 19 | `industry` | `outreach.company_target.industry` | character varying(255) | Y | Industry | attribute | STRING | inferred |
| 20 | `employees` | `outreach.company_target.employees` | integer | Y | Employees | attribute | INTEGER | inferred |
| 21 | `country` | `outreach.company_target.country` | character varying(10) | Y | Country name or code | attribute | STRING | inferred |
| 22 | `state` | `outreach.company_target.state` | character varying(50) | Y | US state code (2-letter) | attribute | ENUM | inferred |
| 23 | `city` | `outreach.company_target.city` | character varying(100) | Y | City name | attribute | STRING | inferred |
| 24 | `postal_code` | `outreach.company_target.postal_code` | character varying(20) | Y | ZIP/postal code (5-digit) | attribute | STRING | inferred |
| 25 | `data_year` | `outreach.company_target.data_year` | integer | Y | Data Year | attribute | INTEGER | inferred |
| 26 | `postal_code_source` | `outreach.company_target.postal_code_source` | text | Y | Postal Code Source | attribute | STRING | inferred |
| 27 | `postal_code_updated_at` | `outreach.company_target.postal_code_updated_at` | timestamp with time zone | Y | Timestamp for postal code updated event | attribute | ISO-8601 | inferred |

### `outreach.company_target_archive` -- ARCHIVE -- 81,753 rows

**Hub**: `04.04.01` Company Target

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `target_id` | `outreach.company_target_archive.target_id` | uuid | N | Primary key for this target record | identifier | UUID | inferred |
| 2 | `company_unique_id` | `outreach.company_target_archive.company_unique_id` | text | Y | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 3 | `outreach_status` | `outreach.company_target_archive.outreach_status` | text | N | Outreach Status | attribute | STRING | inferred |
| 4 | `bit_score_snapshot` | `outreach.company_target_archive.bit_score_snapshot` | integer | Y | Bit Score Snapshot | attribute | INTEGER | inferred |
| 5 | `first_targeted_at` | `outreach.company_target_archive.first_targeted_at` | timestamp with time zone | Y | Timestamp for first targeted event | attribute | ISO-8601 | inferred |
| 6 | `last_targeted_at` | `outreach.company_target_archive.last_targeted_at` | timestamp with time zone | Y | Timestamp for last targeted event | attribute | ISO-8601 | inferred |
| 7 | `sequence_count` | `outreach.company_target_archive.sequence_count` | integer | N | Count of sequence | metric | INTEGER | inferred |
| 8 | `active_sequence_id` | `outreach.company_target_archive.active_sequence_id` | text | Y | Active Sequence Id | identifier | STRING | inferred |
| 9 | `source` | `outreach.company_target_archive.source` | text | Y | Data source identifier | attribute | STRING | inferred |
| 10 | `created_at` | `outreach.company_target_archive.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 11 | `updated_at` | `outreach.company_target_archive.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |
| 12 | `outreach_id` | `outreach.company_target_archive.outreach_id` | uuid | Y | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 13 | `email_method` | `outreach.company_target_archive.email_method` | character varying(100) | Y | Email Method | attribute | EMAIL | inferred |
| 14 | `method_type` | `outreach.company_target_archive.method_type` | character varying(50) | Y | Method Type | attribute | STRING | inferred |
| 15 | `confidence_score` | `outreach.company_target_archive.confidence_score` | numeric | Y | Confidence score (0-100) | metric | NUMERIC | inferred |
| 16 | `execution_status` | `outreach.company_target_archive.execution_status` | character varying(50) | Y | Execution Status | attribute | STRING | inferred |
| 17 | `imo_completed_at` | `outreach.company_target_archive.imo_completed_at` | timestamp with time zone | Y | Timestamp for imo completed event | attribute | ISO-8601 | inferred |
| 18 | `is_catchall` | `outreach.company_target_archive.is_catchall` | boolean | Y | Whether this record catchall | attribute | BOOLEAN | inferred |
| 19 | `archived_at` | `outreach.company_target_archive.archived_at` | timestamp with time zone | Y | When this record was archived | attribute | ISO-8601 | inferred |
| 20 | `archive_reason` | `outreach.company_target_archive.archive_reason` | text | Y | Reason this record was archived | attribute | STRING | inferred |

### `outreach.company_target_dead_ends` -- UNREGISTERED -- 4,427 rows

**Hub**: `04.04.01` Company Target

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `archive_id` | `outreach.company_target_dead_ends.archive_id` | uuid | N | Archive Id | identifier | UUID | inferred |
| 2 | `outreach_id` | `outreach.company_target_dead_ends.outreach_id` | uuid | N | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 3 | `domain` | `outreach.company_target_dead_ends.domain` | text | Y | Company website domain (lowercase, no protocol) | attribute | STRING | inferred |
| 4 | `email_method` | `outreach.company_target_dead_ends.email_method` | text | Y | Email Method | attribute | EMAIL | inferred |
| 5 | `method_type` | `outreach.company_target_dead_ends.method_type` | text | Y | Method Type | attribute | STRING | inferred |
| 6 | `confidence_score` | `outreach.company_target_dead_ends.confidence_score` | numeric | Y | Confidence score (0-100) | metric | NUMERIC | inferred |
| 7 | `archived_at` | `outreach.company_target_dead_ends.archived_at` | timestamp with time zone | Y | When this record was archived | attribute | ISO-8601 | inferred |
| 8 | `archive_reason` | `outreach.company_target_dead_ends.archive_reason` | text | Y | Reason this record was archived | attribute | STRING | inferred |

### `outreach.company_target_errors` -- ERROR -- 4,108 rows

**Hub**: `04.04.01` Company Target

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `error_id` | `outreach.company_target_errors.error_id` | uuid | N | Primary key for error record | identifier | UUID | column_registry.yml |
| 2 | `outreach_id` | `outreach.company_target_errors.outreach_id` | uuid | N | FK to spine (nullable — error may occur before entity exists) | foreign_key | UUID | column_registry.yml |
| 3 | `pipeline_stage` | `outreach.company_target_errors.pipeline_stage` | character varying(100) | N | Pipeline Stage | attribute | STRING | inferred |
| 4 | `failure_code` | `outreach.company_target_errors.failure_code` | character varying(50) | N | Failure Code | attribute | STRING | inferred |
| 5 | `blocking_reason` | `outreach.company_target_errors.blocking_reason` | text | N | Blocking Reason | attribute | STRING | inferred |
| 6 | `severity` | `outreach.company_target_errors.severity` | character varying(20) | N | Severity | attribute | STRING | inferred |
| 7 | `retry_allowed` | `outreach.company_target_errors.retry_allowed` | boolean | N | Retry Allowed | attribute | BOOLEAN | inferred |
| 8 | `created_at` | `outreach.company_target_errors.created_at` | timestamp with time zone | N | When the error was recorded | attribute | ISO-8601 | column_registry.yml |
| 9 | `resolved_at` | `outreach.company_target_errors.resolved_at` | timestamp with time zone | Y | When this error/issue was resolved | attribute | ISO-8601 | inferred |
| 10 | `resolution_note` | `outreach.company_target_errors.resolution_note` | text | Y | Resolution Note | attribute | STRING | inferred |
| 11 | `raw_input` | `outreach.company_target_errors.raw_input` | jsonb | Y | Raw Input | attribute | JSONB | inferred |
| 12 | `stack_trace` | `outreach.company_target_errors.stack_trace` | text | Y | Stack Trace | attribute | STRING | inferred |
| 13 | `imo_stage` | `outreach.company_target_errors.imo_stage` | character varying(10) | Y | Imo Stage | attribute | STRING | inferred |
| 14 | `requeue_attempts` | `outreach.company_target_errors.requeue_attempts` | integer | Y | Requeue Attempts | attribute | INTEGER | inferred |
| 15 | `disposition` | `outreach.company_target_errors.disposition` | USER-DEFINED | Y | Disposition | attribute | STRING | inferred |
| 16 | `retry_count` | `outreach.company_target_errors.retry_count` | integer | Y | Number of retry attempts so far | metric | INTEGER | inferred |
| 17 | `max_retries` | `outreach.company_target_errors.max_retries` | integer | Y | Max Retries | attribute | INTEGER | inferred |
| 18 | `archived_at` | `outreach.company_target_errors.archived_at` | timestamp with time zone | Y | When this record was archived | attribute | ISO-8601 | inferred |
| 19 | `parked_at` | `outreach.company_target_errors.parked_at` | timestamp with time zone | Y | Timestamp for parked event | attribute | ISO-8601 | inferred |
| 20 | `parked_by` | `outreach.company_target_errors.parked_by` | text | Y | Parked By | attribute | STRING | inferred |
| 21 | `park_reason` | `outreach.company_target_errors.park_reason` | text | Y | Park Reason | attribute | STRING | inferred |
| 22 | `escalation_level` | `outreach.company_target_errors.escalation_level` | integer | Y | Escalation Level | attribute | INTEGER | inferred |
| 23 | `escalated_at` | `outreach.company_target_errors.escalated_at` | timestamp with time zone | Y | Timestamp for escalated event | attribute | ISO-8601 | inferred |
| 24 | `ttl_tier` | `outreach.company_target_errors.ttl_tier` | USER-DEFINED | Y | Ttl Tier | attribute | STRING | inferred |
| 25 | `last_retry_at` | `outreach.company_target_errors.last_retry_at` | timestamp with time zone | Y | Timestamp for last retry event | attribute | ISO-8601 | inferred |
| 26 | `next_retry_at` | `outreach.company_target_errors.next_retry_at` | timestamp with time zone | Y | Timestamp for next retry event | attribute | ISO-8601 | inferred |
| 27 | `retry_exhausted` | `outreach.company_target_errors.retry_exhausted` | boolean | Y | Retry Exhausted | attribute | BOOLEAN | inferred |
| 28 | `error_type` | `outreach.company_target_errors.error_type` | character varying(100) | Y | Discriminator column — classifies the error | attribute | ENUM | column_registry.yml |

### `outreach.company_target_errors_archive` -- ARCHIVE -- 0 rows

**Hub**: `04.04.01` Company Target

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `error_id` | `outreach.company_target_errors_archive.error_id` | uuid | N | Primary key for this error record | identifier | UUID | inferred |
| 2 | `outreach_id` | `outreach.company_target_errors_archive.outreach_id` | uuid | Y | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 3 | `pipeline_stage` | `outreach.company_target_errors_archive.pipeline_stage` | character varying(50) | Y | Pipeline Stage | attribute | STRING | inferred |
| 4 | `imo_stage` | `outreach.company_target_errors_archive.imo_stage` | character varying(50) | Y | Imo Stage | attribute | STRING | inferred |
| 5 | `failure_code` | `outreach.company_target_errors_archive.failure_code` | character varying(50) | Y | Failure Code | attribute | STRING | inferred |
| 6 | `blocking_reason` | `outreach.company_target_errors_archive.blocking_reason` | text | Y | Blocking Reason | attribute | STRING | inferred |
| 7 | `severity` | `outreach.company_target_errors_archive.severity` | character varying(20) | Y | Severity | attribute | STRING | inferred |
| 8 | `retry_allowed` | `outreach.company_target_errors_archive.retry_allowed` | boolean | Y | Retry Allowed | attribute | BOOLEAN | inferred |
| 9 | `raw_input` | `outreach.company_target_errors_archive.raw_input` | jsonb | Y | Raw Input | attribute | JSONB | inferred |
| 10 | `stack_trace` | `outreach.company_target_errors_archive.stack_trace` | text | Y | Stack Trace | attribute | STRING | inferred |
| 11 | `created_at` | `outreach.company_target_errors_archive.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 12 | `resolved_at` | `outreach.company_target_errors_archive.resolved_at` | timestamp with time zone | Y | When this error/issue was resolved | attribute | ISO-8601 | inferred |
| 13 | `resolution_note` | `outreach.company_target_errors_archive.resolution_note` | text | Y | Resolution Note | attribute | STRING | inferred |
| 14 | `disposition` | `outreach.company_target_errors_archive.disposition` | USER-DEFINED | Y | Disposition | attribute | STRING | inferred |
| 15 | `retry_count` | `outreach.company_target_errors_archive.retry_count` | integer | Y | Number of retry attempts so far | metric | INTEGER | inferred |
| 16 | `max_retries` | `outreach.company_target_errors_archive.max_retries` | integer | Y | Max Retries | attribute | INTEGER | inferred |
| 17 | `parked_at` | `outreach.company_target_errors_archive.parked_at` | timestamp with time zone | Y | Timestamp for parked event | attribute | ISO-8601 | inferred |
| 18 | `parked_by` | `outreach.company_target_errors_archive.parked_by` | text | Y | Parked By | attribute | STRING | inferred |
| 19 | `park_reason` | `outreach.company_target_errors_archive.park_reason` | text | Y | Park Reason | attribute | STRING | inferred |
| 20 | `escalation_level` | `outreach.company_target_errors_archive.escalation_level` | integer | Y | Escalation Level | attribute | INTEGER | inferred |
| 21 | `escalated_at` | `outreach.company_target_errors_archive.escalated_at` | timestamp with time zone | Y | Timestamp for escalated event | attribute | ISO-8601 | inferred |
| 22 | `ttl_tier` | `outreach.company_target_errors_archive.ttl_tier` | USER-DEFINED | Y | Ttl Tier | attribute | STRING | inferred |
| 23 | `last_retry_at` | `outreach.company_target_errors_archive.last_retry_at` | timestamp with time zone | Y | Timestamp for last retry event | attribute | ISO-8601 | inferred |
| 24 | `retry_exhausted` | `outreach.company_target_errors_archive.retry_exhausted` | boolean | Y | Retry Exhausted | attribute | BOOLEAN | inferred |
| 25 | `archived_at` | `outreach.company_target_errors_archive.archived_at` | timestamp with time zone | N | When this record was archived | attribute | ISO-8601 | inferred |
| 26 | `archived_by` | `outreach.company_target_errors_archive.archived_by` | text | Y | Archived By | attribute | STRING | inferred |
| 27 | `archive_reason` | `outreach.company_target_errors_archive.archive_reason` | text | Y | Reason this record was archived | attribute | STRING | inferred |
| 28 | `final_disposition` | `outreach.company_target_errors_archive.final_disposition` | USER-DEFINED | Y | Final Disposition | attribute | STRING | inferred |
| 29 | `retention_expires_at` | `outreach.company_target_errors_archive.retention_expires_at` | timestamp with time zone | Y | Timestamp for retention expires event | attribute | ISO-8601 | inferred |
| 30 | `error_type` | `outreach.company_target_errors_archive.error_type` | character varying(100) | Y | Discriminator column classifying the error type | attribute | ENUM | inferred |

### `outreach.company_target_orphaned_archive` -- ARCHIVE -- 52,812 rows

**Hub**: `04.04.01` Company Target

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `archived_at` | `outreach.company_target_orphaned_archive.archived_at` | timestamp with time zone | N | When this record was archived | attribute | ISO-8601 | inferred |
| 2 | `archive_reason` | `outreach.company_target_orphaned_archive.archive_reason` | text | Y | Reason this record was archived | attribute | STRING | inferred |
| 3 | `target_id` | `outreach.company_target_orphaned_archive.target_id` | uuid | N | Primary key for this target record | identifier | UUID | inferred |
| 4 | `company_unique_id` | `outreach.company_target_orphaned_archive.company_unique_id` | text | Y | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 5 | `outreach_id` | `outreach.company_target_orphaned_archive.outreach_id` | uuid | Y | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 6 | `email_method` | `outreach.company_target_orphaned_archive.email_method` | character varying(255) | Y | Email Method | attribute | EMAIL | inferred |
| 7 | `method_type` | `outreach.company_target_orphaned_archive.method_type` | character varying(50) | Y | Method Type | attribute | STRING | inferred |
| 8 | `confidence_score` | `outreach.company_target_orphaned_archive.confidence_score` | numeric | Y | Confidence score (0-100) | metric | NUMERIC | inferred |
| 9 | `execution_status` | `outreach.company_target_orphaned_archive.execution_status` | character varying(50) | Y | Execution Status | attribute | STRING | inferred |
| 10 | `outreach_status` | `outreach.company_target_orphaned_archive.outreach_status` | text | Y | Outreach Status | attribute | STRING | inferred |
| 11 | `bit_score_snapshot` | `outreach.company_target_orphaned_archive.bit_score_snapshot` | integer | Y | Bit Score Snapshot | attribute | INTEGER | inferred |
| 12 | `first_targeted_at` | `outreach.company_target_orphaned_archive.first_targeted_at` | timestamp with time zone | Y | Timestamp for first targeted event | attribute | ISO-8601 | inferred |
| 13 | `last_targeted_at` | `outreach.company_target_orphaned_archive.last_targeted_at` | timestamp with time zone | Y | Timestamp for last targeted event | attribute | ISO-8601 | inferred |
| 14 | `sequence_count` | `outreach.company_target_orphaned_archive.sequence_count` | integer | Y | Count of sequence | metric | INTEGER | inferred |
| 15 | `active_sequence_id` | `outreach.company_target_orphaned_archive.active_sequence_id` | text | Y | Active Sequence Id | identifier | STRING | inferred |
| 16 | `source` | `outreach.company_target_orphaned_archive.source` | text | Y | Data source identifier | attribute | STRING | inferred |
| 17 | `imo_completed_at` | `outreach.company_target_orphaned_archive.imo_completed_at` | timestamp with time zone | Y | Timestamp for imo completed event | attribute | ISO-8601 | inferred |
| 18 | `is_catchall` | `outreach.company_target_orphaned_archive.is_catchall` | boolean | Y | Whether this record catchall | attribute | BOOLEAN | inferred |
| 19 | `industry` | `outreach.company_target_orphaned_archive.industry` | character varying(100) | Y | Industry | attribute | STRING | inferred |
| 20 | `employees` | `outreach.company_target_orphaned_archive.employees` | integer | Y | Employees | attribute | INTEGER | inferred |
| 21 | `country` | `outreach.company_target_orphaned_archive.country` | character varying(100) | Y | Country name or code | attribute | STRING | inferred |
| 22 | `state` | `outreach.company_target_orphaned_archive.state` | character varying(100) | Y | US state code (2-letter) | attribute | ENUM | inferred |
| 23 | `city` | `outreach.company_target_orphaned_archive.city` | character varying(100) | Y | City name | attribute | STRING | inferred |
| 24 | `postal_code` | `outreach.company_target_orphaned_archive.postal_code` | character varying(20) | Y | ZIP/postal code (5-digit) | attribute | STRING | inferred |
| 25 | `data_year` | `outreach.company_target_orphaned_archive.data_year` | integer | Y | Data Year | attribute | INTEGER | inferred |
| 26 | `created_at` | `outreach.company_target_orphaned_archive.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 27 | `updated_at` | `outreach.company_target_orphaned_archive.updated_at` | timestamp with time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |
| 28 | `sovereign_id` | `outreach.company_target_orphaned_archive.sovereign_id` | uuid | Y | FK to cl.company_identity (sovereign company identifier) | foreign_key | UUID | inferred |
| 29 | `domain` | `outreach.company_target_orphaned_archive.domain` | character varying(255) | Y | Company website domain (lowercase, no protocol) | attribute | STRING | inferred |

### `outreach.url_discovery_failures` -- ERROR -- 42,348 rows

**Hub**: `04.04.01` Company Target

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `failure_id` | `outreach.url_discovery_failures.failure_id` | uuid | N | Failure Id | identifier | UUID | inferred |
| 2 | `company_unique_id` | `outreach.url_discovery_failures.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 3 | `website_url` | `outreach.url_discovery_failures.website_url` | text | Y | Company website URL | attribute | URL | inferred |
| 4 | `failure_reason` | `outreach.url_discovery_failures.failure_reason` | character varying(100) | N | Failure Reason | attribute | STRING | inferred |
| 5 | `retry_count` | `outreach.url_discovery_failures.retry_count` | integer | Y | Number of retry attempts so far | metric | INTEGER | inferred |
| 6 | `last_attempt_at` | `outreach.url_discovery_failures.last_attempt_at` | timestamp with time zone | Y | Timestamp for lasttempt event | attribute | ISO-8601 | inferred |
| 7 | `next_retry_at` | `outreach.url_discovery_failures.next_retry_at` | timestamp with time zone | Y | Timestamp for next retry event | attribute | ISO-8601 | inferred |
| 8 | `resolved_at` | `outreach.url_discovery_failures.resolved_at` | timestamp with time zone | Y | When this error/issue was resolved | attribute | ISO-8601 | inferred |
| 9 | `created_at` | `outreach.url_discovery_failures.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 10 | `disposition` | `outreach.url_discovery_failures.disposition` | USER-DEFINED | Y | Disposition | attribute | STRING | inferred |
| 11 | `max_retries` | `outreach.url_discovery_failures.max_retries` | integer | Y | Max Retries | attribute | INTEGER | inferred |
| 12 | `archived_at` | `outreach.url_discovery_failures.archived_at` | timestamp with time zone | Y | When this record was archived | attribute | ISO-8601 | inferred |
| 13 | `parked_at` | `outreach.url_discovery_failures.parked_at` | timestamp with time zone | Y | Timestamp for parked event | attribute | ISO-8601 | inferred |
| 14 | `parked_by` | `outreach.url_discovery_failures.parked_by` | text | Y | Parked By | attribute | STRING | inferred |
| 15 | `park_reason` | `outreach.url_discovery_failures.park_reason` | text | Y | Park Reason | attribute | STRING | inferred |
| 16 | `escalation_level` | `outreach.url_discovery_failures.escalation_level` | integer | Y | Escalation Level | attribute | INTEGER | inferred |
| 17 | `escalated_at` | `outreach.url_discovery_failures.escalated_at` | timestamp with time zone | Y | Timestamp for escalated event | attribute | ISO-8601 | inferred |
| 18 | `ttl_tier` | `outreach.url_discovery_failures.ttl_tier` | USER-DEFINED | Y | Ttl Tier | attribute | STRING | inferred |
| 19 | `last_retry_at` | `outreach.url_discovery_failures.last_retry_at` | timestamp with time zone | Y | Timestamp for last retry event | attribute | ISO-8601 | inferred |
| 20 | `retry_exhausted` | `outreach.url_discovery_failures.retry_exhausted` | boolean | Y | Retry Exhausted | attribute | BOOLEAN | inferred |

### `outreach.url_discovery_failures_archive` -- ARCHIVE -- 0 rows

**Hub**: `04.04.01` Company Target

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `failure_id` | `outreach.url_discovery_failures_archive.failure_id` | uuid | N | Failure Id | identifier | UUID | inferred |
| 2 | `company_unique_id` | `outreach.url_discovery_failures_archive.company_unique_id` | text | Y | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 3 | `failure_reason` | `outreach.url_discovery_failures_archive.failure_reason` | character varying(50) | Y | Failure Reason | attribute | STRING | inferred |
| 4 | `created_at` | `outreach.url_discovery_failures_archive.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 5 | `disposition` | `outreach.url_discovery_failures_archive.disposition` | USER-DEFINED | Y | Disposition | attribute | STRING | inferred |
| 6 | `retry_count` | `outreach.url_discovery_failures_archive.retry_count` | integer | Y | Number of retry attempts so far | metric | INTEGER | inferred |
| 7 | `max_retries` | `outreach.url_discovery_failures_archive.max_retries` | integer | Y | Max Retries | attribute | INTEGER | inferred |
| 8 | `parked_at` | `outreach.url_discovery_failures_archive.parked_at` | timestamp with time zone | Y | Timestamp for parked event | attribute | ISO-8601 | inferred |
| 9 | `parked_by` | `outreach.url_discovery_failures_archive.parked_by` | text | Y | Parked By | attribute | STRING | inferred |
| 10 | `park_reason` | `outreach.url_discovery_failures_archive.park_reason` | text | Y | Park Reason | attribute | STRING | inferred |
| 11 | `escalation_level` | `outreach.url_discovery_failures_archive.escalation_level` | integer | Y | Escalation Level | attribute | INTEGER | inferred |
| 12 | `escalated_at` | `outreach.url_discovery_failures_archive.escalated_at` | timestamp with time zone | Y | Timestamp for escalated event | attribute | ISO-8601 | inferred |
| 13 | `ttl_tier` | `outreach.url_discovery_failures_archive.ttl_tier` | USER-DEFINED | Y | Ttl Tier | attribute | STRING | inferred |
| 14 | `last_retry_at` | `outreach.url_discovery_failures_archive.last_retry_at` | timestamp with time zone | Y | Timestamp for last retry event | attribute | ISO-8601 | inferred |
| 15 | `retry_exhausted` | `outreach.url_discovery_failures_archive.retry_exhausted` | boolean | Y | Retry Exhausted | attribute | BOOLEAN | inferred |
| 16 | `archived_at` | `outreach.url_discovery_failures_archive.archived_at` | timestamp with time zone | N | When this record was archived | attribute | ISO-8601 | inferred |
| 17 | `archived_by` | `outreach.url_discovery_failures_archive.archived_by` | text | Y | Archived By | attribute | STRING | inferred |
| 18 | `archive_reason` | `outreach.url_discovery_failures_archive.archive_reason` | text | Y | Reason this record was archived | attribute | STRING | inferred |
| 19 | `final_disposition` | `outreach.url_discovery_failures_archive.final_disposition` | USER-DEFINED | Y | Final Disposition | attribute | STRING | inferred |
| 20 | `retention_expires_at` | `outreach.url_discovery_failures_archive.retention_expires_at` | timestamp with time zone | Y | Timestamp for retention expires event | attribute | ISO-8601 | inferred |
| 21 | `website_url` | `outreach.url_discovery_failures_archive.website_url` | text | Y | Company website URL | attribute | URL | inferred |

---

## `04.04.02` People Intelligence

**Tables**: 24 | **Total rows**: 1,034,589

### `outreach.people` -- SUPPORTING FROZEN -- 335,097 rows

**Hub**: `04.04.02` People Intelligence

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `person_id` | `outreach.people.person_id` | uuid | N | UUID primary key for person record | identifier | UUID | outreach.column_registry |
| 2 | `target_id` | `outreach.people.target_id` | uuid | N | FK to outreach.company_target | foreign_key | UUID | outreach.column_registry |
| 3 | `company_unique_id` | `outreach.people.company_unique_id` | text | N | Denormalized FK to cl.company_identity | foreign_key | TEXT | outreach.column_registry |
| 4 | `slot_type` | `outreach.people.slot_type` | text | Y | Executive slot: CHRO, HR, Benefits, CFO, CEO | attribute | TEXT | outreach.column_registry |
| 5 | `email` | `outreach.people.email` | text | N | Primary email address | attribute | TEXT | outreach.column_registry |
| 6 | `email_verified` | `outreach.people.email_verified` | boolean | N | Email verification status | attribute | BOOLEAN | outreach.column_registry |
| 7 | `email_verified_at` | `outreach.people.email_verified_at` | timestamp with time zone | Y | Verification timestamp | attribute | TIMESTAMPTZ | outreach.column_registry |
| 8 | `contact_status` | `outreach.people.contact_status` | text | N | Contact status | attribute | TEXT | outreach.column_registry |
| 9 | `lifecycle_state` | `outreach.people.lifecycle_state` | USER-DEFINED | N | Lifecycle stage | attribute | outreach.lifecycle_state | outreach.column_registry |
| 10 | `funnel_membership` | `outreach.people.funnel_membership` | USER-DEFINED | N | Funnel position | attribute | outreach.funnel_membership | outreach.column_registry |
| 11 | `email_open_count` | `outreach.people.email_open_count` | integer | N | Email open count | attribute | INTEGER | outreach.column_registry |
| 12 | `email_click_count` | `outreach.people.email_click_count` | integer | N | Email click count | attribute | INTEGER | outreach.column_registry |
| 13 | `email_reply_count` | `outreach.people.email_reply_count` | integer | N | Email reply count | attribute | INTEGER | outreach.column_registry |
| 14 | `current_bit_score` | `outreach.people.current_bit_score` | integer | N | Current BIT score (0-100) | attribute | INTEGER | outreach.column_registry |
| 15 | `last_event_ts` | `outreach.people.last_event_ts` | timestamp with time zone | Y | Last event timestamp | attribute | TIMESTAMPTZ | outreach.column_registry |
| 16 | `last_state_change_ts` | `outreach.people.last_state_change_ts` | timestamp with time zone | Y | Last state change timestamp | attribute | TIMESTAMPTZ | outreach.column_registry |
| 17 | `source` | `outreach.people.source` | text | Y | Record origin | attribute | TEXT | outreach.column_registry |
| 18 | `created_at` | `outreach.people.created_at` | timestamp with time zone | N | Creation timestamp | attribute | TIMESTAMPTZ | outreach.column_registry |
| 19 | `updated_at` | `outreach.people.updated_at` | timestamp with time zone | N | Last update timestamp | attribute | TIMESTAMPTZ | outreach.column_registry |
| 20 | `outreach_id` | `outreach.people.outreach_id` | uuid | Y | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |

### `outreach.people_archive` -- ARCHIVE -- 175 rows

**Hub**: `04.04.02` People Intelligence

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `person_id` | `outreach.people_archive.person_id` | uuid | N | Person Id | identifier | UUID | inferred |
| 2 | `target_id` | `outreach.people_archive.target_id` | uuid | N | Primary key for this target record | identifier | UUID | inferred |
| 3 | `company_unique_id` | `outreach.people_archive.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 4 | `slot_type` | `outreach.people_archive.slot_type` | text | Y | Executive role type (CEO, CFO, HR, CTO, CMO, COO) | attribute | ENUM | inferred |
| 5 | `email` | `outreach.people_archive.email` | text | N | Email address | attribute | EMAIL | inferred |
| 6 | `email_verified` | `outreach.people_archive.email_verified` | boolean | N | Whether email was verified via Million Verifier | attribute | BOOLEAN | inferred |
| 7 | `email_verified_at` | `outreach.people_archive.email_verified_at` | timestamp with time zone | Y | Timestamp for email verified event | attribute | ISO-8601 | inferred |
| 8 | `contact_status` | `outreach.people_archive.contact_status` | text | N | Contact Status | attribute | STRING | inferred |
| 9 | `lifecycle_state` | `outreach.people_archive.lifecycle_state` | USER-DEFINED | N | Lifecycle State | attribute | STRING | inferred |
| 10 | `funnel_membership` | `outreach.people_archive.funnel_membership` | USER-DEFINED | N | Funnel Membership | attribute | STRING | inferred |
| 11 | `email_open_count` | `outreach.people_archive.email_open_count` | integer | N | Count of email open | metric | INTEGER | inferred |
| 12 | `email_click_count` | `outreach.people_archive.email_click_count` | integer | N | Count of email click | metric | INTEGER | inferred |
| 13 | `email_reply_count` | `outreach.people_archive.email_reply_count` | integer | N | Count of email reply | metric | INTEGER | inferred |
| 14 | `current_bit_score` | `outreach.people_archive.current_bit_score` | integer | N | Current Bit score | metric | INTEGER | inferred |
| 15 | `last_event_ts` | `outreach.people_archive.last_event_ts` | timestamp with time zone | Y | Last Event Ts | attribute | ISO-8601 | inferred |
| 16 | `last_state_change_ts` | `outreach.people_archive.last_state_change_ts` | timestamp with time zone | Y | Last State Change Ts | attribute | ISO-8601 | inferred |
| 17 | `source` | `outreach.people_archive.source` | text | Y | Data source identifier | attribute | STRING | inferred |
| 18 | `created_at` | `outreach.people_archive.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 19 | `updated_at` | `outreach.people_archive.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |
| 20 | `outreach_id` | `outreach.people_archive.outreach_id` | uuid | Y | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 21 | `archived_at` | `outreach.people_archive.archived_at` | timestamp with time zone | Y | When this record was archived | attribute | ISO-8601 | inferred |
| 22 | `archive_reason` | `outreach.people_archive.archive_reason` | text | Y | Reason this record was archived | attribute | STRING | inferred |

### `outreach.people_errors` -- ERROR -- 0 rows

**Hub**: `04.04.02` People Intelligence

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `error_id` | `outreach.people_errors.error_id` | uuid | N | Primary key for this error record | identifier | UUID | inferred |
| 2 | `outreach_id` | `outreach.people_errors.outreach_id` | uuid | N | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 3 | `pipeline_stage` | `outreach.people_errors.pipeline_stage` | character varying(100) | N | Pipeline Stage | attribute | STRING | inferred |
| 4 | `failure_code` | `outreach.people_errors.failure_code` | character varying(50) | N | Failure Code | attribute | STRING | inferred |
| 5 | `blocking_reason` | `outreach.people_errors.blocking_reason` | text | N | Blocking Reason | attribute | STRING | inferred |
| 6 | `severity` | `outreach.people_errors.severity` | character varying(20) | N | Severity | attribute | STRING | inferred |
| 7 | `retry_allowed` | `outreach.people_errors.retry_allowed` | boolean | N | Retry Allowed | attribute | BOOLEAN | inferred |
| 8 | `created_at` | `outreach.people_errors.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 9 | `resolved_at` | `outreach.people_errors.resolved_at` | timestamp with time zone | Y | When this error/issue was resolved | attribute | ISO-8601 | inferred |
| 10 | `resolution_note` | `outreach.people_errors.resolution_note` | text | Y | Resolution Note | attribute | STRING | inferred |
| 11 | `raw_input` | `outreach.people_errors.raw_input` | jsonb | Y | Raw Input | attribute | JSONB | inferred |
| 12 | `stack_trace` | `outreach.people_errors.stack_trace` | text | Y | Stack Trace | attribute | STRING | inferred |
| 13 | `requeue_attempts` | `outreach.people_errors.requeue_attempts` | integer | Y | Requeue Attempts | attribute | INTEGER | inferred |
| 14 | `error_type` | `outreach.people_errors.error_type` | character varying(100) | Y | Discriminator column classifying the error type | attribute | ENUM | inferred |

### `people.company_resolution_log` -- SYSTEM -- 155 rows

**Hub**: `04.04.02` People Intelligence

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `log_id` | `people.company_resolution_log.log_id` | integer | N | Primary key for this log entry | identifier | INTEGER | inferred |
| 2 | `person_intake_id` | `people.company_resolution_log.person_intake_id` | text | N | Person Intake Id | identifier | STRING | inferred |
| 3 | `resolution_status` | `people.company_resolution_log.resolution_status` | text | N | Resolution Status | attribute | STRING | inferred |
| 4 | `company_id` | `people.company_resolution_log.company_id` | text | Y | Company Id | identifier | STRING | inferred |
| 5 | `normalized_role` | `people.company_resolution_log.normalized_role` | text | Y | Normalized Role | attribute | STRING | inferred |
| 6 | `reason` | `people.company_resolution_log.reason` | text | Y | Reason | attribute | STRING | inferred |
| 7 | `run_id` | `people.company_resolution_log.run_id` | text | N | Run Id | identifier | STRING | inferred |
| 8 | `created_at` | `people.company_resolution_log.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

### `people.company_slot` -- CANONICAL FROZEN -- 340,815 rows

**Hub**: `04.04.02` People Intelligence

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `slot_id` | `people.company_slot.slot_id` | uuid | N | Primary key for the slot record | identifier | UUID | column_registry.yml |
| 2 | `outreach_id` | `people.company_slot.outreach_id` | uuid | N | FK to outreach.outreach spine table | foreign_key | UUID | column_registry.yml |
| 3 | `company_unique_id` | `people.company_slot.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 4 | `slot_type` | `people.company_slot.slot_type` | text | N | Executive role type (CEO, CFO, HR, CTO, CMO, COO) | attribute | ENUM | column_registry.yml |
| 5 | `person_unique_id` | `people.company_slot.person_unique_id` | text | Y | FK to people.people_master.unique_id (Barton ID format 04.04.02.YY.NNNNNN.NNN) | foreign_key | STRING | column_registry.yml |
| 6 | `is_filled` | `people.company_slot.is_filled` | boolean | Y | Whether this slot has an assigned person (TRUE = people record linked) | attribute | BOOLEAN | column_registry.yml |
| 7 | `filled_at` | `people.company_slot.filled_at` | timestamp with time zone | Y | When this slot was filled with a person | attribute | ISO-8601 | inferred |
| 8 | `confidence_score` | `people.company_slot.confidence_score` | numeric | Y | Confidence score (0-100) | metric | NUMERIC | inferred |
| 9 | `source_system` | `people.company_slot.source_system` | text | Y | System that originated this record | attribute | STRING | inferred |
| 10 | `created_at` | `people.company_slot.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 11 | `updated_at` | `people.company_slot.updated_at` | timestamp with time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |
| 12 | `slot_phone` | `people.company_slot.slot_phone` | text | Y | Phone number stored on the slot | attribute | STRING | inferred |
| 13 | `slot_phone_source` | `people.company_slot.slot_phone_source` | text | Y | Source of the slot phone number | attribute | STRING | inferred |
| 14 | `slot_phone_updated_at` | `people.company_slot.slot_phone_updated_at` | timestamp with time zone | Y | Timestamp for slot phone updated event | attribute | ISO-8601 | inferred |

### `people.company_slot_archive` -- ARCHIVE -- 82,248 rows

**Hub**: `04.04.02` People Intelligence

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `slot_id` | `people.company_slot_archive.slot_id` | uuid | N | Primary key for this company slot record | identifier | UUID | inferred |
| 2 | `outreach_id` | `people.company_slot_archive.outreach_id` | uuid | N | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 3 | `company_unique_id` | `people.company_slot_archive.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 4 | `slot_type` | `people.company_slot_archive.slot_type` | text | N | Executive role type (CEO, CFO, HR, CTO, CMO, COO) | attribute | ENUM | inferred |
| 5 | `person_unique_id` | `people.company_slot_archive.person_unique_id` | text | Y | FK to people.people_master.unique_id (Barton person ID) | foreign_key | STRING | inferred |
| 6 | `is_filled` | `people.company_slot_archive.is_filled` | boolean | Y | Whether this slot has an assigned person | attribute | BOOLEAN | inferred |
| 7 | `filled_at` | `people.company_slot_archive.filled_at` | timestamp with time zone | Y | When this slot was filled with a person | attribute | ISO-8601 | inferred |
| 8 | `confidence_score` | `people.company_slot_archive.confidence_score` | numeric | Y | Confidence score (0-100) | metric | NUMERIC | inferred |
| 9 | `source_system` | `people.company_slot_archive.source_system` | text | Y | System that originated this record | attribute | STRING | inferred |
| 10 | `created_at` | `people.company_slot_archive.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 11 | `updated_at` | `people.company_slot_archive.updated_at` | timestamp with time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |
| 12 | `archived_at` | `people.company_slot_archive.archived_at` | timestamp with time zone | Y | When this record was archived | attribute | ISO-8601 | inferred |
| 13 | `archive_reason` | `people.company_slot_archive.archive_reason` | text | Y | Reason this record was archived | attribute | STRING | inferred |

### `people.paid_enrichment_queue` -- STAGING -- 32,011 rows

**Hub**: `04.04.02` People Intelligence

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `people.paid_enrichment_queue.id` | integer | N | Id | identifier | INTEGER | inferred |
| 2 | `source_url_id` | `people.paid_enrichment_queue.source_url_id` | uuid | N | Source Url Id | identifier | UUID | inferred |
| 3 | `company_unique_id` | `people.paid_enrichment_queue.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 4 | `company_name` | `people.paid_enrichment_queue.company_name` | character varying(255) | Y | Company legal or common name | attribute | STRING | inferred |
| 5 | `source_url` | `people.paid_enrichment_queue.source_url` | text | N | URL of the content source | attribute | URL | inferred |
| 6 | `url_type` | `people.paid_enrichment_queue.url_type` | character varying(50) | Y | Url Type | attribute | STRING | inferred |
| 7 | `failure_reason` | `people.paid_enrichment_queue.failure_reason` | text | Y | Failure Reason | attribute | STRING | inferred |
| 8 | `empty_slots` | `people.paid_enrichment_queue.empty_slots` | ARRAY | Y | Empty Slots | attribute | ARRAY | inferred |
| 9 | `priority` | `people.paid_enrichment_queue.priority` | integer | Y | Priority | attribute | INTEGER | inferred |
| 10 | `queued_at` | `people.paid_enrichment_queue.queued_at` | timestamp without time zone | Y | Timestamp for queued event | attribute | ISO-8601 | inferred |
| 11 | `processed_at` | `people.paid_enrichment_queue.processed_at` | timestamp without time zone | Y | Timestamp for processed event | attribute | ISO-8601 | inferred |
| 12 | `processed_via` | `people.paid_enrichment_queue.processed_via` | character varying(50) | Y | Processed Via | attribute | STRING | inferred |
| 13 | `status` | `people.paid_enrichment_queue.status` | character varying(20) | Y | Current status of this record | attribute | ENUM | inferred |

### `people.people_errors` -- ERROR -- 9,982 rows

**Hub**: `04.04.02` People Intelligence

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `error_id` | `people.people_errors.error_id` | uuid | N | Primary key for error record | identifier | UUID | column_registry.yml |
| 2 | `outreach_id` | `people.people_errors.outreach_id` | uuid | N | FK to spine (nullable — error may occur before entity exists) | foreign_key | UUID | column_registry.yml |
| 3 | `slot_id` | `people.people_errors.slot_id` | uuid | Y | Primary key for this company slot record | identifier | UUID | inferred |
| 4 | `person_id` | `people.people_errors.person_id` | uuid | Y | Person Id | identifier | UUID | inferred |
| 5 | `error_stage` | `people.people_errors.error_stage` | text | N | Pipeline stage where error occurred (slot_creation, slot_fill, etc.) | attribute | ENUM | column_registry.yml |
| 6 | `error_type` | `people.people_errors.error_type` | text | N | Discriminator column (validation, ambiguity, conflict, missing_data, stale_data, external_fail) | attribute | ENUM | column_registry.yml |
| 7 | `error_code` | `people.people_errors.error_code` | text | N | Error Code | attribute | STRING | inferred |
| 8 | `error_message` | `people.people_errors.error_message` | text | N | Human-readable error description | attribute | STRING | column_registry.yml |
| 9 | `source_hints_used` | `people.people_errors.source_hints_used` | jsonb | Y | Source Hints Used | attribute | JSONB | inferred |
| 10 | `raw_payload` | `people.people_errors.raw_payload` | jsonb | N | Raw Payload | attribute | JSONB | inferred |
| 11 | `retry_strategy` | `people.people_errors.retry_strategy` | text | N | How to handle retry (manual_fix, auto_retry, discard) | attribute | ENUM | column_registry.yml |
| 12 | `retry_after` | `people.people_errors.retry_after` | timestamp with time zone | Y | Earliest time to retry | attribute | ISO-8601 | inferred |
| 13 | `status` | `people.people_errors.status` | text | N | Current status of this record | attribute | ENUM | inferred |
| 14 | `created_at` | `people.people_errors.created_at` | timestamp with time zone | N | When the error was recorded | attribute | ISO-8601 | column_registry.yml |
| 15 | `last_updated_at` | `people.people_errors.last_updated_at` | timestamp with time zone | N | Timestamp for last updated event | attribute | ISO-8601 | inferred |
| 16 | `disposition` | `people.people_errors.disposition` | USER-DEFINED | Y | Disposition | attribute | STRING | inferred |
| 17 | `retry_count` | `people.people_errors.retry_count` | integer | Y | Number of retry attempts so far | metric | INTEGER | inferred |
| 18 | `max_retries` | `people.people_errors.max_retries` | integer | Y | Max Retries | attribute | INTEGER | inferred |
| 19 | `archived_at` | `people.people_errors.archived_at` | timestamp with time zone | Y | When this record was archived | attribute | ISO-8601 | inferred |
| 20 | `parked_at` | `people.people_errors.parked_at` | timestamp with time zone | Y | Timestamp for parked event | attribute | ISO-8601 | inferred |
| 21 | `parked_by` | `people.people_errors.parked_by` | text | Y | Parked By | attribute | STRING | inferred |
| 22 | `park_reason` | `people.people_errors.park_reason` | text | Y | Park Reason | attribute | STRING | inferred |
| 23 | `escalation_level` | `people.people_errors.escalation_level` | integer | Y | Escalation Level | attribute | INTEGER | inferred |
| 24 | `escalated_at` | `people.people_errors.escalated_at` | timestamp with time zone | Y | Timestamp for escalated event | attribute | ISO-8601 | inferred |
| 25 | `ttl_tier` | `people.people_errors.ttl_tier` | USER-DEFINED | Y | Ttl Tier | attribute | STRING | inferred |
| 26 | `last_retry_at` | `people.people_errors.last_retry_at` | timestamp with time zone | Y | Timestamp for last retry event | attribute | ISO-8601 | inferred |
| 27 | `next_retry_at` | `people.people_errors.next_retry_at` | timestamp with time zone | Y | Timestamp for next retry event | attribute | ISO-8601 | inferred |
| 28 | `retry_exhausted` | `people.people_errors.retry_exhausted` | boolean | Y | Retry Exhausted | attribute | BOOLEAN | inferred |

### `people.people_errors_archive` -- ARCHIVE -- 0 rows

**Hub**: `04.04.02` People Intelligence

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `error_id` | `people.people_errors_archive.error_id` | uuid | N | Primary key for this error record | identifier | UUID | inferred |
| 2 | `outreach_id` | `people.people_errors_archive.outreach_id` | uuid | Y | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 3 | `person_id` | `people.people_errors_archive.person_id` | uuid | Y | Person Id | identifier | UUID | inferred |
| 4 | `slot_id` | `people.people_errors_archive.slot_id` | uuid | Y | Primary key for this company slot record | identifier | UUID | inferred |
| 5 | `error_stage` | `people.people_errors_archive.error_stage` | character varying(50) | Y | Pipeline stage where error occurred | attribute | ENUM | inferred |
| 6 | `error_type` | `people.people_errors_archive.error_type` | character varying(50) | Y | Discriminator column classifying the error type | attribute | ENUM | inferred |
| 7 | `error_code` | `people.people_errors_archive.error_code` | character varying(50) | Y | Error Code | attribute | STRING | inferred |
| 8 | `error_message` | `people.people_errors_archive.error_message` | text | Y | Human-readable error description | attribute | STRING | inferred |
| 9 | `raw_payload` | `people.people_errors_archive.raw_payload` | jsonb | Y | Raw Payload | attribute | JSONB | inferred |
| 10 | `retry_strategy` | `people.people_errors_archive.retry_strategy` | character varying(50) | Y | How to handle retry (manual_fix, auto_retry, discard) | attribute | ENUM | inferred |
| 11 | `source_hints_used` | `people.people_errors_archive.source_hints_used` | jsonb | Y | Source Hints Used | attribute | JSONB | inferred |
| 12 | `status` | `people.people_errors_archive.status` | character varying(20) | Y | Current status of this record | attribute | ENUM | inferred |
| 13 | `created_at` | `people.people_errors_archive.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 14 | `last_updated_at` | `people.people_errors_archive.last_updated_at` | timestamp with time zone | Y | Timestamp for last updated event | attribute | ISO-8601 | inferred |
| 15 | `disposition` | `people.people_errors_archive.disposition` | USER-DEFINED | Y | Disposition | attribute | STRING | inferred |
| 16 | `retry_count` | `people.people_errors_archive.retry_count` | integer | Y | Number of retry attempts so far | metric | INTEGER | inferred |
| 17 | `max_retries` | `people.people_errors_archive.max_retries` | integer | Y | Max Retries | attribute | INTEGER | inferred |
| 18 | `parked_at` | `people.people_errors_archive.parked_at` | timestamp with time zone | Y | Timestamp for parked event | attribute | ISO-8601 | inferred |
| 19 | `parked_by` | `people.people_errors_archive.parked_by` | text | Y | Parked By | attribute | STRING | inferred |
| 20 | `park_reason` | `people.people_errors_archive.park_reason` | text | Y | Park Reason | attribute | STRING | inferred |
| 21 | `escalation_level` | `people.people_errors_archive.escalation_level` | integer | Y | Escalation Level | attribute | INTEGER | inferred |
| 22 | `escalated_at` | `people.people_errors_archive.escalated_at` | timestamp with time zone | Y | Timestamp for escalated event | attribute | ISO-8601 | inferred |
| 23 | `ttl_tier` | `people.people_errors_archive.ttl_tier` | USER-DEFINED | Y | Ttl Tier | attribute | STRING | inferred |
| 24 | `last_retry_at` | `people.people_errors_archive.last_retry_at` | timestamp with time zone | Y | Timestamp for last retry event | attribute | ISO-8601 | inferred |
| 25 | `retry_exhausted` | `people.people_errors_archive.retry_exhausted` | boolean | Y | Retry Exhausted | attribute | BOOLEAN | inferred |
| 26 | `archived_at` | `people.people_errors_archive.archived_at` | timestamp with time zone | N | When this record was archived | attribute | ISO-8601 | inferred |
| 27 | `archived_by` | `people.people_errors_archive.archived_by` | text | Y | Archived By | attribute | STRING | inferred |
| 28 | `archive_reason` | `people.people_errors_archive.archive_reason` | text | Y | Reason this record was archived | attribute | STRING | inferred |
| 29 | `final_disposition` | `people.people_errors_archive.final_disposition` | USER-DEFINED | Y | Final Disposition | attribute | STRING | inferred |
| 30 | `retention_expires_at` | `people.people_errors_archive.retention_expires_at` | timestamp with time zone | Y | Timestamp for retention expires event | attribute | ISO-8601 | inferred |

### `people.people_invalid` -- ERROR -- 21 rows

**Hub**: `04.04.02` People Intelligence

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `people.people_invalid.id` | bigint | N | Id | identifier | INTEGER | inferred |
| 2 | `unique_id` | `people.people_invalid.unique_id` | text | N | Primary identifier for this record (Barton ID format) | identifier | STRING | inferred |
| 3 | `full_name` | `people.people_invalid.full_name` | text | Y | Full Name | attribute | STRING | inferred |
| 4 | `first_name` | `people.people_invalid.first_name` | text | Y | Person first name | attribute | STRING | inferred |
| 5 | `last_name` | `people.people_invalid.last_name` | text | Y | Person last name | attribute | STRING | inferred |
| 6 | `email` | `people.people_invalid.email` | text | Y | Email address | attribute | EMAIL | inferred |
| 7 | `phone` | `people.people_invalid.phone` | text | Y | Phone number (E.164 format preferred) | attribute | STRING | inferred |
| 8 | `title` | `people.people_invalid.title` | text | Y | Job title or position | attribute | STRING | inferred |
| 9 | `company_name` | `people.people_invalid.company_name` | text | Y | Company legal or common name | attribute | STRING | inferred |
| 10 | `company_unique_id` | `people.people_invalid.company_unique_id` | text | Y | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 11 | `linkedin_url` | `people.people_invalid.linkedin_url` | text | Y | LinkedIn profile URL | attribute | URL | inferred |
| 12 | `city` | `people.people_invalid.city` | text | Y | City name | attribute | STRING | inferred |
| 13 | `state` | `people.people_invalid.state` | text | Y | US state code (2-letter) | attribute | ENUM | inferred |
| 14 | `validation_status` | `people.people_invalid.validation_status` | text | Y | Validation Status | attribute | STRING | inferred |
| 15 | `reason_code` | `people.people_invalid.reason_code` | text | N | Reason Code | attribute | STRING | inferred |
| 16 | `validation_errors` | `people.people_invalid.validation_errors` | jsonb | N | Validation Errors | attribute | JSONB | inferred |
| 17 | `validation_warnings` | `people.people_invalid.validation_warnings` | jsonb | Y | Validation Warnings | attribute | JSONB | inferred |
| 18 | `failed_at` | `people.people_invalid.failed_at` | timestamp without time zone | Y | Timestamp for failed event | attribute | ISO-8601 | inferred |
| 19 | `reviewed` | `people.people_invalid.reviewed` | boolean | Y | Reviewed | attribute | BOOLEAN | inferred |
| 20 | `batch_id` | `people.people_invalid.batch_id` | text | Y | Batch Id | identifier | STRING | inferred |
| 21 | `source_table` | `people.people_invalid.source_table` | text | Y | Source Table | attribute | STRING | inferred |
| 22 | `created_at` | `people.people_invalid.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 23 | `updated_at` | `people.people_invalid.updated_at` | timestamp without time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |
| 24 | `promoted_to` | `people.people_invalid.promoted_to` | text | Y | Promoted To | attribute | STRING | inferred |
| 25 | `promoted_at` | `people.people_invalid.promoted_at` | timestamp without time zone | Y | Timestamp for promoted event | attribute | ISO-8601 | inferred |
| 26 | `enrichment_data` | `people.people_invalid.enrichment_data` | jsonb | Y | Enrichment Data | attribute | JSONB | inferred |

### `people.people_master` -- SUPPORTING FROZEN -- 182,842 rows

**Hub**: `04.04.02` People Intelligence

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `unique_id` | `people.people_master.unique_id` | text | N | Barton person identifier (04.04.02.YY.NNNNNN.NNN format, immutable) | identifier | STRING | column_registry.yml |
| 2 | `company_unique_id` | `people.people_master.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 3 | `company_slot_unique_id` | `people.people_master.company_slot_unique_id` | text | N | FK to people.company_slot.slot_id | foreign_key | STRING | inferred |
| 4 | `first_name` | `people.people_master.first_name` | text | N | Person first name from Hunter, Clay, or manual enrichment | attribute | STRING | column_registry.yml |
| 5 | `last_name` | `people.people_master.last_name` | text | N | Person last name from Hunter, Clay, or manual enrichment | attribute | STRING | column_registry.yml |
| 6 | `full_name` | `people.people_master.full_name` | text | Y | Full Name | attribute | STRING | inferred |
| 7 | `title` | `people.people_master.title` | text | Y | Job title or position | attribute | STRING | inferred |
| 8 | `seniority` | `people.people_master.seniority` | text | Y | Seniority | attribute | STRING | inferred |
| 9 | `department` | `people.people_master.department` | text | Y | Department | attribute | STRING | inferred |
| 10 | `email` | `people.people_master.email` | text | Y | Person email address | attribute | EMAIL | column_registry.yml |
| 11 | `work_phone_e164` | `people.people_master.work_phone_e164` | text | Y | Phone number (E.164 format preferred) | attribute | STRING | inferred |
| 12 | `personal_phone_e164` | `people.people_master.personal_phone_e164` | text | Y | Personal Phone E164 | attribute | STRING | inferred |
| 13 | `linkedin_url` | `people.people_master.linkedin_url` | text | Y | Person LinkedIn profile URL | attribute | STRING | column_registry.yml |
| 14 | `twitter_url` | `people.people_master.twitter_url` | text | Y | Twitter URL | attribute | URL | inferred |
| 15 | `facebook_url` | `people.people_master.facebook_url` | text | Y | Facebook URL | attribute | URL | inferred |
| 16 | `bio` | `people.people_master.bio` | text | Y | Bio | attribute | STRING | inferred |
| 17 | `skills` | `people.people_master.skills` | ARRAY | Y | Skills | attribute | ARRAY | inferred |
| 18 | `education` | `people.people_master.education` | text | Y | Education | attribute | STRING | inferred |
| 19 | `certifications` | `people.people_master.certifications` | ARRAY | Y | Certifications | attribute | ARRAY | inferred |
| 20 | `source_system` | `people.people_master.source_system` | text | N | System that originated this record | attribute | STRING | inferred |
| 21 | `source_record_id` | `people.people_master.source_record_id` | text | Y | Source Record Id | identifier | STRING | inferred |
| 22 | `promoted_from_intake_at` | `people.people_master.promoted_from_intake_at` | timestamp with time zone | N | Timestamp for promoted from intake event | attribute | ISO-8601 | inferred |
| 23 | `promotion_audit_log_id` | `people.people_master.promotion_audit_log_id` | integer | Y | Promotion Audit Log Id | identifier | INTEGER | inferred |
| 24 | `created_at` | `people.people_master.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 25 | `updated_at` | `people.people_master.updated_at` | timestamp with time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |
| 26 | `email_verified` | `people.people_master.email_verified` | boolean | Y | Whether email was checked via Million Verifier (TRUE = checked) | attribute | BOOLEAN | column_registry.yml |
| 27 | `message_key_scheduled` | `people.people_master.message_key_scheduled` | text | Y | Message Key Scheduled | attribute | STRING | inferred |
| 28 | `email_verification_source` | `people.people_master.email_verification_source` | text | Y | Email Verification Source | attribute | EMAIL | inferred |
| 29 | `email_verified_at` | `people.people_master.email_verified_at` | timestamp with time zone | Y | Timestamp for email verified event | attribute | ISO-8601 | inferred |
| 30 | `validation_status` | `people.people_master.validation_status` | character varying | Y | Validation Status | attribute | STRING | inferred |
| 31 | `last_verified_at` | `people.people_master.last_verified_at` | timestamp without time zone | N | Timestamp for last verified event | attribute | ISO-8601 | inferred |
| 32 | `last_enrichment_attempt` | `people.people_master.last_enrichment_attempt` | timestamp without time zone | Y | Last Enrichment Attempt | attribute | ISO-8601 | inferred |
| 33 | `is_decision_maker` | `people.people_master.is_decision_maker` | boolean | Y | Whether this record decision maker | attribute | BOOLEAN | inferred |
| 34 | `outreach_ready` | `people.people_master.outreach_ready` | boolean | Y | Whether email is safe to send outreach (TRUE = VALID verified) | attribute | BOOLEAN | column_registry.yml |
| 35 | `outreach_ready_at` | `people.people_master.outreach_ready_at` | timestamp with time zone | Y | Timestamp for outreach ready event | attribute | ISO-8601 | inferred |

### `people.people_master_archive` -- ARCHIVE -- 47,486 rows

**Hub**: `04.04.02` People Intelligence

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `archived_at` | `people.people_master_archive.archived_at` | timestamp without time zone | N | When this record was archived | attribute | ISO-8601 | inferred |
| 2 | `archive_reason` | `people.people_master_archive.archive_reason` | text | Y | Reason this record was archived | attribute | STRING | inferred |
| 3 | `unique_id` | `people.people_master_archive.unique_id` | text | Y | Primary identifier for this record (Barton ID format) | identifier | STRING | inferred |
| 4 | `company_unique_id` | `people.people_master_archive.company_unique_id` | text | Y | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 5 | `company_slot_unique_id` | `people.people_master_archive.company_slot_unique_id` | text | Y | FK to people.company_slot.slot_id | foreign_key | STRING | inferred |
| 6 | `first_name` | `people.people_master_archive.first_name` | text | Y | Person first name | attribute | STRING | inferred |
| 7 | `last_name` | `people.people_master_archive.last_name` | text | Y | Person last name | attribute | STRING | inferred |
| 8 | `full_name` | `people.people_master_archive.full_name` | text | Y | Full Name | attribute | STRING | inferred |
| 9 | `title` | `people.people_master_archive.title` | text | Y | Job title or position | attribute | STRING | inferred |
| 10 | `seniority` | `people.people_master_archive.seniority` | text | Y | Seniority | attribute | STRING | inferred |
| 11 | `department` | `people.people_master_archive.department` | text | Y | Department | attribute | STRING | inferred |
| 12 | `email` | `people.people_master_archive.email` | text | Y | Email address | attribute | EMAIL | inferred |
| 13 | `work_phone_e164` | `people.people_master_archive.work_phone_e164` | text | Y | Phone number (E.164 format preferred) | attribute | STRING | inferred |
| 14 | `personal_phone_e164` | `people.people_master_archive.personal_phone_e164` | text | Y | Personal Phone E164 | attribute | STRING | inferred |
| 15 | `linkedin_url` | `people.people_master_archive.linkedin_url` | text | Y | LinkedIn profile URL | attribute | URL | inferred |
| 16 | `twitter_url` | `people.people_master_archive.twitter_url` | text | Y | Twitter URL | attribute | URL | inferred |
| 17 | `facebook_url` | `people.people_master_archive.facebook_url` | text | Y | Facebook URL | attribute | URL | inferred |
| 18 | `bio` | `people.people_master_archive.bio` | text | Y | Bio | attribute | STRING | inferred |
| 19 | `skills` | `people.people_master_archive.skills` | ARRAY | Y | Skills | attribute | ARRAY | inferred |
| 20 | `education` | `people.people_master_archive.education` | text | Y | Education | attribute | STRING | inferred |
| 21 | `certifications` | `people.people_master_archive.certifications` | ARRAY | Y | Certifications | attribute | ARRAY | inferred |
| 22 | `source_system` | `people.people_master_archive.source_system` | text | Y | System that originated this record | attribute | STRING | inferred |
| 23 | `source_record_id` | `people.people_master_archive.source_record_id` | text | Y | Source Record Id | identifier | STRING | inferred |
| 24 | `promoted_from_intake_at` | `people.people_master_archive.promoted_from_intake_at` | timestamp without time zone | Y | Timestamp for promoted from intake event | attribute | ISO-8601 | inferred |
| 25 | `promotion_audit_log_id` | `people.people_master_archive.promotion_audit_log_id` | integer | Y | Promotion Audit Log Id | identifier | INTEGER | inferred |
| 26 | `created_at` | `people.people_master_archive.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 27 | `updated_at` | `people.people_master_archive.updated_at` | timestamp without time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |
| 28 | `email_verified` | `people.people_master_archive.email_verified` | boolean | Y | Whether email was verified via Million Verifier | attribute | BOOLEAN | inferred |
| 29 | `message_key_scheduled` | `people.people_master_archive.message_key_scheduled` | text | Y | Message Key Scheduled | attribute | STRING | inferred |
| 30 | `email_verification_source` | `people.people_master_archive.email_verification_source` | text | Y | Email Verification Source | attribute | EMAIL | inferred |
| 31 | `email_verified_at` | `people.people_master_archive.email_verified_at` | timestamp without time zone | Y | Timestamp for email verified event | attribute | ISO-8601 | inferred |
| 32 | `validation_status` | `people.people_master_archive.validation_status` | character varying | Y | Validation Status | attribute | STRING | inferred |
| 33 | `last_verified_at` | `people.people_master_archive.last_verified_at` | timestamp without time zone | Y | Timestamp for last verified event | attribute | ISO-8601 | inferred |
| 34 | `last_enrichment_attempt` | `people.people_master_archive.last_enrichment_attempt` | timestamp without time zone | Y | Last Enrichment Attempt | attribute | ISO-8601 | inferred |
| 35 | `is_decision_maker` | `people.people_master_archive.is_decision_maker` | boolean | Y | Whether this record decision maker | attribute | BOOLEAN | inferred |

### `people.people_promotion_audit` -- SYSTEM -- 9 rows

**Hub**: `04.04.02` People Intelligence

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `audit_id` | `people.people_promotion_audit.audit_id` | integer | N | Audit Id | identifier | INTEGER | inferred |
| 2 | `run_id` | `people.people_promotion_audit.run_id` | text | N | Run Id | identifier | STRING | inferred |
| 3 | `resolution_status` | `people.people_promotion_audit.resolution_status` | text | N | Resolution Status | attribute | STRING | inferred |
| 4 | `role` | `people.people_promotion_audit.role` | text | Y | Role | attribute | STRING | inferred |
| 5 | `count` | `people.people_promotion_audit.count` | integer | Y | Count | attribute | INTEGER | inferred |
| 6 | `created_at` | `people.people_promotion_audit.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

### `people.people_resolution_history` -- SYSTEM -- 0 rows

**Hub**: `04.04.02` People Intelligence

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `history_id` | `people.people_resolution_history.history_id` | uuid | N | History Id | identifier | UUID | inferred |
| 2 | `outreach_id` | `people.people_resolution_history.outreach_id` | uuid | N | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 3 | `slot_type` | `people.people_resolution_history.slot_type` | character varying(20) | N | Executive role type (CEO, CFO, HR, CTO, CMO, COO) | attribute | ENUM | inferred |
| 4 | `person_identifier` | `people.people_resolution_history.person_identifier` | text | N | Person Identifier | attribute | STRING | inferred |
| 5 | `resolution_outcome` | `people.people_resolution_history.resolution_outcome` | character varying(30) | N | Resolution Outcome | attribute | STRING | inferred |
| 6 | `rejection_reason` | `people.people_resolution_history.rejection_reason` | text | Y | Rejection Reason | attribute | STRING | inferred |
| 7 | `confidence_score` | `people.people_resolution_history.confidence_score` | numeric | Y | Confidence score (0-100) | metric | NUMERIC | inferred |
| 8 | `source` | `people.people_resolution_history.source` | character varying(50) | Y | Data source identifier | attribute | STRING | inferred |
| 9 | `source_response` | `people.people_resolution_history.source_response` | jsonb | Y | Source Response | attribute | JSONB | inferred |
| 10 | `checked_at` | `people.people_resolution_history.checked_at` | timestamp with time zone | Y | When this record was last checked/verified | attribute | ISO-8601 | inferred |
| 11 | `process_id` | `people.people_resolution_history.process_id` | uuid | Y | Process Id | identifier | UUID | inferred |
| 12 | `correlation_id` | `people.people_resolution_history.correlation_id` | uuid | Y | UUID linking related operations across tables | identifier | UUID | inferred |
| 13 | `created_at` | `people.people_resolution_history.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

### `people.people_resolution_queue` -- STAGING -- 1,206 rows

**Hub**: `04.04.02` People Intelligence

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `queue_id` | `people.people_resolution_queue.queue_id` | integer | N | Queue Id | identifier | INTEGER | inferred |
| 2 | `company_unique_id` | `people.people_resolution_queue.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 3 | `company_slot_unique_id` | `people.people_resolution_queue.company_slot_unique_id` | text | N | FK to people.company_slot.slot_id | foreign_key | STRING | inferred |
| 4 | `slot_type` | `people.people_resolution_queue.slot_type` | text | Y | Executive role type (CEO, CFO, HR, CTO, CMO, COO) | attribute | ENUM | inferred |
| 5 | `existing_email` | `people.people_resolution_queue.existing_email` | text | Y | Existing Email | attribute | EMAIL | inferred |
| 6 | `issue_type` | `people.people_resolution_queue.issue_type` | text | N | Issue Type | attribute | STRING | inferred |
| 7 | `priority` | `people.people_resolution_queue.priority` | integer | Y | Priority | attribute | INTEGER | inferred |
| 8 | `status` | `people.people_resolution_queue.status` | text | Y | Current status of this record | attribute | ENUM | inferred |
| 9 | `resolved_contact_id` | `people.people_resolution_queue.resolved_contact_id` | text | Y | Resolved Contact Id | identifier | STRING | inferred |
| 10 | `created_at` | `people.people_resolution_queue.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 11 | `last_touched_at` | `people.people_resolution_queue.last_touched_at` | timestamp without time zone | Y | Timestamp for last touched event | attribute | ISO-8601 | inferred |
| 12 | `resolved_at` | `people.people_resolution_queue.resolved_at` | timestamp without time zone | Y | When this error/issue was resolved | attribute | ISO-8601 | inferred |
| 13 | `touched_by` | `people.people_resolution_queue.touched_by` | text | Y | Touched By | attribute | STRING | inferred |
| 14 | `assigned_to` | `people.people_resolution_queue.assigned_to` | text | Y | Assigned To | attribute | STRING | inferred |
| 15 | `notes` | `people.people_resolution_queue.notes` | text | Y | Human-readable notes | attribute | STRING | inferred |
| 16 | `error_details` | `people.people_resolution_queue.error_details` | jsonb | Y | Error Details | attribute | JSONB | inferred |
| 17 | `attempt_count` | `people.people_resolution_queue.attempt_count` | integer | Y | Count of attempt | metric | INTEGER | inferred |

### `people.people_sidecar` -- SUPPORTING -- 0 rows

**Hub**: `04.04.02` People Intelligence

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `person_unique_id` | `people.people_sidecar.person_unique_id` | character varying(50) | N | FK to people.people_master.unique_id (Barton person ID) | foreign_key | STRING | inferred |
| 2 | `clay_insight_summary` | `people.people_sidecar.clay_insight_summary` | text | Y | Clay Insight Summary | attribute | STRING | inferred |
| 3 | `clay_segments` | `people.people_sidecar.clay_segments` | ARRAY | Y | Clay Segments | attribute | ARRAY | inferred |
| 4 | `social_profiles` | `people.people_sidecar.social_profiles` | jsonb | Y | Social Profiles | attribute | JSONB | inferred |
| 5 | `enrichment_payload` | `people.people_sidecar.enrichment_payload` | jsonb | Y | Enrichment Payload | attribute | JSONB | inferred |
| 6 | `last_enriched_at` | `people.people_sidecar.last_enriched_at` | timestamp without time zone | Y | Timestamp for last enriched event | attribute | ISO-8601 | inferred |
| 7 | `enrichment_source` | `people.people_sidecar.enrichment_source` | text | Y | Enrichment Source | attribute | STRING | inferred |
| 8 | `confidence_score` | `people.people_sidecar.confidence_score` | numeric | Y | Confidence score (0-100) | metric | NUMERIC | inferred |
| 9 | `created_at` | `people.people_sidecar.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 10 | `updated_at` | `people.people_sidecar.updated_at` | timestamp without time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |

### `people.person_movement_history` -- SYSTEM -- 0 rows

**Hub**: `04.04.02` People Intelligence

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `people.person_movement_history.id` | integer | N | Id | identifier | INTEGER | inferred |
| 2 | `person_unique_id` | `people.person_movement_history.person_unique_id` | text | N | FK to people.people_master.unique_id (Barton person ID) | foreign_key | STRING | inferred |
| 3 | `linkedin_url` | `people.person_movement_history.linkedin_url` | text | Y | LinkedIn profile URL | attribute | URL | inferred |
| 4 | `company_from_id` | `people.person_movement_history.company_from_id` | text | N | Company From Id | identifier | STRING | inferred |
| 5 | `company_to_id` | `people.person_movement_history.company_to_id` | text | Y | Company To Id | identifier | STRING | inferred |
| 6 | `title_from` | `people.person_movement_history.title_from` | text | N | Title From | attribute | STRING | inferred |
| 7 | `title_to` | `people.person_movement_history.title_to` | text | Y | Title To | attribute | STRING | inferred |
| 8 | `movement_type` | `people.person_movement_history.movement_type` | text | N | Movement Type | attribute | STRING | inferred |
| 9 | `detected_at` | `people.person_movement_history.detected_at` | timestamp without time zone | N | When this event/signal was detected | attribute | ISO-8601 | inferred |
| 10 | `raw_payload` | `people.person_movement_history.raw_payload` | jsonb | Y | Raw Payload | attribute | JSONB | inferred |
| 11 | `created_at` | `people.person_movement_history.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

### `people.person_scores` -- SUPPORTING -- 0 rows

**Hub**: `04.04.02` People Intelligence

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `people.person_scores.id` | integer | N | Id | identifier | INTEGER | inferred |
| 2 | `person_unique_id` | `people.person_scores.person_unique_id` | text | N | FK to people.people_master.unique_id (Barton person ID) | foreign_key | STRING | inferred |
| 3 | `bit_score` | `people.person_scores.bit_score` | integer | Y | BIT/CLS authorization score | metric | INTEGER | inferred |
| 4 | `confidence_score` | `people.person_scores.confidence_score` | integer | Y | Confidence score (0-100) | metric | INTEGER | inferred |
| 5 | `calculated_at` | `people.person_scores.calculated_at` | timestamp without time zone | N | Timestamp for calculated event | attribute | ISO-8601 | inferred |
| 6 | `score_factors` | `people.person_scores.score_factors` | jsonb | Y | Score Factors | attribute | JSONB | inferred |
| 7 | `created_at` | `people.person_scores.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 8 | `updated_at` | `people.person_scores.updated_at` | timestamp without time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |

### `people.pressure_signals` -- MV -- 0 rows

**Hub**: `04.04.02` People Intelligence

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `signal_id` | `people.pressure_signals.signal_id` | uuid | N | Signal Id | identifier | UUID | inferred |
| 2 | `company_unique_id` | `people.pressure_signals.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 3 | `signal_type` | `people.pressure_signals.signal_type` | character varying(50) | N | Signal Type | attribute | STRING | inferred |
| 4 | `pressure_domain` | `people.pressure_signals.pressure_domain` | USER-DEFINED | N | Pressure Domain | attribute | STRING | inferred |
| 5 | `pressure_class` | `people.pressure_signals.pressure_class` | USER-DEFINED | Y | Pressure Class | attribute | STRING | inferred |
| 6 | `signal_value` | `people.pressure_signals.signal_value` | jsonb | N | Signal Value | attribute | JSONB | inferred |
| 7 | `magnitude` | `people.pressure_signals.magnitude` | integer | N | Magnitude | attribute | INTEGER | inferred |
| 8 | `detected_at` | `people.pressure_signals.detected_at` | timestamp with time zone | N | When this event/signal was detected | attribute | ISO-8601 | inferred |
| 9 | `expires_at` | `people.pressure_signals.expires_at` | timestamp with time zone | N | When this record expires | attribute | ISO-8601 | inferred |
| 10 | `correlation_id` | `people.pressure_signals.correlation_id` | uuid | Y | UUID linking related operations across tables | identifier | UUID | inferred |
| 11 | `source_record_id` | `people.pressure_signals.source_record_id` | text | Y | Source Record Id | identifier | STRING | inferred |
| 12 | `created_at` | `people.pressure_signals.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |

### `people.slot_assignment_history` -- SYSTEM -- 1,370 rows

**Hub**: `04.04.02` People Intelligence

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `history_id` | `people.slot_assignment_history.history_id` | bigint | N | History Id | identifier | INTEGER | inferred |
| 2 | `event_type` | `people.slot_assignment_history.event_type` | text | N | Type of audit/system event | attribute | STRING | inferred |
| 3 | `company_slot_unique_id` | `people.slot_assignment_history.company_slot_unique_id` | text | N | FK to people.company_slot.slot_id | foreign_key | STRING | inferred |
| 4 | `company_unique_id` | `people.slot_assignment_history.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 5 | `slot_type` | `people.slot_assignment_history.slot_type` | text | N | Executive role type (CEO, CFO, HR, CTO, CMO, COO) | attribute | ENUM | inferred |
| 6 | `person_unique_id` | `people.slot_assignment_history.person_unique_id` | text | Y | FK to people.people_master.unique_id (Barton person ID) | foreign_key | STRING | inferred |
| 7 | `confidence_score` | `people.slot_assignment_history.confidence_score` | numeric | Y | Confidence score (0-100) | metric | NUMERIC | inferred |
| 8 | `displaced_by_person_id` | `people.slot_assignment_history.displaced_by_person_id` | text | Y | Displaced By Person Id | identifier | STRING | inferred |
| 9 | `displacement_reason` | `people.slot_assignment_history.displacement_reason` | text | Y | Displacement Reason | attribute | STRING | inferred |
| 10 | `source_system` | `people.slot_assignment_history.source_system` | text | N | System that originated this record | attribute | STRING | inferred |
| 11 | `event_ts` | `people.slot_assignment_history.event_ts` | timestamp with time zone | N | Event Ts | attribute | ISO-8601 | inferred |
| 12 | `created_at` | `people.slot_assignment_history.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 13 | `original_filled_at` | `people.slot_assignment_history.original_filled_at` | timestamp with time zone | Y | Timestamp for original filled event | attribute | ISO-8601 | inferred |
| 14 | `tenure_days` | `people.slot_assignment_history.tenure_days` | integer | Y | Tenure Days | attribute | INTEGER | inferred |
| 15 | `event_metadata` | `people.slot_assignment_history.event_metadata` | jsonb | N | Event Metadata | attribute | JSONB | inferred |

### `people.slot_ingress_control` -- REGISTRY -- 1 rows

**Hub**: `04.04.02` People Intelligence

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `switch_id` | `people.slot_ingress_control.switch_id` | uuid | N | Switch Id | identifier | UUID | inferred |
| 2 | `switch_name` | `people.slot_ingress_control.switch_name` | character varying(50) | N | Switch Name | attribute | STRING | inferred |
| 3 | `is_enabled` | `people.slot_ingress_control.is_enabled` | boolean | N | Whether this record enabled | attribute | BOOLEAN | inferred |
| 4 | `description` | `people.slot_ingress_control.description` | text | Y | Description | attribute | STRING | inferred |
| 5 | `enabled_by` | `people.slot_ingress_control.enabled_by` | character varying(100) | Y | Enabled By | attribute | STRING | inferred |
| 6 | `enabled_at` | `people.slot_ingress_control.enabled_at` | timestamp with time zone | Y | Timestamp for enabled event | attribute | ISO-8601 | inferred |
| 7 | `disabled_by` | `people.slot_ingress_control.disabled_by` | character varying(100) | Y | Disabled By | attribute | STRING | inferred |
| 8 | `disabled_at` | `people.slot_ingress_control.disabled_at` | timestamp with time zone | Y | Timestamp for disabled event | attribute | ISO-8601 | inferred |
| 9 | `created_at` | `people.slot_ingress_control.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |

### `people.slot_orphan_snapshot_r0_002` -- ARCHIVE -- 1,053 rows

**Hub**: `04.04.02` People Intelligence

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `snapshot_id` | `people.slot_orphan_snapshot_r0_002.snapshot_id` | integer | N | Snapshot Id | identifier | INTEGER | inferred |
| 2 | `company_slot_unique_id` | `people.slot_orphan_snapshot_r0_002.company_slot_unique_id` | text | N | FK to people.company_slot.slot_id | foreign_key | STRING | inferred |
| 3 | `company_unique_id` | `people.slot_orphan_snapshot_r0_002.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 4 | `slot_type` | `people.slot_orphan_snapshot_r0_002.slot_type` | text | N | Executive role type (CEO, CFO, HR, CTO, CMO, COO) | attribute | ENUM | inferred |
| 5 | `original_outreach_id` | `people.slot_orphan_snapshot_r0_002.original_outreach_id` | uuid | Y | Original Outreach Id | identifier | UUID | inferred |
| 6 | `derived_outreach_id` | `people.slot_orphan_snapshot_r0_002.derived_outreach_id` | uuid | Y | Derived Outreach Id | identifier | UUID | inferred |
| 7 | `derivation_status` | `people.slot_orphan_snapshot_r0_002.derivation_status` | text | Y | Derivation Status | attribute | STRING | inferred |
| 8 | `snapshot_at` | `people.slot_orphan_snapshot_r0_002.snapshot_at` | timestamp with time zone | Y | Timestamp for snapshot event | attribute | ISO-8601 | inferred |

### `people.slot_quarantine_r0_002` -- ARCHIVE -- 75 rows

**Hub**: `04.04.02` People Intelligence

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `quarantine_id` | `people.slot_quarantine_r0_002.quarantine_id` | integer | N | Quarantine Id | identifier | INTEGER | inferred |
| 2 | `company_slot_unique_id` | `people.slot_quarantine_r0_002.company_slot_unique_id` | text | N | FK to people.company_slot.slot_id | foreign_key | STRING | inferred |
| 3 | `company_unique_id` | `people.slot_quarantine_r0_002.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 4 | `slot_type` | `people.slot_quarantine_r0_002.slot_type` | text | N | Executive role type (CEO, CFO, HR, CTO, CMO, COO) | attribute | ENUM | inferred |
| 5 | `quarantine_reason` | `people.slot_quarantine_r0_002.quarantine_reason` | text | N | Quarantine Reason | attribute | STRING | inferred |
| 6 | `quarantined_at` | `people.slot_quarantine_r0_002.quarantined_at` | timestamp with time zone | Y | Timestamp for quarantined event | attribute | ISO-8601 | inferred |

### `people.title_slot_mapping` -- REGISTRY -- 43 rows

**Hub**: `04.04.02` People Intelligence

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `people.title_slot_mapping.id` | integer | N | Id | identifier | INTEGER | inferred |
| 2 | `title_pattern` | `people.title_slot_mapping.title_pattern` | character varying(100) | N | Title Pattern | attribute | STRING | inferred |
| 3 | `slot_type` | `people.title_slot_mapping.slot_type` | character varying(20) | N | Executive role type (CEO, CFO, HR, CTO, CMO, COO) | attribute | ENUM | inferred |
| 4 | `priority` | `people.title_slot_mapping.priority` | integer | Y | Priority | attribute | INTEGER | inferred |
| 5 | `created_at` | `people.title_slot_mapping.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

---

## `04.04.03` DOL Filings

**Tables**: 37 | **Total rows**: 11,301,618

### `dol.column_metadata` -- REGISTRY -- 1,081 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `dol.column_metadata.id` | integer | N | Id | identifier | INTEGER | inferred |
| 2 | `table_name` | `dol.column_metadata.table_name` | character varying(50) | N | Table Name | attribute | STRING | inferred |
| 3 | `column_name` | `dol.column_metadata.column_name` | character varying(100) | N | Column Name | attribute | STRING | inferred |
| 4 | `column_id` | `dol.column_metadata.column_id` | character varying(100) | N | Column Id | identifier | STRING | inferred |
| 5 | `description` | `dol.column_metadata.description` | text | N | Description | attribute | STRING | inferred |
| 6 | `category` | `dol.column_metadata.category` | character varying(50) | Y | Category | attribute | STRING | inferred |
| 7 | `data_type` | `dol.column_metadata.data_type` | character varying(50) | N | Data Type | attribute | STRING | inferred |
| 8 | `format_pattern` | `dol.column_metadata.format_pattern` | character varying(100) | Y | Format Pattern | attribute | STRING | inferred |
| 9 | `max_length` | `dol.column_metadata.max_length` | integer | Y | Max Length | attribute | INTEGER | inferred |
| 10 | `search_keywords` | `dol.column_metadata.search_keywords` | ARRAY | Y | Search Keywords | attribute | ARRAY | inferred |
| 11 | `is_pii` | `dol.column_metadata.is_pii` | boolean | Y | Whether this record pii | attribute | BOOLEAN | inferred |
| 12 | `is_searchable` | `dol.column_metadata.is_searchable` | boolean | Y | Whether this record searchable | attribute | BOOLEAN | inferred |
| 13 | `example_values` | `dol.column_metadata.example_values` | ARRAY | Y | Example Values | attribute | ARRAY | inferred |
| 14 | `created_at` | `dol.column_metadata.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

### `dol.ein_urls` -- CANONICAL -- 127,909 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `ein` | `dol.ein_urls.ein` | character varying(9) | N | Employer Identification Number (9-digit, no dashes) | attribute | STRING | inferred |
| 2 | `company_name` | `dol.ein_urls.company_name` | text | N | Company legal or common name | attribute | STRING | inferred |
| 3 | `city` | `dol.ein_urls.city` | text | Y | City name | attribute | STRING | inferred |
| 4 | `state` | `dol.ein_urls.state` | character varying(2) | Y | US state code (2-letter) | attribute | ENUM | inferred |
| 5 | `domain` | `dol.ein_urls.domain` | text | Y | Company website domain (lowercase, no protocol) | attribute | STRING | inferred |
| 6 | `url` | `dol.ein_urls.url` | text | Y | Url | attribute | URL | inferred |
| 7 | `discovered_at` | `dol.ein_urls.discovered_at` | timestamp without time zone | Y | Timestamp for discovered event | attribute | ISO-8601 | inferred |
| 8 | `discovery_method` | `dol.ein_urls.discovery_method` | text | Y | Discovery Method | attribute | STRING | inferred |
| 9 | `normalized_domain` | `dol.ein_urls.normalized_domain` | text | Y | Normalized Domain | attribute | STRING | inferred |

### `dol.form_5500` -- CANONICAL -- 432,582 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `filing_id` | `dol.form_5500.filing_id` | uuid | N | Unique filing identifier (UUID) / ID: DOL_F5500_FILING_ID / Format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | attribute | UUID | dol.column_metadata |
| 2 | `ack_id` | `dol.form_5500.ack_id` | character varying(255) | N | DOL acknowledgment ID for the filing / ID: DOL_F5500_ACK_ID / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 3 | `company_unique_id` | `dol.form_5500.company_unique_id` | text | Y | Company unique id / ID: DOL_F5500_COMPANY_UNIQUE_ID / Format: Variable length text | attribute | STRING | dol.column_metadata |
| 4 | `sponsor_dfe_ein` | `dol.form_5500.sponsor_dfe_ein` | character varying(20) | N | Employer Identification Number of sponsor / ID: DOL_F5500_SPONSOR_DFE_EIN / Format: 9 digits (XX-XXXXXXX) | identifier | STRING | dol.column_metadata |
| 5 | `sponsor_dfe_name` | `dol.form_5500.sponsor_dfe_name` | character varying(500) | N | Legal name of the plan sponsor or DFE / ID: DOL_F5500_SPONSOR_DFE_NAME / Format: Up to 500 characters | attribute | STRING | dol.column_metadata |
| 6 | `spons_dfe_dba_name` | `dol.form_5500.spons_dfe_dba_name` | character varying(500) | Y | Plan Sponsor dfe dba (name) / ID: DOL_F5500_SPONS_DFE_DBA_NAME / Format: Up to 500 characters | attribute | STRING | dol.column_metadata |
| 7 | `plan_name` | `dol.form_5500.plan_name` | character varying(500) | Y | Official name of the benefit plan / ID: DOL_F5500_PLAN_NAME / Format: Up to 500 characters | attribute | STRING | dol.column_metadata |
| 8 | `plan_number` | `dol.form_5500.plan_number` | character varying(20) | Y | Plan number / ID: DOL_F5500_PLAN_NUMBER / Format: Up to 20 characters | attribute | STRING | dol.column_metadata |
| 9 | `plan_eff_date` | `dol.form_5500.plan_eff_date` | character varying(20) | Y | Plan effective date / ID: DOL_F5500_PLAN_EFF_DATE / Format: YYYY-MM-DD | attribute | STRING | dol.column_metadata |
| 10 | `spons_dfe_mail_us_city` | `dol.form_5500.spons_dfe_mail_us_city` | character varying(100) | Y | Sponsor mailing city / ID: DOL_F5500_SPONS_DFE_MAIL_US_CITY / Format: Up to 100 characters | attribute | STRING | dol.column_metadata |
| 11 | `spons_dfe_mail_us_state` | `dol.form_5500.spons_dfe_mail_us_state` | character varying(10) | Y | Sponsor mailing state (2-letter) / ID: DOL_F5500_SPONS_DFE_MAIL_US_STATE / Format: Up to 10 characters | attribute | STRING | dol.column_metadata |
| 12 | `spons_dfe_mail_us_zip` | `dol.form_5500.spons_dfe_mail_us_zip` | character varying(20) | Y | Sponsor mailing ZIP code / ID: DOL_F5500_SPONS_DFE_MAIL_US_ZIP / Format: 5 or 9 digits | attribute | STRING | dol.column_metadata |
| 13 | `tot_active_partcp_cnt` | `dol.form_5500.tot_active_partcp_cnt` | integer | Y | Total active participants / ID: DOL_F5500_TOT_ACTIVE_PARTCP_CNT / Format: Whole number | attribute | INTEGER | dol.column_metadata |
| 14 | `tot_partcp_boy_cnt` | `dol.form_5500.tot_partcp_boy_cnt` | integer | Y | Total participants at beginning of year / ID: DOL_F5500_TOT_PARTCP_BOY_CNT / Format: Whole number | attribute | INTEGER | dol.column_metadata |
| 15 | `sch_a_attached_ind` | `dol.form_5500.sch_a_attached_ind` | character varying(5) | Y | Schedule A attached (indicator flag) / ID: DOL_F5500_SCH_A_ATTACHED_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 16 | `num_sch_a_attached_cnt` | `dol.form_5500.num_sch_a_attached_cnt` | integer | Y | Num sch a attached (count/number) / ID: DOL_F5500_NUM_SCH_A_ATTACHED_CNT / Format: Whole number | attribute | INTEGER | dol.column_metadata |
| 17 | `admin_name` | `dol.form_5500.admin_name` | character varying(255) | Y | Plan Administrator name / ID: DOL_F5500_ADMIN_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 18 | `admin_ein` | `dol.form_5500.admin_ein` | character varying(20) | Y | Plan Administrator ein / ID: DOL_F5500_ADMIN_EIN / Format: 9 digits (XX-XXXXXXX) | identifier | STRING | dol.column_metadata |
| 19 | `form_plan_year_begin_date` | `dol.form_5500.form_plan_year_begin_date` | character varying(20) | Y | Form plan year begin (date) / ID: DOL_F5500_FORM_PLAN_YEAR_BEGIN_DATE / Format: YYYY-MM-DD | attribute | STRING | dol.column_metadata |
| 20 | `form_year` | `dol.form_5500.form_year` | character varying(10) | Y | Tax/plan year for this filing / ID: DOL_F5500_FORM_YEAR / Format: Up to 10 characters | attribute | STRING | dol.column_metadata |
| 21 | `filing_status` | `dol.form_5500.filing_status` | character varying(50) | Y | Filing status / ID: DOL_F5500_FILING_STATUS / Format: Up to 50 characters | attribute | STRING | dol.column_metadata |
| 22 | `date_received` | `dol.form_5500.date_received` | character varying(30) | Y | Date filing was received by DOL / ID: DOL_F5500_DATE_RECEIVED / Format: Up to 30 characters | attribute | STRING | dol.column_metadata |
| 23 | `created_at` | `dol.form_5500.created_at` | timestamp with time zone | N | Record creation timestamp / ID: DOL_F5500_CREATED_AT / Format: YYYY-MM-DD HH:MM:SS | attribute | ISO-8601 | dol.column_metadata |
| 24 | `updated_at` | `dol.form_5500.updated_at` | timestamp with time zone | N | Record last update timestamp / ID: DOL_F5500_UPDATED_AT / Format: YYYY-MM-DD HH:MM:SS | attribute | ISO-8601 | dol.column_metadata |
| 25 | `form_tax_prd` | `dol.form_5500.form_tax_prd` | character varying(255) | Y | Form tax prd / ID: DOL_F5500_FORM_TAX_PRD / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 26 | `type_plan_entity_cd` | `dol.form_5500.type_plan_entity_cd` | character varying(255) | Y | Type of plan entity code / ID: DOL_F5500_TYPE_PLAN_ENTITY_CD / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 27 | `type_dfe_plan_entity_cd` | `dol.form_5500.type_dfe_plan_entity_cd` | character varying(255) | Y | Type of DFE plan entity code / ID: DOL_F5500_TYPE_DFE_PLAN_ENTITY_CD / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 28 | `initial_filing_ind` | `dol.form_5500.initial_filing_ind` | character varying(5) | Y | Initial filing (indicator flag) / ID: DOL_F5500_INITIAL_FILING_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 29 | `amended_ind` | `dol.form_5500.amended_ind` | character varying(5) | Y | Amended (indicator flag) / ID: DOL_F5500_AMENDED_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 30 | `final_filing_ind` | `dol.form_5500.final_filing_ind` | character varying(5) | Y | Final filing (indicator flag) / ID: DOL_F5500_FINAL_FILING_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 31 | `short_plan_yr_ind` | `dol.form_5500.short_plan_yr_ind` | character varying(5) | Y | Short plan yr (indicator flag) / ID: DOL_F5500_SHORT_PLAN_YR_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 32 | `collective_bargain_ind` | `dol.form_5500.collective_bargain_ind` | character varying(5) | Y | Collective bargain (indicator flag) / ID: DOL_F5500_COLLECTIVE_BARGAIN_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 33 | `f5558_application_filed_ind` | `dol.form_5500.f5558_application_filed_ind` | character varying(5) | Y | F5558 application filed (indicator flag) / ID: DOL_F5500_F5558_APPLICATION_FILED_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 34 | `ext_automatic_ind` | `dol.form_5500.ext_automatic_ind` | character varying(5) | Y | Ext automatic (indicator flag) / ID: DOL_F5500_EXT_AUTOMATIC_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 35 | `dfvc_program_ind` | `dol.form_5500.dfvc_program_ind` | character varying(5) | Y | Dfvc program (indicator flag) / ID: DOL_F5500_DFVC_PROGRAM_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 36 | `ext_special_ind` | `dol.form_5500.ext_special_ind` | character varying(5) | Y | Ext special (indicator flag) / ID: DOL_F5500_EXT_SPECIAL_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 37 | `ext_special_text` | `dol.form_5500.ext_special_text` | text | Y | Ext special (text description) / ID: DOL_F5500_EXT_SPECIAL_TEXT / Format: Variable length text | attribute | STRING | dol.column_metadata |
| 38 | `spons_dfe_pn` | `dol.form_5500.spons_dfe_pn` | character varying(255) | Y | Plan Sponsor dfe pn / ID: DOL_F5500_SPONS_DFE_PN / Format: Up to 255 characters | identifier | STRING | dol.column_metadata |
| 39 | `spons_dfe_care_of_name` | `dol.form_5500.spons_dfe_care_of_name` | character varying(255) | Y | Plan Sponsor dfe care of (name) / ID: DOL_F5500_SPONS_DFE_CARE_OF_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 40 | `spons_dfe_mail_us_address1` | `dol.form_5500.spons_dfe_mail_us_address1` | character varying(255) | Y | Sponsor mailing address line 1 / ID: DOL_F5500_SPONS_DFE_MAIL_US_ADDRESS1 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 41 | `spons_dfe_mail_us_address2` | `dol.form_5500.spons_dfe_mail_us_address2` | character varying(255) | Y | Sponsor mailing address line 2 / ID: DOL_F5500_SPONS_DFE_MAIL_US_ADDRESS2 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 42 | `spons_dfe_mail_foreign_addr1` | `dol.form_5500.spons_dfe_mail_foreign_addr1` | character varying(255) | Y | Plan Sponsor dfe mail foreign addr1 / ID: DOL_F5500_SPONS_DFE_MAIL_FOREIGN_ADDR1 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 43 | `spons_dfe_mail_foreign_addr2` | `dol.form_5500.spons_dfe_mail_foreign_addr2` | character varying(255) | Y | Plan Sponsor dfe mail foreign addr2 / ID: DOL_F5500_SPONS_DFE_MAIL_FOREIGN_ADDR2 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 44 | `spons_dfe_mail_foreign_city` | `dol.form_5500.spons_dfe_mail_foreign_city` | character varying(100) | Y | Plan Sponsor dfe mail foreign city / ID: DOL_F5500_SPONS_DFE_MAIL_FOREIGN_CITY / Format: Up to 100 characters | attribute | STRING | dol.column_metadata |
| 45 | `spons_dfe_mail_forgn_prov_st` | `dol.form_5500.spons_dfe_mail_forgn_prov_st` | character varying(255) | Y | Plan Sponsor dfe mail forgn province st / ID: DOL_F5500_SPONS_DFE_MAIL_FORGN_PROV_ST / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 46 | `spons_dfe_mail_foreign_cntry` | `dol.form_5500.spons_dfe_mail_foreign_cntry` | character varying(100) | Y | Plan Sponsor dfe mail foreign cntry / ID: DOL_F5500_SPONS_DFE_MAIL_FOREIGN_CNTRY / Format: Decimal number | attribute | STRING | dol.column_metadata |
| 47 | `spons_dfe_mail_forgn_postal_cd` | `dol.form_5500.spons_dfe_mail_forgn_postal_cd` | character varying(255) | Y | Plan Sponsor dfe mail forgn postal cd / ID: DOL_F5500_SPONS_DFE_MAIL_FORGN_POSTAL_CD / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 48 | `spons_dfe_loc_us_address1` | `dol.form_5500.spons_dfe_loc_us_address1` | character varying(255) | Y | Plan Sponsor dfe location us address1 / ID: DOL_F5500_SPONS_DFE_LOC_US_ADDRESS1 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 49 | `spons_dfe_loc_us_address2` | `dol.form_5500.spons_dfe_loc_us_address2` | character varying(255) | Y | Plan Sponsor dfe location us address2 / ID: DOL_F5500_SPONS_DFE_LOC_US_ADDRESS2 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 50 | `spons_dfe_loc_us_city` | `dol.form_5500.spons_dfe_loc_us_city` | character varying(100) | Y | Plan Sponsor dfe location us city / ID: DOL_F5500_SPONS_DFE_LOC_US_CITY / Format: Up to 100 characters | attribute | STRING | dol.column_metadata |
| 51 | `spons_dfe_loc_us_state` | `dol.form_5500.spons_dfe_loc_us_state` | character varying(10) | Y | Plan Sponsor dfe location us state / ID: DOL_F5500_SPONS_DFE_LOC_US_STATE / Format: Up to 10 characters | attribute | STRING | dol.column_metadata |
| 52 | `spons_dfe_loc_us_zip` | `dol.form_5500.spons_dfe_loc_us_zip` | character varying(20) | Y | Plan Sponsor dfe location us (ZIP code) / ID: DOL_F5500_SPONS_DFE_LOC_US_ZIP / Format: 5 or 9 digits | attribute | STRING | dol.column_metadata |
| 53 | `spons_dfe_loc_foreign_address1` | `dol.form_5500.spons_dfe_loc_foreign_address1` | character varying(255) | Y | Plan Sponsor dfe location foreign address1 / ID: DOL_F5500_SPONS_DFE_LOC_FOREIGN_ADDRESS1 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 54 | `spons_dfe_loc_foreign_address2` | `dol.form_5500.spons_dfe_loc_foreign_address2` | character varying(255) | Y | Plan Sponsor dfe location foreign address2 / ID: DOL_F5500_SPONS_DFE_LOC_FOREIGN_ADDRESS2 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 55 | `spons_dfe_loc_foreign_city` | `dol.form_5500.spons_dfe_loc_foreign_city` | character varying(100) | Y | Plan Sponsor dfe location foreign city / ID: DOL_F5500_SPONS_DFE_LOC_FOREIGN_CITY / Format: Up to 100 characters | attribute | STRING | dol.column_metadata |
| 56 | `spons_dfe_loc_forgn_prov_st` | `dol.form_5500.spons_dfe_loc_forgn_prov_st` | character varying(255) | Y | Plan Sponsor dfe location forgn province st / ID: DOL_F5500_SPONS_DFE_LOC_FORGN_PROV_ST / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 57 | `spons_dfe_loc_foreign_cntry` | `dol.form_5500.spons_dfe_loc_foreign_cntry` | character varying(100) | Y | Plan Sponsor dfe location foreign cntry / ID: DOL_F5500_SPONS_DFE_LOC_FOREIGN_CNTRY / Format: Decimal number | attribute | STRING | dol.column_metadata |
| 58 | `spons_dfe_loc_forgn_postal_cd` | `dol.form_5500.spons_dfe_loc_forgn_postal_cd` | character varying(255) | Y | Plan Sponsor dfe location forgn postal cd / ID: DOL_F5500_SPONS_DFE_LOC_FORGN_POSTAL_CD / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 59 | `spons_dfe_ein` | `dol.form_5500.spons_dfe_ein` | character varying(20) | Y | Plan Sponsor dfe (Employer Identification Number) / ID: DOL_F5500_SPONS_DFE_EIN / Format: 9 digits (XX-XXXXXXX) | identifier | STRING | dol.column_metadata |
| 60 | `spons_dfe_phone_num` | `dol.form_5500.spons_dfe_phone_num` | character varying(30) | Y | Sponsor phone number / ID: DOL_F5500_SPONS_DFE_PHONE_NUM / Format: Up to 30 characters | attribute | STRING | dol.column_metadata |
| 61 | `business_code` | `dol.form_5500.business_code` | character varying(50) | Y | Business (code value) / ID: DOL_F5500_BUSINESS_CODE / Format: Up to 50 characters | attribute | STRING | dol.column_metadata |
| 62 | `admin_care_of_name` | `dol.form_5500.admin_care_of_name` | character varying(255) | Y | Plan Administrator care of (name) / ID: DOL_F5500_ADMIN_CARE_OF_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 63 | `admin_us_address1` | `dol.form_5500.admin_us_address1` | character varying(255) | Y | Plan Administrator us address1 / ID: DOL_F5500_ADMIN_US_ADDRESS1 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 64 | `admin_us_address2` | `dol.form_5500.admin_us_address2` | character varying(255) | Y | Plan Administrator us address2 / ID: DOL_F5500_ADMIN_US_ADDRESS2 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 65 | `admin_us_city` | `dol.form_5500.admin_us_city` | character varying(100) | Y | Plan Administrator us city / ID: DOL_F5500_ADMIN_US_CITY / Format: Up to 100 characters | attribute | STRING | dol.column_metadata |
| 66 | `admin_us_state` | `dol.form_5500.admin_us_state` | character varying(10) | Y | Plan Administrator us state / ID: DOL_F5500_ADMIN_US_STATE / Format: Up to 10 characters | attribute | STRING | dol.column_metadata |
| 67 | `admin_us_zip` | `dol.form_5500.admin_us_zip` | character varying(20) | Y | Plan Administrator us (ZIP code) / ID: DOL_F5500_ADMIN_US_ZIP / Format: 5 or 9 digits | attribute | STRING | dol.column_metadata |
| 68 | `admin_foreign_address1` | `dol.form_5500.admin_foreign_address1` | character varying(255) | Y | Plan Administrator foreign address1 / ID: DOL_F5500_ADMIN_FOREIGN_ADDRESS1 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 69 | `admin_foreign_address2` | `dol.form_5500.admin_foreign_address2` | character varying(255) | Y | Plan Administrator foreign address2 / ID: DOL_F5500_ADMIN_FOREIGN_ADDRESS2 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 70 | `admin_foreign_city` | `dol.form_5500.admin_foreign_city` | character varying(100) | Y | Plan Administrator foreign city / ID: DOL_F5500_ADMIN_FOREIGN_CITY / Format: Up to 100 characters | attribute | STRING | dol.column_metadata |
| 71 | `admin_foreign_prov_state` | `dol.form_5500.admin_foreign_prov_state` | character varying(255) | Y | Plan Administrator foreign province state / ID: DOL_F5500_ADMIN_FOREIGN_PROV_STATE / Format: Up to 10 characters | attribute | STRING | dol.column_metadata |
| 72 | `admin_foreign_cntry` | `dol.form_5500.admin_foreign_cntry` | character varying(100) | Y | Plan Administrator foreign cntry / ID: DOL_F5500_ADMIN_FOREIGN_CNTRY / Format: Decimal number | attribute | STRING | dol.column_metadata |
| 73 | `admin_foreign_postal_cd` | `dol.form_5500.admin_foreign_postal_cd` | character varying(255) | Y | Plan Administrator foreign postal cd / ID: DOL_F5500_ADMIN_FOREIGN_POSTAL_CD / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 74 | `admin_phone_num` | `dol.form_5500.admin_phone_num` | character varying(30) | Y | Plan Administrator phone (number/identifier) / ID: DOL_F5500_ADMIN_PHONE_NUM / Format: Up to 30 characters | attribute | STRING | dol.column_metadata |
| 75 | `last_rpt_spons_name` | `dol.form_5500.last_rpt_spons_name` | character varying(255) | Y | Last rpt spons (name) / ID: DOL_F5500_LAST_RPT_SPONS_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 76 | `last_rpt_spons_ein` | `dol.form_5500.last_rpt_spons_ein` | character varying(20) | Y | Last rpt spons (Employer Identification Number) / ID: DOL_F5500_LAST_RPT_SPONS_EIN / Format: 9 digits (XX-XXXXXXX) | identifier | STRING | dol.column_metadata |
| 77 | `last_rpt_plan_num` | `dol.form_5500.last_rpt_plan_num` | character varying(255) | Y | Last rpt plan (number/identifier) / ID: DOL_F5500_LAST_RPT_PLAN_NUM / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 78 | `admin_signed_date` | `dol.form_5500.admin_signed_date` | character varying(30) | Y | Plan Administrator signed (date) / ID: DOL_F5500_ADMIN_SIGNED_DATE / Format: YYYY-MM-DD | attribute | STRING | dol.column_metadata |
| 79 | `admin_signed_name` | `dol.form_5500.admin_signed_name` | character varying(255) | Y | Plan Administrator signed (name) / ID: DOL_F5500_ADMIN_SIGNED_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 80 | `spons_signed_date` | `dol.form_5500.spons_signed_date` | character varying(30) | Y | Plan Sponsor signed (date) / ID: DOL_F5500_SPONS_SIGNED_DATE / Format: YYYY-MM-DD | attribute | STRING | dol.column_metadata |
| 81 | `spons_signed_name` | `dol.form_5500.spons_signed_name` | character varying(255) | Y | Plan Sponsor signed (name) / ID: DOL_F5500_SPONS_SIGNED_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 82 | `dfe_signed_date` | `dol.form_5500.dfe_signed_date` | character varying(30) | Y | Direct Filing Entity signed (date) / ID: DOL_F5500_DFE_SIGNED_DATE / Format: YYYY-MM-DD | attribute | STRING | dol.column_metadata |
| 83 | `dfe_signed_name` | `dol.form_5500.dfe_signed_name` | character varying(255) | Y | Direct Filing Entity signed (name) / ID: DOL_F5500_DFE_SIGNED_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 84 | `rtd_sep_partcp_rcvg_cnt` | `dol.form_5500.rtd_sep_partcp_rcvg_cnt` | numeric | Y | Retired/separated participants receiving benefits / ID: DOL_F5500_RTD_SEP_PARTCP_RCVG_CNT / Format: Whole number | attribute | NUMERIC | dol.column_metadata |
| 85 | `rtd_sep_partcp_fut_cnt` | `dol.form_5500.rtd_sep_partcp_fut_cnt` | numeric | Y | Rtd separated participant fut (count/number) / ID: DOL_F5500_RTD_SEP_PARTCP_FUT_CNT / Format: Whole number | attribute | NUMERIC | dol.column_metadata |
| 86 | `subtl_act_rtd_sep_cnt` | `dol.form_5500.subtl_act_rtd_sep_cnt` | numeric | Y | Subtl act retired sep (count/number) / ID: DOL_F5500_SUBTL_ACT_RTD_SEP_CNT / Format: Whole number | attribute | NUMERIC | dol.column_metadata |
| 87 | `benef_rcvg_bnft_cnt` | `dol.form_5500.benef_rcvg_bnft_cnt` | numeric | Y | Benef receiving bnft (count/number) / ID: DOL_F5500_BENEF_RCVG_BNFT_CNT / Format: Whole number | attribute | NUMERIC | dol.column_metadata |
| 88 | `tot_act_rtd_sep_benef_cnt` | `dol.form_5500.tot_act_rtd_sep_benef_cnt` | numeric | Y | Tot act retired separated benef (count/number) / ID: DOL_F5500_TOT_ACT_RTD_SEP_BENEF_CNT / Format: Whole number | attribute | NUMERIC | dol.column_metadata |
| 89 | `partcp_account_bal_cnt` | `dol.form_5500.partcp_account_bal_cnt` | numeric | Y | Participants with account balances / ID: DOL_F5500_PARTCP_ACCOUNT_BAL_CNT / Format: Whole number | attribute | NUMERIC | dol.column_metadata |
| 90 | `sep_partcp_partl_vstd_cnt` | `dol.form_5500.sep_partcp_partl_vstd_cnt` | numeric | Y | Sep participant partl vstd (count/number) / ID: DOL_F5500_SEP_PARTCP_PARTL_VSTD_CNT / Format: Whole number | attribute | NUMERIC | dol.column_metadata |
| 91 | `contrib_emplrs_cnt` | `dol.form_5500.contrib_emplrs_cnt` | numeric | Y | Contrib emplrs (count/number) / ID: DOL_F5500_CONTRIB_EMPLRS_CNT / Format: Whole number | attribute | NUMERIC | dol.column_metadata |
| 92 | `type_pension_bnft_code` | `dol.form_5500.type_pension_bnft_code` | character varying(50) | Y | Type pension bnft (code value) / ID: DOL_F5500_TYPE_PENSION_BNFT_CODE / Format: Up to 50 characters | attribute | STRING | dol.column_metadata |
| 93 | `type_welfare_bnft_code` | `dol.form_5500.type_welfare_bnft_code` | character varying(50) | Y | Type welfare bnft (code value) / ID: DOL_F5500_TYPE_WELFARE_BNFT_CODE / Format: Up to 50 characters | attribute | STRING | dol.column_metadata |
| 94 | `funding_insurance_ind` | `dol.form_5500.funding_insurance_ind` | character varying(5) | Y | Funding insurance (indicator flag) / ID: DOL_F5500_FUNDING_INSURANCE_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 95 | `funding_sec412_ind` | `dol.form_5500.funding_sec412_ind` | character varying(5) | Y | Funding sec412 (indicator flag) / ID: DOL_F5500_FUNDING_SEC412_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 96 | `funding_trust_ind` | `dol.form_5500.funding_trust_ind` | character varying(5) | Y | Funding trust (indicator flag) / ID: DOL_F5500_FUNDING_TRUST_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 97 | `funding_gen_asset_ind` | `dol.form_5500.funding_gen_asset_ind` | character varying(5) | Y | Funding gen asset (indicator flag) / ID: DOL_F5500_FUNDING_GEN_ASSET_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 98 | `benefit_insurance_ind` | `dol.form_5500.benefit_insurance_ind` | character varying(5) | Y | Benefit insurance (indicator flag) / ID: DOL_F5500_BENEFIT_INSURANCE_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 99 | `benefit_sec412_ind` | `dol.form_5500.benefit_sec412_ind` | character varying(5) | Y | Benefit sec412 (indicator flag) / ID: DOL_F5500_BENEFIT_SEC412_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 100 | `benefit_trust_ind` | `dol.form_5500.benefit_trust_ind` | character varying(5) | Y | Benefit trust (indicator flag) / ID: DOL_F5500_BENEFIT_TRUST_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 101 | `benefit_gen_asset_ind` | `dol.form_5500.benefit_gen_asset_ind` | character varying(5) | Y | Benefit gen asset (indicator flag) / ID: DOL_F5500_BENEFIT_GEN_ASSET_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 102 | `sch_r_attached_ind` | `dol.form_5500.sch_r_attached_ind` | character varying(5) | Y | Sch r attached (indicator flag) / ID: DOL_F5500_SCH_R_ATTACHED_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 103 | `sch_mb_attached_ind` | `dol.form_5500.sch_mb_attached_ind` | character varying(5) | Y | Sch mb attached (indicator flag) / ID: DOL_F5500_SCH_MB_ATTACHED_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 104 | `sch_sb_attached_ind` | `dol.form_5500.sch_sb_attached_ind` | character varying(5) | Y | Sch sb attached (indicator flag) / ID: DOL_F5500_SCH_SB_ATTACHED_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 105 | `sch_h_attached_ind` | `dol.form_5500.sch_h_attached_ind` | character varying(5) | Y | Sch h attached (indicator flag) / ID: DOL_F5500_SCH_H_ATTACHED_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 106 | `sch_i_attached_ind` | `dol.form_5500.sch_i_attached_ind` | character varying(5) | Y | Sch i attached (indicator flag) / ID: DOL_F5500_SCH_I_ATTACHED_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 107 | `sch_c_attached_ind` | `dol.form_5500.sch_c_attached_ind` | character varying(5) | Y | Sch c attached (indicator flag) / ID: DOL_F5500_SCH_C_ATTACHED_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 108 | `sch_d_attached_ind` | `dol.form_5500.sch_d_attached_ind` | character varying(5) | Y | Sch d attached (indicator flag) / ID: DOL_F5500_SCH_D_ATTACHED_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 109 | `sch_g_attached_ind` | `dol.form_5500.sch_g_attached_ind` | character varying(5) | Y | Sch g attached (indicator flag) / ID: DOL_F5500_SCH_G_ATTACHED_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 110 | `valid_admin_signature` | `dol.form_5500.valid_admin_signature` | character varying(255) | Y | Valid administrative signature / ID: DOL_F5500_VALID_ADMIN_SIGNATURE / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 111 | `valid_dfe_signature` | `dol.form_5500.valid_dfe_signature` | character varying(255) | Y | Valid Direct Filing Entity signature / ID: DOL_F5500_VALID_DFE_SIGNATURE / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 112 | `valid_sponsor_signature` | `dol.form_5500.valid_sponsor_signature` | character varying(255) | Y | Valid sponsor signature / ID: DOL_F5500_VALID_SPONSOR_SIGNATURE / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 113 | `admin_phone_num_foreign` | `dol.form_5500.admin_phone_num_foreign` | character varying(255) | Y | Plan Administrator phone number foreign / ID: DOL_F5500_ADMIN_PHONE_NUM_FOREIGN / Format: Up to 30 characters | attribute | STRING | dol.column_metadata |
| 114 | `spons_dfe_phone_num_foreign` | `dol.form_5500.spons_dfe_phone_num_foreign` | character varying(255) | Y | Plan Sponsor dfe phone number foreign / ID: DOL_F5500_SPONS_DFE_PHONE_NUM_FOREIGN / Format: Up to 30 characters | attribute | STRING | dol.column_metadata |
| 115 | `admin_name_same_spon_ind` | `dol.form_5500.admin_name_same_spon_ind` | character varying(5) | Y | Plan Administrator name same spon (indicator flag) / ID: DOL_F5500_ADMIN_NAME_SAME_SPON_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 116 | `admin_address_same_spon_ind` | `dol.form_5500.admin_address_same_spon_ind` | character varying(5) | Y | Plan Administrator address same spon (indicator flag) / ID: DOL_F5500_ADMIN_ADDRESS_SAME_SPON_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 117 | `preparer_name` | `dol.form_5500.preparer_name` | character varying(255) | Y | Form Preparer name / ID: DOL_F5500_PREPARER_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 118 | `preparer_firm_name` | `dol.form_5500.preparer_firm_name` | character varying(255) | Y | Form Preparer firm (name) / ID: DOL_F5500_PREPARER_FIRM_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 119 | `preparer_us_address1` | `dol.form_5500.preparer_us_address1` | character varying(255) | Y | Form Preparer us address1 / ID: DOL_F5500_PREPARER_US_ADDRESS1 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 120 | `preparer_us_address2` | `dol.form_5500.preparer_us_address2` | character varying(255) | Y | Form Preparer us address2 / ID: DOL_F5500_PREPARER_US_ADDRESS2 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 121 | `preparer_us_city` | `dol.form_5500.preparer_us_city` | character varying(100) | Y | Form Preparer us city / ID: DOL_F5500_PREPARER_US_CITY / Format: Up to 100 characters | attribute | STRING | dol.column_metadata |
| 122 | `preparer_us_state` | `dol.form_5500.preparer_us_state` | character varying(10) | Y | Form Preparer us state / ID: DOL_F5500_PREPARER_US_STATE / Format: Up to 10 characters | attribute | STRING | dol.column_metadata |
| 123 | `preparer_us_zip` | `dol.form_5500.preparer_us_zip` | character varying(20) | Y | Form Preparer us (ZIP code) / ID: DOL_F5500_PREPARER_US_ZIP / Format: 5 or 9 digits | attribute | STRING | dol.column_metadata |
| 124 | `preparer_foreign_address1` | `dol.form_5500.preparer_foreign_address1` | character varying(255) | Y | Form Preparer foreign address1 / ID: DOL_F5500_PREPARER_FOREIGN_ADDRESS1 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 125 | `preparer_foreign_address2` | `dol.form_5500.preparer_foreign_address2` | character varying(255) | Y | Form Preparer foreign address2 / ID: DOL_F5500_PREPARER_FOREIGN_ADDRESS2 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 126 | `preparer_foreign_city` | `dol.form_5500.preparer_foreign_city` | character varying(100) | Y | Form Preparer foreign city / ID: DOL_F5500_PREPARER_FOREIGN_CITY / Format: Up to 100 characters | attribute | STRING | dol.column_metadata |
| 127 | `preparer_foreign_prov_state` | `dol.form_5500.preparer_foreign_prov_state` | character varying(255) | Y | Form Preparer foreign province state / ID: DOL_F5500_PREPARER_FOREIGN_PROV_STATE / Format: Up to 10 characters | attribute | STRING | dol.column_metadata |
| 128 | `preparer_foreign_cntry` | `dol.form_5500.preparer_foreign_cntry` | character varying(100) | Y | Form Preparer foreign cntry / ID: DOL_F5500_PREPARER_FOREIGN_CNTRY / Format: Decimal number | attribute | STRING | dol.column_metadata |
| 129 | `preparer_foreign_postal_cd` | `dol.form_5500.preparer_foreign_postal_cd` | character varying(255) | Y | Form Preparer foreign postal cd / ID: DOL_F5500_PREPARER_FOREIGN_POSTAL_CD / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 130 | `preparer_phone_num` | `dol.form_5500.preparer_phone_num` | character varying(30) | Y | Form Preparer phone (number/identifier) / ID: DOL_F5500_PREPARER_PHONE_NUM / Format: Up to 30 characters | attribute | STRING | dol.column_metadata |
| 131 | `preparer_phone_num_foreign` | `dol.form_5500.preparer_phone_num_foreign` | character varying(255) | Y | Form Preparer phone number foreign / ID: DOL_F5500_PREPARER_PHONE_NUM_FOREIGN / Format: Up to 30 characters | attribute | STRING | dol.column_metadata |
| 132 | `tot_act_partcp_boy_cnt` | `dol.form_5500.tot_act_partcp_boy_cnt` | numeric | Y | Tot act participant boy (count/number) / ID: DOL_F5500_TOT_ACT_PARTCP_BOY_CNT / Format: Whole number | attribute | NUMERIC | dol.column_metadata |
| 133 | `subj_m1_filing_req_ind` | `dol.form_5500.subj_m1_filing_req_ind` | character varying(5) | Y | Subj m1 filing req (indicator flag) / ID: DOL_F5500_SUBJ_M1_FILING_REQ_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 134 | `compliance_m1_filing_req_ind` | `dol.form_5500.compliance_m1_filing_req_ind` | character varying(5) | Y | Compliance m1 filing req (indicator flag) / ID: DOL_F5500_COMPLIANCE_M1_FILING_REQ_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 135 | `m1_receipt_confirmation_code` | `dol.form_5500.m1_receipt_confirmation_code` | character varying(50) | Y | M1 receipt confirmation (code value) / ID: DOL_F5500_M1_RECEIPT_CONFIRMATION_CODE / Format: Up to 50 characters | attribute | STRING | dol.column_metadata |
| 136 | `admin_manual_signed_date` | `dol.form_5500.admin_manual_signed_date` | character varying(30) | Y | Plan Administrator manual signed (date) / ID: DOL_F5500_ADMIN_MANUAL_SIGNED_DATE / Format: YYYY-MM-DD | attribute | STRING | dol.column_metadata |
| 137 | `admin_manual_signed_name` | `dol.form_5500.admin_manual_signed_name` | character varying(255) | Y | Plan Administrator manual signed (name) / ID: DOL_F5500_ADMIN_MANUAL_SIGNED_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 138 | `last_rpt_plan_name` | `dol.form_5500.last_rpt_plan_name` | character varying(255) | Y | Last rpt plan (name) / ID: DOL_F5500_LAST_RPT_PLAN_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 139 | `spons_manual_signed_date` | `dol.form_5500.spons_manual_signed_date` | character varying(30) | Y | Plan Sponsor manual signed (date) / ID: DOL_F5500_SPONS_MANUAL_SIGNED_DATE / Format: YYYY-MM-DD | attribute | STRING | dol.column_metadata |
| 140 | `spons_manual_signed_name` | `dol.form_5500.spons_manual_signed_name` | character varying(255) | Y | Plan Sponsor manual signed (name) / ID: DOL_F5500_SPONS_MANUAL_SIGNED_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 141 | `dfe_manual_signed_date` | `dol.form_5500.dfe_manual_signed_date` | character varying(30) | Y | Direct Filing Entity manual signed (date) / ID: DOL_F5500_DFE_MANUAL_SIGNED_DATE / Format: YYYY-MM-DD | attribute | STRING | dol.column_metadata |
| 142 | `dfe_manual_signed_name` | `dol.form_5500.dfe_manual_signed_name` | character varying(255) | Y | Direct Filing Entity manual signed (name) / ID: DOL_F5500_DFE_MANUAL_SIGNED_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 143 | `adopted_plan_perm_sec_act` | `dol.form_5500.adopted_plan_perm_sec_act` | character varying(255) | Y | Adopted plan perm sec act / ID: DOL_F5500_ADOPTED_PLAN_PERM_SEC_ACT / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 144 | `partcp_account_bal_cnt_boy` | `dol.form_5500.partcp_account_bal_cnt_boy` | numeric | Y | Partcp account balance cnt boy / ID: DOL_F5500_PARTCP_ACCOUNT_BAL_CNT_BOY / Format: Decimal number | attribute | NUMERIC | dol.column_metadata |
| 145 | `sch_dcg_attached_ind` | `dol.form_5500.sch_dcg_attached_ind` | character varying(5) | Y | Sch dcg attached (indicator flag) / ID: DOL_F5500_SCH_DCG_ATTACHED_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 146 | `num_sch_dcg_attached_cnt` | `dol.form_5500.num_sch_dcg_attached_cnt` | numeric | Y | Num sch dcg attached (count/number) / ID: DOL_F5500_NUM_SCH_DCG_ATTACHED_CNT / Format: Whole number | attribute | NUMERIC | dol.column_metadata |
| 147 | `sch_mep_attached_ind` | `dol.form_5500.sch_mep_attached_ind` | character varying(5) | Y | Sch mep attached (indicator flag) / ID: DOL_F5500_SCH_MEP_ATTACHED_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |

### `dol.form_5500_icp_filtered` -- MV -- 24,892 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `sponsor_dfe_ein` | `dol.form_5500_icp_filtered.sponsor_dfe_ein` | character varying(20) | Y | Sponsor Dfe Ein | attribute | STRING | inferred |
| 2 | `sponsor_dfe_name` | `dol.form_5500_icp_filtered.sponsor_dfe_name` | character varying(500) | Y | Sponsor Dfe Name | attribute | STRING | inferred |
| 3 | `spons_dfe_mail_us_state` | `dol.form_5500_icp_filtered.spons_dfe_mail_us_state` | character varying(10) | Y | Spons Dfe Mail Us State | attribute | STRING | inferred |
| 4 | `spons_dfe_mail_us_city` | `dol.form_5500_icp_filtered.spons_dfe_mail_us_city` | character varying(100) | Y | Spons Dfe Mail Us City | attribute | STRING | inferred |
| 5 | `tot_active_partcp_cnt` | `dol.form_5500_icp_filtered.tot_active_partcp_cnt` | integer | Y | Tot Active Partcp Cnt | attribute | INTEGER | inferred |
| 6 | `normalized_name` | `dol.form_5500_icp_filtered.normalized_name` | text | Y | Normalized Name | attribute | STRING | inferred |
| 7 | `filter_id` | `dol.form_5500_icp_filtered.filter_id` | integer | N | Filter Id | identifier | INTEGER | inferred |

### `dol.form_5500_sf` -- CANONICAL -- 1,535,727 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `filing_id` | `dol.form_5500_sf.filing_id` | uuid | N | Unique filing identifier (UUID) / ID: DOL_F5500SF_FILING_ID / Format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | attribute | UUID | dol.column_metadata |
| 2 | `company_unique_id` | `dol.form_5500_sf.company_unique_id` | text | Y | Company unique id / ID: DOL_F5500SF_COMPANY_UNIQUE_ID / Format: Variable length text | attribute | STRING | dol.column_metadata |
| 3 | `ack_id` | `dol.form_5500_sf.ack_id` | character varying(255) | Y | DOL acknowledgment ID for the filing / ID: DOL_F5500SF_ACK_ID / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 4 | `sf_plan_year_begin_date` | `dol.form_5500_sf.sf_plan_year_begin_date` | character varying(255) | Y | Short Form (5500-SF) plan year begin (date) / ID: DOL_F5500SF_SF_PLAN_YEAR_BEGIN_DATE / Format: YYYY-MM-DD | attribute | STRING | dol.column_metadata |
| 5 | `sf_tax_prd` | `dol.form_5500_sf.sf_tax_prd` | character varying(255) | Y | Short Form (5500-SF) tax prd / ID: DOL_F5500SF_SF_TAX_PRD / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 6 | `sf_plan_entity_cd` | `dol.form_5500_sf.sf_plan_entity_cd` | character varying(255) | Y | Short Form (5500-SF) plan entity cd / ID: DOL_F5500SF_SF_PLAN_ENTITY_CD / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 7 | `sf_initial_filing_ind` | `dol.form_5500_sf.sf_initial_filing_ind` | character varying(5) | Y | Short Form (5500-SF) initial filing (indicator flag) / ID: DOL_F5500SF_SF_INITIAL_FILING_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 8 | `sf_amended_ind` | `dol.form_5500_sf.sf_amended_ind` | character varying(5) | Y | Short Form (5500-SF) amended (indicator flag) / ID: DOL_F5500SF_SF_AMENDED_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 9 | `sf_final_filing_ind` | `dol.form_5500_sf.sf_final_filing_ind` | character varying(5) | Y | Short Form (5500-SF) final filing (indicator flag) / ID: DOL_F5500SF_SF_FINAL_FILING_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 10 | `sf_short_plan_yr_ind` | `dol.form_5500_sf.sf_short_plan_yr_ind` | character varying(5) | Y | Short Form (5500-SF) short plan yr (indicator flag) / ID: DOL_F5500SF_SF_SHORT_PLAN_YR_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 11 | `sf_5558_application_filed_ind` | `dol.form_5500_sf.sf_5558_application_filed_ind` | character varying(5) | Y | Short Form (5500-SF) 5558 application filed (indicator flag) / ID: DOL_F5500SF_SF_5558_APPLICATION_FILED_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 12 | `sf_ext_automatic_ind` | `dol.form_5500_sf.sf_ext_automatic_ind` | character varying(5) | Y | Short Form (5500-SF) ext automatic (indicator flag) / ID: DOL_F5500SF_SF_EXT_AUTOMATIC_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 13 | `sf_dfvc_program_ind` | `dol.form_5500_sf.sf_dfvc_program_ind` | character varying(5) | Y | Short Form (5500-SF) dfvc program (indicator flag) / ID: DOL_F5500SF_SF_DFVC_PROGRAM_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 14 | `sf_ext_special_ind` | `dol.form_5500_sf.sf_ext_special_ind` | character varying(5) | Y | Short Form (5500-SF) ext special (indicator flag) / ID: DOL_F5500SF_SF_EXT_SPECIAL_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 15 | `sf_ext_special_text` | `dol.form_5500_sf.sf_ext_special_text` | text | Y | Short Form (5500-SF) ext special (text description) / ID: DOL_F5500SF_SF_EXT_SPECIAL_TEXT / Format: Variable length text | attribute | STRING | dol.column_metadata |
| 16 | `sf_plan_name` | `dol.form_5500_sf.sf_plan_name` | character varying(255) | Y | Short Form (5500-SF) plan (name) / ID: DOL_F5500SF_SF_PLAN_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 17 | `sf_plan_num` | `dol.form_5500_sf.sf_plan_num` | character varying(255) | Y | Short Form (5500-SF) plan (number/identifier) / ID: DOL_F5500SF_SF_PLAN_NUM / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 18 | `sf_plan_eff_date` | `dol.form_5500_sf.sf_plan_eff_date` | character varying(255) | Y | Short Form (5500-SF) plan eff (date) / ID: DOL_F5500SF_SF_PLAN_EFF_DATE / Format: YYYY-MM-DD | attribute | STRING | dol.column_metadata |
| 19 | `sf_sponsor_name` | `dol.form_5500_sf.sf_sponsor_name` | character varying(255) | Y | Plan Sponsor (SF) name / ID: DOL_F5500SF_SF_SPONSOR_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 20 | `sf_sponsor_dfe_dba_name` | `dol.form_5500_sf.sf_sponsor_dfe_dba_name` | character varying(255) | Y | Plan Sponsor (SF) dfe dba (name) / ID: DOL_F5500SF_SF_SPONSOR_DFE_DBA_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 21 | `sf_spons_us_address1` | `dol.form_5500_sf.sf_spons_us_address1` | character varying(255) | Y | Plan Sponsor (SF) us address1 / ID: DOL_F5500SF_SF_SPONS_US_ADDRESS1 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 22 | `sf_spons_us_address2` | `dol.form_5500_sf.sf_spons_us_address2` | character varying(255) | Y | Plan Sponsor (SF) us address2 / ID: DOL_F5500SF_SF_SPONS_US_ADDRESS2 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 23 | `sf_spons_us_city` | `dol.form_5500_sf.sf_spons_us_city` | character varying(255) | Y | Plan Sponsor (SF) us city / ID: DOL_F5500SF_SF_SPONS_US_CITY / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 24 | `sf_spons_us_state` | `dol.form_5500_sf.sf_spons_us_state` | character varying(255) | Y | Plan Sponsor (SF) us state / ID: DOL_F5500SF_SF_SPONS_US_STATE / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 25 | `sf_spons_us_zip` | `dol.form_5500_sf.sf_spons_us_zip` | character varying(255) | Y | Plan Sponsor (SF) us (ZIP code) / ID: DOL_F5500SF_SF_SPONS_US_ZIP / Format: 5 or 9 digits | attribute | STRING | dol.column_metadata |
| 26 | `sf_spons_foreign_address1` | `dol.form_5500_sf.sf_spons_foreign_address1` | character varying(255) | Y | Plan Sponsor (SF) foreign address1 / ID: DOL_F5500SF_SF_SPONS_FOREIGN_ADDRESS1 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 27 | `sf_spons_foreign_address2` | `dol.form_5500_sf.sf_spons_foreign_address2` | character varying(255) | Y | Plan Sponsor (SF) foreign address2 / ID: DOL_F5500SF_SF_SPONS_FOREIGN_ADDRESS2 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 28 | `sf_spons_foreign_city` | `dol.form_5500_sf.sf_spons_foreign_city` | character varying(255) | Y | Plan Sponsor (SF) foreign city / ID: DOL_F5500SF_SF_SPONS_FOREIGN_CITY / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 29 | `sf_spons_foreign_prov_state` | `dol.form_5500_sf.sf_spons_foreign_prov_state` | character varying(255) | Y | Plan Sponsor (SF) foreign province state / ID: DOL_F5500SF_SF_SPONS_FOREIGN_PROV_STATE / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 30 | `sf_spons_foreign_cntry` | `dol.form_5500_sf.sf_spons_foreign_cntry` | character varying(255) | Y | Plan Sponsor (SF) foreign cntry / ID: DOL_F5500SF_SF_SPONS_FOREIGN_CNTRY / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 31 | `sf_spons_foreign_postal_cd` | `dol.form_5500_sf.sf_spons_foreign_postal_cd` | character varying(255) | Y | Plan Sponsor (SF) foreign postal cd / ID: DOL_F5500SF_SF_SPONS_FOREIGN_POSTAL_CD / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 32 | `sf_spons_ein` | `dol.form_5500_sf.sf_spons_ein` | character varying(255) | Y | Plan Sponsor (SF) ein / ID: DOL_F5500SF_SF_SPONS_EIN / Format: 9 digits (XX-XXXXXXX) | identifier | STRING | dol.column_metadata |
| 33 | `sf_spons_phone_num` | `dol.form_5500_sf.sf_spons_phone_num` | character varying(255) | Y | Plan Sponsor (SF) phone (number/identifier) / ID: DOL_F5500SF_SF_SPONS_PHONE_NUM / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 34 | `sf_business_code` | `dol.form_5500_sf.sf_business_code` | character varying(255) | Y | Short Form (5500-SF) business (code value) / ID: DOL_F5500SF_SF_BUSINESS_CODE / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 35 | `sf_admin_name` | `dol.form_5500_sf.sf_admin_name` | character varying(255) | Y | Plan Administrator (SF) name / ID: DOL_F5500SF_SF_ADMIN_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 36 | `sf_admin_care_of_name` | `dol.form_5500_sf.sf_admin_care_of_name` | character varying(255) | Y | Plan Administrator (SF) care of (name) / ID: DOL_F5500SF_SF_ADMIN_CARE_OF_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 37 | `sf_admin_us_address1` | `dol.form_5500_sf.sf_admin_us_address1` | character varying(255) | Y | Plan Administrator (SF) us address1 / ID: DOL_F5500SF_SF_ADMIN_US_ADDRESS1 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 38 | `sf_admin_us_address2` | `dol.form_5500_sf.sf_admin_us_address2` | character varying(255) | Y | Plan Administrator (SF) us address2 / ID: DOL_F5500SF_SF_ADMIN_US_ADDRESS2 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 39 | `sf_admin_us_city` | `dol.form_5500_sf.sf_admin_us_city` | character varying(255) | Y | Plan Administrator (SF) us city / ID: DOL_F5500SF_SF_ADMIN_US_CITY / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 40 | `sf_admin_us_state` | `dol.form_5500_sf.sf_admin_us_state` | character varying(255) | Y | Plan Administrator (SF) us state / ID: DOL_F5500SF_SF_ADMIN_US_STATE / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 41 | `sf_admin_us_zip` | `dol.form_5500_sf.sf_admin_us_zip` | character varying(255) | Y | Plan Administrator (SF) us (ZIP code) / ID: DOL_F5500SF_SF_ADMIN_US_ZIP / Format: 5 or 9 digits | attribute | STRING | dol.column_metadata |
| 42 | `sf_admin_foreign_address1` | `dol.form_5500_sf.sf_admin_foreign_address1` | character varying(255) | Y | Plan Administrator (SF) foreign address1 / ID: DOL_F5500SF_SF_ADMIN_FOREIGN_ADDRESS1 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 43 | `sf_admin_foreign_address2` | `dol.form_5500_sf.sf_admin_foreign_address2` | character varying(255) | Y | Plan Administrator (SF) foreign address2 / ID: DOL_F5500SF_SF_ADMIN_FOREIGN_ADDRESS2 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 44 | `sf_admin_foreign_city` | `dol.form_5500_sf.sf_admin_foreign_city` | character varying(255) | Y | Plan Administrator (SF) foreign city / ID: DOL_F5500SF_SF_ADMIN_FOREIGN_CITY / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 45 | `sf_admin_foreign_prov_state` | `dol.form_5500_sf.sf_admin_foreign_prov_state` | character varying(255) | Y | Plan Administrator (SF) foreign province state / ID: DOL_F5500SF_SF_ADMIN_FOREIGN_PROV_STATE / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 46 | `sf_admin_foreign_cntry` | `dol.form_5500_sf.sf_admin_foreign_cntry` | character varying(255) | Y | Plan Administrator (SF) foreign cntry / ID: DOL_F5500SF_SF_ADMIN_FOREIGN_CNTRY / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 47 | `sf_admin_foreign_postal_cd` | `dol.form_5500_sf.sf_admin_foreign_postal_cd` | character varying(255) | Y | Plan Administrator (SF) foreign postal cd / ID: DOL_F5500SF_SF_ADMIN_FOREIGN_POSTAL_CD / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 48 | `sf_admin_ein` | `dol.form_5500_sf.sf_admin_ein` | character varying(255) | Y | Plan Administrator (SF) ein / ID: DOL_F5500SF_SF_ADMIN_EIN / Format: 9 digits (XX-XXXXXXX) | identifier | STRING | dol.column_metadata |
| 49 | `sf_admin_phone_num` | `dol.form_5500_sf.sf_admin_phone_num` | character varying(255) | Y | Plan Administrator (SF) phone (number/identifier) / ID: DOL_F5500SF_SF_ADMIN_PHONE_NUM / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 50 | `sf_last_rpt_spons_name` | `dol.form_5500_sf.sf_last_rpt_spons_name` | character varying(255) | Y | Short Form (5500-SF) last rpt spons (name) / ID: DOL_F5500SF_SF_LAST_RPT_SPONS_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 51 | `sf_last_rpt_spons_ein` | `dol.form_5500_sf.sf_last_rpt_spons_ein` | character varying(255) | Y | Short Form (5500-SF) last rpt spons (Employer Identification Number) / ID: DOL_F5500SF_SF_LAST_RPT_SPONS_EIN / Format: 9 digits (XX-XXXXXXX) | identifier | STRING | dol.column_metadata |
| 52 | `sf_last_rpt_plan_num` | `dol.form_5500_sf.sf_last_rpt_plan_num` | character varying(255) | Y | Short Form (5500-SF) last rpt plan (number/identifier) / ID: DOL_F5500SF_SF_LAST_RPT_PLAN_NUM / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 53 | `sf_tot_partcp_boy_cnt` | `dol.form_5500_sf.sf_tot_partcp_boy_cnt` | numeric | Y | Short Form (5500-SF) tot participant boy (count/number) / ID: DOL_F5500SF_SF_TOT_PARTCP_BOY_CNT / Format: Whole number | attribute | NUMERIC | dol.column_metadata |
| 54 | `sf_tot_act_rtd_sep_benef_cnt` | `dol.form_5500_sf.sf_tot_act_rtd_sep_benef_cnt` | numeric | Y | Short Form (5500-SF) tot act retired separated benef (count/number) / ID: DOL_F5500SF_SF_TOT_ACT_RTD_SEP_BENEF_CNT / Format: Whole number | attribute | NUMERIC | dol.column_metadata |
| 55 | `sf_partcp_account_bal_cnt` | `dol.form_5500_sf.sf_partcp_account_bal_cnt` | numeric | Y | Short Form (5500-SF) partcp account bal (count/number) / ID: DOL_F5500SF_SF_PARTCP_ACCOUNT_BAL_CNT / Format: Whole number | attribute | NUMERIC | dol.column_metadata |
| 56 | `sf_eligible_assets_ind` | `dol.form_5500_sf.sf_eligible_assets_ind` | character varying(5) | Y | Short Form (5500-SF) eligible assets (indicator flag) / ID: DOL_F5500SF_SF_ELIGIBLE_ASSETS_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 57 | `sf_iqpa_waiver_ind` | `dol.form_5500_sf.sf_iqpa_waiver_ind` | character varying(5) | Y | Short Form (5500-SF) iqpa waiver (indicator flag) / ID: DOL_F5500SF_SF_IQPA_WAIVER_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 58 | `sf_tot_assets_boy_amt` | `dol.form_5500_sf.sf_tot_assets_boy_amt` | numeric | Y | Short Form (5500-SF) tot assets boy (amount in dollars) / ID: DOL_F5500SF_SF_TOT_ASSETS_BOY_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 59 | `sf_tot_liabilities_boy_amt` | `dol.form_5500_sf.sf_tot_liabilities_boy_amt` | numeric | Y | Short Form (5500-SF) tot liabilities boy (amount in dollars) / ID: DOL_F5500SF_SF_TOT_LIABILITIES_BOY_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 60 | `sf_net_assets_boy_amt` | `dol.form_5500_sf.sf_net_assets_boy_amt` | numeric | Y | Short Form (5500-SF) net assets boy (amount in dollars) / ID: DOL_F5500SF_SF_NET_ASSETS_BOY_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 61 | `sf_tot_assets_eoy_amt` | `dol.form_5500_sf.sf_tot_assets_eoy_amt` | numeric | Y | Short Form (5500-SF) tot assets eoy (amount in dollars) / ID: DOL_F5500SF_SF_TOT_ASSETS_EOY_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 62 | `sf_tot_liabilities_eoy_amt` | `dol.form_5500_sf.sf_tot_liabilities_eoy_amt` | numeric | Y | Short Form (5500-SF) tot liabilities eoy (amount in dollars) / ID: DOL_F5500SF_SF_TOT_LIABILITIES_EOY_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 63 | `sf_net_assets_eoy_amt` | `dol.form_5500_sf.sf_net_assets_eoy_amt` | numeric | Y | Short Form (5500-SF) net assets eoy (amount in dollars) / ID: DOL_F5500SF_SF_NET_ASSETS_EOY_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 64 | `sf_emplr_contrib_income_amt` | `dol.form_5500_sf.sf_emplr_contrib_income_amt` | numeric | Y | Short Form (5500-SF) emplr contribution income (amount in dollars) / ID: DOL_F5500SF_SF_EMPLR_CONTRIB_INCOME_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 65 | `sf_particip_contrib_income_amt` | `dol.form_5500_sf.sf_particip_contrib_income_amt` | numeric | Y | Short Form (5500-SF) particip contribution income (amount in dollars) / ID: DOL_F5500SF_SF_PARTICIP_CONTRIB_INCOME_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 66 | `sf_oth_contrib_rcvd_amt` | `dol.form_5500_sf.sf_oth_contrib_rcvd_amt` | numeric | Y | Short Form (5500-SF) oth contribution rcvd (amount in dollars) / ID: DOL_F5500SF_SF_OTH_CONTRIB_RCVD_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 67 | `sf_other_income_amt` | `dol.form_5500_sf.sf_other_income_amt` | numeric | Y | Short Form (5500-SF) other income (amount in dollars) / ID: DOL_F5500SF_SF_OTHER_INCOME_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 68 | `sf_tot_income_amt` | `dol.form_5500_sf.sf_tot_income_amt` | numeric | Y | Short Form (5500-SF) tot income (amount in dollars) / ID: DOL_F5500SF_SF_TOT_INCOME_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 69 | `sf_tot_distrib_bnft_amt` | `dol.form_5500_sf.sf_tot_distrib_bnft_amt` | numeric | Y | Short Form (5500-SF) tot distrib bnft (amount in dollars) / ID: DOL_F5500SF_SF_TOT_DISTRIB_BNFT_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 70 | `sf_corrective_deemed_distr_amt` | `dol.form_5500_sf.sf_corrective_deemed_distr_amt` | numeric | Y | Short Form (5500-SF) corrective deemed distr (amount in dollars) / ID: DOL_F5500SF_SF_CORRECTIVE_DEEMED_DISTR_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 71 | `sf_admin_srvc_providers_amt` | `dol.form_5500_sf.sf_admin_srvc_providers_amt` | numeric | Y | Plan Administrator (SF) srvc providers (amount in dollars) / ID: DOL_F5500SF_SF_ADMIN_SRVC_PROVIDERS_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 72 | `sf_oth_expenses_amt` | `dol.form_5500_sf.sf_oth_expenses_amt` | numeric | Y | Short Form (5500-SF) oth expenses (amount in dollars) / ID: DOL_F5500SF_SF_OTH_EXPENSES_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 73 | `sf_tot_expenses_amt` | `dol.form_5500_sf.sf_tot_expenses_amt` | numeric | Y | Short Form (5500-SF) tot expenses (amount in dollars) / ID: DOL_F5500SF_SF_TOT_EXPENSES_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 74 | `sf_net_income_amt` | `dol.form_5500_sf.sf_net_income_amt` | numeric | Y | Short Form (5500-SF) net income (amount in dollars) / ID: DOL_F5500SF_SF_NET_INCOME_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 75 | `sf_tot_plan_transfers_amt` | `dol.form_5500_sf.sf_tot_plan_transfers_amt` | numeric | Y | Short Form (5500-SF) tot plan transfers (amount in dollars) / ID: DOL_F5500SF_SF_TOT_PLAN_TRANSFERS_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 76 | `sf_type_pension_bnft_code` | `dol.form_5500_sf.sf_type_pension_bnft_code` | character varying(255) | Y | Short Form (5500-SF) type pension bnft (code value) / ID: DOL_F5500SF_SF_TYPE_PENSION_BNFT_CODE / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 77 | `sf_type_welfare_bnft_code` | `dol.form_5500_sf.sf_type_welfare_bnft_code` | character varying(255) | Y | Short Form (5500-SF) type welfare bnft (code value) / ID: DOL_F5500SF_SF_TYPE_WELFARE_BNFT_CODE / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 78 | `sf_fail_transmit_contrib_ind` | `dol.form_5500_sf.sf_fail_transmit_contrib_ind` | character varying(5) | Y | Short Form (5500-SF) fail transmit contrib (indicator flag) / ID: DOL_F5500SF_SF_FAIL_TRANSMIT_CONTRIB_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 79 | `sf_fail_transmit_contrib_amt` | `dol.form_5500_sf.sf_fail_transmit_contrib_amt` | numeric | Y | Short Form (5500-SF) fail transmit contrib (amount in dollars) / ID: DOL_F5500SF_SF_FAIL_TRANSMIT_CONTRIB_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 80 | `sf_party_in_int_not_rptd_ind` | `dol.form_5500_sf.sf_party_in_int_not_rptd_ind` | character varying(5) | Y | Short Form (5500-SF) party in int not rptd (indicator flag) / ID: DOL_F5500SF_SF_PARTY_IN_INT_NOT_RPTD_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 81 | `sf_party_in_int_not_rptd_amt` | `dol.form_5500_sf.sf_party_in_int_not_rptd_amt` | numeric | Y | Short Form (5500-SF) party in int not rptd (amount in dollars) / ID: DOL_F5500SF_SF_PARTY_IN_INT_NOT_RPTD_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 82 | `sf_plan_ins_fdlty_bond_ind` | `dol.form_5500_sf.sf_plan_ins_fdlty_bond_ind` | character varying(5) | Y | Short Form (5500-SF) plan ins fdlty bond (indicator flag) / ID: DOL_F5500SF_SF_PLAN_INS_FDLTY_BOND_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 83 | `sf_plan_ins_fdlty_bond_amt` | `dol.form_5500_sf.sf_plan_ins_fdlty_bond_amt` | numeric | Y | Short Form (5500-SF) plan ins fdlty bond (amount in dollars) / ID: DOL_F5500SF_SF_PLAN_INS_FDLTY_BOND_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 84 | `sf_loss_discv_dur_year_ind` | `dol.form_5500_sf.sf_loss_discv_dur_year_ind` | character varying(5) | Y | Short Form (5500-SF) loss discv dur year (indicator flag) / ID: DOL_F5500SF_SF_LOSS_DISCV_DUR_YEAR_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 85 | `sf_loss_discv_dur_year_amt` | `dol.form_5500_sf.sf_loss_discv_dur_year_amt` | numeric | Y | Short Form (5500-SF) loss discv dur year (amount in dollars) / ID: DOL_F5500SF_SF_LOSS_DISCV_DUR_YEAR_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 86 | `sf_broker_fees_paid_ind` | `dol.form_5500_sf.sf_broker_fees_paid_ind` | character varying(5) | Y | Short Form (5500-SF) broker fees paid (indicator flag) / ID: DOL_F5500SF_SF_BROKER_FEES_PAID_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 87 | `sf_broker_fees_paid_amt` | `dol.form_5500_sf.sf_broker_fees_paid_amt` | numeric | Y | Short Form (5500-SF) broker fees paid (amount in dollars) / ID: DOL_F5500SF_SF_BROKER_FEES_PAID_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 88 | `sf_fail_provide_benef_due_ind` | `dol.form_5500_sf.sf_fail_provide_benef_due_ind` | character varying(5) | Y | Short Form (5500-SF) fail provide benef due (indicator flag) / ID: DOL_F5500SF_SF_FAIL_PROVIDE_BENEF_DUE_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 89 | `sf_fail_provide_benef_due_amt` | `dol.form_5500_sf.sf_fail_provide_benef_due_amt` | numeric | Y | Short Form (5500-SF) fail provide benef due (amount in dollars) / ID: DOL_F5500SF_SF_FAIL_PROVIDE_BENEF_DUE_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 90 | `sf_partcp_loans_ind` | `dol.form_5500_sf.sf_partcp_loans_ind` | character varying(5) | Y | Short Form (5500-SF) partcp loans (indicator flag) / ID: DOL_F5500SF_SF_PARTCP_LOANS_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 91 | `sf_partcp_loans_eoy_amt` | `dol.form_5500_sf.sf_partcp_loans_eoy_amt` | numeric | Y | Short Form (5500-SF) partcp loans eoy (amount in dollars) / ID: DOL_F5500SF_SF_PARTCP_LOANS_EOY_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 92 | `sf_plan_blackout_period_ind` | `dol.form_5500_sf.sf_plan_blackout_period_ind` | character varying(5) | Y | Short Form (5500-SF) plan blackout period (indicator flag) / ID: DOL_F5500SF_SF_PLAN_BLACKOUT_PERIOD_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 93 | `sf_comply_blackout_notice_ind` | `dol.form_5500_sf.sf_comply_blackout_notice_ind` | character varying(5) | Y | Short Form (5500-SF) comply blackout notice (indicator flag) / ID: DOL_F5500SF_SF_COMPLY_BLACKOUT_NOTICE_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 94 | `sf_db_plan_funding_reqd_ind` | `dol.form_5500_sf.sf_db_plan_funding_reqd_ind` | character varying(5) | Y | Short Form (5500-SF) db plan funding reqd (indicator flag) / ID: DOL_F5500SF_SF_DB_PLAN_FUNDING_REQD_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 95 | `sf_dc_plan_funding_reqd_ind` | `dol.form_5500_sf.sf_dc_plan_funding_reqd_ind` | character varying(5) | Y | Short Form (5500-SF) dc plan funding reqd (indicator flag) / ID: DOL_F5500SF_SF_DC_PLAN_FUNDING_REQD_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 96 | `sf_ruling_letter_grant_date` | `dol.form_5500_sf.sf_ruling_letter_grant_date` | character varying(255) | Y | Short Form (5500-SF) ruling letter grant (date) / ID: DOL_F5500SF_SF_RULING_LETTER_GRANT_DATE / Format: YYYY-MM-DD | attribute | STRING | dol.column_metadata |
| 97 | `sf_sec_412_req_contrib_amt` | `dol.form_5500_sf.sf_sec_412_req_contrib_amt` | numeric | Y | Short Form (5500-SF) sec 412 req contrib (amount in dollars) / ID: DOL_F5500SF_SF_SEC_412_REQ_CONTRIB_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 98 | `sf_emplr_contrib_paid_amt` | `dol.form_5500_sf.sf_emplr_contrib_paid_amt` | numeric | Y | Short Form (5500-SF) emplr contribution paid (amount in dollars) / ID: DOL_F5500SF_SF_EMPLR_CONTRIB_PAID_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 99 | `sf_funding_deficiency_amt` | `dol.form_5500_sf.sf_funding_deficiency_amt` | numeric | Y | Short Form (5500-SF) funding deficiency (amount in dollars) / ID: DOL_F5500SF_SF_FUNDING_DEFICIENCY_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 100 | `sf_funding_deadline_ind` | `dol.form_5500_sf.sf_funding_deadline_ind` | character varying(5) | Y | Short Form (5500-SF) funding deadline (indicator flag) / ID: DOL_F5500SF_SF_FUNDING_DEADLINE_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 101 | `sf_res_term_plan_adpt_ind` | `dol.form_5500_sf.sf_res_term_plan_adpt_ind` | character varying(5) | Y | Short Form (5500-SF) res term plan adpt (indicator flag) / ID: DOL_F5500SF_SF_RES_TERM_PLAN_ADPT_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 102 | `sf_res_term_plan_adpt_amt` | `dol.form_5500_sf.sf_res_term_plan_adpt_amt` | numeric | Y | Short Form (5500-SF) res term plan adpt (amount in dollars) / ID: DOL_F5500SF_SF_RES_TERM_PLAN_ADPT_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 103 | `sf_all_plan_ast_distrib_ind` | `dol.form_5500_sf.sf_all_plan_ast_distrib_ind` | character varying(5) | Y | Short Form (5500-SF) all plan ast distrib (indicator flag) / ID: DOL_F5500SF_SF_ALL_PLAN_AST_DISTRIB_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 104 | `sf_admin_signed_date` | `dol.form_5500_sf.sf_admin_signed_date` | character varying(255) | Y | Plan Administrator (SF) signed (date) / ID: DOL_F5500SF_SF_ADMIN_SIGNED_DATE / Format: YYYY-MM-DD | attribute | STRING | dol.column_metadata |
| 105 | `sf_admin_signed_name` | `dol.form_5500_sf.sf_admin_signed_name` | character varying(255) | Y | Plan Administrator (SF) signed (name) / ID: DOL_F5500SF_SF_ADMIN_SIGNED_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 106 | `sf_spons_signed_date` | `dol.form_5500_sf.sf_spons_signed_date` | character varying(255) | Y | Plan Sponsor (SF) signed (date) / ID: DOL_F5500SF_SF_SPONS_SIGNED_DATE / Format: YYYY-MM-DD | attribute | STRING | dol.column_metadata |
| 107 | `sf_spons_signed_name` | `dol.form_5500_sf.sf_spons_signed_name` | character varying(255) | Y | Plan Sponsor (SF) signed (name) / ID: DOL_F5500SF_SF_SPONS_SIGNED_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 108 | `filing_status` | `dol.form_5500_sf.filing_status` | character varying(255) | Y | Filing status / ID: DOL_F5500SF_FILING_STATUS / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 109 | `date_received` | `dol.form_5500_sf.date_received` | character varying(255) | Y | Date filing was received by DOL / ID: DOL_F5500SF_DATE_RECEIVED / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 110 | `valid_admin_signature` | `dol.form_5500_sf.valid_admin_signature` | character varying(255) | Y | Valid administrative signature / ID: DOL_F5500SF_VALID_ADMIN_SIGNATURE / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 111 | `valid_sponsor_signature` | `dol.form_5500_sf.valid_sponsor_signature` | character varying(255) | Y | Valid sponsor signature / ID: DOL_F5500SF_VALID_SPONSOR_SIGNATURE / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 112 | `sf_admin_phone_num_foreign` | `dol.form_5500_sf.sf_admin_phone_num_foreign` | character varying(255) | Y | Plan Administrator (SF) phone number foreign / ID: DOL_F5500SF_SF_ADMIN_PHONE_NUM_FOREIGN / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 113 | `sf_spons_care_of_name` | `dol.form_5500_sf.sf_spons_care_of_name` | character varying(255) | Y | Plan Sponsor (SF) care of (name) / ID: DOL_F5500SF_SF_SPONS_CARE_OF_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 114 | `sf_spons_loc_foreign_address1` | `dol.form_5500_sf.sf_spons_loc_foreign_address1` | character varying(255) | Y | Plan Sponsor (SF) loc foreign address1 / ID: DOL_F5500SF_SF_SPONS_LOC_FOREIGN_ADDRESS1 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 115 | `sf_spons_loc_foreign_address2` | `dol.form_5500_sf.sf_spons_loc_foreign_address2` | character varying(255) | Y | Plan Sponsor (SF) loc foreign address2 / ID: DOL_F5500SF_SF_SPONS_LOC_FOREIGN_ADDRESS2 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 116 | `sf_spons_loc_foreign_city` | `dol.form_5500_sf.sf_spons_loc_foreign_city` | character varying(255) | Y | Plan Sponsor (SF) loc foreign city / ID: DOL_F5500SF_SF_SPONS_LOC_FOREIGN_CITY / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 117 | `sf_spons_loc_foreign_cntry` | `dol.form_5500_sf.sf_spons_loc_foreign_cntry` | character varying(255) | Y | Plan Sponsor (SF) loc foreign cntry / ID: DOL_F5500SF_SF_SPONS_LOC_FOREIGN_CNTRY / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 118 | `sf_spons_loc_foreign_postal_cd` | `dol.form_5500_sf.sf_spons_loc_foreign_postal_cd` | character varying(255) | Y | Plan Sponsor (SF) loc foreign postal cd / ID: DOL_F5500SF_SF_SPONS_LOC_FOREIGN_POSTAL_CD / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 119 | `sf_spons_loc_foreign_prov_stat` | `dol.form_5500_sf.sf_spons_loc_foreign_prov_stat` | character varying(255) | Y | Plan Sponsor (SF) loc foreign province stat / ID: DOL_F5500SF_SF_SPONS_LOC_FOREIGN_PROV_STAT / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 120 | `sf_spons_loc_us_address1` | `dol.form_5500_sf.sf_spons_loc_us_address1` | character varying(255) | Y | Plan Sponsor (SF) loc us address1 / ID: DOL_F5500SF_SF_SPONS_LOC_US_ADDRESS1 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 121 | `sf_spons_loc_us_address2` | `dol.form_5500_sf.sf_spons_loc_us_address2` | character varying(255) | Y | Plan Sponsor (SF) loc us address2 / ID: DOL_F5500SF_SF_SPONS_LOC_US_ADDRESS2 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 122 | `sf_spons_loc_us_city` | `dol.form_5500_sf.sf_spons_loc_us_city` | character varying(255) | Y | Plan Sponsor (SF) loc us city / ID: DOL_F5500SF_SF_SPONS_LOC_US_CITY / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 123 | `sf_spons_loc_us_state` | `dol.form_5500_sf.sf_spons_loc_us_state` | character varying(255) | Y | Plan Sponsor (SF) loc us state / ID: DOL_F5500SF_SF_SPONS_LOC_US_STATE / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 124 | `sf_spons_loc_us_zip` | `dol.form_5500_sf.sf_spons_loc_us_zip` | character varying(255) | Y | Plan Sponsor (SF) loc us (ZIP code) / ID: DOL_F5500SF_SF_SPONS_LOC_US_ZIP / Format: 5 or 9 digits | attribute | STRING | dol.column_metadata |
| 125 | `sf_spons_phone_num_foreign` | `dol.form_5500_sf.sf_spons_phone_num_foreign` | character varying(255) | Y | Plan Sponsor (SF) phone number foreign / ID: DOL_F5500SF_SF_SPONS_PHONE_NUM_FOREIGN / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 126 | `sf_admin_name_same_spon_ind` | `dol.form_5500_sf.sf_admin_name_same_spon_ind` | character varying(5) | Y | Plan Administrator (SF) name same spon (indicator flag) / ID: DOL_F5500SF_SF_ADMIN_NAME_SAME_SPON_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 127 | `sf_admin_addrss_same_spon_ind` | `dol.form_5500_sf.sf_admin_addrss_same_spon_ind` | character varying(5) | Y | Plan Administrator (SF) addrss same spon (indicator flag) / ID: DOL_F5500SF_SF_ADMIN_ADDRSS_SAME_SPON_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 128 | `sf_preparer_name` | `dol.form_5500_sf.sf_preparer_name` | character varying(255) | Y | Short Form (5500-SF) preparer (name) / ID: DOL_F5500SF_SF_PREPARER_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 129 | `sf_preparer_firm_name` | `dol.form_5500_sf.sf_preparer_firm_name` | character varying(255) | Y | Short Form (5500-SF) preparer firm (name) / ID: DOL_F5500SF_SF_PREPARER_FIRM_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 130 | `sf_preparer_us_address1` | `dol.form_5500_sf.sf_preparer_us_address1` | character varying(255) | Y | Short Form (5500-SF) preparer us address1 / ID: DOL_F5500SF_SF_PREPARER_US_ADDRESS1 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 131 | `sf_preparer_us_address2` | `dol.form_5500_sf.sf_preparer_us_address2` | character varying(255) | Y | Short Form (5500-SF) preparer us address2 / ID: DOL_F5500SF_SF_PREPARER_US_ADDRESS2 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 132 | `sf_preparer_us_city` | `dol.form_5500_sf.sf_preparer_us_city` | character varying(255) | Y | Short Form (5500-SF) preparer us city / ID: DOL_F5500SF_SF_PREPARER_US_CITY / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 133 | `sf_preparer_us_state` | `dol.form_5500_sf.sf_preparer_us_state` | character varying(255) | Y | Short Form (5500-SF) preparer us state / ID: DOL_F5500SF_SF_PREPARER_US_STATE / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 134 | `sf_preparer_us_zip` | `dol.form_5500_sf.sf_preparer_us_zip` | character varying(255) | Y | Short Form (5500-SF) preparer us (ZIP code) / ID: DOL_F5500SF_SF_PREPARER_US_ZIP / Format: 5 or 9 digits | attribute | STRING | dol.column_metadata |
| 135 | `sf_preparer_foreign_address1` | `dol.form_5500_sf.sf_preparer_foreign_address1` | character varying(255) | Y | Short Form (5500-SF) preparer foreign address1 / ID: DOL_F5500SF_SF_PREPARER_FOREIGN_ADDRESS1 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 136 | `sf_preparer_foreign_address2` | `dol.form_5500_sf.sf_preparer_foreign_address2` | character varying(255) | Y | Short Form (5500-SF) preparer foreign address2 / ID: DOL_F5500SF_SF_PREPARER_FOREIGN_ADDRESS2 / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 137 | `sf_preparer_foreign_city` | `dol.form_5500_sf.sf_preparer_foreign_city` | character varying(255) | Y | Short Form (5500-SF) preparer foreign city / ID: DOL_F5500SF_SF_PREPARER_FOREIGN_CITY / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 138 | `sf_preparer_foreign_prov_state` | `dol.form_5500_sf.sf_preparer_foreign_prov_state` | character varying(255) | Y | Short Form (5500-SF) preparer foreign province state / ID: DOL_F5500SF_SF_PREPARER_FOREIGN_PROV_STATE / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 139 | `sf_preparer_foreign_cntry` | `dol.form_5500_sf.sf_preparer_foreign_cntry` | character varying(255) | Y | Short Form (5500-SF) preparer foreign cntry / ID: DOL_F5500SF_SF_PREPARER_FOREIGN_CNTRY / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 140 | `sf_preparer_foreign_postal_cd` | `dol.form_5500_sf.sf_preparer_foreign_postal_cd` | character varying(255) | Y | Short Form (5500-SF) preparer foreign postal cd / ID: DOL_F5500SF_SF_PREPARER_FOREIGN_POSTAL_CD / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 141 | `sf_preparer_phone_num` | `dol.form_5500_sf.sf_preparer_phone_num` | character varying(255) | Y | Short Form (5500-SF) preparer phone (number/identifier) / ID: DOL_F5500SF_SF_PREPARER_PHONE_NUM / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 142 | `sf_preparer_phone_num_foreign` | `dol.form_5500_sf.sf_preparer_phone_num_foreign` | character varying(255) | Y | Short Form (5500-SF) preparer phone number foreign / ID: DOL_F5500SF_SF_PREPARER_PHONE_NUM_FOREIGN / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 143 | `sf_fdcry_trust_name` | `dol.form_5500_sf.sf_fdcry_trust_name` | character varying(255) | Y | Short Form (5500-SF) fdcry trust (name) / ID: DOL_F5500SF_SF_FDCRY_TRUST_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 144 | `sf_fdcry_trust_ein` | `dol.form_5500_sf.sf_fdcry_trust_ein` | character varying(255) | Y | Short Form (5500-SF) fdcry trust (Employer Identification Number) / ID: DOL_F5500SF_SF_FDCRY_TRUST_EIN / Format: 9 digits (XX-XXXXXXX) | identifier | STRING | dol.column_metadata |
| 145 | `sf_unp_min_cont_cur_yrtot_amt` | `dol.form_5500_sf.sf_unp_min_cont_cur_yrtot_amt` | numeric | Y | Short Form (5500-SF) unp min cont cur yrtot (amount in dollars) / ID: DOL_F5500SF_SF_UNP_MIN_CONT_CUR_YRTOT_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 146 | `sf_covered_pbgc_insurance_ind` | `dol.form_5500_sf.sf_covered_pbgc_insurance_ind` | character varying(5) | Y | Short Form (5500-SF) covered pbgc insurance (indicator flag) / ID: DOL_F5500SF_SF_COVERED_PBGC_INSURANCE_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 147 | `sf_tot_act_partcp_boy_cnt` | `dol.form_5500_sf.sf_tot_act_partcp_boy_cnt` | numeric | Y | Short Form (5500-SF) tot act participant boy (count/number) / ID: DOL_F5500SF_SF_TOT_ACT_PARTCP_BOY_CNT / Format: Whole number | attribute | NUMERIC | dol.column_metadata |
| 148 | `sf_tot_act_partcp_eoy_cnt` | `dol.form_5500_sf.sf_tot_act_partcp_eoy_cnt` | numeric | Y | Short Form (5500-SF) tot act participant eoy (count/number) / ID: DOL_F5500SF_SF_TOT_ACT_PARTCP_EOY_CNT / Format: Whole number | attribute | NUMERIC | dol.column_metadata |
| 149 | `sf_sep_partcp_partl_vstd_cnt` | `dol.form_5500_sf.sf_sep_partcp_partl_vstd_cnt` | numeric | Y | Short Form (5500-SF) sep participant partl vstd (count/number) / ID: DOL_F5500SF_SF_SEP_PARTCP_PARTL_VSTD_CNT / Format: Whole number | attribute | NUMERIC | dol.column_metadata |
| 150 | `sf_trus_inc_unrel_tax_inc_ind` | `dol.form_5500_sf.sf_trus_inc_unrel_tax_inc_ind` | character varying(5) | Y | Short Form (5500-SF) trus inc unrel tax inc (indicator flag) / ID: DOL_F5500SF_SF_TRUS_INC_UNREL_TAX_INC_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 151 | `sf_trus_inc_unrel_tax_inc_amt` | `dol.form_5500_sf.sf_trus_inc_unrel_tax_inc_amt` | numeric | Y | Short Form (5500-SF) trus inc unrel tax inc (amount in dollars) / ID: DOL_F5500SF_SF_TRUS_INC_UNREL_TAX_INC_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 152 | `sf_fdcry_truste_cust_name` | `dol.form_5500_sf.sf_fdcry_truste_cust_name` | character varying(255) | Y | Short Form (5500-SF) fdcry truste cust (name) / ID: DOL_F5500SF_SF_FDCRY_TRUSTE_CUST_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 153 | `sf_fdcry_truste_cust_phone_num` | `dol.form_5500_sf.sf_fdcry_truste_cust_phone_num` | character varying(255) | Y | Short Form (5500-SF) fdcry truste cust phone (number/identifier) / ID: DOL_F5500SF_SF_FDCRY_TRUSTE_CUST_PHONE_NUM / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 154 | `sf_fdcry_trus_cus_phon_numfore` | `dol.form_5500_sf.sf_fdcry_trus_cus_phon_numfore` | character varying(255) | Y | Short Form (5500-SF) fdcry trus cus phon numfore / ID: DOL_F5500SF_SF_FDCRY_TRUS_CUS_PHON_NUMFORE / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 155 | `sf_401k_plan_ind` | `dol.form_5500_sf.sf_401k_plan_ind` | character varying(5) | Y | Short Form (5500-SF) 401k plan (indicator flag) / ID: DOL_F5500SF_SF_401K_PLAN_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 156 | `sf_401k_satisfy_rqmts_ind` | `dol.form_5500_sf.sf_401k_satisfy_rqmts_ind` | character varying(5) | Y | Short Form (5500-SF) 401k satisfy rqmts (indicator flag) / ID: DOL_F5500SF_SF_401K_SATISFY_RQMTS_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 157 | `sf_adp_acp_test_ind` | `dol.form_5500_sf.sf_adp_acp_test_ind` | character varying(5) | Y | Short Form (5500-SF) adp acp test (indicator flag) / ID: DOL_F5500SF_SF_ADP_ACP_TEST_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 158 | `sf_mthd_used_satisfy_rqmts_ind` | `dol.form_5500_sf.sf_mthd_used_satisfy_rqmts_ind` | character varying(5) | Y | Short Form (5500-SF) mthd used satisfy rqmts (indicator flag) / ID: DOL_F5500SF_SF_MTHD_USED_SATISFY_RQMTS_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 159 | `sf_plan_satisfy_tests_ind` | `dol.form_5500_sf.sf_plan_satisfy_tests_ind` | character varying(5) | Y | Short Form (5500-SF) plan satisfy tests (indicator flag) / ID: DOL_F5500SF_SF_PLAN_SATISFY_TESTS_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 160 | `sf_plan_timely_amended_ind` | `dol.form_5500_sf.sf_plan_timely_amended_ind` | character varying(5) | Y | Short Form (5500-SF) plan timely amended (indicator flag) / ID: DOL_F5500SF_SF_PLAN_TIMELY_AMENDED_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 161 | `sf_last_plan_amendment_date` | `dol.form_5500_sf.sf_last_plan_amendment_date` | character varying(255) | Y | Short Form (5500-SF) last plan amendment (date) / ID: DOL_F5500SF_SF_LAST_PLAN_AMENDMENT_DATE / Format: YYYY-MM-DD | attribute | STRING | dol.column_metadata |
| 162 | `sf_tax_code` | `dol.form_5500_sf.sf_tax_code` | character varying(255) | Y | Short Form (5500-SF) tax (code value) / ID: DOL_F5500SF_SF_TAX_CODE / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 163 | `sf_last_opin_advi_date` | `dol.form_5500_sf.sf_last_opin_advi_date` | character varying(255) | Y | Short Form (5500-SF) last opinion advi (date) / ID: DOL_F5500SF_SF_LAST_OPIN_ADVI_DATE / Format: YYYY-MM-DD | attribute | STRING | dol.column_metadata |
| 164 | `sf_last_opin_advi_serial_num` | `dol.form_5500_sf.sf_last_opin_advi_serial_num` | character varying(255) | Y | Short Form (5500-SF) last opinion advisory serial (number/identifier) / ID: DOL_F5500SF_SF_LAST_OPIN_ADVI_SERIAL_NUM / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 165 | `sf_fav_determ_ltr_date` | `dol.form_5500_sf.sf_fav_determ_ltr_date` | character varying(255) | Y | Short Form (5500-SF) fav determination ltr (date) / ID: DOL_F5500SF_SF_FAV_DETERM_LTR_DATE / Format: YYYY-MM-DD | attribute | STRING | dol.column_metadata |
| 166 | `sf_plan_maintain_us_terri_ind` | `dol.form_5500_sf.sf_plan_maintain_us_terri_ind` | character varying(5) | Y | Short Form (5500-SF) plan maintain us terri (indicator flag) / ID: DOL_F5500SF_SF_PLAN_MAINTAIN_US_TERRI_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 167 | `sf_in_service_distrib_ind` | `dol.form_5500_sf.sf_in_service_distrib_ind` | character varying(5) | Y | Short Form (5500-SF) in service distrib (indicator flag) / ID: DOL_F5500SF_SF_IN_SERVICE_DISTRIB_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 168 | `sf_in_service_distrib_amt` | `dol.form_5500_sf.sf_in_service_distrib_amt` | numeric | Y | Short Form (5500-SF) in service distrib (amount in dollars) / ID: DOL_F5500SF_SF_IN_SERVICE_DISTRIB_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 169 | `sf_min_req_distrib_ind` | `dol.form_5500_sf.sf_min_req_distrib_ind` | character varying(5) | Y | Short Form (5500-SF) min req distrib (indicator flag) / ID: DOL_F5500SF_SF_MIN_REQ_DISTRIB_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 170 | `sf_admin_manual_sign_date` | `dol.form_5500_sf.sf_admin_manual_sign_date` | character varying(255) | Y | Plan Administrator (SF) manual sign (date) / ID: DOL_F5500SF_SF_ADMIN_MANUAL_SIGN_DATE / Format: YYYY-MM-DD | attribute | STRING | dol.column_metadata |
| 171 | `sf_admin_manual_signed_name` | `dol.form_5500_sf.sf_admin_manual_signed_name` | character varying(255) | Y | Plan Administrator (SF) manual signed (name) / ID: DOL_F5500SF_SF_ADMIN_MANUAL_SIGNED_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 172 | `sf_401k_design_based_safe_ind` | `dol.form_5500_sf.sf_401k_design_based_safe_ind` | character varying(5) | Y | Short Form (5500-SF) 401k design based safe (indicator flag) / ID: DOL_F5500SF_SF_401K_DESIGN_BASED_SAFE_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 173 | `sf_401k_prior_year_adp_ind` | `dol.form_5500_sf.sf_401k_prior_year_adp_ind` | character varying(5) | Y | Short Form (5500-SF) 401k prior year adp (indicator flag) / ID: DOL_F5500SF_SF_401K_PRIOR_YEAR_ADP_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 174 | `sf_401k_current_year_adp_ind` | `dol.form_5500_sf.sf_401k_current_year_adp_ind` | character varying(5) | Y | Short Form (5500-SF) 401k current year adp (indicator flag) / ID: DOL_F5500SF_SF_401K_CURRENT_YEAR_ADP_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 175 | `sf_401k_na_ind` | `dol.form_5500_sf.sf_401k_na_ind` | character varying(5) | Y | Short Form (5500-SF) 401k na (indicator flag) / ID: DOL_F5500SF_SF_401K_NA_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 176 | `sf_mthd_ratio_prcnt_test_ind` | `dol.form_5500_sf.sf_mthd_ratio_prcnt_test_ind` | character varying(5) | Y | Short Form (5500-SF) mthd ratio prcnt test (indicator flag) / ID: DOL_F5500SF_SF_MTHD_RATIO_PRCNT_TEST_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 177 | `sf_mthd_avg_bnft_test_ind` | `dol.form_5500_sf.sf_mthd_avg_bnft_test_ind` | character varying(5) | Y | Short Form (5500-SF) mthd avg benefit test (indicator flag) / ID: DOL_F5500SF_SF_MTHD_AVG_BNFT_TEST_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 178 | `sf_mthd_na_ind` | `dol.form_5500_sf.sf_mthd_na_ind` | character varying(5) | Y | Short Form (5500-SF) mthd na (indicator flag) / ID: DOL_F5500SF_SF_MTHD_NA_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 179 | `sf_distrib_made_employe_62_ind` | `dol.form_5500_sf.sf_distrib_made_employe_62_ind` | character varying(5) | Y | Short Form (5500-SF) distrib made employe 62 (indicator flag) / ID: DOL_F5500SF_SF_DISTRIB_MADE_EMPLOYE_62_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 180 | `sf_last_rpt_plan_name` | `dol.form_5500_sf.sf_last_rpt_plan_name` | character varying(255) | Y | Short Form (5500-SF) last rpt plan (name) / ID: DOL_F5500SF_SF_LAST_RPT_PLAN_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 181 | `sf_premium_filing_confirm_no` | `dol.form_5500_sf.sf_premium_filing_confirm_no` | character varying(255) | Y | Short Form (5500-SF) premium filing confirm no / ID: DOL_F5500SF_SF_PREMIUM_FILING_CONFIRM_NO / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 182 | `sf_spons_manual_signed_date` | `dol.form_5500_sf.sf_spons_manual_signed_date` | character varying(255) | Y | Plan Sponsor (SF) manual signed (date) / ID: DOL_F5500SF_SF_SPONS_MANUAL_SIGNED_DATE / Format: YYYY-MM-DD | attribute | STRING | dol.column_metadata |
| 183 | `sf_spons_manual_signed_name` | `dol.form_5500_sf.sf_spons_manual_signed_name` | character varying(255) | Y | Plan Sponsor (SF) manual signed (name) / ID: DOL_F5500SF_SF_SPONS_MANUAL_SIGNED_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 184 | `sf_pbgc_notified_cd` | `dol.form_5500_sf.sf_pbgc_notified_cd` | character varying(255) | Y | Short Form (5500-SF) pbgc notified cd / ID: DOL_F5500SF_SF_PBGC_NOTIFIED_CD / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 185 | `sf_pbgc_notified_explan_text` | `dol.form_5500_sf.sf_pbgc_notified_explan_text` | text | Y | Short Form (5500-SF) pbgc notified explan (text description) / ID: DOL_F5500SF_SF_PBGC_NOTIFIED_EXPLAN_TEXT / Format: Variable length text | attribute | STRING | dol.column_metadata |
| 186 | `sf_adopted_plan_perm_sec_act` | `dol.form_5500_sf.sf_adopted_plan_perm_sec_act` | character varying(255) | Y | Short Form (5500-SF) adopted plan perm sec act / ID: DOL_F5500SF_SF_ADOPTED_PLAN_PERM_SEC_ACT / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 187 | `collectively_bargained` | `dol.form_5500_sf.collectively_bargained` | character varying(255) | Y | Collectively bargained / ID: DOL_F5500SF_COLLECTIVELY_BARGAINED / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 188 | `sf_partcp_account_bal_cnt_boy` | `dol.form_5500_sf.sf_partcp_account_bal_cnt_boy` | character varying(255) | Y | Short Form (5500-SF) partcp account balance cnt boy / ID: DOL_F5500SF_SF_PARTCP_ACCOUNT_BAL_CNT_BOY / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 189 | `sf_401k_design_based_safe_harbor_ind` | `dol.form_5500_sf.sf_401k_design_based_safe_harbor_ind` | character varying(5) | Y | Short Form (5500-SF) 401k design based safe harbor (indicator flag) / ID: DOL_F5500SF_SF_401K_DESIGN_BASED_SAFE_HARBOR_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 190 | `sf_401k_prior_year_adp_test_ind` | `dol.form_5500_sf.sf_401k_prior_year_adp_test_ind` | character varying(5) | Y | Short Form (5500-SF) 401k prior year adp test (indicator flag) / ID: DOL_F5500SF_SF_401K_PRIOR_YEAR_ADP_TEST_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 191 | `sf_401k_current_year_adp_test_ind` | `dol.form_5500_sf.sf_401k_current_year_adp_test_ind` | character varying(5) | Y | Short Form (5500-SF) 401k current year adp test (indicator flag) / ID: DOL_F5500SF_SF_401K_CURRENT_YEAR_ADP_TEST_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 192 | `sf_opin_letter_date` | `dol.form_5500_sf.sf_opin_letter_date` | character varying(255) | Y | Short Form (5500-SF) opin letter (date) / ID: DOL_F5500SF_SF_OPIN_LETTER_DATE / Format: YYYY-MM-DD | attribute | STRING | dol.column_metadata |
| 193 | `sf_opin_letter_serial_num` | `dol.form_5500_sf.sf_opin_letter_serial_num` | character varying(255) | Y | Short Form (5500-SF) opin letter serial (number/identifier) / ID: DOL_F5500SF_SF_OPIN_LETTER_SERIAL_NUM / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 194 | `form_year` | `dol.form_5500_sf.form_year` | character varying(10) | Y | Tax/plan year for this filing / ID: DOL_F5500SF_FORM_YEAR / Format: Up to 10 characters | attribute | STRING | dol.column_metadata |
| 195 | `created_at` | `dol.form_5500_sf.created_at` | timestamp with time zone | Y | Record creation timestamp / ID: DOL_F5500SF_CREATED_AT / Format: YYYY-MM-DD HH:MM:SS | attribute | ISO-8601 | dol.column_metadata |
| 196 | `updated_at` | `dol.form_5500_sf.updated_at` | timestamp with time zone | Y | Record last update timestamp / ID: DOL_F5500SF_UPDATED_AT / Format: YYYY-MM-DD HH:MM:SS | attribute | ISO-8601 | dol.column_metadata |

### `dol.form_5500_sf_part7` -- UNREGISTERED -- 10,613 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `dol.form_5500_sf_part7.id` | bigint | N | Auto-increment surrogate primary key | attribute | INTEGER | dol.column_metadata |
| 2 | `ack_id` | `dol.form_5500_sf_part7.ack_id` | character varying(50) | N | DOL acknowledgment ID — unique filing identifier. Foreign key to dol.form_5500.ack_id or dol.form_5500_sf.ack_id for joining across schedules | attribute | STRING | dol.column_metadata |
| 3 | `row_order` | `dol.form_5500_sf_part7.row_order` | integer | Y | Sequence number within a single filing — preserves original CSV row ordering when multiple line items exist per filing | attribute | INTEGER | dol.column_metadata |
| 4 | `sf_plan_transfer_name` | `dol.form_5500_sf_part7.sf_plan_transfer_name` | character varying(500) | Y | Name of the plan to which assets were transferred | attribute | STRING | dol.column_metadata |
| 5 | `sf_plan_transfer_ein` | `dol.form_5500_sf_part7.sf_plan_transfer_ein` | character varying(20) | Y | EIN (Employer Identification Number) of the receiving plan | identifier | STRING | dol.column_metadata |
| 6 | `sf_plan_transfer_pn` | `dol.form_5500_sf_part7.sf_plan_transfer_pn` | character varying(10) | Y | Plan number of the receiving plan | identifier | STRING | dol.column_metadata |
| 7 | `form_year` | `dol.form_5500_sf_part7.form_year` | character varying(10) | Y | Filing year (2023, 2024, 2025, etc.) — partition key for cross-year queries | attribute | STRING | dol.column_metadata |
| 8 | `created_at` | `dol.form_5500_sf_part7.created_at` | timestamp with time zone | N | Timestamp when this row was loaded into the database | attribute | ISO-8601 | dol.column_metadata |

### `dol.pressure_signals` -- MV -- 0 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `signal_id` | `dol.pressure_signals.signal_id` | uuid | N | Signal Id | identifier | UUID | inferred |
| 2 | `company_unique_id` | `dol.pressure_signals.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 3 | `signal_type` | `dol.pressure_signals.signal_type` | character varying(50) | N | Signal Type | attribute | STRING | inferred |
| 4 | `pressure_domain` | `dol.pressure_signals.pressure_domain` | USER-DEFINED | N | Pressure Domain | attribute | STRING | inferred |
| 5 | `pressure_class` | `dol.pressure_signals.pressure_class` | USER-DEFINED | Y | Pressure Class | attribute | STRING | inferred |
| 6 | `signal_value` | `dol.pressure_signals.signal_value` | jsonb | N | Signal Value | attribute | JSONB | inferred |
| 7 | `magnitude` | `dol.pressure_signals.magnitude` | integer | N | Magnitude | attribute | INTEGER | inferred |
| 8 | `detected_at` | `dol.pressure_signals.detected_at` | timestamp with time zone | N | When this event/signal was detected | attribute | ISO-8601 | inferred |
| 9 | `expires_at` | `dol.pressure_signals.expires_at` | timestamp with time zone | N | When this record expires | attribute | ISO-8601 | inferred |
| 10 | `correlation_id` | `dol.pressure_signals.correlation_id` | uuid | Y | UUID linking related operations across tables | identifier | UUID | inferred |
| 11 | `source_record_id` | `dol.pressure_signals.source_record_id` | text | Y | Source Record Id | identifier | STRING | inferred |
| 12 | `created_at` | `dol.pressure_signals.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |

### `dol.renewal_calendar` -- CANONICAL -- 0 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `renewal_id` | `dol.renewal_calendar.renewal_id` | uuid | N | Renewal Id | identifier | UUID | inferred |
| 2 | `company_unique_id` | `dol.renewal_calendar.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 3 | `schedule_id` | `dol.renewal_calendar.schedule_id` | uuid | Y | Schedule Id | identifier | UUID | inferred |
| 4 | `filing_id` | `dol.renewal_calendar.filing_id` | uuid | Y | Filing Id | identifier | UUID | inferred |
| 5 | `renewal_month` | `dol.renewal_calendar.renewal_month` | integer | Y | Plan year begin month (1-12) | attribute | INTEGER | inferred |
| 6 | `renewal_year` | `dol.renewal_calendar.renewal_year` | integer | Y | Renewal Year | attribute | INTEGER | inferred |
| 7 | `renewal_date` | `dol.renewal_calendar.renewal_date` | date | Y | Renewal Date | attribute | DATE | inferred |
| 8 | `plan_name` | `dol.renewal_calendar.plan_name` | character varying(500) | Y | Plan Name | attribute | STRING | inferred |
| 9 | `carrier_name` | `dol.renewal_calendar.carrier_name` | character varying(500) | Y | Carrier Name | attribute | STRING | inferred |
| 10 | `is_upcoming` | `dol.renewal_calendar.is_upcoming` | boolean | N | Whether this record upcoming | attribute | BOOLEAN | inferred |
| 11 | `days_until_renewal` | `dol.renewal_calendar.days_until_renewal` | integer | Y | Days Until Renewal | attribute | INTEGER | inferred |
| 12 | `created_at` | `dol.renewal_calendar.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 13 | `updated_at` | `dol.renewal_calendar.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |

### `dol.schedule_a` -- CANONICAL -- 625,520 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `schedule_id` | `dol.schedule_a.schedule_id` | uuid | N | Schedule id / ID: DOL_SCHA_SCHEDULE_ID / Format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | attribute | UUID | dol.column_metadata |
| 2 | `filing_id` | `dol.schedule_a.filing_id` | uuid | Y | Unique filing identifier (UUID) / ID: DOL_SCHA_FILING_ID / Format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | attribute | UUID | dol.column_metadata |
| 3 | `company_unique_id` | `dol.schedule_a.company_unique_id` | text | Y | Company unique id / ID: DOL_SCHA_COMPANY_UNIQUE_ID / Format: Variable length text | attribute | STRING | dol.column_metadata |
| 4 | `sponsor_state` | `dol.schedule_a.sponsor_state` | character varying(10) | Y | Sponsor state (derived from Form 5500 for Schedule A) / ID: DOL_SCHA_SPONSOR_STATE / Format: Up to 10 characters | attribute | STRING | dol.column_metadata |
| 5 | `sponsor_name` | `dol.schedule_a.sponsor_name` | character varying(255) | Y | Sponsor name (derived from Form 5500 for Schedule A) / ID: DOL_SCHA_SPONSOR_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 6 | `ack_id` | `dol.schedule_a.ack_id` | character varying(255) | Y | DOL acknowledgment ID for the filing / ID: DOL_SCHA_ACK_ID / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 7 | `form_id` | `dol.schedule_a.form_id` | character varying(255) | Y | Form type identifier / ID: DOL_SCHA_FORM_ID / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 8 | `sch_a_plan_year_begin_date` | `dol.schedule_a.sch_a_plan_year_begin_date` | character varying(30) | Y | Schedule A plan year begin (date) / ID: DOL_SCHA_SCH_A_PLAN_YEAR_BEGIN_DATE / Format: YYYY-MM-DD | attribute | STRING | dol.column_metadata |
| 9 | `sch_a_plan_year_end_date` | `dol.schedule_a.sch_a_plan_year_end_date` | character varying(30) | Y | Schedule A plan year end (date) / ID: DOL_SCHA_SCH_A_PLAN_YEAR_END_DATE / Format: YYYY-MM-DD | attribute | STRING | dol.column_metadata |
| 10 | `sch_a_plan_num` | `dol.schedule_a.sch_a_plan_num` | character varying(255) | Y | Schedule A plan (number/identifier) / ID: DOL_SCHA_SCH_A_PLAN_NUM / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 11 | `sch_a_ein` | `dol.schedule_a.sch_a_ein` | character varying(20) | Y | Schedule A ein / ID: DOL_SCHA_SCH_A_EIN / Format: 9 digits (XX-XXXXXXX) | identifier | STRING | dol.column_metadata |
| 12 | `ins_carrier_name` | `dol.schedule_a.ins_carrier_name` | character varying(255) | Y | Name of insurance carrier / ID: DOL_SCHA_INS_CARRIER_NAME / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 13 | `ins_carrier_ein` | `dol.schedule_a.ins_carrier_ein` | character varying(20) | Y | Insurance carrier EIN / ID: DOL_SCHA_INS_CARRIER_EIN / Format: 9 digits (XX-XXXXXXX) | identifier | STRING | dol.column_metadata |
| 14 | `ins_carrier_naic_code` | `dol.schedule_a.ins_carrier_naic_code` | character varying(255) | Y | Insurance carrier NAIC code (5 digits) / ID: DOL_SCHA_INS_CARRIER_NAIC_CODE / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 15 | `ins_contract_num` | `dol.schedule_a.ins_contract_num` | character varying(255) | Y | Insurance contract/policy number / ID: DOL_SCHA_INS_CONTRACT_NUM / Format: Up to 255 characters | attribute | STRING | dol.column_metadata |
| 16 | `ins_prsn_covered_eoy_cnt` | `dol.schedule_a.ins_prsn_covered_eoy_cnt` | numeric | Y | Persons covered at end of year / ID: DOL_SCHA_INS_PRSN_COVERED_EOY_CNT / Format: Whole number | attribute | NUMERIC | dol.column_metadata |
| 17 | `ins_policy_from_date` | `dol.schedule_a.ins_policy_from_date` | character varying(30) | Y | Policy effective start date / ID: DOL_SCHA_INS_POLICY_FROM_DATE / Format: YYYY-MM-DD | attribute | STRING | dol.column_metadata |
| 18 | `ins_policy_to_date` | `dol.schedule_a.ins_policy_to_date` | character varying(30) | Y | Policy effective end date / ID: DOL_SCHA_INS_POLICY_TO_DATE / Format: YYYY-MM-DD | attribute | STRING | dol.column_metadata |
| 19 | `ins_broker_comm_tot_amt` | `dol.schedule_a.ins_broker_comm_tot_amt` | numeric | Y | Total broker commissions paid / ID: DOL_SCHA_INS_BROKER_COMM_TOT_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 20 | `ins_broker_fees_tot_amt` | `dol.schedule_a.ins_broker_fees_tot_amt` | numeric | Y | Total broker fees paid / ID: DOL_SCHA_INS_BROKER_FEES_TOT_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 21 | `pension_eoy_gen_acct_amt` | `dol.schedule_a.pension_eoy_gen_acct_amt` | numeric | Y | Pension general account value at EOY / ID: DOL_SCHA_PENSION_EOY_GEN_ACCT_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 22 | `pension_eoy_sep_acct_amt` | `dol.schedule_a.pension_eoy_sep_acct_amt` | numeric | Y | Pension separate account value at EOY / ID: DOL_SCHA_PENSION_EOY_SEP_ACCT_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 23 | `pension_basis_rates_text` | `dol.schedule_a.pension_basis_rates_text` | text | Y | Pension basis rates (text description) / ID: DOL_SCHA_PENSION_BASIS_RATES_TEXT / Format: Variable length text | attribute | STRING | dol.column_metadata |
| 24 | `pension_prem_paid_tot_amt` | `dol.schedule_a.pension_prem_paid_tot_amt` | numeric | Y | Total pension premiums paid / ID: DOL_SCHA_PENSION_PREM_PAID_TOT_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 25 | `pension_unpaid_premium_amt` | `dol.schedule_a.pension_unpaid_premium_amt` | numeric | Y | Unpaid pension premiums / ID: DOL_SCHA_PENSION_UNPAID_PREMIUM_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 26 | `pension_contract_cost_amt` | `dol.schedule_a.pension_contract_cost_amt` | numeric | Y | Pension contract cost / ID: DOL_SCHA_PENSION_CONTRACT_COST_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 27 | `pension_cost_text` | `dol.schedule_a.pension_cost_text` | text | Y | Pension cost (text description) / ID: DOL_SCHA_PENSION_COST_TEXT / Format: Variable length text | attribute | STRING | dol.column_metadata |
| 28 | `alloc_contracts_indiv_ind` | `dol.schedule_a.alloc_contracts_indiv_ind` | character varying(5) | Y | Allocated Contract contracts indiv (indicator flag) / ID: DOL_SCHA_ALLOC_CONTRACTS_INDIV_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 29 | `alloc_contracts_group_ind` | `dol.schedule_a.alloc_contracts_group_ind` | character varying(5) | Y | Allocated Contract contracts group (indicator flag) / ID: DOL_SCHA_ALLOC_CONTRACTS_GROUP_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 30 | `alloc_contracts_other_ind` | `dol.schedule_a.alloc_contracts_other_ind` | character varying(5) | Y | Allocated Contract contracts other (indicator flag) / ID: DOL_SCHA_ALLOC_CONTRACTS_OTHER_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 31 | `alloc_contracts_other_text` | `dol.schedule_a.alloc_contracts_other_text` | text | Y | Allocated Contract contracts other (text description) / ID: DOL_SCHA_ALLOC_CONTRACTS_OTHER_TEXT / Format: Variable length text | attribute | STRING | dol.column_metadata |
| 32 | `pens_distr_bnft_term_pln_ind` | `dol.schedule_a.pens_distr_bnft_term_pln_ind` | character varying(5) | Y | Pens distr benefit term pln (indicator flag) / ID: DOL_SCHA_PENS_DISTR_BNFT_TERM_PLN_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 33 | `unalloc_contracts_dep_adm_ind` | `dol.schedule_a.unalloc_contracts_dep_adm_ind` | character varying(5) | Y | Unallocated Contract contracts dep adm (indicator flag) / ID: DOL_SCHA_UNALLOC_CONTRACTS_DEP_ADM_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 34 | `unal_contrac_imm_part_guar_ind` | `dol.schedule_a.unal_contrac_imm_part_guar_ind` | character varying(5) | Y | Unallocated Contract contrac imm part guar (indicator flag) / ID: DOL_SCHA_UNAL_CONTRAC_IMM_PART_GUAR_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 35 | `unal_contracts_guar_invest_ind` | `dol.schedule_a.unal_contracts_guar_invest_ind` | character varying(5) | Y | Unallocated Contract contracts guar invest (indicator flag) / ID: DOL_SCHA_UNAL_CONTRACTS_GUAR_INVEST_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 36 | `unalloc_contracts_other_ind` | `dol.schedule_a.unalloc_contracts_other_ind` | character varying(5) | Y | Unallocated Contract contracts other (indicator flag) / ID: DOL_SCHA_UNALLOC_CONTRACTS_OTHER_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 37 | `unalloc_contracts_other_text` | `dol.schedule_a.unalloc_contracts_other_text` | text | Y | Unallocated Contract contracts other (text description) / ID: DOL_SCHA_UNALLOC_CONTRACTS_OTHER_TEXT / Format: Variable length text | attribute | STRING | dol.column_metadata |
| 38 | `pension_end_prev_bal_amt` | `dol.schedule_a.pension_end_prev_bal_amt` | numeric | Y | Pension end previous bal (amount in dollars) / ID: DOL_SCHA_PENSION_END_PREV_BAL_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 39 | `pension_contrib_dep_amt` | `dol.schedule_a.pension_contrib_dep_amt` | numeric | Y | Pension contributions deposited / ID: DOL_SCHA_PENSION_CONTRIB_DEP_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 40 | `pension_divnd_cr_dep_amt` | `dol.schedule_a.pension_divnd_cr_dep_amt` | numeric | Y | Pension dividend credits deposited / ID: DOL_SCHA_PENSION_DIVND_CR_DEP_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 41 | `pension_int_cr_dur_yr_amt` | `dol.schedule_a.pension_int_cr_dur_yr_amt` | numeric | Y | Pension interest credits during year / ID: DOL_SCHA_PENSION_INT_CR_DUR_YR_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 42 | `pension_transfer_from_amt` | `dol.schedule_a.pension_transfer_from_amt` | numeric | Y | Pension transfer from (amount in dollars) / ID: DOL_SCHA_PENSION_TRANSFER_FROM_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 43 | `pension_other_amt` | `dol.schedule_a.pension_other_amt` | numeric | Y | Pension other (amount in dollars) / ID: DOL_SCHA_PENSION_OTHER_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 44 | `pension_other_text` | `dol.schedule_a.pension_other_text` | text | Y | Pension other (text description) / ID: DOL_SCHA_PENSION_OTHER_TEXT / Format: Variable length text | attribute | STRING | dol.column_metadata |
| 45 | `pension_tot_additions_amt` | `dol.schedule_a.pension_tot_additions_amt` | numeric | Y | Pension tot additions (amount in dollars) / ID: DOL_SCHA_PENSION_TOT_ADDITIONS_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 46 | `pension_tot_bal_addn_amt` | `dol.schedule_a.pension_tot_bal_addn_amt` | numeric | Y | Pension tot balance addn (amount in dollars) / ID: DOL_SCHA_PENSION_TOT_BAL_ADDN_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 47 | `pension_bnfts_dsbrsd_amt` | `dol.schedule_a.pension_bnfts_dsbrsd_amt` | numeric | Y | Pension benefits disbursed / ID: DOL_SCHA_PENSION_BNFTS_DSBRSD_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 48 | `pension_admin_chrg_amt` | `dol.schedule_a.pension_admin_chrg_amt` | numeric | Y | Pension administrative charges / ID: DOL_SCHA_PENSION_ADMIN_CHRG_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 49 | `pension_transfer_to_amt` | `dol.schedule_a.pension_transfer_to_amt` | numeric | Y | Pension transfer to (amount in dollars) / ID: DOL_SCHA_PENSION_TRANSFER_TO_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 50 | `pension_oth_ded_amt` | `dol.schedule_a.pension_oth_ded_amt` | numeric | Y | Pension oth ded (amount in dollars) / ID: DOL_SCHA_PENSION_OTH_DED_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 51 | `pension_oth_ded_text` | `dol.schedule_a.pension_oth_ded_text` | text | Y | Pension oth ded (text description) / ID: DOL_SCHA_PENSION_OTH_DED_TEXT / Format: Variable length text | attribute | STRING | dol.column_metadata |
| 52 | `pension_tot_ded_amt` | `dol.schedule_a.pension_tot_ded_amt` | numeric | Y | Pension tot ded (amount in dollars) / ID: DOL_SCHA_PENSION_TOT_DED_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 53 | `pension_eoy_bal_amt` | `dol.schedule_a.pension_eoy_bal_amt` | numeric | Y | Pension end of year balance / ID: DOL_SCHA_PENSION_EOY_BAL_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 54 | `wlfr_bnft_health_ind` | `dol.schedule_a.wlfr_bnft_health_ind` | character varying(5) | Y | Plan provides health benefits / ID: DOL_SCHA_WLFR_BNFT_HEALTH_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 55 | `wlfr_bnft_dental_ind` | `dol.schedule_a.wlfr_bnft_dental_ind` | character varying(5) | Y | Plan provides dental benefits / ID: DOL_SCHA_WLFR_BNFT_DENTAL_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 56 | `wlfr_bnft_vision_ind` | `dol.schedule_a.wlfr_bnft_vision_ind` | character varying(5) | Y | Plan provides vision benefits / ID: DOL_SCHA_WLFR_BNFT_VISION_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 57 | `wlfr_bnft_life_insur_ind` | `dol.schedule_a.wlfr_bnft_life_insur_ind` | character varying(5) | Y | Plan provides life insurance / ID: DOL_SCHA_WLFR_BNFT_LIFE_INSUR_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 58 | `wlfr_bnft_temp_disab_ind` | `dol.schedule_a.wlfr_bnft_temp_disab_ind` | character varying(5) | Y | Plan provides temporary disability / ID: DOL_SCHA_WLFR_BNFT_TEMP_DISAB_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 59 | `wlfr_bnft_long_term_disab_ind` | `dol.schedule_a.wlfr_bnft_long_term_disab_ind` | character varying(5) | Y | Plan provides long-term disability / ID: DOL_SCHA_WLFR_BNFT_LONG_TERM_DISAB_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 60 | `wlfr_bnft_unemp_ind` | `dol.schedule_a.wlfr_bnft_unemp_ind` | character varying(5) | Y | Plan provides unemployment benefits / ID: DOL_SCHA_WLFR_BNFT_UNEMP_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 61 | `wlfr_bnft_drug_ind` | `dol.schedule_a.wlfr_bnft_drug_ind` | character varying(5) | Y | Plan provides prescription drug benefits / ID: DOL_SCHA_WLFR_BNFT_DRUG_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 62 | `wlfr_bnft_stop_loss_ind` | `dol.schedule_a.wlfr_bnft_stop_loss_ind` | character varying(5) | Y | Plan has stop-loss coverage / ID: DOL_SCHA_WLFR_BNFT_STOP_LOSS_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 63 | `wlfr_bnft_hmo_ind` | `dol.schedule_a.wlfr_bnft_hmo_ind` | character varying(5) | Y | Plan uses HMO arrangement / ID: DOL_SCHA_WLFR_BNFT_HMO_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 64 | `wlfr_bnft_ppo_ind` | `dol.schedule_a.wlfr_bnft_ppo_ind` | character varying(5) | Y | Plan uses PPO arrangement / ID: DOL_SCHA_WLFR_BNFT_PPO_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 65 | `wlfr_bnft_indemnity_ind` | `dol.schedule_a.wlfr_bnft_indemnity_ind` | character varying(5) | Y | Plan uses indemnity arrangement / ID: DOL_SCHA_WLFR_BNFT_INDEMNITY_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 66 | `wlfr_bnft_other_ind` | `dol.schedule_a.wlfr_bnft_other_ind` | character varying(5) | Y | Plan provides other welfare benefits / ID: DOL_SCHA_WLFR_BNFT_OTHER_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 67 | `wlfr_type_bnft_oth_text` | `dol.schedule_a.wlfr_type_bnft_oth_text` | text | Y | Welfare Benefit type benefit oth (text description) / ID: DOL_SCHA_WLFR_TYPE_BNFT_OTH_TEXT / Format: Variable length text | attribute | STRING | dol.column_metadata |
| 68 | `wlfr_premium_rcvd_amt` | `dol.schedule_a.wlfr_premium_rcvd_amt` | numeric | Y | Welfare Benefit premium rcvd (amount in dollars) / ID: DOL_SCHA_WLFR_PREMIUM_RCVD_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 69 | `wlfr_unpaid_due_amt` | `dol.schedule_a.wlfr_unpaid_due_amt` | numeric | Y | Welfare Benefit unpaid due (amount in dollars) / ID: DOL_SCHA_WLFR_UNPAID_DUE_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 70 | `wlfr_reserve_amt` | `dol.schedule_a.wlfr_reserve_amt` | numeric | Y | Welfare Benefit reserve (amount in dollars) / ID: DOL_SCHA_WLFR_RESERVE_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 71 | `wlfr_tot_earned_prem_amt` | `dol.schedule_a.wlfr_tot_earned_prem_amt` | numeric | Y | Welfare Benefit tot earned prem (amount in dollars) / ID: DOL_SCHA_WLFR_TOT_EARNED_PREM_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 72 | `wlfr_claims_paid_amt` | `dol.schedule_a.wlfr_claims_paid_amt` | numeric | Y | Welfare Benefit claims paid (amount in dollars) / ID: DOL_SCHA_WLFR_CLAIMS_PAID_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 73 | `wlfr_incr_reserve_amt` | `dol.schedule_a.wlfr_incr_reserve_amt` | numeric | Y | Welfare Benefit incr reserve (amount in dollars) / ID: DOL_SCHA_WLFR_INCR_RESERVE_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 74 | `wlfr_incurred_claim_amt` | `dol.schedule_a.wlfr_incurred_claim_amt` | numeric | Y | Welfare Benefit incurred claim (amount in dollars) / ID: DOL_SCHA_WLFR_INCURRED_CLAIM_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 75 | `wlfr_claims_chrgd_amt` | `dol.schedule_a.wlfr_claims_chrgd_amt` | numeric | Y | Welfare Benefit claims chrgd (amount in dollars) / ID: DOL_SCHA_WLFR_CLAIMS_CHRGD_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 76 | `wlfr_ret_commissions_amt` | `dol.schedule_a.wlfr_ret_commissions_amt` | numeric | Y | Welfare Benefit ret commissions (amount in dollars) / ID: DOL_SCHA_WLFR_RET_COMMISSIONS_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 77 | `wlfr_ret_admin_amt` | `dol.schedule_a.wlfr_ret_admin_amt` | numeric | Y | Welfare Benefit ret admin (amount in dollars) / ID: DOL_SCHA_WLFR_RET_ADMIN_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 78 | `wlfr_ret_oth_cost_amt` | `dol.schedule_a.wlfr_ret_oth_cost_amt` | numeric | Y | Welfare Benefit ret other cost (amount in dollars) / ID: DOL_SCHA_WLFR_RET_OTH_COST_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 79 | `wlfr_ret_oth_expense_amt` | `dol.schedule_a.wlfr_ret_oth_expense_amt` | numeric | Y | Welfare Benefit ret other expense (amount in dollars) / ID: DOL_SCHA_WLFR_RET_OTH_EXPENSE_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 80 | `wlfr_ret_taxes_amt` | `dol.schedule_a.wlfr_ret_taxes_amt` | numeric | Y | Welfare Benefit ret taxes (amount in dollars) / ID: DOL_SCHA_WLFR_RET_TAXES_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 81 | `wlfr_ret_charges_amt` | `dol.schedule_a.wlfr_ret_charges_amt` | numeric | Y | Welfare Benefit ret charges (amount in dollars) / ID: DOL_SCHA_WLFR_RET_CHARGES_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 82 | `wlfr_ret_oth_chrgs_amt` | `dol.schedule_a.wlfr_ret_oth_chrgs_amt` | numeric | Y | Welfare Benefit ret other chrgs (amount in dollars) / ID: DOL_SCHA_WLFR_RET_OTH_CHRGS_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 83 | `wlfr_ret_tot_amt` | `dol.schedule_a.wlfr_ret_tot_amt` | numeric | Y | Welfare Benefit ret tot (amount in dollars) / ID: DOL_SCHA_WLFR_RET_TOT_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 84 | `wlfr_refund_cash_ind` | `dol.schedule_a.wlfr_refund_cash_ind` | character varying(5) | Y | Welfare Benefit refund cash (indicator flag) / ID: DOL_SCHA_WLFR_REFUND_CASH_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 85 | `wlfr_refund_credit_ind` | `dol.schedule_a.wlfr_refund_credit_ind` | character varying(5) | Y | Welfare Benefit refund credit (indicator flag) / ID: DOL_SCHA_WLFR_REFUND_CREDIT_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 86 | `wlfr_refund_amt` | `dol.schedule_a.wlfr_refund_amt` | numeric | Y | Welfare Benefit refund (amount in dollars) / ID: DOL_SCHA_WLFR_REFUND_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 87 | `wlfr_held_bnfts_amt` | `dol.schedule_a.wlfr_held_bnfts_amt` | numeric | Y | Welfare Benefit held bnfts (amount in dollars) / ID: DOL_SCHA_WLFR_HELD_BNFTS_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 88 | `wlfr_claims_reserve_amt` | `dol.schedule_a.wlfr_claims_reserve_amt` | numeric | Y | Welfare Benefit claims reserve (amount in dollars) / ID: DOL_SCHA_WLFR_CLAIMS_RESERVE_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 89 | `wlfr_oth_reserve_amt` | `dol.schedule_a.wlfr_oth_reserve_amt` | numeric | Y | Welfare Benefit oth reserve (amount in dollars) / ID: DOL_SCHA_WLFR_OTH_RESERVE_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 90 | `wlfr_divnds_due_amt` | `dol.schedule_a.wlfr_divnds_due_amt` | numeric | Y | Welfare Benefit divnds due (amount in dollars) / ID: DOL_SCHA_WLFR_DIVNDS_DUE_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 91 | `wlfr_tot_charges_paid_amt` | `dol.schedule_a.wlfr_tot_charges_paid_amt` | numeric | Y | Welfare Benefit tot charges paid (amount in dollars) / ID: DOL_SCHA_WLFR_TOT_CHARGES_PAID_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 92 | `wlfr_acquis_cost_amt` | `dol.schedule_a.wlfr_acquis_cost_amt` | numeric | Y | Welfare Benefit acquis cost (amount in dollars) / ID: DOL_SCHA_WLFR_ACQUIS_COST_AMT / Format: Decimal dollars (e.g., 12345.67) | attribute | NUMERIC | dol.column_metadata |
| 93 | `wlfr_acquis_cost_text` | `dol.schedule_a.wlfr_acquis_cost_text` | text | Y | Welfare Benefit acquis cost (text description) / ID: DOL_SCHA_WLFR_ACQUIS_COST_TEXT / Format: Variable length text | attribute | STRING | dol.column_metadata |
| 94 | `ins_fail_provide_info_ind` | `dol.schedule_a.ins_fail_provide_info_ind` | character varying(5) | Y | Insurance fail provide info (indicator flag) / ID: DOL_SCHA_INS_FAIL_PROVIDE_INFO_IND / Format: Y/N/X or 1/0 | attribute | STRING | dol.column_metadata |
| 95 | `ins_fail_provide_info_text` | `dol.schedule_a.ins_fail_provide_info_text` | text | Y | Insurance fail provide info (text description) / ID: DOL_SCHA_INS_FAIL_PROVIDE_INFO_TEXT / Format: Variable length text | attribute | STRING | dol.column_metadata |
| 96 | `form_year` | `dol.schedule_a.form_year` | character varying(10) | Y | Tax/plan year for this filing / ID: DOL_SCHA_FORM_YEAR / Format: Up to 10 characters | attribute | STRING | dol.column_metadata |
| 97 | `created_at` | `dol.schedule_a.created_at` | timestamp with time zone | Y | Record creation timestamp / ID: DOL_SCHA_CREATED_AT / Format: YYYY-MM-DD HH:MM:SS | attribute | ISO-8601 | dol.column_metadata |
| 98 | `updated_at` | `dol.schedule_a.updated_at` | timestamp with time zone | Y | Record last update timestamp / ID: DOL_SCHA_UPDATED_AT / Format: YYYY-MM-DD HH:MM:SS | attribute | ISO-8601 | dol.column_metadata |

### `dol.schedule_a_part1` -- UNREGISTERED -- 380,509 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `dol.schedule_a_part1.id` | bigint | N | Auto-increment surrogate primary key | attribute | INTEGER | dol.column_metadata |
| 2 | `ack_id` | `dol.schedule_a_part1.ack_id` | character varying(50) | N | DOL acknowledgment ID — unique filing identifier. Foreign key to dol.form_5500.ack_id or dol.form_5500_sf.ack_id for joining across schedules | attribute | STRING | dol.column_metadata |
| 3 | `form_id` | `dol.schedule_a_part1.form_id` | character varying(50) | Y | DOL internal form identifier | attribute | STRING | dol.column_metadata |
| 4 | `row_order` | `dol.schedule_a_part1.row_order` | integer | Y | Sequence number within a single filing — preserves original CSV row ordering when multiple line items exist per filing | attribute | INTEGER | dol.column_metadata |
| 5 | `ins_broker_name` | `dol.schedule_a_part1.ins_broker_name` | character varying(500) | Y | Name of insurance broker or agent | attribute | STRING | dol.column_metadata |
| 6 | `ins_broker_us_address1` | `dol.schedule_a_part1.ins_broker_us_address1` | character varying(500) | Y | Broker US mailing address line 1 | attribute | STRING | dol.column_metadata |
| 7 | `ins_broker_us_address2` | `dol.schedule_a_part1.ins_broker_us_address2` | character varying(500) | Y | Broker US mailing address line 2 | attribute | STRING | dol.column_metadata |
| 8 | `ins_broker_us_city` | `dol.schedule_a_part1.ins_broker_us_city` | character varying(255) | Y | Broker US city | attribute | STRING | dol.column_metadata |
| 9 | `ins_broker_us_state` | `dol.schedule_a_part1.ins_broker_us_state` | character varying(10) | Y | Broker US state code (2-letter) | attribute | STRING | dol.column_metadata |
| 10 | `ins_broker_us_zip` | `dol.schedule_a_part1.ins_broker_us_zip` | character varying(20) | Y | Broker US ZIP code | attribute | STRING | dol.column_metadata |
| 11 | `ins_broker_foreign_address1` | `dol.schedule_a_part1.ins_broker_foreign_address1` | character varying(500) | Y | Broker foreign address line 1 | attribute | STRING | dol.column_metadata |
| 12 | `ins_broker_foreign_address2` | `dol.schedule_a_part1.ins_broker_foreign_address2` | character varying(500) | Y | Broker foreign address line 2 | attribute | STRING | dol.column_metadata |
| 13 | `ins_broker_foreign_city` | `dol.schedule_a_part1.ins_broker_foreign_city` | character varying(255) | Y | Broker foreign city | attribute | STRING | dol.column_metadata |
| 14 | `ins_broker_foreign_prov_state` | `dol.schedule_a_part1.ins_broker_foreign_prov_state` | character varying(100) | Y | Broker foreign province/state | attribute | STRING | dol.column_metadata |
| 15 | `ins_broker_foreign_cntry` | `dol.schedule_a_part1.ins_broker_foreign_cntry` | character varying(100) | Y | Broker foreign country | attribute | STRING | dol.column_metadata |
| 16 | `ins_broker_foreign_postal_cd` | `dol.schedule_a_part1.ins_broker_foreign_postal_cd` | character varying(50) | Y | Broker foreign postal code | attribute | STRING | dol.column_metadata |
| 17 | `ins_broker_comm_pd_amt` | `dol.schedule_a_part1.ins_broker_comm_pd_amt` | numeric | Y | Total commissions paid to broker (USD) | attribute | NUMERIC | dol.column_metadata |
| 18 | `ins_broker_fees_pd_amt` | `dol.schedule_a_part1.ins_broker_fees_pd_amt` | numeric | Y | Total fees paid to broker (USD) | attribute | NUMERIC | dol.column_metadata |
| 19 | `ins_broker_fees_pd_text` | `dol.schedule_a_part1.ins_broker_fees_pd_text` | text | Y | Description/explanation of fees paid to broker | attribute | STRING | dol.column_metadata |
| 20 | `ins_broker_code` | `dol.schedule_a_part1.ins_broker_code` | character varying(50) | Y | Broker classification code (type of broker/agent) | attribute | STRING | dol.column_metadata |
| 21 | `form_year` | `dol.schedule_a_part1.form_year` | character varying(10) | Y | Filing year (2023, 2024, 2025, etc.) — partition key for cross-year queries | attribute | STRING | dol.column_metadata |
| 22 | `created_at` | `dol.schedule_a_part1.created_at` | timestamp with time zone | N | Timestamp when this row was loaded into the database | attribute | ISO-8601 | dol.column_metadata |

### `dol.schedule_c` -- UNREGISTERED -- 241,556 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `dol.schedule_c.id` | bigint | N | Auto-increment surrogate primary key | attribute | INTEGER | dol.column_metadata |
| 2 | `ack_id` | `dol.schedule_c.ack_id` | character varying(50) | N | DOL acknowledgment ID — unique filing identifier. Foreign key to dol.form_5500.ack_id or dol.form_5500_sf.ack_id for joining across schedules | attribute | STRING | dol.column_metadata |
| 3 | `provider_exclude_ind` | `dol.schedule_c.provider_exclude_ind` | character varying(10) | Y | Indicator (Yes/No) — whether certain service providers are excluded from Part 1 reporting | attribute | STRING | dol.column_metadata |
| 4 | `form_year` | `dol.schedule_c.form_year` | character varying(10) | Y | Filing year (2023, 2024, 2025, etc.) — partition key for cross-year queries | attribute | STRING | dol.column_metadata |
| 5 | `created_at` | `dol.schedule_c.created_at` | timestamp with time zone | N | Timestamp when this row was loaded into the database | attribute | ISO-8601 | dol.column_metadata |

### `dol.schedule_c_part1_item1` -- UNREGISTERED -- 396,838 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `dol.schedule_c_part1_item1.id` | bigint | N | Auto-increment surrogate primary key | attribute | INTEGER | dol.column_metadata |
| 2 | `ack_id` | `dol.schedule_c_part1_item1.ack_id` | character varying(50) | N | DOL acknowledgment ID — unique filing identifier. Foreign key to dol.form_5500.ack_id or dol.form_5500_sf.ack_id for joining across schedules | attribute | STRING | dol.column_metadata |
| 3 | `row_order` | `dol.schedule_c_part1_item1.row_order` | integer | Y | Sequence number within a single filing — preserves original CSV row ordering when multiple line items exist per filing | attribute | INTEGER | dol.column_metadata |
| 4 | `provider_eligible_name` | `dol.schedule_c_part1_item1.provider_eligible_name` | character varying(500) | Y | Name of service provider receiving eligible indirect compensation | attribute | STRING | dol.column_metadata |
| 5 | `provider_eligible_ein` | `dol.schedule_c_part1_item1.provider_eligible_ein` | character varying(20) | Y | EIN of the eligible indirect compensation provider | identifier | STRING | dol.column_metadata |
| 6 | `provider_eligible_us_address1` | `dol.schedule_c_part1_item1.provider_eligible_us_address1` | character varying(500) | Y | Provider US address line 1 | attribute | STRING | dol.column_metadata |
| 7 | `provider_eligible_us_address2` | `dol.schedule_c_part1_item1.provider_eligible_us_address2` | character varying(500) | Y | Provider US address line 2 | attribute | STRING | dol.column_metadata |
| 8 | `provider_eligible_us_city` | `dol.schedule_c_part1_item1.provider_eligible_us_city` | character varying(255) | Y | Provider US city | attribute | STRING | dol.column_metadata |
| 9 | `provider_eligible_us_state` | `dol.schedule_c_part1_item1.provider_eligible_us_state` | character varying(10) | Y | Provider US state code (2-letter) | attribute | STRING | dol.column_metadata |
| 10 | `provider_eligible_us_zip` | `dol.schedule_c_part1_item1.provider_eligible_us_zip` | character varying(20) | Y | Provider US ZIP code | attribute | STRING | dol.column_metadata |
| 11 | `prov_eligible_foreign_address1` | `dol.schedule_c_part1_item1.prov_eligible_foreign_address1` | character varying(500) | Y | Provider foreign address line 1 | attribute | STRING | dol.column_metadata |
| 12 | `prov_eligible_foreign_address2` | `dol.schedule_c_part1_item1.prov_eligible_foreign_address2` | character varying(500) | Y | Provider foreign address line 2 | attribute | STRING | dol.column_metadata |
| 13 | `prov_eligible_foreign_city` | `dol.schedule_c_part1_item1.prov_eligible_foreign_city` | character varying(255) | Y | Provider foreign city | attribute | STRING | dol.column_metadata |
| 14 | `prov_eligible_foreign_prov_st` | `dol.schedule_c_part1_item1.prov_eligible_foreign_prov_st` | character varying(100) | Y | Provider foreign province/state | attribute | STRING | dol.column_metadata |
| 15 | `prov_eligible_foreign_cntry` | `dol.schedule_c_part1_item1.prov_eligible_foreign_cntry` | character varying(100) | Y | Provider foreign country | attribute | STRING | dol.column_metadata |
| 16 | `prov_eligible_foreign_post_cd` | `dol.schedule_c_part1_item1.prov_eligible_foreign_post_cd` | character varying(50) | Y | Provider foreign postal code | attribute | STRING | dol.column_metadata |
| 17 | `form_year` | `dol.schedule_c_part1_item1.form_year` | character varying(10) | Y | Filing year (2023, 2024, 2025, etc.) — partition key for cross-year queries | attribute | STRING | dol.column_metadata |
| 18 | `created_at` | `dol.schedule_c_part1_item1.created_at` | timestamp with time zone | N | Timestamp when this row was loaded into the database | attribute | ISO-8601 | dol.column_metadata |

### `dol.schedule_c_part1_item2` -- UNREGISTERED -- 754,802 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `dol.schedule_c_part1_item2.id` | bigint | N | Auto-increment surrogate primary key | attribute | INTEGER | dol.column_metadata |
| 2 | `ack_id` | `dol.schedule_c_part1_item2.ack_id` | character varying(50) | N | DOL acknowledgment ID — unique filing identifier. Foreign key to dol.form_5500.ack_id or dol.form_5500_sf.ack_id for joining across schedules | attribute | STRING | dol.column_metadata |
| 3 | `row_order` | `dol.schedule_c_part1_item2.row_order` | integer | Y | Sequence number within a single filing — preserves original CSV row ordering when multiple line items exist per filing | attribute | INTEGER | dol.column_metadata |
| 4 | `provider_other_name` | `dol.schedule_c_part1_item2.provider_other_name` | character varying(500) | Y | Name of service provider receiving $5,000+ in compensation | attribute | STRING | dol.column_metadata |
| 5 | `provider_other_ein` | `dol.schedule_c_part1_item2.provider_other_ein` | character varying(20) | Y | EIN of the service provider | identifier | STRING | dol.column_metadata |
| 6 | `provider_other_us_address1` | `dol.schedule_c_part1_item2.provider_other_us_address1` | character varying(500) | Y | Provider US address line 1 | attribute | STRING | dol.column_metadata |
| 7 | `provider_other_us_address2` | `dol.schedule_c_part1_item2.provider_other_us_address2` | character varying(500) | Y | Provider US address line 2 | attribute | STRING | dol.column_metadata |
| 8 | `provider_other_us_city` | `dol.schedule_c_part1_item2.provider_other_us_city` | character varying(255) | Y | Provider US city | attribute | STRING | dol.column_metadata |
| 9 | `provider_other_us_state` | `dol.schedule_c_part1_item2.provider_other_us_state` | character varying(10) | Y | Provider US state code (2-letter) | attribute | STRING | dol.column_metadata |
| 10 | `provider_other_us_zip` | `dol.schedule_c_part1_item2.provider_other_us_zip` | character varying(20) | Y | Provider US ZIP code | attribute | STRING | dol.column_metadata |
| 11 | `prov_other_foreign_address1` | `dol.schedule_c_part1_item2.prov_other_foreign_address1` | character varying(500) | Y | Provider foreign address line 1 | attribute | STRING | dol.column_metadata |
| 12 | `prov_other_foreign_address2` | `dol.schedule_c_part1_item2.prov_other_foreign_address2` | character varying(500) | Y | Provider foreign address line 2 | attribute | STRING | dol.column_metadata |
| 13 | `prov_other_foreign_city` | `dol.schedule_c_part1_item2.prov_other_foreign_city` | character varying(255) | Y | Provider foreign city | attribute | STRING | dol.column_metadata |
| 14 | `prov_other_foreign_prov_state` | `dol.schedule_c_part1_item2.prov_other_foreign_prov_state` | character varying(100) | Y | Provider foreign province/state | attribute | STRING | dol.column_metadata |
| 15 | `prov_other_foreign_cntry` | `dol.schedule_c_part1_item2.prov_other_foreign_cntry` | character varying(100) | Y | Provider foreign country | attribute | STRING | dol.column_metadata |
| 16 | `prov_other_foreign_postal_cd` | `dol.schedule_c_part1_item2.prov_other_foreign_postal_cd` | character varying(50) | Y | Provider foreign postal code | attribute | STRING | dol.column_metadata |
| 17 | `provider_other_srvc_codes` | `dol.schedule_c_part1_item2.provider_other_srvc_codes` | character varying(255) | Y | Concatenated service type codes for this provider | attribute | STRING | dol.column_metadata |
| 18 | `provider_other_relation` | `dol.schedule_c_part1_item2.provider_other_relation` | character varying(255) | Y | Relationship to plan (e.g., party-in-interest) | attribute | STRING | dol.column_metadata |
| 19 | `provider_other_direct_comp_amt` | `dol.schedule_c_part1_item2.provider_other_direct_comp_amt` | numeric | Y | Direct compensation paid to provider (USD) | attribute | NUMERIC | dol.column_metadata |
| 20 | `prov_other_indirect_comp_ind` | `dol.schedule_c_part1_item2.prov_other_indirect_comp_ind` | character varying(10) | Y | Indicator (Yes/No) — did provider receive indirect compensation | attribute | STRING | dol.column_metadata |
| 21 | `prov_other_elig_ind_comp_ind` | `dol.schedule_c_part1_item2.prov_other_elig_ind_comp_ind` | character varying(10) | Y | Indicator (Yes/No) — eligible indirect compensation received | attribute | STRING | dol.column_metadata |
| 22 | `prov_other_tot_ind_comp_amt` | `dol.schedule_c_part1_item2.prov_other_tot_ind_comp_amt` | numeric | Y | Total indirect compensation amount (USD) | attribute | NUMERIC | dol.column_metadata |
| 23 | `provider_other_amt_formula_ind` | `dol.schedule_c_part1_item2.provider_other_amt_formula_ind` | character varying(10) | Y | Indicator (Yes/No) — compensation based on formula rather than fixed amount | attribute | STRING | dol.column_metadata |
| 24 | `form_year` | `dol.schedule_c_part1_item2.form_year` | character varying(10) | Y | Filing year (2023, 2024, 2025, etc.) — partition key for cross-year queries | attribute | STRING | dol.column_metadata |
| 25 | `created_at` | `dol.schedule_c_part1_item2.created_at` | timestamp with time zone | N | Timestamp when this row was loaded into the database | attribute | ISO-8601 | dol.column_metadata |

### `dol.schedule_c_part1_item2_codes` -- UNREGISTERED -- 1,848,202 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `dol.schedule_c_part1_item2_codes.id` | bigint | N | Auto-increment surrogate primary key | attribute | INTEGER | dol.column_metadata |
| 2 | `ack_id` | `dol.schedule_c_part1_item2_codes.ack_id` | character varying(50) | N | DOL acknowledgment ID — unique filing identifier. Foreign key to dol.form_5500.ack_id or dol.form_5500_sf.ack_id for joining across schedules | attribute | STRING | dol.column_metadata |
| 3 | `row_order` | `dol.schedule_c_part1_item2_codes.row_order` | integer | Y | Sequence number within a single filing — preserves original CSV row ordering when multiple line items exist per filing | attribute | INTEGER | dol.column_metadata |
| 4 | `code_order` | `dol.schedule_c_part1_item2_codes.code_order` | integer | Y | Sequence number of the service code within a given row_order — preserves code ordering per provider | attribute | INTEGER | dol.column_metadata |
| 5 | `service_code` | `dol.schedule_c_part1_item2_codes.service_code` | character varying(50) | Y | DOL service type classification code identifying the category of service provided | attribute | STRING | dol.column_metadata |
| 6 | `form_year` | `dol.schedule_c_part1_item2_codes.form_year` | character varying(10) | Y | Filing year (2023, 2024, 2025, etc.) — partition key for cross-year queries | attribute | STRING | dol.column_metadata |
| 7 | `created_at` | `dol.schedule_c_part1_item2_codes.created_at` | timestamp with time zone | N | Timestamp when this row was loaded into the database | attribute | ISO-8601 | dol.column_metadata |

### `dol.schedule_c_part1_item3` -- UNREGISTERED -- 383,338 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `dol.schedule_c_part1_item3.id` | bigint | N | Auto-increment surrogate primary key | attribute | INTEGER | dol.column_metadata |
| 2 | `ack_id` | `dol.schedule_c_part1_item3.ack_id` | character varying(50) | N | DOL acknowledgment ID — unique filing identifier. Foreign key to dol.form_5500.ack_id or dol.form_5500_sf.ack_id for joining across schedules | attribute | STRING | dol.column_metadata |
| 3 | `row_order` | `dol.schedule_c_part1_item3.row_order` | integer | Y | Sequence number within a single filing — preserves original CSV row ordering when multiple line items exist per filing | attribute | INTEGER | dol.column_metadata |
| 4 | `provider_indirect_name` | `dol.schedule_c_part1_item3.provider_indirect_name` | character varying(500) | Y | Name of service provider receiving indirect compensation | attribute | STRING | dol.column_metadata |
| 5 | `provider_indirect_srvc_codes` | `dol.schedule_c_part1_item3.provider_indirect_srvc_codes` | character varying(255) | Y | Concatenated service type codes | attribute | STRING | dol.column_metadata |
| 6 | `provider_indirect_comp_amt` | `dol.schedule_c_part1_item3.provider_indirect_comp_amt` | numeric | Y | Amount of indirect compensation received (USD) | attribute | NUMERIC | dol.column_metadata |
| 7 | `provider_payor_name` | `dol.schedule_c_part1_item3.provider_payor_name` | character varying(500) | Y | Name of the entity that paid the indirect compensation | attribute | STRING | dol.column_metadata |
| 8 | `provider_payor_ein` | `dol.schedule_c_part1_item3.provider_payor_ein` | character varying(20) | Y | EIN of the payor | identifier | STRING | dol.column_metadata |
| 9 | `provider_payor_us_address1` | `dol.schedule_c_part1_item3.provider_payor_us_address1` | character varying(500) | Y | Payor US address line 1 | attribute | STRING | dol.column_metadata |
| 10 | `provider_payor_us_address2` | `dol.schedule_c_part1_item3.provider_payor_us_address2` | character varying(500) | Y | Payor US address line 2 | attribute | STRING | dol.column_metadata |
| 11 | `provider_payor_us_city` | `dol.schedule_c_part1_item3.provider_payor_us_city` | character varying(255) | Y | Payor US city | attribute | STRING | dol.column_metadata |
| 12 | `provider_payor_us_state` | `dol.schedule_c_part1_item3.provider_payor_us_state` | character varying(10) | Y | Payor US state code (2-letter) | attribute | STRING | dol.column_metadata |
| 13 | `provider_payor_us_zip` | `dol.schedule_c_part1_item3.provider_payor_us_zip` | character varying(20) | Y | Payor US ZIP code | attribute | STRING | dol.column_metadata |
| 14 | `prov_payor_foreign_address1` | `dol.schedule_c_part1_item3.prov_payor_foreign_address1` | character varying(500) | Y | Payor foreign address line 1 | attribute | STRING | dol.column_metadata |
| 15 | `prov_payor_foreign_address2` | `dol.schedule_c_part1_item3.prov_payor_foreign_address2` | character varying(500) | Y | Payor foreign address line 2 | attribute | STRING | dol.column_metadata |
| 16 | `prov_payor_foreign_city` | `dol.schedule_c_part1_item3.prov_payor_foreign_city` | character varying(255) | Y | Payor foreign city | attribute | STRING | dol.column_metadata |
| 17 | `prov_payor_foreign_prov_state` | `dol.schedule_c_part1_item3.prov_payor_foreign_prov_state` | character varying(100) | Y | Payor foreign province/state | attribute | STRING | dol.column_metadata |
| 18 | `prov_payor_foreign_cntry` | `dol.schedule_c_part1_item3.prov_payor_foreign_cntry` | character varying(100) | Y | Payor foreign country | attribute | STRING | dol.column_metadata |
| 19 | `prov_payor_foreign_postal_cd` | `dol.schedule_c_part1_item3.prov_payor_foreign_postal_cd` | character varying(50) | Y | Payor foreign postal code | attribute | STRING | dol.column_metadata |
| 20 | `provider_comp_explain_text` | `dol.schedule_c_part1_item3.provider_comp_explain_text` | text | Y | Free-text explanation of the indirect compensation arrangement | attribute | STRING | dol.column_metadata |
| 21 | `form_year` | `dol.schedule_c_part1_item3.form_year` | character varying(10) | Y | Filing year (2023, 2024, 2025, etc.) — partition key for cross-year queries | attribute | STRING | dol.column_metadata |
| 22 | `created_at` | `dol.schedule_c_part1_item3.created_at` | timestamp with time zone | N | Timestamp when this row was loaded into the database | attribute | ISO-8601 | dol.column_metadata |

### `dol.schedule_c_part1_item3_codes` -- UNREGISTERED -- 707,007 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `dol.schedule_c_part1_item3_codes.id` | bigint | N | Auto-increment surrogate primary key | attribute | INTEGER | dol.column_metadata |
| 2 | `ack_id` | `dol.schedule_c_part1_item3_codes.ack_id` | character varying(50) | N | DOL acknowledgment ID — unique filing identifier. Foreign key to dol.form_5500.ack_id or dol.form_5500_sf.ack_id for joining across schedules | attribute | STRING | dol.column_metadata |
| 3 | `row_order` | `dol.schedule_c_part1_item3_codes.row_order` | integer | Y | Sequence number within a single filing — preserves original CSV row ordering when multiple line items exist per filing | attribute | INTEGER | dol.column_metadata |
| 4 | `code_order` | `dol.schedule_c_part1_item3_codes.code_order` | integer | Y | Sequence number of the service code within a given row_order — preserves code ordering per provider | attribute | INTEGER | dol.column_metadata |
| 5 | `service_code` | `dol.schedule_c_part1_item3_codes.service_code` | character varying(50) | Y | DOL service type classification code identifying the category of service provided | attribute | STRING | dol.column_metadata |
| 6 | `form_year` | `dol.schedule_c_part1_item3_codes.form_year` | character varying(10) | Y | Filing year (2023, 2024, 2025, etc.) — partition key for cross-year queries | attribute | STRING | dol.column_metadata |
| 7 | `created_at` | `dol.schedule_c_part1_item3_codes.created_at` | timestamp with time zone | N | Timestamp when this row was loaded into the database | attribute | ISO-8601 | dol.column_metadata |

### `dol.schedule_c_part2` -- UNREGISTERED -- 4,593 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `dol.schedule_c_part2.id` | bigint | N | Auto-increment surrogate primary key | attribute | INTEGER | dol.column_metadata |
| 2 | `ack_id` | `dol.schedule_c_part2.ack_id` | character varying(50) | N | DOL acknowledgment ID — unique filing identifier. Foreign key to dol.form_5500.ack_id or dol.form_5500_sf.ack_id for joining across schedules | attribute | STRING | dol.column_metadata |
| 3 | `row_order` | `dol.schedule_c_part2.row_order` | integer | Y | Sequence number within a single filing — preserves original CSV row ordering when multiple line items exist per filing | attribute | INTEGER | dol.column_metadata |
| 4 | `provider_fail_name` | `dol.schedule_c_part2.provider_fail_name` | character varying(500) | Y | Name of provider who failed/refused to disclose compensation | attribute | STRING | dol.column_metadata |
| 5 | `provider_fail_ein` | `dol.schedule_c_part2.provider_fail_ein` | character varying(20) | Y | EIN of the non-disclosing provider | identifier | STRING | dol.column_metadata |
| 6 | `provider_fail_us_address1` | `dol.schedule_c_part2.provider_fail_us_address1` | character varying(500) | Y | Provider US address line 1 | attribute | STRING | dol.column_metadata |
| 7 | `provider_fail_us_address2` | `dol.schedule_c_part2.provider_fail_us_address2` | character varying(500) | Y | Provider US address line 2 | attribute | STRING | dol.column_metadata |
| 8 | `provider_fail_us_city` | `dol.schedule_c_part2.provider_fail_us_city` | character varying(255) | Y | Provider US city | attribute | STRING | dol.column_metadata |
| 9 | `provider_fail_us_state` | `dol.schedule_c_part2.provider_fail_us_state` | character varying(10) | Y | Provider US state code (2-letter) | attribute | STRING | dol.column_metadata |
| 10 | `provider_fail_us_zip` | `dol.schedule_c_part2.provider_fail_us_zip` | character varying(20) | Y | Provider US ZIP code | attribute | STRING | dol.column_metadata |
| 11 | `provider_fail_foreign_address1` | `dol.schedule_c_part2.provider_fail_foreign_address1` | character varying(500) | Y | Provider foreign address line 1 | attribute | STRING | dol.column_metadata |
| 12 | `provider_fail_foreign_address2` | `dol.schedule_c_part2.provider_fail_foreign_address2` | character varying(500) | Y | Provider foreign address line 2 | attribute | STRING | dol.column_metadata |
| 13 | `provider_fail_foreign_city` | `dol.schedule_c_part2.provider_fail_foreign_city` | character varying(255) | Y | Provider foreign city | attribute | STRING | dol.column_metadata |
| 14 | `provider_fail_foreign_prov_st` | `dol.schedule_c_part2.provider_fail_foreign_prov_st` | character varying(100) | Y | Provider foreign province/state | attribute | STRING | dol.column_metadata |
| 15 | `provider_fail_foreign_cntry` | `dol.schedule_c_part2.provider_fail_foreign_cntry` | character varying(100) | Y | Provider foreign country | attribute | STRING | dol.column_metadata |
| 16 | `provider_fail_forgn_postal_cd` | `dol.schedule_c_part2.provider_fail_forgn_postal_cd` | character varying(50) | Y | Provider foreign postal code | attribute | STRING | dol.column_metadata |
| 17 | `provider_fail_srvc_code` | `dol.schedule_c_part2.provider_fail_srvc_code` | character varying(255) | Y | Service type code(s) for the non-disclosing provider | attribute | STRING | dol.column_metadata |
| 18 | `provider_fail_info_text` | `dol.schedule_c_part2.provider_fail_info_text` | text | Y | Free-text explanation of the provider's failure to disclose | attribute | STRING | dol.column_metadata |
| 19 | `form_year` | `dol.schedule_c_part2.form_year` | character varying(10) | Y | Filing year (2023, 2024, 2025, etc.) — partition key for cross-year queries | attribute | STRING | dol.column_metadata |
| 20 | `created_at` | `dol.schedule_c_part2.created_at` | timestamp with time zone | N | Timestamp when this row was loaded into the database | attribute | ISO-8601 | dol.column_metadata |

### `dol.schedule_c_part2_codes` -- UNREGISTERED -- 2,352 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `dol.schedule_c_part2_codes.id` | bigint | N | Auto-increment surrogate primary key | attribute | INTEGER | dol.column_metadata |
| 2 | `ack_id` | `dol.schedule_c_part2_codes.ack_id` | character varying(50) | N | DOL acknowledgment ID — unique filing identifier. Foreign key to dol.form_5500.ack_id or dol.form_5500_sf.ack_id for joining across schedules | attribute | STRING | dol.column_metadata |
| 3 | `row_order` | `dol.schedule_c_part2_codes.row_order` | integer | Y | Sequence number within a single filing — preserves original CSV row ordering when multiple line items exist per filing | attribute | INTEGER | dol.column_metadata |
| 4 | `code_order` | `dol.schedule_c_part2_codes.code_order` | integer | Y | Sequence number of the service code within a given row_order — preserves code ordering per provider | attribute | INTEGER | dol.column_metadata |
| 5 | `service_code` | `dol.schedule_c_part2_codes.service_code` | character varying(50) | Y | DOL service type classification code identifying the category of service provided | attribute | STRING | dol.column_metadata |
| 6 | `form_year` | `dol.schedule_c_part2_codes.form_year` | character varying(10) | Y | Filing year (2023, 2024, 2025, etc.) — partition key for cross-year queries | attribute | STRING | dol.column_metadata |
| 7 | `created_at` | `dol.schedule_c_part2_codes.created_at` | timestamp with time zone | N | Timestamp when this row was loaded into the database | attribute | ISO-8601 | dol.column_metadata |

### `dol.schedule_c_part3` -- UNREGISTERED -- 15,514 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `dol.schedule_c_part3.id` | bigint | N | Auto-increment surrogate primary key | attribute | INTEGER | dol.column_metadata |
| 2 | `ack_id` | `dol.schedule_c_part3.ack_id` | character varying(50) | N | DOL acknowledgment ID — unique filing identifier. Foreign key to dol.form_5500.ack_id or dol.form_5500_sf.ack_id for joining across schedules | attribute | STRING | dol.column_metadata |
| 3 | `row_order` | `dol.schedule_c_part3.row_order` | integer | Y | Sequence number within a single filing — preserves original CSV row ordering when multiple line items exist per filing | attribute | INTEGER | dol.column_metadata |
| 4 | `provider_term_name` | `dol.schedule_c_part3.provider_term_name` | character varying(500) | Y | Name of the terminated service provider | attribute | STRING | dol.column_metadata |
| 5 | `provider_term_ein` | `dol.schedule_c_part3.provider_term_ein` | character varying(20) | Y | EIN of the terminated provider | identifier | STRING | dol.column_metadata |
| 6 | `provider_term_position` | `dol.schedule_c_part3.provider_term_position` | character varying(500) | Y | Position/role held by the terminated provider | attribute | STRING | dol.column_metadata |
| 7 | `provider_term_us_address1` | `dol.schedule_c_part3.provider_term_us_address1` | character varying(500) | Y | Provider US address line 1 | attribute | STRING | dol.column_metadata |
| 8 | `provider_term_us_address2` | `dol.schedule_c_part3.provider_term_us_address2` | character varying(500) | Y | Provider US address line 2 | attribute | STRING | dol.column_metadata |
| 9 | `provider_term_us_city` | `dol.schedule_c_part3.provider_term_us_city` | character varying(255) | Y | Provider US city | attribute | STRING | dol.column_metadata |
| 10 | `provider_term_us_state` | `dol.schedule_c_part3.provider_term_us_state` | character varying(10) | Y | Provider US state code (2-letter) | attribute | STRING | dol.column_metadata |
| 11 | `provider_term_us_zip` | `dol.schedule_c_part3.provider_term_us_zip` | character varying(20) | Y | Provider US ZIP code | attribute | STRING | dol.column_metadata |
| 12 | `provider_term_foreign_address1` | `dol.schedule_c_part3.provider_term_foreign_address1` | character varying(500) | Y | Provider foreign address line 1 | attribute | STRING | dol.column_metadata |
| 13 | `provider_term_foreign_address2` | `dol.schedule_c_part3.provider_term_foreign_address2` | character varying(500) | Y | Provider foreign address line 2 | attribute | STRING | dol.column_metadata |
| 14 | `provider_term_foreign_city` | `dol.schedule_c_part3.provider_term_foreign_city` | character varying(255) | Y | Provider foreign city | attribute | STRING | dol.column_metadata |
| 15 | `provider_term_foreign_prov_st` | `dol.schedule_c_part3.provider_term_foreign_prov_st` | character varying(100) | Y | Provider foreign province/state | attribute | STRING | dol.column_metadata |
| 16 | `provider_term_foreign_cntry` | `dol.schedule_c_part3.provider_term_foreign_cntry` | character varying(100) | Y | Provider foreign country | attribute | STRING | dol.column_metadata |
| 17 | `provider_term_forgn_postal_cd` | `dol.schedule_c_part3.provider_term_forgn_postal_cd` | character varying(50) | Y | Provider foreign postal code | attribute | STRING | dol.column_metadata |
| 18 | `provider_term_phone_num` | `dol.schedule_c_part3.provider_term_phone_num` | character varying(30) | Y | US phone number of the terminated provider | attribute | STRING | dol.column_metadata |
| 19 | `provider_term_text` | `dol.schedule_c_part3.provider_term_text` | text | Y | Free-text explanation of the termination | attribute | STRING | dol.column_metadata |
| 20 | `provider_term_phone_num_foreig` | `dol.schedule_c_part3.provider_term_phone_num_foreig` | character varying(30) | Y | Foreign phone number of the terminated provider | attribute | STRING | dol.column_metadata |
| 21 | `form_year` | `dol.schedule_c_part3.form_year` | character varying(10) | Y | Filing year (2023, 2024, 2025, etc.) — partition key for cross-year queries | attribute | STRING | dol.column_metadata |
| 22 | `created_at` | `dol.schedule_c_part3.created_at` | timestamp with time zone | N | Timestamp when this row was loaded into the database | attribute | ISO-8601 | dol.column_metadata |

### `dol.schedule_d` -- UNREGISTERED -- 121,813 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `dol.schedule_d.id` | bigint | N | Auto-increment surrogate primary key | attribute | INTEGER | dol.column_metadata |
| 2 | `ack_id` | `dol.schedule_d.ack_id` | character varying(50) | N | DOL acknowledgment ID — unique filing identifier. Foreign key to dol.form_5500.ack_id or dol.form_5500_sf.ack_id for joining across schedules | attribute | STRING | dol.column_metadata |
| 3 | `sch_d_plan_year_begin_date` | `dol.schedule_d.sch_d_plan_year_begin_date` | character varying(30) | Y | First day of the DFE plan year (YYYY-MM-DD) | attribute | STRING | dol.column_metadata |
| 4 | `sch_d_tax_prd` | `dol.schedule_d.sch_d_tax_prd` | character varying(30) | Y | Tax period end date of the DFE filing | attribute | STRING | dol.column_metadata |
| 5 | `sch_d_pn` | `dol.schedule_d.sch_d_pn` | character varying(10) | Y | Plan number of the DFE | identifier | STRING | dol.column_metadata |
| 6 | `sch_d_ein` | `dol.schedule_d.sch_d_ein` | character varying(20) | Y | EIN of the DFE sponsor | identifier | STRING | dol.column_metadata |
| 7 | `form_year` | `dol.schedule_d.form_year` | character varying(10) | Y | Filing year (2023, 2024, 2025, etc.) — partition key for cross-year queries | attribute | STRING | dol.column_metadata |
| 8 | `created_at` | `dol.schedule_d.created_at` | timestamp with time zone | N | Timestamp when this row was loaded into the database | attribute | ISO-8601 | dol.column_metadata |

### `dol.schedule_d_part1` -- UNREGISTERED -- 808,051 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `dol.schedule_d_part1.id` | bigint | N | Auto-increment surrogate primary key | attribute | INTEGER | dol.column_metadata |
| 2 | `ack_id` | `dol.schedule_d_part1.ack_id` | character varying(50) | N | DOL acknowledgment ID — unique filing identifier. Foreign key to dol.form_5500.ack_id or dol.form_5500_sf.ack_id for joining across schedules | attribute | STRING | dol.column_metadata |
| 3 | `row_order` | `dol.schedule_d_part1.row_order` | integer | Y | Sequence number within a single filing — preserves original CSV row ordering when multiple line items exist per filing | attribute | INTEGER | dol.column_metadata |
| 4 | `dfe_p1_entity_name` | `dol.schedule_d_part1.dfe_p1_entity_name` | character varying(500) | Y | Name of the participating plan/entity | attribute | STRING | dol.column_metadata |
| 5 | `dfe_p1_spons_name` | `dol.schedule_d_part1.dfe_p1_spons_name` | character varying(500) | Y | Name of the participating plan's sponsor | attribute | STRING | dol.column_metadata |
| 6 | `dfe_p1_plan_ein` | `dol.schedule_d_part1.dfe_p1_plan_ein` | character varying(20) | Y | EIN of the participating plan | identifier | STRING | dol.column_metadata |
| 7 | `dfe_p1_plan_pn` | `dol.schedule_d_part1.dfe_p1_plan_pn` | character varying(10) | Y | Plan number of the participating plan | identifier | STRING | dol.column_metadata |
| 8 | `dfe_p1_entity_code` | `dol.schedule_d_part1.dfe_p1_entity_code` | character varying(10) | Y | Entity type code of the participating plan | attribute | STRING | dol.column_metadata |
| 9 | `dfe_p1_plan_int_eoy_amt` | `dol.schedule_d_part1.dfe_p1_plan_int_eoy_amt` | numeric | Y | End-of-year interest/value amount for this plan in the DFE (USD) | attribute | NUMERIC | dol.column_metadata |
| 10 | `form_year` | `dol.schedule_d_part1.form_year` | character varying(10) | Y | Filing year (2023, 2024, 2025, etc.) — partition key for cross-year queries | attribute | STRING | dol.column_metadata |
| 11 | `created_at` | `dol.schedule_d_part1.created_at` | timestamp with time zone | N | Timestamp when this row was loaded into the database | attribute | ISO-8601 | dol.column_metadata |

### `dol.schedule_d_part2` -- UNREGISTERED -- 2,392,252 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `dol.schedule_d_part2.id` | bigint | N | Auto-increment surrogate primary key | attribute | INTEGER | dol.column_metadata |
| 2 | `ack_id` | `dol.schedule_d_part2.ack_id` | character varying(50) | N | DOL acknowledgment ID — unique filing identifier. Foreign key to dol.form_5500.ack_id or dol.form_5500_sf.ack_id for joining across schedules | attribute | STRING | dol.column_metadata |
| 3 | `row_order` | `dol.schedule_d_part2.row_order` | integer | Y | Sequence number within a single filing — preserves original CSV row ordering when multiple line items exist per filing | attribute | INTEGER | dol.column_metadata |
| 4 | `dfe_p2_plan_name` | `dol.schedule_d_part2.dfe_p2_plan_name` | character varying(500) | Y | Name of the DFE in which this plan participates | attribute | STRING | dol.column_metadata |
| 5 | `dfe_p2_plan_spons_name` | `dol.schedule_d_part2.dfe_p2_plan_spons_name` | character varying(500) | Y | Name of the DFE sponsor | attribute | STRING | dol.column_metadata |
| 6 | `dfe_p2_plan_ein` | `dol.schedule_d_part2.dfe_p2_plan_ein` | character varying(20) | Y | EIN of the DFE | identifier | STRING | dol.column_metadata |
| 7 | `dfe_p2_plan_pn` | `dol.schedule_d_part2.dfe_p2_plan_pn` | character varying(10) | Y | Plan number of the DFE | identifier | STRING | dol.column_metadata |
| 8 | `form_year` | `dol.schedule_d_part2.form_year` | character varying(10) | Y | Filing year (2023, 2024, 2025, etc.) — partition key for cross-year queries | attribute | STRING | dol.column_metadata |
| 9 | `created_at` | `dol.schedule_d_part2.created_at` | timestamp with time zone | N | Timestamp when this row was loaded into the database | attribute | ISO-8601 | dol.column_metadata |

### `dol.schedule_dcg` -- UNREGISTERED -- 235 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `dol.schedule_dcg.id` | bigint | N | Auto-increment surrogate primary key | attribute | INTEGER | dol.column_metadata |
| 2 | `ack_id` | `dol.schedule_dcg.ack_id` | character varying(50) | N | DOL acknowledgment ID — unique filing identifier. Foreign key to dol.form_5500.ack_id or dol.form_5500_sf.ack_id for joining across schedules | attribute | STRING | dol.column_metadata |
| 3 | `form_id` | `dol.schedule_dcg.form_id` | character varying(50) | Y | DOL internal form identifier | attribute | STRING | dol.column_metadata |
| 4 | `sch_dcg_name` | `dol.schedule_dcg.sch_dcg_name` | character varying(500) | Y | Name of the Direct Filing Entity | attribute | STRING | dol.column_metadata |
| 5 | `sch_dcg_plan_num` | `dol.schedule_dcg.sch_dcg_plan_num` | character varying(10) | Y | Plan number of the DFE | attribute | STRING | dol.column_metadata |
| 6 | `sch_dcg_sponsor_name` | `dol.schedule_dcg.sch_dcg_sponsor_name` | character varying(500) | Y | Sponsor name of the DFE | attribute | STRING | dol.column_metadata |
| 7 | `sch_dcg_ein` | `dol.schedule_dcg.sch_dcg_ein` | character varying(20) | Y | EIN of the DFE sponsor | identifier | STRING | dol.column_metadata |
| 8 | `dcg_plan_type` | `dol.schedule_dcg.dcg_plan_type` | character varying(50) | Y | Type of plan (e.g., Master Trust, PSA, 103-12 IE, GIA) | attribute | STRING | dol.column_metadata |
| 9 | `dcg_initial_filing_ind` | `dol.schedule_dcg.dcg_initial_filing_ind` | character varying(10) | Y | Indicator — initial filing for this DFE | attribute | STRING | dol.column_metadata |
| 10 | `dcg_amended_ind` | `dol.schedule_dcg.dcg_amended_ind` | character varying(10) | Y | Indicator — this is an amended filing | attribute | STRING | dol.column_metadata |
| 11 | `dcg_final_ind` | `dol.schedule_dcg.dcg_final_ind` | character varying(10) | Y | Indicator — this is the final filing for this DFE | attribute | STRING | dol.column_metadata |
| 12 | `dcg_plan_name` | `dol.schedule_dcg.dcg_plan_name` | character varying(500) | Y | Plan name as reported on the filing | attribute | STRING | dol.column_metadata |
| 13 | `dcg_plan_num` | `dol.schedule_dcg.dcg_plan_num` | character varying(10) | Y | Plan number as reported on the filing | attribute | STRING | dol.column_metadata |
| 14 | `dcg_plan_eff_date` | `dol.schedule_dcg.dcg_plan_eff_date` | character varying(30) | Y | Effective date of the plan | attribute | STRING | dol.column_metadata |
| 15 | `dcg_sponsor_name` | `dol.schedule_dcg.dcg_sponsor_name` | character varying(500) | Y | Sponsor name as reported | attribute | STRING | dol.column_metadata |
| 16 | `dcg_spons_dba_name` | `dol.schedule_dcg.dcg_spons_dba_name` | character varying(500) | Y | Sponsor DBA (doing business as) name | attribute | STRING | dol.column_metadata |
| 17 | `dcg_spons_care_of_name` | `dol.schedule_dcg.dcg_spons_care_of_name` | character varying(500) | Y | Sponsor care-of name | attribute | STRING | dol.column_metadata |
| 18 | `dcg_spons_us_address1` | `dol.schedule_dcg.dcg_spons_us_address1` | character varying(500) | Y | Sponsor US mailing address line 1 | attribute | STRING | dol.column_metadata |
| 19 | `dcg_spons_us_address2` | `dol.schedule_dcg.dcg_spons_us_address2` | character varying(500) | Y | Sponsor US mailing address line 2 | attribute | STRING | dol.column_metadata |
| 20 | `dcg_spons_us_city` | `dol.schedule_dcg.dcg_spons_us_city` | character varying(255) | Y | Sponsor US city | attribute | STRING | dol.column_metadata |
| 21 | `dcg_spons_us_state` | `dol.schedule_dcg.dcg_spons_us_state` | character varying(10) | Y | Sponsor US state code (2-letter) | attribute | STRING | dol.column_metadata |
| 22 | `dcg_spons_us_zip` | `dol.schedule_dcg.dcg_spons_us_zip` | character varying(20) | Y | Sponsor US ZIP code | attribute | STRING | dol.column_metadata |
| 23 | `dcg_spons_foreign_address1` | `dol.schedule_dcg.dcg_spons_foreign_address1` | character varying(500) | Y | Sponsor foreign address line 1 | attribute | STRING | dol.column_metadata |
| 24 | `dcg_spons_foreign_address2` | `dol.schedule_dcg.dcg_spons_foreign_address2` | character varying(500) | Y | Sponsor foreign address line 2 | attribute | STRING | dol.column_metadata |
| 25 | `dcg_spons_foreign_city` | `dol.schedule_dcg.dcg_spons_foreign_city` | character varying(255) | Y | Sponsor foreign city | attribute | STRING | dol.column_metadata |
| 26 | `dcg_spons_foreign_prov_state` | `dol.schedule_dcg.dcg_spons_foreign_prov_state` | character varying(100) | Y | Sponsor foreign province/state | attribute | STRING | dol.column_metadata |
| 27 | `dcg_spons_foreign_cntry` | `dol.schedule_dcg.dcg_spons_foreign_cntry` | character varying(100) | Y | Sponsor foreign country | attribute | STRING | dol.column_metadata |
| 28 | `dcg_spons_foreign_postal_cd` | `dol.schedule_dcg.dcg_spons_foreign_postal_cd` | character varying(50) | Y | Sponsor foreign postal code | attribute | STRING | dol.column_metadata |
| 29 | `dcg_spons_loc_us_address1` | `dol.schedule_dcg.dcg_spons_loc_us_address1` | character varying(500) | Y | Sponsor location (physical) US address line 1 | attribute | STRING | dol.column_metadata |
| 30 | `dcg_spons_loc_us_address2` | `dol.schedule_dcg.dcg_spons_loc_us_address2` | character varying(500) | Y | Sponsor location US address line 2 | attribute | STRING | dol.column_metadata |
| 31 | `dcg_spons_loc_us_city` | `dol.schedule_dcg.dcg_spons_loc_us_city` | character varying(255) | Y | Sponsor location US city | attribute | STRING | dol.column_metadata |
| 32 | `dcg_spons_loc_us_state` | `dol.schedule_dcg.dcg_spons_loc_us_state` | character varying(10) | Y | Sponsor location US state code | attribute | STRING | dol.column_metadata |
| 33 | `dcg_spons_loc_us_zip` | `dol.schedule_dcg.dcg_spons_loc_us_zip` | character varying(20) | Y | Sponsor location US ZIP code | attribute | STRING | dol.column_metadata |
| 34 | `dcg_spons_loc_foreign_address1` | `dol.schedule_dcg.dcg_spons_loc_foreign_address1` | character varying(500) | Y | Sponsor location foreign address line 1 | attribute | STRING | dol.column_metadata |
| 35 | `dcg_spons_loc_foreign_address2` | `dol.schedule_dcg.dcg_spons_loc_foreign_address2` | character varying(500) | Y | Sponsor location foreign address line 2 | attribute | STRING | dol.column_metadata |
| 36 | `dcg_spons_loc_foreign_city` | `dol.schedule_dcg.dcg_spons_loc_foreign_city` | character varying(255) | Y | Sponsor location foreign city | attribute | STRING | dol.column_metadata |
| 37 | `dcg_spons_loc_foreign_prov_state` | `dol.schedule_dcg.dcg_spons_loc_foreign_prov_state` | character varying(100) | Y | Sponsor location foreign province/state | attribute | STRING | dol.column_metadata |
| 38 | `dcg_spons_loc_foreign_cntry` | `dol.schedule_dcg.dcg_spons_loc_foreign_cntry` | character varying(100) | Y | Sponsor location foreign country | attribute | STRING | dol.column_metadata |
| 39 | `dcg_spons_loc_foreign_postal_cd` | `dol.schedule_dcg.dcg_spons_loc_foreign_postal_cd` | character varying(50) | Y | Sponsor location foreign postal code | attribute | STRING | dol.column_metadata |
| 40 | `dcg_spons_ein` | `dol.schedule_dcg.dcg_spons_ein` | character varying(20) | Y | EIN of the plan sponsor | identifier | STRING | dol.column_metadata |
| 41 | `dcg_spons_phone_num` | `dol.schedule_dcg.dcg_spons_phone_num` | character varying(30) | Y | Sponsor US phone number | attribute | STRING | dol.column_metadata |
| 42 | `dcg_spons_phone_num_foreign` | `dol.schedule_dcg.dcg_spons_phone_num_foreign` | character varying(30) | Y | Sponsor foreign phone number | attribute | STRING | dol.column_metadata |
| 43 | `dcg_business_code` | `dol.schedule_dcg.dcg_business_code` | character varying(20) | Y | NAICS business code of the sponsor | attribute | STRING | dol.column_metadata |
| 44 | `dcg_last_rpt_spons_name` | `dol.schedule_dcg.dcg_last_rpt_spons_name` | character varying(500) | Y | Sponsor name from the last reported filing | attribute | STRING | dol.column_metadata |
| 45 | `dcg_last_rpt_spons_ein` | `dol.schedule_dcg.dcg_last_rpt_spons_ein` | character varying(20) | Y | Sponsor EIN from the last reported filing | identifier | STRING | dol.column_metadata |
| 46 | `dcg_last_rpt_plan_name` | `dol.schedule_dcg.dcg_last_rpt_plan_name` | character varying(500) | Y | Plan name from the last reported filing | attribute | STRING | dol.column_metadata |
| 47 | `dcg_last_rpt_plan_num` | `dol.schedule_dcg.dcg_last_rpt_plan_num` | character varying(10) | Y | Plan number from the last reported filing | attribute | STRING | dol.column_metadata |
| 48 | `dcg_admin_name` | `dol.schedule_dcg.dcg_admin_name` | character varying(500) | Y | Plan administrator name | attribute | STRING | dol.column_metadata |
| 49 | `dcg_admin_us_address1` | `dol.schedule_dcg.dcg_admin_us_address1` | character varying(500) | Y | Administrator US address line 1 | attribute | STRING | dol.column_metadata |
| 50 | `dcg_admin_us_address2` | `dol.schedule_dcg.dcg_admin_us_address2` | character varying(500) | Y | Administrator US address line 2 | attribute | STRING | dol.column_metadata |
| 51 | `dcg_admin_us_city` | `dol.schedule_dcg.dcg_admin_us_city` | character varying(255) | Y | Administrator US city | attribute | STRING | dol.column_metadata |
| 52 | `dcg_admin_us_state` | `dol.schedule_dcg.dcg_admin_us_state` | character varying(10) | Y | Administrator US state code | attribute | STRING | dol.column_metadata |
| 53 | `dcg_admin_us_zip` | `dol.schedule_dcg.dcg_admin_us_zip` | character varying(20) | Y | Administrator US ZIP code | attribute | STRING | dol.column_metadata |
| 54 | `dcg_admin_foreign_address1` | `dol.schedule_dcg.dcg_admin_foreign_address1` | character varying(500) | Y | Administrator foreign address line 1 | attribute | STRING | dol.column_metadata |
| 55 | `dcg_admin_foreign_address2` | `dol.schedule_dcg.dcg_admin_foreign_address2` | character varying(500) | Y | Administrator foreign address line 2 | attribute | STRING | dol.column_metadata |
| 56 | `dcg_admin_foreign_city` | `dol.schedule_dcg.dcg_admin_foreign_city` | character varying(255) | Y | Administrator foreign city | attribute | STRING | dol.column_metadata |
| 57 | `dcg_admin_foreign_prov_state` | `dol.schedule_dcg.dcg_admin_foreign_prov_state` | character varying(100) | Y | Administrator foreign province/state | attribute | STRING | dol.column_metadata |
| 58 | `dcg_admin_foreign_cntry` | `dol.schedule_dcg.dcg_admin_foreign_cntry` | character varying(100) | Y | Administrator foreign country | attribute | STRING | dol.column_metadata |
| 59 | `dcg_admin_foreign_postal_cd` | `dol.schedule_dcg.dcg_admin_foreign_postal_cd` | character varying(50) | Y | Administrator foreign postal code | attribute | STRING | dol.column_metadata |
| 60 | `dcg_admin_ein` | `dol.schedule_dcg.dcg_admin_ein` | character varying(20) | Y | Administrator EIN | identifier | STRING | dol.column_metadata |
| 61 | `dcg_admin_phone_num` | `dol.schedule_dcg.dcg_admin_phone_num` | character varying(30) | Y | Administrator US phone number | attribute | STRING | dol.column_metadata |
| 62 | `dcg_admin_phone_num_foreign` | `dol.schedule_dcg.dcg_admin_phone_num_foreign` | character varying(30) | Y | Administrator foreign phone number | attribute | STRING | dol.column_metadata |
| 63 | `dcg_tot_partcp_boy_cnt` | `dol.schedule_dcg.dcg_tot_partcp_boy_cnt` | numeric | Y | Total participants at beginning of year | attribute | NUMERIC | dol.column_metadata |
| 64 | `dcg_tot_act_rtd_sep_benef_cnt` | `dol.schedule_dcg.dcg_tot_act_rtd_sep_benef_cnt` | numeric | Y | Total active, retired, separated beneficiaries count | attribute | NUMERIC | dol.column_metadata |
| 65 | `dcg_tot_act_partcp_boy_cnt` | `dol.schedule_dcg.dcg_tot_act_partcp_boy_cnt` | numeric | Y | Total active participants at beginning of year | attribute | NUMERIC | dol.column_metadata |
| 66 | `dcg_tot_act_partcp_eoy_cnt` | `dol.schedule_dcg.dcg_tot_act_partcp_eoy_cnt` | numeric | Y | Total active participants at end of year | attribute | NUMERIC | dol.column_metadata |
| 67 | `dcg_partcp_account_bal_boy_cnt` | `dol.schedule_dcg.dcg_partcp_account_bal_boy_cnt` | numeric | Y | Participants with account balances at beginning of year | attribute | NUMERIC | dol.column_metadata |
| 68 | `dcg_partcp_account_bal_eoy_cnt` | `dol.schedule_dcg.dcg_partcp_account_bal_eoy_cnt` | numeric | Y | Participants with account balances at end of year | attribute | NUMERIC | dol.column_metadata |
| 69 | `dcg_sep_partcp_partl_vstd_cnt` | `dol.schedule_dcg.dcg_sep_partcp_partl_vstd_cnt` | numeric | Y | Separated participants with partially vested benefits | attribute | NUMERIC | dol.column_metadata |
| 70 | `dcg_tot_assets_boy_amt` | `dol.schedule_dcg.dcg_tot_assets_boy_amt` | numeric | Y | Total assets at beginning of year (USD) | attribute | NUMERIC | dol.column_metadata |
| 71 | `dcg_partcp_loans_boy_amt` | `dol.schedule_dcg.dcg_partcp_loans_boy_amt` | numeric | Y | Participant loans at beginning of year (USD) | attribute | NUMERIC | dol.column_metadata |
| 72 | `dcg_tot_liabilities_boy_amt` | `dol.schedule_dcg.dcg_tot_liabilities_boy_amt` | numeric | Y | Total liabilities at beginning of year (USD) | attribute | NUMERIC | dol.column_metadata |
| 73 | `dcg_net_assets_boy_amt` | `dol.schedule_dcg.dcg_net_assets_boy_amt` | numeric | Y | Net assets at beginning of year (USD) | attribute | NUMERIC | dol.column_metadata |
| 74 | `dcg_tot_assets_eoy_amt` | `dol.schedule_dcg.dcg_tot_assets_eoy_amt` | numeric | Y | Total assets at end of year (USD) | attribute | NUMERIC | dol.column_metadata |
| 75 | `dcg_partcp_loans_eoy_amt` | `dol.schedule_dcg.dcg_partcp_loans_eoy_amt` | numeric | Y | Participant loans at end of year (USD) | attribute | NUMERIC | dol.column_metadata |
| 76 | `dcg_tot_liabilities_eoy_amt` | `dol.schedule_dcg.dcg_tot_liabilities_eoy_amt` | numeric | Y | Total liabilities at end of year (USD) | attribute | NUMERIC | dol.column_metadata |
| 77 | `dcg_net_assets_eoy_amt` | `dol.schedule_dcg.dcg_net_assets_eoy_amt` | numeric | Y | Net assets at end of year (USD) | attribute | NUMERIC | dol.column_metadata |
| 78 | `dcg_emplr_contrib_income_amt` | `dol.schedule_dcg.dcg_emplr_contrib_income_amt` | numeric | Y | Employer contributions received (USD) | attribute | NUMERIC | dol.column_metadata |
| 79 | `dcg_participant_contrib_income_amt` | `dol.schedule_dcg.dcg_participant_contrib_income_amt` | numeric | Y | Participant contributions received (USD) | attribute | NUMERIC | dol.column_metadata |
| 80 | `dcg_oth_contrib_rcvd_amt` | `dol.schedule_dcg.dcg_oth_contrib_rcvd_amt` | numeric | Y | Other contributions received (USD) | attribute | NUMERIC | dol.column_metadata |
| 81 | `dcg_non_cash_contrib_amt` | `dol.schedule_dcg.dcg_non_cash_contrib_amt` | numeric | Y | Non-cash contributions (USD) | attribute | NUMERIC | dol.column_metadata |
| 82 | `dcg_tot_contrib_amt` | `dol.schedule_dcg.dcg_tot_contrib_amt` | numeric | Y | Total contributions (USD) | attribute | NUMERIC | dol.column_metadata |
| 83 | `dcg_other_income_amt` | `dol.schedule_dcg.dcg_other_income_amt` | numeric | Y | Other income (USD) | attribute | NUMERIC | dol.column_metadata |
| 84 | `dcg_tot_income_amt` | `dol.schedule_dcg.dcg_tot_income_amt` | numeric | Y | Total income (USD) | attribute | NUMERIC | dol.column_metadata |
| 85 | `dcg_tot_bnft_amt` | `dol.schedule_dcg.dcg_tot_bnft_amt` | numeric | Y | Total benefits paid (USD) | attribute | NUMERIC | dol.column_metadata |
| 86 | `dcg_corrective_distrib_amt` | `dol.schedule_dcg.dcg_corrective_distrib_amt` | numeric | Y | Corrective distributions (USD) | attribute | NUMERIC | dol.column_metadata |
| 87 | `dcg_deemed_distrib_partcp_lns_amt` | `dol.schedule_dcg.dcg_deemed_distrib_partcp_lns_amt` | numeric | Y | Deemed distributions from participant loans (USD) | attribute | NUMERIC | dol.column_metadata |
| 88 | `dcg_admin_srvc_providers_amt` | `dol.schedule_dcg.dcg_admin_srvc_providers_amt` | numeric | Y | Payments to administrative service providers (USD) | attribute | NUMERIC | dol.column_metadata |
| 89 | `dcg_oth_expenses_amt` | `dol.schedule_dcg.dcg_oth_expenses_amt` | numeric | Y | Other expenses (USD) | attribute | NUMERIC | dol.column_metadata |
| 90 | `dcg_tot_expenses_amt` | `dol.schedule_dcg.dcg_tot_expenses_amt` | numeric | Y | Total expenses (USD) | attribute | NUMERIC | dol.column_metadata |
| 91 | `dcg_net_income_amt` | `dol.schedule_dcg.dcg_net_income_amt` | numeric | Y | Net income/loss (USD) | attribute | NUMERIC | dol.column_metadata |
| 92 | `dcg_tot_transfers_to_amt` | `dol.schedule_dcg.dcg_tot_transfers_to_amt` | numeric | Y | Total transfers to other plans (USD) | attribute | NUMERIC | dol.column_metadata |
| 93 | `dcg_tot_transfers_from_amt` | `dol.schedule_dcg.dcg_tot_transfers_from_amt` | numeric | Y | Total transfers from other plans (USD) | attribute | NUMERIC | dol.column_metadata |
| 94 | `dcg_type_pension_bnft_code` | `dol.schedule_dcg.dcg_type_pension_bnft_code` | character varying(50) | Y | Type of pension benefit code | attribute | STRING | dol.column_metadata |
| 95 | `dcg_fail_transmit_contrib_ind` | `dol.schedule_dcg.dcg_fail_transmit_contrib_ind` | character varying(10) | Y | Indicator — employer failed to timely transmit participant contributions | attribute | STRING | dol.column_metadata |
| 96 | `dcg_fail_transmit_contrib_amt` | `dol.schedule_dcg.dcg_fail_transmit_contrib_amt` | numeric | Y | Amount of late-transmitted contributions (USD) | attribute | NUMERIC | dol.column_metadata |
| 97 | `dcg_party_in_int_not_rptd_ind` | `dol.schedule_dcg.dcg_party_in_int_not_rptd_ind` | character varying(10) | Y | Indicator — party-in-interest transactions not reported on Schedule G | attribute | STRING | dol.column_metadata |
| 98 | `dcg_party_in_int_not_rptd_amt` | `dol.schedule_dcg.dcg_party_in_int_not_rptd_amt` | numeric | Y | Amount of unreported party-in-interest transactions (USD) | attribute | NUMERIC | dol.column_metadata |
| 99 | `dcg_fail_provide_benefit_due_ind` | `dol.schedule_dcg.dcg_fail_provide_benefit_due_ind` | character varying(10) | Y | Indicator — plan failed to provide benefits when due | attribute | STRING | dol.column_metadata |
| 100 | `dcg_fail_provide_benefit_due_amt` | `dol.schedule_dcg.dcg_fail_provide_benefit_due_amt` | numeric | Y | Amount of benefits not provided when due (USD) | attribute | NUMERIC | dol.column_metadata |
| 101 | `dcg_fidelity_bond_ind` | `dol.schedule_dcg.dcg_fidelity_bond_ind` | character varying(10) | Y | Indicator — plan covered by fidelity bond | attribute | STRING | dol.column_metadata |
| 102 | `dcg_fidelity_bond_amt` | `dol.schedule_dcg.dcg_fidelity_bond_amt` | numeric | Y | Fidelity bond coverage amount (USD) | attribute | NUMERIC | dol.column_metadata |
| 103 | `dcg_loss_discv_dur_year_ind` | `dol.schedule_dcg.dcg_loss_discv_dur_year_ind` | character varying(10) | Y | Indicator — losses discovered during year due to fraud/dishonesty | attribute | STRING | dol.column_metadata |
| 104 | `dcg_loss_discv_dur_year_amt` | `dol.schedule_dcg.dcg_loss_discv_dur_year_amt` | numeric | Y | Amount of losses discovered (USD) | attribute | NUMERIC | dol.column_metadata |
| 105 | `dcg_dc_plan_funding_reqd_ind` | `dol.schedule_dcg.dcg_dc_plan_funding_reqd_ind` | character varying(10) | Y | Indicator — defined contribution plan funding required | attribute | STRING | dol.column_metadata |
| 106 | `dcg_plan_satisfy_tests_ind` | `dol.schedule_dcg.dcg_plan_satisfy_tests_ind` | character varying(10) | Y | Indicator — plan satisfied coverage/nondiscrimination tests | attribute | STRING | dol.column_metadata |
| 107 | `dcg_401k_design_based_safe_harbor_ind` | `dol.schedule_dcg.dcg_401k_design_based_safe_harbor_ind` | character varying(10) | Y | Indicator — 401(k) uses design-based safe harbor | attribute | STRING | dol.column_metadata |
| 108 | `dcg_401k_prior_year_adp_test_ind` | `dol.schedule_dcg.dcg_401k_prior_year_adp_test_ind` | character varying(10) | Y | Indicator — 401(k) uses prior year ADP test | attribute | STRING | dol.column_metadata |
| 109 | `dcg_401k_current_year_adp_test_ind` | `dol.schedule_dcg.dcg_401k_current_year_adp_test_ind` | character varying(10) | Y | Indicator — 401(k) uses current year ADP test | attribute | STRING | dol.column_metadata |
| 110 | `dcg_401k_na_ind` | `dol.schedule_dcg.dcg_401k_na_ind` | character varying(10) | Y | Indicator — 401(k) testing not applicable | attribute | STRING | dol.column_metadata |
| 111 | `dcg_opin_letter_date` | `dol.schedule_dcg.dcg_opin_letter_date` | character varying(30) | Y | Date of IRS opinion/advisory letter | attribute | STRING | dol.column_metadata |
| 112 | `dcg_opin_letter_serial_num` | `dol.schedule_dcg.dcg_opin_letter_serial_num` | character varying(50) | Y | IRS opinion/advisory letter serial number | attribute | STRING | dol.column_metadata |
| 113 | `dcg_iqpa_attached_ind` | `dol.schedule_dcg.dcg_iqpa_attached_ind` | character varying(10) | Y | Indicator — Independent Qualified Public Accountant (IQPA) report attached | attribute | STRING | dol.column_metadata |
| 114 | `dcg_acctnt_opinion_type_cd` | `dol.schedule_dcg.dcg_acctnt_opinion_type_cd` | character varying(10) | Y | Accountant opinion type code (1=Unqualified, 2=Qualified, 3=Disclaimer, 4=Adverse) | attribute | STRING | dol.column_metadata |
| 115 | `dcg_acct_performed_ltd_audit_103_8_ind` | `dol.schedule_dcg.dcg_acct_performed_ltd_audit_103_8_ind` | character varying(10) | Y | Indicator — accountant performed limited-scope audit per ERISA Sec 103(a)(3)(C) — DOL Reg 2520.103-8 | attribute | STRING | dol.column_metadata |
| 116 | `dcg_acct_performed_ltd_audit_103_12d_ind` | `dol.schedule_dcg.dcg_acct_performed_ltd_audit_103_12d_ind` | character varying(10) | Y | Indicator — accountant performed limited-scope audit per DOL Reg 2520.103-12(d) | attribute | STRING | dol.column_metadata |
| 117 | `dcg_acct_performed_not_ltd_audit_ind` | `dol.schedule_dcg.dcg_acct_performed_not_ltd_audit_ind` | character varying(10) | Y | Indicator — accountant performed full (non-limited-scope) audit | attribute | STRING | dol.column_metadata |
| 118 | `dcg_accountant_firm_name` | `dol.schedule_dcg.dcg_accountant_firm_name` | character varying(500) | Y | Name of the accounting firm | attribute | STRING | dol.column_metadata |
| 119 | `dcg_accountant_firm_ein` | `dol.schedule_dcg.dcg_accountant_firm_ein` | character varying(20) | Y | EIN of the accounting firm | identifier | STRING | dol.column_metadata |
| 120 | `form_year` | `dol.schedule_dcg.form_year` | character varying(10) | Y | Filing year (2023, 2024, 2025, etc.) — partition key for cross-year queries | attribute | STRING | dol.column_metadata |
| 121 | `created_at` | `dol.schedule_dcg.created_at` | timestamp with time zone | N | Timestamp when this row was loaded into the database | attribute | ISO-8601 | dol.column_metadata |

### `dol.schedule_g` -- UNREGISTERED -- 568 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `dol.schedule_g.id` | bigint | N | Auto-increment surrogate primary key | attribute | INTEGER | dol.column_metadata |
| 2 | `ack_id` | `dol.schedule_g.ack_id` | character varying(50) | N | DOL acknowledgment ID — unique filing identifier. Foreign key to dol.form_5500.ack_id or dol.form_5500_sf.ack_id for joining across schedules | attribute | STRING | dol.column_metadata |
| 3 | `sch_g_plan_year_begin_date` | `dol.schedule_g.sch_g_plan_year_begin_date` | character varying(30) | Y | First day of the plan year (YYYY-MM-DD) | attribute | STRING | dol.column_metadata |
| 4 | `sch_g_tax_prd` | `dol.schedule_g.sch_g_tax_prd` | character varying(30) | Y | Tax period end date | attribute | STRING | dol.column_metadata |
| 5 | `sch_g_pn` | `dol.schedule_g.sch_g_pn` | character varying(10) | Y | Plan number | identifier | STRING | dol.column_metadata |
| 6 | `sch_g_ein` | `dol.schedule_g.sch_g_ein` | character varying(20) | Y | EIN of the plan sponsor | identifier | STRING | dol.column_metadata |
| 7 | `form_year` | `dol.schedule_g.form_year` | character varying(10) | Y | Filing year (2023, 2024, 2025, etc.) — partition key for cross-year queries | attribute | STRING | dol.column_metadata |
| 8 | `created_at` | `dol.schedule_g.created_at` | timestamp with time zone | N | Timestamp when this row was loaded into the database | attribute | ISO-8601 | dol.column_metadata |

### `dol.schedule_g_part1` -- UNREGISTERED -- 784 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `dol.schedule_g_part1.id` | bigint | N | Auto-increment surrogate primary key | attribute | INTEGER | dol.column_metadata |
| 2 | `ack_id` | `dol.schedule_g_part1.ack_id` | character varying(50) | N | DOL acknowledgment ID — unique filing identifier. Foreign key to dol.form_5500.ack_id or dol.form_5500_sf.ack_id for joining across schedules | attribute | STRING | dol.column_metadata |
| 3 | `row_order` | `dol.schedule_g_part1.row_order` | integer | Y | Sequence number within a single filing — preserves original CSV row ordering when multiple line items exist per filing | attribute | INTEGER | dol.column_metadata |
| 4 | `lns_default_pii_ind` | `dol.schedule_g_part1.lns_default_pii_ind` | character varying(10) | Y | Indicator — party-in-interest involvement in the defaulted loan | attribute | STRING | dol.column_metadata |
| 5 | `lns_default_obligor_name` | `dol.schedule_g_part1.lns_default_obligor_name` | character varying(500) | Y | Name of the loan obligor in default | attribute | STRING | dol.column_metadata |
| 6 | `lns_default_obligor_us_addr1` | `dol.schedule_g_part1.lns_default_obligor_us_addr1` | character varying(500) | Y | Obligor US address line 1 | attribute | STRING | dol.column_metadata |
| 7 | `lns_default_obligor_us_addr2` | `dol.schedule_g_part1.lns_default_obligor_us_addr2` | character varying(500) | Y | Obligor US address line 2 | attribute | STRING | dol.column_metadata |
| 8 | `lns_default_obligor_us_city` | `dol.schedule_g_part1.lns_default_obligor_us_city` | character varying(255) | Y | Obligor US city | attribute | STRING | dol.column_metadata |
| 9 | `lns_default_obligor_us_state` | `dol.schedule_g_part1.lns_default_obligor_us_state` | character varying(10) | Y | Obligor US state code | attribute | STRING | dol.column_metadata |
| 10 | `lns_default_obligor_us_zip` | `dol.schedule_g_part1.lns_default_obligor_us_zip` | character varying(20) | Y | Obligor US ZIP code | attribute | STRING | dol.column_metadata |
| 11 | `lns_dft_obligor_foreign_addr1` | `dol.schedule_g_part1.lns_dft_obligor_foreign_addr1` | character varying(500) | Y | Obligor foreign address line 1 | attribute | STRING | dol.column_metadata |
| 12 | `lns_dft_obligor_foreign_addr2` | `dol.schedule_g_part1.lns_dft_obligor_foreign_addr2` | character varying(500) | Y | Obligor foreign address line 2 | attribute | STRING | dol.column_metadata |
| 13 | `lns_dft_obligor_foreign_city` | `dol.schedule_g_part1.lns_dft_obligor_foreign_city` | character varying(255) | Y | Obligor foreign city | attribute | STRING | dol.column_metadata |
| 14 | `lns_dft_obligor_forgn_prov_st` | `dol.schedule_g_part1.lns_dft_obligor_forgn_prov_st` | character varying(100) | Y | Obligor foreign province/state | attribute | STRING | dol.column_metadata |
| 15 | `lns_dft_obligor_forgn_country` | `dol.schedule_g_part1.lns_dft_obligor_forgn_country` | character varying(100) | Y | Obligor foreign country | attribute | STRING | dol.column_metadata |
| 16 | `lns_dft_obligor_forgn_post_cd` | `dol.schedule_g_part1.lns_dft_obligor_forgn_post_cd` | character varying(50) | Y | Obligor foreign postal code | attribute | STRING | dol.column_metadata |
| 17 | `lns_default_description_text` | `dol.schedule_g_part1.lns_default_description_text` | text | Y | Description of the defaulted loan terms | attribute | STRING | dol.column_metadata |
| 18 | `lns_default_original_amt` | `dol.schedule_g_part1.lns_default_original_amt` | numeric | Y | Original loan amount (USD) | attribute | NUMERIC | dol.column_metadata |
| 19 | `lns_default_prncpl_rcvd_amt` | `dol.schedule_g_part1.lns_default_prncpl_rcvd_amt` | numeric | Y | Principal payments received (USD) | attribute | NUMERIC | dol.column_metadata |
| 20 | `lns_default_int_rcvd_amt` | `dol.schedule_g_part1.lns_default_int_rcvd_amt` | numeric | Y | Interest payments received (USD) | attribute | NUMERIC | dol.column_metadata |
| 21 | `lns_default_unpaid_bal_amt` | `dol.schedule_g_part1.lns_default_unpaid_bal_amt` | numeric | Y | Unpaid balance (USD) | attribute | NUMERIC | dol.column_metadata |
| 22 | `lns_default_prcpl_overdue_amt` | `dol.schedule_g_part1.lns_default_prcpl_overdue_amt` | numeric | Y | Overdue principal amount (USD) | attribute | NUMERIC | dol.column_metadata |
| 23 | `lns_default_int_overdue_amt` | `dol.schedule_g_part1.lns_default_int_overdue_amt` | numeric | Y | Overdue interest amount (USD) | attribute | NUMERIC | dol.column_metadata |
| 24 | `form_year` | `dol.schedule_g_part1.form_year` | character varying(10) | Y | Filing year (2023, 2024, 2025, etc.) — partition key for cross-year queries | attribute | STRING | dol.column_metadata |
| 25 | `created_at` | `dol.schedule_g_part1.created_at` | timestamp with time zone | N | Timestamp when this row was loaded into the database | attribute | ISO-8601 | dol.column_metadata |

### `dol.schedule_g_part2` -- UNREGISTERED -- 97 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `dol.schedule_g_part2.id` | bigint | N | Auto-increment surrogate primary key | attribute | INTEGER | dol.column_metadata |
| 2 | `ack_id` | `dol.schedule_g_part2.ack_id` | character varying(50) | N | DOL acknowledgment ID — unique filing identifier. Foreign key to dol.form_5500.ack_id or dol.form_5500_sf.ack_id for joining across schedules | attribute | STRING | dol.column_metadata |
| 3 | `row_order` | `dol.schedule_g_part2.row_order` | integer | Y | Sequence number within a single filing — preserves original CSV row ordering when multiple line items exist per filing | attribute | INTEGER | dol.column_metadata |
| 4 | `leases_default_pii_ind` | `dol.schedule_g_part2.leases_default_pii_ind` | character varying(10) | Y | Indicator — party-in-interest involvement in the defaulted lease | attribute | STRING | dol.column_metadata |
| 5 | `leases_default_lessor_name` | `dol.schedule_g_part2.leases_default_lessor_name` | character varying(500) | Y | Name of the lessor in default | attribute | STRING | dol.column_metadata |
| 6 | `leases_default_relation_text` | `dol.schedule_g_part2.leases_default_relation_text` | text | Y | Relationship of lessor to the plan | attribute | STRING | dol.column_metadata |
| 7 | `leases_default_terms_text` | `dol.schedule_g_part2.leases_default_terms_text` | text | Y | Description of the lease terms | attribute | STRING | dol.column_metadata |
| 8 | `leases_default_cost_amt` | `dol.schedule_g_part2.leases_default_cost_amt` | numeric | Y | Original cost of the leased property (USD) | attribute | NUMERIC | dol.column_metadata |
| 9 | `leases_default_curr_value_amt` | `dol.schedule_g_part2.leases_default_curr_value_amt` | numeric | Y | Current value of the leased property (USD) | attribute | NUMERIC | dol.column_metadata |
| 10 | `leases_default_rentl_rcpt_amt` | `dol.schedule_g_part2.leases_default_rentl_rcpt_amt` | numeric | Y | Gross rental receipts (USD) | attribute | NUMERIC | dol.column_metadata |
| 11 | `leases_default_expense_pd_amt` | `dol.schedule_g_part2.leases_default_expense_pd_amt` | numeric | Y | Expenses paid by plan related to the lease (USD) | attribute | NUMERIC | dol.column_metadata |
| 12 | `leases_default_net_rcpt_amt` | `dol.schedule_g_part2.leases_default_net_rcpt_amt` | numeric | Y | Net rental receipts (USD) | attribute | NUMERIC | dol.column_metadata |
| 13 | `leases_default_arrears_amt` | `dol.schedule_g_part2.leases_default_arrears_amt` | numeric | Y | Amount in arrears (USD) | attribute | NUMERIC | dol.column_metadata |
| 14 | `form_year` | `dol.schedule_g_part2.form_year` | character varying(10) | Y | Filing year (2023, 2024, 2025, etc.) — partition key for cross-year queries | attribute | STRING | dol.column_metadata |
| 15 | `created_at` | `dol.schedule_g_part2.created_at` | timestamp with time zone | N | Timestamp when this row was loaded into the database | attribute | ISO-8601 | dol.column_metadata |

### `dol.schedule_g_part3` -- UNREGISTERED -- 469 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `dol.schedule_g_part3.id` | bigint | N | Auto-increment surrogate primary key | attribute | INTEGER | dol.column_metadata |
| 2 | `ack_id` | `dol.schedule_g_part3.ack_id` | character varying(50) | N | DOL acknowledgment ID — unique filing identifier. Foreign key to dol.form_5500.ack_id or dol.form_5500_sf.ack_id for joining across schedules | attribute | STRING | dol.column_metadata |
| 3 | `row_order` | `dol.schedule_g_part3.row_order` | integer | Y | Sequence number within a single filing — preserves original CSV row ordering when multiple line items exist per filing | attribute | INTEGER | dol.column_metadata |
| 4 | `non_exempt_party_name` | `dol.schedule_g_part3.non_exempt_party_name` | character varying(500) | Y | Name of the party involved in the nonexempt transaction | attribute | STRING | dol.column_metadata |
| 5 | `non_exempt_relation_text` | `dol.schedule_g_part3.non_exempt_relation_text` | text | Y | Relationship of the party to the plan | attribute | STRING | dol.column_metadata |
| 6 | `non_exempt_terms_text` | `dol.schedule_g_part3.non_exempt_terms_text` | text | Y | Description of the transaction terms | attribute | STRING | dol.column_metadata |
| 7 | `non_exempt_pur_price_amt` | `dol.schedule_g_part3.non_exempt_pur_price_amt` | numeric | Y | Purchase price (USD) | attribute | NUMERIC | dol.column_metadata |
| 8 | `non_exempt_sell_price_amt` | `dol.schedule_g_part3.non_exempt_sell_price_amt` | numeric | Y | Selling price (USD) | attribute | NUMERIC | dol.column_metadata |
| 9 | `non_exempt_ls_rntl_amt` | `dol.schedule_g_part3.non_exempt_ls_rntl_amt` | numeric | Y | Lease/rental amount (USD) | attribute | NUMERIC | dol.column_metadata |
| 10 | `non_exempt_expense_incr_amt` | `dol.schedule_g_part3.non_exempt_expense_incr_amt` | numeric | Y | Expenses incurred (USD) | attribute | NUMERIC | dol.column_metadata |
| 11 | `non_exempt_cost_ast_amt` | `dol.schedule_g_part3.non_exempt_cost_ast_amt` | numeric | Y | Cost of asset (USD) | attribute | NUMERIC | dol.column_metadata |
| 12 | `non_exempt_curr_value_ast_amt` | `dol.schedule_g_part3.non_exempt_curr_value_ast_amt` | numeric | Y | Current value of asset (USD) | attribute | NUMERIC | dol.column_metadata |
| 13 | `non_exempt_gain_loss_amt` | `dol.schedule_g_part3.non_exempt_gain_loss_amt` | numeric | Y | Net gain or loss on the transaction (USD) | attribute | NUMERIC | dol.column_metadata |
| 14 | `form_year` | `dol.schedule_g_part3.form_year` | character varying(10) | Y | Filing year (2023, 2024, 2025, etc.) — partition key for cross-year queries | attribute | STRING | dol.column_metadata |
| 15 | `created_at` | `dol.schedule_g_part3.created_at` | timestamp with time zone | N | Timestamp when this row was loaded into the database | attribute | ISO-8601 | dol.column_metadata |

### `dol.schedule_h` -- UNREGISTERED -- 169,276 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `dol.schedule_h.id` | bigint | N | Auto-increment surrogate primary key | attribute | INTEGER | dol.column_metadata |
| 2 | `ack_id` | `dol.schedule_h.ack_id` | character varying(50) | N | DOL acknowledgment ID — unique filing identifier. Foreign key to dol.form_5500.ack_id or dol.form_5500_sf.ack_id for joining across schedules | attribute | STRING | dol.column_metadata |
| 3 | `sch_h_plan_year_begin_date` | `dol.schedule_h.sch_h_plan_year_begin_date` | character varying(30) | Y | First day of the plan year (YYYY-MM-DD) | attribute | STRING | dol.column_metadata |
| 4 | `sch_h_tax_prd` | `dol.schedule_h.sch_h_tax_prd` | character varying(30) | Y | Tax period end date | attribute | STRING | dol.column_metadata |
| 5 | `sch_h_pn` | `dol.schedule_h.sch_h_pn` | character varying(10) | Y | Plan number | identifier | STRING | dol.column_metadata |
| 6 | `sch_h_ein` | `dol.schedule_h.sch_h_ein` | character varying(20) | Y | EIN of the plan sponsor | identifier | STRING | dol.column_metadata |
| 7 | `non_int_bear_cash_boy_amt` | `dol.schedule_h.non_int_bear_cash_boy_amt` | numeric | Y | Non-interest-bearing cash — beginning of year (USD) | attribute | NUMERIC | dol.column_metadata |
| 8 | `emplr_contrib_boy_amt` | `dol.schedule_h.emplr_contrib_boy_amt` | numeric | Y | Employer contributions receivable — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 9 | `partcp_contrib_boy_amt` | `dol.schedule_h.partcp_contrib_boy_amt` | numeric | Y | Participant contributions receivable — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 10 | `other_receivables_boy_amt` | `dol.schedule_h.other_receivables_boy_amt` | numeric | Y | Other receivables — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 11 | `int_bear_cash_boy_amt` | `dol.schedule_h.int_bear_cash_boy_amt` | numeric | Y | Interest-bearing cash — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 12 | `govt_sec_boy_amt` | `dol.schedule_h.govt_sec_boy_amt` | numeric | Y | US government securities — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 13 | `corp_debt_preferred_boy_amt` | `dol.schedule_h.corp_debt_preferred_boy_amt` | numeric | Y | Corporate debt instruments (preferred) — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 14 | `corp_debt_other_boy_amt` | `dol.schedule_h.corp_debt_other_boy_amt` | numeric | Y | Corporate debt instruments (other) — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 15 | `pref_stock_boy_amt` | `dol.schedule_h.pref_stock_boy_amt` | numeric | Y | Preferred stock — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 16 | `common_stock_boy_amt` | `dol.schedule_h.common_stock_boy_amt` | numeric | Y | Common stock — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 17 | `joint_venture_boy_amt` | `dol.schedule_h.joint_venture_boy_amt` | numeric | Y | Partnership/joint venture interests — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 18 | `real_estate_boy_amt` | `dol.schedule_h.real_estate_boy_amt` | numeric | Y | Real estate (other than employer property) — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 19 | `other_loans_boy_amt` | `dol.schedule_h.other_loans_boy_amt` | numeric | Y | Loans (other than to participants) — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 20 | `partcp_loans_boy_amt` | `dol.schedule_h.partcp_loans_boy_amt` | numeric | Y | Participant loans — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 21 | `int_common_tr_boy_amt` | `dol.schedule_h.int_common_tr_boy_amt` | numeric | Y | Value of interest in common/collective trusts — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 22 | `int_pool_sep_acct_boy_amt` | `dol.schedule_h.int_pool_sep_acct_boy_amt` | numeric | Y | Value of interest in pooled separate accounts — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 23 | `int_master_tr_boy_amt` | `dol.schedule_h.int_master_tr_boy_amt` | numeric | Y | Value of interest in master trust — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 24 | `int_103_12_invst_boy_amt` | `dol.schedule_h.int_103_12_invst_boy_amt` | numeric | Y | Value of interest in 103-12 investment entities — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 25 | `int_reg_invst_co_boy_amt` | `dol.schedule_h.int_reg_invst_co_boy_amt` | numeric | Y | Value of interest in registered investment companies — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 26 | `ins_co_gen_acct_boy_amt` | `dol.schedule_h.ins_co_gen_acct_boy_amt` | numeric | Y | Value of funds in insurance company general accounts — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 27 | `oth_invst_boy_amt` | `dol.schedule_h.oth_invst_boy_amt` | numeric | Y | Other investments — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 28 | `emplr_sec_boy_amt` | `dol.schedule_h.emplr_sec_boy_amt` | numeric | Y | Employer securities — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 29 | `emplr_prop_boy_amt` | `dol.schedule_h.emplr_prop_boy_amt` | numeric | Y | Employer real property — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 30 | `bldgs_used_boy_amt` | `dol.schedule_h.bldgs_used_boy_amt` | numeric | Y | Buildings and other property used in plan operation — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 31 | `tot_assets_boy_amt` | `dol.schedule_h.tot_assets_boy_amt` | numeric | Y | Total assets — beginning of year (USD) | attribute | NUMERIC | dol.column_metadata |
| 32 | `bnfts_payable_boy_amt` | `dol.schedule_h.bnfts_payable_boy_amt` | numeric | Y | Benefit claims payable — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 33 | `oprtng_payable_boy_amt` | `dol.schedule_h.oprtng_payable_boy_amt` | numeric | Y | Operating payables — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 34 | `acquis_indbt_boy_amt` | `dol.schedule_h.acquis_indbt_boy_amt` | numeric | Y | Acquisition indebtedness — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 35 | `other_liab_boy_amt` | `dol.schedule_h.other_liab_boy_amt` | numeric | Y | Other liabilities — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 36 | `tot_liabilities_boy_amt` | `dol.schedule_h.tot_liabilities_boy_amt` | numeric | Y | Total liabilities — BOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 37 | `net_assets_boy_amt` | `dol.schedule_h.net_assets_boy_amt` | numeric | Y | Net assets — beginning of year (USD) | attribute | NUMERIC | dol.column_metadata |
| 38 | `non_int_bear_cash_eoy_amt` | `dol.schedule_h.non_int_bear_cash_eoy_amt` | numeric | Y | Non-interest-bearing cash — end of year (USD) | attribute | NUMERIC | dol.column_metadata |
| 39 | `emplr_contrib_eoy_amt` | `dol.schedule_h.emplr_contrib_eoy_amt` | numeric | Y | Employer contributions receivable — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 40 | `partcp_contrib_eoy_amt` | `dol.schedule_h.partcp_contrib_eoy_amt` | numeric | Y | Participant contributions receivable — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 41 | `other_receivables_eoy_amt` | `dol.schedule_h.other_receivables_eoy_amt` | numeric | Y | Other receivables — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 42 | `int_bear_cash_eoy_amt` | `dol.schedule_h.int_bear_cash_eoy_amt` | numeric | Y | Interest-bearing cash — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 43 | `govt_sec_eoy_amt` | `dol.schedule_h.govt_sec_eoy_amt` | numeric | Y | US government securities — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 44 | `corp_debt_preferred_eoy_amt` | `dol.schedule_h.corp_debt_preferred_eoy_amt` | numeric | Y | Corporate debt instruments (preferred) — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 45 | `corp_debt_other_eoy_amt` | `dol.schedule_h.corp_debt_other_eoy_amt` | numeric | Y | Corporate debt instruments (other) — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 46 | `pref_stock_eoy_amt` | `dol.schedule_h.pref_stock_eoy_amt` | numeric | Y | Preferred stock — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 47 | `common_stock_eoy_amt` | `dol.schedule_h.common_stock_eoy_amt` | numeric | Y | Common stock — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 48 | `joint_venture_eoy_amt` | `dol.schedule_h.joint_venture_eoy_amt` | numeric | Y | Partnership/joint venture interests — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 49 | `real_estate_eoy_amt` | `dol.schedule_h.real_estate_eoy_amt` | numeric | Y | Real estate (other than employer property) — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 50 | `other_loans_eoy_amt` | `dol.schedule_h.other_loans_eoy_amt` | numeric | Y | Loans (other than to participants) — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 51 | `partcp_loans_eoy_amt` | `dol.schedule_h.partcp_loans_eoy_amt` | numeric | Y | Participant loans — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 52 | `int_common_tr_eoy_amt` | `dol.schedule_h.int_common_tr_eoy_amt` | numeric | Y | Value of interest in common/collective trusts — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 53 | `int_pool_sep_acct_eoy_amt` | `dol.schedule_h.int_pool_sep_acct_eoy_amt` | numeric | Y | Value of interest in pooled separate accounts — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 54 | `int_master_tr_eoy_amt` | `dol.schedule_h.int_master_tr_eoy_amt` | numeric | Y | Value of interest in master trust — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 55 | `int_103_12_invst_eoy_amt` | `dol.schedule_h.int_103_12_invst_eoy_amt` | numeric | Y | Value of interest in 103-12 investment entities — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 56 | `int_reg_invst_co_eoy_amt` | `dol.schedule_h.int_reg_invst_co_eoy_amt` | numeric | Y | Value of interest in registered investment companies — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 57 | `ins_co_gen_acct_eoy_amt` | `dol.schedule_h.ins_co_gen_acct_eoy_amt` | numeric | Y | Value of funds in insurance company general accounts — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 58 | `oth_invst_eoy_amt` | `dol.schedule_h.oth_invst_eoy_amt` | numeric | Y | Other investments — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 59 | `emplr_sec_eoy_amt` | `dol.schedule_h.emplr_sec_eoy_amt` | numeric | Y | Employer securities — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 60 | `emplr_prop_eoy_amt` | `dol.schedule_h.emplr_prop_eoy_amt` | numeric | Y | Employer real property — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 61 | `bldgs_used_eoy_amt` | `dol.schedule_h.bldgs_used_eoy_amt` | numeric | Y | Buildings and other property used in plan operation — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 62 | `tot_assets_eoy_amt` | `dol.schedule_h.tot_assets_eoy_amt` | numeric | Y | Total assets — end of year (USD) | attribute | NUMERIC | dol.column_metadata |
| 63 | `bnfts_payable_eoy_amt` | `dol.schedule_h.bnfts_payable_eoy_amt` | numeric | Y | Benefit claims payable — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 64 | `oprtng_payable_eoy_amt` | `dol.schedule_h.oprtng_payable_eoy_amt` | numeric | Y | Operating payables — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 65 | `acquis_indbt_eoy_amt` | `dol.schedule_h.acquis_indbt_eoy_amt` | numeric | Y | Acquisition indebtedness — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 66 | `other_liab_eoy_amt` | `dol.schedule_h.other_liab_eoy_amt` | numeric | Y | Other liabilities — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 67 | `tot_liabilities_eoy_amt` | `dol.schedule_h.tot_liabilities_eoy_amt` | numeric | Y | Total liabilities — EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 68 | `net_assets_eoy_amt` | `dol.schedule_h.net_assets_eoy_amt` | numeric | Y | Net assets — end of year (USD) | attribute | NUMERIC | dol.column_metadata |
| 69 | `emplr_contrib_income_amt` | `dol.schedule_h.emplr_contrib_income_amt` | numeric | Y | Employer contributions received (USD) | attribute | NUMERIC | dol.column_metadata |
| 70 | `participant_contrib_amt` | `dol.schedule_h.participant_contrib_amt` | numeric | Y | Participant contributions received (USD) | attribute | NUMERIC | dol.column_metadata |
| 71 | `oth_contrib_rcvd_amt` | `dol.schedule_h.oth_contrib_rcvd_amt` | numeric | Y | Other contributions received (USD) | attribute | NUMERIC | dol.column_metadata |
| 72 | `non_cash_contrib_bs_amt` | `dol.schedule_h.non_cash_contrib_bs_amt` | numeric | Y | Non-cash contributions included in total (USD) | attribute | NUMERIC | dol.column_metadata |
| 73 | `tot_contrib_amt` | `dol.schedule_h.tot_contrib_amt` | numeric | Y | Total contributions (USD) | attribute | NUMERIC | dol.column_metadata |
| 74 | `int_bear_cash_amt` | `dol.schedule_h.int_bear_cash_amt` | numeric | Y | Interest on interest-bearing cash (USD) | attribute | NUMERIC | dol.column_metadata |
| 75 | `int_on_govt_sec_amt` | `dol.schedule_h.int_on_govt_sec_amt` | numeric | Y | Interest on government securities (USD) | attribute | NUMERIC | dol.column_metadata |
| 76 | `int_on_corp_debt_amt` | `dol.schedule_h.int_on_corp_debt_amt` | numeric | Y | Interest on corporate debt instruments (USD) | attribute | NUMERIC | dol.column_metadata |
| 77 | `int_on_oth_loans_amt` | `dol.schedule_h.int_on_oth_loans_amt` | numeric | Y | Interest on other loans (USD) | attribute | NUMERIC | dol.column_metadata |
| 78 | `int_on_partcp_loans_amt` | `dol.schedule_h.int_on_partcp_loans_amt` | numeric | Y | Interest on participant loans (USD) | attribute | NUMERIC | dol.column_metadata |
| 79 | `int_on_oth_invst_amt` | `dol.schedule_h.int_on_oth_invst_amt` | numeric | Y | Interest on other investments (USD) | attribute | NUMERIC | dol.column_metadata |
| 80 | `total_interest_amt` | `dol.schedule_h.total_interest_amt` | numeric | Y | Total interest income (USD) | attribute | NUMERIC | dol.column_metadata |
| 81 | `divnd_pref_stock_amt` | `dol.schedule_h.divnd_pref_stock_amt` | numeric | Y | Dividends from preferred stock (USD) | attribute | NUMERIC | dol.column_metadata |
| 82 | `divnd_common_stock_amt` | `dol.schedule_h.divnd_common_stock_amt` | numeric | Y | Dividends from common stock (USD) | attribute | NUMERIC | dol.column_metadata |
| 83 | `registered_invst_amt` | `dol.schedule_h.registered_invst_amt` | numeric | Y | Dividends from registered investment companies (USD) | attribute | NUMERIC | dol.column_metadata |
| 84 | `total_dividends_amt` | `dol.schedule_h.total_dividends_amt` | numeric | Y | Total dividend income (USD) | attribute | NUMERIC | dol.column_metadata |
| 85 | `total_rents_amt` | `dol.schedule_h.total_rents_amt` | numeric | Y | Total rents (USD) | attribute | NUMERIC | dol.column_metadata |
| 86 | `aggregate_proceeds_amt` | `dol.schedule_h.aggregate_proceeds_amt` | numeric | Y | Aggregate proceeds from sale/exchange of assets (USD) | attribute | NUMERIC | dol.column_metadata |
| 87 | `aggregate_costs_amt` | `dol.schedule_h.aggregate_costs_amt` | numeric | Y | Aggregate costs of sold/exchanged assets (USD) | attribute | NUMERIC | dol.column_metadata |
| 88 | `tot_gain_loss_sale_ast_amt` | `dol.schedule_h.tot_gain_loss_sale_ast_amt` | numeric | Y | Net gain/loss on sale of assets (USD) | attribute | NUMERIC | dol.column_metadata |
| 89 | `unrealzd_apprctn_re_amt` | `dol.schedule_h.unrealzd_apprctn_re_amt` | numeric | Y | Unrealized appreciation/depreciation — real estate (USD) | attribute | NUMERIC | dol.column_metadata |
| 90 | `unrealzd_apprctn_oth_amt` | `dol.schedule_h.unrealzd_apprctn_oth_amt` | numeric | Y | Unrealized appreciation/depreciation — other (USD) | attribute | NUMERIC | dol.column_metadata |
| 91 | `tot_unrealzd_apprctn_amt` | `dol.schedule_h.tot_unrealzd_apprctn_amt` | numeric | Y | Total unrealized appreciation/depreciation (USD) | attribute | NUMERIC | dol.column_metadata |
| 92 | `gain_loss_com_trust_amt` | `dol.schedule_h.gain_loss_com_trust_amt` | numeric | Y | Net investment gain/loss from common/collective trusts (USD) | attribute | NUMERIC | dol.column_metadata |
| 93 | `gain_loss_pool_sep_amt` | `dol.schedule_h.gain_loss_pool_sep_amt` | numeric | Y | Net investment gain/loss from pooled separate accounts (USD) | attribute | NUMERIC | dol.column_metadata |
| 94 | `gain_loss_master_tr_amt` | `dol.schedule_h.gain_loss_master_tr_amt` | numeric | Y | Net investment gain/loss from master trusts (USD) | attribute | NUMERIC | dol.column_metadata |
| 95 | `gain_loss_103_12_invst_amt` | `dol.schedule_h.gain_loss_103_12_invst_amt` | numeric | Y | Net investment gain/loss from 103-12 investment entities (USD) | attribute | NUMERIC | dol.column_metadata |
| 96 | `gain_loss_reg_invst_amt` | `dol.schedule_h.gain_loss_reg_invst_amt` | numeric | Y | Net investment gain/loss from registered investment companies (USD) | attribute | NUMERIC | dol.column_metadata |
| 97 | `other_income_amt` | `dol.schedule_h.other_income_amt` | numeric | Y | Other income (USD) | attribute | NUMERIC | dol.column_metadata |
| 98 | `tot_income_amt` | `dol.schedule_h.tot_income_amt` | numeric | Y | Total income (USD) | attribute | NUMERIC | dol.column_metadata |
| 99 | `distrib_drt_partcp_amt` | `dol.schedule_h.distrib_drt_partcp_amt` | numeric | Y | Distributions directly to participants/beneficiaries (USD) | attribute | NUMERIC | dol.column_metadata |
| 100 | `ins_carrier_bnfts_amt` | `dol.schedule_h.ins_carrier_bnfts_amt` | numeric | Y | Benefits paid via insurance carriers (USD) | attribute | NUMERIC | dol.column_metadata |
| 101 | `oth_bnft_payment_amt` | `dol.schedule_h.oth_bnft_payment_amt` | numeric | Y | Other benefit payments (USD) | attribute | NUMERIC | dol.column_metadata |
| 102 | `tot_distrib_bnft_amt` | `dol.schedule_h.tot_distrib_bnft_amt` | numeric | Y | Total benefit distributions (USD) | attribute | NUMERIC | dol.column_metadata |
| 103 | `tot_corrective_distrib_amt` | `dol.schedule_h.tot_corrective_distrib_amt` | numeric | Y | Corrective distributions (USD) | attribute | NUMERIC | dol.column_metadata |
| 104 | `tot_deemed_distr_part_lns_amt` | `dol.schedule_h.tot_deemed_distr_part_lns_amt` | numeric | Y | Deemed distributions from participant loans (USD) | attribute | NUMERIC | dol.column_metadata |
| 105 | `tot_int_expense_amt` | `dol.schedule_h.tot_int_expense_amt` | numeric | Y | Total interest expense (USD) | attribute | NUMERIC | dol.column_metadata |
| 106 | `professional_fees_amt` | `dol.schedule_h.professional_fees_amt` | numeric | Y | Professional fees (legal, accounting) (USD) | attribute | NUMERIC | dol.column_metadata |
| 107 | `contract_admin_fees_amt` | `dol.schedule_h.contract_admin_fees_amt` | numeric | Y | Contract administrator fees (USD) | attribute | NUMERIC | dol.column_metadata |
| 108 | `invst_mgmt_fees_amt` | `dol.schedule_h.invst_mgmt_fees_amt` | numeric | Y | Investment management fees (USD) | attribute | NUMERIC | dol.column_metadata |
| 109 | `other_admin_fees_amt` | `dol.schedule_h.other_admin_fees_amt` | numeric | Y | Other administrative fees (USD) | attribute | NUMERIC | dol.column_metadata |
| 110 | `tot_admin_expenses_amt` | `dol.schedule_h.tot_admin_expenses_amt` | numeric | Y | Total administrative expenses (USD) | attribute | NUMERIC | dol.column_metadata |
| 111 | `tot_expenses_amt` | `dol.schedule_h.tot_expenses_amt` | numeric | Y | Total expenses (USD) | attribute | NUMERIC | dol.column_metadata |
| 112 | `net_income_amt` | `dol.schedule_h.net_income_amt` | numeric | Y | Net income/loss (USD) | attribute | NUMERIC | dol.column_metadata |
| 113 | `tot_transfers_to_amt` | `dol.schedule_h.tot_transfers_to_amt` | numeric | Y | Total transfers to other plans (USD) | attribute | NUMERIC | dol.column_metadata |
| 114 | `tot_transfers_from_amt` | `dol.schedule_h.tot_transfers_from_amt` | numeric | Y | Total transfers from other plans (USD) | attribute | NUMERIC | dol.column_metadata |
| 115 | `acctnt_opinion_type_cd` | `dol.schedule_h.acctnt_opinion_type_cd` | character varying(10) | Y | Accountant opinion type code (1=Unqualified, 2=Qualified, 3=Disclaimer, 4=Adverse) | attribute | STRING | dol.column_metadata |
| 116 | `acct_performed_ltd_audit_ind` | `dol.schedule_h.acct_performed_ltd_audit_ind` | character varying(10) | Y | Indicator — accountant performed a limited-scope audit | attribute | STRING | dol.column_metadata |
| 117 | `accountant_firm_name` | `dol.schedule_h.accountant_firm_name` | character varying(500) | Y | Name of the accounting firm | attribute | STRING | dol.column_metadata |
| 118 | `accountant_firm_ein` | `dol.schedule_h.accountant_firm_ein` | character varying(20) | Y | EIN of the accounting firm | identifier | STRING | dol.column_metadata |
| 119 | `acct_opin_not_on_file_ind` | `dol.schedule_h.acct_opin_not_on_file_ind` | character varying(10) | Y | Indicator — accountant opinion not on file | attribute | STRING | dol.column_metadata |
| 120 | `fail_transmit_contrib_ind` | `dol.schedule_h.fail_transmit_contrib_ind` | character varying(10) | Y | Indicator — employer failed to timely transmit participant contributions | attribute | STRING | dol.column_metadata |
| 121 | `fail_transmit_contrib_amt` | `dol.schedule_h.fail_transmit_contrib_amt` | numeric | Y | Amount of late-transmitted contributions (USD) | attribute | NUMERIC | dol.column_metadata |
| 122 | `loans_in_default_ind` | `dol.schedule_h.loans_in_default_ind` | character varying(10) | Y | Indicator — plan has loans in default or uncollectible | attribute | STRING | dol.column_metadata |
| 123 | `loans_in_default_amt` | `dol.schedule_h.loans_in_default_amt` | numeric | Y | Amount of loans in default (USD) | attribute | NUMERIC | dol.column_metadata |
| 124 | `leases_in_default_ind` | `dol.schedule_h.leases_in_default_ind` | character varying(10) | Y | Indicator — plan has leases in default or uncollectible | attribute | STRING | dol.column_metadata |
| 125 | `leases_in_default_amt` | `dol.schedule_h.leases_in_default_amt` | numeric | Y | Amount of leases in default (USD) | attribute | NUMERIC | dol.column_metadata |
| 126 | `party_in_int_not_rptd_ind` | `dol.schedule_h.party_in_int_not_rptd_ind` | character varying(10) | Y | Indicator — party-in-interest transactions not reported on Sch G | attribute | STRING | dol.column_metadata |
| 127 | `party_in_int_not_rptd_amt` | `dol.schedule_h.party_in_int_not_rptd_amt` | numeric | Y | Amount of unreported party-in-interest transactions (USD) | attribute | NUMERIC | dol.column_metadata |
| 128 | `plan_ins_fdlty_bond_ind` | `dol.schedule_h.plan_ins_fdlty_bond_ind` | character varying(10) | Y | Indicator — plan covered by fidelity bond | attribute | STRING | dol.column_metadata |
| 129 | `plan_ins_fdlty_bond_amt` | `dol.schedule_h.plan_ins_fdlty_bond_amt` | numeric | Y | Fidelity bond coverage amount (USD) | attribute | NUMERIC | dol.column_metadata |
| 130 | `loss_discv_dur_year_ind` | `dol.schedule_h.loss_discv_dur_year_ind` | character varying(10) | Y | Indicator — losses discovered during year from fraud/dishonesty | attribute | STRING | dol.column_metadata |
| 131 | `loss_discv_dur_year_amt` | `dol.schedule_h.loss_discv_dur_year_amt` | numeric | Y | Amount of losses discovered (USD) | attribute | NUMERIC | dol.column_metadata |
| 132 | `asset_undeterm_val_ind` | `dol.schedule_h.asset_undeterm_val_ind` | character varying(10) | Y | Indicator — plan assets include investments with undetermined value | attribute | STRING | dol.column_metadata |
| 133 | `asset_undeterm_val_amt` | `dol.schedule_h.asset_undeterm_val_amt` | numeric | Y | Amount of assets with undetermined value (USD) | attribute | NUMERIC | dol.column_metadata |
| 134 | `non_cash_contrib_ind` | `dol.schedule_h.non_cash_contrib_ind` | character varying(10) | Y | Indicator — plan received non-cash contributions | attribute | STRING | dol.column_metadata |
| 135 | `non_cash_contrib_amt` | `dol.schedule_h.non_cash_contrib_amt` | numeric | Y | Total non-cash contributions (USD) | attribute | NUMERIC | dol.column_metadata |
| 136 | `ast_held_invst_ind` | `dol.schedule_h.ast_held_invst_ind` | character varying(10) | Y | Indicator — plan held assets for investment | attribute | STRING | dol.column_metadata |
| 137 | `five_prcnt_trans_ind` | `dol.schedule_h.five_prcnt_trans_ind` | character varying(10) | Y | Indicator — single transaction exceeded 5% of plan assets | attribute | STRING | dol.column_metadata |
| 138 | `all_plan_ast_distrib_ind` | `dol.schedule_h.all_plan_ast_distrib_ind` | character varying(10) | Y | Indicator — all plan assets distributed to participants | attribute | STRING | dol.column_metadata |
| 139 | `fail_provide_benefit_due_ind` | `dol.schedule_h.fail_provide_benefit_due_ind` | character varying(10) | Y | Indicator — plan failed to provide benefits when due | attribute | STRING | dol.column_metadata |
| 140 | `fail_provide_benefit_due_amt` | `dol.schedule_h.fail_provide_benefit_due_amt` | numeric | Y | Amount of benefits not provided when due (USD) | attribute | NUMERIC | dol.column_metadata |
| 141 | `plan_blackout_period_ind` | `dol.schedule_h.plan_blackout_period_ind` | character varying(10) | Y | Indicator — plan had a blackout period | attribute | STRING | dol.column_metadata |
| 142 | `comply_blackout_notice_ind` | `dol.schedule_h.comply_blackout_notice_ind` | character varying(10) | Y | Indicator — plan complied with blackout notice requirements | attribute | STRING | dol.column_metadata |
| 143 | `res_term_plan_adpt_ind` | `dol.schedule_h.res_term_plan_adpt_ind` | character varying(10) | Y | Indicator — resolution to terminate plan adopted | attribute | STRING | dol.column_metadata |
| 144 | `res_term_plan_adpt_amt` | `dol.schedule_h.res_term_plan_adpt_amt` | numeric | Y | Amount of plan assets at time of termination resolution (USD) | attribute | NUMERIC | dol.column_metadata |
| 145 | `fdcry_trust_ein` | `dol.schedule_h.fdcry_trust_ein` | character varying(20) | Y | EIN of the fiduciary trust | identifier | STRING | dol.column_metadata |
| 146 | `fdcry_trust_name` | `dol.schedule_h.fdcry_trust_name` | character varying(500) | Y | Name of the fiduciary trust | attribute | STRING | dol.column_metadata |
| 147 | `covered_pbgc_insurance_ind` | `dol.schedule_h.covered_pbgc_insurance_ind` | character varying(10) | Y | Indicator — plan covered by PBGC insurance | attribute | STRING | dol.column_metadata |
| 148 | `trust_incur_unrel_tax_inc_ind` | `dol.schedule_h.trust_incur_unrel_tax_inc_ind` | character varying(10) | Y | Indicator — trust incurred unrelated business taxable income | attribute | STRING | dol.column_metadata |
| 149 | `trust_incur_unrel_tax_inc_amt` | `dol.schedule_h.trust_incur_unrel_tax_inc_amt` | numeric | Y | Amount of unrelated business taxable income (USD) | attribute | NUMERIC | dol.column_metadata |
| 150 | `in_service_distrib_ind` | `dol.schedule_h.in_service_distrib_ind` | character varying(10) | Y | Indicator — in-service distributions made | attribute | STRING | dol.column_metadata |
| 151 | `in_service_distrib_amt` | `dol.schedule_h.in_service_distrib_amt` | numeric | Y | Total in-service distributions (USD) | attribute | NUMERIC | dol.column_metadata |
| 152 | `fdcry_trustee_cust_name` | `dol.schedule_h.fdcry_trustee_cust_name` | character varying(500) | Y | Name of the fiduciary trustee/custodian | attribute | STRING | dol.column_metadata |
| 153 | `fdcry_trust_cust_phon_num` | `dol.schedule_h.fdcry_trust_cust_phon_num` | character varying(30) | Y | Trustee/custodian US phone number | attribute | STRING | dol.column_metadata |
| 154 | `fdcry_trust_cust_phon_nu_fore` | `dol.schedule_h.fdcry_trust_cust_phon_nu_fore` | character varying(30) | Y | Trustee/custodian foreign phone number | attribute | STRING | dol.column_metadata |
| 155 | `distrib_made_employee_62_ind` | `dol.schedule_h.distrib_made_employee_62_ind` | character varying(10) | Y | Indicator — distributions made to employees under age 62 who separated | attribute | STRING | dol.column_metadata |
| 156 | `premium_filing_confirm_number` | `dol.schedule_h.premium_filing_confirm_number` | character varying(50) | Y | PBGC premium filing confirmation number | attribute | STRING | dol.column_metadata |
| 157 | `acct_perf_ltd_audit_103_8_ind` | `dol.schedule_h.acct_perf_ltd_audit_103_8_ind` | character varying(10) | Y | Indicator — accountant performed limited-scope audit per DOL Reg 2520.103-8 | attribute | STRING | dol.column_metadata |
| 158 | `acct_perf_ltd_audit_103_12_ind` | `dol.schedule_h.acct_perf_ltd_audit_103_12_ind` | character varying(10) | Y | Indicator — accountant performed limited-scope audit per DOL Reg 2520.103-12(d) | attribute | STRING | dol.column_metadata |
| 159 | `acct_perf_not_ltd_audit_ind` | `dol.schedule_h.acct_perf_not_ltd_audit_ind` | character varying(10) | Y | Indicator — accountant performed full (non-limited-scope) audit | attribute | STRING | dol.column_metadata |
| 160 | `salaries_allowances_amt` | `dol.schedule_h.salaries_allowances_amt` | numeric | Y | Salaries and allowances — administrative expenses (USD) | attribute | NUMERIC | dol.column_metadata |
| 161 | `oth_recordkeeping_fees_amt` | `dol.schedule_h.oth_recordkeeping_fees_amt` | numeric | Y | Other recordkeeping fees (USD) | attribute | NUMERIC | dol.column_metadata |
| 162 | `iqpa_audit_fees_amt` | `dol.schedule_h.iqpa_audit_fees_amt` | numeric | Y | IQPA audit fees (USD) | attribute | NUMERIC | dol.column_metadata |
| 163 | `trustee_custodial_fees_amt` | `dol.schedule_h.trustee_custodial_fees_amt` | numeric | Y | Trustee/custodial fees (USD) | attribute | NUMERIC | dol.column_metadata |
| 164 | `actuarial_fees_amt` | `dol.schedule_h.actuarial_fees_amt` | numeric | Y | Actuarial fees (USD) | attribute | NUMERIC | dol.column_metadata |
| 165 | `legal_fees_amt` | `dol.schedule_h.legal_fees_amt` | numeric | Y | Legal fees (USD) | attribute | NUMERIC | dol.column_metadata |
| 166 | `valuation_appraisal_fees_amt` | `dol.schedule_h.valuation_appraisal_fees_amt` | numeric | Y | Valuation/appraisal fees (USD) | attribute | NUMERIC | dol.column_metadata |
| 167 | `other_trustee_fees_expenses_amt` | `dol.schedule_h.other_trustee_fees_expenses_amt` | numeric | Y | Other trustee fees and expenses (USD) | attribute | NUMERIC | dol.column_metadata |
| 168 | `form_year` | `dol.schedule_h.form_year` | character varying(10) | Y | Filing year (2023, 2024, 2025, etc.) — partition key for cross-year queries | attribute | STRING | dol.column_metadata |
| 169 | `created_at` | `dol.schedule_h.created_at` | timestamp with time zone | N | Timestamp when this row was loaded into the database | attribute | ISO-8601 | dol.column_metadata |

### `dol.schedule_h_part1` -- UNREGISTERED -- 20,359 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `dol.schedule_h_part1.id` | bigint | N | Auto-increment surrogate primary key | attribute | INTEGER | dol.column_metadata |
| 2 | `ack_id` | `dol.schedule_h_part1.ack_id` | character varying(50) | N | DOL acknowledgment ID — unique filing identifier. Foreign key to dol.form_5500.ack_id or dol.form_5500_sf.ack_id for joining across schedules | attribute | STRING | dol.column_metadata |
| 3 | `row_order` | `dol.schedule_h_part1.row_order` | integer | Y | Sequence number within a single filing — preserves original CSV row ordering when multiple line items exist per filing | attribute | INTEGER | dol.column_metadata |
| 4 | `plan_transfer_name` | `dol.schedule_h_part1.plan_transfer_name` | character varying(500) | Y | Name of the plan to which assets were transferred | attribute | STRING | dol.column_metadata |
| 5 | `plan_transfer_ein` | `dol.schedule_h_part1.plan_transfer_ein` | character varying(20) | Y | EIN of the receiving plan | identifier | STRING | dol.column_metadata |
| 6 | `plan_transfer_pn` | `dol.schedule_h_part1.plan_transfer_pn` | character varying(10) | Y | Plan number of the receiving plan | identifier | STRING | dol.column_metadata |
| 7 | `form_year` | `dol.schedule_h_part1.form_year` | character varying(10) | Y | Filing year (2023, 2024, 2025, etc.) — partition key for cross-year queries | attribute | STRING | dol.column_metadata |
| 8 | `created_at` | `dol.schedule_h_part1.created_at` | timestamp with time zone | N | Timestamp when this row was loaded into the database | attribute | ISO-8601 | dol.column_metadata |

### `dol.schedule_i` -- UNREGISTERED -- 116,493 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `dol.schedule_i.id` | bigint | N | Auto-increment surrogate primary key | attribute | INTEGER | dol.column_metadata |
| 2 | `ack_id` | `dol.schedule_i.ack_id` | character varying(50) | N | DOL acknowledgment ID — unique filing identifier. Foreign key to dol.form_5500.ack_id or dol.form_5500_sf.ack_id for joining across schedules | attribute | STRING | dol.column_metadata |
| 3 | `sch_i_plan_year_begin_date` | `dol.schedule_i.sch_i_plan_year_begin_date` | character varying(30) | Y | First day of the plan year (YYYY-MM-DD) | attribute | STRING | dol.column_metadata |
| 4 | `sch_i_tax_prd` | `dol.schedule_i.sch_i_tax_prd` | character varying(30) | Y | Tax period end date | attribute | STRING | dol.column_metadata |
| 5 | `sch_i_plan_num` | `dol.schedule_i.sch_i_plan_num` | character varying(10) | Y | Plan number | attribute | STRING | dol.column_metadata |
| 6 | `sch_i_ein` | `dol.schedule_i.sch_i_ein` | character varying(20) | Y | EIN of the plan sponsor | identifier | STRING | dol.column_metadata |
| 7 | `small_tot_assets_boy_amt` | `dol.schedule_i.small_tot_assets_boy_amt` | numeric | Y | Total assets — beginning of year (USD) | attribute | NUMERIC | dol.column_metadata |
| 8 | `small_tot_liabilities_boy_amt` | `dol.schedule_i.small_tot_liabilities_boy_amt` | numeric | Y | Total liabilities — beginning of year (USD) | attribute | NUMERIC | dol.column_metadata |
| 9 | `small_net_assets_boy_amt` | `dol.schedule_i.small_net_assets_boy_amt` | numeric | Y | Net assets — beginning of year (USD) | attribute | NUMERIC | dol.column_metadata |
| 10 | `small_tot_assets_eoy_amt` | `dol.schedule_i.small_tot_assets_eoy_amt` | numeric | Y | Total assets — end of year (USD) | attribute | NUMERIC | dol.column_metadata |
| 11 | `small_tot_liabilities_eoy_amt` | `dol.schedule_i.small_tot_liabilities_eoy_amt` | numeric | Y | Total liabilities — end of year (USD) | attribute | NUMERIC | dol.column_metadata |
| 12 | `small_net_assets_eoy_amt` | `dol.schedule_i.small_net_assets_eoy_amt` | numeric | Y | Net assets — end of year (USD) | attribute | NUMERIC | dol.column_metadata |
| 13 | `small_emplr_contrib_income_amt` | `dol.schedule_i.small_emplr_contrib_income_amt` | numeric | Y | Employer contributions received (USD) | attribute | NUMERIC | dol.column_metadata |
| 14 | `small_participant_contrib_amt` | `dol.schedule_i.small_participant_contrib_amt` | numeric | Y | Participant contributions received (USD) | attribute | NUMERIC | dol.column_metadata |
| 15 | `small_oth_contrib_rcvd_amt` | `dol.schedule_i.small_oth_contrib_rcvd_amt` | numeric | Y | Other contributions received (USD) | attribute | NUMERIC | dol.column_metadata |
| 16 | `small_non_cash_contrib_bs_amt` | `dol.schedule_i.small_non_cash_contrib_bs_amt` | numeric | Y | Non-cash contributions included in total (USD) | attribute | NUMERIC | dol.column_metadata |
| 17 | `small_other_income_amt` | `dol.schedule_i.small_other_income_amt` | numeric | Y | Other income (USD) | attribute | NUMERIC | dol.column_metadata |
| 18 | `small_tot_income_amt` | `dol.schedule_i.small_tot_income_amt` | numeric | Y | Total income (USD) | attribute | NUMERIC | dol.column_metadata |
| 19 | `small_tot_distrib_bnft_amt` | `dol.schedule_i.small_tot_distrib_bnft_amt` | numeric | Y | Total benefit distributions (USD) | attribute | NUMERIC | dol.column_metadata |
| 20 | `small_corrective_distrib_amt` | `dol.schedule_i.small_corrective_distrib_amt` | numeric | Y | Corrective distributions (USD) | attribute | NUMERIC | dol.column_metadata |
| 21 | `small_deem_dstrb_partcp_ln_amt` | `dol.schedule_i.small_deem_dstrb_partcp_ln_amt` | numeric | Y | Deemed distributions from participant loans (USD) | attribute | NUMERIC | dol.column_metadata |
| 22 | `small_admin_srvc_providers_amt` | `dol.schedule_i.small_admin_srvc_providers_amt` | numeric | Y | Payments to administrative service providers (USD) | attribute | NUMERIC | dol.column_metadata |
| 23 | `small_oth_expenses_amt` | `dol.schedule_i.small_oth_expenses_amt` | numeric | Y | Other expenses (USD) | attribute | NUMERIC | dol.column_metadata |
| 24 | `small_tot_expenses_amt` | `dol.schedule_i.small_tot_expenses_amt` | numeric | Y | Total expenses (USD) | attribute | NUMERIC | dol.column_metadata |
| 25 | `small_net_income_amt` | `dol.schedule_i.small_net_income_amt` | numeric | Y | Net income/loss (USD) | attribute | NUMERIC | dol.column_metadata |
| 26 | `small_tot_plan_transfers_amt` | `dol.schedule_i.small_tot_plan_transfers_amt` | numeric | Y | Total plan transfers (USD) | attribute | NUMERIC | dol.column_metadata |
| 27 | `small_joint_venture_eoy_ind` | `dol.schedule_i.small_joint_venture_eoy_ind` | character varying(10) | Y | Indicator — plan invested in joint ventures at EOY | attribute | STRING | dol.column_metadata |
| 28 | `small_joint_venture_eoy_amt` | `dol.schedule_i.small_joint_venture_eoy_amt` | numeric | Y | Joint venture investments at EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 29 | `small_emplr_prop_eoy_ind` | `dol.schedule_i.small_emplr_prop_eoy_ind` | character varying(10) | Y | Indicator — plan held employer real property at EOY | attribute | STRING | dol.column_metadata |
| 30 | `small_emplr_prop_eoy_amt` | `dol.schedule_i.small_emplr_prop_eoy_amt` | numeric | Y | Employer real property at EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 31 | `small_inv_real_estate_eoy_ind` | `dol.schedule_i.small_inv_real_estate_eoy_ind` | character varying(10) | Y | Indicator — plan invested in real estate at EOY | attribute | STRING | dol.column_metadata |
| 32 | `small_inv_real_estate_eoy_amt` | `dol.schedule_i.small_inv_real_estate_eoy_amt` | numeric | Y | Real estate investments at EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 33 | `small_emplr_sec_eoy_ind` | `dol.schedule_i.small_emplr_sec_eoy_ind` | character varying(10) | Y | Indicator — plan held employer securities at EOY | attribute | STRING | dol.column_metadata |
| 34 | `small_emplr_sec_eoy_amt` | `dol.schedule_i.small_emplr_sec_eoy_amt` | numeric | Y | Employer securities at EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 35 | `small_mortg_partcp_eoy_ind` | `dol.schedule_i.small_mortg_partcp_eoy_ind` | character varying(10) | Y | Indicator — plan held participant mortgages at EOY | attribute | STRING | dol.column_metadata |
| 36 | `small_mortg_partcp_eoy_amt` | `dol.schedule_i.small_mortg_partcp_eoy_amt` | numeric | Y | Participant mortgages at EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 37 | `small_oth_lns_partcp_eoy_ind` | `dol.schedule_i.small_oth_lns_partcp_eoy_ind` | character varying(10) | Y | Indicator — plan held other participant loans at EOY | attribute | STRING | dol.column_metadata |
| 38 | `small_oth_lns_partcp_eoy_amt` | `dol.schedule_i.small_oth_lns_partcp_eoy_amt` | numeric | Y | Other participant loans at EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 39 | `small_personal_prop_eoy_ind` | `dol.schedule_i.small_personal_prop_eoy_ind` | character varying(10) | Y | Indicator — plan held tangible personal property at EOY | attribute | STRING | dol.column_metadata |
| 40 | `small_personal_prop_eoy_amt` | `dol.schedule_i.small_personal_prop_eoy_amt` | numeric | Y | Tangible personal property at EOY (USD) | attribute | NUMERIC | dol.column_metadata |
| 41 | `small_fail_transm_contrib_ind` | `dol.schedule_i.small_fail_transm_contrib_ind` | character varying(10) | Y | Indicator — employer failed to timely transmit participant contributions | attribute | STRING | dol.column_metadata |
| 42 | `small_fail_transm_contrib_amt` | `dol.schedule_i.small_fail_transm_contrib_amt` | numeric | Y | Amount of late-transmitted contributions (USD) | attribute | NUMERIC | dol.column_metadata |
| 43 | `small_loans_in_default_ind` | `dol.schedule_i.small_loans_in_default_ind` | character varying(10) | Y | Indicator — plan has loans in default | attribute | STRING | dol.column_metadata |
| 44 | `small_loans_in_default_amt` | `dol.schedule_i.small_loans_in_default_amt` | numeric | Y | Amount of loans in default (USD) | attribute | NUMERIC | dol.column_metadata |
| 45 | `small_leases_in_default_ind` | `dol.schedule_i.small_leases_in_default_ind` | character varying(10) | Y | Indicator — plan has leases in default | attribute | STRING | dol.column_metadata |
| 46 | `small_leases_in_default_amt` | `dol.schedule_i.small_leases_in_default_amt` | numeric | Y | Amount of leases in default (USD) | attribute | NUMERIC | dol.column_metadata |
| 47 | `sm_party_in_int_not_rptd_ind` | `dol.schedule_i.sm_party_in_int_not_rptd_ind` | character varying(10) | Y | Indicator — party-in-interest transactions not reported | attribute | STRING | dol.column_metadata |
| 48 | `sm_party_in_int_not_rptd_amt` | `dol.schedule_i.sm_party_in_int_not_rptd_amt` | numeric | Y | Amount of unreported party-in-interest transactions (USD) | attribute | NUMERIC | dol.column_metadata |
| 49 | `small_plan_ins_fdlty_bond_ind` | `dol.schedule_i.small_plan_ins_fdlty_bond_ind` | character varying(10) | Y | Indicator — plan covered by fidelity bond | attribute | STRING | dol.column_metadata |
| 50 | `small_plan_ins_fdlty_bond_amt` | `dol.schedule_i.small_plan_ins_fdlty_bond_amt` | numeric | Y | Fidelity bond coverage amount (USD) | attribute | NUMERIC | dol.column_metadata |
| 51 | `small_loss_discv_dur_year_ind` | `dol.schedule_i.small_loss_discv_dur_year_ind` | character varying(10) | Y | Indicator — losses discovered from fraud/dishonesty | attribute | STRING | dol.column_metadata |
| 52 | `small_loss_discv_dur_year_amt` | `dol.schedule_i.small_loss_discv_dur_year_amt` | numeric | Y | Amount of losses discovered (USD) | attribute | NUMERIC | dol.column_metadata |
| 53 | `small_asset_undeterm_val_ind` | `dol.schedule_i.small_asset_undeterm_val_ind` | character varying(10) | Y | Indicator — assets with undetermined value | attribute | STRING | dol.column_metadata |
| 54 | `small_asset_undeterm_val_amt` | `dol.schedule_i.small_asset_undeterm_val_amt` | numeric | Y | Amount of assets with undetermined value (USD) | attribute | NUMERIC | dol.column_metadata |
| 55 | `small_non_cash_contrib_ind` | `dol.schedule_i.small_non_cash_contrib_ind` | character varying(10) | Y | Indicator — plan received non-cash contributions | attribute | STRING | dol.column_metadata |
| 56 | `small_non_cash_contrib_amt` | `dol.schedule_i.small_non_cash_contrib_amt` | numeric | Y | Total non-cash contributions (USD) | attribute | NUMERIC | dol.column_metadata |
| 57 | `small_20_prcnt_sngl_invst_ind` | `dol.schedule_i.small_20_prcnt_sngl_invst_ind` | character varying(10) | Y | Indicator — single investment exceeded 20% of plan assets | attribute | STRING | dol.column_metadata |
| 58 | `small_20_prcnt_sngl_invst_amt` | `dol.schedule_i.small_20_prcnt_sngl_invst_amt` | numeric | Y | Amount of single investment exceeding 20% (USD) | attribute | NUMERIC | dol.column_metadata |
| 59 | `small_all_plan_ast_distrib_ind` | `dol.schedule_i.small_all_plan_ast_distrib_ind` | character varying(10) | Y | Indicator — all plan assets distributed | attribute | STRING | dol.column_metadata |
| 60 | `sm_waiv_annual_iqpa_report_ind` | `dol.schedule_i.sm_waiv_annual_iqpa_report_ind` | character varying(10) | Y | Indicator — annual IQPA report waived | attribute | STRING | dol.column_metadata |
| 61 | `sm_fail_provide_benef_due_ind` | `dol.schedule_i.sm_fail_provide_benef_due_ind` | character varying(10) | Y | Indicator — failed to provide benefits when due | attribute | STRING | dol.column_metadata |
| 62 | `sm_fail_provide_benef_due_amt` | `dol.schedule_i.sm_fail_provide_benef_due_amt` | numeric | Y | Amount of benefits not provided when due (USD) | attribute | NUMERIC | dol.column_metadata |
| 63 | `small_plan_blackout_period_ind` | `dol.schedule_i.small_plan_blackout_period_ind` | character varying(10) | Y | Indicator — plan had a blackout period | attribute | STRING | dol.column_metadata |
| 64 | `sm_comply_blackout_notice_ind` | `dol.schedule_i.sm_comply_blackout_notice_ind` | character varying(10) | Y | Indicator — complied with blackout notice requirements | attribute | STRING | dol.column_metadata |
| 65 | `small_res_term_plan_adpt_ind` | `dol.schedule_i.small_res_term_plan_adpt_ind` | character varying(10) | Y | Indicator — resolution to terminate plan adopted | attribute | STRING | dol.column_metadata |
| 66 | `small_res_term_plan_adpt_amt` | `dol.schedule_i.small_res_term_plan_adpt_amt` | numeric | Y | Amount of plan assets at time of termination resolution (USD) | attribute | NUMERIC | dol.column_metadata |
| 67 | `fdcry_trust_ein` | `dol.schedule_i.fdcry_trust_ein` | character varying(20) | Y | EIN of the fiduciary trust | identifier | STRING | dol.column_metadata |
| 68 | `fdcry_trust_name` | `dol.schedule_i.fdcry_trust_name` | character varying(500) | Y | Name of the fiduciary trust | attribute | STRING | dol.column_metadata |
| 69 | `small_covered_pbgc_ins_ind` | `dol.schedule_i.small_covered_pbgc_ins_ind` | character varying(10) | Y | Indicator — plan covered by PBGC insurance | attribute | STRING | dol.column_metadata |
| 70 | `trust_incur_unrel_tax_inc_ind` | `dol.schedule_i.trust_incur_unrel_tax_inc_ind` | character varying(10) | Y | Indicator — trust incurred unrelated business taxable income | attribute | STRING | dol.column_metadata |
| 71 | `trust_incur_unrel_tax_inc_amt` | `dol.schedule_i.trust_incur_unrel_tax_inc_amt` | numeric | Y | Amount of unrelated business taxable income (USD) | attribute | NUMERIC | dol.column_metadata |
| 72 | `in_service_distrib_ind` | `dol.schedule_i.in_service_distrib_ind` | character varying(10) | Y | Indicator — in-service distributions made | attribute | STRING | dol.column_metadata |
| 73 | `in_service_distrib_amt` | `dol.schedule_i.in_service_distrib_amt` | numeric | Y | Total in-service distributions (USD) | attribute | NUMERIC | dol.column_metadata |
| 74 | `fdcry_trustee_cust_name` | `dol.schedule_i.fdcry_trustee_cust_name` | character varying(500) | Y | Name of the fiduciary trustee/custodian | attribute | STRING | dol.column_metadata |
| 75 | `fdcry_trust_cust_phone_num` | `dol.schedule_i.fdcry_trust_cust_phone_num` | character varying(30) | Y | Trustee/custodian US phone number | attribute | STRING | dol.column_metadata |
| 76 | `fdcry_trust_cust_phon_nu_fore` | `dol.schedule_i.fdcry_trust_cust_phon_nu_fore` | character varying(30) | Y | Trustee/custodian foreign phone number | attribute | STRING | dol.column_metadata |
| 77 | `distrib_made_employee_62_ind` | `dol.schedule_i.distrib_made_employee_62_ind` | character varying(10) | Y | Indicator — distributions made to employees under age 62 who separated | attribute | STRING | dol.column_metadata |
| 78 | `premium_filing_confirm_number` | `dol.schedule_i.premium_filing_confirm_number` | character varying(50) | Y | PBGC premium filing confirmation number | attribute | STRING | dol.column_metadata |
| 79 | `form_year` | `dol.schedule_i.form_year` | character varying(10) | Y | Filing year (2023, 2024, 2025, etc.) — partition key for cross-year queries | attribute | STRING | dol.column_metadata |
| 80 | `created_at` | `dol.schedule_i.created_at` | timestamp with time zone | N | Timestamp when this row was loaded into the database | attribute | ISO-8601 | dol.column_metadata |

### `dol.schedule_i_part1` -- UNREGISTERED -- 944 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `dol.schedule_i_part1.id` | bigint | N | Auto-increment surrogate primary key | attribute | INTEGER | dol.column_metadata |
| 2 | `ack_id` | `dol.schedule_i_part1.ack_id` | character varying(50) | N | DOL acknowledgment ID — unique filing identifier. Foreign key to dol.form_5500.ack_id or dol.form_5500_sf.ack_id for joining across schedules | attribute | STRING | dol.column_metadata |
| 3 | `row_order` | `dol.schedule_i_part1.row_order` | integer | Y | Sequence number within a single filing — preserves original CSV row ordering when multiple line items exist per filing | attribute | INTEGER | dol.column_metadata |
| 4 | `small_plan_transfer_name` | `dol.schedule_i_part1.small_plan_transfer_name` | character varying(500) | Y | Name of the plan to which assets were transferred | attribute | STRING | dol.column_metadata |
| 5 | `small_plan_transfer_ein` | `dol.schedule_i_part1.small_plan_transfer_ein` | character varying(20) | Y | EIN of the receiving plan | identifier | STRING | dol.column_metadata |
| 6 | `small_plan_transfer_pn` | `dol.schedule_i_part1.small_plan_transfer_pn` | character varying(10) | Y | Plan number of the receiving plan | identifier | STRING | dol.column_metadata |
| 7 | `form_year` | `dol.schedule_i_part1.form_year` | character varying(10) | Y | Filing year (2023, 2024, 2025, etc.) — partition key for cross-year queries | attribute | STRING | dol.column_metadata |
| 8 | `created_at` | `dol.schedule_i_part1.created_at` | timestamp with time zone | N | Timestamp when this row was loaded into the database | attribute | ISO-8601 | dol.column_metadata |

### `outreach.dol` -- CANONICAL FROZEN -- 147,031 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `dol_id` | `outreach.dol.dol_id` | uuid | N | Dol Id | identifier | UUID | inferred |
| 2 | `outreach_id` | `outreach.dol.outreach_id` | uuid | N | FK to outreach.outreach spine table | foreign_key | UUID | column_registry.yml |
| 3 | `ein` | `outreach.dol.ein` | text | Y | Employer Identification Number (9-digit, no dashes) | identifier | STRING | column_registry.yml |
| 4 | `filing_present` | `outreach.dol.filing_present` | boolean | Y | Whether a Form 5500 filing exists for this EIN | attribute | BOOLEAN | column_registry.yml |
| 5 | `funding_type` | `outreach.dol.funding_type` | text | Y | Benefit funding classification (pension_only, fully_insured, self_funded) | attribute | ENUM | column_registry.yml |
| 6 | `broker_or_advisor` | `outreach.dol.broker_or_advisor` | text | Y | Broker/advisor name from Schedule C code 28 | attribute | STRING | inferred |
| 7 | `carrier` | `outreach.dol.carrier` | text | Y | Insurance carrier name from Schedule A | attribute | STRING | inferred |
| 8 | `created_at` | `outreach.dol.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 9 | `updated_at` | `outreach.dol.updated_at` | timestamp with time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |
| 10 | `url_enrichment_data` | `outreach.dol.url_enrichment_data` | jsonb | Y | Url Enrichment Data | attribute | JSONB | inferred |
| 11 | `renewal_month` | `outreach.dol.renewal_month` | integer | Y | Plan year begin month (1-12) | metric | INTEGER | column_registry.yml |
| 12 | `outreach_start_month` | `outreach.dol.outreach_start_month` | integer | Y | 5 months before renewal month (1-12) — when to begin outreach | metric | INTEGER | column_registry.yml |

### `outreach.dol_archive` -- ARCHIVE -- 1,623 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `dol_id` | `outreach.dol_archive.dol_id` | uuid | N | Dol Id | identifier | UUID | inferred |
| 2 | `outreach_id` | `outreach.dol_archive.outreach_id` | uuid | N | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 3 | `ein` | `outreach.dol_archive.ein` | text | Y | Employer Identification Number (9-digit, no dashes) | attribute | STRING | inferred |
| 4 | `filing_present` | `outreach.dol_archive.filing_present` | boolean | Y | Whether a Form 5500 filing exists for this EIN | attribute | BOOLEAN | inferred |
| 5 | `funding_type` | `outreach.dol_archive.funding_type` | text | Y | Benefit funding classification (pension_only, fully_insured, self_funded) | attribute | ENUM | inferred |
| 6 | `broker_or_advisor` | `outreach.dol_archive.broker_or_advisor` | text | Y | Broker/advisor name from Schedule C code 28 | attribute | STRING | inferred |
| 7 | `carrier` | `outreach.dol_archive.carrier` | text | Y | Insurance carrier name from Schedule A | attribute | STRING | inferred |
| 8 | `created_at` | `outreach.dol_archive.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 9 | `updated_at` | `outreach.dol_archive.updated_at` | timestamp with time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |
| 10 | `archived_at` | `outreach.dol_archive.archived_at` | timestamp with time zone | Y | When this record was archived | attribute | ISO-8601 | inferred |
| 11 | `archive_reason` | `outreach.dol_archive.archive_reason` | text | Y | Reason this record was archived | attribute | STRING | inferred |

### `outreach.dol_audit_log` -- SYSTEM -- 0 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `log_id` | `outreach.dol_audit_log.log_id` | integer | N | Primary key for this log entry | identifier | INTEGER | inferred |
| 2 | `company_id` | `outreach.dol_audit_log.company_id` | text | N | Company Id | identifier | STRING | inferred |
| 3 | `state` | `outreach.dol_audit_log.state` | text | Y | US state code (2-letter) | attribute | ENUM | inferred |
| 4 | `attempted` | `outreach.dol_audit_log.attempted` | boolean | Y | Attempted | attribute | BOOLEAN | inferred |
| 5 | `outcome` | `outreach.dol_audit_log.outcome` | text | N | Outcome | attribute | STRING | inferred |
| 6 | `ein` | `outreach.dol_audit_log.ein` | text | Y | Employer Identification Number (9-digit, no dashes) | attribute | STRING | inferred |
| 7 | `fail_reason` | `outreach.dol_audit_log.fail_reason` | text | Y | Fail Reason | attribute | STRING | inferred |
| 8 | `run_id` | `outreach.dol_audit_log.run_id` | text | N | Run Id | identifier | STRING | inferred |
| 9 | `created_at` | `outreach.dol_audit_log.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

### `outreach.dol_errors` -- ERROR -- 28,572 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `error_id` | `outreach.dol_errors.error_id` | uuid | N | Primary key for error record | identifier | UUID | column_registry.yml |
| 2 | `outreach_id` | `outreach.dol_errors.outreach_id` | uuid | N | FK to spine (nullable — error may occur before entity exists) | foreign_key | UUID | column_registry.yml |
| 3 | `pipeline_stage` | `outreach.dol_errors.pipeline_stage` | character varying(100) | N | Pipeline Stage | attribute | STRING | inferred |
| 4 | `failure_code` | `outreach.dol_errors.failure_code` | character varying(50) | N | Failure Code | attribute | STRING | inferred |
| 5 | `blocking_reason` | `outreach.dol_errors.blocking_reason` | text | N | Blocking Reason | attribute | STRING | inferred |
| 6 | `severity` | `outreach.dol_errors.severity` | character varying(20) | N | Severity | attribute | STRING | inferred |
| 7 | `retry_allowed` | `outreach.dol_errors.retry_allowed` | boolean | N | Retry Allowed | attribute | BOOLEAN | inferred |
| 8 | `created_at` | `outreach.dol_errors.created_at` | timestamp with time zone | N | When the error was recorded | attribute | ISO-8601 | column_registry.yml |
| 9 | `resolved_at` | `outreach.dol_errors.resolved_at` | timestamp with time zone | Y | When this error/issue was resolved | attribute | ISO-8601 | inferred |
| 10 | `resolution_note` | `outreach.dol_errors.resolution_note` | text | Y | Resolution Note | attribute | STRING | inferred |
| 11 | `raw_input` | `outreach.dol_errors.raw_input` | jsonb | Y | Raw Input | attribute | JSONB | inferred |
| 12 | `stack_trace` | `outreach.dol_errors.stack_trace` | text | Y | Stack Trace | attribute | STRING | inferred |
| 13 | `requeue_attempts` | `outreach.dol_errors.requeue_attempts` | integer | Y | Requeue Attempts | attribute | INTEGER | inferred |
| 14 | `disposition` | `outreach.dol_errors.disposition` | USER-DEFINED | Y | Disposition | attribute | STRING | inferred |
| 15 | `retry_count` | `outreach.dol_errors.retry_count` | integer | Y | Number of retry attempts so far | metric | INTEGER | inferred |
| 16 | `max_retries` | `outreach.dol_errors.max_retries` | integer | Y | Max Retries | attribute | INTEGER | inferred |
| 17 | `archived_at` | `outreach.dol_errors.archived_at` | timestamp with time zone | Y | When this record was archived | attribute | ISO-8601 | inferred |
| 18 | `parked_at` | `outreach.dol_errors.parked_at` | timestamp with time zone | Y | Timestamp for parked event | attribute | ISO-8601 | inferred |
| 19 | `parked_by` | `outreach.dol_errors.parked_by` | text | Y | Parked By | attribute | STRING | inferred |
| 20 | `park_reason` | `outreach.dol_errors.park_reason` | text | Y | Park Reason | attribute | STRING | inferred |
| 21 | `escalation_level` | `outreach.dol_errors.escalation_level` | integer | Y | Escalation Level | attribute | INTEGER | inferred |
| 22 | `escalated_at` | `outreach.dol_errors.escalated_at` | timestamp with time zone | Y | Timestamp for escalated event | attribute | ISO-8601 | inferred |
| 23 | `ttl_tier` | `outreach.dol_errors.ttl_tier` | USER-DEFINED | Y | Ttl Tier | attribute | STRING | inferred |
| 24 | `last_retry_at` | `outreach.dol_errors.last_retry_at` | timestamp with time zone | Y | Timestamp for last retry event | attribute | ISO-8601 | inferred |
| 25 | `next_retry_at` | `outreach.dol_errors.next_retry_at` | timestamp with time zone | Y | Timestamp for next retry event | attribute | ISO-8601 | inferred |
| 26 | `retry_exhausted` | `outreach.dol_errors.retry_exhausted` | boolean | Y | Retry Exhausted | attribute | BOOLEAN | inferred |
| 27 | `error_type` | `outreach.dol_errors.error_type` | character varying(100) | N | Discriminator column — classifies the DOL error | attribute | ENUM | column_registry.yml |

### `outreach.dol_errors_archive` -- ARCHIVE -- 0 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `error_id` | `outreach.dol_errors_archive.error_id` | uuid | N | Primary key for this error record | identifier | UUID | inferred |
| 2 | `outreach_id` | `outreach.dol_errors_archive.outreach_id` | uuid | Y | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 3 | `pipeline_stage` | `outreach.dol_errors_archive.pipeline_stage` | character varying(50) | Y | Pipeline Stage | attribute | STRING | inferred |
| 4 | `failure_code` | `outreach.dol_errors_archive.failure_code` | character varying(50) | Y | Failure Code | attribute | STRING | inferred |
| 5 | `blocking_reason` | `outreach.dol_errors_archive.blocking_reason` | text | Y | Blocking Reason | attribute | STRING | inferred |
| 6 | `severity` | `outreach.dol_errors_archive.severity` | character varying(20) | Y | Severity | attribute | STRING | inferred |
| 7 | `retry_allowed` | `outreach.dol_errors_archive.retry_allowed` | boolean | Y | Retry Allowed | attribute | BOOLEAN | inferred |
| 8 | `raw_input` | `outreach.dol_errors_archive.raw_input` | jsonb | Y | Raw Input | attribute | JSONB | inferred |
| 9 | `stack_trace` | `outreach.dol_errors_archive.stack_trace` | text | Y | Stack Trace | attribute | STRING | inferred |
| 10 | `created_at` | `outreach.dol_errors_archive.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 11 | `resolved_at` | `outreach.dol_errors_archive.resolved_at` | timestamp with time zone | Y | When this error/issue was resolved | attribute | ISO-8601 | inferred |
| 12 | `resolution_note` | `outreach.dol_errors_archive.resolution_note` | text | Y | Resolution Note | attribute | STRING | inferred |
| 13 | `disposition` | `outreach.dol_errors_archive.disposition` | USER-DEFINED | Y | Disposition | attribute | STRING | inferred |
| 14 | `retry_count` | `outreach.dol_errors_archive.retry_count` | integer | Y | Number of retry attempts so far | metric | INTEGER | inferred |
| 15 | `max_retries` | `outreach.dol_errors_archive.max_retries` | integer | Y | Max Retries | attribute | INTEGER | inferred |
| 16 | `parked_at` | `outreach.dol_errors_archive.parked_at` | timestamp with time zone | Y | Timestamp for parked event | attribute | ISO-8601 | inferred |
| 17 | `parked_by` | `outreach.dol_errors_archive.parked_by` | text | Y | Parked By | attribute | STRING | inferred |
| 18 | `park_reason` | `outreach.dol_errors_archive.park_reason` | text | Y | Park Reason | attribute | STRING | inferred |
| 19 | `escalation_level` | `outreach.dol_errors_archive.escalation_level` | integer | Y | Escalation Level | attribute | INTEGER | inferred |
| 20 | `escalated_at` | `outreach.dol_errors_archive.escalated_at` | timestamp with time zone | Y | Timestamp for escalated event | attribute | ISO-8601 | inferred |
| 21 | `ttl_tier` | `outreach.dol_errors_archive.ttl_tier` | USER-DEFINED | Y | Ttl Tier | attribute | STRING | inferred |
| 22 | `last_retry_at` | `outreach.dol_errors_archive.last_retry_at` | timestamp with time zone | Y | Timestamp for last retry event | attribute | ISO-8601 | inferred |
| 23 | `retry_exhausted` | `outreach.dol_errors_archive.retry_exhausted` | boolean | Y | Retry Exhausted | attribute | BOOLEAN | inferred |
| 24 | `archived_at` | `outreach.dol_errors_archive.archived_at` | timestamp with time zone | N | When this record was archived | attribute | ISO-8601 | inferred |
| 25 | `archived_by` | `outreach.dol_errors_archive.archived_by` | text | Y | Archived By | attribute | STRING | inferred |
| 26 | `archive_reason` | `outreach.dol_errors_archive.archive_reason` | text | Y | Reason this record was archived | attribute | STRING | inferred |
| 27 | `final_disposition` | `outreach.dol_errors_archive.final_disposition` | USER-DEFINED | Y | Final Disposition | attribute | STRING | inferred |
| 28 | `retention_expires_at` | `outreach.dol_errors_archive.retention_expires_at` | timestamp with time zone | Y | Timestamp for retention expires event | attribute | ISO-8601 | inferred |
| 29 | `error_type` | `outreach.dol_errors_archive.error_type` | character varying(100) | Y | Discriminator column classifying the error type | attribute | ENUM | inferred |

### `outreach.dol_url_enrichment` -- STAGING -- 16 rows

**Hub**: `04.04.03` DOL Filings

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `outreach.dol_url_enrichment.id` | uuid | N | Id | identifier | UUID | inferred |
| 2 | `ein` | `outreach.dol_url_enrichment.ein` | character varying(9) | N | Employer Identification Number (9-digit, no dashes) | attribute | STRING | inferred |
| 3 | `legal_name` | `outreach.dol_url_enrichment.legal_name` | text | N | Legal Name | attribute | STRING | inferred |
| 4 | `dba_name` | `outreach.dol_url_enrichment.dba_name` | text | Y | Dba Name | attribute | STRING | inferred |
| 5 | `city` | `outreach.dol_url_enrichment.city` | text | Y | City name | attribute | STRING | inferred |
| 6 | `state` | `outreach.dol_url_enrichment.state` | character varying(2) | Y | US state code (2-letter) | attribute | ENUM | inferred |
| 7 | `zip` | `outreach.dol_url_enrichment.zip` | character varying(10) | Y | ZIP/postal code (5-digit) | attribute | STRING | inferred |
| 8 | `participants` | `outreach.dol_url_enrichment.participants` | integer | Y | Participants | attribute | INTEGER | inferred |
| 9 | `enriched_url` | `outreach.dol_url_enrichment.enriched_url` | text | Y | Enriched URL | attribute | URL | inferred |
| 10 | `search_query` | `outreach.dol_url_enrichment.search_query` | text | Y | Search Query | attribute | STRING | inferred |
| 11 | `confidence` | `outreach.dol_url_enrichment.confidence` | character varying(10) | Y | Confidence score (0-100) | attribute | STRING | inferred |
| 12 | `matched_company_unique_id` | `outreach.dol_url_enrichment.matched_company_unique_id` | text | Y | Matched Company Unique Id | identifier | STRING | inferred |
| 13 | `match_status` | `outreach.dol_url_enrichment.match_status` | character varying(20) | Y | Match Status | attribute | STRING | inferred |
| 14 | `created_at` | `outreach.dol_url_enrichment.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

---

## `04.04.04` BIT/CLS Authorization

**Tables**: 12 | **Total rows**: 14,408

### `bit.authorization_log` -- CANONICAL -- 0 rows

**Hub**: `04.04.04` BIT/CLS Authorization

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `log_id` | `bit.authorization_log.log_id` | uuid | N | Primary key for this log entry | identifier | UUID | inferred |
| 2 | `company_unique_id` | `bit.authorization_log.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 3 | `requested_action` | `bit.authorization_log.requested_action` | text | N | Requested Action | attribute | STRING | inferred |
| 4 | `requested_band` | `bit.authorization_log.requested_band` | integer | N | Requested Band | attribute | INTEGER | inferred |
| 5 | `authorized` | `bit.authorization_log.authorized` | boolean | N | Authorized | attribute | BOOLEAN | inferred |
| 6 | `actual_band` | `bit.authorization_log.actual_band` | integer | N | Actual Band | attribute | INTEGER | inferred |
| 7 | `denial_reason` | `bit.authorization_log.denial_reason` | text | Y | Denial Reason | attribute | STRING | inferred |
| 8 | `proof_id` | `bit.authorization_log.proof_id` | text | Y | Proof Id | identifier | STRING | inferred |
| 9 | `proof_valid` | `bit.authorization_log.proof_valid` | boolean | Y | Proof Valid | attribute | BOOLEAN | inferred |
| 10 | `requested_at` | `bit.authorization_log.requested_at` | timestamp with time zone | N | When this request was made | attribute | ISO-8601 | inferred |
| 11 | `requested_by` | `bit.authorization_log.requested_by` | text | N | Requested By | attribute | STRING | inferred |
| 12 | `correlation_id` | `bit.authorization_log.correlation_id` | text | Y | UUID linking related operations across tables | identifier | STRING | inferred |

### `bit.movement_events` -- MV -- 0 rows

**Hub**: `04.04.04` BIT/CLS Authorization

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `movement_id` | `bit.movement_events.movement_id` | uuid | N | Primary key for this movement event | identifier | UUID | inferred |
| 2 | `company_unique_id` | `bit.movement_events.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 3 | `source_hub` | `bit.movement_events.source_hub` | text | N | Source Hub | attribute | STRING | inferred |
| 4 | `source_table` | `bit.movement_events.source_table` | text | N | Source Table | attribute | STRING | inferred |
| 5 | `source_fields` | `bit.movement_events.source_fields` | ARRAY | N | Source Fields | attribute | ARRAY | inferred |
| 6 | `movement_class` | `bit.movement_events.movement_class` | text | N | Movement Class | attribute | STRING | inferred |
| 7 | `pressure_class` | `bit.movement_events.pressure_class` | text | N | Pressure Class | attribute | STRING | inferred |
| 8 | `domain` | `bit.movement_events.domain` | text | N | Company website domain (lowercase, no protocol) | attribute | STRING | inferred |
| 9 | `direction` | `bit.movement_events.direction` | text | N | Direction | attribute | STRING | inferred |
| 10 | `magnitude` | `bit.movement_events.magnitude` | numeric | N | Magnitude | attribute | NUMERIC | inferred |
| 11 | `detected_at` | `bit.movement_events.detected_at` | timestamp with time zone | N | When this event/signal was detected | attribute | ISO-8601 | inferred |
| 12 | `valid_from` | `bit.movement_events.valid_from` | timestamp with time zone | N | Valid From | attribute | ISO-8601 | inferred |
| 13 | `valid_until` | `bit.movement_events.valid_until` | timestamp with time zone | N | Valid Until | attribute | ISO-8601 | inferred |
| 14 | `comparison_period` | `bit.movement_events.comparison_period` | text | Y | Comparison Period | attribute | STRING | inferred |
| 15 | `evidence` | `bit.movement_events.evidence` | jsonb | N | Evidence | attribute | JSONB | inferred |
| 16 | `source_record_ids` | `bit.movement_events.source_record_ids` | jsonb | N | Source Record Ids | attribute | JSONB | inferred |
| 17 | `created_at` | `bit.movement_events.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |

### `bit.phase_state` -- CANONICAL -- 0 rows

**Hub**: `04.04.04` BIT/CLS Authorization

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `company_unique_id` | `bit.phase_state.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 2 | `current_band` | `bit.phase_state.current_band` | integer | N | Current Band | attribute | INTEGER | inferred |
| 3 | `phase_status` | `bit.phase_state.phase_status` | text | N | Phase Status | attribute | ENUM | inferred |
| 4 | `dol_active` | `bit.phase_state.dol_active` | boolean | N | Dol Active | attribute | BOOLEAN | inferred |
| 5 | `people_active` | `bit.phase_state.people_active` | boolean | N | People Active | attribute | BOOLEAN | inferred |
| 6 | `blog_active` | `bit.phase_state.blog_active` | boolean | N | Blog Active | attribute | BOOLEAN | inferred |
| 7 | `primary_pressure` | `bit.phase_state.primary_pressure` | text | Y | Primary Pressure | attribute | STRING | inferred |
| 8 | `aligned_domains` | `bit.phase_state.aligned_domains` | integer | N | Aligned Domains | attribute | INTEGER | inferred |
| 9 | `last_movement_at` | `bit.phase_state.last_movement_at` | timestamp with time zone | Y | Timestamp for last movement event | attribute | ISO-8601 | inferred |
| 10 | `last_band_change_at` | `bit.phase_state.last_band_change_at` | timestamp with time zone | Y | Timestamp for last band change event | attribute | ISO-8601 | inferred |
| 11 | `phase_entered_at` | `bit.phase_state.phase_entered_at` | timestamp with time zone | Y | Timestamp for phase entered event | attribute | ISO-8601 | inferred |
| 12 | `stasis_start` | `bit.phase_state.stasis_start` | timestamp with time zone | Y | Stasis Start | attribute | ISO-8601 | inferred |
| 13 | `stasis_years` | `bit.phase_state.stasis_years` | numeric | Y | Stasis Years | attribute | NUMERIC | inferred |
| 14 | `updated_at` | `bit.phase_state.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |

### `bit.proof_lines` -- CANONICAL -- 0 rows

**Hub**: `04.04.04` BIT/CLS Authorization

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `proof_id` | `bit.proof_lines.proof_id` | text | N | Proof Id | identifier | STRING | inferred |
| 2 | `company_unique_id` | `bit.proof_lines.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 3 | `band` | `bit.proof_lines.band` | integer | N | Band | attribute | INTEGER | inferred |
| 4 | `pressure_class` | `bit.proof_lines.pressure_class` | text | N | Pressure Class | attribute | STRING | inferred |
| 5 | `sources` | `bit.proof_lines.sources` | ARRAY | N | Sources | attribute | ARRAY | inferred |
| 6 | `evidence` | `bit.proof_lines.evidence` | jsonb | N | Evidence | attribute | JSONB | inferred |
| 7 | `movement_ids` | `bit.proof_lines.movement_ids` | ARRAY | N | Movement Ids | attribute | ARRAY | inferred |
| 8 | `human_readable` | `bit.proof_lines.human_readable` | text | N | Human Readable | attribute | STRING | inferred |
| 9 | `generated_at` | `bit.proof_lines.generated_at` | timestamp with time zone | N | Timestamp for generated event | attribute | ISO-8601 | inferred |
| 10 | `valid_until` | `bit.proof_lines.valid_until` | timestamp with time zone | N | Valid Until | attribute | ISO-8601 | inferred |
| 11 | `generated_by` | `bit.proof_lines.generated_by` | text | N | Generated By | attribute | STRING | inferred |

### `outreach.bit_errors` -- ERROR -- 0 rows

**Hub**: `04.04.04` BIT/CLS Authorization

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `error_id` | `outreach.bit_errors.error_id` | uuid | N | Primary key for error record | identifier | UUID | column_registry.yml |
| 2 | `outreach_id` | `outreach.bit_errors.outreach_id` | uuid | Y | FK to spine (nullable — error may occur before entity exists) | foreign_key | UUID | column_registry.yml |
| 3 | `pipeline_stage` | `outreach.bit_errors.pipeline_stage` | character varying(20) | N | Pipeline Stage | attribute | STRING | inferred |
| 4 | `failure_code` | `outreach.bit_errors.failure_code` | character varying(30) | N | Failure Code | attribute | STRING | inferred |
| 5 | `blocking_reason` | `outreach.bit_errors.blocking_reason` | text | N | Blocking Reason | attribute | STRING | inferred |
| 6 | `severity` | `outreach.bit_errors.severity` | character varying(10) | N | Severity | attribute | STRING | inferred |
| 7 | `retry_allowed` | `outreach.bit_errors.retry_allowed` | boolean | N | Retry Allowed | attribute | BOOLEAN | inferred |
| 8 | `correlation_id` | `outreach.bit_errors.correlation_id` | uuid | Y | UUID linking related operations across tables | identifier | UUID | inferred |
| 9 | `process_id` | `outreach.bit_errors.process_id` | uuid | Y | Process Id | identifier | UUID | inferred |
| 10 | `raw_input` | `outreach.bit_errors.raw_input` | jsonb | Y | Raw Input | attribute | JSONB | inferred |
| 11 | `stack_trace` | `outreach.bit_errors.stack_trace` | text | Y | Stack Trace | attribute | STRING | inferred |
| 12 | `created_at` | `outreach.bit_errors.created_at` | timestamp with time zone | N | When the error was recorded | attribute | ISO-8601 | column_registry.yml |
| 13 | `error_type` | `outreach.bit_errors.error_type` | character varying(100) | Y | Discriminator column — classifies the scoring error | attribute | ENUM | column_registry.yml |

### `outreach.bit_input_history` -- SYSTEM -- 0 rows

**Hub**: `04.04.04` BIT/CLS Authorization

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `history_id` | `outreach.bit_input_history.history_id` | uuid | N | History Id | identifier | UUID | inferred |
| 2 | `outreach_id` | `outreach.bit_input_history.outreach_id` | uuid | N | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 3 | `signal_type` | `outreach.bit_input_history.signal_type` | character varying(50) | N | Signal Type | attribute | STRING | inferred |
| 4 | `source` | `outreach.bit_input_history.source` | character varying(50) | N | Data source identifier | attribute | STRING | inferred |
| 5 | `signal_fingerprint` | `outreach.bit_input_history.signal_fingerprint` | text | N | Signal Fingerprint | attribute | STRING | inferred |
| 6 | `signal_payload` | `outreach.bit_input_history.signal_payload` | jsonb | Y | Signal Payload | attribute | JSONB | inferred |
| 7 | `first_seen_at` | `outreach.bit_input_history.first_seen_at` | timestamp with time zone | Y | Timestamp for first seen event | attribute | ISO-8601 | inferred |
| 8 | `last_used_at` | `outreach.bit_input_history.last_used_at` | timestamp with time zone | Y | Timestamp for last used event | attribute | ISO-8601 | inferred |
| 9 | `use_count` | `outreach.bit_input_history.use_count` | integer | Y | Count of use | metric | INTEGER | inferred |
| 10 | `score_contribution` | `outreach.bit_input_history.score_contribution` | integer | Y | Score Contribution | attribute | INTEGER | inferred |
| 11 | `correlation_id` | `outreach.bit_input_history.correlation_id` | uuid | Y | UUID linking related operations across tables | identifier | UUID | inferred |
| 12 | `process_id` | `outreach.bit_input_history.process_id` | uuid | Y | Process Id | identifier | UUID | inferred |
| 13 | `created_at` | `outreach.bit_input_history.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

### `outreach.bit_scores` -- CANONICAL FROZEN -- 12,602 rows

**Hub**: `04.04.04` BIT/CLS Authorization

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `outreach_id` | `outreach.bit_scores.outreach_id` | uuid | N | FK to outreach.outreach spine table | foreign_key | UUID | column_registry.yml |
| 2 | `score` | `outreach.bit_scores.score` | numeric | N | Score | attribute | NUMERIC | inferred |
| 3 | `score_tier` | `outreach.bit_scores.score_tier` | character varying(10) | N | Score Tier | attribute | STRING | inferred |
| 4 | `signal_count` | `outreach.bit_scores.signal_count` | integer | N | Count of signal | metric | INTEGER | inferred |
| 5 | `people_score` | `outreach.bit_scores.people_score` | numeric | N | People score | metric | NUMERIC | inferred |
| 6 | `dol_score` | `outreach.bit_scores.dol_score` | numeric | N | Dol score | metric | NUMERIC | inferred |
| 7 | `blog_score` | `outreach.bit_scores.blog_score` | numeric | N | Blog score | metric | NUMERIC | inferred |
| 8 | `talent_flow_score` | `outreach.bit_scores.talent_flow_score` | numeric | N | Talent Flow score | metric | NUMERIC | inferred |
| 9 | `last_signal_at` | `outreach.bit_scores.last_signal_at` | timestamp with time zone | Y | Timestamp for last signal event | attribute | ISO-8601 | inferred |
| 10 | `last_scored_at` | `outreach.bit_scores.last_scored_at` | timestamp with time zone | Y | Timestamp for last scored event | attribute | ISO-8601 | inferred |
| 11 | `created_at` | `outreach.bit_scores.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 12 | `updated_at` | `outreach.bit_scores.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |

### `outreach.bit_scores_archive` -- ARCHIVE -- 1,806 rows

**Hub**: `04.04.04` BIT/CLS Authorization

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `outreach_id` | `outreach.bit_scores_archive.outreach_id` | uuid | N | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 2 | `score` | `outreach.bit_scores_archive.score` | numeric | N | Score | attribute | NUMERIC | inferred |
| 3 | `score_tier` | `outreach.bit_scores_archive.score_tier` | character varying(10) | N | Score Tier | attribute | STRING | inferred |
| 4 | `signal_count` | `outreach.bit_scores_archive.signal_count` | integer | N | Count of signal | metric | INTEGER | inferred |
| 5 | `people_score` | `outreach.bit_scores_archive.people_score` | numeric | N | People score | metric | NUMERIC | inferred |
| 6 | `dol_score` | `outreach.bit_scores_archive.dol_score` | numeric | N | Dol score | metric | NUMERIC | inferred |
| 7 | `blog_score` | `outreach.bit_scores_archive.blog_score` | numeric | N | Blog score | metric | NUMERIC | inferred |
| 8 | `talent_flow_score` | `outreach.bit_scores_archive.talent_flow_score` | numeric | N | Talent Flow score | metric | NUMERIC | inferred |
| 9 | `last_signal_at` | `outreach.bit_scores_archive.last_signal_at` | timestamp with time zone | Y | Timestamp for last signal event | attribute | ISO-8601 | inferred |
| 10 | `last_scored_at` | `outreach.bit_scores_archive.last_scored_at` | timestamp with time zone | Y | Timestamp for last scored event | attribute | ISO-8601 | inferred |
| 11 | `created_at` | `outreach.bit_scores_archive.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 12 | `updated_at` | `outreach.bit_scores_archive.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |
| 13 | `archived_at` | `outreach.bit_scores_archive.archived_at` | timestamp with time zone | Y | When this record was archived | attribute | ISO-8601 | inferred |
| 14 | `archive_reason` | `outreach.bit_scores_archive.archive_reason` | text | Y | Reason this record was archived | attribute | STRING | inferred |

### `outreach.bit_signals` -- MV -- 0 rows

**Hub**: `04.04.04` BIT/CLS Authorization

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `signal_id` | `outreach.bit_signals.signal_id` | uuid | N | Signal Id | identifier | UUID | inferred |
| 2 | `outreach_id` | `outreach.bit_signals.outreach_id` | uuid | N | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 3 | `signal_type` | `outreach.bit_signals.signal_type` | character varying(50) | N | Signal Type | attribute | STRING | inferred |
| 4 | `signal_impact` | `outreach.bit_signals.signal_impact` | numeric | N | Signal Impact | attribute | NUMERIC | inferred |
| 5 | `source_spoke` | `outreach.bit_signals.source_spoke` | character varying(50) | N | Source Spoke | attribute | STRING | inferred |
| 6 | `correlation_id` | `outreach.bit_signals.correlation_id` | uuid | N | UUID linking related operations across tables | identifier | UUID | inferred |
| 7 | `process_id` | `outreach.bit_signals.process_id` | uuid | Y | Process Id | identifier | UUID | inferred |
| 8 | `signal_metadata` | `outreach.bit_signals.signal_metadata` | jsonb | Y | Signal Metadata | attribute | JSONB | inferred |
| 9 | `decay_period_days` | `outreach.bit_signals.decay_period_days` | integer | N | Decay Period Days | attribute | INTEGER | inferred |
| 10 | `decayed_impact` | `outreach.bit_signals.decayed_impact` | numeric | Y | Decayed Impact | attribute | NUMERIC | inferred |
| 11 | `signal_timestamp` | `outreach.bit_signals.signal_timestamp` | timestamp with time zone | N | Signal Timestamp | attribute | ISO-8601 | inferred |
| 12 | `processed_at` | `outreach.bit_signals.processed_at` | timestamp with time zone | Y | Timestamp for processed event | attribute | ISO-8601 | inferred |
| 13 | `created_at` | `outreach.bit_signals.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 14 | `signal_source` | `outreach.bit_signals.signal_source` | character varying(50) | Y | Signal Source | attribute | STRING | inferred |

### `outreach.campaigns` -- DEPRECATED -- 0 rows

**Hub**: `04.04.04` Outreach Execution (deprecated)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `campaign_id` | `outreach.campaigns.campaign_id` | uuid | N | Campaign Id | identifier | UUID | inferred |
| 2 | `campaign_name` | `outreach.campaigns.campaign_name` | character varying(255) | N | Campaign Name | attribute | STRING | inferred |
| 3 | `campaign_type` | `outreach.campaigns.campaign_type` | character varying(50) | N | Campaign Type | attribute | STRING | inferred |
| 4 | `campaign_status` | `outreach.campaigns.campaign_status` | character varying(50) | N | Campaign Status | attribute | STRING | inferred |
| 5 | `target_bit_score_min` | `outreach.campaigns.target_bit_score_min` | integer | Y | Target Bit Score Min | attribute | INTEGER | inferred |
| 6 | `target_outreach_state` | `outreach.campaigns.target_outreach_state` | character varying(50) | Y | Target Outreach State | attribute | STRING | inferred |
| 7 | `daily_send_limit` | `outreach.campaigns.daily_send_limit` | integer | Y | Daily Send Limit | attribute | INTEGER | inferred |
| 8 | `total_send_limit` | `outreach.campaigns.total_send_limit` | integer | Y | Total Send Limit | metric | INTEGER | inferred |
| 9 | `total_targeted` | `outreach.campaigns.total_targeted` | integer | N | Total Targeted | metric | INTEGER | inferred |
| 10 | `total_sent` | `outreach.campaigns.total_sent` | integer | N | Total Sent | metric | INTEGER | inferred |
| 11 | `total_opened` | `outreach.campaigns.total_opened` | integer | N | Total Opened | metric | INTEGER | inferred |
| 12 | `total_clicked` | `outreach.campaigns.total_clicked` | integer | N | Total Clicked | metric | INTEGER | inferred |
| 13 | `total_replied` | `outreach.campaigns.total_replied` | integer | N | Total Replied | metric | INTEGER | inferred |
| 14 | `start_date` | `outreach.campaigns.start_date` | date | Y | Start Date | attribute | DATE | inferred |
| 15 | `end_date` | `outreach.campaigns.end_date` | date | Y | End Date | attribute | DATE | inferred |
| 16 | `created_by` | `outreach.campaigns.created_by` | character varying(100) | Y | Created By | attribute | STRING | inferred |
| 17 | `created_at` | `outreach.campaigns.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 18 | `updated_at` | `outreach.campaigns.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |

### `outreach.send_log` -- DEPRECATED -- 0 rows

**Hub**: `04.04.04` Outreach Execution (deprecated)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `send_id` | `outreach.send_log.send_id` | uuid | N | Send Id | identifier | UUID | inferred |
| 2 | `campaign_id` | `outreach.send_log.campaign_id` | uuid | Y | Campaign Id | identifier | UUID | inferred |
| 3 | `sequence_id` | `outreach.send_log.sequence_id` | uuid | Y | Sequence Id | identifier | UUID | inferred |
| 4 | `person_id` | `outreach.send_log.person_id` | uuid | Y | Person Id | identifier | UUID | inferred |
| 5 | `target_id` | `outreach.send_log.target_id` | uuid | Y | Primary key for this target record | identifier | UUID | inferred |
| 6 | `company_unique_id` | `outreach.send_log.company_unique_id` | text | Y | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 7 | `email_to` | `outreach.send_log.email_to` | character varying(255) | N | Email To | attribute | EMAIL | inferred |
| 8 | `email_subject` | `outreach.send_log.email_subject` | text | Y | Email Subject | attribute | EMAIL | inferred |
| 9 | `sequence_step` | `outreach.send_log.sequence_step` | integer | N | Sequence Step | attribute | INTEGER | inferred |
| 10 | `send_status` | `outreach.send_log.send_status` | character varying(50) | N | Send Status | attribute | STRING | inferred |
| 11 | `scheduled_at` | `outreach.send_log.scheduled_at` | timestamp with time zone | Y | Timestamp for scheduled event | attribute | ISO-8601 | inferred |
| 12 | `sent_at` | `outreach.send_log.sent_at` | timestamp with time zone | Y | Timestamp for sent event | attribute | ISO-8601 | inferred |
| 13 | `delivered_at` | `outreach.send_log.delivered_at` | timestamp with time zone | Y | Timestamp for delivered event | attribute | ISO-8601 | inferred |
| 14 | `bounced_at` | `outreach.send_log.bounced_at` | timestamp with time zone | Y | Timestamp for bounced event | attribute | ISO-8601 | inferred |
| 15 | `opened_at` | `outreach.send_log.opened_at` | timestamp with time zone | Y | Timestamp for opened event | attribute | ISO-8601 | inferred |
| 16 | `clicked_at` | `outreach.send_log.clicked_at` | timestamp with time zone | Y | Timestamp for clicked event | attribute | ISO-8601 | inferred |
| 17 | `replied_at` | `outreach.send_log.replied_at` | timestamp with time zone | Y | Timestamp for replied event | attribute | ISO-8601 | inferred |
| 18 | `open_count` | `outreach.send_log.open_count` | integer | N | Count of open | metric | INTEGER | inferred |
| 19 | `click_count` | `outreach.send_log.click_count` | integer | N | Count of click | metric | INTEGER | inferred |
| 20 | `error_message` | `outreach.send_log.error_message` | text | Y | Human-readable error description | attribute | STRING | inferred |
| 21 | `retry_count` | `outreach.send_log.retry_count` | integer | N | Number of retry attempts so far | metric | INTEGER | inferred |
| 22 | `source_system` | `outreach.send_log.source_system` | character varying(100) | Y | System that originated this record | attribute | STRING | inferred |
| 23 | `external_id` | `outreach.send_log.external_id` | character varying(255) | Y | External Id | identifier | STRING | inferred |
| 24 | `created_at` | `outreach.send_log.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 25 | `updated_at` | `outreach.send_log.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |

### `outreach.sequences` -- DEPRECATED -- 0 rows

**Hub**: `04.04.04` Outreach Execution (deprecated)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `sequence_id` | `outreach.sequences.sequence_id` | uuid | N | Sequence Id | identifier | UUID | inferred |
| 2 | `campaign_id` | `outreach.sequences.campaign_id` | uuid | Y | Campaign Id | identifier | UUID | inferred |
| 3 | `sequence_name` | `outreach.sequences.sequence_name` | character varying(255) | N | Sequence Name | attribute | STRING | inferred |
| 4 | `sequence_order` | `outreach.sequences.sequence_order` | integer | N | Sequence Order | attribute | INTEGER | inferred |
| 5 | `subject_template` | `outreach.sequences.subject_template` | text | Y | Subject Template | attribute | STRING | inferred |
| 6 | `body_template` | `outreach.sequences.body_template` | text | Y | Body Template | attribute | STRING | inferred |
| 7 | `template_type` | `outreach.sequences.template_type` | character varying(50) | Y | Template Type | attribute | STRING | inferred |
| 8 | `delay_days` | `outreach.sequences.delay_days` | integer | N | Delay Days | attribute | INTEGER | inferred |
| 9 | `delay_hours` | `outreach.sequences.delay_hours` | integer | N | Delay Hours | attribute | INTEGER | inferred |
| 10 | `send_time_preference` | `outreach.sequences.send_time_preference` | character varying(20) | Y | Send Time Preference | attribute | STRING | inferred |
| 11 | `sequence_status` | `outreach.sequences.sequence_status` | character varying(50) | N | Sequence Status | attribute | STRING | inferred |
| 12 | `created_at` | `outreach.sequences.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 13 | `updated_at` | `outreach.sequences.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |

---

## `04.04.05` Blog Content

**Tables**: 8 | **Total rows**: 272,917

### `blog.pressure_signals` -- MV -- 0 rows

**Hub**: `04.04.05` Blog Content

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `signal_id` | `blog.pressure_signals.signal_id` | uuid | N | Signal Id | identifier | UUID | inferred |
| 2 | `company_unique_id` | `blog.pressure_signals.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 3 | `signal_type` | `blog.pressure_signals.signal_type` | character varying(50) | N | Signal Type | attribute | STRING | inferred |
| 4 | `pressure_domain` | `blog.pressure_signals.pressure_domain` | USER-DEFINED | N | Pressure Domain | attribute | STRING | inferred |
| 5 | `pressure_class` | `blog.pressure_signals.pressure_class` | USER-DEFINED | Y | Pressure Class | attribute | STRING | inferred |
| 6 | `signal_value` | `blog.pressure_signals.signal_value` | jsonb | N | Signal Value | attribute | JSONB | inferred |
| 7 | `magnitude` | `blog.pressure_signals.magnitude` | integer | N | Magnitude | attribute | INTEGER | inferred |
| 8 | `detected_at` | `blog.pressure_signals.detected_at` | timestamp with time zone | N | When this event/signal was detected | attribute | ISO-8601 | inferred |
| 9 | `expires_at` | `blog.pressure_signals.expires_at` | timestamp with time zone | N | When this record expires | attribute | ISO-8601 | inferred |
| 10 | `correlation_id` | `blog.pressure_signals.correlation_id` | uuid | Y | UUID linking related operations across tables | identifier | UUID | inferred |
| 11 | `source_record_id` | `blog.pressure_signals.source_record_id` | text | Y | Source Record Id | identifier | STRING | inferred |
| 12 | `created_at` | `blog.pressure_signals.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |

### `outreach.blog` -- CANONICAL FROZEN -- 93,596 rows

**Hub**: `04.04.05` Blog Content

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `blog_id` | `outreach.blog.blog_id` | uuid | N | Primary key for this blog record | identifier | UUID | inferred |
| 2 | `outreach_id` | `outreach.blog.outreach_id` | uuid | N | FK to outreach.outreach spine table | foreign_key | UUID | column_registry.yml |
| 3 | `context_summary` | `outreach.blog.context_summary` | text | Y | Summary of blog/content context | attribute | STRING | inferred |
| 4 | `source_type` | `outreach.blog.source_type` | text | Y | Source Type | attribute | ENUM | inferred |
| 5 | `source_url` | `outreach.blog.source_url` | text | Y | URL of the content source | attribute | URL | inferred |
| 6 | `context_timestamp` | `outreach.blog.context_timestamp` | timestamp with time zone | Y | Context Timestamp | attribute | ISO-8601 | inferred |
| 7 | `created_at` | `outreach.blog.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 8 | `source_type_enum` | `outreach.blog.source_type_enum` | USER-DEFINED | Y | Source Type Enum | attribute | ENUM | inferred |
| 9 | `about_url` | `outreach.blog.about_url` | text | Y | Company About Us page URL | attribute | URL | inferred |
| 10 | `news_url` | `outreach.blog.news_url` | text | Y | Company news/press page URL | attribute | URL | inferred |
| 11 | `extraction_method` | `outreach.blog.extraction_method` | text | Y | Method used to extract content (sitemap, crawl, etc.) | attribute | STRING | inferred |
| 12 | `last_extracted_at` | `outreach.blog.last_extracted_at` | timestamp with time zone | Y | When data was last extracted/scraped | attribute | ISO-8601 | inferred |
| 13 | `updated_at` | `outreach.blog.updated_at` | timestamp with time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |

### `outreach.blog_archive` -- ARCHIVE -- 4,391 rows

**Hub**: `04.04.05` Blog Content

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `blog_id` | `outreach.blog_archive.blog_id` | uuid | N | Primary key for this blog record | identifier | UUID | inferred |
| 2 | `outreach_id` | `outreach.blog_archive.outreach_id` | uuid | N | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 3 | `context_summary` | `outreach.blog_archive.context_summary` | text | Y | Summary of blog/content context | attribute | STRING | inferred |
| 4 | `source_type` | `outreach.blog_archive.source_type` | text | Y | Source Type | attribute | ENUM | inferred |
| 5 | `source_url` | `outreach.blog_archive.source_url` | text | Y | URL of the content source | attribute | URL | inferred |
| 6 | `context_timestamp` | `outreach.blog_archive.context_timestamp` | timestamp with time zone | Y | Context Timestamp | attribute | ISO-8601 | inferred |
| 7 | `created_at` | `outreach.blog_archive.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 8 | `source_type_enum` | `outreach.blog_archive.source_type_enum` | USER-DEFINED | Y | Source Type Enum | attribute | ENUM | inferred |
| 9 | `archived_at` | `outreach.blog_archive.archived_at` | timestamp with time zone | Y | When this record was archived | attribute | ISO-8601 | inferred |
| 10 | `archive_reason` | `outreach.blog_archive.archive_reason` | text | Y | Reason this record was archived | attribute | STRING | inferred |

### `outreach.blog_errors` -- ERROR -- 41 rows

**Hub**: `04.04.05` Blog Content

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `error_id` | `outreach.blog_errors.error_id` | uuid | N | Primary key for error record | identifier | UUID | column_registry.yml |
| 2 | `outreach_id` | `outreach.blog_errors.outreach_id` | uuid | N | FK to spine (nullable — error may occur before entity exists) | foreign_key | UUID | column_registry.yml |
| 3 | `pipeline_stage` | `outreach.blog_errors.pipeline_stage` | character varying(100) | N | Pipeline Stage | attribute | STRING | inferred |
| 4 | `failure_code` | `outreach.blog_errors.failure_code` | character varying(50) | N | Failure Code | attribute | STRING | inferred |
| 5 | `blocking_reason` | `outreach.blog_errors.blocking_reason` | text | N | Blocking Reason | attribute | STRING | inferred |
| 6 | `severity` | `outreach.blog_errors.severity` | character varying(20) | N | Severity | attribute | STRING | inferred |
| 7 | `retry_allowed` | `outreach.blog_errors.retry_allowed` | boolean | N | Retry Allowed | attribute | BOOLEAN | inferred |
| 8 | `created_at` | `outreach.blog_errors.created_at` | timestamp with time zone | N | When the error was recorded | attribute | ISO-8601 | column_registry.yml |
| 9 | `resolved_at` | `outreach.blog_errors.resolved_at` | timestamp with time zone | Y | When this error/issue was resolved | attribute | ISO-8601 | inferred |
| 10 | `resolution_note` | `outreach.blog_errors.resolution_note` | text | Y | Resolution Note | attribute | STRING | inferred |
| 11 | `raw_input` | `outreach.blog_errors.raw_input` | jsonb | Y | Raw Input | attribute | JSONB | inferred |
| 12 | `stack_trace` | `outreach.blog_errors.stack_trace` | text | Y | Stack Trace | attribute | STRING | inferred |
| 13 | `process_id` | `outreach.blog_errors.process_id` | uuid | Y | Process Id | identifier | UUID | inferred |
| 14 | `requeue_attempts` | `outreach.blog_errors.requeue_attempts` | integer | Y | Requeue Attempts | attribute | INTEGER | inferred |
| 15 | `error_type` | `outreach.blog_errors.error_type` | character varying(100) | N | Discriminator column — classifies the blog error (e.g., BLOG_MISSING) | attribute | ENUM | column_registry.yml |

### `outreach.blog_ingress_control` -- REGISTRY -- 1 rows

**Hub**: `04.04.05` Blog Content

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `control_id` | `outreach.blog_ingress_control.control_id` | uuid | N | Control Id | identifier | UUID | inferred |
| 2 | `enabled` | `outreach.blog_ingress_control.enabled` | boolean | N | Enabled | attribute | BOOLEAN | inferred |
| 3 | `enabled_at` | `outreach.blog_ingress_control.enabled_at` | timestamp with time zone | Y | Timestamp for enabled event | attribute | ISO-8601 | inferred |
| 4 | `enabled_by` | `outreach.blog_ingress_control.enabled_by` | text | Y | Enabled By | attribute | STRING | inferred |
| 5 | `disabled_at` | `outreach.blog_ingress_control.disabled_at` | timestamp with time zone | Y | Timestamp for disabled event | attribute | ISO-8601 | inferred |
| 6 | `disabled_by` | `outreach.blog_ingress_control.disabled_by` | text | Y | Disabled By | attribute | STRING | inferred |
| 7 | `max_urls_per_hour` | `outreach.blog_ingress_control.max_urls_per_hour` | integer | Y | Max Urls Per Hour | attribute | INTEGER | inferred |
| 8 | `max_urls_per_company` | `outreach.blog_ingress_control.max_urls_per_company` | integer | Y | Max Urls Per Company | attribute | INTEGER | inferred |
| 9 | `url_ttl_days` | `outreach.blog_ingress_control.url_ttl_days` | integer | Y | Url Ttl Days | attribute | INTEGER | inferred |
| 10 | `content_ttl_days` | `outreach.blog_ingress_control.content_ttl_days` | integer | Y | Content Ttl Days | attribute | INTEGER | inferred |
| 11 | `notes` | `outreach.blog_ingress_control.notes` | text | Y | Human-readable notes | attribute | STRING | inferred |
| 12 | `singleton_key` | `outreach.blog_ingress_control.singleton_key` | integer | Y | Singleton Key | attribute | INTEGER | inferred |
| 13 | `created_at` | `outreach.blog_ingress_control.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 14 | `updated_at` | `outreach.blog_ingress_control.updated_at` | timestamp with time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |

### `outreach.blog_source_history` -- SYSTEM -- 0 rows

**Hub**: `04.04.05` Blog Content

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `history_id` | `outreach.blog_source_history.history_id` | uuid | N | History Id | identifier | UUID | inferred |
| 2 | `outreach_id` | `outreach.blog_source_history.outreach_id` | uuid | N | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 3 | `source_type` | `outreach.blog_source_history.source_type` | character varying(50) | N | Source Type | attribute | ENUM | inferred |
| 4 | `source_url` | `outreach.blog_source_history.source_url` | text | N | URL of the content source | attribute | URL | inferred |
| 5 | `first_seen_at` | `outreach.blog_source_history.first_seen_at` | timestamp with time zone | N | Timestamp for first seen event | attribute | ISO-8601 | inferred |
| 6 | `last_checked_at` | `outreach.blog_source_history.last_checked_at` | timestamp with time zone | Y | Timestamp for last checked event | attribute | ISO-8601 | inferred |
| 7 | `status` | `outreach.blog_source_history.status` | character varying(20) | Y | Current status of this record | attribute | ENUM | inferred |
| 8 | `http_status` | `outreach.blog_source_history.http_status` | integer | Y | Http Status | attribute | INTEGER | inferred |
| 9 | `redirect_url` | `outreach.blog_source_history.redirect_url` | text | Y | Redirect URL | attribute | URL | inferred |
| 10 | `checksum` | `outreach.blog_source_history.checksum` | text | Y | Checksum | attribute | STRING | inferred |
| 11 | `process_id` | `outreach.blog_source_history.process_id` | uuid | Y | Process Id | identifier | UUID | inferred |
| 12 | `correlation_id` | `outreach.blog_source_history.correlation_id` | uuid | Y | UUID linking related operations across tables | identifier | UUID | inferred |
| 13 | `created_at` | `outreach.blog_source_history.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

### `outreach.sitemap_discovery` -- UNREGISTERED -- 93,596 rows

**Hub**: `04.04.05` Blog Content

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `outreach_id` | `outreach.sitemap_discovery.outreach_id` | uuid | N | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 2 | `domain` | `outreach.sitemap_discovery.domain` | character varying | N | Company website domain (lowercase, no protocol) | attribute | STRING | inferred |
| 3 | `sitemap_url` | `outreach.sitemap_discovery.sitemap_url` | text | Y | Sitemap URL | attribute | URL | inferred |
| 4 | `sitemap_source` | `outreach.sitemap_discovery.sitemap_source` | character varying(10) | Y | Sitemap Source | attribute | STRING | inferred |
| 5 | `has_sitemap` | `outreach.sitemap_discovery.has_sitemap` | boolean | N | Whether this record sitemap | attribute | BOOLEAN | inferred |
| 6 | `discovered_at` | `outreach.sitemap_discovery.discovered_at` | timestamp with time zone | N | Timestamp for discovered event | attribute | ISO-8601 | inferred |
| 7 | `domain_reachable` | `outreach.sitemap_discovery.domain_reachable` | boolean | Y | Domain Reachable | attribute | BOOLEAN | inferred |
| 8 | `http_status` | `outreach.sitemap_discovery.http_status` | smallint | Y | Http Status | attribute | INTEGER | inferred |
| 9 | `reachable_checked_at` | `outreach.sitemap_discovery.reachable_checked_at` | timestamp with time zone | Y | Timestamp for reachable checked event | attribute | ISO-8601 | inferred |

### `outreach.source_urls` -- UNREGISTERED -- 81,292 rows

**Hub**: `04.04.05` Blog Content

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `outreach.source_urls.id` | bigint | N | Id | identifier | INTEGER | inferred |
| 2 | `outreach_id` | `outreach.source_urls.outreach_id` | uuid | N | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 3 | `source_type` | `outreach.source_urls.source_type` | text | N | Source Type | attribute | ENUM | inferred |
| 4 | `source_url` | `outreach.source_urls.source_url` | text | N | URL of the content source | attribute | URL | inferred |
| 5 | `discovered_from` | `outreach.source_urls.discovered_from` | text | Y | Discovered From | attribute | STRING | inferred |
| 6 | `discovered_at` | `outreach.source_urls.discovered_at` | timestamp with time zone | Y | Timestamp for discovered event | attribute | ISO-8601 | inferred |

---

## `04.04.06` Coverage

**Tables**: 2 | **Total rows**: 10

### `coverage.service_agent` -- CANONICAL -- 3 rows

**Hub**: `04.04.06` Coverage

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `service_agent_id` | `coverage.service_agent.service_agent_id` | uuid | N | FK to coverage.service_agent | foreign_key | UUID | inferred |
| 2 | `agent_name` | `coverage.service_agent.agent_name` | text | N | Service agent display name | attribute | STRING | inferred |
| 3 | `status` | `coverage.service_agent.status` | text | N | Current status of this record | attribute | ENUM | inferred |
| 4 | `created_at` | `coverage.service_agent.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 5 | `agent_number` | `coverage.service_agent.agent_number` | text | N | Service agent identifier (SA-NNN format) | attribute | STRING | inferred |
| 6 | `first_name` | `coverage.service_agent.first_name` | text | Y | Person first name | attribute | STRING | inferred |
| 7 | `last_name` | `coverage.service_agent.last_name` | text | Y | Person last name | attribute | STRING | inferred |

### `coverage.service_agent_coverage` -- CANONICAL -- 7 rows

**Hub**: `04.04.06` Coverage

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `coverage_id` | `coverage.service_agent_coverage.coverage_id` | uuid | N | FK to coverage.service_agent_coverage | foreign_key | UUID | inferred |
| 2 | `service_agent_id` | `coverage.service_agent_coverage.service_agent_id` | uuid | N | FK to coverage.service_agent | foreign_key | UUID | inferred |
| 3 | `anchor_zip` | `coverage.service_agent_coverage.anchor_zip` | text | N | Center ZIP code for this market radius | attribute | STRING | inferred |
| 4 | `radius_miles` | `coverage.service_agent_coverage.radius_miles` | numeric | N | Radius in miles from anchor ZIP | attribute | NUMERIC | inferred |
| 5 | `status` | `coverage.service_agent_coverage.status` | text | N | Current status of this record | attribute | ENUM | inferred |
| 6 | `created_by` | `coverage.service_agent_coverage.created_by` | text | N | Created By | attribute | STRING | inferred |
| 7 | `created_at` | `coverage.service_agent_coverage.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 8 | `retired_at` | `coverage.service_agent_coverage.retired_at` | timestamp with time zone | Y | Timestamp for retired event | attribute | ISO-8601 | inferred |
| 9 | `retired_by` | `coverage.service_agent_coverage.retired_by` | text | Y | Retired By | attribute | STRING | inferred |
| 10 | `notes` | `coverage.service_agent_coverage.notes` | text | Y | Human-readable notes | attribute | STRING | inferred |

---

## `LANE-A` Appointment Reactivation (isolated lane)

**Tables**: 2 | **Total rows**: 1,473

### `outreach.appointments` -- SUPPORTING -- 702 rows

**Hub**: `LANE-A` Appointment Reactivation

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `appointment_id` | `outreach.appointments.appointment_id` | uuid | N | Appointment Id | identifier | UUID | inferred |
| 2 | `outreach_id` | `outreach.appointments.outreach_id` | uuid | Y | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 3 | `domain` | `outreach.appointments.domain` | character varying(255) | Y | Company website domain (lowercase, no protocol) | attribute | STRING | inferred |
| 4 | `prospect_keycode_id` | `outreach.appointments.prospect_keycode_id` | bigint | Y | Prospect Keycode Id | identifier | INTEGER | inferred |
| 5 | `appt_number` | `outreach.appointments.appt_number` | character varying(50) | Y | Appt Number | attribute | STRING | inferred |
| 6 | `appt_date` | `outreach.appointments.appt_date` | date | Y | Appt Date | attribute | DATE | inferred |
| 7 | `contact_first_name` | `outreach.appointments.contact_first_name` | character varying(100) | Y | Contact First Name | attribute | STRING | inferred |
| 8 | `contact_last_name` | `outreach.appointments.contact_last_name` | character varying(100) | Y | Contact Last Name | attribute | STRING | inferred |
| 9 | `contact_title` | `outreach.appointments.contact_title` | character varying(200) | Y | Contact Title | attribute | STRING | inferred |
| 10 | `contact_email` | `outreach.appointments.contact_email` | character varying(255) | Y | Contact Email | attribute | EMAIL | inferred |
| 11 | `contact_phone` | `outreach.appointments.contact_phone` | character varying(20) | Y | Contact Phone | attribute | STRING | inferred |
| 12 | `company_name` | `outreach.appointments.company_name` | character varying(255) | N | Company legal or common name | attribute | STRING | inferred |
| 13 | `address_1` | `outreach.appointments.address_1` | character varying(255) | Y | Address 1 | attribute | STRING | inferred |
| 14 | `address_2` | `outreach.appointments.address_2` | character varying(255) | Y | Address 2 | attribute | STRING | inferred |
| 15 | `city` | `outreach.appointments.city` | character varying(100) | Y | City name | attribute | STRING | inferred |
| 16 | `state` | `outreach.appointments.state` | character varying(10) | Y | US state code (2-letter) | attribute | ENUM | inferred |
| 17 | `zip` | `outreach.appointments.zip` | character varying(20) | Y | ZIP/postal code (5-digit) | attribute | STRING | inferred |
| 18 | `county` | `outreach.appointments.county` | character varying(100) | Y | County | attribute | STRING | inferred |
| 19 | `notes` | `outreach.appointments.notes` | text | Y | Human-readable notes | attribute | STRING | inferred |
| 20 | `source_file` | `outreach.appointments.source_file` | character varying(255) | Y | Source File | attribute | STRING | inferred |
| 21 | `created_at` | `outreach.appointments.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 22 | `updated_at` | `outreach.appointments.updated_at` | timestamp with time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |

### `sales.appointments_already_had` -- UNREGISTERED -- 771 rows

**Hub**: `LANE-A` Appointment Reactivation

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `appointment_uid` | `sales.appointments_already_had.appointment_uid` | text | N | Appointment Uid | attribute | STRING | inferred |
| 2 | `company_id` | `sales.appointments_already_had.company_id` | uuid | Y | Company Id | identifier | UUID | inferred |
| 3 | `people_id` | `sales.appointments_already_had.people_id` | uuid | Y | People Id | identifier | UUID | inferred |
| 4 | `outreach_id` | `sales.appointments_already_had.outreach_id` | uuid | Y | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 5 | `meeting_date` | `sales.appointments_already_had.meeting_date` | date | N | Meeting Date | attribute | DATE | inferred |
| 6 | `meeting_type` | `sales.appointments_already_had.meeting_type` | USER-DEFINED | N | Meeting Type | attribute | STRING | inferred |
| 7 | `meeting_outcome` | `sales.appointments_already_had.meeting_outcome` | USER-DEFINED | N | Meeting Outcome | attribute | STRING | inferred |
| 8 | `stalled_reason` | `sales.appointments_already_had.stalled_reason` | text | Y | Stalled Reason | attribute | STRING | inferred |
| 9 | `source` | `sales.appointments_already_had.source` | USER-DEFINED | N | Data source identifier | attribute | STRING | inferred |
| 10 | `source_record_id` | `sales.appointments_already_had.source_record_id` | text | Y | Source Record Id | identifier | STRING | inferred |
| 11 | `metadata` | `sales.appointments_already_had.metadata` | jsonb | Y | Metadata | attribute | JSONB | inferred |
| 12 | `created_at` | `sales.appointments_already_had.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |

---

## `LANE-B` Fractional CFO Partners (isolated lane)

**Tables**: 2 | **Total rows**: 833

### `partners.fractional_cfo_master` -- UNREGISTERED -- 833 rows

**Hub**: `LANE-B` Fractional CFO Partners

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `fractional_cfo_id` | `partners.fractional_cfo_master.fractional_cfo_id` | uuid | N | Fractional Cfo Id | identifier | UUID | inferred |
| 2 | `firm_name` | `partners.fractional_cfo_master.firm_name` | text | N | Firm Name | attribute | STRING | inferred |
| 3 | `primary_contact_name` | `partners.fractional_cfo_master.primary_contact_name` | text | N | Primary Contact Name | attribute | STRING | inferred |
| 4 | `linkedin_url` | `partners.fractional_cfo_master.linkedin_url` | text | Y | LinkedIn profile URL | attribute | URL | inferred |
| 5 | `email` | `partners.fractional_cfo_master.email` | text | Y | Email address | attribute | EMAIL | inferred |
| 6 | `geography` | `partners.fractional_cfo_master.geography` | text | Y | Geography | attribute | STRING | inferred |
| 7 | `niche_focus` | `partners.fractional_cfo_master.niche_focus` | text | Y | Niche Focus | attribute | STRING | inferred |
| 8 | `source` | `partners.fractional_cfo_master.source` | text | N | Data source identifier | attribute | STRING | inferred |
| 9 | `source_detail` | `partners.fractional_cfo_master.source_detail` | text | Y | Source Detail | attribute | STRING | inferred |
| 10 | `status` | `partners.fractional_cfo_master.status` | USER-DEFINED | N | Current status of this record | attribute | ENUM | inferred |
| 11 | `metadata` | `partners.fractional_cfo_master.metadata` | jsonb | Y | Metadata | attribute | JSONB | inferred |
| 12 | `created_at` | `partners.fractional_cfo_master.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 13 | `updated_at` | `partners.fractional_cfo_master.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |

### `partners.partner_appointments` -- UNREGISTERED -- 0 rows

**Hub**: `LANE-B` Fractional CFO Partners

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `partner_appointment_uid` | `partners.partner_appointments.partner_appointment_uid` | text | N | Partner Appointment Uid | attribute | STRING | inferred |
| 2 | `fractional_cfo_id` | `partners.partner_appointments.fractional_cfo_id` | uuid | N | Fractional Cfo Id | identifier | UUID | inferred |
| 3 | `meeting_date` | `partners.partner_appointments.meeting_date` | date | N | Meeting Date | attribute | DATE | inferred |
| 4 | `meeting_type` | `partners.partner_appointments.meeting_type` | USER-DEFINED | N | Meeting Type | attribute | STRING | inferred |
| 5 | `outcome` | `partners.partner_appointments.outcome` | USER-DEFINED | N | Outcome | attribute | STRING | inferred |
| 6 | `notes` | `partners.partner_appointments.notes` | text | Y | Human-readable notes | attribute | STRING | inferred |
| 7 | `metadata` | `partners.partner_appointments.metadata` | jsonb | Y | Metadata | attribute | JSONB | inferred |
| 8 | `created_at` | `partners.partner_appointments.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |

---

## `SYS` System / Reference / Enrichment

**Tables**: 23 | **Total rows**: 1,182,515

### `catalog.columns` -- SYSTEM -- 725 rows

**Hub**: `SYS` Catalog (system)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `column_id` | `catalog.columns.column_id` | character varying(200) | N | Column Id | identifier | STRING | inferred |
| 2 | `table_id` | `catalog.columns.table_id` | character varying(100) | N | Table Id | identifier | STRING | inferred |
| 3 | `column_name` | `catalog.columns.column_name` | character varying(100) | N | Column Name | attribute | STRING | inferred |
| 4 | `ordinal_position` | `catalog.columns.ordinal_position` | integer | Y | Ordinal Position | attribute | INTEGER | inferred |
| 5 | `data_type` | `catalog.columns.data_type` | character varying(50) | N | Data Type | attribute | STRING | inferred |
| 6 | `max_length` | `catalog.columns.max_length` | integer | Y | Max Length | attribute | INTEGER | inferred |
| 7 | `is_nullable` | `catalog.columns.is_nullable` | boolean | Y | Whether this record nullable | attribute | BOOLEAN | inferred |
| 8 | `default_value` | `catalog.columns.default_value` | text | Y | Default Value | attribute | STRING | inferred |
| 9 | `description` | `catalog.columns.description` | text | N | Description | attribute | STRING | inferred |
| 10 | `business_name` | `catalog.columns.business_name` | character varying(100) | Y | Business Name | attribute | STRING | inferred |
| 11 | `business_definition` | `catalog.columns.business_definition` | text | Y | Business Definition | attribute | STRING | inferred |
| 12 | `format_pattern` | `catalog.columns.format_pattern` | character varying(100) | Y | Format Pattern | attribute | STRING | inferred |
| 13 | `format_example` | `catalog.columns.format_example` | character varying(200) | Y | Format Example | attribute | STRING | inferred |
| 14 | `valid_values` | `catalog.columns.valid_values` | ARRAY | Y | Valid Values | attribute | ARRAY | inferred |
| 15 | `validation_rule` | `catalog.columns.validation_rule` | text | Y | Validation Rule | attribute | STRING | inferred |
| 16 | `is_primary_key` | `catalog.columns.is_primary_key` | boolean | Y | Whether this record primary key | attribute | BOOLEAN | inferred |
| 17 | `is_foreign_key` | `catalog.columns.is_foreign_key` | boolean | Y | Whether this record foreign key | attribute | BOOLEAN | inferred |
| 18 | `references_column` | `catalog.columns.references_column` | character varying(200) | Y | References Column | attribute | STRING | inferred |
| 19 | `pii_classification` | `catalog.columns.pii_classification` | character varying(20) | Y | Pii Classification | attribute | STRING | inferred |
| 20 | `data_sensitivity` | `catalog.columns.data_sensitivity` | character varying(20) | Y | Data Sensitivity | attribute | STRING | inferred |
| 21 | `source_system` | `catalog.columns.source_system` | character varying(100) | Y | System that originated this record | attribute | STRING | inferred |
| 22 | `source_field` | `catalog.columns.source_field` | character varying(200) | Y | Source Field | attribute | STRING | inferred |
| 23 | `transformation_logic` | `catalog.columns.transformation_logic` | text | Y | Transformation Logic | attribute | STRING | inferred |
| 24 | `tags` | `catalog.columns.tags` | ARRAY | Y | Tags | attribute | ARRAY | inferred |
| 25 | `synonyms` | `catalog.columns.synonyms` | ARRAY | Y | Synonyms | attribute | ARRAY | inferred |
| 26 | `created_at` | `catalog.columns.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 27 | `updated_at` | `catalog.columns.updated_at` | timestamp without time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |

### `catalog.relationships` -- SYSTEM -- 0 rows

**Hub**: `SYS` Catalog (system)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `relationship_id` | `catalog.relationships.relationship_id` | integer | N | Relationship Id | identifier | INTEGER | inferred |
| 2 | `from_table_id` | `catalog.relationships.from_table_id` | character varying(100) | N | From Table Id | identifier | STRING | inferred |
| 3 | `from_column_id` | `catalog.relationships.from_column_id` | character varying(200) | N | From Column Id | identifier | STRING | inferred |
| 4 | `to_table_id` | `catalog.relationships.to_table_id` | character varying(100) | N | To Table Id | identifier | STRING | inferred |
| 5 | `to_column_id` | `catalog.relationships.to_column_id` | character varying(200) | N | To Column Id | identifier | STRING | inferred |
| 6 | `relationship_type` | `catalog.relationships.relationship_type` | character varying(20) | N | Relationship Type | attribute | STRING | inferred |
| 7 | `relationship_name` | `catalog.relationships.relationship_name` | character varying(100) | Y | Relationship Name | attribute | STRING | inferred |
| 8 | `description` | `catalog.relationships.description` | text | Y | Description | attribute | STRING | inferred |
| 9 | `is_enforced` | `catalog.relationships.is_enforced` | boolean | Y | Whether this record enforced | attribute | BOOLEAN | inferred |
| 10 | `created_at` | `catalog.relationships.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

### `catalog.schemas` -- SYSTEM -- 6 rows

**Hub**: `SYS` Catalog (system)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `schema_id` | `catalog.schemas.schema_id` | character varying(50) | N | Schema Id | identifier | STRING | inferred |
| 2 | `schema_name` | `catalog.schemas.schema_name` | character varying(50) | N | Schema Name | attribute | STRING | inferred |
| 3 | `schema_type` | `catalog.schemas.schema_type` | character varying(20) | N | Schema Type | attribute | STRING | inferred |
| 4 | `description` | `catalog.schemas.description` | text | N | Description | attribute | STRING | inferred |
| 5 | `parent_schema` | `catalog.schemas.parent_schema` | character varying(50) | Y | Parent Schema | attribute | STRING | inferred |
| 6 | `owner` | `catalog.schemas.owner` | character varying(100) | Y | Owner | attribute | STRING | inferred |
| 7 | `created_at` | `catalog.schemas.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 8 | `updated_at` | `catalog.schemas.updated_at` | timestamp without time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |

### `catalog.tables` -- SYSTEM -- 31 rows

**Hub**: `SYS` Catalog (system)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `table_id` | `catalog.tables.table_id` | character varying(100) | N | Table Id | identifier | STRING | inferred |
| 2 | `schema_id` | `catalog.tables.schema_id` | character varying(50) | N | Schema Id | identifier | STRING | inferred |
| 3 | `table_name` | `catalog.tables.table_name` | character varying(100) | N | Table Name | attribute | STRING | inferred |
| 4 | `table_type` | `catalog.tables.table_type` | character varying(20) | N | Table Type | attribute | STRING | inferred |
| 5 | `description` | `catalog.tables.description` | text | N | Description | attribute | STRING | inferred |
| 6 | `business_purpose` | `catalog.tables.business_purpose` | text | Y | Business Purpose | attribute | STRING | inferred |
| 7 | `primary_key` | `catalog.tables.primary_key` | character varying(100) | Y | Primary Key | attribute | STRING | inferred |
| 8 | `foreign_keys` | `catalog.tables.foreign_keys` | jsonb | Y | Foreign Keys | attribute | JSONB | inferred |
| 9 | `row_count_approx` | `catalog.tables.row_count_approx` | integer | Y | Row Count Approx | attribute | INTEGER | inferred |
| 10 | `data_source` | `catalog.tables.data_source` | character varying(100) | Y | Data Source | attribute | STRING | inferred |
| 11 | `refresh_frequency` | `catalog.tables.refresh_frequency` | character varying(50) | Y | Refresh Frequency | attribute | STRING | inferred |
| 12 | `owner` | `catalog.tables.owner` | character varying(100) | Y | Owner | attribute | STRING | inferred |
| 13 | `tags` | `catalog.tables.tags` | ARRAY | Y | Tags | attribute | ARRAY | inferred |
| 14 | `created_at` | `catalog.tables.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 15 | `updated_at` | `catalog.tables.updated_at` | timestamp without time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |

### `enrichment.column_registry` -- SYSTEM -- 53 rows

**Hub**: `SYS` Enrichment (system)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `enrichment.column_registry.id` | integer | N | Id | identifier | INTEGER | inferred |
| 2 | `table_name` | `enrichment.column_registry.table_name` | character varying(100) | N | Table Name | attribute | STRING | inferred |
| 3 | `column_name` | `enrichment.column_registry.column_name` | character varying(100) | N | Column Name | attribute | STRING | inferred |
| 4 | `column_id` | `enrichment.column_registry.column_id` | character varying(50) | N | Column Id | identifier | STRING | inferred |
| 5 | `data_type` | `enrichment.column_registry.data_type` | character varying(50) | N | Data Type | attribute | STRING | inferred |
| 6 | `format_pattern` | `enrichment.column_registry.format_pattern` | character varying(255) | Y | Format Pattern | attribute | STRING | inferred |
| 7 | `description` | `enrichment.column_registry.description` | text | N | Description | attribute | STRING | inferred |
| 8 | `example_value` | `enrichment.column_registry.example_value` | text | Y | Example Value | attribute | STRING | inferred |
| 9 | `is_required` | `enrichment.column_registry.is_required` | boolean | Y | Whether this record required | attribute | BOOLEAN | inferred |
| 10 | `is_pii` | `enrichment.column_registry.is_pii` | boolean | Y | Whether this record pii | attribute | BOOLEAN | inferred |
| 11 | `ai_usage_hint` | `enrichment.column_registry.ai_usage_hint` | text | Y | Ai Usage Hint | attribute | STRING | inferred |
| 12 | `created_at` | `enrichment.column_registry.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

### `enrichment.hunter_company` -- SYSTEM -- 88,554 rows

**Hub**: `SYS` Enrichment (system)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `HC_ID` | integer | N | Primary key, auto-generated sequential ID | identifier | auto-increment | enrichment.column_registry |
| 2 | `domain` | `HC_DOMAIN` | character varying(255) | N | Company website domain - primary identifier | attribute | lowercase, no protocol | enrichment.column_registry |
| 3 | `organization` | `HC_ORG_NAME` | character varying(500) | Y | Legal or common company name from Hunter | attribute | title case | enrichment.column_registry |
| 4 | `headcount` | `HC_HEADCOUNT_RAW` | character varying(50) | Y | Employee count range as string | attribute | range format: X-Y | enrichment.column_registry |
| 5 | `country` | `HC_COUNTRY` | character varying(10) | Y | Two-letter country code | attribute | ISO 3166-1 alpha-2 | enrichment.column_registry |
| 6 | `state` | `HC_STATE` | character varying(50) | Y | State/province/region | attribute | US state abbreviation or full name | enrichment.column_registry |
| 7 | `city` | `HC_CITY` | character varying(100) | Y | City name | attribute | title case | enrichment.column_registry |
| 8 | `postal_code` | `HC_POSTAL` | character varying(20) | Y | ZIP or postal code | attribute | varies by country | enrichment.column_registry |
| 9 | `street` | `HC_STREET` | character varying(255) | Y | Street address line | attribute | street address format | enrichment.column_registry |
| 10 | `email_pattern` | `HC_EMAIL_PATTERN` | character varying(100) | Y | Email pattern for generating addresses | attribute | {first}.{last} format | enrichment.column_registry |
| 11 | `company_type` | `HC_COMPANY_TYPE` | character varying(100) | Y | Company ownership type | attribute | Hunter classification | enrichment.column_registry |
| 12 | `industry` | `HC_INDUSTRY` | character varying(255) | Y | Industry classification from Hunter | attribute | Hunter industry taxonomy | enrichment.column_registry |
| 13 | `enriched_at` | `HC_ENRICHED_TS` | timestamp without time zone | Y | When Hunter data was fetched | attribute | ISO 8601 | enrichment.column_registry |
| 14 | `created_at` | `HC_CREATED_TS` | timestamp without time zone | Y | Record creation timestamp | attribute | ISO 8601 | enrichment.column_registry |
| 15 | `updated_at` | `HC_UPDATED_TS` | timestamp without time zone | Y | Last update timestamp | attribute | ISO 8601 | enrichment.column_registry |
| 16 | `company_embedding` | `HC_EMBEDDING` | USER-DEFINED | Y | Semantic embedding for similarity search | attribute | OpenAI ada-002 format | enrichment.column_registry |
| 17 | `industry_normalized` | `HC_INDUSTRY_NORM` | character varying(100) | Y | Cleaned/mapped industry category | attribute | standardized taxonomy | enrichment.column_registry |
| 18 | `headcount_min` | `HC_HEADCOUNT_MIN` | integer | Y | Minimum employee count from range | attribute | positive integer | enrichment.column_registry |
| 19 | `headcount_max` | `HC_HEADCOUNT_MAX` | integer | Y | Maximum employee count from range | attribute | positive integer | enrichment.column_registry |
| 20 | `location_full` | `HC_LOCATION_FULL` | text | Y | Full address string for display | attribute | concatenated address | enrichment.column_registry |
| 21 | `data_quality_score` | `HC_QUALITY` | numeric | Y | Composite data completeness score | metric | 0.00 to 1.00 | enrichment.column_registry |
| 22 | `tags` | `HC_TAGS` | ARRAY | Y | Custom classification tags | attribute | array of strings | enrichment.column_registry |
| 23 | `source` | `HC_SOURCE` | character varying(50) | Y | Data source system | attribute | source identifier | enrichment.column_registry |
| 24 | `company_unique_id` | `HC_CT_ID` | character varying(50) | Y | Link to company_target.company_unique_id | foreign_key | UUID format | enrichment.column_registry |
| 25 | `outreach_id` | `HC_OUTREACH_ID` | uuid | Y | Link to outreach.outreach.outreach_id | foreign_key | UUID format | enrichment.column_registry |
| 26 | `source_file` | `enrichment.hunter_company.source_file` | character varying(255) | Y | Source File | attribute | STRING | inferred |

### `enrichment.hunter_contact` -- SYSTEM -- 583,580 rows

**Hub**: `SYS` Enrichment (system)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `HCT_ID` | integer | N | Primary key, auto-generated sequential ID | identifier | auto-increment | enrichment.column_registry |
| 2 | `domain` | `HCT_DOMAIN` | character varying(255) | N | Company domain this contact belongs to | attribute | lowercase, no protocol | enrichment.column_registry |
| 3 | `email` | `HCT_EMAIL` | character varying(255) | Y | Verified email address from Hunter | attribute | valid email format | enrichment.column_registry |
| 4 | `first_name` | `HCT_FIRST_NAME` | character varying(100) | Y | Contact first name | attribute | title case | enrichment.column_registry |
| 5 | `last_name` | `HCT_LAST_NAME` | character varying(100) | Y | Contact last name | attribute | title case | enrichment.column_registry |
| 6 | `department` | `HCT_DEPT_RAW` | character varying(100) | Y | Department from Hunter | attribute | Hunter department taxonomy | enrichment.column_registry |
| 7 | `job_title` | `HCT_TITLE_RAW` | character varying(255) | Y | Job title from Hunter | attribute | free text | enrichment.column_registry |
| 8 | `position_raw` | `HCT_POSITION_RAW` | character varying(500) | Y | Full position description from source | attribute | free text | enrichment.column_registry |
| 9 | `linkedin_url` | `HCT_LINKEDIN` | character varying(500) | Y | LinkedIn profile URL | attribute | https://linkedin.com/in/... | enrichment.column_registry |
| 10 | `twitter_handle` | `HCT_TWITTER` | character varying(100) | Y | Twitter/X handle | attribute | @handle format | enrichment.column_registry |
| 11 | `phone_number` | `HCT_PHONE` | character varying(50) | Y | Phone number if available | attribute | E.164 or formatted | enrichment.column_registry |
| 12 | `confidence_score` | `HCT_CONFIDENCE` | integer | Y | Hunter email confidence score | metric | 0-100 | enrichment.column_registry |
| 13 | `email_type` | `HCT_EMAIL_TYPE` | character varying(20) | Y | Whether email is personal or generic | attribute | personal|generic | enrichment.column_registry |
| 14 | `num_sources` | `HCT_NUM_SOURCES` | integer | Y | Number of sources confirming this email | metric | positive integer | enrichment.column_registry |
| 15 | `created_at` | `HCT_CREATED_TS` | timestamp without time zone | Y | Record creation timestamp | attribute | ISO 8601 | enrichment.column_registry |
| 16 | `contact_embedding` | `HCT_EMBEDDING` | USER-DEFINED | Y | Semantic embedding for similarity search | attribute | OpenAI ada-002 format | enrichment.column_registry |
| 17 | `title_normalized` | `HCT_TITLE_NORM` | character varying(100) | Y | Normalized job title | attribute | standardized title | enrichment.column_registry |
| 18 | `seniority_level` | `HCT_SENIORITY` | character varying(50) | Y | Seniority classification | attribute | enum: C-Level/Owner|VP|Director|Manager|Senior|Junior|Individual Contributor | enrichment.column_registry |
| 19 | `department_normalized` | `HCT_DEPT_NORM` | character varying(50) | Y | Normalized department | attribute | standardized taxonomy | enrichment.column_registry |
| 20 | `is_decision_maker` | `HCT_IS_DM` | boolean | Y | Whether contact is a decision maker | attribute | true/false | enrichment.column_registry |
| 21 | `full_name` | `HCT_FULL_NAME` | character varying(200) | Y | Combined full name | attribute | First Last format | enrichment.column_registry |
| 22 | `email_verified` | `HCT_EMAIL_VERIFIED` | boolean | Y | Hunter verification status | attribute | true/false | enrichment.column_registry |
| 23 | `data_quality_score` | `HCT_QUALITY` | numeric | Y | Composite data completeness score | metric | 0.00 to 1.00 | enrichment.column_registry |
| 24 | `outreach_priority` | `HCT_PRIORITY` | integer | Y | Computed outreach priority | attribute | 1-5 (5=highest) | enrichment.column_registry |
| 25 | `tags` | `HCT_TAGS` | ARRAY | Y | Custom classification tags | attribute | array of strings | enrichment.column_registry |
| 26 | `source` | `HCT_SOURCE` | character varying(50) | Y | Data source system | attribute | source identifier | enrichment.column_registry |
| 27 | `company_unique_id` | `HCT_CT_ID` | character varying(50) | Y | Link to company_target.company_unique_id | foreign_key | UUID format | enrichment.column_registry |
| 28 | `outreach_id` | `HCT_OUTREACH_ID` | uuid | Y | Link to outreach.outreach.outreach_id | foreign_key | UUID format | enrichment.column_registry |
| 29 | `source_1` | `enrichment.hunter_contact.source_1` | text | Y | Source 1 | attribute | STRING | inferred |
| 30 | `source_2` | `enrichment.hunter_contact.source_2` | text | Y | Source 2 | attribute | STRING | inferred |
| 31 | `source_3` | `enrichment.hunter_contact.source_3` | text | Y | Source 3 | attribute | STRING | inferred |
| 32 | `source_4` | `enrichment.hunter_contact.source_4` | text | Y | Source 4 | attribute | STRING | inferred |
| 33 | `source_5` | `enrichment.hunter_contact.source_5` | text | Y | Source 5 | attribute | STRING | inferred |
| 34 | `source_6` | `enrichment.hunter_contact.source_6` | text | Y | Source 6 | attribute | STRING | inferred |
| 35 | `source_7` | `enrichment.hunter_contact.source_7` | text | Y | Source 7 | attribute | STRING | inferred |
| 36 | `source_8` | `enrichment.hunter_contact.source_8` | text | Y | Source 8 | attribute | STRING | inferred |
| 37 | `source_9` | `enrichment.hunter_contact.source_9` | text | Y | Source 9 | attribute | STRING | inferred |
| 38 | `source_10` | `enrichment.hunter_contact.source_10` | text | Y | Source 10 | attribute | STRING | inferred |
| 39 | `source_11` | `enrichment.hunter_contact.source_11` | text | Y | Source 11 | attribute | STRING | inferred |
| 40 | `source_12` | `enrichment.hunter_contact.source_12` | text | Y | Source 12 | attribute | STRING | inferred |
| 41 | `source_13` | `enrichment.hunter_contact.source_13` | text | Y | Source 13 | attribute | STRING | inferred |
| 42 | `source_14` | `enrichment.hunter_contact.source_14` | text | Y | Source 14 | attribute | STRING | inferred |
| 43 | `source_15` | `enrichment.hunter_contact.source_15` | text | Y | Source 15 | attribute | STRING | inferred |
| 44 | `source_16` | `enrichment.hunter_contact.source_16` | text | Y | Source 16 | attribute | STRING | inferred |
| 45 | `source_17` | `enrichment.hunter_contact.source_17` | text | Y | Source 17 | attribute | STRING | inferred |
| 46 | `source_18` | `enrichment.hunter_contact.source_18` | text | Y | Source 18 | attribute | STRING | inferred |
| 47 | `source_19` | `enrichment.hunter_contact.source_19` | text | Y | Source 19 | attribute | STRING | inferred |
| 48 | `source_20` | `enrichment.hunter_contact.source_20` | text | Y | Source 20 | attribute | STRING | inferred |
| 49 | `source_21` | `enrichment.hunter_contact.source_21` | text | Y | Source 21 | attribute | STRING | inferred |
| 50 | `source_22` | `enrichment.hunter_contact.source_22` | text | Y | Source 22 | attribute | STRING | inferred |
| 51 | `source_23` | `enrichment.hunter_contact.source_23` | text | Y | Source 23 | attribute | STRING | inferred |
| 52 | `source_24` | `enrichment.hunter_contact.source_24` | text | Y | Source 24 | attribute | STRING | inferred |
| 53 | `source_25` | `enrichment.hunter_contact.source_25` | text | Y | Source 25 | attribute | STRING | inferred |
| 54 | `source_26` | `enrichment.hunter_contact.source_26` | text | Y | Source 26 | attribute | STRING | inferred |
| 55 | `source_27` | `enrichment.hunter_contact.source_27` | text | Y | Source 27 | attribute | STRING | inferred |
| 56 | `source_28` | `enrichment.hunter_contact.source_28` | text | Y | Source 28 | attribute | STRING | inferred |
| 57 | `source_29` | `enrichment.hunter_contact.source_29` | text | Y | Source 29 | attribute | STRING | inferred |
| 58 | `source_30` | `enrichment.hunter_contact.source_30` | text | Y | Source 30 | attribute | STRING | inferred |
| 59 | `source_file` | `enrichment.hunter_contact.source_file` | character varying(255) | Y | Source File | attribute | STRING | inferred |

### `intake.company_raw_intake` -- STAGING -- 563 rows

**Hub**: `SYS` Intake & Staging (system)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `intake.company_raw_intake.id` | bigint | N | Id | identifier | INTEGER | inferred |
| 2 | `company` | `intake.company_raw_intake.company` | text | N | Company | attribute | STRING | inferred |
| 3 | `company_name_for_emails` | `intake.company_raw_intake.company_name_for_emails` | text | Y | Company Name For Emails | attribute | EMAIL | inferred |
| 4 | `num_employees` | `intake.company_raw_intake.num_employees` | integer | Y | Num Employees | metric | INTEGER | inferred |
| 5 | `industry` | `intake.company_raw_intake.industry` | text | Y | Industry | attribute | STRING | inferred |
| 6 | `website` | `intake.company_raw_intake.website` | text | Y | Website | attribute | STRING | inferred |
| 7 | `company_linkedin_url` | `intake.company_raw_intake.company_linkedin_url` | text | Y | Company Linkedin URL | attribute | URL | inferred |
| 8 | `facebook_url` | `intake.company_raw_intake.facebook_url` | text | Y | Facebook URL | attribute | URL | inferred |
| 9 | `twitter_url` | `intake.company_raw_intake.twitter_url` | text | Y | Twitter URL | attribute | URL | inferred |
| 10 | `company_street` | `intake.company_raw_intake.company_street` | text | Y | Company Street | attribute | STRING | inferred |
| 11 | `company_city` | `intake.company_raw_intake.company_city` | text | Y | Company City | attribute | STRING | inferred |
| 12 | `company_state` | `intake.company_raw_intake.company_state` | text | Y | Company State | attribute | STRING | inferred |
| 13 | `company_country` | `intake.company_raw_intake.company_country` | text | Y | Company Country | attribute | STRING | inferred |
| 14 | `company_postal_code` | `intake.company_raw_intake.company_postal_code` | text | Y | Company Postal Code | attribute | STRING | inferred |
| 15 | `company_address` | `intake.company_raw_intake.company_address` | text | Y | Address | attribute | STRING | inferred |
| 16 | `company_phone` | `intake.company_raw_intake.company_phone` | text | Y | Company Phone | attribute | STRING | inferred |
| 17 | `sic_codes` | `intake.company_raw_intake.sic_codes` | text | Y | Sic Codes | attribute | STRING | inferred |
| 18 | `founded_year` | `intake.company_raw_intake.founded_year` | integer | Y | Founded Year | attribute | INTEGER | inferred |
| 19 | `created_at` | `intake.company_raw_intake.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 20 | `state_abbrev` | `intake.company_raw_intake.state_abbrev` | text | Y | State Abbrev | attribute | STRING | inferred |
| 21 | `import_batch_id` | `intake.company_raw_intake.import_batch_id` | text | Y | Import Batch Id | identifier | STRING | inferred |
| 22 | `validated` | `intake.company_raw_intake.validated` | boolean | Y | Validated | attribute | BOOLEAN | inferred |
| 23 | `validation_notes` | `intake.company_raw_intake.validation_notes` | text | Y | Validation Notes | attribute | STRING | inferred |
| 24 | `validated_at` | `intake.company_raw_intake.validated_at` | timestamp with time zone | Y | Timestamp for validated event | attribute | ISO-8601 | inferred |
| 25 | `validated_by` | `intake.company_raw_intake.validated_by` | text | Y | Validated By | attribute | STRING | inferred |
| 26 | `enrichment_attempt` | `intake.company_raw_intake.enrichment_attempt` | integer | Y | Enrichment Attempt | attribute | INTEGER | inferred |
| 27 | `chronic_bad` | `intake.company_raw_intake.chronic_bad` | boolean | Y | Chronic Bad | attribute | BOOLEAN | inferred |
| 28 | `last_enriched_at` | `intake.company_raw_intake.last_enriched_at` | timestamp without time zone | Y | Timestamp for last enriched event | attribute | ISO-8601 | inferred |
| 29 | `enriched_by` | `intake.company_raw_intake.enriched_by` | character varying(255) | Y | Enriched By | attribute | STRING | inferred |
| 30 | `b2_file_path` | `intake.company_raw_intake.b2_file_path` | text | Y | B2 File Path | attribute | STRING | inferred |
| 31 | `b2_uploaded_at` | `intake.company_raw_intake.b2_uploaded_at` | timestamp without time zone | Y | Timestamp for b2 uploaded event | attribute | ISO-8601 | inferred |
| 32 | `apollo_id` | `intake.company_raw_intake.apollo_id` | character varying(255) | Y | Apollo Id | identifier | STRING | inferred |
| 33 | `last_hash` | `intake.company_raw_intake.last_hash` | character varying(64) | Y | Last Hash | attribute | STRING | inferred |
| 34 | `garage_bay` | `intake.company_raw_intake.garage_bay` | character varying(10) | Y | Garage Bay | attribute | STRING | inferred |
| 35 | `validation_reasons` | `intake.company_raw_intake.validation_reasons` | text | Y | Validation Reasons | attribute | STRING | inferred |

### `intake.company_raw_wv` -- STAGING -- 62,146 rows

**Hub**: `SYS` Intake & Staging (system)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `company_unique_id` | `intake.company_raw_wv.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 2 | `company_name` | `intake.company_raw_wv.company_name` | text | Y | Company legal or common name | attribute | STRING | inferred |
| 3 | `domain` | `intake.company_raw_wv.domain` | text | Y | Company website domain (lowercase, no protocol) | attribute | STRING | inferred |
| 4 | `website` | `intake.company_raw_wv.website` | text | Y | Website | attribute | STRING | inferred |
| 5 | `industry` | `intake.company_raw_wv.industry` | text | Y | Industry | attribute | STRING | inferred |
| 6 | `employee_count` | `intake.company_raw_wv.employee_count` | integer | Y | Count of employee | metric | INTEGER | inferred |
| 7 | `phone` | `intake.company_raw_wv.phone` | text | Y | Phone number (E.164 format preferred) | attribute | STRING | inferred |
| 8 | `address` | `intake.company_raw_wv.address` | text | Y | Mailing address | attribute | STRING | inferred |
| 9 | `city` | `intake.company_raw_wv.city` | text | Y | City name | attribute | STRING | inferred |
| 10 | `state` | `intake.company_raw_wv.state` | text | Y | US state code (2-letter) | attribute | ENUM | inferred |
| 11 | `zip` | `intake.company_raw_wv.zip` | text | Y | ZIP/postal code (5-digit) | attribute | STRING | inferred |
| 12 | `created_at` | `intake.company_raw_wv.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

### `intake.people_candidate` -- STAGING -- 0 rows

**Hub**: `SYS` Intake & Staging (system)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `candidate_id` | `intake.people_candidate.candidate_id` | uuid | N | Primary key for this candidate record | identifier | UUID | inferred |
| 2 | `outreach_id` | `intake.people_candidate.outreach_id` | uuid | N | FK to outreach.outreach spine table (universal join key) | foreign_key | UUID | inferred |
| 3 | `slot_type` | `intake.people_candidate.slot_type` | character varying(20) | N | Executive role type (CEO, CFO, HR, CTO, CMO, COO) | attribute | ENUM | inferred |
| 4 | `person_name` | `intake.people_candidate.person_name` | text | Y | Person Name | attribute | STRING | inferred |
| 5 | `person_title` | `intake.people_candidate.person_title` | text | Y | Person Title | attribute | STRING | inferred |
| 6 | `person_email` | `intake.people_candidate.person_email` | text | Y | Person Email | attribute | EMAIL | inferred |
| 7 | `linkedin_url` | `intake.people_candidate.linkedin_url` | text | Y | LinkedIn profile URL | attribute | URL | inferred |
| 8 | `confidence_score` | `intake.people_candidate.confidence_score` | numeric | Y | Confidence score (0-100) | metric | NUMERIC | inferred |
| 9 | `source` | `intake.people_candidate.source` | character varying(50) | N | Data source identifier | attribute | STRING | inferred |
| 10 | `status` | `intake.people_candidate.status` | character varying(20) | N | Current status of this record | attribute | ENUM | inferred |
| 11 | `rejection_reason` | `intake.people_candidate.rejection_reason` | text | Y | Rejection Reason | attribute | STRING | inferred |
| 12 | `created_at` | `intake.people_candidate.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 13 | `processed_at` | `intake.people_candidate.processed_at` | timestamp with time zone | Y | Timestamp for processed event | attribute | ISO-8601 | inferred |
| 14 | `expires_at` | `intake.people_candidate.expires_at` | timestamp with time zone | Y | When this record expires | attribute | ISO-8601 | inferred |

### `intake.people_raw_intake` -- STAGING -- 120,045 rows

**Hub**: `SYS` Intake & Staging (system)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `intake.people_raw_intake.id` | integer | N | Id | identifier | INTEGER | inferred |
| 2 | `first_name` | `intake.people_raw_intake.first_name` | character varying(255) | Y | Person first name | attribute | STRING | inferred |
| 3 | `last_name` | `intake.people_raw_intake.last_name` | character varying(255) | Y | Person last name | attribute | STRING | inferred |
| 4 | `full_name` | `intake.people_raw_intake.full_name` | character varying(500) | Y | Full Name | attribute | STRING | inferred |
| 5 | `email` | `intake.people_raw_intake.email` | character varying(500) | Y | Email address | attribute | EMAIL | inferred |
| 6 | `work_phone` | `intake.people_raw_intake.work_phone` | character varying(50) | Y | Work Phone | attribute | STRING | inferred |
| 7 | `personal_phone` | `intake.people_raw_intake.personal_phone` | character varying(50) | Y | Personal Phone | attribute | STRING | inferred |
| 8 | `title` | `intake.people_raw_intake.title` | character varying(500) | Y | Job title or position | attribute | STRING | inferred |
| 9 | `seniority` | `intake.people_raw_intake.seniority` | character varying(100) | Y | Seniority | attribute | STRING | inferred |
| 10 | `department` | `intake.people_raw_intake.department` | character varying(255) | Y | Department | attribute | STRING | inferred |
| 11 | `company_name` | `intake.people_raw_intake.company_name` | character varying(500) | Y | Company legal or common name | attribute | STRING | inferred |
| 12 | `company_unique_id` | `intake.people_raw_intake.company_unique_id` | character varying(100) | Y | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 13 | `linkedin_url` | `intake.people_raw_intake.linkedin_url` | text | Y | LinkedIn profile URL | attribute | URL | inferred |
| 14 | `twitter_url` | `intake.people_raw_intake.twitter_url` | text | Y | Twitter URL | attribute | URL | inferred |
| 15 | `facebook_url` | `intake.people_raw_intake.facebook_url` | text | Y | Facebook URL | attribute | URL | inferred |
| 16 | `bio` | `intake.people_raw_intake.bio` | text | Y | Bio | attribute | STRING | inferred |
| 17 | `skills` | `intake.people_raw_intake.skills` | ARRAY | Y | Skills | attribute | ARRAY | inferred |
| 18 | `education` | `intake.people_raw_intake.education` | text | Y | Education | attribute | STRING | inferred |
| 19 | `certifications` | `intake.people_raw_intake.certifications` | text | Y | Certifications | attribute | STRING | inferred |
| 20 | `city` | `intake.people_raw_intake.city` | character varying(255) | Y | City name | attribute | STRING | inferred |
| 21 | `state` | `intake.people_raw_intake.state` | character varying(100) | Y | US state code (2-letter) | attribute | ENUM | inferred |
| 22 | `state_abbrev` | `intake.people_raw_intake.state_abbrev` | character varying(2) | Y | State Abbrev | attribute | STRING | inferred |
| 23 | `country` | `intake.people_raw_intake.country` | character varying(100) | Y | Country name or code | attribute | STRING | inferred |
| 24 | `source_system` | `intake.people_raw_intake.source_system` | character varying(100) | Y | System that originated this record | attribute | STRING | inferred |
| 25 | `source_record_id` | `intake.people_raw_intake.source_record_id` | character varying(255) | Y | Source Record Id | identifier | STRING | inferred |
| 26 | `import_batch_id` | `intake.people_raw_intake.import_batch_id` | character varying(100) | Y | Import Batch Id | identifier | STRING | inferred |
| 27 | `validated` | `intake.people_raw_intake.validated` | boolean | Y | Validated | attribute | BOOLEAN | inferred |
| 28 | `validation_notes` | `intake.people_raw_intake.validation_notes` | text | Y | Validation Notes | attribute | STRING | inferred |
| 29 | `validated_at` | `intake.people_raw_intake.validated_at` | timestamp without time zone | Y | Timestamp for validated event | attribute | ISO-8601 | inferred |
| 30 | `validated_by` | `intake.people_raw_intake.validated_by` | character varying(255) | Y | Validated By | attribute | STRING | inferred |
| 31 | `enrichment_attempt` | `intake.people_raw_intake.enrichment_attempt` | integer | Y | Enrichment Attempt | attribute | INTEGER | inferred |
| 32 | `chronic_bad` | `intake.people_raw_intake.chronic_bad` | boolean | Y | Chronic Bad | attribute | BOOLEAN | inferred |
| 33 | `last_enriched_at` | `intake.people_raw_intake.last_enriched_at` | timestamp without time zone | Y | Timestamp for last enriched event | attribute | ISO-8601 | inferred |
| 34 | `enriched_by` | `intake.people_raw_intake.enriched_by` | character varying(255) | Y | Enriched By | attribute | STRING | inferred |
| 35 | `b2_file_path` | `intake.people_raw_intake.b2_file_path` | text | Y | B2 File Path | attribute | STRING | inferred |
| 36 | `b2_uploaded_at` | `intake.people_raw_intake.b2_uploaded_at` | timestamp without time zone | Y | Timestamp for b2 uploaded event | attribute | ISO-8601 | inferred |
| 37 | `created_at` | `intake.people_raw_intake.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 38 | `updated_at` | `intake.people_raw_intake.updated_at` | timestamp without time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |
| 39 | `slot_type` | `intake.people_raw_intake.slot_type` | character varying(10) | Y | Executive role type (CEO, CFO, HR, CTO, CMO, COO) | attribute | ENUM | inferred |
| 40 | `backfill_source` | `intake.people_raw_intake.backfill_source` | character varying(50) | Y | Backfill Source | attribute | STRING | inferred |

### `intake.people_raw_wv` -- STAGING -- 10 rows

**Hub**: `SYS` Intake & Staging (system)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `unique_id` | `intake.people_raw_wv.unique_id` | text | N | Primary identifier for this record (Barton ID format) | identifier | STRING | inferred |
| 2 | `full_name` | `intake.people_raw_wv.full_name` | text | Y | Full Name | attribute | STRING | inferred |
| 3 | `first_name` | `intake.people_raw_wv.first_name` | text | Y | Person first name | attribute | STRING | inferred |
| 4 | `last_name` | `intake.people_raw_wv.last_name` | text | Y | Person last name | attribute | STRING | inferred |
| 5 | `email` | `intake.people_raw_wv.email` | text | Y | Email address | attribute | EMAIL | inferred |
| 6 | `phone` | `intake.people_raw_wv.phone` | text | Y | Phone number (E.164 format preferred) | attribute | STRING | inferred |
| 7 | `title` | `intake.people_raw_wv.title` | text | Y | Job title or position | attribute | STRING | inferred |
| 8 | `company_name` | `intake.people_raw_wv.company_name` | text | Y | Company legal or common name | attribute | STRING | inferred |
| 9 | `company_unique_id` | `intake.people_raw_wv.company_unique_id` | text | Y | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 10 | `linkedin_url` | `intake.people_raw_wv.linkedin_url` | text | Y | LinkedIn profile URL | attribute | URL | inferred |
| 11 | `city` | `intake.people_raw_wv.city` | text | Y | City name | attribute | STRING | inferred |
| 12 | `state` | `intake.people_raw_wv.state` | text | Y | US state code (2-letter) | attribute | ENUM | inferred |
| 13 | `created_at` | `intake.people_raw_wv.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

### `intake.people_staging` -- STAGING -- 139,859 rows

**Hub**: `SYS` Intake & Staging (system)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `intake.people_staging.id` | integer | N | Id | identifier | INTEGER | inferred |
| 2 | `source_url_id` | `intake.people_staging.source_url_id` | uuid | Y | Source Url Id | identifier | UUID | inferred |
| 3 | `company_unique_id` | `intake.people_staging.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 4 | `raw_name` | `intake.people_staging.raw_name` | text | Y | Raw Name | attribute | STRING | inferred |
| 5 | `first_name` | `intake.people_staging.first_name` | character varying(100) | Y | Person first name | attribute | STRING | inferred |
| 6 | `last_name` | `intake.people_staging.last_name` | character varying(100) | Y | Person last name | attribute | STRING | inferred |
| 7 | `raw_title` | `intake.people_staging.raw_title` | text | Y | Raw Title | attribute | STRING | inferred |
| 8 | `normalized_title` | `intake.people_staging.normalized_title` | character varying(100) | Y | Normalized Title | attribute | STRING | inferred |
| 9 | `mapped_slot_type` | `intake.people_staging.mapped_slot_type` | character varying(20) | Y | Mapped Slot Type | attribute | STRING | inferred |
| 10 | `linkedin_url` | `intake.people_staging.linkedin_url` | character varying(500) | Y | LinkedIn profile URL | attribute | URL | inferred |
| 11 | `email` | `intake.people_staging.email` | character varying(255) | Y | Email address | attribute | EMAIL | inferred |
| 12 | `confidence_score` | `intake.people_staging.confidence_score` | numeric | Y | Confidence score (0-100) | metric | NUMERIC | inferred |
| 13 | `status` | `intake.people_staging.status` | character varying(20) | Y | Current status of this record | attribute | ENUM | inferred |
| 14 | `created_at` | `intake.people_staging.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 15 | `processed_at` | `intake.people_staging.processed_at` | timestamp without time zone | Y | Timestamp for processed event | attribute | ISO-8601 | inferred |

### `intake.quarantine` -- STAGING -- 2 rows

**Hub**: `SYS` Intake & Staging (system)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `intake.quarantine.id` | bigint | N | Id | identifier | INTEGER | inferred |
| 2 | `company_unique_id` | `intake.quarantine.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 3 | `company_name` | `intake.quarantine.company_name` | text | Y | Company legal or common name | attribute | STRING | inferred |
| 4 | `domain` | `intake.quarantine.domain` | text | Y | Company website domain (lowercase, no protocol) | attribute | STRING | inferred |
| 5 | `industry` | `intake.quarantine.industry` | text | Y | Industry | attribute | STRING | inferred |
| 6 | `employee_count` | `intake.quarantine.employee_count` | integer | Y | Count of employee | metric | INTEGER | inferred |
| 7 | `website` | `intake.quarantine.website` | text | Y | Website | attribute | STRING | inferred |
| 8 | `phone` | `intake.quarantine.phone` | text | Y | Phone number (E.164 format preferred) | attribute | STRING | inferred |
| 9 | `address` | `intake.quarantine.address` | text | Y | Mailing address | attribute | STRING | inferred |
| 10 | `city` | `intake.quarantine.city` | text | Y | City name | attribute | STRING | inferred |
| 11 | `state` | `intake.quarantine.state` | text | Y | US state code (2-letter) | attribute | ENUM | inferred |
| 12 | `zip` | `intake.quarantine.zip` | text | Y | ZIP/postal code (5-digit) | attribute | STRING | inferred |
| 13 | `validation_status` | `intake.quarantine.validation_status` | text | Y | Validation Status | attribute | STRING | inferred |
| 14 | `reason_code` | `intake.quarantine.reason_code` | text | N | Reason Code | attribute | STRING | inferred |
| 15 | `validation_errors` | `intake.quarantine.validation_errors` | jsonb | N | Validation Errors | attribute | JSONB | inferred |
| 16 | `validation_warnings` | `intake.quarantine.validation_warnings` | jsonb | Y | Validation Warnings | attribute | JSONB | inferred |
| 17 | `failed_at` | `intake.quarantine.failed_at` | timestamp without time zone | Y | Timestamp for failed event | attribute | ISO-8601 | inferred |
| 18 | `reviewed` | `intake.quarantine.reviewed` | boolean | Y | Reviewed | attribute | BOOLEAN | inferred |
| 19 | `batch_id` | `intake.quarantine.batch_id` | text | Y | Batch Id | identifier | STRING | inferred |
| 20 | `source_table` | `intake.quarantine.source_table` | text | Y | Source Table | attribute | STRING | inferred |
| 21 | `created_at` | `intake.quarantine.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 22 | `updated_at` | `intake.quarantine.updated_at` | timestamp without time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |
| 23 | `promoted_to` | `intake.quarantine.promoted_to` | text | Y | Promoted To | attribute | STRING | inferred |
| 24 | `promoted_at` | `intake.quarantine.promoted_at` | timestamp without time zone | Y | Timestamp for promoted event | attribute | ISO-8601 | inferred |
| 25 | `enrichment_data` | `intake.quarantine.enrichment_data` | jsonb | Y | Enrichment Data | attribute | JSONB | inferred |
| 26 | `linkedin_url` | `intake.quarantine.linkedin_url` | text | Y | LinkedIn profile URL | attribute | URL | inferred |
| 27 | `revenue` | `intake.quarantine.revenue` | numeric | Y | Revenue | attribute | NUMERIC | inferred |
| 28 | `location` | `intake.quarantine.location` | text | Y | Location | attribute | STRING | inferred |

### `outreach_ctx.context` -- SYSTEM -- 3 rows

**Hub**: `SYS` Outreach Context (system)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `outreach_context_id` | `outreach_ctx.context.outreach_context_id` | text | N | Outreach Context Id | identifier | STRING | inferred |
| 2 | `created_at` | `outreach_ctx.context.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 3 | `status` | `outreach_ctx.context.status` | text | N | Current status of this record | attribute | ENUM | inferred |
| 4 | `notes` | `outreach_ctx.context.notes` | text | Y | Human-readable notes | attribute | STRING | inferred |

### `outreach_ctx.spend_log` -- SYSTEM -- 0 rows

**Hub**: `SYS` Outreach Context (system)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `outreach_ctx.spend_log.id` | bigint | N | Id | identifier | INTEGER | inferred |
| 2 | `outreach_context_id` | `outreach_ctx.spend_log.outreach_context_id` | text | N | Outreach Context Id | identifier | STRING | inferred |
| 3 | `company_sov_id` | `outreach_ctx.spend_log.company_sov_id` | uuid | N | Company Sov Id | identifier | UUID | inferred |
| 4 | `tool_name` | `outreach_ctx.spend_log.tool_name` | text | N | Tool Name | attribute | STRING | inferred |
| 5 | `tier` | `outreach_ctx.spend_log.tier` | integer | N | Tier | attribute | INTEGER | inferred |
| 6 | `cost_credits` | `outreach_ctx.spend_log.cost_credits` | numeric | Y | Cost Credits | attribute | NUMERIC | inferred |
| 7 | `attempted_at` | `outreach_ctx.spend_log.attempted_at` | timestamp with time zone | N | Timestamp for attempted event | attribute | ISO-8601 | inferred |

### `outreach_ctx.tool_attempts` -- SYSTEM -- 0 rows

**Hub**: `SYS` Outreach Context (system)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `outreach_ctx.tool_attempts.id` | bigint | N | Id | identifier | INTEGER | inferred |
| 2 | `outreach_context_id` | `outreach_ctx.tool_attempts.outreach_context_id` | text | N | Outreach Context Id | identifier | STRING | inferred |
| 3 | `tool_name` | `outreach_ctx.tool_attempts.tool_name` | text | N | Tool Name | attribute | STRING | inferred |
| 4 | `tier` | `outreach_ctx.tool_attempts.tier` | integer | N | Tier | attribute | INTEGER | inferred |
| 5 | `attempted_at` | `outreach_ctx.tool_attempts.attempted_at` | timestamp with time zone | N | Timestamp for attempted event | attribute | ISO-8601 | inferred |

### `ref.county_fips` -- SYSTEM -- 3,222 rows

**Hub**: `SYS` Reference Data (system)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `county_fips` | `ref.county_fips.county_fips` | character(5) | N | County Fips | attribute | STRING | inferred |
| 2 | `state_fips` | `ref.county_fips.state_fips` | character(2) | N | State Fips | attribute | STRING | inferred |
| 3 | `county_code` | `ref.county_fips.county_code` | character(3) | N | County Code | attribute | STRING | inferred |
| 4 | `county_name` | `ref.county_fips.county_name` | text | N | County Name | attribute | STRING | inferred |
| 5 | `state_name` | `ref.county_fips.state_name` | text | N | State Name | attribute | STRING | inferred |
| 6 | `source` | `ref.county_fips.source` | text | Y | Data source identifier | attribute | STRING | inferred |
| 7 | `source_year` | `ref.county_fips.source_year` | integer | N | Source Year | attribute | INTEGER | inferred |
| 8 | `created_at` | `ref.county_fips.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

### `ref.zip_county_map` -- SYSTEM -- 46,641 rows

**Hub**: `SYS` Reference Data (system)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `zip` | `ref.zip_county_map.zip` | character(5) | N | ZIP/postal code (5-digit) | attribute | STRING | inferred |
| 2 | `county_fips` | `ref.zip_county_map.county_fips` | character(5) | N | County Fips | attribute | STRING | inferred |
| 3 | `is_primary` | `ref.zip_county_map.is_primary` | boolean | Y | Whether this record primary | attribute | BOOLEAN | inferred |
| 4 | `source` | `ref.zip_county_map.source` | text | Y | Data source identifier | attribute | STRING | inferred |
| 5 | `created_at` | `ref.zip_county_map.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

### `reference.us_zip_codes` -- REGISTRY -- 41,551 rows

**Hub**: `SYS` Reference Data (system)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `zip` | `reference.us_zip_codes.zip` | text | N | ZIP/postal code (5-digit) | attribute | STRING | inferred |
| 2 | `lat` | `reference.us_zip_codes.lat` | numeric | Y | Lat | attribute | NUMERIC | inferred |
| 3 | `lng` | `reference.us_zip_codes.lng` | numeric | Y | Lng | attribute | NUMERIC | inferred |
| 4 | `city` | `reference.us_zip_codes.city` | text | Y | City name | attribute | STRING | inferred |
| 5 | `state_id` | `reference.us_zip_codes.state_id` | text | Y | US state code (2-letter) | identifier | STRING | inferred |
| 6 | `state_name` | `reference.us_zip_codes.state_name` | text | Y | State Name | attribute | STRING | inferred |
| 7 | `zcta` | `reference.us_zip_codes.zcta` | boolean | Y | Zcta | attribute | BOOLEAN | inferred |
| 8 | `parent_zcta` | `reference.us_zip_codes.parent_zcta` | text | Y | Parent Zcta | attribute | STRING | inferred |
| 9 | `population` | `reference.us_zip_codes.population` | integer | Y | Population | attribute | INTEGER | inferred |
| 10 | `density` | `reference.us_zip_codes.density` | numeric | Y | Density | attribute | NUMERIC | inferred |
| 11 | `county_fips` | `reference.us_zip_codes.county_fips` | text | Y | County Fips | attribute | STRING | inferred |
| 12 | `county_name` | `reference.us_zip_codes.county_name` | text | Y | County Name | attribute | STRING | inferred |
| 13 | `county_weights` | `reference.us_zip_codes.county_weights` | jsonb | Y | County Weights | attribute | JSONB | inferred |
| 14 | `county_names_all` | `reference.us_zip_codes.county_names_all` | text | Y | County Names All | attribute | STRING | inferred |
| 15 | `county_fips_all` | `reference.us_zip_codes.county_fips_all` | text | Y | County Fips All | attribute | STRING | inferred |
| 16 | `imprecise` | `reference.us_zip_codes.imprecise` | boolean | Y | Imprecise | attribute | BOOLEAN | inferred |
| 17 | `military` | `reference.us_zip_codes.military` | boolean | Y | Military | attribute | BOOLEAN | inferred |
| 18 | `timezone` | `reference.us_zip_codes.timezone` | text | Y | Timezone | attribute | STRING | inferred |
| 19 | `age_median` | `reference.us_zip_codes.age_median` | numeric | Y | Age Median | attribute | NUMERIC | inferred |
| 20 | `male` | `reference.us_zip_codes.male` | numeric | Y | Male | attribute | NUMERIC | inferred |
| 21 | `female` | `reference.us_zip_codes.female` | numeric | Y | Female | attribute | NUMERIC | inferred |
| 22 | `married` | `reference.us_zip_codes.married` | numeric | Y | Married | attribute | NUMERIC | inferred |
| 23 | `family_size` | `reference.us_zip_codes.family_size` | numeric | Y | Family Size | attribute | NUMERIC | inferred |
| 24 | `income_household_median` | `reference.us_zip_codes.income_household_median` | integer | Y | Income Household Median | attribute | INTEGER | inferred |
| 25 | `income_household_six_figure` | `reference.us_zip_codes.income_household_six_figure` | numeric | Y | Income Household Six Figure | attribute | NUMERIC | inferred |
| 26 | `home_ownership` | `reference.us_zip_codes.home_ownership` | numeric | Y | Home Ownership | attribute | NUMERIC | inferred |
| 27 | `home_value` | `reference.us_zip_codes.home_value` | integer | Y | Home Value | attribute | INTEGER | inferred |
| 28 | `rent_median` | `reference.us_zip_codes.rent_median` | integer | Y | Rent Median | attribute | INTEGER | inferred |
| 29 | `education_college_or_above` | `reference.us_zip_codes.education_college_or_above` | numeric | Y | Education College Or Above | attribute | NUMERIC | inferred |
| 30 | `labor_force_participation` | `reference.us_zip_codes.labor_force_participation` | numeric | Y | Labor Force Participation | attribute | NUMERIC | inferred |
| 31 | `unemployment_rate` | `reference.us_zip_codes.unemployment_rate` | numeric | Y | Unemployment Rate | metric | NUMERIC | inferred |
| 32 | `race_white` | `reference.us_zip_codes.race_white` | numeric | Y | Race White | attribute | NUMERIC | inferred |
| 33 | `race_black` | `reference.us_zip_codes.race_black` | numeric | Y | Race Black | attribute | NUMERIC | inferred |
| 34 | `race_asian` | `reference.us_zip_codes.race_asian` | numeric | Y | Race Asian | attribute | NUMERIC | inferred |
| 35 | `race_native` | `reference.us_zip_codes.race_native` | numeric | Y | Race Native | attribute | NUMERIC | inferred |
| 36 | `race_pacific` | `reference.us_zip_codes.race_pacific` | numeric | Y | Race Pacific | attribute | NUMERIC | inferred |
| 37 | `race_other` | `reference.us_zip_codes.race_other` | numeric | Y | Race Other | attribute | NUMERIC | inferred |
| 38 | `race_multiple` | `reference.us_zip_codes.race_multiple` | numeric | Y | Race Multiple | attribute | NUMERIC | inferred |
| 39 | `created_at` | `reference.us_zip_codes.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

### `shq.audit_log` -- SYSTEM -- 1,609 rows

**Hub**: `SYS` System Health (system)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `shq.audit_log.id` | integer | N | Id | identifier | INTEGER | inferred |
| 2 | `event_type` | `shq.audit_log.event_type` | character varying(255) | N | Type of audit/system event | attribute | STRING | inferred |
| 3 | `event_source` | `shq.audit_log.event_source` | character varying(255) | N | System or process that generated this event | attribute | STRING | inferred |
| 4 | `details` | `shq.audit_log.details` | jsonb | Y | Event details (JSON) | attribute | JSONB | inferred |
| 5 | `created_at` | `shq.audit_log.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

### `shq.error_master` -- SYSTEM -- 93,915 rows

**Hub**: `SYS` System Health (system)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `error_id` | `shq.error_master.error_id` | uuid | N | Primary key for this error record | identifier | UUID | inferred |
| 2 | `process_id` | `shq.error_master.process_id` | character varying(50) | N | Process Id | identifier | STRING | inferred |
| 3 | `agent_id` | `shq.error_master.agent_id` | character varying(50) | N | Agent Id | identifier | STRING | inferred |
| 4 | `severity` | `shq.error_master.severity` | character varying(20) | N | Severity | attribute | STRING | inferred |
| 5 | `error_type` | `shq.error_master.error_type` | character varying(50) | N | Discriminator column classifying the error type | attribute | ENUM | inferred |
| 6 | `message` | `shq.error_master.message` | text | N | Message | attribute | STRING | inferred |
| 7 | `company_unique_id` | `shq.error_master.company_unique_id` | character varying(50) | Y | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 8 | `outreach_context_id` | `shq.error_master.outreach_context_id` | character varying(100) | Y | Outreach Context Id | identifier | STRING | inferred |
| 9 | `air_event_id` | `shq.error_master.air_event_id` | character varying(50) | Y | Air Event Id | identifier | STRING | inferred |
| 10 | `context` | `shq.error_master.context` | jsonb | Y | Context | attribute | JSONB | inferred |
| 11 | `created_at` | `shq.error_master.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 12 | `resolved_at` | `shq.error_master.resolved_at` | timestamp with time zone | Y | When this error/issue was resolved | attribute | ISO-8601 | inferred |
| 13 | `resolution_type` | `shq.error_master.resolution_type` | character varying(30) | Y | Resolution Type | attribute | STRING | inferred |
| 14 | `disposition` | `shq.error_master.disposition` | USER-DEFINED | Y | Disposition | attribute | STRING | inferred |
| 15 | `archived_at` | `shq.error_master.archived_at` | timestamp with time zone | Y | When this record was archived | attribute | ISO-8601 | inferred |
| 16 | `ttl_tier` | `shq.error_master.ttl_tier` | USER-DEFINED | Y | Ttl Tier | attribute | STRING | inferred |

### `shq.error_master_archive` -- SYSTEM -- 0 rows

**Hub**: `SYS` System Health (system)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `shq.error_master_archive.id` | integer | N | Id | identifier | INTEGER | inferred |
| 2 | `error_id` | `shq.error_master_archive.error_id` | uuid | N | Primary key for this error record | identifier | UUID | inferred |
| 3 | `process_id` | `shq.error_master_archive.process_id` | text | Y | Process Id | identifier | STRING | inferred |
| 4 | `agent_id` | `shq.error_master_archive.agent_id` | text | Y | Agent Id | identifier | STRING | inferred |
| 5 | `severity` | `shq.error_master_archive.severity` | text | Y | Severity | attribute | STRING | inferred |
| 6 | `error_type` | `shq.error_master_archive.error_type` | text | Y | Discriminator column classifying the error type | attribute | ENUM | inferred |
| 7 | `message` | `shq.error_master_archive.message` | text | Y | Message | attribute | STRING | inferred |
| 8 | `company_unique_id` | `shq.error_master_archive.company_unique_id` | text | Y | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 9 | `outreach_context_id` | `shq.error_master_archive.outreach_context_id` | text | Y | Outreach Context Id | identifier | STRING | inferred |
| 10 | `air_event_id` | `shq.error_master_archive.air_event_id` | text | Y | Air Event Id | identifier | STRING | inferred |
| 11 | `context` | `shq.error_master_archive.context` | jsonb | Y | Context | attribute | JSONB | inferred |
| 12 | `created_at` | `shq.error_master_archive.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 13 | `resolved_at` | `shq.error_master_archive.resolved_at` | timestamp with time zone | Y | When this error/issue was resolved | attribute | ISO-8601 | inferred |
| 14 | `resolution_type` | `shq.error_master_archive.resolution_type` | text | Y | Resolution Type | attribute | STRING | inferred |
| 15 | `disposition` | `shq.error_master_archive.disposition` | USER-DEFINED | Y | Disposition | attribute | STRING | inferred |
| 16 | `ttl_tier` | `shq.error_master_archive.ttl_tier` | USER-DEFINED | Y | Ttl Tier | attribute | STRING | inferred |
| 17 | `archived_at` | `shq.error_master_archive.archived_at` | timestamp with time zone | N | When this record was archived | attribute | ISO-8601 | inferred |
| 18 | `archived_by` | `shq.error_master_archive.archived_by` | text | Y | Archived By | attribute | STRING | inferred |
| 19 | `archive_reason` | `shq.error_master_archive.archive_reason` | text | Y | Reason this record was archived | attribute | STRING | inferred |
| 20 | `final_disposition` | `shq.error_master_archive.final_disposition` | USER-DEFINED | Y | Final Disposition | attribute | STRING | inferred |
| 21 | `retention_expires_at` | `shq.error_master_archive.retention_expires_at` | timestamp with time zone | Y | Timestamp for retention expires event | attribute | ISO-8601 | inferred |

---

## `DEPRECATED` DEPRECATED (legacy, do not use)

**Tables**: 21 | **Total rows**: 212,156

### `company.company_events` -- DEPRECATED -- 0 rows

**Hub**: `DEPRECATED` company schema (deprecated)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `company.company_events.id` | integer | N | Id | identifier | INTEGER | inferred |
| 2 | `company_unique_id` | `company.company_events.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 3 | `event_type` | `company.company_events.event_type` | text | Y | Type of audit/system event | attribute | STRING | inferred |
| 4 | `event_date` | `company.company_events.event_date` | date | Y | Event Date | attribute | DATE | inferred |
| 5 | `source_url` | `company.company_events.source_url` | text | Y | URL of the content source | attribute | URL | inferred |
| 6 | `summary` | `company.company_events.summary` | text | Y | Summary | attribute | STRING | inferred |
| 7 | `detected_at` | `company.company_events.detected_at` | timestamp without time zone | N | When this event/signal was detected | attribute | ISO-8601 | inferred |
| 8 | `impacts_bit` | `company.company_events.impacts_bit` | boolean | Y | Impacts Bit | attribute | BOOLEAN | inferred |
| 9 | `bit_impact_score` | `company.company_events.bit_impact_score` | integer | Y | Bit Impact score | metric | INTEGER | inferred |
| 10 | `created_at` | `company.company_events.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

### `company.company_master` -- DEPRECATED -- 92,116 rows

**Hub**: `DEPRECATED` company schema (deprecated)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `company_unique_id` | `company.company_master.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 2 | `company_name` | `company.company_master.company_name` | text | N | Company legal or common name | attribute | STRING | inferred |
| 3 | `website_url` | `company.company_master.website_url` | text | Y | Company website URL | attribute | URL | inferred |
| 4 | `industry` | `company.company_master.industry` | text | Y | Industry | attribute | STRING | inferred |
| 5 | `employee_count` | `company.company_master.employee_count` | integer | N | Count of employee | metric | INTEGER | inferred |
| 6 | `company_phone` | `company.company_master.company_phone` | text | Y | Company Phone | attribute | STRING | inferred |
| 7 | `address_street` | `company.company_master.address_street` | text | Y | Address Street | attribute | STRING | inferred |
| 8 | `address_city` | `company.company_master.address_city` | text | Y | Address City | attribute | STRING | inferred |
| 9 | `address_state` | `company.company_master.address_state` | text | N | Address State | attribute | STRING | inferred |
| 10 | `address_zip` | `company.company_master.address_zip` | text | Y | Address Zip | attribute | STRING | inferred |
| 11 | `address_country` | `company.company_master.address_country` | text | Y | Address Country | attribute | STRING | inferred |
| 12 | `linkedin_url` | `company.company_master.linkedin_url` | text | Y | LinkedIn profile URL | attribute | URL | inferred |
| 13 | `facebook_url` | `company.company_master.facebook_url` | text | Y | Facebook URL | attribute | URL | inferred |
| 14 | `twitter_url` | `company.company_master.twitter_url` | text | Y | Twitter URL | attribute | URL | inferred |
| 15 | `sic_codes` | `company.company_master.sic_codes` | text | Y | Sic Codes | attribute | STRING | inferred |
| 16 | `founded_year` | `company.company_master.founded_year` | integer | Y | Founded Year | attribute | INTEGER | inferred |
| 17 | `keywords` | `company.company_master.keywords` | ARRAY | Y | Keywords | attribute | ARRAY | inferred |
| 18 | `description` | `company.company_master.description` | text | Y | Description | attribute | STRING | inferred |
| 19 | `source_system` | `company.company_master.source_system` | text | N | System that originated this record | attribute | STRING | inferred |
| 20 | `source_record_id` | `company.company_master.source_record_id` | text | Y | Source Record Id | identifier | STRING | inferred |
| 21 | `promoted_from_intake_at` | `company.company_master.promoted_from_intake_at` | timestamp with time zone | N | Timestamp for promoted from intake event | attribute | ISO-8601 | inferred |
| 22 | `promotion_audit_log_id` | `company.company_master.promotion_audit_log_id` | integer | Y | Promotion Audit Log Id | identifier | INTEGER | inferred |
| 23 | `created_at` | `company.company_master.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 24 | `updated_at` | `company.company_master.updated_at` | timestamp with time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |
| 25 | `state_abbrev` | `company.company_master.state_abbrev` | text | Y | State Abbrev | attribute | STRING | inferred |
| 26 | `import_batch_id` | `company.company_master.import_batch_id` | text | Y | Import Batch Id | identifier | STRING | inferred |
| 27 | `validated_at` | `company.company_master.validated_at` | timestamp with time zone | Y | Timestamp for validated event | attribute | ISO-8601 | inferred |
| 28 | `validated_by` | `company.company_master.validated_by` | text | Y | Validated By | attribute | STRING | inferred |
| 29 | `data_quality_score` | `company.company_master.data_quality_score` | numeric | Y | Data Quality score | metric | NUMERIC | inferred |
| 30 | `email_pattern` | `company.company_master.email_pattern` | character varying(50) | Y | Email Pattern | attribute | EMAIL | inferred |
| 31 | `email_pattern_confidence` | `company.company_master.email_pattern_confidence` | integer | Y | Email Pattern Confidence | metric | INTEGER | inferred |
| 32 | `email_pattern_source` | `company.company_master.email_pattern_source` | character varying(50) | Y | Email Pattern Source | attribute | EMAIL | inferred |
| 33 | `email_pattern_verified_at` | `company.company_master.email_pattern_verified_at` | timestamp without time zone | Y | Timestamp for email pattern verified event | attribute | ISO-8601 | inferred |
| 34 | `ein` | `company.company_master.ein` | character varying(9) | Y | Employer Identification Number (9-digit, no dashes) | attribute | STRING | inferred |
| 35 | `duns` | `company.company_master.duns` | character varying(9) | Y | Duns | attribute | STRING | inferred |
| 36 | `cage_code` | `company.company_master.cage_code` | character varying(5) | Y | Cage Code | attribute | STRING | inferred |

### `company.company_sidecar` -- DEPRECATED -- 0 rows

**Hub**: `DEPRECATED` company schema (deprecated)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `company_unique_id` | `company.company_sidecar.company_unique_id` | character varying(50) | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 2 | `ein_number` | `company.company_sidecar.ein_number` | character varying(20) | Y | Ein Number | attribute | STRING | inferred |
| 3 | `dun_and_bradstreet_number` | `company.company_sidecar.dun_and_bradstreet_number` | character varying(20) | Y | Dun And Bradstreet Number | attribute | STRING | inferred |
| 4 | `clay_tags` | `company.company_sidecar.clay_tags` | ARRAY | Y | Clay Tags | attribute | ARRAY | inferred |
| 5 | `clay_segments` | `company.company_sidecar.clay_segments` | ARRAY | Y | Clay Segments | attribute | ARRAY | inferred |
| 6 | `enrichment_payload` | `company.company_sidecar.enrichment_payload` | jsonb | Y | Enrichment Payload | attribute | JSONB | inferred |
| 7 | `last_enriched_at` | `company.company_sidecar.last_enriched_at` | timestamp without time zone | Y | Timestamp for last enriched event | attribute | ISO-8601 | inferred |
| 8 | `enrichment_source` | `company.company_sidecar.enrichment_source` | text | Y | Enrichment Source | attribute | STRING | inferred |
| 9 | `confidence_score` | `company.company_sidecar.confidence_score` | numeric | Y | Confidence score (0-100) | metric | NUMERIC | inferred |
| 10 | `created_at` | `company.company_sidecar.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 11 | `updated_at` | `company.company_sidecar.updated_at` | timestamp without time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |

### `company.company_slots` -- DEPRECATED -- 1,359 rows

**Hub**: `DEPRECATED` company schema (deprecated)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `company_slot_unique_id` | `company.company_slots.company_slot_unique_id` | text | N | FK to people.company_slot.slot_id | foreign_key | STRING | inferred |
| 2 | `company_unique_id` | `company.company_slots.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 3 | `slot_type` | `company.company_slots.slot_type` | text | Y | Executive role type (CEO, CFO, HR, CTO, CMO, COO) | attribute | ENUM | inferred |
| 4 | `slot_label` | `company.company_slots.slot_label` | text | Y | Slot Label | attribute | STRING | inferred |
| 5 | `created_at` | `company.company_slots.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

### `company.company_source_urls` -- DEPRECATED -- 114,736 rows

**Hub**: `DEPRECATED` company schema (deprecated)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `source_id` | `company.company_source_urls.source_id` | uuid | N | Source Id | identifier | UUID | inferred |
| 2 | `company_unique_id` | `company.company_source_urls.company_unique_id` | text | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 3 | `source_type` | `company.company_source_urls.source_type` | character varying(50) | N | Source Type | attribute | ENUM | inferred |
| 4 | `source_url` | `company.company_source_urls.source_url` | text | N | URL of the content source | attribute | URL | inferred |
| 5 | `page_title` | `company.company_source_urls.page_title` | text | Y | Page Title | attribute | STRING | inferred |
| 6 | `discovered_at` | `company.company_source_urls.discovered_at` | timestamp with time zone | N | Timestamp for discovered event | attribute | ISO-8601 | inferred |
| 7 | `discovered_from` | `company.company_source_urls.discovered_from` | character varying(100) | Y | Discovered From | attribute | STRING | inferred |
| 8 | `last_checked_at` | `company.company_source_urls.last_checked_at` | timestamp with time zone | Y | Timestamp for last checked event | attribute | ISO-8601 | inferred |
| 9 | `http_status` | `company.company_source_urls.http_status` | integer | Y | Http Status | attribute | INTEGER | inferred |
| 10 | `is_accessible` | `company.company_source_urls.is_accessible` | boolean | Y | Whether this record accessible | attribute | BOOLEAN | inferred |
| 11 | `content_checksum` | `company.company_source_urls.content_checksum` | text | Y | Content Checksum | attribute | STRING | inferred |
| 12 | `last_content_change_at` | `company.company_source_urls.last_content_change_at` | timestamp with time zone | Y | Timestamp for last content change event | attribute | ISO-8601 | inferred |
| 13 | `extraction_status` | `company.company_source_urls.extraction_status` | character varying(50) | Y | Extraction Status | attribute | STRING | inferred |
| 14 | `extracted_at` | `company.company_source_urls.extracted_at` | timestamp with time zone | Y | Timestamp for extracted event | attribute | ISO-8601 | inferred |
| 15 | `created_at` | `company.company_source_urls.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 16 | `updated_at` | `company.company_source_urls.updated_at` | timestamp with time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |
| 17 | `extraction_error` | `company.company_source_urls.extraction_error` | text | Y | Extraction Error | attribute | STRING | inferred |
| 18 | `people_extracted` | `company.company_source_urls.people_extracted` | integer | Y | People Extracted | attribute | INTEGER | inferred |
| 19 | `requires_paid_enrichment` | `company.company_source_urls.requires_paid_enrichment` | boolean | Y | Requires Paid Enrichment | attribute | BOOLEAN | inferred |

### `company.contact_enrichment` -- DEPRECATED -- 0 rows

**Hub**: `DEPRECATED` company schema (deprecated)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `company.contact_enrichment.id` | integer | N | Id | identifier | INTEGER | inferred |
| 2 | `company_slot_unique_id` | `company.contact_enrichment.company_slot_unique_id` | text | N | FK to people.company_slot.slot_id | foreign_key | STRING | inferred |
| 3 | `linkedin_url` | `company.contact_enrichment.linkedin_url` | text | Y | LinkedIn profile URL | attribute | URL | inferred |
| 4 | `full_name` | `company.contact_enrichment.full_name` | text | Y | Full Name | attribute | STRING | inferred |
| 5 | `email` | `company.contact_enrichment.email` | text | Y | Email address | attribute | EMAIL | inferred |
| 6 | `phone` | `company.contact_enrichment.phone` | text | Y | Phone number (E.164 format preferred) | attribute | STRING | inferred |
| 7 | `enrichment_status` | `company.contact_enrichment.enrichment_status` | text | Y | Enrichment Status | attribute | STRING | inferred |
| 8 | `enrichment_source` | `company.contact_enrichment.enrichment_source` | text | Y | Enrichment Source | attribute | STRING | inferred |
| 9 | `enrichment_data` | `company.contact_enrichment.enrichment_data` | jsonb | Y | Enrichment Data | attribute | JSONB | inferred |
| 10 | `created_at` | `company.contact_enrichment.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 11 | `enriched_at` | `company.contact_enrichment.enriched_at` | timestamp without time zone | Y | Timestamp for enriched event | attribute | ISO-8601 | inferred |

### `company.email_verification` -- DEPRECATED -- 0 rows

**Hub**: `DEPRECATED` company schema (deprecated)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `company.email_verification.id` | integer | N | Id | identifier | INTEGER | inferred |
| 2 | `enrichment_id` | `company.email_verification.enrichment_id` | integer | N | Enrichment Id | identifier | INTEGER | inferred |
| 3 | `email` | `company.email_verification.email` | text | N | Email address | attribute | EMAIL | inferred |
| 4 | `verification_status` | `company.email_verification.verification_status` | text | Y | Current verification status | attribute | ENUM | inferred |
| 5 | `verification_service` | `company.email_verification.verification_service` | text | Y | Verification Service | attribute | STRING | inferred |
| 6 | `verification_result` | `company.email_verification.verification_result` | jsonb | Y | Verification Result | attribute | JSONB | inferred |
| 7 | `verified_at` | `company.email_verification.verified_at` | timestamp without time zone | Y | When verification was completed | attribute | ISO-8601 | inferred |
| 8 | `created_at` | `company.email_verification.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

### `company.message_key_reference` -- DEPRECATED -- 8 rows

**Hub**: `DEPRECATED` company schema (deprecated)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `message_key` | `company.message_key_reference.message_key` | text | N | Message Key | attribute | STRING | inferred |
| 2 | `role` | `company.message_key_reference.role` | text | N | Role | attribute | STRING | inferred |
| 3 | `message_type` | `company.message_key_reference.message_type` | text | N | Message Type | attribute | STRING | inferred |
| 4 | `trigger_condition` | `company.message_key_reference.trigger_condition` | text | Y | Trigger Condition | attribute | STRING | inferred |
| 5 | `vibeos_template_id` | `company.message_key_reference.vibeos_template_id` | text | Y | Vibeos Template Id | identifier | STRING | inferred |
| 6 | `message_channel` | `company.message_key_reference.message_channel` | text | Y | Message Channel | attribute | STRING | inferred |
| 7 | `subject_line` | `company.message_key_reference.subject_line` | text | Y | Subject Line | attribute | STRING | inferred |
| 8 | `preview_text` | `company.message_key_reference.preview_text` | text | Y | Preview Text | attribute | STRING | inferred |
| 9 | `send_delay_hours` | `company.message_key_reference.send_delay_hours` | integer | Y | Send Delay Hours | attribute | INTEGER | inferred |
| 10 | `optimal_send_time` | `company.message_key_reference.optimal_send_time` | text | Y | Optimal Send Time | attribute | STRING | inferred |
| 11 | `active` | `company.message_key_reference.active` | boolean | Y | Active | attribute | BOOLEAN | inferred |
| 12 | `created_at` | `company.message_key_reference.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 13 | `updated_at` | `company.message_key_reference.updated_at` | timestamp with time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |

### `company.pipeline_errors` -- DEPRECATED -- 0 rows

**Hub**: `DEPRECATED` company schema (deprecated)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `company.pipeline_errors.id` | integer | N | Id | identifier | INTEGER | inferred |
| 2 | `event_type` | `company.pipeline_errors.event_type` | text | N | Type of audit/system event | attribute | STRING | inferred |
| 3 | `record_id` | `company.pipeline_errors.record_id` | text | N | Record Id | identifier | STRING | inferred |
| 4 | `error_message` | `company.pipeline_errors.error_message` | text | N | Human-readable error description | attribute | STRING | inferred |
| 5 | `error_details` | `company.pipeline_errors.error_details` | jsonb | Y | Error Details | attribute | JSONB | inferred |
| 6 | `severity` | `company.pipeline_errors.severity` | text | Y | Severity | attribute | STRING | inferred |
| 7 | `resolved` | `company.pipeline_errors.resolved` | boolean | Y | Resolved | attribute | BOOLEAN | inferred |
| 8 | `resolved_at` | `company.pipeline_errors.resolved_at` | timestamp without time zone | Y | When this error/issue was resolved | attribute | ISO-8601 | inferred |
| 9 | `resolved_by` | `company.pipeline_errors.resolved_by` | text | Y | Resolved By | attribute | STRING | inferred |
| 10 | `resolution_notes` | `company.pipeline_errors.resolution_notes` | text | Y | Resolution Notes | attribute | STRING | inferred |
| 11 | `created_at` | `company.pipeline_errors.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 12 | `error_type` | `company.pipeline_errors.error_type` | character varying(100) | Y | Discriminator column classifying the error type | attribute | ENUM | inferred |

### `company.pipeline_events` -- DEPRECATED -- 2,185 rows

**Hub**: `DEPRECATED` company schema (deprecated)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `company.pipeline_events.id` | integer | N | Id | identifier | INTEGER | inferred |
| 2 | `event_type` | `company.pipeline_events.event_type` | text | N | Type of audit/system event | attribute | STRING | inferred |
| 3 | `payload` | `company.pipeline_events.payload` | jsonb | N | Payload | attribute | JSONB | inferred |
| 4 | `status` | `company.pipeline_events.status` | text | Y | Current status of this record | attribute | ENUM | inferred |
| 5 | `error_message` | `company.pipeline_events.error_message` | text | Y | Human-readable error description | attribute | STRING | inferred |
| 6 | `retry_count` | `company.pipeline_events.retry_count` | integer | Y | Number of retry attempts so far | metric | INTEGER | inferred |
| 7 | `created_at` | `company.pipeline_events.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 8 | `processed_at` | `company.pipeline_events.processed_at` | timestamp without time zone | Y | Timestamp for processed event | attribute | ISO-8601 | inferred |

### `company.validation_failures_log` -- DEPRECATED -- 0 rows

**Hub**: `DEPRECATED` company schema (deprecated)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `company.validation_failures_log.id` | integer | N | Id | identifier | INTEGER | inferred |
| 2 | `company_id` | `company.validation_failures_log.company_id` | text | Y | Company Id | identifier | STRING | inferred |
| 3 | `person_id` | `company.validation_failures_log.person_id` | text | Y | Person Id | identifier | STRING | inferred |
| 4 | `company_name` | `company.validation_failures_log.company_name` | text | Y | Company legal or common name | attribute | STRING | inferred |
| 5 | `person_name` | `company.validation_failures_log.person_name` | text | Y | Person Name | attribute | STRING | inferred |
| 6 | `fail_reason` | `company.validation_failures_log.fail_reason` | text | N | Fail Reason | attribute | STRING | inferred |
| 7 | `state` | `company.validation_failures_log.state` | text | Y | US state code (2-letter) | attribute | ENUM | inferred |
| 8 | `validation_timestamp` | `company.validation_failures_log.validation_timestamp` | timestamp with time zone | Y | Validation Timestamp | attribute | ISO-8601 | inferred |
| 9 | `pipeline_id` | `company.validation_failures_log.pipeline_id` | text | N | Pipeline Id | identifier | STRING | inferred |
| 10 | `failure_type` | `company.validation_failures_log.failure_type` | text | N | Failure Type | attribute | STRING | inferred |
| 11 | `created_at` | `company.validation_failures_log.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 12 | `updated_at` | `company.validation_failures_log.updated_at` | timestamp with time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |
| 13 | `exported_to_sheets` | `company.validation_failures_log.exported_to_sheets` | boolean | Y | Exported To Sheets | attribute | BOOLEAN | inferred |
| 14 | `exported_at` | `company.validation_failures_log.exported_at` | timestamp with time zone | Y | Timestamp for exported event | attribute | ISO-8601 | inferred |
| 15 | `exported_to_b2` | `company.validation_failures_log.exported_to_b2` | boolean | Y | Exported To B2 | attribute | BOOLEAN | inferred |
| 16 | `exported_to_b2_at` | `company.validation_failures_log.exported_to_b2_at` | timestamp without time zone | Y | Timestamp for exported to b2 event | attribute | ISO-8601 | inferred |

### `marketing.company_master` -- DEPRECATED -- 512 rows

**Hub**: `DEPRECATED` marketing schema (deprecated)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `company_unique_id` | `marketing.company_master.company_unique_id` | character varying(50) | N | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 2 | `company_name` | `marketing.company_master.company_name` | character varying(500) | N | Company legal or common name | attribute | STRING | inferred |
| 3 | `domain` | `marketing.company_master.domain` | character varying(255) | Y | Company website domain (lowercase, no protocol) | attribute | STRING | inferred |
| 4 | `industry` | `marketing.company_master.industry` | character varying(255) | Y | Industry | attribute | STRING | inferred |
| 5 | `employee_count` | `marketing.company_master.employee_count` | integer | Y | Count of employee | metric | INTEGER | inferred |
| 6 | `email_pattern` | `marketing.company_master.email_pattern` | character varying(50) | Y | Email Pattern | attribute | EMAIL | inferred |
| 7 | `pattern_confidence` | `marketing.company_master.pattern_confidence` | numeric | Y | Pattern Confidence | metric | NUMERIC | inferred |
| 8 | `source` | `marketing.company_master.source` | character varying(100) | Y | Data source identifier | attribute | STRING | inferred |
| 9 | `source_file` | `marketing.company_master.source_file` | character varying(255) | Y | Source File | attribute | STRING | inferred |
| 10 | `created_at` | `marketing.company_master.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 11 | `updated_at` | `marketing.company_master.updated_at` | timestamp without time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |
| 12 | `bit_band` | `marketing.company_master.bit_band` | integer | Y | Bit Band | attribute | INTEGER | inferred |
| 13 | `bit_phase` | `marketing.company_master.bit_phase` | text | Y | Bit Phase | attribute | STRING | inferred |

### `marketing.failed_company_match` -- DEPRECATED -- 32 rows

**Hub**: `DEPRECATED` marketing schema (deprecated)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `marketing.failed_company_match.id` | integer | N | Id | identifier | INTEGER | inferred |
| 2 | `person_id` | `marketing.failed_company_match.person_id` | character varying(50) | N | Person Id | identifier | STRING | inferred |
| 3 | `full_name` | `marketing.failed_company_match.full_name` | character varying(500) | N | Full Name | attribute | STRING | inferred |
| 4 | `job_title` | `marketing.failed_company_match.job_title` | character varying(500) | Y | Job title or position | attribute | STRING | inferred |
| 5 | `title_seniority` | `marketing.failed_company_match.title_seniority` | character varying(50) | Y | Title Seniority | attribute | STRING | inferred |
| 6 | `company_name_raw` | `marketing.failed_company_match.company_name_raw` | character varying(500) | N | Company Name Raw | attribute | STRING | inferred |
| 7 | `linkedin_url` | `marketing.failed_company_match.linkedin_url` | character varying(500) | Y | LinkedIn profile URL | attribute | URL | inferred |
| 8 | `best_match_company` | `marketing.failed_company_match.best_match_company` | character varying(500) | Y | Best Match Company | attribute | STRING | inferred |
| 9 | `best_match_score` | `marketing.failed_company_match.best_match_score` | numeric | Y | Best Match score | metric | NUMERIC | inferred |
| 10 | `best_match_notes` | `marketing.failed_company_match.best_match_notes` | text | Y | Best Match Notes | attribute | STRING | inferred |
| 11 | `resolution_status` | `marketing.failed_company_match.resolution_status` | character varying(50) | Y | Resolution Status | attribute | STRING | inferred |
| 12 | `resolution` | `marketing.failed_company_match.resolution` | character varying(50) | Y | Resolution | attribute | STRING | inferred |
| 13 | `resolution_notes` | `marketing.failed_company_match.resolution_notes` | text | Y | Resolution Notes | attribute | STRING | inferred |
| 14 | `resolved_by` | `marketing.failed_company_match.resolved_by` | character varying(255) | Y | Resolved By | attribute | STRING | inferred |
| 15 | `resolved_at` | `marketing.failed_company_match.resolved_at` | timestamp without time zone | Y | When this error/issue was resolved | attribute | ISO-8601 | inferred |
| 16 | `resolved_company_id` | `marketing.failed_company_match.resolved_company_id` | character varying(50) | Y | Resolved Company Id | identifier | STRING | inferred |
| 17 | `source` | `marketing.failed_company_match.source` | character varying(100) | Y | Data source identifier | attribute | STRING | inferred |
| 18 | `source_file` | `marketing.failed_company_match.source_file` | character varying(255) | Y | Source File | attribute | STRING | inferred |
| 19 | `created_at` | `marketing.failed_company_match.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 20 | `updated_at` | `marketing.failed_company_match.updated_at` | timestamp without time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |

### `marketing.failed_email_verification` -- DEPRECATED -- 310 rows

**Hub**: `DEPRECATED` marketing schema (deprecated)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `marketing.failed_email_verification.id` | integer | N | Id | identifier | INTEGER | inferred |
| 2 | `person_id` | `marketing.failed_email_verification.person_id` | character varying(50) | N | Person Id | identifier | STRING | inferred |
| 3 | `full_name` | `marketing.failed_email_verification.full_name` | character varying(500) | N | Full Name | attribute | STRING | inferred |
| 4 | `job_title` | `marketing.failed_email_verification.job_title` | character varying(500) | Y | Job title or position | attribute | STRING | inferred |
| 5 | `title_seniority` | `marketing.failed_email_verification.title_seniority` | character varying(50) | Y | Title Seniority | attribute | STRING | inferred |
| 6 | `company_name_raw` | `marketing.failed_email_verification.company_name_raw` | character varying(500) | Y | Company Name Raw | attribute | STRING | inferred |
| 7 | `linkedin_url` | `marketing.failed_email_verification.linkedin_url` | character varying(500) | Y | LinkedIn profile URL | attribute | URL | inferred |
| 8 | `company_id` | `marketing.failed_email_verification.company_id` | character varying(50) | Y | Company Id | identifier | STRING | inferred |
| 9 | `company_name` | `marketing.failed_email_verification.company_name` | character varying(500) | Y | Company legal or common name | attribute | STRING | inferred |
| 10 | `company_domain` | `marketing.failed_email_verification.company_domain` | character varying(255) | Y | Company Domain | attribute | STRING | inferred |
| 11 | `email_pattern` | `marketing.failed_email_verification.email_pattern` | character varying(50) | Y | Email Pattern | attribute | EMAIL | inferred |
| 12 | `slot_type` | `marketing.failed_email_verification.slot_type` | character varying(50) | Y | Executive role type (CEO, CFO, HR, CTO, CMO, COO) | attribute | ENUM | inferred |
| 13 | `generated_email` | `marketing.failed_email_verification.generated_email` | character varying(255) | Y | Generated Email | attribute | EMAIL | inferred |
| 14 | `verification_error` | `marketing.failed_email_verification.verification_error` | character varying(255) | Y | Error message from verification attempt | attribute | STRING | inferred |
| 15 | `verification_notes` | `marketing.failed_email_verification.verification_notes` | text | Y | Verification Notes | attribute | STRING | inferred |
| 16 | `email_variants` | `marketing.failed_email_verification.email_variants` | text | Y | Email Variants | attribute | EMAIL | inferred |
| 17 | `resolution_status` | `marketing.failed_email_verification.resolution_status` | character varying(50) | Y | Resolution Status | attribute | STRING | inferred |
| 18 | `resolution` | `marketing.failed_email_verification.resolution` | character varying(50) | Y | Resolution | attribute | STRING | inferred |
| 19 | `resolution_notes` | `marketing.failed_email_verification.resolution_notes` | text | Y | Resolution Notes | attribute | STRING | inferred |
| 20 | `resolved_by` | `marketing.failed_email_verification.resolved_by` | character varying(255) | Y | Resolved By | attribute | STRING | inferred |
| 21 | `resolved_at` | `marketing.failed_email_verification.resolved_at` | timestamp without time zone | Y | When this error/issue was resolved | attribute | ISO-8601 | inferred |
| 22 | `verified_email` | `marketing.failed_email_verification.verified_email` | character varying(255) | Y | Verified Email | attribute | EMAIL | inferred |
| 23 | `verified_email_source` | `marketing.failed_email_verification.verified_email_source` | character varying(100) | Y | Verified Email Source | attribute | EMAIL | inferred |
| 24 | `source` | `marketing.failed_email_verification.source` | character varying(100) | Y | Data source identifier | attribute | STRING | inferred |
| 25 | `source_file` | `marketing.failed_email_verification.source_file` | character varying(255) | Y | Source File | attribute | STRING | inferred |
| 26 | `created_at` | `marketing.failed_email_verification.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 27 | `updated_at` | `marketing.failed_email_verification.updated_at` | timestamp without time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |

### `marketing.failed_low_confidence` -- DEPRECATED -- 5 rows

**Hub**: `DEPRECATED` marketing schema (deprecated)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `marketing.failed_low_confidence.id` | integer | N | Id | identifier | INTEGER | inferred |
| 2 | `person_id` | `marketing.failed_low_confidence.person_id` | character varying(50) | N | Person Id | identifier | STRING | inferred |
| 3 | `full_name` | `marketing.failed_low_confidence.full_name` | character varying(500) | N | Full Name | attribute | STRING | inferred |
| 4 | `job_title` | `marketing.failed_low_confidence.job_title` | character varying(500) | Y | Job title or position | attribute | STRING | inferred |
| 5 | `title_seniority` | `marketing.failed_low_confidence.title_seniority` | character varying(50) | Y | Title Seniority | attribute | STRING | inferred |
| 6 | `company_name_raw` | `marketing.failed_low_confidence.company_name_raw` | character varying(500) | N | Company Name Raw | attribute | STRING | inferred |
| 7 | `linkedin_url` | `marketing.failed_low_confidence.linkedin_url` | character varying(500) | Y | LinkedIn profile URL | attribute | URL | inferred |
| 8 | `matched_company_id` | `marketing.failed_low_confidence.matched_company_id` | character varying(50) | Y | Matched Company Id | identifier | STRING | inferred |
| 9 | `matched_company_name` | `marketing.failed_low_confidence.matched_company_name` | character varying(500) | Y | Matched Company Name | attribute | STRING | inferred |
| 10 | `matched_company_domain` | `marketing.failed_low_confidence.matched_company_domain` | character varying(255) | Y | Matched Company Domain | attribute | STRING | inferred |
| 11 | `fuzzy_score` | `marketing.failed_low_confidence.fuzzy_score` | numeric | Y | Fuzzy score | metric | NUMERIC | inferred |
| 12 | `match_notes` | `marketing.failed_low_confidence.match_notes` | text | Y | Match Notes | attribute | STRING | inferred |
| 13 | `resolution_status` | `marketing.failed_low_confidence.resolution_status` | character varying(50) | Y | Resolution Status | attribute | STRING | inferred |
| 14 | `resolution` | `marketing.failed_low_confidence.resolution` | character varying(50) | Y | Resolution | attribute | STRING | inferred |
| 15 | `resolution_notes` | `marketing.failed_low_confidence.resolution_notes` | text | Y | Resolution Notes | attribute | STRING | inferred |
| 16 | `resolved_by` | `marketing.failed_low_confidence.resolved_by` | character varying(255) | Y | Resolved By | attribute | STRING | inferred |
| 17 | `resolved_at` | `marketing.failed_low_confidence.resolved_at` | timestamp without time zone | Y | When this error/issue was resolved | attribute | ISO-8601 | inferred |
| 18 | `confirmed_company_id` | `marketing.failed_low_confidence.confirmed_company_id` | character varying(50) | Y | Confirmed Company Id | identifier | STRING | inferred |
| 19 | `source` | `marketing.failed_low_confidence.source` | character varying(100) | Y | Data source identifier | attribute | STRING | inferred |
| 20 | `source_file` | `marketing.failed_low_confidence.source_file` | character varying(255) | Y | Source File | attribute | STRING | inferred |
| 21 | `created_at` | `marketing.failed_low_confidence.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 22 | `updated_at` | `marketing.failed_low_confidence.updated_at` | timestamp without time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |

### `marketing.failed_no_pattern` -- DEPRECATED -- 6 rows

**Hub**: `DEPRECATED` marketing schema (deprecated)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `marketing.failed_no_pattern.id` | integer | N | Id | identifier | INTEGER | inferred |
| 2 | `person_id` | `marketing.failed_no_pattern.person_id` | character varying(50) | N | Person Id | identifier | STRING | inferred |
| 3 | `full_name` | `marketing.failed_no_pattern.full_name` | character varying(500) | N | Full Name | attribute | STRING | inferred |
| 4 | `job_title` | `marketing.failed_no_pattern.job_title` | character varying(500) | Y | Job title or position | attribute | STRING | inferred |
| 5 | `title_seniority` | `marketing.failed_no_pattern.title_seniority` | character varying(50) | Y | Title Seniority | attribute | STRING | inferred |
| 6 | `company_name_raw` | `marketing.failed_no_pattern.company_name_raw` | character varying(500) | Y | Company Name Raw | attribute | STRING | inferred |
| 7 | `linkedin_url` | `marketing.failed_no_pattern.linkedin_url` | character varying(500) | Y | LinkedIn profile URL | attribute | URL | inferred |
| 8 | `company_id` | `marketing.failed_no_pattern.company_id` | character varying(50) | Y | Company Id | identifier | STRING | inferred |
| 9 | `company_name` | `marketing.failed_no_pattern.company_name` | character varying(500) | Y | Company legal or common name | attribute | STRING | inferred |
| 10 | `company_domain` | `marketing.failed_no_pattern.company_domain` | character varying(255) | Y | Company Domain | attribute | STRING | inferred |
| 11 | `slot_type` | `marketing.failed_no_pattern.slot_type` | character varying(50) | Y | Executive role type (CEO, CFO, HR, CTO, CMO, COO) | attribute | ENUM | inferred |
| 12 | `failure_reason` | `marketing.failed_no_pattern.failure_reason` | character varying(100) | Y | Failure Reason | attribute | STRING | inferred |
| 13 | `failure_notes` | `marketing.failed_no_pattern.failure_notes` | text | Y | Failure Notes | attribute | STRING | inferred |
| 14 | `resolution_status` | `marketing.failed_no_pattern.resolution_status` | character varying(50) | Y | Resolution Status | attribute | STRING | inferred |
| 15 | `resolution` | `marketing.failed_no_pattern.resolution` | character varying(50) | Y | Resolution | attribute | STRING | inferred |
| 16 | `resolution_notes` | `marketing.failed_no_pattern.resolution_notes` | text | Y | Resolution Notes | attribute | STRING | inferred |
| 17 | `resolved_by` | `marketing.failed_no_pattern.resolved_by` | character varying(255) | Y | Resolved By | attribute | STRING | inferred |
| 18 | `resolved_at` | `marketing.failed_no_pattern.resolved_at` | timestamp without time zone | Y | When this error/issue was resolved | attribute | ISO-8601 | inferred |
| 19 | `manual_email` | `marketing.failed_no_pattern.manual_email` | character varying(255) | Y | Manual Email | attribute | EMAIL | inferred |
| 20 | `manual_email_source` | `marketing.failed_no_pattern.manual_email_source` | character varying(100) | Y | Manual Email Source | attribute | EMAIL | inferred |
| 21 | `source` | `marketing.failed_no_pattern.source` | character varying(100) | Y | Data source identifier | attribute | STRING | inferred |
| 22 | `source_file` | `marketing.failed_no_pattern.source_file` | character varying(255) | Y | Source File | attribute | STRING | inferred |
| 23 | `created_at` | `marketing.failed_no_pattern.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 24 | `updated_at` | `marketing.failed_no_pattern.updated_at` | timestamp without time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |

### `marketing.failed_slot_assignment` -- DEPRECATED -- 222 rows

**Hub**: `DEPRECATED` marketing schema (deprecated)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `marketing.failed_slot_assignment.id` | integer | N | Id | identifier | INTEGER | inferred |
| 2 | `person_id` | `marketing.failed_slot_assignment.person_id` | character varying(50) | N | Person Id | identifier | STRING | inferred |
| 3 | `full_name` | `marketing.failed_slot_assignment.full_name` | character varying(500) | N | Full Name | attribute | STRING | inferred |
| 4 | `job_title` | `marketing.failed_slot_assignment.job_title` | character varying(500) | Y | Job title or position | attribute | STRING | inferred |
| 5 | `title_seniority` | `marketing.failed_slot_assignment.title_seniority` | character varying(50) | Y | Title Seniority | attribute | STRING | inferred |
| 6 | `company_name_raw` | `marketing.failed_slot_assignment.company_name_raw` | character varying(500) | Y | Company Name Raw | attribute | STRING | inferred |
| 7 | `linkedin_url` | `marketing.failed_slot_assignment.linkedin_url` | character varying(500) | Y | LinkedIn profile URL | attribute | URL | inferred |
| 8 | `matched_company_id` | `marketing.failed_slot_assignment.matched_company_id` | character varying(50) | Y | Matched Company Id | identifier | STRING | inferred |
| 9 | `matched_company_name` | `marketing.failed_slot_assignment.matched_company_name` | character varying(500) | Y | Matched Company Name | attribute | STRING | inferred |
| 10 | `matched_company_domain` | `marketing.failed_slot_assignment.matched_company_domain` | character varying(255) | Y | Matched Company Domain | attribute | STRING | inferred |
| 11 | `fuzzy_score` | `marketing.failed_slot_assignment.fuzzy_score` | numeric | Y | Fuzzy score | metric | NUMERIC | inferred |
| 12 | `slot_type` | `marketing.failed_slot_assignment.slot_type` | character varying(50) | Y | Executive role type (CEO, CFO, HR, CTO, CMO, COO) | attribute | ENUM | inferred |
| 13 | `lost_to_person_id` | `marketing.failed_slot_assignment.lost_to_person_id` | character varying(50) | Y | Lost To Person Id | identifier | STRING | inferred |
| 14 | `lost_to_person_name` | `marketing.failed_slot_assignment.lost_to_person_name` | character varying(500) | Y | Lost To Person Name | attribute | STRING | inferred |
| 15 | `lost_to_seniority` | `marketing.failed_slot_assignment.lost_to_seniority` | character varying(50) | Y | Lost To Seniority | attribute | STRING | inferred |
| 16 | `resolution_status` | `marketing.failed_slot_assignment.resolution_status` | character varying(50) | Y | Resolution Status | attribute | STRING | inferred |
| 17 | `resolution` | `marketing.failed_slot_assignment.resolution` | character varying(50) | Y | Resolution | attribute | STRING | inferred |
| 18 | `resolution_notes` | `marketing.failed_slot_assignment.resolution_notes` | text | Y | Resolution Notes | attribute | STRING | inferred |
| 19 | `resolved_by` | `marketing.failed_slot_assignment.resolved_by` | character varying(255) | Y | Resolved By | attribute | STRING | inferred |
| 20 | `resolved_at` | `marketing.failed_slot_assignment.resolved_at` | timestamp without time zone | Y | When this error/issue was resolved | attribute | ISO-8601 | inferred |
| 21 | `source` | `marketing.failed_slot_assignment.source` | character varying(100) | Y | Data source identifier | attribute | STRING | inferred |
| 22 | `source_file` | `marketing.failed_slot_assignment.source_file` | character varying(255) | Y | Source File | attribute | STRING | inferred |
| 23 | `created_at` | `marketing.failed_slot_assignment.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 24 | `updated_at` | `marketing.failed_slot_assignment.updated_at` | timestamp without time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |

### `marketing.people_master` -- DEPRECATED -- 149 rows

**Hub**: `DEPRECATED` marketing schema (deprecated)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `unique_id` | `marketing.people_master.unique_id` | character varying(50) | N | Primary identifier for this record (Barton ID format) | identifier | STRING | inferred |
| 2 | `company_unique_id` | `marketing.people_master.company_unique_id` | character varying(50) | Y | FK to cl.company_identity or Barton company ID | foreign_key | STRING | inferred |
| 3 | `full_name` | `marketing.people_master.full_name` | character varying(500) | N | Full Name | attribute | STRING | inferred |
| 4 | `first_name` | `marketing.people_master.first_name` | character varying(255) | Y | Person first name | attribute | STRING | inferred |
| 5 | `last_name` | `marketing.people_master.last_name` | character varying(255) | Y | Person last name | attribute | STRING | inferred |
| 6 | `email` | `marketing.people_master.email` | character varying(255) | Y | Email address | attribute | EMAIL | inferred |
| 7 | `email_verified` | `marketing.people_master.email_verified` | boolean | Y | Whether email was verified via Million Verifier | attribute | BOOLEAN | inferred |
| 8 | `email_confidence` | `marketing.people_master.email_confidence` | numeric | Y | Email Confidence | metric | NUMERIC | inferred |
| 9 | `linkedin_url` | `marketing.people_master.linkedin_url` | character varying(500) | Y | LinkedIn profile URL | attribute | URL | inferred |
| 10 | `title` | `marketing.people_master.title` | character varying(500) | Y | Job title or position | attribute | STRING | inferred |
| 11 | `title_seniority` | `marketing.people_master.title_seniority` | character varying(50) | Y | Title Seniority | attribute | STRING | inferred |
| 12 | `location` | `marketing.people_master.location` | character varying(500) | Y | Location | attribute | STRING | inferred |
| 13 | `source` | `marketing.people_master.source` | character varying(100) | Y | Data source identifier | attribute | STRING | inferred |
| 14 | `source_file` | `marketing.people_master.source_file` | character varying(255) | Y | Source File | attribute | STRING | inferred |
| 15 | `created_at` | `marketing.people_master.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 16 | `updated_at` | `marketing.people_master.updated_at` | timestamp without time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |
| 17 | `slot_complete` | `marketing.people_master.slot_complete` | boolean | Y | Slot Complete | attribute | BOOLEAN | inferred |

### `marketing.review_queue` -- DEPRECATED -- 516 rows

**Hub**: `DEPRECATED` marketing schema (deprecated)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `review_id` | `marketing.review_queue.review_id` | integer | N | Review Id | identifier | INTEGER | inferred |
| 2 | `person_id` | `marketing.review_queue.person_id` | character varying(50) | N | Person Id | identifier | STRING | inferred |
| 3 | `full_name` | `marketing.review_queue.full_name` | character varying(500) | N | Full Name | attribute | STRING | inferred |
| 4 | `job_title` | `marketing.review_queue.job_title` | character varying(500) | Y | Job title or position | attribute | STRING | inferred |
| 5 | `company_name_raw` | `marketing.review_queue.company_name_raw` | character varying(500) | Y | Company Name Raw | attribute | STRING | inferred |
| 6 | `review_reason` | `marketing.review_queue.review_reason` | character varying(50) | N | Review Reason | attribute | STRING | inferred |
| 7 | `review_notes` | `marketing.review_queue.review_notes` | text | Y | Review Notes | attribute | STRING | inferred |
| 8 | `fuzzy_score` | `marketing.review_queue.fuzzy_score` | numeric | Y | Fuzzy score | metric | NUMERIC | inferred |
| 9 | `fuzzy_matched_company` | `marketing.review_queue.fuzzy_matched_company` | character varying(500) | Y | Fuzzy Matched Company | attribute | STRING | inferred |
| 10 | `matched_company_id` | `marketing.review_queue.matched_company_id` | character varying(50) | Y | Matched Company Id | identifier | STRING | inferred |
| 11 | `linkedin_url` | `marketing.review_queue.linkedin_url` | character varying(500) | Y | LinkedIn profile URL | attribute | URL | inferred |
| 12 | `review_status` | `marketing.review_queue.review_status` | character varying(50) | Y | Review Status | attribute | STRING | inferred |
| 13 | `reviewed_by` | `marketing.review_queue.reviewed_by` | character varying(255) | Y | Reviewed By | attribute | STRING | inferred |
| 14 | `reviewed_at` | `marketing.review_queue.reviewed_at` | timestamp without time zone | Y | Timestamp for reviewed event | attribute | ISO-8601 | inferred |
| 15 | `resolution` | `marketing.review_queue.resolution` | character varying(50) | Y | Resolution | attribute | STRING | inferred |
| 16 | `resolution_notes` | `marketing.review_queue.resolution_notes` | text | Y | Resolution Notes | attribute | STRING | inferred |
| 17 | `source` | `marketing.review_queue.source` | character varying(100) | Y | Data source identifier | attribute | STRING | inferred |
| 18 | `source_file` | `marketing.review_queue.source_file` | character varying(255) | Y | Source File | attribute | STRING | inferred |
| 19 | `created_at` | `marketing.review_queue.created_at` | timestamp without time zone | Y | When this record was created | attribute | ISO-8601 | inferred |
| 20 | `updated_at` | `marketing.review_queue.updated_at` | timestamp without time zone | Y | When this record was last updated | attribute | ISO-8601 | inferred |

### `talent_flow.movement_history` -- DEPRECATED -- 0 rows

**Hub**: `DEPRECATED` talent_flow schema (deprecated)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `history_id` | `talent_flow.movement_history.history_id` | uuid | N | History Id | identifier | UUID | inferred |
| 2 | `person_identifier` | `talent_flow.movement_history.person_identifier` | text | N | Person Identifier | attribute | STRING | inferred |
| 3 | `from_outreach_id` | `talent_flow.movement_history.from_outreach_id` | uuid | Y | From Outreach Id | identifier | UUID | inferred |
| 4 | `to_outreach_id` | `talent_flow.movement_history.to_outreach_id` | uuid | Y | To Outreach Id | identifier | UUID | inferred |
| 5 | `movement_type` | `talent_flow.movement_history.movement_type` | character varying(30) | Y | Movement Type | attribute | STRING | inferred |
| 6 | `detected_at` | `talent_flow.movement_history.detected_at` | timestamp with time zone | Y | When this event/signal was detected | attribute | ISO-8601 | inferred |
| 7 | `detection_source` | `talent_flow.movement_history.detection_source` | character varying(50) | Y | Detection Source | attribute | STRING | inferred |
| 8 | `processed_at` | `talent_flow.movement_history.processed_at` | timestamp with time zone | Y | Timestamp for processed event | attribute | ISO-8601 | inferred |
| 9 | `signal_emitted` | `talent_flow.movement_history.signal_emitted` | character varying(50) | Y | Signal Emitted | attribute | STRING | inferred |
| 10 | `bit_event_created` | `talent_flow.movement_history.bit_event_created` | boolean | Y | Bit Event Created | attribute | BOOLEAN | inferred |
| 11 | `correlation_id` | `talent_flow.movement_history.correlation_id` | uuid | Y | UUID linking related operations across tables | identifier | UUID | inferred |
| 12 | `process_id` | `talent_flow.movement_history.process_id` | uuid | Y | Process Id | identifier | UUID | inferred |
| 13 | `created_at` | `talent_flow.movement_history.created_at` | timestamp with time zone | Y | When this record was created | attribute | ISO-8601 | inferred |

### `talent_flow.movements` -- DEPRECATED -- 0 rows

**Hub**: `DEPRECATED` talent_flow schema (deprecated)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `movement_id` | `talent_flow.movements.movement_id` | uuid | N | Primary key for this movement event | identifier | UUID | inferred |
| 2 | `contact_id` | `talent_flow.movements.contact_id` | uuid | N | Contact Id | identifier | UUID | inferred |
| 3 | `movement_type` | `talent_flow.movements.movement_type` | character varying(20) | N | Movement Type | attribute | STRING | inferred |
| 4 | `old_company_id` | `talent_flow.movements.old_company_id` | text | Y | Old Company Id | identifier | STRING | inferred |
| 5 | `new_company_id` | `talent_flow.movements.new_company_id` | text | Y | New Company Id | identifier | STRING | inferred |
| 6 | `old_title` | `talent_flow.movements.old_title` | text | Y | Old Title | attribute | STRING | inferred |
| 7 | `new_title` | `talent_flow.movements.new_title` | text | Y | New Title | attribute | STRING | inferred |
| 8 | `confidence_score` | `talent_flow.movements.confidence_score` | integer | N | Confidence score (0-100) | metric | INTEGER | inferred |
| 9 | `detected_at` | `talent_flow.movements.detected_at` | timestamp with time zone | N | When this event/signal was detected | attribute | ISO-8601 | inferred |
| 10 | `detected_source` | `talent_flow.movements.detected_source` | character varying(50) | N | Detected Source | attribute | STRING | inferred |
| 11 | `created_at` | `talent_flow.movements.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 12 | `updated_at` | `talent_flow.movements.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |

---

## `FUTURE` Future Hubs (scaffolded, not active)

**Tables**: 24 | **Total rows**: 32

### `clnt.audit_event` -- UNREGISTERED -- 0 rows

**Hub**: `FUTURE` Client Hub (future)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `audit_event_id` | `clnt.audit_event.audit_event_id` | uuid | N | Audit Event Id | identifier | UUID | inferred |
| 2 | `client_id` | `clnt.audit_event.client_id` | uuid | N | Client Id | identifier | UUID | inferred |
| 3 | `entity_type` | `clnt.audit_event.entity_type` | text | N | Entity Type | attribute | STRING | inferred |
| 4 | `entity_id` | `clnt.audit_event.entity_id` | uuid | N | Entity Id | identifier | UUID | inferred |
| 5 | `action` | `clnt.audit_event.action` | text | N | Action | attribute | STRING | inferred |
| 6 | `created_at` | `clnt.audit_event.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |

### `clnt.client_hub` -- UNREGISTERED -- 0 rows

**Hub**: `FUTURE` Client Hub (future)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `client_id` | `clnt.client_hub.client_id` | uuid | N | Client Id | identifier | UUID | inferred |
| 2 | `created_at` | `clnt.client_hub.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 3 | `status` | `clnt.client_hub.status` | text | N | Current status of this record | attribute | ENUM | inferred |
| 4 | `source` | `clnt.client_hub.source` | text | Y | Data source identifier | attribute | STRING | inferred |
| 5 | `version` | `clnt.client_hub.version` | integer | N | Version | attribute | INTEGER | inferred |

### `clnt.client_master` -- UNREGISTERED -- 0 rows

**Hub**: `FUTURE` Client Hub (future)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `client_id` | `clnt.client_master.client_id` | uuid | N | Client Id | identifier | UUID | inferred |
| 2 | `legal_name` | `clnt.client_master.legal_name` | text | N | Legal Name | attribute | STRING | inferred |
| 3 | `fein` | `clnt.client_master.fein` | text | Y | Fein | attribute | STRING | inferred |
| 4 | `domicile_state` | `clnt.client_master.domicile_state` | text | Y | Domicile State | attribute | STRING | inferred |
| 5 | `effective_date` | `clnt.client_master.effective_date` | date | Y | Effective Date | attribute | DATE | inferred |
| 6 | `created_at` | `clnt.client_master.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 7 | `updated_at` | `clnt.client_master.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |

### `clnt.compliance_flag` -- UNREGISTERED -- 0 rows

**Hub**: `FUTURE` Client Hub (future)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `compliance_flag_id` | `clnt.compliance_flag.compliance_flag_id` | uuid | N | Compliance Flag Id | identifier | UUID | inferred |
| 2 | `client_id` | `clnt.compliance_flag.client_id` | uuid | N | Client Id | identifier | UUID | inferred |
| 3 | `flag_type` | `clnt.compliance_flag.flag_type` | text | N | Flag Type | attribute | STRING | inferred |
| 4 | `status` | `clnt.compliance_flag.status` | text | N | Current status of this record | attribute | ENUM | inferred |
| 5 | `effective_date` | `clnt.compliance_flag.effective_date` | date | Y | Effective Date | attribute | DATE | inferred |
| 6 | `created_at` | `clnt.compliance_flag.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 7 | `updated_at` | `clnt.compliance_flag.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |

### `clnt.election` -- UNREGISTERED -- 0 rows

**Hub**: `FUTURE` Client Hub (future)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `election_id` | `clnt.election.election_id` | uuid | N | Election Id | identifier | UUID | inferred |
| 2 | `client_id` | `clnt.election.client_id` | uuid | N | Client Id | identifier | UUID | inferred |
| 3 | `person_id` | `clnt.election.person_id` | uuid | N | Person Id | identifier | UUID | inferred |
| 4 | `plan_id` | `clnt.election.plan_id` | uuid | N | Plan Id | identifier | UUID | inferred |
| 5 | `coverage_tier` | `clnt.election.coverage_tier` | text | N | Coverage Tier | attribute | STRING | inferred |
| 6 | `effective_date` | `clnt.election.effective_date` | date | N | Effective Date | attribute | DATE | inferred |
| 7 | `created_at` | `clnt.election.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 8 | `updated_at` | `clnt.election.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |

### `clnt.external_identity_map` -- UNREGISTERED -- 0 rows

**Hub**: `FUTURE` Client Hub (future)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `external_identity_id` | `clnt.external_identity_map.external_identity_id` | uuid | N | External Identity Id | identifier | UUID | inferred |
| 2 | `client_id` | `clnt.external_identity_map.client_id` | uuid | N | Client Id | identifier | UUID | inferred |
| 3 | `entity_type` | `clnt.external_identity_map.entity_type` | text | N | Entity Type | attribute | STRING | inferred |
| 4 | `internal_id` | `clnt.external_identity_map.internal_id` | uuid | N | Internal Id | identifier | UUID | inferred |
| 5 | `vendor_id` | `clnt.external_identity_map.vendor_id` | uuid | N | Vendor Id | identifier | UUID | inferred |
| 6 | `external_id_value` | `clnt.external_identity_map.external_id_value` | text | N | External Id Value | attribute | STRING | inferred |
| 7 | `effective_date` | `clnt.external_identity_map.effective_date` | date | Y | Effective Date | attribute | DATE | inferred |
| 8 | `status` | `clnt.external_identity_map.status` | text | N | Current status of this record | attribute | ENUM | inferred |
| 9 | `created_at` | `clnt.external_identity_map.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 10 | `updated_at` | `clnt.external_identity_map.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |

### `clnt.intake_batch` -- UNREGISTERED -- 0 rows

**Hub**: `FUTURE` Client Hub (future)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `intake_batch_id` | `clnt.intake_batch.intake_batch_id` | uuid | N | Intake Batch Id | identifier | UUID | inferred |
| 2 | `client_id` | `clnt.intake_batch.client_id` | uuid | N | Client Id | identifier | UUID | inferred |
| 3 | `upload_date` | `clnt.intake_batch.upload_date` | timestamp with time zone | N | Upload Date | attribute | ISO-8601 | inferred |
| 4 | `status` | `clnt.intake_batch.status` | text | N | Current status of this record | attribute | ENUM | inferred |
| 5 | `created_at` | `clnt.intake_batch.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 6 | `updated_at` | `clnt.intake_batch.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |

### `clnt.intake_record` -- UNREGISTERED -- 0 rows

**Hub**: `FUTURE` Client Hub (future)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `intake_record_id` | `clnt.intake_record.intake_record_id` | uuid | N | Intake Record Id | identifier | UUID | inferred |
| 2 | `client_id` | `clnt.intake_record.client_id` | uuid | N | Client Id | identifier | UUID | inferred |
| 3 | `intake_batch_id` | `clnt.intake_record.intake_batch_id` | uuid | N | Intake Batch Id | identifier | UUID | inferred |
| 4 | `raw_payload` | `clnt.intake_record.raw_payload` | jsonb | N | Raw Payload | attribute | JSONB | inferred |
| 5 | `created_at` | `clnt.intake_record.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |

### `clnt.person` -- UNREGISTERED -- 0 rows

**Hub**: `FUTURE` Client Hub (future)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `person_id` | `clnt.person.person_id` | uuid | N | Person Id | identifier | UUID | inferred |
| 2 | `client_id` | `clnt.person.client_id` | uuid | N | Client Id | identifier | UUID | inferred |
| 3 | `first_name` | `clnt.person.first_name` | text | N | Person first name | attribute | STRING | inferred |
| 4 | `last_name` | `clnt.person.last_name` | text | N | Person last name | attribute | STRING | inferred |
| 5 | `ssn_hash` | `clnt.person.ssn_hash` | text | Y | Ssn Hash | attribute | STRING | inferred |
| 6 | `status` | `clnt.person.status` | text | N | Current status of this record | attribute | ENUM | inferred |
| 7 | `created_at` | `clnt.person.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 8 | `updated_at` | `clnt.person.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |

### `clnt.plan` -- UNREGISTERED -- 0 rows

**Hub**: `FUTURE` Client Hub (future)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `plan_id` | `clnt.plan.plan_id` | uuid | N | Plan Id | identifier | UUID | inferred |
| 2 | `client_id` | `clnt.plan.client_id` | uuid | N | Client Id | identifier | UUID | inferred |
| 3 | `benefit_type` | `clnt.plan.benefit_type` | text | N | Benefit Type | attribute | STRING | inferred |
| 4 | `carrier_id` | `clnt.plan.carrier_id` | text | Y | Carrier Id | identifier | STRING | inferred |
| 5 | `effective_date` | `clnt.plan.effective_date` | date | Y | Effective Date | attribute | DATE | inferred |
| 6 | `status` | `clnt.plan.status` | text | N | Current status of this record | attribute | ENUM | inferred |
| 7 | `version` | `clnt.plan.version` | integer | N | Version | attribute | INTEGER | inferred |
| 8 | `rate_ee` | `clnt.plan.rate_ee` | numeric | Y | Rate Ee | metric | NUMERIC | inferred |
| 9 | `rate_es` | `clnt.plan.rate_es` | numeric | Y | Rate Es | metric | NUMERIC | inferred |
| 10 | `rate_ec` | `clnt.plan.rate_ec` | numeric | Y | Rate Ec | metric | NUMERIC | inferred |
| 11 | `rate_fam` | `clnt.plan.rate_fam` | numeric | Y | Rate Fam | metric | NUMERIC | inferred |
| 12 | `employer_rate_ee` | `clnt.plan.employer_rate_ee` | numeric | Y | Employer Rate Ee | attribute | NUMERIC | inferred |
| 13 | `employer_rate_es` | `clnt.plan.employer_rate_es` | numeric | Y | Employer Rate Es | attribute | NUMERIC | inferred |
| 14 | `employer_rate_ec` | `clnt.plan.employer_rate_ec` | numeric | Y | Employer Rate Ec | attribute | NUMERIC | inferred |
| 15 | `employer_rate_fam` | `clnt.plan.employer_rate_fam` | numeric | Y | Employer Rate Fam | attribute | NUMERIC | inferred |
| 16 | `created_at` | `clnt.plan.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 17 | `updated_at` | `clnt.plan.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |
| 18 | `source_quote_id` | `clnt.plan.source_quote_id` | uuid | Y | Source Quote Id | identifier | UUID | inferred |

### `clnt.plan_quote` -- UNREGISTERED -- 0 rows

**Hub**: `FUTURE` Client Hub (future)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `plan_quote_id` | `clnt.plan_quote.plan_quote_id` | uuid | N | Plan Quote Id | identifier | UUID | inferred |
| 2 | `client_id` | `clnt.plan_quote.client_id` | uuid | N | Client Id | identifier | UUID | inferred |
| 3 | `benefit_type` | `clnt.plan_quote.benefit_type` | text | N | Benefit Type | attribute | STRING | inferred |
| 4 | `carrier_id` | `clnt.plan_quote.carrier_id` | text | N | Carrier Id | identifier | STRING | inferred |
| 5 | `effective_year` | `clnt.plan_quote.effective_year` | integer | N | Effective Year | attribute | INTEGER | inferred |
| 6 | `rate_ee` | `clnt.plan_quote.rate_ee` | numeric | Y | Rate Ee | metric | NUMERIC | inferred |
| 7 | `rate_es` | `clnt.plan_quote.rate_es` | numeric | Y | Rate Es | metric | NUMERIC | inferred |
| 8 | `rate_ec` | `clnt.plan_quote.rate_ec` | numeric | Y | Rate Ec | metric | NUMERIC | inferred |
| 9 | `rate_fam` | `clnt.plan_quote.rate_fam` | numeric | Y | Rate Fam | metric | NUMERIC | inferred |
| 10 | `source` | `clnt.plan_quote.source` | text | Y | Data source identifier | attribute | STRING | inferred |
| 11 | `received_date` | `clnt.plan_quote.received_date` | date | Y | Received Date | attribute | DATE | inferred |
| 12 | `status` | `clnt.plan_quote.status` | text | N | Current status of this record | attribute | ENUM | inferred |
| 13 | `created_at` | `clnt.plan_quote.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |

### `clnt.service_request` -- UNREGISTERED -- 0 rows

**Hub**: `FUTURE` Client Hub (future)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `service_request_id` | `clnt.service_request.service_request_id` | uuid | N | Service Request Id | identifier | UUID | inferred |
| 2 | `client_id` | `clnt.service_request.client_id` | uuid | N | Client Id | identifier | UUID | inferred |
| 3 | `category` | `clnt.service_request.category` | text | N | Category | attribute | STRING | inferred |
| 4 | `status` | `clnt.service_request.status` | text | N | Current status of this record | attribute | ENUM | inferred |
| 5 | `opened_at` | `clnt.service_request.opened_at` | timestamp with time zone | N | Timestamp for opened event | attribute | ISO-8601 | inferred |
| 6 | `created_at` | `clnt.service_request.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 7 | `updated_at` | `clnt.service_request.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |

### `clnt.vendor` -- UNREGISTERED -- 0 rows

**Hub**: `FUTURE` Client Hub (future)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `vendor_id` | `clnt.vendor.vendor_id` | uuid | N | Vendor Id | identifier | UUID | inferred |
| 2 | `client_id` | `clnt.vendor.client_id` | uuid | N | Client Id | identifier | UUID | inferred |
| 3 | `vendor_name` | `clnt.vendor.vendor_name` | text | N | Vendor Name | attribute | STRING | inferred |
| 4 | `vendor_type` | `clnt.vendor.vendor_type` | text | Y | Vendor Type | attribute | STRING | inferred |
| 5 | `created_at` | `clnt.vendor.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 6 | `updated_at` | `clnt.vendor.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |

### `lcs.adapter_registry` -- UNREGISTERED -- 3 rows

**Hub**: `FUTURE` Lifecycle Signals (future)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `adapter_type` | `lcs.adapter_registry.adapter_type` | text | N | Adapter Type | attribute | STRING | inferred |
| 2 | `adapter_name` | `lcs.adapter_registry.adapter_name` | text | N | Adapter Name | attribute | STRING | inferred |
| 3 | `channel` | `lcs.adapter_registry.channel` | text | N | Channel | attribute | STRING | inferred |
| 4 | `direction` | `lcs.adapter_registry.direction` | text | N | Direction | attribute | STRING | inferred |
| 5 | `description` | `lcs.adapter_registry.description` | text | Y | Description | attribute | STRING | inferred |
| 6 | `domain_rotation_config` | `lcs.adapter_registry.domain_rotation_config` | jsonb | Y | Domain Rotation Config | attribute | JSONB | inferred |
| 7 | `health_status` | `lcs.adapter_registry.health_status` | text | N | Health Status | attribute | STRING | inferred |
| 8 | `daily_cap` | `lcs.adapter_registry.daily_cap` | integer | Y | Daily Cap | attribute | INTEGER | inferred |
| 9 | `sent_today` | `lcs.adapter_registry.sent_today` | integer | N | Sent Today | attribute | INTEGER | inferred |
| 10 | `bounce_rate_24h` | `lcs.adapter_registry.bounce_rate_24h` | numeric | Y | Bounce Rate 24H | attribute | NUMERIC | inferred |
| 11 | `complaint_rate_24h` | `lcs.adapter_registry.complaint_rate_24h` | numeric | Y | Complaint Rate 24H | attribute | NUMERIC | inferred |
| 12 | `auto_pause_rules` | `lcs.adapter_registry.auto_pause_rules` | jsonb | Y | Auto Pause Rules | attribute | JSONB | inferred |
| 13 | `is_active` | `lcs.adapter_registry.is_active` | boolean | N | Whether this record active | attribute | BOOLEAN | inferred |
| 14 | `created_at` | `lcs.adapter_registry.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 15 | `updated_at` | `lcs.adapter_registry.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |

### `lcs.domain_pool` -- UNREGISTERED -- 10 rows

**Hub**: `FUTURE` Lifecycle Signals (future)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `lcs.domain_pool.id` | uuid | N | Id | identifier | UUID | inferred |
| 2 | `domain` | `lcs.domain_pool.domain` | text | N | Company website domain (lowercase, no protocol) | attribute | STRING | inferred |
| 3 | `subdomain` | `lcs.domain_pool.subdomain` | text | N | Subdomain | attribute | STRING | inferred |
| 4 | `sender_name` | `lcs.domain_pool.sender_name` | text | N | Sender Name | attribute | STRING | inferred |
| 5 | `sender_email` | `lcs.domain_pool.sender_email` | text | N | Sender Email | attribute | EMAIL | inferred |
| 6 | `status` | `lcs.domain_pool.status` | text | N | Current status of this record | attribute | ENUM | inferred |
| 7 | `warmup_day` | `lcs.domain_pool.warmup_day` | integer | N | Warmup Day | attribute | INTEGER | inferred |
| 8 | `daily_cap` | `lcs.domain_pool.daily_cap` | integer | N | Daily Cap | attribute | INTEGER | inferred |
| 9 | `sent_today` | `lcs.domain_pool.sent_today` | integer | N | Sent Today | attribute | INTEGER | inferred |
| 10 | `bounce_rate_24h` | `lcs.domain_pool.bounce_rate_24h` | numeric | N | Bounce Rate 24H | attribute | NUMERIC | inferred |
| 11 | `complaint_rate_24h` | `lcs.domain_pool.complaint_rate_24h` | numeric | N | Complaint Rate 24H | attribute | NUMERIC | inferred |
| 12 | `last_sent_at` | `lcs.domain_pool.last_sent_at` | timestamp with time zone | Y | Timestamp for last sent event | attribute | ISO-8601 | inferred |
| 13 | `last_health_check_at` | `lcs.domain_pool.last_health_check_at` | timestamp with time zone | Y | Timestamp for last health check event | attribute | ISO-8601 | inferred |
| 14 | `paused_at` | `lcs.domain_pool.paused_at` | timestamp with time zone | Y | Timestamp for paused event | attribute | ISO-8601 | inferred |
| 15 | `pause_reason` | `lcs.domain_pool.pause_reason` | text | Y | Pause Reason | attribute | STRING | inferred |
| 16 | `mailgun_verified` | `lcs.domain_pool.mailgun_verified` | boolean | N | Mailgun Verified | attribute | BOOLEAN | inferred |
| 17 | `created_at` | `lcs.domain_pool.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 18 | `updated_at` | `lcs.domain_pool.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |

### `lcs.err0` -- UNREGISTERED -- 0 rows

**Hub**: `FUTURE` Lifecycle Signals (future)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `error_id` | `lcs.err0.error_id` | uuid | N | Primary key for this error record | identifier | UUID | inferred |
| 2 | `message_run_id` | `lcs.err0.message_run_id` | text | N | Run identifier for message batch | identifier | STRING | inferred |
| 3 | `communication_id` | `lcs.err0.communication_id` | text | Y | Communication Id | identifier | STRING | inferred |
| 4 | `sovereign_company_id` | `lcs.err0.sovereign_company_id` | text | Y | FK to cl.company_identity (sovereign company identifier) | foreign_key | STRING | inferred |
| 5 | `failure_type` | `lcs.err0.failure_type` | text | N | Failure Type | attribute | STRING | inferred |
| 6 | `failure_message` | `lcs.err0.failure_message` | text | N | Failure Message | attribute | STRING | inferred |
| 7 | `lifecycle_phase` | `lcs.err0.lifecycle_phase` | text | Y | Lifecycle Phase | attribute | STRING | inferred |
| 8 | `adapter_type` | `lcs.err0.adapter_type` | text | Y | Adapter Type | attribute | STRING | inferred |
| 9 | `orbt_strike_number` | `lcs.err0.orbt_strike_number` | integer | Y | Orbt Strike Number | attribute | INTEGER | inferred |
| 10 | `orbt_action_taken` | `lcs.err0.orbt_action_taken` | text | Y | Orbt Action Taken | attribute | STRING | inferred |
| 11 | `orbt_alt_channel_eligible` | `lcs.err0.orbt_alt_channel_eligible` | boolean | Y | Orbt Alt Channel Eligible | attribute | BOOLEAN | inferred |
| 12 | `orbt_alt_channel_reason` | `lcs.err0.orbt_alt_channel_reason` | text | Y | Orbt Alt Channel Reason | attribute | STRING | inferred |
| 13 | `created_at` | `lcs.err0.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |

### `lcs.event` -- UNREGISTERED -- 0 rows

**Hub**: `FUTURE` Lifecycle Signals (future)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `communication_id` | `lcs.event.communication_id` | text | N | Communication Id | identifier | STRING | inferred |
| 2 | `message_run_id` | `lcs.event.message_run_id` | text | N | Run identifier for message batch | identifier | STRING | inferred |
| 3 | `sovereign_company_id` | `lcs.event.sovereign_company_id` | uuid | N | FK to cl.company_identity (sovereign company identifier) | foreign_key | UUID | inferred |
| 4 | `entity_type` | `lcs.event.entity_type` | text | N | Entity Type | attribute | STRING | inferred |
| 5 | `entity_id` | `lcs.event.entity_id` | uuid | N | Entity Id | identifier | UUID | inferred |
| 6 | `signal_set_hash` | `lcs.event.signal_set_hash` | text | N | Signal Set Hash | attribute | STRING | inferred |
| 7 | `frame_id` | `lcs.event.frame_id` | text | N | Frame Id | identifier | STRING | inferred |
| 8 | `adapter_type` | `lcs.event.adapter_type` | text | N | Adapter Type | attribute | STRING | inferred |
| 9 | `channel` | `lcs.event.channel` | text | N | Channel | attribute | STRING | inferred |
| 10 | `delivery_status` | `lcs.event.delivery_status` | text | N | Delivery Status | attribute | STRING | inferred |
| 11 | `lifecycle_phase` | `lcs.event.lifecycle_phase` | text | N | Lifecycle Phase | attribute | STRING | inferred |
| 12 | `event_type` | `lcs.event.event_type` | text | N | Type of audit/system event | attribute | STRING | inferred |
| 13 | `lane` | `lcs.event.lane` | text | N | Lane | attribute | STRING | inferred |
| 14 | `agent_number` | `lcs.event.agent_number` | text | N | Service agent identifier (SA-NNN format) | attribute | STRING | inferred |
| 15 | `step_number` | `lcs.event.step_number` | integer | N | Step Number | attribute | INTEGER | inferred |
| 16 | `step_name` | `lcs.event.step_name` | text | N | Step Name | attribute | STRING | inferred |
| 17 | `payload` | `lcs.event.payload` | jsonb | Y | Payload | attribute | JSONB | inferred |
| 18 | `adapter_response` | `lcs.event.adapter_response` | jsonb | Y | Adapter Response | attribute | JSONB | inferred |
| 19 | `intelligence_tier` | `lcs.event.intelligence_tier` | integer | Y | Intelligence Tier | attribute | INTEGER | inferred |
| 20 | `sender_identity` | `lcs.event.sender_identity` | text | Y | Sender Identity | attribute | STRING | inferred |
| 21 | `created_at` | `lcs.event.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |

### `lcs.event_2026_02` -- UNREGISTERED -- 0 rows

**Hub**: `FUTURE` Lifecycle Signals (future)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `communication_id` | `lcs.event_2026_02.communication_id` | text | N | Communication Id | identifier | STRING | inferred |
| 2 | `message_run_id` | `lcs.event_2026_02.message_run_id` | text | N | Run identifier for message batch | identifier | STRING | inferred |
| 3 | `sovereign_company_id` | `lcs.event_2026_02.sovereign_company_id` | uuid | N | FK to cl.company_identity (sovereign company identifier) | foreign_key | UUID | inferred |
| 4 | `entity_type` | `lcs.event_2026_02.entity_type` | text | N | Entity Type | attribute | STRING | inferred |
| 5 | `entity_id` | `lcs.event_2026_02.entity_id` | uuid | N | Entity Id | identifier | UUID | inferred |
| 6 | `signal_set_hash` | `lcs.event_2026_02.signal_set_hash` | text | N | Signal Set Hash | attribute | STRING | inferred |
| 7 | `frame_id` | `lcs.event_2026_02.frame_id` | text | N | Frame Id | identifier | STRING | inferred |
| 8 | `adapter_type` | `lcs.event_2026_02.adapter_type` | text | N | Adapter Type | attribute | STRING | inferred |
| 9 | `channel` | `lcs.event_2026_02.channel` | text | N | Channel | attribute | STRING | inferred |
| 10 | `delivery_status` | `lcs.event_2026_02.delivery_status` | text | N | Delivery Status | attribute | STRING | inferred |
| 11 | `lifecycle_phase` | `lcs.event_2026_02.lifecycle_phase` | text | N | Lifecycle Phase | attribute | STRING | inferred |
| 12 | `event_type` | `lcs.event_2026_02.event_type` | text | N | Type of audit/system event | attribute | STRING | inferred |
| 13 | `lane` | `lcs.event_2026_02.lane` | text | N | Lane | attribute | STRING | inferred |
| 14 | `agent_number` | `lcs.event_2026_02.agent_number` | text | N | Service agent identifier (SA-NNN format) | attribute | STRING | inferred |
| 15 | `step_number` | `lcs.event_2026_02.step_number` | integer | N | Step Number | attribute | INTEGER | inferred |
| 16 | `step_name` | `lcs.event_2026_02.step_name` | text | N | Step Name | attribute | STRING | inferred |
| 17 | `payload` | `lcs.event_2026_02.payload` | jsonb | Y | Payload | attribute | JSONB | inferred |
| 18 | `adapter_response` | `lcs.event_2026_02.adapter_response` | jsonb | Y | Adapter Response | attribute | JSONB | inferred |
| 19 | `intelligence_tier` | `lcs.event_2026_02.intelligence_tier` | integer | Y | Intelligence Tier | attribute | INTEGER | inferred |
| 20 | `sender_identity` | `lcs.event_2026_02.sender_identity` | text | Y | Sender Identity | attribute | STRING | inferred |
| 21 | `created_at` | `lcs.event_2026_02.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |

### `lcs.event_2026_03` -- UNREGISTERED -- 0 rows

**Hub**: `FUTURE` Lifecycle Signals (future)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `communication_id` | `lcs.event_2026_03.communication_id` | text | N | Communication Id | identifier | STRING | inferred |
| 2 | `message_run_id` | `lcs.event_2026_03.message_run_id` | text | N | Run identifier for message batch | identifier | STRING | inferred |
| 3 | `sovereign_company_id` | `lcs.event_2026_03.sovereign_company_id` | uuid | N | FK to cl.company_identity (sovereign company identifier) | foreign_key | UUID | inferred |
| 4 | `entity_type` | `lcs.event_2026_03.entity_type` | text | N | Entity Type | attribute | STRING | inferred |
| 5 | `entity_id` | `lcs.event_2026_03.entity_id` | uuid | N | Entity Id | identifier | UUID | inferred |
| 6 | `signal_set_hash` | `lcs.event_2026_03.signal_set_hash` | text | N | Signal Set Hash | attribute | STRING | inferred |
| 7 | `frame_id` | `lcs.event_2026_03.frame_id` | text | N | Frame Id | identifier | STRING | inferred |
| 8 | `adapter_type` | `lcs.event_2026_03.adapter_type` | text | N | Adapter Type | attribute | STRING | inferred |
| 9 | `channel` | `lcs.event_2026_03.channel` | text | N | Channel | attribute | STRING | inferred |
| 10 | `delivery_status` | `lcs.event_2026_03.delivery_status` | text | N | Delivery Status | attribute | STRING | inferred |
| 11 | `lifecycle_phase` | `lcs.event_2026_03.lifecycle_phase` | text | N | Lifecycle Phase | attribute | STRING | inferred |
| 12 | `event_type` | `lcs.event_2026_03.event_type` | text | N | Type of audit/system event | attribute | STRING | inferred |
| 13 | `lane` | `lcs.event_2026_03.lane` | text | N | Lane | attribute | STRING | inferred |
| 14 | `agent_number` | `lcs.event_2026_03.agent_number` | text | N | Service agent identifier (SA-NNN format) | attribute | STRING | inferred |
| 15 | `step_number` | `lcs.event_2026_03.step_number` | integer | N | Step Number | attribute | INTEGER | inferred |
| 16 | `step_name` | `lcs.event_2026_03.step_name` | text | N | Step Name | attribute | STRING | inferred |
| 17 | `payload` | `lcs.event_2026_03.payload` | jsonb | Y | Payload | attribute | JSONB | inferred |
| 18 | `adapter_response` | `lcs.event_2026_03.adapter_response` | jsonb | Y | Adapter Response | attribute | JSONB | inferred |
| 19 | `intelligence_tier` | `lcs.event_2026_03.intelligence_tier` | integer | Y | Intelligence Tier | attribute | INTEGER | inferred |
| 20 | `sender_identity` | `lcs.event_2026_03.sender_identity` | text | Y | Sender Identity | attribute | STRING | inferred |
| 21 | `created_at` | `lcs.event_2026_03.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |

### `lcs.event_2026_04` -- UNREGISTERED -- 0 rows

**Hub**: `FUTURE` Lifecycle Signals (future)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `communication_id` | `lcs.event_2026_04.communication_id` | text | N | Communication Id | identifier | STRING | inferred |
| 2 | `message_run_id` | `lcs.event_2026_04.message_run_id` | text | N | Run identifier for message batch | identifier | STRING | inferred |
| 3 | `sovereign_company_id` | `lcs.event_2026_04.sovereign_company_id` | uuid | N | FK to cl.company_identity (sovereign company identifier) | foreign_key | UUID | inferred |
| 4 | `entity_type` | `lcs.event_2026_04.entity_type` | text | N | Entity Type | attribute | STRING | inferred |
| 5 | `entity_id` | `lcs.event_2026_04.entity_id` | uuid | N | Entity Id | identifier | UUID | inferred |
| 6 | `signal_set_hash` | `lcs.event_2026_04.signal_set_hash` | text | N | Signal Set Hash | attribute | STRING | inferred |
| 7 | `frame_id` | `lcs.event_2026_04.frame_id` | text | N | Frame Id | identifier | STRING | inferred |
| 8 | `adapter_type` | `lcs.event_2026_04.adapter_type` | text | N | Adapter Type | attribute | STRING | inferred |
| 9 | `channel` | `lcs.event_2026_04.channel` | text | N | Channel | attribute | STRING | inferred |
| 10 | `delivery_status` | `lcs.event_2026_04.delivery_status` | text | N | Delivery Status | attribute | STRING | inferred |
| 11 | `lifecycle_phase` | `lcs.event_2026_04.lifecycle_phase` | text | N | Lifecycle Phase | attribute | STRING | inferred |
| 12 | `event_type` | `lcs.event_2026_04.event_type` | text | N | Type of audit/system event | attribute | STRING | inferred |
| 13 | `lane` | `lcs.event_2026_04.lane` | text | N | Lane | attribute | STRING | inferred |
| 14 | `agent_number` | `lcs.event_2026_04.agent_number` | text | N | Service agent identifier (SA-NNN format) | attribute | STRING | inferred |
| 15 | `step_number` | `lcs.event_2026_04.step_number` | integer | N | Step Number | attribute | INTEGER | inferred |
| 16 | `step_name` | `lcs.event_2026_04.step_name` | text | N | Step Name | attribute | STRING | inferred |
| 17 | `payload` | `lcs.event_2026_04.payload` | jsonb | Y | Payload | attribute | JSONB | inferred |
| 18 | `adapter_response` | `lcs.event_2026_04.adapter_response` | jsonb | Y | Adapter Response | attribute | JSONB | inferred |
| 19 | `intelligence_tier` | `lcs.event_2026_04.intelligence_tier` | integer | Y | Intelligence Tier | attribute | INTEGER | inferred |
| 20 | `sender_identity` | `lcs.event_2026_04.sender_identity` | text | Y | Sender Identity | attribute | STRING | inferred |
| 21 | `created_at` | `lcs.event_2026_04.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |

### `lcs.frame_registry` -- UNREGISTERED -- 10 rows

**Hub**: `FUTURE` Lifecycle Signals (future)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `frame_id` | `lcs.frame_registry.frame_id` | text | N | Frame Id | identifier | STRING | inferred |
| 2 | `frame_name` | `lcs.frame_registry.frame_name` | text | N | Frame Name | attribute | STRING | inferred |
| 3 | `lifecycle_phase` | `lcs.frame_registry.lifecycle_phase` | text | N | Lifecycle Phase | attribute | STRING | inferred |
| 4 | `frame_type` | `lcs.frame_registry.frame_type` | text | N | Frame Type | attribute | STRING | inferred |
| 5 | `tier` | `lcs.frame_registry.tier` | integer | N | Tier | attribute | INTEGER | inferred |
| 6 | `required_fields` | `lcs.frame_registry.required_fields` | jsonb | N | Required Fields | attribute | JSONB | inferred |
| 7 | `fallback_frame` | `lcs.frame_registry.fallback_frame` | text | Y | Fallback Frame | attribute | STRING | inferred |
| 8 | `channel` | `lcs.frame_registry.channel` | text | Y | Channel | attribute | STRING | inferred |
| 9 | `step_in_sequence` | `lcs.frame_registry.step_in_sequence` | integer | Y | Step In Sequence | attribute | INTEGER | inferred |
| 10 | `description` | `lcs.frame_registry.description` | text | Y | Description | attribute | STRING | inferred |
| 11 | `is_active` | `lcs.frame_registry.is_active` | boolean | N | Whether this record active | attribute | BOOLEAN | inferred |
| 12 | `created_at` | `lcs.frame_registry.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 13 | `updated_at` | `lcs.frame_registry.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |

### `lcs.signal_queue` -- UNREGISTERED -- 0 rows

**Hub**: `FUTURE` Lifecycle Signals (future)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `lcs.signal_queue.id` | uuid | N | Id | identifier | UUID | inferred |
| 2 | `signal_set_hash` | `lcs.signal_queue.signal_set_hash` | text | N | Signal Set Hash | attribute | STRING | inferred |
| 3 | `signal_category` | `lcs.signal_queue.signal_category` | text | N | Signal Category | attribute | STRING | inferred |
| 4 | `sovereign_company_id` | `lcs.signal_queue.sovereign_company_id` | uuid | N | FK to cl.company_identity (sovereign company identifier) | foreign_key | UUID | inferred |
| 5 | `lifecycle_phase` | `lcs.signal_queue.lifecycle_phase` | text | N | Lifecycle Phase | attribute | STRING | inferred |
| 6 | `preferred_channel` | `lcs.signal_queue.preferred_channel` | text | Y | Preferred Channel | attribute | STRING | inferred |
| 7 | `preferred_lane` | `lcs.signal_queue.preferred_lane` | text | Y | Preferred Lane | attribute | STRING | inferred |
| 8 | `agent_number` | `lcs.signal_queue.agent_number` | text | Y | Service agent identifier (SA-NNN format) | attribute | STRING | inferred |
| 9 | `signal_data` | `lcs.signal_queue.signal_data` | jsonb | N | Signal Data | attribute | JSONB | inferred |
| 10 | `source_hub` | `lcs.signal_queue.source_hub` | text | N | Source Hub | attribute | STRING | inferred |
| 11 | `source_signal_id` | `lcs.signal_queue.source_signal_id` | uuid | Y | Source Signal Id | identifier | UUID | inferred |
| 12 | `status` | `lcs.signal_queue.status` | text | N | Current status of this record | attribute | ENUM | inferred |
| 13 | `priority` | `lcs.signal_queue.priority` | integer | N | Priority | attribute | INTEGER | inferred |
| 14 | `created_at` | `lcs.signal_queue.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 15 | `processed_at` | `lcs.signal_queue.processed_at` | timestamp with time zone | Y | Timestamp for processed event | attribute | ISO-8601 | inferred |

### `lcs.signal_registry` -- UNREGISTERED -- 9 rows

**Hub**: `FUTURE` Lifecycle Signals (future)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `signal_set_hash` | `lcs.signal_registry.signal_set_hash` | text | N | Signal Set Hash | attribute | STRING | inferred |
| 2 | `signal_name` | `lcs.signal_registry.signal_name` | text | N | Signal Name | attribute | STRING | inferred |
| 3 | `lifecycle_phase` | `lcs.signal_registry.lifecycle_phase` | text | N | Lifecycle Phase | attribute | STRING | inferred |
| 4 | `signal_category` | `lcs.signal_registry.signal_category` | text | N | Signal Category | attribute | STRING | inferred |
| 5 | `description` | `lcs.signal_registry.description` | text | Y | Description | attribute | STRING | inferred |
| 6 | `data_fetched_at` | `lcs.signal_registry.data_fetched_at` | timestamp with time zone | Y | Timestamp for data fetched event | attribute | ISO-8601 | inferred |
| 7 | `data_expires_at` | `lcs.signal_registry.data_expires_at` | timestamp with time zone | Y | Timestamp for data expires event | attribute | ISO-8601 | inferred |
| 8 | `freshness_window` | `lcs.signal_registry.freshness_window` | interval | N | Freshness Window | attribute | STRING | inferred |
| 9 | `signal_validity_score` | `lcs.signal_registry.signal_validity_score` | numeric | Y | Signal Validity score | metric | NUMERIC | inferred |
| 10 | `validity_threshold` | `lcs.signal_registry.validity_threshold` | numeric | N | Validity Threshold | attribute | NUMERIC | inferred |
| 11 | `is_active` | `lcs.signal_registry.is_active` | boolean | N | Whether this record active | attribute | BOOLEAN | inferred |
| 12 | `created_at` | `lcs.signal_registry.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 13 | `updated_at` | `lcs.signal_registry.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |

### `lcs.suppression` -- UNREGISTERED -- 0 rows

**Hub**: `FUTURE` Lifecycle Signals (future)

| # | Column | Unique ID | Type | Null | Description | Role | Format | Source |
|---|--------|-----------|------|------|-------------|------|--------|--------|
| 1 | `id` | `lcs.suppression.id` | uuid | N | Id | identifier | UUID | inferred |
| 2 | `email` | `lcs.suppression.email` | text | Y | Email address | attribute | EMAIL | inferred |
| 3 | `entity_id` | `lcs.suppression.entity_id` | uuid | Y | Entity Id | identifier | UUID | inferred |
| 4 | `sovereign_company_id` | `lcs.suppression.sovereign_company_id` | uuid | Y | FK to cl.company_identity (sovereign company identifier) | foreign_key | UUID | inferred |
| 5 | `suppression_state` | `lcs.suppression.suppression_state` | text | N | Suppression State | attribute | STRING | inferred |
| 6 | `never_contact` | `lcs.suppression.never_contact` | boolean | N | Never Contact | attribute | BOOLEAN | inferred |
| 7 | `unsubscribed` | `lcs.suppression.unsubscribed` | boolean | N | Unsubscribed | attribute | BOOLEAN | inferred |
| 8 | `hard_bounced` | `lcs.suppression.hard_bounced` | boolean | N | Hard Bounced | attribute | BOOLEAN | inferred |
| 9 | `complained` | `lcs.suppression.complained` | boolean | N | Complained | attribute | BOOLEAN | inferred |
| 10 | `suppression_source` | `lcs.suppression.suppression_source` | text | N | Suppression Source | attribute | STRING | inferred |
| 11 | `source_event_id` | `lcs.suppression.source_event_id` | text | Y | Source Event Id | identifier | STRING | inferred |
| 12 | `channel` | `lcs.suppression.channel` | text | Y | Channel | attribute | STRING | inferred |
| 13 | `domain` | `lcs.suppression.domain` | text | Y | Company website domain (lowercase, no protocol) | attribute | STRING | inferred |
| 14 | `created_at` | `lcs.suppression.created_at` | timestamp with time zone | N | When this record was created | attribute | ISO-8601 | inferred |
| 15 | `updated_at` | `lcs.suppression.updated_at` | timestamp with time zone | N | When this record was last updated | attribute | ISO-8601 | inferred |
| 16 | `expires_at` | `lcs.suppression.expires_at` | timestamp with time zone | Y | When this record expires | attribute | ISO-8601 | inferred |

---

## Statistics

| Metric | Count |
|--------|-------|
| Total columns documented | 3,592 |
| From DB registries (dol/outreach/enrichment) | 1,182 |
| From column_registry.yml | 47 |
| Pattern-inferred | 2,363 |
