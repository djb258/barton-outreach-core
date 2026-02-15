"""
Document all columns on the 9 frozen core tables.
Adds pg_description COMMENT ON COLUMN for every undocumented column.
Safe to re-run (only adds where description is NULL).
"""
import os
import psycopg2

DATABASE_URL = os.environ["DATABASE_URL"]

# ============================================================================
# Column descriptions for all 9 frozen core tables
# Format: (schema, table, column, description)
# ============================================================================

COLUMN_DOCS = [
    # ========================================================================
    # cl.company_identity — Authority registry (identity pointers only)
    # ========================================================================
    ("cl", "company_identity", "sovereign_company_id",
     "CTB_CONTRACT: Primary key. Immutable UUID minted by CL. One per company, forever. All hubs reference this."),
    ("cl", "company_identity", "company_name",
     "Legal or trade name of the company as received from the originating source system."),
    ("cl", "company_identity", "domain",
     "Primary web domain (e.g. acme.com). Used for domain-level deduplication. No protocol prefix."),
    ("cl", "company_identity", "source",
     "Originating source system that first introduced this company. Values: hunter_dol_enrichment, clay_import, clay, fractional_cfo_outreach, orphan_mint, barton_appointments, apollo_import, MANUAL_OUTREACH_2026."),
    ("cl", "company_identity", "outreach_id",
     "CTB_CONTRACT: Write-once pointer to outreach.outreach.outreach_id. Minted by Outreach hub, registered here ONCE. NULL means not yet claimed by Outreach."),
    ("cl", "company_identity", "sales_process_id",
     "CTB_CONTRACT: Write-once pointer to Sales hub. Minted by Sales, registered here ONCE. NULL means not yet in sales pipeline."),
    ("cl", "company_identity", "client_id",
     "CTB_CONTRACT: Write-once pointer to Client hub. Minted by Client, registered here ONCE. NULL means not yet a client."),
    ("cl", "company_identity", "lifecycle_state",
     "Current lifecycle phase of the company across all hubs. Derived from which hub IDs are populated."),
    ("cl", "company_identity", "created_at",
     "Timestamp when this company was first registered in the CL authority registry."),
    ("cl", "company_identity", "updated_at",
     "Timestamp of last modification to this CL record."),
    ("cl", "company_identity", "status",
     "CL gate status. PASS = eligible for downstream processing. PENDING/FAIL = blocked from waterfall."),
    ("cl", "company_identity", "linkedin_company_url",
     "Company LinkedIn profile URL. Source: Clay import or manual enrichment. ~48% fill rate."),
    ("cl", "company_identity", "state",
     "US state code (2-letter) where the company is headquartered or registered."),
    ("cl", "company_identity", "city",
     "City where the company is headquartered or registered."),
    ("cl", "company_identity", "postal_code",
     "5-digit US ZIP code for the company location. Used by coverage run system for geographic market definition."),
    ("cl", "company_identity", "country",
     "Country code for company location. Primarily US."),
    ("cl", "company_identity", "industry",
     "Industry classification as received from source system. Not standardized across sources."),
    ("cl", "company_identity", "employee_count",
     "Approximate employee count from source system. Integer. May be stale depending on source freshness."),
    ("cl", "company_identity", "phone",
     "Company main phone number as received from source system."),
    ("cl", "company_identity", "website_url",
     "Full website URL with protocol (https://). May differ from domain field by having www prefix or path."),
    ("cl", "company_identity", "description",
     "Brief company description from source system. Free text."),
    ("cl", "company_identity", "founded_year",
     "Year the company was founded, from source system. Integer."),
    ("cl", "company_identity", "annual_revenue",
     "Estimated annual revenue from source system. Text field — not normalized to numeric."),
    ("cl", "company_identity", "company_unique_id",
     "Legacy Barton ID (text). Used for bridge to company.company_master. NOT a UUID — distinct from sovereign_company_id."),

    # ========================================================================
    # outreach.outreach — Operational spine (workflow state)
    # ========================================================================
    ("outreach", "outreach", "ein",
     "9-digit Employer Identification Number from DOL bridge. No dashes. NULL if DOL bridge not yet established."),

    # ========================================================================
    # outreach.company_target — Company targeting data (Gate #1)
    # ========================================================================
    ("outreach", "company_target", "mx_valid",
     "Whether MX DNS records were found for the domain. TRUE = mail server exists. Used to validate email deliverability."),
    ("outreach", "company_target", "email_method",
     "Email pattern discovery method. HUNTER_VERIFIED = from Hunter API. PATTERN_DERIVED = inferred from verified contact."),
    ("outreach", "company_target", "outreach_id",
     "CTB_CONTRACT: Primary key. FK to outreach.outreach.outreach_id. Links this company target record to the operational spine."),
    ("outreach", "company_target", "company_unique_id",
     "Legacy Barton company ID (text). Bridge key to company.company_master. NOT a UUID."),
    ("outreach", "company_target", "source",
     "Originating source system. Same values as cl.company_identity.source."),
    ("outreach", "company_target", "email_pattern_status",
     "Pattern verification status. GUESS = algorithmically derived, unverified. FACT = confirmed via verified email delivery."),

    # ========================================================================
    # outreach.dol — DOL filing references (Gate #2)
    # ========================================================================
    ("outreach", "dol", "outreach_id",
     "CTB_CONTRACT: Primary key. FK to outreach.outreach.outreach_id. Links DOL intelligence to the operational spine."),
    ("outreach", "dol", "ein",
     "9-digit Employer Identification Number from IRS/DOL. No dashes. Bridges to dol.form_5500 and dol.schedule_a via sponsor_dfe_ein."),
    ("outreach", "dol", "filing_present",
     "Whether a Form 5500 filing was found for this EIN. TRUE = filing exists in dol.form_5500. FALSE = EIN known but no filing matched."),
    ("outreach", "dol", "funding_type",
     "Benefits plan funding classification. Values: fully_insured, self_funded, pension_only, unknown. Derived from Form 5500 plan characteristics."),
    ("outreach", "dol", "carrier",
     "Primary health insurance carrier name from Schedule A. NULL if no Schedule A data or no health line found. ~14.6% fill rate."),
    ("outreach", "dol", "broker_or_advisor",
     "Broker or advisor name from Schedule C (service provider code 28). NULL if no Schedule C data. ~10% fill rate."),
    ("outreach", "dol", "renewal_month",
     "Plan year begin month (1-12) from Form 5500. Indicates when the benefits plan renews annually. Used to calculate outreach timing."),
    ("outreach", "dol", "outreach_start_month",
     "Calculated outreach start month (1-12). Equals renewal_month minus 5 months (wraps around). Outreach should begin this month."),
    ("outreach", "dol", "created_at",
     "Timestamp when this DOL bridge record was created."),
    ("outreach", "dol", "updated_at",
     "Timestamp of last modification to this DOL record."),

    # ========================================================================
    # outreach.blog — Blog/content signals (Gate #4)
    # ========================================================================
    ("outreach", "blog", "outreach_id",
     "CTB_CONTRACT: Primary key. FK to outreach.outreach.outreach_id. Links blog/content signals to the operational spine."),
    ("outreach", "blog", "source_url",
     "Full URL to the discovered content page (About Us, News, Press, Leadership, etc.). From company.company_source_urls."),
    ("outreach", "blog", "source_type",
     "Content page classification. Values: about_page, press_page, leadership_page, team_page, careers_page, contact_page, blog_page, investor_page, pending."),
    ("outreach", "blog", "context_summary",
     "Extracted text content or HTML snippet from the source URL. Used for narrative signal detection."),
    ("outreach", "blog", "signal_detected",
     "Whether a narrative signal (hiring, funding, leadership change, etc.) was detected in the content. Boolean."),
    ("outreach", "blog", "signal_type",
     "Classification of the detected narrative signal. NULL if no signal detected."),
    ("outreach", "blog", "signal_strength",
     "Numeric strength/confidence of the detected signal. Higher = stronger evidence. NULL if no signal."),
    ("outreach", "blog", "created_at",
     "Timestamp when this blog record was created."),
    ("outreach", "blog", "updated_at",
     "Timestamp of last modification to this blog record."),

    # ========================================================================
    # outreach.bit_scores — BIT/CLS scoring engine
    # ========================================================================
    ("outreach", "bit_scores", "outreach_id",
     "CTB_CONTRACT: Primary key. FK to outreach.outreach.outreach_id. Links CLS authorization score to the operational spine."),
    ("outreach", "bit_scores", "score",
     "Composite CLS authorization score (0-100). Determines authorization band (0=SILENT, 1=WATCH, 2=EXPLORATORY, 3=TARGETED, 4=ENGAGED, 5=DIRECT)."),
    ("outreach", "bit_scores", "signal_count",
     "Total number of distinct movement signals contributing to this score. More signals = higher convergence confidence."),
    ("outreach", "bit_scores", "people_score",
     "Decision Surface domain score component. Derived from People sub-hub signals (executive changes, slot fills). Medium velocity."),
    ("outreach", "bit_scores", "dol_score",
     "Structural Pressure domain score component. Derived from DOL filing signals (cost changes, broker churn, funding shifts). Highest trust. Slow velocity."),
    ("outreach", "bit_scores", "blog_score",
     "Narrative Volatility domain score component. Derived from blog/content signals (news, press, hiring). Lowest trust. Amplifier only — never justifies contact alone."),
    ("outreach", "bit_scores", "talent_flow_score",
     "Talent flow domain score component. Derived from executive movement signals (joins, departures, promotions)."),
    ("outreach", "bit_scores", "score_tier",
     "CLS authorization tier label. Values: COLD (0-24), WARM (25-49), HOT (50-74), BURNING (75+). Determines permitted outreach actions."),
    ("outreach", "bit_scores", "created_at",
     "Timestamp when this score record was first created."),
    ("outreach", "bit_scores", "updated_at",
     "Timestamp of last score recalculation."),

    # ========================================================================
    # people.people_master — Contact/executive data (SUPPORTING for company_slot)
    # ========================================================================
    ("people", "people_master", "people_id",
     "CTB_CONTRACT: Primary key. UUID. Unique identifier for each person record. Referenced by people.company_slot.people_id."),
    ("people", "people_master", "outreach_id",
     "CTB_CONTRACT: FK to outreach.outreach.outreach_id. Links this person to their company via the operational spine."),
    ("people", "people_master", "first_name",
     "Person first name. From Hunter.io, Clay, or manual enrichment."),
    ("people", "people_master", "last_name",
     "Person last name. From Hunter.io, Clay, or manual enrichment."),
    ("people", "people_master", "full_name",
     "Full name (first + last). Concatenated or from source system."),
    ("people", "people_master", "title",
     "Job title as received from source. Used for slot type classification (CEO/CFO/HR keywords)."),
    ("people", "people_master", "email",
     "Business email address. May be Hunter-verified or pattern-derived (first.last@domain.com)."),
    ("people", "people_master", "phone",
     "Direct phone number. ~680 records have phone data. From Hunter or manual enrichment."),
    ("people", "people_master", "linkedin_url",
     "Person LinkedIn profile URL. Primary source: Hunter.io contacts (354,647 have LinkedIn). ~80.8% fill rate."),
    ("people", "people_master", "source",
     "Data source that provided this person record. Values: hunter, clay, manual, apollo."),
    ("people", "people_master", "confidence_score",
     "Email confidence score from Hunter.io (0-100). Higher = more likely deliverable. NULL if not from Hunter."),
    ("people", "people_master", "email_verified",
     "Whether email was checked via Million Verifier. TRUE = verification attempted (result may be VALID or INVALID)."),
    ("people", "people_master", "outreach_ready",
     "CTB_CONTRACT: Safety gate for outreach. TRUE = email is VALID and safe to send. FALSE = email is INVALID or RISKY. Critical: NEVER send outreach when FALSE."),
    ("people", "people_master", "verification_result",
     "Million Verifier result. Values: valid (safe to send), risky (catch-all domain), invalid (do not send), unknown (not yet verified)."),
    ("people", "people_master", "created_at",
     "Timestamp when this person record was first created."),
    ("people", "people_master", "updated_at",
     "Timestamp of last modification to this person record."),
    ("people", "people_master", "barton_id",
     "Barton ID format: 04.04.02.YY.NNNNNN.NNN. Structured identifier with doctrine code + year + sequence + sub-sequence."),
    ("people", "people_master", "slot_type",
     "Executive slot classification. Values: CEO, CFO, HR, CTO, CMO, COO. Determines which company_slot this person fills."),
    ("people", "people_master", "email_type",
     "Email pattern type. Values: personal, generic, professional. Indicates whether email follows a derivable pattern."),
    ("people", "people_master", "department",
     "Department classification from source system. Not standardized."),
    ("people", "people_master", "seniority",
     "Seniority level from source system. Values like: executive, senior, director, manager."),
    ("people", "people_master", "twitter_url",
     "Twitter/X profile URL from source system. Low fill rate."),
    ("people", "people_master", "company_name",
     "Company name as associated with this person in the source system. May differ from CL company_name."),
    ("people", "people_master", "domain",
     "Company domain associated with this person. Used for matching to outreach.outreach."),
    ("people", "people_master", "position",
     "Normalized job position. May differ from raw title field."),

    # ========================================================================
    # people.company_slot — Executive slot assignments (CANONICAL for people sub-hub)
    # ========================================================================
    ("people", "company_slot", "slot_id",
     "CTB_CONTRACT: Primary key. UUID. Unique identifier for each executive slot (3 per company: CEO, CFO, HR)."),
    ("people", "company_slot", "outreach_id",
     "CTB_CONTRACT: FK to outreach.outreach.outreach_id. Links this slot to the company via the operational spine."),
    ("people", "company_slot", "slot_type",
     "Executive position type. Values: CEO, CFO, HR. Each company has exactly 3 slots (one per type)."),
    ("people", "company_slot", "people_id",
     "CTB_CONTRACT: FK to people.people_master.people_id. The person currently filling this slot. NULL if slot is unfilled (gap)."),
    ("people", "company_slot", "is_filled",
     "Whether this slot has a person assigned. TRUE = people_id is not NULL. FALSE = gap requiring enrichment."),
    ("people", "company_slot", "created_at",
     "Timestamp when this slot record was first created."),
    ("people", "company_slot", "updated_at",
     "Timestamp of last modification (e.g. when a person was assigned or removed)."),
    ("people", "company_slot", "slot_phone",
     "Direct phone number for the person in this slot. Denormalized from people_master for quick access."),
    ("people", "company_slot", "barton_id",
     "Barton ID of the person filling this slot. Denormalized from people_master.barton_id for quick reference."),
]


def run():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    added = 0
    skipped = 0
    errors = []

    for schema, table, column, description in COLUMN_DOCS:
        # Check if description already exists
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

        # Add the description
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

    # Verification pass
    print(f"\n{'='*80}")
    print("VERIFICATION - Post-documentation coverage")
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

    pct = 100 * total_documented / total_cols if total_cols > 0 else 0
    print(f"\n  TOTAL: {total_documented}/{total_cols} columns documented ({pct:.1f}%)")

    cur.close()
    conn.close()


if __name__ == "__main__":
    run()
