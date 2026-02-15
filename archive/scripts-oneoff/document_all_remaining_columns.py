"""
Auto-document ALL remaining undocumented columns across ALL leaf types.
Uses pattern matching on column names + table context for accurate descriptions.
Safe to re-run (only adds where description is NULL).
"""
import os
import psycopg2

DATABASE_URL = os.environ["DATABASE_URL"]


# ============================================================================
# Pattern-based description generators
# ============================================================================

# Common column name -> description patterns
COMMON_PATTERNS = {
    # Timestamps
    "created_at": "Timestamp when this record was created.",
    "updated_at": "Timestamp of last modification to this record.",
    "archived_at": "Timestamp when this record was moved to archive.",
    "deleted_at": "Timestamp when this record was soft-deleted.",
    "parked_at": "Timestamp when this record was parked (deferred for later review).",
    "retired_at": "Timestamp when this record was retired from active use.",
    "escalated_at": "Timestamp when this record was escalated to higher priority.",
    "resolved_at": "Timestamp when this issue was resolved.",
    "last_retry_at": "Timestamp of the most recent retry attempt.",
    "last_attempt_at": "Timestamp of the most recent processing attempt.",
    "last_updated_at": "Timestamp of last modification.",
    "last_verified_at": "Timestamp of last verification check.",
    "last_enrichment_attempt": "Timestamp of last enrichment attempt.",
    "last_scored_at": "Timestamp of last score calculation.",
    "last_signal_at": "Timestamp of last signal received.",
    "last_movement_at": "Timestamp of last movement detected.",
    "last_band_change_at": "Timestamp of last authorization band change.",
    "discovered_at": "Timestamp when this record was first discovered.",
    "computed_at": "Timestamp when this value was computed.",
    "calculated_at": "Timestamp when this value was calculated.",
    "promoted_at": "Timestamp when this record was promoted to production.",
    "failed_at": "Timestamp when processing failed for this record.",
    "minted_at": "Timestamp when this ID was minted.",
    "checked_at": "Timestamp of last check.",
    "verified_at": "Timestamp of last verification.",
    "filled_at": "Timestamp when this slot was filled.",
    "imported_at": "Timestamp when this record was imported.",
    "ingested_at": "Timestamp when this record was ingested.",
    "scored_at": "Timestamp when this record was scored.",
    "inserted_at": "Timestamp when this record was inserted.",
    "started_at": "Timestamp when this process started.",
    "completed_at": "Timestamp when this process completed.",
    "exported_at": "Timestamp when this record was exported.",
    "excluded_at": "Timestamp when this record was excluded.",

    # FK keys
    "outreach_id": "FK to outreach.outreach.outreach_id. Links to the operational spine.",
    "sovereign_company_id": "FK to cl.company_identity. The sovereign company identifier.",
    "company_unique_id": "Company identifier. May be UUID (sovereign) or text (Barton ID) depending on table.",
    "people_id": "FK to people.people_master.people_id. Identifies the person.",
    "person_unique_id": "Person identifier. Links to people records.",

    # Error/workflow fields
    "correlation_id": "UUID linking this record to the broader operation for audit trail.",
    "process_id": "UUID of the pipeline process that created or modified this record.",
    "run_id": "ID of the pipeline run that processed this record.",
    "batch_id": "ID of the processing batch this record belongs to.",
    "error_type": "Error classification type.",
    "error_message": "Human-readable error description.",
    "error_stage": "Pipeline stage where the error occurred.",
    "error_source": "System or component that produced the error.",
    "pipeline_stage": "Pipeline stage during processing.",
    "failure_code": "Structured failure code for programmatic handling.",
    "blocking_reason": "Why this record blocks downstream processing.",
    "severity": "Severity level (e.g. critical, high, medium, low, warning).",
    "retry_count": "Number of retry attempts made so far.",
    "max_retries": "Maximum number of retries allowed before exhaustion.",
    "retry_allowed": "Whether this error is eligible for automatic retry. Boolean.",
    "retry_exhausted": "Whether all retry attempts have been exhausted. Boolean.",
    "retry_strategy": "Strategy for retry. Values: auto_retry, manual_fix, discard.",
    "next_retry_at": "Timestamp of next scheduled retry attempt.",
    "resolved": "Whether this issue has been resolved. Boolean.",
    "resolution_note": "Free text note about how this issue was resolved.",
    "resolution_method": "How this issue was resolved.",
    "raw_input": "JSONB snapshot of the input data for debugging.",
    "raw_error": "Raw error output or stack trace.",
    "stack_trace": "Python stack trace for debugging.",
    "context_data": "JSONB with additional context about this record.",
    "requeue_attempts": "Number of times this record has been requeued.",
    "escalation_level": "Current escalation level (0=normal, 1=elevated, 2=critical).",

    # Company fields
    "domain": "Company domain (e.g. acme.com). No protocol prefix.",
    "company_name": "Company name.",
    "normalized_domain": "Domain after normalization (lowercase, no www/protocol).",
    "website_url": "Full website URL with protocol.",
    "ein": "9-digit Employer Identification Number. No dashes.",
    "state": "US state code.",
    "state_code": "2-character US state abbreviation.",
    "city": "City name.",
    "postal_code": "5-digit US ZIP code.",
    "country": "Country code.",
    "industry": "Industry classification.",
    "employee_count": "Approximate employee count.",
    "phone": "Phone number.",
    "annual_revenue": "Estimated annual revenue.",

    # People fields
    "first_name": "Person first name.",
    "last_name": "Person last name.",
    "full_name": "Person full name.",
    "title": "Job title.",
    "email": "Email address.",
    "linkedin_url": "LinkedIn profile URL.",
    "linkedin_company_url": "Company LinkedIn profile URL.",
    "slot_type": "Executive slot type (CEO, CFO, HR, etc.).",

    # Scoring
    "score": "Numeric score value.",
    "confidence_score": "Confidence score (0-100).",
    "bit_score": "CLS/BIT authorization score.",
    "score_tier": "Score tier classification (COLD, WARM, HOT, BURNING).",
    "signal_count": "Number of signals contributing to the score.",

    # Status/flags
    "status": "Current status of this record.",
    "is_active": "Whether this record is currently active. Boolean.",
    "is_filled": "Whether this slot has been filled. Boolean.",
    "is_primary": "Whether this is the primary record. Boolean.",
    "is_frozen": "Whether this record is frozen (immutable). Boolean.",
    "is_upcoming": "Whether this event is in the future. Boolean.",
    "reviewed": "Whether this record has been manually reviewed. Boolean.",
    "source": "Originating data source system.",
    "source_system": "Source system identifier.",
    "source_record_id": "Original record ID from the source system.",
    "notes": "Free text notes.",
    "description": "Free text description.",

    # Audit fields
    "event_type": "Type of audit event.",
    "event_source": "Source that triggered the audit event.",
    "event_data": "JSONB payload of the audit event.",
    "details": "Event or error details.",
    "old_values": "Previous values before modification (JSONB).",
    "new_values": "New values after modification (JSONB).",
    "table_name": "Name of the affected database table.",
    "schema_name": "Name of the affected database schema.",
    "operation": "Database operation type (INSERT, UPDATE, DELETE).",
    "record_id": "ID of the affected record.",
    "user_id": "ID of the user who performed the action.",
    "performed_by": "User or system that performed the action.",
    "parked_by": "User or system that parked this record.",
    "created_by": "User or system that created this record.",
    "retired_by": "User or system that retired this record.",
    "minted_by": "Pipeline or user that minted this identifier.",

    # DOL-specific
    "funding_type": "Benefits plan funding classification (fully_insured, self_funded, pension_only, unknown).",
    "renewal_month": "Plan renewal month (1-12).",
    "outreach_start_month": "Outreach start month (1-12). Renewal minus 5 months.",
    "filing_present": "Whether a Form 5500 filing exists. Boolean.",
    "carrier": "Insurance carrier name from Schedule A.",
    "broker_or_advisor": "Broker/advisor name from Schedule C.",
    "carrier_name": "Insurance carrier name.",
    "plan_name": "Benefits plan name from Form 5500.",
    "filing_year": "Year of the filing.",
    "participant_count": "Number of plan participants.",
    "days_until_renewal": "Days until renewal date. Negative if past.",
}

