"""
Document ALL undocumented columns on:
  - Remaining CANONICAL tables (not frozen core)
  - SUPPORTING tables
  - ERROR tables

Safe to re-run (only adds where description is NULL).
"""
import os
import psycopg2

DATABASE_URL = os.environ["DATABASE_URL"]

COLUMN_DOCS = [
    # ========================================================================
    # BIT SCHEMA — CANONICAL TABLES
    # ========================================================================

    # bit.authorization_log — Tracks authorization decisions
    ("bit", "authorization_log", "id", "Primary key. Auto-increment ID for each authorization decision record."),
    ("bit", "authorization_log", "outreach_id", "FK to outreach.outreach. The company for which authorization was evaluated."),
    ("bit", "authorization_log", "requested_action", "The outreach action requested (e.g. send_email, phone_call, meeting_request)."),
    ("bit", "authorization_log", "requested_band", "The authorization band required for the requested action (0-5)."),
    ("bit", "authorization_log", "current_band", "The company current CLS authorization band at time of request."),
    ("bit", "authorization_log", "current_score", "The company current CLS score at time of request."),
    ("bit", "authorization_log", "authorized", "Whether the action was authorized. TRUE = band sufficient, FALSE = blocked."),
    ("bit", "authorization_log", "denial_reason", "Reason for denial if authorized=FALSE. NULL if authorized."),
    ("bit", "authorization_log", "proof_id", "FK to bit.proof_lines if Band 3+ action. The proof line used to justify authorization."),
    ("bit", "authorization_log", "proof_valid", "Whether the proof line was valid at time of authorization check."),
    ("bit", "authorization_log", "created_at", "Timestamp of the authorization decision."),
    ("bit", "authorization_log", "correlation_id", "UUID linking this authorization to the broader operation for audit trail."),

    # bit.phase_state — Tracks company phase transitions
    ("bit", "phase_state", "id", "Primary key. Auto-increment ID for each phase state record."),
    ("bit", "phase_state", "outreach_id", "FK to outreach.outreach. The company whose phase state is tracked."),
    ("bit", "phase_state", "company_unique_id", "Legacy Barton company ID. Bridge key for backward compatibility."),
    ("bit", "phase_state", "current_phase", "Current lifecycle phase of this company in the CLS system."),
    ("bit", "phase_state", "previous_phase", "Phase before the most recent transition. NULL if first phase."),
    ("bit", "phase_state", "phase_entered_at", "Timestamp when the company entered the current phase."),
    ("bit", "phase_state", "phase_source", "Source/trigger that caused the phase transition (e.g. dol_signal, people_change, blog_event)."),
    ("bit", "phase_state", "structural_pressure", "Structural Pressure domain state. From DOL signals. Highest trust."),
    ("bit", "phase_state", "decision_surface", "Decision Surface domain state. From People signals. Medium trust."),
    ("bit", "phase_state", "narrative_volatility", "Narrative Volatility domain state. From Blog signals. Lowest trust. Amplifier only."),
    ("bit", "phase_state", "convergence_count", "Number of domains currently showing movement (0-3). 3 = act."),
    ("bit", "phase_state", "is_active", "Whether this phase state is the current active state for the company."),
    ("bit", "phase_state", "created_at", "Timestamp when this phase state record was created."),
    ("bit", "phase_state", "updated_at", "Timestamp of last modification to this phase state."),
    ("bit", "phase_state", "notes", "Free text notes about this phase state or transition."),

    # bit.proof_lines — Evidence citations for Band 3+ outreach
    ("bit", "proof_lines", "proof_id", "Primary key. UUID uniquely identifying this proof line."),
    ("bit", "proof_lines", "outreach_id", "FK to outreach.outreach. The company this proof line applies to."),
    ("bit", "proof_lines", "company_unique_id", "Legacy Barton company ID. Bridge key for backward compatibility."),
    ("bit", "proof_lines", "pressure_class", "Pressure class this proof evidences. Values: COST_PRESSURE, VENDOR_DISSATISFACTION, DEADLINE_PROXIMITY, ORGANIZATIONAL_RECONFIGURATION, OPERATIONAL_CHAOS."),
    ("bit", "proof_lines", "proof_text", "The formatted proof line citation text. Required for Band 3+ messages."),
    ("bit", "proof_lines", "source_domains", "Array of source domains contributing to this proof (DOL, People, Blog)."),
    ("bit", "proof_lines", "min_band", "Minimum authorization band this proof supports. Band 3 = single-source, 4 = multi-source, 5 = full-chain."),
    ("bit", "proof_lines", "valid_from", "Timestamp when this proof line became valid. Proofs expire when movements expire."),
    ("bit", "proof_lines", "valid_until", "Timestamp when this proof line expires. Cannot be refreshed — must regenerate from current state."),
    ("bit", "proof_lines", "is_active", "Whether this proof line is currently valid and usable. FALSE after expiration."),
    ("bit", "proof_lines", "created_at", "Timestamp when this proof line was generated."),

    # ========================================================================
    # CL SCHEMA — CANONICAL TABLES (non-frozen)
    # ========================================================================

    # cl.company_domains
    ("cl", "company_domains", "id", "Primary key. Auto-increment ID."),
    ("cl", "company_domains", "sovereign_company_id", "FK to cl.company_identity. The company this domain belongs to."),
    ("cl", "company_domains", "domain", "Domain name (e.g. acme.com). No protocol prefix."),
    ("cl", "company_domains", "is_primary", "Whether this is the primary domain for the company. Only one per company should be TRUE."),
    ("cl", "company_domains", "status", "Domain status. Values: alive, dead, unknown."),
    ("cl", "company_domains", "created_at", "Timestamp when this domain record was created."),
    ("cl", "company_domains", "updated_at", "Timestamp of last modification."),

    # cl.company_domains_excluded
    ("cl", "company_domains_excluded", "id", "Primary key. Auto-increment ID."),
    ("cl", "company_domains_excluded", "sovereign_company_id", "FK to cl.company_identity_excluded. The excluded company this domain belongs to."),
    ("cl", "company_domains_excluded", "domain", "Domain name. No protocol prefix."),
    ("cl", "company_domains_excluded", "is_primary", "Whether this was the primary domain for the excluded company."),
    ("cl", "company_domains_excluded", "status", "Domain status at time of exclusion."),
    ("cl", "company_domains_excluded", "created_at", "Timestamp when this domain record was created."),
    ("cl", "company_domains_excluded", "updated_at", "Timestamp of last modification."),

    # cl.company_identity_bridge
    ("cl", "company_identity_bridge", "id", "Primary key. Auto-increment ID."),
    ("cl", "company_identity_bridge", "sovereign_company_id", "FK to cl.company_identity. The company on one side of the bridge."),
    ("cl", "company_identity_bridge", "company_unique_id", "Legacy Barton ID. Bridge key to company.company_master."),
    ("cl", "company_identity_bridge", "bridge_type", "Type of identity bridge (e.g. domain_match, name_match, ein_match)."),
    ("cl", "company_identity_bridge", "confidence", "Confidence score (0-100) for the bridge match."),
    ("cl", "company_identity_bridge", "created_at", "Timestamp when this bridge was established."),
    ("cl", "company_identity_bridge", "updated_at", "Timestamp of last modification."),

    # cl.company_identity_excluded — 24 undocumented (same structure as company_identity)
    ("cl", "company_identity_excluded", "company_fingerprint",
     "Deterministic hash of company identity attributes at time of exclusion."),
    ("cl", "company_identity_excluded", "lifecycle_run_id",
     "ID of the lifecycle processing run that evaluated this company before exclusion."),
    ("cl", "company_identity_excluded", "existence_verified",
     "Whether company existence was verified before exclusion."),
    ("cl", "company_identity_excluded", "verification_run_id",
     "ID of the verification batch that checked this company."),
    ("cl", "company_identity_excluded", "verified_at",
     "Timestamp of last verification before exclusion."),
    ("cl", "company_identity_excluded", "domain_status_code",
     "HTTP status code from domain check at time of exclusion."),
    ("cl", "company_identity_excluded", "name_match_score",
     "Fuzzy name match score at time of exclusion."),
    ("cl", "company_identity_excluded", "state_match_result",
     "State matching result at time of exclusion."),
    ("cl", "company_identity_excluded", "canonical_name",
     "Normalized company name at time of exclusion."),
    ("cl", "company_identity_excluded", "state_verified",
     "Verified state code at time of exclusion."),
    ("cl", "company_identity_excluded", "employee_count_band",
     "Employee count band at time of exclusion."),
    ("cl", "company_identity_excluded", "identity_pass",
     "Number of identity validation passes before exclusion."),
    ("cl", "company_identity_excluded", "identity_status",
     "Identity validation status at time of exclusion."),
    ("cl", "company_identity_excluded", "last_pass_at",
     "Timestamp of last successful identity pass before exclusion."),
    ("cl", "company_identity_excluded", "eligibility_status",
     "Eligibility status that led to exclusion."),
    ("cl", "company_identity_excluded", "exclusion_reason",
     "Reason for exclusion. Values: government, education, healthcare, religious, insurance, financial_services, etc."),
    ("cl", "company_identity_excluded", "entity_role",
     "Entity classification that triggered exclusion."),
    ("cl", "company_identity_excluded", "final_outcome",
     "Final eligibility determination: excluded."),
    ("cl", "company_identity_excluded", "final_reason",
     "Human-readable explanation of why this company was excluded."),
    ("cl", "company_identity_excluded", "outreach_attached_at",
     "Timestamp when outreach_id was attached, if any, before exclusion."),
    ("cl", "company_identity_excluded", "sales_opened_at",
     "Timestamp when sales opened, if any, before exclusion."),
    ("cl", "company_identity_excluded", "client_promoted_at",
     "Timestamp when client promoted, if any, before exclusion."),
    ("cl", "company_identity_excluded", "normalized_domain",
     "Normalized domain at time of exclusion."),
    ("cl", "company_identity_excluded", "state_code",
     "2-character US state code at time of exclusion."),

    # cl.company_names
    ("cl", "company_names", "id", "Primary key. Auto-increment ID."),
    ("cl", "company_names", "sovereign_company_id", "FK to cl.company_identity. The company this name variant belongs to."),
    ("cl", "company_names", "name", "A known name variant for this company (trade name, DBA, legal name)."),
    ("cl", "company_names", "source", "Source system that provided this name variant."),
    ("cl", "company_names", "created_at", "Timestamp when this name was recorded."),

    # cl.company_names_excluded
    ("cl", "company_names_excluded", "id", "Primary key. Auto-increment ID."),
    ("cl", "company_names_excluded", "sovereign_company_id", "FK to cl.company_identity_excluded. The excluded company this name belongs to."),
    ("cl", "company_names_excluded", "name", "Name variant for the excluded company."),
    ("cl", "company_names_excluded", "source", "Source system that provided this name."),
    ("cl", "company_names_excluded", "created_at", "Timestamp when this name was recorded."),

    # cl.domain_hierarchy
    ("cl", "domain_hierarchy", "id", "Primary key. Auto-increment ID."),
    ("cl", "domain_hierarchy", "parent_domain", "Parent domain in the hierarchy (e.g. acme.com)."),
    ("cl", "domain_hierarchy", "child_domain", "Child/subdomain in the hierarchy (e.g. mail.acme.com)."),
    ("cl", "domain_hierarchy", "relationship_type", "Type of domain relationship (e.g. subdomain, redirect, alias)."),
    ("cl", "domain_hierarchy", "confidence", "Confidence score (0-100) for this domain relationship."),
    ("cl", "domain_hierarchy", "source", "Source that identified this relationship."),
    ("cl", "domain_hierarchy", "created_at", "Timestamp when this relationship was identified."),
    ("cl", "domain_hierarchy", "updated_at", "Timestamp of last modification."),
    ("cl", "domain_hierarchy", "sovereign_company_id", "FK to cl.company_identity if relationship is anchored to a specific company."),

    # cl.identity_confidence
    ("cl", "identity_confidence", "id", "Primary key. Auto-increment ID."),
    ("cl", "identity_confidence", "sovereign_company_id", "FK to cl.company_identity. The company this confidence score applies to."),
    ("cl", "identity_confidence", "confidence_score", "Overall identity confidence score (0-100). Higher = more verified identity data."),
    ("cl", "identity_confidence", "factors", "JSONB or text describing the factors that contributed to the confidence score."),

    # cl.identity_confidence_excluded
    ("cl", "identity_confidence_excluded", "id", "Primary key. Auto-increment ID."),
    ("cl", "identity_confidence_excluded", "sovereign_company_id", "FK to cl.company_identity_excluded. The excluded company this confidence applies to."),
    ("cl", "identity_confidence_excluded", "confidence_score", "Identity confidence score at time of exclusion."),
    ("cl", "identity_confidence_excluded", "factors", "Factors contributing to confidence score at time of exclusion."),

    # ========================================================================
    # COVERAGE SCHEMA — CANONICAL TABLES
    # ========================================================================

    # coverage.service_agent
    ("coverage", "service_agent", "agent_name", "Name of the service agent (sales rep, account manager)."),
    ("coverage", "service_agent", "agent_number", "Numeric identifier for the agent. Used in assignment tracking."),
    ("coverage", "service_agent", "created_at", "Timestamp when this agent record was created."),

    # coverage.service_agent_coverage
    ("coverage", "service_agent_coverage", "anchor_zip", "5-digit ZIP code that defines the center of the coverage market area."),
    ("coverage", "service_agent_coverage", "radius_miles", "Radius in miles from anchor_zip that defines the coverage area boundary."),
    ("coverage", "service_agent_coverage", "states", "Array of US state codes within the coverage radius. Used for CT postal_code filtering."),
    ("coverage", "service_agent_coverage", "company_count", "Number of CT companies found within this coverage area."),
    ("coverage", "service_agent_coverage", "status", "Coverage status. Values: active, retired. Active markets are included in --list output."),
    ("coverage", "service_agent_coverage", "created_at", "Timestamp when this coverage area was first defined."),

    # ========================================================================
    # DOL SCHEMA — CANONICAL TABLES (non-frozen)
    # ========================================================================

    # dol.ein_urls — 4 undocumented
    ("dol", "ein_urls", "source", "Source that provided this EIN-to-URL mapping. Primarily: hunter_dol_enrichment."),
    ("dol", "ein_urls", "created_at", "Timestamp when this EIN-URL mapping was created."),
    ("dol", "ein_urls", "company_name", "Company name associated with this EIN from the source system."),
    ("dol", "ein_urls", "match_type", "How this EIN was matched to the URL. Values: exact, fuzzy_t1, fuzzy_t2, fuzzy_t3."),

    # dol.renewal_calendar — 13 undocumented
    ("dol", "renewal_calendar", "id", "Primary key. Auto-increment ID."),
    ("dol", "renewal_calendar", "ein", "9-digit Employer Identification Number. No dashes. Links to form_5500 via sponsor_dfe_ein."),
    ("dol", "renewal_calendar", "company_name", "Company name from the Form 5500 filing (sponsor_dfe_name)."),
    ("dol", "renewal_calendar", "plan_year_begin", "Plan year begin date from Form 5500. Determines renewal month."),
    ("dol", "renewal_calendar", "plan_year_end", "Plan year end date from Form 5500."),
    ("dol", "renewal_calendar", "renewal_month", "Month (1-12) when the benefits plan renews annually. Derived from plan_year_begin."),
    ("dol", "renewal_calendar", "outreach_start_month", "Month (1-12) to begin outreach. Calculated as renewal_month minus 5 months (wraps around)."),
    ("dol", "renewal_calendar", "filing_year", "Year of the Form 5500 filing used to derive this calendar entry."),
    ("dol", "renewal_calendar", "funding_type", "Plan funding classification. Values: fully_insured, self_funded, pension_only, unknown."),
    ("dol", "renewal_calendar", "participant_count", "Number of plan participants from the Form 5500 filing."),
    ("dol", "renewal_calendar", "domain", "Company domain if known. From dol.ein_urls bridge."),
    ("dol", "renewal_calendar", "created_at", "Timestamp when this calendar record was created."),
    ("dol", "renewal_calendar", "updated_at", "Timestamp of last modification."),

    # ========================================================================
    # SUPPORTING TABLES (non-frozen)
    # ========================================================================

    # people.people_sidecar — 2 undocumented
    ("people", "people_sidecar", "created_at", "Timestamp when this sidecar enrichment record was created."),
    ("people", "people_sidecar", "updated_at", "Timestamp of last modification to this sidecar record."),

    # people.person_scores — 8 undocumented
    ("people", "person_scores", "id", "Primary key. Auto-increment ID."),
    ("people", "person_scores", "people_id", "FK to people.people_master.people_id. The person this score applies to."),
    ("people", "person_scores", "outreach_id", "FK to outreach.outreach. The company associated with this person."),
    ("people", "person_scores", "bit_score", "Person-level CLS/BIT score. Reflects individual-level movement signals."),
    ("people", "person_scores", "confidence_score", "Confidence in the person data quality (name, email, title accuracy)."),
    ("people", "person_scores", "score_factors", "JSONB describing the factors contributing to this person score."),
    ("people", "person_scores", "created_at", "Timestamp when this person score was first created."),
    ("people", "person_scores", "updated_at", "Timestamp of last score recalculation."),

    # ========================================================================
    # ERROR TABLES
    # ========================================================================

    # people.people_invalid — 26 columns
    ("people", "people_invalid", "id", "Primary key. Auto-increment ID for the invalid person record."),
    ("people", "people_invalid", "outreach_id", "FK to outreach.outreach. The company this invalid person was associated with."),
    ("people", "people_invalid", "first_name", "First name from source. May be invalid or unverifiable."),
    ("people", "people_invalid", "last_name", "Last name from source. May be invalid or unverifiable."),
    ("people", "people_invalid", "full_name", "Full name from source."),
    ("people", "people_invalid", "title", "Job title from source."),
    ("people", "people_invalid", "email", "Email address that failed validation or verification."),
    ("people", "people_invalid", "phone", "Phone number from source."),
    ("people", "people_invalid", "linkedin_url", "LinkedIn URL from source."),
    ("people", "people_invalid", "source", "Data source that provided this record."),
    ("people", "people_invalid", "confidence_score", "Confidence score from source. Low scores may indicate invalid data."),
    ("people", "people_invalid", "email_verified", "Whether email verification was attempted."),
    ("people", "people_invalid", "outreach_ready", "Always FALSE for invalid records."),
    ("people", "people_invalid", "verification_result", "Verification result that caused invalidation (e.g. invalid, unknown)."),
    ("people", "people_invalid", "created_at", "Timestamp when this record was created."),
    ("people", "people_invalid", "updated_at", "Timestamp of last modification."),
    ("people", "people_invalid", "invalidation_reason", "Specific reason this person record was marked invalid."),
    ("people", "people_invalid", "invalidated_at", "Timestamp when the record was moved to the invalid table."),
    ("people", "people_invalid", "original_people_id", "The people_id this record had before being moved to invalid."),
    ("people", "people_invalid", "slot_type", "Slot type the person was associated with before invalidation."),
    ("people", "people_invalid", "barton_id", "Barton ID the person had before invalidation."),
    ("people", "people_invalid", "domain", "Company domain associated with this person."),
    ("people", "people_invalid", "company_name", "Company name associated with this person."),
    ("people", "people_invalid", "source_system", "Source system identifier."),
    ("people", "people_invalid", "source_record_id", "Original record ID from source system."),
    ("people", "people_invalid", "validation_status", "Validation status at time of invalidation."),

    # outreach.url_discovery_failures — 18 undocumented
    ("outreach", "url_discovery_failures", "id", "Primary key. Auto-increment ID."),
    ("outreach", "url_discovery_failures", "outreach_id", "FK to outreach.outreach. The company whose URL discovery failed."),
    ("outreach", "url_discovery_failures", "domain", "Domain that was being probed for URL discovery."),
    ("outreach", "url_discovery_failures", "url_type", "Type of URL being discovered (about_page, press_page, blog_page, etc.)."),
    ("outreach", "url_discovery_failures", "failure_reason", "Why URL discovery failed (dns_error, timeout, http_error, no_match, etc.)."),
    ("outreach", "url_discovery_failures", "http_status_code", "HTTP status code received during the discovery attempt. NULL if DNS failed."),
    ("outreach", "url_discovery_failures", "attempted_url", "The URL that was actually probed/tested."),
    ("outreach", "url_discovery_failures", "discovery_method", "Method used: sitemap, homepage_links, brute_force_probe."),
    ("outreach", "url_discovery_failures", "retry_count", "Number of times this URL discovery has been retried."),
    ("outreach", "url_discovery_failures", "max_retries", "Maximum number of retries allowed before marking as permanent failure."),
    ("outreach", "url_discovery_failures", "next_retry_at", "Timestamp of the next scheduled retry attempt."),
    ("outreach", "url_discovery_failures", "created_at", "Timestamp when this failure was first recorded."),
    ("outreach", "url_discovery_failures", "updated_at", "Timestamp of last modification."),
    ("outreach", "url_discovery_failures", "resolved", "Whether this failure has been resolved (URL found on retry). Boolean."),
    ("outreach", "url_discovery_failures", "resolved_at", "Timestamp when the failure was resolved."),
    ("outreach", "url_discovery_failures", "resolved_url", "The URL that was eventually found when the failure was resolved."),
    ("outreach", "url_discovery_failures", "error_details", "Detailed error message or stack trace from the failed attempt."),
    ("outreach", "url_discovery_failures", "correlation_id", "UUID linking to the broader operation for audit trail."),

    # cl.cl_err_existence — 18 columns
    ("cl", "cl_err_existence", "id", "Primary key. Auto-increment ID."),
    ("cl", "cl_err_existence", "sovereign_company_id", "FK to cl.company_identity. The company that failed existence verification."),
    ("cl", "cl_err_existence", "domain", "Domain that was checked for existence."),
    ("cl", "cl_err_existence", "error_type", "Type of existence verification error."),
    ("cl", "cl_err_existence", "error_message", "Human-readable error message describing the failure."),
    ("cl", "cl_err_existence", "http_status_code", "HTTP status code received during verification. NULL if DNS failed."),
    ("cl", "cl_err_existence", "dns_resolved", "Whether the domain DNS resolved successfully. Boolean."),
    ("cl", "cl_err_existence", "verification_run_id", "ID of the verification batch run that produced this error."),
    ("cl", "cl_err_existence", "retry_count", "Number of verification retries attempted."),
    ("cl", "cl_err_existence", "max_retries", "Maximum retries before marking as permanent failure."),
    ("cl", "cl_err_existence", "next_retry_at", "Timestamp of next scheduled retry."),
    ("cl", "cl_err_existence", "resolved", "Whether this error has been resolved on retry."),
    ("cl", "cl_err_existence", "resolved_at", "Timestamp when the error was resolved."),
    ("cl", "cl_err_existence", "created_at", "Timestamp when this error was first recorded."),
    ("cl", "cl_err_existence", "updated_at", "Timestamp of last modification."),
    ("cl", "cl_err_existence", "company_name", "Company name for context."),
    ("cl", "cl_err_existence", "correlation_id", "UUID linking to the broader operation for audit trail."),
    ("cl", "cl_err_existence", "severity", "Error severity level."),

    # outreach.company_target_errors — 26 undocumented
    ("outreach", "company_target_errors", "id", "Primary key. Auto-increment ID."),
    ("outreach", "company_target_errors", "outreach_id", "FK to outreach.outreach. The company that encountered the error."),
    ("outreach", "company_target_errors", "domain", "Domain being processed when error occurred."),
    ("outreach", "company_target_errors", "error_type", "Error classification type."),
    ("outreach", "company_target_errors", "error_message", "Human-readable error description."),
    ("outreach", "company_target_errors", "error_stage", "Pipeline stage where the error occurred (e.g. domain_resolution, pattern_discovery)."),
    ("outreach", "company_target_errors", "error_source", "System or component that produced the error."),
    ("outreach", "company_target_errors", "severity", "Error severity level (critical, high, medium, low)."),
    ("outreach", "company_target_errors", "retry_count", "Number of retries attempted."),
    ("outreach", "company_target_errors", "max_retries", "Maximum retries before permanent failure."),
    ("outreach", "company_target_errors", "retry_strategy", "Strategy for retry. Values: auto_retry, manual_fix, discard."),
    ("outreach", "company_target_errors", "next_retry_at", "Timestamp of next scheduled retry."),
    ("outreach", "company_target_errors", "resolved", "Whether this error has been resolved."),
    ("outreach", "company_target_errors", "resolved_at", "Timestamp of resolution."),
    ("outreach", "company_target_errors", "resolution_method", "How the error was resolved (retry_success, manual_fix, data_correction)."),
    ("outreach", "company_target_errors", "created_at", "Timestamp when error was first recorded."),
    ("outreach", "company_target_errors", "updated_at", "Timestamp of last modification."),
    ("outreach", "company_target_errors", "correlation_id", "UUID for operation audit trail."),
    ("outreach", "company_target_errors", "process_id", "ID of the pipeline process that generated this error."),
    ("outreach", "company_target_errors", "company_name", "Company name for context."),
    ("outreach", "company_target_errors", "blocking_reason", "Why this error blocks downstream processing."),
    ("outreach", "company_target_errors", "escalation_level", "Current escalation level (0=normal, 1=elevated, 2=critical)."),
    ("outreach", "company_target_errors", "failure_code", "Structured failure code for programmatic handling."),
    ("outreach", "company_target_errors", "source_system", "System that produced the error."),
    ("outreach", "company_target_errors", "raw_error", "Raw error output/stack trace."),
    ("outreach", "company_target_errors", "context_data", "JSONB with additional context about the error condition."),

    # people.people_errors — 14 undocumented
    ("people", "people_errors", "resolved", "Whether this error has been resolved. Boolean."),
    ("people", "people_errors", "resolved_at", "Timestamp when the error was resolved."),
    ("people", "people_errors", "resolution_method", "How the error was resolved."),
    ("people", "people_errors", "next_retry_at", "Timestamp of next scheduled retry."),
    ("people", "people_errors", "correlation_id", "UUID for operation audit trail."),
    ("people", "people_errors", "process_id", "ID of the pipeline process that generated this error."),
    ("people", "people_errors", "blocking_reason", "Why this error blocks downstream processing."),
    ("people", "people_errors", "escalation_level", "Current escalation level."),
    ("people", "people_errors", "failure_code", "Structured failure code."),
    ("people", "people_errors", "source_system", "System that produced the error."),
    ("people", "people_errors", "raw_error", "Raw error output/stack trace."),
    ("people", "people_errors", "context_data", "JSONB with additional context."),
    ("people", "people_errors", "parked_at", "Timestamp when error was parked (deferred for later review)."),
    ("people", "people_errors", "archived_at", "Timestamp when error was archived (no longer actionable)."),

    # outreach.dol_errors — 14 undocumented
    ("outreach", "dol_errors", "resolved", "Whether this error has been resolved."),
    ("outreach", "dol_errors", "resolved_at", "Timestamp of resolution."),
    ("outreach", "dol_errors", "resolution_method", "How the error was resolved."),
    ("outreach", "dol_errors", "next_retry_at", "Timestamp of next scheduled retry."),
    ("outreach", "dol_errors", "correlation_id", "UUID for operation audit trail."),
    ("outreach", "dol_errors", "process_id", "ID of the pipeline process that generated this error."),
    ("outreach", "dol_errors", "blocking_reason", "Why this error blocks downstream DOL processing."),
    ("outreach", "dol_errors", "escalation_level", "Current escalation level."),
    ("outreach", "dol_errors", "failure_code", "Structured failure code."),
    ("outreach", "dol_errors", "source_system", "System that produced the error."),
    ("outreach", "dol_errors", "raw_error", "Raw error output/stack trace."),
    ("outreach", "dol_errors", "context_data", "JSONB with additional context."),
    ("outreach", "dol_errors", "parked_at", "Timestamp when error was parked."),
    ("outreach", "dol_errors", "archived_at", "Timestamp when error was archived."),

    # outreach.blog_errors — 15 undocumented
    ("outreach", "blog_errors", "id", "Primary key. Auto-increment ID."),
    ("outreach", "blog_errors", "outreach_id", "FK to outreach.outreach. The company that encountered the blog error."),
    ("outreach", "blog_errors", "domain", "Domain being processed for blog content."),
    ("outreach", "blog_errors", "error_type", "Error classification. Values: BLOG_MISSING, extraction_failure, timeout, etc."),
    ("outreach", "blog_errors", "error_message", "Human-readable error description."),
    ("outreach", "blog_errors", "error_stage", "Pipeline stage where error occurred."),
    ("outreach", "blog_errors", "severity", "Error severity level."),
    ("outreach", "blog_errors", "retry_count", "Number of retries attempted."),
    ("outreach", "blog_errors", "max_retries", "Maximum retries before permanent failure."),
    ("outreach", "blog_errors", "retry_strategy", "Strategy for retry. Values: auto_retry, manual_fix, discard."),
    ("outreach", "blog_errors", "resolved", "Whether this error has been resolved."),
    ("outreach", "blog_errors", "resolved_at", "Timestamp of resolution."),
    ("outreach", "blog_errors", "created_at", "Timestamp when error was first recorded."),
    ("outreach", "blog_errors", "updated_at", "Timestamp of last modification."),
    ("outreach", "blog_errors", "correlation_id", "UUID for operation audit trail."),

    # outreach.bit_errors — 12 undocumented
    ("outreach", "bit_errors", "id", "Primary key. Auto-increment ID."),
    ("outreach", "bit_errors", "outreach_id", "FK to outreach.outreach. The company that encountered the CLS scoring error."),
    ("outreach", "bit_errors", "error_type", "Error classification type."),
    ("outreach", "bit_errors", "error_message", "Human-readable error description."),
    ("outreach", "bit_errors", "error_stage", "Pipeline stage where the scoring error occurred."),
    ("outreach", "bit_errors", "severity", "Error severity level."),
    ("outreach", "bit_errors", "retry_count", "Number of retries attempted."),
    ("outreach", "bit_errors", "max_retries", "Maximum retries before permanent failure."),
    ("outreach", "bit_errors", "resolved", "Whether this error has been resolved."),
    ("outreach", "bit_errors", "resolved_at", "Timestamp of resolution."),
    ("outreach", "bit_errors", "created_at", "Timestamp when error was first recorded."),
    ("outreach", "bit_errors", "updated_at", "Timestamp of last modification."),

    # outreach.people_errors — 14 undocumented
    ("outreach", "people_errors", "id", "Primary key. Auto-increment ID."),
    ("outreach", "people_errors", "outreach_id", "FK to outreach.outreach. The company that encountered the people processing error."),
    ("outreach", "people_errors", "error_type", "Error classification type."),
    ("outreach", "people_errors", "error_message", "Human-readable error description."),
    ("outreach", "people_errors", "error_stage", "Pipeline stage where the people error occurred."),
    ("outreach", "people_errors", "severity", "Error severity level."),
    ("outreach", "people_errors", "retry_count", "Number of retries attempted."),
    ("outreach", "people_errors", "max_retries", "Maximum retries before permanent failure."),
    ("outreach", "people_errors", "resolved", "Whether this error has been resolved."),
    ("outreach", "people_errors", "resolved_at", "Timestamp of resolution."),
    ("outreach", "people_errors", "created_at", "Timestamp when error was first recorded."),
    ("outreach", "people_errors", "updated_at", "Timestamp of last modification."),
    ("outreach", "people_errors", "correlation_id", "UUID for operation audit trail."),
    ("outreach", "people_errors", "domain", "Company domain for context."),

    # outreach.outreach_errors — 9 undocumented
    ("outreach", "outreach_errors", "id", "Primary key. Auto-increment ID."),
    ("outreach", "outreach_errors", "outreach_id", "FK to outreach.outreach. The outreach spine record that encountered the error."),
    ("outreach", "outreach_errors", "error_type", "Error classification type."),
    ("outreach", "outreach_errors", "error_message", "Human-readable error description."),
    ("outreach", "outreach_errors", "error_stage", "Pipeline stage where the spine error occurred."),
    ("outreach", "outreach_errors", "severity", "Error severity level."),
    ("outreach", "outreach_errors", "resolved", "Whether this error has been resolved."),
    ("outreach", "outreach_errors", "created_at", "Timestamp when error was first recorded."),
    ("outreach", "outreach_errors", "updated_at", "Timestamp of last modification."),

    # cl.cl_errors_archive — 13 undocumented
    ("cl", "cl_errors_archive", "sovereign_company_id", "FK to cl.company_identity. The company associated with this archived error."),
    ("cl", "cl_errors_archive", "domain", "Company domain for context."),
    ("cl", "cl_errors_archive", "error_message", "Human-readable error description."),
    ("cl", "cl_errors_archive", "error_stage", "Processing stage where the error occurred."),
    ("cl", "cl_errors_archive", "severity", "Error severity level."),
    ("cl", "cl_errors_archive", "retry_count", "Number of retries at time of archival."),
    ("cl", "cl_errors_archive", "resolved", "Whether error was resolved before archival."),
    ("cl", "cl_errors_archive", "resolved_at", "Timestamp of resolution if resolved."),
    ("cl", "cl_errors_archive", "created_at", "Timestamp when error was first recorded."),
    ("cl", "cl_errors_archive", "updated_at", "Timestamp of last modification before archival."),
    ("cl", "cl_errors_archive", "archived_at", "Timestamp when this error was moved to the archive."),
    ("cl", "cl_errors_archive", "correlation_id", "UUID for operation audit trail."),
    ("cl", "cl_errors_archive", "company_name", "Company name for context."),
]


