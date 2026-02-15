"""
Batch 2: Document remaining undocumented columns on frozen core tables.
Uses exact column names from database introspection.
"""
import os
import psycopg2

DATABASE_URL = os.environ["DATABASE_URL"]

COLUMN_DOCS = [
    # ========================================================================
    # cl.company_identity — 24 undocumented columns
    # ========================================================================
    ("cl", "company_identity", "company_fingerprint",
     "Deterministic hash of company identity attributes. Used for deduplication detection across source systems."),
    ("cl", "company_identity", "lifecycle_run_id",
     "ID of the lifecycle processing run that last evaluated this company. Links to batch processing audit trail."),
    ("cl", "company_identity", "existence_verified",
     "Whether this company has been verified to exist (domain alive, business active). FALSE = not yet checked or verification failed."),
    ("cl", "company_identity", "verification_run_id",
     "ID of the verification batch run that last checked this company existence."),
    ("cl", "company_identity", "verified_at",
     "Timestamp when company existence was last verified."),
    ("cl", "company_identity", "domain_status_code",
     "HTTP status code from domain verification check. 200 = alive. 4xx/5xx = potential issues. NULL = not yet checked."),
    ("cl", "company_identity", "name_match_score",
     "Fuzzy match score (0-100) comparing company_name against DOL sponsor name. Used during EIN bridge building."),
    ("cl", "company_identity", "state_match_result",
     "Result of state-level geographic matching. Values describe whether company state matches DOL filing state."),
    ("cl", "company_identity", "canonical_name",
     "Normalized company name after standardization (lowercase, stripped of Inc/LLC/Corp suffixes). Used for fuzzy matching."),
    ("cl", "company_identity", "state_verified",
     "Verified US state code after geographic validation. May differ from original state if source data was corrected."),
    ("cl", "company_identity", "employee_count_band",
     "Binned employee count range (e.g. 1-10, 11-50, 51-200, 201-500, 500+). Derived from employee_count for segmentation."),
    ("cl", "company_identity", "identity_pass",
     "Number of times this company has passed CL identity validation. Incremented on each successful pass. 0 = never passed."),
    ("cl", "company_identity", "identity_status",
     "Current CL identity validation status. Values: PENDING (awaiting check), PASS (eligible), FAIL (blocked). Default: PENDING."),
    ("cl", "company_identity", "last_pass_at",
     "Timestamp of the most recent successful identity validation pass."),
    ("cl", "company_identity", "eligibility_status",
     "Commercial eligibility determination. Indicates whether this entity is a valid commercial target for outreach."),
    ("cl", "company_identity", "exclusion_reason",
     "Reason for exclusion if entity is non-commercial. Values: government, education, healthcare, religious, insurance, etc. NULL if eligible."),
    ("cl", "company_identity", "entity_role",
     "Entity classification role. Distinguishes commercial businesses from non-commercial entities."),
    ("cl", "company_identity", "final_outcome",
     "Final eligibility determination after all validation passes. Summarizes the end result of identity processing."),
    ("cl", "company_identity", "final_reason",
     "Human-readable reason for the final_outcome. Explains why a company was included or excluded."),
    ("cl", "company_identity", "outreach_attached_at",
     "Timestamp when outreach_id was written to this CL record. Marks when Outreach hub claimed this company."),
    ("cl", "company_identity", "sales_opened_at",
     "Timestamp when sales_process_id was written to this CL record. Marks when Sales hub claimed this company."),
    ("cl", "company_identity", "client_promoted_at",
     "Timestamp when client_id was written to this CL record. Marks when Client hub claimed this company."),
    ("cl", "company_identity", "normalized_domain",
     "Domain after normalization (lowercase, stripped of www/protocol). Used as the canonical domain for matching and deduplication."),
    ("cl", "company_identity", "state_code",
     "2-character US state abbreviation. Fixed-width CHAR(2). Used for geographic filtering in coverage runs."),

    # ========================================================================
    # outreach.company_target — 5 undocumented columns
    # ========================================================================
    ("outreach", "company_target", "method_type",
     "Email pattern discovery method subtype. Provides detail beyond email_method. Values: hunter_api, pattern_match, manual_entry."),
    ("outreach", "company_target", "confidence_score",
     "Confidence score (0-100) for the email pattern derived for this company. Higher = more reliable pattern."),
    ("outreach", "company_target", "execution_status",
     "Pipeline execution status for this company target. Values: pending, processing, completed, failed. Default: pending."),
    ("outreach", "company_target", "imo_completed_at",
     "Timestamp when IMO (Ingress-Middle-Output) pipeline processing completed for this company target."),
    ("outreach", "company_target", "is_catchall",
     "Whether this domain is a catch-all (accepts all emails). TRUE = risky for email verification. Default: FALSE."),

    # ========================================================================
    # outreach.dol — 1 undocumented column
    # ========================================================================
    ("outreach", "dol", "url_enrichment_data",
     "JSONB blob containing supplemental URL enrichment data from Hunter DOL enrichment pipeline. Stores raw API response metadata."),

    # ========================================================================
    # outreach.blog — 5 undocumented columns
    # ========================================================================
    ("outreach", "blog", "context_timestamp",
     "Timestamp when the content at source_url was last fetched or extracted."),
    ("outreach", "blog", "about_url",
     "Direct URL to the company About Us page. Denormalized from company.company_source_urls for quick access."),
    ("outreach", "blog", "news_url",
     "Direct URL to the company News/Press page. Denormalized from company.company_source_urls for quick access."),
    ("outreach", "blog", "extraction_method",
     "Method used to extract content. Values: sitemap, homepage_links, brute_force_probe, manual."),
    ("outreach", "blog", "last_extracted_at",
     "Timestamp of the most recent content extraction attempt for this company."),

    # ========================================================================
    # outreach.bit_scores — 2 undocumented columns
    # ========================================================================
    ("outreach", "bit_scores", "last_signal_at",
     "Timestamp of the most recent movement signal that contributed to this score."),
    ("outreach", "bit_scores", "last_scored_at",
     "Timestamp when the CLS score was last recalculated for this company."),

    # ========================================================================
    # people.people_master — 13 undocumented columns
    # ========================================================================
    ("people", "people_master", "work_phone_e164",
     "Work phone number in E.164 international format (e.g. +12125551234). Standardized for dialing."),
    ("people", "people_master", "personal_phone_e164",
     "Personal phone number in E.164 international format. Rarely populated. Use work_phone_e164 for outreach."),
    ("people", "people_master", "facebook_url",
     "Facebook profile URL from source system. Low fill rate. Not used for outreach."),
    ("people", "people_master", "bio",
     "Person biography or professional summary from source system. Free text."),
    ("people", "people_master", "skills",
     "Array of professional skills from source system (e.g. ARRAY[finance, accounting, leadership]). TEXT[]."),
    ("people", "people_master", "education",
     "Education history or highest degree from source system. Free text."),
    ("people", "people_master", "certifications",
     "Array of professional certifications (e.g. ARRAY[CPA, CFP, SHRM-CP]). TEXT[]."),
    ("people", "people_master", "source_system",
     "Source system that provided this person record. NOT NULL. Values: hunter, clay, apollo, manual. More specific than source column."),
    ("people", "people_master", "source_record_id",
     "Original record ID from the source system. Used for deduplication and tracing back to source data."),
    ("people", "people_master", "validation_status",
     "Current validation status of this person record. Tracks whether data has been verified for accuracy."),
    ("people", "people_master", "last_verified_at",
     "Timestamp of the most recent data verification for this person. Default: now() at creation."),
    ("people", "people_master", "last_enrichment_attempt",
     "Timestamp of the most recent enrichment attempt (e.g. Hunter API call) for this person."),
    ("people", "people_master", "outreach_ready_at",
     "Timestamp when outreach_ready was set to TRUE. NULL if never verified as outreach-ready."),

    # ========================================================================
    # people.company_slot — 5 undocumented columns
    # ========================================================================
    ("people", "company_slot", "company_unique_id",
     "Legacy Barton company ID (text). NOT NULL. Bridge key to company.company_master. NOT a UUID."),
    ("people", "company_slot", "person_unique_id",
     "Legacy Barton person ID (text). Bridge key to legacy person records. NULL if slot is unfilled."),
    ("people", "company_slot", "filled_at",
     "Timestamp when a person was assigned to this slot (is_filled set to TRUE). NULL if never filled."),
    ("people", "company_slot", "confidence_score",
     "Confidence score (0-100) for the person-to-slot assignment. Higher = stronger title-to-slot match."),
    ("people", "company_slot", "source_system",
     "Source system that provided the person filling this slot. Values: hunter, clay, apollo, manual."),
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
            print(f"  ADDED  {schema}.{table}.{column}")
        except Exception as e:
            errors.append(f"Error on {schema}.{table}.{column}: {e}")
            conn.rollback()

    conn.commit()

    print(f"\n{'='*80}")
    print(f"RESULTS: {added} added, {skipped} already documented, {len(errors)} errors")
    print(f"{'='*80}")
    for err in errors:
        print(f"  ERROR: {err}")

    # Final verification
    print(f"\n{'='*80}")
    print("FINAL VERIFICATION - Frozen Core Tables")
    print(f"{'='*80}")

    frozen_tables = [
        ("cl", "company_identity"),
        ("outreach", "outreach"),
        ("outreach", "company_target"),
        ("outreach", "dol"),
        ("outreach", "blog"),
        ("outreach", "people"),
        ("outreach", "bit_scores"),
        ("people", "people_master"),
        ("people", "company_slot"),
    ]

    total_cols = 0
    total_documented = 0

    for schema, table in frozen_tables:
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
        total_cols += total
        total_documented += documented
        pct = 100 * documented / total if total > 0 else 0
        status = "DONE" if pct == 100 else f"{pct:.0f}%"
        print(f"  {status:6}  {schema}.{table:30}  {documented}/{total}")

        # Show any remaining gaps
        if pct < 100:
            cur.execute("""
                SELECT c.column_name
                FROM information_schema.columns c
                LEFT JOIN pg_catalog.pg_description d
                    ON d.objoid = (quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass
                    AND d.objsubid = c.ordinal_position
                WHERE c.table_schema = %s AND c.table_name = %s
                  AND d.description IS NULL
                ORDER BY c.ordinal_position
            """, (schema, table))
            gaps = [r[0] for r in cur.fetchall()]
            if gaps:
                print(f"         GAPS: {', '.join(gaps)}")

    pct = 100 * total_documented / total_cols if total_cols > 0 else 0
    print(f"\n  TOTAL: {total_documented}/{total_cols} columns documented ({pct:.1f}%)")

    cur.close()
    conn.close()


if __name__ == "__main__":
    run()