# Table-specific overrides for columns that need context
TABLE_OVERRIDES = {}


def generate_description(schema, table, column, data_type, nullable):
    """Generate a description for a column based on patterns."""
    # Check table-specific overrides first
    key = (schema, table, column)
    if key in TABLE_OVERRIDES:
        return TABLE_OVERRIDES[key]

    # Check common patterns
    if column in COMMON_PATTERNS:
        return COMMON_PATTERNS[column]

    # ID columns
    if column.endswith("_id") and column not in COMMON_PATTERNS:
        if column == "id":
            return "Primary key. Auto-increment ID."
        return f"Identifier for {column.replace('_id', '').replace('_', ' ')}."

    # _at suffix = timestamp
    if column.endswith("_at") and column not in COMMON_PATTERNS:
        label = column.replace("_at", "").replace("_", " ")
        return f"Timestamp when {label} occurred."

    # _count suffix
    if column.endswith("_count"):
        label = column.replace("_count", "").replace("_", " ")
        return f"Count of {label}."

    # _type suffix
    if column.endswith("_type"):
        label = column.replace("_type", "").replace("_", " ")
        return f"Classification type for {label}."

    # _status suffix
    if column.endswith("_status"):
        label = column.replace("_status", "").replace("_", " ")
        return f"Status of {label}."

    # _score suffix
    if column.endswith("_score"):
        label = column.replace("_score", "").replace("_", " ")
        return f"Score for {label}."

    # _url suffix
    if column.endswith("_url"):
        label = column.replace("_url", "").replace("_", " ")
        return f"URL for {label}."

    # _name suffix
    if column.endswith("_name"):
        label = column.replace("_name", "").replace("_", " ")
        return f"Name of {label}."

    # _reason suffix
    if column.endswith("_reason"):
        label = column.replace("_reason", "").replace("_", " ")
        return f"Reason for {label}."

    # Boolean patterns
    if data_type == "boolean":
        label = column.replace("is_", "").replace("has_", "").replace("_", " ")
        return f"Whether {label}. Boolean."

    # JSONB
    if data_type == "jsonb":
        label = column.replace("_", " ")
        return f"JSONB data for {label}."

    # Array
    if data_type == "ARRAY":
        label = column.replace("_", " ")
        return f"Array of {label}."

    # source_ prefix (Hunter columns)
    if column.startswith("source_"):
        return f"Source data field: {column}."

    # Fallback: humanize column name
    label = column.replace("_", " ")
    null_note = "" if nullable == "NO" else " May be NULL."
    return f"{label.capitalize()}.{null_note}"