def run():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    added = 0
    skipped = 0
    errors = []

    for schema, table, column, description in COLUMN_DOCS:
        cur.execute("""
            SELECT d.description
            FROM information_schema.columns c
            LEFT JOIN pg_catalog.pg_description d
                ON d.objoid = (quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass
                AND d.objsubid = c.ordinal_position
            WHERE c.table_schema = %s AND c.table_name = %s AND c.column_name = %s
        """, (schema, table, column))
        row = cur.fetchone()

        if row is None:
            errors.append(f"Column not found: {schema}.{table}.{column}")
            continue

        if row[0]:
            skipped += 1
            continue

        try:
            cur.execute(
                f'COMMENT ON COLUMN "{schema}"."{table}"."{column}" IS %s',
                (description,)
            )
            added += 1
        except Exception as e:
            errors.append(f"Error on {schema}.{table}.{column}: {e}")
            conn.rollback()

    conn.commit()

    print(f"RESULTS: {added} added, {skipped} already documented, {len(errors)} errors")
    if errors:
        print(f"\nErrors:")
        for err in errors:
            print(f"  {err}")

    # Verification
    print(f"\n{'='*80}")
    print("VERIFICATION")
    print(f"{'='*80}")

    for leaf_type in ['CANONICAL', 'SUPPORTING', 'ERROR']:
        cur.execute("""
            SELECT table_schema, table_name
            FROM ctb.table_registry
            WHERE leaf_type = %s
            ORDER BY table_schema, table_name
        """, (leaf_type,))
        tables = cur.fetchall()

        print(f"\n  {leaf_type} TABLES:")
        type_total = 0
        type_documented = 0

        for schema, table in tables:
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(d.description) as documented
                FROM information_schema.columns c
                LEFT JOIN pg_catalog.pg_description d
                    ON d.objoid = (quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass
                    AND d.objsubid = c.ordinal_position
                WHERE c.table_schema = %s AND c.table_name = %s
            """, (schema, table))
            total, documented = cur.fetchone()
            type_total += total
            type_documented += documented
            pct = 100 * documented / total if total > 0 else 0
            status = "DONE" if pct == 100 else f"{pct:.0f}%"
            print(f"    {status:6}  {schema}.{table:40}  {documented}/{total}")

        pct = 100 * type_documented / type_total if type_total > 0 else 0
        print(f"    SUBTOTAL: {type_documented}/{type_total} ({pct:.1f}%)")

    cur.close()
    conn.close()


if __name__ == "__main__":
    run()
