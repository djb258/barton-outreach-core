"""
Final batch: Document ALL remaining undocumented columns across
CANONICAL, SUPPORTING, and ERROR tables.
Uses exact column names from database introspection.
"""
import os
import psycopg2

DATABASE_URL = os.environ["DATABASE_URL"]

COLUMN_DOCS = [
    # ========================================================================
    # BIT CANONICAL TABLES
    # ========================================================================

    # bit.authorization_log (5 gaps)
    ("bit", "authorization_log", "log_id",
     "Primary key. UUID uniquely identifying this authorization decision."),
    ("bit", "authorization_log", "company_unique_id",
     "Legacy Barton company ID. Identifies the company for which authorization was evaluated."),
    ("bit", "authorization_log", "actual_band",
     "The actual CLS authorization band at the time of the request (0-5)."),
    ("bit", "authorization_log", "requested_at",
     "Timestamp when the authorization request was made."),
    ("bit", "authorization_log", "requested_by",
     "Identifier of the system or user that requested authorization."),

    # bit.phase_state (11 gaps)
    ("bit", "phase_state", "current_band",
     "Current CLS authorization band (0-5) for this company. Determines permitted outreach actions."),
    ("bit", "phase_state", "phase_status",
     "Status of the current phase. Values indicate whether the company is in active movement or stasis."),
    ("bit", "phase_state", "dol_active",
     "Whether the DOL (Structural Pressure) domain is currently showing movement. Boolean."),
    ("bit", "phase_state", "people_active",
     "Whether the People (Decision Surface) domain is currently showing movement. Boolean."),
    ("bit", "phase_state", "blog_active",
     "Whether the Blog (Narrative Volatility) domain is currently showing movement. Boolean."),
    ("bit", "phase_state", "primary_pressure",
     "Primary pressure class driving this phase. Values: COST_PRESSURE, VENDOR_DISSATISFACTION, DEADLINE_PROXIMITY, ORGANIZATIONAL_RECONFIGURATION, OPERATIONAL_CHAOS."),
    ("bit", "phase_state", "aligned_domains",
     "Number of domains currently aligned in movement (0-3). 1=noise, 2=watch, 3=act."),
    ("bit", "phase_state", "last_movement_at",
     "Timestamp of the most recent movement signal detected for this company."),
    ("bit", "phase_state", "last_band_change_at",
     "Timestamp when the authorization band last changed for this company."),
    ("bit", "phase_state", "stasis_start",
     "Timestamp when the company entered stasis (no movement detected)."),
    ("bit", "phase_state", "stasis_years",
     "Number of years the company has been in stasis. Calculated from stasis_start."),

    # bit.proof_lines (7 gaps)
    ("bit", "proof_lines", "band",
     "Authorization band this proof supports. 3=single-source, 4=multi-source, 5=full-chain."),
    ("bit", "proof_lines", "sources",
     "Array of source domains contributing to this proof (e.g. ARRAY['DOL','People','Blog'])."),
    ("bit", "proof_lines", "evidence",
     "JSONB containing the structured evidence for this proof line. Includes specific metrics and citations."),
    ("bit", "proof_lines", "movement_ids",
     "Array of movement event IDs that this proof references. Links to bit.movement_events."),
    ("bit", "proof_lines", "human_readable",
     "Formatted proof line text for inclusion in outreach messages. Required at Band 3+."),
    ("bit", "proof_lines", "generated_at",
     "Timestamp when this proof line was generated from movement events."),
    ("bit", "proof_lines", "generated_by",
     "System or process that generated this proof line."),

    # ========================================================================
    # CL CANONICAL TABLES
    # ========================================================================

    # cl.company_domains (6 gaps)
    ("cl", "company_domains", "domain_id",
     "Primary key. UUID uniquely identifying this domain record."),
    ("cl", "company_domains", "company_unique_id",
     "FK to cl.company_identity.sovereign_company_id. The company this domain belongs to."),
    ("cl", "company_domains", "domain_health",
     "Domain health status. Values: LIVE (responding), DEAD (unreachable), UNKNOWN (not yet checked)."),
    ("cl", "company_domains", "mx_present",
     "Whether MX DNS records exist for this domain. TRUE = can receive email."),
    ("cl", "company_domains", "domain_name_confidence",
     "Confidence score (0-100) that this domain correctly belongs to the company. 0 = unverified."),
    ("cl", "company_domains", "checked_at",
     "Timestamp of the most recent domain health check."),

    # cl.company_domains_excluded (6 gaps)
    ("cl", "company_domains_excluded", "domain_id",
     "Primary key. UUID uniquely identifying this excluded domain record."),
    ("cl", "company_domains_excluded", "company_unique_id",
     "FK to cl.company_identity_excluded. The excluded company this domain belongs to."),
    ("cl", "company_domains_excluded", "domain_health",
     "Domain health status at time of exclusion. Values: LIVE, DEAD, UNKNOWN."),
    ("cl", "company_domains_excluded", "mx_present",
     "Whether MX records existed at time of exclusion."),
    ("cl", "company_domains_excluded", "domain_name_confidence",
     "Domain-company match confidence at time of exclusion."),
    ("cl", "company_domains_excluded", "checked_at",
     "Timestamp of last domain check before exclusion."),

    # cl.company_identity_bridge (7 gaps)
    ("cl", "company_identity_bridge", "bridge_id",
     "Primary key. UUID uniquely identifying this identity bridge."),
    ("cl", "company_identity_bridge", "source_company_id",
     "Company ID from the source system (e.g. Barton ID format 04.04.01.YY.NNNNN.NNN)."),
    ("cl", "company_identity_bridge", "company_sov_id",
     "FK to cl.company_identity.sovereign_company_id. The sovereign identity this source ID maps to."),
    ("cl", "company_identity_bridge", "source_system",
     "Source system that provided the source_company_id. Values: clay, hunter, apollo, manual."),
    ("cl", "company_identity_bridge", "minted_at",
     "Timestamp when this bridge mapping was created."),
    ("cl", "company_identity_bridge", "minted_by",
     "Pipeline or user that created this bridge (e.g. nc_pipeline, manual)."),
    ("cl", "company_identity_bridge", "lifecycle_run_id",
     "ID of the lifecycle processing run that created this bridge."),

    # cl.company_identity_excluded (1 gap)
    ("cl", "company_identity_excluded", "sovereign_company_id",
     "Original sovereign_company_id from cl.company_identity before exclusion. May be NULL if excluded pre-minting."),

    # cl.company_names (4 gaps)
    ("cl", "company_names", "name_id",
     "Primary key. UUID uniquely identifying this company name variant."),
    ("cl", "company_names", "company_unique_id",
     "FK to cl.company_identity.sovereign_company_id. The company this name belongs to."),
    ("cl", "company_names", "name_value",
     "The actual name text (trade name, DBA, legal name, canonical form)."),
    ("cl", "company_names", "name_type",
     "Classification of this name variant. Values: canonical (normalized), legal, trade, dba, source_raw."),

    # cl.company_names_excluded (4 gaps)
    ("cl", "company_names_excluded", "name_id",
     "Primary key. UUID for this excluded company name."),
    ("cl", "company_names_excluded", "company_unique_id",
     "FK to cl.company_identity_excluded. The excluded company this name belongs to."),
    ("cl", "company_names_excluded", "name_value",
     "The actual name text at time of exclusion."),
    ("cl", "company_names_excluded", "name_type",
     "Name type classification at time of exclusion."),

    # cl.domain_hierarchy (6 gaps)
    ("cl", "domain_hierarchy", "hierarchy_id",
     "Primary key. UUID uniquely identifying this domain hierarchy relationship."),
    ("cl", "domain_hierarchy", "domain",
     "The domain being classified in the hierarchy."),
    ("cl", "domain_hierarchy", "parent_company_id",
     "FK to cl.company_identity. The parent company in the hierarchy. NULL if unknown."),
    ("cl", "domain_hierarchy", "child_company_id",
     "FK to cl.company_identity. The child company in the hierarchy. NULL if unknown."),
    ("cl", "domain_hierarchy", "confidence_score",
     "Confidence (0-100) in this hierarchy relationship."),
    ("cl", "domain_hierarchy", "resolution_method",
     "How this hierarchy was determined. Values: ENTITY_ROLE_PRESET, DOMAIN_ANALYSIS, MANUAL."),

    # cl.identity_confidence (3 gaps)
    ("cl", "identity_confidence", "company_unique_id",
     "FK to cl.company_identity.sovereign_company_id. The company this confidence score applies to."),
    ("cl", "identity_confidence", "confidence_bucket",
     "Confidence classification bucket. Values: HIGH, MEDIUM, LOW, UNVERIFIED."),
    ("cl", "identity_confidence", "computed_at",
     "Timestamp when this confidence score was last computed."),

    # cl.identity_confidence_excluded (3 gaps)
    ("cl", "identity_confidence_excluded", "company_unique_id",
     "FK to cl.company_identity_excluded. The excluded company."),
    ("cl", "identity_confidence_excluded", "confidence_bucket",
     "Confidence bucket at time of exclusion."),
    ("cl", "identity_confidence_excluded", "computed_at",
     "Timestamp of last confidence computation before exclusion."),

    # ========================================================================
    # COVERAGE + DOL SUPPORTING/CANONICAL
    # ========================================================================

    # coverage.service_agent_coverage (5 gaps)
    ("coverage", "service_agent_coverage", "service_agent_id",
     "FK to coverage.service_agent. The agent assigned to this coverage area."),
    ("coverage", "service_agent_coverage", "created_by",
     "User or system that created this coverage definition."),
    ("coverage", "service_agent_coverage", "retired_at",
     "Timestamp when this coverage area was retired. NULL if still active."),
    ("coverage", "service_agent_coverage", "retired_by",
     "User or system that retired this coverage area."),
    ("coverage", "service_agent_coverage", "notes",
     "Free text notes about this coverage area (e.g. 'Dallas metro test run')."),

    # dol.ein_urls (4 gaps)
    ("dol", "ein_urls", "city",
     "City associated with this EIN from DOL filing data."),
    ("dol", "ein_urls", "state",
     "State code associated with this EIN from DOL filing data."),
    ("dol", "ein_urls", "discovered_at",
     "Timestamp when this EIN-URL mapping was discovered or created."),
    ("dol", "ein_urls", "normalized_domain",
     "Domain after normalization (lowercase, no www/protocol). Used for canonical matching."),

    # dol.renewal_calendar (10 gaps)
    ("dol", "renewal_calendar", "renewal_id",
     "Primary key. UUID uniquely identifying this renewal calendar entry."),
    ("dol", "renewal_calendar", "company_unique_id",
     "Company identifier linking to the outreach system. Text format Barton ID."),
    ("dol", "renewal_calendar", "schedule_id",
     "FK to dol.schedule_a if this renewal has associated Schedule A data."),
    ("dol", "renewal_calendar", "filing_id",
     "FK to dol.form_5500 filing that this renewal was derived from."),
    ("dol", "renewal_calendar", "renewal_year",
     "Year of the upcoming renewal (e.g. 2026). Derived from plan year."),
    ("dol", "renewal_calendar", "renewal_date",
     "Exact date of the renewal. Derived from plan_year_begin in Form 5500."),
    ("dol", "renewal_calendar", "plan_name",
     "Name of the benefits plan from Form 5500 filing."),
    ("dol", "renewal_calendar", "carrier_name",
     "Insurance carrier name from Schedule A, if known."),
    ("dol", "renewal_calendar", "is_upcoming",
     "Whether this renewal is in the future. TRUE = upcoming, FALSE = past."),
    ("dol", "renewal_calendar", "days_until_renewal",
     "Number of days until renewal date. Negative if past. Used for outreach timing."),

    # people.person_scores (2 gaps)
    ("people", "person_scores", "person_unique_id",
     "Legacy Barton person ID. Links to people.people_master via barton_id."),
    ("people", "person_scores", "calculated_at",
     "Timestamp when this person score was last calculated."),

    # ========================================================================
    # ERROR TABLES
    # ========================================================================

    # cl.cl_err_existence (14 gaps)
    ("cl", "cl_err_existence", "error_id",
     "Primary key. UUID uniquely identifying this existence verification error."),
    ("cl", "cl_err_existence", "company_unique_id",
     "FK to cl.company_identity. The company that failed existence verification."),
    ("cl", "cl_err_existence", "company_domain",
     "Domain that was checked for existence."),
    ("cl", "cl_err_existence", "linkedin_company_url",
     "Company LinkedIn URL at time of error, if available."),
    ("cl", "cl_err_existence", "reason_code",
     "Structured error code. Values: DOMAIN_FAIL, NAME_MISMATCH, STATE_MISMATCH, etc."),
    ("cl", "cl_err_existence", "domain_status_code",
     "HTTP status code received during domain verification. NULL if DNS failed."),
    ("cl", "cl_err_existence", "domain_redirect_chain",
     "Array of redirect URLs encountered during domain verification."),
    ("cl", "cl_err_existence", "domain_final_url",
     "Final URL after following all redirects during verification."),
    ("cl", "cl_err_existence", "domain_error",
     "Error message from the domain verification attempt."),
    ("cl", "cl_err_existence", "extracted_name",
     "Company name extracted from the domain during verification."),
    ("cl", "cl_err_existence", "name_match_score",
     "Fuzzy match score (0-100) between extracted_name and expected company_name."),
    ("cl", "cl_err_existence", "extracted_state",
     "State code extracted from the domain during verification."),
    ("cl", "cl_err_existence", "state_match_result",
     "Result of state matching. Values: MATCH, SOFT_FAIL, HARD_FAIL."),
    ("cl", "cl_err_existence", "evidence",
     "JSONB with additional verification evidence and metadata."),

    # cl.cl_errors_archive (10 gaps)
    ("cl", "cl_errors_archive", "error_id",
     "Primary key. UUID of the archived error."),
    ("cl", "cl_errors_archive", "company_unique_id",
     "FK to cl.company_identity. The company associated with this archived error."),
    ("cl", "cl_errors_archive", "lifecycle_run_id",
     "ID of the lifecycle processing run that produced this error."),
    ("cl", "cl_errors_archive", "pass_name",
     "Name of the processing pass where the error occurred (e.g. collision, existence)."),
    ("cl", "cl_errors_archive", "failure_reason_code",
     "Structured failure code (e.g. COLLISION_DOMAIN, NAME_MISMATCH)."),
    ("cl", "cl_errors_archive", "inputs_snapshot",
     "JSONB snapshot of the input data at time of error."),
    ("cl", "cl_errors_archive", "archive_reason",
     "Reason for archiving this error (e.g. EXPECTED_HIERARCHY, RESOLVED)."),
    ("cl", "cl_errors_archive", "final_outcome",
     "Final outcome of the error resolution."),
    ("cl", "cl_errors_archive", "final_reason",
     "Human-readable reason for the final outcome."),
    ("cl", "cl_errors_archive", "error_type",
     "Error classification type. NOT NULL. Values per CHECK constraint."),

    # outreach.bit_errors (8 gaps)
    ("outreach", "bit_errors", "error_id",
     "Primary key. UUID uniquely identifying this CLS scoring error."),
    ("outreach", "bit_errors", "pipeline_stage",
     "Pipeline stage where the scoring error occurred (e.g. signal_collection, score_calculation)."),
    ("outreach", "bit_errors", "failure_code",
     "Structured failure code for programmatic error handling."),
    ("outreach", "bit_errors", "blocking_reason",
     "Why this error blocks downstream CLS scoring."),
    ("outreach", "bit_errors", "correlation_id",
     "UUID linking to the broader operation for audit trail."),
    ("outreach", "bit_errors", "process_id",
     "UUID of the pipeline process that generated this error."),
    ("outreach", "bit_errors", "raw_input",
     "JSONB snapshot of the input data that caused the error."),
    ("outreach", "bit_errors", "stack_trace",
     "Python stack trace from the error for debugging."),

    # outreach.blog_errors (10 gaps)
    ("outreach", "blog_errors", "error_id",
     "Primary key. UUID uniquely identifying this blog processing error."),
    ("outreach", "blog_errors", "pipeline_stage",
     "Pipeline stage where the error occurred (e.g. ingest, extraction, analysis)."),
    ("outreach", "blog_errors", "failure_code",
     "Structured failure code (e.g. BLOG-I-UPSTREAM-FAIL)."),
    ("outreach", "blog_errors", "blocking_reason",
     "Why this error blocks downstream blog content processing."),
    ("outreach", "blog_errors", "retry_allowed",
     "Whether this error is eligible for automatic retry. FALSE = permanent failure."),
    ("outreach", "blog_errors", "resolution_note",
     "Free text note about how this error was resolved, if resolved."),
    ("outreach", "blog_errors", "raw_input",
     "JSONB snapshot of the input that caused the error."),
    ("outreach", "blog_errors", "stack_trace",
     "Python stack trace for debugging."),
    ("outreach", "blog_errors", "process_id",
     "UUID of the pipeline process that generated this error."),
    ("outreach", "blog_errors", "requeue_attempts",
     "Number of times this error has been requeued for retry."),

    # outreach.company_target_errors (15 gaps)
    ("outreach", "company_target_errors", "error_id",
     "Primary key. UUID uniquely identifying this company target error."),
    ("outreach", "company_target_errors", "pipeline_stage",
     "Pipeline stage where error occurred (e.g. domain_resolution, pattern_discovery)."),
    ("outreach", "company_target_errors", "retry_allowed",
     "Whether this error is eligible for automatic retry."),
    ("outreach", "company_target_errors", "resolution_note",
     "Note about how this error was resolved."),
    ("outreach", "company_target_errors", "raw_input",
     "JSONB snapshot of input data that caused the error."),
    ("outreach", "company_target_errors", "stack_trace",
     "Python stack trace for debugging."),
    ("outreach", "company_target_errors", "imo_stage",
     "IMO processing stage: I (Ingress), M (Middle), O (Output)."),
    ("outreach", "company_target_errors", "requeue_attempts",
     "Number of times this error has been requeued for retry."),
    ("outreach", "company_target_errors", "archived_at",
     "Timestamp when error was archived (no longer actionable)."),
    ("outreach", "company_target_errors", "parked_at",
     "Timestamp when error was parked (deferred for later review)."),
    ("outreach", "company_target_errors", "parked_by",
     "User or system that parked this error."),
    ("outreach", "company_target_errors", "park_reason",
     "Reason for parking (e.g. NO_MX_RECORD - Domain has no valid MX, unfixable by enrichment)."),
    ("outreach", "company_target_errors", "escalated_at",
     "Timestamp when error was escalated to a higher priority."),
    ("outreach", "company_target_errors", "last_retry_at",
     "Timestamp of the most recent retry attempt."),
    ("outreach", "company_target_errors", "retry_exhausted",
     "Whether all retry attempts have been exhausted. Boolean."),

    # outreach.dol_errors (11 gaps)
    ("outreach", "dol_errors", "error_id",
     "Primary key. UUID uniquely identifying this DOL processing error."),
    ("outreach", "dol_errors", "outreach_id",
     "FK to outreach.outreach. The company that encountered the DOL error."),
    ("outreach", "dol_errors", "pipeline_stage",
     "Pipeline stage where the DOL error occurred."),
    ("outreach", "dol_errors", "severity",
     "Error severity. Values: WARNING, ERROR, CRITICAL."),
    ("outreach", "dol_errors", "retry_allowed",
     "Whether this error is eligible for automatic retry."),
    ("outreach", "dol_errors", "created_at",
     "Timestamp when this DOL error was first recorded."),
    ("outreach", "dol_errors", "resolution_note",
     "Note about error resolution."),
    ("outreach", "dol_errors", "raw_input",
     "JSONB snapshot of input data."),
    ("outreach", "dol_errors", "stack_trace",
     "Python stack trace for debugging."),
    ("outreach", "dol_errors", "requeue_attempts",
     "Number of requeue attempts."),
    ("outreach", "dol_errors", "error_type",
     "Error classification type. NOT NULL. Per CHECK constraint."),

    # outreach.outreach_errors (6 gaps)
    ("outreach", "outreach_errors", "error_id",
     "Primary key. UUID uniquely identifying this outreach spine error."),
    ("outreach", "outreach_errors", "company_unique_id",
     "Legacy Barton company ID for the company that encountered the error."),
    ("outreach", "outreach_errors", "pipeline_stage",
     "Pipeline stage where the spine error occurred."),
    ("outreach", "outreach_errors", "failure_code",
     "Structured failure code for programmatic handling."),
    ("outreach", "outreach_errors", "details",
     "Free text error details and context."),
    ("outreach", "outreach_errors", "run_id",
     "ID of the pipeline run that generated this error."),

    # outreach.people_errors (9 gaps)
    ("outreach", "people_errors", "error_id",
     "Primary key. UUID uniquely identifying this people processing error."),
    ("outreach", "people_errors", "pipeline_stage",
     "Pipeline stage where the people error occurred."),
    ("outreach", "people_errors", "failure_code",
     "Structured failure code for programmatic handling."),
    ("outreach", "people_errors", "blocking_reason",
     "Why this error blocks downstream people processing."),
    ("outreach", "people_errors", "retry_allowed",
     "Whether this error is eligible for automatic retry."),
    ("outreach", "people_errors", "resolution_note",
     "Note about error resolution."),
    ("outreach", "people_errors", "raw_input",
     "JSONB snapshot of input data that caused the error."),
    ("outreach", "people_errors", "stack_trace",
     "Python stack trace for debugging."),
    ("outreach", "people_errors", "requeue_attempts",
     "Number of requeue attempts."),

    # outreach.url_discovery_failures (12 gaps)
    ("outreach", "url_discovery_failures", "failure_id",
     "Primary key. UUID uniquely identifying this URL discovery failure."),
    ("outreach", "url_discovery_failures", "company_unique_id",
     "Legacy Barton company ID for the company whose URL discovery failed."),
    ("outreach", "url_discovery_failures", "website_url",
     "The company website URL that was being probed."),
    ("outreach", "url_discovery_failures", "last_attempt_at",
     "Timestamp of the most recent discovery attempt."),
    ("outreach", "url_discovery_failures", "archived_at",
     "Timestamp when this failure was archived."),
    ("outreach", "url_discovery_failures", "parked_at",
     "Timestamp when this failure was parked for deferred review."),
    ("outreach", "url_discovery_failures", "parked_by",
     "User or system that parked this failure."),
    ("outreach", "url_discovery_failures", "park_reason",
     "Reason for parking this failure."),
    ("outreach", "url_discovery_failures", "escalation_level",
     "Current escalation level (0=normal, 1=elevated, 2=critical)."),
    ("outreach", "url_discovery_failures", "escalated_at",
     "Timestamp when this failure was escalated."),
    ("outreach", "url_discovery_failures", "last_retry_at",
     "Timestamp of the most recent retry attempt."),
    ("outreach", "url_discovery_failures", "retry_exhausted",
     "Whether all retry attempts have been exhausted."),

    # people.people_errors (10 gaps)
    ("people", "people_errors", "error_id",
     "Primary key. UUID uniquely identifying this people sub-hub error."),
    ("people", "people_errors", "created_at",
     "Timestamp when this error was first recorded."),
    ("people", "people_errors", "last_updated_at",
     "Timestamp of last modification to this error record."),
    ("people", "people_errors", "retry_count",
     "Number of retry attempts made so far."),
    ("people", "people_errors", "max_retries",
     "Maximum number of retries allowed before exhaustion."),
    ("people", "people_errors", "parked_by",
     "User or system that parked this error."),
    ("people", "people_errors", "park_reason",
     "Reason for parking this error."),
    ("people", "people_errors", "escalated_at",
     "Timestamp when this error was escalated."),
    ("people", "people_errors", "last_retry_at",
     "Timestamp of the most recent retry attempt."),
    ("people", "people_errors", "retry_exhausted",
     "Whether all retry attempts have been exhausted. Boolean."),

    # people.people_invalid (14 gaps)
    ("people", "people_invalid", "unique_id",
     "Primary key. Text identifier for this invalid person record."),
    ("people", "people_invalid", "company_unique_id",
     "Legacy Barton company ID associated with this invalid person."),
    ("people", "people_invalid", "city",
     "City associated with this person from source data."),
    ("people", "people_invalid", "state",
     "State code associated with this person from source data."),
    ("people", "people_invalid", "reason_code",
     "Structured reason why this person was marked invalid (e.g. name validation failure)."),
    ("people", "people_invalid", "validation_errors",
     "JSONB array of specific validation errors that caused invalidation."),
    ("people", "people_invalid", "validation_warnings",
     "JSONB array of validation warnings (non-blocking issues)."),
    ("people", "people_invalid", "failed_at",
     "Timestamp when validation failed for this person."),
    ("people", "people_invalid", "reviewed",
     "Whether this invalid record has been manually reviewed. Boolean."),
    ("people", "people_invalid", "batch_id",
     "ID of the processing batch that produced this invalid record."),
    ("people", "people_invalid", "source_table",
     "Original source table this record came from (e.g. marketing.people_raw_wv)."),
    ("people", "people_invalid", "promoted_to",
     "Target table if this record was later promoted after correction. NULL if still invalid."),
    ("people", "people_invalid", "promoted_at",
     "Timestamp when this record was promoted after correction."),
    ("people", "people_invalid", "enrichment_data",
     "JSONB with supplemental enrichment data collected for this person."),
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
            errors.append(f"NOT FOUND: {schema}.{table}.{column}")
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
            errors.append(f"ERROR: {schema}.{table}.{column}: {e}")
            conn.rollback()

    conn.commit()

    print(f"RESULTS: {added} added, {skipped} skipped, {len(errors)} errors")
    if errors:
        for err in errors:
            print(f"  {err}")

    # Final verification
    print(f"\n{'='*80}")
    print("FINAL COVERAGE - CANONICAL + SUPPORTING + ERROR")
    print(f"{'='*80}")

    grand_total = 0
    grand_documented = 0

    for leaf_type in ['CANONICAL', 'SUPPORTING', 'ERROR']:
        cur.execute("""
            SELECT table_schema, table_name
            FROM ctb.table_registry
            WHERE leaf_type = %s
            ORDER BY table_schema, table_name
        """, (leaf_type,))
        tables = cur.fetchall()

        type_total = 0
        type_documented = 0

        print(f"\n  {leaf_type}:")
        for schema, table in tables:
            cur.execute("""
                SELECT COUNT(*), COUNT(d.description)
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

        grand_total += type_total
        grand_documented += type_documented
        pct = 100 * type_documented / type_total if type_total > 0 else 0
        print(f"    SUBTOTAL: {type_documented}/{type_total} ({pct:.1f}%)")

    pct = 100 * grand_documented / grand_total if grand_total > 0 else 0
    print(f"\n  GRAND TOTAL: {grand_documented}/{grand_total} ({pct:.1f}%)")

    cur.close()
    conn.close()


if __name__ == "__main__":
    run()