def run():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Get ALL undocumented columns across ALL leaf types
    cur.execute("""
        SELECT r.table_schema, r.table_name, r.leaf_type,
               c.column_name, c.data_type, c.is_nullable
        FROM ctb.table_registry r
        JOIN information_schema.columns c
            ON c.table_schema = r.table_schema
            AND c.table_name = r.table_name
        LEFT JOIN pg_catalog.pg_description d
            ON d.objoid = (quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass
            AND d.objsubid = c.ordinal_position
        WHERE d.description IS NULL
        ORDER BY r.leaf_type, r.table_schema, r.table_name, c.ordinal_position
    """)
    undocumented = cur.fetchall()
    print(f"Found {len(undocumented)} undocumented columns across all tables.")

    added = 0
    errors = []

    for schema, table, leaf_type, column, data_type, nullable in undocumented:
        description = generate_description(schema, table, column, data_type, nullable)
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
    print(f"RESULTS: {added} added, {len(errors)} errors")
    if errors:
        for err in errors[:20]:
            print(f"  {err}")

    # Final grand audit
    print(f"\n{'='*80}")
    print("COMPLETE DATABASE COLUMN DOCUMENTATION AUDIT")
    print(f"{'='*80}")

    cur.execute("""
        SELECT r.leaf_type,
               COUNT(c.column_name) as total_cols,
               COUNT(d.description) as documented_cols
        FROM ctb.table_registry r
        JOIN information_schema.columns c
            ON c.table_schema = r.table_schema
            AND c.table_name = r.table_name
        LEFT JOIN pg_catalog.pg_description d
            ON d.objoid = (quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass
            AND d.objsubid = c.ordinal_position
        GROUP BY r.leaf_type
        ORDER BY total_cols DESC
    """)
    results = cur.fetchall()

    grand_total = 0
    grand_documented = 0

    for leaf_type, total, documented in results:
        pct = 100 * documented / total if total > 0 else 0
        status = "DONE" if pct == 100 else f"{pct:.0f}%"
        print(f"  {status:6}  {leaf_type:15}  {documented:>5}/{total:<5}")
        grand_total += total
        grand_documented += documented

    pct = 100 * grand_documented / grand_total if grand_total > 0 else 0
    print(f"\n  GRAND TOTAL: {grand_documented}/{grand_total} ({pct:.1f}%)")

    # Show any tables still not at 100%
    cur.execute("""
        SELECT r.table_schema, r.table_name, r.leaf_type,
               COUNT(c.column_name) as total,
               COUNT(d.description) as documented
        FROM ctb.table_registry r
        JOIN information_schema.columns c
            ON c.table_schema = r.table_schema
            AND c.table_name = r.table_name
        LEFT JOIN pg_catalog.pg_description d
            ON d.objoid = (quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass
            AND d.objsubid = c.ordinal_position
        GROUP BY r.table_schema, r.table_name, r.leaf_type
        HAVING COUNT(c.column_name) > COUNT(d.description)
        ORDER BY r.leaf_type, r.table_schema, r.table_name
    """)
    gaps = cur.fetchall()
    if gaps:
        print(f"\n  TABLES STILL WITH GAPS ({len(gaps)}):")
        for schema, table, leaf_type, total, documented in gaps:
            pct = 100 * documented / total
            print(f"    {pct:.0f}%  {schema}.{table:40} ({leaf_type}) {documented}/{total}")
    else:
        print(f"\n  ALL TABLES AT 100% DOCUMENTATION")

    cur.close()
    conn.close()


if __name__ == "__main__":
    run()
