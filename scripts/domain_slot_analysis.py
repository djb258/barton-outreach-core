"""
Domain-Based Slot Filling Analysis
===================================
READ-ONLY investigation of Hunter.io contact matching via domain linkage.

Queries:
1. Hunter contacts matchable via domain
2. CEO slot fill potential via domain matching
3. CFO slot fill potential
4. HR slot fill potential
5. Sample CEO slot fills with contact details
6. Schema verification for outreach.company_target.domain
"""

import psycopg2
import os
from datetime import datetime

# Database connection from environment
HOST = os.getenv('NEON_HOST', 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech')
DATABASE = os.getenv('NEON_DATABASE', 'Marketing DB')
USER = os.getenv('NEON_USER', 'Marketing DB_owner')
PASSWORD = os.getenv('NEON_PASSWORD')

def run_analysis():
    """Execute all domain-based slot analysis queries."""

    conn = psycopg2.connect(
        host=HOST,
        database=DATABASE,
        user=USER,
        password=PASSWORD,
        sslmode='require'
    )
    cur = conn.cursor()

    print('=' * 80)
    print('DOMAIN-BASED SLOT FILLING ANALYSIS')
    print('=' * 80)
    print(f'Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('Status: READ-ONLY')
    print('')

    # -------------------------------------------------------------------------
    # Query 1: Hunter contacts matchable via domain
    # -------------------------------------------------------------------------
    print('[1/6] Hunter contacts matchable via domain')
    print('-' * 80)

    cur.execute("""
        SELECT COUNT(DISTINCT hc.domain) as matchable_domains
        FROM enrichment.hunter_contact hc
        JOIN outreach.outreach o ON LOWER(hc.domain) = LOWER(o.domain);
    """)
    result = cur.fetchone()
    print(f'Matchable domains: {result[0]:,}')
    print('')

    # -------------------------------------------------------------------------
    # Query 2: CEO slot fill potential
    # -------------------------------------------------------------------------
    print('[2/6] CEO slot fill potential via domain matching')
    print('-' * 80)

    cur.execute("""
        SELECT COUNT(*) as fillable_ceo_slots
        FROM people.company_slot cs
        JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
        JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
        WHERE cs.slot_type = 'CEO'
          AND cs.is_filled = FALSE
          AND cs.person_unique_id IS NULL
          AND (hc.job_title ILIKE '%chief executive%'
               OR hc.job_title ILIKE '%ceo%'
               OR (hc.job_title ILIKE '%president%' AND hc.job_title NOT ILIKE '%vice%'));
    """)
    result = cur.fetchone()
    ceo_fillable = result[0]
    print(f'Fillable CEO slots: {ceo_fillable:,}')

    # Get total unfilled CEO slots
    cur.execute("""
        SELECT COUNT(*) as total_unfilled_ceo
        FROM people.company_slot
        WHERE slot_type = 'CEO'
          AND is_filled = FALSE
          AND person_unique_id IS NULL;
    """)
    result = cur.fetchone()
    total_ceo_unfilled = result[0]
    fill_rate = (ceo_fillable / total_ceo_unfilled * 100) if total_ceo_unfilled > 0 else 0
    print(f'Total unfilled CEO slots: {total_ceo_unfilled:,}')
    print(f'Fill potential: {fill_rate:.1f}%')
    print('')

    # -------------------------------------------------------------------------
    # Query 3: CFO slot fill potential
    # -------------------------------------------------------------------------
    print('[3/6] CFO slot fill potential via domain matching')
    print('-' * 80)

    cur.execute("""
        SELECT COUNT(*) as fillable_cfo_slots
        FROM people.company_slot cs
        JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
        JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
        WHERE cs.slot_type = 'CFO'
          AND cs.is_filled = FALSE
          AND cs.person_unique_id IS NULL
          AND (hc.job_title ILIKE '%chief financial%'
               OR hc.job_title ILIKE '%cfo%'
               OR hc.job_title ILIKE '%finance director%');
    """)
    result = cur.fetchone()
    cfo_fillable = result[0]
    print(f'Fillable CFO slots: {cfo_fillable:,}')

    cur.execute("""
        SELECT COUNT(*) as total_unfilled_cfo
        FROM people.company_slot
        WHERE slot_type = 'CFO'
          AND is_filled = FALSE
          AND person_unique_id IS NULL;
    """)
    result = cur.fetchone()
    total_cfo_unfilled = result[0]
    fill_rate = (cfo_fillable / total_cfo_unfilled * 100) if total_cfo_unfilled > 0 else 0
    print(f'Total unfilled CFO slots: {total_cfo_unfilled:,}')
    print(f'Fill potential: {fill_rate:.1f}%')
    print('')

    # -------------------------------------------------------------------------
    # Query 4: HR slot fill potential
    # -------------------------------------------------------------------------
    print('[4/6] HR slot fill potential via domain matching')
    print('-' * 80)

    cur.execute("""
        SELECT COUNT(*) as fillable_hr_slots
        FROM people.company_slot cs
        JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
        JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
        WHERE cs.slot_type = 'HR'
          AND cs.is_filled = FALSE
          AND cs.person_unique_id IS NULL
          AND (hc.job_title ILIKE '%human resources%'
               OR hc.job_title ILIKE '%hr director%'
               OR hc.job_title ILIKE '%hr manager%'
               OR hc.job_title ILIKE '%people%');
    """)
    result = cur.fetchone()
    hr_fillable = result[0]
    print(f'Fillable HR slots: {hr_fillable:,}')

    cur.execute("""
        SELECT COUNT(*) as total_unfilled_hr
        FROM people.company_slot
        WHERE slot_type = 'HR'
          AND is_filled = FALSE
          AND person_unique_id IS NULL;
    """)
    result = cur.fetchone()
    total_hr_unfilled = result[0]
    fill_rate = (hr_fillable / total_hr_unfilled * 100) if total_hr_unfilled > 0 else 0
    print(f'Total unfilled HR slots: {total_hr_unfilled:,}')
    print(f'Fill potential: {fill_rate:.1f}%')
    print('')

    # -------------------------------------------------------------------------
    # Query 5: Sample CEO slot fills
    # -------------------------------------------------------------------------
    print('[5/6] Sample CEO slot fills (5 records)')
    print('-' * 80)

    cur.execute("""
        SELECT
            cs.outreach_id,
            o.domain,
            hc.email,
            hc.first_name,
            hc.last_name,
            hc.job_title,
            hc.confidence_score,
            hc.linkedin_url
        FROM people.company_slot cs
        JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
        JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
        WHERE cs.slot_type = 'CEO'
          AND cs.is_filled = FALSE
          AND cs.person_unique_id IS NULL
          AND (hc.job_title ILIKE '%chief executive%'
               OR hc.job_title ILIKE '%ceo%'
               OR (hc.job_title ILIKE '%president%' AND hc.job_title NOT ILIKE '%vice%'))
        ORDER BY hc.confidence_score DESC NULLS LAST
        LIMIT 5;
    """)

    results = cur.fetchall()
    if results:
        print(f'{"Outreach ID":<40} {"Domain":<25} {"Name":<25} {"Title":<30} {"Score":<10}')
        print('-' * 130)
        for row in results:
            outreach_id = str(row[0])[:36]
            domain = row[1] or 'N/A'
            name = f"{row[3] or ''} {row[4] or ''}".strip() or 'N/A'
            title = row[5] or 'N/A'
            score = row[6] if row[6] is not None else 'N/A'
            print(f'{outreach_id:<40} {domain:<25} {name:<25} {title:<30} {score:<10}')
            print(f'  Email: {row[2] or "N/A"}')
            print(f'  LinkedIn: {row[7] or "N/A"}')
            print('')
    else:
        print('No CEO slot fill candidates found')
    print('')

    # -------------------------------------------------------------------------
    # Query 6: Schema verification
    # -------------------------------------------------------------------------
    print('[6/6] Schema verification: outreach.company_target')
    print('-' * 80)

    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'outreach'
          AND table_name = 'company_target'
        ORDER BY ordinal_position;
    """)

    results = cur.fetchall()
    print(f'{"Column Name":<30} {"Data Type":<20} {"Nullable":<10}')
    print('-' * 60)
    for row in results:
        print(f'{row[0]:<30} {row[1]:<20} {row[2]:<10}')

    # Check if domain column exists
    domain_exists = any(row[0] == 'domain' for row in results)
    print('')
    if domain_exists:
        print('RESULT: outreach.company_target.domain column EXISTS')
    else:
        print('RESULT: outreach.company_target.domain column DOES NOT EXIST')
        print('NOTE: Domain is stored in outreach.outreach table instead')

    print('')
    print('=' * 80)
    print('ANALYSIS COMPLETE')
    print('=' * 80)

    cur.close()
    conn.close()

if __name__ == '__main__':
    run_analysis()
